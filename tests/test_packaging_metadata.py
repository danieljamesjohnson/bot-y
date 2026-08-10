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

WHY THE README'S *LICENCE* CLAIM IS STILL NOT READ HERE — AND ITS *VERSION*
CLAIM NOW IS
---------------------------------------------------------------------------
This section originally said "WHY README IS NOT READ HERE". It is amended rather
than deleted, because half of it was right and the half that was wrong is worth
seeing corrected — `boty/models.py` and `boty/pacing.py` set the house style for
a reversal: argue it where the old argument lives, name what overruled it, keep
the original.

**The original argument, kept verbatim, and it still stands — for the licence:**

    `README.md` also claims MIT, in prose, under ``## License``. That claim is
    not asserted here on purpose. The README is edited by several plans in this
    phase — the contributor-docs section, the `make verify` stage table — and a
    licence rule bound to prose those plans keep moving would go red for reasons
    that have nothing to do with the licence. It would also put a second
    machine-read binding into a file that already carries
    `tests/test_support_matrix.py`'s. The coupling with legal weight is
    metadata <-> file, and that is the one asserted.

That was, and is, an argument about a **licence** claim bound to **prose that
several plans keep moving**. Nothing below weakens it: the README's ``## License``
heading is still read by nothing here.

**What overruled it for the version claim.** Three measurements, none of which
the licence argument answers:

* The README's version claim is not moving prose. It is **one specific sentence
  naming one specific tag** — ``Publication happens from the `v0.2.0` tag`` —
  and ``grep -n 'v[0-9]\\+\\.[0-9]' README.md`` returns exactly one line. A rule
  can anchor on that sentence and on nothing else.
* That sentence is **false the moment the version rolls**. It has to be edited by
  the plan that rolls it whether or not anything gates it, so gating it costs one
  rule and buys the claim a reader acts on first.
* It is the **only** statement of this project's version that the mutation
  sandbox can see. `CHANGELOG.md` and `.planning/` are both absent from
  ``scripts/mutation_check.SANDBOX_CONTENTS``; `README.md` and `pyproject.toml`
  are both in it. Without this binding, every version rule in this file would
  skip under `make mutation` and the criterion would be met by two skip lines.

**The cost, named rather than glossed:** two test files now read `README.md`.
They cannot collide. `tests/test_support_matrix.py` locates its subject by the
seven-cell header row ``| Retailer | Rung | Extraction | robots.txt | Terms |
Method | Status |`` and asserts that exactly one such row exists; a prose
sentence in the install section cannot hijack a table locator that matches on
seven exact cells. The two rules read disjoint parts of one file, and each says
so.

THE VERSION BINDING: FOUR STATEMENTS, ONE REFERENT
--------------------------------------------------
Phase 6 criterion 5, quoted rather than paraphrased:

    `pyproject.toml` reads `0.2.0`, agrees with the project's milestone version,
    and cannot silently diverge

**"Cannot silently diverge" is the whole requirement.** A one-time edit satisfies
nothing. This project states its own version in four places, and before this file
gained the rules below, **nothing offline read any of them** — grepped: this file
never touched ``[project] version``, `boty/__init__.py` is a zero-byte file with
no ``__version__`` to bind to, and the only cross-check in the tree was
`scripts/release_check.py`'s five-way comparison, which needs the network and
sits outside `make verify` on purpose. They had already diverged: `pyproject.toml`
said ``1.0.0`` while `.planning/STATE.md` said ``milestone: v0.2``, in a
repository whose entire subject is claims with nothing checking them.

**`pyproject.toml` is authoritative, and the direction is written down.** Three
reasons rather than a preference:

1. It is the only one that **becomes the artifact** — the wheel filename, the
   wheel ``METADATA`` and what ``pip install bot-y==0.2.0`` resolves all derive
   from it. The other three are records *about* it.
2. `scripts/release_check.py` **already treats it as the referent**: its
   comparison computes disagreement as everything that differs from ``declared``,
   and ``declared`` is pyproject's. A different referent here would put two
   disagreeing definitions of "the version" into one repository, which is the
   defect this criterion names.
3. It is the only one of the four inside the sdist, inside ``SANDBOX_CONTENTS``,
   and read by the build.

So `README.md`, `CHANGELOG.md` and `.planning/STATE.md` are each checked
*against* pyproject and the finding says which one moved. Never the reverse, and
never a majority vote.

**Normalisation is a rule, not an implicit ``startswith``.** Three shapes:
the README states a git tag (``v`` plus a full triple, ``v`` stripped, all three
components compared); the changelog states a full triple (all three compared);
the milestone states ``v`` plus **two** components, and is compared only on the
components it actually states, because a milestone names a *minor line* and a
patch release inside it must not redden the tree. That leniency is stated out
loud instead of being discovered.

**And the trap that makes it a rule.** ``"0.2.0".startswith("0.2")`` is ``True``
— and so is ``"0.21.0".startswith("0.2")``. A string-prefix comparison silently
accepts a milestone that describes a different minor line entirely, and looks
like it is working while it does it. Components are compared as **lists of
integers-as-strings**, never as string prefixes, and the ``v0.2`` versus
``0.21.0`` case has its own corruption test so the shortcut cannot come back.

**Absence is a finding.** Three of these four rules are trivially satisfied by
*removing* the statement: delete the README sentence, delete the changelog
heading, delete the ``milestone`` key, and a naive comparator finds nothing to
disagree with and reports clean. That is `_extraction_mismatch`'s *"one-directional
would be worthless"*, applied to a version. So every reader returns a value **or
a named absence**, and an absence in a file that is *present* is reported as a
finding naming the file. The only case that is not a finding is the file itself
being absent, which is the sandbox — and that is what the two skips below are
for. The classifier rule is the one deliberate exception, and its reason is in
its own docstring: a removed classifier makes no claim, and 04-02 shipped with
none on purpose.

**Which rules skip, and why that does not hollow the gate out.** `CHANGELOG.md`
and `.planning/` are absent from ``SANDBOX_CONTENTS``, so `build_sandbox()` never
copies them; a test that read either unconditionally would raise at the
*baseline*, ``run_baseline`` would turn that into a ``HarnessError``, and
`make verify` would die at the mutation stage for a reason with nothing to do
with any mutation. Those two rules therefore carry file-presence skips, on
`tests/test_identity_check.py`'s ``needs_repo`` and `tests/test_config.py`'s
precedent. **The sandbox is NOT widened** — Phase 4's rule for that constant is
that an entry lands in the same commit as the file it names and is proven
load-bearing by removal, which neither entry could satisfy, and `.planning/` is
2.9 MB across 101 tracked files copied once per mutation plus a baseline.

This file already refused exactly that trade once, for `MANIFEST.in`, and named
the failure mode in as many words: *"``addopts = "-ra"`` printed a skip line
nobody reads as a defect."* The reason it is acceptable here and was not there is
that **the always-on rule exists**: the ``pyproject.toml`` <-> ``README.md``
binding reads two files that are both in ``SANDBOX_CONTENTS``, so something real
still runs where the other two cannot. That pairing is **pinned rather than
promised** — `test_every_version_rule_is_exercised_where_the_absent_files_are_absent`
walks this module's own AST, discovers every rule named ``_version_*``, and fails
if one of them is named by no undecorated test.

**A correction to this phase's own outline, recorded because it is load-bearing.**
`06-PLAN-OUTLINE.md` § *Finding 7* proposed pairing the STATE rule with a
``pyproject.toml`` <-> ``CHANGELOG.md`` binding, on the grounds that the latter is
*"entirely inside the shipped tree and runs everywhere"*. **Measured false:**
`CHANGELOG.md` is not in ``SANDBOX_CONTENTS``, so that pairing would have had
*both* of its rules skipping under `make mutation` — precisely the defect the
pairing exists to prevent. `README.md` replaced it.

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

Nothing here touches the network. It reads `pyproject.toml`, `LICENSE`,
`MANIFEST.in` and `README.md` off disk unconditionally, `CHANGELOG.md` and
`.planning/STATE.md` only where they exist, and shells out to ``git ls-files``
once.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
LICENSE_PATH = REPO_ROOT / "LICENSE"
MANIFEST = REPO_ROOT / "MANIFEST.in"

#: In `SANDBOX_CONTENTS`, so this one is always there. That is the whole reason
#: the always-on version binding is the one that reads it.
README_PATH = REPO_ROOT / "README.md"

#: NOT in `SANDBOX_CONTENTS`. Read only behind `needs_changelog`.
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"

#: NOT in `SANDBOX_CONTENTS`, and a first in this repository: **nothing under
#: `tests/` or `scripts/` has ever read `.planning/` before this line.** The
#: consequence is deliberate rather than incidental — the `milestone` key in this
#: file's first frontmatter block is now a machine-read fact, so editing it is a
#: gate-visible act and `make verify-offline` will say so. Any plan that moves the
#: milestone must move `pyproject.toml`'s version with it, or the other way round.
STATE_PATH = REPO_ROOT / ".planning" / "STATE.md"

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


# --------------------------------------------------------------------------
# The two skips, and why neither is a shrug
# --------------------------------------------------------------------------

needs_changelog = pytest.mark.skipif(
    not CHANGELOG_PATH.is_file(),
    reason=(
        "no CHANGELOG.md here, so this is the mutation sandbox — which deliberately does "
        "not copy one: `CHANGELOG.md` is absent from "
        "scripts/mutation_check.SANDBOX_CONTENTS, and an unconditional read would raise "
        "at the baseline, become a HarnessError, and kill `make verify` at the mutation "
        "stage for a reason unrelated to any mutation. SANDBOX_CONTENTS is NOT widened to "
        "buy this rule green there: Phase 4's rule for that constant requires an entry to "
        "be proven load-bearing by removal, which needs a mutation targeting CHANGELOG.md, "
        "and none can exist while the file is uncopied. So this follows "
        "tests/test_identity_check.py's `needs_repo` and tests/test_config.py's precedent "
        "instead. THE SKIP IS ONLY SOUND BECAUSE THE ALWAYS-ON RULE EXISTS: "
        "test_the_readme_publication_instruction_names_the_declared_version carries no "
        "skip marker and reads pyproject.toml and README.md, BOTH of which are in "
        "SANDBOX_CONTENTS, so the version binding really does run where this one cannot — "
        "and every _version_ rule is exercised against in-module text besides."
    ),
)

needs_state = pytest.mark.skipif(
    not STATE_PATH.is_file(),
    reason=(
        "no .planning/STATE.md here, so this is the mutation sandbox — which deliberately "
        "does not copy `.planning/`: it is absent from "
        "scripts/mutation_check.SANDBOX_CONTENTS, and an unconditional read would raise at "
        "the baseline, become a HarnessError, and kill `make verify` at the mutation stage "
        "for a reason unrelated to any mutation. SANDBOX_CONTENTS is NOT widened for it, "
        "and this entry has a cost the CHANGELOG.md one does not: `.planning/` is 2.9 MB "
        "across 101 tracked files, and build_sandbox() copies the whole set once per "
        "mutation plus once for the baseline — so widening is not a small price even "
        "before Phase 4's load-bearing-by-removal rule for that constant is considered. "
        "This follows tests/test_identity_check.py's `needs_repo` and tests/test_config.py's "
        "precedent. THE SKIP IS ONLY SOUND BECAUSE THE ALWAYS-ON RULE EXISTS: "
        "test_the_readme_publication_instruction_names_the_declared_version carries no "
        "skip marker and reads two files that ARE in SANDBOX_CONTENTS, so the version "
        "binding still runs here — and every _version_ rule is exercised against in-module "
        "text besides."
    ),
)


# --------------------------------------------------------------------------
# The trove Development Status vocabulary, pinned rather than pattern-matched
# --------------------------------------------------------------------------

#: The `Development Status` values that claim shipped, battle-tested software.
#:
#: WHY THIS IS A PIN AND NOT A RULE, in `UNREAD_POSITIONS`' sense: there is no
#: parseable property of the string `5 - Production/Stable` that says "this is a
#: claim to have shipped". The trove list is a fixed vocabulary maintained by
#: PyPI, so the honest implementation is to enumerate the members with the
#: justification inline, and make widening the set an edit to a red test rather
#: than a default. A rule that inferred the meaning from the leading digit would
#: silently accept a seventh status invented tomorrow.
PRODUCTION_STATUSES = (
    "Development Status :: 5 - Production/Stable",
    "Development Status :: 6 - Mature",
)

#: The values that say, in the vocabulary's own words, that this is not shipped
#: yet. Enumerated for the same reason and with the same consequence.
#:
#: `7 - Inactive` is in neither tuple deliberately: it is a claim about
#: maintenance rather than about maturity, and it can honestly sit beside any
#: version number at all.
PRERELEASE_STATUSES = (
    "Development Status :: 1 - Planning",
    "Development Status :: 2 - Pre-Alpha",
    "Development Status :: 3 - Alpha",
    "Development Status :: 4 - Beta",
)

#: The prefix every trove status shares. Named once so the reader below and the
#: two tuples above cannot drift apart in spelling.
DEVELOPMENT_STATUS_PREFIX = "Development Status :: "


# --------------------------------------------------------------------------
# The changelog heading reader, borrowed rather than written twice
# --------------------------------------------------------------------------


def _load_release_check() -> Any:
    """Import `scripts/release_check.py` by path, for `_changelog_version`.

    The `spec_from_file_location` idiom this repository uses in six other places,
    and borrowed for the reason `tests/test_ci_workflow.py` records about this
    very file: **two readers of one document drift.** `scripts/release_check.py`
    already owns *"the version in the first ``## [x.y.z]`` heading that is not
    Unreleased"*, and `make release-check`'s five-way comparison and this file's
    four-way one must not be able to disagree about what `CHANGELOG.md` says.

    THE MEASURED COST, named rather than discovered later. Importing that module
    executes ``sys.path.insert(0, <scripts dir>)`` at module scope and then
    imports `identity_check`. So `scripts/` is on ``sys.path`` for the rest of the
    pytest session, which nothing else in this suite does today. `scripts` IS in
    ``SANDBOX_CONTENTS``, so the import resolves inside the mutation sandbox too,
    and this suite already loads `control_check.py`, `evidence_check.py` and
    `identity_check.py` by path — the *class* of side effect is established even
    though this particular directory insertion is new. Accepted, and observed
    working inside a real ``build_sandbox()`` before it was trusted.
    """
    spec = importlib.util.spec_from_file_location(
        "release_check_for_packaging_metadata", REPO_ROOT / "scripts" / "release_check.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RELEASE_CHECK: Any = _load_release_check()


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
# The version binding: four readers, one comparator, one classifier rule
#
# EVERY RULE BELOW IS NAMED `_version_*`, AND THAT PREFIX IS THE DISCOVERY
# CONVENTION, not a stylistic choice. `test_every_version_rule_is_exercised_where_
# the_absent_files_are_absent` walks this module's AST, collects the functions
# whose names start with it, and fails if one of them is named by no undecorated
# test. A rule added OUTSIDE the convention escapes that pin in silence — which is
# exactly the trap 06-03 recorded when a rule slipped past a hand-maintained
# tuple, and it is this criterion's own defect one level up. If a version rule
# ever needs a different name, change the pin in the same commit.
# --------------------------------------------------------------------------


class AmbiguousVersionClaim(RuntimeError):
    """`README.md` states its publication tag more than once, so there is no answer.

    Raised rather than reported as a value, in `NotATrackedTree`'s spirit: two
    publication instructions naming two tags is a document with two answers, and
    silently taking the first would let a second instruction rot unnoticed behind
    a green gate. The binding refuses to run instead of running on half the file.
    """


#: The one sentence in `README.md` that states this project's version.
#:
#: ANCHORED ON THE SENTENCE, NOT ON A TAG-SHAPED TOKEN, and the difference
#: matters. A rule that matched any backticked ``v<digits>`` would fire on a
#: changelog link, a git example or a quoted release note the moment one is added,
#: and its finding would then describe a claim nobody made. Measured on the tree
#: this rule was written against: ``grep -n 'v[0-9]\+\.[0-9]' README.md`` returns
#: exactly one line, and it is this sentence.
README_PUBLICATION_RE = re.compile(r"Publication happens from the `([^`]+)` tag")


class _FileAbsent:
    """The statement's FILE is not on disk, so there is nothing to check.

    Distinct from ``None``, which means *the file is here and says nothing* — and
    that is a finding. Conflating the two is how a binding reports agreement it
    never checked, so the two are different objects with different consequences.
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        return "<file absent>"


FILE_ABSENT = _FileAbsent()


def _version_declared(pyproject_text: str) -> str | None:
    """``[project] version``, the referent every other statement is checked against.

    Read through `_project_table` and `_string` above rather than through a second
    parser, for the reason `tests/test_ci_workflow.py` records about this same
    table: two readers of one `pyproject.toml` drift.
    """
    return _string(_project_table(pyproject_text).get("version"))


def _version_in_readme(readme_text: str) -> str | None:
    """The tag `README.md`'s publication instruction names, ``v`` and all.

    The leading ``v`` is deliberately **not** stripped here: the finding has to be
    able to quote what the file actually says, and the file says a git tag. The
    normalisation belongs in `_version_components`, in one place, with its reason.

    Raises `AmbiguousVersionClaim` when more than one publication sentence exists
    — see that class. Returns ``None`` when there is none, which is a finding
    rather than agreement.
    """
    found = README_PUBLICATION_RE.findall(readme_text)
    if len(found) > 1:
        raise AmbiguousVersionClaim(
            f"README.md carries {len(found)} publication instructions naming {found}. "
            "There is no single tag this package would be built as, so this binding "
            "refuses to answer rather than silently taking the first one."
        )
    return found[0] if found else None


def _version_in_changelog(changelog_text: str) -> str | None:
    """The top non-``Unreleased`` release heading, read through `release_check`.

    Borrowed, not re-implemented — see `_load_release_check`.
    """
    version: str | None = RELEASE_CHECK._changelog_version(changelog_text)
    return version


def _version_in_state(state_text: str) -> str | None:
    """``milestone`` from the **first** frontmatter block of `.planning/STATE.md`.

    THE FIRST BLOCK ONLY, and that is load-bearing rather than tidy.
    `.planning/STATE.md` keeps the whole of the previous milestone's state verbatim
    below a horizontal rule — including a ``# Previous milestone — v1.0.0`` heading
    and its own milestone prose. A rule that scanned the entire file would read the
    archive and report that this project's current milestone is the one it finished
    two phases ago, which is a wrong answer delivered confidently.
    """
    lines = state_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            return None
        match = re.match(r"^milestone:\s*(\S+)\s*$", line)
        if match is not None:
            return match.group(1)
    return None


def _version_components(raw: str | None) -> list[int] | None:
    """``"v0.2"`` -> ``[0, 2]``. ``None`` if it is not a dotted numeric version.

    One optional leading ``v`` is stripped, because the README states a git tag and
    a tag is not a version until the ``v`` comes off.

    THE TRAP THIS FUNCTION EXISTS TO CLOSE. ``"0.2.0".startswith("0.2")`` is
    ``True`` — and so is ``"0.21.0".startswith("0.2")``. A string-prefix comparison
    would let a ``v0.2`` milestone agree with a ``0.21.0`` package, silently, while
    looking exactly like a working rule. So versions are compared as **lists of
    components** and never as strings, and `_version_disagreements` compares those
    lists element by element.

    Components come back as ``int`` rather than ``str`` so that a leading zero
    cannot manufacture a disagreement (``0.02`` and ``0.2`` are the same minor
    line) while ``0.2`` and ``0.21`` still are one.
    """
    if raw is None:
        return None
    text = raw.strip()
    if text[:1] == "v":
        text = text[1:]
    parts = text.split(".")
    if not all(part.isdigit() for part in parts):
        return None
    return [int(part) for part in parts]


def _version_disagreements(
    declared: str | None,
    readme: str | _FileAbsent | None = FILE_ABSENT,
    changelog: str | _FileAbsent | None = FILE_ABSENT,
    state: str | _FileAbsent | None = FILE_ABSENT,
) -> list[str]:
    """Every way the three records disagree with `pyproject.toml`, named.

    ``declared`` is the referent — see the module docstring's three reasons. Each
    finding says which file moved, what it says, and what `pyproject.toml` says.
    There is no majority vote and no reverse direction.

    ``FILE_ABSENT`` is the default for the three records rather than ``None``
    because the two mean different things and only one of them is acceptable:
    ``FILE_ABSENT`` says *the file is not on disk* (the mutation sandbox, and the
    only case that is not a finding), while ``None`` says *the file is here and
    states nothing*, which IS a finding. Passing ``FILE_ABSENT`` for a file that
    exists would be buying a green by not looking, so the callers below pass it
    only from behind the matching skip marker.

    THE MILESTONE IS COMPARED LENIENTLY, ON PURPOSE AND OUT LOUD. A milestone
    names a *minor line*, not a release: ``v0.2`` agrees with ``0.2.0`` and with a
    future ``0.2.7``, because a patch release inside a milestone is expected and
    must not redden the tree. It is compared only on the components it actually
    states — which is a prefix comparison over *component lists*, and is precisely
    not `str.startswith`.
    """
    if declared is None:
        return [
            "pyproject.toml states no [project] version, so the three records about it "
            "have nothing to agree with. UNKNOWN is not a verdict here: a version this "
            "gate cannot read is reported as a finding, never as agreement"
        ]
    declared_parts = _version_components(declared)
    if declared_parts is None:
        return [
            f"pyproject.toml declares version {declared!r}, which is not a dotted numeric "
            "version. Nothing can be compared against it, and reporting agreement would be "
            "reporting a check that did not run"
        ]

    findings: list[str] = []
    subjects: tuple[tuple[str, str, str | _FileAbsent | None, bool], ...] = (
        ("README.md", "its publication instruction", readme, True),
        ("CHANGELOG.md", "its top released heading", changelog, True),
        (".planning/STATE.md", "its frontmatter milestone", state, False),
    )

    for source, where, value, exact in subjects:
        if isinstance(value, _FileAbsent):
            continue
        if value is None:
            findings.append(
                f"{source} is present but {where} states no version at all, while "
                f"pyproject.toml declares {declared!r}. A DELETED STATEMENT IS A FINDING, "
                "not agreement — removing the claim is the cheapest way to satisfy a naive "
                "binding, and it leaves a reader with one fewer answer rather than a "
                "consistent one"
            )
            continue
        parts = _version_components(value)
        if parts is None:
            findings.append(
                f"{source} states {value!r} in {where}, which is not a dotted numeric "
                f"version, so it cannot be compared with pyproject.toml's {declared!r}. "
                "Unreadable is not agreement"
            )
            continue
        if exact:
            if parts != declared_parts:
                findings.append(
                    f"{source} states {value!r} in {where} but pyproject.toml declares "
                    f"{declared!r}. pyproject.toml is the referent, so {source} is what "
                    "moved — unless pyproject.toml moved and this record did not, which is "
                    "the same finding read the other way and needs the same fix"
                )
        elif len(parts) > len(declared_parts) or parts != declared_parts[: len(parts)]:
            findings.append(
                f"{source} states {value!r} in {where} but pyproject.toml declares "
                f"{declared!r}. A milestone names a minor line, so it is compared only on "
                f"the {len(parts)} component(s) it states — and those do not match "
                f"{declared_parts[: len(parts)]}. Compared as component lists rather than "
                'as a string prefix, because "0.21.0".startswith("0.2") is True'
            )
    return findings


def _version_status_disagreement(pyproject_text: str) -> str | None:
    """Why the ``Development Status`` classifier contradicts the version, or ``None``.

    A trove classifier is a claim made to everyone who installs this, and
    development status is a claim *about the version number*. So the two can
    disagree, and before this rule existed the disagreement was prose in a comment
    block that nobody would re-read at the next bump — which is the exact failure
    this phase is about, so it is a rule instead.

    TWO DIRECTIONS, because one would be worthless:

    * major component ``0`` refuses `PRODUCTION_STATUSES` — a package nobody has
      published, tagged or installed cannot be Production/Stable;
    * major component ``1`` or above refuses `PRERELEASE_STATUSES` — this is Phase
      4's own recorded reasoning made executable, *"tagging 1.0.0 while classifying
      the package Beta is exactly the asserted-versus-real disagreement this phase
      exists to close"*. Without it, a rule that only stopped Production/Stable at
      0.x would be perfectly satisfied by a 2.0.0 classified Alpha.

    THE DELIBERATE EXCEPTION: no ``Development Status`` classifier at all returns
    ``None``. A removed classifier makes no claim, and 04-02 shipped with none on
    purpose while the version was 0.1.0. This rule polices disagreement, not
    completeness — that is a different rule, and it is not this one's to smuggle in.

    Named `_version_status_disagreement` rather than `_status_version_disagreement`
    (which is what 06-05's plan called it) so the `_version_` discovery convention
    picks it up. A rule outside the convention escapes the pairing pin silently,
    which is the trap the convention exists for.
    """
    statuses = [
        c
        for c in _string_list(_project_table(pyproject_text).get("classifiers"))
        if c.startswith(DEVELOPMENT_STATUS_PREFIX)
    ]
    if not statuses:
        return None
    if len(statuses) > 1:
        return (
            f"pyproject.toml carries {len(statuses)} Development Status classifiers "
            f"({statuses}). Two statuses are two claims about one version, and a reader is "
            "left to decide which to believe"
        )
    status = statuses[0]

    declared = _version_declared(pyproject_text)
    parts = _version_components(declared)
    if parts is None:
        return (
            f"pyproject.toml classifies itself {status!r} while its [project] version reads "
            f"{declared!r}, which this gate cannot parse. A status is a claim about a "
            "version number, and there is no readable number here for it to be about"
        )
    major = parts[0]

    if major == 0 and status in PRODUCTION_STATUSES:
        return (
            f"pyproject.toml classifies itself {status!r} at version {declared!r}. Major "
            "version 0 says the interface is not settled and the package is not shipped; "
            "the classifier tells every installer it is battle-tested. That is the "
            "asserted-versus-real disagreement this milestone exists to close, and it "
            "leaves a reader to decide which of the two to believe"
        )
    if major >= 1 and status in PRERELEASE_STATUSES:
        return (
            f"pyproject.toml classifies itself {status!r} at version {declared!r}. Phase 4 "
            "refused exactly this in writing: tagging 1.0.0 while classifying the package "
            "Beta is the same disagreement pointed the other way"
        )
    return None


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


# --------------------------------------------------------------------------
# The version binding, against the shipped tree
# --------------------------------------------------------------------------


def _real_changelog_heading_line(changelog_text: str) -> str:
    """The exact top released heading line, read from the file rather than typed.

    That heading carries a date, so its text is not a fixed string this module can
    hardcode. `_corrupt_line` asserts the line it is given exists; handing it a
    guess would turn a rotted anchor into a red test with a misleading message,
    and handing it a derived line turns the same rot into `_corrupt_line`'s own
    "the real file moved out from under this test".
    """
    for line in changelog_text.splitlines():
        match = re.match(r"^##\s*\[([^\]]+)\]", line)
        if match and match.group(1).lower() != "unreleased":
            return line
    raise AssertionError("CHANGELOG.md carries no released heading to derive a corruption from")


def _real_state_milestone_line(state_text: str) -> str:
    """The exact ``milestone:`` line of the first frontmatter block, derived not typed.

    Same reason as `_real_changelog_heading_line`, with one extra: this plan is
    about a version that moves, so the literal text of this line is guaranteed to
    change and a hardcoded copy would rot on the very next milestone.
    """
    lines = state_text.splitlines()
    assert lines and lines[0].strip() == "---", ".planning/STATE.md opens with no frontmatter block"
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if re.match(r"^milestone:\s*\S+\s*$", line):
            return line
    raise AssertionError("the first frontmatter block of .planning/STATE.md carries no milestone key")


def test_the_declared_version_is_readable_at_all() -> None:
    """The referent, before anything is compared to it.

    Everything below is a statement about this value, so a `pyproject.toml` whose
    version this file cannot parse would make three rules vacuous at once — the
    quiet way a binding stops binding.
    """
    declared = _version_declared(PYPROJECT.read_text(encoding="utf-8"))

    assert declared is not None, "pyproject.toml states no readable [project] version"
    assert _version_components(declared) is not None, declared


def test_the_readme_publication_instruction_names_the_declared_version() -> None:
    """THE ALWAYS-ON BINDING. No skip marker, and that is the point of it.

    `README.md` and `pyproject.toml` are the only two of this project's four
    version statements that are BOTH in `scripts/mutation_check.SANDBOX_CONTENTS`,
    so this is the one version rule that runs in both of the places this suite
    executes. The other two skip under `make mutation`, and a criterion met by two
    skip lines is met by nothing — this rule is what makes those skips sound, and
    it is observed passing inside a real `build_sandbox()` rather than assumed to.

    What it protects is not academic: this sentence tells a stranger which tag
    produced the thing they just installed. It is false the moment the version
    rolls and nothing else in the tree would notice.
    """
    pyproject_text = PYPROJECT.read_text(encoding="utf-8")
    findings = _version_disagreements(
        _version_declared(pyproject_text),
        readme=_version_in_readme(README_PATH.read_text(encoding="utf-8")),
    )

    assert not findings, findings


@needs_changelog
def test_the_changelog_top_release_heading_names_the_declared_version() -> None:
    """The published record of what changed, bound to the number it changed to.

    Read through `scripts/release_check.py`'s own `_changelog_version`, so the
    network release check's comparison and this offline one cannot disagree about
    what this file's top heading says.
    """
    pyproject_text = PYPROJECT.read_text(encoding="utf-8")
    findings = _version_disagreements(
        _version_declared(pyproject_text),
        changelog=_version_in_changelog(CHANGELOG_PATH.read_text(encoding="utf-8")),
    )

    assert not findings, findings


@needs_state
def test_the_projects_own_milestone_names_the_declared_version() -> None:
    """THE ONE THAT WAS RED ON ARRIVAL, and the reason this gate was written first.

    Measured before anything was rolled: `pyproject.toml` said ``1.0.0`` and
    `.planning/STATE.md` said ``milestone: v0.2``. Both are tracked, both are this
    project's own statement about itself, they had been disagreeing since the
    milestone was scoped, and **nothing in the tree read either one**. That is
    criterion 5's own defect, sitting in a repository whose entire subject is
    claims with nothing checking them.

    This test was committed red on purpose and the roll turned it green. Same
    command on both sides; the only thing that changed between them was the
    version.
    """
    pyproject_text = PYPROJECT.read_text(encoding="utf-8")
    findings = _version_disagreements(
        _version_declared(pyproject_text),
        state=_version_in_state(STATE_PATH.read_text(encoding="utf-8")),
    )

    assert not findings, findings


def test_the_development_status_classifier_does_not_contradict_the_version() -> None:
    """A trove status is a claim about the version, so the two can disagree.

    Unconditional: both halves live in `pyproject.toml`, which is in the sandbox.
    """
    reason = _version_status_disagreement(PYPROJECT.read_text(encoding="utf-8"))

    assert reason is None, reason


@needs_changelog
@needs_state
def test_all_four_statements_of_the_version_agree_right_now() -> None:
    """The shipped-tree guard, in the position this file already uses it.

    Without it, every corruption test below could be passing because the tree was
    already broken — a corrupted copy of an inconsistent file is inconsistent for
    reasons that have nothing to do with the corruption.
    """
    findings = _version_disagreements(
        _version_declared(PYPROJECT.read_text(encoding="utf-8")),
        readme=_version_in_readme(README_PATH.read_text(encoding="utf-8")),
        changelog=_version_in_changelog(CHANGELOG_PATH.read_text(encoding="utf-8")),
        state=_version_in_state(STATE_PATH.read_text(encoding="utf-8")),
    )

    assert not findings, findings


# --------------------------------------------------------------------------
# The same rules, watched going red — in BOTH directions, on copies derived
# from the real files
#
# Three of the four bindings are satisfied by DELETING the statement, so each
# deletion gets its own test. A binding that reports clean when a claim is
# removed is a binding that rewards removing claims.
# --------------------------------------------------------------------------


@needs_changelog
@needs_state
def test_a_pyproject_version_that_moves_away_from_all_three_records_is_caught() -> None:
    """Direction one: `pyproject.toml` moves and the three records do not.

    One corruption, three findings, each asserted individually — a comparator that
    reported only the first would leave two silent disagreements behind a red test
    that looked like it had found everything.
    """
    pyproject_text = PYPROJECT.read_text(encoding="utf-8")
    declared = _version_declared(pyproject_text)
    assert declared is not None
    moved = _corrupt_line(pyproject_text, f'version = "{declared}"', 'version = "9.9.9"')

    findings = _version_disagreements(
        _version_declared(moved),
        readme=_version_in_readme(README_PATH.read_text(encoding="utf-8")),
        changelog=_version_in_changelog(CHANGELOG_PATH.read_text(encoding="utf-8")),
        state=_version_in_state(STATE_PATH.read_text(encoding="utf-8")),
    )

    assert len(findings) == 3, findings
    assert any("README.md" in f for f in findings), findings
    assert any("CHANGELOG.md" in f for f in findings), findings
    assert any(".planning/STATE.md" in f for f in findings), findings
    assert all("9.9.9" in f for f in findings), findings


def test_a_readme_that_moves_away_from_pyproject_is_caught() -> None:
    """Direction two for the always-on binding: the record moves, pyproject does not.

    Unconditional, like the rule it watches — this red-watch runs inside the
    mutation sandbox too, which is where M26 needs it to.
    """
    readme_text = README_PATH.read_text(encoding="utf-8")
    stated = _version_in_readme(readme_text)
    assert stated is not None
    moved = readme_text.replace(f"`{stated}` tag", "`v8.8.8` tag", 1)
    assert moved != readme_text

    findings = _version_disagreements(
        _version_declared(PYPROJECT.read_text(encoding="utf-8")),
        readme=_version_in_readme(moved),
    )

    assert len(findings) == 1, findings
    assert "README.md" in findings[0] and "v8.8.8" in findings[0], findings


@needs_changelog
def test_a_changelog_that_moves_away_from_pyproject_is_caught() -> None:
    """The published record of what changed, naming a version nothing built."""
    changelog_text = CHANGELOG_PATH.read_text(encoding="utf-8")
    heading = _real_changelog_heading_line(changelog_text)
    moved = _corrupt_line(changelog_text, heading, "## [7.7.7] - 2026-01-01")

    findings = _version_disagreements(
        _version_declared(PYPROJECT.read_text(encoding="utf-8")),
        changelog=_version_in_changelog(moved),
    )

    assert len(findings) == 1, findings
    assert "CHANGELOG.md" in findings[0] and "7.7.7" in findings[0], findings


@needs_state
def test_a_milestone_that_moves_away_from_pyproject_is_caught() -> None:
    """The project's own record of what it is, disagreeing with what it declares."""
    state_text = STATE_PATH.read_text(encoding="utf-8")
    milestone_line = _real_state_milestone_line(state_text)
    moved = _corrupt_line(state_text, milestone_line, "milestone: v6.6")

    findings = _version_disagreements(
        _version_declared(PYPROJECT.read_text(encoding="utf-8")),
        state=_version_in_state(moved),
    )

    assert len(findings) == 1, findings
    assert ".planning/STATE.md" in findings[0] and "v6.6" in findings[0], findings


def test_deleting_the_readme_publication_instruction_is_a_finding_not_a_pass() -> None:
    """Deletion case one. The cheapest way to satisfy a naive binding is to remove
    the claim, and a gate that rewards that is worse than no gate."""
    readme_text = README_PATH.read_text(encoding="utf-8")
    stated = _version_in_readme(readme_text)
    assert stated is not None
    deleted = readme_text.replace(f"Publication happens from the `{stated}` tag", "", 1)
    assert _version_in_readme(deleted) is None

    findings = _version_disagreements(
        _version_declared(PYPROJECT.read_text(encoding="utf-8")), readme=None
    )

    assert len(findings) == 1, findings
    assert "README.md" in findings[0] and "DELETED STATEMENT IS A FINDING" in findings[0], findings


@needs_changelog
def test_deleting_every_changelog_release_heading_is_a_finding_not_a_pass() -> None:
    """Deletion case two, and the one a version comparator is most likely to miss:
    a changelog with only an `## [Unreleased]` section states no released version
    at all, and there is then nothing to disagree with."""
    changelog_text = CHANGELOG_PATH.read_text(encoding="utf-8")
    # EVERY released heading, not just the top one: after this milestone's roll
    # there are two, and removing only the first would leave `_version_in_changelog`
    # answering with the one below it — a deletion test that deleted nothing.
    def _is_release_heading(line: str) -> bool:
        match = re.match(r"^##\s*\[([^\]]+)\]", line)
        return match is not None and match.group(1).lower() != "unreleased"

    deleted = "\n".join(
        "## Older releases" if _is_release_heading(line) else line
        for line in changelog_text.splitlines()
    )
    assert deleted != changelog_text
    assert _version_in_changelog(deleted) is None

    findings = _version_disagreements(
        _version_declared(PYPROJECT.read_text(encoding="utf-8")), changelog=None
    )

    assert len(findings) == 1, findings
    assert "CHANGELOG.md" in findings[0] and "DELETED STATEMENT IS A FINDING" in findings[0], findings


@needs_state
def test_deleting_the_milestone_key_is_a_finding_not_a_pass() -> None:
    """Deletion case three, and the easiest of the three to do by accident — the
    `milestone` line sits in a frontmatter block a tool rewrites."""
    state_text = STATE_PATH.read_text(encoding="utf-8")
    milestone_line = _real_state_milestone_line(state_text)
    deleted = _corrupt_line(state_text, milestone_line, "gsd_state_note: none")
    assert _version_in_state(deleted) is None

    findings = _version_disagreements(
        _version_declared(PYPROJECT.read_text(encoding="utf-8")), state=None
    )

    assert len(findings) == 1, findings
    assert ".planning/STATE.md" in findings[0], findings
    assert "DELETED STATEMENT IS A FINDING" in findings[0], findings


def test_a_milestone_that_is_only_a_string_prefix_of_the_version_is_a_disagreement() -> None:
    """THE NORMALISATION TRAP, pinned so the shortcut cannot come back.

    ``"0.21.0".startswith("0.2")`` is ``True``. A milestone of ``v0.2`` beside a
    package version of ``0.21.0`` describes a different minor line entirely, and a
    prefix comparison would accept it while looking exactly like a working rule.
    The leniency this rule DOES grant is asserted alongside it, so the fix for
    this test cannot be to make the milestone comparison exact and redden every
    patch release.
    """
    assert _version_components("v0.2") == [0, 2]
    assert _version_components("0.21.0") == [0, 21, 0]

    caught = _version_disagreements("0.21.0", state="v0.2")
    assert len(caught) == 1, caught
    assert "startswith" in caught[0], caught

    # The other half: the leniency is real, and a patch release inside the
    # milestone must not redden the tree.
    assert _version_disagreements("0.2.0", state="v0.2") == []
    assert _version_disagreements("0.2.7", state="v0.2") == []


def _real_status_classifier_line(pyproject_text: str) -> str:
    """The exact `Development Status` classifier line, derived rather than typed.

    Which status the shipped file carries is exactly what this milestone changes,
    so a hardcoded copy would rot at the roll — and it would rot into a
    `_corrupt_line` failure whose message pointed at the corruption rather than at
    the classifier. Derived, the same rot reads as "the real file moved out from
    under this test", which is true and actionable.
    """
    for line in pyproject_text.splitlines():
        if line.strip().strip(",").strip('"').startswith(DEVELOPMENT_STATUS_PREFIX):
            return line
    raise AssertionError("pyproject.toml carries no Development Status classifier line")


def _restated(pyproject_text: str, version: str, status: str) -> str:
    """The real file with its version line and its status line both replaced.

    Both, together, because the rule is about the RELATIONSHIP between them: a
    corruption that moved only one would pass or fail depending on which side of
    this milestone's roll the tree happens to be on, and a red-watch whose verdict
    depends on the day is not a red-watch.
    """
    declared = _version_declared(pyproject_text)
    assert declared is not None, "pyproject.toml states no readable version to restate"
    status_line = _real_status_classifier_line(pyproject_text)
    text = _corrupt_line(pyproject_text, f'version = "{declared}"', f'version = "{version}"')
    indent = status_line[: len(status_line) - len(status_line.lstrip())]
    return _corrupt_line(text, status_line, f'{indent}"{status}",')


def test_a_production_status_beside_a_major_zero_version_is_caught() -> None:
    """Classifier direction one, derived from the real file rather than a fixture."""
    text = _restated(
        PYPROJECT.read_text(encoding="utf-8"), "0.2.0", "Development Status :: 5 - Production/Stable"
    )

    reason = _version_status_disagreement(text)

    assert reason is not None
    assert "Production/Stable" in reason and "Major version 0" in reason, reason


def test_a_prerelease_status_beside_a_major_one_version_is_caught() -> None:
    """Classifier direction two — Phase 4's own recorded reasoning, executable.

    A rule that only refused Production/Stable below 1.0 would be perfectly
    satisfied by a 2.0.0 classified Alpha, which is the same false claim with the
    sign flipped.
    """
    text = _restated(
        PYPROJECT.read_text(encoding="utf-8"), "1.0.0", "Development Status :: 4 - Beta"
    )

    reason = _version_status_disagreement(text)

    assert reason is not None
    assert "Beta" in reason and "1.0.0" in reason, reason
    assert "Phase 4 refused exactly this in writing" in reason, reason


# --------------------------------------------------------------------------
# The unconditional half: every rule exercised against text this module owns,
# with no file read at all, so the whole set runs where `CHANGELOG.md` and
# `.planning/` do not exist
# --------------------------------------------------------------------------

#: A `[project]` table with one of everything the version rules read. Deliberately
#: NOT a copy of the real file: a fixture that quoted the shipped one would go red
#: every time the shipped one moved, for reasons unrelated to any rule here.
WELL_FORMED_PYPROJECT = """[project]
name = "bot-y"
version = "0.2.0"
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
]
"""

WELL_FORMED_README = (
    "## Install\n\nPublication happens from the `v0.2.0` tag. If that command reports no "
    "matching\ndistribution, the tag has not been pushed yet.\n"
)

WELL_FORMED_CHANGELOG = (
    "# Changelog\n\n## [Unreleased]\n\nNothing yet.\n\n## [0.2.0] - 2026-08-10\n\nA body.\n"
)

#: Two frontmatter-shaped blocks, because the archive below the rule is the whole
#: reason `_version_in_state` reads the first block only.
WELL_FORMED_STATE = (
    "---\ngsd_state_version: 1.0\nmilestone: v0.2\nstatus: Executing\n---\n\n"
    "# State\n\n---\n\n# Previous milestone — v1.0.0\n\nmilestone: v1.0\n"
)


def test_every_version_rule_is_green_on_documents_this_module_owns() -> None:
    """The unconditional green side: all four readers and both comparators, on
    text held in this file, so they run inside the mutation sandbox."""
    declared = _version_declared(WELL_FORMED_PYPROJECT)
    readme = _version_in_readme(WELL_FORMED_README)
    changelog = _version_in_changelog(WELL_FORMED_CHANGELOG)
    state = _version_in_state(WELL_FORMED_STATE)

    assert (declared, readme, changelog, state) == ("0.2.0", "v0.2.0", "0.2.0", "v0.2")
    assert _version_components(readme) == [0, 2, 0]
    assert _version_disagreements(declared, readme=readme, changelog=changelog, state=state) == []
    assert _version_status_disagreement(WELL_FORMED_PYPROJECT) is None


def test_every_version_rule_bites_on_a_corruption_of_those_documents() -> None:
    """The unconditional red side. Without it the sandbox would run six rules that
    have only ever been watched passing, which is the artefact this phase refuses."""
    assert _version_declared('[project]\nname = "bot-y"\n') is None
    assert _version_in_readme("no publication instruction here\n") is None
    assert _version_in_changelog("# Changelog\n\n## [Unreleased]\n\nNothing yet.\n") is None
    assert _version_in_state("no frontmatter at all\n") is None
    assert _version_in_state("---\nstatus: Executing\n---\nmilestone: v0.2\n") is None
    assert _version_components("not.a.version") is None
    assert _version_components("") is None

    assert _version_disagreements("0.2.0", readme="v0.3.0")
    assert _version_disagreements("0.2.0", changelog="0.3.0")
    assert _version_disagreements("0.2.0", state="v0.3")
    assert _version_disagreements(None)
    assert _version_disagreements("not-a-version", readme="v0.2.0")
    assert _version_disagreements("0.2.0", readme="the tag")
    assert _version_status_disagreement(
        WELL_FORMED_PYPROJECT.replace("4 - Beta", "5 - Production/Stable")
    )
    assert _version_status_disagreement(
        WELL_FORMED_PYPROJECT.replace('version = "0.2.0"', 'version = "1.0.0"')
    )


def test_a_missing_development_status_classifier_is_not_a_disagreement() -> None:
    """The deliberate exception, exercised so it cannot be quietly tightened.

    A removed classifier makes no claim, and 04-02 shipped with none on purpose.
    This rule polices disagreement, not completeness.
    """
    no_status = WELL_FORMED_PYPROJECT.replace('    "Development Status :: 4 - Beta",\n', "")

    assert "Development Status" not in no_status
    assert _version_status_disagreement(no_status) is None


def test_two_publication_instructions_refuse_to_answer_rather_than_guessing() -> None:
    """`README.md` with two publication sentences has two answers, so the reader
    raises instead of silently taking the first — the shape `NotATrackedTree`
    already uses in this file for an input that cannot be answered."""
    doubled = WELL_FORMED_README + "\nPublication happens from the `v9.9.9` tag.\n"

    with pytest.raises(AmbiguousVersionClaim) as excinfo:
        _version_in_readme(doubled)

    assert "v9.9.9" in str(excinfo.value), excinfo.value


def test_the_state_reader_reads_the_current_milestone_and_not_the_archive() -> None:
    """`.planning/STATE.md` keeps the previous milestone's state verbatim below a
    horizontal rule. A reader that scanned the whole file would report the
    milestone this project finished two phases ago, confidently."""
    assert _version_in_state(WELL_FORMED_STATE) == "v0.2"
    assert "v1.0" in WELL_FORMED_STATE.split("---", 3)[-1]


def test_every_version_rule_is_exercised_where_the_absent_files_are_absent() -> None:
    """THE PAIRING PIN. No version rule may run only where a skipped file exists.

    Two of the four bindings read files that `scripts/mutation_check.SANDBOX_CONTENTS`
    does not copy, so they skip under `make mutation`. A rule whose only exercise
    carries a skip marker therefore stops running in one of the two places this
    suite executes, while ``addopts = "-ra"`` prints a skip line nobody reads as a
    defect — this file's own words, about this file's own earlier refusal of the
    same trade for `MANIFEST.in`.

    The rules are DISCOVERED from this module's AST by the `_version_` prefix
    rather than listed in a tuple. 06-03 recorded a rule escaping a hand-maintained
    tuple in silence, and a registry somebody has to remember to update is this
    criterion's defect one level up.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    module = ast.parse(source)

    rules = [
        node.name
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_version_")
    ]
    unconditional = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("test_")
        and not node.decorator_list
    ]
    exercised = "\n".join(ast.get_source_segment(source, node) or "" for node in unconditional)

    assert len(rules) >= 5, (
        f"only {rules} discovered — the version rule set is too thin, or a rule was named "
        "outside the `_version_` convention and this pin cannot see it"
    )
    missing = [rule for rule in rules if rule not in exercised]
    assert not missing, (
        f"these version rules are named by no unconditional test: {missing}. They run only "
        "where CHANGELOG.md or .planning/ exists, which is not where `make mutation` runs, "
        "so criterion 5 would be met there by a skip line."
    )
