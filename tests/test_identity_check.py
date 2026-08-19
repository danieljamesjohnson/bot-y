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

import hashlib
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


@needs_repo
def test_the_shipped_config_is_in_scope_because_it_now_carries_a_store_pin() -> None:
    """REQ-14 puts a `store_id` key into `config/products.yaml`.

    That file is tracked and public, and a store number is a geolocator: it
    resolves to one street address. The rule that catches the key lives in
    `_identity_leaks` and is watched going red in `tests/test_fetch.py` — this
    asserts the other half, which is that the guard ever LOOKS at the file.

    Adding `config` to `_SKIP_DIRS` or `.yaml` to `_SKIP_SUFFIXES` would take the
    store pin out of scope without reddening anything, and this is the phase that
    made that regression possible. Scope, not the rule, is what this module is
    for — seven leaks in two days and the rule caught none of them.
    """
    scanned = {str(p.relative_to(REPO_ROOT)) for p in identity_check._tracked_files(REPO_ROOT)}
    assert "config/products.yaml" in scanned, (
        "the identity scan does not cover config/products.yaml, which carries "
        "the per-watch store pin. Check _SKIP_DIRS and _SKIP_SUFFIXES."
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
    # The regex arm is pinned the same way and for the same reason. A literal
    # prefix cannot express "the milestone version does not exist yet", so the
    # archived-phase exemption is a pattern — and a pattern is exactly the shape
    # that widens without looking like it widened. Compare the SOURCE, so
    # loosening one character is a red diff.
    assert tuple(p.pattern for p in identity_check._PROBE_DIR_PATTERNS) == (
        r"\.planning/milestones/v[0-9][^/]*-phases/",
    ), (
        "the archived-phase exemption changed. It is deliberately narrower than "
        "`.planning/milestones/`, which also holds archived ROADMAP, REQUIREMENTS "
        "and AUDIT documents that keep the full pattern check — widen it and "
        "test_an_archived_roadmap_is_not_exempt_from_the_pattern_rules goes red."
    )


# --------------------------------------------------------------------------
# Archiving a phase must not change what its documents ARE
#
# A milestone roll `git mv`s completed phase directories from
# `.planning/phases/` to `.planning/milestones/vX.Y-phases/`. Measured
# 2026-08-19, on a pure rename with no content change: the identity scan went
# from PASS to `FAIL — 6 leak(s)`, every one of them in Phase 5's planning
# documents, and every one of them a probe written to develop and red-watch this
# guard's own store-number rule. Nothing leaked. The move took documents whose
# exemption was keyed to their PATH out from under that path, and their nature
# had not changed at all.
#
# The probe bodies below are COMPOSED FROM PARTS rather than written as
# literals. This file is not a probe file, so a literal probe here would redden
# the very gate these tests exist to keep green — which is the trap
# `tests/test_fetch.py` exists to absorb, and it only has room for one file.
# --------------------------------------------------------------------------

_INVENTED_DIGITS = "7" * 5
_KEYED_PROBE = f"  store_id: {_INVENTED_DIGITS}\n"

_ARCHIVED_PLAN = ".planning/milestones/v0.2-phases/05-a-reading-means-something/05-01-PLAN.md"
_ARCHIVED_ROADMAP = ".planning/milestones/v0.3-ROADMAP.md"


def _scan_one(tmp_path: Path, rel: str, body: str) -> list[str]:
    """Run the real `scan` over a one-file tree rooted at `tmp_path`.

    Not the live repo: these assertions are about the RULE for a path shape, and
    a test that reads `.planning/` off disk cannot run inside the mutation
    sandbox, which does not copy that directory.
    """
    target = tmp_path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return identity_check.scan([target], tmp_path)


def test_an_archived_phase_document_keeps_the_exemption_it_had_before_the_move() -> None:
    """The exemption follows the document, because it was never about the path.

    A planning record quotes the probes of the rule it was written to develop.
    Phase 5 is the phase that WIDENED the store-number rule, so its documents
    necessarily contain the strings that rule matches — under
    `.planning/phases/` and under `.planning/milestones/v0.2-phases/` alike.
    """
    assert identity_check._is_probe_file(_ARCHIVED_PLAN), (
        "an archived phase document is held to the pattern rules, so every probe "
        "it quotes reports as a leak. Archiving is a `git mv`; it changes no byte "
        "of the document and must not change what the guard thinks it is."
    )


def test_an_archived_phase_document_no_longer_reports_its_own_probes(tmp_path: Path) -> None:
    """The failure as it was actually observed, reduced to one file."""
    assert _scan_one(tmp_path, _ARCHIVED_PLAN, _KEYED_PROBE) == []


def test_an_archived_roadmap_is_not_exempt_from_the_pattern_rules(tmp_path: Path) -> None:
    """The exemption is narrow, and this is the half that proves it.

    `.planning/milestones/` holds two different classes. The `vX.Y-phases/`
    subtrees are archived planning records that quote probes. The ROADMAP,
    REQUIREMENTS and MILESTONE-AUDIT documents beside them are ordinary prose
    with no reason to carry a probe — so they keep the full pattern check.

    Exempting the whole of `.planning/milestones/` would fix the reported
    failure and pass every other test in this file. It is one character of
    regex away, and this is the only thing standing in front of it.
    """
    assert not identity_check._is_probe_file(_ARCHIVED_ROADMAP)

    leaks = _scan_one(tmp_path, _ARCHIVED_ROADMAP, _KEYED_PROBE)

    assert leaks, (
        "an archived roadmap is exempt from the pattern rules. The exemption was "
        "widened past the archived PHASE directories it was argued for, and the "
        "documents that gained it were never the ones quoting probes."
    )


def test_a_previously_scrubbed_value_is_still_caught_inside_an_archived_phase_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exemption SWAPS which check runs. It does not stop checking.

    This is the whole reason it is safe to widen, so it is asserted rather than
    argued. Probe-bearing files are held to `_is_known_real` — the exact hash of
    every value this repo has had to scrub — which is a harder bar than the
    pattern rules, not an easier one: the patterns ask "does this look like an
    identity?", this asks "is this a value we already removed once?".

    The deny-list is monkeypatched to the hash of an INVENTED token, because the
    real entries are hashed precisely so that nobody has to handle the values to
    work on this file.
    """
    invented = "not-a-real-value-0000"
    monkeypatch.setattr(
        identity_check,
        "_SCRUBBED_VALUE_HASHES",
        frozenset({hashlib.sha256(invented.encode()).hexdigest()[:16]}),
    )

    leaks = _scan_one(tmp_path, _ARCHIVED_PLAN, f"a document reusing {invented} here\n")

    assert len(leaks) == 1 and "PREVIOUSLY-SCRUBBED VALUE" in leaks[0], leaks


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
