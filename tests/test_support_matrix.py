"""The README support matrix, checked mechanically rather than by eye.

WHY THIS FILE EXISTS
--------------------
Phase 3 criterion 3 reads: *any retailer reached via rung 3 is flagged DEGRADED
in the matrix AND in `boty check` output*. The runtime half of that is pinned in
three separate places already — `Result.degraded` is derived from the rung,
mutation M6 flips it and the suite notices,
`test_a_browser_reading_serialises_as_degraded` reads it out of the published
payload, and `tests/test_dashboard.py` pins the page that renders it.

The matrix half was prose in `README.md` and nothing checked it.

That asymmetry is exactly the shape of WR-04: a contract asserted at the
producing end and quietly unimplemented at the consuming one. It also fails in
the most expensive direction — a retailer whose reading is genuinely
lower-confidence looks first-class in the table a reader consults *before* they
decide whether to trust the number, and the runtime flag they never see is no
help at all.

WHY THE RETAILER SET IS IMPORTED RATHER THAN RETYPED
----------------------------------------------------
`ROADMAP_RETAILERS` in `scripts/evidence_check.py` is the one machine-readable
statement of which stores are in scope. Retyping the list here would give the
tree two definitions free to drift into disagreeing about which retailers
exist, and the drift would be invisible: each gate would go on passing against
its own list.

Note the match here is **exact** — the display value must equal the README
row's first cell character for character, accent included — whereas
`evidence_check` matches the same value as a *prefix* of a `## ` heading. Those
are two different obligations on one constant, which is why 03-01 pins the seven
literals in `test_roadmap_retailers_is_exactly_the_seven_in_scope`. If a row
does not match, fix the README label; do not loosen the comparison, or this file
stops being able to fail.

WHY THE CHECKS ARE FUNCTIONS OVER PARSED ROWS
----------------------------------------------
Each rule is a function of the table, so the corruption tests at the bottom run
the *same* rule against a deliberately broken copy of the real README. A gate
asserted only against the tree it is meant to guard has never been watched
failing, and this project has already shipped one of those.

WHY THE RUNG CELL IS BOUND TO THE CODE, AND WHAT THAT BINDING COSTS
--------------------------------------------------------------------
The Rung cell was the one column in this table bound to nothing at all.
Measured 2026-08-10 against the tree with no binding in it: mutating
`check_amazon` to return `Rung.BROWSER` — which contradicts the shipped
`| Amazon | 1 | dom |` row outright — left the suite GREEN, pytest exit 0,
`687 passed, 1 skipped`. REQ-18 recorded the same measurement at an older
suite size ("left 131 tests green"); the number moved and the fact did not.

Two joins had to be built, not one, and neither existed before. The
README-to-code binding runs retailer → adapter (the `if`-chain inside
`cli._make_checker`) and then adapter → rung (the literal `rung=Rung.X`
keywords in `boty/retailers.py`). A gate that bound only the second half would
stay green the day `_make_checker` stopped routing amazon to `check_amazon`,
which is the same false claim one join further along.

The binding is STATIC: it walks the source of those two files with `ast` and
never imports or runs either. That is what makes the routing chain visible at
all — a dynamic binding would have to drive five adapters across three
transports, including `check_bestbuy_api`, for which this repository holds no
fixture, and it still could not see the `if`-chain. THE COST IS STATED RATHER
THAN BURIED: a static gate asserts what the source SAYS, not what RUNS. That
cost is small here because the failure REQ-18 names *is* a source edit —
somebody changes an adapter's rung and forgets the README — and because the
runtime half is already covered elsewhere: `tests/test_retailers.py` asserts
`result.rung is Rung.BROWSER` / `Rung.API` through `cli._make_checker` for Best
Buy on both of its arms. This file binds the README to the source; those tests
bind the source to behaviour. Neither substitutes for the other.

`ast` over this repository's own files is an established idiom here rather
than a new one: `tests/test_ci_workflow.py` walks its own source, and
`tests/test_alert_text.py` walks `boty/monitor.py` and `boty/notify.py`.

Nothing here touches the network. It reads four files off disk.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from typing import Any

from boty.config import Config
from boty.models import KNOWN_RETAILERS, Rung

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
CONFIG = REPO_ROOT / "config" / "products.yaml"

#: The two source files the Rung binding reads. Text, never imports.
#:
#: `REPO_ROOT` is `Path(__file__).resolve().parent.parent`, which inside
#: `scripts/mutation_check.py`'s sandbox resolves to the SANDBOX root rather
#: than to this repository — `boty` and `README.md` are both in
#: `SANDBOX_CONTENTS`. That is not incidental: it is the entire mechanism by
#: which a mutated adapter becomes visible to this gate, and it costs no
#: sandbox edit, no skip and no `HarnessError` risk.
CLI = REPO_ROOT / "boty" / "cli.py"
RETAILERS = REPO_ROOT / "boty" / "retailers.py"

#: The header of the retailer table in README.md. Located by its cells rather
#: than by a line number, so editing the prose around it cannot silently point
#: this file at some other table — the `make verify` verdict table further down
#: is three columns and the stage table is two, but that is luck, not a rule.
HEADER_CELLS = ("Retailer", "Rung", "Extraction", "robots.txt", "Terms", "Method", "Status")

#: Column indices within a matrix row.
RETAILER, RUNG, EXTRACTION, ROBOTS, TERMS, METHOD, STATUS = 0, 1, 2, 3, 4, 5, 6

#: The vocabulary a robots.txt cell may open with (REQ-13).
#:
#: Fixed, because a cell nothing can parse is prose nobody enforces — `TBD`,
#: `n/a`, a blank and a paragraph of hedging are all ways of not answering, and
#: they all look filled in.
#:
#: `silent on` and `permits` are BOTH permissive and the distinction is
#: editorial: `robots.txt` is a deny-list, so a path with no matching rule is
#: permitted. `unread` is the fourth state and the honest one — see
#: `UNREAD_POSITIONS`.
ROBOTS_POSITIONS = ("permits", "disallows", "silent on", "unread")

#: The vocabulary a Terms cell may open with (REQ-13).
#:
#: `silent` here means only the ABSENCE OF A PROHIBITION, which is not the same
#: claim `silent on` makes in the robots column. A terms document that does not
#: mention automated access has not licensed it.
TERMS_POSITIONS = ("forbids", "permits", "silent", "unread")

#: The positions that are prohibitive. Everything else in the vocabularies is
#: permissive, except `unread`, which is neither and must not be treated as
#: either — see `_disagrees`.
PROHIBITIVE = ("disallows", "forbids")

#: The literal marker a row carries when its two positions point opposite ways.
DISAGREE = "⚠ disagree"

#: Exactly which (retailer, column) cells may say `unread`, pinned literally.
#:
#: WHY THIS IS A PIN AND NOT A RULE. `unread` is the honest answer for a policy
#: document that refused us, and three retailers did refuse on 2026-08-03 — but
#: an unconditional fourth vocabulary word is also the cheapest possible escape
#: from REQ-13. Paste `unread` into all fourteen position cells and every row is
#: vocabulary-clean, no row can ever disagree, and `_misdeclared_disagreement`
#: becomes a rule about the empty set. That is precisely how the Phase 2 count
#: clause rotted: an escape hatch that stayed satisfied forever.
#:
#: So the set is enumerated. Widening it means editing a red test, in the same
#: commit as the evidence-log entry that justifies it, exactly as
#: `test_roadmap_retailers_is_exactly_the_seven_in_scope` forces for the
#: retailer list. Narrowing it is what a later plan does when it finally reads
#: one of these documents.
UNREAD_POSITIONS = frozenset(
    {
        ("GameStop", ROBOTS),  # robots.txt itself returned 403 (Cloudflare)
        ("GameStop", TERMS),  # not requested — no-escalation rule after the 403
        ("Walmart", TERMS),  # `Robot or human?` challenge served at HTTP 200
        ("Best Buy", ROBOTS),  # HTTP/2 INTERNAL_ERROR, connection layer
        ("Best Buy", TERMS),  # same refusal, same day
    }
)

#: A rung cell must begin with one of these. Rung 4 — "dropped, with the
#: evidence written down" — is a real answer, so there is no honest reason for
#: a retailer in scope to have `—`, `Planned` or nothing here.
RUNGS = {"1", "2", "3", "4"}

#: The rungs that claim the monitor CAN read this retailer. Rung 4 is the only
#: honest rung for a retailer nothing watches, so these three are exactly the
#: cells that must be backed by a configured watch.
WORKING_RUNGS = {"1", "2", "3"}

#: The numeral each `Rung` member is published as in the README's rung column.
#:
#: WHY IT DID NOT ALREADY EXIST. Nothing in this tree mapped a `Rung` to a
#: numeral anywhere — `boty/models.py` names the members and `README.md` numbers
#: the ladder, and the two were joined only in a reader's head. That is the
#: whole of REQ-18's gap: the column could say anything.
#:
#: WHY IT LIVES HERE AND NOT IN `boty/models.py`. A numeral is a documentation
#: fact about the ladder `README.md` publishes, not a runtime fact. `models.Rung`
#: deliberately keeps itself out of `monitor` and `Health`, and nothing in the
#: package needs to know what a rung is *called* in a table. Putting it in the
#: package would give `boty/` a constant whose only consumer is a test.
#:
#: WHY IT IS A PIN AND NOT A RULE, in `UNREAD_POSITIONS`' and
#: `TRUSTED_ACTION_OWNERS`' sense: it is enumerated with its justification
#: inline, so widening it means editing a red test rather than deriving a
#: number from whatever the enum happens to hold. The justification is quotable
#: from both sides and the two already agree word for word — README's ladder
#: paragraph ("Rung 1 is impersonated HTTP, rung 2 a retailer's own sanctioned
#: API, rung 3 a real browser, rung 4 'dropped, with the evidence written
#: down'") and the three `Rung` member docstrings ("Impersonated TLS against the
#: public product page", "The retailer's own sanctioned API", "A real browser
#: rendering the page").
#:
#: RUNG 4 HAS NO MEMBER ON PURPOSE, and that absence is load-bearing rather than
#: an oversight — `models.Rung`'s own docstring says so: "There is no member for
#: rung 4 ('dropped'): a dropped retailer produces no readings, so a `Rung` for
#: it would be a value that can never appear on a `Result`." So the values of
#: this mapping are exactly `WORKING_RUNGS`, asserted in both directions by
#: `test_every_rung_member_has_a_numeral_and_rung_four_has_none`, and a rung-4
#: matrix row is a claim that NOTHING reads that retailer rather than a claim
#: about a transport.
RUNG_NUMERALS: dict[Rung, str] = {Rung.TLS: "1", Rung.API: "2", Rung.BROWSER: "3"}

#: The vocabulary an Extraction cell may state, mirroring `boty.models.Extraction`
#: — `structured` for a retailer's own machine-readable feed, `dom` for
#: presentation markup a reskin breaks silently.
#:
#: The second axis exists because a rung is only half of what a reading is
#: worth. Best Buy is rung 3 + `structured`: a browser renders the page and
#: what is read off it is Best Buy's own schema.org feed. A rung-3 + `dom` row
#: would sit on the same rung and be worth materially less.
EXTRACTIONS = ("structured", "dom")

#: What a rung-4 row states, because nothing is extracted from a retailer the
#: monitor does not read.
#:
#: Tied to the Rung cell in BOTH directions by `_extraction_mismatch`, so this
#: is a claim rather than a blank. A `—` accepted unconditionally would be the
#: REQ-13 escape hatch `UNREAD_POSITIONS` had to be pinned against: paste it
#: into all seven rows and the column distinguishes nothing while looking
#: filled in.
NO_EXTRACTION = "—"


def _load_evidence_check() -> Any:
    """Import `scripts/evidence_check.py` by path — `scripts/` is not a package.

    The same `spec_from_file_location` idiom `tests/test_control_check.py` uses.
    """
    spec = importlib.util.spec_from_file_location(
        "evidence_check_for_matrix", REPO_ROOT / "scripts" / "evidence_check.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVIDENCE_CHECK: Any = _load_evidence_check()
ROADMAP_RETAILERS: dict[str, str] = EVIDENCE_CHECK.ROADMAP_RETAILERS
EVIDENCE = REPO_ROOT / "docs" / "retailer-evidence.md"

#: The rung cell of a retailer in scope that nobody has probed yet.
#:
#: There is no rung to report — that is the whole content of an UNPROBED verdict
#: — so the cell says so rather than guessing a number. Accepted ONLY for a
#: retailer whose evidence-log section carries the matching verdict, because a
#: bare `—` accepted unconditionally is exactly the "Planned" evasion
#: `test_a_planned_rung_cell_fails_too` exists to catch.
UNPROBED_RUNG = "—"


def _unprobed_retailers(evidence_text: str | None = None) -> set[str]:
    """Display names carrying a well-formed UNPROBED verdict in the evidence log.

    Read through `evidence_check` rather than re-derived, for the reason WR-04
    gave: two readers of one document drift, and these two already had.
    """
    text = EVIDENCE.read_text(encoding="utf-8") if evidence_text is None else evidence_text
    sections = EVIDENCE_CHECK.split_sections(text)
    return {
        name
        for name in ROADMAP_RETAILERS.values()
        for body in EVIDENCE_CHECK.sections_for(name, sections)
        if EVIDENCE_CHECK.unprobed_lines(body)
    }


# --------------------------------------------------------------------------
# Reading the table
# --------------------------------------------------------------------------


def _cells(line: str) -> list[str]:
    """The pipe-delimited cells of one markdown table row."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _matrix(readme_text: str | None = None) -> dict[str, list[str]]:
    """Map each retailer label to the cells of its row in the support matrix."""
    text = README.read_text(encoding="utf-8") if readme_text is None else readme_text
    lines = text.splitlines()

    start = next(
        (
            i
            for i, line in enumerate(lines)
            if line.startswith("|") and tuple(_cells(line)) == HEADER_CELLS
        ),
        None,
    )
    assert start is not None, (
        f"no retailer table in {README}: expected a header row of {HEADER_CELLS}. "
        "The support matrix is a phase deliverable; if it moved, this test moves with it."
    )

    rows: dict[str, list[str]] = {}
    for line in lines[start + 2 :]:  # +2 skips the header and its |---| separator
        if not line.startswith("|"):
            break
        cells = _cells(line)
        rows[cells[RETAILER]] = cells
    return rows


# --------------------------------------------------------------------------
# The rules, as functions, so the corruption tests can run the same ones
# --------------------------------------------------------------------------


def _missing(rows: dict[str, list[str]]) -> list[str]:
    return [name for name in ROADMAP_RETAILERS.values() if name not in rows]


def _rungless(
    rows: dict[str, list[str]], unprobed: set[str] | None = None
) -> dict[str, str]:
    """Retailers in scope whose rung cell does not answer the question.

    `unprobed` is the set carrying an UNPROBED verdict in the evidence log, and
    only those may use `—`. Defaulting it to empty keeps the corruption tests
    below honest: they assert that a blank or `Planned` cell fails, and they must
    go on doing so for a retailer that has no unprobed verdict backing it.
    """
    unprobed = set() if unprobed is None else unprobed
    return {
        name: rows[name][RUNG]
        for name in ROADMAP_RETAILERS.values()
        if name in rows
        and rows[name][RUNG][:1] not in RUNGS
        and not (name in unprobed and rows[name][RUNG].startswith(UNPROBED_RUNG))
    }


def _overstated(rows: dict[str, list[str]], configured: set[str]) -> list[str]:
    """Retailers the table claims a working rung for while nothing watches them.

    The direction `test_every_configured_retailer_is_documented_in_the_matrix`
    does NOT cover, and the more dangerous of the two. That rule checks
    `configured ⊆ documented` — the table understating what the monitor does.
    This checks the reverse: the table OVERSTATING it.

    Nothing enforced it before. `_rungless` only wants a digit 1-4 and
    `_undeclared_degraded` looked only at rung-3 rows (it now looks at `dom`
    rows too, but that is still not this claim), so
    `| GameStop | 1 | curl_cffi + schema.org JSON-LD | ✅ Working |` passed every
    rule whether or not a gamestop watch existed. Reproduced: with the gamestop
    and walmart watch blocks deleted and two REFUSED sections appended, 253
    tests passed, `evidence_check --phase` returned `[]`, and the table went on
    telling a reader both were watched at rung 1 and working. That reader is the
    person this whole phase built the matrix for.
    """
    return sorted(
        name
        for key, name in ROADMAP_RETAILERS.items()
        if name in rows and rows[name][RUNG][:1] in WORKING_RUNGS and key not in configured
    )


def _position(cell: str, vocabulary: tuple[str, ...]) -> str | None:
    """The vocabulary word a cell opens with, or None if it opens with none.

    Longest match first, so `silent on` is not shadowed by a shorter entry if
    one is ever added — a prefix vocabulary where order changes the answer is a
    rule that depends on how somebody typed the tuple.
    """
    for word in sorted(vocabulary, key=len, reverse=True):
        if cell.startswith(word):
            return word
    return None


def _positionless(rows: dict[str, list[str]]) -> dict[str, tuple[str, str]]:
    """Retailers whose robots.txt or Terms cell does not state a position.

    REQ-13's floor. A cell fails if it does not open with a word from its
    vocabulary — blank, `TBD`, `n/a` and free prose all fail — and a *judged*
    robots cell fails if it does not name the path in backticks, because a
    position on no particular path is not a position. `robots.txt` rules are
    per-path: `permits` is meaningless until you say permits WHAT, and the whole
    reason this column exists is that Target permits `/p/` while disallowing all
    of `redsky.target.com`.

    An `unread` robots cell is exempt from the backtick requirement in the sense
    that it is making a claim about a document rather than a path — but it is
    not exempt from the vocabulary, and which rows may use it is pinned in
    `UNREAD_POSITIONS`.
    """
    bad: dict[str, tuple[str, str]] = {}
    for name in ROADMAP_RETAILERS.values():
        if name not in rows:
            continue
        robots, terms = rows[name][ROBOTS], rows[name][TERMS]
        position = _position(robots, ROBOTS_POSITIONS)
        if (
            position is None
            or (position != "unread" and "`" not in robots)
            or _position(terms, TERMS_POSITIONS) is None
        ):
            bad[name] = (robots, terms)
    return bad


def _disagrees(row: list[str]) -> bool | None:
    """Do this row's two positions point in opposite directions?

    `None` means the question cannot be asked — one side is `unread`, or the
    cell states no position at all. That third answer is load-bearing: treating
    `unread` as permissive would demand a `⚠ disagree` marker on a row where a
    prohibition faces a document nobody has read, which claims a comparison
    nobody has made.
    """
    robots = _position(row[ROBOTS], ROBOTS_POSITIONS)
    terms = _position(row[TERMS], TERMS_POSITIONS)
    if robots is None or terms is None or "unread" in (robots, terms):
        return None
    return (robots in PROHIBITIVE) != (terms in PROHIBITIVE)


def _misdeclared_disagreement(rows: dict[str, list[str]]) -> list[str]:
    """Rows whose `⚠ disagree` marker does not match whether they disagree.

    DELIBERATELY TWO-DIRECTIONAL, and that is the whole value of it. A rule of
    the form "every row must carry `⚠ disagree`" is satisfied by pasting the
    marker into all seven rows, at which point it distinguishes nothing and
    REQ-13's "a reader sees the disagreement" is decoration. This one goes red
    for a marker that is MISSING and for one that is NOT EARNED, so the marker
    keeps meaning something.

    A row that cannot be compared (`_disagrees` → None) must not carry the
    marker either: "we could not read one of these documents" is not a
    disagreement, and dressing it as one would overstate what this repo knows.
    """
    return sorted(
        name
        for name in ROADMAP_RETAILERS.values()
        if name in rows
        and (DISAGREE in " ".join(rows[name])) is not (_disagrees(rows[name]) is True)
    )


def _unread_cells(rows: dict[str, list[str]]) -> set[tuple[str, int]]:
    """Every (retailer, column) position cell currently saying `unread`."""
    return {
        (name, column)
        for name in ROADMAP_RETAILERS.values()
        if name in rows
        for column, vocabulary in ((ROBOTS, ROBOTS_POSITIONS), (TERMS, TERMS_POSITIONS))
        if _position(rows[name][column], vocabulary) == "unread"
    }


def _extraction_mismatch(rows: dict[str, list[str]]) -> dict[str, tuple[str, str]]:
    """Rows whose Extraction cell and Rung cell disagree about whether anything is read.

    DELIBERATELY TWO-DIRECTIONAL, for the reason `_misdeclared_disagreement`
    is. A rung-4 row must carry `—` because nothing is extracted from a
    retailer the monitor does not read; a rung-1/2/3 row must carry a member of
    `EXTRACTIONS`, because a row claiming a working rung is claiming a reading,
    and a reading came from somewhere.

    One-directional would be worthless. "Every row must state an Extraction" is
    satisfied by writing `—` in all seven, at which point the column says
    nothing and the rung-3-versus-rung-3 distinction it was added for is gone.
    So `—` is not a free cell: it is a claim about the rung beside it, and it
    goes red when the two disagree either way.

    Returns `{retailer: (rung_cell, extraction_cell)}`.
    """
    bad: dict[str, tuple[str, str]] = {}
    for name in ROADMAP_RETAILERS.values():
        if name not in rows:
            continue
        rung, extraction = rows[name][RUNG], rows[name][EXTRACTION]
        working = rung[:1] in WORKING_RUNGS
        if (working and extraction not in EXTRACTIONS) or (
            not working and extraction != NO_EXTRACTION
        ):
            bad[name] = (rung, extraction)
    return bad


def _undeclared_degraded(rows: dict[str, list[str]]) -> list[str]:
    """Rows whose reading is lower-confidence and whose text does not say so.

    `Result.degraded` has TWO disjuncts now — `rung is BROWSER or extraction is
    DOM` — and the matrix half has to track both. If it only tracked the rung,
    the two halves of criterion 3's degraded contract would drift apart: a DOM
    reading would be flagged at runtime and presented as first-class in the
    table a reader consults *before* deciding whether to trust the number. That
    is the WR-04 shape this file's preamble was written about, and it is the
    more expensive direction of the two.

    A `dom` row on rung 1 is the case worth naming. Nothing about its transport
    is wrong; it is what was read out of the bytes that a reader has to
    discount, and no rule looking only at the rung column can see it.
    """
    return [
        name
        for name in ROADMAP_RETAILERS.values()
        if name in rows
        and (rows[name][RUNG].startswith("3") or rows[name][EXTRACTION] == "dom")
        and "degrad" not in " ".join(rows[name]).lower()
    ]


# --------------------------------------------------------------------------
# The Rung cell, bound to the code that takes it — both joins, statically
# --------------------------------------------------------------------------


def _scoped_nodes(function: ast.FunctionDef) -> list[ast.AST]:
    """Every node inside `function` that is not inside a NESTED function.

    Attribution matters here: a `rung=Rung.X` keyword written inside a closure
    is a claim made by that closure, not by whatever encloses it. A plain
    `ast.walk` would credit both, and the adapter map would start reporting
    rungs an adapter does not itself take.
    """
    found: list[ast.AST] = []
    stack: list[ast.AST] = list(ast.iter_child_nodes(function))
    while stack:
        node = stack.pop()
        found.append(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        stack.extend(ast.iter_child_nodes(node))
    return found


def _called_names(node: ast.AST) -> list[str]:
    """The plainly-named functions called in every `return` under `node`.

    RECURSIVE, and that is the point rather than a convenience: Best Buy's arm
    holds a nested `if cfg.bestbuy_api_key:` whose own `return` names
    `check_bestbuy_api`. A walk that looked only at an arm's top-level returns
    would drop that adapter silently, and the Best Buy row's second numeral —
    the `(2 with a key)` half — would become unbacked without anything going
    red.
    """
    names: list[str] = []
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Return) or inner.value is None:
            continue
        for call in ast.walk(inner.value):
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
                names.append(call.func.id)
    return names


def _routing(
    cli_text: str | None = None, known: frozenset[str] | None = None
) -> dict[str, tuple[str, ...]]:
    """Retailer key → the adapter functions `cli._make_checker` can return for it.

    The first of the Rung binding's two joins. It is read out of the source
    because that `if`-chain is the only place a watch is matched to a transport
    — `_make_checker`'s own docstring says so — and because nothing else in
    this tree can see it: no test routes a `target` watch through
    `_make_checker` at all.

    `known` is the set of retailers the FALLTHROUGH `return` serves, and it is a
    PARAMETER rather than a closed-over import for one reason: it is what lets
    the corruption tests below watch the rung-4 direction go red without editing
    a byte of source text. Passing `frozenset()` yields exactly the keys the
    router names in an `if`, which is a different and also useful question.

    AN UNPARSEABLE ROUTER RAISES. It does not return `{}`. A rule handed an
    empty mapping reports all seven rows clean and every gate above it goes on
    passing — the vacuous pass this file's preamble was written against, one
    column over. `_matrix` already set the precedent with its `assert start is
    not None`, and the messages here name what was not found for the same
    reason: a gate that loses its footing has to say where.
    """
    text = CLI.read_text(encoding="utf-8") if cli_text is None else cli_text
    known = KNOWN_RETAILERS if known is None else known
    tree = ast.parse(text)

    maker = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_make_checker"),
        None,
    )
    assert maker is not None, (
        f"no `_make_checker` function in {CLI}: the one place a watch is matched to a "
        "transport. If it was renamed or replaced by a registry, this binding moves with it — "
        "it must never quietly report that every retailer routes nowhere."
    )
    checker = next(
        (n for n in ast.iter_child_nodes(maker) if isinstance(n, ast.FunctionDef) and n.name == "check"),
        None,
    )
    assert checker is not None, (
        f"no nested `check` closure inside `_make_checker` in {CLI}. The routing `if`-chain "
        "lives in that closure; without it there is nothing to read, and an empty mapping "
        "would report the whole support matrix clean."
    )

    arms: dict[str, tuple[str, ...]] = {}
    fallthrough: tuple[str, ...] | None = None
    for statement in checker.body:
        if isinstance(statement, ast.If):
            keys = [
                node.value
                for node in ast.walk(statement.test)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
            ]
            adapters = tuple(dict.fromkeys(_called_names(statement)))
            for key in keys:
                arms[key] = adapters
        elif isinstance(statement, ast.Return):
            fallthrough = tuple(dict.fromkeys(_called_names(statement)))

    assert fallthrough is not None, (
        f"no fallthrough `return` at the end of `check` in {CLI}. Every retailer with no arm "
        "of its own is served by that return, so without it this binding would report "
        "GameStop, Walmart and Nintendo as routed to nothing — three false clean rows."
    )

    routing = dict(arms)
    for key in sorted(known - set(arms)):
        routing[key] = fallthrough
    return routing


def _adapter_rungs(retailers_text: str | None = None) -> dict[str, tuple[str, ...]]:
    """Adapter function name → the rung numerals its own source can produce.

    The second join. Collected from LITERAL `rung=Rung.X` keyword arguments and
    from nothing else.

    WHY ONLY A LITERAL. `_verdict_from_html` takes `rung` as a parameter and
    passes `rung=rung` into every `Result(...)` it builds. That is an `ast.Name`
    rather than an `ast.Attribute`, so this walk does not see it and
    `_verdict_from_html` does not appear in this mapping at all. That is
    deliberate: a pass-through is not a claim about which rung anything takes.
    The claim is made at the call site that supplies the literal, which is
    exactly where `check_html`, `check_amazon` and the three others make it.

    An unrecognised member name RAISES rather than being skipped, for
    `_routing`'s reason: a `Rung` member this mapping cannot name is a rung the
    support matrix cannot describe, and quietly dropping it would report the
    adapter as taking one fewer rung than it does.
    """
    text = RETAILERS.read_text(encoding="utf-8") if retailers_text is None else retailers_text
    tree = ast.parse(text)

    rungs: dict[str, tuple[str, ...]] = {}
    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef):
            continue
        numerals: set[str] = set()
        for node in _scoped_nodes(function):
            if not isinstance(node, ast.keyword) or node.arg != "rung":
                continue
            value = node.value
            if not (isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name)):
                continue
            if value.value.id != "Rung":
                continue
            member = Rung.__members__.get(value.attr)
            assert member is not None, (
                f"{function.name} names `Rung.{value.attr}`, which is not a member of "
                f"boty.models.Rung ({sorted(Rung.__members__)}). Either the enum moved or the "
                "source is unparseable by this gate; both are louder than a dropped rung."
            )
            assert member in RUNG_NUMERALS, (
                f"{function.name} takes {member!r}, which RUNG_NUMERALS does not name. "
                "Add it there, with the README ladder sentence that justifies its numeral."
            )
            numerals.add(RUNG_NUMERALS[member])
        if numerals:
            rungs[function.name] = tuple(sorted(numerals))
    return rungs


def _declared_rungs(cell: str) -> tuple[str, ...]:
    """The numerals a README rung cell declares — the primary, plus any alternates.

    The primary is the established `cell[:1]`, the same one-character read
    `_rungless`, `_overstated` and `_extraction_mismatch` all make. Every digit
    inside parentheses is an ALTERNATE.

    That is what makes Best Buy's `3 (2 with a key)` a two-numeral claim instead
    of a special case: it declares `('2', '3')`, its two adapters take `('2',
    '3')`, and a plain set comparison settles it. A conditional cell needs no
    exemption, which is the only version of it worth having — an exemption is a
    row that stops being checked.

    A parenthetical this pattern cannot read yields the primary alone, and that
    FAILS SAFE rather than passing: Best Buy's code side would still be
    `('2', '3')` against a declared `('3',)`, so the row goes red and somebody
    looks at the cell.
    """
    alternates = {
        digit
        for group in re.findall(r"\(([^)]*)\)", cell)
        for digit in re.findall(r"\d", group)
    }
    return tuple(sorted({cell[:1]} | alternates))


def _rung_mismatch(
    rows: dict[str, list[str]],
    routing: dict[str, tuple[str, ...]] | None = None,
    rungs: dict[str, tuple[str, ...]] | None = None,
) -> dict[str, tuple[str, str]]:
    """Rows whose Rung cell disagrees with the rung the code actually takes.

    DELIBERATELY TWO-DIRECTIONAL, for the reason `_extraction_mismatch` and
    `_misdeclared_disagreement` both give, and it is worth restating because
    this rule spans two files rather than two columns:

    - a WORKING-RUNG row (`1`, `2`, `3`) must declare EXACTLY the numerals its
      routed adapters take. Not "include" — equality, so an adapter taking a
      rung the cell does not name goes red, and a cell naming a rung no adapter
      takes goes red too;
    - a NON-WORKING row (`4`, or the `—` of `UNPROBED_RUNG`) must have no
      adapter binding at all. Rung 4 is a claim that nothing reads this
      retailer, and it must go red the moment something does.

    A one-directional version would be satisfied by deleting adapters, or by
    writing `4` in every row.

    BOTH JOINS ARE LOAD-BEARING AND THIS RULE SPANS BOTH. A binding to
    `check_amazon`'s rung alone stays perfectly green the day `_make_checker`
    stops routing amazon to `check_amazon` — the adapter still says `Rung.TLS`,
    the README still says `1`, and Amazon is silently read by something else.
    So the code side is resolved as the union over the adapters the ROUTER
    reaches, never over an adapter named by hand.

    "NO ADAPTER AT ALL" AND "AN ADAPTER THAT STATES NO RUNG" ARE DIFFERENT
    FINDINGS and are reported differently. Only the first is a legitimate rung-4
    row. Collapsing the second into it would let an adapter this gate cannot
    read masquerade as a retailer nothing reads, which is precisely the shape a
    rung-4 row wants to see.

    Returns `{display name: (what the README declares, what the code takes)}`.
    """
    routing = _routing() if routing is None else routing
    rungs = _adapter_rungs() if rungs is None else rungs

    bad: dict[str, tuple[str, str]] = {}
    for key, name in ROADMAP_RETAILERS.items():
        if name not in rows:
            continue
        cell = rows[name][RUNG]
        adapters = routing.get(key, ())
        unreadable = sorted(a for a in adapters if not rungs.get(a))
        if unreadable:
            bad[name] = (cell, f"{', '.join(unreadable)} states no rung")
            continue
        code = sorted({numeral for a in adapters for numeral in rungs[a]})
        if cell[:1] in WORKING_RUNGS:
            if tuple(code) != _declared_rungs(cell):
                bad[name] = (cell, ", ".join(code) if code else "no adapter")
        elif adapters:
            bad[name] = (cell, ", ".join(code))
    return bad


# --------------------------------------------------------------------------
# The shipped README
# --------------------------------------------------------------------------


def test_every_roadmap_retailer_has_a_row_in_the_support_matrix() -> None:
    """A retailer in scope and absent from the table is a silent gap.

    "No silent gaps" is Phase 3's whole goal, and the table is where a reader
    looks first. A store that was never tried and a store that was tried and
    refused are different facts; a missing row states neither.
    """
    rows = _matrix()

    assert not _missing(rows), (
        f"no README support-matrix row for: {_missing(rows)}. Every retailer in "
        "ROADMAP_RETAILERS needs one, and the label must match character for "
        f"character. Rows found: {sorted(rows)}"
    )


def test_every_roadmap_retailer_carries_a_rung_of_one_to_four() -> None:
    """`—`, `Planned` and blank are all ways of not answering the question.

    An unsettled retailer is a finding about the phase, not a reason to soften
    this assertion.
    """
    rows = _matrix()
    unprobed = _unprobed_retailers()

    assert not _rungless(rows, unprobed), (
        f"no rung recorded in the README support matrix for: {_rungless(rows, unprobed)}. "
        f"A retailer nobody has probed yet may use {UNPROBED_RUNG!r} here, but only while "
        "docs/retailer-evidence.md carries its UNPROBED verdict — which expires."
    )


def test_the_matrix_header_is_exactly_the_seven_cells() -> None:
    """Asserted literally, so a column cannot move without a red test.

    Every rule in this file indexes cells by position. Insert a column, or swap
    `robots.txt` and `Terms`, and `_positionless` starts reading the Method cell
    against the robots vocabulary — which fails loudly — while
    `_misdeclared_disagreement` would quietly compare the wrong two cells and go
    on passing. `_matrix` already asserts it can FIND this header; this asserts
    the header is the one the constants describe.

    This is the test that caught the change it is now asserting. Inserting
    `Extraction` at index 2 went red here first, and the reindex below it was
    made deliberately rather than discovered later by a rule quietly comparing
    the wrong two cells. That is the whole reason the header is written out
    literally instead of derived from the file.
    """
    lines = README.read_text(encoding="utf-8").splitlines()
    headers = [tuple(_cells(line)) for line in lines if line.startswith("| Retailer |")]

    assert headers == [HEADER_CELLS], headers


def test_every_roadmap_retailer_states_a_robots_and_a_terms_position() -> None:
    """REQ-13: three things per row, not one.

    The rung says what bot-y managed to do. These two say what the retailer
    published about it — the deny-list rule on the exact path fetched, and the
    prose. A reader who only ever sees the resolved verdict has to take somebody
    else's reading of both on trust.
    """
    rows = _matrix()

    assert not _positionless(rows), (
        f"no robots.txt/Terms position in the README support matrix for: {_positionless(rows)}. "
        f"A robots cell opens with one of {ROBOTS_POSITIONS} and names the path in backticks; a "
        f"Terms cell opens with one of {TERMS_POSITIONS}. Every position is backed by a URL and "
        "a retrieval date in docs/retailer-evidence.md."
    )


def test_the_disagreement_marker_is_on_exactly_the_rows_that_earn_it() -> None:
    """Both directions, against the shipped table.

    Target is why REQ-13 exists — `robots.txt` permits `/p/` and publishes a
    product sitemap while the Terms forbid extraction — and Nintendo is why it
    is not a rule about retailers this repo declined: Nintendo ships, is watched
    every five minutes, and its two signals disagree just as sharply.
    """
    rows = _matrix()

    assert not _misdeclared_disagreement(rows), (
        f"the {DISAGREE!r} marker does not match the stated positions for: "
        f"{_misdeclared_disagreement(rows)}. The marker belongs on a row where exactly one of "
        "the two positions is prohibitive, and nowhere else — including not on a row where one "
        "document is `unread`, because that is not a comparison anybody has made."
    )


def test_only_the_pinned_cells_say_unread() -> None:
    """`unread` is a written refusal, not a spare cell value.

    Pinned literally for the reason `UNREAD_POSITIONS` gives: an unconditional
    fourth vocabulary word is the cheapest way out of REQ-13, and it would rot
    the way the Phase 2 count clause rotted — permanently satisfied, still
    looking like a rule. Reading one of these documents narrows this set and is
    a deliberate edit; adding a row to it is the edit worth reviewing.
    """
    rows = _matrix()

    assert _unread_cells(rows) == set(UNREAD_POSITIONS), {
        "unexpected": sorted(_unread_cells(rows) - set(UNREAD_POSITIONS)),
        "no longer unread": sorted(set(UNREAD_POSITIONS) - _unread_cells(rows)),
    }


def test_every_roadmap_retailer_states_an_extraction_matching_its_rung() -> None:
    """REQ-13's fourth field, against the shipped table.

    A rung says how the bytes were obtained; an Extraction says what was read
    out of them. Best Buy is rung 3 + `structured` and Target would be rung 3 +
    `dom` — same rung, materially different readings — which is the whole
    reason this column is not folded into the one beside it.
    """
    rows = _matrix()

    assert not _extraction_mismatch(rows), (
        f"the Extraction cell disagrees with the Rung cell for: {_extraction_mismatch(rows)}. "
        f"A working rung (1-3) states one of {EXTRACTIONS}; rung 4 states {NO_EXTRACTION!r}, "
        "because nothing is extracted from a retailer the monitor does not read."
    )


def test_a_lower_confidence_retailer_is_flagged_degraded_in_the_matrix() -> None:
    """The matrix half of phase criterion 3, on both of the flag's disjuncts.

    A browser-rendered reading is a page we rendered rather than an answer the
    retailer gave us, and the table is consulted before the number is trusted.
    Flagging it at runtime while the matrix presents it as first-class puts the
    caveat exactly where nobody reads it.

    `Result.degraded` widened to fire on a `dom` extraction as well, so this
    rule widened with it in the same commit. Two halves of one contract that
    are allowed to drift are the WR-04 failure this file exists to prevent.
    """
    rows = _matrix()

    assert not _undeclared_degraded(rows), (
        f"retailers not flagged degraded in the README support matrix: "
        f"{_undeclared_degraded(rows)}. Phase 3 criterion 3 requires DEGRADED in the "
        "matrix as well as in `boty check`, for a rung-3 row or a `dom` row alike."
    )


def test_every_configured_retailer_is_documented_in_the_matrix() -> None:
    """Shipping a detector without a matrix row is the reverse silent gap.

    `evidence_check.py --phase` catches a configured retailer that is out of
    scope. This catches one that is in scope, shipped, and undescribed — the
    table would understate what the monitor actually does, which is the one
    direction a reader has no way to notice.
    """
    rows = _matrix()
    configured = {w.retailer for w in Config.load(CONFIG).watches}
    undocumented = sorted(
        ROADMAP_RETAILERS.get(key, key)
        for key in configured
        if ROADMAP_RETAILERS.get(key, key) not in rows
    )

    assert not undocumented, (
        f"configured in {CONFIG} but absent from the README matrix: {undocumented}"
    )


def test_the_matrix_does_not_advertise_a_retailer_the_monitor_does_not_watch() -> None:
    """The other direction, and the one a reader has no defence against.

    A row claiming rung 1-3 is a claim that the monitor reads this retailer. If
    no watch exists, that claim is false, no alert will ever arrive, and nothing
    else in the tree noticed: `evidence_check`'s rules 1-3 impose a ceiling on
    the retailer count and no floor, and the rule above only catches the table
    understating. `README.md` says "`scripts/evidence_check.py` is what stops
    that number drifting" — this test and rule 4 are what make that true in the
    second direction.
    """
    rows = _matrix()
    configured = {w.retailer for w in Config.load(CONFIG).watches}

    assert not _overstated(rows, configured), (
        f"the README matrix shows a working rung (1-3) for retailers with no watch in "
        f"{CONFIG}: {_overstated(rows, configured)}. Rung 4 — dropped, with the evidence "
        "written down — is the only honest rung for a retailer the monitor does not read. "
        "If the watch was deliberately removed, move the row to rung 4 and record why in "
        "docs/retailer-evidence.md in the same commit."
    )


def test_every_rung_member_has_a_numeral_and_rung_four_has_none() -> None:
    """The pin, asserted against the enum in both directions.

    A new `Rung` member arriving with no numeral would be a transport the
    support matrix has no way to describe, and `_adapter_rungs` would raise on
    the first adapter that took it — loudly, but at the wrong layer and with a
    worse message. A numeral with no member would be the opposite: a column
    value nothing can ever produce.

    This is also where `RUNGS - WORKING_RUNGS == {"4"}` stops being an
    assumption. Rung 4 has no `Rung` member on purpose — `models.Rung` says a
    dropped retailer produces no readings — and the whole non-working half of
    `_rung_mismatch` rests on that.
    """
    assert set(RUNG_NUMERALS) == set(Rung), {
        "members with no numeral": sorted(m.name for m in set(Rung) - set(RUNG_NUMERALS)),
        "numerals with no member": sorted(m.name for m in set(RUNG_NUMERALS) - set(Rung)),
    }
    assert set(RUNG_NUMERALS.values()) == WORKING_RUNGS, sorted(RUNG_NUMERALS.values())
    assert RUNGS - WORKING_RUNGS == {"4"}, RUNGS - WORKING_RUNGS


def test_every_retailer_the_router_names_is_a_known_retailer() -> None:
    """`_make_checker`'s string comparisons, checked against the one spelling list.

    `models.KNOWN_RETAILERS`' own comment names `_make_checker`'s `== "bestbuy"
    / "amazon" / "target"` as its consumers, and nothing checked that. A typo in
    an arm does not fail: the watch falls through to `check_html`, which is a
    real transport, so the retailer is read by the wrong adapter at the wrong
    rung while every test stays green.

    `known=frozenset()` gives exactly the keys the router names in an `if`,
    because the fallthrough is then assigned to nobody.
    """
    named = set(_routing(known=frozenset()))

    assert named <= set(KNOWN_RETAILERS), sorted(named - set(KNOWN_RETAILERS))


def test_every_routed_adapter_states_a_rung_in_its_own_source() -> None:
    """Every adapter the router can reach names exactly one rung, in its own file.

    Two claims, and the second is the interesting one. An adapter that states NO
    rung is one this gate cannot read, and `_rung_mismatch` reports it as such
    rather than as an absent adapter — but the honest state is that there are
    none, and this is where that is asserted positively.

    An adapter that could produce TWO different rungs would make its README cell
    unwritable: the row would have to name both, and a reader could not tell
    which one produced the number in front of them. Best Buy's two rungs come
    from two adapters, which is the coherent way to say it.
    """
    rungs = _adapter_rungs()
    adapters = sorted({a for names in _routing().values() for a in names})

    assert all(len(rungs.get(a, ())) == 1 for a in adapters), {
        a: rungs.get(a, ()) for a in adapters if len(rungs.get(a, ())) != 1
    }


def test_every_matrix_rung_cell_matches_the_rung_its_adapter_takes() -> None:
    """REQ-18, against the shipped tree: the claim, and the code under it.

    Both joins at once. The Rung cell is compared against the rung taken by the
    adapters `cli._make_checker` actually routes that retailer to — not against
    an adapter named here by hand, which would leave the routing half unbound
    and the claim half-checked.
    """
    rows = _matrix()

    assert not _rung_mismatch(rows), (
        f"the README Rung cell disagrees with the rung the code takes for: {_rung_mismatch(rows)}. "
        "A working-rung row (1-3) declares exactly the numerals the adapters `cli._make_checker` "
        "routes it to take, including a conditional second rung in parentheses; a rung-4 row has "
        "no adapter at all. Both joins are read out of boty/cli.py and boty/retailers.py as text."
    )


# --------------------------------------------------------------------------
# The same rules, watched failing on a deliberately broken copy
# --------------------------------------------------------------------------


def _corrupt(retailer: str, column: int, value: str) -> str:
    """The real README with one cell of one retailer's row replaced."""
    return _corrupt_text(README.read_text(encoding="utf-8"), retailer, column, value)


def _corrupt_text(text: str, retailer: str, column: int, value: str) -> str:
    """The same edit against text already corrupted once.

    Two cells have to move together to build the clean `dom` case: a row that
    reads `dom` AND declares itself degraded. Composing corruptions is what
    keeps that case derived from the real README rather than typed out, which
    is the point of running these rules against the shipped table at all.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("|") and _cells(line)[RETAILER] == retailer:
            cells = _cells(line)
            cells[column] = value
            lines[i] = "| " + " | ".join(cells) + " |"
            return "\n".join(lines)
    raise AssertionError(f"no row for {retailer!r} to corrupt")


def test_a_blanked_rung_cell_fails_the_rung_rule() -> None:
    rows = _matrix(_corrupt("GameStop", RUNG, ""))

    assert _rungless(rows) == {"GameStop": ""}


def test_a_planned_rung_cell_fails_too() -> None:
    """The specific evasion this rule exists for: a row that looks filled in."""
    rows = _matrix(_corrupt("Target", RUNG, "Planned"))

    assert _rungless(rows) == {"Target": "Planned"}


def test_an_unprobed_rung_cell_needs_an_unprobed_verdict_behind_it() -> None:
    """The `—` cell is not a free pass; it is the second half of a written claim.

    A retailer in scope that nobody has probed has no rung to report, so the
    table has to be able to say so — otherwise the README rung rule joins rule 2
    in making the honest state unrepresentable, and the fastest green for a
    scope expansion is inventing a number as well as a refusal.

    But `—` accepted unconditionally is exactly the `Planned` evasion the rule
    above exists to catch. So it is accepted ONLY alongside the evidence log's
    UNPROBED verdict, which carries a date and expires. Both directions here.
    """
    rows = _matrix(_corrupt("Target", RUNG, UNPROBED_RUNG))

    assert _rungless(rows, unprobed=set()) == {"Target": UNPROBED_RUNG}
    assert _rungless(rows, unprobed={"Target"}) == {}


def test_a_planned_rung_cell_fails_even_for_an_unprobed_retailer() -> None:
    """The exemption is for one cell value, not for the retailer.

    Without this, "unprobed" would become a licence to write anything in the
    rung column — and `Planned` is the specific word the rung rule was written
    against.
    """
    rows = _matrix(_corrupt("Target", RUNG, "Planned"))

    assert _rungless(rows, unprobed={"Target"}) == {"Target": "Planned"}


def test_a_blanked_extraction_cell_fails_the_extraction_rule() -> None:
    """The blank cell, which is how a column quietly stops being filled in.

    Same failure `_positionless` was written for one column over: nobody
    notices an empty cell in a wide markdown table, and the row still parses.
    """
    rows = _matrix(_corrupt("GameStop", EXTRACTION, ""))

    assert _extraction_mismatch(rows) == {"GameStop": ("1", "")}


def test_a_rung_four_row_claiming_an_extraction_fails() -> None:
    """Direction one: a claim to have read something off a retailer nobody watches.

    Pokémon Center is rung 4 with no watch. `structured` in its Extraction cell
    says a schema.org feed is being read every five minutes, which is false in a
    way no other rule here can see — `_overstated` reads the Rung cell, and the
    Rung cell is honest.

    Pokémon Center rather than Target, which this used to name: Target moved to
    rung 3 + `dom` when it was registered. Pokémon Center is the most durable
    rung-4 row in the table — refused at every rung, in writing, with a technical
    wall behind it — so it is the one least likely to move this test again.
    """
    rows = _matrix(_corrupt("Pokémon Center", EXTRACTION, "structured"))

    assert rows["Pokémon Center"][RUNG].startswith("4"), "the corruption must leave the rung alone"
    assert _extraction_mismatch(rows) == {"Pokémon Center": ("4", "structured")}


def test_a_working_rung_row_disclaiming_an_extraction_fails() -> None:
    """Direction two, and the one that makes the rule worth having.

    Without it, `—` would be an unconditional escape from the column: paste it
    into all seven rows and every one is clean while the axis states nothing.
    That is exactly how `unread` would have rotted REQ-13 had it not been
    pinned, and how the Phase 2 count clause actually did rot.
    """
    rows = _matrix(_corrupt("Walmart", EXTRACTION, NO_EXTRACTION))

    assert _extraction_mismatch(rows) == {"Walmart": ("1", NO_EXTRACTION)}


def test_a_rung_one_dom_row_with_no_degraded_flag_fails_the_degraded_rule() -> None:
    """The matrix half of the hole the runtime half closed, watched biting.

    A rung-1 DOM adapter is cheap to write and the most fragile thing anyone
    could add to this codebase. Before `Result.degraded` widened, it would have
    shipped looking fully trustworthy — and before this rule widened with it,
    its README row would have too, sitting at rung 1 beside GameStop's
    schema.org feed with nothing to tell them apart.

    GameStop's Status cell contains no `degrad` today, so this corruption
    really does go red rather than being masked by prose that happens to
    mention the word.
    """
    rows = _matrix(_corrupt("GameStop", EXTRACTION, "dom"))

    assert rows["GameStop"][RUNG].startswith("1"), "the corruption must leave the rung alone"
    assert not _extraction_mismatch(rows), "a rung-1 `dom` row is a coherent claim, not a mismatch"
    assert _undeclared_degraded(rows) == ["GameStop"]


def test_the_same_dom_row_declaring_degraded_is_clean() -> None:
    """The rule is about the disagreement, not about the word `dom`.

    Without this pair, `_undeclared_degraded` would be indistinguishable from
    "no row may say `dom`" — which would make the honest state unrepresentable
    and pressure exactly the padding every other gate here was built to stop.
    A DOM reading that says it is degraded is a supported retailer, correctly
    described.
    """
    corrupted = _corrupt("GameStop", EXTRACTION, "dom")
    rows = _matrix(_corrupt_text(corrupted, "GameStop", STATUS, "✅ Working, `[degraded]`"))

    assert rows["GameStop"][EXTRACTION] == "dom"
    assert _undeclared_degraded(rows) == []


def test_a_rung_three_row_stripped_of_degraded_fails_the_degraded_rule() -> None:
    """The assertion carrying criterion 3, driven against a tree that breaks it.

    Best Buy is the only rung-3 retailer today, so without this the degraded
    rule would be one nobody has seen bite — and if Best Buy ever moves to rung
    2 with a key, it would quietly become a rule about an empty set.
    """
    rows = _matrix(_corrupt("Best Buy", STATUS, "✅ Working"))

    assert rows["Best Buy"][RUNG].startswith("3"), "the corruption must leave the rung alone"
    assert _undeclared_degraded(rows) == ["Best Buy"]


def test_a_watch_dropped_while_the_row_still_says_working_fails_the_overstatement_rule() -> None:
    """The reviewer's reproduction, as a rule run against the real table.

    The README is untouched — that is the point. Somebody deletes the gamestop
    watch during a config rewrite, or "cleans up" a retailer that has been
    failing, and the matrix goes on advertising `| GameStop | 1 | ... | ✅
    Working |`. Rung 1 with nothing watching it is a false claim, and this is
    what turns it red.
    """
    rows = _matrix()
    configured = {w.retailer for w in Config.load(CONFIG).watches} - {"gamestop"}

    assert _overstated(rows, configured) == ["GameStop"]


def test_a_rung_four_row_promoted_to_rung_one_fails_the_overstatement_rule() -> None:
    """The same rule from the other side: the table moving without the config.

    Pokémon Center is settled at rung 4 with no watch. Editing its rung cell to
    `1` — the one-character version of claiming a retailer works — is caught by
    the same predicate, so this is a rule about the disagreement rather than a
    rule about `config/products.yaml` alone.

    This used to name Target, and Target was registered at rung 3, so it had to
    be repointed. **Pokémon Center and not Amazon**, deliberately: 03.1-03 may
    move Amazon's row, and a test repointed twice is a test nobody trusts.
    Pokémon Center is the most durable rung-4 row here — it was walked down the
    whole ladder and refused at every one, so its rung is held up by a measured
    wall rather than only by a written policy that a maintainer could reverse.
    """
    rows = _matrix(_corrupt("Pokémon Center", RUNG, "1"))
    configured = {w.retailer for w in Config.load(CONFIG).watches}

    assert _overstated(rows, configured) == ["Pokémon Center"]


def test_the_shipped_rung_four_rows_are_not_flagged_as_overstatement() -> None:
    """The clean side. Rung 4 for an unwatched retailer is the honest answer.

    Without this, the rule could be satisfied by flagging every unconfigured
    retailer, which would make the honest shortfall this phase recorded — two
    retailers dropped with the evidence written down — unrepresentable.

    Target is no longer in this tuple. It was registered at rung 3 with `dom`
    extraction and a live control, so a rung-4 assertion on it would now be
    asserting the opposite of the truth. Dropping it narrows what this test
    watches by exactly one row and loosens no rule: Target is instead covered by
    `_undeclared_degraded` and `_extraction_mismatch`, which both bite harder on
    a rung-3 `dom` row than the overstatement rule ever did on a rung-4 one.

    **Amazon left the same way on 2026-08-03, one wave later**, and for a
    stronger reason: it was registered at rung **1** with `dom` extraction, a
    live control and a real product watch. One name is left in the tuple, which
    is the point at which a list like this stops being a list — Pokémon Center is
    now the only genuinely dropped retailer in scope, and if it ever lands, this
    test has nothing left to assert and should be deleted rather than kept green
    by inventing a row for it.

    The clean-side assertion (`_overstated(...) == []`) is unchanged and still
    covers all seven rows, so nothing stops watching when a name leaves the
    tuple — only the "and its rung really is 4" half narrows.
    """
    rows = _matrix()
    configured = {w.retailer for w in Config.load(CONFIG).watches}

    for name in ("Pokémon Center",):
        assert rows[name][RUNG].startswith("4"), (name, rows[name][RUNG])
    assert _overstated(rows, configured) == []


def test_a_blanked_robots_cell_fails_the_position_rule() -> None:
    """The blank cell, which is how a column quietly stops being filled in."""
    rows = _matrix(_corrupt("Target", ROBOTS, ""))

    assert list(_positionless(rows)) == ["Target"]


def test_a_tbd_terms_cell_fails_the_position_rule() -> None:
    """`TBD` is the `Planned` evasion one column over: it looks filled in.

    A reader skimming the table sees text in the cell and moves on. The rung
    rule already learned this, which is why the vocabulary here is a fixed list
    rather than "not empty".
    """
    rows = _matrix(_corrupt("Nintendo", TERMS, "TBD"))

    assert list(_positionless(rows)) == ["Nintendo"]


def test_a_robots_position_without_a_path_fails_the_position_rule() -> None:
    """`permits` on its own is not a position — robots.txt rules are per-path.

    Target is the case that proves it: `www.target.com` permits `/p/` while
    `redsky.target.com` is `Disallow: /` for every agent. A bare `permits`
    would be true of one host and false of the other, in a cell claiming to
    describe the path this repo actually fetches.
    """
    rows = _matrix(_corrupt("Target", ROBOTS, "permits"))

    assert list(_positionless(rows)) == ["Target"]


def test_stripping_the_marker_from_a_disagreeing_row_fails() -> None:
    """Direction one: the marker missing from a row that earns it.

    Target's Status cell carries the whole of REQ-13 for the retailer REQ-13 was
    written for. Remove it and the row still reads as a settled rung-4 refusal,
    with the fact that Target's own `robots.txt` points the other way visible
    nowhere in the table.
    """
    rows = _matrix(_corrupt("Target", STATUS, "❌ Dropped. Not configured"))

    assert _disagrees(rows["Target"]) is True
    assert _misdeclared_disagreement(rows) == ["Target"]


def test_an_unearned_marker_on_an_agreeing_row_fails() -> None:
    """Direction two, and the one that makes the rule worth having.

    A one-directional rule — "a disagreeing row must be marked" — is satisfied
    by marking all seven, which states nothing at all. So the marker must also
    come OFF when it is not earned.

    No shipped row has two agreeing positions today, so the agreeing case is
    built: Pokémon Center's `robots.txt` cell is corrupted from `permits` to
    `disallows`, which makes both of its positions prohibitive and the row an
    agreement — and its `⚠ disagree` marker instantly unearned. Without this,
    the rule would be one nobody has seen bite in this direction, which is
    exactly the shape of every gate this project has had to replace.
    """
    rows = _matrix(_corrupt("Pokémon Center", ROBOTS, "disallows `/product/`"))

    assert _disagrees(rows["Pokémon Center"]) is False
    assert DISAGREE in " ".join(rows["Pokémon Center"])
    assert _misdeclared_disagreement(rows) == ["Pokémon Center"]


def test_the_marker_is_unearned_on_a_row_whose_document_was_never_read() -> None:
    """The third answer: `unread` is not half of a disagreement.

    Walmart's `robots.txt` permits `/ip/` and its terms were refused by a
    challenge page. Marking that row `⚠ disagree` would claim a comparison
    nobody has made — the more tempting error, because a prohibition is usually
    what a terms document turns out to contain.
    """
    rows = _matrix(_corrupt("Walmart", STATUS, f"✅ Working. {DISAGREE}"))

    assert _disagrees(rows["Walmart"]) is None
    assert _misdeclared_disagreement(rows) == ["Walmart"]


def test_an_unread_cell_on_a_row_that_never_earned_one_fails_the_pin() -> None:
    """`unread` pasted into a new row is the escape REQ-13 would rot through.

    Nintendo's terms were read in full and quoted in the evidence log. Replacing
    that position with `unread` is vocabulary-clean, kills the row's
    disagreement, and would be invisible to every other rule here.
    """
    rows = _matrix(_corrupt("Nintendo", TERMS, "unread — refused"))

    assert not _positionless(rows), "the corrupted cell is still vocabulary-clean"
    assert _unread_cells(rows) - set(UNREAD_POSITIONS) == {("Nintendo", TERMS)}


def test_a_deleted_row_fails_the_presence_rule() -> None:
    """Deleting a retailer's row must not read as "nothing to report"."""
    without_target = "\n".join(
        line
        for line in README.read_text(encoding="utf-8").splitlines()
        if not line.startswith("| Target |")
    )
    rows = _matrix(without_target)

    assert _missing(rows) == ["Target"]
