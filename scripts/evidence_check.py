#!/usr/bin/env python3
"""The honesty gate over the evidence log and the shipped retailer set.

This exists because the previous version of this rule decayed into a gate that
could not fail, and nobody would have noticed.

02-04 gated the retailer count with a clause of the form: "five or more
retailers, OR `rung 4` appears in QUESTIONS.md and `**Verdict: REFUSED**`
appears in docs/retailer-evidence.md". It was correct the day it was written.
It stopped being correct the same day, because Pokémon Center's rung-4 finding
put BOTH of those substrings permanently into the tree. Re-used in Phase 3 it
is a clause satisfied by documents that predate the phase — worse than no gate
at all, because it still looks like one, and a green from it reads as evidence.

Two lessons are baked into what replaced it:

1. **Per-retailer, not per-document.** A substring search over
   `docs/retailer-evidence.md` is unusable on that file by construction: its
   own vocabulary preamble spells out both verdict strings so a reader knows
   the grammar. Any whole-file grep therefore passes against a document that
   records nothing. So this script splits the document into `## ` sections,
   drops everything above the first heading, and asks its questions of one
   retailer's section at a time.

2. **The count has a second padding door.** Reaching five retailers by adding
   one that is not in the roadmap's scope moves the counter without moving the
   goal. A control-only Micro Center was probed in Phase 2, found viable at
   rung 1 with a real control and a real fixture, and explicitly declined
   because it does not carry the Pokémon GO Plus + and could never alert on it.

WHY THE EXISTING ENFORCEMENT LAYERS DO NOT COVER THAT SECOND DOOR
-----------------------------------------------------------------
Three mechanisms already stop a *fake* padded retailer:

- `scripts/control_check.py` computes `configured - verified` before any
  request, so a watch with no control fails offline;
- `boty.monitor.assess_health` fails a retailer whose control cannot be read;
- `test_no_retailer_is_configured_without_a_page_we_have_actually_read`
  requires a captured fixture, and `boty.fixtures.capture` only writes one
  after a live fetch that was not blocked.

Every one of them passes a padded retailer that is entirely REAL — reachable,
controlled, fixtured — but cannot carry the product this project exists for.
That is the gap rule 1 below closes, and it is the only thing that closes it.

MODES
-----
`--retailer <display name>` asks one question: does this retailer's section
exist exactly once, and carry exactly one well-formed verdict line?

`--phase` asks whether the tree as a whole is telling the truth about its own
retailer count, via the three rules in `check_phase`.

`--config` and `--evidence` exist so the tests can point either mode at a
synthetic tree and watch it go red. A gate nobody has watched fail is not a
gate; the watching is `tests/test_evidence_check.py`.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Run from a checkout without installing: make the repo root importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boty.config import Config  # noqa: E402

#: Every retailer in the Retailer Scope table of `.planning/ROADMAP.md`, mapping
#: the `Watch.retailer` key to its display name.
#:
#: WHAT THIS CONSTANT IS FOR. It is the list of stores where a Pokémon GO Plus +
#: could genuinely appear. Reaching five retailers by adding a store that does
#: not carry the product moves the counter without moving the goal — Micro
#: Center is reachable, controllable and completely useless here for exactly
#: that reason, and it was declined in Phase 2 on those grounds. Admitting one
#: means editing this constant, which is a visible, reviewable change with a red
#: test attached, rather than a quiet line of YAML.
#:
#: EACH DISPLAY VALUE CARRIES TWO OBLIGATIONS, AND THEY ARE DIFFERENT MATCHES:
#:
#:   1. It must be a **prefix** of that retailer's `## ` heading in
#:      `docs/retailer-evidence.md`. The existing shapes are
#:      `## Nintendo (store.nintendo.com / …)` and
#:      `## Pokémon Center (pokemoncenter.com)` — a name, then a parenthetical.
#:   2. It must be the **exact** first-cell label of that retailer's row in the
#:      README retailer table, which 03-03 keys on.
#:
#: Those two agree today only by luck of capitalisation, and nothing in either
#: file makes the coupling visible. So: renaming a value here silently unhooks a
#: README row AS WELL AS an evidence heading, and the two will not fail
#: together. `test_roadmap_retailers_is_exactly_the_seven_in_scope` asserts this
#: mapping literally so a rename has to be a deliberate edit to a red test
#: rather than a quiet one that half-works.
ROADMAP_RETAILERS: dict[str, str] = {
    "gamestop": "GameStop",
    "walmart": "Walmart",
    "bestbuy": "Best Buy",
    "pokemoncenter": "Pokémon Center",
    "nintendo": "Nintendo",
    "target": "Target",
    "amazon": "Amazon",
}

#: Phase 3's two, both expected hostile. Used by rule 3 only: they are the
#: retailers whose landing would take the count to five, so a short count with
#: one of them configured means two things in this tree disagree.
HARD_TWO: tuple[str, ...] = ("target", "amazon")

#: The count `.planning/ROADMAP.md` Phase 3 criterion 5 asks for.
TARGET_RETAILER_COUNT = 5

#: A verdict line, anchored to a whole line.
#:
#: There is deliberately NO rung-4 REACHABLE form. Rung 4 *is* REFUSED — a
#: section claiming to have reached a retailer it dropped is a contradiction the
#: grammar should not be able to express.
#:
#: Anchored, rather than a substring test, for the reason in the module
#: docstring: `docs/retailer-evidence.md` states both verdict strings in its own
#: preamble so a reader knows the vocabulary, which makes
#: `'**Verdict: REFUSED**' in text` True for a document recording nothing at all.
VERDICT_RE = re.compile(
    r"^\*\*Verdict: (?:REACHABLE \(rung [1-3]\)|REFUSED)\*\*$",
    re.MULTILINE,
)

#: The one verdict that permits a roadmap retailer to be absent from the config.
REFUSED = "**Verdict: REFUSED**"

_HEADING_RE = re.compile(r"^## (.+)$", re.MULTILINE)


def split_sections(text: str) -> list[tuple[str, str]]:
    """Every `## ` heading paired with its body, in document order.

    Everything above the first heading is excluded BY CONSTRUCTION rather than
    by a filter somebody could later forget. That preamble is where the evidence
    log spells out the verdict vocabulary, so a checker able to see it would
    find both verdict strings in a document containing no findings whatsoever.

    A LIST OF PAIRS, NOT A DICT, AND THAT IS LOAD-BEARING. Keying on the heading
    means two sections with the SAME heading overwrite rather than accumulate,
    and the one that survives is whichever came last in the file. `check_retailer`
    has a bespoke failure for exactly that case — "two records of one retailer
    means nothing here can tell which is current" — and a dict makes it
    unreachable for the likeliest duplicate there is: a re-record appended under
    a copy-pasted heading. A self-contradicting evidence log then passes clean,
    with document order silently choosing its verdict. Both existing duplicate
    tests used deliberately DISTINCT headings, so the hole was invisible to the
    suite; `test_two_sections_under_the_same_heading_fail` covers it now.
    """
    matches = list(_HEADING_RE.finditer(text))
    return [
        (
            match.group(1).strip(),
            text[match.end() : (matches[i + 1].start() if i + 1 < len(matches) else len(text))],
        )
        for i, match in enumerate(matches)
    ]


def sections_for(display_name: str, sections: list[tuple[str, str]]) -> list[str]:
    """Bodies of every section whose heading BEGINS WITH `display_name`.

    Prefix rather than equality because the headings carry a parenthetical of
    the domains actually probed — `## Amazon (amazon.com)` — and that
    parenthetical is worth keeping. Zero matches and more than one match are
    both failures, and callers word them differently: "nobody wrote this down"
    and "two people wrote it down and we cannot tell which is current" send a
    reader to completely different places.
    """
    return [body for heading, body in sections if heading.startswith(display_name)]


def verdict_lines(body: str) -> list[str]:
    """Every well-formed verdict line in a section body, in order.

    "None" and "two" are different failures, so this returns a list rather than
    a bool or an Optional: the caller has to look at the count to word the
    message, which makes it hard to accidentally collapse the two cases.
    """
    return [match.group(0) for match in VERDICT_RE.finditer(body)]


def check_retailer(display_name: str, evidence_path: str | Path) -> list[str]:
    """Problems with one retailer's section. An empty list means it is sound.

    Returns data rather than printing so the tests can assert on the wording. A
    failure message nobody can act on gets ignored inside a week, so every one
    of these names both the file and the retailer.
    """
    path = Path(evidence_path)
    problems: list[str] = []
    bodies = sections_for(display_name, split_sections(path.read_text(encoding="utf-8")))

    if not bodies:
        return [
            f"{path}: no section for {display_name!r}. Expected exactly one `## ` heading "
            f"beginning with {display_name!r}, recording what was probed and one verdict line."
        ]
    if len(bodies) > 1:
        return [
            f"{path}: {len(bodies)} sections begin with {display_name!r}, expected exactly 1. "
            "Two records of one retailer means nothing here can tell which is current."
        ]

    found = verdict_lines(bodies[0])
    if not found:
        problems.append(
            f"{path}: the {display_name!r} section carries no verdict line. It must carry exactly "
            f"one of `{REFUSED}` or `**Verdict: REACHABLE (rung N)**` for N in 1-3, character for "
            "character — later gates read it mechanically. There is deliberately no rung-4 "
            "REACHABLE form: rung 4 IS refused."
        )
    elif len(found) > 1:
        problems.append(
            f"{path}: the {display_name!r} section carries {len(found)} verdict lines "
            f"({', '.join(found)}), expected exactly 1."
        )
    return problems


def check_phase(config_path: str | Path, evidence_path: str | Path) -> list[str]:
    """Is this tree telling the truth about its own retailer count?

    Three rules, applied in order, reporting EVERY violation rather than
    stopping at the first — being told about one gap, fixing it, and being told
    about the next is how a gate gets muted.
    """
    config_path = Path(config_path)
    evidence_path = Path(evidence_path)
    problems: list[str] = []

    # Read the configured set through Config.load rather than parsing the YAML
    # again, for the same reason `scripts/control_check.py` builds its checker
    # with `boty.cli._make_checker`: a gate reading the file differently from
    # the monitor would enforce a rule about a code path nobody runs, and the
    # two would drift apart the first time the schema moved.
    cfg = Config.load(config_path)
    configured = {w.retailer for w in cfg.watches}
    sections = split_sections(evidence_path.read_text(encoding="utf-8"))

    # RULE 1 — in scope.
    for retailer in sorted(configured - set(ROADMAP_RETAILERS)):
        problems.append(
            f"rule 1 (in scope): {config_path} configures {retailer!r}, which is not in the "
            "Retailer Scope table of .planning/ROADMAP.md. That table is the list of stores "
            "where a Pokémon GO Plus + could genuinely appear; a retailer outside it can be "
            "entirely real, control-verified and fixture-backed while still being unable to "
            "alert on the one product this project exists for. If it does carry the product, "
            "add it to ROADMAP_RETAILERS in this script and to the roadmap, deliberately."
        )

    # RULE 2 — configured, or refused. There is no silent third state.
    for retailer, display in ROADMAP_RETAILERS.items():
        if retailer in configured:
            continue
        found = sections_for(display, sections)
        if len(found) != 1 or verdict_lines(found[0]) != [REFUSED]:
            problems.append(
                f"rule 2 (configured or refused): {display} is not configured in {config_path} "
                f"and {evidence_path} does not record exactly one section for it carrying "
                f"`{REFUSED}`. A retailer that is neither shipped nor refused in writing is the "
                "silent gap this phase exists to make impossible — nothing in the tree says "
                "whether it was ever tried."
            )

    # RULE 3 — count consistency.
    if len(configured) < TARGET_RETAILER_COUNT:
        landed = sorted(configured & set(HARD_TWO))
        if landed:
            problems.append(
                f"rule 3 (count consistency): {config_path} configures only {len(configured)} "
                f"retailers, fewer than {TARGET_RETAILER_COUNT}, while {', '.join(landed)} IS "
                "configured. A short count is honest only when neither of the hard two landed — "
                "one of them landing is what takes the count to five — so this combination means "
                "something here disagrees with something else and should be read rather than "
                "rounded."
            )

    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="evidence_check",
        description="Machine-checkable honesty over the evidence log and the shipped retailers.",
    )
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--retailer",
        metavar="DISPLAY_NAME",
        help="check one retailer's section, e.g. --retailer 'Pokémon Center'",
    )
    mode.add_argument(
        "--phase",
        action="store_true",
        help="check the whole tree: scope, configured-or-refused, count consistency",
    )
    ap.add_argument("-c", "--config", default="config/products.yaml")
    ap.add_argument("-e", "--evidence", default="docs/retailer-evidence.md")
    args = ap.parse_args(argv)

    if args.retailer is not None:
        problems = check_retailer(args.retailer, args.evidence)
    else:
        problems = check_phase(args.config, args.evidence)

    for problem in problems:
        print(problem, file=sys.stderr)

    if problems:
        print(f"evidence check: FAIL — {len(problems)} problem(s)", file=sys.stderr)
        return 1

    what = f"retailer {args.retailer!r}" if args.retailer is not None else "phase"
    print(f"evidence check: PASS — {what}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
