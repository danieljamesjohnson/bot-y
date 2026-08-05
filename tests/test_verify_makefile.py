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
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MAKEFILE = REPO_ROOT / "Makefile"

pytestmark = pytest.mark.skipif(
    shutil.which("make") is None, reason="`make` is not installed, so `make verify` cannot be tested"
)

#: Stands in for $(PYTHON). Every stage succeeds except the two whose exit codes
#: come from the environment: the live control check reads CONTROL_RC and the
#: lint stage reads LINT_RC. Both are parameterised for the same reason — they
#: are the branches `verify` treats specially, and the only way to exercise a
#: failure path is to make the stage fail on demand rather than for real. It
#: echoes its argv so a test can assert which flags actually reached it, and
#: which stages were never reached at all.
#:
#: `lint` is matched here as `-m ruff` rather than as a bare `ruff`, because the
#: Makefile invokes it through the interpreter: a console-script invocation would
#: not route through this stub at all, and the stage could never be watched
#: failing.
_STUB = """\
#!/bin/sh
echo "stub: $*"
case "$*" in
  *control_check.py*--fixtures*) exit 0 ;;
  *control_check.py*)            exit "$CONTROL_RC" ;;
  *-m\\ ruff*)                    exit "$LINT_RC" ;;
  *)                             exit 0 ;;
esac
"""


def _run(
    tmp_path: Path, target: str, control_rc: int, *, lint_rc: int = 0
) -> subprocess.CompletedProcess[str]:
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    stub = tmp_path / "stub-python"
    stub.write_text(_STUB, encoding="utf-8")
    stub.chmod(0o755)

    env = {**os.environ, "CONTROL_RC": str(control_rc), "LINT_RC": str(lint_rc)}
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


def _recipe(makefile: str, target: str) -> str:
    """The recipe body of one target, read out of the real Makefile.

    Parsed rather than pattern-matched against the whole file so a stage
    mentioned in `help` or in a comment cannot be mistaken for a stage `verify`
    actually invokes.
    """
    lines = makefile.splitlines()
    for i, line in enumerate(lines):
        if re.match(rf"^{re.escape(target)}\s*:", line):
            body = []
            for follow in lines[i + 1 :]:
                if follow.startswith("\t"):
                    body.append(follow)
                elif follow.strip() == "" or follow.lstrip().startswith("#"):
                    continue
                else:
                    break
            return "\n".join(body)
    raise AssertionError(f"no `{target}` target in the Makefile")


def _stage_table(readme: Path) -> set[str]:
    """The backticked stage names in README's `| Stage | Proves |` table.

    Only the FIRST cell of each row is read. The `Proves` column is full of
    backticked things that are not stages — `mypy`, `ruff`, `pyproject.toml` —
    and scanning the whole row would quietly turn this gate into noise.
    """
    lines = readme.read_text(encoding="utf-8").splitlines()
    header = next(
        (n for n, line in enumerate(lines) if line.startswith("| Stage | Proves |")),
        None,
    )
    if header is None:
        raise AssertionError("no `| Stage | Proves |` table in README.md")

    stages: set[str] = set()
    for row in lines[header + 2 :]:  # +2 skips the |---|---| separator
        if not row.startswith("|"):
            break
        stages.update(re.findall(r"`([a-z-]+)`", row.split("|")[1]))
    return stages


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


def test_controls_that_could_not_run_here_pass_but_say_so(tmp_path: Path) -> None:
    """Exit 4: some controls ran and passed, others could not run on this host.

    The fresh-clone case. Exiting non-zero there told contributors their
    extractor was broken when the machine simply had no Chrome; exiting 0 with
    no caveat would claim a detector was verified that was never reached. It
    needs its own verdict for the same reason the offline skip does, and it must
    not borrow the offline wording — "live controls were NOT run" is false when
    three of four ran and passed.
    """
    proc = _run(tmp_path, "verify", control_rc=4)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "INCOMPLETE" in proc.stdout
    assert "VERIFY: FAIL" not in proc.stdout
    assert "OFFLINE" not in proc.stdout, "an incomplete run is not an offline run"


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


def test_a_failing_lint_fails_verify(tmp_path: Path) -> None:
    """A stage wired into `verify` whose failure does not reach the exit code.

    That is worse than no stage at all, because everything downstream is built
    on trusting the number: a green `verify` would now additionally claim the
    tree is lint-clean when nobody checked. This project has already shipped one
    gate that was never watched failing, which is why `lint` is not allowed to
    be the second — the trap line has to be observed re-raising, not read and
    agreed with.

    The last assertion is the one that proves the trap re-raised rather than
    letting the recipe carry on: the stub echoes its argv, so the ABSENCE of the
    pytest invocation is evidence that `verify` stopped at the failing stage.
    """
    proc = _run(tmp_path, "verify", control_rc=0, lint_rc=1)

    assert proc.returncode != 0
    assert "VERIFY: FAIL (lint)" in proc.stdout
    assert "VERIFY: PASS" not in proc.stdout
    assert "-m pytest" not in proc.stdout, (
        "verify reached the test suite after lint failed, so the lint trap did "
        "not re-raise — the stage can fail without the verdict noticing"
    )


def test_the_documented_stages_are_the_stages_verify_runs() -> None:
    """README's stage table and the real `verify` recipe, bound together.

    Documentation that drifts from the recipe is a quiet lie about what a green
    run proves. This was already true before the table gained a `lint` row:
    `identity` had run first for two phases and the table had never said so, so
    a reader counting stages got the wrong number and no test minded. The next
    stage to land undocumented goes red here instead.
    """
    verify = _recipe(MAKEFILE.read_text(encoding="utf-8"), "verify")

    stages = set(re.findall(r"\$\(MAKE_Q\)\s+([a-z-]+)", verify))
    # `verify-offline` delegates to `verify` through $(MAKE_Q), so drop the
    # self-reference — it is a target, not a stage.
    stages.discard("verify")
    # The live control check is invoked inline as $(CONTROL_CMD) rather than
    # through $(MAKE), and the Makefile says why: it has to tell exit code 3
    # (SKIPPED) apart from a real failure, and a sub-make that exits 3 prints
    # its own "Error 3" first. It is still a stage, and it is still documented.
    if "$(CONTROL_CMD)" in verify:
        stages.add("controls")

    documented = _stage_table(REPO_ROOT / "README.md")

    assert stages == documented, (
        f"README's stage table and `make verify` disagree. "
        f"Runs but undocumented: {sorted(stages - documented)}. "
        f"Documented but never run: {sorted(documented - stages)}."
    )


def test_verify_offline_propagates_the_offline_flag(tmp_path: Path) -> None:
    """`verify-offline` delegates through two levels of recursive make.

    A lost variable here would silently run the LIVE control check in CI while
    reporting the offline verdict.
    """
    proc = _run(tmp_path, "verify-offline", control_rc=3)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "control_check.py --offline" in proc.stdout
    assert "OFFLINE" in proc.stdout
