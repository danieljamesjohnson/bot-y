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

import json
import re
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


# --------------------------------------------------------------------------
# WR-08: a permanently broken monitor must not look alive
# --------------------------------------------------------------------------


def _explodes(exc: Exception, *, after: int = 0):
    """A checker that succeeds `after` times, then raises forever."""
    calls = {"n": 0}

    def check(watch: Watch) -> Result:
        calls["n"] += 1
        if calls["n"] > after:
            raise exc
        return Result(watch, Availability.OUT_OF_STOCK, detail="synthetic")

    return check


def test_a_transient_failure_is_tolerated(cfg: Config, sent: dict[str, list]) -> None:
    """One bad cycle is normal — a timeout, a hiccup. Keep going, stay quiet."""
    state = State.load(cfg.state_path)

    rc = cli.watch_loop(
        cfg, _explodes(RuntimeError("boom"), after=1), state, cycles=2, sleep=lambda s: None
    )

    assert rc == 0
    assert sent["health"] == [["gamestop"]], "only the ordinary no-control warning"


def test_three_consecutive_failures_are_announced(cfg: Config, sent: dict[str, list]) -> None:
    """The failure mode this project exists to eliminate, one level up.

    Under systemd a loop that catches everything leaves the unit `active
    (running)` forever: the process never exits non-zero, the health-warning
    call is itself inside the `try` so it never runs, and status.json keeps
    serving whatever it last held. A stale green dashboard over a monitor that
    has not checked anything in a week.
    """
    state = State.load(cfg.state_path)

    cli.watch_loop(cfg, _explodes(RuntimeError("boom")), state, cycles=3, sleep=lambda s: None)

    assert sent["health"] == [["(all)"]], (
        "three cycles raised in a row and nothing was said — the monitor is "
        "running but not monitoring, and only it can know that"
    )


def test_the_stuck_warning_is_sent_once_not_every_cycle(
    cfg: Config, sent: dict[str, list]
) -> None:
    """A warning per poll is a warning you filter out."""
    state = State.load(cfg.state_path)

    cli.watch_loop(cfg, _explodes(RuntimeError("boom")), state, cycles=6, sleep=lambda s: None)

    assert sent["health"] == [["(all)"]]


def test_a_recovery_resets_the_failure_count(cfg: Config, sent: dict[str, list]) -> None:
    """Two failures, a success, two failures is not "four in a row"."""
    calls = {"n": 0}

    def check(watch: Watch) -> Result:
        calls["n"] += 1
        if calls["n"] in (1, 2, 4, 5):
            raise RuntimeError("boom")
        return Result(watch, Availability.OUT_OF_STOCK, detail="synthetic")

    state = State.load(cfg.state_path)
    rc = cli.watch_loop(cfg, check, state, cycles=5, sleep=lambda s: None)

    assert rc == 0
    assert ["(all)"] not in sent["health"], "an intermittent fault is not a stuck monitor"


def test_the_loop_gives_up_after_ten_consecutive_failures(
    cfg: Config, sent: dict[str, list]
) -> None:
    """Exiting non-zero is the only thing systemd can actually see.

    A persistent fault — a config error, a parser AttributeError, a full disk
    on state.save() — is not something to log forever. Returning 1 lets the
    unit restart or be marked failed, which is what makes the failure visible
    outside this process.
    """
    state = State.load(cfg.state_path)

    rc = cli.watch_loop(
        cfg, _explodes(RuntimeError("boom")), state, cycles=50, sleep=lambda s: None
    )

    assert rc == 1


def test_giving_up_does_not_happen_before_the_threshold(
    cfg: Config, sent: dict[str, list]
) -> None:
    """Bounded on both sides: nine failures is still "keep trying"."""
    state = State.load(cfg.state_path)

    rc = cli.watch_loop(
        cfg, _explodes(RuntimeError("boom")), state, cycles=9, sleep=lambda s: None
    )

    assert rc == 0


def test_a_failing_notifier_cannot_stop_the_loop_giving_up(
    cfg: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The stuck-monitor warning is a best effort, not a new way to crash.

    If whatever broke the cycle also broke notification, raising from inside
    the failure handler would replace a diagnosable exit with a stack trace
    from the wrong place.
    """

    def _raises(*args: object, **kwargs: object) -> bool:
        raise RuntimeError("notifier is down too")

    monkeypatch.setattr(cli, "send_health_warning", _raises)
    monkeypatch.setattr(cli, "send_restock", _raises)
    state = State.load(cfg.state_path)

    rc = cli.watch_loop(
        cfg, _explodes(RuntimeError("boom")), state, cycles=50, sleep=lambda s: None
    )

    assert rc == 1


# --------------------------------------------------------------------------
# REQ-08: every pass says how long it took
# --------------------------------------------------------------------------


def _check_config(tmp_path: Path) -> Path:
    """A one-watch config whose state and status land in `tmp_path`.

    `status_path` matters: without it `boty check` would write over the real
    `served/boty/status.json` that the deployed dashboard serves, so running
    the test suite would clobber the live monitor's published state.
    """
    config = tmp_path / "products.yaml"
    config.write_text(
        "settings:\n"
        f"  state_path: {tmp_path / 'state.json'}\n"
        f"  status_path: {tmp_path / 'status.json'}\n"
        "watches:\n"
        "  - name: goplusplus\n"
        "    retailer: gamestop\n"
        "    target: https://x/1\n",
        encoding="utf-8",
    )
    return config


def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Route every watch to a synthetic result, so nothing touches the network."""
    monkeypatch.setattr(cli, "_make_checker", lambda cfg: _checker(Availability.OUT_OF_STOCK))


def test_check_prints_how_long_the_pass_took(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`boty check` is the human surface for REQ-08's two-minute budget.

    The JSON key below is the machine one. Both are cheap, and a budget whose
    only reading lives in a served file is one nobody checks while watching a
    pass run.
    """
    _offline(monkeypatch)

    assert cli.main(["check", "-c", str(_check_config(tmp_path))]) == 0

    out = capsys.readouterr().out
    assert "1 watch" in out
    assert "1 retailer" in out
    assert re.search(r"\d+\.\d\s*s", out), f"no elapsed time printed:\n{out}"


def test_check_publishes_the_time_it_measured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real pass publishes a real number, not the null of an untimed one."""
    _offline(monkeypatch)

    cli.main(["check", "-c", str(_check_config(tmp_path))])

    published = json.loads((tmp_path / "status.json").read_text())["duration_seconds"]
    assert isinstance(published, float), f"nothing measured: {published!r}"
    assert published > 0


def test_a_watch_cycle_publishes_a_duration_too(cfg: Config, sent: dict[str, list]) -> None:
    """The dashboard's number must stay current between manual checks.

    `watch` is what actually runs in production; if only `boty check`
    published a duration, the served figure would be whatever a human last
    measured by hand rather than what the service is doing now.
    """
    state = State.load(cfg.state_path)

    cli.watch_loop(cfg, _checker(Availability.OUT_OF_STOCK), state, cycles=1, sleep=lambda s: None)

    published = json.loads(cfg.status_path.read_text())["duration_seconds"]
    assert isinstance(published, float) and published > 0, f"cycle published {published!r}"


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


def test_a_missing_config_file_is_an_error_message_not_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The first command README teaches must not die at a path only a checkout has.

    `[tool.setuptools.packages.find] include = ["boty*"]` means `config/` is not
    packaged, and `-c/--config` defaults to the repo-relative
    `config/products.yaml`. So on `pip install bot-y` — where there is no
    checkout — `boty check` reached `Config.load` with a path that does not
    exist and raised an uncaught `FileNotFoundError` naming a directory this
    package deliberately does not ship. Measured 2026-08-04 against a wheel in a
    clean venv; `make verify` could never see it, because it runs from the repo
    root where that path resolves.

    A stack trace is not an answer. This pins the answer: exit 2, the same code
    the two neighbouring "you have not configured this yet" refusals use, and a
    message naming the path, the flag and where to get a config.
    """
    missing = tmp_path / "nowhere" / "products.yaml"
    assert not missing.exists()

    assert cli.main(["check", "-c", str(missing)]) == 2
    err = capsys.readouterr().err
    assert str(missing) in err, err
    assert "--config" in err, err

    assert cli.main(["watch", "-c", str(missing)]) == 2
    assert str(missing) in capsys.readouterr().err


def test_capture_fixture_still_needs_no_config_file(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The early return above the guard is a decision with nothing under it today.

    `main` returns `_capture_fixture(args)` before any config is read, and the
    comment there says why: capturing a fixture takes a URL directly and has
    nothing to say about watches. The missing-config guard sits below that
    return, so adding it must not make a standalone tool start demanding a file
    it never used. Nothing asserted that until now.
    """
    monkeypatch.setattr(cli, "_capture_fixture", lambda args: 7)

    assert cli.main(["capture-fixture", "gamestop", "goplusplus", "https://x/1"]) == 7
    assert capsys.readouterr().err == ""
