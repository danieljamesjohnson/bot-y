"""The three-state verdict contract, and both defences against flippers.

`check_html` is where the project's core claim lives: a stock reading you can
trust. That means two things, tested separately here because they fail
separately:

- A page it cannot read is UNKNOWN, never OUT_OF_STOCK. Conflating them is the
  silent failure the whole design exists to prevent — the monitor reports
  out-of-stock forever after a reskin and looks perfectly healthy doing it.
- A reseller listing is not a restock. The seller filter and the price ceiling
  are independent defences: either alone suppresses the Walmart reseller
  fixture, so losing one does not lose the protection.

`boty.retailers.get` is monkeypatched throughout, so nothing here touches the
network — and conftest's guard would raise loudly if anything tried.
"""

from __future__ import annotations

import pytest

from boty import retailers
from boty.fetch import Blocked, FetchError, Page
from boty.models import Availability, Watch

GAMESTOP_URL = "https://www.gamestop.com/example"
WALMART_URL = "https://www.walmart.com/ip/example/1"


def _serve(monkeypatch: pytest.MonkeyPatch, html: str, url: str = GAMESTOP_URL) -> None:
    """Make `check_html`'s fetch return this HTML instead of hitting the site."""

    def _get(target: str, **kwargs: object) -> Page:
        return Page(url=target, status=200, text=html)

    monkeypatch.setattr(retailers, "get", _get)


def _raise(monkeypatch: pytest.MonkeyPatch, exc: Exception) -> None:
    def _get(target: str, **kwargs: object) -> Page:
        raise exc

    monkeypatch.setattr(retailers, "get", _get)


# --------------------------------------------------------------------------
# 1-2: GameStop, ld+json
# --------------------------------------------------------------------------


def test_gamestop_out_of_stock_is_not_alertable(
    monkeypatch: pytest.MonkeyPatch, gamestop_goplusplus: str
) -> None:
    _serve(monkeypatch, gamestop_goplusplus)
    watch = Watch(name="GO Plus +", retailer="gamestop", target=GAMESTOP_URL)

    result = retailers.check_html(watch)

    assert result.availability is Availability.OUT_OF_STOCK
    assert result.price == 54.99
    assert result.alertable is False


def test_gamestop_control_is_in_stock_and_alertable(
    monkeypatch: pytest.MonkeyPatch, gamestop_ps5: str
) -> None:
    """No max_price set, so a buyable first-party offer alerts."""
    _serve(monkeypatch, gamestop_ps5)
    watch = Watch(name="PS5", retailer="gamestop", target=GAMESTOP_URL, control=True)

    result = retailers.check_html(watch)

    assert result.availability is Availability.IN_STOCK
    assert result.alertable is True


# --------------------------------------------------------------------------
# 3-5: Walmart, __NEXT_DATA__ — the two independent flipper defences
# --------------------------------------------------------------------------


def test_walmart_reseller_rejected_by_first_party_filter(
    monkeypatch: pytest.MonkeyPatch, walmart_goplusplus: str
) -> None:
    """Defence one: the buy box is held by a marketplace seller, so it is not a restock.

    The item is genuinely purchasable — the parser reads IN_STOCK — but not
    from Walmart, and alerting on a flipper's listing trains you to ignore the
    notifications, which is worse than not alerting at all.
    """
    _serve(monkeypatch, walmart_goplusplus, WALMART_URL)
    watch = Watch(name="GO Plus +", retailer="walmart", target=WALMART_URL)

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is not Availability.IN_STOCK
    assert result.alertable is False
    assert "first-party" in result.detail


def test_walmart_reseller_rejected_by_price_ceiling_alone(
    monkeypatch: pytest.MonkeyPatch, walmart_goplusplus: str
) -> None:
    """Defence two, tested with defence one switched off.

    With `first_party_only=False` the reseller's offer is accepted as the
    reading — the item really is IN_STOCK — but $229.99 against an $80 ceiling
    is not a restock, so it must not alert. Proving this independently matters:
    if the seller filter ever regresses, the price ceiling still holds the line.
    """
    _serve(monkeypatch, walmart_goplusplus, WALMART_URL)
    watch = Watch(name="GO Plus +", retailer="walmart", target=WALMART_URL, max_price=80)

    result = retailers.check_html(watch, first_party_only=False)

    assert result.availability is Availability.IN_STOCK
    assert result.price is not None and result.price > 80
    assert result.alertable is False


def test_walmart_first_party_offer_is_accepted(
    monkeypatch: pytest.MonkeyPatch, walmart_milk: str
) -> None:
    """The control case: a genuine Walmart.com listing passes both defences."""
    _serve(monkeypatch, walmart_milk, WALMART_URL)
    watch = Watch(name="milk", retailer="walmart", target=WALMART_URL, control=True)

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.IN_STOCK
    assert "Walmart.com" in result.detail
    assert result.price == 2.42


# --------------------------------------------------------------------------
# 6-8: the negative contract — every failure mode is UNKNOWN
# --------------------------------------------------------------------------


def test_unparseable_page_is_unknown_not_out_of_stock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The single most important assertion in this suite.

    A page with no structured data means the detector got lost — the retailer
    reskinned, or a soft block came back dressed as a product page. Reporting
    that as OUT_OF_STOCK is the classic silent failure: the monitor keeps
    saying "not available" forever, never alerts again, and looks healthy the
    entire time. You find out weeks later, having missed the drop.
    """
    _serve(monkeypatch, "<html><body>we redesigned the site!</body></html>")
    watch = Watch(name="GO Plus +", retailer="gamestop", target=GAMESTOP_URL)

    result = retailers.check_html(watch)

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK, (
        "an unreadable page must never be reported as out-of-stock — that is "
        "the silent failure mode this project exists to prevent"
    )
    assert result.alertable is False
    assert result.detail


def test_blocked_fetch_is_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    _raise(monkeypatch, Blocked("challenge page matched 'robot or human' (HTTP 200)"))
    watch = Watch(name="GO Plus +", retailer="gamestop", target=GAMESTOP_URL)

    result = retailers.check_html(watch)

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK
    assert "blocked" in result.detail
    assert result.url == GAMESTOP_URL


def test_fetch_error_is_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    _raise(monkeypatch, FetchError("HTTP 503"))
    watch = Watch(name="GO Plus +", retailer="gamestop", target=GAMESTOP_URL)

    result = retailers.check_html(watch)

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK
    assert "fetch failed" in result.detail
    assert "503" in result.detail


# --------------------------------------------------------------------------
# The guard itself
# --------------------------------------------------------------------------


def test_the_network_guard_actually_fires() -> None:
    """A test that reaches the network fails loudly rather than passing quietly.

    Without this, conftest's guard could silently stop working (a curl_cffi
    refactor, a renamed attribute) and the suite would start making live
    requests without anyone noticing.
    """
    from boty import fetch

    with pytest.raises(BaseException, match="test attempted a live network request"):
        fetch.get("https://example.invalid/", jitter=(0, 0))


def test_the_network_guard_is_not_downgraded_to_a_verdict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The guard must escape `fetch.get`'s `except Exception`, not become UNKNOWN.

    This is the shape a Phase 2 adapter test will have: call the checker,
    assert on the verdict. If the author forgets to monkeypatch
    `retailers.get`, the guard fires — but an Exception-derived guard is caught
    by `fetch.get`'s blanket handler, re-raised as FetchError, and turned into
    Availability.UNKNOWN by `check_html`. The test then PASSES while asserting
    on a verdict the guard itself manufactured, and on any machine where the
    guard is not active the same test quietly makes a real request to GameStop
    and still passes.
    """
    monkeypatch.setattr("time.sleep", lambda _seconds: None)  # skip fetch.get's politeness jitter
    watch = Watch(name="GO Plus +", retailer="gamestop", target="https://example.invalid/")

    with pytest.raises(BaseException, match="test attempted a live network request"):
        retailers.check_html(watch)


def test_the_network_guard_covers_transports_that_bypass_curl_cffi() -> None:
    """apprise reaches the network through `requests`, control_check through a raw socket.

    Patching only `curl_cffi.requests` leaves both wide open, so the first test
    to touch notifications or the connectivity probe would silently go live.
    """
    import socket

    with pytest.raises(BaseException, match="test attempted a live network request"):
        socket.create_connection(("1.1.1.1", 443), timeout=1)

    with pytest.raises(BaseException, match="test attempted a live network request"):
        socket.socket().connect(("1.1.1.1", 443))
