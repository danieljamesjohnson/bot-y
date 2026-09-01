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
import random
import re
import time
from dataclasses import replace
from pathlib import Path

import pytest

from boty import cli
from boty.config import Config
from boty.models import Availability, Health, Result, Watch
from boty.monitor import State
from boty.pacing import (
    COOLOFF_SECONDS,
    MAX_BACKOFF_SECONDS,
    REFUSALS_BEFORE_COOLOFF,
    Pacer,
    loop_tick_seconds,
)

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

    `pacer_state_path` is here, and the reason it is here CHANGED on 2026-08-13.
    Until then this paragraph read:

        "`pacer_state_path` is here even though `boty check` builds no pacer and
        so writes no such file. A defence that depends on a code path staying
        absent is a defence with a countdown on it."

    REQ-21 ran the countdown down. `boty check` now builds a `Pacer` and loads
    this document, so that it can answer *"what cadence is this retailer on"*
    with the daemon's own backoff depth instead of the config value.

    The line survives with a STRONGER reason, which is why this is a rewrite
    rather than a deletion: the premise died and the conclusion did not. The
    defence used to be against a code path staying absent; it is now against one
    that exists and must stay READ-ONLY. That is asserted directly by the REQ-21
    cross-surface section below — the document's bytes are compared across a
    check — rather than inferred from the absence of a file.
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


def test_a_check_that_catches_a_restock_does_not_consume_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`boty check` reports a transition. It must not also SPEND one.

    `run_once` calls `state.transitioned_to_stock(r)` for every result and then
    `state.save()` — committing the transition to `state.json` — before it
    returns. `boty check` calls it, prints `N alertable transition(s)`, and
    sends nothing. So a check that happened to catch a restock wrote "already
    seen, in stock" to disk and no alert was delivered by anybody.

    THE LOSS IS NOT IMMEDIATE AND THAT IS STATED RATHER THAN INFLATED: the
    running daemon holds its own in-memory `State`, so it still fires on its
    own next cycle and its next `save()` overwrites the file. It becomes real
    if the daemon restarts, or is not running, between the check and the
    daemon's own detection — which under `Restart=` semantics is not a rare
    state, as `boty/pacing.py`'s own persistence argument already records.
    `cli.py` states the governing principle for the class: *"a send that does
    not arrive is not a retry — it is a drop nothing will ever mention again."*

    THE RESIDUAL IS ASSERTED HERE TOO, in the third block: a check that does not
    commit cannot report transitions relative to the DAEMON's memory, only
    relative to the file as it stood. Two checks in a row therefore both report
    the same restock. That is the correct behaviour for a read-only surface and
    it is pinned so nobody later "fixes" it by committing.
    """
    config = _check_config(tmp_path)
    cfg = Config.load(config)

    # The ledger as the daemon left it: this watch was last seen out of stock.
    seed = State.load(cfg.state_path)
    seed.seen[KEY] = Availability.OUT_OF_STOCK.value
    seed.save()
    before = cfg.state_path.read_text(encoding="utf-8")

    monkeypatch.setattr(cli, "_make_checker", lambda c: _checker(Availability.IN_STOCK))
    assert cli.main(["check", "-c", str(config)]) == 0

    out = capsys.readouterr().out
    assert "1 alertable transition(s)" in out
    # The residual said out loud on the surface a human reads, so a repeated
    # count is legible rather than alarming.
    assert "not sent, and not consumed" in out, out

    assert cfg.state_path.read_text(encoding="utf-8") == before, (
        "`boty check` committed a restock to the daemon's ledger and sent "
        "nothing — the transition is spent and no alert was delivered by anybody"
    )
    assert State.load(cfg.state_path).seen[KEY] == "out_of_stock"

    # And again, because the file did not move: the same restock is still there
    # to be found. This is the recorded residual, not an accident.
    assert cli.main(["check", "-c", str(config)]) == 0
    assert "1 alertable transition(s)" in capsys.readouterr().out


def test_a_watch_cycle_still_commits_the_transition_it_alerts_on(
    cfg: Config, sent: dict[str, list]
) -> None:
    """The other half, and the reason `commit` defaults to True.

    The daemon MUST write. Its whole restock rule is "in stock now and not in
    stock last time", so a cycle that alerted and did not commit would alert
    again on the next cycle, and the next — the 20-pages-in-24-hours failure
    this project already has a module dedicated to preventing.
    """
    state = State.load(cfg.state_path)
    state.seen[KEY] = Availability.OUT_OF_STOCK.value
    state.save()

    cli.watch_loop(cfg, _checker(Availability.IN_STOCK), state, cycles=1, sleep=lambda s: None)

    assert sent["restock"] == [["goplusplus"]], f"the daemon did not send: {sent['restock']}"
    assert State.load(cfg.state_path).seen[KEY] == "in_stock", (
        "the daemon alerted and did not commit — it will alert again next cycle"
    )


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
# REQ-21: one cadence, read the same way by both surfaces
# --------------------------------------------------------------------------
#
# Criterion 3 says a reading is stale when it is older than "its retailer's
# current interval". If `boty check` and the daemon compute that threshold
# separately they will disagree — measured on this host 2026-08-13, four of six
# retailers were on a cadence different from their configured one, by factors of
# up to 72 — and two surfaces publishing different staleness verdicts about one
# reading is this project's own defect one level up, rebuilt on the surface the
# criterion names. So both go through `cli._current_intervals`, and this is
# where that is asserted rather than described.
#
# `boty check` therefore builds a `Pacer` where it built none before, under
# three constraints that are each a defect if a later edit drops them: it never
# saves, it is never passed to `run_once`, and a missing document is the
# standing interval rather than an error. All three are asserted below.


def _published_cadence(cfg: Config, retailer: str = "gamestop") -> float | None:
    """The `current_interval_seconds` for one retailer, off the written file.

    Read out of the bytes rather than off a returned object, because what is
    under test is what the two surfaces PUBLISH — the dashboard has nothing else
    to read.
    """
    published = json.loads(cfg.status_path.read_text())["retailers"]
    (row,) = [r for r in published if r["retailer"] == retailer]
    return row["current_interval_seconds"]


def test_both_surfaces_publish_one_cadence_from_one_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The join this plan exists to make, asserted at the same refusal depth.

    The ordering is the whole of this test's validity. A naive version compares
    a daemon that has just recorded an outcome against a check that recorded
    nothing, so the two are read at different depths and an equality between
    them means nothing. Here gamestop is deep enough in its backoff to be
    PACED OUT of the daemon's cycle, so `run_once` records nothing for it and
    the depth stays at 3 across both surfaces.

    It also pins the two branches of the retailers array to each other: the
    daemon's row is built from `paced` and the check's from `health`.
    """
    from boty.pacing import Pacer

    config = _check_config(tmp_path)
    cfg = Config.load(config)

    # One document, written by a pacer built exactly as `watch_loop` builds one.
    pacer = Pacer(
        default_interval=cfg.interval_seconds,
        overrides=dict(cfg.retailer_intervals),
        state_path=cfg.pacer_state_path,
    )
    for _ in range(3):
        pacer.record("gamestop", refused=True, now=0.0)
    pacer.save(set())

    # THE DAEMON. gamestop is not due — 0.0 + 150.0 >= 2400.0 is false — so it
    # is published on the PACED branch and nothing is recorded against it.
    cli.watch_cycle(
        cfg,
        _checker(Availability.OUT_OF_STOCK),
        State.load(cfg.state_path),
        set(),
        pacer=pacer,
        now=0.0,
    )
    from_the_daemon = _published_cadence(cfg)
    document_before = cfg.pacer_state_path.read_bytes()

    # `boty check`, which built no pacer at all before 2026-08-13.
    _offline(monkeypatch)
    assert cli.main(["check", "-c", str(config)]) == 0
    from_the_check = _published_cadence(cfg)

    assert from_the_daemon == from_the_check, (
        f"the daemon published {from_the_daemon} and `boty check` published "
        f"{from_the_check} for the same retailer off the same document — the "
        f"two surfaces are answering 'is this reading stale?' with different "
        f"thresholds, which is this project's own defect one level up and the "
        f"reason criterion 3 is structural rather than cosmetic"
    )
    # THE BACKED-OFF NUMBER, not the standing one. Without this the test would
    # pass if both surfaces silently returned 300 — which is exactly what M33
    # makes them do.
    assert from_the_check == 2400.0, "300 x 2**3, the cadence three refusals put gamestop on"
    assert from_the_check > cfg.interval_seconds

    # LOAD-ONLY, proved on the bytes. The daemon owns this document and `boty
    # check` is routinely run while the service is running.
    assert cfg.pacer_state_path.read_bytes() == document_before, (
        "`boty check` rewrote pacer-state.json — two writers to one document is "
        "the contradiction the single-write argument in boty/pacing.py exists "
        "to prevent, pointed the other way"
    )

    # AND NOTHING WAS SKIPPED. A pacer passed to `run_once` would have skipped
    # this watch, and `boty check` is the one surface that shows every watch.
    checked = json.loads(cfg.status_path.read_text())["watches"]
    assert [w["name"] for w in checked] == ["goplusplus"], (
        "`boty check` dropped a watch — its pacer reached `run_once`, which "
        "makes the check start skipping and imports the vanishing-row problem "
        "onto the surface that exists to show all of them"
    )


def test_a_check_with_no_pacer_state_publishes_the_standing_interval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A fresh clone must not be told it is missing something it never had.

    No document means zero refusals means the config value, which is the
    correct answer and not a degraded one.
    """
    config = _check_config(tmp_path)
    cfg = Config.load(config)
    assert not cfg.pacer_state_path.exists()
    _offline(monkeypatch)

    with caplog.at_level(logging.WARNING):
        assert cli.main(["check", "-c", str(config)]) == 0

    assert _published_cadence(cfg) == float(cfg.interval_seconds)
    assert caplog.records == [], (
        f"an absent pacer-state.json warned: {[r.getMessage() for r in caplog.records]}"
    )


def test_a_per_retailer_override_reaches_the_published_cadence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The half of the cadence that comes from config rather than from the file.

    Without this the standing-interval path is only ever exercised at the
    default, and an accessor that ignored `overrides` would publish 300 for
    every retailer while GameStop was actually being asked every 15 minutes.
    """
    config = tmp_path / "products.yaml"
    config.write_text(
        "settings:\n"
        f"  state_path: {tmp_path / 'state.json'}\n"
        f"  status_path: {tmp_path / 'status.json'}\n"
        f"  pacer_state_path: {tmp_path / 'pacer-state.json'}\n"
        "  retailer_intervals:\n"
        "    gamestop: 900\n"
        "watches:\n"
        "  - name: goplusplus\n"
        "    retailer: gamestop\n"
        "    target: https://x/1\n",
        encoding="utf-8",
    )
    cfg = Config.load(config)
    _offline(monkeypatch)

    assert cli.main(["check", "-c", str(config)]) == 0

    assert _published_cadence(cfg) == 900.0


def test_a_retailer_in_cooloff_publishes_the_days_scale_cadence_it_is_actually_on(
    tmp_path: Path,
) -> None:
    """The one path proving a cool-off reaches the schedule and the page as ONE expression.

    REQ-22, 2026-08-28. A retailer past `REFUSALS_BEFORE_COOLOFF` is left alone
    for days rather than asked every six hours. That days-scale number has to
    arrive in two places at once — the wait `record` schedules, and the
    `current_interval_seconds` the dashboard reads — and it has to arrive there
    because they are the SAME expression rather than because two sites were kept
    in step.

    THAT IS WHY THE COOL-OFF BRANCH LIVES INSIDE `current_interval` and not in a
    guard clause of its own. `record` computes its wait THROUGH the accessor and
    `cli._current_intervals` publishes the accessor's answer, so one branch in
    one method reaches both. A second site would be a second thing to edit, and
    two copies of a rule only have to disagree once.

    Asserted off the WRITTEN BYTES via `_published_cadence`, not off a returned
    object: the dashboard has nothing else to read.

    The depth is driven off `REFUSALS_BEFORE_COOLOFF` rather than off a hardcoded
    30, so a later edit to the threshold cannot leave this test quietly exercising
    an off-threshold depth. The EXPECTED number is the hand-written literal
    259200.0 and never `COOLOFF_SECONDS`, so the assertion is not a re-derivation
    of the constant it is checking.
    """
    from boty.pacing import REFUSALS_BEFORE_COOLOFF, Pacer, loop_tick_seconds

    config = _check_config(tmp_path)
    cfg = Config.load(config)

    # Built exactly as `watch_loop` builds one — INCLUDING the roster and the
    # tick REQ-23 added on 2026-09-01. A pacer missing them is a valid
    # construction and not the SHIPPING one, and a cross-surface test that
    # asserted the published cadence against a schedule the daemon does not run
    # would be the "green defaulted site" `09-DECISIONS.md` names.
    roster = tuple(sorted({w.retailer for w in cfg.watches}))
    pacer = Pacer(
        default_interval=cfg.interval_seconds,
        overrides=dict(cfg.retailer_intervals),
        state_path=cfg.pacer_state_path,
        roster=roster,
        tick=loop_tick_seconds(cfg.interval_seconds, roster),
    )
    for _ in range(REFUSALS_BEFORE_COOLOFF - 1):
        pacer.record("gamestop", refused=True, now=0.0)
    # Read between the second-to-last refusal and the last one, because it is the
    # LAST refusal — the one that crosses `REFUSALS_BEFORE_COOLOFF` — whose wait
    # the assertion at the foot of this test is about. The cycle below asks
    # nobody, which is the point of it, so nothing moves the schedule in between.
    before_the_crossing = pacer._for("gamestop").due_at
    pacer.record("gamestop", refused=True, now=0.0)

    cli.watch_cycle(
        cfg,
        _checker(Availability.OUT_OF_STOCK),
        State.load(cfg.state_path),
        set(),
        pacer=pacer,
        now=0.0,
    )

    assert _published_cadence(cfg) == 259200.0, (
        f"the dashboard was told this retailer is on a "
        f"{_published_cadence(cfg)} s cadence while the schedule is holding it "
        f"for three days — the published number and the fetch schedule have "
        f"stopped being one expression"
    )

    # THE PACED BRANCH, which is the branch a cool-off always lands on. A row
    # published as `checked: true` would be a cool-off reported as an observation.
    published = json.loads(cfg.status_path.read_text())["retailers"]
    (row,) = [r for r in published if r["retailer"] == "gamestop"]
    assert row["checked"] is False, (
        "a retailer nobody asked was published as checked — a green row over a "
        "question this cycle deliberately did not ask"
    )

    # The schedule and the published number pinned to EACH OTHER rather than
    # separately, so neither can move without the other.
    #
    # THE ANCHOR MOVED ON 2026-09-01 AND THE PINNING DID NOT — REQ-23. This read
    # `== 259200.0` against a `now` frozen at 0.0; `record` now steps from the
    # retailer's own previous due time, so at a frozen clock the thirty refusals
    # accumulate and the reading was 793800.0. The claim is unchanged and is
    # re-pointed at the increment: the cool-off's DURATION is what reaches the
    # schedule, and it is the same days-scale number the dashboard was told.
    # `skipped_reason` and `current_interval` are untouched by this repair, which
    # is the signal `09-DECISIONS.md` § *Collision 3* says to watch for.
    assert pacer._for("gamestop").due_at - before_the_crossing == 259200.0


# --------------------------------------------------------------------------
# REQ-21: every configured watch has a row, on both surfaces
# --------------------------------------------------------------------------
#
# `status.write` rebuilds its `watches` array from `results`, and `run_once`
# filters the watches down to those the pacer says are due. So before 07-04 a
# paced-out watch did not leave a STALE row behind — it had no row at all.
# Measured on the live served file: 3 rows for 13 configured watches at 08:25:10
# on 2026-08-13, 8 at 09:24:54 the same morning, 5 at 07:36:57 on 2026-08-14,
# from a config that did not change between any of them.
#
# "not watched this cycle" and "watched, and out of stock" are indistinguishable
# when one of them is simply missing, so a reader could not answer *"so they are
# out of stock as of when?"* about the two watches that opened this phase — both
# of which were among the absent ones on every one of those three readings.
#
# THE HEADLINE TEST ASSERTS BOTH HALVES IN ONE PLACE, deliberately: every
# configured watch has a row AND only the due ones were fetched. Split into two
# tests, each could pass while the pair was false — thirteen rows because
# thirteen were fetched is precisely the change this plan must not make.


def _paced_config(tmp_path: Path) -> Path:
    """Two retailers, three watches, all state under `tmp_path`.

    `_check_config` above is one watch at one retailer, which cannot express the
    case this section is about: a cycle in which SOME retailers are due and
    others are not. Both are needed, so this is a sibling rather than an edit —
    changing `_check_config` would move the ground under the cadence section
    that uses it.
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
        "    target: https://x/1\n"
        "  - name: CONTROL — PS5 console\n"
        "    retailer: gamestop\n"
        "    target: https://x/2\n"
        "    control: true\n"
        "  - name: goplusplus\n"
        "    retailer: walmart\n"
        "    target: https://x/3\n",
        encoding="utf-8",
    )
    return config


def _backed_off_pacer(cfg: Config, retailer: str = "gamestop", refusals: int = 3):
    """A saved document with one retailer deep enough not to be due at `now=0.0`.

    Three refusals puts gamestop on 300 x 2**3 = 2400 s, and `0.0 + 150.0 >=
    2400.0` is false — the same arithmetic the cadence section above relies on,
    cited rather than re-derived so the two cannot drift.
    """
    from boty.pacing import Pacer

    pacer = Pacer(
        default_interval=cfg.interval_seconds,
        overrides=dict(cfg.retailer_intervals),
        state_path=cfg.pacer_state_path,
    )
    for _ in range(refusals):
        pacer.record(retailer, refused=True, now=0.0)
    pacer.save(set())
    return pacer


def _published_watches(cfg: Config) -> dict[str, dict]:
    """The published watch rows, keyed as `Watch.key` is, off the bytes."""
    published = json.loads(cfg.status_path.read_text())["watches"]
    return {w["retailer"] + ":" + w["name"]: w for w in published}


def test_every_configured_watch_has_a_row_while_only_the_due_ones_are_fetched(
    tmp_path: Path,
) -> None:
    """The plan in one sentence: N rows published while fewer than N were fetched.

    BOTH HALVES BELONG IN ONE TEST. A version that only counted rows would pass
    if this plan had made the daemon fetch every watch every cycle — which would
    satisfy the letter of "every watch has a row" by breaking the politeness
    constraint that is the whole reason rows go missing. A version that only
    counted fetches would pass on the pre-07-04 code.
    """
    config = _paced_config(tmp_path)
    cfg = Config.load(config)
    pacer = _backed_off_pacer(cfg)

    state = State.load(cfg.state_path)
    # What the ledger remembers about the two watches nobody is about to ask.
    state.seen["gamestop:goplusplus"] = "out_of_stock"
    state.seen["gamestop:CONTROL — PS5 console"] = "in_stock"

    asked: list[str] = []

    def watching_checker(watch: Watch) -> Result:
        asked.append(watch.key)
        return Result(watch, Availability.OUT_OF_STOCK, price=54.99, detail="synthetic")

    cli.watch_cycle(cfg, watching_checker, state, set(), pacer=pacer, now=0.0)

    rows = _published_watches(cfg)
    assert asked == ["walmart:goplusplus"], (
        f"the cycle moved: the checker was asked for {asked}, and this plan "
        f"changes what is REPORTED rather than what is fetched"
    )
    assert set(rows) == {w.key for w in cfg.watches}, (
        f"a watch that was not asked has a row that says nobody asked, rather "
        f"than no row at all — published {sorted(rows)} for "
        f"{sorted(w.key for w in cfg.watches)}"
    )
    assert len(rows) == 3 and len(asked) == 1, "3 rows published while 1 was fetched"

    assert rows["walmart:goplusplus"]["checked"] is True
    for key, remembered in (
        ("gamestop:goplusplus", "out_of_stock"),
        ("gamestop:CONTROL — PS5 console", "in_stock"),
    ):
        assert rows[key]["checked"] is False
        assert rows[key]["availability"] == remembered
        assert rows[key]["alertable"] is False, (
            "a memory acquired a reading's authority — the control is "
            "remembered in stock and carries no ceiling, which is exactly the "
            "configuration where a derived value would be True"
        )


def test_a_remembered_row_publishes_the_age_the_ledger_holds(tmp_path: Path) -> None:
    """Two days old, and still two days old on the page.

    `_TWO_DAYS` is REQ-21's own example and criterion 4's sentence. The stamp is
    constructed by subtraction from the real clock rather than by freezing one —
    this phase's standing rule, `tests/test_pacing.py:585-591`'s method.

    The `!=` against `updated` is the assertion that matters most: `updated` is
    written this second on every cycle, and a row that published it instead of
    the ledger's stamp would look four seconds old forever. That is REQ-21's
    opening complaint rebuilt inside the fix for it.
    """
    stamp = time.time() - _TWO_DAYS
    config = _paced_config(tmp_path)
    cfg = Config.load(config)
    pacer = _backed_off_pacer(cfg)

    state = State.load(cfg.state_path)
    state.seen["gamestop:goplusplus"] = "out_of_stock"
    state.read_at["gamestop:goplusplus"] = stamp
    # Seen, never dated: a remembered reading whose moment was never
    # established. It must publish `null` rather than be dropped from the file.
    state.seen["gamestop:CONTROL — PS5 console"] = "in_stock"

    cli.watch_cycle(cfg, _checker(Availability.OUT_OF_STOCK), state, set(), pacer=pacer, now=0.0)

    rows = _published_watches(cfg)
    updated = json.loads(cfg.status_path.read_text())["updated"]

    assert rows["gamestop:goplusplus"]["read_at"] == stamp
    assert rows["gamestop:goplusplus"]["read_at"] != updated
    assert rows["gamestop:CONTROL — PS5 console"]["read_at"] is None, (
        "a key present in `seen` and absent from `read_at` is a remembered "
        "reading whose moment was never established — an UNKNOWN age, which is "
        "not 0.0 and is not now"
    )


def test_a_check_publishes_every_watch_and_calls_none_of_them_remembered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`boty check` re-reads every watch, so its remembered branch produces nothing.

    That emptiness is asserted rather than assumed, and the assertion is only
    meaningful because the branch was AVAILABLE: `main` passes both keywords, so
    a `checked: false` row on this surface would mean a pacer had reached
    `run_once` and the check had started skipping.
    """
    config = _paced_config(tmp_path)
    cfg = Config.load(config)
    # A document deep in a backoff, so a pacer that reached `run_once` would
    # visibly drop two of the three rows.
    _backed_off_pacer(cfg)
    _offline(monkeypatch)

    assert cli.main(["check", "-c", str(config)]) == 0

    rows = _published_watches(cfg)
    assert set(rows) == {w.key for w in cfg.watches}
    assert len(rows) == len(cfg.watches) == 3
    assert all(row["checked"] is True for row in rows.values()), (
        f"`boty check` published a row nobody read: "
        f"{[k for k, v in rows.items() if not v['checked']]}"
    )


def test_both_write_status_call_sites_thread_the_watches_and_the_ledger() -> None:
    """Static, over the module's AST, because no behavioural test can see this.

    `status.write`'s `watches` and `remembered` default to `None` so that every
    pre-07-04 caller in `tests/` stays valid. That default is a compatibility
    default, and it has one cost: a production call site that DROPPED one of
    these keywords would keep every assertion in this file green — each of them
    passes its own arguments — while Dan's dashboard quietly went back to
    publishing five rows out of thirteen.

    So this is the gate that default is paid for with. It lives in the suite
    rather than only in a plan's `<verify>` because it has to run on every future
    edit, not once. The AST idiom is `tests/test_support_matrix.py`'s and
    `tests/test_ci_workflow.py`'s, and 07-03 used it on this same module to pin
    the check path's pacer as load-only.
    """
    import ast

    tree = ast.parse(Path(cli.__file__).read_text(encoding="utf-8"))
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "write_status"
    ]

    assert len(calls) == 2, (
        f"expected exactly 2 `write_status` call sites in boty/cli.py — the "
        f"daemon's and `boty check`'s — found {len(calls)}. A third surface "
        f"publishing this file needs to be in this assertion before it ships"
    )
    for call in calls:
        missing = {"watches", "remembered"} - {kw.arg for kw in call.keywords}
        assert not missing, (
            f"a `write_status` call site at line {call.lineno} passes no "
            f"{sorted(missing)} — that surface publishes only the watches it "
            f"read this cycle, which is the defect 07-04 exists to remove"
        )


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
    """`check` is one pass with no schedule, so it persists no pacer state.

    THE FIRST HALF OF THIS SENTENCE WAS WITHDRAWN ON 2026-08-13. It read:

        "`check` is one pass with no schedule, so it builds no pacer to
        persist."

    REQ-21 falsified the premise and left the assertion untouched: `boty check`
    now builds a `Pacer` and `load()`s it, to answer criterion 3 with the
    daemon's own backoff depth — and still writes nothing, because that pacer is
    load-only by construction. So this test stopped being a statement about a
    code path that does not exist and became a statement about one that does.
    Its stronger sibling is
    `test_both_surfaces_publish_one_cadence_from_one_document`, which compares
    the document's BYTES across a check; this one keeps the cheaper claim, that
    a check with no document does not create one.

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


# --------------------------------------------------------------------------
# CR-01: the pacer's clock must track wall clock, not just the sleeps
# --------------------------------------------------------------------------


def test_the_pacer_clock_advances_by_the_time_the_check_pass_really_took(
    cfg: Config, sent: dict[str, list], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The clock `due_at` is measured in must not lag the clock `refused_at` is in.

    THE TWO CLOCKS THIS JOINS. `Pacer.record` stamps `refused_at` from
    `time.time()` — wall clock, because it is the moment evidence was collected
    and the only thing a later process can date. `due_at` is `now + wait`, where
    `now` is this loop's `scheduled_now`. `Pacer.load`'s two-sided bound then
    compares wall against wall against `STATE_MAX_AGE_SECONDS`.

    So if `scheduled_now` advances by less than the wall time a cycle really
    consumed, the two clocks drift apart monotonically and in one direction, and
    the cool-off probe fires LATER in wall terms than the record ages out.
    `STATE_MAX_AGE_SECONDS` and `COOLOFF_SECONDS` are deliberately EQUAL, so
    there is no slack to absorb it: every second of drift is a second in which a
    restart drops the entry, the retailer returns at 0 refusals, and it must
    climb the backoff and re-earn 30 consecutive refusals — REQ-22's own result
    undone by REQ-22's own persistence layer.

    MEASURED, NOT ARGUED, on 2026-08-31: `served/boty/status.json` recorded
    `duration_seconds: 20.43` for a live cycle. At the 300 s standing cadence one
    cool-off window is 865 cycles, so the drift is 17 741 s — 4.93 h, or 6.84% of
    every window. `target` sat at 46 refusals on that date, past the threshold of
    30, so this bound on a real retailer rather than a hypothetical one.

    WHY THIS TEST INJECTS A SLOW CYCLE RATHER THAN READING THE CONSTANT. The
    defect is not a wrong number anywhere; it is a missing term. Only a cycle
    that actually consumes wall time can tell `+= delay` apart from
    `+= delay + duration`, which is why the pass below sleeps for real.
    """
    seen: list[float] = []
    real_cycle = cli.watch_cycle

    def _slow_cycle(cfg_, checker, state_, warned, *, pacer, now):  # type: ignore[no-untyped-def]
        seen.append(now)
        time.sleep(0.05)
        return real_cycle(cfg_, checker, state_, warned, pacer=pacer, now=now)

    monkeypatch.setattr(cli, "watch_cycle", _slow_cycle)
    delays: list[float] = []
    state = State.load(cfg.state_path)

    cli.watch_loop(
        cfg,
        _checker(Availability.OUT_OF_STOCK),
        state,
        cycles=3,
        sleep=lambda s: delays.append(s),
    )

    assert len(seen) == 3, seen
    for i in range(len(seen) - 1):
        advance = seen[i + 1] - seen[i]
        assert advance >= delays[i] + 0.04, (
            f"cycle {i}: the pacer's clock advanced {advance:.4f}s while the "
            f"cycle really consumed {delays[i] + 0.05:.4f}s of wall time — the "
            f"check pass's own duration was never added back, so `due_at` "
            f"drifts behind `refused_at` and a cool-off ages out before its probe"
        )


def test_the_pacer_clock_is_still_deterministic_under_a_fake_sleep(
    cfg: Config, sent: dict[str, list]
) -> None:
    """The fix for the test above must not cost the property the loop was built on.

    `scheduled_now` advances by the delay we ASK for precisely so a test passing
    `sleep=lambda s: None` still moves the clock a full interval per cycle. A fix
    that replaced the delay term with a measured elapsed time — rather than
    ADDING the duration to it — would advance the clock by microseconds here and
    make every retailer look never-due, silently disarming every paced assertion
    in this file. This test is what stops that being the fix.
    """
    seen: list[float] = []
    real_cycle = cli.watch_cycle

    def _record(cfg_, checker, state_, warned, *, pacer, now):  # type: ignore[no-untyped-def]
        seen.append(now)
        return real_cycle(cfg_, checker, state_, warned, pacer=pacer, now=now)

    import boty.cli as _cli

    _orig = _cli.watch_cycle
    _cli.watch_cycle = _record  # type: ignore[assignment]
    try:
        state = State.load(cfg.state_path)
        cli.watch_loop(
            cfg,
            _checker(Availability.OUT_OF_STOCK),
            state,
            cycles=3,
            sleep=lambda s: None,
        )
    finally:
        _cli.watch_cycle = _orig  # type: ignore[assignment]

    for i in range(len(seen) - 1):
        advance = seen[i + 1] - seen[i]
        assert advance >= 0.85 * cfg.interval_seconds, (
            f"cycle {i}: the clock advanced only {advance:.4f}s under a fake "
            f"sleep — a retailer on a {cfg.interval_seconds}s cadence would "
            f"never come due, disarming every paced assertion in this file"
        )


# --------------------------------------------------------------------------
# REQ-23: the tick reaches the loop, and both terms of the pacer clock survive
# --------------------------------------------------------------------------
#
# WHAT THE SHORTER TICK COSTS THE DAEMON, AS NUMBERS AND NOT AS REASSURANCE.
# DERIVED, NOT OBSERVED — every figure below comes from the day-long simulation
# in `tests/test_pacing.py` and from counting the call sites in `watch_loop`.
# NOTHING IN PHASE 9 RAN ON THE WIRE and `boty` is an editable install, so none
# of it reaches the service until a `systemctl restart boty` that is the user's
# call and is deliberately not part of this phase. The daemon is still running
# the pre-REQ-23 schedule as this is written.
#
#     per day, six retailers, interval_seconds 300   before      after
#     loop wake-ups (86 400 / tick)                     288       1728
#     served/boty/status.json writes (1 per cycle)      288       1728
#     pacer-state.json writes (1 per cycle)             288       1728
#     retailer requests                                1296       1296
#     retailers asked per wake, mean                    4.5       0.75
#     wakes that ask NOBODY                               0        432
#     most retailers a single wake asks                   6          1
#
# THE REQUEST COUNT IS THE ROW THAT DID NOT MOVE, and it is the one the
# retailers can see. What rose six-fold is how often this process wakes, writes
# two files and asks nobody: a quarter of all wakes now dispatch no retailer at
# all, and a wake that dispatches anybody dispatches exactly one. Pricing that —
# an empty tick publishing a vacuously green document, and two failure counters
# that count CYCLES rather than time — is `09-04`'s, and these numbers exist so
# `09-04` prices a recorded fact rather than discovering one.

#: The six retailers `config/products.yaml` configures. Written out here rather
#: than read, because these tests are about the LOOP and a config read would
#: make a failure ambiguous between the two.
_FLEET = ("amazon", "bestbuy", "gamestop", "nintendo", "target", "walmart")

#: The tick a six-retailer fleet on a 300 s global cadence produces, written out
#: for `_MIN_SEPARATION_SECONDS`'s reason: an edit to `loop_tick_seconds` has to
#: change this by hand, and that is the moment somebody notices the daemon's
#: wake rate moved.
_FLEET_TICK_SECONDS = 50.0

#: `cli.watch_loop` sleeps `tick * random.uniform(0.85, 1.15)`. THE BAND AND NOT
#: AN EXACT VALUE, because the jitter is deliberate — "we do not hammer on a
#: fixed cadence, which is itself a signal" — and a test pinning one delay would
#: forbid the property it exists to preserve.
_JITTER_LOW = 0.85
_JITTER_HIGH = 1.15


@pytest.fixture
def fleet_cfg(cfg: Config) -> Config:
    """`cfg` with all six configured retailers, which is what makes a tick a tick.

    Every other `watch_loop` fixture in this file carries ONE retailer, and
    `loop_tick_seconds` returns the standing interval for a one-retailer roster
    — so those fixtures wake at exactly the rate they woke at before REQ-23.
    `09-02` recorded that as a finding: a regression sweep built on
    single-retailer fixtures cannot fail for the reason it exists. This fixture
    is the answer to it.
    """
    return replace(
        cfg,
        watches=[Watch(name="goplusplus", retailer=r, target=f"https://x/{r}") for r in _FLEET],
    )


def test_the_loop_sleeps_the_tick_and_not_the_standing_cadence(
    fleet_cfg: Config, sent: dict[str, list]
) -> None:
    """The wake rate the schedule's separation is bought with, observed at the sleep.

    `Pacer` can lay six retailers out at 50 s apart all it likes; if the loop
    still wakes once per 300 s cadence there is exactly one wake per cadence for
    the four retailers configured on it, and all four are dispatched at it
    whatever position they hold. That is `09-DECISIONS.md` § *Collision 1*, and
    it is why this test asserts on the LOOP rather than on the pacer.

    THE BAND, NOT A VALUE. `_JITTER_LOW` and `_JITTER_HIGH` are the loop's own
    multipliers; an assertion on an exact delay would pass only by forbidding
    the jitter.
    """
    delays: list[float] = []
    state = State.load(fleet_cfg.state_path)

    cli.watch_loop(
        fleet_cfg,
        _checker(Availability.OUT_OF_STOCK),
        state,
        cycles=12,
        sleep=delays.append,
    )

    assert len(delays) == 12, delays
    low = _FLEET_TICK_SECONDS * _JITTER_LOW
    high = _FLEET_TICK_SECONDS * _JITTER_HIGH
    for i, d in enumerate(delays):
        assert low <= d <= high, (
            f"wake {i} slept {d:.3f}s, outside the [{low}, {high}] band a "
            f"{_FLEET_TICK_SECONDS}s tick jittered by "
            f"[{_JITTER_LOW}, {_JITTER_HIGH}] can produce"
        )

    # AND THE BAND IS NOT THE STANDING CADENCE'S. Stated as its own assertion
    # rather than left implied by the numbers above: the whole of criterion 1
    # rests on there being more than one wake per cadence, and a change that put
    # the loop back on `cfg.interval_seconds` would satisfy every "the delay is
    # inside a band" check if the band moved with it.
    assert high < fleet_cfg.interval_seconds * _JITTER_LOW, (
        f"the tick band tops out at {high}s and the standing cadence's band "
        f"starts at {fleet_cfg.interval_seconds * _JITTER_LOW}s — they overlap, so "
        f"this test cannot tell a loop sleeping the tick from one sleeping the "
        f"cadence, which is the only thing it is for"
    )


def test_the_loops_tick_and_its_pacers_tolerance_are_one_number(
    fleet_cfg: Config, sent: dict[str, list], monkeypatch: pytest.MonkeyPatch
) -> None:
    """One expression read twice, rather than two that happen to agree today.

    `watch_loop` computes `tick` once and hands it to BOTH the sleep and the
    `Pacer`. If the two were derived separately the disagreement would be a loop
    waking at one rate while the schedule granted grace sized for another —
    `Pacer.due`'s tolerance is half a TICK, so a pacer that never received one
    falls back to half the standing default and lets a retailer fire a third of a
    cadence early, every cadence.

    THE ROSTER IS ASSERTED HERE TOO. It must be the CONFIGURED retailers, sorted
    — not whatever this cycle happens to be checking — because `slot_offset`
    derives each retailer's position from its index in it, and a roster that
    arrived in watch order would give the same fleet a different schedule
    depending on how `products.yaml` was typed.
    """
    built: list[dict] = []
    real_pacer = cli.Pacer

    class _Capturing(real_pacer):  # type: ignore[valid-type,misc]
        def __init__(self, **kwargs: object) -> None:
            built.append(dict(kwargs))
            super().__init__(**kwargs)

    monkeypatch.setattr(cli, "Pacer", _Capturing)

    delays: list[float] = []
    state = State.load(fleet_cfg.state_path)
    cli.watch_loop(
        fleet_cfg,
        _checker(Availability.OUT_OF_STOCK),
        state,
        cycles=4,
        sleep=delays.append,
    )

    assert len(built) == 1, (
        f"the loop built {len(built)} pacers; the backoff is memory and a pacer "
        f"rebuilt per cycle would forget every refusal"
    )
    # `.get` rather than `[...]`, so a loop that stopped passing these fields at
    # all fails with the sentence below rather than with a `KeyError` naming the
    # test's own dictionary. Measured: it does, and a KeyError is what this read
    # produced before the change.
    assert built[0].get("roster") == tuple(sorted(_FLEET)), (
        f"the loop handed its pacer roster {built[0].get('roster')!r}, not the "
        f"sorted configured retailers {tuple(sorted(_FLEET))} — every retailer's "
        f"position on the schedule is its index in this tuple, and a pacer that "
        f"never receives one gives every retailer the same position"
    )
    assert built[0].get("tick") == _FLEET_TICK_SECONDS, (
        f"the loop handed its pacer a tick of {built[0].get('tick')!r} against the "
        f"{_FLEET_TICK_SECONDS}s six retailers on a "
        f"{fleet_cfg.interval_seconds}s cadence produce; a pacer with no tick "
        f"falls back to half the standing default for its grace"
    )

    # THE TWO READERS OF THAT ONE NUMBER, joined by an assertion rather than by
    # a comment: every delay the loop asked for is the band around the same tick
    # the pacer was given.
    handed = built[0]["tick"]
    for i, d in enumerate(delays):
        assert handed * _JITTER_LOW <= d <= handed * _JITTER_HIGH, (
            f"wake {i} slept {d:.3f}s, which is not the jitter band around the "
            f"{handed}s tick the pacer was built with — the loop's wake rate and "
            f"the schedule's tolerance have become two numbers"
        )


# --------------------------------------------------------------------------
# REQ-23: the empty tick is REACHABLE, and what it publishes
# --------------------------------------------------------------------------
#
# `tests/test_status.py`'s REQ-23 section proves the empty pass is HANDLED, by
# calling `status.write` with an empty health list directly. That is a guard,
# and a guard nobody can reach is a guard with no subject. This section supplies
# the subject: the loop, at the tick it ships, driving itself onto a wake where
# `Pacer.due` says no to every one of the six configured retailers.
#
# WHERE THE IDLE WAKES COME FROM — MEASURED 2026-09-01, AND THE FIRST TWO
# ANSWERS THIS SECTION GAVE WERE BOTH WRONG. Recorded in order, because the
# corrections are the finding.
#
# The first form used `fleet_cfg` — six retailers, all on the 300 s global
# cadence — for 24 wakes, and every wake asked exactly one:
#
#     retailers asked per wake was [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
#                                   1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
#
# so the reachability assertion failed. Six retailers at 300 s laid on a 50 s
# grid fill 6 x 50 = 300 s exactly: the grid is SATURATED and every slot is
# claimed every cadence. The idle wakes come from the retailers on LONGER
# cadences — `amazon` at 1800 s and `gamestop` at 900 s hold a slot each and use
# it once every 36 and 18 wakes, leaving it empty the rest of the time. The idle
# tick is therefore a consequence of the fleet's SHAPE and not of the tick
# alone, exactly as `09-02` recorded that single-retailer fixtures cannot reach
# the tick at all.
#
# THE SECOND ANSWER — "under a uniform fleet the idle wake does not exist" — was
# written down, and it is FALSE. It survived one unseeded run and died on the
# next: a later run of the same 24 wakes produced
#
#     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1]
#
# The loop jitters every wake by +/-15%, so a wake can drift past a slot's
# tolerance (half a tick, 25 s), skip it, and the next wake collects two. Idle
# wakes exist on a uniform fleet too; they are just rare and accidental rather
# than structural. An `== [1] * 24` assertion would have been a flake shipped as
# a gate — which is what an unseeded jitter measurement read once always is.
#
# THE MEASUREMENT THAT REPLACED BOTH, over 20 seeds x 200 wakes each:
#
#     fleet        idle-rate min   max     mean    first idle wake
#     uniform          0.015   0.075   0.035    7 to 122, varies by seed
#     configured       0.250   0.285   0.269    6 in 19 seeds of 20, else 7
#
# So: structural on the configured fleet, accidental on the uniform one, by an
# order of magnitude, and the configured fleet reaches its first idle wake at 6
# under every seed tried. `09-03` derived 432 of 1728 (25.0%) analytically over
# an unjittered day; the 26.9% here is a jittered simulation of the same fleet.
# Two instruments, agreeing — not one number quoted twice.
#
# THE SEED IS LICENSED BY THAT SWEEP RATHER THAN HIDING BEHIND IT. Both tests
# below seed the loop's jitter so a red is reproducible, and the sweep above is
# the evidence that the seeded sequence is typical rather than the one that
# happened to work.
#
# `fleet_cfg` IS LEFT EXACTLY AS 09-03 BUILT IT. Its two tests are about the
# loop's sleep and the pacer's construction, where the overrides are irrelevant,
# and re-pointing a fixture underneath somebody else's evidence is how a green
# suite stops describing what it described.

#: `config/products.yaml`'s two non-default cadences, written out here for the
#: reason `_FLEET` and `_FLEET_TICK_SECONDS` are: these tests are about the LOOP,
#: and a config read would make a failure ambiguous between the two. The same
#: pair is bound to the real file by `tests/test_pacing.py`'s `_FLEET_INTERVALS`
#: assertion, so the copy cannot drift unnoticed.
_FLEET_OVERRIDES = {"amazon": 1800, "gamestop": 900}

#: One stated seed for the loop's `random.uniform` jitter, so a red here is
#: reproducible. NOT a proof over all sequences, and the section comment above
#: carries the 20-seed sweep that says so.
_IDLE_SEED = 20260901

#: How many wakes the sweep above measured each fleet over. Kept at 200 in the
#: comparison test so the rates below are read off the same denominator the
#: sweep used.
_IDLE_WAKES = 200


@pytest.fixture
def configured_fleet_cfg(fleet_cfg: Config) -> Config:
    """`fleet_cfg` plus the cadences `config/products.yaml` actually configures.

    This is the shape the daemon runs, and it is the shape in which the idle
    wake is STRUCTURAL rather than a jitter accident — see the section comment
    above for the two measurements that forced this fixture into being.
    """
    return replace(fleet_cfg, retailer_intervals=dict(_FLEET_OVERRIDES))


def _asked_per_wake(cfg: Config, cycles: int, seed: int) -> list[int]:
    """Drive `watch_loop` and record how many retailers each wake actually asked.

    Read through the loop's own `sleep`, which `watch_loop` calls immediately
    after `watch_cycle` has published — so each reading is one wake's document,
    in order, exactly as the daemon would have written it.
    """
    counts: list[int] = []

    def _count(_delay: float) -> None:
        payload = json.loads(cfg.status_path.read_text())
        counts.append(sum(1 for r in payload["retailers"] if r["checked"]))

    random.seed(seed)
    cli.watch_loop(
        cfg, _checker(Availability.OUT_OF_STOCK), State.load(cfg.state_path), cycles=cycles, sleep=_count
    )
    return counts


def test_the_idle_wake_is_structural_on_the_configured_fleet_and_incidental_on_a_uniform_one(
    fleet_cfg: Config, configured_fleet_cfg: Config, sent: dict[str, list]
) -> None:
    """Why the reachability test needs its own fixture — asserted, not asserted about.

    Both fleets are six retailers on the same 50 s tick and the same seed. The
    only difference is that one of them carries `config/products.yaml`'s two
    longer cadences. That difference is worth an order of magnitude in how often
    the monitor wakes and asks nobody, and it is the whole reason the empty-pass
    verdict had to be fixed in this phase rather than left as the rarity it was.

    A reader who "simplified" the test below back onto `fleet_cfg` would get a
    run that passes without reaching the case it exists for. This is the
    assertion that stops that.
    """
    uniform = _asked_per_wake(fleet_cfg, _IDLE_WAKES, _IDLE_SEED)
    configured = _asked_per_wake(configured_fleet_cfg, _IDLE_WAKES, _IDLE_SEED)

    uniform_rate = uniform.count(0) / _IDLE_WAKES
    configured_rate = configured.count(0) / _IDLE_WAKES

    assert configured_rate >= 0.20, (
        f"the configured fleet idled on {configured_rate:.1%} of {_IDLE_WAKES} "
        f"wakes, under the 20% floor. Measured 2026-09-01 over 20 seeds: 25.0% "
        f"to 28.5%, mean 26.9%, against 09-03's analytic 25.0% — so a rate this "
        f"low means the tick, the roster, the overrides or the schedule moved"
    )
    assert uniform_rate <= 0.10, (
        f"the uniform fleet idled on {uniform_rate:.1%} of {_IDLE_WAKES} wakes, "
        f"over the 10% ceiling. Six retailers at the {fleet_cfg.interval_seconds}s "
        f"global cadence claim all six slots of the {_FLEET_TICK_SECONDS}s grid, "
        f"so its idle wakes are jitter accidents — measured 1.5% to 7.5%, mean "
        f"3.5%. A uniform fleet idling this often is a saturated grid that "
        f"stopped being saturated"
    )
    assert configured_rate > uniform_rate * 2, (
        f"configured {configured_rate:.1%} against uniform {uniform_rate:.1%} — "
        f"the two fleets no longer differ in the way that makes "
        f"`configured_fleet_cfg` the only fixture this section can be run on"
    )


def test_a_wake_that_asks_nobody_is_reachable_at_the_shipping_tick(
    configured_fleet_cfg: Config, sent: dict[str, list]
) -> None:
    """The empty pass, reached rather than constructed — and what it publishes.

    THREE ASSERTIONS AND THEY ARE NOT THE SAME ONE. That an empty wake HAPPENS
    is what makes `T-09-04` live rather than theoretical. That every empty wake
    publishes `null` is the mitigation. That every NON-empty wake still publishes
    a real boolean is the over-reach guard, asserted here at the loop as well as
    at `status.write`, because a fix that withheld the verdict from every wake
    would satisfy the first two while taking the flag off the dashboard entirely.
    """
    published: list[dict] = []

    def _snapshot(_delay: float) -> None:
        published.append(json.loads(configured_fleet_cfg.status_path.read_text()))

    random.seed(_IDLE_SEED)
    cli.watch_loop(
        configured_fleet_cfg,
        _checker(Availability.OUT_OF_STOCK),
        State.load(configured_fleet_cfg.state_path),
        cycles=48,
        sleep=_snapshot,
    )

    assert len(published) == 48, published
    asked = [sum(1 for r in p["retailers"] if r["checked"]) for p in published]
    empty = [i for i, n in enumerate(asked) if n == 0]

    assert empty, (
        f"no wake in 48 asked nobody, so this test cannot be evidence that the "
        f"empty pass is reachable at the shipping tick — retailers asked per "
        f"wake was {asked}. Measured over 20 seeds on this fixture: the first "
        f"idle wake lands at 6 under 19 of them and at 7 under the twentieth"
    )
    for i in empty:
        assert published[i]["healthy"] is None, (
            f"wake {i} asked none of the six configured retailers and published "
            f"healthy={published[i]['healthy']!r}. That document is a record of "
            f"a check that never happened — T-09-04, and after 09-02 it is a "
            f"quarter of every day's documents rather than a rarity"
        )
    for i, n in enumerate(asked):
        if n:
            assert published[i]["healthy"] in (True, False), (
                f"wake {i} asked {n} retailer(s) and still withheld the verdict "
                f"({published[i]['healthy']!r}) — the empty-pass fix reached "
                f"into the wakes that DID check something, which takes the flag "
                f"off the dashboard rather than making it honest"
            )

    # AND THE FACTS UNDER THE WITHHELD VERDICT ARE STILL THERE. An idle tick
    # publishes no verdict; it does not publish an empty page. `07-04`'s rule —
    # one row per configured retailer, one per configured watch — is unchanged,
    # and this asserts it on the tick that would be the tempting place to skip
    # the write altogether.
    for i in empty:
        assert len(published[i]["retailers"]) == len(_FLEET), (
            f"wake {i} published {len(published[i]['retailers'])} retailer rows "
            f"of {len(_FLEET)}; withholding the verdict must not withhold the "
            f"rows under it"
        )
        assert len(published[i]["watches"]) == len(configured_fleet_cfg.watches)
        assert published[i]["duration_seconds"] is not None, (
            "an idle wake still TIMED its pass — the document says nothing was "
            "asked, not that nothing ran"
        )


# --------------------------------------------------------------------------
# REQ-23: the two failure thresholds are DURATIONS, and the tick changed
# --------------------------------------------------------------------------
#
# `09-DECISIONS.md` § *Collision 5*. `FAILURES_BEFORE_WARNING = 3` and
# `FAILURES_BEFORE_GIVING_UP = 10` are counts of CYCLES sized against a 300 s
# cycle — fifteen minutes to a warning, fifty to a give-up. 09-02 put the loop on
# a 50 s tick. Inherited as counts they would have fired SIX TIMES SOONER: 2.5
# minutes to a push, 8.3 to an exit.
#
# THE RESOLUTION TAKEN IS RE-DERIVATION, not acceptance, and the reasoning is at
# `cli.failures_before` rather than in a planning document. Both halves are worth
# a sentence here because they push the same way:
#
#   - The warning PUSHES TO A PHONE, and its own docstring earns that send by
#     arguing it is "RARE BY CONSTRUCTION". At 150 seconds it is not rare.
#   - The give-up exits non-zero so the supervisor restarts — and since 09-02 a
#     restart RE-PHASES every retailer, delaying some first checks by up to one
#     standing interval. So a restart costs MORE after this phase, at exactly the
#     moment the threshold would have started firing six times sooner.
#
# A DERIVED CONSTANT NOTHING CHECKS IS A CONSTANT THAT DRIFTS, so the derivation
# is asserted at both ticks and in both units — the count, and the wall clock it
# buys — rather than only at the one the daemon happens to run today.


def test_the_failure_thresholds_are_the_old_counts_at_the_old_cycle(cfg: Config) -> None:
    """The identity, and it is what keeps every other test in this file honest.

    At the 300 s reference cycle the derivation returns exactly the literals it
    was derived from. That is not a coincidence to be smiled at — it is why the
    single-retailer tests above still exercise the thresholds they were written
    against, and why this change has no behavioural effect on any fleet whose
    tick is still the standing cadence.
    """
    assert cli.failures_before(cli.WARN_AFTER_SECONDS, 300.0) == cli.FAILURES_BEFORE_WARNING
    assert cli.failures_before(cli.GIVE_UP_AFTER_SECONDS, 300.0) == cli.FAILURES_BEFORE_GIVING_UP
    assert (cli.WARN_AFTER_SECONDS, cli.GIVE_UP_AFTER_SECONDS) == (900.0, 3000.0), (
        "the two durations being preserved are 15 and 50 minutes; if these moved "
        "the preservation claim moved with them"
    )


def test_the_failure_thresholds_keep_their_wall_clock_at_the_new_tick() -> None:
    """The whole point, asserted in MINUTES and not only in cycles.

    A count is not a promise a reader can check. 18 failed cycles at 50 s is the
    same fifteen minutes 3 at 300 s was, and 60 is the same fifty — and stating
    it in the unit the promise is made in is what stops the next tick change
    being inherited silently the way this one nearly was.
    """
    tick = _FLEET_TICK_SECONDS

    warn = cli.failures_before(cli.WARN_AFTER_SECONDS, tick)
    give_up = cli.failures_before(cli.GIVE_UP_AFTER_SECONDS, tick)

    assert (warn, give_up) == (18, 60), (
        f"at the six-retailer fleet's {tick}s tick the thresholds derive to "
        f"{warn} and {give_up} cycles, not 18 and 60"
    )
    assert warn * tick / 60 == 15.0, (
        f"the monitor would now push to a phone after {warn * tick / 60:.1f} "
        f"minutes of total blindness rather than 15 — `_warn_monitor_is_stuck` "
        f"earns its send by being RARE, and that word is measured in time"
    )
    assert give_up * tick / 60 == 50.0, (
        f"the monitor would now exit non-zero after {give_up * tick / 60:.1f} "
        f"minutes rather than 50 — and since 09-02 a restart re-phases every "
        f"retailer, so restarting sooner costs more than it used to"
    )


def test_a_threshold_never_rounds_down_and_never_reaches_zero() -> None:
    """Two boundary properties, both of which fire in the unsafe direction.

    `ceil` rather than `round`: rounding down fires EARLIER than the stated
    duration, which is the thing being prevented. `max(1, ...)` because a tick
    longer than the duration must still cost at least one failed cycle — a
    threshold of 0 would push on a loop that has not failed at all.
    """
    assert cli.failures_before(900.0, 400.0) == 3, "2.25 cycles must round UP to 3"
    assert cli.failures_before(900.0, 901.0) == 1, "a tick past the duration still costs a cycle"
    assert cli.failures_before(900.0, 100000.0) == 1


def test_the_stuck_warning_waits_the_derived_count_on_the_shipping_fleet(
    configured_fleet_cfg: Config, sent: dict[str, list]
) -> None:
    """The derivation observed through the loop, not only at the function.

    Seventeen consecutive raising cycles on the fleet the daemon runs say
    nothing; the eighteenth pushes. Under the inherited count the third would
    have — which at a 50 s tick is 150 seconds of a transient fault reaching
    Dan's phone.
    """
    state = State.load(configured_fleet_cfg.state_path)

    cli.watch_loop(
        configured_fleet_cfg, _explodes(RuntimeError("boom")), state, cycles=17, sleep=lambda s: None
    )
    assert sent["health"] == [], (
        "the monitor pushed before 15 minutes of blindness had passed — 17 "
        "cycles at a 50s tick is 14 minutes"
    )

    cli.watch_loop(
        configured_fleet_cfg, _explodes(RuntimeError("boom")), State.load(configured_fleet_cfg.state_path), cycles=18, sleep=lambda s: None
    )
    assert sent["health"] == [["(all)"]], (
        "eighteen consecutive raising cycles at a 50s tick is fifteen minutes of "
        "a monitor that is running and not monitoring, and nothing was said"
    )


def test_the_loop_gives_up_on_the_derived_count_on_the_shipping_fleet(
    configured_fleet_cfg: Config, sent: dict[str, list]
) -> None:
    """Bounded on both sides, at the tick the daemon ships.

    59 failed cycles is still "keep trying"; 60 is fifty minutes and the exit
    code systemd can act on. Asserted on both sides because a threshold checked
    only from above passes for a loop that gives up immediately.
    """
    state = State.load(configured_fleet_cfg.state_path)
    assert (
        cli.watch_loop(
            configured_fleet_cfg, _explodes(RuntimeError("boom")), state, cycles=59, sleep=lambda s: None
        )
        == 0
    ), "the loop gave up before fifty minutes had passed"

    assert (
        cli.watch_loop(
            configured_fleet_cfg,
            _explodes(RuntimeError("boom")),
            State.load(configured_fleet_cfg.state_path),
            cycles=60,
            sleep=lambda s: None,
        )
        == 1
    ), "sixty failed cycles at a 50s tick is fifty minutes and the loop kept going"


# --------------------------------------------------------------------------
# Criterion 4, first half: per-retailer cadence and Phase 8's backoff still hold
# --------------------------------------------------------------------------
#
# "No regression in what already works" is a claim about Phase 8's BEHAVIOURS
# surviving Phase 9's change, and it is asserted here rather than inferred from a
# green suite. Two things make that harder than it sounds and both are named
# before anything is run.
#
# FIRST: SEVERAL OF PHASE 8'S TESTS WERE ADJUSTED IN 09-02, so "unchanged" is the
# wrong question. `09-02-SUMMARY.md` enumerated them and 09-04 re-measured the
# enumeration against the whole phase (`87871b4..HEAD`) by comparing each test's
# source segment rather than trusting the list:
#
#     RE-POINTED ASSERTIONS — the behaviour is unchanged and only the
#     arithmetic's anchor moved, because `record` steps from the retailer's own
#     previous due time instead of re-anchoring to the cycle's clock:
#       1. test_pacing::test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring
#       2. test_pacing::test_the_backoff_schedule_is_exactly_the_schedule_it_was[300.0]
#       3. test_pacing::…[1800.0]
#       4. test_pacing::test_one_good_read_clears_the_backoff_completely
#       5. test_pacing::test_a_retailer_that_answers_during_its_probe_is_back_on_its_standing_interval_at_once
#       6. test_cli_watch::test_a_retailer_in_cooloff_publishes_the_days_scale_cadence_it_is_actually_on
#
#     DATED REVERSALS — a withdrawn claim, quoted in full with what overruled it:
#       9.  test_pacing::test_a_retailer_at_the_default_cadence_is_due_every_cycle
#       10. test_pacing::test_the_restored_pacer_starts_its_schedule_from_zero
#
# and no others. Of the four gates `09-04-PLAN.md` names, THREE CAME THROUGH
# BYTE-IDENTICAL — the cool-off literal-seconds table, the exactly-one-probe
# simulation, and four of the five restart tests — while
# `test_one_good_read_clears_the_backoff_completely` is a re-pointed assertion
# and `test_the_restored_pacer_starts_its_schedule_from_zero` is a dated
# reversal. No repair weakens a Phase 8 claim: the `MAX_BACKOFF_SECONDS <= 6h`
# ceiling, the 259200.0 cool-off literal at every site, and the depth literals in
# `_CADENCE_AFTER_N_REFUSALS` are all untouched.
#
# SECOND, AND IT IS THE HALF THAT WOULD HAVE MADE THIS SWEEP TAUTOLOGICAL: most
# of `tests/test_pacing.py` builds a `Pacer` with NO ROSTER AND NO TICK. Such a
# pacer gets a phase of 0.0 for every retailer and sizes `due`'s tolerance off
# the standing default — so the tolerance and the birth phase are DEFAULTED AWAY
# on those sites, and `cli.watch_loop` never builds one that way. 09-02 measured
# exactly what that costs: `test_the_max_retailers_in_any_sixty_seconds_over_a_
# day_is_a_stated_number` "still read 6 against the landed mechanism … it went
# red only once its pacer was given a roster and a tick."
#
# `record`'S GRID ADVANCE IS UNCONDITIONAL, and that is stated rather than
# assumed either way: it is not gated behind a non-empty roster, which is why the
# defaulted sites DID redden and why 09-02 had to repair seven of them. So those
# sites exercise half the mechanism honestly. What they cannot reach is the other
# half, and this section is that half — every assertion below builds the pacer
# the way `watch_loop` builds one, or drives `watch_loop` itself.


def _shipping_pacer(cfg: Config) -> Pacer:
    """A `Pacer` constructed exactly the way `cli.watch_loop` constructs one.

    Roster and tick both present, from the same two expressions the loop uses.
    Not a copy of the loop's arithmetic: `loop_tick_seconds` is imported and the
    roster is derived from `cfg.watches`, so a change to either reaches here.
    """
    roster = tuple(sorted({w.retailer for w in cfg.watches}))
    return Pacer(
        default_interval=cfg.interval_seconds,
        overrides=dict(cfg.retailer_intervals),
        roster=roster,
        tick=loop_tick_seconds(cfg.interval_seconds, roster),
    )


def test_the_shipping_pacer_is_built_the_way_the_loop_builds_one(
    configured_fleet_cfg: Config, sent: dict[str, list], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The helper above is bound to the loop, so this section cannot drift off it.

    A sweep whose "shipping construction" was a hand-written imitation would keep
    passing after the loop stopped constructing pacers that way — which is the
    single-retailer-fixture finding one level up.
    """
    built: list[dict] = []
    real = cli.Pacer

    class _Capturing(real):  # type: ignore[valid-type,misc]
        def __init__(self, **kwargs: object) -> None:
            built.append(dict(kwargs))
            super().__init__(**kwargs)

    monkeypatch.setattr(cli, "Pacer", _Capturing)
    cli.watch_loop(
        configured_fleet_cfg,
        _checker(Availability.OUT_OF_STOCK),
        State.load(configured_fleet_cfg.state_path),
        cycles=1,
        sleep=lambda s: None,
    )

    mine = _shipping_pacer(configured_fleet_cfg)
    assert built[0].get("roster") == mine.roster
    assert built[0].get("tick") == mine.tick
    assert built[0].get("default_interval") == mine.default_interval
    assert built[0].get("overrides") == dict(configured_fleet_cfg.retailer_intervals)


def test_each_retailer_is_asked_the_same_number_of_times_a_day_as_before(
    configured_fleet_cfg: Config, sent: dict[str, list]
) -> None:
    """Criterion 4's first half, driven through `cli.watch_loop` over a whole day.

    NOT through a `Pacer` simulation. Every other statement of this claim in the
    suite steps the pacer directly; this one runs the daemon's own loop for the
    1728 wakes a 50 s tick makes in 86 400 s and counts what reached
    `status.json` as `checked: true`. The literals are `09-DECISIONS.md`'s
    recorded BEFORE-numbers, measured on 2026-09-01 against the pre-REQ-23 rule
    at `87871b4` — so this is a comparison against the old schedule and not a
    re-derivation from the new one.

    THE REDUCTION-BY-NOT-ASKING GUARD. 09-02 recorded that the max-in-60s literal
    is BLIND to a fleet asked half as often — it still read 2 while every count
    halved. The per-retailer counts are what is not blind to it, and criterion 4
    is the criterion they answer.
    """
    counted: dict[str, int] = {}

    def _count(_delay: float) -> None:
        for row in json.loads(configured_fleet_cfg.status_path.read_text())["retailers"]:
            if row["checked"]:
                counted[row["retailer"]] = counted.get(row["retailer"], 0) + 1

    random.seed(_IDLE_SEED)
    cli.watch_loop(
        configured_fleet_cfg,
        _checker(Availability.OUT_OF_STOCK),
        State.load(configured_fleet_cfg.state_path),
        cycles=_WAKES_PER_DAY,
        sleep=_count,
    )

    assert dict(sorted(counted.items())) == _BEFORE_PER_RETAILER_PER_DAY, (
        f"over a simulated day the loop asked {dict(sorted(counted.items()))}, "
        f"against the {_BEFORE_PER_RETAILER_PER_DAY} the OLD rule produced. A "
        f"schedule spread out by asking less often is coverage sold for a number"
    )
    assert sum(counted.values()) == 1296, (
        f"{sum(counted.values())} requests over a simulated day against 1296 — "
        f"the total the retailers can see, and the row 09-03 recorded as the one "
        f"that did not move"
    )


#: 86 400 s of simulated day at the six-retailer fleet's 50 s tick. Written out
#: rather than computed for `_FLEET_TICK_SECONDS`'s reason.
_WAKES_PER_DAY = 1728

#: PHASE 8'S THREE NUMBERS, WRITTEN OUT, AND THE SECOND DRAFT OF THIS SECTION
#: DID NOT DO THIS — which is the finding these three lines exist to record.
#:
#: The cool-off assertions below originally read `REFUSALS_BEFORE_COOLOFF` and
#: `COOLOFF_SECONDS` from `boty.pacing`. Perturbing `REFUSALS_BEFORE_COOLOFF`
#: from 30 to 31 left **60 passed, 0 failed**: every assertion moved with the
#: constant it was supposed to be checking, so the gate could not fail for the
#: reason it exists. That is `_CADENCE_ACROSS_THE_COOLOFF_THRESHOLD`'s own rule
#: — "a number derived from the constant under test cannot contradict it" —
#: rediscovered by measurement rather than inherited.
#:
#: Written out, the same perturbation reddens. The module constants are still
#: BOUND to these literals, immediately below, so the two cannot drift apart
#: silently; what changed is which of them is the authority.
_COOLOFF_THRESHOLD_REFUSALS = 30
_COOLOFF_SECONDS_LITERAL = 259200.0
_MAX_BACKOFF_LITERAL = 21600.0


def test_phase_eights_three_numbers_are_the_numbers_this_section_asserts() -> None:
    """The binding between the literals above and the constants they describe.

    Separate from the behaviour tests deliberately. If `boty.pacing` moves one of
    these, exactly this test says so — rather than five behavioural assertions
    failing in five different sentences about backoff.
    """
    assert REFUSALS_BEFORE_COOLOFF == _COOLOFF_THRESHOLD_REFUSALS
    assert float(COOLOFF_SECONDS) == _COOLOFF_SECONDS_LITERAL
    assert float(MAX_BACKOFF_SECONDS) == _MAX_BACKOFF_LITERAL

#: `09-DECISIONS.md`'s recorded before-numbers, measured at `87871b4` against the
#: PRE-REQ-23 rule. Literals rather than `86400 // interval` arithmetic: a number
#: derived from the config under test cannot contradict the config under test,
#: and these have to be comparable to something the old code produced.
_BEFORE_PER_RETAILER_PER_DAY = {
    "amazon": 48,
    "bestbuy": 288,
    "gamestop": 96,
    "nintendo": 288,
    "target": 288,
    "walmart": 288,
}


def test_the_backoff_ladder_and_the_cooloff_hold_under_the_shipping_construction(
    configured_fleet_cfg: Config,
) -> None:
    """Phase 8's literal seconds, on the pacer the daemon builds rather than a bare one.

    The three literals are Phase 8's own and are written out here rather than
    imported from `_CADENCE_AFTER_N_REFUSALS`, so this cannot agree with that
    table by construction — it has to agree with it by both being right.

    Read as an INCREMENT from the retailer's own previous due time, which is
    09-02's re-pointing: `record` steps the grid rather than re-anchoring on the
    cycle clock, so `due_at - now` at a frozen clock is the sum of every wait
    rather than the last one. The claim asserted is the one Phase 8 always made.
    """
    p = _shipping_pacer(configured_fleet_cfg)

    # One refusal on the 300 s standing group: 300 x 2 = 600.
    previous = p._for("walmart").due_at
    p.record("walmart", refused=True, now=0.0)
    assert p._for("walmart").due_at - previous == 600.0
    assert p.current_interval("walmart") == 600.0

    # Climbing to the six-hour ceiling and staying there.
    for _ in range(12):
        p.record("walmart", refused=True, now=0.0)
    assert p.current_interval("walmart") == _MAX_BACKOFF_LITERAL, (
        f"the backoff ceiling read {p.current_interval('walmart')} on a pacer "
        f"built the way the daemon builds one, against {_MAX_BACKOFF_LITERAL}"
    )
    previous = p._for("walmart").due_at
    p.record("walmart", refused=True, now=0.0)
    assert p._for("walmart").due_at - previous == _MAX_BACKOFF_LITERAL

    # And the cool-off past thirty consecutive refusals.
    while p._for("walmart").refusals < _COOLOFF_THRESHOLD_REFUSALS:
        p.record("walmart", refused=True, now=0.0)
    assert p.current_interval("walmart") == _COOLOFF_SECONDS_LITERAL, (
        f"the cool-off read {p.current_interval('walmart')} against the "
        f"{_COOLOFF_SECONDS_LITERAL} s (three days) Phase 8 fixed"
    )

    # One good read clears it completely — one standing interval on, not a
    # fraction of the backoff still being paid off.
    previous = p._for("walmart").due_at
    p.record("walmart", refused=False, now=0.0)
    assert p._for("walmart").refusals == 0
    assert p.current_interval("walmart") == 300.0
    assert p._for("walmart").due_at - previous == 300.0


def test_a_cooled_off_retailer_is_probed_exactly_once_over_a_window_at_the_new_tick(
    configured_fleet_cfg: Config,
) -> None:
    """Phase 8's exactly-one-probe property, on the pacer the daemon builds.

    The property is a bound in BOTH directions, and the tick is what makes
    re-asserting it here worth the lines: the loop wakes six times more often
    than the cycle this was measured on, so a cool-off that leaked would leak six
    times faster, and a schedule that dropped the retailer would drop it just as
    silently.

    STEPPED AT THE LOOP'S OWN TICK, on a pacer with roster and tick present —
    `tests/test_pacing.py`'s copy of this property steps a DEFAULTED pacer at the
    standing cadence, which is neither the wake rate nor the construction the
    daemon runs.

    NOT DRIVEN THROUGH `watch_loop`, and that is a measured cost rather than a
    preference. Climbing to the thirtieth consecutive refusal takes about 700 000
    simulated seconds, and one further cool-off window is 259 200 more — roughly
    20 000 wakes, which through the loop is 20 000 `status.json` writes and a
    full check pass each. Measured at 6000 wakes: 3.9 s, and it had reached only
    19 refusals. `test_each_retailer_is_asked_the_same_number_of_times_a_day_as_
    before` above is the loop-driven evidence; this is the schedule's.
    """
    p = _shipping_pacer(configured_fleet_cfg)
    tick = p.tick
    assert tick == _FLEET_TICK_SECONDS, tick
    refusing = "walmart"

    now = 0.0
    dispatches = 0
    # Climb to the cool-off, asking only when the schedule says to — which is
    # what makes the wall-clock arithmetic below the schedule's and not a
    # simulation of it.
    while p._for(refusing).refusals < _COOLOFF_THRESHOLD_REFUSALS:
        if p.due(refusing, now):
            p.record(refusing, refused=True, now=now)
            dispatches += 1
        now += tick
        assert now < 2_000_000, "never reached the cool-off threshold"

    assert dispatches == _COOLOFF_THRESHOLD_REFUSALS
    assert p.current_interval(refusing) == _COOLOFF_SECONDS_LITERAL

    # One window and a bit: longer than 259 200 s so the probe must happen,
    # shorter than two so a second probe is a failure rather than the next
    # window's first.
    began, probes = now, 0
    while now - began < _COOLOFF_SECONDS_LITERAL * 1.15:
        if p.due(refusing, now):
            p.record(refusing, refused=True, now=now)
            probes += 1
        now += tick

    assert probes == 1, (
        f"across {(now - began) / 3600:.1f} simulated hours after the thirtieth "
        f"consecutive refusal the schedule dispatched {refusing} {probes} "
        f"time(s). Phase 8 fixed that at exactly one — not dropped, and not "
        f"probed twice"
    )
