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
HEADER_CELLS = ("Retailer", "Rung", "Method", "Status")

#: Column indices within a matrix row.
RETAILER, RUNG, METHOD, STATUS = 0, 1, 2, 3

#: A rung cell must begin with one of these. Rung 4 — "dropped, with the
#: evidence written down" — is a real answer, so there is no honest reason for
#: a retailer in scope to have `—`, `Planned` or nothing here.
RUNGS = {"1", "2", "3", "4"}


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


ROADMAP_RETAILERS: dict[str, str] = _load_evidence_check().ROADMAP_RETAILERS


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


def _rungless(rows: dict[str, list[str]]) -> dict[str, str]:
    return {
        name: rows[name][RUNG]
        for name in ROADMAP_RETAILERS.values()
        if name in rows and rows[name][RUNG][:1] not in RUNGS
    }


def _undeclared_degraded(rows: dict[str, list[str]]) -> list[str]:
    return [
        name
        for name in ROADMAP_RETAILERS.values()
        if name in rows
        and rows[name][RUNG].startswith("3")
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

    assert not _rungless(rows), (
        f"no rung recorded in the README support matrix for: {_rungless(rows)}"
    )


def test_a_rung_three_retailer_is_flagged_degraded_in_the_matrix() -> None:
    """The matrix half of phase criterion 3.

    A browser-rendered reading is a page we rendered rather than an answer the
    retailer gave us, and the table is consulted before the number is trusted.
    Flagging it at runtime while the matrix presents it as first-class puts the
    caveat exactly where nobody reads it.
    """
    rows = _matrix()

    assert not _undeclared_degraded(rows), (
        f"rung-3 retailers not flagged degraded in the README support matrix: "
        f"{_undeclared_degraded(rows)}. Phase 3 criterion 3 requires DEGRADED in the "
        "matrix as well as in `boty check`."
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


# --------------------------------------------------------------------------
# The same rules, watched failing on a deliberately broken copy
# --------------------------------------------------------------------------


def _corrupt(retailer: str, column: int, value: str) -> str:
    """The real README with one cell of one retailer's row replaced."""
    lines = README.read_text(encoding="utf-8").splitlines()
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


def test_a_rung_three_row_stripped_of_degraded_fails_the_degraded_rule() -> None:
    """The assertion carrying criterion 3, driven against a tree that breaks it.

    Best Buy is the only rung-3 retailer today, so without this the degraded
    rule would be one nobody has seen bite — and if Best Buy ever moves to rung
    2 with a key, it would quietly become a rule about an empty set.
    """
    rows = _matrix(_corrupt("Best Buy", STATUS, "✅ Working"))

    assert rows["Best Buy"][RUNG].startswith("3"), "the corruption must leave the rung alone"
    assert _undeclared_degraded(rows) == ["Best Buy"]


def test_a_deleted_row_fails_the_presence_rule() -> None:
    """Deleting a retailer's row must not read as "nothing to report"."""
    without_target = "\n".join(
        line
        for line in README.read_text(encoding="utf-8").splitlines()
        if not line.startswith("| Target |")
    )
    rows = _matrix(without_target)

    assert _missing(rows) == ["Target"]
