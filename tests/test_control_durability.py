"""The durability rule, bound to the controls it judges — in both directions.

WHY THIS FILE EXISTS
--------------------
`docs/adding-a-retailer.md` carried a rule for what makes a control durable —
*"first-party, evergreen, restocked routinely, never the subject of a buy-box
fight, and not a console"* — from early in this project's life. It had never been
applied to anything in writing and nothing gated it, and the tree quietly
violated it the whole time: the rule's own last clause forbids a console and
GameStop's control is a PS5 console. Nobody noticed for the life of the project,
because there was nothing that could notice.

That is the argument for this module. A rule that is written down and not gated
is a rule that is already being broken; the only question is when somebody
finds out.

THE TWO DIRECTIONS, AND WHY ONE WOULD ROT
-----------------------------------------
- **Config to document.** Every control the loader yields must appear in the
  applied table with a verdict against every clause the document declares, and
  must carry a verdict line beside its own entry in `config/products.yaml`. A
  control added next year with no verdict reddens.
- **Document to config.** Every clause the document declares must have a verdict
  in every row, every clause column must correspond to a declared clause, and
  every row must be a control the config actually configures. A clause dropped
  from the document, or a table row for a watch nobody watches, reddens.

Only the first direction protects the naming from being dropped by the next
person to add a control; only the second protects it from being dropped by the
next person to edit the rule. A gate with one of them is a gate that rots at the
other end.

THE CLAUSE LIST IS READ OUT OF THE DOCUMENT, NEVER CARRIED HERE
---------------------------------------------------------------
`declared_clauses` parses the identifiers from the document's own clause
bullets. A gate that carried its own copy of the rule would be a second place
for the rule to live, and two copies only have to disagree once — which is the
same failure `tests/test_alert_text.py` has now been repaired for twice in one
phase. It would also make the document's "you may re-cut the clauses" false: a
re-cut would redden a test that had no business having an opinion.

THE CONTROL SET COMES FROM THE LOADER, NEVER FROM A GREP
--------------------------------------------------------
`grep -c 'control: true' config/products.yaml` returns **7** and there are
**6**. The seventh match is the comment above the transition watches saying they
are *deliberately not* controls. A grep-based gate would demand a durability
verdict for a watch that has none to give, and would be measuring the file
rather than the configuration. `Config.load(...).watches` filtered on `control`
is what `scripts/control_check.py` and `boty.monitor.assess_health` both filter
on, so this gate and the code it guards are looking at the same set.

THE RULES ARE FUNCTIONS OVER TEXT
---------------------------------
Each rule is a pure function returning a list of problems rather than asserting
anything, on `tests/test_support_matrix.py`'s precedent, so the corruption tests
at the bottom run the *same* rules against deliberately broken copies of the
real inputs. A gate asserted only against the tree it guards has never been
watched failing, and this project has shipped one of those before.

Nothing here touches the network. It reads two files off disk.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from boty.config import Config
from boty.models import Watch

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC = REPO_ROOT / "docs" / "adding-a-retailer.md"
CONFIG = REPO_ROOT / "config" / "products.yaml"

#: The verdict vocabulary, longest first so `NOT SATISFIED` is never read as
#: `SATISFIED` with a stray word in front of it. That ordering is the whole
#: correctness of the parse: the two verdicts are opposites and one contains the
#: other as a substring.
VERDICTS = ("NOT SATISFIED", "SATISFIED", "PARTIAL")

#: A clause declaration bullet in the document, e.g.
#: ``- **`D3` — not generation-bound.**``. The identifier is what the table and
#: the config verdict lines cite, so it is the only part this gate pins.
_CLAUSE_BULLET = re.compile(r"^- \*\*`(D\d+)` — ", re.MULTILINE)

#: A clause identifier standing alone in a table header cell.
_CLAUSE_CELL = re.compile(r"^D\d+$")

#: A durability verdict line in `config/products.yaml`, keyed by the watch's
#: own `name` so the binding is an exact match rather than a positional guess.
#: A comment cannot be attached to a YAML node by the loader, so the name is the
#: only honest join key available here.
_CONFIG_VERDICT_LINE = re.compile(r"^\s*#\s*DURABILITY — (.+?): (.+)$", re.MULTILINE)

#: One `D<n> <verdict>` pair inside a verdict line.
_VERDICT_PAIR = re.compile(r"\b(D\d+) (NOT SATISFIED|SATISFIED|PARTIAL)\b")


# --------------------------------------------------------------------------
# Reading the inputs
# --------------------------------------------------------------------------


def loaded_controls(config_path: Path | None = None) -> list[Watch]:
    """The control watches, through the loader, exactly as the code sees them."""
    path = CONFIG if config_path is None else config_path
    return [w for w in Config.load(str(path)).watches if w.control]


def declared_clauses(doc_text: str) -> tuple[str, ...]:
    """The clause identifiers the document declares, in document order.

    Raises rather than returning empty. A gate that cannot find the rule must
    say so: reporting "no problems" because the section was renamed is the
    failure mode this whole module exists to prevent, one level up.
    """
    clauses = tuple(_CLAUSE_BULLET.findall(doc_text))
    if not clauses:
        raise AssertionError(
            f"no clause declarations in {DOC}: expected bullets of the form "
            "``- **`D1` — first-party by construction.**``. The durability rule is a "
            "phase deliverable; if its shape moved, this parser moves with it — in the "
            "same commit, deliberately."
        )
    return clauses


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def applied_table(doc_text: str) -> tuple[tuple[str, ...], dict[str, list[str]]]:
    """The applied table: its clause columns, and each row keyed by control name.

    Located by its header rather than by a line number or a heading, so a
    reworded section keeps working and a deleted table does not pass silently.
    """
    lines = doc_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if cells[:2] == ["Control", "Retailer"] and all(
            _CLAUSE_CELL.fullmatch(c) for c in cells[2:]
        ):
            start = i
            break

    if start is None:
        raise AssertionError(
            f"no applied durability table in {DOC}: expected a header row of "
            "| Control | Retailer | D1 | ... |. Criterion 4 is *applied to every "
            "existing control*, and a table is the only form in which 'every' is "
            "checkable by eye and by machine."
        )

    columns = tuple(_cells(lines[start])[2:])
    rows: dict[str, list[str]] = {}
    for line in lines[start + 2 :]:  # +2 skips the header and its |---| separator
        if not line.startswith("|"):
            break
        cells = _cells(line)
        rows[cells[0]] = cells
    return columns, rows


def config_verdicts(config_text: str) -> dict[str, dict[str, str]]:
    """Each control name's clause verdicts, as written beside its config entry."""
    return {
        name.strip(): dict(_VERDICT_PAIR.findall(body))
        for name, body in _CONFIG_VERDICT_LINE.findall(config_text)
    }


# --------------------------------------------------------------------------
# The rules, as functions, so the corruption tests can run the same ones
# --------------------------------------------------------------------------


def controls_missing_from_the_table(
    controls: list[Watch], rows: dict[str, list[str]]
) -> list[str]:
    """Rule 1 — every loaded control has a row in the applied table."""
    return [w.name for w in controls if w.name not in rows]


def controls_missing_a_config_verdict(
    controls: list[Watch], verdicts: dict[str, dict[str, str]]
) -> list[str]:
    """Rule 2 — every loaded control carries a verdict line in the config."""
    return [w.name for w in controls if w.name not in verdicts]


def table_rows_that_are_not_controls(
    controls: list[Watch], rows: dict[str, list[str]]
) -> list[str]:
    """Rule 3 — every table row is a control the config actually configures."""
    names = {w.name for w in controls}
    return sorted(name for name in rows if name not in names)


def orphan_columns(columns: tuple[str, ...], clauses: tuple[str, ...]) -> list[str]:
    """Rule 4 — the table's clause columns are exactly the declared clauses.

    Runs in both directions on purpose. A clause dropped from the document
    leaves a column nothing declares; a clause added to the document with no
    column leaves six controls unjudged against it. Neither may pass.
    """
    return sorted(set(columns) ^ set(clauses))


def missing_verdicts(
    columns: tuple[str, ...], rows: dict[str, list[str]]
) -> list[str]:
    """Rule 5 — every row states a known verdict in every clause column."""
    problems = []
    for name, cells in rows.items():
        for offset, clause in enumerate(columns):
            cell = cells[offset + 2] if offset + 2 < len(cells) else ""
            if cell not in VERDICTS:
                problems.append(f"{name} / {clause}: {cell!r}")
    return sorted(problems)


def record_disagreements(
    columns: tuple[str, ...],
    rows: dict[str, list[str]],
    verdicts: dict[str, dict[str, str]],
) -> list[str]:
    """Rule 6 — the two records agree, cell for cell.

    The verdict is written twice deliberately — in the document a contributor
    reads and beside the entry an operator edits — and two copies of a fact are
    two chances for one of them to go stale. This is the rule that makes writing
    it twice safe rather than merely convenient.
    """
    problems = []
    for name, cells in rows.items():
        beside = verdicts.get(name)
        if beside is None:
            continue  # rule 2's business, and it names it better
        for offset, clause in enumerate(columns):
            in_table = cells[offset + 2] if offset + 2 < len(cells) else ""
            in_config = beside.get(clause, "")
            if in_table != in_config:
                problems.append(
                    f"{name} / {clause}: table says {in_table!r}, "
                    f"config/products.yaml says {in_config!r}"
                )
    return sorted(problems)


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


def _config_text() -> str:
    return CONFIG.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# The rules against the real tree
# --------------------------------------------------------------------------


def test_the_control_set_comes_from_the_loader_and_not_from_a_grep() -> None:
    """The count this gate works from is the configuration's, not the file's.

    Asserted rather than commented because the two numbers differ TODAY: the
    file says seven and the configuration says six. If they ever agree, this
    test still passes and nothing is lost; if somebody replaces the loader call
    with a grep, the seventh match is a comment and this is where it surfaces.
    """
    controls = loaded_controls()
    grepped = _config_text().count("control: true")

    assert len(controls) == 6
    assert grepped == 7, (
        "the grep count moved. That is fine — but it is the reason this gate does "
        "not use one, and the divergence is worth re-reading before it is edited."
    )
    assert all(w.control for w in controls)


def test_every_configured_control_has_a_row_in_the_applied_table() -> None:
    problems = controls_missing_from_the_table(loaded_controls(), applied_table(_doc())[1])

    assert not problems, (
        f"controls with no durability verdict in {DOC}: {problems}. Criterion 4 asks "
        "for the rule applied to EVERY existing control, with any control failing it "
        "named. A control with no row has not been judged, and the way that reads from "
        "outside is that it passed."
    )


def test_every_configured_control_has_a_verdict_beside_its_config_entry() -> None:
    problems = controls_missing_a_config_verdict(loaded_controls(), config_verdicts(_config_text()))

    assert not problems, (
        f"controls with no DURABILITY line in {CONFIG}: {problems}. The verdict lives "
        "here as well as in the document because this file is where a replacement is "
        "actually chosen, and a person editing it should not have to open a document to "
        "learn that the thing they are replacing failed three clauses."
    )


def test_the_table_lists_no_control_the_config_does_not_configure() -> None:
    problems = table_rows_that_are_not_controls(loaded_controls(), applied_table(_doc())[1])

    assert not problems, (
        f"rows in the applied table for watches that are not configured controls: "
        f"{problems}. A verdict about a control nobody watches is a record of work "
        "that protects nothing."
    )


def test_the_table_columns_are_exactly_the_clauses_the_document_declares() -> None:
    columns, _ = applied_table(_doc())
    problems = orphan_columns(columns, declared_clauses(_doc()))

    assert not problems, (
        f"clause columns and declared clauses disagree: {problems}. A clause dropped "
        "from the rule leaves a column nothing declares; a clause added leaves six "
        "controls unjudged against it. The clause list is read out of the document "
        "precisely so that re-cutting the rule stays legal — but it has to be re-cut "
        "in both places."
    )


def test_every_control_states_a_verdict_against_every_clause() -> None:
    columns, rows = applied_table(_doc())
    problems = missing_verdicts(columns, rows)

    assert not problems, (
        f"cells that state no verdict from {VERDICTS}: {problems}. A blank cell is the "
        "quietest way to drop a failure, which is why it is spelled out rather than "
        "left to the eye."
    )


def test_the_document_and_the_config_agree_cell_for_cell() -> None:
    columns, rows = applied_table(_doc())
    problems = record_disagreements(columns, rows, config_verdicts(_config_text()))

    assert not problems, (
        f"the two records disagree: {problems}. Fix the record that is wrong; do not "
        "loosen the comparison. Which one is wrong is a question about the control, and "
        "it has an answer."
    )


def test_the_rule_condemns_something_which_is_the_point_of_applying_it() -> None:
    """A table whose every cell passes is a rule that was fitted to its subjects.

    THIS IS NOT A REQUIREMENT THAT CONTROLS BE BAD. It is the non-vacuousness
    assertion the other tests need: every rule above is satisfied by a table of
    thirty SATISFIED cells, and such a table would be exactly what a rule
    written to describe six controls chosen before it existed produces. Twelve
    of the thirty cells were not SATISFIED on 2026-09-02 when this was written;
    THIRTEEN were by the end of the same day, because `10-04` spent its live
    reads and moved `bestbuy`/`D5` from PARTIAL to NOT SATISFIED on what came
    back. Both figures are kept: the first was true when taken, and what changed
    it was a measurement rather than a re-reading.

    If a future phase genuinely repairs every control, this test is the one that
    goes red, and the honest repair is to DELETE it with the measurement that
    justified deleting it — not to reintroduce a failure to keep it green.
    """
    columns, rows = applied_table(_doc())
    failing = [
        f"{name} / {clause}"
        for name, cells in rows.items()
        for offset, clause in enumerate(columns)
        if cells[offset + 2] != "SATISFIED"
    ]

    assert failing, (
        "every cell in the applied table says SATISFIED. Applied to six controls that "
        "were all chosen before the rule existed, that is evidence the rule was fitted "
        "to them rather than applied to them. See this test's docstring before editing it."
    )


# --------------------------------------------------------------------------
# The same rules, watched failing on deliberately broken copies
# --------------------------------------------------------------------------
#
# Not against the real tree — against copies of it, so the rules are watched
# failing on the documents this project actually ships rather than on fiction
# typed out here. `tests/test_support_matrix.py` established the shape and the
# reason: a rule nobody has seen fail is a rule nobody has tested.


def _drop_line(text: str, needle: str) -> str:
    """The real text with the single line containing `needle` removed."""
    lines = text.splitlines()
    hits = [i for i, line in enumerate(lines) if needle in line]
    assert len(hits) == 1, (
        f"{needle!r} occurs on {len(hits)} lines, not one. A corruption that cannot say "
        "WHICH line it removed proves nothing about the one it names."
    )
    del lines[hits[0]]
    return "\n".join(lines)


def _replace_once(text: str, search: str, replace: str) -> str:
    assert text.count(search) == 1, (
        f"{search!r} occurs {text.count(search)} times, not once."
    )
    return text.replace(search, replace, 1)


def test_a_control_whose_config_verdict_is_removed_fails() -> None:
    """Broken copy 1 — the naming dropped where the decision is made."""
    broken = _drop_line(_config_text(), "# DURABILITY — CONTROL — Nintendo HDMI cable:")

    problems = controls_missing_a_config_verdict(loaded_controls(), config_verdicts(broken))

    assert problems == ["CONTROL — Nintendo HDMI cable"]


def test_a_clause_removed_from_the_document_fails() -> None:
    """Broken copy 2 — the rule quietly loses the clause most controls fail.

    `D5` is the one removed because it is the clause with two failing cells, so
    dropping it is the edit with the most to gain from going unnoticed.
    """
    broken = _drop_line(_doc(), "- **`D5` — its death is legible.**")

    clauses = declared_clauses(broken)
    columns, _ = applied_table(broken)

    assert "D5" not in clauses
    assert orphan_columns(columns, clauses) == ["D5"]


def test_a_table_row_for_a_control_nobody_watches_fails() -> None:
    """Broken copy 3 — a verdict about a watch that is not in the config."""
    broken = _replace_once(
        _doc(),
        "| CONTROL — PS5 console | gamestop |",
        "| CONTROL — a control that does not exist | gamestop | SATISFIED | SATISFIED "
        "| SATISFIED | SATISFIED | SATISFIED |\n| CONTROL — PS5 console | gamestop |",
    )

    problems = table_rows_that_are_not_controls(loaded_controls(), applied_table(broken)[1])

    assert problems == ["CONTROL — a control that does not exist"]


def test_a_control_with_no_row_in_the_table_fails() -> None:
    """Broken copy 4 — the other direction of the same drop.

    Broken copy 3 catches a row with no control. This catches a control with no
    row, which is the direction a person adding a control walks into.
    """
    broken = _drop_line(_doc(), "| CONTROL — up&up microfiber dust cloths | target |")

    problems = controls_missing_from_the_table(loaded_controls(), applied_table(broken)[1])

    assert problems == ["CONTROL — up&up microfiber dust cloths"]


def test_a_blanked_verdict_cell_fails() -> None:
    """Broken copy 5 — the quietest way to drop a failure."""
    broken = _replace_once(
        _doc(),
        "| CONTROL — up&up microfiber dust cloths | target | SATISFIED | SATISFIED "
        "| SATISFIED | NOT SATISFIED | NOT SATISFIED |",
        "| CONTROL — up&up microfiber dust cloths | target | SATISFIED | SATISFIED "
        "| SATISFIED | NOT SATISFIED |  |",
    )

    columns, rows = applied_table(broken)

    assert missing_verdicts(columns, rows) == [
        "CONTROL — up&up microfiber dust cloths / D5: ''"
    ]


def test_a_verdict_softened_in_one_record_only_fails() -> None:
    """Broken copy 6 — Target's `D5`, made to pass in the document alone.

    This is the specific edit the phase was warned against: rung 3 surfaces no
    HTTP status, so a dead Target control cannot be made legible by writing that
    it is.
    """
    broken = _replace_once(
        _doc(),
        "| CONTROL — up&up microfiber dust cloths | target | SATISFIED | SATISFIED "
        "| SATISFIED | NOT SATISFIED | NOT SATISFIED |",
        "| CONTROL — up&up microfiber dust cloths | target | SATISFIED | SATISFIED "
        "| SATISFIED | NOT SATISFIED | SATISFIED |",
    )

    columns, rows = applied_table(broken)

    assert record_disagreements(columns, rows, config_verdicts(_config_text())) == [
        "CONTROL — up&up microfiber dust cloths / D5: table says 'SATISFIED', "
        "config/products.yaml says 'NOT SATISFIED'"
    ]


def test_a_document_with_no_clause_declarations_raises_rather_than_passing() -> None:
    """An unparseable rule must raise, not report everything clean.

    The failure this module exists to prevent, one level up: a gate that goes
    quiet when its subject disappears is worse than no gate, because the silence
    reads as a pass.
    """
    with pytest.raises(AssertionError, match="no clause declarations"):
        declared_clauses("# a document about something else\n")


def test_a_document_with_no_applied_table_raises_rather_than_passing() -> None:
    with pytest.raises(AssertionError, match="no applied durability table"):
        applied_table("# a document about something else\n")
