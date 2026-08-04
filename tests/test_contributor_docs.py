"""The contributor documentation, checked mechanically rather than by eye.

WHY THIS FILE EXISTS
--------------------
REQ-09 asks for a contributor guide that walks a real adapter end to end. The
failure mode of every such guide is not bad prose — it is a citation that used
to be true. A doc that sends a contributor to a file that moved, a function that
was renamed or a line that shifted is *worse* than no doc at all: it costs them
the time to discover it is wrong, and it looks authoritative the whole way.

`README.md`'s support matrix was prose that nothing checked until 03-03 checked
it, and the same asymmetry applies one directory over. So the two contributor
documents are read the way `tests/test_support_matrix.py` reads the README:
every path they cite must exist, every symbol they pin must still be in the file
they pin it to, and the headings a contributor navigates by must be there.

WHY THERE ARE NO LINE NUMBERS
-----------------------------
`.planning/phases/04-open-source-ready/04-PATTERNS.md` cites this repository
forty-odd times by `file:line`, and every one of those citations is already
expiring: 04-03 lands a linter in this same phase and resolves 43 findings
across `boty/`, `scripts/` and `tests/`. A line number written today is a
citation with a known expiry date, so the contributor docs cite a Python file by
naming a symbol in it and the evidence log by naming its `## ` heading. Rule 2
is what keeps that true after the first person who finds a line number
convenient.

That rule reads the file, not the intent, which is why the docs must not carry a
line-numbered citation even as an illustration of what not to do. A gate that
invalidates itself to make a point is worse than no gate.

WHY THE CHECKS ARE FUNCTIONS OVER TEXT
--------------------------------------
Each rule is a pure function of the document's text, returning a list of
problems rather than asserting anything, so the corruption tests at the bottom
run the *same* rule against a deliberately broken copy of the real file. From
`tests/test_support_matrix.py`: a gate asserted only against the tree it is
meant to guard has never been watched failing, and this project has already
shipped one of those.

Nothing here touches the network. It reads three documents off disk, plus
whichever source files `REQUIRED_SYMBOLS` names.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RETAILER_DOC = REPO_ROOT / "docs" / "adding-a-retailer.md"
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"
README = REPO_ROOT / "README.md"

# --------------------------------------------------------------------------
# The pins
# --------------------------------------------------------------------------

#: The (file, symbol) pairs `docs/adding-a-retailer.md` must name, and which
#: must still exist in the file named.
#:
#: WHY THIS IS A PIN AND NOT A RULE. A rule that said "every backticked
#: identifier in the doc must exist somewhere in the tree" would be satisfied by
#: a doc that names nothing at all, which is exactly the doc REQ-09 is trying to
#: prevent — a contributor guide can be fluent, accurate and completely useless
#: by never pointing at anything. The enumeration is the obligation: these seven
#: are the load-bearing parts of "adding a retailer" in this codebase, so a doc
#: that does not mention `MARKETPLACES` has not explained why Nintendo is absent
#: from it, and a doc that does not mention `_make_checker` has not said where
#: the one dispatch `if` lives.
#:
#: It runs in BOTH directions, the same way `_extraction_mismatch` ties Rung to
#: Extraction in `tests/test_support_matrix.py`: a doc naming a symbol the tree
#: has dropped is as wrong as a doc that never mentions it, and only the second
#: direction catches a rename.
#:
#: All seven verified present in the tree on 2026-08-04, pair by pair.
#: Widening or narrowing it means editing a red test in the same commit as the
#: doc change that justifies it.
REQUIRED_SYMBOLS: tuple[tuple[str, str], ...] = (
    ("boty/retailers.py", "FIRST_PARTY"),
    ("boty/retailers.py", "MARKETPLACES"),
    ("boty/retailers.py", "check_html"),
    ("boty/retailers.py", "check_amazon"),
    ("boty/cli.py", "_make_checker"),
    ("boty/parse.py", "add_to_cart_offers"),
    ("scripts/evidence_check.py", "ROADMAP_RETAILERS"),
)

#: The `## ` headings `docs/adding-a-retailer.md` must carry, verbatim.
#:
#: WHY THIS IS A PIN AND NOT A RULE. There is no way to check that a document
#: answers a question; there is a way to check that it still has the section
#: that answered it. REQ-09 names two of these outright — the control-product
#: requirement and the UNKNOWN contract — so those two headings are the
#: requirement made checkable. The other four are the argument they sit in:
#: without "the default answer is no adapter" first, the control section reads
#: as paperwork attached to code the contributor should not be writing.
#:
#: A heading rename is a deliberate edit to a red test, not a tidy-up.
RETAILER_DOC_HEADINGS: tuple[str, ...] = (
    '## The default answer is "no adapter"',
    "## Why a control product is mandatory",
    "## The UNKNOWN contract",
    "## When a new adapter is genuinely needed",
    "## What the gates already require of you",
    "## Before you open a pull request",
)

#: The `## ` headings `CONTRIBUTING.md` must carry, verbatim.
#:
#: WHY THIS IS A PIN AND NOT A RULE. Same reason one file over, with one
#: addition: the hook section's heading is itself the instruction. "Install the
#: commit hook before your first commit" says the thing even to a contributor
#: who reads nothing but the table of contents, and a rename to something
#: shorter would take the timing — which is the entire point — out of the only
#: line most people read.
CONTRIBUTING_HEADINGS: tuple[str, ...] = (
    "## Set up",
    "## Install the commit hook before your first commit",
    "## Run the checks",
    "## Adding a retailer",
    "## What a pull request has to carry",
)

#: The operational strings a contributor must be told, checked literally.
#:
#: `make hooks` is the security-critical one and it is why this constant exists
#: at all: the identity guard is tracked but installation is opt-in, so a
#: contributor who is never told to run it has no protection at any point before
#: their first push.
CONTRIBUTING_MENTIONS: tuple[str, ...] = (
    "make hooks",
    "scripts/identity_check.py",
    "make verify-offline",
)

#: The link targets `README.md` must carry, in `](target)` form.
#:
#: `LICENSE` is here as a LINK-TEXT obligation only — see
#: `test_the_readme_links_the_licence_file_without_this_test_stating_it_exists`.
README_LINKS: tuple[str, ...] = (
    "docs/adding-a-retailer.md",
    "CONTRIBUTING.md",
    "LICENSE",
)

# --------------------------------------------------------------------------
# The six rules, as pure functions over text
# --------------------------------------------------------------------------

#: A single-backtick span. Deliberately not multiline: a citation that wraps a
#: line is not a citation anybody can follow.
_SPAN = re.compile(r"`([^`\n]+)`")

#: A fenced code block, stripped before path extraction. A shell command in a
#: fence is an instruction, not a citation — `python3 -m venv .venv` names a
#: directory that does not exist until a contributor runs the line it appears
#: in, and failing on it would teach the doc to stop showing commands.
_FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)

#: The extensions that make a token a path even with no `/` in it.
_KNOWN_EXTENSIONS = (".py", ".md", ".yaml", ".yml", ".toml", ".cfg")

#: Files this repo cites by bare name.
_BARE_FILENAMES = ("Makefile",)

#: A hostname, used to reject a URL that lost its scheme. `nintendo.com/us/store`
#: contains a `/` and is not a path in this tree.
_HOSTNAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")

#: Characters that mean a backticked token is code, a shell fragment or markup
#: rather than a path. Conservative on purpose: skipping an ambiguous token
#: costs coverage, failing on one costs the rule its credibility, and the
#: corruption test for rule 1 is what proves it still bites.
_NOT_IN_A_PATH = set("*?\"'<>=(),;{}[]|$&:!@#%^")

#: A path citation carrying a line number, in either `:N` or `:N-M` form.
_LINE_NUMBERED = re.compile(
    r"(?:[A-Za-z0-9_./-]*\.[A-Za-z0-9]{1,5}|Makefile):\d+(?:-\d+)?"
)


def _prose(text: str) -> str:
    """The document with its fenced code blocks removed."""
    return _FENCE.sub("", text)


def _looks_like_a_repo_path(token: str) -> bool:
    """Whether a backticked token is claiming to be a path in this tree."""
    if not token or any(ch.isspace() for ch in token):
        return False
    if "://" in token or token.startswith("-"):
        return False
    if any(ch in _NOT_IN_A_PATH for ch in token):
        return False
    if "/" in token:
        first = token.split("/", 1)[0]
        return not _HOSTNAME.fullmatch(first)
    return token.endswith(_KNOWN_EXTENSIONS) or token in _BARE_FILENAMES


def missing_cited_paths(text: str, root: Path) -> list[str]:
    """Rule 1 — every backticked path the document cites must exist under `root`.

    `root` rather than `REPO_ROOT` because this rule runs in two places. Inside
    `scripts/mutation_check.py`'s sandbox the tree root is a temp directory
    holding only `SANDBOX_CONTENTS`, so a citation of something the sandbox does
    not copy fails there and passes here — which is why `CONTRIBUTING.md` and
    `hooks` are entries in that tuple.
    """
    problems = []
    for token in _SPAN.findall(_prose(text)):
        if not _looks_like_a_repo_path(token):
            continue
        if not (root / token.rstrip("/")).exists():
            problems.append(token)
    return sorted(set(problems))


def line_numbered_citations(text: str) -> list[str]:
    """Rule 2 — no citation may carry a `:N` or `:N-M` suffix."""
    problems = []
    for token in _SPAN.findall(_prose(text)):
        problems.extend(_LINE_NUMBERED.findall(token))
    return sorted(set(problems))


def symbol_disagreements(
    text: str, root: Path, pinned: tuple[tuple[str, str], ...]
) -> list[str]:
    """Rule 3 — each pinned symbol is named by the doc AND still in its file."""
    problems = []
    for path, symbol in pinned:
        if symbol not in text:
            problems.append(f"the document never names {symbol} (pinned to {path})")
        target = root / path
        if not target.is_file():
            problems.append(f"{path} does not exist, so {symbol} cannot be pinned to it")
        elif symbol not in target.read_text(encoding="utf-8"):
            problems.append(f"{symbol} is no longer in {path}")
    return problems


def missing_headings(text: str, required: tuple[str, ...]) -> list[str]:
    """Rule 4 — every required `## ` heading appears as a whole line."""
    lines = {line.rstrip() for line in text.splitlines()}
    return [heading for heading in required if heading not in lines]


def missing_links(text: str, required: tuple[str, ...]) -> list[str]:
    """Rule 5 — every required markdown link target appears in `](target)` form."""
    return [target for target in required if f"]({target})" not in text]


def missing_mentions(text: str, required: tuple[str, ...]) -> list[str]:
    """Rule 6 — every required literal string appears somewhere in the text."""
    return [needle for needle in required if needle not in text]


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(
            f"{path.relative_to(REPO_ROOT)} does not exist. This gate was written "
            "before the documents it guards, deliberately, so this failure is the "
            "expected state between the test landing and the docs landing."
        )
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# The rules against the real tree
# --------------------------------------------------------------------------


def test_the_retailer_doc_cites_no_path_that_does_not_exist() -> None:
    problems = missing_cited_paths(_read(RETAILER_DOC), REPO_ROOT)

    assert not problems, (
        f"docs/adding-a-retailer.md cites paths that are not in this tree: {problems}. "
        "A contributor sent to a file that is not there loses the time it takes to "
        "find that out, and the doc looks authoritative while they do."
    )


def test_the_retailer_doc_cites_no_line_number() -> None:
    problems = line_numbered_citations(_read(RETAILER_DOC))

    assert not problems, (
        f"docs/adding-a-retailer.md carries line-numbered citations: {problems}. "
        "04-03 moves several hundred lines in this phase alone. Cite a Python file "
        "by naming a symbol in it and the evidence log by naming its heading."
    )


def test_the_retailer_doc_and_the_tree_agree_about_every_pinned_symbol() -> None:
    problems = symbol_disagreements(_read(RETAILER_DOC), REPO_ROOT, REQUIRED_SYMBOLS)

    assert not problems, (
        f"docs/adding-a-retailer.md and the tree disagree: {problems}. Both "
        "directions are failures — a doc that never names the dispatch point has "
        "not explained where an adapter goes, and a doc naming a symbol that was "
        "renamed sends a contributor after something that is not there."
    )


def test_the_retailer_doc_carries_every_required_heading() -> None:
    problems = missing_headings(_read(RETAILER_DOC), RETAILER_DOC_HEADINGS)

    assert not problems, f"docs/adding-a-retailer.md is missing headings: {problems}"


def test_the_retailer_doc_tells_a_contributor_to_install_the_commit_hook() -> None:
    """The security-critical instruction, checked in the document that walks a capture.

    A contributor following this doc will capture a fixture from a retailer that
    echoes their own network back at them. The hook is tracked but opt-in, so
    until they run `make hooks` there is nothing between that capture and a
    public repository.
    """
    problems = missing_mentions(_read(RETAILER_DOC), ("make hooks", "--no-verify"))

    assert not problems, (
        f"docs/adding-a-retailer.md no longer states: {problems}. `make hooks` is "
        "the instruction; the `--no-verify` prohibition is the half that stops the "
        "instruction being worked around."
    )


def test_contributing_cites_no_path_that_does_not_exist() -> None:
    problems = missing_cited_paths(_read(CONTRIBUTING), REPO_ROOT)

    assert not problems, f"CONTRIBUTING.md cites paths that are not in this tree: {problems}"


def test_contributing_cites_no_line_number() -> None:
    problems = line_numbered_citations(_read(CONTRIBUTING))

    assert not problems, f"CONTRIBUTING.md carries line-numbered citations: {problems}"


def test_contributing_carries_every_required_heading() -> None:
    problems = missing_headings(_read(CONTRIBUTING), CONTRIBUTING_HEADINGS)

    assert not problems, f"CONTRIBUTING.md is missing headings: {problems}"


def test_contributing_names_the_three_commands_a_contributor_has_to_run() -> None:
    problems = missing_mentions(_read(CONTRIBUTING), CONTRIBUTING_MENTIONS)

    assert not problems, (
        f"CONTRIBUTING.md no longer names: {problems}. These are the three "
        "operational facts a contributor cannot infer: install the hook, what the "
        "guard is, and which verify target is the one that makes no live requests."
    )


def test_the_readme_points_at_both_contributor_documents() -> None:
    problems = missing_links(_read(README), ("docs/adding-a-retailer.md", "CONTRIBUTING.md"))

    assert not problems, (
        f"README.md no longer links: {problems}. A contributor doc nothing links to "
        "is a doc nobody finds."
    )


def test_the_readme_links_the_licence_file_without_this_test_stating_it_exists() -> None:
    """The link text is this plan's obligation; the file is 04-02's.

    Deliberately NO `LICENSE.exists()` here. 04-02 creates that file in the next
    wave, and a stat in this test would make this plan's gate pass or fail on
    another plan's completion order — the same defect whether the waves are
    ordered or not. 04-02 ships its own packaging-metadata test that fails if the
    declared licence and the shipped file ever disagree.
    """
    problems = missing_links(_read(README), ("LICENSE",))

    assert not problems, "README.md's License section no longer links the LICENSE file"


# --------------------------------------------------------------------------
# The same rules, watched failing on a deliberately broken copy
# --------------------------------------------------------------------------


def _corrupt(path: Path, old: str, new: str) -> str:
    """The real document with one thing changed. Fails loudly if `old` is absent.

    The assertion matters more than the substitution: a corruption test whose
    edit silently did nothing asserts that a rule fires on the SHIPPED file,
    which is the one thing it must never claim.
    """
    text = _read(path)
    assert old in text, f"nothing to corrupt: {old!r} is not in {path.name}"
    return text.replace(old, new, 1)


def test_a_fabricated_path_citation_is_caught() -> None:
    broken = _corrupt(
        RETAILER_DOC,
        "## Why a control product is mandatory",
        "See `boty/no_such_module.py`.\n\n## Why a control product is mandatory",
    )

    problems = missing_cited_paths(broken, REPO_ROOT)

    assert problems == ["boty/no_such_module.py"]


def test_a_line_numbered_citation_is_caught() -> None:
    broken = _corrupt(RETAILER_DOC, "`boty/retailers.py`", "`boty/retailers.py:42`")

    problems = line_numbered_citations(broken)

    assert problems == ["boty/retailers.py:42"]
    assert not line_numbered_citations(_read(RETAILER_DOC)), (
        "the shipped document must be clean, or the test above proves nothing"
    )


def test_a_symbol_the_document_stops_naming_is_caught() -> None:
    """Direction one: the doc drops a symbol that is still in the tree."""
    broken = _read(RETAILER_DOC).replace("MARKETPLACES", "the marketplace set")

    problems = symbol_disagreements(broken, REPO_ROOT, REQUIRED_SYMBOLS)

    assert problems == ["the document never names MARKETPLACES (pinned to boty/retailers.py)"]


def test_a_symbol_the_tree_no_longer_carries_is_caught() -> None:
    """Direction two, and the one that catches a rename nobody told the doc about."""
    pinned = (("boty/cli.py", "_no_such_function"),)

    problems = symbol_disagreements(_read(RETAILER_DOC), REPO_ROOT, pinned)

    assert problems == [
        "the document never names _no_such_function (pinned to boty/cli.py)",
        "_no_such_function is no longer in boty/cli.py",
    ]


def test_a_deleted_heading_is_caught() -> None:
    broken = _corrupt(RETAILER_DOC, "## The UNKNOWN contract", "### The unknown bit")

    problems = missing_headings(broken, RETAILER_DOC_HEADINGS)

    assert problems == ["## The UNKNOWN contract"]


def test_a_deleted_readme_link_is_caught() -> None:
    broken = _read(README).replace("](docs/adding-a-retailer.md)", "(that doc)")

    problems = missing_links(broken, README_LINKS)

    assert problems == ["docs/adding-a-retailer.md"]


def test_a_deleted_mention_is_caught() -> None:
    broken = _read(CONTRIBUTING).replace("make hooks", "the hook target")

    problems = missing_mentions(broken, CONTRIBUTING_MENTIONS)

    assert problems == ["make hooks"]


def test_the_path_extractor_skips_what_it_cannot_be_sure_about() -> None:
    """The other half of rule 1: what it must NOT fail on.

    A rule that fails on a shell fragment, a URL or an identifier gets loosened
    by the next person who trips over it, and a loosened rule catches nothing.
    Every token here appears in one of the two documents this file guards.
    """
    assert not _looks_like_a_repo_path("make hooks")
    assert not _looks_like_a_repo_path("--no-verify")
    assert not _looks_like_a_repo_path("_make_checker")
    assert not _looks_like_a_repo_path("MARKETPLACES")
    assert not _looks_like_a_repo_path("https://schema.org/InStock")
    assert not _looks_like_a_repo_path("nintendo.com/us/store/products/")
    assert not _looks_like_a_repo_path("boty.fetch.BLOCK_PHRASES")

    assert _looks_like_a_repo_path("boty/retailers.py")
    assert _looks_like_a_repo_path("hooks/pre-commit")
    assert _looks_like_a_repo_path("README.md")
    assert _looks_like_a_repo_path("Makefile")
