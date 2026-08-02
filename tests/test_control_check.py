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
from pathlib import Path
from typing import Any, Callable

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
