"""What the package declares about itself, checked against what it ships.

WHY THIS FILE EXISTS
--------------------
Measured against setuptools 83.0.0, and this is the whole reason there is a test
here rather than a trust in the build: with ``license-files = ["LICENSE"]``
declared in `pyproject.toml` and **no `LICENSE` on disk**, the build succeeds
without complaint. It still emits ``License-Expression: MIT``. It emits no
``License-File`` at all, and it writes no ``licenses/`` directory into the
dist-info. Nothing warns, nothing exits non-zero. **The build is not the gate.**

And that is not a hypothetical. This repository was public, declared MIT in
`pyproject.toml`, carried a ``## License`` heading in `README.md` saying MIT, and
shipped no licence text whatsoever for three phases. ``git ls-files`` matched
nothing for ``licen*``; the GitHub API reported ``license: None``. A public
project asserting a licence with no licence text arguably grants nobody any
rights, and nothing in this tree noticed, because nothing was looking.

That is WR-04 exactly: a contract asserted at the producing end and quietly
unimplemented at the consuming one. `tests/test_support_matrix.py` is the
precedent — same shape, same remedy — and this file copies its architecture
deliberately: rules as pure functions over text, run first against the shipped
tree and then against a deliberately corrupted copy of it, so that every rule
here has been watched failing rather than only watched passing.

WHY THIS DOES NOT IMPORT tomllib
--------------------------------
`tomllib` is stdlib only from Python 3.11. This package declares
``requires-python = ">=3.10"``, ``[tool.mypy] python_version = "3.10"`` says the
same thing, and CI pins 3.10 precisely because testing the floor is what the
config claims. A gate that cannot run on the floor the package advertises stops
running exactly where it matters most — on the oldest interpreter, which is the
one nobody develops against. So the ``[project]`` table is read by a deliberately
narrow hand parser below. It is the same trade `_matrix` makes against README
markdown one file over: parse the one shape this repository actually writes, and
fail loudly rather than widen quietly.

WHY README IS NOT READ HERE
---------------------------
`README.md` also claims MIT, in prose, under ``## License``. That claim is not
asserted here on purpose. The README is edited by several plans in this phase —
the contributor-docs section, the `make verify` stage table — and a licence rule
bound to prose those plans keep moving would go red for reasons that have nothing
to do with the licence. It would also put a second machine-read binding into a
file that already carries `tests/test_support_matrix.py`'s. The coupling with
legal weight is metadata <-> file, and that is the one asserted.

WHY THE SANDBOX HAS A GIT INDEX
-------------------------------
`_tracked_top_level_dirs` shells out to ``git ls-files``, and `make mutation`
runs this suite inside a plain directory copy where that command used to exit 128
with ``fatal: not a git repository``. Three behaviours were available:

* **Return an empty set.** Rejected outright. ``_unpruned_directories(manifest,
  <nothing>)`` reports nothing, the test passes, and the only gate on this
  project's published file surface reports success in precisely the place it
  could not run. That is the defect this whole file exists to close, reintroduced
  by the file written to close it — and it would be invisible forever.
* **Skip, following `tests/test_identity_check.py` § ``needs_repo``.** Rejected
  here, and the precedent is real so the reason is written down. That skip is
  sound for *those* tests: they are about this repository's own tracked surface,
  which a copy genuinely has nothing to say about. It is not sound for this rule.
  `MANIFEST.in` is in the sandbox, this rule is about `MANIFEST.in`, and skipping
  would stop the published-file-surface gate running in one of the two places
  this suite executes, while ``addopts = "-ra"`` printed a skip line nobody reads
  as a defect.
* **Give the sandbox a git index.** Chosen. `scripts/mutation_check.py`
  ``build_sandbox()`` now runs ``git init`` and ``git add -A`` after the copy
  loop, so ``git ls-files`` answers inside the sandbox with exactly the files
  that were copied and the rule runs there for real.

Because "the sandbox is a repo now" is a claim about today's tooling rather than
a property of this code, the rule **also** fails loudly: `_tracked_top_level_dirs`
raises `NotATrackedTree` in both of git's failure shapes rather than reporting an
absence. If a future change strips the index back out, `make verify` dies with a
message naming the cause instead of going green having checked nothing.

WHAT IS DELIBERATELY *NOT* TESTED IN THIS FILE
----------------------------------------------
That the sandbox really is a git tree, that its index carries no file the real
repo does not track, and that the sandbox suite skips nothing. All three are
verified by running `scripts/mutation_check.py` and by the standalone commands in
this plan's verification — never from inside this suite. A test here that called
``build_sandbox()`` would build a sandbox inside the sandbox, whose suite would
build another one, without bound.

Nothing here touches the network. It reads three files off disk and shells out to
``git ls-files`` once.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
LICENSE_PATH = REPO_ROOT / "LICENSE"
MANIFEST = REPO_ROOT / "MANIFEST.in"

#: The SPDX expression the metadata must declare, and which the shipped file
#: must be. One constant, used from both sides, so the two cannot be made to
#: agree by editing this test twice in opposite directions.
SPDX = "MIT"

#: The exact first line of the canonical SPDX MIT text.
LICENSE_TITLE = "MIT License"

#: A fingerprint of the canonical MIT text, not a diff of it.
#:
#: Three fragments that together identify MIT and that no other common licence
#: contains. A diff would go red because somebody rewrapped a line, which would
#: teach everyone to stop believing this test; a single fragment would survive a
#: file with its warranty disclaimer deleted, which is the mutilation that
#: matters most. Three clauses, each on one line of the shipped file, is the
#: balance: strong enough to catch a licence swap and a gutted file, loose enough
#: not to fire on whitespace.
MIT_CLAUSES = (
    "Permission is hereby granted, free of charge",
    "The above copyright notice and this permission notice shall be included",
    'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND',
)

#: ``Copyright (c) <year> <holder>``, both captured.
#:
#: An MIT text with no copyright line names nobody, so there is no holder to
#: point at and no year to date the grant from. The holder is then checked
#: against ``[project] authors`` so the two statements of who owns this cannot
#: drift apart.
COPYRIGHT_RE = re.compile(r"^Copyright \(c\) (\d{4}(?:-\d{4})?) (.+)$", re.MULTILINE)

#: Not style. Measured: with an SPDX expression in ``[project] license``, a
#: classifier opening with this prefix makes setuptools raise
#: ``InvalidConfigError: License classifiers have been superseded by license
#: expressions (see PEP 639)`` and the build fails outright. This rule is here so
#: the failure is a red test on a developer's machine rather than a red build on
#: a release day.
FORBIDDEN_CLASSIFIER_PREFIX = "License ::"

#: The only tracked top-level directory that is packaged.
#:
#: Every OTHER tracked top-level directory is unpackaged and must carry a
#: ``prune`` line in `MANIFEST.in`. That is what makes adding a directory to this
#: repository force a decision about whether it ships, instead of letting a
#: setuptools default decide silently — measured, that default put every
#: ``tests/test_*.py`` into the sdist and left out the fixtures and the conftest
#: they need, publishing a test suite that cannot run.
PACKAGED_DIRECTORY = "boty"


class NotATrackedTree(RuntimeError):
    """``git ls-files`` could not answer, so the prune rule has no input.

    Raised rather than reported as an absence. An empty answer here would make
    `_unpruned_directories` find nothing to complain about, and the only gate on
    this project's published file surface would report success in exactly the
    place it could not run — the same shape as an MIT declaration with no MIT
    text, reintroduced by the test written to close it.
    """


# --------------------------------------------------------------------------
# Reading the [project] table, narrowly and on purpose
# --------------------------------------------------------------------------


def _strip_comment(line: str) -> str:
    """Drop a trailing ``#`` comment, ignoring ``#`` inside a double-quoted string."""
    in_string = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_string = not in_string
        elif ch == "#" and not in_string:
            return line[:i]
    return line


def _project_table(pyproject_text: str) -> dict[str, str]:
    """The raw right-hand side of every ``key = value`` in the ``[project]`` table.

    Understands exactly the shapes this file writes: single-line scalars, and
    arrays which may span lines. The multi-line case is here consciously rather
    than by default — ``dependencies`` and ``classifiers`` both span lines in
    this repository's `pyproject.toml`, and `_forbidden_classifiers` has to be
    able to read the second one. A value shape beyond these two is a reason to
    widen this deliberately, in a commit that says so, rather than a reason to
    reach for a parser the declared floor Python does not have.

    Values are returned with comments stripped and lines joined by a space.
    """
    table: dict[str, str] = {}
    lines = pyproject_text.splitlines()
    i = 0
    in_project = False
    key_re = re.compile(r"^([A-Za-z0-9_.-]+)\s*=\s*(.*)$")

    while i < len(lines):
        line = lines[i]
        if line.startswith("["):
            in_project = line.strip() == "[project]"
            i += 1
            continue
        if not in_project:
            i += 1
            continue

        stripped = _strip_comment(line).strip()
        match = key_re.match(stripped)
        if match is None:
            i += 1
            continue

        key, raw = match.group(1), match.group(2).strip()
        # An array may open here and close several lines down. Accumulate until
        # the brackets balance, so the value is complete before it is parsed.
        while raw.count("[") > raw.count("]") and i + 1 < len(lines):
            i += 1
            raw = (raw + " " + _strip_comment(lines[i]).strip()).strip()
        table[key] = raw
        i += 1

    return table


def _string(raw: str | None) -> str | None:
    """A double- or single-quoted scalar, unquoted. ``None`` if it is not one."""
    if raw is None:
        return None
    match = re.fullmatch(r'"([^"]*)"|\'([^\']*)\'', raw.strip())
    if match is None:
        return None
    return match.group(1) if match.group(1) is not None else match.group(2)


def _string_list(raw: str | None) -> list[str]:
    """Every double-quoted string inside a bracketed value. ``[]`` if not one."""
    if raw is None or not raw.strip().startswith("["):
        return []
    return re.findall(r'"([^"]*)"', raw)


# --------------------------------------------------------------------------
# The rules, each a pure function so the corruption tests run the same one
# --------------------------------------------------------------------------


def _declared_licence(pyproject_text: str) -> str | None:
    """The declared SPDX expression, or ``None`` if there isn't one.

    The deprecated ``license = { text = "MIT" }`` table form returns ``None``
    deliberately. setuptools has scheduled it for removal on 2027-02-18 and names
    the SPDX-string replacement in the warning it prints, so it is not a
    declaration this gate accepts — treating it as one would let the repository
    drift back into a form that stops building, quietly, with a green suite.
    """
    raw = _project_table(pyproject_text).get("license")
    if raw is None or raw.strip().startswith("{"):
        return None
    return _string(raw)


def _declared_licence_files(pyproject_text: str) -> list[str]:
    """The paths ``[project] license-files`` promises."""
    return _string_list(_project_table(pyproject_text).get("license-files"))


def _missing_licence_files(pyproject_text: str, root: Path) -> list[str]:
    """Declared licence-file paths with no file behind them.

    This is the rule that would have caught the state this repository was found
    in. setuptools does not perform this check — it builds happily and silently
    drops the ``License-File`` metadata field.
    """
    return [p for p in _declared_licence_files(pyproject_text) if not (root / p).is_file()]


def _licence_body_mismatch(spdx: str | None, license_text: str) -> str | None:
    """Why the shipped file is not the licence the metadata names, or ``None``.

    **Two-directional by construction**, in the language of
    `_misdeclared_disagreement` one file over. It goes red when the metadata
    moves away from the file, and when the file moves away from the metadata. A
    one-directional version — "the shipped file must say MIT" — would be
    perfectly satisfied while `pyproject.toml` said Apache-2.0, which is the more
    likely edit of the two and the more consequential one.
    """
    if spdx is None:
        return (
            "pyproject.toml declares no SPDX expression in [project] license, so there is "
            "nothing for the shipped LICENSE to agree with"
        )
    if spdx != SPDX:
        return (
            f"pyproject.toml declares {spdx!r} in [project] license, but the shipped "
            f"LICENSE is the {SPDX} text. The metadata moved and the file did not"
        )

    first_line = license_text.splitlines()[0] if license_text.splitlines() else ""
    if first_line != LICENSE_TITLE:
        return (
            f"LICENSE opens with {first_line!r}, not {LICENSE_TITLE!r}, while the metadata "
            f"declares {spdx!r}. The file moved and the metadata did not"
        )

    absent = [clause for clause in MIT_CLAUSES if clause not in license_text]
    if absent:
        return (
            f"LICENSE is missing {len(absent)} clause(s) of the canonical {SPDX} text "
            f"while the metadata declares {spdx!r}: {absent}. The file moved and the "
            "metadata did not"
        )
    return None


def _copyright(license_text: str) -> tuple[str, str] | None:
    """``(year, holder)`` from the licence's copyright line, or ``None``."""
    match = COPYRIGHT_RE.search(license_text)
    if match is None:
        return None
    return match.group(1), match.group(2).strip()


def _forbidden_classifiers(pyproject_text: str) -> list[str]:
    """Classifiers that cannot coexist with an SPDX licence expression."""
    return [
        c
        for c in _string_list(_project_table(pyproject_text).get("classifiers"))
        if c.startswith(FORBIDDEN_CLASSIFIER_PREFIX)
    ]


def _pruned_directories(manifest_text: str) -> set[str]:
    """Every directory `MANIFEST.in` prunes."""
    return {
        line.strip().split(None, 1)[1].strip()
        for line in manifest_text.splitlines()
        if line.strip().startswith("prune ") and len(line.strip().split(None, 1)) == 2
    }


def _unpruned_directories(manifest_text: str, tracked_dirs: set[str]) -> list[str]:
    """Tracked top-level directories other than the package with no ``prune`` line."""
    pruned = _pruned_directories(manifest_text)
    return sorted(d for d in tracked_dirs if d != PACKAGED_DIRECTORY and d not in pruned)


def _tracked_top_level_dirs(root: Path) -> set[str]:
    """Top-level directories git reports under ``root``.

    Read from git rather than from ``iterdir()`` so this is a rule about what the
    repository ships rather than about what happens to be on this disk — a
    ``.venv``, a ``dist/`` or a stray scratch directory is not a packaging
    decision anybody made. `tests/conftest.py` deliberately does not patch
    ``subprocess``, and says so in its own note, so shelling out here is within
    the network guard's contract.

    It takes ``root`` as a parameter rather than closing over `REPO_ROOT` for one
    reason: that is what makes its behaviour outside a repository testable, and
    its behaviour outside a repository is the load-bearing part.

    Raises `NotATrackedTree` in both of git's failure shapes rather than
    reporting an absence — see that class, and the module docstring.
    """
    proc = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise NotATrackedTree(
            f"git ls-files exited {proc.returncode} in {root}: "
            f"{proc.stderr.strip() or '(no stderr)'}. The sdist prune rule has no input, "
            "and reporting no unpruned directories here would make it pass by not running."
        )
    entries = proc.stdout.split()
    if not entries:
        # git answered, with nothing. Exit code 0 and an empty index look
        # identical to a healthy repository that ships nothing, and only one of
        # those is real. Both failure shapes are caught because an exit-code
        # check alone would let this one through silently.
        raise NotATrackedTree(
            f"git ls-files exited 0 but listed no files in {root}. An empty index is not "
            "an answer about what this project ships, and treating it as one would make "
            "the sdist prune rule pass by not running."
        )
    return {e.split("/", 1)[0] for e in entries if "/" in e}


# --------------------------------------------------------------------------
# The shipped tree
# --------------------------------------------------------------------------


def test_the_repo_ships_the_licence_text_its_metadata_declares() -> None:
    """Prevents the state this file was written in response to: a public repo
    declaring a licence with no licence text anywhere in it."""
    assert LICENSE_PATH.is_file(), (
        f"{LICENSE_PATH.name} does not exist. pyproject.toml declares a licence and "
        "README.md repeats the claim; without the text, neither grants anybody anything."
    )
    assert _declared_licence(PYPROJECT.read_text(encoding="utf-8")) == SPDX


def test_every_declared_licence_file_exists() -> None:
    """Prevents a silent build. setuptools does NOT check this: with a missing
    target it emits License-Expression, drops License-File and says nothing."""
    missing = _missing_licence_files(PYPROJECT.read_text(encoding="utf-8"), REPO_ROOT)

    assert not missing, (
        f"[project] license-files names files that do not exist: {missing}. The build will "
        "not tell you — it succeeds and silently omits the License-File metadata."
    )


def test_the_licence_file_is_the_licence_the_metadata_names() -> None:
    """Prevents the two halves disagreeing in either direction — a metadata edit
    to a different licence, and a shipped file quietly gutted or replaced."""
    text = PYPROJECT.read_text(encoding="utf-8")
    reason = _licence_body_mismatch(_declared_licence(text), LICENSE_PATH.read_text(encoding="utf-8"))

    assert reason is None, reason


def test_the_licence_names_a_copyright_holder_and_a_year() -> None:
    """Prevents a licence that grants rights on behalf of nobody, and prevents
    the holder drifting away from the author the package metadata publishes."""
    found = _copyright(LICENSE_PATH.read_text(encoding="utf-8"))
    assert found is not None, "LICENSE carries no `Copyright (c) <year> <holder>` line"
    year, holder = found

    assert year.isdigit() and len(year) == 4, year
    authors = _string_list(_project_table(PYPROJECT.read_text(encoding="utf-8")).get("authors"))
    assert authors, "[project] authors is unreadable, so the holder has nothing to agree with"
    assert holder == authors[0], (
        f"LICENSE names {holder!r} but [project] authors names {authors[0]!r}. Two statements "
        "of who owns this, free to drift apart."
    )


def test_no_license_classifier_survives_beside_the_expression() -> None:
    """Prevents a red build on a release day. Measured: setuptools raises
    InvalidConfigError, so this is a hard failure and not a style preference."""
    found = _forbidden_classifiers(PYPROJECT.read_text(encoding="utf-8"))

    assert not found, (
        f"classifiers carries {found} alongside an SPDX license expression. setuptools "
        "raises InvalidConfigError for this — the build fails outright, it does not warn."
    )


def test_every_unpackaged_top_level_directory_is_pruned_from_the_sdist() -> None:
    """Prevents a directory added to this repo shipping to PyPI because nobody
    made a decision. Measured: with no manifest the sdist carried every test
    file and none of the fixtures they read."""
    unpruned = _unpruned_directories(
        MANIFEST.read_text(encoding="utf-8"), _tracked_top_level_dirs(REPO_ROOT)
    )

    assert not unpruned, (
        f"these tracked top-level directories have no `prune` line in MANIFEST.in: {unpruned}. "
        "`[tool.setuptools.packages.find]` governs the WHEEL only, so without a line here they "
        "are candidates for the published sdist. Add `prune <dir>` if it should not ship."
    )


# --------------------------------------------------------------------------
# The same rules, watched failing on a deliberately broken copy
# --------------------------------------------------------------------------


def _corrupt_line(text: str, old: str, new: str) -> str:
    """The real file's text with one exact line replaced.

    Asserts the line was found, the way `_corrupt` in `test_support_matrix.py`
    raises when a row is missing: a corruption test that silently corrupts
    nothing asserts that the rule passes on the healthy tree, which is the one
    thing already covered above.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line == old:
            lines[i] = new
            return "\n".join(lines)
    raise AssertionError(f"no line {old!r} to corrupt — the real file moved out from under this test")


def test_a_metadata_licence_swap_is_caught() -> None:
    """The headline case, direction one: the metadata moves, the file does not."""
    text = _corrupt_line(
        PYPROJECT.read_text(encoding="utf-8"), 'license = "MIT"', 'license = "Apache-2.0"'
    )

    reason = _licence_body_mismatch(_declared_licence(text), LICENSE_PATH.read_text(encoding="utf-8"))

    assert reason is not None
    assert "Apache-2.0" in reason and "pyproject.toml" in reason, reason
    assert "The metadata moved and the file did not" in reason, reason


def test_a_gutted_licence_file_is_caught_from_the_other_side() -> None:
    """The headline case, direction two: the file loses its warranty disclaimer
    and the metadata still says MIT. A one-directional rule would pass here."""
    text = _corrupt_line(
        LICENSE_PATH.read_text(encoding="utf-8"),
        'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR',
        "",
    )

    reason = _licence_body_mismatch(SPDX, text)

    assert reason is not None
    assert "LICENSE is missing" in reason, reason
    assert "The file moved and the metadata did not" in reason, reason


def test_a_licence_file_with_another_licences_title_is_caught() -> None:
    """A whole-file swap, which the clause fingerprint alone would also catch —
    but the title line is the cheapest and clearest thing to report."""
    text = _corrupt_line(LICENSE_PATH.read_text(encoding="utf-8"), "MIT License", "Apache License")

    reason = _licence_body_mismatch(SPDX, text)

    assert reason is not None
    assert "Apache License" in reason, reason


def test_the_deprecated_table_form_is_not_a_declaration() -> None:
    """Restoring `license = { text = "MIT" }` must not read as a declaration.
    setuptools removes it on 2027-02-18; accepting it here would let the tree
    drift back to a form that stops building, with a green suite."""
    text = _corrupt_line(
        PYPROJECT.read_text(encoding="utf-8"), 'license = "MIT"', 'license = { text = "MIT" }'
    )

    assert _declared_licence(text) is None
    reason = _licence_body_mismatch(_declared_licence(text), LICENSE_PATH.read_text(encoding="utf-8"))
    assert reason is not None and "no SPDX expression" in reason, reason


def test_a_declared_licence_file_that_does_not_exist_is_reported() -> None:
    """The exact state this repository was in, reconstructed: a declaration
    pointing at a file nobody shipped. The build stays green for this."""
    text = _corrupt_line(
        PYPROJECT.read_text(encoding="utf-8"),
        'license-files = ["LICENSE"]',
        'license-files = ["COPYING"]',
    )

    assert _missing_licence_files(text, REPO_ROOT) == ["COPYING"]


def test_a_license_classifier_is_reported() -> None:
    """The classifier that is a hard build error, caught before the build."""
    text = _corrupt_line(
        PYPROJECT.read_text(encoding="utf-8"),
        '    "Environment :: Console",',
        '    "Environment :: Console",\n    "License :: OSI Approved :: MIT License",',
    )

    assert _forbidden_classifiers(text) == ["License :: OSI Approved :: MIT License"]


def test_a_licence_with_no_copyright_line_reports_nothing_found() -> None:
    """A licence naming no holder dates and attributes the grant to nobody."""
    text = _corrupt_line(
        LICENSE_PATH.read_text(encoding="utf-8"), "Copyright (c) 2026 Dan Johnson", ""
    )

    assert _copyright(text) is None


def test_a_manifest_that_stops_pruning_tests_is_reported() -> None:
    """The regression that matters: `prune tests` is the one line here that
    removes anything today, and losing it republishes the fixtures question."""
    text = _corrupt_line(MANIFEST.read_text(encoding="utf-8"), "prune tests", "")

    assert _unpruned_directories(text, {"boty", "tests", "docs"}) == ["tests"]


def test_an_empty_manifest_is_a_finding_not_a_pass() -> None:
    """A manifest with nothing in it prunes nothing, which is the default this
    file exists to replace — so it must report, not stay quiet."""
    assert _unpruned_directories("", {"tests"}) == ["tests"]


def test_the_package_directory_is_never_reported_as_unpruned() -> None:
    """The one directory that is supposed to ship. Reporting it would make the
    rule unsatisfiable and the fastest green would be deleting the test."""
    assert _unpruned_directories("", {PACKAGED_DIRECTORY}) == []


def test_the_prune_rule_raises_outside_a_repo_rather_than_reporting_nothing(
    tmp_path: Path,
) -> None:
    """git's first failure shape: exit 128, `fatal: not a git repository`.

    Reporting an absence here would make `_unpruned_directories` find nothing to
    complain about and the sdist gate would pass by not running — invisibly, and
    forever, since a passing test says nothing about whether it ran.
    """
    with pytest.raises(NotATrackedTree) as excinfo:
        _tracked_top_level_dirs(tmp_path)

    assert str(tmp_path) in str(excinfo.value), excinfo.value


def test_the_prune_rule_raises_on_an_empty_index_too(tmp_path: Path) -> None:
    """git's second failure shape, and the one an exit-code check misses.

    Inside a repository with nothing staged, ``git ls-files`` exits **0** and
    prints nothing. A rule that only checked the return code would read that as
    "this project ships no directories" and report success.
    """
    subprocess.run(
        ["git", "-c", "init.defaultBranch=main", "init", "-q"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    with pytest.raises(NotATrackedTree) as excinfo:
        _tracked_top_level_dirs(tmp_path)

    assert "listed no files" in str(excinfo.value), excinfo.value


def test_the_prune_rule_answers_for_real_inside_a_git_tree(tmp_path: Path) -> None:
    """The positive control for the two raises above.

    Without this, `NotATrackedTree` could be raised unconditionally and both
    tests above would still pass while the rule never answered anything.
    """
    (tmp_path / "boty").mkdir()
    (tmp_path / "boty" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("", encoding="utf-8")
    (tmp_path / "README.md").write_text("top level files carry no directory\n", encoding="utf-8")
    subprocess.run(
        ["git", "-c", "init.defaultBranch=main", "init", "-q"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)

    assert _tracked_top_level_dirs(tmp_path) == {"boty", "tests"}
    assert _unpruned_directories("", _tracked_top_level_dirs(tmp_path)) == ["tests"]
