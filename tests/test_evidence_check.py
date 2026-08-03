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

        problems = evidence_check.check_phase(config, evidence)

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
            ["--phase", "--config", str(config), "--evidence", str(evidence)]
        )
        == 1
    )


def test_the_out_of_scope_message_names_the_retailer_and_points_at_the_roadmap(
    tmp_path: Path,
) -> None:
    config = _write_config(tmp_path, _SHIPPED + ["microcenter"])
    problems = evidence_check.check_phase(config, _full_evidence(tmp_path))

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
            ["--phase", "--config", str(config), "--evidence", str(evidence)]
        )
        == 1
    )

    problems = evidence_check.check_phase(config, evidence)
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

    problems = evidence_check.check_phase(config, evidence)
    assert len(problems) == 1
    assert "Target" in problems[0]
    assert "REFUSED" in problems[0]


def test_every_violation_is_reported_not_just_the_first(tmp_path: Path) -> None:
    """Fixing one gap only to be told about the next is how a gate gets muted."""
    config = _write_config(tmp_path, _SHIPPED + ["microcenter"])
    evidence = _write_evidence(tmp_path, [("Amazon (amazon.com)", _REFUSED)])

    problems = evidence_check.check_phase(config, evidence)

    # rule 1: microcenter out of scope. rule 2: pokemoncenter and target unrecorded.
    assert len(problems) == 3
    joined = "\n".join(problems)
    assert "microcenter" in joined
    assert "Pokémon Center" in joined
    assert "Target" in joined


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
            ["--phase", "--config", str(config), "--evidence", str(evidence)]
        )
        == 1
    )

    problems = evidence_check.check_phase(config, evidence)
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
            ["--phase", "--config", str(config), "--evidence", str(evidence)]
        )
        == 0
    )


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
            ["--phase", "--config", str(config), "--evidence", str(evidence)]
        )
        == 0
    )
    assert evidence_check.check_phase(config, evidence) == []


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

    problems = evidence_check.check_phase(config, evidence)

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
        evidence_check.check_phase(config, evidence)
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
    )

    assert problems == [], "the shipped tree fails its own honesty gate:\n  " + "\n  ".join(problems)
