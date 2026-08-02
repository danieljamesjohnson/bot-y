"""The extraction contract, pinned against frozen retailer pages.

Two distinctions carry most of the weight here:

- ``None`` means "no structured data of this kind on the page, try something
  else"; ``[]`` means "there is a product here and it has no offers". The
  caller branches differently on each, so collapsing them would turn a page
  whose shape changed into a confident verdict.
- ``nextdata_offers`` must read the *primary* product only. Walmart pages embed
  recommendations and accessories with their own availability, and a generic
  walk would happily report a $12 screen protector as your restock.
"""

from __future__ import annotations

import json

from boty.parse import ldjson_offers, nextdata_offers

#: MSRP of the Pokémon GO Plus +. Anything far above this is a flipper.
MSRP = 54.99


def _ldjson_page(payload: object) -> str:
    return (
        "<html><head>"
        f'<script type="application/ld+json">{json.dumps(payload)}</script>'
        "</head><body></body></html>"
    )


# --------------------------------------------------------------------------
# ldjson_offers — GameStop
# --------------------------------------------------------------------------


def test_gamestop_out_of_stock_fixture(gamestop_goplusplus: str) -> None:
    offers = ldjson_offers(gamestop_goplusplus)
    assert offers is not None
    assert len(offers) >= 1

    offer = offers[0]
    assert offer.available is False
    assert offer.raw_availability == "OutOfStock"
    assert offer.price == MSRP
    assert offer.seller == "GameStop"


def test_gamestop_control_fixture_has_a_buyable_offer(gamestop_ps5: str) -> None:
    """At least one offer is buyable.

    Deliberately not ``offers[0]``: this page carries three offers, and the
    first is an OutOfStock $749.99 bundle. Asserting on the first would fail
    for a reason that has nothing to do with the extractor.
    """
    offers = ldjson_offers(gamestop_ps5)
    assert offers is not None

    buyable = [o for o in offers if o.available]
    assert buyable, f"expected a buyable offer among {offers}"
    assert any(o.price == 549.99 and o.raw_availability == "InStock" for o in buyable)


def test_ldjson_returns_none_when_no_product_node() -> None:
    """No Product markup is 'nothing here', not 'a product with no offers'.

    None tells the caller to try another extractor; [] would say the page was
    understood and the product has no offers at all. Conflating them is how a
    reshaped page becomes a confident out-of-stock verdict.
    """
    assert ldjson_offers("<html><body>no structured data at all</body></html>") is None
    assert ldjson_offers(_ldjson_page({"@type": "Organization", "name": "GameStop"})) is None


def test_ldjson_returns_empty_list_for_product_with_no_offers() -> None:
    """The other side of the same distinction: a Product with no offers is []."""
    offers = ldjson_offers(_ldjson_page({"@type": "Product", "name": "Thing"}))
    assert offers == []


def test_ldjson_ignores_malformed_blocks() -> None:
    """A broken ld+json block must not take the whole page down with it."""
    html = (
        '<html><head><script type="application/ld+json">{not json at all</script>'
        f'<script type="application/ld+json">{json.dumps({"@type": "Product", "offers": {"availability": "https://schema.org/InStock", "price": "9.99"}})}</script>'
        "</head></html>"
    )
    offers = ldjson_offers(html)
    assert offers is not None
    assert len(offers) == 1
    assert offers[0].available is True
    assert offers[0].price == 9.99


def test_ldjson_empty_input_is_none() -> None:
    assert ldjson_offers("") is None


# --------------------------------------------------------------------------
# nextdata_offers — Walmart
# --------------------------------------------------------------------------


def test_walmart_reseller_fixture_reads_the_marketplace_seller(walmart_goplusplus: str) -> None:
    offers = nextdata_offers(walmart_goplusplus)
    assert offers is not None
    assert len(offers) == 1

    offer = offers[0]
    assert offer.available is True
    assert offer.raw_availability == "IN_STOCK"
    assert offer.seller is not None
    assert offer.seller.strip().lower() != "walmart.com", (
        "this fixture's value is that a marketplace reseller holds the buy box; "
        "if it now reads Walmart.com the page was re-captured and the seller "
        "filter is no longer being exercised"
    )
    assert offer.price is not None
    assert offer.price > MSRP * 2, (
        f"expected a scalper price well above the ${MSRP} MSRP, got {offer.price}"
    )


def test_walmart_reads_only_the_primary_product(walmart_goplusplus: str) -> None:
    """Regression: exactly one offer, from the primary product node.

    Walmart product pages also embed recommendations, bundles and
    "customers also bought" — each with its own availabilityStatus. An earlier
    implementation walked the whole document and returned all of them, which
    would let a $12 in-stock accessory be reported as the GO Plus + restocking.
    """
    offers = nextdata_offers(walmart_goplusplus)
    assert offers is not None
    assert len(offers) == 1


def test_walmart_first_party_fixture(walmart_milk: str) -> None:
    offers = nextdata_offers(walmart_milk)
    assert offers is not None
    assert len(offers) == 1
    assert offers[0].seller == "Walmart.com"
    assert offers[0].available is True
    assert offers[0].price == 2.42


def test_nextdata_returns_none_without_the_blob() -> None:
    assert nextdata_offers("<html><body>plain page</body></html>") is None


def test_nextdata_returns_none_when_the_product_node_is_missing() -> None:
    """The blob is present but the expected path is not — that is UNKNOWN territory."""
    html = '<script id="__NEXT_DATA__">{"props": {"pageProps": {}}}</script>'
    assert nextdata_offers(html) is None


def test_nextdata_returns_none_on_malformed_json() -> None:
    assert nextdata_offers('<script id="__NEXT_DATA__">{broken</script>') is None


def test_nextdata_empty_input_is_none() -> None:
    assert nextdata_offers("") is None


# --------------------------------------------------------------------------
# Cross-extractor
# --------------------------------------------------------------------------


def test_walmart_fixture_has_no_ldjson_product(walmart_goplusplus: str) -> None:
    """Why check_html's fallback chain exists: ld+json finds nothing here."""
    assert ldjson_offers(walmart_goplusplus) is None
