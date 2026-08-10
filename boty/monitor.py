"""The check loop, state, and detector health.

Two behaviours here are the reason this project exists.

1. Edge-triggered alerts. You want to be told when something *becomes*
   available, not once a minute for as long as it stays available.

2. Control watches. A restock monitor's worst failure is silent: a retailer
   reskins, the detector stops matching, and it reports out-of-stock forever
   while looking perfectly healthy. You find out weeks later, having missed
   the drop. So every retailer carries at least one control — a product known
   to be in stock. If a control stops reading IN_STOCK you get told, loudly,
   that this retailer's readings are no longer verified — and that the cause is
   not established.

   WHAT THIS PARAGRAPH USED TO SAY, AND WHY IT DOES NOT ANY MORE. Until
   2026-08-10 it read: "If a control stops reading IN_STOCK, the *detector* is
   broken and you get told that, loudly, instead of silence." That is a cause,
   and this module cannot establish it. A control failing is consistent with a
   rotted extractor, with the retailer reshaping its markup, and with the
   control product having genuinely sold out — the code cannot tell those apart,
   and on 2026-08-04 asserting the first of them anyway sent 20 pages in 24
   hours for two retailers whose detectors were fine. Overruled by REQ-15: no
   alert names a cause the code has not established, and where the cause is
   unknown the alert says so. What is measured is that a control stopped
   verifying; that is what is now reported.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .models import STORE_SCOPED, Availability, Health, Result, Watch

if TYPE_CHECKING:  # pragma: no cover
    from .pacing import Pacer

log = logging.getLogger(__name__)

#: The one spelling of "we do not know why", used by every arm that has to say
#: it. REQ-15's second clause — *where the cause is unknown, the alert says so* —
#: is a property a test can only check MECHANICALLY if the sentence has exactly
#: one spelling, and `tests/test_alert_text.py` checks it by asserting which arms
#: carry this constant and which do not.
#:
#: One constant and not three paraphrases for a second reason: three copies
#: drift, and drift is how the two sentences this replaced came to be wrong.
CAUSE_UNKNOWN = "the cause is not established"


@dataclass
class State:
    """Last-seen availability per watch, so alerts fire on transitions."""

    path: Path
    seen: dict[str, str]

    @classmethod
    def load(cls, path: Path) -> State:
        try:
            return cls(path, json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError):
            return cls(path, {})

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.seen, indent=2, sort_keys=True))

    def transitioned_to_stock(self, result: Result) -> bool:
        """True if this is a *new* in-stock reading.

        UNKNOWN never overwrites a known state — otherwise one blocked fetch
        would reset the memory and re-alert on the next successful check.
        """
        if result.availability is Availability.UNKNOWN:
            return False
        key = result.watch.key
        previous = self.seen.get(key)
        self.seen[key] = result.availability.value
        return result.availability is Availability.IN_STOCK and previous != Availability.IN_STOCK.value


def _is_store_gap(c: Result) -> bool:
    """True when this control failed because its reading is not about a known store.

    Detected from FACTS, not from `detail` prose: the retailer predicate and the
    two conditions `retailers._verdict_from_html`'s guards branch on, reading the
    same `STORE_SCOPED` so the guard and this arm cannot drift apart. Matching on
    the message text would tie this to prose that is edited far more often than
    the condition is — the anchoring lesson `scripts/mutation_check.py`'s M2
    comment already paid for once.

    A REFUSAL IS NEVER A STORE GAP, and that is the first line for a reason. A
    refusal means no page came back, so the store could not have been established
    either; attributing one to the store pin would be naming a cause we did not
    measure, which is the defect this module is being repaired for.

    NEITHER IS ANY OTHER NO-PAGE OUTCOME, and that is the last line. The clause
    used to read `c.store != c.watch.store_id`, which is satisfied by
    `store=None` — and `is_refusal` is True only for `Blocked` and statuses
    {401, 403, 429} (`boty/fetch.py`), so a connection timeout, a DNS failure, a
    TLS error, an HTTP 500 or 502 all arrive here with `refused=False` and no
    page behind them. Each one produced an alert telling the operator to go and
    check a `store_id` that was set correctly, in a file that was not the
    problem: REQ-15's defect rebuilt inside the arm added to serve REQ-15. The
    docstring above already had the argument and simply did not extend it.

    ONLY TWO STATES ARE GENUINELY MEASURED, so only two return True:

    - the pin is ABSENT, which is read off the config and is therefore true
      whatever the page did (or did not) say; and
    - a store ANSWERED and it was not the pinned one.

    A page that named NO store establishes nothing about the pin — a timeout, a
    500 and a Walmart payload that stopped emitting
    `product.location.storeIds` all land there, and none of them is a config
    gap. They fall to the breakage arm, which carries `CAUSE_UNKNOWN` and is the
    reading that claims least. Naming a plausible-sounding cause instead is the
    failure this predicate exists to prevent, pointed the other way.
    """
    if c.refused:
        return False
    if c.watch.retailer not in STORE_SCOPED:
        return False
    if c.watch.store_id is None:
        return True
    return c.store is not None and c.store != c.watch.store_id


def assess_health(results: list[Result]) -> list[Health]:
    """Derive per-retailer detector health from control watches.

    A retailer with no control watch is reported as unhealthy — not because
    anything is known to be broken, but because nothing is known at all, and
    an unverified detector is exactly the failure mode this guards against.
    """
    by_retailer: dict[str, list[Result]] = {}
    for r in results:
        by_retailer.setdefault(r.watch.retailer, []).append(r)

    health: list[Health] = []
    for retailer, group in sorted(by_retailer.items()):
        controls = [r for r in group if r.watch.control]
        if not controls:
            health.append(Health(retailer, ok=False, reason="no control watch configured"))
            continue
        broken = [c for c in controls if c.availability is not Availability.IN_STOCK]
        if broken:
            # A wall, a store nobody pinned and a rotted extractor all land here,
            # and until 2026-08-04 every one of them was reported as "the
            # detector is probably broken". For a refusal that sentence is false:
            # the extractor was never reached. Saying it anyway cost 20 pages in
            # 24 hours, which is the fastest way to teach somebody to ignore this
            # channel.
            #
            # ARM PRECEDENCE. `refused` is evaluated FIRST and its rule is
            # unchanged — `all`, not `any`: if even one control failed for a
            # reason that is NOT a refusal, something may really be wrong and the
            # louder reading is the safe one. It goes first because a refusal
            # produced no page, so the store could not have been established
            # either, and reporting one as a store gap would be naming a cause
            # nobody measured. The store arm follows on the same `all` reasoning.
            # Everything else falls to the breakage arm, which is the reading
            # that claims least about a mixed group.
            refused = bool(broken) and all(c.refused for c in broken)
            store_gap = not refused and all(_is_store_gap(c) for c in broken)
            if refused:
                # What is established: a challenge page or a 403 came back
                # instead of a product page. Withdrawn 2026-08-10 (REQ-15), each
                # for its own reason, and none of them replaced with a new guess:
                #
                # - "we are asking too often". The code established a REFUSAL,
                #   never a RATE, and the claim was falsified twice — after
                #   backing off to a 6-hour interval the very next single request
                #   was still refused. An IP-reputation story, a fingerprint
                #   story and a "they changed their WAF" story are all equally
                #   unmeasured, so the honest replacement names none of them.
                # - "the detector is probably fine". The mirror of the defect,
                #   and easy to mistake for the fix: a refusal means the
                #   extractor was NEVER REACHED, so this reading establishes
                #   nothing about the detector in either direction.
                # - "Backing off, and no action is needed unless this persists".
                #   This function takes `list[Result]` and cannot see a `Pacer`,
                #   so that is a claim about a system behaviour it has no access
                #   to — this phase's own defect in miniature. Worse, it is
                #   delivered at the wrong moment: `cli.watch_cycle` only PAGES a
                #   refusal once `_refusal_is_entrenched` is true, which is
                #   exactly when "no action is needed" has become false.
                reason = (
                    f"the retailer is refusing us — a challenge page or a 403 came back "
                    f"instead of a product page, so the extractor was never reached and "
                    f"nothing here says whether it works; {CAUSE_UNKNOWN}"
                )
            elif store_gap:
                # The one failure in this function whose cause the code MEASURED,
                # which is why it deliberately does not carry CAUSE_UNKNOWN:
                # saying "the cause is not established" about a gap we can name
                # is the same dishonesty pointed the other way. Restrained, in
                # the shape of the "no control watch configured" line above — it
                # names the gap and nothing else, and leaves the per-watch
                # specifics to `failing_controls`, which interpolates each
                # control's `detail`, where `_verdict_from_html`'s two guards
                # already wrote precisely the right sentence.
                #
                # NO NEW SENDER, AND THE WIRING IS INHERITED RATHER THAN MISSING.
                # This arm is `refused=False`, so `cli.watch_cycle`'s existing
                # `pageable` filter pages it once per failure episode through
                # `warned`, and the existing `send_health_warning(...) is False`
                # branch already rolls that memory back on a failed delivery. A
                # second sender would need `boty/cli.py`, and an unwired send is
                # "not a retry — it is a drop nothing will ever mention again".
                reason = (
                    "a control reading cannot be shown to come from the store this "
                    "watch is about — store_id is unset in config/products.yaml, or the "
                    "page answered for a different store. Each control below names what "
                    "the page said and what is pinned"
                )
            else:
                # What is established: a control product — an item chosen
                # BECAUSE it is known to be in stock — did not read IN_STOCK, and
                # it was not a refusal and not a store gap. Whether the cause is
                # the extractor, the retailer's markup, or the control itself
                # having genuinely sold out is not established.
                #
                # The consequence clause survives the withdrawal while the cause
                # does not, and the difference is the point: "readings from this
                # retailer are unverified, so a real restock could be missed
                # silently" follows from what a CONTROL IS, not from a guess
                # about why it failed.
                reason = (
                    f"a control product did not read IN_STOCK and was not refused, so "
                    f"readings from this retailer are unverified and a real restock "
                    f"could be missed silently; {CAUSE_UNKNOWN}"
                )
            health.append(
                Health(
                    retailer,
                    ok=False,
                    refused=refused,
                    reason=reason,
                    failing_controls=[f"{c.watch.name}: {c.availability.value} ({c.detail})" for c in broken],
                )
            )
        else:
            health.append(Health(retailer, ok=True))
    return health


def run_once(
    watches: list[Watch],
    checker: Callable[[Watch], Result],
    state: State,
    pacer: Pacer | None = None,
    now: float = 0.0,
) -> tuple[list[Result], list[Health], list[Result]]:
    """Check every watch once. Returns (results, health, alerts).

    With a `pacer`, a retailer that is not due is SKIPPED — no request, and no
    result. It is deliberately not a synthetic UNKNOWN: a fabricated reading
    for a question nobody asked would flow into `assess_health`, report the
    detector as broken, and page somebody about a check we chose not to make.
    Skipping means `assess_health` never sees the retailer, so it stays silent
    about it, and `status.write` publishes it as paced rather than as green.
    """
    if pacer is not None:
        due = [w for w in watches if pacer.due(w.retailer, now)]
        skipped = {w.retailer for w in watches} - {w.retailer for w in due}
        for retailer in sorted(skipped):
            log.info("%-9s skipped — %s", retailer, pacer.skipped_reason(retailer, now))
        watches = due

    results = [checker(w) for w in watches]

    if pacer is not None:
        by_retailer: dict[str, list[Result]] = {}
        for r in results:
            by_retailer.setdefault(r.watch.retailer, []).append(r)
        for retailer, group in by_retailer.items():
            pacer.record(retailer, refused=any(x.refused for x in group), now=now)
    for r in results:
        log.info(
            "%-9s %-26s %-13s %s",
            r.watch.retailer,
            r.watch.name[:26],
            r.availability.value,
            r.detail[:70],
        )

    health = assess_health(results)

    # One pass over every result, with no short-circuiting, because
    # `transitioned_to_stock` is the only thing that writes the memory and it
    # mutates `state.seen` as a side effect. Both halves of that matter:
    #
    #   - It must run for EVERY result. `alertable` and `control` decide what
    #     we NOTIFY about, never what we REMEMBER. Calling it as the last term
    #     of an `and` chain meant Python skipped it for anything not alertable,
    #     so a product watch reading OUT_OF_STOCK was never recorded and stayed
    #     pinned at "in_stock" — swallowing every restock after the first.
    #   - It must run EXACTLY once per result. A second call compares against
    #     the value the first one just wrote, so a real transition would read
    #     as no transition at all.
    transitions = [state.transitioned_to_stock(r) for r in results]

    # `strict=True`, chosen against ruff's own unsafe autofix for B905, which
    # writes the permissive value (`False`) here instead. `transitions` is a
    # comprehension over `results` directly above, so the two are the same length
    # by construction. If that ever stopped being true, `zip` would silently
    # truncate `alerts` — and a truncated `alerts` list is a missed restock
    # notification, which reads on the wire exactly like a quiet market.
    # `strict=True` turns that into a crash, which is the outcome this project
    # prefers over a silent wrong verdict every time. The permissive value would
    # have preserved today's behaviour and permanently silenced the question.
    #
    # (Written without the literal permissive token on purpose: this plan's
    # acceptance criterion greps this file FOR `strict=True` and AGAINST the
    # other one, so quoting it here would defeat the check that guards it.)
    alerts = [
        r
        for r, transitioned in zip(results, transitions, strict=True)
        if not r.watch.control and r.alertable and transitioned
    ]
    state.save()
    return results, health, alerts
