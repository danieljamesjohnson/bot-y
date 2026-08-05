"""`scripts/identity_check.py` — the guard's SCOPE, pinned.

The rule itself is watched failing in `test_fetch.py`, class by class and
carrier by carrier. What is pinned here is the thing that actually failed:
**where it looks and when it runs.**

Seven leaks in two days, and the rule caught none of them, because it only ever
read `tests/fixtures/**` from inside the test suite. The public IP was in
`.planning/`. The ZIP was in `docs/`. The worst one was in the guard's own test
file, put there by the commit that added the coverage grid.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = REPO_ROOT / "scripts" / "identity_check.py"


def _load():
    spec = importlib.util.spec_from_file_location("identity_check_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


identity_check = _load()


def _in_git_repo() -> bool:
    """`make mutation` runs the suite in a plain directory copy, not a repo.

    These tests are about the repo's own tracked surface, so they have nothing
    to say there — and a hard failure would turn a mutation run into a HARNESS
    ERROR, which proves nothing about the suite either way.
    """
    return subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--git-dir"],
                          capture_output=True).returncode == 0


needs_repo = pytest.mark.skipif(not _in_git_repo(),
                                reason="not a git checkout (mutation sandbox)")


@needs_repo
def test_the_scan_covers_every_tracked_file_not_just_the_fixtures() -> None:
    """The scope defect, pinned. This is the whole reason the script exists."""
    scanned = {str(p.relative_to(REPO_ROOT)) for p in identity_check._tracked_files(REPO_ROOT)}
    tracked = set(subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"],
        capture_output=True, text=True, check=True).stdout.split())

    # Directories that actually held leaks, each of which the old fixture-only
    # scan was blind to.
    for prefix in (".planning/", "docs/", "tests/", "boty/", "scripts/"):
        expected = {f for f in tracked if f.startswith(prefix)
                    and Path(f).suffix.lower() not in identity_check._SKIP_SUFFIXES}
        missing = expected - scanned
        assert not missing, (
            f"the identity scan does not cover {prefix} — missing {sorted(missing)[:5]}. "
            f"Every one of these directories has held a leak."
        )


def test_the_probe_file_exemption_cannot_quietly_grow() -> None:
    """Files exempt from the pattern rules are held to the deny-list instead.

    That is a stricter bar, not a weaker one — but only while the set stays
    small and deliberate. Skipping by path is what let the `.json` provenance
    notes leak in the first place.
    """
    assert frozenset({"tests/test_fetch.py"}) == identity_check._PROBE_FILES, (
        "the probe-file exemption changed. Each entry skips the pattern rules, "
        "so adding one is a real decision — make it in a diff with a reason, "
        "and confirm the file is still covered by the deny-list check."
    )
    assert identity_check._PROBE_DIR_PREFIXES == (".planning/phases/",)


@needs_repo
def test_the_repo_is_clean_right_now() -> None:
    """The end-to-end assertion: run the real scan over the real tree."""
    paths = identity_check._tracked_files(REPO_ROOT)
    leaks = identity_check.scan(paths, REPO_ROOT)
    assert not leaks, "tracked files carry host identity:\n  " + "\n  ".join(sorted(set(leaks)))


@needs_repo
def test_the_tracked_hook_exists_and_runs_the_staged_scan() -> None:
    """A hook nobody can install is a hook nobody has.

    `.git/hooks` is not cloned, so the guard has to be a tracked file plus a
    `make hooks` target — otherwise it protects exactly one machine, which is
    the machine that already leaked.
    """
    hook = REPO_ROOT / "hooks" / "pre-commit"
    assert hook.exists(), "hooks/pre-commit is not tracked — contributors get no guard"
    body = hook.read_text(encoding="utf-8")
    assert "identity_check.py --staged" in body, "the hook does not run the staged scan"
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "hooks:" in makefile and "hooks/pre-commit" in makefile, (
        "no `make hooks` target — the hook cannot be installed by a contributor"
    )
    verify_recipe = makefile.split("\nverify:", 1)[1].split("\n\n", 1)[0]
    assert "identity" in verify_recipe, (
        "`make verify` does not run the identity scan — a leak would only be "
        "found by reading, which is how the last seven were found"
    )
