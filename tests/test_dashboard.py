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

import re
from pathlib import Path

import pytest

DASHBOARD = Path(__file__).resolve().parent.parent / "served" / "boty" / "index.html"

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
UNTRUSTED = (
    "w.name",
    "w.detail",
    "w.retailer",
    "w.url",
    "w.store",
    "w.store_pinned",
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
