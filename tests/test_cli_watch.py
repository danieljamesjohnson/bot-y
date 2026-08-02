"""The watch loop: what happens when delivery fails, and when checking fails.

Alerts here are edge-triggered, which makes the loop's error handling part of
the product rather than housekeeping. `run_once` commits the transition to
`state.seen` and saves it *before* the caller gets a chance to deliver
anything, so a notification that does not arrive is not a retry — it is a drop
that will never be mentioned again. The monitor goes on looking healthy: the
status page is green, the log has nothing in it, and the next cycle compares
against a remembered "in_stock" and stays quiet.

The same shape applies one level up. A cycle that raises every time leaves the
systemd unit `active (running)` forever while nothing is monitored, because the
handler catches everything and continues.

Both are tested through `watch_loop` with a bounded cycle count, so a sequence
of polls is the unit — the loop's whole failure mode is what it does on the
cycle *after* something went wrong.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from boty import cli
from boty.config import Config
from boty.models import Availability, Health, Result, Watch
from boty.monitor import State

WATCH = Watch(name="goplusplus", retailer="gamestop", target="https://x/1")
KEY = "gamestop:goplusplus"


@pytest.fixture
def cfg(tmp_path: Path) -> Config:
    return Config(
        watches=[WATCH],
        notify_urls=["tgram://token/chat"],
        interval_seconds=300,
        state_path=tmp_path / "state.json",
        status_path=tmp_path / "status.json",
    )


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> dict[str, list]:
    """Capture notification attempts and let each test choose the outcome."""
    record: dict[str, list] = {"restock": [], "health": [], "restock_ok": [], "health_ok": []}

    def _restock(urls: list[str], results: list[Result]) -> bool:
        record["restock"].append([r.watch.name for r in results])
        return record["restock_ok"].pop(0) if record["restock_ok"] else True

    def _health(urls: list[str], unhealthy: list[Health]) -> bool:
        record["health"].append([h.retailer for h in unhealthy])
        return record["health_ok"].pop(0) if record["health_ok"] else True

    monkeypatch.setattr(cli, "send_restock", _restock)
    monkeypatch.setattr(cli, "send_health_warning", _health)
    return record


def _checker(*availabilities: Availability):
    """A checker that returns each availability in turn, then repeats the last."""
    remaining = list(availabilities)

    def check(watch: Watch) -> Result:
        current = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        return Result(watch, current, price=54.99, detail="synthetic")

    return check


# --------------------------------------------------------------------------
# WR-06: a failed notification must not consume the alert
# --------------------------------------------------------------------------


def test_a_failed_restock_notification_is_retried_next_cycle(
    cfg: Config, sent: dict[str, list], tmp_path: Path
) -> None:
    """Delivery failing must not spend the edge.

    `run_once` records the transition and saves before delivery is attempted,
    so once "in_stock" is in the memory the alert is gone: the next cycle sees
    no transition and says nothing. Telegram rate-limiting for one cycle would
    therefore cost the drop outright, silently, with a green dashboard — which
    is precisely the failure this project exists to make impossible.

    Rolling the memory back on a failed send turns a lost alert into a retry.
    """
    sent["restock_ok"] = [False, True]
    state = State.load(cfg.state_path)

    cli.watch_loop(cfg, _checker(Availability.IN_STOCK), state, cycles=2, sleep=lambda s: None)

    assert sent["restock"] == [["goplusplus"], ["goplusplus"]], (
        "the alert was delivered once, failed, and was never attempted again — "
        "the transition had already been committed to state"
    )


def test_a_failed_restock_notification_rolls_the_memory_back(
    cfg: Config, sent: dict[str, list]
) -> None:
    """The retry above works by un-remembering, so assert that directly."""
    sent["restock_ok"] = [False]
    state = State.load(cfg.state_path)

    cli.watch_loop(cfg, _checker(Availability.IN_STOCK), state, cycles=1, sleep=lambda s: None)

    assert KEY not in state.seen, (
        "an undelivered alert must leave no trace of the transition, or the "
        "next cycle will treat the unchanged in-stock reading as old news"
    )
    assert State.load(cfg.state_path).seen == state.seen, "the rollback must reach disk too"


def test_a_delivered_restock_notification_is_not_repeated(
    cfg: Config, sent: dict[str, list]
) -> None:
    """The rollback must be conditional. Alerts stay edge-triggered."""
    state = State.load(cfg.state_path)

    cli.watch_loop(cfg, _checker(Availability.IN_STOCK), state, cycles=3, sleep=lambda s: None)

    assert sent["restock"] == [["goplusplus"]], "a delivered alert must fire exactly once"
    assert state.seen == {KEY: "in_stock"}


def test_a_failed_health_warning_is_retried_next_cycle(
    cfg: Config, sent: dict[str, list]
) -> None:
    """`warned` had the same defect as `state.seen`, for the same reason.

    It was updated from `health` regardless of whether the warning was
    delivered, so a broken detector could be reported once, fail to send, and
    never be mentioned again — the "tells you when it breaks" promise silently
    voided.
    """
    # No control watch for gamestop, so assess_health reports it unhealthy.
    sent["health_ok"] = [False, True]
    state = State.load(cfg.state_path)

    cli.watch_loop(cfg, _checker(Availability.OUT_OF_STOCK), state, cycles=2, sleep=lambda s: None)

    assert sent["health"] == [["gamestop"], ["gamestop"]], (
        "the health warning was not delivered, but the retailer was marked as "
        "already warned, so the retry never happened"
    )


def test_a_delivered_health_warning_is_not_repeated_every_cycle(
    cfg: Config, sent: dict[str, list]
) -> None:
    """Once per failure episode, not once per poll — the reason `warned` exists."""
    state = State.load(cfg.state_path)

    cli.watch_loop(cfg, _checker(Availability.OUT_OF_STOCK), state, cycles=3, sleep=lambda s: None)

    assert sent["health"] == [["gamestop"]]


def test_watch_refuses_to_start_with_nothing_to_notify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`notify: [${BOTY_NOTIFY_URL}]` with the variable unset yields [].

    `send_restock` returns False immediately on an empty URL list without
    logging anything, so the loop would run forever, find the restock, and tell
    nobody — indistinguishable from a working monitor right up until the drop
    is missed. Refusing to start is the only honest answer.
    """
    config = tmp_path / "products.yaml"
    config.write_text(
        "watches:\n"
        "  - name: goplusplus\n"
        "    retailer: gamestop\n"
        "    target: https://x/1\n",
        encoding="utf-8",
    )

    assert cli.main(["watch", "-c", str(config)]) == 2
    assert "tell nobody" in capsys.readouterr().err
