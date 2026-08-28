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
import time
from itertools import pairwise
from pathlib import Path

import pytest

from boty.fetch import Blocked, FetchError, is_refusal
from boty.models import Availability, Health, Result, Watch
from boty.monitor import CAUSE_UNKNOWN, State, assess_health, run_once
from boty.pacing import (
    MAX_BACKOFF_SECONDS,
    MAX_PERSISTED_REFUSALS,
    REFUSALS_BEFORE_COOLOFF,
    STATE_MAX_AGE_SECONDS,
    STATE_VERSION,
    Pacer,
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
    """
    p = Pacer(default_interval=300)
    now = 0.0
    for _ in range(REFUSALS_BEFORE_COOLOFF - 1):
        p.record("amazon", refused=True, now=now)
    assert p._for("amazon").due_at - now == MAX_BACKOFF_SECONDS
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
    retailer under-polled for no reason."""
    p = Pacer(default_interval=300)
    for _ in range(5):
        p.record("amazon", refused=True, now=0.0)
    p.record("amazon", refused=False, now=0.0)
    assert p._for("amazon").refusals == 0
    assert p._for("amazon").due_at == 300


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

    The loop sleeps `interval` WITH jitter, so a strict `now >= due_at` skips a
    default-cadence retailer roughly half the time — for no reason, since this
    class exists to stretch intervals beyond the loop's, never to drop cycles
    from a retailer keeping to it.
    """
    p = Pacer(default_interval=300)
    now = 0.0
    for cycle in range(20):
        assert p.due("walmart", now), f"walmart not due at cycle {cycle} (t={now})"
        p.record("walmart", refused=False, now=now)
        now += 300 * 0.86  # a short-jitter cycle, the adversarial case


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
    """
    p = Pacer(default_interval=interval)
    now = 0.0

    for refusals, seconds in enumerate(expected[1:], start=1):
        p.record("amazon", refused=True, now=now)
        assert p._for("amazon").due_at == now + seconds, (
            f"refusal {refusals} scheduled the next attempt at "
            f"{p._for('amazon').due_at - now}s, not {seconds}s — the fetch "
            f"schedule moved, and nothing in REQ-21 is allowed to move it"
        )

    p.record("amazon", refused=False, now=now)
    assert p._for("amazon").due_at == now + interval, (
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
    """
    p = Pacer(default_interval=300, overrides={"amazon": 1800})
    for _ in range(REFUSALS_BEFORE_COOLOFF):
        p.record("amazon", refused=True, now=0.0)
    assert p.current_interval("amazon") == 259200.0, (
        "the setup never reached cool-off depth, so what follows would be a "
        "recovery from the cap and not from a cool-off"
    )

    p.record("amazon", refused=False, now=0.0)

    assert p._for("amazon").refusals == 0
    assert p.current_interval("amazon") == 1800.0
    assert p._for("amazon").due_at == 1800.0


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
    process. Leaving it at 0.0 also KEEPS the withdrawn docstring's concession —
    a restart still tries once at full rate.
    """
    path = tmp_path / "pacer-state.json"
    first = _pacer(path)
    for _ in range(5):
        first.record("amazon", refused=True, now=0.0)
    assert first._for("amazon").due_at > 0, "the writing pacer really did have a schedule"
    first.save(set())

    second = _pacer(path)
    second.load()

    assert second._for("amazon").due_at == 0.0, (
        "a due_at came back from disk. It was measured against a clock that no "
        "longer exists, so it is not a schedule — it is an accident"
    )
    assert second.due("amazon", 0.0), "a restart must still try once, immediately"


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
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=5, age=STATE_MAX_AGE_SECONDS + 1))

    p = _pacer(path)
    p.load()

    assert p._for("amazon").refusals == 0, (
        "state older than one full cap-length window was applied — it has "
        "outlived the reasoning that produced it"
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
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=1, age=1.0, warned_age=STATE_MAX_AGE_SECONDS + 1))

    assert _pacer(path).load() == set(), (
        "a paging memory older than one full cap-length window was restored — the "
        "retailer it names can never be paged about again"
    )


def test_a_paging_memory_younger_than_the_cap_is_restored(tmp_path: Path) -> None:
    """Bounded on both sides, so the age-out cannot pass by discarding everything.

    Discarding every entry would restore REQ-16's "pushed once per process" from
    the other end, which is the regression M13 exists to catch.
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
    """Bounded on both sides, so the age-out cannot pass by discarding everything."""
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
    p.record("amazon", refused=True, now=0.0)  # must not raise
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


def test_the_age_out_is_derived_from_the_backoff_cap() -> None:
    """Derived, not re-chosen, so the two can never drift apart.

    The cap already IS this project's written answer to how long a refusal stays
    evidence; a second number here would be a second answer to the same question.
    """
    assert STATE_MAX_AGE_SECONDS == MAX_BACKOFF_SECONDS


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
