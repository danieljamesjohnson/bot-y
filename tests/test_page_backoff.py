"""A refusal is a fact about a PAGE until every page says so.

Dan, 2026-10-19: *"I think per page makes sense to me."*

WHY THIS EXISTS. `run_once` used to fold a cycle into the pacer with
`refused=any(x.refused for x in group)`, so one challenged page put its whole
retailer on the backoff ladder. Measured twice on Amazon — 2026-09-14 03:26:17
and 2026-10-18 11:52:50 — the AA-battery control read `in_stock` and the GO
Plus + page was challenged two seconds later, in the same cycle. The control
answered; the retailer was recorded refused anyway, climbed to 30 in a row, and
went dark for three days at a time with a working page in it.

THE RULE NOW. A retailer is refused when EVERY page it was asked for this
cycle was refused — that is a wall, and the retailer ladder handles it exactly
as before. When only SOME pages were refused, the retailer counts as having
answered, and each refused page climbs its own copy of the same ladder: it
sits out while the retailer's other pages keep being read. A page that answers
clears its own count.

A store-wide refusal deliberately does NOT also climb the page ladders. The
retailer ladder already owns that case, and charging both would compound: a
page would still be sitting out when the store's own cool-off ended, and the
probe that tells us whether the wall is down would never be made.
"""

from __future__ import annotations

from pathlib import Path

from boty.models import Availability, Result, Watch
from boty.monitor import State, run_once
from boty.pacing import (
    COOLOFF_SECONDS,
    MAX_BACKOFF_SECONDS,
    REFUSALS_BEFORE_COOLOFF,
    Pacer,
)

CONTROL = Watch(name="ctl", retailer="amazon", target="https://amazon.test/dp/CTL", control=True)
PRODUCT = Watch(name="zelda", retailer="amazon", target="https://amazon.test/dp/ZELDA")
WATCHES = [CONTROL, PRODUCT]


def _ok(w: Watch) -> Result:
    return Result(w, Availability.IN_STOCK, price=1.0, detail="fine")


def _refused(w: Watch) -> Result:
    return Result(w, Availability.UNKNOWN, detail="blocked: challenge page", refused=True)


def _checker(refuse: set[str], asked: list[str] | None = None):
    def check(w: Watch) -> Result:
        if asked is not None:
            asked.append(w.name)
        return _refused(w) if w.name in refuse else _ok(w)

    return check


def _state(tmp_path: Path) -> State:
    return State(tmp_path / "state.json", {})


def test_one_refused_page_among_answered_pages_does_not_refuse_the_retailer(tmp_path: Path) -> None:
    p = Pacer(default_interval=300)
    run_once(WATCHES, _checker({"zelda"}), _state(tmp_path), pacer=p, now=0.0)

    assert p._for("amazon").refusals == 0, (
        "the control answered and the retailer was still recorded refused — the "
        "any() rule that put Amazon on three-day cool-offs with a working page in it"
    )
    assert p.due("amazon", 300.0), "the retailer is not back on its standing interval"


def test_the_refused_page_sits_out_while_its_retailer_keeps_being_read(tmp_path: Path) -> None:
    p = Pacer(default_interval=300)
    state = _state(tmp_path)
    run_once(WATCHES, _checker({"zelda"}), state, pacer=p, now=0.0)

    asked: list[str] = []
    run_once(WATCHES, _checker({"zelda"}, asked), state, pacer=p, now=300.0)

    assert asked == ["ctl"], (
        f"asked {asked} one standing interval after the product page was refused — "
        f"the refused page must wait out its own backoff, and the control must not"
    )


def test_a_refused_page_climbs_the_same_ladder_a_retailer_does(tmp_path: Path) -> None:
    p = Pacer(default_interval=300)
    state = _state(tmp_path)
    waits = []
    now = 0.0
    for _ in range(4):
        run_once([PRODUCT, CONTROL], _checker({"zelda"}), state, pacer=p, now=now)
        due_at = p._page(PRODUCT).due_at
        waits.append(due_at - now)
        now = due_at
    assert waits == [600, 1200, 2400, 4800], f"page backoff is {waits}"


def test_a_persistently_refused_page_reaches_the_cap_and_the_cooloff() -> None:
    p = Pacer(default_interval=300)
    for _ in range(REFUSALS_BEFORE_COOLOFF - 1):
        p.record_page(PRODUCT, refused=True, now=0.0)
    assert p.page_interval(PRODUCT) == MAX_BACKOFF_SECONDS
    p.record_page(PRODUCT, refused=True, now=0.0)
    assert p.page_interval(PRODUCT) == COOLOFF_SECONDS


def test_a_page_that_answers_clears_its_own_backoff(tmp_path: Path) -> None:
    p = Pacer(default_interval=300)
    state = _state(tmp_path)
    run_once(WATCHES, _checker({"zelda"}), state, pacer=p, now=0.0)
    run_once(WATCHES, _checker(set()), state, pacer=p, now=600.0)

    assert p._page(PRODUCT).refusals == 0
    asked: list[str] = []
    run_once(WATCHES, _checker(set(), asked), state, pacer=p, now=900.0)
    assert sorted(asked) == ["ctl", "zelda"]


def test_a_wall_is_still_a_retailer_refusal_and_charges_no_page(tmp_path: Path) -> None:
    p = Pacer(default_interval=300)
    run_once(WATCHES, _checker({"ctl", "zelda"}), _state(tmp_path), pacer=p, now=0.0)

    assert p._for("amazon").refusals == 1, "every page refused is a wall, and the retailer ladder owns it"
    assert p._page(PRODUCT).refusals == 0 and p._page(CONTROL).refusals == 0, (
        "a store-wide refusal also climbed the page ladders — the two would compound, "
        "and a page could still be sitting out when the store's own cool-off ends"
    )


def test_page_refusals_survive_a_restart_and_the_old_document_still_loads(tmp_path: Path) -> None:
    path = tmp_path / "pacer-state.json"
    first = Pacer(default_interval=300, state_path=path)
    first.record("target", refused=True, now=0.0)
    for _ in range(3):
        first.record_page(PRODUCT, refused=True, now=0.0)
    first.save(set())

    second = Pacer(default_interval=300, state_path=path)
    second.load()
    assert second._page(PRODUCT).refusals == 3
    assert second._for("target").refusals == 1, "adding pages broke the retailer half of the document"

    # A document written before pages existed — today's production file — must load unchanged.
    old = tmp_path / "old.json"
    old.write_text(path.read_text().replace('"pages"', '"unrelated"'))
    third = Pacer(default_interval=300, state_path=old)
    third.load()
    assert third._for("target").refusals == 1
    assert third._page(PRODUCT).refusals == 0
