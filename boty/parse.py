"""Extracting stock state from product pages.

Retailers publish stock state in structured blobs, not just in the DOM. Those
blobs are commercially load-bearing — schema.org JSON-LD feeds Google
Shopping, and Next.js hydration data drives the page itself — so they are
kept accurate and change far less often than CSS class names. Reading them
is both more reliable and cheaper than rendering a page.

Every extractor here returns None when it cannot find what it expects. The
caller turns that into UNKNOWN, never into out-of-stock.

`add_to_cart_offers` is the exception that proves the paragraph above, and it
is deliberately the last resort. Target ships its product pages with the price
module empty and renders stock client-side from an API host it closes to every
agent, so there is no structured blob to read — measured across two unrelated
PDPs and two archive snapshots, `docs/retailer-evidence.md` § Target. The only
thing left on the page is the presentation markup, which is a retailer's CSS
decision and rots without warning. That reader is therefore opt-in per adapter,
labelled `Extraction.DOM`, and every reading through it is `degraded`.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

#: schema.org availability values that mean "you can buy it now".
BUYABLE = {"InStock", "PreOrder", "LimitedAvailability", "BackOrder"}

_LDJSON_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I
)
_NEXTDATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


@dataclass(frozen=True)
class Offer:
    """One seller's offer for a product."""

    available: bool
    price: float | None
    seller: str | None
    raw_availability: str = ""


def _as_float(v: Any) -> float | None:
    try:
        return float(str(v).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None


def _iter_nodes(doc: Any) -> Iterator[dict[str, Any]]:
    """Walk a JSON-LD document, which may be a node, a list, or an @graph."""
    stack: list[Any] = [doc]
    while stack:
        node = stack.pop()
        if isinstance(node, list):
            stack.extend(node)
        elif isinstance(node, dict):
            yield node
            if "@graph" in node:
                stack.append(node["@graph"])


def ldjson_offers(html: str, *, sku: str | None = None) -> list[Offer] | None:
    """Offers from schema.org Product markup, or None if there is none.

    `sku` binds the answer to the question. Without it this walks every Product
    node on the page and pools their offers, which is right for a retailer whose
    product URL *is* the identity — GameStop and Nintendo are addressed by URL,
    so whatever product page came back is the one that was asked for.

    It is wrong for Best Buy, which has no SKU-shaped product URL and is reached
    through a search redirect. There, "the page that came back" and "the product
    that was requested" are different claims, and the gap between them is the
    worst failure this project can produce: `_pick` returns the cheapest
    available first-party offer on the page, so a search-results page carrying
    Product markup yields a $9.99 cable reported as the watched item's stock
    state, with the watch's own name attached.

    A page-level check ("does this SKU appear in the HTML") does not close that.
    The requested SKU appears 71 times in the shipped Best Buy control fixture —
    recommendation rails, breadcrumbs, "customers also viewed" — so a results
    page listing the requested product among eleven others contains it too, and
    the cheapest offer still wins. The binding therefore has to be at the node:
    only the Product whose `sku` *is* the requested one contributes offers.

    This is the same reasoning `_WALMART_PRODUCT_PATH` records below, reached
    the same way. When `sku` is given and no such Product is on the page, the
    return is None — UNKNOWN — including the case where the markup is there but
    carries no `sku` field at all. That costs coverage rather than correctness,
    and Best Buy's control watch turns it into a loud failure within a cycle.
    """
    found: list[Offer] = []
    saw_product = False
    wanted = sku.strip() if sku else None

    for block in _LDJSON_RE.findall(html):
        try:
            doc = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        for node in _iter_nodes(doc):
            # schema.org allows a node to declare several types at once, and
            # `["Product", "ProductModel"]` is ordinary first-party markup. An
            # exact comparison skips it, and the skip is quiet: `saw_product`
            # stays False, so the page reads as "no product here" and the
            # caller says UNKNOWN. That fails safe — it costs coverage, not
            # correctness — which is exactly why nobody noticed, and why it
            # would present as a mysterious UNKNOWN on a retailer whose page
            # is otherwise perfectly readable.
            #
            # Membership, not attribute access: a `@type` that is a dict, an
            # int or a nested list simply fails the test and the node is
            # skipped, rather than raising on retailer-controlled JSON.
            types = node.get("@type")
            types = types if isinstance(types, list) else [types]
            if "Product" not in types:
                continue
            if wanted is not None:
                # `str()` because retailers publish SKUs as both `"6216393"` and
                # `6216393`, and the config supplies a string either way.
                if str(node.get("sku") or "").strip() != wanted:
                    continue
            saw_product = True
            offers = node.get("offers") or []
            for offer in offers if isinstance(offers, list) else [offers]:
                if not isinstance(offer, dict):
                    continue
                raw = str(offer.get("availability") or "")
                seller = offer.get("seller")
                found.append(
                    Offer(
                        available=raw.rsplit("/", 1)[-1] in BUYABLE,
                        price=_as_float(offer.get("price")),
                        seller=(seller or {}).get("name") if isinstance(seller, dict) else seller,
                        raw_availability=raw.rsplit("/", 1)[-1],
                    )
                )

    if not saw_product:
        return None
    return found


#: Walmart's primary product node. Addressed explicitly rather than by
#: searching, because a product page also embeds recommendations, bundles and
#: "customers also bought" — all with their own availabilityStatus. A generic
#: walk happily reports a $12 screen protector as your restock.
_WALMART_PRODUCT_PATH = ("props", "pageProps", "initialData", "data", "product")


def _dig(doc: Any, path: Iterable[str]) -> Any | None:
    for key in path:
        if not isinstance(doc, dict):
            return None
        doc = doc.get(key)
    return doc


def nextdata_offers(html: str) -> list[Offer] | None:
    """The buy-box offer from Next.js hydration data (Walmart).

    Returns a single-element list: whoever currently holds the buy box, with
    their seller name attached. On a scarce item that is usually a marketplace
    reseller at a markup, which is exactly what the caller needs to know —
    "in stock" from a flipper is not a restock.
    """
    m = _NEXTDATA_RE.search(html)
    if not m:
        return None
    try:
        doc = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None

    product = _dig(doc, _WALMART_PRODUCT_PATH)
    if not isinstance(product, dict):
        return None

    status = product.get("availabilityStatus")
    if isinstance(status, dict):
        status = status.get("value")
    if not isinstance(status, str):
        return None

    current = _dig(product, ("priceInfo", "currentPrice")) or {}
    return [
        Offer(
            available=status.upper() in {"IN_STOCK", "AVAILABLE"},
            price=_as_float(current.get("price")) if isinstance(current, dict) else None,
            seller=product.get("sellerName"),
            raw_availability=status,
        )
    ]


#: Button text that means "you can buy this right now".
#:
#: Lifted verbatim from Dan's original pre-bot-y script, which drove Selenium at
#: GameStop and Walmart and decided stock from the Add to Cart button's label and
#: whether it was enabled. It never touched Target. Its method is nonetheless
#: what Target needs, because Target renders the button while shipping no
#: structured data at all.
#:
#: Matched case-insensitively as substrings, so "Add to cart" and
#: "Add to cart for <product name>" both hit.
ADD_TO_CART_PHRASES = ("add to cart", "preorder", "pre-order")

#: The `id` prefix Target puts on the add-to-cart control, plus the TCIN.
#:
#: The `id` and not `data-test`, and that choice is an observation rather than a
#: preference. Three rendered Target PDPs gave three different `data-test` values
#: for the same control — `orderPickupButton` on a pickup-eligible item,
#: `shippingButton` on a ship-only one, and **no `data-test` attribute at all** on
#: the out-of-stock page. An extractor anchored on `data-test` would have read the
#: out-of-stock page as "no control found" and returned UNKNOWN forever, which is
#: safe but useless. The `id` was identical on all three.
#:
#: Target's own name for it is a warning worth keeping: `addToCartButtonOrText`.
#: Target considers this slot capable of rendering text rather than a button, so
#: `_TargetPdpParser` matches the prefix on *any* tag, not just `<button>`.
_CONTROL_ID_PREFIX = "addToCartButtonOrTextIdFor"

#: The Target Plus partner block — `data-test` here, because this one is stable
#: across the pages seen and there is no id to key on. Present on a partner-sold
#: item, and absent — zero occurrences, along with every wording of "sold by" —
#: on a Target-sold one.
_PARTNER_TEST = "targetPlusExtraInfoSection"

#: The rendered price. Appears twice on an in-stock page (the price module and
#: the sticky add-to-cart bar) with the same value, and once when out of stock.
_PRICE_TEST = "product-price"

#: What this reader emits as the seller when no partner block is present.
#:
#: A statement about THIS READER'S OUTPUT, not a guess about Target's markup —
#: which matters, because `boty.retailers.FIRST_PARTY['target']` is checked
#: against it and used to be an unverifiable guess. See that dict's comment.
TARGET_FIRST_PARTY_SELLER = "target"

#: Strips the lead-in off a partner block so only the partner's name is left.
#: "Sold & shipped by Joyin" -> "Joyin". The ampersand is Target's actual
#: wording; "and" and the bare "Sold by" / "Shipped by" forms are accepted too so
#: that a rewording does not silently promote a reseller to first-party.
#:
#: A leading `sold` or `shipped` is REQUIRED rather than optional, so a partner
#: whose own name starts with "By" — "By The Bay" — keeps it. And the trailing
#: space is optional, so a block whose name did not render leaves the empty
#: string rather than the lead-in itself; the caller turns that into `seller=None`,
#: which on a marketplace is UNKNOWN. Both directions fail away from first-party.
_PARTNER_PREFIX_RE = re.compile(
    r"^\s*(?:sold|shipped)\s*(?:&|and)?\s*(?:sold|shipped)?\s*by\b\s*", re.I
)

#: Elements with no end tag, so the depth counter does not drift on them.
_VOID_TAGS = frozenset(
    {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }
)


class _TargetPdpParser(HTMLParser):
    """Pull the add-to-cart control, the price and the partner block out of a PDP.

    `html.parser` from the standard library, deliberately: this project keeps a
    small dependency surface, and adding an HTML parsing library to read three
    elements off one retailer's page would be a poor trade. It also means there
    is no third-party parser sitting in front of bytes a retailer controls.

    Regions are captured by depth rather than by tag, because all three targets
    wrap their text in nested spans and divs — the partner name is in a `Subtext`
    span inside an anchor, and the button label can sit beside an SVG.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._depth = 0
        # (kind, depth_at_open, disabled, text buffer)
        self._open: list[tuple[str, int, bool, list[str]]] = []
        self.controls: list[tuple[str, bool]] = []
        self.prices: list[str] = []
        self.partners: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _VOID_TAGS:
            return
        self._depth += 1
        a = {k.lower(): (v or "") for k, v in attrs}

        kind: str | None = None
        if a.get("id", "").startswith(_CONTROL_ID_PREFIX):
            kind = "control"
        elif a.get("data-test") == _PARTNER_TEST:
            kind = "partner"
        elif a.get("data-test") == _PRICE_TEST:
            kind = "price"
        if kind is None:
            return

        # `aria-disabled` counts as well as the real attribute. Only `disabled=""`
        # was observed on the control itself, but a React component that swaps to
        # the ARIA form is a rewrite away, and the direction of this default is
        # the safe one: an unrecognised disabled state reads as NOT buyable.
        disabled = "disabled" in a or a.get("aria-disabled", "").lower() == "true"
        self._open.append((kind, self._depth, disabled, []))

    def handle_data(self, data: str) -> None:
        for _, _, _, buf in self._open:
            buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID_TAGS:
            return
        while self._open and self._open[-1][1] >= self._depth:
            kind, _, disabled, buf = self._open.pop()
            text = " ".join("".join(buf).split())
            if kind == "control":
                self.controls.append((text, disabled))
            elif kind == "partner":
                self.partners.append(text)
            else:
                self.prices.append(text)
        self._depth = max(0, self._depth - 1)


def add_to_cart_offers(html: str) -> list[Offer] | None:
    """Stock state read off the rendered add-to-cart control. Target's only path.

    Returns None — never `[]`, never `available=False` — when the control is not
    on the page. The distinction is the whole safety property of this reader, and
    it is affordable because of a measured fact: **Target keeps the button and
    disables it when an item is out of stock.** Observed on a page Target's own
    variation chip labelled `Count, 200  - Out of Stock`: same tag, same id, same
    visible text `Add to cart`, plus `disabled=""`, and neither "Out of stock" nor
    "Sold out" anywhere in the document.

    So absence of the control means the render failed, not that the item sold
    out, and returning None for it costs nothing. Had Target *removed* the button
    instead, absence would have been indistinguishable from a broken render and
    this reader would have needed a separate positive out-of-stock marker before
    it could say `available=False` about anything.

    Unrecognised control text is None for the same reason one step along. If the
    slot ever renders something this reader does not know — which Target's own
    name for it, `addToCartButtonOrText`, says is a thing it can do — the honest
    answer is "the page changed and I got lost", not out-of-stock.

    The seller is a Target Plus question. A partner-sold listing carries a
    "Sold & shipped by <Partner>" block and a first-party one carries nothing in
    its place, so absence is what this reader reports as first-party. That claim
    is an observation (`docs/retailer-evidence.md` § Target) rather than an
    assumption, and it is what `FIRST_PARTY['target']` now means. A partner block
    whose name cannot be read yields `seller=None`, which on a marketplace is
    UNKNOWN — the safe direction, and not first-party.
    """
    parser = _TargetPdpParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # pragma: no cover - html.parser is lenient by design
        return None

    if not parser.controls:
        return None

    # First in document order: the primary fulfilment section. A page renders a
    # second, identical control in the sticky bar when the item is buyable, and
    # only the one when it is not, so "first" and "the real one" have coincided
    # on every page seen. If that ever stops being true the control watch reads
    # wrong and reddens `make verify` within a cycle, which is the drift
    # detector this retailer is registered control-only to provide.
    text, disabled = parser.controls[0]
    if not any(phrase in text.lower() for phrase in ADD_TO_CART_PHRASES):
        return None

    available = not disabled

    seller: str | None = TARGET_FIRST_PARTY_SELLER
    if parser.partners:
        stripped = _PARTNER_PREFIX_RE.sub("", parser.partners[0]).strip()
        seller = stripped or None

    price = None
    for raw in parser.prices:
        price = _as_float(raw)
        if price is not None:
            break

    return [
        Offer(
            available=available,
            price=price,
            seller=seller,
            raw_availability="add-to-cart enabled" if available else "add-to-cart disabled",
        )
    ]
