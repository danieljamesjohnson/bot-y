"""`scripts/control_check.py` — the gate `make verify` trusts.

This script is the only check in `make verify` that can tell you a retailer
changed its page. Everything downstream is built on believing its exit code, so
the exit code itself needs testing: a verify that prints a verdict nobody has
checked is worse than no verify at all.

Two properties are pinned here, and both are about the *number* rather than the
prose next to it:

- A retailer with product watches and no control must FAIL. `assess_health`
  already implements that rule, and the acceptance criteria state it, but the
  gate never consulted it — so `make verify` went green while a detector had
  never been verified by anything.
- A skipped live check must not be reported as a pass. "We could not check"
  and "we checked and it was fine" have to be distinguishable to a machine,
  not just to a human reading stdout.

Nothing here touches the network: conftest's guard blocks the socket layer, so
a regression that started making live requests from these tests would raise
rather than quietly slow the suite down.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from boty.models import Availability, Result, Watch

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = REPO_ROOT / "scripts" / "control_check.py"


def _load() -> Any:
    """Import control_check by path — `scripts/` is not a package."""
    spec = importlib.util.spec_from_file_location("control_check_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


control_check = _load()


_CONFIG = """\
settings:
  first_party_only: true
watches:
{watches}
"""

_WATCH = """\
  - name: {name}
    retailer: {retailer}
    target: https://{retailer}.example/{name}
    control: {control}
"""


def _write_config(tmp_path: Path, watches: list[tuple[str, str, bool]]) -> str:
    body = "".join(
        _WATCH.format(name=name, retailer=retailer, control=str(control).lower())
        for name, retailer, control in watches
    )
    path = tmp_path / "products.yaml"
    path.write_text(_CONFIG.format(watches=body), encoding="utf-8")
    return str(path)


def _stub_checker(
    monkeypatch: pytest.MonkeyPatch,
    availability: Availability = Availability.IN_STOCK,
) -> list[str]:
    """Replace the live checker. Returns the list of watch keys it was asked about."""
    called: list[str] = []

    def _make(cfg: object) -> Callable[[Watch], Result]:
        def _check(watch: Watch) -> Result:
            called.append(watch.key)
            return Result(watch, availability, price=1.0, detail="stub")

        return _check

    monkeypatch.setattr(control_check, "_make_checker", _make)
    return called


# --------------------------------------------------------------------------
# A retailer with no control at all
# --------------------------------------------------------------------------


def test_a_retailer_with_no_control_watch_fails_the_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`make verify` must not go green over an unverified detector.

    The script used to fail only in the all-or-nothing case — zero controls
    across the whole config. A retailer with product watches and no control was
    invisible to it, so a `target` adapter that had never parsed a real page
    once produced "control check: PASS — 1/1 controls in stock" and exit 0.
    REQ-06 exists to close precisely this gap, and Phase 2 adds three more
    adapters through the same door.
    """
    _stub_checker(monkeypatch)
    config = _write_config(
        tmp_path,
        [
            ("goplusplus", "target", False),  # product watch, no control anywhere for target
            ("ps5", "gamestop", True),
        ],
    )

    assert control_check.check_controls(config) == 2


def test_the_unverified_retailer_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A failure you cannot act on gets ignored — say which retailer is bare."""
    _stub_checker(monkeypatch)
    config = _write_config(
        tmp_path, [("goplusplus", "target", False), ("ps5", "gamestop", True)]
    )

    control_check.check_controls(config)

    assert "target" in capsys.readouterr().err


def test_the_gate_refuses_before_making_any_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The config is wrong regardless of what the retailers say today.

    Checking it first means the failure is instant and deterministic instead of
    arriving after a round of live fetches that were never going to change the
    answer.
    """
    called = _stub_checker(monkeypatch)
    config = _write_config(
        tmp_path, [("goplusplus", "target", False), ("ps5", "gamestop", True)]
    )

    control_check.check_controls(config)

    assert called == []


def test_every_retailer_covered_by_a_control_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The control case: this must not become a gate nothing can satisfy."""
    called = _stub_checker(monkeypatch)
    config = _write_config(
        tmp_path,
        [
            ("goplusplus", "gamestop", False),
            ("ps5", "gamestop", True),
            ("goplusplus", "walmart", False),
            ("milk", "walmart", True),
        ],
    )

    assert control_check.check_controls(config) == 0
    assert called == ["gamestop:ps5", "walmart:milk"]


def test_no_controls_anywhere_still_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_checker(monkeypatch)
    config = _write_config(tmp_path, [("goplusplus", "gamestop", False)])

    assert control_check.check_controls(config) == 2


def test_a_control_not_reading_in_stock_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The original contract, still intact: a broken detector is a failure."""
    _stub_checker(monkeypatch, Availability.OUT_OF_STOCK)
    config = _write_config(tmp_path, [("ps5", "gamestop", True)])

    assert control_check.check_controls(config, retries=0) == 1


# --------------------------------------------------------------------------
# "This host cannot run that control" is not "that detector is broken"
# --------------------------------------------------------------------------


def _stub_failing_checker(monkeypatch: pytest.MonkeyPatch, detail: str) -> None:
    """A checker whose control comes back UNKNOWN with a given detail."""

    def _make(cfg: object) -> Callable[[Watch], Result]:
        def _check(watch: Watch) -> Result:
            return Result(watch, Availability.UNKNOWN, detail=detail)

        return _check

    monkeypatch.setattr(control_check, "_make_checker", _make)


@pytest.mark.parametrize("gap", control_check.HOST_GAPS)
def test_a_control_that_cannot_run_on_this_host_is_not_a_detector_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, gap: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """A fresh clone that follows the README failed the gate, and was told the
    extractor had broken.

    The shipped config carries a mandatory Best Buy control whose only
    credential-free path is rung 3. Rung 3 needs the `browser` extra *and* a
    Chrome binary, and neither comes with `dev` — deliberately: nodriver is
    AGPL-3.0 to this project's MIT and a contributor working on the HTTP
    retailers must never be made to pull a browser stack (recorded in STATE.md).
    So a contributor runs `pip install -e '.[dev]'`, runs `make verify`, and is
    told "This is a statement about the DETECTOR... the extractor has stopped
    matching", with instructions to re-capture a fixture.

    That diagnosis is wrong in exactly the way this phase already fixed twice,
    for the Imperva and the Akamai walls: a refusal that has nothing to do with
    our parser, reported as our parser. Here it is not even a refusal — it is a
    missing optional dependency on the machine doing the asking.
    """
    _stub_failing_checker(monkeypatch, f"fetch failed: {gap} (ImportError: no module)")
    config = _write_config(tmp_path, [("pikachu", "bestbuy", True)])

    rc = control_check.check_controls(config, retries=0)
    out = capsys.readouterr()

    assert rc == control_check.INCOMPLETE, (
        f"exit {rc}: a control that could not run on this host was reported as "
        "a detector failure"
    )
    assert "statement about the DETECTOR" not in out.err, (
        "the gate still blames the extractor for a missing optional dependency"
    )
    assert "extractor has stopped matching" not in out.err
    assert "capture-fixture" not in out.err, (
        "still telling the reader to re-capture a fixture for a page it never fetched"
    )
    assert "THIS HOST" in out.out + out.err, "the real cause is not named"
    assert "[browser]" in out.err, "the actionable next step is not given"


def test_a_real_detector_failure_still_fails_even_beside_a_host_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The direction that must not regress while fixing the other one.

    If a host gap downgraded the whole run, one missing Chrome would mask a
    genuinely broken GameStop detector — turning a fix for a false red into a
    machine for false greens, which is far worse than what it replaced.
    """

    def _make(cfg: object) -> Callable[[Watch], Result]:
        def _check(watch: Watch) -> Result:
            if watch.retailer == "bestbuy":
                return Result(
                    watch,
                    Availability.UNKNOWN,
                    detail=f"fetch failed: {control_check.HOST_GAPS[0]} (ImportError)",
                )
            return Result(watch, Availability.OUT_OF_STOCK, detail="ld+json: OutOfStock")

        return _check

    monkeypatch.setattr(control_check, "_make_checker", _make)
    config = _write_config(
        tmp_path, [("pikachu", "bestbuy", True), ("ps5", "gamestop", True)]
    )

    assert control_check.check_controls(config, retries=0) == 1


def test_a_blocked_retailer_is_still_a_failure_not_a_host_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Being turned away by a retailer is the monitor not working.

    The script's own docstring draws this line: "Connectivity present, but a
    control does not read IN_STOCK — including a fetch failure or a bot wall
    from the retailer: FAIL. Being blocked by Walmart is not an infrastructure
    hiccup." A host-gap carve-out that swallowed bot walls would hide the exact
    failure this gate exists to catch.
    """
    _stub_failing_checker(monkeypatch, "blocked: challenge page matched 'robot or human' (HTTP 200)")
    config = _write_config(tmp_path, [("milk", "walmart", True)])

    assert control_check.check_controls(config, retries=0) == 1


def test_the_host_gap_markers_are_the_strings_the_browser_actually_produces(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """Otherwise this is a carve-out that can only ever fail silently.

    Classifying on prose is a bet that the prose does not drift. This closes
    that: it drives the real `fetch_rendered` failure paths and asserts each
    produced detail is recognised, so rewording a message in `boty.browser`
    fails here rather than quietly restoring the wrong diagnosis.
    """
    from boty import browser, retailers
    from boty.models import Watch as W

    watch = W(name="c", retailer="bestbuy", target="6216393", control=True)

    for exc in (
        ImportError("No module named 'nodriver'"),
        FileNotFoundError("could not find a valid chrome browser binary"),
    ):
        monkeypatch.setattr(browser, "_render", _raiser(exc))
        result = retailers.check_bestbuy_browser(watch)

        assert control_check._is_host_gap(result), (
            f"{result.detail!r} is not recognised as a host gap — the markers in "
            "control_check have drifted from the messages boty.browser emits"
        )


def _raiser(exc: BaseException) -> Callable[..., str]:
    def _fake(*args: object, **kwargs: object) -> str:
        raise exc

    return _fake


# --------------------------------------------------------------------------
# A skip is not a pass
# --------------------------------------------------------------------------


def test_skipping_the_live_check_is_not_reported_as_success() -> None:
    """"We could not check" must be distinguishable from "we checked".

    The skip-when-offline policy is deliberate and correct — a check that fails
    because someone's wifi dropped gets ignored within a week. The defect was
    that the *verdict* carried no caveat: the script returned 0, so `make
    verify` printed "VERIFY: PASS" and exited 0, identical in every
    machine-readable respect to a run where the live controls actually passed.
    Phase success criteria are written as "`make verify` exits 0", so a run
    that verified nothing about any retailer was indistinguishable from a fully
    green one.
    """
    assert control_check.main(["--offline"]) == control_check.SKIPPED
    assert control_check.SKIPPED not in (0, 1, 2), (
        "the skip needs its own exit code: 0 is a pass, 1 is a control failure, "
        "2 is a config error"
    )


def test_no_connectivity_skips_rather_than_passing(monkeypatch: pytest.MonkeyPatch) -> None:
    """The residual risk WR-05 names: a host that cannot reach 1.1.1.1 or
    8.8.8.8 but can reach walmart.com fine skips a live check that would have
    failed. That is tolerable only if the skip is visible in the exit code."""
    monkeypatch.setattr(control_check, "have_connectivity", lambda: False)

    assert control_check.main([]) == control_check.SKIPPED


def test_the_fixture_report_still_exits_zero() -> None:
    """`--fixtures` warns and never fails — that is its whole contract."""
    assert control_check.main(["--fixtures"]) == 0
