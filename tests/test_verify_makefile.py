"""`make verify` — the exit-code contract everything downstream is built on.

Every phase of this project states its success criteria as "`make verify` exits
non-zero if any check fails", so the recipe itself needs testing. Reading it and
agreeing it looks right is not evidence: a pipeline takes the status of its last
command, a `-` prefix discards a failure, and a recursive `$(MAKE)` that loses a
variable produces a green run that checked something else. All three are silent.

These tests run the REAL Makefile against a stub interpreter, so no venv, no
network and no test suite are involved — only the control flow. The stub's exit
code is set per-case, which is the only way to exercise the failure branches
without breaking something for real.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MAKEFILE = REPO_ROOT / "Makefile"

pytestmark = pytest.mark.skipif(
    shutil.which("make") is None, reason="`make` is not installed, so `make verify` cannot be tested"
)

#: Stands in for $(PYTHON). Every stage succeeds except the live control check,
#: whose exit code comes from CONTROL_RC. It echoes its argv so a test can
#: assert which flags actually reached it.
_STUB = """\
#!/bin/sh
echo "stub: $*"
case "$*" in
  *control_check.py*--fixtures*) exit 0 ;;
  *control_check.py*)            exit "$CONTROL_RC" ;;
  *)                             exit 0 ;;
esac
"""


def _run(tmp_path: Path, target: str, control_rc: int) -> subprocess.CompletedProcess[str]:
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    stub = tmp_path / "stub-python"
    stub.write_text(_STUB, encoding="utf-8")
    stub.chmod(0o755)

    env = {**os.environ, "CONTROL_RC": str(control_rc)}
    # Scrubbed because this suite is itself usually run from `make test`, and an
    # inherited MAKEFLAGS/jobserver would change how the make under test behaves.
    for leaked in ("MAKEFLAGS", "MAKELEVEL", "MFLAGS", "MAKE_TERMOUT", "MAKE_TERMERR"):
        env.pop(leaked, None)

    return subprocess.run(
        ["make", "-C", str(tmp_path), target, f"PYTHON={stub}"],
        capture_output=True,
        text=True,
        env=env,
    )


def test_all_stages_green_is_a_pass(tmp_path: Path) -> None:
    proc = _run(tmp_path, "verify", control_rc=0)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "VERIFY: PASS" in proc.stdout
    assert "OFFLINE" not in proc.stdout


def test_a_skipped_live_check_does_not_produce_an_unqualified_pass(tmp_path: Path) -> None:
    """The only check that can detect a retailer change did not run — say so.

    Exiting 0 is right: a machine with no connectivity has not discovered a
    problem, and failing there would train everyone to ignore the check. But
    the verdict has to carry the caveat, or a run that verified nothing about
    any retailer is textually identical to a fully green one.
    """
    proc = _run(tmp_path, "verify", control_rc=3)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OFFLINE" in proc.stdout
    assert "live controls were NOT run" in proc.stdout


def test_a_failing_live_check_fails_verify(tmp_path: Path) -> None:
    """A skip must not be confused with a failure in the other direction."""
    proc = _run(tmp_path, "verify", control_rc=1)

    assert proc.returncode != 0
    assert "VERIFY: FAIL (live controls)" in proc.stdout
    assert "VERIFY: PASS" not in proc.stdout


def test_a_config_error_from_the_control_check_fails_verify(tmp_path: Path) -> None:
    """Exit 2 is "no control watch configured" — a real failure, not a skip.

    Pinned separately because the skip branch matches on a specific code: a
    `case` arm written as `0|3|*)` or a `>= 3` comparison would swallow this.
    """
    proc = _run(tmp_path, "verify", control_rc=2)

    assert proc.returncode != 0
    assert "VERIFY: FAIL (live controls)" in proc.stdout
    assert "VERIFY: PASS" not in proc.stdout


def test_verify_offline_propagates_the_offline_flag(tmp_path: Path) -> None:
    """`verify-offline` delegates through two levels of recursive make.

    A lost variable here would silently run the LIVE control check in CI while
    reporting the offline verdict.
    """
    proc = _run(tmp_path, "verify-offline", control_rc=3)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "control_check.py --offline" in proc.stdout
    assert "OFFLINE" in proc.stdout
