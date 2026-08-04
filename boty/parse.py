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


#: The only characters JSON allows after a backslash (RFC 8259 §7). Anything
#: else is not a "lenient" escape — it is malformed, and `json.loads` is right
#: to refuse it.
_JSON_ESCAPES = frozenset('"\\/bfnrtu')


def _repair_ldjson(block: str) -> str | None:
    """Undo JavaScript string escaping in a JSON-LD block, or None if there is none.

    Runs **only** on a block that already failed `json.loads`, so it cannot
    change the reading of any page that parses today. That ordering is the
    whole safety argument: strict first, repair second, and the caller is told
    which one produced the answer.

    Best Buy started serving its JSON-LD JavaScript-escaped on 2026-08-04 —
    same three blocks, same SKU, previously valid. Measured on the live page
    against `tests/fixtures/bestbuy/pikachu-control.html`, which parses 3/3
    with no backslashes at all:

    - **Outside a string**, 34 occurrences of `\\n` where real newlines belong.
      A backslash outside a JSON string is never valid, which is why the
      breadcrumb block failed at column 2 rather than at the escape.
    - **Inside a string**, 8 occurrences of `\\'` (`Let\\'s Go, Pikachu!`).
      Legal in a JavaScript string literal, illegal in JSON.

    Neither block contained a single *valid* escape — no `\\"`, no `\\\\`, no
    `\\uXXXX` — so there was nothing for a repair to confuse. This function
    still tracks string state rather than running a blind replace, because the
    next retailer to break this way will not be so tidy, and a blind
    `\\n`-to-newline would corrupt a legitimately escaped newline inside a
    string into a raw one, which JSON also forbids.

    Returns None when nothing was changed, so "unparseable and unrepairable"
    stays distinguishable from "repaired".
    """
    out: list[str] = []
    in_string = False
    changed = False
    i, n = 0, len(block)

    while i < n:
        ch = block[i]
        nxt = block[i + 1] if i + 1 < n else ""

        if ch == "\\":
            if in_string and nxt in _JSON_ESCAPES:
                out.append(ch)
                out.append(nxt)
            elif in_string:
                # Invalid escape inside a string: drop the backslash, keep the
                # character. `\'` becomes `'`.
                out.append(nxt)
                changed = True
            else:
                # A backslash outside a string is structural damage. `\n`, `\t`
                # and `\r` stood in for real whitespace; anything else loses
                # only the backslash.
                out.append({"n": "\n", "t": "\t", "r": "\r"}.get(nxt, nxt))
                changed = True
            i += 2
            continue

        if ch == '"':
            in_string = not in_string
        out.append(ch)
        i += 1

    return "".join(out) if changed else None


@dataclass(frozen=True)
class LdJsonRead:
    """What a JSON-LD read *saw*, not only what it extracted.

    `ldjson_offers` returns `list[Offer] | None` and that is all a caller needs
    to decide a verdict. It is not enough to diagnose one. On 2026-08-04 Best
    Buy's control went UNKNOWN with the detail "no schema.org Product on it
    carries that sku", which was true and pointed at the wrong thing entirely:
    three blocks were present and all three were unparseable. "The markup is
    absent", "the markup is malformed" and "the markup is fine but describes a
    different product" demand different responses, and the first message cost
    real time before the second was found.
    """

    offers: list[Offer] | None
    blocks: int = 0
    unparseable: int = 0
    repaired: int = 0

    @property
    def summary(self) -> str:
        """A phrase for `Result.detail`. Empty when there is nothing worth saying."""
        if self.repaired:
            return f"{self.repaired} of {self.blocks} ld+json block(s) needed escape repair"
        if self.unparseable:
            return f"{self.blocks} ld+json block(s) present, {self.unparseable} unparseable"
        return ""


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
    return ldjson_read(html, sku=sku).offers


def ldjson_read(html: str, *, sku: str | None = None) -> LdJsonRead:
    """`ldjson_offers`, plus what was seen on the way. See `LdJsonRead`.

    The verdict logic is identical — this is where it lives, and
    `ldjson_offers` is the thin wrapper for callers that only want offers.
    """
    found: list[Offer] = []
    saw_product = False
    wanted = sku.strip() if sku else None
    blocks = unparseable = repaired = 0

    for block in _LDJSON_RE.findall(html):
        blocks += 1
        try:
            doc = json.loads(block.strip())
        except json.JSONDecodeError:
            # Strict first. Only a block that has already failed is offered to
            # the repair, so no page that parses today can change its reading.
            patched = _repair_ldjson(block.strip())
            if patched is None:
                unparseable += 1
                continue
            try:
                doc = json.loads(patched)
            except json.JSONDecodeError:
                unparseable += 1
                continue
            repaired += 1
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

    return LdJsonRead(
        offers=None if not saw_product else found,
        blocks=blocks,
        unparseable=unparseable,
        repaired=repaired,
    )


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
#: `_AddToCartParser` matches the prefix on *any* tag, not just `<button>`.
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
#:
#: **It applies to Target's page family and to nothing else.** Amazon states its
#: buy-box seller in every layout observed, so on an Amazon page the absence of
#: a seller block means this reader could not read one — UNKNOWN on a
#: marketplace — not that Amazon is selling it. That distinction is why
#: `_ControlFamily` exists rather than one global default.
TARGET_FIRST_PARTY_SELLER = "target"

#: Which retailer's page family a control was found on.
#:
#: The DOM reader serves two retailers and they disagree about exactly one
#: thing: what the ABSENCE of a seller block means. On Target it means
#: first-party — measured, `docs/retailer-evidence.md` § Target: a Target Plus
#: listing carries a "Sold & shipped by" block and a Target-sold one carries
#: nothing in its place. On Amazon it means the opposite of a fact: Amazon names
#: its buy-box seller in both layouts seen (`Shipper / Seller` on a new offer, a
#: `Sold by` anchor on a used one), so nothing to read is this reader getting
#: lost, and `amazon` is in `MARKETPLACES` precisely so that reads UNKNOWN.
#:
#: A single global default would have to pick one of those and be wrong for the
#: other retailer, silently, in the direction that lets a reseller alert.
_TARGET_FAMILY = "target"
_AMAZON_FAMILY = "amazon"

#: Amazon's add-to-cart control ids — EXACT strings, not a prefix.
#:
#: Amazon's is the mirror image of Target's control and every difference is
#: structural rather than cosmetic (observed 2026-08-03, `/dp/B00NTCH52W` and
#: `/dp/B0BX2P43PX`):
#:
#:   - it is a **void `<input>`**, so the depth-based region capture below never
#:     sees it and it has to be read straight off its attributes;
#:   - its label lives in the **`value` attribute**, not in child text;
#:   - its id is fixed per layout rather than per product — `add-to-cart-button`
#:     for the ordinary buy box and `add-to-cart-button-ubb` for a **used** one,
#:     which is the layout the Pokémon GO Plus + is currently sold through.
#:
#: Amazon removes the control when an item cannot be bought rather than
#: disabling it, which is the opposite of Target's measured behaviour. Absence
#: therefore reads UNKNOWN here for a different reason than it does there, and
#: the same safe direction: this plan never observed an unavailable Amazon page,
#: so nothing in this reader may say OUT_OF_STOCK on Amazon's word.
AMAZON_CONTROL_IDS = frozenset({"add-to-cart-button", "add-to-cart-button-ubb"})

#: The buy-box seller on Amazon's ordinary offer-display layout. Two nested
#: anchors, because neither is safe alone: the container slot id is the
#: semantically correct region but its body also carries a popover description,
#: and the inner message class is reused by every other offer-display feature on
#: the page (ten of them). The inner class is read only inside the container.
_AMAZON_SELLER_SLOT = "odf-feature-text-desktop-merchant-info"
_AMAZON_SELLER_TEXT = "offer-display-feature-text-message"

#: The buy-box seller on Amazon's USED offer layout, where the seller is the
#: text of a profile link. The lead-in ("Sold by") sits outside the anchor, so
#: the anchor's text is the seller name and nothing else.
_AMAZON_UBB_SELLER_ID = "sellerProfileTriggerId"

#: Amazon's buy-box price. A class fragment rather than an id: `priceToPay` is
#: Amazon's own name for "the number in the buy box", and it appears on the
#: element wrapping both the screen-reader and the visual copies of it.
#:
#: An Amazon page carries SEVERAL of these — the headline price and then one per
#: buying option (`$9.99` headline, `$9.49` one-time at -5%, `$8.49` Subscribe &
#: Save at -15%, on the shipped control fixture). The reader takes the first in
#: document order, which is the headline the buy box actually displays and, on
#: everything observed, the HIGHEST of them. That is the safe direction for the
#: `max_price` ceiling: reporting a price no lower than the one you would pay
#: can suppress a marginal alert, while reporting a discounted option as the
#: price could let a flip through a ceiling it should have failed.
_AMAZON_PRICE_CLASS = "priceToPay"

#: The first money-shaped run in a price region.
#:
#: Both retailers wrap a price in several elements and Amazon interleaves the
#: accessible copy with a savings blurb, so a region reads
#: `$8.49 with 15 percent savings $ 8 . 49`. `_as_float` over that whole string
#: returns None and the reader would report a priced offer with no price —
#: which `Result.alertable` treats as not alertable, so the failure would be a
#: silent missed restock rather than a loud error.
_MONEY_RE = re.compile(r"\$\s*([\d,]+(?:\.\d{1,2})?)")

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


def _disabled(a: dict[str, str]) -> bool:
    """Whether an element's attributes say the control cannot be used.

    `aria-disabled` counts as well as the real attribute. Only `disabled=""` was
    observed on a control itself, but a React component that swaps to the ARIA
    form is a rewrite away, and the direction of this default is the safe one:
    an unrecognised disabled state reads as NOT buyable.
    """
    return "disabled" in a or a.get("aria-disabled", "").lower() == "true"


class _AddToCartParser(HTMLParser):
    """Pull the add-to-cart control, the price and the seller out of a PDP.

    `html.parser` from the standard library, deliberately: this project keeps a
    small dependency surface, and adding an HTML parsing library to read four
    elements off two retailers' pages would be a poor trade. It also means there
    is no third-party parser sitting in front of bytes a retailer controls.

    Regions are captured by depth rather than by tag, because most of the
    targets wrap their text in nested spans and divs — Target's partner name is
    in a `Subtext` span inside an anchor, Amazon's seller is a span inside a div
    inside a feature container, and a button label can sit beside an SVG.

    **Amazon's control is the exception and it is handled before the depth
    counter is touched at all.** It is a void `<input>`: it never gets an end
    tag, so there is no region to close and nothing between the tags to buffer.
    Its label is in the `value` attribute and its state is on the same element,
    so both are read straight off the attributes as the tag goes past.

    One parser and not two, on purpose. A second near-identical reader is a
    second place for the same bug, and the bug this one exists to prevent —
    reporting out-of-stock when the honest answer is "I got lost" — is exactly
    the kind that gets fixed in one copy.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._depth = 0
        # (kind, depth_at_open, disabled, text buffer)
        self._open: list[tuple[str, int, bool, list[str]]] = []
        # (visible text, disabled, which retailer's page family it came from)
        self.controls: list[tuple[str, bool, str]] = []
        self.prices: list[str] = []
        self.partners: list[str] = []
        self.sellers: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}

        # Amazon's control, read off the attributes before the void-tag return
        # below discards it. Recorded even on a non-void tag, so a future layout
        # that renders the same id as a <button> still reads.
        if a.get("id", "") in AMAZON_CONTROL_IDS:
            self.controls.append((a.get("value", ""), _disabled(a), _AMAZON_FAMILY))

        if tag in _VOID_TAGS:
            return
        self._depth += 1

        kind: str | None = None
        if a.get("id", "").startswith(_CONTROL_ID_PREFIX):
            kind = "control"
        elif a.get("data-test") == _PARTNER_TEST:
            kind = "partner"
        elif a.get("data-test") == _PRICE_TEST:
            kind = "price"
        elif a.get("data-csa-c-slot-id") == _AMAZON_SELLER_SLOT:
            # The container, not the value. Its body also carries a popover
            # description, so the name is read from the inner span below.
            kind = "merchant"
        elif a.get("id", "") == _AMAZON_UBB_SELLER_ID:
            kind = "seller"
        elif _AMAZON_SELLER_TEXT in a.get("class", "") and any(
            open_kind == "merchant" for open_kind, _, _, _ in self._open
        ):
            # Only inside the merchant container: this class is shared by all ten
            # offer-display features on an Amazon page, so unscoped it would read
            # the return policy as the seller.
            kind = "seller"
        elif _AMAZON_PRICE_CLASS in a.get("class", ""):
            kind = "price"
        if kind is None:
            return

        self._open.append((kind, self._depth, _disabled(a), []))

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
                self.controls.append((text, disabled, _TARGET_FAMILY))
            elif kind == "partner":
                self.partners.append(text)
            elif kind == "seller":
                self.sellers.append(text)
            elif kind == "merchant":
                # A container, never a value.
                pass
            else:
                self.prices.append(text)
        self._depth = max(0, self._depth - 1)


def add_to_cart_offers(html: str) -> list[Offer] | None:
    """Stock state read off the add-to-cart control. Target's and Amazon's only path.

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

    Amazon reaches the same conclusion from the opposite fact and the two must
    not be collapsed. Amazon **removes** the control when an item cannot be
    bought, so absence there is genuinely ambiguous between "sold out" and "the
    page changed" — and since this reader has never seen an unavailable Amazon
    page, it says UNKNOWN rather than guessing which. Amazon also serves this
    control in the plain HTTP response, with no browser: it is a `dom`
    extraction on a rung-1 transport, which is why `Result.degraded` was widened
    to fire on the extraction axis independently of the rung.

    **The seller is where the two retailers disagree, and the disagreement is
    load-bearing.** On Target it is a Target Plus question: a partner-sold
    listing carries a "Sold & shipped by <Partner>" block and a first-party one
    carries nothing in its place, so absence is what this reader reports as
    first-party. That claim is an observation
    (`docs/retailer-evidence.md` § Target) rather than an assumption, and it is
    what `FIRST_PARTY['target']` means. On Amazon there is no such absence to
    read: Amazon names the buy-box seller in both layouts observed, so nothing
    to read means this reader could not read it, and the answer is `None` —
    UNKNOWN on a marketplace, never first-party. A partner or buy-box block
    whose name will not parse yields `None` on both. Every direction fails away
    from first-party.
    """
    parser = _AddToCartParser()
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
    text, disabled, family = parser.controls[0]
    if not any(phrase in text.lower() for phrase in ADD_TO_CART_PHRASES):
        return None

    available = not disabled

    # The default is per page family, not global. See `_TARGET_FAMILY`.
    seller: str | None = TARGET_FIRST_PARTY_SELLER if family == _TARGET_FAMILY else None
    if family == _TARGET_FAMILY and parser.partners:
        stripped = _PARTNER_PREFIX_RE.sub("", parser.partners[0]).strip()
        seller = stripped or None
    elif family == _AMAZON_FAMILY and parser.sellers:
        seller = parser.sellers[0].strip() or None

    price = None
    for raw in parser.prices:
        money = _MONEY_RE.search(raw)
        price = _as_float(money.group(1)) if money else _as_float(raw)
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
