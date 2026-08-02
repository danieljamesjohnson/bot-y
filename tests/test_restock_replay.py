"""Replay a real watch across many cycles: every rising edge must alert.

The other monitor tests hand `run_once` a synthetic `Result`. This one drives
the whole stack the way production does — `run_once` -> `check_html` -> the
parser -> frozen GameStop HTML — and runs it for several cycles in a row
against one persistent `State`.

That shape is deliberate, because the worst bug found in this phase was only
visible across cycles. `state.transitioned_to_stock` is the sole writer of the
memory, and it used to be called as the last term of an `and` chain that
Python short-circuited whenever a result was not alertable. A single cycle
looked perfect. Two cycles looked perfect. The damage appeared on the *second*
rising edge: the out-of-stock reading in between was never recorded, so the
monitor still believed the item was in stock and swallowed the restock — for
the rest of the process's life, silently, with a green dashboard.

Thirty-six passing tests did not see it. A single-cycle assertion cannot: the
bug is a property of the sequence, not of any one verdict. So the unit here is
a session, not a call.

The fixtures do double duty. Using the real captures rather than hand-built
`Result`s means this also fails if the parser stops reading GameStop's
schema.org markup, and the availability assertions below state which fixture
means what so a future reader can tell a monitor regression from a parser one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from boty import retailers
from boty.fetch import Page
from boty.fixtures import load
from boty.models import Availability, Watch
from boty.monitor import State, run_once

PRODUCT_URL = "https://www.gamestop.com/products/pokemon-go-plus-plus/20003961.html"
KEY = "gamestop:goplusplus"

#: Neither ld+json nor __NEXT_DATA__: the shape a soft block or a reskin has.
#: `check_html` must call this UNKNOWN — "I could not tell" — and the memory
#: must survive it untouched, which is the property `transitioned_to_stock`
#: documents and the reason UNKNOWN is a first-class state in this codebase.
UNREADABLE = "<html><body><h1>Robot or human?</h1></body></html>"


@pytest.fixture
def replay(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Drive `run_once` through a list of pages, one page per cycle.

    Returns a callable taking the pages to serve and giving back, per cycle,
    the verdict reached, the names alerted on, and what the state remembered
    afterwards. State persists across the whole sequence, exactly as the real
    `watch` loop persists it across polls.
    """
    served = {"html": ""}

    def _get(target: str, **kwargs: object) -> Page:
        return Page(url=target, status=200, text=served["html"])

    monkeypatch.setattr(retailers, "get", _get)

    def _run(pages: list[str], *, control: bool = False, max_price: float | None = None):
        watch = Watch(
            name="goplusplus",
            retailer="gamestop",
            target=PRODUCT_URL,
            max_price=max_price,
            control=control,
        )
        state = State.load(tmp_path / "state.json")

        verdicts: list[Availability] = []
        fired: list[list[str]] = []
        remembered: list[str | None] = []
        for html in pages:
            served["html"] = html
            results, _health, alerts = run_once([watch], retailers.check_html, state)
            verdicts.append(results[0].availability)
            fired.append([r.watch.name for r in alerts])
            remembered.append(state.seen.get(KEY))
        return verdicts, fired, remembered

    return _run


def test_a_product_watch_alerts_on_every_rising_edge_not_just_the_first(replay) -> None:
    """out -> in -> out -> in must alert TWICE.

    This is the whole point of the tool. Missing the second drop is not a
    degraded experience, it is the failure the project was built to prevent,
    and it is invisible from the outside: no error, no health warning, no
    change on the status page.

    Against the pre-fix code this fails at cycle 3 with alerts `[]` — the
    out-of-stock at cycle 2 was never written, so the monitor compared the
    restock against a remembered "in_stock" and concluded nothing had changed.
    """
    out_of_stock = load("gamestop", "goplusplus")
    in_stock = load("gamestop", "ps5-control")

    verdicts, fired, remembered = replay([out_of_stock, in_stock, out_of_stock, in_stock])

    # State the fixtures' meaning explicitly: if GameStop's markup changes and
    # these stop reading as intended, this test should say so plainly rather
    # than fail somewhere confusing further down.
    assert verdicts == [
        Availability.OUT_OF_STOCK,
        Availability.IN_STOCK,
        Availability.OUT_OF_STOCK,
        Availability.IN_STOCK,
    ], "the fixtures no longer drive the transitions this test replays"

    assert fired == [[], ["goplusplus"], [], ["goplusplus"]], (
        "the second restock was swallowed: an alert fired on the first rising "
        "edge but not the second, which means the out-of-stock reading between "
        "them was never recorded"
    )
    assert remembered == ["out_of_stock", "in_stock", "out_of_stock", "in_stock"], (
        "what we NOTIFY about must never decide what we REMEMBER"
    )


def test_an_unknown_reading_neither_alerts_nor_erases_what_is_known(replay) -> None:
    """UNKNOWN is "I could not tell", and must behave like it in both directions.

    It must not fabricate a transition — a blocked fetch is not a restock — and
    it must not wipe a known state, or the next successful check would look
    like a fresh rising edge and re-alert on something that never changed. An
    alert stream you learn to distrust is worse than no alert stream.
    """
    out_of_stock = load("gamestop", "goplusplus")
    in_stock = load("gamestop", "ps5-control")

    verdicts, fired, remembered = replay(
        [out_of_stock, in_stock, out_of_stock, UNREADABLE, in_stock, in_stock]
    )

    assert verdicts[3] is Availability.UNKNOWN, "an unreadable page must never be OUT_OF_STOCK"

    # Cycle 3 is UNKNOWN: no alert, and the memory still says out_of_stock.
    assert fired[3] == [], "an unreadable page is not a restock"
    assert remembered[3] == "out_of_stock", "UNKNOWN must not erase a known state"

    # Cycle 4 is the genuine restock the UNKNOWN interrupted; cycle 5 repeats
    # it and must stay quiet, because alerts are edge-triggered.
    assert fired == [[], ["goplusplus"], [], [], ["goplusplus"], []]


def test_a_control_watch_records_state_but_never_alerts(replay) -> None:
    """Controls prove the detector works; they are not things you want to buy.

    Their state still has to be recorded every cycle. It is the same single
    call that records a product's, so a fix that special-cased controls into a
    second pass would call `transitioned_to_stock` twice for them — and because
    it mutates `state.seen`, the second call compares against what the first
    just wrote and reports no transition at all.
    """
    out_of_stock = load("gamestop", "goplusplus")
    in_stock = load("gamestop", "ps5-control")

    _verdicts, fired, remembered = replay(
        [out_of_stock, in_stock, out_of_stock, in_stock], control=True
    )

    assert fired == [[], [], [], []], "a control must never produce a restock alert"
    assert remembered == ["out_of_stock", "in_stock", "out_of_stock", "in_stock"], (
        "a control's state is still recorded once per cycle"
    )


def test_the_price_ceiling_suppresses_the_alert_without_freezing_the_memory(replay) -> None:
    """A too-expensive listing is not alertable — and must still be remembered.

    This is the same class of bug as the original, one step along: filtering
    the alert must not also filter the bookkeeping. If the $549.99 in-stock
    reading were dropped from the memory because an $80 ceiling suppressed its
    alert, the state would be wrong for every later cycle.
    """
    out_of_stock = load("gamestop", "goplusplus")
    in_stock = load("gamestop", "ps5-control")  # $549.99, far above the ceiling

    verdicts, fired, remembered = replay(
        [out_of_stock, in_stock, out_of_stock, in_stock], max_price=80
    )

    assert verdicts[1] is Availability.IN_STOCK, "the ceiling filters alerts, not verdicts"
    assert fired == [[], [], [], []], "$549.99 must not alert against an $80 ceiling"
    assert remembered == ["out_of_stock", "in_stock", "out_of_stock", "in_stock"]
