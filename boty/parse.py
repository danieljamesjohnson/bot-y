"""Extracting stock state from product pages.

Retailers publish stock state in structured blobs, not just in the DOM. Those
blobs are commercially load-bearing — schema.org JSON-LD feeds Google
Shopping, and Next.js hydration data drives the page itself — so they are
kept accurate and change far less often than CSS class names. Reading them
is both more reliable and cheaper than rendering a page.

Every extractor here returns None when it cannot find what it expects. The
caller turns that into UNKNOWN, never into out-of-stock.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
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


def ldjson_offers(html: str) -> list[Offer] | None:
    """Offers from schema.org Product markup, or None if there is none."""
    found: list[Offer] = []
    saw_product = False

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
