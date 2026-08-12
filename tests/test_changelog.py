"""`CHANGELOG.md`, read rather than merely counted.

WHY THIS FILE EXISTS
--------------------
`CHANGELOG.md` shipped with two literal lines of leaked agent tool-call markup
for the whole of Phase 4. Not a hypothetical and not a near miss reconstructed
afterwards: `git show 2ac965f^:CHANGELOG.md` still hands back the bytes, and
`2ac965f` — *fix(04): strip leaked agent tool-call markup from CHANGELOG.md*,
2026-08-06 — is the commit that removed them.

Two publication paths were open the whole time. `MANIFEST.in` deliberately
includes this file in the sdist, and `pyproject.toml`'s `[project.urls]
Changelog` points every installer at it. The markup was on the path to a
stranger's screen; the only reason it did not publish is that the release was
deferred.

It survived a whole phase of gates because nothing read the body.
`scripts/release_check.py` asserts the file *exists*, and `_changelog_version`
reads its first heading and stops. A contents rule cannot live there either, for
a reason that is a measurement rather than a preference: `release_check.py` needs
the network, so it sits outside `make verify` on purpose, and a rule placed there
would never run in `make verify-offline` — which is this phase's gate.

Phase 6's success criterion 4, verbatim, because this file is judged on it:

    `CHANGELOG.md` is gated on its **contents**, not its existence — the
    leaked-markup class cannot ship again

WHY THE SCOPE IS THIS ONE FILE
------------------------------
Two independent arguments, and the second is the stronger one.

*Measured.* A sweep of the tracked tree for the tool-call shapes found 9 matching
lines in 4 files: `.planning/phases/04-open-source-ready/04-REVIEW.md` (3),
`.planning/phases/06-claims-with-gates-under-them/06-CONTEXT.md` (1), that same
phase's `06-PATTERNS.md` (3) and
`.planning/seeds/nothing-reads-the-changelog-body.md` (2). Every one is a
deliberate quotation of the defect, and `06-PATTERNS.md` became three of them in
the act of recording the sweep. `CHANGELOG.md`, `README.md`, `boty/`, `scripts/`,
`tests/`, `docs/` and `.github/` were all clean.

*Structural, and it does not depend on who quoted what.* This module must contain
the shapes it forbids or it cannot forbid them. A rule scoped to the tracked tree
would therefore redden **its own definition**, always, by construction — the
self-invalidating gate `tests/test_contributor_docs.py` names in its own
docstring: *"A gate that invalidates itself to make a point is worse than no
gate."* That is asserted here rather than claimed, by
`test_this_gate_would_redden_its_own_definition_if_it_were_scoped_to_the_tree`.

So widening the scope is a decision with an exemption mechanism attached, not a
default. `scripts/identity_check.py`'s `_PROBE_FILES` / `_PROBE_DIR_PREFIXES` is
the shape such a widening would need, and it is named here so a future widening
starts from the right place instead of discovering the problem by reddening the
suite.

WHY THE RULES ARE FUNCTIONS OVER TEXT
-------------------------------------
`tests/test_contributor_docs.py`'s idiom, for its recorded reason: each rule is a
pure function of the document's text returning a list of problems, so the
corruption tests below run the *same* rule against a deliberately broken copy of
the real file. A gate asserted only against the tree it guards has never been
watched failing, and this project has already shipped one of those.

And the set is two-directional on purpose. `_extraction_mismatch` in
`tests/test_support_matrix.py` records that a one-directional binding *"would be
worthless"*, and the same trap is one step away here: no markup, no placeholders
and a single trailing newline are **all satisfied by an empty file**. So every
prohibition below is paired with a presence rule — a title, an `## [Unreleased]`
heading, at least one released heading, and a body under every released
heading — and those land in the same commit as the prohibitions rather than in a
later one.

WHY SOME TESTS SKIP AND SOME CANNOT
-----------------------------------
`scripts/mutation_check.SANDBOX_CONTENTS` does not list `CHANGELOG.md`, so
`build_sandbox()` never copies it. A test that unconditionally reads the file
raises `FileNotFoundError` at the *baseline*, `run_baseline` turns that into a
`HarnessError`, and `make verify` dies at the mutation stage for a reason with
nothing to do with any mutation.

The sandbox is deliberately **not** widened to buy this gate green there. Three
reasons, all measured:

1. Phase 4's recorded rule for that constant — *"a `SANDBOX_CONTENTS` entry lands
   in the same commit as the file it names, and is proven load-bearing by
   removal"* — could never be met by an entry added so that a `CHANGELOG.md` gate
   could run, because proving it load-bearing needs a mutation targeting
   `CHANGELOG.md` and no such mutation is registered.
2. `scripts/mutation_check.py` is another plan's file in this phase.
3. Phase 5 answered the identical question the same way; the precedent is in the
   tree at `tests/test_config.py`, keyed on `.gitignore`'s absence, itself on
   `tests/test_identity_check.py`'s `needs_repo`.

**A skip is only sound if something still runs.**
`tests/test_packaging_metadata.py` refused this exact trade for `MANIFEST.in` and
named the failure mode in as many words: *"`addopts = "-ra"` printed a skip line
nobody reads as a defect."* So this file is written in two halves. The
shipped-tree half reads `CHANGELOG.md` and carries `needs_changelog`. The
unconditional half exercises every rule against `MINIMAL`, `HISTORICAL_TAIL` and
the empty document, reads no file, and therefore runs wherever this suite runs.
`test_every_rule_is_exercised_where_the_shipped_file_is_absent` pins the pairing
by walking this module's own AST, so a rule added without an unconditional
exercise reddens rather than quietly stops running.

WHAT IS DELIBERATELY NOT CHECKED HERE
-------------------------------------
*Version ordering.* The obvious Keep-a-Changelog rule is "versions descend down
the file". It is **not** written, because it would be wrong the moment plan 06-05
lands: `pyproject.toml` rolls 1.0.0 down to 0.2.0, and the phase's locked
decision is *"Do not treat the roll as a normal version bump; it is the
correction"* — so this changelog will legitimately carry `## [0.2.0]` above
`## [1.0.0]` forever. Do not add the rule.

*Any requirement that `## [Unreleased]` carry entries.* It reads "Nothing yet."
today, and requiring otherwise would redden the shipped tree the fastest way
available: by inventing an entry. `## [Unreleased]` is therefore exempt from
`empty_release_sections`, in the code and not only here.

*The version binding itself.* Whether the top heading agrees with
`pyproject.toml` belongs to `tests/test_packaging_metadata.py` and plan 06-05,
which already owns that file's TOML reader. `tests/test_ci_workflow.py` records
why that matters: *two readers of one `pyproject.toml` drift.* This file gates
the **shape** of every release heading — `## [x.y.z] - YYYY-MM-DD` — which is the
half the version-agreement rule assumes and never checks. The two compose;
neither duplicates the other. Consequence, stated so it is not a surprise: the
`## [0.2.0]` heading 06-05 writes must carry a real ISO date and a non-empty
body, or this gate bites. That is the gate working.

*Style.* No spell-check, no line length, no prose register. The question is
whether what a stranger reads is true and whole, not how it is written.

Nothing here touches the network. It reads one document off disk, and only where
that document exists.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = REPO_ROOT / "CHANGELOG.md"

# --------------------------------------------------------------------------
# The skip, and why it is not a shrug
# --------------------------------------------------------------------------

needs_changelog = pytest.mark.skipif(
    not CHANGELOG.is_file(),
    reason=(
        "no CHANGELOG.md here, so this is the mutation sandbox — which deliberately "
        "does not copy one: `CHANGELOG.md` is absent from "
        "scripts/mutation_check.SANDBOX_CONTENTS, and an unconditional read would "
        "raise a HarnessError at the baseline and kill `make verify` at the mutation "
        "stage for a reason unrelated to any mutation. Widening SANDBOX_CONTENTS was "
        "considered and rejected: Phase 4's rule for that constant requires an entry "
        "to be proven load-bearing by removal, which needs a mutation targeting "
        "CHANGELOG.md, and this plan registers none — and scripts/mutation_check.py "
        "is another plan's file in this phase. So this follows "
        "tests/test_identity_check.py's `needs_repo` and tests/test_config.py's "
        "precedent instead. THE SKIP IS ONLY SOUND BECAUSE THE RULES THEMSELVES ARE "
        "STILL EXERCISED HERE: every rule in this module is run against MINIMAL, "
        "HISTORICAL_TAIL and the empty document by tests carrying no skip marker, and "
        "test_every_rule_is_exercised_where_the_shipped_file_is_absent fails if one "
        "of them ever stops being."
    ),
)


# --------------------------------------------------------------------------
# The incident, recovered rather than retyped
# --------------------------------------------------------------------------

#: The exact two lines `2ac965f` removed from the end of `CHANGELOG.md` — a
#: closing content tag on its own line and a closing invoke tag on its own line,
#: in that order, the file still ending with a single newline.
#:
#: RECOVERED FROM GIT, NOT RETYPED. Generated at execution by substituting the
#: output of `git show 2ac965f^:CHANGELOG.md | tail -2` into this module, so the
#: red-watch below is the incident itself and not an impression of it. Re-verify
#: with:
#:
#:     git show 2ac965f^:CHANGELOG.md | tail -2
#:
#: **Corrected 2026-08-11.** This comment used to claim `git diff --stat 2ac965f --
#: CHANGELOG.md` is empty, and conclude that today's file plus this tail *is*, byte
#: for byte, the document that shipped. That was true when written and is not now:
#: `ac8155b` (06-05, the `1.0.0` → `0.2.0` roll) moved the file, and the diff reads
#: `103 insertions(+), 2 deletions(-)`. The claim was a sentence in a comment with
#: nothing checking it — this phase's own subject, inside this phase's own
#: deliverable, found by Phase 6's verifier.
#:
#: What is still true is the half that matters, and it now has a gate under it:
#: **these bytes are `2ac965f^`'s bytes**, pinned by
#: `test_the_historical_tail_is_the_incidents_own_bytes` below. So the corruption
#: tests append the real tail to the current file — the incident's bytes executed
#: against today's document, rather than a shape resembling them.
HISTORICAL_TAIL = '</content>\n</invoke>\n'

#: The commit that removed it, named beside the bytes so neither travels alone.
FIX_COMMIT = "2ac965f"

def _fix_commit_parent_is_readable() -> bool:
    """True only where git can actually hand back `2ac965f^`'s `CHANGELOG.md`.

    This asks the precondition the test genuinely has, and two cheaper-looking
    questions are both wrong — measured, after each reddened `make verify` in turn:

    * `(REPO_ROOT / ".git").exists()` is wrong because **`build_sandbox()` copies
      `.git`**. The sandbox has one.
    * "is `REPO_ROOT` git's own `--show-toplevel`" is wrong for the same reason:
      inside the sandbox that command exits 0 and answers with the sandbox root, so
      the guard passes and the test runs anyway. What the sandbox's copy lacks is
      the *history* — `git show 2ac965f^:CHANGELOG.md` there exits **128**,
      `fatal: invalid object name '2ac965f^'`.

    So the predicate is not "am I in a repository" but "does this repository hold
    the commit I am about to ask about". Anything weaker skips in the wrong places
    or runs in them.
    """
    import subprocess

    try:
        probe = subprocess.run(
            ["git", "show", f"{FIX_COMMIT}^:CHANGELOG.md"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):  # git absent, or REPO_ROOT unusable as a cwd
        return False
    return probe.returncode == 0


#: The history itself, needed to ask git what `2ac965f^` actually held.
needs_git_history = pytest.mark.skipif(
    not _fix_commit_parent_is_readable(),
    reason=(
        f"git here cannot read {FIX_COMMIT}^:CHANGELOG.md, so this is the mutation "
        "sandbox (whose copied .git carries no history), an unpacked sdist, or a "
        "shallow clone. The rules themselves are still exercised against "
        "HISTORICAL_TAIL by the unconditional tests; what skips is only the "
        "provenance binding."
    ),
)


@needs_git_history
def test_the_historical_tail_is_the_incidents_own_bytes() -> None:
    """`HISTORICAL_TAIL` is what `2ac965f` removed — asked, not asserted.

    The constant's own comment claims it was recovered from git rather than
    retyped, and until 2026-08-11 nothing checked that. A hardcoded literal
    carrying a provenance claim in a comment is a claim asserted at the producing
    end with nothing checking it at the consuming one — which is the defect class
    this whole phase exists to close, sitting inside the module that closes half
    of it. Phase 6's verifier found it.

    It matters beyond tidiness: every corruption test below is only "the incident
    executed" rather than "a shape resembling it" *because* these bytes are the
    incident's. If the constant were edited to something plausible, the gate would
    still pass and the claim in the docstrings would quietly become false.
    """
    import subprocess

    removed = subprocess.run(
        ["git", "show", f"{FIX_COMMIT}^:CHANGELOG.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    kept = subprocess.run(
        ["git", "show", f"{FIX_COMMIT}:CHANGELOG.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert removed.endswith(HISTORICAL_TAIL), (
        f"HISTORICAL_TAIL is not the tail of {FIX_COMMIT}^:CHANGELOG.md. Either the "
        f"constant was edited away from the incident's real bytes, or the commit "
        f"named by FIX_COMMIT is not the one that stripped them. Re-derive with: "
        f"git show {FIX_COMMIT}^:CHANGELOG.md | tail -2"
    )
    assert removed == kept + HISTORICAL_TAIL, (
        f"{FIX_COMMIT} did not remove exactly HISTORICAL_TAIL and nothing else, so "
        f"the constant does not describe that commit's change."
    )
    assert not kept.endswith(HISTORICAL_TAIL), (
        f"{FIX_COMMIT} was supposed to strip the markup; the fixed file still ends "
        f"with it."
    )

# --------------------------------------------------------------------------
# The pins
# --------------------------------------------------------------------------

#: The literal strings a half-written entry leaves behind.
#:
#: WHY THIS IS A PIN AND NOT A RULE, in `UNREAD_POSITIONS`' sense: there is no
#: way to check that an entry was finished, and there is a way to check that the
#: scaffolding somebody typed while not finishing it is gone. Enumerated, so
#: adding one is a decision in a diff.
#:
#: `XXX` IS DELIBERATELY EXCLUDED. This repository redacts with `XX` and `00000`
#: — `scripts/identity_check.py`'s allow-list — so a future entry honestly
#: quoting a redaction would trip a rule about unfinished work. That is the
#: loosening-by-false-positive spiral the markup rule below is also shaped to
#: avoid.
#:
#: Matched case-sensitively and whole-token: a changelog sentence containing the
#: word "todo" in prose is not a placeholder, and a rule that said otherwise
#: would be edited out by the first person it inconvenienced.
PLACEHOLDERS: tuple[str, ...] = ("TODO", "TBD", "FIXME", "x.y.z", "Lorem ipsum")

#: A small, well-formed changelog. THE SUBJECT OF THE UNCONDITIONAL HALF: no file
#: is read to obtain it, so every rule in this module is exercised against it
#: inside the mutation sandbox, where `CHANGELOG.md` does not exist.
#:
#: It carries an inline-code angle-bracket token on purpose. The shipped
#: `CHANGELOG.md` carries exactly one angle-bracket token — a backticked script
#: tag, in a sentence about emptying script bodies in fixtures — so a markup rule
#: written over angle brackets is red on the shipped tree on arrival. Keeping the
#: same shape here means the clean side of the markup rule is asserted in both
#: halves of this file, not only in the half that reads the repository.
#:
#: EVERY BACKTICKED PATH IN HERE MUST BE IN `SANDBOX_CONTENTS`. `pyproject.toml`
#: is; `CHANGELOG.md` is not. Measured, not predicted: an earlier draft of this
#: constant cited the real changelog by name in its preamble, `stale_path_citations`
#: resolved it here and not inside `build_sandbox()`, and
#: `test_every_rule_is_green_on_a_well_formed_changelog` — the test whose whole
#: job is to run where `CHANGELOG.md` does not exist — failed in the one place it
#: was written for. An "unconditional" document that cites an uncopied path is
#: coupled to the sandbox's contents while looking as though it is not.
MINIMAL = """# Changelog

What changed in each release, and what each change was measured against.

Fixture captures in this project are redacted by emptying every `<script>` body,
and that token is here deliberately: it is the one angle-bracket shape the real
changelog carries, so a markup rule written over angle brackets rather than over
the defect would be caught by this document as well as by the shipped one.

## [Unreleased]

Nothing yet.

## [0.1.0] - 2026-01-02

### Added

- A first release, cited against `pyproject.toml` so the borrowed path-citation
  rule has something to resolve here as well as in the repository.
"""

#: The part of `MINIMAL` a corruption removes to leave a released heading with no
#: body under it. Kept as a constant so the corruption is derived rather than a
#: second hand-typed document.
MINIMAL_BODY = """### Added

- A first release, cited against `pyproject.toml` so the borrowed path-citation
  rule has something to resolve here as well as in the repository.
"""

#: A document with a title and a preamble and nothing else. The gutted case: it
#: passes every prohibition in this module and is still not a changelog.
PREAMBLE_ONLY = """# Changelog

What changed in each release, and what each change was measured against.
"""

# --------------------------------------------------------------------------
# The borrowed readers
# --------------------------------------------------------------------------


def _load_contributor_docs() -> Any:
    """Import `tests/test_contributor_docs.py` by path, for its two text rules.

    The `spec_from_file_location` idiom `tests/test_ci_workflow.py` uses to reach
    `tests/test_packaging_metadata.py`, borrowed for the reason that file
    records: two readers drift. `missing_cited_paths` already takes its root
    explicitly and its docstring already anticipates running inside the mutation
    sandbox, so there is nothing here worth writing a second time — and a second
    copy would be a path-citation rule that disagreed with the one guarding the
    contributor documents about what a path is.
    """
    spec = importlib.util.spec_from_file_location(
        "contributor_docs_for_changelog",
        Path(__file__).resolve().parent / "test_contributor_docs.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTRIBUTOR_DOCS: Any = _load_contributor_docs()

# --------------------------------------------------------------------------
# The rules, as pure functions over text
#
# Every rule below is module-level, public, and does not start with `test_`.
# That is not a style choice: `test_every_rule_is_exercised_where_the_shipped_
# file_is_absent` DISCOVERS them from this module's AST rather than from a
# hand-maintained tuple, so a rule cannot be added and left out of the
# unconditional half. Plan 06-03 recorded a rule escaping exactly such a tuple
# silently, and a rule that quietly stops running is this criterion's own defect
# one level up.
# --------------------------------------------------------------------------

#: A line whose entire content is a single tag. THE SHAPE THAT ACTUALLY SHIPPED.
#: Deliberately permissive about the tag name — a namespaced one is the same
#: defect — and deliberately strict about the line: markdown autolinks
#: (`<https://example.com>`) do not match, because a `/` cannot follow the name
#: without an intervening space, and that is checked below rather than assumed.
_WHOLE_LINE_TAG = re.compile(r"\s*</?[A-Za-z][A-Za-z0-9_.:-]*(?:\s[^<>]*)?/?>\s*")

#: The agent namespace prefix. Its presence anywhere is conclusive: no changelog
#: entry has a reason to carry it.
AGENT_NAMESPACE = "antml:"

#: The tool-call block vocabulary, as tag names.
_TOOL_CALL_TAGS = ("function_calls", "invoke", "parameter", "content")

_TOOL_CALL_TAG = re.compile(r"</?(?:" + "|".join(_TOOL_CALL_TAGS) + r")\b[^<>]*>")

#: An inline-code span, stripped before the vocabulary rule runs. Not multiline,
#: for `_SPAN`'s reason one file over.
_INLINE_CODE = re.compile(r"`[^`\n]+`")

#: Any `## [...]` heading line, well formed or not.
_ANY_RELEASE_HEADING = re.compile(r"##\s*\[[^\]]*\].*")

#: The one heading that is allowed to carry no version and no date.
UNRELEASED_HEADING = "## [Unreleased]"

#: A released heading in the only shape this project accepts.
_RELEASED_HEADING = re.compile(r"## \[(?P<version>\d+(?:\.\d+)+)\] - (?P<day>\d{4}-\d{2}-\d{2})")


def _release_headings(text: str) -> list[tuple[int, str]]:
    """Every `## [...]` line except `## [Unreleased]`, with its 1-based line number."""
    return [
        (number, line.rstrip())
        for number, line in enumerate(text.splitlines(), start=1)
        if _ANY_RELEASE_HEADING.fullmatch(line.rstrip())
        and line.rstrip() != UNRELEASED_HEADING
    ]


def leaked_markup(text: str) -> list[str]:
    """Agent tool-call markup, in the three shapes it actually arrives in.

    WHY THREE SHAPES AND NOT ONE REGEX OVER ANGLE BRACKETS. The shipped
    `CHANGELOG.md` already carries an angle-bracket token — a backticked script
    tag, in a sentence about emptying script bodies in fixture captures — and it
    is the only one in the file. A rule written as "any tag-shaped token" is red
    on the shipped tree the moment it lands, and a rule that is red on arrival
    gets loosened by whoever trips over it until it catches nothing. So the rule
    is shaped around the *defect* instead:

    (a) a line whose entire content is a tag — the exact shape that shipped —
        checked against the RAW text, so it is caught inside a fenced code block
        too. A fence is precisely where an agent's output lands, and a prose-only
        rule would wave it through;
    (b) the agent namespace prefix, anywhere in the document;
    (c) the tool-call block vocabulary appearing as a tag, with inline-code spans
        removed first. Fenced blocks are NOT exempt here either.

    It must NOT fire on the shipped file's inline-code script tag. That is the
    point of the green-side test, which is an assertion rather than a formality:
    fix the rule if it ever goes red there, never `CHANGELOG.md` and never the
    assertion.
    """
    findings: list[str] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if _WHOLE_LINE_TAG.fullmatch(raw):
            findings.append(f"line {number}: the whole line is a tag: {raw.strip()!r}")
        if AGENT_NAMESPACE in raw:
            findings.append(
                f"line {number}: the agent tool-call namespace {AGENT_NAMESPACE!r} is in the text"
            )
        for tag in _TOOL_CALL_TAG.findall(_INLINE_CODE.sub("", raw)):
            findings.append(f"line {number}: tool-call markup in the prose: {tag!r}")
    return findings


def malformed_release_headings(text: str) -> list[str]:
    """Every released heading is `## [x.y.z] - YYYY-MM-DD`, with a real date.

    This is the half plan 06-05's `pyproject.toml` <-> `CHANGELOG.md` version
    agreement assumes and never checks: that rule reads the top heading's
    version, and it can only do that if the heading has one in a shape a reader
    can find.

    NO ORDERING IS ASSERTED, deliberately. `pyproject.toml` rolls 1.0.0 down to
    0.2.0 as a correction rather than a bump, so `## [0.2.0]` will sit above
    `## [1.0.0]` in this document permanently and a descending-version rule would
    be wrong the day it landed.
    """
    findings: list[str] = []
    for number, heading in _release_headings(text):
        match = _RELEASED_HEADING.fullmatch(heading)
        if match is None:
            findings.append(
                f"line {number}: {heading!r} is not `## [x.y.z] - YYYY-MM-DD` "
                f"and is not {UNRELEASED_HEADING!r}"
            )
            continue
        try:
            date.fromisoformat(match.group("day"))
        except ValueError:
            findings.append(
                f"line {number}: {heading!r} carries {match.group('day')!r}, "
                "which is not a real calendar date"
            )
    return findings


def unreplaced_placeholders(text: str) -> list[str]:
    """The scaffolding of an entry nobody finished, whole-token and case-sensitive."""
    findings: list[str] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        for placeholder in PLACEHOLDERS:
            if re.search(rf"\b{re.escape(placeholder)}\b", raw):
                findings.append(f"line {number}: unreplaced placeholder {placeholder!r}")
    return findings


def file_shape_problems(text: str) -> list[str]:
    """The document ends with exactly one newline and no run of blank lines.

    NOT A STYLE RULE. The historical defect was *appended at the end of the
    file*, so end-of-file integrity is the defect's own location: two lines of
    markup and a stray blank tail are the same accident caught at different
    stages of tidying it up. It is also half of the two-directional pair — an
    empty document satisfies every prohibition in this module, and this is the
    first rule that notices.
    """
    findings: list[str] = []
    if not text:
        return ["the document is empty"]
    if not text.endswith("\n"):
        findings.append("the document does not end with a newline")
    elif text.endswith("\n\n"):
        findings.append("the document ends with a run of blank lines")
    return findings


def missing_required_headings(text: str) -> list[str]:
    """The presence half: a title, an `## [Unreleased]` heading, and a release.

    WITHOUT THIS RULE, DELETING THE FILE'S CONTENTS SATISFIES EVERY OTHER RULE IN
    THIS MODULE. No markup, no placeholders, no malformed heading and no empty
    release section are all true of an empty document, and of a document gutted
    back to its preamble. A gate a deletion passes is not a gate — the same
    argument `_extraction_mismatch` makes about a one-directional binding, one
    level up and applied to a document instead of a table.
    """
    lines = [line.rstrip() for line in text.splitlines()]
    findings: list[str] = []
    if not any(line.startswith("# ") for line in lines):
        findings.append("no top-level `# ` title")
    if UNRELEASED_HEADING not in lines:
        findings.append(f"no {UNRELEASED_HEADING!r} heading")
    if not _release_headings(text):
        findings.append("no released version heading — this document announces no release")
    return findings


def empty_release_sections(text: str) -> list[str]:
    """Every released heading carries at least one non-blank line under it.

    `## [Unreleased]` IS EXEMPT, and the exemption is the rule's whole subtlety:
    it reads "Nothing yet." today, and a rule requiring it to carry entries would
    redden the shipped tree the fastest way available — by inventing one.
    """
    lines = text.splitlines()
    findings: list[str] = []
    for number, heading in _release_headings(text):
        body = []
        for line in lines[number:]:
            if line.startswith("## "):
                break
            body.append(line)
        if not any(line.strip() for line in body):
            findings.append(f"line {number}: {heading!r} announces a release and says nothing")
    return findings


def stale_path_citations(text: str, root: Path) -> list[str]:
    """Every backticked repo path the changelog cites must exist under `root`.

    Borrowed from `tests/test_contributor_docs.py`, not re-implemented. Measured
    on 2026-08-10: `CHANGELOG.md` cites 17 repo paths and all 17 resolve — the
    same rot class that file closes for the two contributor documents, on the one
    shipped document it does not cover.
    """
    return list(CONTRIBUTOR_DOCS.missing_cited_paths(text, root))


def line_numbered_citations(text: str) -> list[str]:
    """No citation may carry a `:N` or `:N-M` suffix. Borrowed, not re-implemented."""
    return list(CONTRIBUTOR_DOCS.line_numbered_citations(text))


# --------------------------------------------------------------------------
# Reading the shipped file
# --------------------------------------------------------------------------


def _shipped() -> str:
    """`CHANGELOG.md` as it is on disk.

    UNKNOWN IS NEVER A VERDICT: a `CHANGELOG.md` this gate cannot read is not
    reported clean. `needs_changelog` skips only where the file is genuinely
    absent; a file that is present and unreadable raises out of `read_text`, and
    a file that vanished between collection and here raises here.
    """
    if not CHANGELOG.is_file():
        raise AssertionError(
            "CHANGELOG.md is not on disk, but `needs_changelog` let this test run. "
            "That is a contradiction, not a clean changelog."
        )
    return CHANGELOG.read_text(encoding="utf-8")


def _corrupt(text: str, old: str, new: str) -> str:
    """`text` with one thing changed. Fails loudly if `old` is absent.

    `tests/test_contributor_docs.py`'s helper, and the assertion matters more
    than the substitution: a corruption whose edit silently did nothing asserts
    that a rule fires on the document it was derived from, which is the one thing
    it must never claim.
    """
    assert old in text, f"nothing to corrupt: {old!r} is not in the document"
    return text.replace(old, new, 1)


# --------------------------------------------------------------------------
# The green side — every rule against the shipped file
# --------------------------------------------------------------------------


@needs_changelog
def test_the_shipped_changelog_carries_no_leaked_markup() -> None:
    """The green side of the markup rule is an assertion, not a formality.

    `CHANGELOG.md` carries an inline-code script tag — the only angle-bracket
    token in the file — so this test is what proves the rule is shaped around the
    defect rather than around angle brackets. If it ever goes red, fix the rule.
    Never `CHANGELOG.md`, and never this assertion.
    """
    assert not leaked_markup(_shipped())


@needs_changelog
def test_the_shipped_changelog_has_well_formed_release_headings() -> None:
    assert not malformed_release_headings(_shipped())


@needs_changelog
def test_the_shipped_changelog_carries_no_placeholder() -> None:
    assert not unreplaced_placeholders(_shipped())


@needs_changelog
def test_the_shipped_changelog_ends_the_way_a_file_should() -> None:
    assert not file_shape_problems(_shipped())


@needs_changelog
def test_the_shipped_changelog_carries_every_required_heading() -> None:
    assert not missing_required_headings(_shipped())


@needs_changelog
def test_the_shipped_changelog_announces_no_release_it_does_not_describe() -> None:
    assert not empty_release_sections(_shipped())


@needs_changelog
def test_the_shipped_changelog_cites_no_path_that_does_not_exist() -> None:
    """Measured 2026-08-10: 17 repo paths cited, all 17 resolving.

    Recorded so a future reader knows the rule has something to chew on. A
    citation count of zero would make this test pass by describing nothing, which
    is the failure `missing_cited_paths` cannot see and the reason the number is
    written down here rather than inferred.
    """
    text = _shipped()
    cited = [
        token
        for token in CONTRIBUTOR_DOCS._SPAN.findall(CONTRIBUTOR_DOCS._prose(text))
        if CONTRIBUTOR_DOCS._looks_like_a_repo_path(token)
    ]

    assert not stale_path_citations(text, REPO_ROOT)
    assert len(set(cited)) >= 15, (
        f"CHANGELOG.md now cites only {len(set(cited))} repo paths, down from the 17 "
        "measured on 2026-08-10. The rule below is passing because there is nothing "
        "left for it to resolve."
    )


@needs_changelog
def test_the_shipped_changelog_cites_no_line_number() -> None:
    assert not line_numbered_citations(_shipped())


# --------------------------------------------------------------------------
# Block A — watched going red, against copies derived from the shipped file
# --------------------------------------------------------------------------


@needs_changelog
def test_the_markup_that_actually_shipped_is_rejected() -> None:
    """The incident, executed. Not a shape resembling the defect — `2ac965f^`'s bytes.

    Without this test, the whole file is a rule set nobody has watched meet the
    thing it was written for.
    """
    text = _shipped()
    corrupted = text + HISTORICAL_TAIL
    first = len(text.splitlines()) + 1

    findings = leaked_markup(corrupted)

    assert findings, (
        f"the document {FIX_COMMIT} fixed passes the markup rule. The rule does not "
        "catch the class it exists for."
    )
    assert any(f"line {first}:" in finding for finding in findings), findings
    assert any(f"line {first + 1}:" in finding for finding in findings), findings


@needs_changelog
def test_markup_inside_a_fenced_block_is_still_rejected() -> None:
    """A fence is exactly where an agent's output lands.

    A prose-only markup rule — the natural shape, and the one
    `tests/test_contributor_docs.py` uses for path citations — would let a leaked
    block through inside a fence without a word. So shape (a) reads the RAW text,
    and this is the test that would go quiet if anyone changed that.
    """
    corrupted = _corrupt(
        _shipped(),
        "## [Unreleased]",
        "```\n" + HISTORICAL_TAIL + "```\n\n## [Unreleased]",
    )

    findings = leaked_markup(corrupted)

    assert len(findings) >= 2, findings


@needs_changelog
def test_a_release_heading_stripped_of_its_date_is_rejected() -> None:
    corrupted = _corrupt(_shipped(), "## [1.0.0] - 2026-08-05", "## [1.0.0]")

    findings = malformed_release_headings(corrupted)

    assert len(findings) == 1
    assert "'## [1.0.0]'" in findings[0]
    assert not malformed_release_headings(_shipped())


@needs_changelog
def test_a_release_heading_carrying_an_impossible_date_is_rejected() -> None:
    """`\\d{4}-\\d{2}-\\d{2}` is a shape, not a date. `2026-13-45` matches the shape."""
    corrupted = _corrupt(_shipped(), "## [1.0.0] - 2026-08-05", "## [1.0.0] - 2026-13-45")

    findings = malformed_release_headings(corrupted)

    assert len(findings) == 1
    assert "not a real calendar date" in findings[0]


@needs_changelog
def test_a_placeholder_spliced_into_an_entry_is_rejected() -> None:
    # RE-ANCHORED 2026-08-12. This corrupted the literal `Nothing yet.`, which
    # stopped existing when `## [Unreleased]` acquired its first real entries —
    # and `_corrupt` asserts its anchor is present, so the drift went red rather
    # than quietly testing a substitution that did nothing. The new anchor is the
    # file's own subtitle: it is not an entry, so no entry can delete it, and the
    # rule under test scans the whole document rather than any one section.
    corrupted = _corrupt(
        _shipped(),
        "What changed in each release",
        "TODO: write this up before release.",
    )

    findings = unreplaced_placeholders(corrupted)

    assert len(findings) == 1
    assert "'TODO'" in findings[0]


@needs_changelog
def test_a_file_that_stops_ending_in_a_newline_is_rejected() -> None:
    """The defect's own location: the markup arrived by being appended here."""
    assert file_shape_problems(_shipped().rstrip("\n")) == [
        "the document does not end with a newline"
    ]
    assert file_shape_problems(_shipped() + "\n\n") == [
        "the document ends with a run of blank lines"
    ]


@needs_changelog
def test_a_changelog_with_every_release_deleted_is_rejected() -> None:
    """The gutting direction, on the real document rather than a synthetic one.

    EVERY released heading, DERIVED from the file rather than named. This test
    was written when `1.0.0` was the only release and it deleted that one heading
    by its literal text; 06-05 added `## [0.2.0]` above it and the deletion
    stopped producing a document with no release in it, so the rule went quiet
    and the assertion — correctly — failed. The rule was right and the corruption
    had rotted, which is the failure mode `_corrupt`'s own assertion exists to
    make loud. Derived, it cannot rot again at the next release.
    """
    text = _shipped()
    headings = {line for _, line in _release_headings(text)}
    assert headings, "the shipped document announces no release, so there is nothing to gut"
    corrupted = "\n".join(
        "" if line.rstrip() in headings else line for line in text.splitlines()
    )
    assert corrupted != text

    findings = missing_required_headings(corrupted)

    assert findings == ["no released version heading — this document announces no release"]


@needs_changelog
def test_a_released_section_emptied_of_its_body_is_rejected() -> None:
    text = _shipped()
    heading = "## [1.0.0] - 2026-08-05"
    corrupted = text[: text.index(heading)] + heading + "\n"

    findings = empty_release_sections(corrupted)

    assert len(findings) == 1
    assert heading in findings[0]


@needs_changelog
def test_a_citation_repointed_at_a_file_that_does_not_exist_is_rejected() -> None:
    corrupted = _corrupt(_shipped(), "`scripts/identity_check.py`", "`scripts/no_such_check.py`")

    findings = stale_path_citations(corrupted, REPO_ROOT)

    assert findings == ["scripts/no_such_check.py"]


@needs_changelog
def test_a_citation_given_a_line_number_is_rejected() -> None:
    corrupted = _corrupt(_shipped(), "`scripts/identity_check.py`", "`scripts/identity_check.py:42`")

    findings = line_numbered_citations(corrupted)

    assert findings == ["scripts/identity_check.py:42"]


@needs_changelog
def test_the_shipped_file_is_clean_or_the_corruption_tests_prove_nothing() -> None:
    """The guard `tests/test_contributor_docs.py` carries in the same position.

    Every test above derives its corruption from the real document. If the real
    document were already broken, each of them could be passing for a reason that
    has nothing to do with the corruption it applied.
    """
    text = _shipped()

    assert not leaked_markup(text)
    assert not malformed_release_headings(text)
    assert not unreplaced_placeholders(text)
    assert not file_shape_problems(text)
    assert not missing_required_headings(text)
    assert not empty_release_sections(text)
    assert not stale_path_citations(text, REPO_ROOT)
    assert not line_numbered_citations(text)


# --------------------------------------------------------------------------
# Block B — the unconditional half. No file is read, so these run in the sandbox
# --------------------------------------------------------------------------

#: Each rule paired with a corruption of `MINIMAL` it must report. Table-driven so
#: the assertion can name the rule that went quiet rather than the row number.
_CORRUPTIONS: tuple[tuple[str, Callable[[str], list[str]], str], ...] = (
    ("leaked_markup", leaked_markup, MINIMAL + HISTORICAL_TAIL),
    (
        "malformed_release_headings",
        malformed_release_headings,
        MINIMAL.replace("## [0.1.0] - 2026-01-02", "## [0.1.0]"),
    ),
    (
        "unreplaced_placeholders",
        unreplaced_placeholders,
        MINIMAL.replace("Nothing yet.", "TBD"),
    ),
    ("file_shape_problems", file_shape_problems, MINIMAL.rstrip("\n")),
    (
        "missing_required_headings",
        missing_required_headings,
        MINIMAL.replace("## [0.1.0] - 2026-01-02\n", ""),
    ),
    (
        "empty_release_sections",
        empty_release_sections,
        MINIMAL.replace(MINIMAL_BODY, ""),
    ),
    (
        "stale_path_citations",
        lambda text: stale_path_citations(text, REPO_ROOT),
        MINIMAL.replace("`pyproject.toml`", "`boty/no_such_module.py`"),
    ),
    (
        "line_numbered_citations",
        line_numbered_citations,
        MINIMAL.replace("`pyproject.toml`", "`pyproject.toml:42`"),
    ),
)


def test_every_rule_is_green_on_a_well_formed_changelog() -> None:
    """The clean side, proved where `CHANGELOG.md` does not exist.

    Including the markup rule, despite the inline-code angle-bracket token
    `MINIMAL` carries on purpose: a rule written over angle brackets fails here
    as well as on the shipped tree, so the precision proof survives into the
    mutation sandbox.
    """
    assert not leaked_markup(MINIMAL)
    assert not malformed_release_headings(MINIMAL)
    assert not unreplaced_placeholders(MINIMAL)
    assert not file_shape_problems(MINIMAL)
    assert not missing_required_headings(MINIMAL)
    assert not empty_release_sections(MINIMAL)
    assert not stale_path_citations(MINIMAL, REPO_ROOT), (
        "MINIMAL cites a path that does not resolve. If this is red inside "
        "`make mutation` and green in the repository, the citation names something "
        "`SANDBOX_CONTENTS` does not copy — which makes this 'unconditional' test "
        "quietly conditional on the sandbox's contents. Cite a copied path instead; "
        "do not widen SANDBOX_CONTENTS to make this pass."
    )
    assert not line_numbered_citations(MINIMAL)


def test_the_markup_rule_does_not_fire_on_what_a_changelog_legitimately_carries() -> None:
    """The other half of the markup rule: what it must NOT report.

    `tests/test_contributor_docs.py`'s
    `test_the_path_extractor_skips_what_it_cannot_be_sure_about`, one file over
    and for the same reason. A rule that fires on a markdown autolink, on an
    inline-code tag or on a comparison operator gets loosened by the next person
    who trips over it, and a loosened rule catches nothing — which is how the
    defect this file exists for would return through the front door.

    Every shape here either appears in the shipped `CHANGELOG.md` today or is one
    a release note plausibly acquires tomorrow.
    """
    assert not leaked_markup("Fixture captures empty every `<script>` body.\n")
    assert not leaked_markup("See <https://keepachangelog.com/en/1.1.0/>.\n")
    assert not leaked_markup("Supported where `requires-python` is `>=3.10`.\n")
    assert not leaked_markup("A ceiling of `price <= max_price` on the delivered total.\n")
    assert not leaked_markup("- **`Result.degraded` fires on a browser transport.**\n")

    # And the shapes it must always report, on their own lines and in a fence.
    assert leaked_markup("</content>\n")
    assert leaked_markup("```\n</invoke>\n```\n")
    assert leaked_markup(f"prefixed with {AGENT_NAMESPACE} inline\n")


def test_every_rule_bites_on_a_corruption_of_that_document() -> None:
    """Every rule watched going red with no file read.

    The corruptions are derived from `MINIMAL` and `HISTORICAL_TAIL` rather than
    hand-typed a second time, for `_corrupt`'s reason: a corruption that silently
    did nothing asserts that the rule fires on the clean document.
    """
    for name, rule, corrupted in _CORRUPTIONS:
        assert corrupted != MINIMAL, f"{name}: the corruption changed nothing"
        assert rule(corrupted), f"{name} went quiet on a document it must report"


def test_the_markup_that_shipped_is_rejected_without_reading_the_shipped_file() -> None:
    """The sandbox-side twin of the on-tree incident test.

    `CHANGELOG.md` is absent from `SANDBOX_CONTENTS`, so without this the
    leaked-markup class — the one criterion 4 names — would be watched red in
    only one of the two places this suite runs.
    """
    findings = leaked_markup(MINIMAL + HISTORICAL_TAIL)

    first = len(MINIMAL.splitlines()) + 1
    assert any(f"line {first}:" in finding for finding in findings), findings
    assert any(f"line {first + 1}:" in finding for finding in findings), findings
    assert not leaked_markup(MINIMAL)


def test_the_rule_set_is_not_satisfied_by_a_document_with_no_release_in_it() -> None:
    """The two-directional test, and the most important one in this file.

    No markup, no placeholders, no malformed heading, no empty section and a
    single trailing newline are ALL SATISFIED BY DELETING THE CONTENTS. A rule
    set made only of prohibitions is a gate a deletion walks through, and the
    preamble-only document below is the sharper of the two cases: it is clean on
    every prohibition in this module, including the file-shape rule, and it is
    still not a changelog.
    """
    assert file_shape_problems("") == ["the document is empty"]
    assert missing_required_headings("") == [
        "no top-level `# ` title",
        f"no {UNRELEASED_HEADING!r} heading",
        "no released version heading — this document announces no release",
    ]

    assert not leaked_markup(PREAMBLE_ONLY)
    assert not unreplaced_placeholders(PREAMBLE_ONLY)
    assert not malformed_release_headings(PREAMBLE_ONLY)
    assert not empty_release_sections(PREAMBLE_ONLY)
    assert not file_shape_problems(PREAMBLE_ONLY)
    assert missing_required_headings(PREAMBLE_ONLY) == [
        f"no {UNRELEASED_HEADING!r} heading",
        "no released version heading — this document announces no release",
    ]


def test_this_gate_would_redden_its_own_definition_if_it_were_scoped_to_the_tree() -> None:
    """The scope argument, executable.

    This module must contain the shapes it forbids or it could not forbid them —
    the namespace prefix is a constant here and the two closing tags that shipped
    are a constant here. So a tree-wide markup rule reddens the file defining it,
    by construction rather than by accident of who quoted what, and the scope is
    a structural necessity rather than a preference.

    A future widening therefore starts with an exemption mechanism, not with a
    wider glob: `scripts/identity_check.py`'s `_PROBE_FILES` /
    `_PROBE_DIR_PREFIXES` is the shape it would need.
    """
    findings = leaked_markup(Path(__file__).read_text(encoding="utf-8"))

    assert findings, (
        "this module no longer contains the shapes it forbids, which means either the "
        "rule stopped catching them or the constants stopped being the real ones"
    )
    assert any(AGENT_NAMESPACE in finding for finding in findings), findings


def test_every_rule_is_exercised_where_the_shipped_file_is_absent() -> None:
    """The pairing pin: no rule may run only where `CHANGELOG.md` exists.

    `CHANGELOG.md` is not in `SANDBOX_CONTENTS`, so every file-reading test in
    this module skips under `make mutation`. A rule with no unconditional
    exercise is a rule that stops running in one of the two places this suite
    executes, and `tests/test_packaging_metadata.py` already refused that trade
    for `MANIFEST.in`: *"`addopts = "-ra"` printed a skip line nobody reads as a
    defect."*

    The rules are DISCOVERED from this module's AST rather than read from a
    hand-maintained tuple. Plan 06-03 recorded a rule escaping such a tuple in
    silence, and a registry somebody has to remember to update is the same defect
    this criterion is about, one level up.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    module = ast.parse(source)

    rules = [
        node.name
        for node in module.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith(("_", "test_"))
    ]
    unconditional = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("test_")
        and not node.decorator_list
    ]
    exercised = "\n".join(ast.get_source_segment(source, node) or "" for node in unconditional)

    assert rules, "no rule functions discovered — the discovery is wrong, not the module"
    assert len(unconditional) >= 5, (
        f"only {len(unconditional)} tests here carry no skip marker. The unconditional "
        "half is too thin to carry this gate inside the mutation sandbox."
    )

    missing = [rule for rule in rules if rule not in exercised]
    assert not missing, (
        f"these rules are named by no unconditional test: {missing}. They run only "
        "where CHANGELOG.md exists, which is not where `make mutation` runs, so the "
        "criterion would be met there by a skip line."
    )
