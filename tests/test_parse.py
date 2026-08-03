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

from boty.parse import (
    _LDJSON_RE,
    TARGET_FIRST_PARTY_SELLER,
    add_to_cart_offers,
    ldjson_offers,
    nextdata_offers,
)

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
# ldjson_offers — a compound @type is still a Product (IN-03)
# --------------------------------------------------------------------------


def test_ldjson_reads_a_compound_type_as_a_product() -> None:
    """`"@type": ["Product", "ProductModel"]` is valid schema.org.

    An exact `!= "Product"` comparison skips it, and the failure is quiet: the
    page has no product as far as the extractor is concerned, so the caller
    reports UNKNOWN. That costs coverage rather than correctness, which is
    precisely why it survived unnoticed — and it presents as a mysterious
    UNKNOWN on the first-party sites Phase 2 is adding.
    """
    offers = ldjson_offers(
        _ldjson_page(
            {
                "@type": ["Product", "ProductModel"],
                "name": "Pokémon GO Plus +",
                "offers": {
                    "availability": "https://schema.org/InStock",
                    "price": str(MSRP),
                },
            }
        )
    )

    assert offers is not None
    assert len(offers) == 1
    assert offers[0].available is True
    assert offers[0].price == MSRP


def test_ldjson_compound_type_without_product_is_still_none() -> None:
    """A list is not a free pass — membership is what is tested.

    `["Thing"]` has no Product in it, so this must stay "nothing here" rather
    than becoming "a product with no offers".
    """
    assert ldjson_offers(_ldjson_page({"@type": ["Thing"], "name": "x"})) is None


def test_ldjson_node_with_no_type_at_all_is_still_none() -> None:
    """The None case has to survive the list-wrapping.

    A missing `@type` wraps to `[None]`, which does not contain "Product", so
    `saw_product` stays False and the extractor returns None. If it wrapped to
    something truthy the page would come back as `[]` — a confident "this
    product has no offers" about a page with no product in it.
    """
    assert ldjson_offers(_ldjson_page({"name": "no type here"})) is None


def test_ldjson_compound_type_product_with_no_offers_is_an_empty_list() -> None:
    """The None-vs-[] distinction applies to compound types too."""
    assert ldjson_offers(_ldjson_page({"@type": ["Product", "ProductModel"]})) == []


def test_the_compound_type_fix_is_confirmed_by_a_real_retailer(nintendo_goplusplus: str) -> None:
    """IN-03 against live bytes rather than a payload written to prove a point.

    Every test above this one builds its own JSON, which means they all agree
    with each other by construction and none of them is evidence that any
    retailer emits this shape. Nintendo does: the GO Plus + page declares
    `"@type": ["Product"]` — a one-element list, the least suspicious shape
    imaginable, and the exact shape an `== "Product"` comparison drops on the
    floor.

    So this page is not just another fixture. Under the pre-02-02 extractor it
    would have read as "no product markup here" and Nintendo would have been an
    unexplained permanent UNKNOWN — a first-party retailer, publishing complete
    and correct availability, invisible to us for a one-character reason.

    The `@type` assertion looks redundant next to the offer assertion. It is
    not: without it, a future Nintendo redesign to a plain-string `@type` would
    turn this into a test that passes while proving nothing, and the compound
    case would go back to being untested against anything real.
    """
    # The module's own block finder rather than a hand-rolled split: Nintendo
    # carries `data-next-head=""` after the type attribute, and a test that
    # re-implements this scan would go red for its own reasons rather than the
    # extractor's.
    doc = json.loads(_LDJSON_RE.findall(nintendo_goplusplus)[0].strip())
    product = next(n for n in doc["@graph"] if isinstance(n, dict) and "offers" in n)

    assert isinstance(product["@type"], list), (
        "Nintendo stopped emitting a compound @type — this test is now the only "
        "thing claiming a real retailer ever did, so find another one before "
        "re-capturing this fixture"
    )
    assert "Product" in product["@type"]

    offers = ldjson_offers(nintendo_goplusplus)
    assert offers is not None, "the compound @type was skipped — IN-03 has regressed"
    assert len(offers) == 1
    assert offers[0].price == MSRP
    assert offers[0].seller == "Nintendo of America Inc."
    assert offers[0].raw_availability == "OutOfStock"


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


# --------------------------------------------------------------------------
# add_to_cart_offers — Target's DOM reader
# --------------------------------------------------------------------------
#
# Synthetic fragments rather than the captured page, and deliberately so. A
# fragment is readable in a diff, states exactly one thing, and leaks nothing —
# the captured Target fixture is exercised in tests/test_retailers.py, where
# what is being pinned is the whole verdict path rather than the reader.
#
# The markup below is copied from live renders (docs/retailer-evidence.md
# § Target), down to the `id` prefix, the `disabled=""` form and the ampersand
# in "Sold & shipped by".


def _target_pdp(control: str, *, price: str = "$12.59", partner: str = "") -> str:
    price_block = (
        '<div data-test="@web/Price/PriceFull"><div><span>'
        f'<span data-test="product-price">{price}</span>'
        "</span></div></div>"
        if price
        else ""
    )
    return f"<html><body><main>{price_block}{control}{partner}</main></body></html>"


_ENABLED = (
    '<button class="styles_btn__1hjpW" type="button" '
    'aria-label="Add to cart for Microfiber Dust Cloths - 6pk" '
    'data-test="orderPickupButton" '
    'id="addToCartButtonOrTextIdFor90377926">Add to cart</button>'
)

_DISABLED = (
    '<button class="styles_btn__1hjpW" type="button" '
    'aria-label="Add to cart for Joyfy 200 Pcs Easter Eggs" disabled="" '
    'id="addToCartButtonOrTextIdFor90984792">Add to cart</button>'
)

_PARTNER_BLOCK = (
    '<a aria-label="Sold &amp; shipped by Joyin. View partner details" '
    'data-test="targetPlusExtraInfoSection" href="/sp/joyin/-/N-10006960">'
    "<div><div>"
    '<span class="primary">Sold &amp; shipped by </span>'
    '<span class="subtext">Joyin</span>'
    "</div></div></a>"
)


def test_target_enabled_add_to_cart_is_available_with_its_price() -> None:
    offers = add_to_cart_offers(_target_pdp(_ENABLED))
    assert offers is not None
    assert len(offers) == 1
    assert offers[0].available is True
    assert offers[0].price == 12.59


def test_target_preorder_button_is_available() -> None:
    """One of the three phrases from Dan's original script, matched case-blind."""
    control = _ENABLED.replace(">Add to cart<", ">Preorder<")
    offers = add_to_cart_offers(_target_pdp(control))
    assert offers is not None
    assert offers[0].available is True


def test_target_hyphenated_pre_order_button_is_available() -> None:
    control = _ENABLED.replace(">Add to cart<", ">Pre-Order<")
    offers = add_to_cart_offers(_target_pdp(control))
    assert offers is not None
    assert offers[0].available is True


def test_target_disabled_button_is_not_available() -> None:
    """The observed out-of-stock shape: same tag, same text, plus `disabled`."""
    offers = add_to_cart_offers(_target_pdp(_DISABLED, price="$25.99"))
    assert offers is not None
    assert offers[0].available is False
    assert offers[0].price == 25.99


def test_target_aria_disabled_button_is_not_available() -> None:
    """A React rewrite to the ARIA form must not read as buyable."""
    control = _DISABLED.replace('disabled=""', 'aria-disabled="true"')
    offers = add_to_cart_offers(_target_pdp(control))
    assert offers is not None
    assert offers[0].available is False


def test_target_missing_control_is_none_not_an_empty_list() -> None:
    """`is None`, not falsy: `[]` would mean "a product here with no offers".

    Target keeps the button and disables it when an item is out of stock, so a
    page with no control at all is a render that failed — UNKNOWN, never
    OUT_OF_STOCK. Asserted as identity because the caller branches on the
    difference and `assert not offers` would pass for both.
    """
    assert add_to_cart_offers(_target_pdp("<div>no control here</div>")) is None


def test_target_unrecognised_control_text_is_none() -> None:
    """`addToCartButtonOrText` — Target's own name says the slot can render text.

    If it ever does, this reader does not know what it is looking at, and "the
    page changed and I got lost" is UNKNOWN rather than out-of-stock.
    """
    control = _ENABLED.replace(">Add to cart<", ">Only at your store<")
    assert add_to_cart_offers(_target_pdp(control)) is None


def test_target_partner_block_names_the_partner_as_the_seller() -> None:
    offers = add_to_cart_offers(_target_pdp(_ENABLED, partner=_PARTNER_BLOCK))
    assert offers is not None
    assert offers[0].seller == "Joyin"


def test_target_page_with_no_partner_block_is_sold_by_target() -> None:
    """Absence is the first-party signal, and it is an observation not a guess."""
    offers = add_to_cart_offers(_target_pdp(_ENABLED))
    assert offers is not None
    assert offers[0].seller == TARGET_FIRST_PARTY_SELLER


def test_target_partner_block_with_an_unreadable_name_is_not_first_party() -> None:
    """Fails toward UNKNOWN, never toward Target: `None` on a marketplace is UNKNOWN."""
    partner = _PARTNER_BLOCK.replace(">Joyin<", "><")
    offers = add_to_cart_offers(_target_pdp(_ENABLED, partner=partner))
    assert offers is not None
    assert offers[0].seller is None
    assert offers[0].seller != TARGET_FIRST_PARTY_SELLER


def test_target_unreadable_price_still_yields_an_availability() -> None:
    """A missing price does not block the verdict — `Result.alertable` holds the ceiling."""
    offers = add_to_cart_offers(_target_pdp(_ENABLED, price="Price not available"))
    assert offers is not None
    assert offers[0].price is None
    assert offers[0].available is True


def test_target_reader_finds_nothing_on_a_structured_page(gamestop_goplusplus: str) -> None:
    """It is Target's reader, not a universal fallback — no control, no offers."""
    assert add_to_cart_offers(gamestop_goplusplus) is None
