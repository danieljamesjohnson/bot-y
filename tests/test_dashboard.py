"""The one surface anybody actually reads.

`boty.status.write` publishes `rung`, `extraction` and `degraded`, and its own comment calls
those keys "a contract with the dashboard... the page renders it verbatim".
`tests/test_status.py` pins the producing half of that contract. Nothing pinned
the consuming half, so the page could — and did — quietly render neither, which
made a browser-read value look identical to a first-party one on the phone-sized
surface behind `/tools/boty`. A contract asserted at one end only is a comment.

The same file is also where every retailer-controlled string in this project
ends up. `Result.detail` interpolates a seller name and an availability string
straight out of a retailer's JSON, and the page assigns the result to
`innerHTML`. So this module makes two claims about `served/boty/index.html`: it
shows how much a reading is worth, and it does not execute what a retailer says.

These are structural assertions against the file's source rather than a
browser-driven test, deliberately. `make verify` has to run from a fresh clone
with `pip install -e '.[dev]'` and nothing else; requiring a JavaScript runtime
to check the dashboard would put the check behind a dependency most contributors
would not have, and a check that does not run is worse than one that is coarse.
"""

from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

DASHBOARD = Path(__file__).resolve().parent.parent / "served" / "boty" / "index.html"

#: Where a JavaScript runtime lives on a machine that keeps one but does not put
#: it on `PATH`. Every entry is a real install layout of a version manager —
#: nvm, fnm, volta, asdf — rather than a guess, and the list is deliberately
#: short: it is about the CLASS of problem (a runtime managed per-version, which
#: is why it is not on a non-login shell's PATH) and not about one developer's
#: laptop. A box that keeps node somewhere else needs a new entry here; the skip
#: reason below says so, so the day that happens it is a visible gap and not an
#: accepted skip.
NODE_SEARCH_GLOBS = (
    "~/.nvm/versions/node/*/bin/node",
    "~/.local/share/fnm/node-versions/*/installation/bin/node",
    "~/.volta/tools/image/node/*/bin/node",
    "~/.asdf/installs/nodejs/*/bin/node",
)


def _js_runtime() -> tuple[str, str] | None:
    """Find a runtime that can answer `--check`, or say where it looked.

    WHY `PATH` ALONE WAS NOT ENOUGH, MEASURED RATHER THAN ASSUMED. `make`
    inherits the invoking shell's environment and does not source a version
    manager, so on a box whose only node is under `~/.nvm` the check below is
    not opportunistic — it is unreachable. Measured on this host: `command -v
    node` finds nothing, the same check inside a `make` recipe finds nothing,
    and the only runtime present is `~/.nvm/versions/node/v24.16.0/bin/node`.
    The gate added at `9e7d302` on 2026-08-17, specifically to catch a page that
    had just stopped parsing, therefore never ran once inside `make
    verify-offline` — the whole suite's only skip, for the whole of its life.
    A gate that cannot fire in the environment the project's own gate runs in is
    this repository's recorded failure shape, *a bound that cannot bind*, and
    widening the search is what makes it bind.

    WHY THE FIRST MATCH IS TAKEN AND A VERSION IS NOT CHOSEN. The question this
    gate asks is whether the script parses. Any runtime that can answer
    `--check` answers it, so selecting a version would imply the answer depends
    on one — it does not — and would invite a version floor that nothing here
    needs and that would have to be maintained against a page with no version
    dependency. The sort is for determinism between runs, not preference.

    WHY THIS IS STILL A SKIP AND NOT A REQUIREMENT. The module docstring above
    rejects requiring a runtime in as many words — *"`make verify` has to run
    from a fresh clone with `pip install -e '.[dev]'` and nothing else"* — and
    `REQUIREMENTS.md` § Non-Functional's fresh-clone rule says the same. So
    nothing here is installed and nothing is required: this widens what the
    search can FIND, and never what the suite DEMANDS. A contributor with no
    runtime anywhere still gets a skip, not a red tick on a correct tree.
    """
    for name in ("node", "nodejs"):
        found = shutil.which(name)
        if found is not None:
            return found, f"{name} on PATH"
    for pattern in NODE_SEARCH_GLOBS:
        matches = sorted(glob.glob(os.path.expanduser(pattern)))
        if matches:
            return matches[0], pattern
    return None

#: Fields whose values originate with a retailer rather than with the operator.
#: `detail` is the sharp one — `f"{source}: {offer.raw_availability} from
#: {seller}"` in `retailers._verdict_from_html`, both halves lifted verbatim out
#: of the retailer's own JSON-LD. `name` and `url` come from
#: `config/products.yaml` and are operator-controlled, but they are escaped too:
#: the cost is nothing, and the rule "everything at this sink is escaped"
#: survives contact with a future edit in a way that "these three but not those
#: two" does not.
#:
#: `w.store` is retailer-controlled in the sharpest sense: `parse.nextdata_store`
#: hands back whatever string Walmart put in `storeIds[0]`, of any length or
#: content, and it lands in `innerHTML` on Mission Control's origin.
#: `w.store_pinned` comes from `config/products.yaml` and is operator-controlled,
#: and it is listed anyway for the reason `name` and `url` are.
#:
#: BOTH entries are needed and neither implies the other: the regex below is
#: `(?<![\w.])w\.store\b`, and `\b` after `store` does not match inside
#: `w.store_pinned`.
#:
#: `w.read_at` joins the list under REQ-21, and NOT because anybody can make it
#: a string today. What actually reaches the sink is `fmtDur`'s return, and its
#: three bands coerce with `|0`, which produces an int32 for every possible
#: input including a string, an object and `NaN` — so no character outside
#: `[0-9-]` and the formatter's own literal text can reach `innerHTML` through
#: that path.
#:
#: It is listed anyway, and that is the POINT of the list: the rule "everything
#: at this sink is escaped" survives a future edit in a way that "these are
#: currently unreachable" does not. The day somebody writes
#: `title="read at ${w.read_at}"`, the escaping test goes red instead of
#: shipping.
#:
#: AND ITS PROVENANCE IS A THIRD KIND THIS LIST HAS NOT CARRIED. The heading
#: above says "fields whose values originate with a retailer rather than with
#: the operator". `read_at` originates with neither: it comes from `state.json`,
#: a mutable file on the host that a process trusts after a restart — 07-02's
#: threat, mitigated there with a both-ended bound. A value whose upstream is a
#: file on disk is the last one to make an exception for.
#:
#: `w.availability` JOINS THE LIST FOR `w.read_at`'S OWN STATED REASON, and it
#: should have joined it in the same commit. Its provenance is the third kind
#: described directly above — a mutable file on the host — and it travels the
#: SAME route out of the SAME file: `monitor._remembered_availability` returns
#: whatever `str` a `state.json` entry carries, `status.write` publishes it
#: verbatim as `availability`, and the page interpolates it into the dot's
#: `class` attribute. *"A value whose upstream is a file on disk is the last one
#: to make an exception for"* was written one paragraph up about `read_at`, and
#: it was already true of this field when it was written.
#:
#: WHAT USED TO EXCUSE IT, and why the excuse expired. Before 07-04 the only
#: producer of this key was `r.availability.value`, an `Availability` enum
#: member, so the value was one of three literals and no escaper could change
#: anything. 07-04 added a second producer that is deliberately NOT enum-bounded
#: (`boty/monitor.py`'s `_remembered_availability` states the exemption and its
#: reason). Measured against the tree that shipped it: a `state.json` entry of
#: `'" onmouseover=alert(1) x="'` rendered as
#: `<span class="dot " onmouseover=alert(1) x=""></span>` — the attribute broken
#: out of and a handler attached, on Mission Control's origin because the page
#: is proxied under `/tools/boty`.
#:
#: NO REMOTE WRITER REACHES `state.json` TODAY — `State.save` serialises
#: `result.availability.value` and nothing else — so what was demonstrated is the
#: sink and the flow, not an attacker. It is listed anyway, for the reason the
#: `read_at` paragraph gives: this list is not "what is currently reachable".
#: A rule of that shape does not survive the next edit to the template, and the
#: omission of this one field is that rule already not surviving.
#:
#: `w.checked` is DELIBERATELY NOT LISTED. It is a boolean used as a CONDITION
#: and never interpolated, exactly like `w.degraded`, `w.control` and
#: `w.extraction`. The test below only fires on `${...}` interpolation, so
#: listing a condition would demand `esc()` around a comparison and break it.
UNTRUSTED = (
    "w.name",
    "w.detail",
    "w.retailer",
    "w.url",
    "w.store",
    "w.store_pinned",
    "w.read_at",
    "w.availability",
    "r.retailer",
    "r.reason",
)


@pytest.fixture(scope="module")
def page() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def test_the_dashboard_exists_where_the_service_serves_it() -> None:
    """A renamed or moved file would make every assertion below vacuous."""
    assert DASHBOARD.is_file(), f"no dashboard at {DASHBOARD}"


# --------------------------------------------------------------------------
# WR-04: a degraded reading has to look degraded
# --------------------------------------------------------------------------


def test_the_dashboard_renders_the_degraded_flag(page: str) -> None:
    """The whole point of the Rung work, on the surface that gets looked at.

    `02-CONTEXT.md` states the contract as "anything reached via a browser is
    flagged DEGRADED in both the support matrix and `boty check` output". Both
    of those were done. The status page was not, so Best Buy's control rendered
    as a green dot at $59.99, visually identical to GameStop's rung-1 row — the
    letter of the contract met and its purpose defeated, because a rendered
    reading is exactly the one a human should weigh differently.
    """
    assert "degraded" in page, "the dashboard never mentions `degraded` at all"
    assert re.search(r"\bw\.degraded\b", page), (
        "the dashboard does not read the `degraded` key that `status.write` "
        "publishes for it"
    )


def test_the_degraded_tag_is_visually_distinct(page: str) -> None:
    """A tag styled identically to `control` says "here is a word", not "weigh this".

    `.tag` is deliberately dim and low-contrast because `control` is an
    ordinary, expected label. Degraded is not ordinary — it means the value
    beside it came from executing a retailer's JavaScript with no response
    status to check it against.
    """
    assert re.search(r"\.tag\.degraded\s*\{", page), (
        "no `.tag.degraded` rule — a degraded tag styled like every other tag "
        "does not tell a reader to weigh the number differently"
    )


def test_the_dashboard_shows_which_half_of_degraded_fired(page: str) -> None:
    """`degraded` has two disjuncts now, and the page has to say which one.

    `Result.degraded` fires on a browser transport OR a dom extraction, so the
    flag alone no longer identifies the problem. Those are different things to
    plan around — a rendered page is slow and heavy, a presentation-markup read
    is one reskin away from silently reading nothing — and a row that shows
    only the derived flag collapses them into one word on the one surface
    anybody actually looks at.

    `status.write` publishes `extraction` for exactly this. Pinning the
    consuming half here is the same WR-04 lesson that put the module docstring
    above on this file: a contract asserted at one end only is a comment.
    """
    assert re.search(r"\bw\.extraction\b", page), (
        "the dashboard does not read the `extraction` key that `status.write` "
        "publishes for it, so a DOM reading is indistinguishable from a browser one"
    )
    assert re.search(r"\.tag\.dom\s*\{", page), (
        "no `.tag.dom` rule — the tag that says WHY a reading is degraded is "
        "styled like `control`, which is an ordinary label"
    )


# --------------------------------------------------------------------------
# WR-05: retailer strings reach innerHTML
# --------------------------------------------------------------------------


def test_the_dashboard_defines_an_html_escaper(page: str) -> None:
    """Five characters, because escaping four of them is not escaping."""
    assert re.search(r"\bconst\s+esc\s*=", page), "no `esc` helper defined"
    for char, entity in (
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
        ('"', "&quot;"),
        ("'", "&#39;"),
    ):
        assert entity in page, f"the escaper does not map {char!r} to {entity}"


def test_every_retailer_controlled_string_is_escaped_before_innerhtml(page: str) -> None:
    """The assertion that has to survive the next edit to this template.

    `w.detail` is `f"{source}: {offer.raw_availability} from {seller}"` — both
    halves straight out of a retailer's JSON-LD, unescaped, via `status.json`.
    With `first_party_only: false`, a supported and tested setting, `_pick`
    accepts any offer and an arbitrary marketplace seller's display name lands
    in `innerHTML`. `raw_availability` is unbounded on both settings.

    Because the page is proxied under Mission Control's `/tools/boty`, anything
    injected here runs on Mission Control's origin rather than an isolated one.

    Checks every `${...}` in the file rather than the known-bad ones, so adding
    a new raw retailer field to the template fails here rather than shipping.
    """
    offenders = []
    for expr in re.findall(r"\$\{([^{}]*)\}", page):
        for field in UNTRUSTED:
            # `w.url` inside an href is still interpolated into innerHTML, so it
            # is held to the same rule as the rest.
            if re.search(rf"(?<![\w.]){re.escape(field)}\b", expr) and "esc(" not in expr:
                offenders.append(f"{field} in ${{{expr.strip()}}}")

    assert not offenders, (
        "retailer- or config-controlled strings reach `innerHTML` unescaped:\n  "
        + "\n  ".join(sorted(set(offenders)))
    )


def test_the_health_banner_is_escaped_too(page: str) -> None:
    """The banner is the second `innerHTML` sink and it is easy to forget.

    `r.reason` is built from `Health`, which names failing controls and carries
    detail text with the same provenance as `w.detail`. A page that escapes its
    list and not its banner is a page with an XSS in it.
    """
    banner = re.search(r"banner\.innerHTML\s*=\s*(.+)", page)
    assert banner, "the banner no longer assigns innerHTML — update this test"
    line = banner.group(1)
    for field in ("r.retailer", "r.reason"):
        assert f"esc({field})" in line.replace(" ", ""), (
            f"{field} is interpolated into the health banner unescaped"
        )


# --------------------------------------------------------------------------
# REQ-14: the row has to say which store the reading is about
# --------------------------------------------------------------------------


def test_the_dashboard_renders_both_store_keys(page: str) -> None:
    """`status.write` publishes `store` and `store_pinned`; the page reads both.

    One key alone cannot tell "no store recorded" from "store B answered and you
    pinned A", and those are the two states this phase exists to distinguish. A
    contract asserted at the producing end only is a comment — which is the
    lesson that put this module's docstring on this file.
    """
    assert re.search(r"(?<![\w.])w\.store\b", page), (
        "the dashboard does not read the `store` key that `status.write` "
        "publishes for it, so a Walmart row cannot say which store answered"
    )
    assert "w.store_pinned" in page, (
        "the dashboard does not read `store_pinned`, so a mismatch renders "
        "identically to a correct pin"
    )


def test_the_store_tag_has_two_visual_weights(page: str) -> None:
    """A correct pin is a LABEL; an unpinned or mismatched store is a WARNING.

    The same distinction the file already draws between `control` and
    `degraded`: `.tag` recedes because "this is the canary" is ordinary, while
    `degraded` is loud because it is a claim about how much the number beside it
    is worth. A reading from a store you did not ask about is the loud kind.
    """
    assert re.search(r"\.tag\.store\s*\{", page), (
        "no `.tag.store` rule — a store tag styled like every other tag says "
        "'here is a word' rather than 'this reading may not be about you'"
    )
    assert re.search(r"\.tag\.store\.warn\s*\{", page), (
        "no `.tag.store.warn` rule — an unpinned or mismatched store renders "
        "identically to a correctly pinned one"
    )


# --------------------------------------------------------------------------
# REQ-21: the row has to say how old the reading is
# --------------------------------------------------------------------------
#
# Four plans put the facts on the row — a stamp (07-01), a stamp that survives a
# restart (07-02), the cadence each retailer is currently on (07-03), and a row
# for every configured watch saying whether anybody looked (07-04). Nothing
# rendered any of it, so the page still presented a reading taken four seconds
# ago and one last taken two days ago identically.
#
# THE FOUR FORMS ARE `boty check`'s FOUR, deliberately, so a reader comparing
# the two surfaces never has to translate:
#
#     4s ago            [age 4s]
#     7h ago > 6h       [age 7h > 6h]
#     3h ago · cadence ?  [age 3h, cadence ?]
#     age ?             [age ?]
#
# AND THE ROW THRESHOLD IS NOT THE BANNER'S. `index.html`'s 1800-second constant
# asks *is this snapshot being written?*; the row asks *is this reading younger
# than the cadence its own retailer is currently on?* Merging them is wrong in
# BOTH directions at once on this config — see the killer test below.


def test_the_dashboard_reads_the_reading_stamp(page: str) -> None:
    """`status.write` publishes `read_at`; the page has to read it.

    A contract asserted at one end only is a comment — the lesson that put this
    module's docstring on this file, arriving for the fourth key.
    """
    assert re.search(r"\bw\.read_at\b", page), (
        "the dashboard does not read the `read_at` key that `status.write` "
        "publishes for it, so a two-day-old row renders as a fresh one"
    )


def test_the_dashboard_reads_the_checked_flag(page: str) -> None:
    """07-04's carried-forward producer/consumer pair, closed here.

    07-04 published `checked` and could not reach its consumer: this file
    belongs to 07-05, and reaching into it would have broken the phase's serial
    file ownership. Without it the page cannot tell "read this cycle, and out of
    stock" from "nobody looked, and this is what we remember".
    """
    assert re.search(r"\bw\.checked\b", page), (
        "the dashboard does not read the `checked` key that 07-04 published, "
        "so a remembered row is indistinguishable from an observed one"
    )


def test_the_age_tag_has_two_visual_weights(page: str) -> None:
    """A reading inside its cadence is a LABEL; a stale or undated one is a WARNING.

    The same distinction this file already draws between `control` and
    `degraded`, and between `.tag.store` and `.tag.store.warn`. A stale reading
    styled like a fresh one says "here is a word" rather than "this may not be
    true any more" — and an undated one styled like a fresh one is the implicit
    claim this whole phase exists to remove.
    """
    assert re.search(r"\.tag\.age\s*\{", page), (
        "no `.tag.age` rule — an age styled like every other tag says 'here is "
        "a word' rather than 'this is how much this row is worth'"
    )
    assert re.search(r"\.tag\.age\.warn\s*\{", page), (
        "no `.tag.age.warn` rule — a stale or undated reading renders "
        "identically to one taken four seconds ago"
    )


def test_the_row_threshold_is_the_retailers_own_cadence_and_not_a_fixed_clock(
    page: str,
) -> None:
    """Criterion 3 on this surface, and the reason it is worth a mutation.

    The page must read the published per-retailer cadence, and the banner's
    1800-second constant must occur exactly ONCE — where it is, unmoved and
    unreused. A count rather than an absence, because the legitimate occurrence
    is still there and a presence assertion could not tell the two apart.
    """
    assert re.search(r"\bcurrent_interval_seconds\b", page), (
        "the row threshold is not the published per-retailer cadence, so the "
        "page judges every retailer against one number"
    )
    assert len(re.findall(r"\b1800\b", page)) == 1, (
        "the banner's 1800-second constant was reused as a row threshold. It is "
        "wrong in BOTH directions on this config in the same second: target and "
        "walmart sit on the 21 600-second cap when they are refusing us, so "
        "every one of their rows would paint stale while they behave exactly as "
        "the politeness rule requires; and gamestop runs on a 900-second "
        "override, so a 25-minute-old GameStop reading would paint fresh when "
        "its own pacing says it is overdue. The one legitimate 1800 on this "
        "page is the banner's — it asks whether the snapshot is being written, "
        "which is a different question from how old a reading is"
    )


def test_the_page_has_exactly_one_age_formatter(page: str) -> None:
    """`fmtAge` is REUSED, not duplicated: the bands live in `fmtDur`.

    Two formatters drift, and the banner and the row tag must not start
    disagreeing about what "3h" means. `Result.degraded`'s one-source-of-truth
    argument, applied to a template. 5400 is the band boundary and it must occur
    exactly once.
    """
    assert len(re.findall(r"\b5400\b", page)) == 1, (
        "the age formatter's bands appear more than once — `fmtAge` was copied "
        "rather than defined through `fmtDur`"
    )
    assert re.search(r"const fmtAge = s => `\$\{fmtDur\(s\)\} ago`", page), (
        "`fmtAge` is not defined through `fmtDur`, so its output is no longer "
        "provably byte-identical to what the banner printed before"
    )


def test_a_row_nobody_checked_does_not_claim_a_store_answered(page: str) -> None:
    """The register defect 07-04 measured and handed here.

    `storeTag` renders `store: null` with a non-null `store_pinned` as a WARN tag
    saying the page did not name its store. On a remembered row that sentence is
    true in the letter — no page said anything — and false in register: the row's
    actual story is that nobody looked this cycle. 07-04 measured that it fires
    the moment `WALMART_STORE_ID` is set, which is the question 07-06's own
    checkpoint puts in front of Dan; shipping a defect that appears the moment he
    answers a question this phase asks him is a scheduled bug, not a latent one.

    `=== false` and not `!w.checked`, because a pre-07-04 `status.json` sitting
    on disk during a deploy has no `checked` key at all and `!undefined` is
    `true`, which would suppress the store tag on every row of that file —
    07-02's shape-tolerance rule, one file over.
    """
    assert re.search(r"const storeTag[\s\S]{0,400}?w\.checked === false", page), (
        "`storeTag` still renders before it consults `checked`, so a row nobody "
        "read carries a warning about a page that was never fetched"
    )


# --------------------------------------------------------------------------
# The page has to PARSE. Added 2026-08-17 after this gate's absence shipped.
# --------------------------------------------------------------------------


def test_no_html_comment_is_written_inside_the_script_block(page: str) -> None:
    """The dependency-free half, and the one that actually bound the day it was written.

    A `<!-- ... -->` inside the row's template literal is not a comment to
    JavaScript — it is TEXT, and any backtick in it CLOSES THE TEMPLATE. That is
    not hypothetical: it is how this test came to exist. The 07-REVIEW CR-01 fix
    put a paragraph of this project's usual back-quoted prose beside the escaped
    sink, inside the literal, and the page stopped parsing while every
    structural assertion in this file stayed green.

    THE RULE IS THE SHAPE OF THE COMMENT, NOT ITS CONTENT, because this codebase
    argues in comments and always will. `//` above the statement is free and
    carries any characters at all; `<!--` inside a template is a trap that only
    springs on some prose. Banning the trap costs nothing and needs no runtime,
    which is why this is the assertion that runs on a fresh clone rather than
    the `node --check` below.
    """
    script = re.search(r"<script>(.*)</script>", page, re.S)
    assert script, "the dashboard has no <script> block — update this test"

    assert "<!--" not in script.group(1), (
        "an HTML comment appears inside the <script> block. JavaScript does not "
        "treat it as a comment; inside a template literal it is text, and a "
        "backtick in it closes the literal and stops the whole page parsing. "
        "Use `//` above the statement — it carries any characters, including "
        "the back-quoted identifiers this codebase writes everywhere."
    )


def test_the_dashboard_script_parses(page: str) -> None:
    """Every assertion in this module is a regex over source. None of them run it.

    THIS TEST EXISTS BECAUSE THAT GAP WAS PAID FOR. Fixing 07-REVIEW CR-01 added
    a comment beside the escaped sink, INSIDE the row's template literal, and the
    comment contained backticks — which close a template literal. The page
    stopped parsing and rendered nothing at all, and every structural assertion
    in this file stayed green, because a regex looking for `esc(w.availability)`
    finds it just as happily in a file the browser refuses to run.

    That is this repository's own recorded failure shape — a gate that cannot
    bite — pointed at the file whose module docstring claims *"it does not
    execute what a retailer says"*. A page that does not parse does not execute
    anything, which satisfies the letter of that claim and defeats all of it.

    SKIPPED WHERE NO JS RUNTIME EXISTS, and that is the whole reason this is
    shaped as a skip rather than a dependency. This module's docstring rejects
    *requiring* a JavaScript runtime — *"`make verify` has to run from a fresh
    clone with `pip install -e '.[dev]'` and nothing else"* — and that argument
    is untouched: nothing here is required, nothing is installed, and a
    contributor without node sees a skip rather than a failure. It is not
    "verified" on such a machine and this docstring says so rather than
    implying otherwise. On a box that HAS node — this one, and any CI image
    built on a standard runner — a syntax error is caught before it is served.

    AND *NO RUNTIME EXISTS* NOW MEANS WHAT IT SAYS, WHICH IT DID NOT BEFORE.
    Until 07-07 this read `shutil.which("node")`, so it meant *no runtime is on
    this PATH* — and on the box that wrote it, that was true of every `make
    verify-offline` run while a perfectly good runtime sat under `~/.nvm`. The
    gate spent its entire life as the suite's only skip. `_js_runtime` looks
    past PATH into the version-manager roots, so the two cases a reader must be
    able to tell apart — *this host has no JavaScript runtime* and *this test
    did not find the one it has* — are now distinguishable from the transcript
    alone, because the skip reason enumerates everywhere it looked.
    """
    runtime = _js_runtime()
    if runtime is None:
        pytest.skip(
            "SKIPPED, NOT PASSED: nothing below has been checked, and the "
            "dashboard's script may or may not parse. No JavaScript runtime was "
            "found in any of: `node` on PATH, `nodejs` on PATH, "
            + ", ".join(NODE_SEARCH_GLOBS)
            + ". If this host HAS a runtime somewhere else, that is a missing "
            "entry in NODE_SEARCH_GLOBS and not an acceptable skip — add it, "
            "because a gate that cannot fire reads exactly like one that passed."
        )
    node, _found_in = runtime

    script = re.search(r"<script>(.*)</script>", page, re.S)
    assert script, "the dashboard has no <script> block — update this test"

    with tempfile.TemporaryDirectory() as tmp:
        js = Path(tmp) / "dashboard.js"
        js.write_text(script.group(1), encoding="utf-8")
        proc = subprocess.run(
            [node, "--check", str(js)], capture_output=True, text=True
        )

    assert proc.returncode == 0, (
        "the dashboard's script does not parse, so the page renders nothing:\n"
        + (proc.stderr.strip() or proc.stdout.strip())
    )
