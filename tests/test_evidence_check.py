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

_REFUSED = "Probed 2026-08-03. Refused at every rung.\n\n**Verdict: REFUSED**\n"
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
    config = _write_config(tmp_path, _SHIPPED + ["microcenter"])
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
    config = _write_config(tmp_path, _SHIPPED + ["microcenter"])
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
    config = _write_config(tmp_path, _SHIPPED + ["microcenter"])
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
    config = _write_config(tmp_path, _SHIPPED + ["target"])
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
    config = _write_config(tmp_path, _SHIPPED + ["target", "amazon"])

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
    config = _write_config(tmp_path, _SHIPPED + ["pokemoncenter"])
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
