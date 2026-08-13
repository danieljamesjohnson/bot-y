"""The check loop, state, and detector health.

Two behaviours here are the reason this project exists.

1. Edge-triggered alerts. You want to be told when something *becomes*
   available, not once a minute for as long as it stays available.

2. Control watches. A restock monitor's worst failure is silent: a retailer
   reskins, the detector stops matching, and it reports out-of-stock forever
   while looking perfectly healthy. You find out weeks later, having missed
   the drop. So every retailer carries at least one control — a product known
   to be in stock. If a control stops reading IN_STOCK, this retailer's readings
   are recorded as no longer verified — with the cause not established — on the
   status page, in `boty check` and in the log.

   "AND YOU GET TOLD, LOUDLY" USED TO END THAT SENTENCE, AND IT DOES NOT ANY
   MORE. Dan, 2026-08-12, the second time he raised it: *"im still getting
   annoying messages. we need to never hit the user unless its something they
   can buy or actually do"*. Nobody can repair a detector from a phone, and this
   module has just finished saying it does not know why the control failed — so
   the push asked for a decision that does not exist. What is RECORDED is
   unchanged and deliberately so: every state below still reaches every one of
   our own surfaces in full. What changed is that a state now has to carry a
   `Health.action` — a thing a person can DO — before `cli.watch_cycle` will
   wake anybody with it, and exactly one arm here can name one.

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
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
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

#: The one thing in this module a person can actually DO, spelled once — the
#: `Health.action` the store-gap arm carries, and the only reason any health
#: state below is allowed to reach a phone.
#:
#: IT NAMES A CONFIG VALUE AND NOTHING ELSE, and that is what makes it an action
#: rather than a diagnosis: the pin is absent or the page answered for another
#: store, both of which are read off values we hold, and setting it is a step
#: only the operator can take. Every other arm here ends in a fact about a
#: retailer or in `CAUSE_UNKNOWN`, and neither is something anybody can do.
#:
#: NO STORE NUMBER, EVER — this string is joined into a push body that leaves
#: the machine over `ntfy://` and friends, and `notify._redact_store_numbers`
#: exists because a store number resolves publicly to one street address. It
#: names the VARIABLE, not a value.
#:
#: One constant, one spelling, for `CAUSE_UNKNOWN`'s reason: a property stated
#: three ways cannot be checked mechanically, and `scripts/mutation_check.py`
#: anchors on the NAME rather than on this prose.
STORE_PIN_ACTION = (
    "set this watch's store_id in config/products.yaml — it reads "
    "${WALMART_STORE_ID}, so the value goes in the daemon's EnvironmentFile"
)

#: The oldest wall clock a reading time read back off disk may carry: midnight
#: 2000-01-01 UTC. A measured number, not a round one, and argued from both
#: directions in `MAX_PERSISTED_REFUSALS`'s shape.
#:
#: `tzinfo` is explicit so the constant does not depend on the host's zone — a
#: floor that moved by five hours between the daemon's box and a contributor's
#: laptop would be a bound whose value nobody could quote.
#:
#: WHAT IT CATCHES. A `0`, which is the absent-published-as-zero lie one
#: direction over: zero is not "unknown", it renders as 1 January 1970, so a
#: consumer subtracting against `now` reports the reading as fifty-six years
#: stale rather than as unestablished. A seconds value that lost a factor of a
#: thousand (milliseconds divided once too often, or a `/ 1000` applied to a
#: number that was already seconds). A truncated or hand-edited number. All
#: three are numbers this program cannot have written, and believing one
#: publishes an age that was never measured — REQ-21's whole subject.
#:
#: WHAT IT DELIBERATELY DOES NOT DO: expire a real reading.
#: `pacing.STATE_MAX_AGE_SECONDS` is NOT reused as the far bound here, and the
#: difference is not a preference. There the far bound is six hours because a
#: refusal COUNT past the cap "has outlived its reasoning" — a refusal is a
#: penalty, and penalties expire. A reading's age does not: the older it is, the
#: more the operator needs to see it. Applying that constant here would silently
#: delete every stamp older than one backoff window, which is this phase's own
#: datum evaporating twice a day — a bound that binds on the wrong thing, and
#: therefore the very defect this phase exists to remove.
#:
#: WHY IT CAN NEVER BIND ON ANYTHING REAL: this repository's first commit is
#: 2026-08-02, so the floor sits more than a quarter of a century below the
#: earliest stamp any clock this program has ever run on could produce. It
#: rejects impossible numbers and nothing else.
#:
#: AND A STANDING INSTRUCTION: do NOT "tighten" this to the date the field
#: shipped. It is a floor on CREDIBILITY, not a freshness policy. The tests
#: construct aged documents by subtraction from the real clock, and this
#: project's entire subject is a reading that is genuinely days old — a floor
#: near today would reject exactly the readings REQ-21 exists to surface.
EARLIEST_CREDIBLE_READING = datetime(2000, 1, 1, tzinfo=timezone.utc).timestamp()


def _remembered_availability(entry: object) -> str | None:
    """The availability inside one persisted entry, or `None` to skip it whole.

    `object` rather than a narrower type because this reads a `json.loads`
    result: everything here is what a file said, not what a caller promised.

    A `str` entry is THE PRE-07 SHAPE — a bare availability carrying no age at
    all, which is the document on this host today, and it loads as *availability
    with an unknown age*. That branch is the whole migration; there is no version
    field and no conversion pass, because tolerance per entry also reads a
    document an older binary rewrote mixed, which a version could not.

    A `dict` entry is this program's own shape and yields its `availability` when
    that value is a `str`.

    THE REMEMBERED AVAILABILITY IS NOT VALIDATED AGAINST THE `Availability` ENUM,
    and that is a decision rather than an omission. The only comparison ever made
    against this string is `!= Availability.IN_STOCK.value`, so a value outside
    the enum already behaves as "not in stock" — the safe direction. Rejecting it
    would add a branch that changes no outcome, which is a gate that cannot bite,
    which is the defect this phase is being written to remove.
    """
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        availability = entry.get("availability")
        if isinstance(availability, str):
            return availability
    return None


def _remembered_stamp(entry: object, now: float) -> float | None:
    """The reading time inside one persisted entry, or `None` for UNKNOWN age.

    `None` here means the age is not established. It never means `0.0` and it
    never means `now`: manufacturing either is REQ-21's defect, moved from the
    reading to the restart.

    One expression covers both shapes of the document, so the pre-07 bare string
    and the `"read_at": null` this program writes for itself every cycle arrive
    at the same guard rather than at two that could drift.

    `pacing.load`'s worked shape (`pacing.py:335-350`), adapted where it must be.
    """
    stamp = entry.get("read_at") if isinstance(entry, dict) else None
    # `bool` is an `int` subclass, so `"read_at": true` would otherwise restore a
    # reading taken one second after midnight 1970. `config._price`'s precedent,
    # which `pacing.load` cites for the same reason two modules over.
    if not isinstance(stamp, (int, float)) or isinstance(stamp, bool):
        return None
    # BOTH bounds, as one comparison. A stamp in the FUTURE is a clock that
    # jumped backwards, and with only a lower bound it would read as fresh for as
    # long as the skew lasted — the fresh direction, which is the dangerous one.
    # A stamp below the floor was not written by this program at all.
    if not EARLIEST_CREDIBLE_READING <= float(stamp) <= now:
        return None
    return float(stamp)


@dataclass
class State:
    """Last-seen availability per watch and WHEN it was read, so alerts fire on transitions."""

    path: Path
    seen: dict[str, str]
    #: The wall clock at which each remembered availability was read. Keyed by
    #: the same `watch.key` as `seen`, and declared LAST with a default so every
    #: existing positional `State(path, {})` construction stays valid and keeps
    #: its meaning — the chain `Result.rung`, `Result.store`, `Result.shipping`
    #: and `Pacer.state_path` each extend. That is load-bearing rather than
    #: stylistic here: `tests/test_pacing.py:271` and `:299` construct this class
    #: positionally, and `cli.py` and this module construct it in three more
    #: places.
    #:
    #: A KEY PRESENT IN `seen` AND ABSENT FROM HERE IS A REMEMBERED READING WHOSE
    #: MOMENT WAS NEVER ESTABLISHED — an UNKNOWN age, which is not `0.0` and is
    #: not now. Absence is the representation on purpose: there is no `None`
    #: sitting in the map to accidentally do arithmetic against, and
    #: `read_at.get(key)` hands every consumer the three-valued answer directly.
    #:
    #: WALL clock (`time.time()`), never `time.monotonic()`, citing the
    #: distinction `_RetailerState.refused_at` already records
    #: (`pacing.py:159-175`): a monotonic epoch is process- and boot-local, so it
    #: means nothing in a file. This is the same KIND of number as `refused_at` —
    #: a stamp on the EVIDENCE, which exists to be written down, and not a
    #: position on a schedule like `due_at`.
    read_at: dict[str, float] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> State:
        """Restore the memory, tolerating both shapes of the document.

        THE PRE-07 SHAPE IS NOT HYPOTHETICAL. Measured on this host 2026-08-13,
        `state.json` is 13 bare `"retailer:name" -> "in_stock"` strings, and the
        daemon runs this tree through an editable install — so this method is
        what that file meets at the next restart. It loads as availability with an
        UNKNOWN age, which is both the fail-safe direction and simply true of it.

        NO VERSION FIELD, decided rather than defaulted. `pacing.STATE_VERSION`
        exists because `refusals` is a COUNT whose units are a policy decision;
        epoch seconds have no policy constant to be re-pointed against. And the
        price of a version here is paid in ALERTS: a file carrying the wrong one
        is *treated as absent*, which for this document discards 13 remembered
        availabilities, so the next in-stock reading on each reads as a fresh
        restock. Per-entry tolerance costs nothing and keeps the memory.

        THE RESIDUAL IS A DOWNGRADE, AND IT IS PRICED HERE RATHER THAN DESCRIBED.
        An older binary reading the newer document compares a mapping against
        `"in_stock"`, finds them unequal, and re-alerts — it would not read a
        version field either, because the code that would check it is the code
        that does not exist yet. Measured against today's document: 8 of 13
        entries are `in_stock`, 6 of those are controls, and controls never
        alert, so the whole cost is AT MOST TWO duplicate restock pushes (the two
        GameStop `TRANSITION —` watches, which `config/products.yaml:330` records
        as deliberately not controls). It is also not one-way: an old binary
        rewrites the file mixed, and per-entry tolerance reads a mixed document
        without loss in either direction, which a version field could not do.

        `time.time()` is read here and that is not a staleness comparison — it is
        the upper end of a VALIDATION, exactly as `pacing.load:323` reads it.
        Every staleness comparison in this phase takes `now` as a parameter; this
        is not one.
        """
        try:
            doc = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return cls(path, {})
        if not isinstance(doc, dict):
            return cls(path, {})

        now = time.time()
        seen: dict[str, str] = {}
        read_at: dict[str, float] = {}
        # NO `isinstance(key, str)` GUARD, and its absence is deliberate:
        # `json.loads` produces `str` keys by construction, so that branch cannot
        # be taken. `pacing.load` carries one because its keys come from a nested
        # `retailers` mapping it also has to prove is a dict; here it would be a
        # gate that cannot bind.
        for key, entry in doc.items():
            availability = _remembered_availability(entry)
            if availability is None:
                continue
            seen[key] = availability
            # THIS IS WHERE THE COPY OF `pacing.load` DELIBERATELY DIVERGES, and
            # it is written here because here is where a reader will look for it.
            # `pacing.load` `continue`s past a bad entry and drops it WHOLE; a
            # failed stamp check here drops only the AGE and keeps the
            # availability. Dropping the entry would forget a remembered
            # availability, and a forgotten availability re-alerts on the next
            # in-stock reading — so the strict copy would turn one hand-edited
            # number into a push. The fail-safe direction for an age is
            # *unknown*; the fail-safe direction for a memory is *keep it*.
            stamp = _remembered_stamp(entry, now)
            if stamp is not None:
                read_at[key] = stamp
        return cls(path, seen, read_at)

    def save(self) -> None:
        """Write the memory and its dates as one document, one object per entry.

        THIS METHOD NEVER READS THE CLOCK, AND THAT IS THE WHOLE TRAP. `save`
        runs every cycle, so supplying a stamp for an entry that has none would
        refresh the record forever and the age-out would never fire once —
        `pacing.py:196-199` wrote the rule down for `_warned_since` and it is
        inherited verbatim here: *"a bound that cannot bind is worse than no
        bound, because it reads like one in the file."* It is not abstract on
        this host: `walmart:Pokémon GO Plus +` cannot be updated at all while
        `WALMART_STORE_ID` is unset, so a write-time stamp would date a frozen
        reading at the moment of every write, forever.

        An entry with no established moment therefore writes `null`, never `0`.
        `status.py:136-141`'s argument, one direction over: an absent stamp
        published as zero reads as 1 January 1970 — maximally stale rather than
        unknown, which is the same class of lie pointed the other way.

        THE DOCUMENT IS BUILT FROM `seen`, WHICH IS WHAT MAKES `cli.watch_cycle`'s
        ROLLBACK CORRECT. `cli.py:328` pops a key from `state.seen` when a restock
        alert was not delivered; because every entry here comes from `seen`, that
        key's stamp cannot reach disk either. The availability and its age leave
        together, which is what a rollback means. (An orphan stamp can survive in
        `read_at` for the rest of that process and can never be written. Recorded
        rather than guarded: the guard would live in `boty/cli.py`, which this
        plan does not own.)

        WRAPPED, on `Pacer.save`'s precedent (`pacing.py:406-430`), and the reason
        is sharper here than there: `run_once` calls this BEFORE
        `cli.watch_cycle` attempts delivery, so an `OSError` escaping it does not
        merely lose a memory — it takes the cycle down before a real restock
        alert is sent, which is this project's worst outcome. `Exception` rather
        than `OSError`, on WR-05's recorded widening, though only the write is
        known to raise today. `log.exception` carries the type and the traceback,
        so nothing is swallowed silently. The residual, plainly: a failed write
        means the memory does not survive the next restart, costing at most one
        duplicate alert — the direction this project prefers over a missed one.
        """
        try:
            doc = {
                key: {"availability": availability, "read_at": self.read_at.get(key)}
                for key, availability in self.seen.items()
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(doc, indent=2, sort_keys=True))
        except Exception:
            log.exception("could not write the remembered state to %s", self.path)

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
        # THE GUARD ABOVE IS INHERITED, NOT ADDED. The UNKNOWN early return
        # already means the memory is written only when a verdict was RESOLVED,
        # so a refusal — which happened at a wall-clock moment but took no
        # reading — can never reach this line. No `refused` check belongs here:
        # `scripts/mutation_check.py:678` records the rule that two gates on one
        # rule means neither can be shown to bite, and a gate that cannot bite is
        # the defect this phase exists to remove.
        #
        # ONE ACT, TWO FACTS — including the removal case. A resolved reading
        # carrying no stamp is reachable (every hand-built `Result` in the suite
        # is one, and `Result.read_at` defaults to `None`), and leaving the
        # previous stamp in place would attach one reading's moment to a
        # different reading's verdict. That is a smaller lie than the one this
        # phase is fixing and it is the same lie, so the pair is written together
        # or cleared together, never half of each.
        #
        # THIS IS NOT WHERE STALENESS IS DECIDED. Nothing here compares the stamp
        # to anything: 07-03 owns the retailer's current interval, 07-04 the
        # missing rows, 07-05 the rendering.
        if result.read_at is not None:
            self.read_at[key] = result.read_at
        else:
            self.read_at.pop(key, None)
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
                # `cli.watch_cycle`'s existing `pageable` filter pages this arm
                # once per failure episode through `warned`, and the existing
                # `send_health_warning(...) is False` branch already rolls that
                # memory back on a failed delivery. A second sender would need
                # `boty/cli.py`, and an unwired send is "not a retry — it is a
                # drop nothing will ever mention again".
                #
                # WHAT MAKES IT PAGEABLE CHANGED ON 2026-08-12 AND THE OUTCOME
                # DID NOT. It used to reach the filter by being `refused=False`,
                # which was a fact about what it was NOT; since Dan's rule it
                # reaches it by carrying `STORE_PIN_ACTION`, which is a fact
                # about what he can DO. That is now the only route: after that
                # change this is the sole arm here that pages at all.
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
                    # THE ONE ARM THAT NAMES SOMETHING TO DO, and the conditional
                    # is the whole rule rather than a shortcut for it: `action`
                    # defaults to empty on `Health`, so every arm above and every
                    # arm added after this one is silent until somebody can write
                    # down the remedy. `refused` and the breakage arm are not
                    # omissions from a list — they have no remedy to state, which
                    # is exactly why they no longer page.
                    action=STORE_PIN_ACTION if store_gap else "",
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
