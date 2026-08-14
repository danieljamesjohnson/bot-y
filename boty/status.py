"""Status snapshot for the dashboard.

Written after every cycle so the page shows what the monitor actually last
saw, including detector health. The page is deliberately dumb — it renders
this file and nothing else — so the monitor stays the single source of truth.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from .models import Health, Result

log = logging.getLogger(__name__)


def write(
    path: Path,
    results: list[Result],
    health: list[Health],
    *,
    duration_seconds: float | None = None,
    paced: dict[str, str] | None = None,
    intervals: dict[str, float] | None = None,
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
            }
            for r in results
        ],
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(path)  # atomic, so the page never reads a half-written file
    except OSError:
        log.exception("could not write status to %s", path)
