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

Nothing here touches the network. It reads two files off disk.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from boty.config import Config

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
CONFIG = REPO_ROOT / "config" / "products.yaml"

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
        if position is None or (position != "unread" and "`" not in robots):
            bad[name] = (robots, terms)
        elif _position(terms, TERMS_POSITIONS) is None:
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
        if working and extraction not in EXTRACTIONS:
            bad[name] = (rung, extraction)
        elif not working and extraction != NO_EXTRACTION:
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

    Target is rung 4 with no watch. `structured` in its Extraction cell says a
    schema.org feed is being read every five minutes, which is false in a way
    no other rule here can see — `_overstated` reads the Rung cell, and the
    Rung cell is honest.
    """
    rows = _matrix(_corrupt("Target", EXTRACTION, "structured"))

    assert rows["Target"][RUNG].startswith("4"), "the corruption must leave the rung alone"
    assert _extraction_mismatch(rows) == {"Target": ("4", "structured")}


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

    Target is settled at rung 4 with no watch. Editing its rung cell to `1` —
    the one-character version of claiming a retailer works — is caught by the
    same predicate, so this is a rule about the disagreement rather than a rule
    about `config/products.yaml` alone.
    """
    rows = _matrix(_corrupt("Target", RUNG, "1"))
    configured = {w.retailer for w in Config.load(CONFIG).watches}

    assert _overstated(rows, configured) == ["Target"]


def test_the_shipped_rung_four_rows_are_not_flagged_as_overstatement() -> None:
    """The clean side. Rung 4 for an unwatched retailer is the honest answer.

    Without this, the rule could be satisfied by flagging every unconfigured
    retailer, which would make the honest shortfall this phase recorded — three
    retailers dropped with the evidence written down — unrepresentable.
    """
    rows = _matrix()
    configured = {w.retailer for w in Config.load(CONFIG).watches}

    for name in ("Pokémon Center", "Amazon", "Target"):
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
