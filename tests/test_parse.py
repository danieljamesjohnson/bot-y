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
    ldjson_read,
    nextdata_offers,
    nextdata_store,
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
# nextdata_store — WHICH store answered
# --------------------------------------------------------------------------
#
# WHY BOTH SHIPPED FIXTURES READ `"0"`, AND WHY THAT IS NOT A WALMART SENTINEL.
#
# `"0"` here is THIS REPO'S OWN REDACTION PLACEHOLDER. Commit `8dec2e0` replaced
# a real store number with `"0"` throughout both Walmart fixtures — in
# `"storeId"`, in `"storeIds"`, and inside embedded ad hrefs — and `"0"` sits in
# `identity_check.py`'s `allowed` redaction vocabulary beside `"00000"` and
# `"XX"`. The pre-redaction capture carries the real number many times over.
#
# So `"0"` says nothing whatsoever about what Walmart does with an unassigned
# store, and `nextdata_store` must NOT special-case it. A
# `if store == "0": return None` branch would be a claim about Walmart that
# nothing in this repo has measured. `05-PATTERNS.md` drew exactly that
# inference — "very likely Walmart's 'no store assigned' sentinel" — and it is
# wrong. This paragraph exists so the next reader does not draw it again.


def _nextdata_page(**data: object) -> str:
    """A minimal Walmart hydration payload — `data` is the `initialData.data` node."""
    doc = {"props": {"pageProps": {"initialData": {"data": data}}}}
    return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(doc)}</script></html>'


def test_the_walmart_fixtures_say_which_store_answered(
    walmart_milk: str, walmart_goplusplus: str
) -> None:
    """Both captures carry a store, and both read the redacted placeholder.

    See the paragraph above: `"0"` is this repo's redaction of a real number,
    not Walmart's own value. The reading being `"0"` is a fact about `8dec2e0`,
    not about Walmart.
    """
    assert nextdata_store(walmart_milk) == "0"
    assert nextdata_store(walmart_goplusplus) == "0"


def test_no_non_walmart_page_in_the_corpus_claims_a_store(
    gamestop_goplusplus: str,
    gamestop_ps5: str,
    bestbuy_pikachu: str,
    target_dust_cloths: str,
    amazon_aa_batteries: str,
    nintendo_hdmi: str,
) -> None:
    """The reader is called unconditionally, with no retailer predicate.

    That is safe because it is anchored on Walmart's own hydration shape, which
    no other retailer here emits — and this asserts it against the whole
    captured corpus rather than assuming it. A retailer predicate would be a
    claim ("only Walmart has stores") maintained in a second place, which is one
    more place to go stale when a seventh retailer arrives.
    """
    for page in (
        gamestop_goplusplus,
        gamestop_ps5,
        bestbuy_pikachu,
        target_dust_cloths,
        amazon_aa_batteries,
        nintendo_hdmi,
    ):
        assert nextdata_store(page) is None


def test_a_page_that_does_not_say_returns_none_rather_than_guessing() -> None:
    """`None` is "the page did not tell us", never "store 0"."""
    assert nextdata_store("") is None
    assert nextdata_store("<html><body>plain page</body></html>") is None
    assert nextdata_store('<script id="__NEXT_DATA__">{broken</script>') is None
    assert nextdata_store('<script id="__NEXT_DATA__">{"props": {}}</script>') is None


def test_every_shape_the_store_list_could_take_that_is_not_one_string_is_none() -> None:
    """Defensive at each step, in `nextdata_offers`' shape.

    The multi-entry case is the one worth stating: taking `[0]` out of a list
    with two entries would be a guess about ordering that nothing measured. Both
    shipped fixtures carry exactly one element (measured 2026-08-10), so a
    second one means Walmart changed something and we should say we do not know.
    """
    assert nextdata_store(_nextdata_page(product={})) is None
    assert nextdata_store(_nextdata_page(product={"location": {}})) is None
    assert nextdata_store(_nextdata_page(product={"location": {"storeIds": []}})) is None
    assert nextdata_store(_nextdata_page(product={"location": {"storeIds": "0"}})) is None
    assert nextdata_store(_nextdata_page(product={"location": {"storeIds": [0]}})) is None
    assert nextdata_store(_nextdata_page(product={"location": {"storeIds": [None]}})) is None
    assert nextdata_store(_nextdata_page(product={"location": "elsewhere"})) is None
    assert (
        nextdata_store(_nextdata_page(product={"location": {"storeIds": ["0", "00000"]}}))
        is None
    ), "a two-entry list must not be resolved by picking the first one"


def test_the_placeholder_store_is_returned_and_not_swallowed() -> None:
    """The trap, asserted directly: NO `"0"` special case.

    `"0"` is this repo's placeholder, not Walmart's sentinel, so the reader has
    nothing to say about it and must hand it back like any other value. If a
    later change wants to treat some value as "no store assigned", that has to
    be a measurement of Walmart's behaviour, made and cited at the time.
    """
    assert nextdata_store(_nextdata_page(product={"location": {"storeIds": ["0"]}})) == "0"
    assert (
        nextdata_store(_nextdata_page(product={"location": {"storeIds": ["00000"]}})) == "00000"
    )


def test_the_store_is_read_from_the_same_node_as_the_offer(walmart_milk: str) -> None:
    """The invariant this whole phase rests on, pinned.

    The store and the offer come out of ONE node — `product` — so a reading
    cannot attribute a price from one subtree to a store named in another. There
    is a second store in these pages, under
    `contentLayout.pageMetadata.location`, and it was deliberately not taken;
    see the constant's comment in `boty/parse.py`.
    """
    offers = nextdata_offers(walmart_milk)
    store = nextdata_store(walmart_milk)
    assert offers is not None and store is not None

    # Same synthetic node, both readers: remove the product node and BOTH go
    # quiet together, which is what "one node" means operationally.
    empty = _nextdata_page(contentLayout={"pageMetadata": {"location": {"storeId": "00000"}}})
    assert nextdata_offers(empty) is None
    assert nextdata_store(empty) is None, (
        "the store was read out of the page-layout metadata subtree. That is a "
        "fact about the chrome the page rendered, not about the offer — taking "
        "it would let a price from one store be attributed to another."
    )


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


# --------------------------------------------------------------------------
# JavaScript-escaped JSON-LD — Best Buy, observed live 2026-08-04
# --------------------------------------------------------------------------
#
# Best Buy began serving its JSON-LD JavaScript-escaped on 2026-08-04: the same
# three blocks on the same SKU that `tests/fixtures/bestbuy/pikachu-control.html`
# parses 3/3 with no backslashes at all. `json.loads` refused every one, the
# blocks were skipped silently, and the control read UNKNOWN with a detail that
# named the wrong cause ("no schema.org Product on it carries that sku").
#
# The markup below is the real thing, copied verbatim from the live page and
# trimmed — the same treatment the Amazon captcha wall got, and for the same
# reason: a hand-written approximation of a third party's breakage tests the
# approximation. Two defect shapes are present and both are load-bearing:
#
#   * `Let\'s`      — an invalid escape INSIDE a string. Legal JavaScript,
#                     illegal JSON.
#   * `{\n  "@ctx"` — a literal backslash-n OUTSIDE a string, where a real
#                     newline belongs. This is why the breadcrumb block failed
#                     at column 2 rather than at an escape.
#
# Neither carried a single VALID escape — no \", no \\, no \uXXXX — which is
# what made an exact repair possible rather than a heuristic one.
_BESTBUY_ESCAPED_PRODUCT = (
    '<script type="application/ld+json">'
    '{"@context":"http://schema.org/","@type":"Product",'
    "\"name\":\"Pokémon: Let\\'s Go, Pikachu! - Nintendo Switch\","
    '"sku":"6216393",'
    '"offers":[{"@type":"Offer","priceCurrency":"USD","price":59.99,'
    '"availability":"https://schema.org/InStock","sku":"6216393",'
    '"seller":{"@type":"Organization","name":"Best Buy"}}]}'
    "</script>"
)

#: The outside-a-string defect, on its own: structural `\n` between tokens.
_BESTBUY_ESCAPED_BREADCRUMB = (
    '<script type="application/ld+json">'
    '{\\n  "@context": "http://schema.org",\\n  "@type": "BreadcrumbList"\\n}'
    "</script>"
)


def test_js_escaped_ldjson_is_repaired_and_reads_the_real_offer() -> None:
    """The live 2026-08-04 breakage, read correctly — same offer the fixture gives."""
    read = ldjson_read(_BESTBUY_ESCAPED_PRODUCT, sku="6216393")
    assert read.offers is not None
    assert read.offers[0].available is True
    assert read.offers[0].price == 59.99
    assert read.offers[0].seller == "Best Buy"
    assert read.repaired == 1
    assert read.unparseable == 0


def test_a_repaired_read_is_never_silent() -> None:
    """Repair is recorded, so a reading that depended on it cannot look ordinary."""
    read = ldjson_read(_BESTBUY_ESCAPED_PRODUCT, sku="6216393")
    assert read.repaired == 1
    assert "repair" in read.summary


def test_backslash_outside_a_string_is_repaired_too() -> None:
    """The breadcrumb shape — a backslash where JSON allows none at all."""
    read = ldjson_read(_BESTBUY_ESCAPED_BREADCRUMB)
    assert read.blocks == 1
    assert read.unparseable == 0
    assert read.repaired == 1


def test_repair_does_not_invent_a_product_that_is_not_there() -> None:
    """A repaired block still has to carry the requested sku. Binding survives repair."""
    assert ldjson_read(_BESTBUY_ESCAPED_PRODUCT, sku="9999999").offers is None


def test_genuinely_unparseable_markup_stays_unknown_and_is_counted() -> None:
    """Repair is a second chance, not a guarantee — and failure is reported, not swallowed."""
    junk = '<script type="application/ld+json">{"@type":"Product", NOPE</script>'
    read = ldjson_read(junk, sku="6216393")
    assert read.offers is None
    assert read.blocks == 1
    assert read.unparseable == 1
    assert read.repaired == 0
    assert "unparseable" in read.summary


def test_healthy_markup_is_never_touched_by_the_repair(bestbuy_pikachu: str) -> None:
    """Strict first. A page that parses today must not take the repair path at all."""
    read = ldjson_read(bestbuy_pikachu, sku="6216393")
    assert read.repaired == 0
    assert read.unparseable == 0
    assert read.summary == ""
    assert read.offers is not None
    assert read.offers[0].available is True
