"""`scripts/evidence_check.py` — proof that the honesty gate actually bites.

A gate nobody has watched fail is not a gate. This file is the watching.

WHY THIS EXISTS AT ALL, AND WHY IT IS NOT THE PHASE 2 VERSION
-------------------------------------------------------------
02-04 gated the retailer count with a clause of the form "five or more
retailers, OR `rung 4` appears in QUESTIONS.md and `**Verdict: REFUSED**`
appears in docs/retailer-evidence.md". It was correct the day it shipped and
rotted the same day: Pokémon Center put both of those substrings permanently
into the tree, so the escape hatch is now satisfied by documents that predate
Phase 3 entirely. Reused verbatim it is a gate that can never fail — worse than
no gate, because it looks like one.

Two properties of that failure are worth naming, because the replacement has to
avoid both:

- **A bare substring test is unusable on this document.** `docs/retailer-evidence.md`
  opens with a vocabulary preamble that spells out both verdict strings so a
  reader knows the grammar. Any check that greps the whole file therefore passes
  against a document that records nothing at all. `test_the_preamble_alone_satisfies_nothing`
  pins that.
- **The count has a second padding door.** Reaching five by adding a retailer
  that is not in the roadmap's scope moves the counter without moving the goal.
  A control-only Micro Center was probed in Phase 2, found viable at rung 1, and
  explicitly declined because it does not carry the GO Plus + and could never
  alert on it. Nothing mechanical made that decision stick. Rule 1 does.

Nothing here touches the network, and nothing here reads the shipped tree: every
case builds its own evidence document and its own YAML config under `tmp_path`.
The configs are real YAML loaded through `boty.config.Config.load`, the same
read path the script uses, rather than hand-built `Watch` lists — a gate that
agreed with a test fixture while disagreeing with the monitor would be proving
something about a code path nobody runs.
"""

from __future__ import annotations

import importlib.util
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = REPO_ROOT / "scripts" / "evidence_check.py"


def _load() -> Any:
    """Import evidence_check by path — `scripts/` is not a package."""
    spec = importlib.util.spec_from_file_location("evidence_check_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


evidence_check = _load()


# --------------------------------------------------------------------------
# Synthetic trees
# --------------------------------------------------------------------------

#: Deliberately carries BOTH bare verdict strings above the first `## `, exactly
#: as the real document's vocabulary preamble does. Every test below runs
#: against this, so any implementation that greps the file rather than the
#: sections goes green on an empty document and gets caught here instead of in
#: production.
_PREAMBLE = """\
# Retailer evidence log

A verdict line is one of exactly two strings, because later work branches on it
mechanically:

**Verdict: REACHABLE (rung 3)**
**Verdict: REFUSED**

"""

#: A refused section that is WELL-FORMED under every rule, including rule 6.
#:
#: Rule 6 arrived in 03.1-03 and this constant is what it cost: a bare
#: `**Verdict: REFUSED**` with a sentence of prose is exactly what rule 6 exists
#: to reject, so every synthetic tree in this file that uses it would otherwise
#: carry a rule-6 problem and 25 tests asserting a specific problem *count*
#: would be counting somebody else's failure.
#:
#: It clears the HIGHER bar — two observations including one at rung 3 — rather
#: than the base one, deliberately. Half the call sites below name `target` or
#: `amazon`, which are the `HARD_TWO`, and a constant that satisfied only the
#: base bar would make every test's cleanliness depend on which retailer name it
#: happened to pass. The rule-6 tests further down drive both bars explicitly
#: with their own bodies, so nothing is left unwatched by this choice.
_REFUSED = (
    "Probed 2026-08-03. Refused at every rung.\n\n"
    "**Refusal observed (rung 1):** HTTP 403, 858 B, a challenge page.\n\n"
    "**Refusal observed (rung 3):** rendered and refused again, 1,085 B.\n\n"
    "**Verdict: REFUSED**\n"
)
_REACHABLE = "Probed 2026-08-03. Reads clean.\n\n**Verdict: REACHABLE (rung 1)**\n"


def _write_evidence(tmp_path: Path, sections: list[tuple[str, str]]) -> Path:
    """Build an evidence document from (heading, body) pairs."""
    body = "".join(f"## {heading}\n\n{text}\n---\n\n" for heading, text in sections)
    tmp_path.mkdir(parents=True, exist_ok=True)  # several cases want a second tree
    path = tmp_path / "retailer-evidence.md"
    path.write_text(_PREAMBLE + body, encoding="utf-8")
    return path


_CONFIG = """\
settings:
  first_party_only: true
watches:
{watches}
"""

_WATCH = """\
  - name: {name}
    retailer: {retailer}
    target: https://{retailer}.example/{name}
    control: {control}
"""


def _write_config(tmp_path: Path, retailers: list[str]) -> Path:
    """One control watch per named retailer. Real YAML, read via Config.load."""
    body = "".join(
        _WATCH.format(name="control", retailer=r, control="true") for r in retailers
    )
    path = tmp_path / "products.yaml"
    path.write_text(_CONFIG.format(watches=body), encoding="utf-8")
    return path


def _write_fixtures(tmp_path: Path, retailers: list[str]) -> Path:
    """A synthetic captured-page tree: one `*.html` per named retailer.

    Rule 4 reads this, and every case here passes its OWN root rather than
    letting the real `tests/fixtures/` be inherited by default. This file states
    as an invariant that nothing in it reads the shipped tree, and a defaulted
    fixture root would break that silently: `check_phase` would be enforcing
    rule 4 against this repo's four real capture directories while the test
    believed it was describing its `tmp_path`. That is why the parameter is
    required rather than defaulted.
    """
    root = tmp_path / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    for retailer in retailers:
        (root / retailer).mkdir(parents=True, exist_ok=True)
        (root / retailer / "control.html").write_text("<html></html>", encoding="utf-8")
    return root


#: The four retailers that actually ship today.
_SHIPPED = ["gamestop", "walmart", "bestbuy", "nintendo"]


# --------------------------------------------------------------------------
# The constant itself — two literal match obligations, so a rename must be loud
# --------------------------------------------------------------------------


def test_roadmap_retailers_is_exactly_the_seven_in_scope() -> None:
    """Asserted literally, keys AND values, on purpose.

    Both halves of this mapping are matched as literal strings somewhere else in
    the tree, and the two matches are DIFFERENT:

    - the value is a **prefix** of the retailer's `## ` heading in
      `docs/retailer-evidence.md`;
    - the value is the **exact** first cell of that retailer's row in the README
      retailer table, which 03-03 keys on.

    They agree today only by luck of capitalisation. Without this test, renaming
    a value to fix one of them would silently unhook the other — the README row
    would stop being found while every check still went green, which is the same
    class of rot that made the Phase 2 count clause vacuous. Changing this
    mapping should mean deliberately editing a red test.
    """
    assert evidence_check.ROADMAP_RETAILERS == {
        "gamestop": "GameStop",
        "walmart": "Walmart",
        "bestbuy": "Best Buy",
        "pokemoncenter": "Pokémon Center",
        "nintendo": "Nintendo",
        "target": "Target",
        "amazon": "Amazon",
    }


def test_the_hard_two_are_target_and_amazon() -> None:
    assert set(evidence_check.HARD_TWO) == {"target", "amazon"}


# --------------------------------------------------------------------------
# --retailer: one section, exactly one well-formed verdict line
# --------------------------------------------------------------------------


def test_a_well_formed_section_passes(tmp_path: Path) -> None:
    evidence = _write_evidence(tmp_path, [("Amazon (amazon.com)", _REFUSED)])

    assert evidence_check.main(["--retailer", "Amazon", "--evidence", str(evidence)]) == 0


def test_a_reachable_verdict_passes_too(tmp_path: Path) -> None:
    """REFUSED is not the only well-formed answer; rungs 1-3 are equally valid."""
    evidence = _write_evidence(tmp_path, [("Nintendo (store.nintendo.com)", _REACHABLE)])

    assert evidence_check.main(["--retailer", "Nintendo", "--evidence", str(evidence)]) == 0


def test_a_missing_section_fails(tmp_path: Path) -> None:
    evidence = _write_evidence(tmp_path, [("Nintendo (store.nintendo.com)", _REACHABLE)])

    assert evidence_check.main(["--retailer", "Amazon", "--evidence", str(evidence)]) == 1


def test_the_preamble_alone_satisfies_nothing(tmp_path: Path) -> None:
    """The whole reason the Phase 2 clause rotted, pinned as a test.

    This document contains both verdict strings and records nothing. A substring
    check passes it. The section splitter excludes everything above the first
    `## ` by construction, so this must fail for every retailer.
    """
    evidence = _write_evidence(tmp_path, [])

    for display in evidence_check.ROADMAP_RETAILERS.values():
        assert (
            evidence_check.main(["--retailer", display, "--evidence", str(evidence)]) == 1
        ), display


#: A markdown example of the format, exactly as a "how to record a verdict"
#: section would carry it. Every character of it is real grammar; none of it is
#: a finding. Written as a raw triple-quoted string with the fence inside so the
#: test document really does contain a fence.
_FENCED_EXAMPLE = """\
Nothing was actually probed. This section documents the format.

```markdown
## Amazon (amazon.com)

**Verdict: REFUSED**
```
"""


def test_a_fenced_example_of_the_format_is_not_a_record(tmp_path: Path) -> None:
    """`test_the_preamble_alone_satisfies_nothing`, one route along.

    The preamble exclusion is by construction and holds. It does not cover the
    other place this document talks about its own grammar: a fenced template.
    Neither the heading regex nor the verdict regex can see a fence, so before
    `strip_fences` this document — whose only content is an example and the
    sentence "Nothing was actually probed." — certified Amazon as properly
    recorded. Same failure as the Phase 2 substring clause, different door.
    """
    path = tmp_path / "retailer-evidence.md"
    path.write_text(_PREAMBLE + _FENCED_EXAMPLE, encoding="utf-8")

    for display in evidence_check.ROADMAP_RETAILERS.values():
        assert (
            evidence_check.main(["--retailer", display, "--evidence", str(path)]) == 1
        ), display


def test_a_fenced_example_below_a_real_record_does_not_replace_it(tmp_path: Path) -> None:
    """The compounding case, and the reason this is not merely cosmetic.

    An example naturally uses a real retailer's name, which produces a heading
    IDENTICAL to that retailer's real section. So the two failures multiply: the
    dict splitter would have let the example overwrite the record, and with the
    splitter fixed the example instead reads as a second record and trips the
    duplicate rule. Either way a documentation edit silently breaks the log.
    Neither happens now — the record stands and the example is not a section.
    """
    path = tmp_path / "retailer-evidence.md"
    path.write_text(
        _PREAMBLE
        + f"## Amazon (amazon.com)\n\n{_REFUSED}\n---\n\n"
        + "## How to record a verdict\n\n"
        + _FENCED_EXAMPLE,
        encoding="utf-8",
    )

    assert evidence_check.check_retailer("Amazon", path) == []
    assert [heading for heading, _ in evidence_check.split_sections(
        path.read_text(encoding="utf-8")
    )] == ["Amazon (amazon.com)", "How to record a verdict"]


def test_stripping_fences_leaves_the_real_documents_records_alone() -> None:
    """The shipped log is 1400+ lines with 20-odd fenced blocks. Read it.

    A fence regex that mispairs — closing a ``` block on a ~~~, or running greedy
    across two blocks — would swallow whole sections of the real document and
    every gate downstream would go quiet about them. This asserts the count of
    real records and verdicts survives the strip, against the actual file.
    """
    text = (REPO_ROOT / "docs" / "retailer-evidence.md").read_text(encoding="utf-8")

    headings = [heading for heading, _ in evidence_check.split_sections(text)]
    verdicts = [
        line
        for _, body in evidence_check.split_sections(text)
        for line in evidence_check.verdict_lines(body)
    ]

    assert len(headings) == len(set(headings)), f"duplicate headings: {headings}"
    for display in ("Amazon", "Best Buy", "Nintendo", "Pokémon Center", "Target"):
        assert len(evidence_check.sections_for(display, evidence_check.split_sections(text))) == 1
    assert len(verdicts) == 5, verdicts


def test_a_section_with_no_verdict_line_fails(tmp_path: Path) -> None:
    evidence = _write_evidence(
        tmp_path, [("Amazon (amazon.com)", "We had a look. It seemed hard.\n")]
    )

    problems = evidence_check.check_retailer("Amazon", evidence)
    assert len(problems) == 1
    assert "no verdict line" in problems[0].lower()


def test_two_verdict_lines_fail_and_are_reported_differently(tmp_path: Path) -> None:
    """"None" and "two" are distinct failures and must not share a message.

    A section that changed its mind is a different problem from a section that
    never reached one, and sending someone to look for a missing verdict when
    there are two of them wastes the only thing this document is for.
    """
    evidence = _write_evidence(
        tmp_path,
        [("Amazon (amazon.com)", "**Verdict: REACHABLE (rung 1)**\n\n**Verdict: REFUSED**\n")],
    )

    problems = evidence_check.check_retailer("Amazon", evidence)
    assert len(problems) == 1
    assert "2 verdict lines" in problems[0]

    none_problems = evidence_check.check_retailer(
        "Amazon", _write_evidence(tmp_path / "b", [("Amazon (x)", "nothing\n")])
    )
    assert none_problems[0] != problems[0]


def test_two_sections_for_one_retailer_fail(tmp_path: Path) -> None:
    """Ambiguity is its own failure — which of the two is the verdict?"""
    evidence = _write_evidence(
        tmp_path,
        [("Amazon (amazon.com)", _REFUSED), ("Amazon, revisited", _REACHABLE)],
    )

    problems = evidence_check.check_retailer("Amazon", evidence)
    assert len(problems) == 1
    assert "2 sections" in problems[0]


def test_two_sections_under_the_same_heading_fail(tmp_path: Path) -> None:
    """The duplicate the two tests above could not reach, and the likelier one.

    Both existing duplicate cases use deliberately DISTINCT headings — "Amazon
    (amazon.com)" beside "Amazon, revisited", "Amazon (x)" beside "Amazon (y)" —
    so they exercise the prefix match rather than the collapse. The realistic
    mistake is the opposite: appending a re-record under a copy-pasted heading.
    While `split_sections` returned a dict that case did not fail at all, it
    OVERWROTE, and the surviving record was whichever came last in the file.
    """
    evidence = _write_evidence(
        tmp_path,
        [("Amazon (amazon.com)", _REFUSED), ("Amazon (amazon.com)", _REACHABLE)],
    )

    problems = evidence_check.check_retailer("Amazon", evidence)
    assert len(problems) == 1
    assert "2 sections" in problems[0]


def test_a_repeated_heading_does_not_let_the_last_record_win(tmp_path: Path) -> None:
    """Document order must not be what decides a verdict.

    The same two records in either order: a REFUSED and a REACHABLE for one
    unconfigured retailer is a contradiction, and it has to read as one from
    both directions. Under the dict splitter each order quietly produced the
    LAST record's verdict, so `--phase` returned `[]` for one ordering and would
    have returned `[]` for the other — a self-contradicting log certified clean,
    twice, for opposite reasons.
    """
    for i, pair in enumerate(
        [
            [("Amazon (amazon.com)", _REFUSED), ("Amazon (amazon.com)", _REACHABLE)],
            [("Amazon (amazon.com)", _REACHABLE), ("Amazon (amazon.com)", _REFUSED)],
        ]
    ):
        evidence = _write_evidence(
            tmp_path / f"order{i}",
            [
                ("Pokémon Center (pokemoncenter.com)", _REFUSED),
                ("Target (target.com)", _REFUSED),
                *pair,
            ],
        )
        config = _write_config(tmp_path / f"order{i}", _SHIPPED)

        problems = evidence_check.check_phase(config, evidence, _write_fixtures(tmp_path, []))

        assert len(problems) == 1, (pair, problems)
        assert "Amazon" in problems[0]
        assert "rule 2" in problems[0].lower()


def test_the_two_section_message_differs_from_the_missing_section_message(
    tmp_path: Path,
) -> None:
    two = evidence_check.check_retailer(
        "Amazon",
        _write_evidence(tmp_path / "a", [("Amazon (x)", _REFUSED), ("Amazon (y)", _REFUSED)]),
    )
    none = evidence_check.check_retailer(
        "Amazon", _write_evidence(tmp_path / "b", [("Nintendo (x)", _REACHABLE)])
    )
    assert two[0] != none[0]


MALFORMED = [
    # There is deliberately no rung-4 REACHABLE form: rung 4 IS refused, and a
    # section claiming to have reached a retailer it dropped is a contradiction
    # the grammar should not be able to express.
    "**Verdict: REACHABLE (rung 4)**",
    # The bold markers are load-bearing — later gates anchor on them.
    "Verdict: REFUSED",
    # The word `Verdict:` is what makes it a verdict rather than a shout.
    "**REFUSED**",
    # Rung 0 does not exist either.
    "**Verdict: REACHABLE (rung 0)**",
    # Prose after the line means it is a sentence, not a machine-readable claim.
    "**Verdict: REFUSED** for now",
]


def test_malformed_verdict_strings_are_rejected(tmp_path: Path) -> None:
    """Each of these looks like a verdict to a human and is not one to a grep."""
    for i, bad in enumerate(MALFORMED):
        evidence = _write_evidence(tmp_path / f"m{i}", [("Amazon (amazon.com)", bad + "\n")])
        assert (
            evidence_check.main(["--retailer", "Amazon", "--evidence", str(evidence)]) == 1
        ), bad


def test_the_failure_message_names_the_file_and_the_retailer(tmp_path: Path) -> None:
    """A failure you cannot act on gets ignored within a week."""
    evidence = _write_evidence(tmp_path, [("Nintendo (x)", _REACHABLE)])

    problems = evidence_check.check_retailer("Amazon", evidence)

    assert "Amazon" in problems[0]
    assert str(evidence) in problems[0]


# --------------------------------------------------------------------------
# --phase rule 1: in scope. The padding door Micro Center would have walked through
# --------------------------------------------------------------------------


def _full_evidence(tmp_path: Path) -> Path:
    """Sections for every roadmap retailer that is not in `_SHIPPED`."""
    return _write_evidence(
        tmp_path,
        [
            ("Best Buy", _REACHABLE),
            ("Nintendo (store.nintendo.com)", _REACHABLE),
            ("Pokémon Center (pokemoncenter.com)", _REFUSED),
            ("Target (target.com)", _REFUSED),
            ("Amazon (amazon.com)", _REFUSED),
        ],
    )


def test_a_retailer_outside_the_roadmaps_scope_fails_the_phase_gate(tmp_path: Path) -> None:
    """The padding case, and it is not hypothetical.

    Micro Center is REACHABLE at rung 1, config-only, with a viable control — a
    completely real retailer that would produce a completely green fifth row and
    could never once alert on the Pokémon GO Plus +, because it does not carry
    it. Every existing enforcement layer passes it: `control_check.py` sees a
    control, `assess_health` sees it go green, and the fixture test sees a page
    we really read. This rule is the only thing that catches it.
    """
    config = _write_config(tmp_path, [*_SHIPPED, "microcenter"])
    evidence = _full_evidence(tmp_path)

    assert (
        evidence_check.main(
            [
                "--phase",
                "--config",
                str(config),
                "--evidence",
                str(evidence),
                "--fixtures",
                str(_write_fixtures(tmp_path, [])),
            ]
        )
        == 1
    )


def test_the_out_of_scope_message_names_the_retailer_and_points_at_the_roadmap(
    tmp_path: Path,
) -> None:
    config = _write_config(tmp_path, [*_SHIPPED, "microcenter"])
    problems = evidence_check.check_phase(
        config, _full_evidence(tmp_path), _write_fixtures(tmp_path, [])
    )

    assert len(problems) == 1
    assert "microcenter" in problems[0]
    assert str(config) in problems[0]
    assert "Retailer Scope" in problems[0]
    assert "rule 1" in problems[0].lower()


# --------------------------------------------------------------------------
# --phase rule 2: configured, or refused. No silent third state
# --------------------------------------------------------------------------


def test_an_unconfigured_roadmap_retailer_with_no_verdict_fails(tmp_path: Path) -> None:
    """The silent gap this phase exists to make impossible.

    Target is not configured and has no section: nothing in the repo says
    whether it was tried. That is exactly the state the roadmap forbids — "no
    silent gaps" — and it must be a failure rather than an absence.
    """
    config = _write_config(tmp_path, _SHIPPED)
    evidence = _write_evidence(
        tmp_path,
        [
            ("Best Buy", _REACHABLE),
            ("Nintendo (store.nintendo.com)", _REACHABLE),
            ("Pokémon Center (pokemoncenter.com)", _REFUSED),
            ("Amazon (amazon.com)", _REFUSED),
        ],
    )

    assert (
        evidence_check.main(
            [
                "--phase",
                "--config",
                str(config),
                "--evidence",
                str(evidence),
                "--fixtures",
                str(_write_fixtures(tmp_path, [])),
            ]
        )
        == 1
    )

    problems = evidence_check.check_phase(config, evidence, _write_fixtures(tmp_path, []))
    assert len(problems) == 1
    assert "Target" in problems[0]
    assert "rule 2" in problems[0].lower()


def test_an_unconfigured_retailer_recorded_as_REACHABLE_fails(tmp_path: Path) -> None:
    """Reachable but not shipped is a contradiction, not a shortfall.

    If we could read it and chose not to configure it, the document and the
    config disagree about what this project supports, and the support matrix
    built from them will be wrong in the flattering direction.
    """
    config = _write_config(tmp_path, _SHIPPED)
    evidence = _write_evidence(
        tmp_path,
        [
            ("Pokémon Center (pokemoncenter.com)", _REFUSED),
            ("Target (target.com)", _REACHABLE),
            ("Amazon (amazon.com)", _REFUSED),
        ],
    )

    problems = evidence_check.check_phase(config, evidence, _write_fixtures(tmp_path, []))
    assert len(problems) == 1
    assert "Target" in problems[0]
    assert "REFUSED" in problems[0]


def test_every_violation_is_reported_not_just_the_first(tmp_path: Path) -> None:
    """Fixing one gap only to be told about the next is how a gate gets muted."""
    config = _write_config(tmp_path, [*_SHIPPED, "microcenter"])
    evidence = _write_evidence(tmp_path, [("Amazon (amazon.com)", _REFUSED)])

    problems = evidence_check.check_phase(config, evidence, _write_fixtures(tmp_path, []))

    # rule 1: microcenter out of scope. rule 2: pokemoncenter and target unrecorded.
    assert len(problems) == 3
    joined = "\n".join(problems)
    assert "microcenter" in joined
    assert "Pokémon Center" in joined
    assert "Target" in joined


# --------------------------------------------------------------------------
# --phase rule 2, the third state: in scope, nobody has looked, and it expires
# --------------------------------------------------------------------------


def _unprobed(scoped: date) -> str:
    return f"Brought into scope. Nothing probed yet.\n\n**Verdict: UNPROBED (scoped {scoped})**\n"


_TODAY = date(2026, 8, 3)


def _scoped_tree(tmp_path: Path, body: str) -> tuple[Path, Path, Path]:
    """A tree where every roadmap retailer is settled except Target."""
    evidence = _write_evidence(
        tmp_path,
        [
            ("Pokémon Center (pokemoncenter.com)", _REFUSED),
            ("Amazon (amazon.com)", _REFUSED),
            ("Target (target.com)", body),
        ],
    )
    return _write_config(tmp_path, _SHIPPED), evidence, _write_fixtures(tmp_path, [])


def test_a_dated_unprobed_verdict_inside_the_grace_period_passes(tmp_path: Path) -> None:
    """The honest state this grammar could not express, and the reason it needed to.

    Rule 2 admitted two states — configured, or refused in writing — and 03-03
    wired this gate into `make verify` permanently. From the commit that widens
    ROADMAP_RETAILERS until the retailer is settled, the tree is red, and there
    were exactly two ways to green it: ship a detector, or write
    `**Verdict: REFUSED**` for a store nobody had touched. The second is one
    line. A gate that makes the honest answer unrepresentable pressures exactly
    the padding this file exists to prevent, in the opposite sign.

    This phase hit that wall itself: `test_the_repo_as_it_stands_after_this_plan_names_target_as_the_only_gap`
    records that the tree was legitimately red between 03-01 and 03-02, and the
    fix was to keep the gate out of `make verify` for one plan. That escape is
    gone, so the state needed a spelling instead.
    """
    config, evidence, fixtures = _scoped_tree(tmp_path, _unprobed(date(2026, 7, 20)))

    assert evidence_check.check_phase(config, evidence, fixtures, today=_TODAY) == []


def test_an_unprobed_verdict_past_the_grace_period_fails(tmp_path: Path) -> None:
    """The difference between a grace period and an escape hatch is the expiry.

    The Phase 2 clause rotted by PERSISTING — it was correct the day it was
    written and permanently satisfied thereafter. An UNPROBED verdict that never
    expired would be the same shape: a one-line way to be silent forever, with a
    date on it for reassurance. So the clock runs from the scoped date in the
    line itself, which means touching the file does not reset it.
    """
    stale = _TODAY - timedelta(days=evidence_check.UNPROBED_GRACE_DAYS + 1)
    config, evidence, fixtures = _scoped_tree(tmp_path, _unprobed(stale))

    problems = evidence_check.check_phase(config, evidence, fixtures, today=_TODAY)

    assert len(problems) == 1, problems
    assert "Target" in problems[0]
    assert "expires" in problems[0]
    assert str(evidence_check.UNPROBED_GRACE_DAYS) in problems[0]


def test_the_grace_period_boundary_is_inclusive(tmp_path: Path) -> None:
    """Exactly `UNPROBED_GRACE_DAYS` old still passes; one day more does not.

    Pinned because an off-by-one here is invisible: both sides of it look like a
    working gate, and the failing side only appears on one particular day.
    """
    for offset, expected in ((evidence_check.UNPROBED_GRACE_DAYS, 0),
                             (evidence_check.UNPROBED_GRACE_DAYS + 1, 1)):
        scoped = _TODAY - timedelta(days=offset)
        config, evidence, fixtures = _scoped_tree(tmp_path / f"d{offset}", _unprobed(scoped))

        problems = evidence_check.check_phase(config, evidence, fixtures, today=_TODAY)

        assert len(problems) == expected, (offset, problems)


def test_strict_mode_rejects_an_unprobed_verdict_however_fresh(tmp_path: Path) -> None:
    """The phase-close bar. A phase does not get to close on a store nobody read.

    `make verify` runs non-strict so the honest state is expressible while the
    work is in flight. `--strict` is the other end of that bargain, and without
    it "not yet" would be a way of never answering that no gate ever asks about.
    """
    config, evidence, fixtures = _scoped_tree(tmp_path, _unprobed(_TODAY))

    assert evidence_check.check_phase(config, evidence, fixtures, today=_TODAY) == []

    problems = evidence_check.check_phase(
        config, evidence, fixtures, strict=True, today=_TODAY
    )
    assert len(problems) == 1
    assert "--strict" in problems[0]
    assert "Target" in problems[0]


def test_the_strict_flag_reaches_check_phase_from_the_command_line(tmp_path: Path) -> None:
    """A mode reachable only from Python is a mode nobody runs at phase close."""
    config, evidence, fixtures = _scoped_tree(tmp_path, _unprobed(_TODAY))
    argv = [
        "--phase",
        "--config", str(config),
        "--evidence", str(evidence),
        "--fixtures", str(fixtures),
    ]

    assert evidence_check.main(argv) == 0
    assert evidence_check.main([*argv, "--strict"]) == 1


MALFORMED_UNPROBED = [
    # No date at all: "nobody has looked" with no clock is the escape hatch.
    "**Verdict: UNPROBED**",
    # A date shape the grammar does not accept.
    "**Verdict: UNPROBED (scoped 2026-8-3)**",
    # `\\d{4}-\\d{2}-\\d{2}` matches this and it is not a day. An impossible date
    # must not be a way to buy silence forever.
    "**Verdict: UNPROBED (scoped 2026-13-45)**",
    # The word `scoped` is what makes the date a scoping date.
    "**Verdict: UNPROBED (2026-08-03)**",
    # Prose after the line means it is a sentence, not a machine-readable claim.
    "**Verdict: UNPROBED (scoped 2026-08-03)** — will look next week",
]


def test_malformed_unprobed_verdicts_are_rejected(tmp_path: Path) -> None:
    """Each looks like the new verdict to a human and is not one to a grep.

    Same role as `test_malformed_verdict_strings_are_rejected` one form along.
    The impossible-date case is the one worth naming: the regex matches it, so
    without `date.fromisoformat` rejecting it, `2026-13-45` would have been an
    UNPROBED verdict whose age could never be computed.
    """
    for i, bad in enumerate(MALFORMED_UNPROBED):
        config, evidence, fixtures = _scoped_tree(tmp_path / f"u{i}", bad + "\n")

        problems = evidence_check.check_phase(config, evidence, fixtures, today=_TODAY)

        assert len(problems) == 1, (bad, problems)
        assert "rule 2 (configured or refused)" in problems[0], bad


def test_a_section_carrying_both_a_refusal_and_an_unprobed_verdict_fails(
    tmp_path: Path,
) -> None:
    """Two verdicts is two verdicts, whichever forms they take.

    A retailer cannot be both settled and unlooked-at, and the count check has
    to see all three forms or a REFUSED beside an UNPROBED would read as one.
    """
    body = f"{_REFUSED}\n**Verdict: UNPROBED (scoped {_TODAY})**\n"
    config, evidence, fixtures = _scoped_tree(tmp_path, body)

    problems = evidence_check.check_phase(config, evidence, fixtures, today=_TODAY)
    assert len(problems) == 1
    assert "rule 2 (configured or refused)" in problems[0]

    per_retailer = evidence_check.check_retailer("Target", evidence)
    assert len(per_retailer) == 1
    assert "2 verdict lines" in per_retailer[0]


def test_an_unprobed_only_section_is_a_verdict_to_the_per_retailer_mode(
    tmp_path: Path,
) -> None:
    """`--retailer` and `--phase` must agree about what counts as a verdict.

    Without `all_verdict_lines`, a section carrying only an UNPROBED line reads
    as carrying NO verdict to `--retailer` while `--phase` accepts it — the two
    modes disagreeing about the same document, which is how a reader learns to
    trust neither.
    """
    evidence = _write_evidence(
        tmp_path, [("Target (target.com)", _unprobed(_TODAY))]
    )

    assert evidence_check.main(["--retailer", "Target", "--evidence", str(evidence)]) == 0


def test_the_rule_two_failure_names_the_honest_path(tmp_path: Path) -> None:
    """The fastest green has to be an honest one, and it has to be findable.

    Somebody widens the scope, `make verify` goes red, and they read exactly one
    message. If that message only says "configured or refused", the one-line fix
    it suggests is a false REFUSED for a store nobody probed — and a false
    REFUSED never expires. So the message names the third form, spells it, and
    says it runs out.
    """
    config = _write_config(tmp_path, _SHIPPED)
    evidence = _write_evidence(
        tmp_path,
        [
            ("Pokémon Center (pokemoncenter.com)", _REFUSED),
            ("Amazon (amazon.com)", _REFUSED),
        ],
    )

    problems = evidence_check.check_phase(
        config, evidence, _write_fixtures(tmp_path, []), today=_TODAY
    )

    assert len(problems) == 1
    assert evidence_check.UNPROBED_EXAMPLE in problems[0]
    assert str(evidence_check.UNPROBED_GRACE_DAYS) in problems[0]
    assert "never expires" in problems[0]


def test_the_shipped_tree_carries_no_unprobed_verdict() -> None:
    """UNPROBED is temporary, and this is where its existence stays visible.

    Nothing in scope is unprobed today: three retailers are refused in writing
    and four are shipped. If a future scope expansion adds one, this test goes
    red — and the edit that greens it is a deliberate, reviewable line naming
    which retailer is waiting, at which point the grace clock is already running
    in the evidence log. That is the difference between an escape hatch and a
    hole: taking it costs a red test exactly once, and it un-takes itself.

    `make verify` deliberately runs the gate WITHOUT `--strict`, so this test is
    the only place the tree's unprobed set is stated. Do not delete it to make a
    scope expansion quiet.
    """
    text = (REPO_ROOT / "docs" / "retailer-evidence.md").read_text(encoding="utf-8")

    unprobed = {
        heading: evidence_check.unprobed_lines(body)
        for heading, body in evidence_check.split_sections(text)
        if evidence_check.unprobed_lines(body)
    }

    assert unprobed == {}, unprobed


# --------------------------------------------------------------------------
# --phase rule 3: a short count with a hard-two retailer present is incoherent
# --------------------------------------------------------------------------


def test_a_short_count_with_a_hard_two_retailer_configured_fails(tmp_path: Path) -> None:
    """Something disagrees with something else and should be read, not rounded.

    Fewer than five configured while Target or Amazon IS configured means the
    phase both landed a hard retailer and lost one somewhere else. That is a
    real event worth a human look, not a number to move on from.
    """
    config = _write_config(tmp_path, ["gamestop", "walmart", "nintendo", "amazon"])
    evidence = _write_evidence(
        tmp_path,
        [
            ("Best Buy", _REFUSED),
            ("Pokémon Center (pokemoncenter.com)", _REFUSED),
            ("Target (target.com)", _REFUSED),
        ],
    )

    assert (
        evidence_check.main(
            [
                "--phase",
                "--config",
                str(config),
                "--evidence",
                str(evidence),
                "--fixtures",
                str(_write_fixtures(tmp_path, [])),
            ]
        )
        == 1
    )

    problems = evidence_check.check_phase(config, evidence, _write_fixtures(tmp_path, []))
    assert len(problems) == 1
    assert "rule 3" in problems[0].lower()
    assert "amazon" in problems[0]


def test_five_retailers_including_a_hard_two_one_passes(tmp_path: Path) -> None:
    """The outcome the phase is hoping for must verify clean."""
    config = _write_config(tmp_path, [*_SHIPPED, "target"])
    evidence = _write_evidence(
        tmp_path,
        [
            ("Pokémon Center (pokemoncenter.com)", _REFUSED),
            ("Amazon (amazon.com)", _REFUSED),
        ],
    )

    assert (
        evidence_check.main(
            [
                "--phase",
                "--config",
                str(config),
                "--evidence",
                str(evidence),
                "--fixtures",
                str(_write_fixtures(tmp_path, [])),
            ]
        )
        == 0
    )


# --------------------------------------------------------------------------
# --phase rule 4: the floor. A refusal cannot outrank a page we captured
# --------------------------------------------------------------------------


def test_a_retailer_dropped_from_the_config_but_still_fixtured_fails(tmp_path: Path) -> None:
    """Rules 2 and 3 are a ceiling. This is the only thing underneath.

    Every rule that shipped before this one points the same way: they stop the
    retailer count drifting UP. Down was free — any number of configured
    retailers passed, down to zero, provided each absent one carried a written
    REFUSED. A working retailer silently disappearing is precisely the silent
    gap this phase is named after.
    """
    evidence = _write_evidence(
        tmp_path,
        [
            ("GameStop (gamestop.com)", _REFUSED),
            ("Walmart (walmart.com)", _REFUSED),
            ("Pokémon Center (pokemoncenter.com)", _REFUSED),
            ("Target (target.com)", _REFUSED),
            ("Amazon (amazon.com)", _REFUSED),
        ],
    )
    config = _write_config(tmp_path, ["bestbuy", "nintendo"])
    fixtures = _write_fixtures(tmp_path, ["gamestop", "walmart", "bestbuy", "nintendo"])

    problems = evidence_check.check_phase(config, evidence, fixtures)

    assert len(problems) == 2, problems
    assert all(p.startswith("rule 4") for p in problems), problems
    assert "GameStop" in problems[0]
    assert "Walmart" in problems[1]


def test_the_rule_four_message_names_the_captures_and_says_which_way_it_points(
    tmp_path: Path,
) -> None:
    """A failure nobody can act on gets ignored within a week.

    Two facts have to be in the message: WHICH pages contradict the refusal, and
    that this is the count's floor rather than another way of saying rule 2.
    """
    evidence = _write_evidence(
        tmp_path,
        [
            ("GameStop (gamestop.com)", _REFUSED),
            ("Pokémon Center (pokemoncenter.com)", _REFUSED),
            ("Target (target.com)", _REFUSED),
            ("Amazon (amazon.com)", _REFUSED),
        ],
    )
    config = _write_config(tmp_path, ["walmart", "bestbuy", "nintendo"])
    fixtures = _write_fixtures(tmp_path, ["gamestop"])

    problems = evidence_check.check_phase(config, evidence, fixtures)

    assert len(problems) == 1
    assert "rule 4" in problems[0]
    assert "GameStop" in problems[0]
    assert "control.html" in problems[0]
    assert "drifting down" in problems[0]


def test_a_refused_retailer_with_no_captured_page_passes_rule_four(tmp_path: Path) -> None:
    """The clean side, so this is a rule about a fact rather than about absence.

    Without it, rule 4 could be satisfied by a tree that never captures anything
    — and the three retailers this project really did refuse (Pokémon Center,
    Amazon, Target) have no capture directory precisely because the refusal is
    genuine.
    """
    evidence = _full_evidence(tmp_path)
    config = _write_config(tmp_path, _SHIPPED)
    fixtures = _write_fixtures(tmp_path, _SHIPPED)

    assert evidence_check.check_phase(config, evidence, fixtures) == []


def test_rule_four_ignores_a_capture_directory_holding_no_page(tmp_path: Path) -> None:
    """An empty directory is not evidence of a fetch, and `git` cannot commit one.

    Keyed on `*.html` rather than on the directory existing, so a leftover empty
    folder in somebody's working tree cannot redden a gate about what we read.
    """
    evidence = _full_evidence(tmp_path)
    config = _write_config(tmp_path, _SHIPPED)
    fixtures = _write_fixtures(tmp_path, _SHIPPED)
    (fixtures / "target").mkdir()

    assert evidence_check.check_phase(config, evidence, fixtures) == []


# --------------------------------------------------------------------------
# The honest shortfall — this phase's likely end state, and it is not a bug
# --------------------------------------------------------------------------


def test_the_honest_shortfall_of_four_retailers_with_both_hard_two_refused_passes(
    tmp_path: Path,
) -> None:
    """FOUR retailers, both of Phase 3's refused with evidence — this verifies CLEAN.

    Read the name of this test as the specification it is. The roadmap's
    criterion 5 wants five retailers; the likely honest outcome of Phase 3 is
    four, with Target and Amazon each carrying a written REFUSED verdict. That
    is a criterion recorded as unmet, not a broken tree, and the gate must not
    punish it — a gate that goes red on the honest answer is a gate that
    pressures the next person into padding the count, which is the exact
    behaviour it was built to prevent.

    What it does refuse is the same shortfall with any of it left unsaid.
    """
    config = _write_config(tmp_path, _SHIPPED)
    evidence = _full_evidence(tmp_path)

    assert (
        evidence_check.main(
            [
                "--phase",
                "--config",
                str(config),
                "--evidence",
                str(evidence),
                "--fixtures",
                str(_write_fixtures(tmp_path, [])),
            ]
        )
        == 0
    )
    assert evidence_check.check_phase(config, evidence, _write_fixtures(tmp_path, [])) == []


def test_the_repo_as_it_stands_after_this_plan_names_target_as_the_only_gap(
    tmp_path: Path,
) -> None:
    """Why `--phase` is NOT wired into `make verify` until 03-03.

    This mirrors the shipped tree at the end of 03-01: four configured
    retailers, Pokémon Center and Amazon both recorded REFUSED, and Target
    settled by nobody yet. Rule 2 calls that a silent gap, correctly — Target is
    genuinely unrecorded, and weakening the rule so that today's tree passes
    would reintroduce the Phase 2 defect one layer out, an escape hatch that
    stops being able to fail.

    So the rule stays strict and the gate stays out of `make verify` for one
    plan. 03-02 writes Target's verdict; 03-03 wires this in. The gap is
    load-bearing and temporary, and this test is where it is written down.
    """
    config = _write_config(tmp_path, _SHIPPED)
    evidence = _write_evidence(
        tmp_path,
        [
            ("Best Buy", _REACHABLE),
            ("Nintendo (store.nintendo.com)", _REACHABLE),
            ("Pokémon Center (pokemoncenter.com)", _REFUSED),
            ("Amazon (amazon.com)", _REFUSED),
        ],
    )

    problems = evidence_check.check_phase(config, evidence, _write_fixtures(tmp_path, []))

    assert len(problems) == 1
    assert "Target" in problems[0]


# --------------------------------------------------------------------------
# The gate reads the shipped config the way the monitor does
# --------------------------------------------------------------------------


def test_the_configured_set_comes_from_config_load_not_a_second_yaml_parse(
    tmp_path: Path,
) -> None:
    """The gate and the monitor must not be able to disagree about what ships.

    `scripts/control_check.py` gives the same reasoning for building its checker
    with `boty.cli._make_checker`. A private YAML reader here would drift from
    `Config.load` the first time the schema moved, and the gate would then be
    enforcing a rule about a file nobody runs.
    """
    config = _write_config(tmp_path, _SHIPPED)
    evidence = _full_evidence(tmp_path)

    seen: list[str] = []
    real_load = evidence_check.Config.load

    def _spy(path: object) -> Any:
        seen.append(str(path))
        return real_load(path)

    evidence_check.Config.load = _spy  # type: ignore[method-assign]
    try:
        evidence_check.check_phase(config, evidence, _write_fixtures(tmp_path, []))
    finally:
        evidence_check.Config.load = real_load  # type: ignore[method-assign]

    assert seen == [str(config)]


def test_the_real_shipped_evidence_document_passes_per_retailer() -> None:
    """Every settled retailer, checked one at a time against the real file.

    Per-retailer as well as `--phase` below, because the two fail differently:
    this one names the retailer whose section is malformed, while the phase gate
    reports which rule the tree as a whole broke. Being told "something is wrong
    with the evidence log" is how a gate gets muted.

    (Until 03-02 this was deliberately the ONLY real-tree check here, because
    Target had no verdict and a whole-tree assertion would have gone red between
    plans for a reason that was not a defect. Target is now settled at rung 4,
    so the phase gate below can join it.)
    """
    evidence = REPO_ROOT / "docs" / "retailer-evidence.md"
    for display in ("Best Buy", "Nintendo", "Pokémon Center", "Amazon", "Target"):
        assert evidence_check.check_retailer(display, evidence) == [], display


def test_the_shipped_tree_passes_the_whole_phase_gate() -> None:
    """This line is what puts the honesty gate inside `make verify`.

    A gate that only runs inside one plan's `verify` block dies with the plan.
    This one runs in the `test` stage on every `make verify` from now on, so a
    later edit that pads the retailer set with a store that cannot carry the
    product, or leaves a roadmap retailer with no verdict at all, goes red
    without anybody remembering to run a script.

    It is deliberately NOT a new Makefile stage: the stage list and the four
    exit codes are pinned by `tests/test_verify_makefile.py`, so a stage would
    be a large change for no extra signal.

    The problems are included in the message because "the phase gate failed" is
    not actionable and "rule 2 (configured or refused): Target is not
    configured and the evidence log records no section for it" is.
    """
    problems = evidence_check.check_phase(
        REPO_ROOT / "config" / "products.yaml",
        REPO_ROOT / "docs" / "retailer-evidence.md",
        REPO_ROOT / "tests" / "fixtures",
    )

    assert problems == [], "the shipped tree fails its own honesty gate:\n  " + "\n  ".join(problems)


def test_the_shipped_tree_would_fail_if_a_working_retailer_were_quietly_dropped(
    tmp_path: Path,
) -> None:
    """The floor, driven against the REAL evidence log and the REAL captures.

    The test above proves the shipped tree is clean; on its own that is a gate
    nobody has watched fail, and rules 1-3 could not fail in this direction at
    all. This is the reviewer's reproduction, run as a test: the gamestop and
    walmart watches gone, two REFUSED sections appended so rule 2 is fully
    satisfied, the real `tests/fixtures/` left alone.

    Before rule 4 existed that tree produced:

        configured retailers: ['bestbuy', 'nintendo']   watches: 3
        253 passed in 1.07s
        evidence check: PASS — phase

    Rule 4 must fire on its own merits, which is asserted below rather than
    assumed: a floor that only works while rule 2 happens to be broken too is not
    a floor. So rule 2's silence is asserted separately from rule 4's two hits.

    `target` joined the kept config on 2026-08-03 and `amazon` joined it the same
    day, one wave later. Both are configured in the real tree AND have committed
    captures, so leaving either out would fire rules 2 and 4 about a retailer
    this test is not about.

    Keeping them does make **rule 3** fire, and that is correct rather than
    incidental: both are HARD_TWO members, and rule 3 exists to say that a tree
    cannot both land a hard-two retailer and fall short of five. This scenario
    deliberately deletes two working retailers, so it genuinely is such a tree.
    The assertion below therefore filters to rule 4 rather than counting every
    problem — which narrows what is asserted about, not what is required.
    """
    config = _write_config(tmp_path, ["bestbuy", "nintendo", "target", "amazon"])
    evidence = tmp_path / "retailer-evidence.md"
    evidence.write_text(
        (REPO_ROOT / "docs" / "retailer-evidence.md").read_text(encoding="utf-8")
        + "\n---\n\n## GameStop (gamestop.com)\n\nRefused.\n\n**Verdict: REFUSED**\n"
        + "\n---\n\n## Walmart (walmart.com)\n\nRefused.\n\n**Verdict: REFUSED**\n",
        encoding="utf-8",
    )

    problems = evidence_check.check_phase(
        config, evidence, REPO_ROOT / "tests" / "fixtures"
    )

    rule_four = [p for p in problems if p.startswith("rule 4")]

    assert [p for p in problems if p.startswith("rule 2")] == [], (
        "rule 2 must be silent here, or rule 4's two hits prove nothing: a floor "
        "that only bites while rule 2 is also failing is not a floor"
    )
    assert len(rule_four) == 2, problems
    assert "GameStop" in rule_four[0] and "goplusplus.html" in rule_four[0]
    assert "Walmart" in rule_four[1] and "goplusplus.html" in rule_four[1]


def test_a_refusal_for_a_retailer_we_never_captured_is_still_clean(tmp_path: Path) -> None:
    """Rule 4 must not punish the honest refusals this phase actually produced.

    Pokémon Center was walked down every rung and refused, and it is now the ONLY
    retailer in scope in that state. It has no capture directory, so it does not
    trip this rule — which is the whole point of keying rule 4 on a page we
    really read rather than on the count.

    Neither Target nor Amazon is one of them any more, and both are added to the
    config here for that reason rather than left out: each was fetched, each has
    a capture, and each is configured in the shipped tree. Leaving either out
    would fire rules 2 and 4 about a retailer this test is not about. Amazon's
    departure is the sharper one — it was the example this docstring used to
    give for "never fetched at all", and on 2026-08-03 it was fetched.

    `_SHIPPED` itself stays at four, because every other test in this file uses
    it to build SYNTHETIC trees whose evidence documents have no Target or Amazon
    section at all.
    """
    config = _write_config(tmp_path, [*_SHIPPED, "target", "amazon"])

    problems = evidence_check.check_phase(
        config,
        REPO_ROOT / "docs" / "retailer-evidence.md",
        REPO_ROOT / "tests" / "fixtures",
    )

    assert problems == [], problems


# --------------------------------------------------------------------------
# --phase rule 5: a configuration cannot outrank a refusal — the W-02 mirror
# --------------------------------------------------------------------------


def _w02_tree(tmp_path: Path, pokemoncenter_body: str) -> tuple[Path, Path, Path]:
    """The W-02 shape: `pokemoncenter` SHIPPED, its section saying otherwise.

    Returns (config, evidence, fixtures). The Pokémon Center body is the only
    variable, because the whole point of rule 5 is that it is about the
    disagreement and not about the retailer — swap the body for a REACHABLE
    verdict and the same tree must come back clean.
    """
    config = _write_config(tmp_path, [*_SHIPPED, "pokemoncenter"])
    evidence = _write_evidence(
        tmp_path,
        [
            ("Best Buy", _REACHABLE),
            ("Nintendo (store.nintendo.com)", _REACHABLE),
            ("Pokémon Center (pokemoncenter.com)", pokemoncenter_body),
            ("Target (target.com)", _REFUSED),
            ("Amazon (amazon.com)", _REFUSED),
        ],
    )
    return config, evidence, _write_fixtures(tmp_path, [])


def test_a_configured_retailer_with_a_standing_refusal_fails_the_phase_gate(
    tmp_path: Path,
) -> None:
    """W-02, reproduced literally, as the case that used to return exit 0.

    `03-VERIFICATION.md` recorded this tree — a `pokemoncenter` watch added to
    `config/products.yaml` while `docs/retailer-evidence.md` goes on carrying
    `**Verdict: REFUSED**` for Pokémon Center — producing

        evidence check: PASS — phase
        evidence_check exit: 0

    Rule 1 passed (in scope) and rules 2 and 4 both `continue` on
    `retailer in configured`, so the one flatly self-contradicting tree shape
    walked between them. Re-confirmed against the tree immediately before rule 5
    was written: `check_phase` returned `[]`.

    EXACTLY ONE problem, asserted rather than `>= 1`: a rule that fires twice on
    one contradiction reads as two defects, and the reader who chases the second
    one stops trusting the first.
    """
    config, evidence, fixtures = _w02_tree(tmp_path, _REFUSED)

    problems = evidence_check.check_phase(config, evidence, fixtures)

    assert len(problems) == 1, problems
    assert "rule 5" in problems[0], problems[0]
    assert "Pokémon Center" in problems[0], problems[0]


def test_the_same_tree_is_clean_once_the_verdict_agrees_with_the_watch(
    tmp_path: Path,
) -> None:
    """The rule is about the disagreement, not about the retailer.

    Same config, same seven sections, one verdict line changed from REFUSED to
    REACHABLE — and it must go green. Without this, rule 5 could be satisfied by
    a blanket "pokemoncenter must never be configured", which would make the
    outcome this whole phase is walking towards — a refused retailer re-probed,
    reached, and shipped — unrepresentable. That is precisely the failure mode
    rule 2 grew `UNPROBED` to escape.
    """
    config, evidence, fixtures = _w02_tree(tmp_path, _REACHABLE)

    assert evidence_check.check_phase(config, evidence, fixtures) == []


def test_a_configured_retailer_recorded_unprobed_fails_the_phase_gate(
    tmp_path: Path,
) -> None:
    """The same contradiction one step softer, and softer is what ships.

    "Nobody has looked yet" alongside a shipped, control-verified detector is
    not a grace period — it is a section nobody updated after the probe. Left
    unchecked it would be the cheap way through rule 5: an UNPROBED line reads
    as work-in-progress rather than as a claim, and it is one line to write.
    """
    config, evidence, fixtures = _w02_tree(tmp_path, _unprobed(_TODAY))

    problems = evidence_check.check_phase(config, evidence, fixtures, today=_TODAY)

    assert len(problems) == 1, problems
    assert "rule 5" in problems[0], problems[0]
    assert "Pokémon Center" in problems[0], problems[0]
    assert "UNPROBED" in problems[0], problems[0]


def test_a_configured_retailer_with_no_section_at_all_is_deliberately_clean(
    tmp_path: Path,
) -> None:
    """The GameStop/Walmart shape, and it must stay green.

    Both ship today and neither has ever had a section in the evidence log:
    rule 2 requires one only from retailers that are NOT configured. If rule 5
    demanded a section from every configured retailer it would redden the
    shipped tree the moment it landed, and the fastest green would be two
    hand-written sections for retailers nobody re-probed — inventing records to
    satisfy a gate, which is the Phase 2 failure with the sign flipped.

    Silence about a shipped retailer is a documentation gap. Rule 5 is about
    self-contradiction, and a tree cannot contradict a claim nobody made.
    """
    config = _write_config(tmp_path, _SHIPPED)
    evidence = _full_evidence(tmp_path)

    assert evidence_check.check_phase(config, evidence, _write_fixtures(tmp_path, [])) == []

    sections = evidence_check.split_sections(evidence.read_text(encoding="utf-8"))
    for display in ("GameStop", "Walmart"):
        assert evidence_check.sections_for(display, sections) == [], display


def test_the_w02_tree_reaches_a_shell_as_exit_1(tmp_path: Path, capsys: Any) -> None:
    """Driven through `main`, because a rule only a test can see is not a gate.

    W-02's whole content was an exit code: `evidence check: PASS — phase`,
    exit 0, on a tree that contradicts itself. Asserting `check_phase` returns a
    list would leave that exact claim unchecked — the failure has to reach a
    shell, on stderr, naming the rule.
    """
    config, evidence, fixtures = _w02_tree(tmp_path, _REFUSED)

    code = evidence_check.main(
        [
            "--phase",
            "--config",
            str(config),
            "--evidence",
            str(evidence),
            "--fixtures",
            str(fixtures),
        ]
    )

    assert code == 1
    err = capsys.readouterr().err
    assert "rule 5 (a configuration cannot outrank a refusal)" in err, err
    assert "Pokémon Center" in err, err


def test_rule_5_is_silent_on_the_shipped_tree(tmp_path: Path) -> None:
    """Rule 5's silence on the shipped tree, pinned so it stays deliberate.

    This is the assertion rule 5 was landed early for, and it has now been
    exercised for real TWICE. Target was registered on 2026-08-03 and Amazon the
    same day one wave later — and in both cases the verdict moved to REACHABLE in
    the SAME commit as the watch, which is the only reason this tree is silent.
    Register either without flipping its verdict and rule 5 fires.

    Both HARD_TWO members are now configured, so the shipped tree no longer
    contains a single example of the "configured and refused" shape rule 5 is
    about — which is why `_w02_tree` above drives the failing side off a
    synthetic Pokémon Center rather than off anything here. A rule watched only
    on the branch the tree happens to be on is a rule nobody has watched fail.
    """
    problems = evidence_check.check_phase(
        REPO_ROOT / "config" / "products.yaml",
        REPO_ROOT / "docs" / "retailer-evidence.md",
        REPO_ROOT / "tests" / "fixtures",
    )

    assert [p for p in problems if "rule 5" in p] == [], problems

    configured = {
        w.retailer
        for w in evidence_check.Config.load(REPO_ROOT / "config" / "products.yaml").watches
    }
    evidence = (REPO_ROOT / "docs" / "retailer-evidence.md").read_text(encoding="utf-8")

    for retailer, verdict in (("target", "**Verdict: REACHABLE (rung 3)**"),
                              ("amazon", "**Verdict: REACHABLE (rung 1)**")):
        assert retailer in configured, (
            f"{retailer} is expected to be configured here — this test is meaningful "
            "precisely because rule 5 stays silent on a CONFIGURED retailer whose "
            "verdict moved with it"
        )
        assert verdict in evidence, (
            f"a configured {retailer} carrying a standing REFUSED is exactly what "
            "rule 5 catches"
        )


def test_no_roadmap_retailer_resolves_to_more_than_one_section() -> None:
    """The narrow case rule 5 hands to `check_retailer`, kept covered.

    Rule 5 skips a retailer with more than one section, because `check_retailer`
    already words that failure and reporting it twice trains a reader to skim.
    But `test_the_real_shipped_evidence_document_passes_per_retailer` can only
    drive `check_retailer` over retailers that HAVE a section — run it over
    GameStop or Walmart and it fails for the absence, which is legal. So a
    duplicate `## GameStop …` heading would have been seen by nothing at all.

    This asks the one question that is safe for all seven: at most one section
    each. It is also the guard on the Task-2 hazard — `sections_for` matches a
    display name as a PREFIX, so any new `## ` heading beginning with a
    retailer's name silently creates a second section for it.
    """
    sections = evidence_check.split_sections(
        (REPO_ROOT / "docs" / "retailer-evidence.md").read_text(encoding="utf-8")
    )
    duplicated = {
        display: len(evidence_check.sections_for(display, sections))
        for display in evidence_check.ROADMAP_RETAILERS.values()
        if len(evidence_check.sections_for(display, sections)) > 1
    }

    assert duplicated == {}, (
        f"more than one `## ` section begins with these display names: {duplicated}. "
        "`sections_for` matches a prefix, so a heading like `## Target and Amazon, …` "
        "counts as a second Target section and nothing can tell which record is current."
    )


# --------------------------------------------------------------------------
# --phase rule 6: a refusal must cite an observation — REQ-07a, made mechanical
# --------------------------------------------------------------------------
#
# THE TWO LITERALS BELOW ARE THE POINT OF THIS WHOLE BLOCK, so they come first.
#
# They are the `## Amazon` and `## Target` sections of `docs/retailer-evidence.md`
# exactly as they stood at commit `339800e` — the last commit before Phase 3.1
# touched that file — lifted with `git show 339800e:docs/retailer-evidence.md`
# and pasted whole. Not excerpts, not a reconstruction: rule 6's claim about
# them is that they contain NO refusal observation anywhere in 238 and 420 lines
# respectively, and only the whole text can support that claim.
#
# Embedded as literals rather than read from git at test time, because this
# suite is offline and deterministic and a test that shells out to `git` does
# not run in a source tarball. Embedded rather than read from a data file
# because these are the exact bytes the assertion is about, and a reader looking
# at the test should be able to see what it is asserting against.
#
# Neither section says today what it says here. Target became
# `**Verdict: REACHABLE (rung 3)**` in 03.1-02 and Amazon
# `**Verdict: REACHABLE (rung 1)**` in 03.1-03, which is exactly why the text
# has to come out of git: the defect these prove — that the gate which shipped
# in Phase 3 could not tell a wall from a desk review — is no longer visible
# anywhere on disk.

_PRE_031_AMAZON = """\
## Amazon (amazon.com)

**Probed:** 2026-08-03, from danserver over a residential connection.
**Transport:** `curl` — a one-off, human-shaped read of public policy documents.
**`boty.fetch.get` was never pointed at amazon.com and no product page was
requested at any point in this phase.** That ordering is the finding rather than
a courtesy: the question "may we request this at all" was settled *before* any
request whose legitimacy would have depended on the answer, so this section can
make a claim the Pokémon Center one could only make retroactively.

**Verdict: REFUSED**

Rung 4, and the decisive reason is written rather than technical. Amazon's
Conditions of Use prohibit exactly what this monitor does, twice over — once by
naming the *data* and once by naming the *method*. No wall was ever reached
because none needed to be, and no transport work was spent on a retailer that
should not ship regardless of which transport won.

### What was retrieved

| Target | Result |
|---|---|
| `https://www.amazon.com/gp/help/customer/display.html?nodeId=508088` | **HTTP 200**, 344,140 B, `text/html;charset=UTF-8`, after a redirect to the current canonical URL `https://www.amazon.com/gp/help/customer/display.html?nodeId=GLSBYFE9MGKKQXXM`. Document header reads `Last updated: May 30, 2025` |
| `https://www.amazon.com/robots.txt` | **HTTP 200**, 7,887 B, `text/plain`, 436 lines, 100 `User-agent` blocks |
| `https://webservices.amazon.com/paapi5/documentation/register-for-pa-api.html` | **HTTP 200**, 52,744 B, after a redirect to `affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation` — the rung-2 API this repo would have reached for no longer exists |
| `https://affiliate-program.amazon.com/creatorsapi/docs/en-us/onboarding-request-access` | **HTTP 404**, 48,137 B — a guessed slug. Recorded rather than hidden; the correct URL was then read out of the previous page's own links instead of being guessed a second time |
| `https://affiliate-program.amazon.com/creatorsapi/docs/en-us/onboarding` | **HTTP 200**, 52,996 B |
| `https://affiliate-program.amazon.com/creatorsapi/docs/en-us/frequently-asked-questions` | **HTTP 200**, 52,829 B |

**Six requests in total, spaced 22–24 s apart, no retries, no refusals.** Two to
`www.amazon.com` — a public policy page, and the one file on the internet whose
entire purpose is to be fetched by an automated agent. Four to Amazon's developer
documentation hosts. **Zero to a product page. Zero from bot-y.**

### The operative clause, quoted in full

From the `LICENSE AND ACCESS` section of the Conditions of Use, retrieved
2026-08-03 from the URL in the table above. The whole sentence is reproduced so a
future reader can judge its scope for themselves rather than trusting this
document's reading of it:

> Subject to your compliance with these Conditions of Use and any Service Terms,
> and your payment of any applicable fees, Amazon or its content providers grant
> you a limited, non-exclusive, non-transferable, non-sublicensable license to
> access and make personal and non-commercial use of the Amazon Services. **This
> license does not include any resale or commercial use of any Amazon Service, or
> its contents; any collection and use of any product listings, descriptions, or
> prices; any derivative use of any Amazon Service or its contents; any
> downloading, copying, or other use of account information for the benefit of
> any third party; or any use of data mining, robots, or similar data gathering
> and extraction tools.**

And, two sentences later in the same paragraph:

> No Amazon Service, nor any part of any Amazon Service or its contents, may be
> reproduced, duplicated, copied, sold, resold, visited, or otherwise exploited
> for any commercial purpose without express written consent of Amazon.

> You may not misuse the Amazon Services. You may use the Amazon Services only as
> permitted by law.

**This is stronger than the Pokémon Center clause, and it is worth being precise
about why.** Pokémon Center's Terms forbid "data gathering or extraction methods
designed to scrape or extract data" — a prohibition on the *method*, which leaves
a reader room to argue about what counts as one. Amazon's clause forbids the
method *and independently* forbids "any collection and use of any product
listings, descriptions, or **prices**". Availability and price are the only two
fields bot-y reads. There is no reading of that sentence under which a stock
monitor is collecting something else, and no transport — impersonated HTTP, a
real browser, a residential proxy — changes which side of it we are on.

The licence Amazon grants is to "access and make personal and non-commercial use"
of the service. bot-y's use is personal and non-commercial, and that is not the
question: the carve-out for product listings and prices is written as an
exclusion *from* that same personal licence, not as a restriction on commercial
users only.

### robots.txt — narrower than the Conditions of Use, and the disagreement is the finding

The same shape as Pokémon Center, and worth stating explicitly because reading
robots.txt alone would have produced the opposite answer.

`https://www.amazon.com/robots.txt` is 436 lines and defines **100** `User-agent`
groups: one `*` group and 99 named ones. Almost every named group is the same two
lines —

```
User-agent: Scrapy
Disallow: /

User-agent: Crawl4AI
Disallow: /
```

— covering AI crawlers (`GPTBot`, `ClaudeBot`, `CCBot`, `Bytespider`,
`PerplexityBot`…) and, notably, **general-purpose scraping frameworks by name**:
`Scrapy` and `Crawl4AI` are each shut out of the entire site. That is not a
prohibition bot-y's user-agent string trips, but it is a clear statement of
intent from the same file.

The `*` group is a long, specific deny-list rather than a blanket refusal. What
matters for a stock read:

```
Disallow: /gp/product/product-availability
Disallow: /dp/product-availability/
Disallow: /gp/offer-listing/
Allow: /gp/offer-listing/B000
Allow: /gp/offer-listing/9000
```

The bare product page path — `/dp/<ASIN>` — carries **no** `Disallow`, and there
is no rule matching `/dp/` or `/dp/$` anywhere in the `*` group. So a naïve
robots.txt reading says the product page is fair game. But the two paths that most
directly answer *"is this in stock, and from whom"* — `product-availability` and
the buy-box `offer-listing` — are explicitly closed, with a narrow legacy
exception for two ASIN prefixes.

**So robots.txt is narrower than the Conditions of Use, and the two disagree.**
robots.txt would permit fetching `/dp/<ASIN>` and reading whatever it contains;
the Conditions of Use forbid collecting product listings and prices by any means.
Where they disagree, the Conditions of Use are the document Amazon asks you to
agree to by using the site, and the narrower technical file does not license what
the broader written one refuses. Reading `/dp/` because robots.txt forgot to
mention it, while the ToU names prices explicitly, is precisely the "respects
robots.txt while working around the ToU" posture that
`.planning/phases/03-the-hard-two/03-CONTEXT.md` locks this project out of.

There is no `Sitemap:` directive in the file, so there is not even a sanctioned
discovery path of the kind Nintendo publishes.

### Rung 2 evaluated against the fresh-clone rule — and it has moved since anyone last looked

`.planning/REQUIREMENTS.md`'s non-functional requirement is that a retailer's
PRIMARY path must work for someone who clones this repo and adds no credentials;
a credential needing manual approval, a paid domain or a commercial agreement is
a footnote, not support. Best Buy's row is the precedent — its API is real, works
well, and is documented as an *optional* upgrade for exactly this reason.

Amazon fails that test harder than Best Buy does, and the first thing to record
is that **the API this repo would have reached for no longer exists**:

> The Amazon Product Advertising API 5.0 (PA-API 5) has been deprecated and is
> being replaced by the Creators API. […] Applications that continue to call
> PA-API 5 receive an HTTP 403 Forbidden response with an
> `AccessDeniedException`.

The successor, the Creators API, states its onboarding in two steps:

> **1. Sign up as an Amazon Associate.** First, you need to become an Amazon
> Associate. The Associates Program is free to join and enables you to monetize
> your traffic through affiliate commissions.
>
> **2. Register for Creators API.** Once you have an Amazon Associates account,
> you can register for the Creators API to get your API credentials (Access Key
> and Secret Key).

And access is regional and approved rather than issued:

> You will need a valid Partner Tag for the target marketplace and **Creators API
> access approved** in that region.

The FAQ's own account-verification advice names what an Associates account
entails — "if you can access payment method update and **tax interview** pages
for selected store then you are primary owner of the store".

So the rung-2 credential requires: an affiliate account governed by the
Associates Operating Agreement (a commercial agreement), a completed tax
interview, a payment method, a Partner Tag, and a per-region approval. A person
cloning this repo to watch one $54.99 accessory cannot obtain that, and should
not have to enter a commercial relationship with a retailer to check whether it
has something in stock. **Rung 2 is closed against the fresh-clone rule** — and
it would be closed even for someone who had all of it, because the Conditions of
Use above are not suspended by holding an Associates account. The Creators API is
a sanctioned path for affiliate publishers to *promote* products, not a
back-channel around the clause that forbids collecting prices.

### What was NOT done, and why

- **No product page was ever requested.** Not at rung 1, not at rung 3, not
  once. The Conditions of Use were read first precisely so this sentence could
  be written: **bot-y makes no requests to amazon.com.** There is no watch in
  `config/products.yaml`, no `FIRST_PARTY["amazon"]` entry, no dispatch branch
  and no fixture under `tests/fixtures/amazon/`. `amazon` remains in
  `boty.retailers.MARKETPLACES` — it is the archetypal buy-box marketplace and
  that entry is a statement about the retailer, not a claim to support it.
- **No transport work at all.** This is the difference from Pokémon Center,
  which cost ten probes across two transports and two WAF vendors before a desk
  review of its Terms produced the reason that actually settled it. Here the
  reading came first, so nothing was spent finding out how well-defended a page
  is that we would not be entitled to read either way. `.planning/ROADMAP.md`
  asks for reachability to be established "cheaply *before* investing in an
  adapter"; six policy reads is as cheap as that gets.
- **The Creators API was not signed up for.** Rung 2 exists on paper and the
  fresh-clone rule closes it — see above. Obtaining the credential personally
  would have made *this host* able to read Amazon while every clone of this repo
  could not, which is a footnote in the README rather than support, and the
  clause forbidding collection of prices is not suspended by holding one anyway.
- **The `/dp/<ASIN>` gap in robots.txt was not walked through.** It is real: the
  bare product path carries no `Disallow`. Taking it because the narrower
  technical file omits it, while the broader written one names prices
  explicitly, is the posture `03-CONTEXT.md` locks this project out of.

### If somebody revisits this later

**Do not re-probe.** There is nothing to re-probe: no wall was measured, so
there is no wall that could weaken. Periodically retrying a retailer whose terms
forbid automated interaction — waiting for enforcement to lapse, or for a
fingerprint to start working — is exactly the behaviour this project should not
have, and here there is not even the excuse of a technical question left open.
A clean HTTP 200 from `/dp/<ASIN>` would prove only that we had been rude
successfully.

**What would actually change this** is Amazon saying something different. A
product-availability signal a non-commercial user can subscribe to; a Creators
API tier that does not require an affiliate relationship and whose licence
permits reading stock for personal use; or a revision of the LICENSE AND ACCESS
clause that stops naming prices. Any of those is a genuine rung 2 and would be
worth wiring up the same afternoon. The retrieval date and the `Last updated`
header above are recorded so a future reader can tell at a glance whether the
document they are looking at is the one this verdict was based on.

### Why this is the plan succeeding

The roadmap's criterion for this retailer is "Amazon reports stock, **or** the
support matrix records what was tried and why it failed." This is the second
branch, and it is the better one to land on: a written prohibition is a more
durable finding than a wall, because a wall can fall and this cannot. Nobody has
to re-derive it in six months, and nobody has to wonder whether a different TLS
fingerprint would have worked. It would have.

It costs the phase its fifth retailer unless Target lands — see `QUESTIONS.md`.
That is recorded rather than papered over: no Amazon watch, and no substitute
retailer added to move the count. `scripts/evidence_check.py`, added by this same
plan, is what makes that shortfall mechanically impossible to hide later.

"""

_PRE_031_TARGET = """\
## Target (target.com)

**Probed:** 2026-08-03, from danserver over a residential connection.
**Transport:** `curl` — a one-off, human-shaped read of two public policy pages
and two `robots.txt` files. **`boty.fetch.get` was never pointed at target.com,
no browser was ever started against it, and no product page was requested at any
point in this phase.**

**Verdict: REFUSED**

Rung 4, and — as with Amazon — the decisive reason is written rather than
technical. Target's Terms & Conditions prohibit this three separate ways, and
one of the three has no commercial-use qualifier to argue about. The ladder was
never walked, because the question "may we request this at all" was answered
before any request whose legitimacy would have depended on the answer.

This is the outcome that costs the phase its fifth retailer. It is recorded as
that rather than padded — see the bottom of this section, and `QUESTIONS.md`.

### What was retrieved

| Requested | Result |
|---|---|
| `https://www.target.com/c/terms-conditions/-/N-4sr7p` | **HTTP 200**, 374,015 B, `text/html; charset=utf-8`. **The wrong document** — node `4sr7p` is the *Privacy Policy* (`"canonical_url":"/c/target-privacy-policy/-/N-4sr7p"`, `"seo_h1":"Target Privacy Policy"`), despite the `terms-conditions` slug in the requested path. Recorded rather than quietly dropped; the correct node id was then read out of this page's own `children` list instead of guessed a second time |
| `https://www.target.com/c/terms-conditions/-/N-4sr7l` | **HTTP 200**, 471,173 B, `text/html; charset=utf-8`, no redirect. `"seo_h1":"Terms & Conditions"`, `"canonical_url":"/c/terms-conditions/-/N-4sr7l"`. Document header reads `LAST UPDATED: April 15, 2026` |
| `https://www.target.com/robots.txt` | **HTTP 200**, 3,226 B, `text/plain`, 122 lines, **one** `User-agent` group |
| `https://redsky.target.com/robots.txt` | **HTTP 200**, 41 B, `text/plain;charset=UTF-8`. The whole body is three lines |

**Four requests in total, spaced ≥15 s apart, no retries, no refusals, and every
one of them HTTP 200.** Two to a public policy page, two to the files on the
internet whose entire purpose is to be fetched by an automated agent. **Zero to
a product page. Zero from bot-y.** The politeness budget for this plan was 12
requests; 4 were spent, all on documents, and the remaining 8 were not needed
because the first document settled it.

Note the first row: the URL `03-02-PLAN.md` names as the starting point,
`/c/terms-conditions/-/N-4sr7p`, serves Target's Privacy Policy. The Terms &
Conditions live one node over at `N-4sr7l`. Both are recorded because a future
reader following the plan's URL would otherwise quote the wrong document and
find no prohibition in it.

### The operative clauses, quoted in full

All from the Terms & Conditions at
`https://www.target.com/c/terms-conditions/-/N-4sr7l`, retrieved **2026-08-03**,
document header `LAST UPDATED: April 15, 2026`. Whole sentences are reproduced
so a future reader can judge their scope rather than trusting this document's
reading of them.

**1. The Introduction, which is what makes a bot a party to these terms at all:**

> BY ACCESSING OR OTHERWISE USING THE SITE YOU AGREE TO THESE TERMS &
> CONDITIONS. **Any person or entity who interacts with the Site through the use
> of crawlers, robots, browsers, data mining or extraction tools, or other
> functionality, whether such functionality is installed or placed by such person
> or entity or a third party, is considered to be using the Site.** If at any
> time you do not accept all of these Terms & Conditions, you must immediately
> stop using the Site.

That sentence is unusually direct and it forecloses the obvious objection. A
scraper does not click "I agree"; Target has written down that operating one *is*
using the Site, and using the Site *is* agreeing. There is no version of pointing
bot-y at target.com that is outside these terms.

**2. `Unlawful or Prohibited Uses` — three of the "YOU MAY NOT" bullets:**

> Whether on behalf of yourself or on behalf of any third party, YOU MAY NOT:
> Make any commercial use of the Site or its Content, including making any
> collection or use of any product listings, descriptions, prices or images; […]
> **Use or attempt to use any engine, software, tool, agent, data or other device
> or mechanism (including browsers, spiders, robots, avatars or intelligent
> agents) to navigate or search the Site other than the search engine and search
> agents provided by Target, generally publicly available browsers, or approved
> Agentic Commerce Agents;** […] **Make any use of data extraction, scraping,
> mining or other data gathering tools, or create a database by systematically
> downloading or storing Site content, or otherwise scrape, collect, store or use
> any Content, account information, product listings, descriptions, prices or
> images, except pursuant to the limited license granted by these Terms &
> Conditions;**

**3. The `Agentic Commerce and Delegated Access` section**, which is new since
anyone last looked at this file and which closes the one door a 2026 reader might
think had opened:

> The terms in this section apply if you expressly authorize an agent powered
> through AI ("Agentic Commerce Agent") to access and perform certain functions
> in your Target account on your behalf. **Only Agentic Commerce Agents expressly
> approved by you and by Target are considered Agentic Commerce Agents. Other
> automated or unauthorized agentic tools are expressly prohibited.**

### Reading those clauses honestly, including where they do not bite

Two of the three prohibitions have arguable edges, and this record is worth more
if it says so rather than stacking everything up as decisive.

- **The commercial-use bullet does not obviously reach bot-y.** It forbids
  "**any commercial use** of the Site or its Content, including making any
  collection or use of any product listings, descriptions, prices or images". A
  personal restock monitor is not commercial use, so that bullet is not the one
  that settles this. (Amazon's equivalent clause *is* decisive, because Amazon
  writes the listings-and-prices carve-out as an exclusion *from* the personal,
  non-commercial licence rather than as a commercial-use prohibition. The two
  read similarly and are structured differently.)
- **The navigation bullet has a carve-out that might cover rung 3.** It permits
  "generally publicly available browsers", and rung 3 drives a real, publicly
  available Chrome. A determined reading could put headless Chrome inside that
  carve-out — though the same bullet names "robots" and "intelligent agents" in
  its prohibition, and an unattended process polling a product page every five
  minutes is plainly the thing being described. Call it arguable rather than
  settled.

**The third bullet has no such edge, and it is the one that decides this.** It is
not qualified by commercial use, it names no permitted-tool carve-out, and it
prohibits four things bot-y does by definition:

1. "Make any use of **data extraction, scraping, mining or other data gathering
   tools**" — that is a description of this program.
2. "create a database by **systematically downloading or storing Site content**"
   — `boty.fixtures.capture` writes retailer HTML to disk; `state.json` stores a
   per-watch availability and price history.
3. "otherwise **scrape, collect, store or use any Content** […] **product
   listings, descriptions, prices or images**" — availability and price are the
   only two fields bot-y reads, and it stores both.
4. The verb "**use**" in that list is the widest of them. Even a read that
   persisted nothing at all would still be *using* a price.

**The `except pursuant to the limited license` carve-out closes rather than
opens.** The licence it points at is granted in the `License and Access` section
immediately above:

> Target grants you a limited license to access and make personal use of the Site
> and the Content for NONCOMMERCIAL PURPOSES ONLY and **only to the extent such
> use does not violate these Terms & Conditions including, without limitation,
> the prohibitions listed in the "UNLAWFUL OR PROHIBITED USES" section of these
> Terms & Conditions**. You may download, print and copy Content for personal,
> noncommercial purposes only, provided you do not modify or alter the Content in
> any way, delete or change any copyright or trademark notice, or violate these
> Terms & Conditions in any way.

So the exception is circular by construction: the prohibition permits what the
licence allows, and the licence allows nothing the prohibition forbids. The
circle closes against us. bot-y's use being personal and non-commercial gets it
past the *first* condition of that licence and straight into the second.

### robots.txt — permissive, and it disagrees with the Terms

The same shape as Amazon and Pokémon Center, and the disagreement is sharper here
than at either: reading `www.target.com/robots.txt` alone would have produced not
just a different answer but an *encouraging* one.

The file is 122 lines with exactly **one** `User-agent` group — `*`. There are no
named-bot blocks at all: no `GPTBot`, no `ClaudeBot`, no `Scrapy`, nothing of the
kind Amazon lists 99 of. The `Disallow` list is a long, specific set of legacy
WebSphere endpoints, checkout and account paths, and search/facet URLs:

```
Disallow: /s?
Disallow: /cart
Disallow: /account/
Disallow: /shop/
Disallow: /pl/
Disallow: /p/premium-registry
```

**The product-detail path `/p/` is not disallowed.** The only `/p/` rule in the
file is `/p/premium-registry`, and `/p/<slug>/-/A-<TCIN>` — the exact URL form a
stock read needs — carries no rule matching it anywhere in the group. Target goes
further and *publishes the map*:

```
Sitemap: https://www.target.com/sitemap_pdp-index.xml.gz
Sitemap: https://www.target.com/sitemap_keywords-index.xml.gz
Sitemap: https://www.target.com/sitemap_taxonomy-categories-index.xml.gz
Sitemap: https://www.target.com/sitemap_taxonomy-brand-index.xml.gz
Sitemap: https://www.target.com/sitemap_facet-categories-index.xml.gz
Sitemap: https://www.target.com/sitemap_stores-index.xml.gz
```

`sitemap_pdp-index.xml.gz` is a product-detail-page index — a sanctioned
discovery path of exactly the kind Nintendo publishes and Amazon does not, and
the very thing that would have solved the TCIN-discovery problem
`.planning/STATE.md` records Phase 2 stopping on.

**So robots.txt is materially broader than the Terms & Conditions, and the two
disagree.** robots.txt would permit fetching `/p/<slug>/-/A-<TCIN>`, and hands
you an index to find them with; the Terms forbid using data-gathering tools on
the Site and forbid collecting, storing or using prices at all. Where they
disagree, the Terms are the document Target says you agree to by operating a
crawler against the Site, and a narrower technical file does not license what the
broader written one refuses. Taking the `/p/` gap because robots.txt omits it,
while the Terms name prices explicitly, is precisely the "respects robots.txt
while working around the ToU" posture that
`.planning/phases/03-the-hard-two/03-CONTEXT.md` locks this project out of — and
it is the same call this repo already made for Amazon's `/dp/<ASIN>` gap eight
hours earlier.

### Rung 2 — RedSky, settled here rather than left to a ladder walk

`redsky.target.com` is Target's own internal aggregation API
(`/redsky_aggregations/v1/web/pdp_client_v1?tcin=…&key=…`). It is not a
documented public product, has no signup, no terms of service of its own and no
published contract. It is closed **four** separate ways, and the first one is
mechanical:

**1. Its `robots.txt` disallows the entire host, for every agent.** The whole
file, all 41 bytes of it:

```
User-agent: *
Crawl-delay: 1
Disallow: /
```

No `Allow`, no exceptions, no named groups. This is the same standard Pokémon
Center's `/cortex` endpoints were held to, and Target's version is broader than
Pokémon Center's — that file closed five specific paths, this one closes the
host. Reading it would mean taking data the retailer has asked in writing not to
take, to power a monitor whose entire pitch is that its readings are
trustworthy.

**2. The `key` parameter fails the fresh-clone rule.** `.planning/REQUIREMENTS.md`
requires a retailer's PRIMARY path to work for someone who clones this repo and
adds no credentials. RedSky's `key` is not issued to anybody: there is no
developer portal, no application, no approval. The only way to obtain one is to
lift the constant out of Target's own front-end JavaScript. That is not "a
credential a fresh clone cannot get" in the way Best Buy's API key or Amazon's
Partner Tag are — it is worse. Best Buy's key is a real credential this project
could hold and chose to document as optional; RedSky's is Target's internal
secret, and using it means presenting yourself to Target's API as Target's own
website. There is no reading under which that is sanctioned access.

**3. The Terms above cover it regardless of host.** They govern "the Target
website located at www.target.com **and all other sites, mobile sites, services,
applications, platforms and tools where these Terms & Conditions appear or are
linked** (collectively, the 'Site')", and the prohibition is on collecting prices
by any means, not on a particular hostname.

**4. It is CAPTCHA-gated in practice.** `.planning/STATE.md` records from earlier
work that RedSky answers with a CAPTCHA even when driven from a warmed cookie
session. That is a separate, technical fact and it belongs in the record — but it
is the least important of the four, because it is the only one that could change.
The other three cannot.

### The decision this leaves for the ladder walk

Written down explicitly, because the next step branches on it mechanically and a
reader should be able to check the branch was taken correctly.

**The Terms contain a written prohibition on automated access.** The bullet that
establishes it is quoted in full above and is not qualified by commercial use:
*"Make any use of data extraction, scraping, mining or other data gathering
tools, or create a database by systematically downloading or storing Site
content, or otherwise scrape, collect, store or use any Content, account
information, product listings, descriptions, prices or images…"*

So the verdict is `**Verdict: REFUSED**`, the primary reason is that clause, and
**no request may be made to any target.com product page at any rung** — not at
rung 1 to see whether Akamai answers, not at rung 3, not to discover a TCIN, and
not "just to record an observation". Rung 1 is closed by the Terms; rung 2 is
closed four ways above; rung 3 is closed by the same Terms as rung 1 and adds
nothing a prohibition can be argued out of. There is no rung left to walk.

### The ladder walk, and the fact that it did not happen

That branch was taken. **No rung was walked, because the branch above closed all
three of them before any transport work began.**

The request count for this retailer across the whole of Phase 3 is therefore
**4**, every one of them a policy document or a `robots.txt`, all listed in the
table at the top of this section. The plan's politeness budget was 12 requests at
≥15 s spacing with a 120 s backoff before any single retry and a hard stop after
two consecutive refusals. None of the retry machinery was reached: there were no
refusals, because there was nothing to be refused from. **`boty.fetch.get` was
never called with a target.com URL, `boty.browser.fetch_rendered` was never
called at all, and `boty capture-fixture` was never run.**

**Controls before and after.** There was no probing to bracket — the REFUSED
branch makes no product requests — but both runs are recorded anyway, the same
way `03-01` recorded them, because "we would have noticed" is not a control:

```
control check: PASS — 4/4 controls in stock
  in_stock      gamestop  CONTROL — PS5 console                $549.99  ld+json: InStock from GameStop
  in_stock      walmart   CONTROL — Great Value whole milk       $2.42  __NEXT_DATA__: IN_STOCK from Walmart.com
  in_stock      bestbuy   CONTROL — Pokémon Let's Go, Pikach    $59.99  ld+json: InStock from Best Buy
  in_stock      nintendo  CONTROL — Nintendo HDMI cable          $7.99  ld+json: InStock from Nintendo of America Inc.
```

Byte-identical before and after — two standalone runs under the service's own
`EnvironmentFile`, and a third inside `make verify` at the close of this plan.
The GameStop control needed one retry on the *first* run only
(`fetch failed: HTTP 403`, retried automatically and read `InStock`), which is
the script's ordinary backoff behaviour and not a Target finding; the second run
needed none. Dan's monitor was never at risk: no defended endpoint was touched.

**`BLOCK_PHRASES` was not exercised, and that is worth saying out loud.** Phase 2
added `sec-if-cpt-container` and `scf-akamai-protected-by` to
`boty.fetch.BLOCK_PHRASES` *specifically* because Akamai fronts Target and a
Target refusal at HTTP 200 would otherwise have surfaced as "no structured stock
data found (page shape changed?)". Those markers were re-verified against live
Kohl's bytes on 2026-08-03 and they remain correct — but this section provides
**no** evidence for or against them, because no Target page was ever fetched to
put them in front of. Their justification is still the Kohl's re-probe recorded
at the bottom of this file, and nothing here strengthens or weakens it.

### What was NOT done, and why

- **No product page was ever requested.** Not at rung 1, not at rung 3, not
  once. The Terms were read first precisely so this sentence could be written:
  **bot-y makes no requests to target.com.** Four `curl` requests to policy
  documents and `robots.txt`, and nothing else, ever.
- **No TCIN discovery was attempted**, even though robots.txt publishes the PDP
  sitemap that would have made it easy and even though this is the exact problem
  `.planning/STATE.md` records Phase 2 giving up on. Finding the GO Plus +'s TCIN
  would have been a satisfying answer to a question that stopped mattering the
  moment the Terms were read. Whether Target stocks the product is therefore
  **not established here** — and it does not need to be, because a watch could
  not ship either way. This is a deliberate non-finding, unlike Best Buy's, which
  is a disproof.
- **`FIRST_PARTY["target"]` was NOT widened**, and the live `offers.seller.name`
  string was not observed, because observing it would have required fetching a
  product page. See the note below on what that leaves in the code.
- **No fixture was captured**, so `tests/fixtures/target/` does not exist and the
  CR-02 identity-leak guard had nothing new to inspect. Target is Akamai-fronted,
  the same echo shape that froze this repo's public IP and EdgeScape geolocation
  into a committed fixture in Phase 2, so the safest number of rung-3 Target
  captures in a public repo is the one this plan produced.
- **No watch is in `config/products.yaml`.** No `retailer: target` entry, no
  control, no `check_html_browser`, and no new arm in `boty.cli._make_checker`.
- **`target` remains in `boty.retailers.MARKETPLACES`.** Target Plus is a real
  third-party marketplace; that entry is a statement about the retailer, not a
  claim to support it — the same call `03-01` made for `amazon`.

### The sharp edge left in the code, and why it is safe to leave

`boty/retailers.py:31` carries `"target": {"target"}` in `FIRST_PARTY` and
`:54` lists `target` in `MARKETPLACES`. That combination has a real hazard: if
Target's markup names its seller anything other than exactly `target` once
lowercased — `"Target Corporation"`, `"Target.com"` — then `_pick`'s `named` list
is empty, `unattributed` is forced empty by the `MARKETPLACES` membership, and
`_verdict_from_html` falls through to `:177` and returns a **confident
OUT_OF_STOCK** with detail `"N offer(s) via ld+json, none first-party"` on a page
it read perfectly.

That hazard is **unreachable in this tree**, because nothing dispatches a Target
watch: `Config.load` yields no watch with `retailer == 'target'`, so no code path
ever passes `"target"` to `_pick`. The entry is dormant, not live. It was left in
place rather than deleted for the same reason `amazon` stays in `MARKETPLACES` —
it records a true fact about the retailer — and removing it would have been a
change to `boty/retailers.py` in a plan whose whole finding is that no code
change is warranted.

If somebody ever does register Target, **that allow-list entry is a guess**,
never observed on a live page, and it must be replaced with the real
`offers.seller.name` string before a control can go green. Note that the failure
would be loud rather than silent: `boty.monitor.assess_health:78` fails any
retailer whose control does not read IN_STOCK, so seller-string drift on a Target
control reddens the `controls` stage and takes `make verify` non-zero within a
cycle. The control path is the drift detector, and it already works.

### Was Target reachable? — unknown, and deliberately so

This section records no HTTP status from a product page, no byte count from one,
and no observation about Akamai, because none was collected. The two policy pages
and both `robots.txt` files returned clean HTTP 200s from `curl` with no
challenge, which says something about `www.target.com`'s posture toward a plain
document fetch and **nothing** about `/p/`. `.planning/STATE.md`'s note that
"product pages fetch clean but no valid `www` TCIN was ever found" is prior work,
not an observation from this phase, and it is not promoted to one here.

That gap is the correct shape for a rung-4-by-terms finding, and it is the same
shape as Amazon's. A REACHABLE verdict needs observations; a REFUSED-by-written-
prohibition verdict needs the prohibition, and manufacturing transport evidence
to make the section look fuller would mean making exactly the requests the
section's own conclusion says we should not make.

### If somebody revisits this later

**Do not re-probe.** There is nothing to re-probe: no wall was measured, so there
is no wall that could weaken. A clean HTTP 200 from `/p/<slug>/-/A-<TCIN>` would
prove only that we had been rude successfully. This is the same instruction the
Amazon section carries, for the same reason.

**What would actually change this** is Target saying something different: a
product-availability signal a non-commercial user can subscribe to; a RedSky tier
with published terms and an issued key; an "approved Agentic Commerce Agent"
programme that a personal restock monitor can join; or a revision of the
`Unlawful or Prohibited Uses` section that stops naming prices and data-gathering
tools. Any of those is a genuine rung 2 and would be worth wiring up the same
afternoon. The retrieval date and the `LAST UPDATED: April 15, 2026` header are
recorded so a future reader can tell at a glance whether the document they are
looking at is the one this verdict was based on.

**The `Agentic Commerce` section is the one to watch.** It is the newest text in
the document and it is the only place Target contemplates an automated agent
acting for a person at all. Today it is scoped to authenticated account actions —
carts, orders, returns — and it explicitly prohibits everything else. If that
scope ever widens to reading a public product page on a person's behalf, this
verdict should be revisited on purpose rather than by accident.

### Why this is the plan succeeding

The roadmap's criterion for this retailer is "Target reports stock, **or** the
support matrix records what was tried and why it failed." This is the second
branch. It is the branch that was under the most pressure to be the first one:
`03-01` settled Amazon at rung 4 the same day, so criterion 5 — five working
retailers — rested on Target alone, and a REACHABLE here was the only thing that
would have met it.

It is met by not being met. **The count stays at four** — gamestop, walmart,
bestbuy, nintendo — and phase criterion 5 is recorded unmet in `QUESTIONS.md`
rather than padded with a retailer whose own terms forbid the reading.
`scripts/evidence_check.py`, shipped by `03-01` for exactly this moment, is what
makes that shortfall mechanically impossible to hide later: rule 2 requires every
roadmap retailer to be configured *or* to carry `**Verdict: REFUSED**` in this
file, and rule 3 requires a short count to be consistent with the verdicts behind
it.

"""


# --------------------------------------------------------------------------
# rule 6 — the line form and its body predicate
# --------------------------------------------------------------------------

_REFUSED_NO_OBSERVATION = (
    "Probed 2026-08-03. Their terms forbid it, so we did not try.\n\n"
    "**Verdict: REFUSED**\n"
)


def _refused_with(*observations: str) -> str:
    """A REFUSED section carrying exactly these refusal-observation lines."""
    lines = "".join(f"{line}\n\n" for line in observations)
    return f"Probed 2026-08-03.\n\n{lines}**Verdict: REFUSED**\n"


def _rule_six(problems: list[str]) -> list[str]:
    return [p for p in problems if p.startswith("rule 6")]


def _phase_over(tmp_path: Path, sections: list[tuple[str, str]]) -> list[str]:
    """Run `check_phase` over a synthetic tree with NOTHING configured.

    Nothing configured is what puts every roadmap retailer in front of rules 2
    and 6 at once, so each case below supplies a section for all seven and
    varies only the one under test.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)  # several cases want a second tree
    config = _write_config(tmp_path, [])
    evidence = _write_evidence(tmp_path, sections)
    fixtures = _write_fixtures(tmp_path, [])
    return evidence_check.check_phase(config, evidence, fixtures)


def _seven(under_test: tuple[str, str]) -> list[tuple[str, str]]:
    """All seven roadmap retailers, one of them replaced by the case at hand.

    The other six are REACHABLE rather than REFUSED so that rule 6 has exactly
    one section to speak about — otherwise every message below would have to be
    filtered by retailer name and a typo in the rule would hide behind a match
    on the wrong row.
    """
    sections = [
        (f"{display} (example.test)", _REACHABLE)
        for display in evidence_check.ROADMAP_RETAILERS.values()
        if not f"{display} (example.test)".startswith(under_test[0].split(" (")[0])
    ]
    return [under_test, *sections]


def test_a_refused_section_with_no_refusal_observation_fails_rule_six(tmp_path: Path) -> None:
    """The base bar, and the shape Phase 3 shipped twice.

    A written prohibition, a verdict, and no record of anything ever having been
    requested. Every gate in this tree passed that tree.
    """
    problems = _phase_over(
        tmp_path, _seven(("GameStop (example.test)", _REFUSED_NO_OBSERVATION))
    )

    hits = _rule_six(problems)
    assert len(hits) == 1, problems
    assert "GameStop" in hits[0]
    assert "REQ-07a" in hits[0]


def test_one_observation_clears_the_base_bar_but_not_the_hard_two_bar(
    tmp_path: Path,
) -> None:
    """Both halves in one test, because the difference IS the rule.

    A non-hard-two retailer that recorded one measured refusal has done what
    REQ-07a asks. A hard-two retailer has not: dropping `target` or `amazon` is
    what decides whether this project reaches five retailers, so it takes a
    walked ladder rather than one failed request.
    """
    one = _refused_with("**Refusal observed (rung 1):** HTTP 503 from the edge.")

    ordinary = _rule_six(_phase_over(tmp_path, _seven(("GameStop (example.test)", one))))
    assert ordinary == [], ordinary

    hard = _rule_six(
        _phase_over(tmp_path / "hard", _seven(("Amazon (example.test)", one)))
    )
    assert len(hard) == 1, hard
    assert "hard two" in hard[0]
    assert "at least one at rung 3" in hard[0]


def test_two_rung_one_observations_still_fail_the_hard_two_bar(tmp_path: Path) -> None:
    """Count alone is not the bar — the rung-3 attempt is the expensive half.

    Two rung-1 attempts 20 s apart cost a minute. The rung-3 one costs a browser
    and is the one that distinguishes "the cheap transport was refused" from
    "the retailer will not serve us at all".
    """
    body = _refused_with(
        "**Refusal observed (rung 1):** HTTP 503, 812 B.",
        "**Refusal observed (rung 1):** HTTP 503, 812 B again, 40 s later.",
    )

    hits = _rule_six(_phase_over(tmp_path, _seven(("Target (example.test)", body))))

    assert len(hits) == 1, hits
    assert "rung(s) 1" in hits[0], hits[0]


def test_two_observations_including_a_rung_three_clear_the_hard_two_bar(
    tmp_path: Path,
) -> None:
    """The branch both 03.1 retailer plans wrote their refusal case to."""
    body = _refused_with(
        "**Refusal observed (rung 1):** HTTP 503, 812 B.",
        "**Refusal observed (rung 1):** HTTP 503, 812 B again, 40 s later.",
        "**Refusal observed (rung 3):** rendered and refused, 1,085 B.",
    )

    assert _rule_six(_phase_over(tmp_path, _seven(("Target (example.test)", body)))) == []


def test_a_reachable_section_carrying_historical_refusal_lines_is_clean(
    tmp_path: Path,
) -> None:
    """Target's shape after 03.1-02, and Amazon's after 03.1-03.

    Both were refused at *some* rung on the way to one that worked — Target at
    rung 2 by a `Disallow: /`, Amazon once by a cadence throttle — and both kept
    those lines rather than deleting them, because they are the measurements the
    verdict was revised through.

    Rule 6 asking about them would punish the most thorough records in the file
    and would push the next author towards deleting evidence to green a gate,
    which is the precise opposite of what this file is for.
    """
    body = (
        "Probed 2026-08-03.\n\n"
        "**Refusal observed (rung 1):** HTTP 503, 812 B — superseded, see below.\n\n"
        "**Verdict: REACHABLE (rung 3)**\n"
    )

    assert _rule_six(_phase_over(tmp_path, _seven(("Target (example.test)", body)))) == []


def test_an_unprobed_section_is_not_asked_for_an_observation(tmp_path: Path) -> None:
    """An UNPROBED verdict is already SAYING nobody has looked.

    Demanding an observation from it would make the honest state unrepresentable
    and leave exactly two ways to green the tree: ship a detector, or invent a
    refusal. That is the failure mode `UNPROBED_RE` was added against, and rule 6
    must not reintroduce it one rule along.
    """
    body = "Newly in scope.\n\n**Verdict: UNPROBED (scoped 2026-08-01)**\n"

    problems = _phase_over(tmp_path, _seven(("Amazon (example.test)", body)))

    assert _rule_six(problems) == [], problems


@pytest.mark.parametrize(
    "line",
    [
        "**Refusal observed:** HTTP 503",
        "**Refusal observed (rung 4):** HTTP 503",
        "**Refusal observed (rung 1)** HTTP 503",
        "**refusal observed (rung 1):** HTTP 503",
        "**Refusal observed (rung 1):** ",
    ],
    ids=["no-rung", "rung-4", "no-colon", "lower-case", "empty-body"],
)
def test_a_malformed_refusal_line_does_not_satisfy_rule_six(
    tmp_path: Path, line: str
) -> None:
    """Five near misses. The spacing and the casing are load-bearing.

    Each of these looks like a refusal observation to a human and is invisible
    to the gate — so each must fail loudly rather than be silently ignored,
    which is why the base-bar message names the exact literal form.
    """
    assert evidence_check.refusal_observations(line) == []

    problems = _phase_over(tmp_path, _seven(("GameStop (example.test)", _refused_with(line))))

    assert len(_rule_six(problems)) >= 1, problems


def test_a_prose_only_body_is_rejected_and_named_as_such() -> None:
    """The test that stops rule 6 being satisfiable by writing the sentence.

    `**Refusal observed (rung 1):** Amazon refused us` clears the anchor
    perfectly. It carries no status code, no byte count and no matched block
    phrase — nothing that could only have come from an attempt — and the
    anchored-regex-only version of this rule would have counted it. That version
    was the obvious one and it was in this plan's own text before review.
    """
    prose = "**Refusal observed (rung 1):** Amazon refused us"

    assert evidence_check.refusal_observations(prose) == []
    assert evidence_check.unmeasured_refusal_lines(prose) == [prose]


@pytest.mark.parametrize(
    "body",
    [
        "HTTP 503 from the edge",
        "not served — 314,757 B of challenge page",
        "the response matched `pardon our interruption`",
    ],
    ids=["status-code", "byte-count", "block-phrase"],
)
def test_a_body_citing_a_measurement_is_accepted(body: str) -> None:
    """The predicate watched in the other direction, one case per accepted form.

    The block-phrase case is read from `boty.fetch.BLOCK_PHRASES` rather than
    from a list retyped in the gate, so a phrase added to the transport is
    quotable here the same day — which matters, because 03.1-03 added one.
    """
    line = f"**Refusal observed (rung 2):** {body}"

    assert evidence_check.refusal_observations(line) == [line]
    assert evidence_check.unmeasured_refusal_lines(line) == []


def test_the_shipped_target_non_refusal_line_is_only_harmless_because_of_the_section_scope(
    tmp_path: Path,
) -> None:
    """The counterexample that already ships, pinned so nobody widens rule 6 into it.

    `docs/retailer-evidence.md` § Target carries, today, a real anchored refusal
    observation whose body says Target was **not** refused:

        **Refusal observed (rung 1):** not a block — **HTTP 200**, 314,757 B …

    The body predicate does not save us here and cannot: the line has a status
    code AND two byte counts, so it is exactly as "measured" as a genuine
    refusal. The only thing that keeps it harmless is that rule 6 reads REFUSED
    sections and Target is REACHABLE.

    So this test asserts both halves. Put that same line in a REFUSED section and
    the gate counts a non-refusal as evidence of a refusal — which is the failure
    the whole rule exists to prevent, arriving through its own grammar.
    """
    real_line = (
        "**Refusal observed (rung 1):** not a block — **HTTP 200**, 314,757 B "
        "and 318,690 B on two unrelated PDPs, **no `BLOCK_PHRASES` match**."
    )

    assert evidence_check.refusal_observations(real_line) == [real_line], (
        "the body predicate is not what makes this line safe — it clears it"
    )
    assert real_line.split("**Refusal observed")[1][:11] == " (rung 1):*", real_line

    reachable = _seven(
        (
            "Target (example.test)",
            f"Probed 2026-08-03.\n\n{real_line}\n\n**Verdict: REACHABLE (rung 3)**\n",
        )
    )
    assert _rule_six(_phase_over(tmp_path, reachable)) == [], (
        "rule 6 must not read a REACHABLE section"
    )

    refused = _seven(
        (
            "Target (example.test)",
            f"Probed 2026-08-03.\n\n{real_line}\n\n{real_line}\n\n**Verdict: REFUSED**\n",
        )
    )
    hits = _rule_six(_phase_over(tmp_path / "refused", refused))
    assert len(hits) == 1 and "rung 3" in hits[0], (
        "if rule 6 ever reads a REACHABLE section, this line becomes evidence "
        "of a refusal it explicitly records not happening — the only thing left "
        "stopping it is the hard-two rung-3 requirement, and Pokémon Center "
        "would not even have that"
    )


def test_a_refusal_line_inside_a_fenced_example_does_not_satisfy_rule_six(
    tmp_path: Path,
) -> None:
    """`strip_fences` runs before indexing, and this is why it has to.

    The natural way to document a line form is a fenced block using a real
    retailer's name. Counted as a record, that documentation would satisfy the
    rule it describes — verbatim the defect `strip_fences` was written for, one
    rule along.
    """
    body = (
        "Probed 2026-08-03. Their terms forbid it.\n\n"
        "The form to use here is:\n\n"
        "```\n"
        "**Refusal observed (rung 3):** HTTP 503, 812 B\n"
        "```\n\n"
        "**Verdict: REFUSED**\n"
    )

    hits = _rule_six(_phase_over(tmp_path, _seven(("GameStop (example.test)", body))))

    assert len(hits) == 1, hits
    assert "carries no" in hits[0]


# --------------------------------------------------------------------------
# The historical case — what the Phase 3 gate could not see
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("display", "literal"),
    [("Amazon", _PRE_031_AMAZON), ("Target", _PRE_031_TARGET)],
    ids=["amazon", "target"],
)
def test_the_gate_that_shipped_in_phase_three_could_not_tell_a_wall_from_a_desk_review(
    tmp_path: Path, display: str, literal: str
) -> None:
    """Rule 6 against the actual text Phase 3 shipped. Two retailers, one defect.

    These are the `## Amazon` and `## Target` sections verbatim from commit
    `339800e`, and every gate in this repository passed them. Both record
    `**Verdict: REFUSED**`; both state in terms that **no product page was ever
    requested**; Amazon's quotes the LICENSE AND ACCESS clause in full as the
    decisive reason. Between them that is 658 lines of careful, honest, entirely
    accurate writing containing not one observation about whether either page
    could be read.

    That is what REQ-07a forbids and what nothing enforced. Rule 6 reports a
    problem for each — which is the difference between a requirement and a gate,
    and the whole of what this rule is for.
    """
    assert "**Verdict: REFUSED**" in literal
    assert "no product page" in literal
    assert "Refusal observed" not in literal, (
        "the pre-03.1 text is supposed to contain no refusal observation at all "
        "— if this fires, the literal is not the text it claims to be"
    )

    heading, _, body = literal.partition("\n")
    sections = _seven((heading.removeprefix("## "), body))
    hits = _rule_six(_phase_over(tmp_path, sections))

    assert len(hits) == 1, hits
    assert display in hits[0]
    assert "REQ-07a" in hits[0]


def test_the_pre_phase_three_one_amazon_literal_still_carries_its_licence_clause() -> None:
    """The literal is the evidence, so its integrity is worth its own assertion.

    A truncated or hand-edited copy would still go red under rule 6 for the
    wrong reason, and the test above would pass while proving nothing. These
    three markers are the ones the section's argument actually rested on.
    """
    for marker in (
        "LICENSE AND ACCESS",
        "any collection and use of any product listings, descriptions, or\n> prices",
        "no product page was\nrequested at any point in this phase",
        "**`boty.fetch.get` was never pointed at amazon.com",
    ):
        assert marker in _PRE_031_AMAZON, marker


def test_rule_six_is_silent_on_the_real_shipped_tree() -> None:
    """The tree as it stands, including Pokémon Center's backfilled observations.

    Pokémon Center is the only retailer in scope still recorded REFUSED, and it
    is not one of the `HARD_TWO`, so rule 6 asks it for one observation. It
    carries four across two rungs — restated from the table that has been in the
    document since 2026-08-02 rather than newly claimed — so it clears the higher
    bar as well.
    """
    problems = evidence_check.check_phase(
        REPO_ROOT / "config" / "products.yaml",
        REPO_ROOT / "docs" / "retailer-evidence.md",
        REPO_ROOT / "tests" / "fixtures",
        strict=True,
    )

    assert _rule_six(problems) == [], problems
    assert problems == [], problems

    body = evidence_check.sections_for(
        "Pokémon Center",
        evidence_check.split_sections(
            (REPO_ROOT / "docs" / "retailer-evidence.md").read_text(encoding="utf-8")
        ),
    )[0]
    assert len(evidence_check.refusal_observations(body)) >= 2
    assert "3" in evidence_check.refusal_rungs(body)


def test_the_retailer_count_target_is_pinned_at_five_in_both_directions() -> None:
    """`TARGET_RETAILER_COUNT` is 5, and BOTH ways of moving it are defects.

    Six retailers ship as of Phase 3.1, so the obvious tidy-up is to raise the
    constant to 6 "to reflect reality". The ROADMAP forbids exactly that, in
    writing, and the reason is worth restating where someone editing the
    constant will see it: **five was chosen as the honest ceiling for the case
    where Amazon turns out to be unreachable.** Amazon landing is a fact about
    Amazon, not a promise about next month — if it walls us tomorrow the honest
    outcome is five again, and a gate set at six would fire on that. That is
    the Phase 2 rot in the opposite sign: a check that goes red when the truth
    is inconvenient teaches people to edit the check.

    Lowering it is the other failure and the more familiar one: at 4 the rule
    is satisfied by the tree that shipped before this phase, which is a gate
    that can no longer fail.

    Nothing pinned the constant until 2026-08-03; the phase verifier flagged
    that the rule was watched biting but the number it bites at was free to
    move. This is that pin.
    """
    assert evidence_check.TARGET_RETAILER_COUNT == 5, (
        "TARGET_RETAILER_COUNT moved. Raising it to match the six retailers that "
        "currently ship makes the gate fire on the honest five-retailer outcome "
        "the ROADMAP explicitly preserves; lowering it makes the gate satisfiable "
        "by the pre-Phase-3.1 tree. If this is a deliberate change, change the "
        "ROADMAP criterion first and say why here."
    )
