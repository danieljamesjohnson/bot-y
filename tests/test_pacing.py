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
from pathlib import Path

import pytest

from boty.fetch import Blocked, FetchError, is_refusal
from boty.models import Availability, Health, Result, Watch
from boty.monitor import CAUSE_UNKNOWN, State, assess_health, run_once
from boty.pacing import (
    MAX_BACKOFF_SECONDS,
    MAX_PERSISTED_REFUSALS,
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
    p = Pacer(default_interval=300)
    now = 0.0
    for _ in range(30):
        p.record("amazon", refused=True, now=now)
    assert p._for("amazon").due_at - now == MAX_BACKOFF_SECONDS
    assert MAX_BACKOFF_SECONDS <= 6 * 60 * 60, "a cap beyond a few hours is not a monitor"


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


def test_run_once_without_a_pacer_is_unchanged(tmp_path: Path) -> None:
    """Every existing caller passes no pacer and must behave exactly as before."""
    watches = [_w("walmart"), _w("amazon")]
    state = State(tmp_path / "state.json", {})
    results, health, _ = run_once(watches, _ok, state)
    assert len(results) == 2 and len(health) == 2


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


def _document(refusals: int, age: float, warned: list[str] | None = None) -> str:
    return json.dumps(
        {
            "version": STATE_VERSION,
            "retailers": {"amazon": {"refusals": refusals, "refused_at": time.time() - age}},
            "warned": warned or [],
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
    """
    path = tmp_path / "pacer-state.json"
    path.write_text(_document(refusals=10**9, age=1.0))

    p = _pacer(path)
    p.load()

    assert p._for("amazon").refusals == MAX_PERSISTED_REFUSALS
    p.record("amazon", refused=True, now=0.0)  # must not raise
    assert p._for("amazon").due_at == MAX_BACKOFF_SECONDS


def test_the_clamp_stays_above_the_paging_threshold() -> None:
    """Imported from both modules, because `pacing` must not import `cli`.

    A clamp at or below REFUSALS_BEFORE_PAGING would mean persistence silently
    defeated the paging clause it exists to serve.
    """
    from boty.cli import REFUSALS_BEFORE_PAGING

    assert MAX_PERSISTED_REFUSALS >= REFUSALS_BEFORE_PAGING


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
