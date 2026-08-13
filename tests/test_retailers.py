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

import ast
import json
import os
import re
import time
from pathlib import Path

import pytest

from boty import parse, retailers
from boty.cli import _make_checker
from boty.config import Config
from boty.fetch import Blocked, FetchError, Page
from boty.models import Availability, Extraction, Rung, Watch
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
    # `store_id="0"` is the store this fixture answers for, and `"0"` is THIS
    # REPO'S REDACTION PLACEHOLDER — `8dec2e0` wrote it over a real store number
    # in both Walmart captures, and it sits in `identity_check.py`'s allow-list
    # beside `"00000"` and `"XX"`. It is NOT a Walmart "no store assigned"
    # sentinel; nothing here has measured what Walmart does in that case, and
    # `05-PATTERNS.md` inferred exactly that and was wrong.
    #
    # The pin is here, and on every Walmart watch below, because 05-02's
    # config-gap guard turns an UNPINNED Walmart reading into UNKNOWN before any
    # stock verdict can form. Without it this test would still pass — UNKNOWN is
    # `not IN_STOCK` — while asserting nothing about the seller filter at all.
    watch = Watch(name="GO Plus +", retailer="walmart", target=WALMART_URL, store_id="0")

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
    watch = Watch(
        name="GO Plus +", retailer="walmart", target=WALMART_URL, max_price=80, store_id="0"
    )

    result = retailers.check_html(watch, first_party_only=False)

    assert result.availability is Availability.IN_STOCK
    assert result.price is not None and result.price > 80
    assert result.alertable is False


def test_walmart_first_party_offer_is_accepted(
    monkeypatch: pytest.MonkeyPatch, walmart_milk: str
) -> None:
    """The control case: a genuine Walmart.com listing passes both defences."""
    _serve(monkeypatch, walmart_milk, WALMART_URL)
    watch = Watch(
        name="milk", retailer="walmart", target=WALMART_URL, control=True, store_id="0"
    )

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.IN_STOCK
    assert "Walmart.com" in result.detail
    assert result.price == 2.42


# --------------------------------------------------------------------------
# What you would actually pay — the shipping thread-through (REQ-17)
# --------------------------------------------------------------------------


def test_the_gamestop_capture_carries_its_shipping_cost_all_the_way_to_a_result(
    monkeypatch: pytest.MonkeyPatch, gamestop_goplusplus: str
) -> None:
    """The one delivered total in this repository computable from captured data.

    $54.99 + $6.99 = $61.98, read off GameStop's own `OfferShippingDetails`.

    THIS ASSERTS THE THREAD-THROUGH AND THE ARITHMETIC, NOT ALERTABILITY, and
    that is deliberate rather than an omission: this fixture reads OUT_OF_STOCK,
    so `alertable` short-circuits on availability long before any ceiling is
    consulted. What is being pinned is that a number `boty.parse` read off the
    page survives `_verdict_from_html` and reaches the decision layer — the
    step where a missed site would otherwise be silent, because `None` is the
    correct value on every other path.

    `pytest.approx` because `54.99 + 6.99` is `61.980000000000004`. The
    delivered total is never rounded.
    """
    _serve(monkeypatch, gamestop_goplusplus)
    watch = Watch(name="GO Plus +", retailer="gamestop", target=GAMESTOP_URL, max_price=80)

    result = retailers.check_html(watch)

    assert result.price == 54.99
    assert result.shipping == 6.99
    assert result.delivered_total == pytest.approx(61.98)
    # THE HEALTHY STRING STAYS BYTE-IDENTICAL, and it is asserted here rather
    # than described: a ceiling IS configured on this watch, and the suffix that
    # says what the ceiling measured must appear only where a shipping cost
    # could not be established. 03.1-04 verified this shape character-for-
    # character against live output.
    assert result.detail == "ld+json: OutOfStock from GameStop"


def test_a_page_with_no_structured_data_carries_no_shipping_and_moves_no_availability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An offerless UNKNOWN stays UNKNOWN, and states `shipping=None` rather than inheriting it.

    The shipping work must move no `Availability` anywhere: nothing becomes
    OUT_OF_STOCK because a shipping cost could not be read, and no UNKNOWN is
    resolved into a verdict by it.
    """
    _serve(monkeypatch, "<html><body>a page we cannot read</body></html>")
    watch = Watch(name="GO Plus +", retailer="gamestop", target=GAMESTOP_URL, max_price=80)

    result = retailers.check_html(watch)

    assert result.availability is Availability.UNKNOWN
    assert result.shipping is None
    assert result.delivered_total is None
    assert result.alertable is False


def test_a_number_in_a_field_never_observed_carrying_one_is_not_a_shipping_cost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A SYNTHETIC stand-in, in `PUBLISH_WORKFLOW`'s idiom, and what it does not claim.

    WHAT THIS DOES NOT CLAIM: that `shippingAndImportFee.price` is where
    Walmart puts a paid shipping cost. Nobody knows where Walmart puts one —
    **no captured payload in this repository shows Walmart's paid marketplace
    shipping shape at all**, and a fixture cannot be edited to carry shipping
    Walmart never sent without lying about what was captured. So this payload
    is written here, in the test, labelled synthetic, rather than smuggled into
    the fixture tree.

    WHAT IT DOES CLAIM: that a number sitting in a field which has never been
    observed carrying one does not become a shipping cost. The fee here is
    non-zero and the SHIPPING option carries no `freeFulfillment`, so the two
    signals do not agree, so nothing is resolved — and with a ceiling
    configured, nothing resolved is not alertable.

    THIS IS THE $54.99-ITEM-WITH-$45-SHIPPING CASE REQ-17 NAMES, AND AS OF
    2026-08-11 IT PAGES DAN. The name is unchanged and still accurate — the fee
    still does not become a shipping cost, `shipping` is still `None` and the
    delivered total is still unestablished — but the ceiling now falls back to
    the item price where shipping cannot be read, and $54.99 clears $80
    comfortably. That is Dan's decision, verbatim: *"I think where we don't
    know just send it. If the user gets there and it's 50 dollar shipping
    that's disappointing but it's worse to feel like you 'missed out'."* The
    whole of the mitigation is that the push says `shipping: unknown`; Dan is
    not told a total, because there is no total to tell him.
    """
    page = _nextdata(
        availabilityStatus="IN_STOCK",
        sellerName="Walmart.com",
        priceInfo={
            "currentPrice": {"price": 54.99},
            "additionalFees": {"shippingAndImportFee": {"price": 45.0}},
        },
        fulfillmentOptions=[{"type": "SHIPPING", "speedDetails": {}}],
        location={"storeIds": ["0"]},
    )
    _serve(monkeypatch, page, WALMART_URL)
    watch = Watch(
        name="GO Plus +", retailer="walmart", target=WALMART_URL, max_price=80, store_id="0"
    )

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.IN_STOCK
    assert result.price == 54.99
    assert result.shipping is None
    assert result.delivered_total is None
    assert result.alertable is True


def test_the_walmart_capture_that_says_free_shipping_says_so_on_the_result(
    monkeypatch: pytest.MonkeyPatch, walmart_goplusplus: str
) -> None:
    """`0.0` is a claim, and it survives to the Result — but the flip still fails.

    Both of Walmart's free-shipping signals agree on this capture, so shipping
    resolves at `0.0` and the delivered total is the item price. That total is
    $229.99 against an $80 ceiling, so the reseller listing is refused by the
    ceiling exactly as it was before REQ-17 — the new rule tightened this
    defence without loosening it anywhere.
    """
    _serve(monkeypatch, walmart_goplusplus, WALMART_URL)
    watch = Watch(
        name="GO Plus +", retailer="walmart", target=WALMART_URL, max_price=80, store_id="0"
    )

    result = retailers.check_html(watch, first_party_only=False)

    assert result.availability is Availability.IN_STOCK
    assert result.shipping == 0.0
    assert result.delivered_total == pytest.approx(229.99)
    assert result.alertable is False


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
        # The payload names a store, and the watch pins the same one, so the
        # store guards pass and this test still exercises the seller question it
        # was written for rather than short-circuiting on a config gap.
        _nextdata(
            availabilityStatus="IN_STOCK",
            priceInfo={"currentPrice": {"price": 229.99}},
            location={"storeIds": ["0"]},
        ),
        WALMART_URL,
    )
    watch = Watch(
        name="GO Plus +", retailer="walmart", target=WALMART_URL, max_price=80, store_id="0"
    )

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.UNKNOWN
    assert result.alertable is False
    assert "seller" in result.detail.lower()


def test_retailer_with_no_first_party_list_is_unknown_not_out_of_stock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A config gap is not a stock fact.

    `FIRST_PARTY.get(retailer, set())` returns an empty set for any retailer
    key not in the dict, so `named` is always empty and — for a page that does
    name its seller, as most schema.org markup does — `_pick` returns None.
    That used to become a confident OUT_OF_STOCK, when the truth is "this
    retailer has no first-party allow-list configured, so I cannot tell whose
    offer this is". REQUIREMENTS targets seven retailers, and every one of them
    arrives through this door, so the door has to stay guarded while they do.

    The example used to be `pokemoncenter`, and moving it is the point of this
    edit rather than a tidy-up. The moment a retailer key gains a FIRST_PARTY
    entry, a test written against it stops exercising WR-03 at all — it still
    passes, it just proves something else, and nothing goes red to say so. That
    is precisely how a guarantee gets hollowed out by an adapter that had every
    reason to be added.

    `costco` is chosen because it is named in the roadmap's narrowing rationale
    as deliberately out of scope, so it is the key least likely to be configured
    by a future plan. `pokemoncenter` was tempting — 02-04 established it as
    rung 4, refused at every rung — but "unreachable today" is a weaker promise
    than "out of scope on purpose", and the walls a retailer puts up can come
    down again.
    """
    _serve(
        monkeypatch,
        _ldjson(availability="https://schema.org/InStock", price="54.99",
                seller={"@type": "Organization", "name": "Costco Wholesale"}),
        "https://www.costco.com/product.1.html",
    )
    watch = Watch(
        name="GO Plus +", retailer="costco", target="https://www.costco.com/product.1.html"
    )

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK
    assert result.alertable is False
    assert "costco" in result.detail
    assert "costco" not in retailers.FIRST_PARTY, (
        "this test's whole subject is a retailer with no allow-list — configuring "
        "one silently turns it into a test of something else"
    )


def test_a_configured_retailer_still_reports_out_of_stock_for_a_third_party_offer(
    monkeypatch: pytest.MonkeyPatch, walmart_goplusplus: str
) -> None:
    """The WR-03 escape hatch must not swallow the genuine verdict.

    Walmart HAS an allow-list, and the fixture's offer is from a named
    reseller. "Walmart itself is not selling this" is a true stock fact, so it
    stays OUT_OF_STOCK rather than being softened to UNKNOWN along with the
    unconfigured case.
    """
    _serve(monkeypatch, walmart_goplusplus, WALMART_URL)
    watch = Watch(name="GO Plus +", retailer="walmart", target=WALMART_URL, store_id="0")

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.OUT_OF_STOCK
    assert "none first-party" in result.detail


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


#: A SKU somebody has actually seen resolve. The value here used to be
#: `6577129`, introduced as Best Buy's GO Plus + SKU — but it appears nowhere in
#: Best Buy's own search results, its legacy URL is refused, and no probe has
#: ever resolved it to a product page. Best Buy does not appear to carry the
#: GO Plus + at all (`docs/retailer-evidence.md`), so that string was a fixture
#: value dressed as a fact. `6216393` is Pokémon: Let's Go, Pikachu! — read live
#: at $59.99, InStock, sold by Best Buy.
BESTBUY_SKU = "6216393"


def _bestbuy_watch() -> Watch:
    return Watch(name="Let's Go, Pikachu!", retailer="bestbuy", target=BESTBUY_SKU)


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
    # Not the legacy `/site/-/<sku>.p` form this used to publish. That link is
    # refused by Best Buy now (HTTP/2 stream reset, reproducibly, across
    # unrelated SKUs), so every error Result here carried a dead URL onto a
    # status page somebody is meant to click. Both rungs share one helper so
    # they cannot drift into publishing different links for the same watch.
    assert result.url == f"https://www.bestbuy.com/site/searchpage.jsp?st={BESTBUY_SKU}"
    assert result.url == retailers.bestbuy_product_url(BESTBUY_SKU)
    assert result.availability is Availability.UNKNOWN
    assert result.detail, "a UNKNOWN verdict must still say why"
    # An error from the official API is still a rung-2 reading. Leaving the
    # default in place here would label a key-holder's UNKNOWN as a plain TLS
    # fetch, and the support matrix reads exactly this field to say which rung
    # Best Buy landed on — so the error paths have to carry it too, not just
    # the happy one.
    assert result.rung is Rung.API, f"{name}: an api error is still an api reading"
    assert result.degraded is False


def _bestbuy_url() -> str:
    return (
        f"https://api.bestbuy.com/v1/products(sku={BESTBUY_SKU})?apiKey={API_KEY}"
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
    assert result.rung is Rung.API
    assert result.degraded is False, "the sanctioned API is not a degraded transport"


# --------------------------------------------------------------------------
# Best Buy on rung 3: the browser adapter
# --------------------------------------------------------------------------


def _serve_rendered(monkeypatch: pytest.MonkeyPatch, html: str) -> None:
    """Make `check_bestbuy_browser`'s render return this HTML.

    Patches the module attribute rather than `boty.browser.fetch_rendered`, the
    same shape `_serve` uses for `get`, because that is the name
    `boty.retailers` actually looks up at call time — and because conftest's
    guard patches the layer below, so a test that got this wrong fails loudly
    instead of launching Chrome at bestbuy.com.
    """

    def _rendered(target: str, **kwargs: object) -> Page:
        return Page(url=target, status=200, text=html)

    monkeypatch.setattr(retailers, "fetch_rendered", _rendered)


def _raise_rendered(monkeypatch: pytest.MonkeyPatch, exc: Exception) -> None:
    def _rendered(target: str, **kwargs: object) -> Page:
        raise exc

    monkeypatch.setattr(retailers, "fetch_rendered", _rendered)


def test_bestbuy_sku_becomes_the_url_that_actually_resolves() -> None:
    """Both rungs build the link from one helper, and it is not the dead one.

    `/site/-/<sku>.p` is refused by Best Buy (HTTP/2 stream reset, reproducibly),
    so a Result carrying it published a link that does not load. Search on a
    bare SKU redirects to the product page instead — see
    `docs/retailer-evidence.md`.
    """
    url = retailers.bestbuy_product_url("6216393")

    assert url == "https://www.bestbuy.com/site/searchpage.jsp?st=6216393"
    assert ".p" not in url.rsplit("/", 1)[-1], "the legacy refused URL form is back"


def test_bestbuy_control_fixture_is_in_stock_priced_and_alertable(
    monkeypatch: pytest.MonkeyPatch, bestbuy_pikachu: str
) -> None:
    """The control has to be able to go green, and a price has to come with it.

    Price is not decoration here. `Result.alertable` returns False when a
    ceiling is configured and `price is None`, so an adapter that read
    availability and skipped price could never alert on a real product watch —
    it would look like it worked right up until the drop it was bought for.
    """
    _serve_rendered(monkeypatch, bestbuy_pikachu)
    watch = Watch(name="Let's Go, Pikachu!", retailer="bestbuy", target="6216393", control=True)

    result = retailers.check_bestbuy_browser(watch)

    assert result.availability is Availability.IN_STOCK
    assert result.price == 59.99
    assert result.alertable is True
    assert "Best Buy" in result.detail


def test_bestbuy_price_ceiling_still_bites_on_the_browser_rung(
    monkeypatch: pytest.MonkeyPatch, bestbuy_pikachu: str
) -> None:
    """A degraded reading is still subject to both flipper defences.

    Rung 3 changes how confident we are in the reading, not what counts as a
    restock — so the ceiling has to be applied to the price this path extracts,
    not merely to the ones rung 1 does.
    """
    _serve_rendered(monkeypatch, bestbuy_pikachu)
    watch = Watch(name="cheap thing", retailer="bestbuy", target="6216393", max_price=20)

    result = retailers.check_bestbuy_browser(watch)

    assert result.availability is Availability.IN_STOCK
    assert result.alertable is False, "$59.99 cleared a $20 ceiling"


def test_every_browser_reading_is_tagged_browser_and_degraded(
    monkeypatch: pytest.MonkeyPatch, bestbuy_pikachu: str
) -> None:
    """The success path and both failure paths, because a rung is a transport fact.

    An UNKNOWN produced by a browser that could not start is still a browser
    reading. Leaving the `Rung.TLS` default on the error paths would label it a
    plain page fetch, and the support matrix makes its claim on exactly this
    field.
    """
    watch = Watch(name="Let's Go, Pikachu!", retailer="bestbuy", target="6216393")

    _serve_rendered(monkeypatch, bestbuy_pikachu)
    ok = retailers.check_bestbuy_browser(watch)

    _raise_rendered(monkeypatch, Blocked("rendered challenge page matched 'robot or human'"))
    blocked = retailers.check_bestbuy_browser(watch)

    _raise_rendered(monkeypatch, FetchError("browser did not finish rendering within 45.0s"))
    failed = retailers.check_bestbuy_browser(watch)

    for result in (ok, blocked, failed):
        assert result.rung is Rung.BROWSER
        assert result.degraded is True
        assert result.url == "https://www.bestbuy.com/site/searchpage.jsp?st=6216393"


def test_bestbuy_page_with_no_product_markup_is_unknown_not_out_of_stock(
    monkeypatch: pytest.MonkeyPatch, bestbuy_unresolved_sku: str
) -> None:
    """Restated for this adapter deliberately, on a real page, not a synthetic one.

    The suite's most important assertion is repeated per adapter rather than
    assumed to carry over from GameStop's — every transport has its own way of
    getting lost. This fixture is the genuine article: Best Buy's response to a
    SKU that resolves to nothing is a search page listing a dozen other
    products with no schema.org Product markup on any of them. Reading that as
    OUT_OF_STOCK would be a confident wrong answer forever; reading one of
    those other products as the answer would be worse still.
    """
    _serve_rendered(monkeypatch, bestbuy_unresolved_sku)
    watch = Watch(name="not a real sku", retailer="bestbuy", target="6577129")

    result = retailers.check_bestbuy_browser(watch)

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK, (
        "an unreadable Best Buy page must never be reported as out-of-stock — "
        "that is the silent failure mode this project exists to prevent"
    )
    assert result.alertable is False
    assert result.price is None, "a page with no offers must not carry a price from somewhere else"
    assert result.detail


# --------------------------------------------------------------------------
# Binding the answer to the question: WR-03
# --------------------------------------------------------------------------


def _search_page(*products: tuple[str, str, str, float]) -> str:
    """A Best Buy search-results page carrying `Product` markup per result.

    The page Best Buy does not serve *today*, which is the entire point. The
    adapter's safety currently rests on a search-results template carrying no
    schema.org Product markup at all — a third party's SEO decision, reversible
    without notice, and adding Product+Offer markup to result cards is one of
    the most common changes a retailer makes. Neither shipped fixture can
    represent that page, so it is synthesised here.
    """
    blocks = "".join(
        f"""<script type="application/ld+json">{{
          "@context": "https://schema.org", "@type": "Product",
          "sku": "{sku}", "name": "{name}",
          "url": "https://www.bestbuy.com/product/{slug}/ABC123/sku/{sku}",
          "offers": {{"@type": "Offer", "price": {price},
                     "availability": "https://schema.org/InStock",
                     "seller": {{"@type": "Organization", "name": "Best Buy"}}}}
        }}</script>"""
        for sku, name, slug, price in products
    )
    return f"<html><head>{blocks}</head><body>search results</body></html>"


def test_a_search_page_of_other_products_is_unknown_not_somebody_elses_stock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The worst outcome this project can produce: confident, wrong, plausible.

    `bestbuy_product_url` feeds a bare SKU to Best Buy's search and trusts the
    redirect. Nothing bound the page that came back to the SKU that was asked
    for. If Best Buy adds Product markup to its result cards, `_pick` returns
    the cheapest available first-party offer on the page — a $9.99 HDMI cable
    among the results — and the monitor reports it as the stock state of the
    watched product, under the watch's own name.

    Nothing else would catch it: Best Buy's only configured watch is a control,
    the control's own SKU still resolves, so health stays green and the
    dashboard stays green while a product watch reads somebody else's inventory.
    """
    _serve_rendered(
        monkeypatch,
        _search_page(
            ("6665817", "Best Buy essentials HDMI cable", "bbe-hdmi", 9.99),
            ("6554912", "Insignia screen protector", "insignia-sp", 12.99),
        ),
    )
    watch = Watch(name="Pokémon GO Plus +", retailer="bestbuy", target="6577129", max_price=80)

    result = retailers.check_bestbuy_browser(watch)

    assert result.availability is Availability.UNKNOWN, (
        f"read {result.availability.value} at ${result.price} from a page that "
        "does not contain the requested SKU at all"
    )
    assert result.price is None, "a price was carried over from an unrelated product"
    assert result.alertable is False
    assert "6577129" in result.detail, "the detail must name the SKU that did not resolve"


def test_the_requested_sku_is_read_and_the_cheaper_neighbours_are_not(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The case a whole-page substring check passes while still being wrong.

    "Does the requested SKU appear in this HTML" is not the question. It appears
    71 times in the *control* fixture — recommendation rails, "customers also
    viewed", breadcrumbs. So a search page listing the requested product
    alongside eleven others contains it too, and a page-level check would wave
    the page through and let `_pick` return the cheapest offer on it regardless.

    The binding has to be at the node, not at the page: the offers read must
    come from the `Product` whose `sku` *is* the one asked for. `boty.parse`
    already reasoned exactly this way for Walmart — `_WALMART_PRODUCT_PATH`
    addresses the buy box explicitly because "a generic walk happily reports a
    $12 screen protector as your restock". Best Buy went through the generic
    walk.
    """
    _serve_rendered(
        monkeypatch,
        _search_page(
            ("6665817", "Best Buy essentials HDMI cable", "bbe-hdmi", 9.99),
            ("6216393", "Pokémon: Let's Go, Pikachu!", "pikachu", 59.99),
            ("6554912", "Insignia screen protector", "insignia-sp", 12.99),
        ),
    )
    watch = Watch(name="Let's Go, Pikachu!", retailer="bestbuy", target="6216393")

    result = retailers.check_bestbuy_browser(watch)

    assert result.availability is Availability.IN_STOCK
    assert result.price == 59.99, (
        f"read ${result.price} — the cheapest offer on the page, not the "
        "requested product's"
    )


def test_the_real_control_fixture_still_binds_to_its_own_sku(
    monkeypatch: pytest.MonkeyPatch, bestbuy_pikachu: str
) -> None:
    """The identity check must not cost the control its green.

    A real Best Buy product page carries dozens of other SKUs in its
    recommendation rails. If the binding were implemented as "this page mentions
    exactly one SKU" it would fail here, and a fail-safe UNKNOWN on the one
    control that proves this retailer's detector works is a broken gate, not a
    safe one.
    """
    _serve_rendered(monkeypatch, bestbuy_pikachu)
    right = retailers.check_bestbuy_browser(
        Watch(name="Let's Go, Pikachu!", retailer="bestbuy", target="6216393")
    )
    # Same bytes, different question. The page mentions 6665817 in its rails.
    wrong = retailers.check_bestbuy_browser(
        Watch(name="something else", retailer="bestbuy", target="6665817")
    )

    assert right.availability is Availability.IN_STOCK
    assert right.price == 59.99
    assert wrong.availability is Availability.UNKNOWN, (
        "a SKU that merely appears in this page's recommendation rails was read "
        "as the page's own product"
    )


def test_an_unresolved_sku_is_diagnosed_as_unresolved_not_as_our_parser(
    monkeypatch: pytest.MonkeyPatch, bestbuy_unresolved_sku: str
) -> None:
    """IN-03: "page shape changed?" points the reader at a working extractor.

    Best Buy's search-miss is a known, evidenced branch
    (`docs/retailer-evidence.md`), not an unknown one. Blaming our own parser
    for it is the same misattribution the phase fixed twice for Imperva and
    Akamai walls, one layer up.
    """
    _serve_rendered(monkeypatch, bestbuy_unresolved_sku)

    result = retailers.check_bestbuy_browser(
        Watch(name="not a real sku", retailer="bestbuy", target="6577129")
    )

    assert result.availability is Availability.UNKNOWN
    assert "6577129" in result.detail
    assert "page shape changed" not in result.detail, (
        "a known search-miss was reported as an unknown parser failure"
    )


def test_blocked_browser_render_is_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    """A bot wall that renders is still a bot wall, not an out-of-stock reading."""
    _raise_rendered(monkeypatch, Blocked("rendered challenge page matched 'robot or human'"))

    result = retailers.check_bestbuy_browser(_bestbuy_watch())

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK
    assert "blocked" in result.detail
    assert result.url == retailers.bestbuy_product_url(BESTBUY_SKU)


def test_failed_browser_render_is_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    _raise_rendered(monkeypatch, FetchError("chrome exited with status 127"))

    result = retailers.check_bestbuy_browser(_bestbuy_watch())

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK
    assert "fetch failed" in result.detail
    assert "127" in result.detail


def test_browser_failures_do_not_publish_this_machines_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`Result.detail` is served over HTTP, and only this rung talks about the host.

    The browser transport reports failures in terms of the local machine — a
    missing binary, a Chrome that would not start, a profile directory. Those
    strings go straight into `served/boty/status.json`. A restock monitor has
    no business telling whoever can reach the dashboard where this user's home
    directory is.
    """
    home = os.path.expanduser("~")
    monkeypatch.setenv(retailers.BROWSER_PATH_ENV, f"{home}/.cache/secretdir/chrome")
    _raise_rendered(
        monkeypatch,
        FetchError(f"could not launch {home}/.cache/secretdir/chrome from {home}/projects"),
    )

    result = retailers.check_bestbuy_browser(_bestbuy_watch())

    assert result.availability is Availability.UNKNOWN
    assert home not in result.detail, "the browser path leaked a host filesystem path"
    assert "secretdir" not in result.detail
    assert result.detail, "a redacted UNKNOWN must still say why"


def test_the_browser_rung_is_never_reached_without_being_asked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No browser starts in this suite, with or without BOTY_BROWSER_PATH set.

    The offline guarantee is the reason these tests are worth anything, and rung
    3 is the one transport that could break it without tripping a single socket
    patch — Chrome does the fetching in a subprocess. So this deliberately does
    NOT patch `retailers.fetch_rendered`: what must happen is conftest's guard
    firing, un-downgraded, rather than a live render or a bland UNKNOWN.
    """
    monkeypatch.delenv(retailers.BROWSER_PATH_ENV, raising=False)

    with pytest.raises(BaseException, match="test attempted a live network request") as caught:
        retailers.check_bestbuy_browser(_bestbuy_watch())

    assert not isinstance(caught.value, Exception), (
        "the guard was downgraded into an ordinary exception, so check_bestbuy_browser "
        "would have turned a live-network attempt into a quiet UNKNOWN verdict"
    )


# --------------------------------------------------------------------------
# The dispatch seam: same watch, two rungs
# --------------------------------------------------------------------------


def _bestbuy_config(api_key: str) -> Config:
    return Config(watches=[_bestbuy_watch()], bestbuy_api_key=api_key)


def test_a_key_upgrades_the_same_watch_from_browser_to_api(
    monkeypatch: pytest.MonkeyPatch, bestbuy_pikachu: str
) -> None:
    """One YAML entry, two rungs, and the flag follows the transport.

    `scripts/control_check.py` builds its checker with this same function, so
    this is the routing the live gate exercises too. The point of the assertion
    pair is that nothing about the *watch* changes: the SKU, the name and the
    config entry are identical, and only the presence of a credential decides
    whether the reading is degraded.
    """
    watch = _bestbuy_watch()

    _serve_rendered(monkeypatch, bestbuy_pikachu)
    without_key = _make_checker(_bestbuy_config(""))(watch)

    _serve(monkeypatch, '{"products": [{"salePrice": 59.99, "onlineAvailability": true}]}')
    with_key = _make_checker(_bestbuy_config(API_KEY))(watch)

    assert without_key.rung is Rung.BROWSER
    assert without_key.degraded is True

    assert with_key.rung is Rung.API
    assert with_key.degraded is False, "the sanctioned API is not a degraded transport"

    # Same product, same verdict — the rung is the only thing that moved.
    assert without_key.availability is with_key.availability is Availability.IN_STOCK
    assert without_key.price == with_key.price == 59.99


def test_no_key_does_not_mean_no_best_buy(monkeypatch: pytest.MonkeyPatch, bestbuy_pikachu: str) -> None:
    """The regression this whole plan exists to prevent.

    Best Buy used to be gated on a credential that needs manual approval and
    rejects free email domains, which made it a footnote rather than a
    supported retailer. A fresh clone with nothing configured must get a real
    stock verdict.
    """
    _serve_rendered(monkeypatch, bestbuy_pikachu)

    result = _make_checker(_bestbuy_config(""))(_bestbuy_watch())

    assert result.availability is Availability.IN_STOCK
    assert result.detail and "key" not in result.detail.lower()


def test_non_bestbuy_watches_are_untouched_by_the_bestbuy_branch(
    monkeypatch: pytest.MonkeyPatch, gamestop_ps5: str
) -> None:
    """A browser is not a strict upgrade — headless Chrome is walled by GameStop.

    So the new arm must be exactly that, an arm. If `_make_checker` ever
    started routing everything through rung 3, GameStop and Walmart would break
    while Best Buy looked fine.
    """
    _serve(monkeypatch, gamestop_ps5)
    _raise_rendered(monkeypatch, AssertionError("a GameStop watch was routed through the browser"))

    result = _make_checker(_bestbuy_config(""))(
        Watch(name="PS5", retailer="gamestop", target=GAMESTOP_URL, control=True)
    )

    assert result.availability is Availability.IN_STOCK
    assert result.rung is Rung.TLS
    assert result.degraded is False


# --------------------------------------------------------------------------
# Nintendo: rung 1, no adapter, and the only first-party GO Plus + we have
# --------------------------------------------------------------------------

NINTENDO_URL = "https://www.nintendo.com/us/store/products/pokemon-go-plus-plus-112387/"
NINTENDO_HDMI_URL = "https://www.nintendo.com/us/store/products/hdmi-cable-104947/"


def test_nintendo_goplusplus_reads_out_of_stock_at_msrp(
    monkeypatch: pytest.MonkeyPatch, nintendo_goplusplus: str
) -> None:
    """The most credible restock signal this project has, and it needs no adapter.

    Nintendo makes the GO Plus +, lists it at $54.99 — MSRP to the cent — and
    has no marketplace, so neither flipper defence has anything to defend
    against here. `check_html` as shipped reads it: no new extractor, no
    `_make_checker` branch, one `FIRST_PARTY` line.

    The price assertion is not decoration. `Result.alertable` is False whenever
    a ceiling is set and `price is None`, so a reading that got availability
    right and price wrong would look healthy right up until the drop.
    """
    _serve(monkeypatch, nintendo_goplusplus, NINTENDO_URL)
    watch = Watch(name="GO Plus +", retailer="nintendo", target=NINTENDO_URL, max_price=80)

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.OUT_OF_STOCK
    assert result.price == 54.99
    assert result.alertable is False
    assert "Nintendo of America" in result.detail
    assert result.rung is Rung.TLS
    assert result.degraded is False, "rung 1 is not a degraded transport"


def test_nintendo_control_is_in_stock_priced_and_alertable(
    monkeypatch: pytest.MonkeyPatch, nintendo_hdmi: str
) -> None:
    """The control has to be able to go green, with a price attached."""
    _serve(monkeypatch, nintendo_hdmi, NINTENDO_HDMI_URL)
    watch = Watch(name="HDMI cable", retailer="nintendo", target=NINTENDO_HDMI_URL, control=True)

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.IN_STOCK
    assert result.price == 7.99
    assert result.alertable is True
    assert "InStock" in result.detail


def test_nintendo_is_first_party_but_not_a_marketplace() -> None:
    """Membership in each set is a claim about the site, decided by evidence.

    Nintendo's store has no third-party seller surface at all — no buy box, no
    "other sellers", nobody but Nintendo of America who can sell on it. So it
    belongs in FIRST_PARTY and must stay out of MARKETPLACES, which is what
    keeps `_pick`'s unattributed-offer fallback available for a future page that
    drops the seller node. Putting it in MARKETPLACES "to be safe" would be the
    opposite of safe: every unattributed offer would read UNKNOWN and the
    control could never go green.
    """
    assert "nintendo" in retailers.FIRST_PARTY
    assert "nintendo" not in retailers.MARKETPLACES
    assert "nintendo of america inc." in retailers.FIRST_PARTY["nintendo"], (
        "the allow-list is compared against `o.seller.strip().lower()`, and this "
        "is the literal string Nintendo's schema.org markup carries"
    )


def test_unparseable_nintendo_page_is_unknown_not_out_of_stock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Restated for this retailer deliberately, not assumed to carry over.

    Every retailer has its own way of getting lost, and this is the assertion
    the whole project exists to keep true.
    """
    _serve(monkeypatch, "<html><body>Whoops! - Nintendo Official Site</body></html>", NINTENDO_URL)
    watch = Watch(name="GO Plus +", retailer="nintendo", target=NINTENDO_URL, max_price=80)

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK, (
        "an unreadable Nintendo page must never be reported as out-of-stock — "
        "that is the silent failure mode this project exists to prevent"
    )
    assert result.alertable is False
    assert result.price is None
    assert result.detail


def test_blocked_nintendo_fetch_is_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    _raise(monkeypatch, Blocked("challenge page matched 'pardon our interruption' (HTTP 200)"))
    watch = Watch(name="GO Plus +", retailer="nintendo", target=NINTENDO_URL)

    result = retailers.check_html(watch)

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK
    assert "blocked" in result.detail
    assert result.url == NINTENDO_URL


def test_failed_nintendo_fetch_is_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    _raise(monkeypatch, FetchError("HTTP 404"))
    watch = Watch(name="GO Plus +", retailer="nintendo", target=NINTENDO_URL)

    result = retailers.check_html(watch)

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK
    assert "fetch failed" in result.detail
    assert "404" in result.detail


def test_nintendo_is_not_routed_through_the_browser(
    monkeypatch: pytest.MonkeyPatch, nintendo_hdmi: str
) -> None:
    """Rung 1 means rung 1, through the same dispatch the live gate uses.

    A browser is not a strict upgrade — headless Chrome is walled by GameStop
    and by Pokémon Center — so a retailer that reads fine on rung 1 must never
    quietly acquire a Chrome process because `_make_checker` grew an arm.
    """
    _serve(monkeypatch, nintendo_hdmi, NINTENDO_HDMI_URL)
    _raise_rendered(monkeypatch, AssertionError("a Nintendo watch was routed through the browser"))

    result = _make_checker(_bestbuy_config(""))(
        Watch(name="HDMI cable", retailer="nintendo", target=NINTENDO_HDMI_URL, control=True)
    )

    assert result.availability is Availability.IN_STOCK
    assert result.rung is Rung.TLS
    assert result.degraded is False


# --------------------------------------------------------------------------
# The shipped config: every retailer answers for itself
# --------------------------------------------------------------------------


def test_every_configured_retailer_has_a_control_watch() -> None:
    """REQ-06, pinned offline as well as in `make verify`.

    `scripts/control_check.py` fails the live gate on this, but only where
    there is a network. A retailer added with no control is a detector nothing
    can verify — a silent regression in it would look exactly like a drought —
    and that is a fact about the config file, knowable without asking anybody.
    """
    cfg = Config.load(Path(__file__).resolve().parent.parent / "config" / "products.yaml")

    configured = {w.retailer for w in cfg.watches}
    verified = {w.retailer for w in cfg.watches if w.control}

    assert configured, "the shipped config configures no retailers at all"
    assert sorted(configured - verified) == []


def test_the_shipped_bestbuy_watches_are_skus_with_no_ceiling_on_the_control() -> None:
    """Both rungs read `target` as a SKU, and a ceiling on a control is meaningless.

    A `max_price` on a control would make `alertable` depend on the market
    rather than on the detector, which is the one thing a control is chosen to
    be independent of.
    """
    cfg = Config.load(Path(__file__).resolve().parent.parent / "config" / "products.yaml")
    bestbuy = [w for w in cfg.watches if w.retailer == "bestbuy"]

    assert bestbuy, "Best Buy is supported but not configured"
    controls = [w for w in bestbuy if w.control]
    assert controls, "Best Buy has no control watch"

    for w in bestbuy:
        assert not w.target.startswith("http"), f"{w.name}: target must be a SKU, not a URL"
        assert w.target.isdigit(), f"{w.name}: {w.target!r} is not a Best Buy SKU"
    for w in controls:
        assert w.max_price is None, f"{w.name}: a control must not carry a price ceiling"


def test_the_shipped_nintendo_watches_are_urls_with_no_ceiling_on_the_control() -> None:
    """Nintendo reads `target` as a URL — the opposite of Best Buy, on purpose.

    Nintendo publishes a 36,530-entry store sitemap and its product URLs are
    stable and derivable from it, so there is nothing to resolve and no reason
    to route through a search page. Best Buy's SKU indirection exists because
    Best Buy's URLs are *not* derivable; copying that shape here would be
    cargo-culting a workaround for a problem this retailer does not have.
    """
    cfg = Config.load(Path(__file__).resolve().parent.parent / "config" / "products.yaml")
    nintendo = [w for w in cfg.watches if w.retailer == "nintendo"]

    assert nintendo, "Nintendo is supported but not configured"
    controls = [w for w in nintendo if w.control]
    assert controls, "Nintendo has no control watch"

    for w in nintendo:
        assert w.target.startswith("https://www.nintendo.com/"), f"{w.name}: {w.target!r}"
    for w in controls:
        assert w.max_price is None, f"{w.name}: a control must not carry a price ceiling"


def test_no_retailer_is_configured_without_a_page_we_have_actually_read() -> None:
    """The anti-padding gate, and it is mechanical rather than a matter of trust.

    Phase 2's criterion is a retailer *count*, which is exactly the kind of
    target that invites a YAML entry for a site nobody has ever successfully
    fetched. `scripts/control_check.py` already refuses a retailer with no
    control, and `assess_health` already refuses one whose control cannot be
    read — but both need a network to say so, and neither runs in CI.

    A fixture cannot be faked into existence the same way: `boty.fixtures.capture`
    only writes one after a live fetch that was not blocked, and refuses outright
    on a challenge page. So "there is a frozen page on disk for this retailer" is
    a durable, offline claim that we have read it at least once.

    Pokémon Center is the case in point. 02-04 found it refused at every rung and
    it has no fixture, so if a future edit adds a `retailer: pokemoncenter` watch
    to make the count read five, this goes red — and points at
    `docs/retailer-evidence.md`, where the reason is written down.
    """
    cfg = Config.load(Path(__file__).resolve().parent.parent / "config" / "products.yaml")
    root = Path(__file__).resolve().parent / "fixtures"

    unread = sorted(r for r in {w.retailer for w in cfg.watches} if not list((root / r).glob("*.html")))

    assert not unread, (
        f"configured with no captured page to show for it: {unread}. Either capture "
        f"one (boty capture-fixture) or take the watch out — a retailer nobody has "
        f"read is a detector that cannot detect, and it inflates the retailer count "
        f"while doing it. See docs/retailer-evidence.md."
    )


# --------------------------------------------------------------------------
# Target: the verdict in the evidence log and the shipped tree must agree
# --------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_evidence_check() -> object:
    """Import `scripts/evidence_check.py` by path — `scripts/` is not a package.

    The same `spec_from_file_location` idiom `tests/test_evidence_check.py` and
    `tests/test_support_matrix.py` use. This file used to carry its own splitter
    and its own verdict test instead, and the two implementations had already
    drifted apart in both dimensions at once — see WR-04 in `03-REVIEW.md`.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "evidence_check_for_target_guard", _REPO_ROOT / "scripts" / "evidence_check.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_EVIDENCE = _load_evidence_check()
_EVIDENCE_PATH = _REPO_ROOT / "docs" / "retailer-evidence.md"
_REFUSED: str = _EVIDENCE.REFUSED  # type: ignore[attr-defined]


def _target_verdict(evidence_text: str) -> str:
    """The one ANCHORED verdict line of the one `## Target…` section.

    WHY THIS IS NOT `_REFUSED in _target_section(text)`, WHICH IS WHAT IT WAS.

    The shipped Target section contains the exact string `**Verdict: REFUSED**`
    three times: once as the machine-readable verdict line, and twice inside
    prose explaining the grammar ("So the verdict is `**Verdict: REFUSED**`, the
    primary reason is…", and the paragraph describing rule 2). Only the first is
    a verdict. A bare `in` test therefore reports REFUSED for a document that no
    longer says it — the REACHABLE branch below, which holds the entire
    allow-list drift check, could never execute. That is the identical defect
    this phase was created to remove, one file over.

    Measured against the shipped tree before the fix:

        anchored verdict lines in Target section: 1
        raw substring occurrences in Target section: 3

    `evidence_check` already exported the anchored, section-scoped primitives.
    This uses them rather than re-deriving a weaker pair.
    """
    sections = _EVIDENCE.split_sections(evidence_text)  # type: ignore[attr-defined]
    bodies = _EVIDENCE.sections_for("Target", sections)  # type: ignore[attr-defined]
    assert len(bodies) == 1, f"expected exactly one `## Target` section, found {len(bodies)}"
    lines = _EVIDENCE.verdict_lines(bodies[0])  # type: ignore[attr-defined]
    assert len(lines) == 1, f"expected exactly one Target verdict line, found {lines}"
    return str(lines[0])


def _target_disagreements(
    *,
    evidence_text: str,
    configured: set[str],
    controlled: set[str],
    fixture_names: list[str],
    allow_list: set[str],
    fixture_sellers: list[str],
) -> list[str]:
    """Every way the Target verdict and the shipped tree could contradict each other.

    Takes its inputs as plain values rather than reading the repo, so the tests
    below can drive BOTH branches and watch each guard go red. A guard only ever
    exercised on the branch the repo happens to be on is a guard nobody has seen
    fail, which is the species this phase exists to replace.

    **The tree moved to the REACHABLE branch on 2026-08-03**, so the directions
    have swapped: the REACHABLE checks now run against the real repo, and the
    REFUSED checks are driven off a synthetic copy of the document. Both are
    still watched failing, which is the whole point of taking values rather than
    reading the repo.
    """
    refused = _target_verdict(evidence_text) == _REFUSED
    problems: list[str] = []

    if refused:
        if "target" in configured:
            problems.append(
                "docs/retailer-evidence.md records `**Verdict: REFUSED**` for Target while "
                "config/products.yaml configures a target watch. Target's own Terms & "
                "Conditions forbid collecting prices with data-gathering tools, so a watch "
                "here is a request the evidence log says we must not make — not merely a "
                "detector that would read nothing."
            )
        if fixture_names:
            problems.append(
                f"Target is REFUSED but tests/fixtures/target/ holds {sorted(fixture_names)}. "
                "No target.com page was ever fetched, so any HTML under that directory came "
                "from somewhere other than Target and must not be shipped as its capture."
            )
        return problems

    # The REACHABLE branch. Vacuous against today's tree by construction — and
    # exercised anyway, below, because these are the assertions that have to be
    # right on the day somebody registers Target, which is the day nobody will
    # be re-reading this reasoning.
    if "target" not in configured:
        problems.append("Target is REACHABLE but config/products.yaml configures no target watch")
    if "target" not in controlled:
        problems.append(
            "Target is REACHABLE and configured but has no control watch — nothing could "
            "ever verify the detector"
        )
    if not fixture_names:
        problems.append("Target is REACHABLE but no page was frozen under tests/fixtures/target/")
    elif not any(seller.strip().lower() in allow_list for seller in fixture_sellers):
        problems.append(
            f"FIRST_PARTY['target'] is {sorted(allow_list)}, and no seller read off the "
            f"shipped Target fixture ({sorted(fixture_sellers)}) is a member of it. Target "
            "publishes NO seller name at any rung, so this allow-list is not a claim about "
            "Target's markup — it is a claim about `parse.add_to_cart_offers`, which emits "
            "`parse.TARGET_FIRST_PARTY_SELLER` when a PDP carries no Target Plus partner "
            "block. If the two ever drift apart the failure is silent and maximally wrong: "
            "`target` is in MARKETPLACES, so `_pick` finds no named offer, the unattributed "
            "fallback is disabled, and `_verdict_from_html` answers a page it read perfectly "
            "with a CONFIDENT OUT_OF_STOCK. Pin them together, do not loosen either."
        )
    return problems


def test_the_target_verdict_and_the_shipped_tree_agree() -> None:
    """Target is REACHABLE, so the shipped tree must actually back that up.

    The tree moved onto this branch on 2026-08-03: a `retailer: target` control
    watch, a rung-3 fixture, and an allow-list that matches what the reader
    emits. Not a tautology in this direction either — deleting the watch, the
    control or the fixture turns it red, and so does an allow-list that no
    longer matches the reader.
    """
    cfg = Config.load(_REPO_ROOT / "config" / "products.yaml")
    fixture_dir = _REPO_ROOT / "tests" / "fixtures" / "target"
    fixture_paths = sorted(fixture_dir.glob("*.html"))

    # Read the seller names with the SAME extractor the checker uses, so this
    # cannot pass against a fixture `_pick` would read differently.
    #
    # `add_to_cart_offers`, and that substitution is the point rather than a
    # detail. This used to call `ldjson_offers`/`nextdata_offers`, which return
    # None on every Target page ever served — so on the REACHABLE branch the
    # seller list would be empty and this guard would fire for a reason that has
    # nothing to do with drift. Same guard, pointed at the reader that actually
    # reads this retailer.
    sellers: list[str] = []
    for path in fixture_paths:
        html = path.read_text(encoding="utf-8", errors="replace")
        offers = parse.add_to_cart_offers(html) or []
        sellers.extend(o.seller for o in offers if o.seller)

    problems = _target_disagreements(
        evidence_text=_EVIDENCE_PATH.read_text(encoding="utf-8"),
        configured={w.retailer for w in cfg.watches},
        controlled={w.retailer for w in cfg.watches if w.control},
        fixture_names=[p.name for p in fixture_paths],
        allow_list=retailers.FIRST_PARTY.get("target", set()),
        fixture_sellers=sellers,
    )

    assert problems == [], "\n".join(problems)


def test_the_target_allow_list_entry_now_states_what_our_own_reader_emits() -> None:
    """The entry stopped being a guess, and this pins what replaced it.

    `FIRST_PARTY["target"]` could never be verified against Target's markup:
    Target publishes no seller name at any rung, so there was no live string to
    widen it to. It is now a claim about OUR side of the boundary — the literal
    `parse.add_to_cart_offers` emits when a PDP carries no Target Plus partner
    block — and that claim is checkable, so it is checked here rather than
    described in a comment.
    """
    reader_first_party = parse.add_to_cart_offers(
        _target_control_html()
    )
    assert reader_first_party is not None
    assert reader_first_party[0].seller == parse.TARGET_FIRST_PARTY_SELLER
    assert parse.TARGET_FIRST_PARTY_SELLER in retailers.FIRST_PARTY["target"], (
        "the reader's first-party literal and the allow-list are two halves of one "
        "claim; drifting them apart returns a CONFIDENT OUT_OF_STOCK on a readable page"
    )

    assert "target" in retailers.MARKETPLACES, (
        "Target Plus is a real third-party marketplace, so the unattributed-offer "
        "fallback must stay disabled for it — removing it is what would let a "
        "reseller listing alert"
    )

    partner = (
        '<a data-test="targetPlusExtraInfoSection" href="/sp/joyin/-/N-10006960">'
        "<span>Sold &amp; shipped by </span><span>Joyin</span></a>"
    )
    partner_offers = parse.add_to_cart_offers(_target_control_html(partner=partner))
    assert partner_offers is not None
    assert partner_offers[0].seller == "Joyin"
    assert partner_offers[0].seller.strip().lower() not in retailers.FIRST_PARTY["target"], (
        "a Target Plus partner must never land inside the first-party allow-list"
    )


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        pytest.param(
            {"configured": {"gamestop", "target"}},
            "configures a target watch",
            id="a target watch added against a REFUSED verdict",
        ),
        pytest.param(
            {"fixture_names": ["goplusplus.html"]},
            "tests/fixtures/target/",
            id="a target fixture committed against a REFUSED verdict",
        ),
    ],
)
def test_the_refused_branch_catches_a_tree_that_contradicts_it(
    kwargs: dict[str, object], expected: str
) -> None:
    """Watch the REFUSED branch fail. Each case is a real edit somebody could make.

    Driven off a SYNTHETIC refused copy of the document from here on: the tree
    moved to REACHABLE on 2026-08-03, so reading the real file would silently
    take the other branch and this test would assert nothing. The branch itself
    is unchanged and still has to work — Target could be dropped again.
    """
    base: dict[str, object] = {
        "evidence_text": _synthetic_refused_target(),
        "configured": {"gamestop"},
        "controlled": {"gamestop"},
        "fixture_names": [],
        "allow_list": {"target"},
        "fixture_sellers": [],
    }
    problems = _target_disagreements(**{**base, **kwargs})  # type: ignore[arg-type]

    assert len(problems) == 1
    assert expected in problems[0]


def test_a_reachable_target_whose_seller_string_drifted_is_caught() -> None:
    """The drift guard, and it fails OFFLINE rather than waiting for a control.

    `FIRST_PARTY['target']` and what `parse.add_to_cart_offers` emits are two
    halves of one claim. `"Target Corporation"` stands in for the reader having
    drifted away from the allow-list — a rename on either side. That mismatch is
    exactly what produces a confident OUT_OF_STOCK on a page read perfectly:
    `target` is in MARKETPLACES, so `_pick` finds no named offer and the
    unattributed fallback is disabled.
    """
    problems = _target_disagreements(
        # The real document, which now records REACHABLE. The `.replace(_REFUSED,
        # …)` this used to carry is worse than a no-op today: the anchored line no
        # longer says REFUSED, so it would rewrite the two surviving PROSE
        # mentions instead and could mint a second anchored verdict line.
        evidence_text=_EVIDENCE_PATH.read_text(encoding="utf-8"),
        configured={"target"},
        controlled={"target"},
        fixture_names=["control-dust-cloths.html"],
        allow_list={"target"},
        fixture_sellers=["Target Corporation"],
    )

    assert len(problems) == 1
    assert "no seller read off the shipped Target fixture" in problems[0]
    assert "CONFIDENT OUT_OF_STOCK" in problems[0]


_REACHABLE_TARGET = "**Verdict: REACHABLE (rung 3)**"


def _flip_only_the_anchored_target_verdict(evidence_text: str) -> str:
    """The Target section's real verdict LINE flipped to REFUSED, prose untouched.

    Inverted on 2026-08-03 when the tree moved: it used to flip REFUSED to
    REACHABLE. The purpose is unchanged and is the reason it exists at all — the
    other tests here flip a verdict with a whole-document `.replace`, which
    cannot tell an anchored reader from a substring one. This changes exactly the
    one line a person editing the log would change.

    The surviving prose mentions are what make that distinction observable, and
    the count assertion is what stops this helper quietly becoming a no-op. The
    Target section still quotes `**Verdict: REFUSED**` **twice** in prose — once
    explaining the grammar, once describing rule 2 — so flipping the anchored
    line to REFUSED must produce three.
    """
    start = evidence_text.index("\n## Target")
    end = evidence_text.index("\n## ", start + 1)
    section = evidence_text[start:end]

    before = section.count(_REFUSED)
    assert before == 2, (
        "this helper depends on the section quoting the REFUSED string in prose "
        f"exactly twice; found {before}"
    )
    flipped = section.replace(f"\n{_REACHABLE_TARGET}\n", f"\n{_REFUSED}\n", 1)
    assert flipped != section, "no anchored verdict line found to flip"
    assert flipped.count(_REFUSED) == 3, (
        "the point of this helper is that the prose mentions survive the flip; "
        f"found {flipped.count(_REFUSED)} rather than 3"
    )
    return evidence_text[:start] + flipped + evidence_text[end:]


def _synthetic_refused_target() -> str:
    """The shipped document with Target's anchored verdict flipped back to REFUSED.

    The REFUSED branch of the guard has to stay watched failing now that the tree
    is on the other one. Built from the real file rather than typed out, so it
    cannot drift away from the document's actual grammar.
    """
    return _flip_only_the_anchored_target_verdict(
        _EVIDENCE_PATH.read_text(encoding="utf-8")
    )


def test_flipping_only_the_real_verdict_line_switches_the_guard_to_the_refused_branch() -> None:
    """The hole CR-01 found, still pinned — now from the other side.

    The original defect: `_REFUSED in section` reported REFUSED for a document
    whose verdict line said REACHABLE, because the section quotes the string in
    prose too. The anchored reader fixed it. The tree has since moved onto the
    REACHABLE branch, so the test that proves the reader is anchored has to move
    with it — flip the one real verdict LINE to REFUSED, leave the prose alone,
    and the guard must follow the line rather than the prose.

    A substring reader fails this in the obvious direction now: it already sees
    two REFUSED mentions in a REACHABLE document, so it would report the REFUSED
    branch before anything was flipped at all.
    """
    flipped = _flip_only_the_anchored_target_verdict(
        _EVIDENCE_PATH.read_text(encoding="utf-8")
    )

    assert _target_verdict(flipped) == _REFUSED, (
        "the guard did not follow the anchored line onto the REFUSED branch"
    )

    problems = _target_disagreements(
        evidence_text=flipped,
        configured={"target"},
        controlled={"target"},
        fixture_names=["control-dust-cloths.html"],
        allow_list={"target"},
        fixture_sellers=["target"],
    )

    assert problems, "the REFUSED branch did not run: the selector is still a substring test"
    assert len(problems) == 2
    assert "configures a target watch" in problems[0]
    assert "tests/fixtures/target/" in problems[1]


def test_the_prose_mentions_alone_do_not_drag_the_guard_onto_the_refused_branch() -> None:
    """The mirror, so the fix cannot be "always take the REFUSED branch".

    The shipped document records REACHABLE on its anchored line while still
    quoting `**Verdict: REFUSED**` twice in prose — the grammar explanation and
    the rule-2 paragraph. A substring reader would take the REFUSED branch on
    that, which is now the failure with teeth: it would demand the removal of a
    watch, a control and a fixture that are all correct.
    """
    text = _EVIDENCE_PATH.read_text(encoding="utf-8")

    assert _target_verdict(text) == _REACHABLE_TARGET
    assert text.count(_REFUSED) > 1, (
        "this test is only meaningful while the document quotes the string in prose too"
    )


def test_the_target_guard_reads_the_evidence_log_through_the_honesty_gate() -> None:
    """One splitter and one verdict grammar for this document, not two.

    Three independent readers of `docs/retailer-evidence.md` existed, and two of
    them had ALREADY drifted apart in both available dimensions at once: this
    file's splitter was a `split("\\n## ")` list while the gate's was a dict, and
    this file's verdict test was a bare `in` while the gate's was line-anchored.
    Each disagreement was a live defect, and the correct implementation was
    split one to each file — WR-01 belonged to the gate, CR-01 belonged here, and
    neither had both.

    The identity check is the load-bearing half: `_REFUSED` must BE the gate's
    constant, not a retyped copy that can be edited on one side. (Verified: two
    equal literals in separate modules are distinct objects in CPython, so this
    fails if the string is retyped.)
    """
    assert _REFUSED is _EVIDENCE.REFUSED  # type: ignore[attr-defined]

    text = _EVIDENCE_PATH.read_text(encoding="utf-8")
    through_the_gate = _EVIDENCE.verdict_lines(  # type: ignore[attr-defined]
        _EVIDENCE.sections_for(  # type: ignore[attr-defined]
            "Target", _EVIDENCE.split_sections(text)  # type: ignore[attr-defined]
        )[0]
    )
    assert _target_verdict(text) == through_the_gate[0]


def test_the_target_guard_inherits_the_gates_fence_handling() -> None:
    """The behavioural half: a fix on one side must not leave the other behind.

    A "how to record a verdict" section carrying a fenced Target template is a
    realistic edit to a document that already explains its own grammar. The
    private splitter would have counted it as a second `## Target` section and
    tripped `_target_verdict`'s "expected exactly one" assertion — a red test
    naming the wrong problem, for a documentation edit that broke nothing.
    Sharing the gate's reader means `strip_fences` covers both at once.
    """
    real = _synthetic_refused_target()
    with_template = real + (
        "\n---\n\n## How to record a verdict\n\n"
        "```markdown\n## Target (target.com)\n\n**Verdict: REACHABLE (rung 1)**\n```\n"
    )

    assert _target_verdict(with_template) == _REFUSED
    assert (
        _target_disagreements(
            evidence_text=with_template,
            configured=set(),
            controlled=set(),
            fixture_names=[],
            allow_list={"target"},
            fixture_sellers=[],
        )
        == []
    )


def test_a_reachable_target_backed_by_the_observed_seller_string_passes() -> None:
    """The other side of the drift guard: an evidence-backed allow-list is clean.

    Without this the guard could be satisfied by never letting Target be
    REACHABLE at all, which would make it a rule against a branch rather than a
    rule about the branch.
    """
    problems = _target_disagreements(
        evidence_text=_EVIDENCE_PATH.read_text(encoding="utf-8"),
        configured={"target"},
        controlled={"target"},
        fixture_names=["control-dust-cloths.html"],
        allow_list={"target", "target corporation"},
        fixture_sellers=["Target Corporation"],
    )

    assert problems == []


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


# --------------------------------------------------------------------------
# Target — the dom extraction axis, on synthetic markup
# --------------------------------------------------------------------------
#
# The fixture-driven half lives further down. What is pinned here is the
# LABELLING: which reader ran, said on every path including the ones that found
# nothing. A verdict-only suite cannot see any of this, which is exactly why
# `degraded` needed M6 and M7 in the first place.

_TARGET_URL = "https://www.target.com/p/x/-/A-90377926"


def _target_watch(**kw: object) -> Watch:
    return Watch(name="probe", retailer="target", target=_TARGET_URL, **kw)  # type: ignore[arg-type]


def _target_control_html(*, disabled: str = "", partner: str = "") -> str:
    return (
        "<html><body>"
        '<div data-test="@web/Price/PriceFull"><span data-test="product-price">$12.59</span></div>'
        f'<button type="button" {disabled} id="addToCartButtonOrTextIdFor90377926">'
        "Add to cart</button>"
        f"{partner}</body></html>"
    )


def test_a_target_dom_reading_is_labelled_dom_and_degraded() -> None:
    r = retailers._verdict_from_html(
        _target_watch(),
        _target_control_html(),
        url=_TARGET_URL,
        first_party_only=True,
        rung=Rung.BROWSER,
        allow_dom=True,
    )
    assert r.availability is Availability.IN_STOCK
    assert r.price == 12.59
    assert r.extraction is Extraction.DOM
    assert r.rung is Rung.BROWSER
    assert r.degraded


def test_a_target_dom_reading_that_found_nothing_is_still_a_dom_reading() -> None:
    """The path a broken render takes, and the one that would mislabel silently.

    With `allow_dom=True` and every reader empty, the verdict is produced by
    `_verdict_from_html`'s no-offers return rather than by the adapter — so the
    adapter's own `Extraction.DOM` never touches it. Labelling it `structured`
    would tell a reader the DOM path was not involved in precisely the situation
    where it is the thing that failed.
    """
    r = retailers._verdict_from_html(
        _target_watch(),
        "<html><body>nothing here</body></html>",
        url=_TARGET_URL,
        first_party_only=True,
        rung=Rung.BROWSER,
        allow_dom=True,
    )
    assert r.availability is Availability.UNKNOWN
    assert r.extraction is Extraction.DOM
    assert r.degraded


def test_a_disabled_target_button_is_out_of_stock_not_unknown() -> None:
    r = retailers._verdict_from_html(
        _target_watch(),
        _target_control_html(disabled='disabled=""'),
        url=_TARGET_URL,
        first_party_only=True,
        rung=Rung.BROWSER,
        allow_dom=True,
    )
    assert r.availability is Availability.OUT_OF_STOCK
    assert r.extraction is Extraction.DOM


def test_a_target_plus_partner_listing_never_reads_as_first_party() -> None:
    """T-03.1-26. A reseller holding the listing must not be able to alert."""
    partner = (
        '<a data-test="targetPlusExtraInfoSection" href="/sp/joyin/-/N-10006960">'
        "<span>Sold &amp; shipped by </span><span>Joyin</span></a>"
    )
    r = retailers._verdict_from_html(
        _target_watch(max_price=80),
        _target_control_html(partner=partner),
        url=_TARGET_URL,
        first_party_only=True,
        rung=Rung.BROWSER,
        allow_dom=True,
    )
    assert r.availability is not Availability.IN_STOCK
    assert not r.alertable
    assert r.extraction is Extraction.DOM


def test_allow_dom_leaves_a_structured_page_labelled_structured(
    gamestop_goplusplus: str,
) -> None:
    """The opt-in only adds a fallback; it does not relabel what ld+json read."""
    r = retailers._verdict_from_html(
        Watch(name="probe", retailer="gamestop", target="https://www.gamestop.com/x"),
        gamestop_goplusplus,
        url="https://www.gamestop.com/x",
        first_party_only=True,
        rung=Rung.TLS,
        allow_dom=True,
    )
    assert r.extraction is Extraction.STRUCTURED


def test_the_dom_reader_is_opt_in_so_existing_adapters_are_unchanged() -> None:
    """Without `allow_dom`, a Target-shaped page reads UNKNOWN and structured.

    A GameStop page that lost its `ld+json` must not silently start being read
    off its buttons — that is a behaviour change to a shipped retailer that
    nobody decided to make.
    """
    r = retailers._verdict_from_html(
        _target_watch(),
        _target_control_html(),
        url=_TARGET_URL,
        first_party_only=True,
        rung=Rung.TLS,
    )
    assert r.availability is Availability.UNKNOWN
    assert r.extraction is Extraction.STRUCTURED


def test_check_target_browser_labels_both_axes_when_the_browser_will_not_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A rung and an extraction are facts about the attempt, not about the verdict."""

    def boom(url: str, **kw: object) -> Page:
        raise FetchError("no Chrome/Chromium binary found — set BOTY_BROWSER_PATH to one")

    monkeypatch.setattr(retailers, "fetch_rendered", boom)
    r = retailers.check_target_browser(_target_watch())
    assert r.availability is Availability.UNKNOWN
    assert r.rung is Rung.BROWSER
    assert r.extraction is Extraction.DOM
    assert r.degraded


def test_check_target_browser_labels_both_axes_when_target_serves_a_challenge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def blocked(url: str, **kw: object) -> Page:
        raise Blocked("rendered challenge page matched 'sec-if-cpt-container'")

    monkeypatch.setattr(retailers, "fetch_rendered", blocked)
    r = retailers.check_target_browser(_target_watch())
    assert r.availability is Availability.UNKNOWN
    assert r.rung is Rung.BROWSER
    assert r.extraction is Extraction.DOM


def test_check_target_browser_redacts_this_machines_paths_from_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`status.write` copies `detail` into a file served over HTTP."""
    home = os.path.expanduser("~")

    def boom(url: str, **kw: object) -> Page:
        raise FetchError(f"could not start {home}/.cache/ms-playwright/chrome")

    monkeypatch.setattr(retailers, "fetch_rendered", boom)
    r = retailers.check_target_browser(_target_watch())
    assert home not in r.detail
    assert "~" in r.detail


# --------------------------------------------------------------------------
# Target — the captured control page
# --------------------------------------------------------------------------


def test_target_control_fixture_is_in_stock_priced_and_alertable(
    target_dust_cloths: str,
) -> None:
    """The live half of the Target guard, frozen. If this reads anything else the
    detector is broken, and the control watch in `config/products.yaml` is what
    says so within a cycle on the real page.

    THE `max_price: 80` THAT USED TO BE ON THIS SYNTHETIC WATCH IS GONE, and
    removing it made the watch MORE faithful rather than less: the shipped
    Target control carries no ceiling, and no control in `config/products.yaml`
    does. Under REQ-17 a ceiling is measured against the delivered total, and
    Target's reader is an add-to-cart button that publishes no shipping cost —
    so a synthetic ceiling here would have made this assertion a statement
    about REQ-17's refusal rather than about the detector, which is what this
    test exists to watch. The ceiling's own behaviour is pinned where it
    belongs, in
    `test_a_first_party_amazon_offer_under_a_ceiling_alerts_with_its_shipping_unknown`
    — which as of Dan's 2026-08-11 reversal now pins an ALERT rather than a
    refusal. Removing the synthetic ceiling was right either way and for the
    same reason: the shipped control carries none.
    """
    watch = Watch(
        name="CONTROL — up&up microfiber dust cloths",
        retailer="target",
        target=_TARGET_URL,
        control=True,
    )
    r = retailers._verdict_from_html(
        watch,
        target_dust_cloths,
        url=_TARGET_URL,
        first_party_only=True,
        rung=Rung.BROWSER,
        allow_dom=True,
    )

    assert r.availability is Availability.IN_STOCK
    assert r.price == 12.59
    assert r.alertable
    assert "add-to-cart" in r.detail


def test_a_target_reading_declares_both_axes_and_is_degraded(
    target_dust_cloths: str,
) -> None:
    r = retailers._verdict_from_html(
        _target_watch(),
        target_dust_cloths,
        url=_TARGET_URL,
        first_party_only=True,
        rung=Rung.BROWSER,
        allow_dom=True,
    )

    assert r.rung is Rung.BROWSER
    assert r.extraction is Extraction.DOM
    assert r.degraded, "a browser transport AND a dom extraction — either alone is enough"


def test_the_target_fixture_carries_no_structured_data_at_all(
    target_dust_cloths: str,
) -> None:
    """Why this retailer needs a DOM reader, asserted rather than asserted-in-prose.

    If Target ever starts shipping a structured feed this goes red, and the right
    response is to read that instead and drop `allow_dom` — a strictly better
    reading, and one nobody would otherwise notice had become available.
    """
    assert parse.ldjson_offers(target_dust_cloths) is None
    assert parse.nextdata_offers(target_dust_cloths) is None
    assert parse.add_to_cart_offers(target_dust_cloths) is not None


def test_a_target_page_whose_control_vanished_is_unknown_never_out_of_stock(
    target_dust_cloths: str,
) -> None:
    """The real fixture with the add-to-cart control removed — a broken render.

    This is the production failure mode for this retailer: no exception, no
    challenge, no 403, just a page whose control the reader can no longer find.
    OUT_OF_STOCK here would be a confident wrong answer that looks exactly like a
    drought, and it is the bug the whole three-state contract exists to prevent.

    The extraction and the degraded flag are asserted explicitly, and that is the
    half a verdict-only test would miss: this verdict is produced inside
    `_verdict_from_html`, not by `check_target_browser`, so it is the one path
    where a `structured` label could survive and tell a reader the DOM path was
    never involved in the very failure that broke it.
    """
    broken = re.sub(
        r'id="addToCartButtonOrTextIdFor\d+"', 'id="somethingElse"', target_dust_cloths
    )
    assert broken != target_dust_cloths, "the control was not found in the fixture"

    r = retailers._verdict_from_html(
        _target_watch(max_price=80),
        broken,
        url=_TARGET_URL,
        first_party_only=True,
        rung=Rung.BROWSER,
        allow_dom=True,
    )

    assert r.availability is Availability.UNKNOWN
    assert r.availability is not Availability.OUT_OF_STOCK
    assert not r.alertable
    assert r.extraction is Extraction.DOM
    assert r.rung is Rung.BROWSER
    assert r.degraded


def test_the_target_fixture_has_no_partner_block_so_it_reads_first_party(
    target_dust_cloths: str,
) -> None:
    offers = parse.add_to_cart_offers(target_dust_cloths)
    assert offers is not None
    assert offers[0].seller == parse.TARGET_FIRST_PARTY_SELLER
    assert "targetPlusExtraInfoSection" not in target_dust_cloths


def test_a_target_watch_is_dispatched_to_the_browser_and_dom_path() -> None:
    """`_make_checker` is the one place a watch meets a transport, and
    `control_check.py` builds its checker with the same function — so this is
    what makes the gate and the monitor route identically."""
    cfg = Config.load(_REPO_ROOT / "config" / "products.yaml")
    target_watches = [w for w in cfg.watches if w.retailer == "target"]

    assert target_watches, "no target watch is configured"
    assert all(w.control for w in target_watches), (
        "Target is control-only: it delisted the GO Plus +, so a product watch "
        "there would read UNKNOWN forever"
    )

    seen: list[str] = []

    def fake_rendered(url: str, **kw: object) -> Page:
        seen.append(url)
        raise FetchError("stopped before the network")

    import boty.retailers as R

    original = R.fetch_rendered
    try:
        R.fetch_rendered = fake_rendered  # type: ignore[assignment]
        r = _make_checker(cfg)(target_watches[0])
    finally:
        R.fetch_rendered = original  # type: ignore[assignment]

    assert seen == [target_watches[0].target], "a target watch did not reach the browser rung"
    assert r.rung is Rung.BROWSER
    assert r.extraction is Extraction.DOM


# --------------------------------------------------------------------------
# Amazon — rung 1 + dom, and the marketplace case this project was built for
# --------------------------------------------------------------------------

_AMAZON_CONTROL_URL = "https://www.amazon.com/dp/B00NTCH52W"
_AMAZON_PRODUCT_URL = "https://www.amazon.com/dp/B0BX2P43PX"


def _amazon_watch(url: str = _AMAZON_PRODUCT_URL, **kw: object) -> Watch:
    return Watch(name="probe", retailer="amazon", target=url, **kw)  # type: ignore[arg-type]


def _amazon_verdict(html: str, watch: Watch, url: str) -> object:
    """Every Amazon reading goes through the adapter's own arguments.

    Written out rather than defaulted, because the two that matter here are the
    two `check_amazon` sets and a test that guessed them would prove nothing
    about the shipped path: `rung=Rung.TLS` (no browser — Amazon serves this to
    curl) and `allow_dom=True` (no structured data — the control is the only
    reader there is).
    """
    return retailers._verdict_from_html(
        watch,
        html,
        url=url,
        first_party_only=True,
        rung=Rung.TLS,
        allow_dom=True,
    )


def test_the_amazon_fixture_carries_no_structured_data_at_all(
    amazon_aa_batteries: str, amazon_goplusplus: str
) -> None:
    """Why this retailer needs a DOM reader at rung 1, asserted rather than said.

    Amazon is the second retailer here whose product page publishes nothing
    structured — and the first where that is true of the *plain HTTP response*
    rather than of a rendered DOM. If Amazon ever starts shipping a feed this
    goes red, and the right response is to read that instead and drop
    `allow_dom`: a strictly better reading that nobody would otherwise notice had
    become available.
    """
    for html in (amazon_aa_batteries, amazon_goplusplus):
        assert parse.ldjson_offers(html) is None
        assert parse.nextdata_offers(html) is None
        assert "application/ld+json" not in html
        assert parse.add_to_cart_offers(html) is not None


def test_amazon_control_fixture_is_in_stock_first_party_priced_and_alertable(
    amazon_aa_batteries: str,
) -> None:
    """The live half of the Amazon guard, frozen.

    `Amazon.com` is the verbatim buy-box seller string this page renders under
    the label `Shipper / Seller`, and it is the value `FIRST_PARTY['amazon']` was
    set from. If this reads anything else the detector is broken, and the control
    watch in `config/products.yaml` says so within a cycle on the real page.

    THE `max_price: 80` THAT USED TO BE ON THIS SYNTHETIC WATCH IS GONE, for
    the reason the Target control above records: the shipped Amazon control
    carries no ceiling, and Amazon publishes no shipping cost, so a synthetic
    ceiling here would have turned this into an assertion about REQ-17's
    refusal instead of about the detector. The refusal is pinned directly in
    the next test.
    """
    watch = Watch(
        name="CONTROL — Amazon Basics AA batteries (20-pack)",
        retailer="amazon",
        target=_AMAZON_CONTROL_URL,
        control=True,
    )
    r = _amazon_verdict(amazon_aa_batteries, watch, _AMAZON_CONTROL_URL)

    assert r.availability is Availability.IN_STOCK
    assert r.price == 9.99
    assert r.alertable
    assert "add-to-cart" in r.detail
    assert "Amazon.com" in r.detail


def test_a_first_party_amazon_offer_under_a_ceiling_alerts_with_its_shipping_unknown(
    amazon_aa_batteries: str,
) -> None:
    """The watch 06-01 silenced, paging again — measured rather than described.

    This is a first-party Amazon offer, IN_STOCK, at $9.99, against an $80
    ceiling — every other defence satisfied. Under 06-01 it was not alertable,
    because `add_to_cart_offers` reads a button and a button carries no
    shipping cost, so no delivered total could be established. That measured
    cost went to Dan and he reversed the rule on 2026-08-11:

        "I think where we don't know just send it. If the user gets there and
        it's 50 dollar shipping that's disappointing but it's worse to feel
        like you 'missed out'."

    So the ceiling now measures the item price where shipping cannot be read,
    and the shipped Amazon PRODUCT watch (`config/products.yaml`, `max_price:
    80`) can page again the day Amazon itself sells a GO Plus +. The delivered
    total is still `None` and is still not stated anywhere: the push carries
    `price:` and `shipping: unknown` as two fields and no total.

    RENAMED, because the old name asserted the old verdict. Nothing about the
    reading changed — same fixture, same availability, same price, same absent
    shipping cost — only what the ceiling does with it.

    The `detail` says which of the two the ceiling measured, so the decision is
    diagnosable from the status page without re-reading this file.
    """
    watch = Watch(
        name="Pokémon GO Plus +",
        retailer="amazon",
        target=_AMAZON_CONTROL_URL,
        max_price=80,
    )
    r = _amazon_verdict(amazon_aa_batteries, watch, _AMAZON_CONTROL_URL)

    assert r.availability is Availability.IN_STOCK
    assert r.price == 9.99
    assert r.shipping is None
    assert r.delivered_total is None
    assert r.alertable is True
    assert "the ceiling was applied to the item price alone" in r.detail
    assert "no shipping cost was read" in r.detail


def test_an_amazon_reading_declares_both_axes_and_is_degraded(
    amazon_aa_batteries: str,
) -> None:
    """The disjunct 03.1-05 added, with its first rung-1 user.

    Best Buy and Target are degraded because a browser produced them. This
    reading came from plain impersonated HTTP — `Rung.TLS`, the same transport
    GameStop and Walmart use and the least suspicious thing this project does —
    and is degraded anyway, because of WHAT was read rather than HOW. Delete the
    `or self.extraction is Extraction.DOM` half and this row starts publishing
    as a first-class structured reading; that is mutation M7.
    """
    r = _amazon_verdict(amazon_aa_batteries, _amazon_watch(), _AMAZON_CONTROL_URL)

    assert r.rung is Rung.TLS, "no browser: Amazon serves this to curl_cffi"
    assert r.extraction is Extraction.DOM
    assert r.degraded, "a dom extraction alone is enough — the rung is 1 here"


def test_the_amazon_go_plus_plus_reseller_is_rejected_by_the_first_party_filter(
    amazon_goplusplus: str,
) -> None:
    """The whole project, in one fixture, and it is a live page rather than a point.

    Amazon's only offer for the Pokémon GO Plus + on 2026-08-03 was a USED unit
    at $219 — four times the $54.99 MSRP — sold by `LO Store (We Record Serial
    Numbers To avoid FRAUD)` through Amazon's used buy box. It is buyable, it is
    in stock, and alerting on it would be worse than never alerting at all.

    Note which defence fires: the seller filter, *before* the ceiling is ever
    consulted. OUT_OF_STOCK is the correct verdict rather than a hedge — the page
    was read perfectly and there is no first-party offer on it.
    """
    offers = parse.add_to_cart_offers(amazon_goplusplus)
    assert offers is not None
    assert offers[0].available, "the used buy box is live — this is not a sold-out page"
    assert offers[0].price == 219.0
    assert offers[0].seller == "LO Store (We Record Serial Numbers To avoid FRAUD)"
    assert offers[0].seller not in retailers.FIRST_PARTY["amazon"]

    r = _amazon_verdict(amazon_goplusplus, _amazon_watch(max_price=80), _AMAZON_PRODUCT_URL)

    assert r.availability is Availability.OUT_OF_STOCK
    assert not r.alertable
    assert "none first-party" in r.detail


def test_an_amazon_first_party_offer_over_the_ceiling_is_suppressed_independently(
    amazon_aa_batteries: str,
) -> None:
    """The second defence, proved on its own by removing the first from the question.

    The control page IS first-party, so the seller filter passes it — and a
    `max_price` under its price must still stop it. Two independent lines: the
    Walmart pair proves this for a structured reader, and Amazon is where it
    matters most, because Amazon is the marketplace that actually lists the
    product this project watches.
    """
    r = _amazon_verdict(
        amazon_aa_batteries, _amazon_watch(_AMAZON_CONTROL_URL, max_price=5), _AMAZON_CONTROL_URL
    )

    assert r.availability is Availability.IN_STOCK, "the reading is fine; the price is not"
    assert r.price == 9.99
    assert not r.alertable, "$9.99 is over a $5 ceiling"


def test_an_amazon_page_whose_control_vanished_is_unknown_never_out_of_stock(
    amazon_aa_batteries: str,
) -> None:
    """The real fixture with the add-to-cart control removed — a buy-box redesign.

    This is the production failure mode for this retailer, and it is quieter than
    Target's: no browser to fail, no exception, no challenge, no 403 — just an
    `<input>` whose id Amazon renamed. OUT_OF_STOCK here would be a confident
    wrong answer that looks exactly like a drought.

    Amazon compounds it. Target KEEPS its control and disables it when an item is
    out of stock, so absence there provably means the render failed. Amazon
    REMOVES the control instead, so absence is genuinely ambiguous — and this
    plan never observed an unavailable Amazon page, so the reader has no basis to
    resolve the ambiguity and must not try.

    The extraction and the degraded flag are asserted explicitly, and that is the
    half a verdict-only test would miss: this verdict is produced inside
    `_verdict_from_html`, not by `check_amazon`, so it is the one path where a
    `structured` label could survive and tell a reader the DOM path was never
    involved in the very failure that broke it.
    """
    broken = amazon_aa_batteries.replace('id="add-to-cart-button"', 'id="somethingElse"')
    assert broken != amazon_aa_batteries, "the control was not found in the fixture"

    r = _amazon_verdict(broken, _amazon_watch(max_price=80), _AMAZON_CONTROL_URL)

    assert r.availability is Availability.UNKNOWN
    assert r.availability is not Availability.OUT_OF_STOCK
    assert not r.alertable
    assert r.extraction is Extraction.DOM
    assert r.rung is Rung.TLS
    assert r.degraded


def test_an_amazon_offer_with_no_seller_recorded_is_unknown_not_a_verdict(
    amazon_aa_batteries: str,
) -> None:
    """The marketplace case that matters most here, and the one Target cannot have.

    On Target, absence of a seller block IS the first-party signal — measured, and
    `parse.TARGET_FIRST_PARTY_SELLER` is what the reader emits for it. Carrying
    that default across to Amazon would have been the single most damaging line in
    this plan: every unreadable Amazon buy box would read as sold by Amazon, and
    a reseller whose block the parser failed on would alert.

    So the DOM reader defaults per page family, and on Amazon the default is
    `None`. `amazon` is in `MARKETPLACES`, which disables `_pick`'s
    unattributed-offer fallback, and an offer nobody is recorded as selling is
    UNKNOWN — never OUT_OF_STOCK, and never a $229 flip.
    """
    anonymous = amazon_aa_batteries.replace(
        'data-csa-c-slot-id="odf-feature-text-desktop-merchant-info"',
        'data-csa-c-slot-id="odf-feature-text-desktop-something-else"',
    )
    assert anonymous != amazon_aa_batteries, "the merchant-info slot was not found"

    offers = parse.add_to_cart_offers(anonymous)
    assert offers is not None
    assert offers[0].seller is None, (
        "an Amazon page with no readable seller must NOT inherit Target's "
        "first-party-by-absence rule"
    )

    r = _amazon_verdict(anonymous, _amazon_watch(max_price=80), _AMAZON_CONTROL_URL)

    assert r.availability is Availability.UNKNOWN
    assert r.availability is not Availability.OUT_OF_STOCK
    assert not r.alertable
    assert "marketplace" in r.detail


def test_an_amazon_watch_is_dispatched_to_the_rung_one_dom_path() -> None:
    """`_make_checker` is the one place a watch meets a transport, and
    `control_check.py` builds its checker with the same function — so this is
    what makes the gate and the monitor route identically.

    Amazon is the one retailer here with BOTH a control and a real product watch
    on the GO Plus +, which is worth pinning: Best Buy and Target are
    control-only because neither carries the product any more, and Amazon does.
    """
    cfg = Config.load(_REPO_ROOT / "config" / "products.yaml")
    amazon_watches = [w for w in cfg.watches if w.retailer == "amazon"]

    assert amazon_watches, "no amazon watch is configured"
    assert any(w.control for w in amazon_watches), (
        "a configured retailer with no control watch fails control_check outright"
    )
    assert any(not w.control and w.max_price == 80 for w in amazon_watches), (
        "Amazon lists the GO Plus +, so it gets a real product watch with the "
        "MSRP-anchored ceiling on it — unlike Best Buy and Target, which do not"
    )

    seen: list[str] = []

    def fake_get(url: str, **kw: object) -> Page:
        seen.append(url)
        raise FetchError("stopped before the network")

    import boty.retailers as R

    original = R.get
    try:
        R.get = fake_get  # type: ignore[assignment]
        r = _make_checker(cfg)(amazon_watches[0])
    finally:
        R.get = original  # type: ignore[assignment]

    assert seen == [amazon_watches[0].target], "an amazon watch did not reach rung 1"
    assert r.rung is Rung.TLS, "no browser rung for Amazon — the ladder stops at 1"
    assert r.extraction is Extraction.DOM, (
        "the extraction label follows the reader that ran, error paths included"
    )


# --------------------------------------------------------------------------
# WHICH STORE ANSWERED — recorded on every return path, changing no verdict
# --------------------------------------------------------------------------
#
# `"0"` in the Walmart fixtures is THIS REPO'S REDACTION PLACEHOLDER, written
# over a real store number by commit `8dec2e0`, and it sits in
# `identity_check.py`'s allow-list beside `"00000"` and `"XX"`. It is NOT
# Walmart's "no store assigned" sentinel — nothing here has measured what
# Walmart does in that case — which is why `parse.nextdata_store` has no `"0"`
# branch and why the synthetic store values below are `"0"` and `"00000"`, the
# only two store-shaped literals this repo's identity guard permits in a tracked
# file.


def test_the_walmart_control_records_the_store_and_moves_no_verdict(
    monkeypatch: pytest.MonkeyPatch, walmart_milk: str
) -> None:
    """The regression proof for "this plan changes no verdict".

    The three values asserted here are byte-identical to what
    `test_a_first_party_walmart_offer_is_alertable` asserted before the store
    existed. If recording which store answered moved an availability, a price or
    a detail, it would show up right here.
    """
    _serve(monkeypatch, walmart_milk, WALMART_URL)
    watch = Watch(
        name="milk", retailer="walmart", target=WALMART_URL, control=True, store_id="0"
    )

    result = retailers.check_html(watch, first_party_only=True)

    assert result.store == "0"
    assert result.availability is Availability.IN_STOCK
    assert result.price == 2.42
    assert "Walmart.com" in result.detail


def test_a_page_that_names_no_store_records_no_store(
    monkeypatch: pytest.MonkeyPatch, gamestop_goplusplus: str
) -> None:
    """A GameStop reading is unchanged and claims nothing about a store."""
    _serve(monkeypatch, gamestop_goplusplus)
    watch = Watch(name="GO Plus +", retailer="gamestop", target=GAMESTOP_URL)

    result = retailers.check_html(watch)

    assert result.store is None
    assert result.availability is Availability.OUT_OF_STOCK
    assert result.price == 54.99


def test_a_refusal_records_no_store_because_it_produced_no_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both refusal arms state `store=None` rather than inheriting it.

    A refusal produced no page, so nothing said which store answered. The arms
    say so explicitly, the way `check_target_browser` states its metadata on
    every path — the alternative is a field whose value on the error path is an
    accident of the dataclass's declaration order.
    """
    _raise(monkeypatch, Blocked("challenge page"))
    watch = Watch(name="milk", retailer="walmart", target=WALMART_URL, store_id="0")
    blocked = retailers.check_html(watch)

    _raise(monkeypatch, FetchError("connection reset"))
    failed = retailers.check_html(watch)

    assert blocked.store is None
    assert blocked.availability is Availability.UNKNOWN
    assert blocked.refused is True
    assert failed.store is None
    assert failed.availability is Availability.UNKNOWN


def test_every_verdict_path_carries_the_store_including_the_unknowns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Error paths carry the same metadata as success paths.

    That is the rule `check_target_browser`'s docstring commits to for `rung`
    and `extraction`, and it applies here for the reason it applied there: the
    UNKNOWN paths are the ones a human reads when something is wrong, and a
    diagnosis missing the store is missing the thing 05-02 will guard on.

    Every branch below is a distinct `return` in `_verdict_from_html`.
    """
    location = {"location": {"storeIds": ["00000"]}}

    # 1. No offers at all, no SKU — "page shape changed?"
    no_offers = _nextdata(**location)
    _serve(monkeypatch, no_offers, WALMART_URL)
    # Pinned to the store these synthetic payloads answer for, so 05-02's store
    # guards pass and each branch below is still reached. An unpinned watch would
    # collapse all six into the one config-gap UNKNOWN and prove nothing about
    # the six returns this test exists to walk.
    watch = Watch(name="milk", retailer="walmart", target=WALMART_URL, store_id="00000")
    r = retailers.check_html(watch)
    assert r.availability is Availability.UNKNOWN and r.store == "00000"

    # 2. No offers, with a SKU — the unresolved-SKU diagnosis.
    r = retailers._verdict_from_html(
        watch, no_offers, url=WALMART_URL, first_party_only=True, rung=Rung.TLS, sku="6216393"
    )
    assert r.availability is Availability.UNKNOWN and r.store == "00000"
    assert "did not resolve" in r.detail

    # 3. An offer on a retailer with no first-party list configured.
    unknown_retailer = Watch(name="thing", retailer="nowhere", target=WALMART_URL)
    page = _nextdata(
        availabilityStatus="IN_STOCK",
        sellerName="Somebody Else",
        priceInfo={"currentPrice": {"price": 9.99}},
        **location,
    )
    r = retailers._verdict_from_html(
        unknown_retailer, page, url=WALMART_URL, first_party_only=True, rung=Rung.TLS
    )
    assert r.availability is Availability.UNKNOWN and r.store == "00000"
    assert "no first-party seller list" in r.detail

    # 4. A marketplace offer with no seller recorded.
    unattributed = _nextdata(
        availabilityStatus="IN_STOCK",
        priceInfo={"currentPrice": {"price": 9.99}},
        **location,
    )
    r = retailers._verdict_from_html(
        watch, unattributed, url=WALMART_URL, first_party_only=True, rung=Rung.TLS
    )
    assert r.availability is Availability.UNKNOWN and r.store == "00000"
    assert "cannot tell whose offer" in r.detail

    # 5. Offers exist, none of them first-party.
    reseller = _nextdata(
        availabilityStatus="IN_STOCK",
        sellerName="A Flipper LLC",
        priceInfo={"currentPrice": {"price": 219.0}},
        **location,
    )
    r = retailers._verdict_from_html(
        watch, reseller, url=WALMART_URL, first_party_only=True, rung=Rung.TLS
    )
    assert r.availability is Availability.OUT_OF_STOCK and r.store == "00000"
    assert "none first-party" in r.detail

    # 6. The ordinary verdict.
    first_party = _nextdata(
        availabilityStatus="IN_STOCK",
        sellerName="Walmart.com",
        priceInfo={"currentPrice": {"price": 2.42}},
        **location,
    )
    r = retailers._verdict_from_html(
        watch, first_party, url=WALMART_URL, first_party_only=True, rung=Rung.TLS
    )
    assert r.availability is Availability.IN_STOCK and r.store == "00000"


# --------------------------------------------------------------------------
# THE STORE GUARDS — an unpinned or unexpected store is UNKNOWN, never a verdict
# --------------------------------------------------------------------------
#
# The measurement these exist for, 2026-08-09: the daemon recorded the milk
# control OUT_OF_STOCK at $3.17 while three live reads minutes later returned
# IN_STOCK at $2.42. Same URL, same parser. A parser bug does not change a
# price — two different stores answered, and the system published one store's
# shelf as a fact about another's.
#
# Store literals here stay inside this repo's redaction vocabulary, `"0"` and
# `"00000"`. See the note above: `"0"` is the placeholder `8dec2e0` wrote over a
# real store number, not a Walmart sentinel.


def test_an_unpinned_walmart_watch_is_unknown_not_a_verdict(
    monkeypatch: pytest.MonkeyPatch, walmart_milk: str
) -> None:
    """The config gap, against the real fixture — asserted in BOTH directions.

    Not IN_STOCK, because nothing here says the milk is on a shelf you can
    reach. Not OUT_OF_STOCK either, which is the assertion that matters: a guard
    that only avoids IN_STOCK still ships the silent-failure bug this project
    exists to prevent.

    The `detail` names the key by the name a user types and the file they type it
    in, so the message is a fix instruction rather than a complaint.
    """
    _serve(monkeypatch, walmart_milk, WALMART_URL)
    watch = Watch(name="milk", retailer="walmart", target=WALMART_URL, control=True)

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK
    assert result.availability is not Availability.IN_STOCK
    assert result.price is None, "a reading that is not about your store carries no price"
    assert "store_id" in result.detail
    assert "config/products.yaml" in result.detail


def test_pinning_the_store_the_fixture_answered_for_restores_the_verdict(
    monkeypatch: pytest.MonkeyPatch, walmart_milk: str
) -> None:
    """The control the whole plan is measured against.

    These three values are byte-identical to what this fixture read before the
    guards existed. If a guard fired where it should not, or thinned the
    metadata on the way through, it shows up right here.
    """
    _serve(monkeypatch, walmart_milk, WALMART_URL)
    watch = Watch(
        name="milk", retailer="walmart", target=WALMART_URL, control=True, store_id="0"
    )

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.IN_STOCK
    assert result.price == 2.42
    assert "Walmart.com" in result.detail
    assert result.store == "0"


def test_a_page_answering_for_another_store_is_unknown_not_a_verdict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The 2026-08-09 measurement itself, made into a refusal to answer.

    The page says IN_STOCK from Walmart.com at $2.42 — a perfectly readable,
    perfectly true statement about a store nobody asked about. Both directions
    again: it must not be IN_STOCK, and it must not be OUT_OF_STOCK, because the
    honest reading is that this says nothing about the pinned store either way.
    """
    page = _nextdata(
        availabilityStatus="IN_STOCK",
        sellerName="Walmart.com",
        priceInfo={"currentPrice": {"price": 2.42}},
        location={"storeIds": ["0"]},
    )
    _serve(monkeypatch, page, WALMART_URL)
    watch = Watch(name="milk", retailer="walmart", target=WALMART_URL, store_id="00000")

    result = retailers.check_html(watch)

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK
    assert result.availability is not Availability.IN_STOCK
    assert result.price is None
    assert "0" in result.detail and "00000" in result.detail, (
        "both sides have to be named, or the message cannot be acted on"
    )
    assert result.store == "0", "what the page said is still recorded"


def test_a_page_that_names_no_store_reaches_the_same_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """"The page named no store" and "the page named a different store" are the
    same fact for the purposes of the verdict: neither can be SHOWN to come from
    the pinned store. So they share one guard rather than growing a third.
    """
    page = _nextdata(
        availabilityStatus="IN_STOCK",
        sellerName="Walmart.com",
        priceInfo={"currentPrice": {"price": 2.42}},
    )
    _serve(monkeypatch, page, WALMART_URL)
    watch = Watch(name="milk", retailer="walmart", target=WALMART_URL, store_id="0")

    result = retailers.check_html(watch)

    assert result.availability is Availability.UNKNOWN
    assert result.store is None
    assert "no store" in result.detail
    assert "0" in result.detail


def test_the_two_store_guards_say_different_things(
    monkeypatch: pytest.MonkeyPatch, walmart_milk: str
) -> None:
    """A config gap and a wrong store are different facts.

    Asserted directly, so a later edit cannot collapse them into one sentence: a
    reader has to be able to tell "nobody pinned a store" from "the store that
    answered is not yours" off the status page alone, without re-running
    anything. Same reasoning as the two first-party UNKNOWNs above being two
    branches rather than one.
    """
    _serve(monkeypatch, walmart_milk, WALMART_URL)
    unpinned = retailers.check_html(
        Watch(name="milk", retailer="walmart", target=WALMART_URL)
    )
    mismatched = retailers.check_html(
        Watch(name="milk", retailer="walmart", target=WALMART_URL, store_id="00000")
    )

    assert unpinned.availability is Availability.UNKNOWN
    assert mismatched.availability is Availability.UNKNOWN
    assert unpinned.detail != mismatched.detail


def test_the_store_guards_return_before_any_stock_verdict_can_form(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Placement, asserted behaviourally rather than by reading the source.

    The page carries one first-party, in-stock, $9.99 offer — everything an
    IN_STOCK verdict needs. With no store pinned the config-gap UNKNOWN is what
    comes back, which is only true if the guard runs ahead of the offer logic.
    """
    page = _nextdata(
        availabilityStatus="IN_STOCK",
        sellerName="Walmart.com",
        priceInfo={"currentPrice": {"price": 9.99}},
        location={"storeIds": ["0"]},
    )
    _serve(monkeypatch, page, WALMART_URL)
    watch = Watch(name="milk", retailer="walmart", target=WALMART_URL)

    result = retailers.check_html(watch)

    assert result.availability is Availability.UNKNOWN
    assert result.price is None
    assert "config/products.yaml" in result.detail


def test_a_guarded_result_carries_the_same_metadata_as_an_unguarded_one(
    monkeypatch: pytest.MonkeyPatch, walmart_milk: str
) -> None:
    """The store guard is not an error path with thinner metadata.

    That is the rule four adapter docstrings already commit to for `rung` and
    `extraction`: error paths carry the same metadata as success paths, because
    the error paths are the ones a human reads when something is wrong.
    """
    _serve(monkeypatch, walmart_milk, WALMART_URL)
    pinned = retailers.check_html(
        Watch(name="milk", retailer="walmart", target=WALMART_URL, store_id="0")
    )
    unpinned = retailers.check_html(
        Watch(name="milk", retailer="walmart", target=WALMART_URL)
    )
    mismatched = retailers.check_html(
        Watch(name="milk", retailer="walmart", target=WALMART_URL, store_id="00000")
    )

    for guarded in (unpinned, mismatched):
        assert guarded.rung is pinned.rung
        assert guarded.extraction is pinned.extraction
        assert guarded.url == pinned.url
        assert guarded.store == pinned.store == "0"


@pytest.mark.parametrize("store_id", [None, "00000"])
def test_a_refusal_is_never_re_diagnosed_as_a_store_gap(
    monkeypatch: pytest.MonkeyPatch, store_id: str | None
) -> None:
    """`check_html`'s except arms return before `_verdict_from_html` is reached.

    A refusal produced no page, so the store could not have been established
    either — reporting one as a store gap would be naming a cause nobody
    measured, which is the other half of this plan pointed the wrong way.
    """
    _raise(monkeypatch, Blocked("challenge page"))
    watch = Watch(
        name="milk", retailer="walmart", target=WALMART_URL, store_id=store_id
    )

    result = retailers.check_html(watch)

    assert result.availability is Availability.UNKNOWN
    assert result.refused is True
    assert result.detail.startswith("blocked:")
    assert "store_id" not in result.detail


def test_the_guards_do_not_fire_for_a_retailer_that_has_no_stores(
    monkeypatch: pytest.MonkeyPatch,
    gamestop_goplusplus: str,
    bestbuy_pikachu: str,
    target_dust_cloths: str,
    amazon_goplusplus: str,
) -> None:
    """Every non-Walmart fixture, unpinned, reads exactly what it read before.

    `STORE_SCOPED` is a claim about the RETAILER, not about the page. Keying the
    guards on "did this page happen to name a store" would let a Walmart page
    that stopped emitting the field slip past the config gap entirely — and
    keying them on nothing at all would turn every retailer here UNKNOWN, which
    is the failure this asserts against.

    The four expected triples below were measured on this tree at `943a52e`,
    immediately before the guards landed.
    """
    _serve(monkeypatch, gamestop_goplusplus)
    gamestop = retailers.check_html(
        Watch(name="GO Plus +", retailer="gamestop", target=GAMESTOP_URL)
    )
    assert gamestop.availability is Availability.OUT_OF_STOCK
    assert gamestop.price == 54.99
    assert gamestop.detail == "ld+json: OutOfStock from GameStop"
    assert gamestop.store is None

    _serve_rendered(monkeypatch, bestbuy_pikachu)
    bestbuy = retailers.check_bestbuy_browser(
        Watch(name="Let's Go, Pikachu!", retailer="bestbuy", target="6216393")
    )
    assert bestbuy.availability is Availability.IN_STOCK
    assert bestbuy.price == 59.99
    assert bestbuy.detail == "ld+json: InStock from Best Buy"
    assert bestbuy.store is None

    target_result = retailers._verdict_from_html(
        _target_watch(),
        target_dust_cloths,
        url=_TARGET_URL,
        first_party_only=True,
        rung=Rung.BROWSER,
        allow_dom=True,
    )
    assert target_result.availability is Availability.IN_STOCK
    assert target_result.price == 12.59
    assert target_result.detail == "add-to-cart control: add-to-cart enabled from target"
    assert target_result.store is None

    amazon = retailers._verdict_from_html(
        _amazon_watch(),
        amazon_goplusplus,
        url=_AMAZON_PRODUCT_URL,
        first_party_only=True,
        rung=Rung.TLS,
        allow_dom=True,
    )
    assert amazon.availability is Availability.OUT_OF_STOCK
    assert amazon.detail == "1 offer(s) via add-to-cart control, none first-party"
    assert amazon.store is None
    assert "store_id" not in amazon.detail


def test_the_verdict_function_branches_on_the_store_ahead_of_every_verdict() -> None:
    """The successor to 05-01's "does not branch on a store at all".

    That test was written to go red the moment these guards landed, and it did.
    It is rewritten rather than deleted, because the property it was pinning —
    *where* the store is read, and how many times — is still worth pinning, and
    it now also pins the ONE thing a behavioural test states less directly: both
    guards sit ahead of the offer logic in source order, so no stock verdict can
    form ahead of them.
    """
    import inspect

    src = inspect.getsource(retailers._verdict_from_html)
    body = "\n".join(
        line for line in src.splitlines() if not line.lstrip().startswith("#")
    )
    body = body.split('"""', 2)[-1]

    assert body.count("parse.nextdata_store") == 1, (
        "the store must be read exactly once, where the html is, and threaded "
        "onto every return from there."
    )
    assert body.count("STORE_SCOPED") == 1, (
        "one predicate, read once — a second copy is a second place to get it wrong"
    )
    # The property, stated as source order: the FIRST `return` in this function
    # is the config-gap guard's. Nothing — no UNKNOWN, no OUT_OF_STOCK, no
    # IN_STOCK — can be returned ahead of the store check.
    assert body.index("STORE_SCOPED") < body.index("return Result("), (
        "a return precedes the store guards, so a verdict can form for a store "
        "nobody asked about before they are ever consulted"
    )


# --------------------------------------------------------------------------
# REQ-21: a reading carries the moment it was taken; a non-reading carries none
# --------------------------------------------------------------------------
#
# TWO GATES, AND THE FIRST ONE IS STATIC ON PURPOSE. Phase 5's identical bulk
# edit threaded `shipping` onto eight sites and missed two of them; only the
# tests caught it, and the sites at highest risk this time are
# `check_bestbuy_api`'s four, which do not delegate to `_verdict_from_html` at
# all. A behavioural suite that covers nineteen arms passes, and the twentieth
# is the one that ships wrong — so the completeness assertion is made over the
# SOURCE, where "every one" is a thing that can actually be counted.
#
# THE PARTITION IS THE MEASUREMENT, not a rule of thumb. *"An `except` arm read
# nothing"* is FALSE at two of the twenty: `check_bestbuy_api`'s `bad api json`
# arm (`except ValueError`, raised by `page.json` — `get()` already returned, so
# bytes came back) and its `sku not found` arm (an empty `products` list — Best
# Buy answered). Marking those two unstamped errs in the DANGEROUS direction: it
# says a reading that DID happen has no age, and Best Buy is then permanently
# UNKNOWN-aged on the one retailer this project reaches through an official API.
#
# NO CLOCK IS FROZEN, INJECTED OR MONKEYPATCHED. A stamp is asserted by
# BRACKETING — `before = time.time()`, call, `after = time.time()` — which is
# sufficient for everything below and is why this phase adds no time seam.


def _retailers_ast() -> ast.Module:
    return ast.parse(Path(retailers.__file__).read_text(encoding="utf-8"))


def _result_calls(node: ast.AST) -> list[ast.Call]:
    return [
        n
        for n in ast.walk(node)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Result"
    ]


def _read_at_kind(call: ast.Call) -> str:
    """`literal-None`, `variable`, `missing`, or whatever else somebody wrote."""
    for kw in call.keywords:
        if kw.arg != "read_at":
            continue
        if isinstance(kw.value, ast.Constant) and kw.value.value is None:
            return "literal-None"
        if isinstance(kw.value, ast.Name):
            return "variable"
        return f"other:{type(kw.value).__name__}"
    return "missing"


def test_every_result_construction_in_retailers_names_read_at() -> None:
    """All 20 sites, proved over the source rather than arm by arm.

    THE COUNT IS ASSERTED AS WELL AS THE PROPERTY, and that is not belt-and-
    braces: a gate that finds zero `Result(` constructions — because the class
    was aliased, or the module moved — would pass vacuously while proving
    nothing at all. This file's own `_matrix` helper set that precedent.
    """
    calls = _result_calls(_retailers_ast())

    assert len(calls) == 20, (
        f"expected 20 `Result(` constructions in {Path(retailers.__file__).name}, found "
        f"{len(calls)}. A site added here must state `read_at` like the other twenty: "
        "the whole purpose of that field is to distinguish a reading from a non-reading, "
        "and a dataclass default cannot state which one this arm is."
    )
    unnamed = [c.lineno for c in calls if _read_at_kind(c) == "missing"]
    assert not unnamed, (
        f"`Result(` at line(s) {unnamed} does not name `read_at`. Inheriting the default "
        "silently claims 'nothing was read' — which is right at nine arms and a lie at "
        "eleven, and no test of the other nineteen arms can see it."
    )


def test_the_read_and_non_read_arms_are_partitioned_exactly() -> None:
    """11 stamped, 9 literal `None`, per enclosing function — the measured table.

    `(literal-None, variable)` per function. The two entries worth reading twice
    are `check_bestbuy_api`'s: **1** literal and **3** variable, because Best Buy
    ANSWERED on three of its four arms.
    """
    expected = {
        # Every one of these eight follows a successful fetch and parse. They
        # differ in what the page SAID, not in whether it answered.
        "_verdict_from_html": (0, 8),
        "check_html": (2, 0),
        "check_amazon": (2, 0),
        "check_bestbuy_browser": (2, 0),
        "check_target_browser": (2, 0),
        # `api error` alone is the non-read arm here.
        "check_bestbuy_api": (1, 3),
    }

    measured: dict[str, tuple[int, int]] = {}
    for node in _retailers_ast().body:
        if not isinstance(node, ast.FunctionDef):
            continue
        calls = _result_calls(node)
        if not calls:
            continue
        kinds = [_read_at_kind(c) for c in calls]
        measured[node.name] = (kinds.count("literal-None"), kinds.count("variable"))

    assert measured == expected, (
        f"the read/non-read partition moved: {measured} != {expected}.\n"
        "This is a MEASUREMENT, not a rule of thumb. `check_bestbuy_api`'s `bad api json` "
        "and `sku not found` arms are responses that WERE read — `get()` returned before "
        "`page.json` raised, and an empty `products` list is Best Buy answering — so "
        "marking either unstamped is the dangerous direction, not a tidy-up: it dates a "
        "reading that happened as having no age at all, permanently, on the one retailer "
        "reached through an official API.\n"
        "And the inverse is the trap this phase exists to avoid: stamping a refusal "
        "refreshes the age of a reading nobody took (pacing.py:196-199 — 'a bound that "
        "cannot bind is worse than no bound')."
    )
    assert sum(v for pair in measured.values() for v in pair) == 20


@pytest.mark.parametrize("exc", [Blocked("challenge page"), FetchError("HTTP 503")])
@pytest.mark.parametrize(
    ("adapter", "transport"),
    [
        ("check_html", "get"),
        ("check_amazon", "get"),
        ("check_bestbuy_browser", "fetch_rendered"),
        ("check_target_browser", "fetch_rendered"),
    ],
)
def test_a_transport_that_refused_took_no_reading(
    monkeypatch: pytest.MonkeyPatch, adapter: str, transport: str, exc: Exception
) -> None:
    """Four adapters, both refusal arms each: `read_at is None`.

    A refusal DOES have a wall-clock moment. It took no READING, and stamping it
    would refresh the age of a reading that never happened — the 2026-08-12
    Walmart failure rebuilt inside the fix meant to prevent it.

    `is None` and never falsiness: `0.0` is falsy, and `0.0` is the other wrong
    answer (1 January 1970, maximally stale). A future regression to `0.0` must
    not be able to pass this.
    """

    def _refuse(target: str, **kwargs: object) -> Page:
        raise exc

    monkeypatch.setattr(retailers, transport, _refuse)
    watch = Watch(name="probe", retailer="gamestop", target=GAMESTOP_URL)

    r = getattr(retailers, adapter)(watch)

    assert r.availability is Availability.UNKNOWN
    assert r.read_at is None, f"{adapter} stamped an arm where nothing came back"


def test_a_page_that_answered_is_stamped_with_the_moment_it_was_read(
    monkeypatch: pytest.MonkeyPatch, gamestop_goplusplus: str
) -> None:
    """Bracketed, not frozen: `before <= read_at <= after` around the call."""
    _serve(monkeypatch, gamestop_goplusplus)
    watch = Watch(name="GO Plus +", retailer="gamestop", target=GAMESTOP_URL)

    before = time.time()
    r = retailers.check_html(watch)
    after = time.time()

    assert r.read_at is not None, "a page that answered has an age"
    assert before <= r.read_at <= after


def test_best_buy_answering_with_unparseable_bytes_is_still_a_reading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`bad api json` — `get()` returned, so Best Buy answered.

    The bytes were unreadable, which is a fact about what came back, not about
    whether anything did. `except ValueError` is raised by `page.json`, one line
    AFTER the response was in hand.
    """
    _serve(monkeypatch, "<html>403 Forbidden</html>")

    before = time.time()
    r = retailers.check_bestbuy_api(_bestbuy_watch(), API_KEY)
    after = time.time()

    assert r.availability is Availability.UNKNOWN
    assert "bad api json" in r.detail
    assert r.read_at is not None, (
        "an unparseable response is still a response; marking it unstamped leaves "
        "Best Buy permanently UNKNOWN-aged on the one retailer reached through an "
        "official API"
    )
    assert before <= r.read_at <= after


def test_best_buy_answering_that_the_sku_is_unknown_is_still_a_reading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`sku not found` — an empty `products` list IS Best Buy's answer."""
    _serve(monkeypatch, '{"products": []}')

    before = time.time()
    r = retailers.check_bestbuy_api(_bestbuy_watch(), API_KEY)
    after = time.time()

    assert r.availability is Availability.UNKNOWN
    assert "not found" in r.detail
    assert r.read_at is not None
    assert before <= r.read_at <= after


def test_best_buy_refusing_took_no_reading(monkeypatch: pytest.MonkeyPatch) -> None:
    """`api error` — nothing came back, so there is no reading to date."""
    _raise(monkeypatch, Blocked("challenge page"))

    r = retailers.check_bestbuy_api(_bestbuy_watch(), API_KEY)

    assert r.availability is Availability.UNKNOWN
    assert "api error" in r.detail
    assert r.read_at is None
