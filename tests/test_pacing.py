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
"""

from __future__ import annotations

from pathlib import Path

import pytest

from boty.fetch import Blocked, FetchError, is_refusal
from boty.models import Availability, Health, Result, Watch
from boty.monitor import State, assess_health, run_once
from boty.pacing import BACKOFF_FACTOR, MAX_BACKOFF_SECONDS, Pacer


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
    assert "probably fine" in health.reason, (
        f"a refusal is reported as {health.reason!r} — telling the reader the "
        f"detector is probably broken is false, and it is what made this alert "
        f"channel unreadable"
    )


def test_a_genuinely_broken_control_still_says_so_loudly() -> None:
    """The other direction. Backing off must not have muffled the real alarm."""
    (health,) = assess_health([_broken(_w("gamestop"))])
    assert not health.ok and not health.refused
    assert "probably broken" in health.reason
    assert "missed silently" in health.reason


def test_one_non_refusal_among_refusals_is_treated_as_breakage() -> None:
    """`all`, not `any` — the louder reading is the safe one.

    If a retailer's controls are mostly walled but one failed for a reason that
    is NOT a refusal, something may really be broken, and calling the whole
    retailer 'just rate-limited' would bury it.
    """
    w1, w2 = _w("gamestop", "a"), _w("gamestop", "b")
    (health,) = assess_health([_refused(w1), _broken(w2)])
    assert not health.refused, "a non-refusal among refusals must not be swallowed"
    assert "probably broken" in health.reason


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
