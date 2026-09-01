"""Backoff, per-retailer cadence, and the refusal/breakage distinction.

WHAT WENT WRONG, SO THE TESTS BELOW HAVE A SUBJECT
--------------------------------------------------
On 2026-08-04 Amazon and GameStop had been failing continuously for a day.
Neither detector was broken. The monitor polled every 300 s with no backoff, so
a retailer that walled us was asked again five minutes later — 288 times a day.
Two separate defects, and the second is the one that actually cost something:

1. No backoff, so we could not stop being blocked.
2. Every failing control reported as "the detector is probably broken, so real
   restocks would be missed silently". For a refusal that sentence is FALSE —
   the extractor was never reached — and it went out 20 times in 24 hours. An
   alert that cries wolf 20 times is worse than no alert, because this project's
   entire pitch is that its alerts mean something.

   THE SENTENCE QUOTED ABOVE WAS WITHDRAWN IN PHASE 5 (REQ-15, 2026-08-10), and
   so was its replacement's other half — the refusal arm's "we are asking too
   often", which kept firing after a 6-hour backoff had been observed not to
   help. The quotation is HISTORY, kept because it is the subject of the tests
   below; it is not a live claim about what the code says. What the arms say now
   is the measured fact plus `monitor.CAUSE_UNKNOWN`, and the three assertions
   below were rewritten from the prose to that property. The gate on their
   absence is `tests/test_alert_text.py`.

Items 1 and 2 above are the 2026-08-04 defects. Item 3 is the Phase 5 addition,
and it is the subject of the persistence section at the foot of this file:

3. The backoff was in-memory, so a restart reset it to zero. Two things broke at
   once and only the first is obvious: the penalty climbed again from 2x against
   a retailer that had already walled us, and the page-once bookkeeping hung off
   the same counter — so REQ-16's "a refusal that outlasts the cap is pushed
   once" quietly meant "pushed once per PROCESS". Under a systemd unit with
   `Restart=` semantics that is not a rare event. Fixed 2026-08-10 by persisting
   `refusals` and the paging memory (never `due_at`); `boty/pacing.py`'s module
   docstring carries the reversal and the argument for it.
"""

from __future__ import annotations

import json
import random
import time
from itertools import combinations, pairwise
from pathlib import Path

import pytest

from boty.config import Config
from boty.fetch import Blocked, FetchError, is_refusal
from boty.models import Availability, Health, Result, Watch
from boty.monitor import CAUSE_UNKNOWN, State, assess_health, run_once
from boty.pacing import (
    COOLOFF_SECONDS,
    LONGEST_WAIT_SECONDS,
    MAX_BACKOFF_SECONDS,
    MAX_PERSISTED_REFUSALS,
    REFUSALS_BEFORE_COOLOFF,
    STATE_MAX_AGE_SECONDS,
    STATE_VERSION,
    Pacer,
    loop_tick_seconds,
    slot_offset,
)


def _w(retailer: str, name: str = "ctl", *, control: bool = True) -> Watch:
    return Watch(name=name, retailer=retailer, target=f"https://{retailer}.test/p", control=control)


def _ok(w: Watch) -> Result:
    return Result(w, Availability.IN_STOCK, price=1.0, detail="fine")


def _refused(w: Watch) -> Result:
    return Result(w, Availability.UNKNOWN, detail="blocked: challenge page", refused=True)


def _broken(w: Watch) -> Result:
    return Result(w, Availability.UNKNOWN, detail="no structured stock data found")


# --------------------------------------------------------------------------
# A wall is not a broken detector
# --------------------------------------------------------------------------


def test_a_refused_control_is_not_reported_as_a_broken_detector() -> None:
    """The 20-pages-in-24-hours bug, pinned.

    Both readings are UNKNOWN and both are `ok=False` — we do not know the
    stock either way, and the status page must say so. What differs is the
    sentence, and whether a human is needed.
    """
    (health,) = assess_health([_refused(_w("amazon"))])
    assert not health.ok, "a refusal still means we cannot verify the detector"
    assert health.refused, "a refusal must be marked as one"
    assert "refus" in health.reason and CAUSE_UNKNOWN in health.reason, (
        f"a refusal is reported as {health.reason!r} — it must name the measured "
        f"fact (a refusal) and then say the cause is not established. Telling the "
        f"reader the detector is broken is false here, and it is what made this "
        f"alert channel unreadable"
    )


def test_a_genuinely_broken_control_still_says_so_loudly() -> None:
    """The other direction. Backing off must not have muffled the real alarm."""
    (health,) = assess_health([_broken(_w("gamestop"))])
    assert not health.ok and not health.refused
    assert "IN_STOCK" in health.reason, "the measured fact: a control stopped verifying"
    assert CAUSE_UNKNOWN in health.reason
    assert "missed silently" in health.reason, (
        "the consequence follows from what a control IS, so it survives the "
        "withdrawal — unlike the cause, which was never measured"
    )


def test_one_non_refusal_among_refusals_is_treated_as_breakage() -> None:
    """`all`, not `any` — the louder reading is the safe one.

    If a retailer's controls are mostly walled but one failed for a reason that
    is NOT a refusal, something may really be broken, and calling the whole
    retailer 'just rate-limited' would bury it.
    """
    w1, w2 = _w("gamestop", "a"), _w("gamestop", "b")
    (health,) = assess_health([_refused(w1), _broken(w2)])
    assert not health.refused, "a non-refusal among refusals must not be swallowed"
    assert "IN_STOCK" in health.reason and CAUSE_UNKNOWN in health.reason


def test_a_healthy_retailer_is_unaffected() -> None:
    (health,) = assess_health([_ok(_w("walmart"))])
    assert health.ok and not health.refused


# --------------------------------------------------------------------------
# What counts as a refusal
# --------------------------------------------------------------------------


@pytest.mark.parametrize("status", [401, 403, 429])
def test_a_refusal_status_is_a_refusal(status: int) -> None:
    assert is_refusal(FetchError(f"HTTP {status}", status=status))


@pytest.mark.parametrize("status", [500, 502, 503, 404])
def test_a_server_fault_is_not_a_refusal(status: int) -> None:
    """A 500 is the retailer being broken, not the retailer refusing us.

    Backing off on a 5xx would be wrong in an interesting way: it would make
    the monitor quietest exactly when a retailer is having an outage, which is
    when a restock is most likely to be mishandled.
    """
    assert not is_refusal(FetchError(f"HTTP {status}", status=status))


def test_a_transport_failure_is_not_a_refusal() -> None:
    assert not is_refusal(FetchError("Timeout: read timed out"))


def test_a_block_phrase_is_always_a_refusal() -> None:
    assert is_refusal(Blocked("challenge page matched 'are you a human'"))


# --------------------------------------------------------------------------
# Backoff
# --------------------------------------------------------------------------


def test_a_refusal_pushes_the_next_attempt_out_exponentially() -> None:
    p = Pacer(default_interval=300)
    waits = []
    now = 0.0
    for _ in range(4):
        p.record("amazon", refused=True, now=now)
        waits.append(p._for("amazon").due_at - now)
        now = p._for("amazon").due_at
    assert waits == [600, 1200, 2400, 4800], (
        f"backoff is {waits}, expected each refusal to double the wait — a "
        f"linear back-off against an exponential penalty loses"
    )


def test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring() -> None:
    """The cap still governs — up to the point where it stops being the last word.

    THE FIRST ASSERTION WAS WITHDRAWN ON 2026-08-28. It read, in full:

        for _ in range(30):
            p.record("amazon", refused=True, now=now)
        assert p._for("amazon").due_at - now == MAX_BACKOFF_SECONDS

    Two measured facts overruled it.

    1. REQ-22 replaces the six-hour ceiling for a PERSISTENTLY refused retailer.
       Thirty consecutive refusals is precisely the case the requirement exists to
       stop treating as "keep asking every six hours forever", and 30 is
       `REFUSALS_BEFORE_COOLOFF` exactly — so this test drove the loop to the
       boundary and asserted the rule on the wrong side of it. Measured here the
       same day: at 30 refusals the wait read **259200.0** where this line
       expected **21600**.
    2. The 30-day request count against a retailer that never recovers moved from
       **125** (measured 2026-08-27 by `08-01`, against unmodified production
       code) to **37** (measured 2026-08-28, this branch). The flat six-hour tail
       this assertion was pinning is the overwhelming majority of the 125, and it
       is the sentence REQ-22 exists to overrule, stated as arithmetic.

    WHAT SURVIVES, AND WHY THIS IS A REWRITE RATHER THAN A DELETION. Both halves
    survive, and neither is weakened:

    - `MAX_BACKOFF_SECONDS <= 6 * 60 * 60` is untouched, still runs, and is still
      true. **The cap's VALUE did not move.** What this phase replaces is that
      ceiling being applied INDEFINITELY, not its size. Raising the value instead
      would have tripped this very assertion and lost the distinction the phase is
      entirely about — the backoff is still right, it just must not be the last
      word. Holding that distinction in a live assertion rather than in a comment
      is the whole reason this line is kept.
    - The first assertion is re-pointed rather than dropped, at
      `REFUSALS_BEFORE_COOLOFF - 1` — the deepest refusal count at which the cap
      is still the governing rule. So the cap is still gated, one step below where
      it now hands over.

    The name is kept deliberately, because it is still true and because
    `git log -S` reaches this test's history through it.

    THE ANCHOR MOVED ON 2026-09-01 AND THE CLAIM DID NOT — REQ-23. The subtraction
    below read `p._for("amazon").due_at - now`. `record` no longer schedules from
    the cycle's clock; it steps from the retailer's own previous due time, so
    `due_at - now` at a frozen `now` is the SUM of every wait this loop produced
    rather than the last one (measured here: 534600.0 against the 21600 this line
    expected). The wait itself is untouched — `current_interval` is byte-unchanged
    in that phase — so this is a re-pointed assertion and not a withdrawn claim:
    the same number, read from the anchor the schedule now uses.
    """
    p = Pacer(default_interval=300)
    now = 0.0
    for _ in range(REFUSALS_BEFORE_COOLOFF - 2):
        p.record("amazon", refused=True, now=now)
    previous = p._for("amazon").due_at
    p.record("amazon", refused=True, now=now)
    assert p._for("amazon").due_at - previous == MAX_BACKOFF_SECONDS
    assert MAX_BACKOFF_SECONDS <= 6 * 60 * 60, "a cap beyond a few hours is not a monitor"


#: Thirty days, counted in cycles rather than named as a duration.
#:
#: 8640 cycles at the 300 s default cadence is 8640 x 300 = 2 592 000 s, which is
#: 30 days. The arithmetic is stated here rather than performed below.
#:
#: WRITTEN OUT RATHER THAN COMPUTED FROM A `DAYS` CONSTANT, for the same reason
#: `_CADENCE_AFTER_N_REFUSALS` further down this file is written out: a future
#: edit to the window has to change this number BY HAND, and doing that is the
#: moment somebody notices the denominator moved underneath a count that is about
#: to be compared against another count. A window that quietly shrank would
#: present a smaller count as a reduction — a measurement reporting its own
#: shortening as a result — which is the single failure the test below is
#: arranged to be safe from.
_THIRTY_DAYS_OF_CYCLES = 8640


def test_the_thirty_day_request_count_under_the_cooloff_is_a_stated_number() -> None:
    """Criterion 3, BOTH numbers: what the old rule cost, and what this one costs.

    RENAMED FROM `test_the_current_rule_asks_a_never_recovering_retailer_this_many_times_in_thirty_days`
    ON 2026-08-28. The old name asserts the CURRENT rule, and that rule is gone —
    leaving the name would leave a withdrawn claim standing as an assertion's
    title. The old name is written out here so `git log -S` still reaches this
    test's history through the text.

    THE BEFORE-LITERAL WAS WITHDRAWN ON 2026-08-28. It read, in full:

        assert len(offsets) == 125

    **125** was measured on 2026-08-27 by `08-01`, with
    `.venv/bin/python -m pytest tests/test_pacing.py -q`, against `boty/pacing.py`
    at `git rev-parse --short HEAD` = `85a8d9f` — byte-identical to that file's
    last-modified revision `e986d01`, with `git status --porcelain boty/` clean
    before the run. The rule it measured was `MAX_BACKOFF_SECONDS = 6 * 60 * 60`
    applied indefinitely, with no cool-off branch in `current_interval`. Its
    shape, read off the offsets that run printed: 125 = 6 + 1 + 118 — six requests
    while the backoff climbs, one where the cap first binds, and 118 in the flat
    six-hour tail.

    What overruled it: REQ-22's cool-off, which is the change this branch makes.

    WHAT SURVIVES IS THE SIMULATION ITSELF, UNCHANGED, and that is the whole
    reason this is a rewrite of `08-01`'s test rather than a new one beside it.
    The denominator assertion, both independent tallies and the restart assumption
    all stay exactly as they were, and `_THIRTY_DAYS_OF_CYCLES` does not move. The
    same 8640 cycles, the same retailer, the same 300 s standing cadence, the same
    counting idiom — with exactly ONE thing different: the rule. That is what
    makes the two numbers comparable rather than two answers to two questions.

    AFTER THIS REWRITE THE BEFORE-NUMBER IS A DATED RECORD RATHER THAN A
    RE-RUNNABLE ASSERTION, and that is stated plainly rather than papered over.
    Criterion 3 asks for both numbers RECORDED, not both re-runnable. Freezing a
    hand-written reproduction of the old arithmetic to keep 125 re-runnable was
    considered and rejected: it would be a second copy of a number, and the copy
    would be of a RULE THAT NO LONGER EXISTS, so nothing could ever check it
    again. A re-runnable assertion over dead arithmetic looks like evidence and is
    not. This is the same footing every superseded measurement in this repository
    stands on — recorded beside, never edited away.

    THE AFTER-NUMBER IS A MEASUREMENT AND NOT A GATE, exactly as `08-01`'s
    before-number was, and for the same stated reason: its subject is the code as
    it stands rather than a defect, so it cannot be made to fail. It was
    TRANSCRIBED from the failure message this very test produced the moment the
    cool-off branch landed and this assertion still read 125. What carries the
    weight instead is the denominator assertion, the two independent tallies, and
    that transcription.

    THE RESTART ASSUMPTION, STATED RATHER THAN LEFT TO BE INFERRED, and it applies
    to both numbers. The simulation models ZERO restarts across the 30 days, and
    the count holds only under that assumption. A restart costs exactly ONE extra
    request, because `due_at` is deliberately never persisted —
    `boty/pacing.py`'s module docstring, concession (b): *"A restart still tries
    once, immediately, at full rate, so the condition is re-tested at once. What
    is inherited is only the DEPTH the penalty resumes at IF that one request is
    refused again"*. So the honest form of the claim is "N requests over 30 days,
    plus one per restart", and a reader who needs the number for a flapping
    service under a `Restart=` unit adds the restarts themselves.
    """
    p = Pacer(default_interval=300)
    now = 0.0
    offsets: list[float] = []
    for _ in range(_THIRTY_DAYS_OF_CYCLES):
        if p.due("walmart", now):
            offsets.append(now)
            p.record("walmart", refused=True, now=now)
        now += 300.0

    assert len(offsets) == 37, (
        f"the cool-off rule asked a never-recovering retailer {len(offsets)} times "
        f"over a simulated thirty days at the 300-second standing cadence; the "
        f"recorded after-number for criterion 3 is the literal in this assertion"
    )

    # THE WORD *STRICTLY* IN CRITERION 3, and the one thing the before-half has to
    # stay a number for. 125 is the withdrawn literal quoted in the docstring
    # above, written out here so the comparison is a comparison rather than a
    # claim about one number.
    assert len(offsets) < 125, (
        f"the cool-off made {len(offsets)} requests where the six-hour ceiling "
        f"applied indefinitely made 125 — criterion 3 asks for strictly fewer, "
        f"and a count that did not fall is a rule that did not change"
    )

    assert now == 2592000.0, (
        f"the simulated clock finished at {now} s, not the 2 592 000 s that are "
        f"thirty days — so the count above is a count over some other window. A "
        f"run that exited early presents a smaller number as a shorter month, "
        f"which is a reduction achieved by not asking rather than by waiting"
    )

    assert p._for("walmart").refusals == len(offsets), (
        f"the schedule recorded {p._for('walmart').refusals} refusals but the "
        f"simulation counted {len(offsets)} requests; `record` increments once "
        f"per refusal, so a divergence means a request was made and not counted, "
        f"or counted and not made"
    )

    assert all(a < b for a, b in pairwise(offsets)) and all(
        0.0 <= t < 2592000.0 for t in offsets
    ), (
        f"the request offsets are not strictly increasing inside [0, 2 592 000); "
        f"first {offsets[:3]}, last {offsets[-3:]} — a count is not a measurement "
        f"if the things counted could fall outside the window they are attributed to"
    )


def test_a_refusal_never_shortens_the_wait_however_long_the_standing_interval() -> None:
    """The cap is a FLOOR on politeness, not a ceiling on it.

    `current_interval` used to be `min(interval * FACTOR ** refusals, CAP)`
    outright. Above the cap that `min` returns a number SMALLER than the
    standing interval, and `record` schedules `due_at = now + wait` from the
    same call — so a refusal made the monitor ask a refusing retailer MORE
    often, and the log line printed the 4x increase in request rate as a
    backoff. Measured on the pre-fix tree with `interval_seconds: 86400`:

        interval at 0 refusals: 86400.0
        after ONE refusal -> due_at: 21600.0, current_interval: 21600
        log: "x refused us (1 in a row) — next attempt in ~360 min, not 1440"

    `config._interval` enforces a floor (`MIN_INTERVAL_SECONDS`) and no upper
    bound, so that is a config `Config.load` accepts in silence. Not reachable
    on `config/products.yaml` today — the largest standing interval there is
    Amazon's 1800 s — which is exactly why it needs a test rather than a
    comment.

    THE CAP IS NOT WEAKENED. Below it, the backoff still tops out at
    `MAX_BACKOFF_SECONDS`, which the test above pins; the clamp only refuses to
    move a wait DOWNWARDS, and it can only fire where the operator already chose
    a cadence longer than the cap.
    """
    standing = MAX_BACKOFF_SECONDS * 4
    p = Pacer(default_interval=standing)
    assert p.current_interval("x") == standing

    now = 0.0
    p.record("x", refused=True, now=now)
    assert p._for("x").due_at - now >= standing, (
        "one refusal moved the next attempt CLOSER than the standing interval — "
        "the politeness constraint inverted, on a config the loader accepts"
    )
    # Through the accessor as well as through the schedule, because `record`
    # computes its wait through `current_interval` and the two must not be
    # gated separately — the one-expression claim this module makes twice.
    for refusals in range(1, 12):
        assert p.current_interval("x") >= standing
        p.record("x", refused=True, now=now)
        assert p._for("x").refusals == refusals + 1


def test_one_good_read_clears_the_backoff_completely() -> None:
    """Not a decay — a reset. The retailer is answering; there is nothing left
    to back off from, and creeping back over hours would keep a working
    retailer under-polled for no reason.

    THE ANCHOR MOVED ON 2026-09-01 AND THE RESET DID NOT — REQ-23. The second
    assertion read `due_at == 300`; at a frozen `now` the grid advance had it at
    18900.0, which is the five refusals' waits accumulated and then one standing
    interval added. Re-pointed at the increment, the claim is the one this test
    was always making: after a good read the next attempt is ONE standing interval
    on, not a fraction of the backoff still being paid off.
    """
    p = Pacer(default_interval=300)
    for _ in range(5):
        p.record("amazon", refused=True, now=0.0)
    previous = p._for("amazon").due_at
    p.record("amazon", refused=False, now=0.0)
    assert p._for("amazon").refusals == 0
    assert p._for("amazon").due_at - previous == 300


def test_a_parse_failure_does_not_trigger_backoff() -> None:
    """The distinction that makes the whole thing work.

    A parse failure means the retailer SERVED us and our extractor could not
    read it. Backing off would delay the one alert that matters while doing
    nothing about the cause.
    """
    p = Pacer(default_interval=300)
    p.record("gamestop", refused=False, now=0.0)
    assert p._for("gamestop").refusals == 0
    assert p._for("gamestop").due_at == 300


# --------------------------------------------------------------------------
# Per-retailer cadence
# --------------------------------------------------------------------------


def test_a_retailer_at_the_default_cadence_is_due_every_cycle() -> None:
    """The regression that would make this change quietly halve coverage.

    THE UNIT WENT WRONG ON 2026-09-01 AND THE FEAR DID NOT — REQ-23, and this is
    the reversal `09-DECISIONS.md` § *Test collision A* fixed the shape of before
    any code moved. The withdrawn assertion, in full:

        for cycle in range(20):
            assert p.due("walmart", now), f"walmart not due at cycle {cycle} (t={now})"
            p.record("walmart", refused=False, now=now)
            now += 300 * 0.86  # a short-jitter cycle, the adversarial case

    and the docstring called what it guards *"the regression that would make this
    change quietly halve coverage"*.

    WHAT OVERRULED IT. `cli.watch_loop` no longer sleeps the standing interval; it
    sleeps a tick a sixth of it, so a retailer at the default cadence is due once
    per CADENCE and not once per WAKE. Measured against the mechanism the same
    day: walmart was not due at cycle 4 (t=1032.0), because its grid points are
    300 s apart while these cycles are 258 s apart. BEING DUE EVERY WAKE IS NOW
    THE DEFECT the withdrawn form would have asserted into place — at a 50 s tick
    it would mean asking a 300 s retailer six times per cadence.

    WHAT SURVIVES IS THE FEAR, AND IT IS THE HALF THAT WAS EVER LOAD-BEARING: a
    default-cadence retailer must not be quietly asked less often than it is
    configured for. That is now asserted as a COUNT over a fixed window rather
    than as a predicate per cycle — the same guarantee in the unit the loop
    actually runs in. `due`'s grace still exists and is still half the loop's
    sleep; only which sleep that is has changed.

    THE NAME IS KEPT so `git log -S` still reaches this test's history.
    """
    tick = loop_tick_seconds(300, ("bestbuy", "nintendo", "target", "walmart"))
    p = Pacer(
        default_interval=300,
        roster=("bestbuy", "nintendo", "target", "walmart"),
        tick=tick,
    )
    now = 0.0
    asked = 0
    # A SHORT-JITTER WAKE EVERY TIME — the adversarial case the withdrawn form
    # named, kept verbatim in its new unit: every sleep comes up 14% short, which
    # is the direction that could make a retailer LOOK never-due if the grace
    # were sized against the wrong sleep.
    while now < float(_ONE_DAY_OF_SECONDS):
        if p.due("walmart", now):
            # Counted at the grid point being served rather than at the wake that
            # serves it, for the reason the tracer states at length: `due`'s grace
            # can dispatch the first grid point of day two inside the last half
            # tick of day one, so a count by wake is 288 or 289 depending on where
            # the final wake lands and a count by grid point is exactly 288.
            if p._for("walmart").due_at < float(_ONE_DAY_OF_SECONDS):
                asked += 1
            p.record("walmart", refused=False, now=now)
        now += tick * 0.86

    expected = _ONE_DAY_OF_SECONDS // 300
    assert asked == expected, (
        f"walmart was asked {asked} times over a day of short-jitter wakes, "
        f"against the {expected} a 300 s cadence implies. Fewer is the regression "
        f"this test has always guarded — a retailer quietly dropped from cycles it "
        f"was keeping to — and more would be the new one: a tick shorter than the "
        f"cadence asking a retailer several times per cadence"
    )


def test_an_overridden_retailer_is_asked_less_often() -> None:
    p = Pacer(default_interval=300, overrides={"amazon": 1800})
    now = 0.0
    checked = 0
    for _ in range(24):  # two hours of 5-minute cycles
        if p.due("amazon", now):
            checked += 1
            p.record("amazon", refused=False, now=now)
        now += 300
    assert 4 <= checked <= 5, (
        f"amazon checked {checked} times in 2h at a 30-minute cadence; expected ~4"
    )


def test_an_override_does_not_affect_other_retailers() -> None:
    p = Pacer(default_interval=300, overrides={"amazon": 1800})
    now = 0.0
    for _ in range(10):
        assert p.due("walmart", now)
        p.record("walmart", refused=False, now=now)
        now += 300


# --------------------------------------------------------------------------
# A skipped retailer must not become a fake reading
# --------------------------------------------------------------------------


def test_a_paced_out_retailer_produces_no_result_rather_than_a_fake_unknown(
    tmp_path: Path,
) -> None:
    """The failure this change could have introduced, and it would have been bad.

    A synthetic UNKNOWN for a check we chose not to make would flow into
    `assess_health`, report the detector as broken, and page somebody about a
    question nobody asked — reintroducing the exact bug being fixed, from the
    other end.
    """
    watches = [_w("walmart"), _w("amazon")]
    p = Pacer(default_interval=300, overrides={"amazon": 1800})
    state = State(tmp_path / "state.json", {})

    results, health, _ = run_once(watches, _ok, state, pacer=p, now=0.0)
    assert {r.watch.retailer for r in results} == {"walmart", "amazon"}, "first cycle checks both"

    results, health, _ = run_once(watches, _ok, state, pacer=p, now=300.0)
    assert {r.watch.retailer for r in results} == {"walmart"}, "amazon is not due yet"
    assert {h.retailer for h in health} == {"walmart"}, (
        "a skipped retailer appeared in the health report — it was never "
        "checked, so there is nothing to report, and inventing a verdict is "
        "how a green dashboard ends up covering a question nobody asked"
    )


def test_a_skipped_retailer_can_say_why(tmp_path: Path) -> None:
    p = Pacer(default_interval=300, overrides={"amazon": 1800})
    p.record("amazon", refused=False, now=0.0)
    reason = p.skipped_reason("amazon", 300.0)
    assert "paced at 30 min" in reason and "min" in reason

    for _ in range(3):
        p.record("gamestop", refused=True, now=0.0)
    assert "backing off after 3 refusal(s)" in p.skipped_reason("gamestop", 0.0)


def test_a_retailer_in_cooloff_says_so_rather_than_reporting_a_minute_count() -> None:
    """A true wait of "~4320 min" is a number no reader of the dashboard can act on.

    This is the status page's sentence about a retailer nobody is asking, and the
    module's own `skipped_reason` docstring says why it has to be right: a skipped
    retailer published as if it had been checked and found fine is this project's
    defect one level up. "Backing off, next attempt in ~4320 min" is not that
    failure, but it is its quieter cousin — a true statement in units that hide
    what it means. Four thousand minutes is three days, and nobody reads it as
    three days.

    THE SECOND ASSERTION IS WHY THIS IS A NEW BRANCH AND NOT A REPLACEMENT. Below
    the threshold the prose must be byte-unchanged, so the arm is proved to have
    been ADDED rather than to have swallowed the case it sits beside.
    """
    p = Pacer(default_interval=300)
    for _ in range(REFUSALS_BEFORE_COOLOFF):
        p.record("cooling", refused=True, now=0.0)
    reason = p.skipped_reason("cooling", 0.0)

    assert "cooling off" in reason, (
        f"a retailer being left alone for days said {reason!r} — the page has to "
        f"name the state, not just report a bigger number in the same units"
    )
    assert f"{REFUSALS_BEFORE_COOLOFF} refusal(s)" in reason, (
        f"the count is what makes the state legible as evidence rather than as a "
        f"policy nobody can audit; got {reason!r}"
    )
    assert "days" in reason and "min" not in reason, (
        f"the remaining wait is still in minutes: {reason!r}"
    )

    # UNCHANGED BELOW THE THRESHOLD. The existing arm still owns its case.
    p_shallow = Pacer(default_interval=300)
    for _ in range(3):
        p_shallow.record("shallow", refused=True, now=0.0)
    shallow = p_shallow.skipped_reason("shallow", 0.0)
    assert "backing off after 3 refusal(s)" in shallow and "min" in shallow, (
        f"the cool-off arm swallowed the backing-off case: {shallow!r}"
    )


def test_run_once_without_a_pacer_is_unchanged(tmp_path: Path) -> None:
    """Every existing caller passes no pacer and must behave exactly as before."""
    watches = [_w("walmart"), _w("amazon")]
    state = State(tmp_path / "state.json", {})
    results, health, _ = run_once(watches, _ok, state)
    assert len(results) == 2 and len(health) == 2


# --------------------------------------------------------------------------
# REQ-21: the retailer's CURRENT interval, as a number
# --------------------------------------------------------------------------
#
# Criterion 3 says a reading is stale when it is older than "its retailer's
# current interval ... derived from the retailer's own pacing rather than a
# fixed clock". That number existed nowhere before 2026-08-13: `interval` is the
# STANDING config value and is unchanged by any backoff, `skipped_reason`
# returns prose, and the backed-off figure lived for four lines inside `record`
# before being folded into `due_at` — which is a position on a synthetic clock
# that restarts at 0.0 every process and is deliberately never persisted.
#
# So there are two claims below and they are different claims. The first is that
# the accessor answers with the cadence actually in force. The second is that
# EXPOSING it did not move it.

#: The cadence a retailer is on after N consecutive refusals, indexed by N, at
#: each of the two intervals this project configures today (the 300 s default
#: and the 1800 s Amazon override).
#:
#: LITERALS, AND THAT IS THE POINT OF THE LIST. Computing these through
#: `current_interval` — or through `BACKOFF_FACTOR` and `MAX_BACKOFF_SECONDS` —
#: would make every assertion below a re-derivation of the code it is checking,
#: which is a test that cannot fail. Written out, a future edit to the backoff
#: has to change this list BY HAND, and doing that is the moment somebody
#: notices they are changing when a retailer is asked.
#:
#: The cap binds at 7 refusals for the 300 s interval (300 x 2**7 = 38 400 s,
#: clamped to 21 600) and at 4 for the 1800 s one (28 800, clamped). Both
#: sequences run to 8 so the flat tail past the cap is asserted rather than
#: assumed. A third interval is one more row.
_CADENCE_AFTER_N_REFUSALS = [
    (300.0, [300.0, 600.0, 1200.0, 2400.0, 4800.0, 9600.0, 19200.0, 21600.0, 21600.0]),
    (1800.0, [1800.0, 3600.0, 7200.0, 14400.0, 21600.0, 21600.0, 21600.0, 21600.0, 21600.0]),
]


def test_an_unrefused_retailer_is_on_its_standing_interval() -> None:
    """The default and the override, to the float.

    Equality rather than `pytest.approx`: this number is published and then
    subtracted against, and "close to 300" is not a cadence anybody configured.
    """
    p = Pacer(default_interval=300, overrides={"amazon": 1800})

    assert p.current_interval("walmart") == 300.0
    assert p.current_interval("amazon") == 1800.0


def test_a_retailer_never_seen_before_answers_with_its_configured_interval() -> None:
    """No exception, and no requirement that a cycle has run first.

    `boty check` calls this on a fresh clone with no `pacer-state.json` and no
    recorded outcome for anybody, which is exactly this case.
    """
    p = Pacer(default_interval=300, overrides={"gamestop": 900})

    assert p.current_interval("nobody-has-asked-this-one") == 300.0
    assert p.current_interval("gamestop") == 900.0


def test_asking_what_the_cadence_is_does_not_create_the_record_that_answers() -> None:
    """`boty check`'s pacer is load-only, and this is the method it calls most.

    `current_interval` used to reach the state through `_for`, which INSERTS a
    `_RetailerState` for any retailer it has not seen. `_current_intervals`
    calls it once per configured retailer, so a `boty check` run materialised an
    in-memory row for every retailer in the config — including ones
    `pacer-state.json` says nothing about.

    THE CONSEQUENCE TODAY IS NOTHING, AND THIS TEST SAYS SO RATHER THAN
    INFLATING IT. `save` filters `if st.refusals`, the check-path pacer never
    calls `save`, and `test_both_surfaces_publish_one_cadence_from_one_document`
    proves the bytes on disk are unchanged. What this pins is that the ONLY
    thing keeping a read accessor from writing that document is a filter two
    methods away and a caller that happens not to save — the day either moves,
    `boty check` starts writing rows for retailers it never asked about, and
    `boty check` is routinely run while the daemon owns that file.

    So: assert the accessor's read-only-ness where it lives, not where its
    consequences currently happen to be absent.
    """
    p = Pacer(default_interval=300, overrides={"gamestop": 900})

    assert p.current_interval("gamestop") == 900.0
    assert p.current_interval("amazon") == 300.0
    assert p.current_interval("walmart") == 300.0

    assert p._state == {}, (
        "reading the cadence created state for "
        f"{sorted(p._state)} — a read accessor that writes"
    )


@pytest.mark.parametrize("interval,expected", _CADENCE_AFTER_N_REFUSALS)
def test_the_current_interval_widens_with_the_backoff(
    interval: float, expected: list[float]
) -> None:
    """What is published is the cadence in force, not the one in the config.

    Measured on this host 2026-08-13: target and walmart sat at 7 refusals on
    the 300 s default, so their real cadence was the 6-hour cap — 72 times the
    standing value. A surface comparing a reading against 300 s there would
    call every reading stale within five minutes of taking it.
    """
    p = Pacer(default_interval=interval)

    for refusals, seconds in enumerate(expected):
        assert p.current_interval("amazon") == seconds, (
            f"at {refusals} consecutive refusal(s) the cadence read "
            f"{p.current_interval('amazon')}, expected {seconds}"
        )
        p.record("amazon", refused=True, now=0.0)


def test_a_retailer_that_answers_is_back_on_its_standing_interval_at_once() -> None:
    """A reset, not a decay — the same claim `record` already makes for `due_at`.

    Asserted at the CAP rather than one refusal in, because the interesting
    direction is a retailer coming back from a 6-hour wait.
    """
    p = Pacer(default_interval=300, overrides={"amazon": 1800})
    for _ in range(7):
        p.record("amazon", refused=True, now=0.0)
    assert p.current_interval("amazon") == MAX_BACKOFF_SECONDS

    p.record("amazon", refused=False, now=0.0)

    assert p.current_interval("amazon") == 1800.0


@pytest.mark.parametrize("interval,expected", _CADENCE_AFTER_N_REFUSALS)
def test_the_backoff_schedule_is_exactly_the_schedule_it_was(
    interval: float, expected: list[float]
) -> None:
    """WHEN ANYTHING IS FETCHED DID NOT CHANGE, and this is the gate on that.

    REQ-21 exposes a number that `record` was computing and throwing away. It
    does not alter the schedule that number describes — the backoff, its
    multiplier, the cap and the politeness cadence are correct and are not this
    phase's subject.

    The expected seconds are the literals in `_CADENCE_AFTER_N_REFUSALS`, never
    `current_interval`'s return value. A test that asked the accessor what the
    schedule should be would pass for an accessor and a schedule that had drifted
    apart together, which is the one failure this section exists to detect.

    THE ANCHOR MOVED ON 2026-09-01 AND THE SCHEDULE DID NOT — REQ-23, and this
    test is the one that has to say so most carefully, because its own name is the
    claim. Both assertions read `== now + seconds` against a frozen `now`. REQ-23
    makes `record` step from the retailer's own previous due time rather than from
    the cycle's clock, so at a frozen clock the second refusal landed at 1800.0
    where this line expected 1200.0 — not a longer wait, but the same 1200 s wait
    measured from a different place. The waits themselves are the literals in
    `_CADENCE_AFTER_N_REFUSALS` and they are unchanged, which is exactly what the
    re-pointed form below still asserts: each refusal's INCREMENT is the schedule
    it always was. Nothing about the backoff's depth, its multiplier or its cap is
    weakened here; only where the tape measure is held.
    """
    p = Pacer(default_interval=interval)
    now = 0.0

    for refusals, seconds in enumerate(expected[1:], start=1):
        previous = p._for("amazon").due_at
        p.record("amazon", refused=True, now=now)
        assert p._for("amazon").due_at == previous + seconds, (
            f"refusal {refusals} scheduled the next attempt "
            f"{p._for('amazon').due_at - previous}s past the previous one, not "
            f"{seconds}s — the fetch schedule moved, and nothing in REQ-21 or "
            f"REQ-23 is allowed to move it"
        )

    previous = p._for("amazon").due_at
    p.record("amazon", refused=False, now=now)
    assert p._for("amazon").due_at == previous + interval, (
        "a retailer that answered is asked again at its standing interval"
    )


# --------------------------------------------------------------------------
# REQ-22: past 30 refusals, stop knocking for three days
# --------------------------------------------------------------------------
#
# The six-hour ceiling was the LAST WORD until 2026-08-28: a retailer that had
# refused us a hundred times running was still asked four times a day, forever.
# `08-01` measured what that costs against a retailer that never recovers, and
# the number is quoted in the 30-day test further down this file.
#
# What replaces it is not "ask less often". It is a different KIND of wait: past
# `REFUSALS_BEFORE_COOLOFF` the exponential stops being evaluated at all and a
# flat, days-scale literal takes over. That is why the assertions below are
# exact-equality against hand-written seconds rather than `pytest.approx` — see
# `_CADENCE_ACROSS_THE_COOLOFF_THRESHOLD`'s own note.

#: The cadence a retailer is on at N-1, N and N+1 refusals, where N is
#: `REFUSALS_BEFORE_COOLOFF`, at each of the two standing intervals this project
#: configures today. `(standing_interval, refusals, expected_seconds)`.
#:
#: A SIBLING OF `_CADENCE_AFTER_N_REFUSALS` AND NOT AN EXTENSION OF IT. That list
#: is indexed by N from 0, so running it out to 31 would bury this boundary in
#: twenty-two flat entries — the one step this table exists to show, hidden
#: inside the tail it is stepping out of.
#:
#: LITERALS, AND THAT IS THE POINT OF THE TABLE, on `_CADENCE_AFTER_N_REFUSALS`'
#: own argument restated in this table's terms. Computing these through
#: `current_interval`, `BACKOFF_FACTOR`, `MAX_BACKOFF_SECONDS` or
#: `COOLOFF_SECONDS` would make every assertion below a re-derivation of the code
#: it is checking, which is a test that cannot fail. Written out, a future edit to
#: the threshold or the duration has to change these numbers BY HAND, and doing
#: that is the moment somebody notices they have changed how long a retailer is
#: left alone.
#:
#: THE ROWS ARE N-1, N AND N+1 ON PURPOSE, so the threshold is asserted AT the
#: step rather than near it. A table that only checked 25 and 40 would pass for a
#: cool-off that began anywhere in between, which is every value except the one
#: that was chosen.
#:
#: 21600.0 is the six-hour cap, which BOTH standing intervals have long since
#: reached by 29 refusals (the cap binds at 7 for the 300 s default and at 4 for
#: the 1800 s override). 259200.0 is three days.
_CADENCE_ACROSS_THE_COOLOFF_THRESHOLD = [
    (300.0, 29, 21600.0),
    (300.0, 30, 259200.0),
    (300.0, 31, 259200.0),
    (1800.0, 29, 21600.0),
    (1800.0, 30, 259200.0),
    (1800.0, 31, 259200.0),
]


@pytest.mark.parametrize(
    "interval,refusals,expected", _CADENCE_ACROSS_THE_COOLOFF_THRESHOLD
)
def test_the_cadence_across_the_cooloff_threshold_is_the_literal_it_is(
    interval: float, refusals: int, expected: float
) -> None:
    """Criterion 1: the threshold binds at the step, and the wait past it is exact.

    `==` RATHER THAN `pytest.approx`, and that is a claim about the code rather
    than a stylistic preference. Past the threshold `current_interval` never
    evaluates `st.interval * BACKOFF_FACTOR ** st.refusals` at all — a
    conditional expression does not evaluate the branch it does not take — so no
    float rounding contract is entered and there is nothing for a tolerance to
    absorb. An approximate assertion here would be hiding the very property being
    asserted.
    """
    p = Pacer(default_interval=interval)
    for _ in range(refusals):
        p.record("x", refused=True, now=0.0)

    assert p.current_interval("x") == expected, (
        f"at {refusals} consecutive refusal(s) on a {interval} s standing "
        f"interval the cadence read {p.current_interval('x')}, expected "
        f"{expected}"
    )


#: Cycles simulated after the threshold is crossed, at the 300 s standing cadence.
#:
#: STATED RATHER THAN COMPUTED FROM `COOLOFF_SECONDS`, for the same reason the
#: table above is written out: a number derived from the constant under test
#: cannot contradict it. One cool-off window is 259 200 / 300 = 864 cycles, so
#: 1000 is comfortably longer than one window and comfortably shorter than two —
#: which is what makes "exactly one" a real bound in both directions rather than
#: a floor.
_CYCLES_ACROSS_A_COOLOFF_WINDOW = 1000


def test_a_retailer_in_cooloff_is_probed_exactly_once_when_it_expires() -> None:
    """Criterion 2: left alone, then probed — not dropped, and not probed twice.

    WHY THIS IS A SIMULATION AND NOT AN INFERENCE. An interval of 259 200 s is
    consistent with one probe over the window and with none at all; the number
    alone cannot tell a cool-off from a retailer that has silently fallen off the
    schedule, and "silently fallen off the schedule" is the failure this whole
    project exists one level up to prevent. Only driving `due` on every cycle
    distinguishes them.

    The idiom is this repository's own — a plain float `now`, `if p.due(...)`,
    `count += 1`, `p.record(...)`, `now += 300`. No clock library, no fixture, no
    monkeypatched time: the class takes `now` as an argument precisely so a month
    of cycles costs no seconds.

    THE COOL-OFF IS SCOPED TO A RUNNING PROCESS, and that is recorded here rather
    than discovered later. `due_at` is deliberately never persisted, so a restart
    mid-cool-off re-probes immediately at full rate. The price is exactly one
    request per restart.
    """
    p = Pacer(default_interval=300)
    now = 0.0

    # RAMP. Drive the schedule to the threshold the way the daemon would — one
    # refusal per cycle it is actually due — rather than by calling `record` in a
    # tight loop, so the cycle count below is a real position on a real schedule.
    cycles_to_the_threshold = 0
    while p._for("walmart").refusals < REFUSALS_BEFORE_COOLOFF:
        if p.due("walmart", now):
            p.record("walmart", refused=True, now=now)
        now += 300.0
        cycles_to_the_threshold += 1
        assert cycles_to_the_threshold < 100_000, (
            "the ramp never reached the threshold — either the backoff stopped "
            "letting a refused retailer become due at all, or the threshold is "
            "unreachable from a running process"
        )

    at_the_threshold = now

    probes = 0
    for _ in range(_CYCLES_ACROSS_A_COOLOFF_WINDOW):
        if p.due("walmart", now):
            probes += 1
            p.record("walmart", refused=True, now=now)
        now += 300.0

    assert probes == 1, (
        f"a retailer at {REFUSALS_BEFORE_COOLOFF} refusals was asked {probes} "
        f"times over {_CYCLES_ACROSS_A_COOLOFF_WINDOW} cycles "
        f"({_CYCLES_ACROSS_A_COOLOFF_WINDOW * 300} s) after crossing the "
        f"threshold at t={at_the_threshold} — a cool-off is exactly one probe "
        f"per window: more than one is still knocking, and none at all is a "
        f"dropped retailer with a row on the dashboard"
    )


def test_a_retailer_that_answers_during_its_probe_is_back_on_its_standing_interval_at_once() -> None:
    """Criterion 4: a cool-off is a wait, never a never-ask-again.

    Asserted at COOL-OFF depth rather than at the cap, for the same stated reason
    `test_a_retailer_that_answers_is_back_on_its_standing_interval_at_once` is
    asserted at the cap rather than one refusal in: the interesting direction is a
    retailer coming back from three days, not from ten minutes.

    THREE ASSERTIONS AFTER THE GOOD READ, NOT ONE. The field, the accessor and the
    schedule. A reset that cleared the count without reaching the schedule would
    pass on `refusals == 0` alone while the retailer sat unasked for the rest of
    its three days — the count saying "recovered" and the schedule saying
    "cooling off", which is the two-surfaces-disagreeing defect this module keeps
    to one expression to prevent.

    THE THIRD ONE'S ANCHOR MOVED ON 2026-09-01 AND ITS CLAIM DID NOT — REQ-23. It
    read `due_at == 1800.0`; at a frozen `now` the grid advance had it at
    847800.0, which is thirty refusals' waits accumulated and then one standing
    interval added. The distinction this assertion exists to hold is that the
    retailer is asked again ONE STANDING INTERVAL after its last scheduled
    attempt rather than after the rest of its cool-off, and the re-pointed form
    says exactly that. The cool-off's DURATION is asserted two lines above,
    against the hand-written 259200.0, and is untouched.
    """
    p = Pacer(default_interval=300, overrides={"amazon": 1800})
    for _ in range(REFUSALS_BEFORE_COOLOFF):
        p.record("amazon", refused=True, now=0.0)
    assert p.current_interval("amazon") == 259200.0, (
        "the setup never reached cool-off depth, so what follows would be a "
        "recovery from the cap and not from a cool-off"
    )

    previous = p._for("amazon").due_at
    p.record("amazon", refused=False, now=0.0)

    assert p._for("amazon").refusals == 0
    assert p.current_interval("amazon") == 1800.0
    assert p._for("amazon").due_at - previous == 1800.0


# --------------------------------------------------------------------------
# The status page must not lose a paced retailer
# --------------------------------------------------------------------------


def test_a_paced_retailer_is_published_as_unchecked_not_omitted(tmp_path: Path) -> None:
    """Six retailers configured must read as six, not four with a silent gap.

    Pacing introduced a third state and neither of the first two describes it:
    not healthy (nothing verified), not unhealthy (nothing failed) — not asked.
    Dropping the row entirely would make a reader counting retailers conclude
    one had been removed.
    """
    from boty import status

    out = tmp_path / "status.json"
    status.write(
        out,
        [_ok(_w("walmart"))],
        [Health("walmart", ok=True)],
        duration_seconds=1.0,
        paced={"amazon": "paced at 30 min — next attempt in ~25 min"},
    )
    import json

    payload = json.loads(out.read_text())
    by = {r["retailer"]: r for r in payload["retailers"]}
    assert set(by) == {"walmart", "amazon"}, "the paced retailer vanished from the status page"

    assert by["amazon"]["checked"] is False
    assert by["amazon"]["ok"] is False, (
        "an unchecked retailer must not read as ok — nothing was verified, and "
        "claiming otherwise is the green-dashboard failure one level up"
    )
    assert "paced at 30 min" in by["amazon"]["reason"]
    assert by["walmart"]["checked"] is True

    assert payload["healthy"] is True, (
        "a paced retailer flipped `healthy` false. It has not failed anything; "
        "letting it redden the dashboard permanently makes the flag useless — "
        "the same 'a gate that fires on the honest outcome' defect the roadmap names"
    )


# --------------------------------------------------------------------------
# The backoff has to outlive the process (item 3 in this module's docstring)
#
# Every test below builds a SECOND, brand-new Pacer over the same file rather
# than calling `load()` on the one that wrote it. A restart is a new object in
# a new process, and a test that reloaded into the same instance would pass for
# a `load` that did nothing at all.
# --------------------------------------------------------------------------


def _pacer(path: Path | None = None, interval: float = 300) -> Pacer:
    return Pacer(default_interval=interval, state_path=path)


def test_a_pacer_with_no_state_path_persists_nothing(tmp_path: Path) -> None:
    """`state_path=None` is every pre-existing construction site, unchanged.

    Nine of them live in this file alone and not one names a path. The default
    has to mean "do not persist", or adding persistence would change the
    behaviour of every caller that never asked for it.
    """
    p = _pacer()
    p.record("amazon", refused=True, now=0.0)

    assert p.load() == set(), "a pacer with nowhere to read from restores nothing"
    p.save({"amazon"})

    assert list(tmp_path.iterdir()) == [], "a pacer with no state_path wrote a file"


def test_a_refusal_count_survives_into_a_brand_new_pacer(tmp_path: Path) -> None:
    """The whole point: five refusals, a restart, still five.

    Without this the backoff climbs again from 2x after every restart, so a
    retailer that walled us gets asked at full rate and then paced shallowly —
    which is the politeness regression, and one no verdict-level test can see.
    """
    path = tmp_path / "pacer-state.json"
    first = _pacer(path)
    for _ in range(5):
        first.record("amazon", refused=True, now=0.0)
    first.save(set())

    second = _pacer(path)
    second.load()

    assert second._for("amazon").refusals == 5, (
        "the refusal count did not survive the process — the next refusal would "
        "multiply from one instead of from five"
    )


def test_the_restored_pacer_starts_its_schedule_from_zero(tmp_path: Path) -> None:
    """`due_at` is neither written nor read, and that is deliberate.

    `cli.watch_loop` drives this class with a synthetic clock starting at 0.0 in
    every process, so a persisted `due_at` is a number with no referent: it
    either fires immediately or blocks the retailer for the age of the previous
    process.

    THAT SENTENCE IS UNTOUCHED BY REQ-23 AND IS IN FACT WHY THE REPAIR BELOW IS
    AVAILABLE AT ALL. Nothing in that phase persists a next-attempt time; the
    starting position is DERIVED from the retailer's name and the configured
    roster, in this process, from config. The docstring's argument gets stronger:
    "a number with no referent" is the case for deriving the starting position,
    not merely for leaving it at zero.

    TWO SENTENCES ARE WITHDRAWN, 2026-09-01, quoted in full before they go. From
    this docstring:

        Leaving it at 0.0 also KEEPS the withdrawn docstring's concession — a
        restart still tries once at full rate.

    and from the assertion below:

        assert second.due("amazon", 0.0), "a restart must still try once, immediately"

    WHAT OVERRULED THEM: `09-DECISIONS.md` § *Collision 2*. A restart now resets
    the schedule to the retailer's own OFFSET rather than to 0.0, so each retailer
    is re-tested once within one standing interval instead of immediately — at
    most 300 s for the default group, at most 1800 s for amazon. Nothing is
    re-tested less often. The compensating fact recorded beside it: a flapping
    unit under `Restart=` used to re-probe every retailer at full rate on every
    restart, and now does not.

    RE-POINTED AT THE OFFSET, AND ONLY THE OFFSET, which is a STRICTLY STRONGER
    claim than `== 0.0` — 0.0 is also what a truncated or hostile document
    produces, so the old form could not tell a derived schedule from a lost one.
    The pacer here is built with a roster so the offset is non-zero: under the
    defaulted construction the assertion would read 0.0 == 0.0 and pass without a
    subject, which is the shape of a test that cannot fail.
    """
    path = tmp_path / "pacer-state.json"
    roster = ("amazon", "bestbuy", "gamestop", "nintendo", "target", "walmart")
    tick = loop_tick_seconds(300, roster)

    def restored() -> Pacer:
        return Pacer(default_interval=300, state_path=path, roster=roster, tick=tick)

    first = restored()
    for _ in range(5):
        first.record("walmart", refused=True, now=0.0)
    assert first._for("walmart").due_at > 0, "the writing pacer really did have a schedule"
    first.save(set())

    second = restored()
    second.load()

    # walmart AND NOT amazon, because amazon sorts first in this roster and its
    # offset is 0.0 — against which `== 0.0` and `== slot_offset(...)` are the
    # same assertion and neither has a subject.
    offset = slot_offset("walmart", roster, tick, 300)
    assert offset > 0.0, "the fixture has to have an offset before it can assert one"
    assert second._for("walmart").due_at == offset, (
        "a due_at came back from disk. It was measured against a clock that no "
        "longer exists, so it is not a schedule — it is an accident"
    )
    assert second._for("walmart").due_at != first._for("walmart").due_at, (
        "the restored schedule is the writing process's schedule — the number "
        "this process computed and the number the last one left behind must not "
        "be the same number by accident"
    )
    assert not second.due("walmart", 0.0), (
        "a restart asked immediately. That was the concession withdrawn on "
        "2026-09-01: a restart re-tests each retailer within one standing "
        "interval, at its own position, not at t=0 alongside every other retailer"
    )
    assert second.due("walmart", 300.0), (
        "a restart must still try once WITHIN ONE STANDING INTERVAL — later is "
        "the price collision 2 named, and never is not on the table"
    )


def test_the_restored_count_is_load_bearing_on_the_next_wait(tmp_path: Path) -> None:
    """Restoring the number is not enough; it has to reach the arithmetic.

    A `load` that wrote the count somewhere `record` never reads would pass the
    assertion above and change nothing about how often we ask.
    """
    path = tmp_path / "pacer-state.json"
    first = _pacer(path)
    for _ in range(5):
        first.record("amazon", refused=True, now=0.0)
    first.save(set())

    second = _pacer(path)
    second.load()
    second.record("amazon", refused=True, now=0.0)

    assert second._for("amazon").due_at == 300 * 2**6, (
        "the first refusal after a restart produced the wait for refusal 1, not "
        "for refusal 6 — the restored depth never reached the schedule"
    )


def test_a_good_read_clears_the_count_on_disk_as_well(tmp_path: Path) -> None:
    """The file self-cleans: a retailer at zero refusals is not written at all.

    So a retailer that started answering again drops out, and one deleted from
    the config ages out of the document rather than accumulating in it forever.
    """
    path = tmp_path / "pacer-state.json"
    first = _pacer(path)
    first.record("amazon", refused=True, now=0.0)
    first.save(set())
    assert "amazon" in json.loads(path.read_text())["retailers"]

    first.record("amazon", refused=False, now=0.0)
    first.save(set())

    assert json.loads(path.read_text())["retailers"] == {}, (
        "a retailer with no refusals was still written — the document would "
        "accumulate every retailer that ever answered"
    )
    second = _pacer(path)
    second.load()
    assert second._for("amazon").refusals == 0


def test_the_paging_memory_round_trips(tmp_path: Path) -> None:
    """`warned` is passed through, never held — but it must survive the trip.

    Restoring `refusals` without it restores half a decision: process 2 would
    find the retailer entrenched at its first cycle and page immediately about a
    refusal somebody was already told about, which is REQ-16's "once" becoming
    "once per process" from the other end.
    """
    path = tmp_path / "pacer-state.json"
    _pacer(path).save({"amazon", "gamestop"})

    assert _pacer(path).load() == {"amazon", "gamestop"}


def test_an_empty_paging_memory_round_trips(tmp_path: Path) -> None:
    """The other direction, so `load` cannot satisfy the test above by inventing."""
    path = tmp_path / "pacer-state.json"
    _pacer(path).save(set())

    assert _pacer(path).load() == set()


def _document(refusals: int, age: float, warned_age: float | None = None) -> str:
    """A well-formed document. `warned_age` stamps `amazon` that many seconds ago.

    `warned` is a MAPPING of retailer to the wall clock its paging episode
    began, not the list it was before 05-REVIEW's WR-01 — a list carries no
    date, so `load` had nothing to age it by and never did.
    """
    warned = {} if warned_age is None else {"amazon": time.time() - warned_age}
    return json.dumps(
        {
            "version": STATE_VERSION,
            "retailers": {"amazon": {"refusals": refusals, "refused_at": time.time() - age}},
            "warned": warned,
        }
    )


def test_state_older_than_the_backoff_cap_is_discarded(tmp_path: Path) -> None:
    """The objection the withdrawn docstring raised, answered rather than ignored.

    A file written before a machine was off for a week would otherwise restore a
    six-hour backoff against a condition that has had a week to clear.

    THE NAME SAYS "THE BACKOFF CAP" AND THE WINDOW IS NO LONGER THAT, since
    2026-08-28: it is `LONGEST_WAIT_SECONDS`, which past
    `REFUSALS_BEFORE_COOLOFF` is the cool-off rather than the cap. The name is
    KEPT deliberately — this test is written symbolically against
    `STATE_MAX_AGE_SECONDS`, so its assertion is exactly as right as it was, and
    a rename would cost its `git log -S` history while changing nothing it
    checks. See
    `test_the_age_out_is_derived_from_the_longest_wait_the_module_can_produce`
    for where the derivation is asserted and the reversal recorded.
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=5, age=STATE_MAX_AGE_SECONDS + 1))

    p = _pacer(path)
    p.load()

    assert p._for("amazon").refusals == 0, (
        "state older than one full longest-wait-length window was applied — it "
        "has outlived the reasoning that produced it"
    )


def test_a_paging_memory_older_than_the_backoff_cap_is_discarded(tmp_path: Path) -> None:
    """WR-01. The age-out was applied to the refusal counts and to nothing else.

    `warned` was restored unconditionally, whatever the file's age. Combined
    with `cli.watch_cycle`'s `still_unhealthy = ... | (warned - checked)`, an
    entry only leaves the set when the retailer is CHECKED and no longer
    pageable — which for a genuinely broken detector never happens: it stays
    `pageable`, `fresh` excludes it because it is already in `warned`,
    `still_unhealthy` re-adds it, and it is re-written every cycle.

    So a `pacer-state.json` written months ago and left on disk suppressed that
    retailer's health warning INDEFINITELY, from evidence this module's own
    docstring says "has outlived the reasoning that produced it" — silencing the
    one alert this project exists to send, and looking exactly like a healthy
    quiet monitor while it did.

    The sibling of `test_state_older_than_the_backoff_cap_is_discarded`, which
    is where IN-04 said this belonged.

    THE NAME SAYS "THE BACKOFF CAP" AND THE WINDOW IS NO LONGER THAT, since
    2026-08-28 — it is `LONGEST_WAIT_SECONDS`. Name kept for the reason given at
    the sibling above: the assertion is symbolic and unchanged. The widening does
    have a real cost on THIS half, and it is argued at `STATE_MAX_AGE_SECONDS`
    rather than hidden: a health warning about our own dead control can now be
    suppressed for up to three days rather than six hours. Bounded, and never
    unbounded. See
    `test_the_age_out_is_derived_from_the_longest_wait_the_module_can_produce`.
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=1, age=1.0, warned_age=STATE_MAX_AGE_SECONDS + 1))

    assert _pacer(path).load() == set(), (
        "a paging memory older than one full longest-wait-length window was "
        "restored — the retailer it names can never be paged about again"
    )


def test_a_paging_memory_younger_than_the_cap_is_restored(tmp_path: Path) -> None:
    """Bounded on both sides, so the age-out cannot pass by discarding everything.

    Discarding every entry would restore REQ-16's "pushed once per process" from
    the other end, which is the regression M13 exists to catch.

    THE NAME SAYS "THE CAP" AND THE WINDOW IS NO LONGER THAT, since 2026-08-28 —
    it is `LONGEST_WAIT_SECONDS`. Name kept: the assertion is symbolic and holds
    whatever the window is. See
    `test_the_age_out_is_derived_from_the_longest_wait_the_module_can_produce`.
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=1, age=1.0, warned_age=1.0))

    assert _pacer(path).load() == {"amazon"}


def test_a_paging_stamp_in_the_future_is_discarded(tmp_path: Path) -> None:
    """A clock that jumped backwards must not hold the memory forever.

    The same argument the refusal counts make: with only an upper bound,
    `now - stamp` goes negative and stays inside it for as long as the skew
    lasts, which is no expiry at all.
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=1, age=1.0, warned_age=-STATE_MAX_AGE_SECONDS))

    assert _pacer(path).load() == set()


def test_saving_does_not_refresh_an_episodes_stamp(tmp_path: Path) -> None:
    """The property that lets the age-out ever fire, asserted directly.

    `save` runs once per cycle. If it stamped `time.time()` each write, the
    record would be refreshed roughly every five minutes forever and the window
    above could never close — a bound that cannot bind, which is worse than no
    bound because the file reads as though it were dated.
    """
    path = tmp_path / "pacer-state.json"
    began = time.time() - 600.0
    path.write_text(
        json.dumps(
            {
                "version": STATE_VERSION,
                "retailers": {},
                "warned": {"amazon": began},
            }
        )
    )

    p = _pacer(path)
    assert p.load() == {"amazon"}
    p.save({"amazon"})
    p.save({"amazon"})

    written = json.loads(path.read_text())["warned"]["amazon"]
    assert written == pytest.approx(began), (
        "the episode was re-stamped on write, so it can never age out"
    )


def test_a_retailer_that_leaves_the_paging_memory_leaves_the_stamps_too(
    tmp_path: Path,
) -> None:
    """The other half of self-cleaning: the document must not accumulate.

    `save`'s docstring already claimed the retailers half self-cleans. The
    paging half did not — a retailer deleted from the config stayed in `warned`
    forever and nothing bounded the list's length.
    """
    path = tmp_path / "pacer-state.json"
    p = _pacer(path)
    p.save({"amazon", "gamestop"})
    p.save({"amazon"})

    assert set(json.loads(path.read_text())["warned"]) == {"amazon"}


def test_state_younger_than_the_cap_is_restored(tmp_path: Path) -> None:
    """Bounded on both sides, so the age-out cannot pass by discarding everything.

    THE NAME SAYS "THE CAP" AND THE WINDOW IS NO LONGER THAT, since 2026-08-28 —
    it is `LONGEST_WAIT_SECONDS`. Name kept: the assertion is symbolic and holds
    whatever the window is, which is exactly why it could not pin where the
    window moved TO and why `_RESTORE_ACROSS_THE_STALENESS_WINDOW` is written
    out in literals instead. See
    `test_the_age_out_is_derived_from_the_longest_wait_the_module_can_produce`.
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=5, age=1.0))

    p = _pacer(path)
    p.load()

    assert p._for("amazon").refusals == 5


def test_a_stamp_in_the_future_is_discarded(tmp_path: Path) -> None:
    """A clock that jumped backwards must not hold the state forever.

    With only an upper bound, `now - refused_at` goes negative and stays inside
    it for as long as the skew lasts — pinning a retailer at the cap with no
    expiry at all, which is the failure the age-out exists to prevent.
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=5, age=-STATE_MAX_AGE_SECONDS))

    p = _pacer(path)
    p.load()

    assert p._for("amazon").refusals == 0


#: What a document carrying `REFUSALS_BEFORE_COOLOFF` refusals restores, and what
#: cadence that restored depth produces, at five ages spanning both sides of the
#: staleness window. `(age_seconds, expected_refusals, expected_interval)`.
#:
#: EVERY NUMBER HAND-WRITTEN, and that is the point of the table — restating
#: `_CADENCE_AFTER_N_REFUSALS`' own argument in this table's terms. The six window
#: tests above are written SYMBOLICALLY, against `STATE_MAX_AGE_SECONDS` itself,
#: which is exactly right for what they check and exactly why they cannot pin
#: where the window moved TO: they hold whatever the window is. An age written as
#: `MAX_BACKOFF_SECONDS + 1` or `STATE_MAX_AGE_SECONDS + 1` here would be a
#: re-derivation of the constant under test, which is a test that cannot fail.
#: Written out, a future edit to the window has to change these numbers BY HAND,
#: and doing that is the moment somebody notices they have changed how long a
#: refusal stays evidence.
#:
#: WHAT EACH ROW IS FOR, because five rows that all just "check the window" would
#: be one row four times:
#:
#: 1. `1.0` — a fresh record. Green before this change and after it; the control
#:    that says the restore machinery was already there.
#: 2. `21601.0` — ONE SECOND past the ceiling this phase stopped applying
#:    indefinitely, and well inside a cool-off. THIS IS THE ROW THAT IS RED
#:    BEFORE THE DERIVATION MOVES: today it restores 0 and a 300 s cadence, so a
#:    restart throws away a three-day cool-off after six hours.
#: 3. `259199.0` — one second inside the new window. Red before, green after.
#: 4. `259201.0` — one second PAST the new window. The upper bound still binds,
#:    so this change widened the window rather than removing it.
#: 5. `-1.0` — a stamp one second in the FUTURE, i.e. a clock that jumped
#:    backwards, still discarded at cool-off depth. The window is still
#:    TWO-SIDED, which is criterion 5's no-second-rule clause asserted
#:    behaviourally: the cheapest way to make a record survive is to stop
#:    discarding it, and this row is what forbids that.
#:
#: BOTH COLUMNS ARE ASSERTED ON EVERY ROW. A restore that reached the field and
#: not the arithmetic is the exact failure
#: `test_the_restored_count_is_load_bearing_on_the_next_wait`'s docstring names,
#: and asserting it once at one age would leave it unasserted at the age that
#: matters.
_RESTORE_ACROSS_THE_STALENESS_WINDOW = [
    (1.0, 30, 259200.0),
    (21601.0, 30, 259200.0),
    (259199.0, 30, 259200.0),
    (259201.0, 0, 300.0),
    (-1.0, 0, 300.0),
]


@pytest.mark.parametrize(
    "age_seconds, expected_refusals, expected_interval",
    _RESTORE_ACROSS_THE_STALENESS_WINDOW,
)
def test_a_refusal_record_is_restored_across_the_whole_staleness_window(
    tmp_path: Path,
    age_seconds: float,
    expected_refusals: int,
    expected_interval: float,
) -> None:
    """Criterion 5, at the step, on both sides, at cool-off depth.

    A retailer in a three-day cool-off is re-stamped only at its own probe, so
    its record spends almost all of its life older than six hours. Before
    `STATE_MAX_AGE_SECONDS` was re-derived, `load` discarded every such record
    and the retailer came back from a restart on the climbing backoff — the
    cool-off surviving in the file and not in the process.
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=REFUSALS_BEFORE_COOLOFF, age=age_seconds))

    p = _pacer(path)
    p.load()

    assert p._for("amazon").refusals == expected_refusals, (
        f"a record stamped {age_seconds} s ago restored "
        f"{p._for('amazon').refusals} refusals, not {expected_refusals}"
    )
    assert p.current_interval("amazon") == expected_interval, (
        f"a record stamped {age_seconds} s ago produced a cadence of "
        f"{p.current_interval('amazon')} s, not {expected_interval} — the depth "
        f"was restored somewhere the arithmetic never reads"
    )


def test_a_cooloff_survives_into_a_brand_new_pacer_and_reaches_the_schedule(
    tmp_path: Path,
) -> None:
    """The round-trip claim, at cool-off depth, through the REAL `save`.

    Every other test on this window hand-builds its document with `_document`.
    This one drives the threshold with `record` and lets `save` write the file,
    so it is the only place that asserts a document this class actually PRODUCES
    is a document it can read back at cool-off depth.

    IT IS GREEN BEFORE THIS PLAN'S CHANGE, AND THAT IS A FINDING RATHER THAN A
    FORMALITY. Its document is written and read in the same instant, so its age
    is approximately zero and it sits inside the window either way. The survival
    machinery — the counter, the stamp, the clamp, the round trip — already
    existed and was already right; what this plan repairs is only how long the
    window believes it. A reader meeting a green test inside a watched-red plan
    deserves to know which kind it is, so: this one is a control.
    """
    path = tmp_path / "pacer-state.json"
    first = _pacer(path)
    for _ in range(REFUSALS_BEFORE_COOLOFF):
        first.record("amazon", refused=True, now=0.0)
    first.save(set())

    second = _pacer(path)
    second.load()

    assert second._for("amazon").refusals == REFUSALS_BEFORE_COOLOFF, (
        "the cool-off depth did not survive the process at all"
    )
    assert second.current_interval("amazon") == 259200.0, (
        "the restored depth did not produce the cool-off cadence — the retailer "
        "came back from the restart on the six-hour ceiling"
    )

    second.record("amazon", refused=True, now=0.0)

    assert second._for("amazon").due_at == 259200.0, (
        "the first refusal after a restart scheduled a backoff rather than a "
        "cool-off — the restored depth never reached the schedule"
    )


def test_a_restart_mid_cooloff_is_probed_exactly_once_over_a_whole_window(
    tmp_path: Path,
) -> None:
    """A restart mid-cool-off costs exactly one probe. Measured, not inferred.

    864 cycles of 300 s is 259 200 s, which is one whole cool-off window. The
    864 is WRITTEN OUT rather than computed from `COOLOFF_SECONDS`, on
    `_THIRTY_DAYS_OF_CYCLES`' precedent: a future edit to the window has to
    change this number by hand, and doing that is the moment somebody notices
    the denominator moved underneath a count.

    THE AGE IS HAND-WRITTEN AT 21 601 s for the same reason row 2 of
    `_RESTORE_ACROSS_THE_STALENESS_WINDOW` is — one second past the ceiling this
    phase stopped applying indefinitely, so this test is red before the
    derivation moves and green after. With the record discarded the retailer
    comes back on the climbing backoff and is probed many times inside the same
    window.

    THIS MEASURES A PRICE THAT WAS SET IN ADVANCE. `08-DECISIONS.md` § Collision
    2 kept `due_at` unpersisted and priced a restart at exactly one immediate
    request at full rate; this is the first place in the phase that price is
    OBSERVED across an actual restart rather than decided. If the two ever
    disagree, the run wins and the decision record is superseded beside itself.
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=REFUSALS_BEFORE_COOLOFF, age=21601.0))

    p = _pacer(path)
    p.load()

    probes = 0
    now = 0.0
    for _ in range(864):
        if p.due("amazon", now):
            probes += 1
            p.record("amazon", refused=True, now=now)
        now += 300.0

    assert probes == 1, (
        f"a restart mid-cool-off cost {probes} probes over one whole cool-off "
        f"window, not the 1 that 08-DECISIONS.md priced it at"
    )


def test_one_load_restores_the_count_and_the_paging_memory_together(
    tmp_path: Path,
) -> None:
    """Criterion 5's no-second-rule clause, asserted behaviourally.

    Not a duplicate of row 2 of `_RESTORE_ACROSS_THE_STALENESS_WINDOW`. That row
    watches ONE half of the document cross the window; this watches BOTH halves
    cross it in a single `load`, at an age where both used to be thrown away.
    That is only possible if ONE constant governs both, so a future second
    staleness rule written for the cool-off alone — a wider bound on the refusal
    counts, a cool-off-specific age-out, a re-stamp on read — would split them
    and redden this test and nothing else in the file.

    WHY THE SPLIT WOULD MATTER RATHER THAN MERELY BE UNTIDY, in `Pacer.load`'s
    own words: restoring one without the other "restores half a decision", and
    the half that goes missing is the worse one — a process that comes back
    knowing the retailer is entrenched and not knowing it has already said so
    pages immediately about a refusal somebody was already told about. A
    three-day cool-off against a six-hour window would have guaranteed exactly
    that split on every restart, because a retailer left alone for three days is
    not checked for three days and `cli.watch_cycle`'s `still_unhealthy` keeps it
    in `warned` the whole time.
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(
        _document(refusals=REFUSALS_BEFORE_COOLOFF, age=21601.0, warned_age=21601.0)
    )

    p = _pacer(path)
    restored = p.load()

    assert restored == {"amazon"}, (
        "the paging memory was discarded at an age the refusal count survives — "
        "the two halves of this document are aging on different schedules"
    )
    assert p._for("amazon").refusals == REFUSALS_BEFORE_COOLOFF, (
        "the refusal count was discarded at an age the paging memory survives — "
        "the two halves of this document are aging on different schedules"
    )


def test_a_standing_interval_above_the_window_makes_the_restored_depth_irrelevant() -> None:
    """The one case `LONGEST_WAIT_SECONDS` does not bound, shown to cost nothing.

    `config._interval` enforces a floor and NO upper bound, so an operator can
    configure a retailer at a week and `current_interval` will return more than
    the staleness window. Does the window then fail to cover the module's waits?

    No, and it is provable rather than arguable. Once the standing interval
    exceeds both wait arms, the outer `max` returns that interval at EVERY
    refusal depth: at 0 by the `not st.refusals` branch, from 1 to 29 because the
    capped backoff cannot exceed `MAX_BACKOFF_SECONDS`, and at 30 and beyond
    because the cool-off cannot exceed `COOLOFF_SECONDS`. The persisted depth is
    therefore not load-bearing at all there, so a depth aged out changes nothing
    about when the retailer is asked. `LONGEST_WAIT_SECONDS` bounds the module's
    own POLICY range; above it the wait is the operator's standing decision,
    which no persisted count influences.

    GREEN FROM BIRTH, and named as such: it reads no document and no clock, so
    the staleness window cannot reach it. It converts the argument above from
    prose in a comment into a gate, which is the only thing it is for.
    """
    p = _pacer(interval=259201.0)

    assert p.current_interval("amazon") == 259201.0, "0 refusals"
    p.record("amazon", refused=True, now=0.0)
    assert p.current_interval("amazon") == 259201.0, "1 refusal"
    for _ in range(REFUSALS_BEFORE_COOLOFF - 1):
        p.record("amazon", refused=True, now=0.0)
    assert p._for("amazon").refusals == REFUSALS_BEFORE_COOLOFF
    assert p.current_interval("amazon") == 259201.0, "at the cool-off threshold"
    for _ in range(MAX_PERSISTED_REFUSALS - REFUSALS_BEFORE_COOLOFF):
        p.record("amazon", refused=True, now=0.0)
    assert p._for("amazon").refusals == MAX_PERSISTED_REFUSALS
    assert p.current_interval("amazon") == 259201.0, "at the persistence clamp"


def test_the_persisted_count_is_clamped(tmp_path: Path) -> None:
    """A number out of a file reaching `BACKOFF_FACTOR ** refusals`.

    Measured 2026-08-10 on CPython 3.12.3: `2.0 ** 1024` raises OverflowError.
    Inside `record` that is an exception every cycle, caught by `watch_loop`,
    counted to FAILURES_BEFORE_GIVING_UP and returned as exit 1 — a one-line
    denial of service on the monitor, from a file the monitor wrote itself.

    THE LAST ASSERTION'S LITERAL WAS WITHDRAWN ON 2026-08-28. It read, in full:

        assert p._for("amazon").due_at == MAX_BACKOFF_SECONDS

    What overruled it: REQ-22 put a cool-off past `REFUSALS_BEFORE_COOLOFF = 30`,
    and `MAX_PERSISTED_REFUSALS = 64` is above that threshold **on purpose** — the
    threshold is argued to sit under the clamp precisely so that a count restored
    from disk can cross it, since a threshold at or above the clamp could never be
    reached from a restart at all. So a clamped restore now lands in cool-off by
    design, and the old literal was asserting the absence of the feature this
    phase adds. Measured here at 65 refusals (64 restored by the clamp, plus the
    one this test records): **259200.0 observed against an expected 21600**.

    WHAT SURVIVES IS THIS TEST'S ENTIRE SUBJECT, untouched. The subject is the
    measured `2.0 ** 1024` `OverflowError` above and the clamp that prevents it —
    a denial of service on the monitor from a file the monitor wrote itself — and
    a cool-off has nothing to do with it. Both assertions that carry that subject
    are byte-unchanged: the clamp restoring exactly `MAX_PERSISTED_REFUSALS`, and
    `record` completing without raising. Only the scheduled wait moved.

    THE PARAGRAPH ABOVE IS WRONG AND IS LEFT UNEDITED BESIDE THIS NOTE —
    2026-08-31, `08-REVIEW.md` WR-02. It was written by this phase on 2026-08-28
    and it got its own change backwards: a cool-off has EVERYTHING to do with it,
    because the cool-off is now what prevents the overflow. `current_interval` is
    a conditional expression, so past `REFUSALS_BEFORE_COOLOFF` the exponentiation
    is never evaluated. MEASURED 2026-08-31 with the clamp bypassed: an unclamped
    `refusals = 10**9` returns 259200.0 and does not raise.

    SO THE SECOND ASSERTION IS NO LONGER A GATE, and saying so is the point. The
    `record` call below now passes with or WITHOUT the clamp, which by this
    repository's own rule — "a test that has never failed is not a gate" — means
    it defends nothing and must not read as though it does. It is kept as a smoke
    check. The live gate for this constant is
    `test_the_clamp_sits_above_the_cooloff_threshold_so_a_restored_count_can_cross_it`,
    which drives the relationship that IS still load-bearing. The first assertion
    (the clamp restoring exactly `MAX_PERSISTED_REFUSALS`) is untouched and does
    still bite.

    THE NEW LITERAL IS WRITTEN OUT AS `259200.0` RATHER THAN AS `COOLOFF_SECONDS`,
    on the same discipline as the boundary table and for the same reason: a
    symbolic literal here would be a re-derivation of the constant under test, and
    it would let a future edit to `COOLOFF_SECONDS` pass in silence in the one
    place that proves a RESTORED count crosses the threshold.
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=10**9, age=1.0))

    p = _pacer(path)
    p.load()

    assert p._for("amazon").refusals == MAX_PERSISTED_REFUSALS
    # NOT A GATE — see the docstring. `# must not raise` stopped biting when
    # REQ-22 made the exponentiation unreachable past the threshold; this call
    # returns 259200.0 whether or not the clamp ran. Kept as a smoke check.
    p.record("amazon", refused=True, now=0.0)
    assert p._for("amazon").due_at == 259200.0


def test_the_clamp_never_restores_a_shallower_wait_than_the_cap() -> None:
    """The clamp must not quietly undo the backoff it was added to protect.

    RE-ANCHORED 2026-08-12, because its subject was deleted. This read
    `MAX_PERSISTED_REFUSALS >= cli.REFUSALS_BEFORE_PAGING` — "a clamp at or
    below the paging threshold would mean persistence silently defeated the
    paging clause it exists to serve". Dan's rule removed that clause and its
    constant with it: a refusal is recorded and never pushed, however
    entrenched, so there is no longer a paging threshold to stay above.

    What the clamp still protects is the BACKOFF, which is untouched and is the
    monitor's own response to being refused. A count restored below the one that
    reaches `MAX_BACKOFF_SECONDS` would come back from disk asking sooner than
    the retailer's own history says it should — persistence defeating the
    politeness it exists to serve, which is the same sentence one layer down.
    `pacing` still must not import `cli`; now it does not have to.
    """
    from boty.pacing import BACKOFF_FACTOR

    shallowest = min(300.0, MAX_BACKOFF_SECONDS)
    assert shallowest * BACKOFF_FACTOR**MAX_PERSISTED_REFUSALS >= MAX_BACKOFF_SECONDS


def test_the_clamp_sits_above_the_cooloff_threshold_so_a_restored_count_can_cross_it() -> None:
    """A threshold above the clamp is a cool-off no restart can ever reach.

    REQ-22, 2026-08-28. `load` clamps every restored refusal count to
    `MAX_PERSISTED_REFUSALS`, so if the threshold sat at or above that ceiling a
    retailer three days deep in a cool-off would come back from a restart at the
    six-hour cap and start knocking again — the cool-off would be a state only a
    long-lived process could enter, which under a `Restart=` unit is close to no
    state at all. Persistence silently defeating the clause it exists to serve.

    THIS IS THE REPLACEMENT FOR A RELATIONSHIP THAT DIED. `MAX_PERSISTED_REFUSALS`
    used to be pinned above `cli.REFUSALS_BEFORE_PAGING`, and that constant was
    deleted on 2026-08-12 leaving the comment naming it and nothing checking
    anything. The direction is the same one that sentence was reaching for; only
    the requirement on the other side of it is new.

    ASSERTED HERE RATHER THAN IN A COMMENT, because `boty/pacing.py` must not
    import `boty.cli` and learned once already what a relationship stated only in
    prose is worth.
    """
    assert MAX_PERSISTED_REFUSALS > REFUSALS_BEFORE_COOLOFF, (
        f"the clamp restores at most {MAX_PERSISTED_REFUSALS} refusals but the "
        f"cool-off begins at {REFUSALS_BEFORE_COOLOFF} — a count restored from "
        f"disk can never cross the threshold, so the cool-off does not survive a "
        f"restart at all"
    )


def test_the_age_out_is_derived_from_the_longest_wait_the_module_can_produce() -> None:
    """Derived, not re-chosen, so the two can never drift apart.

    RENAMED AND REWRITTEN ON 2026-08-28, from
    `test_the_age_out_is_derived_from_the_backoff_cap` — the old name is written
    out here so `git log -S` can still reach this function's history through the
    text. The name stated the exact claim being withdrawn, so unlike the four
    window tests further up this file (whose names are symbolic and stay), a
    rename was the honest move: leaving it would leave the withdrawn claim
    standing as an assertion's name.

    THE ASSERTION WAS WITHDRAWN ON 2026-08-28. It read, in full:

        assert STATE_MAX_AGE_SECONDS == MAX_BACKOFF_SECONDS

    AND SO WAS THE SENTENCE THAT ARGUED FOR IT, which read, in full:

        "The cap already IS this project's written answer to how long a refusal
        stays evidence; a second number here would be a second answer to the
        same question."

    Two measured facts overruled them.

    1. REQ-22 made the cap stop being the longest wait this module produces.
       Past `REFUSALS_BEFORE_COOLOFF` the exponential is not evaluated at all
       and a flat `COOLOFF_SECONDS` takes over, so "the cap" and "the longest
       wait" — the same number until 2026-08-28 — are now different numbers.
    2. `08-02` measured the cool-off at 259 200 s against a 21 600 s cap. A
       retailer in cool-off is re-stamped only at its own probe, so its record
       is TWELVE window-lengths old at the moment that probe falls due, and
       every restart discarded it. `08-01` measured the old rule at 125
       requests over 30 simulated days and `08-02` measured the new one at 37;
       the 37 is the number a discarded record silently turned back into a 125.

    WHAT SURVIVES IS THE ENTIRE PRINCIPLE, which is why this is a rewrite and
    not a deletion. Derived and never re-chosen, so the two cannot drift apart —
    untouched, and it is still the same argument `Result.degraded` makes about
    deriving rather than storing. "One full cap-length window" survives in
    substance as one full longest-wait-length window: the sentence's shape, its
    reasoning and its conclusion are all intact. Only the premise that the cap
    WAS the longest wait has fallen, and with it the ceiling the window derives
    from. No conclusion fell, which is unusual for a reversal and worth saying
    to a reader who arrives expecting one.

    WHAT THE LAST TWO ASSERTIONS ARE AND ARE NOT. They are a gate against a
    FUTURE re-definition that covers only one arm — someone spelling this
    `= COOLOFF_SECONDS` because that is the winner today would pass the first
    assertion and fail the second the day the cap overtakes it. They are NOT a
    proof of the current expression, which they would follow from trivially: a
    `max` of two numbers is greater than or equal to each of them by
    construction. Stated rather than left to look stronger than it is.

    THE VALUE ITSELF IS DELIBERATELY NOT PINNED HERE. 259 200 belongs in
    `_RESTORE_ACROSS_THE_STALENESS_WINDOW`, whose subject is the behaviour.
    Pinning it here as well would make an edit to `COOLOFF_SECONDS` fail in the
    one place whose subject is the derivation rather than the number.
    """
    assert STATE_MAX_AGE_SECONDS == LONGEST_WAIT_SECONDS, (
        "the staleness window stopped being derived from the longest wait this "
        "module can produce — a record can now age out while the wait it "
        "describes is still running"
    )
    assert LONGEST_WAIT_SECONDS >= MAX_BACKOFF_SECONDS, (
        "the longest wait no longer covers the backoff cap"
    )
    assert LONGEST_WAIT_SECONDS >= COOLOFF_SECONDS, (
        "the longest wait no longer covers the cool-off"
    )


def _versioned(**payload: object) -> str:
    """A document that gets the version right and everything else wrong."""
    return json.dumps({"version": STATE_VERSION, **payload})


def _entry(**fields: object) -> str:
    return _versioned(retailers={"a": fields})


_HOSTILE = [
    ("this is not json at all", "not JSON"),
    ("", "an empty file"),
    ("[]", "a JSON list"),
    ('"amazon"', "a JSON string"),
    ("3", "a JSON number"),
    ("null", "JSON null"),
    (_versioned(retailers=3), "retailers is not a mapping"),
    (_versioned(retailers={"a": 3}), "an entry is not a mapping"),
    (_entry(refusals="x", refused_at=0), "refusals is a string"),
    (_entry(refusals=-5, refused_at=0), "refusals is negative"),
    (_entry(refusals=True, refused_at=0), "refusals is a bool (an int subclass)"),
    (_entry(refusals=10**9), "refusals is huge and refused_at is absent"),
    (_entry(refusals=3, refused_at="now"), "refused_at is a string"),
    (_entry(refusals=3, refused_at=None), "refused_at is null"),
    (_versioned(warned="amazon"), "warned is a bare string"),
    (_versioned(warned=[1, 2]), "warned is a list of ints"),
    (_versioned(warned=7), "warned is a number"),
    (json.dumps({"version": 999, "retailers": {"a": {"refusals": 9}}}), "an unrecognised version"),
    (json.dumps({"retailers": {"a": {"refusals": 9}}}), "no version at all"),
]


@pytest.mark.parametrize(("document", "description"), _HOSTILE, ids=[d for _, d in _HOSTILE])
def test_a_hostile_state_file_yields_a_usable_pacer(
    tmp_path: Path, document: str, description: str
) -> None:
    """T-05-04: a corrupt state file must never stop the monitor starting.

    BOTH halves are asserted, and the second is the one that matters. A table
    that only drove `load` would pass while the crash sat one method along, in
    `record`, where a restored count reaches `BACKOFF_FACTOR ** refusals`.
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(document)

    p = _pacer(path)
    warned = p.load()  # must not raise

    assert warned == set(), f"{description}: restored a paging memory out of a broken file"
    assert p._for("a").refusals == 0, f"{description}: restored a count out of a broken file"
    p.record("a", refused=True, now=0.0)  # must not raise either
    p.record("a", refused=False, now=0.0)
    assert p.due("a", 10_000.0)
    assert p.skipped_reason("a", 0.0)


def test_a_state_path_that_is_a_directory_is_survivable(tmp_path: Path) -> None:
    """`read_text` on a directory raises IsADirectoryError, which is an OSError.

    Listed separately because it is not a document at all — it is the shape of
    accident that a mistyped config produces.
    """
    path = tmp_path / "pacer-state.json"
    path.mkdir()

    p = _pacer(path)
    assert p.load() == set()
    p.record("amazon", refused=True, now=0.0)
    p.save({"amazon"})  # must not raise either


def test_a_missing_state_file_is_an_empty_start_not_an_error(tmp_path: Path) -> None:
    p = _pacer(tmp_path / "nothing-here.json")

    assert p.load() == set()
    p.record("amazon", refused=True, now=0.0)
    assert p._for("amazon").refusals == 1


def test_failing_to_persist_degrades_rather_than_raising(tmp_path: Path) -> None:
    """A full disk is a worse monitor, not a dead one.

    `watch_loop` calls `save` from a `finally` inside its own try/except, so a
    raise here would be counted as a failed cycle — ten of them and the monitor
    exits 1 because it could not write a backoff counter.
    """
    blocker = tmp_path / "blocker"
    blocker.write_text("I am a file, not a directory")
    p = _pacer(blocker / "sub" / "pacer-state.json")
    p.record("amazon", refused=True, now=0.0)

    p.save({"amazon"})  # must not raise


def test_a_serialisation_failure_degrades_the_same_way_a_disk_failure_does(
    tmp_path: Path,
) -> None:
    """The handler was narrower than the promise one line above it.

    `save` wrapped only `OSError`, but `json.dumps` and `sorted(warned)` are
    inside the same `try` and neither raises that. `sorted` over a set with
    mixed key types raises TypeError — reachable, before 05-REVIEW's CR-01,
    because `Watch.retailer` was not coerced, so `Health.retailer` and therefore
    `warned` could hold a non-`str`.

    The docstring commits to "failing to persist a backoff must degrade to the
    old in-memory behaviour, never take down a cycle". `OSError` alone does not
    deliver that, and the call site makes the gap expensive rather than untidy:
    `cli.watch_loop` calls this from a `finally`, so a raise there also DISCARDS
    a pending `return 1` — see the give-up test in `test_cli_watch.py`.

    A set of mixed types is used rather than a monkeypatched `json.dumps`
    because it reaches the real failure through the real code path.
    """
    p = _pacer(tmp_path / "pacer-state.json")
    p.record("amazon", refused=True, now=0.0)

    p.save({"amazon", 1})  # type: ignore[arg-type]  # must not raise

    assert p._for("amazon").refusals == 1, "the in-memory backoff must survive intact"

    assert p._for("amazon").refusals == 1, "the pacer kept working in memory"
    p.record("amazon", refused=True, now=0.0)
    assert p._for("amazon").refusals == 2


def test_the_restored_interval_comes_from_config_not_from_the_file(tmp_path: Path) -> None:
    """The interval is a config decision and is deliberately never persisted.

    A stored copy would let yesterday's file quietly override an edit to
    `retailer_intervals` — the opposite of what a settings file is for.
    """
    path = tmp_path / "pacer-state.json"
    _pacer(path).save(set())
    path.write_text(_document(refusals=1, age=1.0))

    p = Pacer(default_interval=300, overrides={"amazon": 1800}, state_path=path)
    p.load()

    assert p._for("amazon").interval == 1800


# --------------------------------------------------------------------------
# WR-01 / WR-03: the page must not name a cause the schedule did not establish
# --------------------------------------------------------------------------


def test_a_standing_interval_above_the_cooloff_is_not_published_as_a_penalty() -> None:
    """`skipped_reason` must derive the cool-off, not restate its threshold.

    `current_interval` puts the cool-off INSIDE its single `max` precisely so the
    widen-only rule is applied for free rather than restated — the module argues
    that at three separate sites, and it is the whole reason the cool-off is not
    a guard clause. `skipped_reason` then restated the comparison anyway, which
    is the second copy that argument forbids.

    THEY ALREADY DISAGREE, on a config `Config.load` accepts in silence.
    `config._interval` enforces a floor and no upper bound, so `interval_seconds:
    604800` loads. At a week's standing interval `max(604800, COOLOFF_SECONDS)`
    returns the standing interval at EVERY depth — the retailer is asked at
    exactly the cadence the operator chose, and would be at zero refusals too. No
    cool-off is in force. The page nonetheless attributed the wait to a penalty
    this module applied, which is REQ-15's rule: a surface naming a cause the
    code did not establish.

    The sibling test above drives this same config and asserts only
    `current_interval`, which is why the divergence survived it.
    """
    p = Pacer(default_interval=604800)
    for _ in range(REFUSALS_BEFORE_COOLOFF):
        p.record("amazon", refused=True, now=0.0)

    assert p.current_interval("amazon") == 604800, (
        "precondition: at a week's standing interval the cool-off is not in force"
    )
    assert "cooling off" not in p.skipped_reason("amazon", 0.0), (
        "the page called the operator's own standing cadence a cool-off "
        f"penalty: {p.skipped_reason('amazon', 0.0)!r}"
    )


def test_a_cooloff_near_its_probe_does_not_render_as_zero_days() -> None:
    """One decimal place does not close the hole its own comment says it closes.

    `skipped_reason`'s comment states that zero decimals would render a live wait
    as "0 days" — "a retailer that is genuinely being left alone, described as one
    that is not being left alone at all" — and that one decimal place is
    load-bearing against it. It is not: `f"{x:.1f}"` ROUNDS, so every remaining
    wait below 0.05 days (4320 s) renders as `~0.0 days`.

    THE BAND IS REACHABLE AND WRITTEN TO THE PAGE. `due` skips a retailer while
    the remaining wait exceeds `default_interval * 0.5` (150 s at the default), so
    the reachable window is (150 s, 4320 s) — about 14 cycles per cool-off window,
    each writing a `status.json` row that says the retailer is cooling off and
    that its next attempt is in ~0.0 days.
    """
    p = Pacer(default_interval=300)
    for _ in range(REFUSALS_BEFORE_COOLOFF):
        p.record("cooling", refused=True, now=0.0)

    reason = p.skipped_reason("cooling", COOLOFF_SECONDS - 3600.0)

    assert "cooling off" in reason, "precondition: the cool-off arm is the one under test"
    assert "0.0 days" not in reason, (
        "a live wait of one hour rendered as '~0.0 days' — the exact failure the "
        f"decimal place is documented to prevent, one band down: {reason!r}"
    )


# --------------------------------------------------------------------------
# Criterion 3: a simulated day over the fleet that exists — before, and after
# --------------------------------------------------------------------------

#: One simulated day, in seconds. The denominator both numbers are counts over,
#: and the thing that makes them rates rather than anecdotes. UNCHANGED by
#: REQ-23: the day is the same day, which is what makes the two comparable.
_ONE_DAY_OF_SECONDS = 86400

#: 86 400 / 50 = 1728, at the loop tick the six-retailer fleet below produces.
#: WRITTEN OUT RATHER THAN COMPUTED, on `_THIRTY_DAYS_OF_CYCLES`'s precedent: the
#: arithmetic is stated in this comment so a reader checks it once, and a future
#: edit to the cycle length has to change this number BY HAND — which is the
#: moment somebody notices that the window a published number is attributed to
#: has moved.
#:
#: IT READ 288 UNTIL 2026-09-01 — 86 400 / 300, one cycle per standing cadence —
#: and that is recorded here rather than edited away, because the two numbers are
#: the whole difference between the before-count and the after-count. The DAY did
#: not change and the number of times each retailer is asked did not change; what
#: changed is how often the loop WAKES to ask somebody. The denominator assertion
#: below is what holds those two facts apart: 1728 x 50 s must still be 86 400 s.
_ONE_DAY_OF_CYCLES = 1728

#: The window criterion 3 names, in seconds. Not derived from anything: it is
#: the criterion's own number, quoted.
_WINDOW_SECONDS = 60.0

#: CRITERION 3's BEFORE-NUMBER, AS A DATED RECORD AND NOT AS A RE-RUNNABLE
#: MEASUREMENT. Six of the six configured retailers, measured by `09-01` on
#: 2026-09-01 at `87871b4` against unmodified production code, transcribed from
#: the failure message of the assertion that now reads `_AFTER_MAX_IN_ANY_60S`.
#:
#: IT CANNOT BE RE-MEASURED HERE AND THAT IS STATED RATHER THAN PAPERED OVER. The
#: rule it describes no longer exists in this tree. Freezing a hand-written
#: reproduction of the old arithmetic to keep 6 re-runnable was considered and is
#: rejected on `08-02`'s precedent: it would be a second copy of a number, the
#: copy would be of a rule nothing runs, and a re-runnable assertion over dead
#: arithmetic looks like evidence and is not. Criterion 3 asks for both numbers
#: RECORDED, not both re-runnable.
_BEFORE_MAX_IN_ANY_60S = 6

#: CRITERION 3's AFTER-NUMBER. Transcribed from this test's own failure message
#: the moment the mechanism landed, not reasoned and then written down:
#:
#:     E  AssertionError: the current rule put 2 of the six configured retailers
#:        (amazon, bestbuy, gamestop, nintendo, target, walmart) inside a single
#:        60-second window at least once over a simulated day
#:     E  assert 2 == 6
#:
#: 2 IS THE ARITHMETIC FLOOR AND NOT MERELY THE BEST RESULT MEASURED. Six
#: retailers cannot be spread more than 60 s apart inside a 300 s cadence,
#: because 6 x 60 = 360 > 300, so some 60-second window must hold two of them.
#: A phase claiming 1 would be claiming something unavailable.
_AFTER_MAX_IN_ANY_60S = 2

#: The global `interval_seconds` the fleet table below sits on, and the length
#: of one simulated cycle. ONE name, read by the cycle step, by the pacer's
#: default and by the override derivation — so the simulation cannot be running
#: a different cadence from the one the table claims.
_FLEET_DEFAULT_INTERVAL = 300

#: THE FLEET, WRITTEN OUT RATHER THAN READ. `config/products.yaml` configures
#: six retailers; four sit on the 300 s global `interval_seconds` and two carry
#: `retailer_intervals` overrides. This table is a literal for the same reason
#: `_CADENCE_AFTER_N_REFUSALS` is one: a number published about a fleet must not
#: silently re-point itself at a different fleet. A config change has to edit
#: this table by hand, and the assertion below reddens until it does.
#:
#: IT IS ALSO WHAT THE SIMULATION IS BUILT FROM, deliberately: the `Pacer` below
#: takes its standing intervals from this table rather than from a second literal
#: beside it. A second copy of the fleet inside one test would only have to
#: disagree with this one once — the same argument `current_interval` and
#: `STATE_MAX_AGE_SECONDS` make one module over.
_FLEET_INTERVALS = {
    "amazon": 1800,
    "bestbuy": 300,
    "gamestop": 900,
    "nintendo": 300,
    "target": 300,
    "walmart": 300,
}

#: WHAT EACH RETAILER WAS ASKED OVER THE SIMULATED DAY UNDER THE OLD RULE,
#: transcribed from `09-01`'s recorded tallies (`09-01-SUMMARY.md`, measured at
#: `87871b4` on 2026-09-01: "Total requests counted | 1296 = 48 + 96 + 4 x 288").
#:
#: A SECOND, INDEPENDENT STATEMENT OF THE SAME EXPECTATION, and deliberately so.
#: The tally below already checks each count against `86400 // interval` derived
#: from the fleet table; this table is the number a DIFFERENT RULE actually
#: produced, on a different day, recorded before the rule moved. If REQ-23 had
#: bought its smaller maximum by asking anybody less often, the derived check and
#: this one would both catch it — and this one would catch it even if the fleet
#: table and the arithmetic drifted together.
_BEFORE_PER_RETAILER = {
    "amazon": 48,
    "bestbuy": 288,
    "gamestop": 96,
    "nintendo": 288,
    "target": 288,
    "walmart": 288,
}

#: `config/products.yaml`, located from this file rather than from the working
#: directory — inside `scripts/mutation_check.py`'s sandbox this resolves to the
#: SANDBOX's copy, which is what makes the fleet assertion a gate there too
#: (`config` is in `SANDBOX_CONTENTS`).
_CONFIG = Path(__file__).resolve().parent.parent / "config" / "products.yaml"

#: The same file as `_CONFIG`, named the way a READER names it. The assertions
#: below quote this rather than `_CONFIG`, because an absolute path in a failure
#: message is this machine's home directory printed into a transcript that gets
#: pasted into planning documents and issues — the exact shape
#: `scripts/identity_check.py` exists to keep out of a public repository, arriving
#: from the one direction it cannot scan. DERIVED from `_CONFIG` rather than
#: written out, so the two cannot name different files.
_CONFIG_SHOWN = "/".join(_CONFIG.parts[-2:])


def _max_in_any_window(times: list[float], span: float) -> int:
    """The most events falling inside any window of `span` seconds.

    A SLIDING window over the event times, never fixed bins. Bucketing into
    fixed 60 s bins from t=0 would split a burst that straddles a boundary and
    report a smaller maximum than actually occurred — a reduction achieved by
    where the ruler was laid down, which is exactly the failure mode this
    plan's prohibition names. `times` must be non-decreasing; the caller
    asserts that separately rather than sorting here, because a simulation that
    produced out-of-order events has a defect the sort would hide.
    """
    largest = 0
    start = 0
    for end, t in enumerate(times):
        while t - times[start] >= span:
            start += 1
        largest = max(largest, end - start + 1)
    return largest


def test_the_max_retailers_in_any_sixty_seconds_over_a_day_is_a_stated_number() -> None:
    """Criterion 3, both halves: what the rule puts in one 60-second window.

    THE SAME SIMULATION IT ALWAYS WAS, WITH ONE RULE CHANGED — rewritten in place
    on 2026-09-01 rather than copied, so the two numbers are two answers to ONE
    question. The fleet table, the denominator, the sliding window, the two
    tallies and the window model are untouched; the pacer is now built and
    stepped the way `cli.watch_loop` builds and steps one, which is the whole of
    the difference.

    THE BEFORE-LITERAL IS WITHDRAWN AS AN ASSERTION AND KEPT AS A RECORD. It
    read, in full:

        assert max_in_any_60s == 6, (
            f"the current rule put {max_in_any_60s} of the six configured retailers "
            ...
            f"for criterion 3 is the literal in this assertion"
        )

    measured by `09-01` with `.venv/bin/python -m pytest tests/test_pacing.py -q`
    at `87871b4` on 2026-09-01, against `boty/pacing.py` unmodified and
    `git status --porcelain boty/` empty.

    WHAT OVERRULED IT is this phase's own mechanism, and that is the point rather
    than a casualty: `09-DECISIONS.md` § *Test collision C* recorded before any
    code moved that turning this test red WAS this plan's watched-red evidence
    for criterion 3, because the literal had no other subject available (see the
    stated exception below). The after-number was transcribed from the failure
    message that red produced.

    AND IT WENT RED FOR A REASON WORTH RECORDING, because it did not go red on
    its own. Against the new mechanism this test still read 6 until its pacer was
    given a roster and a tick: a `Pacer` built with neither keeps a zero offset
    and the standing tolerance by design, and stepping it once per cadence
    reproduces the old schedule exactly. A simulation over a defaulted pacer would
    have gone on publishing 6 about code that no longer runs — which is
    `09-DECISIONS.md`'s "a green defaulted site proves nothing about the schedule
    the daemon runs", arriving as a number rather than as an argument.

    THE BEFORE-NUMBER IS NOW A DATED RECORD RATHER THAN A RE-RUNNABLE ASSERTION,
    stated plainly rather than papered over — see `_BEFORE_MAX_IN_ANY_60S` for
    why freezing a reproduction of the old arithmetic was rejected.

    THIS TEST MEASURES; IT DOES NOT GATE ON ITS LITERAL, and this repository's
    standing rule — every gate is watched red before it is trusted — has a
    stated exception here rather than a skipped formality. A watched-red gate
    works by pointing a new assertion at code that is currently wrong, so the
    failure count is evidence that the assertion has a subject. THIS LITERAL'S
    SUBJECT IS THE CODE AS IT STANDS. The lockstep is not a defect being fixed
    in this plan — it is the thing being measured. Writing a deliberately wrong
    literal and watching `assert ==` reject it would prove that `assert ==`
    works, and nothing else. THAT IS THE FINDING.

    What carries the weight instead is four things that do have subjects, three
    of which were watched red on 2026-09-01 with their failure counts recorded
    in `.planning/phases/09-out-of-lockstep/09-DECISIONS.md`: the DENOMINATOR
    assertion (a loop that exited early would present a smaller maximum as a
    shorter day), the FLEET assertion (a config change would re-point the number
    at a different fleet), the TWO INDEPENDENT TALLIES (a request the simulation
    made but did not count), and the fact that the literal was TRANSCRIBED from
    a run rather than reasoned and then written down.

    THE WINDOW MODEL, STATED RATHER THAN LEFT IMPLICIT. `monitor.run_once` asks
    its due retailers BACK TO BACK inside one pass — `results = [checker(w) for
    w in watches]`, with no sleep between them — so every request one pass makes
    is modelled here as falling inside one 60-second window, whatever their
    order inside it. That is a modelling claim and it carries its measurement:
    the last published WHOLE-pass figure is `duration_seconds: 20.43` for 13
    watches across all six retailers, read from `served/boty/status.json` on
    2026-08-31 by the phase-8 code review and QUOTED here rather than re-read
    (nothing in this phase reads or writes that file). A tick's due set is a
    subset of that pass, so a pass is comfortably inside 60 s on that one
    reading.

    THE RESIDUAL'S DIRECTION, because one reading is a bound and not a
    guarantee: if a pass ever exceeded 60 s, this model would OVER-count — some
    of that pass's requests would in truth fall into the next window. So the
    number below is an UPPER BOUND on the before-number, which is the safe
    direction for a number this phase must come in under. It cannot flatter the
    change.

    THE COUNT IS A COUNT OF RETAILERS, NOT OF REQUESTS. `run_once` dispatches
    one `Result` per WATCH and `record`s once per retailer; criterion 3 asks for
    "the maximum number of retailers requested", so the unit here is the
    retailer. The fleet carries 13 watches, so a window holding six retailers
    holds more than six HTTP requests. Stated because a later reader comparing
    this against a request count would be comparing two different things.

    THE RESTART ASSUMPTION. Zero restarts across the day. `due_at` is never
    persisted, so every process starts with all six retailers due at once —
    which is the t=0 burst this simulation counts. A restart mid-day would add
    another such burst, not remove one, so restarts cannot make this number
    smaller.
    """
    roster = tuple(sorted(_FLEET_INTERVALS))
    tick = loop_tick_seconds(_FLEET_DEFAULT_INTERVAL, roster)
    # BUILT AND STEPPED THE WAY `cli.watch_loop` BUILDS AND STEPS ONE. A pacer
    # constructed with neither field keeps today's tolerance and a zero offset by
    # design, so a simulation over a defaulted pacer would measure a schedule
    # nobody runs — and it would still read 6, which is how a green number can be
    # about the wrong code.
    p = Pacer(
        default_interval=_FLEET_DEFAULT_INTERVAL,
        overrides=dict(_FLEET_INTERVALS),
        roster=roster,
        tick=tick,
    )
    now = 0.0
    events: list[tuple[float, str]] = []
    per_retailer: dict[str, int] = dict.fromkeys(_FLEET_INTERVALS, 0)

    for _ in range(_ONE_DAY_OF_CYCLES):
        for retailer in sorted(_FLEET_INTERVALS):
            if p.due(retailer, now):
                events.append((now, retailer))
                per_retailer[retailer] += 1
                p.record(retailer, refused=False, now=now)
        now += tick

    times = [t for t, _ in events]
    max_in_any_60s = _max_in_any_window(times, _WINDOW_SECONDS)

    # 1. THE STATED LITERAL. Transcribed from a run, not reasoned.
    assert max_in_any_60s == _AFTER_MAX_IN_ANY_60S, (
        f"the schedule put {max_in_any_60s} of the six configured retailers "
        f"({', '.join(sorted(_FLEET_INTERVALS))}) inside a single 60-second "
        f"window at least once over a simulated day; the recorded after-number "
        f"for criterion 3 is the literal in this assertion"
    )

    # 1b. AND THE WORD IN CRITERION 3 IS *SMALLER*, WRITTEN OUT AS A COMPARISON.
    #     The left side is measured by the run above and the right side is a
    #     dated record, so this is a live gate on the new rule rather than a
    #     tautology over two literals: a change that pushed the maximum back up
    #     fails here even if somebody edited the after-literal to match it.
    assert max_in_any_60s < _BEFORE_MAX_IN_ANY_60S, (
        f"criterion 3 asks for a number SMALLER than the six the old rule "
        f"produced; this run put {max_in_any_60s} retailers in one 60-second "
        f"window against the recorded before-number of {_BEFORE_MAX_IN_ANY_60S}"
    )

    # 2. THE DENOMINATOR.
    assert now == float(_ONE_DAY_OF_SECONDS), (
        f"the simulated clock finished at {now} s, not the {_ONE_DAY_OF_SECONDS} s "
        f"that are one day — so the maximum above is a maximum over some other "
        f"window. A run that exited early presents a smaller maximum as a shorter "
        f"day, which is a reduction achieved by not asking rather than by spreading"
    )

    # 3. THE FLEET. The literal table must still describe what is configured.
    cfg = Config.load(_CONFIG)
    assert {w.retailer for w in cfg.watches} == set(_FLEET_INTERVALS), (
        f"{_CONFIG_SHOWN} configures watches on {sorted({w.retailer for w in cfg.watches})}, "
        f"but the number above is about {sorted(_FLEET_INTERVALS)}. A stated number "
        f"must not outlive the fleet it describes"
    )
    assert cfg.retailer_intervals == {
        r: i for r, i in _FLEET_INTERVALS.items() if i != cfg.interval_seconds
    }, (
        f"{_CONFIG_SHOWN} overrides {cfg.retailer_intervals}, but this table's non-default "
        f"cadences are {({r: i for r, i in _FLEET_INTERVALS.items() if i != cfg.interval_seconds})} "
        f"against a global interval_seconds of {cfg.interval_seconds}"
    )
    assert cfg.interval_seconds == _FLEET_DEFAULT_INTERVAL, (
        f"{_CONFIG_SHOWN} sets interval_seconds to {cfg.interval_seconds}, but this "
        f"simulation cycles every {_FLEET_DEFAULT_INTERVAL} s and calls that the "
        f"global cadence — the number above would be a number about some other loop"
    )
    assert all(
        i == cfg.interval_seconds
        for r, i in _FLEET_INTERVALS.items()
        if r not in cfg.retailer_intervals
    ), (
        f"a retailer with no override must sit on interval_seconds "
        f"({cfg.interval_seconds}); this table says {_FLEET_INTERVALS}"
    )

    # 4. TWO INDEPENDENT TALLIES. The recorded events, and each retailer's own
    #    count — cross-checked BOTH ways, and then against the cadence
    #    arithmetic the fleet table implies, which is derived from the config
    #    rather than from the loop and so is the genuinely independent one: a
    #    cycle the loop skipped shows up as a shortfall against it.
    assert len(events) == sum(per_retailer.values()), (
        f"{len(events)} recorded events against {sum(per_retailer.values())} "
        f"counted requests — a request was made and not counted, or counted and "
        f"not made"
    )
    assert per_retailer == _BEFORE_PER_RETAILER, (
        f"over the same simulated day each retailer was asked {per_retailer}, "
        f"against the {_BEFORE_PER_RETAILER} the OLD rule produced. A smaller "
        f"maximum bought with a smaller count is coverage sold for a number: the "
        f"reduction this phase claims is in coincidence, never in how often "
        f"anybody is asked"
    )
    for retailer, count in sorted(per_retailer.items()):
        observed = sum(1 for _, r in events if r == retailer)
        expected = _ONE_DAY_OF_SECONDS // _FLEET_INTERVALS[retailer]
        assert observed == count == expected, (
            f"{retailer} appears {observed} times in the event list, was counted "
            f"{count} times, and a {_FLEET_INTERVALS[retailer]}-second cadence over "
            f"{_ONE_DAY_OF_SECONDS} s implies {expected}. All three must agree or "
            f"the maximum above is a maximum over requests that were not all counted"
        )

    # 5. EVERY EVENT INSIDE THE WINDOW IT IS ATTRIBUTED TO.
    assert all(a <= b for a, b in pairwise(times)) and all(
        0.0 <= t < float(_ONE_DAY_OF_SECONDS) for t in times
    ), (
        f"the event times are not non-decreasing inside [0, {_ONE_DAY_OF_SECONDS}); "
        f"first {times[:3]}, last {times[-3:]} — a maximum is not a measurement if "
        f"the things counted could fall outside the window they are attributed to"
    )


# --------------------------------------------------------------------------
# REQ-23: two retailers at one cadence, out of lockstep — the tracer
# --------------------------------------------------------------------------
#
# ONE PATH END TO END before anything is generalised: two retailers at the same
# standing interval, through `loop_tick_seconds`, through `slot_offset`, through
# `_for`, through `due`, through `record`'s grid advance, driven by the jittered
# tick `cli.watch_loop` sleeps. The six-retailer number is further down; this is
# the path it stands on.
#
# THE SEPARATION IS ASSERTED ON THE SCHEDULE — the recorded next-attempt times —
# and never on elapsed time. Criterion 1 requires that in its own words, and the
# reason is visible in this test's own jitter: the wake TIMES wander by ±15% per
# cycle while the schedule does not move at all, so a bound read off the wall
# clock would be a bound on the sleep's randomness rather than on the schedule.

#: A deterministic jitter sequence. `cli.watch_loop` sleeps
#: `tick * random.uniform(0.85, 1.15)`, and this reproduces that band exactly
#: rather than approximating it with a fixed step — the convergence this test
#: exists to rule out was a convergence UNDER jitter, and a fixed step cannot
#: exhibit it. SEEDED, so a failure is reproducible and a passing run is not one
#: lucky draw; it is one jitter sequence and not a proof over all of them, which
#: is why the schedule assertions below are exact rather than statistical.
_TRACER_SEED = 20260901

#: Two retailers on ONE cadence — the case criterion 1 names. `config/products.yaml`
#: puts four retailers on its global `interval_seconds`; these two are the tracer's
#: slice of that group.
_TRACER_ROSTER = ("bestbuy", "walmart")
_TRACER_INTERVAL = 300.0


def test_two_retailers_at_one_cadence_are_born_apart_and_stay_apart() -> None:
    """The whole mechanism on one path: an offset that is a POSITION, held by the advance.

    THREE ASSERTIONS ABOUT THE SEPARATION AND ONE ABOUT THE COUNT, and the count
    is the one that makes the other three mean anything. Spreading two retailers
    by asking each of them less often would satisfy every separation assertion
    here and give away the coverage this project exists to provide — it is the
    reduction-by-not-asking move Phase 2 already caught this project making. So
    the day-long count is asserted against the cadence arithmetic
    `config/products.yaml` implies, derived from the interval rather than read
    back out of the schedule under test.

    WHY THE SEPARATION SURVIVES, stated so a reader can check it rather than
    trust it: `record` steps from the retailer's own previous due time, so the
    half-tick of grace `due` grants is not compounded into a drift. Under the old
    `now + wait` these two were handed the SAME next due time the first time they
    fired together and stayed merged from then on.
    """
    tick = loop_tick_seconds(_TRACER_INTERVAL, _TRACER_ROSTER)
    assert tick == 150.0, (
        f"two retailers on a {_TRACER_INTERVAL} s cadence should wake the loop "
        f"every {_TRACER_INTERVAL / 2} s; loop_tick_seconds says {tick}"
    )

    p = Pacer(
        default_interval=_TRACER_INTERVAL,
        roster=_TRACER_ROSTER,
        tick=tick,
    )
    a, b = _TRACER_ROSTER

    # 1. AT BIRTH. Nothing has fired yet, so this is the offset and nothing else.
    born = abs(p._for(a).due_at - p._for(b).due_at)
    assert born == tick, (
        f"the two were born {born} s apart on a {_TRACER_INTERVAL} s cadence with "
        f"a {tick} s tick — a starting offset of zero is the lockstep, whatever "
        f"the advance does afterwards"
    )

    rng = random.Random(_TRACER_SEED)
    now = 0.0
    fired: dict[str, int] = dict.fromkeys(_TRACER_ROSTER, 0)
    separations: list[float] = []
    early: float | None = None

    while now < float(_ONE_DAY_OF_SECONDS):
        for retailer in _TRACER_ROSTER:
            if p.due(retailer, now):
                # COUNTED AT THE GRID POINT BEING SERVED, NOT AT THE WAKE THAT
                # SERVES IT, and the difference is one request at the day
                # boundary — measured here, not assumed. `due` grants half a tick
                # of grace, so the first grid point of DAY TWO (t=86400) can be
                # dispatched by a wake in the last 75 s of day one: counted by
                # wake this run read `{'bestbuy': 289, 'walmart': 288}`, an
                # asymmetry produced entirely by where the final wake landed under
                # this seed. The cadence did not move and neither retailer was
                # asked more often; a day's count simply is not a whole number of
                # requests unless the day is cut at the same place the schedule
                # is. Cutting it on the grid point is what makes 288 an exact
                # number rather than a rounded one.
                position = p._for(retailer).due_at
                if position < float(_ONE_DAY_OF_SECONDS):
                    fired[retailer] += 1
                p.record(retailer, refused=False, now=now)
        separations.append(abs(p._for(a).due_at - p._for(b).due_at))
        if min(fired.values()) == 5 and early is None:
            # 2. AFTER EACH HAS BEEN ASKED SEVERAL TIMES — read here rather than
            #    at the end, because a schedule that decayed and then re-separated
            #    would pass an endpoint check.
            early = separations[-1]
        now += tick * rng.uniform(0.85, 1.15)

    assert early == tick, (
        f"after five requests each the two were {early} s apart, not {tick} — the "
        f"offset is being eroded, which is what a schedule re-anchored to the "
        f"cycle's clock does one cycle at a time"
    )

    # 3. AT THE END OF THE DAY, and at every cycle in between. The `set` is what
    #    makes this a statement about the WHOLE day rather than about its last
    #    moment: a single merged cycle anywhere in the day puts a second value in
    #    it, and the merge is absorbing, so one is all it takes.
    assert set(separations) == {tick}, (
        f"over a simulated day the separation took the values "
        f"{sorted(set(separations))}; it must be exactly {tick} at every cycle, "
        f"because a retailer that drifts into another's slot stays there"
    )

    # 4. AND NEITHER WAS ASKED LESS OFTEN FOR IT. Derived from the cadence, not
    #    read back out of the schedule under test.
    expected = _ONE_DAY_OF_SECONDS // int(_TRACER_INTERVAL)
    assert fired == dict.fromkeys(_TRACER_ROSTER, expected), (
        f"over one simulated day the two retailers were asked {fired}, against "
        f"the {expected} a {_TRACER_INTERVAL} s cadence implies. A separation "
        f"bought by asking less often is coverage sold for a number"
    )


def test_the_tracer_pair_publishes_the_cadence_it_published_before() -> None:
    """An offset is a POSITION, and this is the assertion that says so.

    `current_interval` is byte-unchanged in this phase and this test is what
    makes that a claim about behaviour rather than about a diff: at zero refusals
    and after refusals, both retailers publish exactly what they published before
    REQ-23 — the same numbers `_CADENCE_AFTER_N_REFUSALS` states for a 300 s
    standing interval.
    """
    p = Pacer(
        default_interval=_TRACER_INTERVAL,
        roster=_TRACER_ROSTER,
        tick=loop_tick_seconds(_TRACER_INTERVAL, _TRACER_ROSTER),
    )
    for retailer in _TRACER_ROSTER:
        assert p.current_interval(retailer) == 300.0, (
            f"{retailer} publishes {p.current_interval(retailer)} s at zero "
            f"refusals; an offset moved a cadence, which is the one thing it may "
            f"never do"
        )
    for retailer in _TRACER_ROSTER:
        for _ in range(3):
            p.record(retailer, refused=True, now=0.0)
        assert p.current_interval(retailer) == 2400.0, (
            f"{retailer} publishes {p.current_interval(retailer)} s after three "
            f"refusals, against the 2400 s the backoff has always produced at a "
            f"300 s standing interval"
        )


# --------------------------------------------------------------------------
# Criterion 1: a STATED separation in seconds, asserted on the schedule
# --------------------------------------------------------------------------
#
# Criterion 1, verbatim: "Two retailers whose intervals coincide are NOT
# dispatched inside the same short window; the bound is a stated number of
# seconds and is asserted on the schedule, never on a wall clock."
#
# NOTHING IN THIS SECTION READS A CLOCK. No `time.time()`, no
# `time.monotonic()`, no elapsed subtraction — the assertions read `due_at`,
# which is the schedule's own record of when each retailer may next be asked.
# The criterion says so in its own words and the reason is measurable: the wake
# times below wander by +/-15% per cycle while the schedule does not move at
# all, so a bound read off elapsed time would be a bound on the sleep's
# randomness. It would also pass on an idle host and flake on a loaded one,
# which is the least attributable failure this suite could produce.

#: CRITERION 1's BOUND, IN SECONDS, WRITTEN OUT BY HAND AND NOT COMPUTED.
#:
#: Fifty. At the six retailers `config/products.yaml` configures on a 300 s
#: global `interval_seconds`, `loop_tick_seconds` gives a 50 s tick and
#: `slot_offset` lays the slots at `index * tick` modulo each retailer's own
#: standing cadence, so the four retailers that share the 300 s cadence are born
#: at 50, 150, 200 and 250 s and the closest pair of them is 50 s apart.
#:
#: WRITTEN OUT FOR `_CADENCE_AFTER_N_REFUSALS`'s REASON, WHICH IS THE WHOLE
#: POINT OF THE LITERAL. Computing this from `loop_tick_seconds` at test time
#: would make the assertion a re-derivation of the code it checks — the code
#: agreeing with itself, which is a test that cannot fail. Written out, an edit
#: to the tick expression or to the slot arithmetic has to change this number BY
#: HAND, and that is the moment somebody notices that the separation two
#: retailers are guaranteed has moved.
#:
#: "AT LEAST", BECAUSE THAT IS WHAT THE CRITERION ASKS FOR. The schedule
#: measured on 2026-09-01 holds this separation exactly, at birth and at every
#: cycle of a simulated day; the gate below is `>=` because criterion 1 states a
#: bound and a future fleet with more room in it may exceed the bound without
#: being a regression. A schedule that fell BELOW it is the lockstep coming back.
_MIN_SEPARATION_SECONDS = 50.0

#: The jitter sequence these tests step by, seeded for the tracer's reason: a
#: failure is reproducible and a passing run is not one lucky draw. It is one
#: sequence and not a proof over all of them, which is why the assertions read
#: the schedule — where the numbers are exact — rather than the wake times.
_SEPARATION_SEED = 20260903


def _coinciding_pairs() -> list[tuple[str, str]]:
    """Every pair in `_FLEET_INTERVALS` whose STANDING intervals are equal.

    Criterion 1 is about retailers "whose intervals coincide" and nobody else:
    `amazon` at 1800 s and `gamestop` at 900 s share their cadence with no one,
    so a separation between them is not what the criterion bounds. Derived from
    the fleet table rather than written out a second time, so a config change
    that moved a retailer onto or off the default cadence cannot leave this
    test bounding a pair that no longer coincides.
    """
    return [
        (a, b)
        for a, b in combinations(sorted(_FLEET_INTERVALS), 2)
        if _FLEET_INTERVALS[a] == _FLEET_INTERVALS[b]
    ]


def _closest_coinciding(p: Pacer) -> tuple[float, str, str]:
    """The smallest gap between two coinciding retailers' NEXT-ATTEMPT TIMES.

    `p._for(r).due_at` and nothing else — the schedule's own record. Reaching
    through `_for` rather than `due` is deliberate: `due` answers a question
    about a moment, and criterion 1 is about the schedule at every moment.
    """
    gaps = [(abs(p._for(a).due_at - p._for(b).due_at), a, b) for a, b in _coinciding_pairs()]
    return min(gaps)


def test_two_retailers_at_one_cadence_are_separated_by_the_stated_number_of_seconds() -> None:
    """Criterion 1, on the fleet that is configured and under the pacer that ships.

    THE BOUND IS `_MIN_SEPARATION_SECONDS` — fifty seconds, written out by hand
    at its definition — and it is read off `due_at`, the recorded next-attempt
    time. Nothing here reads a wall clock; see this section's header for why the
    criterion forbids it in its own words.

    BUILT THE WAY `cli.watch_loop` BUILDS ONE, roster and tick present. That is
    the construction the daemon runs, and `09-02` measured what happens when a
    test asserts under the defaulted one instead: criterion 3's simulation went
    on reading 6 against code that no longer produced 6, because a `Pacer` with
    no roster keeps a zero offset by design. A separation asserted under the
    defaulted construction would be an assertion about a schedule nobody runs.

    THE CONTRAST CASE AT THE FOOT OF THIS TEST IS NOT A SECOND GATE, and its
    docstring says what it does and does not prove — see the comment there.

    AT BIRTH AND AFTER EACH HAS BEEN ASKED SEVERAL TIMES, because those are two
    different claims: the first is about `slot_offset`, the second is about
    `record`'s advance holding the position `slot_offset` set. A mechanism that
    started the retailers apart and let them drift together would satisfy the
    first alone, and that is exactly what `09-02` measured a birth offset doing
    without the grid advance (142.5 s against 150 on the tracer pair).
    """
    pairs = _coinciding_pairs()
    assert pairs, (
        f"no two of {sorted(_FLEET_INTERVALS)} share a standing interval, so this "
        f"test has no subject: criterion 1 bounds retailers WHOSE INTERVALS "
        f"COINCIDE, and there are none in {_FLEET_INTERVALS}"
    )

    roster = tuple(sorted(_FLEET_INTERVALS))
    tick = loop_tick_seconds(_FLEET_DEFAULT_INTERVAL, roster)
    p = Pacer(
        default_interval=_FLEET_DEFAULT_INTERVAL,
        overrides=dict(_FLEET_INTERVALS),
        roster=roster,
        tick=tick,
    )

    # 1. AT BIRTH. Nothing has been recorded, so this is `slot_offset` alone.
    born, a, b = _closest_coinciding(p)
    assert born >= _MIN_SEPARATION_SECONDS, (
        f"{a} and {b} both stand on a {_FLEET_INTERVALS[a]} s cadence and were "
        f"born {born} s apart on the schedule, against the "
        f"{_MIN_SEPARATION_SECONDS} s criterion 1 states. Two retailers at one "
        f"position are the lockstep, whatever the advance does afterwards"
    )

    # 2. AND AT EVERY CYCLE OF A SIMULATED DAY. Stepped by the jittered tick
    #    `cli.watch_loop` sleeps, because the convergence this rules out was a
    #    convergence UNDER jitter — a fixed step cannot exhibit it. The WAKE
    #    times are jittered; the assertion is on the schedule regardless.
    rng = random.Random(_SEPARATION_SEED)
    now = 0.0
    worst, worst_a, worst_b = born, a, b
    while now < float(_ONE_DAY_OF_SECONDS):
        for retailer in roster:
            if p.due(retailer, now):
                p.record(retailer, refused=False, now=now)
        gap, ga, gb = _closest_coinciding(p)
        if gap < worst:
            worst, worst_a, worst_b = gap, ga, gb
        now += tick * rng.uniform(0.85, 1.15)

    assert worst >= _MIN_SEPARATION_SECONDS, (
        f"over a simulated day the closest two coinciding retailers came was "
        f"{worst} s ({worst_a} and {worst_b}), against the "
        f"{_MIN_SEPARATION_SECONDS} s criterion 1 states. An offset eroded one "
        f"cycle at a time is what a schedule re-anchored to the cycle's clock "
        f"does, and the merge is absorbing: once they are together they stay"
    )

    # 3. THE CONTRAST, AND WHAT IT IS FOR. A `Pacer` built with neither field
    #    gives every retailer a 0.0 offset by design (`slot_offset`'s last
    #    paragraph), so this case is the ABSENCE of the mechanism rather than a
    #    second gate on it. It is here to show which behaviour comes from which
    #    field — the separation above is bought by `roster` and `tick`, and a
    #    reader who assumed it came from `record` alone would be wrong. It
    #    proves nothing about the schedule the daemon runs, and it is not
    #    evidence for criterion 1; the assertion above is.
    defaulted = Pacer(
        default_interval=_FLEET_DEFAULT_INTERVAL,
        overrides=dict(_FLEET_INTERVALS),
    )
    absent, da, db = _closest_coinciding(defaulted)
    assert absent == 0.0, (
        f"a pacer built with no roster and no tick put {da} and {db} {absent} s "
        f"apart; with no roster every offset is 0.0, so this construction is the "
        f"lockstep by design and a non-zero answer here means the defaults have "
        f"started doing something the {len(_FLEET_INTERVALS)} defaulted "
        f"construction sites in this file were not told about"
    )


# --------------------------------------------------------------------------
# Criterion 2: independence, asserted in BOTH directions
# --------------------------------------------------------------------------
#
# Criterion 2, verbatim: "Each retailer's next-attempt time is INDEPENDENT:
# changing one retailer's interval or backoff moves that retailer's schedule and
# no other's, asserted in both directions."
#
# TWO TESTS AND NOT ONE. The interval direction and the backoff direction fail
# for different reasons — one is `_standing_interval` and `slot_offset`, the
# other is `current_interval` and the refusal arm — and a combined test would
# name the wrong one in its failure message. The cost of the second test is a
# duplicated fixture; the cost of combining them is a red that points at the
# wrong half of the mechanism.
#
# EACH ASSERTS THE NEGATIVE HALF EXPLICITLY, FIELD BY FIELD. "Changing X moved
# X" is compatible with a change that moved everything, so every untouched
# retailer's whole recorded state is captured before the change and compared
# after it. Inferring independence from the positive half alone is the failure
# mode this criterion names in its own words.
#
# WHY INDEPENDENCE IS AVAILABLE TO ASSERT AT ALL, in one sentence: `record`
# steps each retailer from its OWN previous due time rather than from the
# cycle's clock, so nothing one retailer does can re-anchor another.
#
# WHY THESE ARE NOT `test_an_override_does_not_affect_other_retailers` AGAIN.
# That test (above, unchanged) builds a DEFAULTED pacer, overrides `amazon`, and
# asserts that `walmart` is still due every cycle. Three things it does not do,
# and each is why a second test earns its place rather than raising the count:
# it asserts DUENESS at a moment rather than the recorded NEXT-ATTEMPT TIME; it
# never runs the same scenario WITHOUT the override, so it cannot tell "walmart
# was unaffected" from "walmart would have looked like that either way"; and it
# builds the construction the daemon does not run. It is kept as it is — it
# guards the coverage half, which these do not.

#: The wake sequence both directions are stepped by. Long enough that every
#: retailer in the fleet has been dispatched several times (the 1800 s one needs
#: 36 wakes at a 50 s tick), short enough to stay a unit test.
_INDEPENDENCE_WAKES = 400
_INDEPENDENCE_SEED = 20260904


def _shipping_pacer(overrides: dict[str, int]) -> tuple[Pacer, tuple[str, ...]]:
    """A `Pacer` built the way `cli.watch_loop` builds one, over the real fleet.

    The ROSTER is the configured retailers and the TICK is derived from it, so
    changing an override cannot change either — which is what makes the
    comparison below a comparison of one variable.
    """
    roster = tuple(sorted(_FLEET_INTERVALS))
    return (
        Pacer(
            default_interval=_FLEET_DEFAULT_INTERVAL,
            overrides=dict(overrides),
            roster=roster,
            tick=loop_tick_seconds(_FLEET_DEFAULT_INTERVAL, roster),
        ),
        roster,
    )


def _trajectory(
    p: Pacer, roster: tuple[str, ...], *, refusing: frozenset[str]
) -> dict[str, list[tuple[float, float, int, float]]]:
    """Every retailer's recorded state after every wake — the WHOLE run, not its end.

    ALL FOUR FIELDS of `_RetailerState` and not just `due_at`: criterion 2 is
    about the next-attempt time, but a change that left `due_at` alone while
    moving another retailer's `interval` or `refusals` would move its next
    attempt one cycle later. Comparing the whole record catches it now rather
    than then.

    AND EVERY WAKE, NOT THE LAST ONE, WHICH WAS A MEASURED CORRECTION RATHER
    THAN A PRECAUTION. This helper first captured the state once, at the end of
    the run. Perturbing `record`'s refusal arm to increment EVERY retailer's
    count — a fleet-wide refusal counter, which is precisely the leak the
    negative half below exists to catch — left both tests GREEN: the untouched
    retailers are dispatched often enough that their own next `record(refused=
    False)` resets the count to 0 before the run ends, so the defect was live
    for most of the day and invisible at the moment it was read. An end-state
    comparison is blind to anything that heals. The trajectory is not.

    The wake sequence is SEEDED IDENTICALLY for every call, so two runs differ
    only by the argument that was changed. The jitter is the loop's own band;
    the assertions read the schedule, never these wake times.
    """
    rng = random.Random(_INDEPENDENCE_SEED)
    tick = loop_tick_seconds(_FLEET_DEFAULT_INTERVAL, roster)
    now = 0.0
    seen: dict[str, list[tuple[float, float, int, float]]] = {r: [] for r in roster}
    for _ in range(_INDEPENDENCE_WAKES):
        for retailer in roster:
            if p.due(retailer, now):
                p.record(retailer, refused=retailer in refusing, now=now)
        for retailer in roster:
            st = p._for(retailer)
            seen[retailer].append((st.due_at, st.interval, st.refusals, st.refused_at))
        now += tick * rng.uniform(0.85, 1.15)
    return seen


def _first_divergence(
    left: list[tuple[float, float, int, float]], right: list[tuple[float, float, int, float]]
) -> int | None:
    """The wake index where two trajectories first differ, or `None` if they never do.

    Reported rather than the whole list, because a 400-wake diff in a failure
    message is a wall of numbers and the useful fact is WHEN a retailer moved:
    the first wake is the one the cause is at.
    """
    for i, (a, b) in enumerate(zip(left, right, strict=True)):
        if a != b:
            return i
    return None


def test_changing_one_retailers_interval_moves_that_retailers_schedule_and_no_other() -> None:
    """Criterion 2, the interval direction — positive half AND negative half.

    `gamestop` carries a 900 s override in `config/products.yaml`; the second run
    below moves it to 600 s and changes nothing else. Its own next-attempt time
    must move, and the other five retailers' recorded state must be EQUAL to
    what it was, field by field.

    600 rather than an arbitrary number, and the reason is worth stating:
    `slot_offset` lays gamestop's position at `index * tick` modulo its standing
    cadence, and 100 s is inside both 900 and 600, so its BIRTH POSITION is
    identical under both intervals. The only thing this test changes is the
    advance — which is the thing criterion 2 is about.

    THE NEGATIVE HALF IS THE POINT. See this section's header for why it is not
    inferred from the positive one, and for why this is not a second copy of
    `test_an_override_does_not_affect_other_retailers`.
    """
    changed_retailer = "gamestop"
    assert _FLEET_INTERVALS[changed_retailer] == 900, (
        f"this test moves {changed_retailer} from 900 s to 600 s and the fleet "
        f"table now says {_FLEET_INTERVALS[changed_retailer]} s — the comparison "
        f"below would be between two intervals neither of which is configured"
    )

    base, roster = _shipping_pacer(_FLEET_INTERVALS)
    before = _trajectory(base, roster, refusing=frozenset())

    moved, _ = _shipping_pacer({**_FLEET_INTERVALS, changed_retailer: 600})
    after = _trajectory(moved, roster, refusing=frozenset())

    # THE POSITIVE HALF: the retailer whose interval changed moved.
    assert _first_divergence(before[changed_retailer], after[changed_retailer]) is not None, (
        f"{changed_retailer}'s interval was changed from "
        f"{_FLEET_INTERVALS[changed_retailer]} s to 600 s and its schedule did "
        f"not move at any of the {_INDEPENDENCE_WAKES} wakes — its next attempt "
        f"is still recorded at {after[changed_retailer][-1][0]} s. The configured "
        f"cadence is not reaching the schedule at all"
    )

    # THE NEGATIVE HALF, FIELD BY FIELD, AT EVERY WAKE, FOR EVERY RETAILER THAT
    # WAS NOT TOUCHED.
    for retailer in roster:
        if retailer == changed_retailer:
            continue
        at = _first_divergence(before[retailer], after[retailer])
        assert at is None, (
            f"changing {changed_retailer}'s interval moved {retailer} as well: at "
            f"wake {at} its (due_at, interval, refusals, refused_at) went "
            f"{before[retailer][at]} -> {after[retailer][at]} over the same wake "
            f"sequence. Each retailer's next attempt is stepped from its OWN "
            f"previous due time, so a change to one may not re-anchor another"
        )


def test_driving_one_retailer_into_backoff_moves_that_retailers_schedule_and_no_other() -> None:
    """Criterion 2, the backoff direction — positive half AND negative half.

    The same fleet, the same wake sequence, and one retailer refusing every time
    it is asked. Its next attempt must be pushed out; nobody else's recorded
    state may move by so much as a field.

    A SEPARATE TEST FROM THE INTERVAL DIRECTION, deliberately. This one fails
    when `record`'s refusal arm or `current_interval` is wrong; the other fails
    when `_standing_interval` or `slot_offset` is wrong. One test carrying both
    would report whichever assertion happened to be written first, which is the
    least useful thing a failure message can do.

    THIS IS ALSO THE DIRECTION WITH A LIVE STAKE. A refusal is the one event that
    lengthens a wait, so a mechanism that let a backoff leak into the fleet would
    quietly stop asking retailers that had never refused us — coverage lost to a
    penalty they did not earn, which is the failure this project exists to
    notice rather than commit.
    """
    refused_retailer = "gamestop"

    base, roster = _shipping_pacer(_FLEET_INTERVALS)
    calm = _trajectory(base, roster, refusing=frozenset())

    backed_off, _ = _shipping_pacer(_FLEET_INTERVALS)
    penalised = _trajectory(backed_off, roster, refusing=frozenset({refused_retailer}))

    # THE POSITIVE HALF: the refusing retailer's next attempt was pushed OUT.
    assert penalised[refused_retailer][-1][0] > calm[refused_retailer][-1][0], (
        f"{refused_retailer} refused us at every dispatch and its next attempt is "
        f"recorded at {penalised[refused_retailer][-1][0]} s against the "
        f"{calm[refused_retailer][-1][0]} s of the run where it answered — a "
        f"backoff that does not push the next attempt out is not a backoff"
    )
    assert penalised[refused_retailer][-1][2] > 0, (
        f"{refused_retailer} refused at every dispatch and its recorded refusal "
        f"count is {penalised[refused_retailer][-1][2]} — the run did not "
        f"exercise the arm this test is about"
    )

    # THE NEGATIVE HALF, FIELD BY FIELD, AT EVERY WAKE, FOR EVERY RETAILER THAT
    # ANSWERED.
    for retailer in roster:
        if retailer == refused_retailer:
            continue
        at = _first_divergence(calm[retailer], penalised[retailer])
        assert at is None, (
            f"{refused_retailer}'s backoff moved {retailer} as well: at wake {at} "
            f"its (due_at, interval, refusals, refused_at) went {calm[retailer][at]} "
            f"-> {penalised[retailer][at]} over the same wake sequence. A penalty "
            f"one retailer earned may not be served to a retailer that answered"
        )
