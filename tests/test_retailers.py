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
import os
from pathlib import Path

from boty import retailers
from boty.cli import _make_checker
from boty.config import Config
from boty.fetch import Blocked, FetchError, Page
from boty.models import Availability, Rung, Watch
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


def test_retailer_with_no_first_party_list_is_unknown_not_out_of_stock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A config gap is not a stock fact.

    `FIRST_PARTY.get(retailer, set())` returns an empty set for any retailer
    key not in the dict, so `named` is always empty and — for a page that does
    name its seller, as most schema.org markup does — `_pick` returns None.
    That used to become a confident OUT_OF_STOCK, when the truth is "this
    retailer has no first-party allow-list configured, so I cannot tell whose
    offer this is". FIRST_PARTY covers four keys and REQUIREMENTS targets
    seven retailers, so three Phase 2 adapters land straight into this path.
    """
    _serve(
        monkeypatch,
        _ldjson(availability="https://schema.org/InStock", price="54.99",
                seller={"@type": "Organization", "name": "Pokémon Center"}),
        "https://www.pokemoncenter.com/product/1",
    )
    watch = Watch(
        name="GO Plus +", retailer="pokemoncenter", target="https://www.pokemoncenter.com/product/1"
    )

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.UNKNOWN
    assert result.availability is not Availability.OUT_OF_STOCK
    assert result.alertable is False
    assert "pokemoncenter" in result.detail


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
    watch = Watch(name="GO Plus +", retailer="walmart", target=WALMART_URL)

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
