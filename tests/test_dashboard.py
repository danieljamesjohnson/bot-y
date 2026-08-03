"""The one surface anybody actually reads.

`boty.status.write` publishes `rung` and `degraded`, and its own comment calls
those keys "a contract with the dashboard... the page renders it verbatim".
`tests/test_status.py` pins the producing half of that contract. Nothing pinned
the consuming half, so the page could — and did — quietly render neither, which
made a browser-read value look identical to a first-party one on the phone-sized
surface behind `/tools/boty`. A contract asserted at one end only is a comment.

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


