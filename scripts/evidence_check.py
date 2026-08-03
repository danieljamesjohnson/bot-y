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
retailer count, via the five rules in `check_phase`.

`--config`, `--evidence` and `--fixtures` exist so the tests can point either
mode at a synthetic tree and watch it go red. A gate nobody has watched fail is
not a gate; the watching is `tests/test_evidence_check.py`.

THE COUNT NEEDS A FLOOR AS WELL AS A CEILING
--------------------------------------------
Rules 1-3 shipped first and they all point the same way: they stop the retailer
count drifting UP, by refusing a padded retailer and refusing a short count that
contradicts itself. Nothing stopped it drifting DOWN. Any number of configured
retailers passed, down to zero, provided each absent one carried a written
REFUSED — and `README.md` would go on advertising the removed ones as working,
because the support matrix only checked `configured ⊆ documented`.

Reproduced end to end before rule 4 existed: delete the gamestop and walmart
watch blocks, append two REFUSED sections, leave the README alone.

    configured retailers: ['bestbuy', 'nintendo']   watches: 3
    README still shows: | GameStop | 1 | ... | ✅ Working |
                        | Walmart  | 1 | ... | ✅ Working |
    253 passed in 1.07s
    evidence check: PASS — phase

Half the shipped detectors gone, every gate green, and the surface this phase
built specifically to be trustworthy still telling a reader both are watched. A
working retailer silently disappearing is precisely the silent gap the phase is
named after. Rule 4 is the floor, and `tests/test_support_matrix.py`'s
overstatement rule is the other half of it.

AND THE FLOOR NEEDED A MIRROR — W-02
------------------------------------
Rule 4 says a refusal cannot outrank a capture. It shipped without its opposite:
*a configuration cannot outrank a refusal*. `03-VERIFICATION.md` recorded that
hole as W-02, proved by execution — add a `pokemoncenter` watch to
`config/products.yaml` while `docs/retailer-evidence.md` goes on carrying
`**Verdict: REFUSED**` for Pokémon Center, and this script said

    evidence check: PASS — phase
    evidence_check exit: 0

Rule 1 passed (in scope), and rules 2 and 4 BOTH `continue` on
`retailer in configured` — so the one tree shape that is flatly
self-contradicting walked between them untouched. Re-confirmed on the tree
immediately before rule 5 was written: `check_phase` returned `[]`.

`make verify` did still go red on that tree, which is why W-02 was a warning
rather than a blocker — but it went red via
`test_no_retailer_is_configured_without_a_page_we_have_actually_read`, a
Phase-1-era fixture-provenance guard, and it did so BY ACCIDENT. That test wants
a captured `tests/fixtures/pokemoncenter/*.html`, and padding this way cannot
produce one because `boty.fixtures.capture` only writes after a live fetch and
Imperva refuses to hand Pokémon Center's page over. The catch was a property of
one retailer's anti-bot vendor, not of any rule. A retailer that a wall lets
through — Target, next — would have padded the count clean.

Note the shape, because it is the reason this paragraph is this long: the defect
class CR-02 named — *a rule that points one way is half a rule* — survived the
fix that named it, one rule over. Rule 5 is the mirror, and it is watched failing
on the literal W-02 reproduction in `tests/test_evidence_check.py`.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

# Run from a checkout without installing: make the repo root importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boty.config import Config  # noqa: E402
from boty.fetch import BLOCK_PHRASES  # noqa: E402

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

#: Where `boty.fixtures.capture` writes a page, one directory per retailer key.
#:
#: Rule 4 treats a `*.html` file here as DURABLE PROOF that this repo once read
#: that retailer, because that is exactly what it is: `capture` only writes one
#: after a live fetch that was not blocked, which is why
#: `test_no_retailer_is_configured_without_a_page_we_have_actually_read` already
#: trusts the same artefact in the opposite direction. A retailer we have read
#: is not a retailer that refused us.
#:
#: Script-relative rather than CWD-relative because it is evidence about THIS
#: checkout. The `--fixtures` flag overrides it so the tests can point rule 4 at
#: a synthetic tree; nothing in this module reaches for the real one implicitly.
FIXTURE_ROOT = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

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

#: The one SETTLED verdict that permits a roadmap retailer to be absent from the
#: config. See `UNPROBED_RE` for the other, temporary, way to be absent.
REFUSED = "**Verdict: REFUSED**"

#: The honest third state: in scope, and nobody has looked yet.
#:
#: WHY THIS EXISTS. Rule 2 admitted exactly two states for a roadmap retailer —
#: configured, or carrying a written REFUSED — and 03-03 wired this gate into
#: the `test` stage of `make verify` permanently. Together those make the honest
#: answer to "we just widened the scope and have not probed it yet"
#: UNEXPRESSIBLE. From the commit that adds a retailer to ROADMAP_RETAILERS
#: until the day it is settled, `make verify` is red, and there are exactly two
#: ways to make it green: ship a detector, or write `**Verdict: REFUSED**` for a
#: store nobody has touched. The second is one line and takes a second.
#:
#: This phase hit that wall itself and routed around it — the tree was
#: legitimately red between 03-01 and 03-02, and the fix was to keep the gate
#: out of `make verify` for one plan. That escape no longer exists. A gate that
#: makes the honest state unrepresentable pressures exactly the padding this
#: file was written to prevent, in the opposite sign.
#:
#: WHY IT IS NOT A HOLE. It is not a quiet exemption; it is a fourth claim, and
#: it costs more to write than the lie it replaces:
#:
#:   - it is written down in the evidence log, like every other verdict, so
#:     "nobody has looked" is a statement somebody made rather than an absence;
#:   - it carries the date the retailer entered scope, so it cannot be confused
#:     with a retailer we stopped looking at years ago;
#:   - it EXPIRES. After `UNPROBED_GRACE_DAYS` this gate goes red anyway. That
#:     is the difference between a grace period and an escape hatch — an escape
#:     hatch is the thing that rotted in Phase 2, and it rotted by persisting.
#:   - `--strict` rejects it outright, which is the bar at phase close: a phase
#:     does not get to close with a retailer nobody looked at.
UNPROBED_RE = re.compile(
    r"^\*\*Verdict: UNPROBED \(scoped (\d{4}-\d{2}-\d{2})\)\*\*$",
    re.MULTILINE,
)

#: The literal form, for failure messages. A message that describes a grammar
#: without showing it makes the reader guess at the spacing, and the spacing is
#: load-bearing — every one of the MALFORMED cases in the tests is a near miss.
UNPROBED_EXAMPLE = "**Verdict: UNPROBED (scoped YYYY-MM-DD)**"

#: How long "nobody has looked yet" stays a true statement.
#:
#: Long enough to be useful across a phase boundary, short enough that leaving
#: one in place is not a way of never answering. The clock runs from the scoped
#: date in the verdict itself, so it cannot be reset by touching the file.
UNPROBED_GRACE_DAYS = 60

#: A refusal observation, anchored to a whole line — rule 6's grammar.
#:
#: Anchored for the same reason `VERDICT_RE` is, and it is not a theoretical
#: reason here: this file documents its own vocabulary, so the paragraph in the
#: evidence log's preamble *describing* this line form would satisfy a substring
#: rule. `strip_fences` removes the worked example; the anchor removes the
#: prose.
#:
#: Capturing group 1 is the BODY, which is where the reason actually lives —
#: see `_MEASURED`.
REFUSAL_RE = re.compile(r"^\*\*Refusal observed \(rung ([1-3])\):\*\* (.+)$", re.MULTILINE)

#: The literal form, for failure messages, on the same principle as
#: `UNPROBED_EXAMPLE`: a message describing a grammar without showing it makes
#: the reader guess at the spacing, and the spacing is load-bearing.
REFUSAL_EXAMPLE = "**Refusal observed (rung N):** …"

#: A measurement in a refusal observation's body: a status code, a byte count,
#: or a matched `BLOCK_PHRASES` entry.
#:
#: THIS PREDICATE IS THE WHOLE OF RULE 6, AND THE ANCHOR ALONE IS NOT.
#: `^\*\*Refusal observed \(rung [1-3]\):\*\* .+$` was the obvious line form and
#: it is the wrong one: `.+` accepts anything, so a gate written to make REQ-07a
#: mechanical would be satisfiable by typing the sentence. That is the same
#: failure this whole file exists to close, one rule further along — 02-04's
#: retailer-count clause was also satisfiable by a document that recorded
#: nothing.
#:
#: So the body has to carry something that could only come from an attempt. Not
#: proof — a determined author can type `HTTP 503` as easily as a sentence — but
#: a claim specific enough to be checkable against a retailer, and specific
#: enough that writing it is a decision rather than a phrasing.
#:
#: AND IT IS NOT SUFFICIENT ON ITS OWN EITHER, which is worth stating here
#: because the counterexample is in this repository. § Target carries
#:
#:     **Refusal observed (rung 1):** not a block — **HTTP 200**, 314,757 B …
#:
#: — an anchored refusal observation whose body records that Target was *not*
#: refused. It has a status code AND two byte counts and clears this predicate
#: comfortably. What keeps it harmless is the other half of rule 6: the rule
#: reads only REFUSED sections, and Target is REACHABLE.
#: `test_the_shipped_target_non_refusal_line_is_only_harmless_because_of_the_section_scope`
#: pins exactly that, so whoever widens rule 6's scope finds out from a red test
#: rather than from a shipped falsehood.
_MEASURED = (
    re.compile(r"HTTP\s*\d{3}"),
    re.compile(r"\b\d[\d,]*\s*(?:B|bytes)\b"),
)

_HEADING_RE = re.compile(r"^## (.+)$", re.MULTILINE)

#: A fenced code block, opened and closed by the SAME fence marker.
#:
#: Non-greedy so consecutive blocks do not merge into one, and the closing fence
#: is matched by backreference so a ```` ``` ```` block is not closed by a `~~~`.
_FENCE_RE = re.compile(r"^(?P<fence>```|~~~).*?^(?P=fence)[ \t]*$", re.MULTILINE | re.DOTALL)


def strip_fences(text: str) -> str:
    """Remove fenced code blocks, so an EXAMPLE of the format is not a record.

    Neither `_HEADING_RE` nor `VERDICT_RE` can tell a real heading from one
    inside a fence, and the evidence log is a document about its own grammar: it
    already carries a vocabulary preamble, and the natural way to document how
    to record a verdict is a fenced template using a real retailer's name. Left
    in, that template is indexed as a genuine record — a document whose ONLY
    content is a fenced example and the sentence "Nothing was actually probed."
    passed `check_retailer` for Amazon, which is verbatim the failure the module
    docstring above exists to close, reached by a route the preamble exclusion
    does not cover.

    Worse in combination with the duplicate-heading collapse this file used to
    have: an example using a real retailer's name produces an IDENTICAL heading
    to that retailer's real section, so a template placed below a real record
    would have replaced it outright.

    The fenced text is dropped rather than blanked line-for-line: nothing here
    reports line numbers, and the sections either side keep their own bodies.
    """
    return _FENCE_RE.sub("", text)


def split_sections(text: str) -> list[tuple[str, str]]:
    """Every `## ` heading paired with its body, in document order.

    Fenced code blocks are stripped first — see `strip_fences`.

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
    text = strip_fences(text)
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


def unprobed_lines(body: str) -> list[str]:
    """Every well-formed UNPROBED line in a section body, in order.

    Kept separate from `verdict_lines` rather than folded into `VERDICT_RE`,
    because the two answer different questions and rule 2 branches on which one
    it got: a settled verdict is permanent and an UNPROBED one is on a clock.
    Merging them would make "is this retailer settled?" a string comparison
    somebody could get subtly wrong at each of the three call sites.
    """
    return [match.group(0) for match in UNPROBED_RE.finditer(body)]


def unprobed_dates(body: str) -> list[date]:
    """The scoped dates of every UNPROBED line, skipping any that is not a date.

    `\\d{4}-\\d{2}-\\d{2}` matches `2026-13-45`, which is not a day. A line that
    looks like an UNPROBED verdict and carries an impossible date is NOT one:
    dropping it here means the caller sees a section with one UNPROBED line and
    zero usable dates, which falls through to rule 2's ordinary failure. An
    unparseable date must not be a way to buy silence forever.
    """
    dates: list[date] = []
    for match in UNPROBED_RE.finditer(body):
        try:
            dates.append(date.fromisoformat(match.group(1)))
        except ValueError:
            continue
    return dates


def _cites_a_measurement(refusal_body: str) -> bool:
    """Does this refusal observation's body carry something that was measured?

    A status code, a byte count, or one of the challenge phrases
    `boty.fetch.get` actually matches on. The block phrases are imported from
    the transport rather than retyped here for the reason `check_phase` reads
    the config through `Config.load`: a gate that knows a different list from
    the code would enforce a rule about strings nobody matches on, and the two
    would drift the first time a phrase was added — which happened twice in
    Phase 2 and again in 03.1-03.
    """
    if any(pattern.search(refusal_body) for pattern in _MEASURED):
        return True
    lowered = refusal_body.lower()
    return any(phrase in lowered for phrase in BLOCK_PHRASES)


def refusal_observations(body: str) -> list[str]:
    """Every well-formed, MEASURED refusal observation in a section body.

    Both halves are required — see `REFUSAL_RE` for the anchor's reason and
    `_MEASURED` for the predicate's. A line clearing the anchor and failing the
    predicate is deliberately NOT returned here and is reported separately by
    `unmeasured_refusal_lines`, because the two need different fixes: one says
    "record what came back", the other says "you did record something, but it is
    a sentence rather than an observation".
    """
    return [
        match.group(0)
        for match in REFUSAL_RE.finditer(body)
        if _cites_a_measurement(match.group(2))
    ]


def unmeasured_refusal_lines(body: str) -> list[str]:
    """Refusal observations that are prose: right shape, nothing measured.

    Its own function and its own failure message rather than silence, because a
    line that looks exactly like the thing the gate asked for and is ignored by
    it is worse than no line — the author believes they satisfied the rule.
    """
    return [
        match.group(0)
        for match in REFUSAL_RE.finditer(body)
        if not _cites_a_measurement(match.group(2))
    ]


def refusal_rungs(body: str) -> set[str]:
    """Which rungs the MEASURED refusal observations name."""
    return {
        match.group(1)
        for match in REFUSAL_RE.finditer(body)
        if _cites_a_measurement(match.group(2))
    }


def all_verdict_lines(body: str) -> list[str]:
    """Every line of any accepted verdict form, in document order.

    `check_retailer` asks "does this section carry exactly one verdict?", and
    the answer has to count all three forms — otherwise a section carrying only
    an UNPROBED line reads as having no verdict at all, and a section carrying
    both an UNPROBED and a REFUSED reads as having one.
    """
    matches = [*VERDICT_RE.finditer(body), *UNPROBED_RE.finditer(body)]
    return [match.group(0) for match in sorted(matches, key=lambda m: m.start())]


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

    found = all_verdict_lines(bodies[0])
    if not found:
        problems.append(
            f"{path}: the {display_name!r} section carries no verdict line. It must carry exactly "
            f"one of `{REFUSED}`, `**Verdict: REACHABLE (rung N)**` for N in 1-3, or "
            f"`{UNPROBED_EXAMPLE}` — character for character, because later gates read it "
            "mechanically. There is deliberately no rung-4 REACHABLE form: rung 4 IS refused."
        )
    elif len(found) > 1:
        problems.append(
            f"{path}: the {display_name!r} section carries {len(found)} verdict lines "
            f"({', '.join(found)}), expected exactly 1."
        )
    return problems


def check_phase(
    config_path: str | Path,
    evidence_path: str | Path,
    fixture_root: str | Path,
    *,
    strict: bool = False,
    today: date | None = None,
) -> list[str]:
    """Is this tree telling the truth about its own retailer count?

    Five rules, applied in order, reporting EVERY violation rather than stopping
    at the first — being told about one gap, fixing it, and being told about the
    next is how a gate gets muted.

    `strict` is the phase-close bar: it refuses an UNPROBED verdict outright.
    `make verify` runs non-strict, so a newly-scoped retailer has a grace period
    in which the honest answer is expressible; `--strict` is what says the phase
    does not get to close on it. `today` is injectable so the expiry can be
    tested without waiting sixty days or freezing a clock globally.

    `fixture_root` is REQUIRED rather than defaulted, deliberately. A default
    would be inherited silently by every synthetic-tree test in
    `tests/test_evidence_check.py`, which states as an invariant that nothing in
    it reads the shipped tree — and rule 4 would then be enforced against this
    repo's real fixtures while the test believed it was describing its own
    `tmp_path`. Making it explicit costs one argument per call site and means
    every caller has said which tree it means.
    """
    config_path = Path(config_path)
    evidence_path = Path(evidence_path)
    fixture_root = Path(fixture_root)
    today = date.today() if today is None else today
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

    # RULE 2 — configured, refused, or unprobed-and-dated. No SILENT third state.
    for retailer, display in ROADMAP_RETAILERS.items():
        if retailer in configured:
            continue
        found = sections_for(display, sections)
        settled = verdict_lines(found[0]) if len(found) == 1 else []
        pending = unprobed_lines(found[0]) if len(found) == 1 else []
        scoped = unprobed_dates(found[0]) if len(found) == 1 else []

        if settled == [REFUSED] and not pending:
            continue

        if not settled and len(pending) == 1 and len(scoped) == 1:
            # In scope, written down, dated — and on a clock.
            if strict:
                problems.append(
                    f"rule 2 (--strict): {display} is recorded `{pending[0]}` in {evidence_path}. "
                    "UNPROBED is a state to pass through, not one to close a phase in: at phase "
                    "close every retailer in scope is either shipped or refused in writing. "
                    "Probe it and record the verdict, or take it out of ROADMAP_RETAILERS "
                    "deliberately."
                )
                continue
            age = (today - scoped[0]).days
            if age > UNPROBED_GRACE_DAYS:
                problems.append(
                    f"rule 2 (an unprobed retailer expires): {display} is recorded "
                    f"`{pending[0]}` in {evidence_path}, scoped {age} days ago, past the "
                    f"{UNPROBED_GRACE_DAYS}-day grace. UNPROBED is how a newly-scoped retailer "
                    "says 'nobody has looked yet' without inventing a refusal; it is not "
                    "somewhere to leave one. Probe it and write the verdict, or drop it from "
                    "ROADMAP_RETAILERS. Re-dating the line to buy another grace period is the "
                    "one edit this gate cannot see, so it is the one to raise in review."
                )
            continue

        problems.append(
            f"rule 2 (configured or refused): {display} is not configured in {config_path} "
            f"and {evidence_path} does not record exactly one section for it carrying "
            f"`{REFUSED}`. A retailer that is neither shipped nor refused in writing is the "
            "silent gap this phase exists to make impossible — nothing in the tree says "
            "whether it was ever tried. IF NOBODY HAS LOOKED YET, SAY THAT rather than "
            f"inventing a refusal: a section carrying `{UNPROBED_EXAMPLE}` is accepted for "
            f"{UNPROBED_GRACE_DAYS} days from the scoped date, after which this gate goes red "
            "again. A false REFUSED is one line and never expires, which is why the honest "
            "answer needed a spelling."
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

    # RULE 4 — a refusal cannot outrank a capture. THE FLOOR.
    #
    # Rules 2 and 3 are a ceiling on the count. This is the only thing under it:
    # a roadmap retailer that is not configured, but whose page this repo
    # demonstrably fetched, is not a retailer that refused us — it is a watch
    # that was dropped without saying so. Checked against evidence already on
    # disk, offline, with no request to anybody.
    for retailer, display in sorted(ROADMAP_RETAILERS.items()):
        if retailer in configured:
            continue
        captures = sorted(path.name for path in (fixture_root / retailer).glob("*.html"))
        if captures:
            problems.append(
                f"rule 4 (a refusal cannot outrank a capture): {display} is not configured in "
                f"{config_path}, yet {fixture_root / retailer} holds {captures} — pages this "
                "repo really fetched. `boty.fixtures.capture` only writes one after a live "
                "fetch that was not blocked, so a retailer we have read is not a retailer that "
                "refused us: either the verdict is wrong, or a working watch was dropped and "
                "nothing in the tree says so. Rules 2 and 3 stop the retailer count drifting "
                "UP; this is what stops it drifting down. If the retailer is genuinely gone, "
                "delete its fixtures in the same commit and say why in the evidence log."
            )

    # RULE 5 — a configuration cannot outrank a refusal. THE MIRROR OF RULE 4.
    #
    # W-02, from the module docstring: rules 2 and 4 both `continue` on
    # `retailer in configured`, so a tree that SHIPS a detector for a retailer
    # its own evidence log records as refused passed clean. This is the rule for
    # the one shape neither of them looks at.
    #
    # THREE CASES DELIBERATELY DO NOT FIRE, and each is an allowance rather than
    # an oversight, so each is stated here rather than left to be inferred:
    #
    #   1. NO SECTION AT ALL. GameStop and Walmart are configured and have never
    #      had a section in the evidence log; rule 2 requires one only from
    #      retailers that are NOT configured. Demanding one here would redden the
    #      shipped tree over a gap that is not a lie. Silence about a shipped
    #      retailer is a documentation gap; this rule is about self-contradiction
    #      only, and a tree cannot contradict a claim nobody made.
    #   2. A REACHABLE VERDICT. Configured and recorded as readable is the
    #      agreeing case — the state this whole phase is walking Target and
    #      Amazon towards.
    #   3. MORE THAN ONE SECTION. `check_retailer` already words that failure
    #      ("two records of one retailer means nothing here can tell which is
    #      current") and reporting it twice trains a reader to skim. Note the
    #      narrow cost: `check_retailer` is driven over the real document by
    #      `test_the_real_shipped_evidence_document_passes_per_retailer`, which
    #      can only cover retailers that HAVE a section — so
    #      `test_no_roadmap_retailer_resolves_to_more_than_one_section` covers
    #      the rest, and duplicate headings stay caught for all seven.
    for retailer, display in sorted(ROADMAP_RETAILERS.items()):
        if retailer not in configured:
            continue
        found = sections_for(display, sections)
        if len(found) != 1:
            continue

        if verdict_lines(found[0]) == [REFUSED]:
            problems.append(
                f"rule 5 (a configuration cannot outrank a refusal): {config_path} configures "
                f"{retailer!r} while {evidence_path} records `{REFUSED}` for {display}. Rule 4 "
                "stops a refusal outranking a capture; this is its mirror. A tree that ships a "
                "detector for a retailer it has written down as refused is telling two stories, "
                "and the honest edit is whichever one is now false — flip the verdict and say "
                "why in the same commit, or drop the watch."
            )

        # "In scope, nobody has looked yet" and "shipped and control-verified"
        # are the same contradiction one step softer, and softer is the version
        # that survives review. A watch cannot have been built for a page nobody
        # has opened.
        pending = unprobed_lines(found[0])
        if pending:
            problems.append(
                f"rule 5 (a configuration cannot outrank a refusal): {config_path} configures "
                f"{retailer!r} while {evidence_path} still records `{pending[0]}` for {display}. "
                "UNPROBED means nobody has looked yet, and a shipped detector is somebody having "
                "looked — one of the two is stale. Record what the probe found and give the "
                "section a settled verdict, or drop the watch."
            )

    # RULE 6 — a refusal must cite an observation. REQ-07a, made mechanical.
    #
    # Rules 1-5 are all about the retailer COUNT: whether it drifts up, whether
    # it drifts down, whether two places in the tree disagree about it. None of
    # them looks at *why* a retailer is absent, and Phase 3 is the proof that
    # this mattered: it dropped two retailers on a desk review of their written
    # terms, made zero product-page requests to either, and every gate in this
    # tree stayed green. REQ-07a already said a retailer is dropped only when it
    # is technically unreachable — it was a sentence in a requirements document
    # and nothing read it.
    #
    # WHAT THIS RULE DOES NOT ASK ABOUT, and each omission is deliberate:
    #
    #   1. REACHABLE sections. A section may legitimately carry refusal
    #      observations from a rung that failed on the way to one that worked —
    #      § Target carries two, § Amazon carries one — and reading them here
    #      would punish the most thorough records in the file. Worse, Target's
    #      rung-1 line says "not a block — HTTP 200": it is an anchored refusal
    #      observation recording a NON-refusal, and it is harmless only because
    #      of this scope. See `_MEASURED`.
    #   2. UNPROBED sections. An UNPROBED verdict is *saying* nobody has looked,
    #      and it already carries a dated, expiring claim. Demanding an
    #      observation from it would make the honest state unrepresentable,
    #      which is the exact failure mode `UNPROBED_RE` was added against.
    #   3. Retailers with no section, or with more than one. Rule 2 and
    #      `check_retailer` respectively already word those, and reporting the
    #      same defect twice trains a reader to skim.
    for retailer, display in sorted(ROADMAP_RETAILERS.items()):
        found = sections_for(display, sections)
        if len(found) != 1 or verdict_lines(found[0]) != [REFUSED]:
            continue

        prose_only = unmeasured_refusal_lines(found[0])
        observed = refusal_observations(found[0])

        if prose_only:
            problems.append(
                f"rule 6 (a refusal must cite an observation): {evidence_path} records "
                f"{len(prose_only)} refusal observation(s) for {display} whose body cites no "
                f"status code, byte count or matched block phrase — e.g. `{prose_only[0]}`. "
                "The anchor is the easy half; the measurement is the half that could only come "
                "from an attempt. A gate that can be satisfied by typing the sentence is not a "
                "gate, which is the defect this whole file was written after. Quote what came "
                "back: `HTTP 503`, `6,183 B`, or the `BLOCK_PHRASES` entry that matched."
            )

        if not observed:
            problems.append(
                f"rule 6 (a refusal must cite an observation): {evidence_path} records "
                f"`{REFUSED}` for {display} and carries no `{REFUSAL_EXAMPLE}` line. REQ-07a: a "
                "retailer is dropped only when it is technically unreachable, and the reason "
                "recorded is the observation, not a policy reading. Phase 3 dropped two "
                "retailers without making a single product-page request and every gate in this "
                "tree stayed green. Either record what came back when it was tried, or stop "
                "recording a refusal."
            )
        elif retailer in HARD_TWO and (len(observed) < 2 or "3" not in refusal_rungs(found[0])):
            # The higher bar, and the reason it exists rather than being left to
            # the plans that write these branches: both retailer plans in 03.1
            # specify the same refusal branch — two spaced rung-1 attempts plus
            # one rung-3 attempt — and without this the branch is bounded by a
            # promise. A single `**Refusal observed (rung 1):** 503` would
            # otherwise satisfy a rule whose branch demanded a walked ladder.
            rungs = ", ".join(sorted(refusal_rungs(found[0]))) or "none"
            problems.append(
                f"rule 6 (a refusal must cite an observation): {display} is one of the hard two "
                f"({', '.join(HARD_TWO)}) and is recorded `{REFUSED}`, but {evidence_path} "
                f"carries {len(observed)} refusal observation(s), at rung(s) {rungs}. A hard-two "
                "refusal needs at least 2, including at least one at rung 3. These are the two "
                "retailers whose landing takes the count to five, so dropping one is the most "
                "consequential thing this document can say — it takes a walked ladder, not one "
                "failed request. If a rung was not walked, the honest verdict is not a refusal."
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
        help=(
            "check the whole tree: scope, configured-or-refused, count consistency, "
            "and that no refusal contradicts a page we captured or a watch we ship"
        ),
    )
    ap.add_argument("-c", "--config", default="config/products.yaml")
    ap.add_argument("-e", "--evidence", default="docs/retailer-evidence.md")
    ap.add_argument(
        "--strict",
        action="store_true",
        help=(
            "phase-close bar: refuse an UNPROBED verdict outright. `make verify` runs "
            "without it, so a newly-scoped retailer can say 'nobody has looked yet' in "
            f"writing for {UNPROBED_GRACE_DAYS} days; this is what says a phase does not "
            "get to close on one"
        ),
    )
    ap.add_argument(
        "-f",
        "--fixtures",
        default=None,
        help=(
            "root of the captured-page tree rule 4 reads "
            f"(default: {FIXTURE_ROOT}, resolved relative to this script)"
        ),
    )
    args = ap.parse_args(argv)

    if args.retailer is not None:
        problems = check_retailer(args.retailer, args.evidence)
    else:
        problems = check_phase(
            args.config,
            args.evidence,
            FIXTURE_ROOT if args.fixtures is None else args.fixtures,
            strict=args.strict,
        )

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
