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
import logging
import re
import time
from dataclasses import replace
from pathlib import Path

import pytest

from boty import cli
from boty.config import Config
from boty.models import Availability, Health, Result, Watch
from boty.monitor import State

WATCH = Watch(name="goplusplus", retailer="gamestop", target="https://x/1")
KEY = "gamestop:goplusplus"

#: The age REQ-21's opening measurement is about, and the one criterion 4 names:
#: "a restart cannot make a two-day-old reading look fresh".
_TWO_DAYS = 172800.0


@pytest.fixture
def cfg(tmp_path: Path) -> Config:
    return Config(
        watches=[WATCH],
        notify_urls=["tgram://token/chat"],
        interval_seconds=300,
        state_path=tmp_path / "state.json",
        status_path=tmp_path / "status.json",
        # Not tidiness. `pacer_state_path` defaults to a REPO-RELATIVE
        # `pacer-state.json`, so without this line every `watch_loop` test in
        # this file writes one into the process's working directory — the
        # repository root under `make verify-offline`, and the sandbox root
        # under `scripts/mutation_check.py`, where the sandboxes are built after
        # `git add -A` has already run. `_check_config` below makes the same
        # argument about `status_path` clobbering the deployed dashboard, and
        # `mutation_check.py`'s `_IGNORE` comment makes it again about a
        # nondeterministic runtime artifact inside a harness whose entire claim
        # is reproducibility.
        pacer_state_path=tmp_path / "pacer-state.json",
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


def _stamped(stamp: float, availability: Availability = Availability.IN_STOCK):
    """A checker whose reading carries the moment it was taken (REQ-21).

    SEPARATE FROM `_checker` ON PURPOSE, and `_checker` is left alone. Every
    other test in this file depends on it, and an unstamped `Result` is what a
    hand-built one is — `Result.read_at` defaults to `None`. Changing it would
    quietly stop the whole file exercising the no-stamp path, which is the path
    `State.transitioned_to_stock` has to CLEAR a stale stamp on.
    """

    def check(watch: Watch) -> Result:
        return Result(watch, availability, price=54.99, detail="synthetic", read_at=stamp)

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
    """The retry above works by un-remembering, so assert that directly.

    The checker is `_stamped` rather than `_checker` for the REQ-21 assertion at
    the end: against an unstamped reading nothing would ever write an age, and
    "no age on disk" would be green about a field this test never exercised.
    """
    sent["restock_ok"] = [False]
    state = State.load(cfg.state_path)

    cli.watch_loop(
        cfg, _stamped(time.time() - _TWO_DAYS), state, cycles=1, sleep=lambda s: None
    )

    assert KEY not in state.seen, (
        "an undelivered alert must leave no trace of the transition, or the "
        "next cycle will treat the unchanged in-stock reading as old news"
    )
    assert State.load(cfg.state_path).seen == state.seen, "the rollback must reach disk too"
    # REQ-21, and it is the same claim one field along rather than a new one.
    # `save` builds its document FROM `seen`, so popping the key takes its age
    # with it: the availability and the moment it was read leave together, which
    # is what a rollback means. (The in-memory `read_at` can still hold the
    # orphan for the rest of this process — it simply has no way to reach disk.)
    assert State.load(cfg.state_path).read_at == {}, (
        "the availability was rolled back and its age was not, so the document "
        "on disk dates a reading it no longer remembers taking"
    )


def test_a_delivered_restock_notification_is_not_repeated(
    cfg: Config, sent: dict[str, list]
) -> None:
    """The rollback must be conditional. Alerts stay edge-triggered."""
    state = State.load(cfg.state_path)

    cli.watch_loop(cfg, _checker(Availability.IN_STOCK), state, cycles=3, sleep=lambda s: None)

    assert sent["restock"] == [["goplusplus"]], "a delivered alert must fire exactly once"
    assert state.seen == {KEY: "in_stock"}


def test_a_failed_health_warning_is_retried_next_cycle(
    gap_cfg: Config, sent: dict[str, list]
) -> None:
    """`warned` had the same defect as `state.seen`, for the same reason.

    It was updated from `health` regardless of whether the warning was
    delivered, so a state somebody needed to act on could be reported once, fail
    to send, and never be mentioned again — the "tells you when it breaks"
    promise silently voided.

    THE SCENARIO MOVED TO THE STORE-PIN GAP ON 2026-08-12 and the claim did not.
    It used to ride on `gamestop` having no control watch, which was convenient
    rather than chosen: since Dan's rule that state is recorded and not pushed,
    so a rollback test built on it would assert the retry of a warning that is
    never sent — green, and about nothing. `gap_cfg` is the one config whose
    health state still pages, which is the only place this rollback can be seen.
    """
    sent["health_ok"] = [False, True]
    state = State.load(gap_cfg.state_path)

    cli.watch_loop(gap_cfg, _store_gap, state, cycles=2, sleep=lambda s: None)

    assert sent["health"] == [["walmart"], ["walmart"]], (
        "the health warning was not delivered, but the retailer was marked as "
        "already warned, so the retry never happened"
    )


def test_a_delivered_health_warning_is_not_repeated_every_cycle(
    gap_cfg: Config, sent: dict[str, list]
) -> None:
    """Once per failure episode, not once per poll — the reason `warned` exists."""
    state = State.load(gap_cfg.state_path)

    cli.watch_loop(gap_cfg, _store_gap, state, cycles=3, sleep=lambda s: None)

    assert sent["health"] == [["walmart"]]


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
    # Before 2026-08-12 this line read `== [["gamestop"]]`, "only the ordinary
    # no-control warning". `gamestop` has no control watch here, so it is still
    # reported unhealthy on every surface we own — but *configure a control* is
    # not a thing the person holding the phone can do, so it is recorded and not
    # pushed. "Stay quiet" in the docstring above got stronger, not weaker.
    assert sent["health"] == [], "a tolerated hiccup wakes nobody, and neither does the state"


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


def test_a_failing_pacer_write_cannot_stop_the_loop_giving_up(
    cfg: Config, monkeypatch: pytest.MonkeyPatch, sent: dict[str, list]
) -> None:
    """The `finally` is not allowed to eat the exit code, and it could.

    `pacer.save` is called from a `finally` — deliberately, so a cycle that
    raises after a refusal was recorded does not lose that refusal. The cost of
    that placement is that ANY exception escaping `save` replaces the pending
    `return 1` on the give-up path with a traceback from the wrong place, which
    is precisely the outcome `_warn_monitor_is_stuck`'s docstring says it exists
    to avoid: a diagnosable exit turned into a stack trace nobody can act on,
    from a function whose only job is writing a counter to disk.

    `save` wrapped only `OSError`, so `json.dumps` raising anything else walked
    straight out. Driven here through `json.dumps` rather than by replacing
    `save` itself, because replacing `save` would test the test.
    """
    import boty.pacing

    def _unserialisable(*args: object, **kwargs: object) -> str:
        raise TypeError("keys must be str, not tuple")

    monkeypatch.setattr(boty.pacing.json, "dumps", _unserialisable)
    state = State.load(cfg.state_path)

    rc = cli.watch_loop(
        cfg, _explodes(RuntimeError("boom")), state, cycles=50, sleep=lambda s: None
    )

    assert rc == 1, "the give-up exit code was replaced by a raise from the finally"


# --------------------------------------------------------------------------
# REQ-08: every pass says how long it took
# --------------------------------------------------------------------------


def _check_config(tmp_path: Path) -> Path:
    """A one-watch config whose state and status land in `tmp_path`.

    `status_path` matters: without it `boty check` would write over the real
    `served/boty/status.json` that the deployed dashboard serves, so running
    the test suite would clobber the live monitor's published state.

    `pacer_state_path` is here even though `boty check` builds no pacer and so
    writes no such file. A defence that depends on a code path staying absent is
    a defence with a countdown on it.
    """
    config = tmp_path / "products.yaml"
    config.write_text(
        "settings:\n"
        f"  state_path: {tmp_path / 'state.json'}\n"
        f"  status_path: {tmp_path / 'status.json'}\n"
        f"  pacer_state_path: {tmp_path / 'pacer-state.json'}\n"
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


# --------------------------------------------------------------------------
# REQ-16 across a RESTART: recorded not pushed, and pushed once — not once
# per process
#
# WHICH STATE CARRIES THESE CLAIMS CHANGED ON 2026-08-12, AND THE CLAIMS DID
# NOT. They used to be demonstrated on a refusal past the cap, because that was
# then the only state that both waited and pushed. Under Dan's rule a refusal
# never pushes at all, so a "pushed once" assertion built on one would be green
# about a notification that cannot happen — the most comfortable kind of dead
# test. The persistence they guard is not about refusals: it is `warned`
# crossing a process boundary and surviving a paced-out cycle, and that is now
# shown on the store-pin gap, the one state a person can act on. The refusal
# scenario stays, asserting the half that is still true of it — RECORDED, and
# never pushed however entrenched.
#
# A restart is modelled as two `watch_loop` calls sharing one
# `pacer_state_path`, and that is a faithful model rather than a convenience:
# `watch_loop` constructs its own `Pacer`, its own `warned` and its own
# `scheduled_now`, so a second call is a second process in every respect these
# criteria are about. Only the file crosses between them.
#
# THE CYCLE COUNTS ARE MEASURED, NOT GUESSED. The loop sleeps
# `interval_seconds * uniform(0.85, 1.15)` and the backoff doubles, so a
# refusal is only RECORDED on a cycle where the retailer is due. Over 300 seeds:
# 10 cycles yields exactly 3 refusals, the fifth refusal lands at cycle 30-32
# and the sixth at 61-65. Hence 10 for "below the cap" and 40 for "past it",
# with the resulting count asserted off the file rather than assumed.
# --------------------------------------------------------------------------

CONTROL = Watch(name="ctl", retailer="gamestop", target="https://x/2", control=True)


@pytest.fixture
def restart_cfg(tmp_path: Path) -> Config:
    """A config whose watch is a CONTROL, which the `cfg` fixture's is not.

    Without one `assess_health` reports gamestop unhealthy for *no control watch
    configured*, `Health.refused` is never set, and every assertion below would
    be testing the wrong arm — looking right and proving nothing.
    """
    return Config(
        watches=[CONTROL],
        notify_urls=["tgram://token/chat"],
        interval_seconds=300,
        state_path=tmp_path / "state.json",
        status_path=tmp_path / "status.json",
        pacer_state_path=tmp_path / "pacer-state.json",
    )


def _refuses(watch: Watch) -> Result:
    """The shape `tests/test_pacing.py` already uses for a wall."""
    return Result(watch, Availability.UNKNOWN, detail="blocked: challenge page", refused=True)


def _run(cfg: Config, cycles: int, checker=_refuses) -> None:
    """One process: a fresh State, a fresh Pacer, a fresh `warned`."""
    cli.watch_loop(cfg, checker, State.load(cfg.state_path), cycles=cycles, sleep=lambda s: None)


def _persisted(cfg: Config) -> dict:
    return json.loads(cfg.pacer_state_path.read_text())


def _refusals(cfg: Config) -> int:
    return _persisted(cfg)["retailers"]["gamestop"]["refusals"]


def test_a_refusal_the_backoff_is_handling_is_recorded_not_pushed_across_a_restart(
    restart_cfg: Config, sent: dict[str, list], caplog: pytest.LogCaptureFixture
) -> None:
    """REQ-16 clause 1, across the restart.

    "Recorded, not pushed" is a claim about a record EXISTING, so both halves
    are asserted: the log line saying why we are not paging, and the count on
    disk. Asserting only the absence of a push would pass for a loop that had
    silently stopped noticing the refusals at all.
    """
    caplog.set_level(logging.INFO, logger="boty.cli")

    _run(restart_cfg, cycles=10)
    assert _refusals(restart_cfg) == 3, "10 cycles is measured to yield 3 refusals"

    _run(restart_cfg, cycles=1)

    assert _refusals(restart_cfg) == 4, (
        "the second process started counting from one — the refusal it recorded "
        "was its first rather than the run's fourth"
    )
    assert sent["health"] == [], (
        "a refusal the backoff is still handling was pushed. Below the cap, "
        "backing off IS the whole response"
    )
    assert "not pushed" in caplog.text, "the refusal was not recorded anywhere a human can see"


def test_an_actionable_state_is_pushed_once_not_once_per_process(
    gap_cfg: Config, sent: dict[str, list]
) -> None:
    """REQ-16's headline clause, and the reason that plan existed.

    Process 1 finds the store-pin gap and pages. Process 2 starts with a fresh
    `warned` by construction — `watch_loop` builds its own — and must NOT page
    again, because the paging memory came back off disk. Before this, "pushed
    once" meant "pushed once per process", and under a systemd unit with
    `Restart=` semantics that is not a rare event.

    Nothing about this needs a cap or a backoff, which is why it survived the
    2026-08-12 rule while the refusal version of it did not: the memory is what
    is under test, and the gap is simply the state that still reaches a phone.
    """
    _run(gap_cfg, cycles=10, checker=_store_gap)
    assert sent["health"] == [["walmart"]], "process 1 pages exactly once"

    _run(gap_cfg, cycles=10, checker=_store_gap)

    assert sent["health"] == [["walmart"]], (
        "the retailer was paged again after the restart. REQ-16 says such a "
        "state is pushed ONCE, and this is how that quietly became once per "
        "process"
    )


@pytest.fixture
def paced_gap_cfg(gap_cfg: Config) -> Config:
    """`gap_cfg`, but with the retailer asked less often than the loop cycles.

    NOT A CONVENIENCE, AND MEASURED RATHER THAN ASSUMED. The claim below is that
    a cycle in which a retailer was NOT ASKED does not end its failure episode,
    so the test is worthless unless such a cycle happens. `Pacer.due` grants half
    an interval of grace, and `watch_loop` sleeps `interval_seconds * uniform(
    0.85, 1.15)` — so at the default cadence the shortest possible sleep still
    clears the grace and the retailer is due on EVERY cycle. The refusal version
    of this test got its skips from the backoff stretching the interval by 2**N;
    with no refusal in sight, the skips have to come from the schedule.

    1800 s against a 300 s pass is `config/products.yaml`'s own shape — Amazon
    sits at exactly that — so this is the shipped configuration, not a contrived
    one.
    """
    return replace(gap_cfg, retailer_intervals={"walmart": 1800})


def test_an_actionable_state_is_pushed_once_within_one_process_too(
    paced_gap_cfg: Config, sent: dict[str, list]
) -> None:
    """The same clause without any restart at all, and it was broken separately.

    `warned` is recomputed from `health` each cycle, and `health` is derived
    from `results` — of which a retailer the pacer did not ask has none. So "not
    checked" read as "recovered", and the memory was erased by the very next
    such cycle: measured 2026-08-10, it survived exactly one cycle out of the
    nine that followed the page, and the retailer was paged again at its next
    check. That is a notification every few minutes, forever, about a config gap
    somebody was already told about — the 20-pages-in-24-hours failure rebuilt
    at a slower cadence.

    NO BACKOFF IS INVOLVED HERE, so the skips come from the SCHEDULE instead —
    see `paced_gap_cfg`, which is where that is argued and where the numbers are.
    120 passes at 300 s against a 1800 s retailer is roughly 20 checks and 100
    cycles in which nothing was learned about Walmart; without the union each of
    those hundred reads as a recovery.
    """
    _run(paced_gap_cfg, cycles=120, checker=_store_gap)

    assert sent["health"] == [["walmart"]], (
        "the retailer was paged twice in one process. A cycle the pacer skipped "
        "is not the retailer recovering, and only a retailer that was actually "
        "checked can have ended its failure episode"
    )


def test_the_same_scenario_pushes_twice_when_the_state_file_is_deleted(
    gap_cfg: Config, sent: dict[str, list]
) -> None:
    """The permanent negative control for the test above, and it does not decay.

    Without it, that test passes for a tree where nothing was ever persisted and
    nothing was ever pushed twice for some unrelated reason. Delete the one
    thing that crosses between the processes and the second page comes back —
    so if persistence ever stops working the test above goes red, and if that
    test ever stops testing persistence this one does.
    """
    _run(gap_cfg, cycles=10, checker=_store_gap)
    assert sent["health"] == [["walmart"]]

    gap_cfg.pacer_state_path.unlink()
    _run(gap_cfg, cycles=10, checker=_store_gap)

    assert sent["health"] == [["walmart"], ["walmart"]], (
        "deleting the state file changed nothing, so the single push in the "
        "test above was not evidence of persistence"
    )


def test_the_backoff_comes_back_deep_rather_than_shallow(
    restart_cfg: Config, sent: dict[str, list]
) -> None:
    """The politeness half, which no verdict-level test can see.

    Read off the persisted document rather than inferred from how many cycles
    were skipped, so the assertion names the quantity that actually matters: the
    first refusal after a restart must multiply from the restored depth, not
    from one.
    """
    _run(restart_cfg, cycles=40)
    before = _refusals(restart_cfg)

    _run(restart_cfg, cycles=1)

    assert _refusals(restart_cfg) == before + 1, (
        f"after the restart the count is {_refusals(restart_cfg)}, not {before + 1} — "
        f"the backoff climbed again from the bottom against a retailer that has "
        f"refused us {before} times in a row"
    )
    # `due_at` is deliberately NOT restored, so the withdrawn docstring's
    # concession survives: the restarted process really did ask once, at full
    # rate, on its very first cycle. That is what produced the increment above.
    assert _persisted(restart_cfg)["retailers"]["gamestop"]["refused_at"] > 0


def test_a_restored_paging_memory_does_not_silence_a_new_actionable_state(
    gap_cfg: Config, sent: dict[str, list]
) -> None:
    """Clause 3 across the restart: an actionable state pages immediately.

    The restore has to be checked for over-reach as well as under-reach. A
    `load` that returned every retailer it had ever heard of would pass the
    pushed-once test above and silence the one alert that survived 2026-08-12 —
    there is nothing for a config gap to outlast, so it pages on the first cycle
    it appears in.

    Process 1 is REFUSED, which is the state that pushes nothing, so `warned`
    ends empty rather than by assumption: `_is_store_gap` returns False for a
    refusal (no page came back, so the store was never established either), and
    the assertion below is what proves the setup rather than the subject.
    """
    _run(gap_cfg, cycles=10, checker=_refuses)
    assert sent["health"] == [], "a refusal pushed nobody, so `warned` is empty"

    _run(gap_cfg, cycles=1, checker=_store_gap)

    assert sent["health"] == [["walmart"]], (
        "a store-pin gap — the one state naming something the operator can do — "
        "was not pushed on the first cycle of the new process"
    )


def test_boty_check_writes_no_pacer_state_at_all(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`check` is one pass with no schedule, so it builds no pacer to persist.

    Pinned rather than assumed: `_check_config` points the path at `tmp_path`
    precisely so this test can tell "nothing was written" from "something was
    written somewhere else".
    """
    _offline(monkeypatch)

    assert cli.main(["check", "-c", str(_check_config(tmp_path))]) == 0

    assert not (tmp_path / "pacer-state.json").exists()


# --------------------------------------------------------------------------
# REQ-21 across a RESTART: an age that does not survive the process is the
# failure this phase exists to fix
#
# Criterion 4, verbatim: "the age survives a service restart, so a restart
# cannot make a two-day-old reading look fresh". REQ-21's opening measurement
# was not that Walmart's last reading was old — it was that its age could not be
# ESTABLISHED AT ALL, because a service restart at 2026-08-12 16:49:57 zeroed the
# counter that held the evidence. 07-01 gave a reading a moment; that moment
# lived in a `Result` and died with the process. This is where it stops dying.
#
# A restart is modelled as two `watch_loop` calls sharing one `state_path`. The
# `REQ-16 across a RESTART` section above already argues why that model is
# faithful rather than convenient — each call builds its own `State`, its own
# `Pacer` and its own `warned`, so only the file crosses between them — and that
# argument is cited here rather than re-made, so the two cannot drift apart.
#
# THIS IS THIS FILE'S FIRST GENUINE `REQ-21` SECTION. The header at the section
# below carried that ident until 2026-08-13 and had no claim to it; 07-01
# relabelled it REQ-16 and re-pointed `scripts/mutation_check.py`'s citation.
# Confirmed against the tree before this section was written, because two
# `REQ-21` sections in one file would rebuild exactly the ambiguity that closed.
# --------------------------------------------------------------------------


def test_the_age_of_a_reading_survives_the_restart(cfg: Config, sent: dict[str, list]) -> None:
    """A two-day-old reading is still two days old on the other side, to the float.

    Both ends are asserted — the bytes on disk and what a fresh `State` makes of
    them — because they fail in different ways: a `save` that never wrote the
    stamp and a `load` that manufactured one both look identical from the other
    side of a single assertion.
    """
    stamp = time.time() - _TWO_DAYS

    cli.watch_loop(
        cfg,
        _stamped(stamp, Availability.OUT_OF_STOCK),
        State.load(cfg.state_path),
        cycles=1,
        sleep=lambda s: None,
    )

    assert json.loads(cfg.state_path.read_text())[KEY]["read_at"] == stamp

    restarted = State.load(cfg.state_path)

    assert restarted.seen[KEY] == "out_of_stock"
    assert restarted.read_at[KEY] == stamp, (
        "the restart did not carry the age across, so a two-day-old reading "
        "comes back looking fresh — criterion 4's failure exactly, and the "
        "2026-08-12 event REQ-21 was written for"
    )


def test_the_second_process_reads_the_first_process_stamp_and_not_its_own_clock(
    cfg: Config, sent: dict[str, list]
) -> None:
    """The stamp that crosses is the one the READING carried, not the one either process started at.

    The second cycle takes a reading of its own, one hour old, and the document
    has to move to it — an age that survived a restart but then refused to update
    would be a bound stuck at the first value it ever saw, which is the same
    defect standing still instead of running fast.
    """
    old = time.time() - _TWO_DAYS
    newer = time.time() - 3600

    cli.watch_loop(
        cfg,
        _stamped(old, Availability.OUT_OF_STOCK),
        State.load(cfg.state_path),
        cycles=1,
        sleep=lambda s: None,
    )
    cli.watch_loop(
        cfg,
        _stamped(newer, Availability.OUT_OF_STOCK),
        State.load(cfg.state_path),
        cycles=1,
        sleep=lambda s: None,
    )

    assert State.load(cfg.state_path).read_at[KEY] == newer


def test_a_reading_the_first_process_could_not_date_comes_back_undated(
    cfg: Config, sent: dict[str, list]
) -> None:
    """The restart must not INVENT an age either, and that is the other half of criterion 4.

    An age that does not survive is one failure; an age manufactured at the
    moment of the restart is the same failure wearing the fix's clothes, and it
    is worse because it reads like an answer. This is `walmart:Pokémon GO Plus +`
    on this host in miniature: a remembered availability whose moment cannot be
    established, restarted. It has to come back UNKNOWN, indefinitely, rather
    than dated at whenever the daemon last came up.

    `_checker` is the unstamped one on purpose here — a hand-built `Result` took
    no reading, which is exactly the input this claim is about.
    """
    cli.watch_loop(
        cfg,
        _checker(Availability.OUT_OF_STOCK),
        State.load(cfg.state_path),
        cycles=1,
        sleep=lambda s: None,
    )

    assert json.loads(cfg.state_path.read_text())[KEY]["read_at"] is None, (
        "null and never 0 — a zero here renders as 1 January 1970, which reads "
        "as maximally stale rather than as unknown"
    )
    assert State.load(cfg.state_path).read_at == {}, (
        "the restart dated a reading nobody stamped, so a frozen row comes back "
        "looking as though it had just been taken"
    )


# --------------------------------------------------------------------------
# REQ-16: a push has to carry a human action, and the default is silence
#
# RELABELLED FROM `REQ-21` ON 2026-08-13, and argued here rather than silently
# retyped. This section was written 2026-08-12 by Phase 6's paging work, and
# REQ-21 was minted NOWHERE in v0.2's archive and nowhere in Phase 6's planning
# — that ident was invented in this file and never existed as a requirement.
# The section's own subject is REQ-16's ("A notification is sent only when a
# human decision changes the outcome"), and `tests/test_cli_watch.py:510`
# already carries a `REQ-16 across a RESTART` section, so the label was a slip:
# somebody reached for the next free number instead of the governing
# requirement. v0.3 then minted a REAL REQ-21 on 2026-08-13, meaning something
# entirely different — when a reading was taken — and 07-01 writes genuine
# `REQ-21` sections in three test files, which would make
# `scripts/mutation_check.py`'s citation of "test_cli_watch.py's REQ-21
# section" ambiguous the moment it landed. M29's citation is re-pointed in the
# same commit.
#
# NO CRITERION, REQUIREMENT OR MEASUREMENT CHANGES HERE. A mistyped
# cross-reference is being made to point at what it always meant. Every
# assertion below is byte-unchanged.
#
# Dan, 2026-08-12, the second time he raised it: *"im still getting annoying
# messages. we need to never hit the user unless its something they can buy or
# actually do"*. The message that produced it fired at 16:49:58 that day —
# Amazon's control did not read IN_STOCK, and there is nothing a person can buy
# or do about that.
#
# THE RULE IS A POSITIVE ONE, NOT A BLOCKLIST, and that is the property these
# tests exist to pin. A list of cases that must stay quiet is stale the moment
# an arm is added — the new one is loud by default, which is how this channel
# filled up twice. So `Health.action` names the thing a person can DO, it is
# EMPTY unless an arm deliberately fills it, and `watch_cycle` pages exactly
# what carries one. A health arm written next year is silent until somebody
# writes down what to do about it.
#
# RECORDING IS UNTOUCHED, and that is asserted here rather than assumed. Every
# state still reaches `status.json` and the log in full; what changed is only
# which of them wake somebody up.
# --------------------------------------------------------------------------

#: A Walmart control with no store pinned — the ONE health state a person can
#: act on, because closing it means setting a value in the EnvironmentFile.
#: `store_id=None` is the config gap itself, not a redaction.
GAP_CONTROL = Watch(
    name="ctl", retailer="walmart", target="https://x/3", control=True, store_id=None
)


@pytest.fixture
def gap_cfg(tmp_path: Path) -> Config:
    """A config whose control watch reaches `assess_health`'s store-gap arm."""
    return Config(
        watches=[GAP_CONTROL],
        notify_urls=["tgram://token/chat"],
        interval_seconds=300,
        state_path=tmp_path / "state.json",
        status_path=tmp_path / "status.json",
        pacer_state_path=tmp_path / "pacer-state.json",
    )


def _store_gap(watch: Watch) -> Result:
    """A reading that establishes nothing about the store it came from."""
    return Result(watch, Availability.UNKNOWN, detail="no store_id pinned for this watch")


def _health_rows(cfg: Config) -> dict[str, dict]:
    return {row["retailer"]: row for row in json.loads(cfg.status_path.read_text())["retailers"]}


def test_a_control_that_stopped_reading_in_stock_is_recorded_and_not_pushed(
    restart_cfg: Config, sent: dict[str, list], caplog: pytest.LogCaptureFixture
) -> None:
    """The 16:49:58 message, and the reason this rule exists.

    A control not reading IN_STOCK is real, and it is published in full. It is
    not a push: nobody can repair a detector from a phone, and `assess_health`
    has already said the cause is not established — an alert that wakes somebody
    to tell them a cause is unknown asks for a decision that does not exist.

    Both halves are asserted, on the precedent of the refusal test above:
    "recorded, not pushed" is a claim about a record EXISTING, and asserting the
    absence of the push alone would pass for a loop that had stopped noticing.
    """
    caplog.set_level(logging.INFO, logger="boty.cli")

    def _broken(watch: Watch) -> Result:
        return Result(watch, Availability.UNKNOWN, detail="no structured stock data found")

    _run(restart_cfg, cycles=3, checker=_broken)

    assert sent["health"] == [], (
        "a control that stopped verifying was pushed. There is nothing to buy "
        "and nothing to do about it, which is the whole of the rule"
    )
    row = _health_rows(restart_cfg)["gamestop"]
    assert row["ok"] is False, "the state was silenced instead of merely not pushed"
    assert "IN_STOCK" in row["reason"], "status.json lost the reason it used to carry"
    assert "gamestop" in caplog.text and "not pushed" in caplog.text, (
        "nothing in the log says the state was seen and deliberately not pushed"
    )


def test_a_refusal_past_the_old_cap_is_still_never_pushed(
    restart_cfg: Config, sent: dict[str, list]
) -> None:
    """The clause this supersedes, watched at the point where it used to fire.

    REQ-16 said a refusal that outlasts the backoff is pushed once. Dan's
    2026-08-12 rule overrules that: he cannot make a retailer answer, so the
    entrenchment of a refusal changes nothing a person can do about it. 40
    cycles is measured to carry the count past the old threshold of five, and
    the count is read off disk so this cannot pass by the refusals having
    stopped being recorded.
    """
    _run(restart_cfg, cycles=40)

    assert _refusals(restart_cfg) >= 5, "40 cycles is measured to pass the old cap"
    assert sent["health"] == [], (
        "an entrenched refusal was pushed. It is worth recording and it is not "
        "worth waking somebody for — the retailer is not ours to fix"
    )


def test_the_store_pin_gap_is_pushed_because_a_person_can_close_it(
    gap_cfg: Config, sent: dict[str, list]
) -> None:
    """The positive half, without which silence would be free.

    A gate that only ever suppresses is satisfied by pushing nothing at all.
    This is the one health state that names an action only Dan can take — set
    the store id in the daemon's EnvironmentFile — so it must still reach him.
    """
    _run(gap_cfg, cycles=3, checker=_store_gap)

    assert sent["health"] == [["walmart"]], (
        "the one health state carrying a human action did not reach a phone"
    )


def test_a_health_state_nobody_has_written_yet_is_silent(
    cfg: Config, sent: dict[str, list], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The anti-blocklist property, and the reason the field is opt-in.

    A synthetic arm stands in for the one somebody adds next year. Nothing in
    `watch_cycle` knows what it is; it carries no action, so it is silent. A
    rule written as a list of known-quiet cases would push this one.
    """
    invented = Health("gamestop", ok=False, reason="a state this rule has never heard of")
    monkeypatch.setattr(cli, "run_once", lambda *a, **k: ([], [invented], []))

    _run(cfg, cycles=2)

    assert sent["health"] == [], (
        "an unrecognised health state was pushed by default. Every future arm "
        "starts loud, which is the failure this rule exists to prevent"
    )


def test_boty_check_still_prints_a_state_that_is_never_pushed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The third recording surface, and the one a person reads on purpose.

    `_check_config`'s watch has no control, so `assess_health` reports it
    unhealthy and nothing pages about it. That must not become invisible: the
    rule is *record everything, push what can be acted on*, and a change that
    quietly turned one into the other would look identical from the phone.
    """
    _offline(monkeypatch)

    assert cli.main(["check", "-c", str(_check_config(tmp_path))]) == 0

    out = capsys.readouterr().out
    assert "gamestop" in out and "no control watch configured" in out, out


def test_the_same_state_pushes_once_somebody_writes_down_what_to_do(
    cfg: Config, sent: dict[str, list], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other direction of the test above, so silence cannot be the answer to
    everything: the ONLY difference between the two is the stated action."""
    actionable = Health(
        "gamestop",
        ok=False,
        reason="a state this rule has never heard of",
        action="something a person can actually do",
    )
    monkeypatch.setattr(cli, "run_once", lambda *a, **k: ([], [actionable], []))

    _run(cfg, cycles=2)

    assert sent["health"] == [["gamestop"]], (
        "a state that names a human action was suppressed, so the rule is "
        "'push nothing' rather than 'push what can be acted on'"
    )
