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

import json

from boty import retailers
from boty.fetch import Blocked, FetchError, Page
from boty.models import Availability, Watch
from boty.parse import Offer

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


def _nextdata(**product: object) -> str:
    """A minimal Walmart hydration payload, shaped like the real fixture."""
    doc = {"props": {"pageProps": {"initialData": {"data": {"product": product}}}}}
    return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(doc)}</script></html>'


def _ldjson(**offer: object) -> str:
    doc = {"@type": "Product", "name": "thing", "offers": [offer]}
    return f'<html><script type="application/ld+json">{json.dumps(doc)}</script></html>'


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
# Who is selling this? — the seller filter's own failure modes
# --------------------------------------------------------------------------


def test_unattributed_offer_is_not_first_party_on_a_marketplace() -> None:
    """"No seller recorded" is not the same claim on Walmart as on GameStop.

    `nextdata_offers` sets `seller=product.get("sellerName")`, which is None
    whenever Walmart's hydration payload omits that key. The fallback that
    treats unattributed offers as first-party is right for a single-seller
    retailer, but Walmart and Target are in FIRST_PARTY precisely *because*
    a third party can hold their buy box — so there, "I do not know who is
    selling this" must not read as "the retailer is selling this".
    """
    flip = Offer(available=True, price=229.99, seller=None, raw_availability="IN_STOCK")

    assert retailers._pick([flip], "walmart", first_party_only=True) is None
    assert retailers._pick([flip], "target", first_party_only=True) is None


def test_unattributed_offer_is_still_first_party_on_a_single_seller_retailer() -> None:
    """The fallback exists for a reason and must survive: GameStop's schema.org
    markup carries no seller node at all, and nothing there is a marketplace."""
    offer = Offer(available=True, price=54.99, seller=None, raw_availability="InStock")

    assert retailers._pick([offer], "gamestop", first_party_only=True) is offer


def test_walmart_offer_with_no_seller_recorded_is_unknown_not_a_verdict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End to end: an unattributed marketplace offer is UNKNOWN, both ways.

    It must not be IN_STOCK (that would alert on a possible flipper), and it
    must not be OUT_OF_STOCK either — the page says something IS buyable, and
    claiming otherwise is the confident-wrong-answer failure this project
    exists to prevent. The only true statement is "I cannot tell whose offer
    this is".
    """
    _serve(
        monkeypatch,
        _nextdata(availabilityStatus="IN_STOCK", priceInfo={"currentPrice": {"price": 229.99}}),
        WALMART_URL,
    )
    watch = Watch(name="GO Plus +", retailer="walmart", target=WALMART_URL, max_price=80)

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.UNKNOWN
    assert result.alertable is False
    assert "seller" in result.detail.lower()


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
# Best Buy: the API key must never reach a Result
# --------------------------------------------------------------------------

#: Realistic shape — long enough that a substring check is meaningful.
API_KEY = "SUPERSECRETKEY123abcdefghijklmnop"


def _bestbuy_watch() -> Watch:
    return Watch(name="GO Plus +", retailer="bestbuy", target="6577129")


@pytest.mark.parametrize(
    ("name", "install"),
    [
        # curl error strings routinely echo the requested URL back, so the
        # credential arrives in `detail` as well as in `url`.
        ("transport error", lambda mp: _raise(mp, FetchError(f"HTTP 403 for url: {_bestbuy_url()}"))),
        ("blocked", lambda mp: _raise(mp, Blocked(f"challenge page for {_bestbuy_url()}"))),
        ("bad json", lambda mp: _serve(mp, "<html>403 Forbidden</html>")),
        ("sku not found", lambda mp: _serve(mp, '{"products": []}')),
    ],
)
def test_bestbuy_api_key_never_reaches_the_result(
    monkeypatch: pytest.MonkeyPatch, name: str, install: object
) -> None:
    """A credential in a Result is a credential on the public status page.

    `boty.status.write` copies `r.url` and `r.detail` verbatim into
    `served/boty/status.json`, which is served over HTTP through the Mission
    Control /tools/boty proxy. Every error path here used to return the full
    credentialed API URL as `Result.url`, and REQ-04 records HTTP 403 as Best
    Buy's *normal* behaviour — so this is the ordinary case, not the edge one.
    It also violates the project constraint that credentials live only in
    ~/.config/boty/env at mode 600.
    """
    install(monkeypatch)  # type: ignore[operator]

    result = retailers.check_bestbuy_api(_bestbuy_watch(), API_KEY)

    assert API_KEY not in result.url, f"{name}: api key leaked into Result.url"
    assert API_KEY not in result.detail, f"{name}: api key leaked into Result.detail"
    assert "apiKey" not in result.url
    assert result.url == "https://www.bestbuy.com/site/-/6577129.p"
    assert result.availability is Availability.UNKNOWN
    assert result.detail, "a UNKNOWN verdict must still say why"


def _bestbuy_url() -> str:
    return (
        f"https://api.bestbuy.com/v1/products(sku=6577129)?apiKey={API_KEY}"
        "&format=json&show=sku,name,salePrice,onlineAvailability"
    )


def test_bestbuy_success_reports_the_public_product_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _serve(monkeypatch, '{"products": [{"salePrice": 54.99, "onlineAvailability": true}]}')

    result = retailers.check_bestbuy_api(_bestbuy_watch(), API_KEY)

    assert result.availability is Availability.IN_STOCK
    assert result.price == 54.99
    assert API_KEY not in result.url and API_KEY not in result.detail


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
