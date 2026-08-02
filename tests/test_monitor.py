"""Detector health, and edge-triggered alerting with a memory that survives UNKNOWN.

Both behaviours here exist because of the same failure: a monitor that looks
healthy while being broken.

`assess_health` refuses to call a retailer healthy on the strength of its
product watches alone. Only a control — an item known to be in stock — can say
the detector still works, and a retailer with no control is reported unhealthy
rather than assumed fine.

`State.transitioned_to_stock` is edge-triggered, and UNKNOWN never overwrites
what it remembers. One blocked fetch resetting the memory would produce a
duplicate alert on the next successful check, and an alert stream you learn to
distrust is worse than no alert stream.

No fixtures needed — these are hand-built Results.
"""

from __future__ import annotations

from pathlib import Path

from boty.models import Availability, Result, Watch
from boty.monitor import State, assess_health, run_once


def _result(
    availability: Availability,
    *,
    retailer: str = "gamestop",
    name: str = "thing",
    control: bool = False,
    price: float | None = None,
    max_price: float | None = None,
) -> Result:
    watch = Watch(
        name=name,
        retailer=retailer,
        target=f"https://{retailer}.example/{name}",
        max_price=max_price,
        control=control,
    )
    return Result(watch, availability, price=price, detail="synthetic")


def _health_for(results: list[Result], retailer: str):
    (found,) = [h for h in assess_health(results) if h.retailer == retailer]
    return found


# --------------------------------------------------------------------------
# assess_health
# --------------------------------------------------------------------------


def test_control_in_stock_is_healthy() -> None:
    results = [
        _result(Availability.OUT_OF_STOCK, name="goplusplus"),
        _result(Availability.IN_STOCK, name="ps5", control=True),
    ]
    assert _health_for(results, "gamestop").ok is True


def test_control_out_of_stock_means_the_detector_is_broken() -> None:
    """The detector-broken alarm.

    A control is an item that is always in stock. If it reads OUT_OF_STOCK the
    honest conclusion is not "the retailer sold out of milk" — it is "we can no
    longer read this site", and every product verdict alongside it is suspect.
    """
    results = [
        _result(Availability.OUT_OF_STOCK, name="goplusplus"),
        _result(Availability.OUT_OF_STOCK, name="ps5", control=True),
    ]
    health = _health_for(results, "gamestop")

    assert health.ok is False
    assert health.failing_controls
    assert "ps5" in health.failing_controls[0]


def test_control_unknown_is_also_unhealthy() -> None:
    """UNKNOWN on a control is just as disqualifying as a wrong answer."""
    results = [_result(Availability.UNKNOWN, name="ps5", control=True)]
    health = _health_for(results, "gamestop")

    assert health.ok is False
    assert health.failing_controls


def test_retailer_with_no_control_watch_is_unhealthy() -> None:
    """An unverified detector is treated as broken, deliberately.

    Nothing is known to be wrong — but nothing is known at all, and "we have
    never checked" must not read the same as "we checked and it was fine".
    """
    results = [
        _result(Availability.OUT_OF_STOCK, retailer="target", name="goplusplus"),
        _result(Availability.IN_STOCK, retailer="target", name="something-else"),
    ]
    health = _health_for(results, "target")

    assert health.ok is False
    assert "control" in health.reason
    assert health.failing_controls == []


def test_health_is_reported_per_retailer() -> None:
    results = [
        _result(Availability.IN_STOCK, retailer="gamestop", name="ps5", control=True),
        _result(Availability.OUT_OF_STOCK, retailer="walmart", name="milk", control=True),
    ]
    health = {h.retailer: h.ok for h in assess_health(results)}

    assert health == {"gamestop": True, "walmart": False}


# --------------------------------------------------------------------------
# State — edge-triggered alerting
# --------------------------------------------------------------------------


def test_first_in_stock_sighting_transitions(tmp_path: Path) -> None:
    state = State.load(tmp_path / "state.json")
    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is True


def test_second_consecutive_in_stock_does_not_transition(tmp_path: Path) -> None:
    """Alerts are edge-triggered, not level-triggered.

    You want to be told when something *becomes* available, not once a minute
    for as long as it stays available.
    """
    state = State.load(tmp_path / "state.json")
    first = _result(Availability.IN_STOCK)

    assert state.transitioned_to_stock(first) is True
    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is False


def test_out_of_stock_then_in_stock_transitions_again(tmp_path: Path) -> None:
    state = State.load(tmp_path / "state.json")

    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is True
    assert state.transitioned_to_stock(_result(Availability.OUT_OF_STOCK)) is False
    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is True


def test_unknown_does_not_overwrite_remembered_state(tmp_path: Path) -> None:
    """A blocked fetch must not cause a spurious re-alert on recovery.

    IN_STOCK, then UNKNOWN, then IN_STOCK again is one continuous in-stock
    period interrupted by a failed check. If UNKNOWN cleared the memory, the
    third reading would look like a fresh restock and fire a duplicate alert —
    and duplicate alerts are how you learn to ignore the notifications.
    """
    state = State.load(tmp_path / "state.json")

    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is True
    assert state.transitioned_to_stock(_result(Availability.UNKNOWN)) is False
    assert state.seen["gamestop:thing"] == Availability.IN_STOCK.value
    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is False


def test_state_survives_a_save_and_reload(tmp_path: Path) -> None:
    """The memory has to outlive the process — the monitor runs as a service."""
    path = tmp_path / "nested" / "state.json"
    state = State.load(path)
    state.transitioned_to_stock(_result(Availability.IN_STOCK))
    state.save()

    assert State.load(path).transitioned_to_stock(_result(Availability.IN_STOCK)) is False


def test_unreadable_state_file_starts_empty(tmp_path: Path) -> None:
    """A corrupt state file must not crash the service on boot."""
    path = tmp_path / "state.json"
    path.write_text("{ not json")

    assert State.load(path).seen == {}


# --------------------------------------------------------------------------
# run_once — the pieces wired together
# --------------------------------------------------------------------------


def test_run_once_alerts_on_products_only_and_records_controls(tmp_path: Path) -> None:
    """Controls are canaries, not shopping list items — they never alert.

    Their state is still recorded, so that flipping a watch from control to
    product later does not fire a phantom "restock".
    """
    product = Watch(name="goplusplus", retailer="gamestop", target="https://x/1")
    control = Watch(name="ps5", retailer="gamestop", target="https://x/2", control=True)

    def checker(watch: Watch) -> Result:
        return Result(watch, Availability.IN_STOCK, price=54.99, detail="synthetic")

    state = State.load(tmp_path / "state.json")
    results, health, alerts = run_once([product, control], checker, state)

    assert len(results) == 2
    assert [h.ok for h in health] == [True]
    assert [a.watch.name for a in alerts] == ["goplusplus"]
    assert state.seen["gamestop:ps5"] == Availability.IN_STOCK.value

    # Second pass: nothing changed, so nothing alerts.
    _, _, alerts_again = run_once([product, control], checker, state)
    assert alerts_again == []


def test_run_once_does_not_alert_above_the_price_ceiling(tmp_path: Path) -> None:
    watch = Watch(name="goplusplus", retailer="walmart", target="https://x/1", max_price=80)

    def checker(w: Watch) -> Result:
        return Result(w, Availability.IN_STOCK, price=229.99, detail="reseller")

    state = State.load(tmp_path / "state.json")
    _, _, alerts = run_once([watch], checker, state)

    assert alerts == []
