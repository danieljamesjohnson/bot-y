"""Status snapshot for the dashboard.

Written after every cycle so the page shows what the monitor actually last
saw, including detector health. The page is deliberately dumb — it renders
this file and nothing else — so the monitor stays the single source of truth.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from .models import Availability, Health, Result, Watch

log = logging.getLogger(__name__)


def _remembered_rows(
    watches: list[Watch] | None,
    results: list[Result],
    remembered: dict[str, tuple[str, float | None]] | None,
) -> list[tuple[Watch, str, float | None]]:
    """The configured watches nobody read this cycle, each with what is remembered.

    Three jobs, and each one is a decision rather than plumbing:

    1. IT SELECTS BY ABSENCE FROM `results`, not by anything the pacer says.
       A watch is served by the fresh comprehension if and only if a `Result`
       exists for it, so the two branches are disjoint by construction and no row
       can be emitted twice or claimed by both. Returns `[]` when `watches` is
       `None`, which is the pre-07-04 payload exactly.

    2. IT SORTS BY `Watch.key`, mirroring `sorted((paced or {}).items())`
       directly below it. This ordering reaches a served file, so it is stable
       rather than whatever order a dict happened to be built in.

    3. `(Availability.UNKNOWN.value, None)` IS THE DEFAULT FOR A KEY THE LEDGER
       NEVER RESOLVED — and that single expression is REQ-21's criterion 2
       written as code: *where nothing was ever recorded, the age is UNKNOWN,
       never "now"*. Two ways a configured watch reaches it, both live: a fresh
       clone whose `state.json` does not exist yet, and a watch every reading of
       which has been UNKNOWN, because `State.transitioned_to_stock` returns on
       UNKNOWN before it writes. Both Walmart watches on this host are the second
       case today, `WALMART_STORE_ID` being unset.

    Extracted from the payload literal so that literal keeps flat local names and
    the partition logic has one home to be read in.
    """
    if watches is None:
        return []
    read_this_cycle = {r.watch.key for r in results}
    return [
        (w, *(remembered or {}).get(w.key, (Availability.UNKNOWN.value, None)))
        for w in sorted(watches, key=lambda w: w.key)
        if w.key not in read_this_cycle
    ]


def write(
    path: Path,
    results: list[Result],
    health: list[Health],
    *,
    duration_seconds: float | None = None,
    paced: dict[str, str] | None = None,
    intervals: dict[str, float] | None = None,
    watches: list[Watch] | None = None,
    remembered: dict[str, tuple[str, float | None]] | None = None,
) -> None:
    """Publish the current reading.

    `paced` maps a retailer that was NOT checked this cycle to the reason. It
    exists because pacing introduced a third state and neither of the first two
    describes it: the retailer is not healthy (nothing was verified) and not
    unhealthy (nothing failed) — it simply was not asked.

    Without this the retailer vanishes from the file entirely, and a reader
    counting rows sees five retailers where there are six and concludes one was
    dropped. Publishing it as `checked: false` with a reason is the same
    three-valued honesty `Availability` is built on, applied to a schedule.

    `intervals` maps a retailer to the cadence it is CURRENTLY on — the standing
    interval with whatever backoff is in force applied to it — and that is a
    different number from the `interval_seconds` in the operator's own config.
    Say the distinction rather than leave it to be inferred: a reader who
    conflates the two reads a six-hour cadence as a misconfiguration, when what
    it actually is is a retailer that has refused us seven times running.

    IT IS PUBLISHED BECAUSE THE PAGE HAS TO COMPARE AGAINST SOMETHING. REQ-21's
    criterion 3 says a reading is stale when it is older than its retailer's own
    current interval, derived from that retailer's pacing rather than from a
    fixed clock — so the threshold has to travel with the reading. 07-05 is where
    the comparison lands, in each of the three surfaces that make it.

    THE RAW FACT GOES OUT AND THE FLAG DOES NOT, which is the rule the `store`
    paragraph below states and this is its fourth application. A `stale` computed
    here would be written `false` and keep saying `false` for exactly the
    interval during which the row becomes stale — `pacing.py`'s
    stamp-at-write-time trap in mirror image, a bound that cannot bind. Every
    consumer subtracts against its own `now` instead.

    `null`, NEVER `0`. The `duration_seconds` and `store` arguments apply word
    for word and are sharper here: a cadence of `0` says *this retailer is
    checked continuously*, so every reading against it is stale the instant it
    is taken — the most confident possible lie about a number nobody
    established. `null` is "the cadence is not established on this surface",
    which is the same three-valued honesty the `checked: false` row beside it
    already carries.

    PER RETAILER, NOT PER WATCH. A cadence is a per-retailer fact, and a copy on
    each of fourteen watch rows is thirteen more copies that can drift.
    `served/boty/index.html` already holds `d.retailers` and already interpolates
    `w.retailer`, so the join is a lookup rather than a new payload shape.

    `watches` is every watch the operator CONFIGURED and `remembered` is what the
    ledger holds for them. Together they are what makes this file publish one row
    per configured watch instead of one row per reading taken this cycle. See the
    comment block on the second `watches` comprehension below for why that
    matters and what such a row is allowed to say.

    `remembered` MAPS A KEY TO A PAIR — the availability and the moment it was
    read — and that is the decision in this signature a reader will want to undo,
    so it is argued here. `monitor.State` holds `seen` and `read_at` as two
    separate attributes, so two keywords would be the shorter diff and the more
    obvious one. They are not taken: a caller that passed one and forgot the
    other would publish a remembered availability with no age, silently, with
    every test still green — this plan's own defect rebuilt in the plumbing that
    delivers the fix. Pairing them at one call site makes half a memory
    unrepresentable, which is `monitor.State`'s one-act rule pointed at the read
    side.

    BOTH DEFAULT TO `None`, AND THAT IS A COMPATIBILITY DEFAULT RATHER THAN A
    DEGRADED MODE — say which, because a permissive default looks like a soft
    failure path and this one is not. With no `watches` the remembered block is
    empty and the payload is what it was before 07-04 plus the `checked` key,
    deliberately, so every existing caller in `tests/` stays valid. WHAT STOPS
    THAT FROM BECOMING A PRODUCTION REGRESSION IS NOT THIS DEFAULT: it is the
    static AST gate in `tests/test_cli_watch.py` that asserts both `boty/cli.py`
    call sites pass both keywords. A behavioural test cannot see a call site that
    dropped a keyword — every assertion stays green and the dashboard quietly
    goes back to publishing five rows out of thirteen. That gate is where the
    teeth are.
    """
    payload: dict[str, Any] = {
        "updated": int(time.time()),
        # Only over retailers actually CHECKED. A paced retailer has not
        # failed anything; letting it flip this false would put the dashboard
        # permanently red and make the flag useless — the same "a gate that
        # fires on the honest outcome" defect the roadmap names.
        "healthy": all(h.ok for h in health),
        # How long the pass that produced this file took, in seconds. Published
        # so REQ-08's two-minute budget can be READ rather than re-measured by
        # hand — the only figure this project had before it existed was a
        # stopwatch number in a plan summary, which is a budget asserted rather
        # than measured.
        #
        # `None` means "nobody timed this pass", which is not "it took no
        # time": the same three-valued honesty `Availability` is built on,
        # applied to a number. A missing measurement serialised as 0 would read
        # off the dashboard as the fastest check ever recorded.
        #
        # Callers must time with `time.monotonic()`, never `time.time()`. This
        # file is served over HTTP, and a wall clock stepping backwards during
        # an NTP correction would publish a negative duration.
        "duration_seconds": duration_seconds,
        "retailers": [
            {
                "retailer": h.retailer,
                "ok": h.ok,
                # `refused` distinguishes "the retailer is turning us away"
                # from "our detector stopped working". Both are ok=False; only
                # the second one wants a human.
                "refused": h.refused,
                "checked": True,
                "reason": h.reason,
                "failing_controls": h.failing_controls,
                # The cadence this retailer is currently on. See the docstring:
                # `null` where none is established, never `0`.
                "current_interval_seconds": (intervals or {}).get(h.retailer),
            }
            for h in health
        ]
        + [
            {
                "retailer": retailer,
                # NOT ok: nothing was verified this cycle, and claiming
                # otherwise is the green-dashboard failure one level up.
                "ok": False,
                "refused": False,
                "checked": False,
                "reason": reason,
                "failing_controls": [],
                # ON THIS BRANCH TOO, and this is the row it matters most on: a
                # retailer deep enough in a backoff to be skipped is the one
                # whose readings are oldest.
                "current_interval_seconds": (intervals or {}).get(retailer),
            }
            for retailer, reason in sorted((paced or {}).items())
        ],
        "watches": [
            {
                "name": r.watch.name,
                "retailer": r.watch.retailer,
                "availability": r.availability.value,
                "price": r.price,
                "detail": r.detail,
                "url": r.url,
                "control": r.watch.control,
                "alertable": r.alertable,
                # Public API, not an internal detail: this file is served over
                # HTTP and the page renders it verbatim, so these three keys
                # are a contract with the dashboard and with the support
                # matrix, which reads them to say which rung each retailer
                # landed on. `rung` is written rather than only `degraded`
                # because "we reached Best Buy through its official API" and
                # "we reached it through a browser" are both non-default and
                # only one of them is a lower-confidence reading.
                #
                # `extraction` is published beside it for the same reason one
                # axis along. `degraded` alone cannot tell a reader WHY to
                # discount a reading, and the two reasons need different
                # plans: a browser transport means expect it to be slow and
                # heavy, while a dom extraction means expect a reskin to break
                # the parser without anything going red. Publishing only the
                # derived flag would collapse those into one word.
                "rung": r.rung.value,
                "extraction": r.extraction.value,
                "degraded": r.degraded,
                # WHICH STORE. Two keys, and that is the point: `store` is what
                # the page said answered, `store_pinned` is what the operator
                # configured. Published together for the reason `rung` and
                # `extraction` are published beside `degraded` — the raw facts go
                # out alongside any derived flag, because a single value cannot
                # tell a reader WHY.
                #
                # Applied here: one key alone cannot distinguish "no store
                # recorded" from "store B answered and you pinned A", and those
                # are the two states this phase exists to tell apart. On
                # 2026-08-09 this monitor recorded the Walmart milk control out
                # of stock at one price while three live reads minutes later
                # returned in stock at another. Same URL, same parser — two
                # stores answered, and nothing in the file could say so.
                #
                # `None` for a non-Walmart watch is correct and permanent: no
                # other retailer here publishes a store on a product page.
                # Serialised as `null`, NEVER as `0` and never as `""` — the
                # `duration_seconds` argument above applies word for word, and
                # here it is sharper than an analogy, because `0` is this repo's
                # own redaction placeholder and the literal value both Walmart
                # fixtures carry. An absent store published as `0` would read off
                # the dashboard as a real store.
                "store": r.store,
                "store_pinned": r.watch.store_id,
                # WHEN THIS READING WAS TAKEN — REQ-21's criterion 1, and the
                # answer to *"so they are out of stock as of when?"*, which this
                # file could not give at all before today.
                #
                # `null`, NEVER `0`. The `store` argument directly above applies
                # word for word, and here it is sharper in one respect: an absent
                # store published as `0` reads off the dashboard as a real store,
                # and an absent stamp published as `0` reads as 1 January 1970 —
                # MAXIMALLY STALE rather than unknown. That is the same class of
                # lie pointed the other way. Both directions of dishonesty are
                # available and `null` is the only value that takes neither.
                #
                # THIS IS NOT `updated`, and this is where a reader will look for
                # that sentence. The top-level `updated` above is computed ONCE
                # per `write` call, outside this comprehension, and it is when the
                # CYCLE ran — it is fresh when every row beneath it is stale, and
                # that exact confusion is the thing REQ-21 exists to remove. It is
                # not reused here and it is not renamed: `index.html:133-142`
                # reads it for the "monitor may not be running" banner, which asks
                # whether this snapshot is still being WRITTEN. Different
                # question, correct where it is, stays where it is.
                #
                # NO DERIVED `stale` KEY, and that is a decision rather than an
                # omission. A flag computed at write time fails the mirror way to
                # `pacing.py:196-199`: a row written fresh carries `stale: false`
                # and keeps carrying it for exactly the interval during which it
                # becomes stale — a bound that cannot bind. So the raw fact goes
                # out and every consumer subtracts against its own `now`, which is
                # this file's own rule from the `store` paragraph above ("the raw
                # facts go out alongside any derived flag") applied a third time.
                # 07-05 is where that comparison lands, in each of the three
                # surfaces that make it.
                "read_at": r.read_at,
                # WHERE THIS ROW CAME FROM. `true` means a `Result` exists for
                # this watch, i.e. somebody read a page this cycle. Appended
                # last so no existing key moves, on the precedent
                # `current_interval_seconds` set on the retailer rows above.
                #
                # It is the provenance flag the remembered rows below carry as
                # `false`, and together with `read_at` it is the ONLY thing that
                # tells the two kinds of row apart — see the comment block on
                # that comprehension.
                "checked": True,
            }
            for r in results
        ]
        + [
            {
                # EVERY CONFIGURED WATCH HAS A ROW, and this is the comprehension
                # that makes the rest of them exist. It is the `paced` retailer
                # rows one level up in this file, applied one level down, and the
                # paragraph that argues those applies to a watch WORD FOR WORD:
                #
                #   "the retailer is not healthy (nothing was verified) and not
                #   unhealthy (nothing failed) — it simply was not asked.
                #   Without this the retailer vanishes from the file entirely,
                #   and a reader counting rows sees five retailers where there
                #   are six and concludes one was dropped."
                #
                # THAT WAS NOT A HYPOTHETICAL FOR WATCHES. Measured on the live
                # file this daemon writes: 8 rows for 13 configured watches at
                # 09:24:54 on 2026-08-13, 3 rows at 08:25:10 the same morning,
                # 5 rows at 07:36:57 on 2026-08-14 — an unchanged config every
                # time. The row count was a function of PACING, so a reader who
                # opened the page twice in one morning watched the watch list
                # change size with no way to tell a watch that had been removed
                # from a watch that had not been asked.
                #
                # THE THREE-WAY PARTITION OF A ROW, which is the whole design:
                # config facts are published because they are true whether or
                # not anybody looked; the remembered reading is published
                # because it is what the ledger holds; facts about the ACT of
                # reading are `null` because nobody performed one; and
                # `alertable` — authority — is refused outright.
                #
                # `null` AND NEVER A DEFAULT, extending the `store` paragraph
                # above rather than restating it. `detail: ""` is a value the
                # fresh path already produces and it means *the page said
                # nothing worth repeating*; `null` never appears on a fresh row,
                # so it is the only one of the two a reader can tell apart. And
                # `degraded: false` on a memory would be a confidence claim
                # about a reading nobody took — which is why `rung`,
                # `extraction` and their derived flag go out as `null` together.
                #
                # WHY `alertable` IS A LITERAL, with the claim made carefully
                # rather than loudly. THIS KEY DOES NOT SEND ANYTHING: pushes
                # come from `run_once`'s `alerts` list, built from `Result`
                # objects, and no remembered row ever becomes a `Result`. What a
                # `true` here would be is a PUBLISHED CLAIM, on a served page
                # and in a file this project already has three consumers for,
                # that a reading nobody took is worth waking somebody for. And
                # it is not hypothetical arithmetic: measured against this
                # host's ledger, 8 of 13 remembered entries are `in_stock`, 6 of
                # those are controls, and the remaining two are the GameStop
                # `TRANSITION —` watches, which carry no `max_price` — so a
                # value derived from the memory would publish two false
                # buy-signals on every cycle GameStop is paced out, and GameStop
                # runs on a 900-second override.
                #
                # WHAT THIS ROW IS NOT: it carries no staleness verdict and no
                # tag. The raw facts go out and each consumer subtracts against
                # its own `now`, which is this file's own rule applied a fifth
                # time. 07-05 is where the three renderings land.
                "name": w.name,
                "retailer": w.retailer,
                "availability": availability,
                "price": None,
                "detail": None,
                "url": w.target,
                "control": w.control,
                "alertable": False,
                "rung": None,
                "extraction": None,
                "degraded": None,
                "store": None,
                "store_pinned": w.store_id,
                "read_at": read_at,
                "checked": False,
            }
            # SAME KEYS, SAME ORDER as the fresh row above. That is a decision
            # rather than an accident: it means `checked` and `read_at` are the
            # only things that distinguish a memory from an observation, which
            # is REQ-21's own opening sentence — *"byte-identical in shape"* —
            # converted from the defect into a stated property with exactly two
            # fields carrying the difference.
            for w, availability, read_at in _remembered_rows(watches, results, remembered)
        ],
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # A PER-PROCESS TEMP NAME, AND THE RENAME WAS NEVER THE PROBLEM. This
        # used to be `path.with_suffix(".tmp")` — a FIXED SIBLING shared by every
        # caller of this function — with the rename commented `# atomic, so the
        # page never reads a half-written file`. The rename is atomic. The
        # staging file was not private, and REQ-21 made two concurrent callers a
        # documented workflow: `boty/pacing.py` states that *"`cli.main`'s
        # `check` branch now loads this document too, on a surface routinely run
        # while the daemon is writing"*, and that same `boty check` invocation
        # also WRITES `cfg.status_path` through this function.
        #
        # The interleaving that allowed: the daemon truncates and begins writing
        # `status.tmp`; a concurrent `boty check` truncates the same file and
        # writes its own payload; the daemon renames. Whichever process renames
        # last publishes whatever bytes are in that one file, `JSON.parse` in the
        # dashboard's `tick()` throws, and the page reads `status unavailable`
        # until the next write. Transient and self-healing — and not what the
        # comment promised, which is the part that matters in a file where the
        # comment is the argument.
        #
        # SAME DIRECTORY, so `replace` stays on one filesystem and stays atomic.
        # A temp in `/tmp` would make the rename a cross-device copy, which is
        # exactly the half-written read this whole dance exists to prevent.
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        try:
            tmp.write_text(json.dumps(payload, indent=2))
            tmp.replace(path)  # atomic, so the page never reads a half-written file
        finally:
            # `replace` consumed it on the happy path, so this is a no-op there.
            # It is here for the unhappy one: a temp named after a process that
            # has since exited is an orphan nothing will ever clean up, which is
            # the cost of making the name unique and is paid rather than
            # discovered.
            tmp.unlink(missing_ok=True)
    except OSError:
        log.exception("could not write status to %s", path)
