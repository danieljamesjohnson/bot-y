"""Per-retailer checkers.

A checker takes a Watch and returns a Result. The contract that matters:
if it cannot determine stock state, it returns UNKNOWN with a reason. It
never guesses, and it never reports out-of-stock as a way of saying "the
page changed and I got lost".

`first_party_only` is the other load-bearing idea. On marketplaces, a
sold-out product is almost always "in stock" from resellers at a markup.
Alerting on those is worse than not alerting at all, because it trains you
to ignore the notifications.
"""

from __future__ import annotations

import logging

from . import parse
from .fetch import Blocked, FetchError, get
from .models import Availability, Result, Watch

log = logging.getLogger(__name__)

#: Seller names that mean "the retailer itself", per retailer.
FIRST_PARTY = {
    "walmart": {"walmart.com", "walmart"},
    "gamestop": {"gamestop", "gamestop.com"},
    "target": {"target"},
    "bestbuy": {"best buy", "bestbuy.com"},
}


def _pick(offers: list[parse.Offer], retailer: str, first_party_only: bool) -> parse.Offer | None:
    """Choose the offer we care about, preferring first-party and cheapest."""
    candidates = offers
    if first_party_only:
        allowed = FIRST_PARTY.get(retailer, set())
        named = [o for o in offers if o.seller and o.seller.strip().lower() in allowed]
        # A page with no seller attribution at all (single-seller retailers
        # like GameStop) is implicitly first-party.
        candidates = named or [o for o in offers if o.seller is None]
    if not candidates:
        return None
    live = [o for o in candidates if o.available]
    pool = live or candidates
    return min(pool, key=lambda o: (o.price is None, o.price or 0))


def check_html(watch: Watch, *, first_party_only: bool = True) -> Result:
    """Generic checker: fetch the product page and read its structured data."""
    try:
        page = get(watch.target)
    except Blocked as exc:
        return Result(watch, Availability.UNKNOWN, detail=f"blocked: {exc}", url=watch.target)
    except FetchError as exc:
        return Result(watch, Availability.UNKNOWN, detail=f"fetch failed: {exc}", url=watch.target)

    offers = parse.ldjson_offers(page.text)
    source = "ld+json"
    if not offers:
        offers = parse.nextdata_offers(page.text)
        source = "__NEXT_DATA__"

    if not offers:
        # Neither structured source present. The page shape changed, or we got
        # a soft block that did not match a known challenge phrase. Either way
        # we do not know — say so loudly rather than implying out-of-stock.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail="no structured stock data found (page shape changed?)",
            url=watch.target,
        )

    offer = _pick(offers, watch.retailer, first_party_only)
    if offer is None:
        return Result(
            watch,
            Availability.OUT_OF_STOCK,
            detail=f"{len(offers)} offer(s) via {source}, none first-party",
            url=watch.target,
        )

    state = Availability.IN_STOCK if offer.available else Availability.OUT_OF_STOCK
    seller = offer.seller or "first-party"
    return Result(
        watch,
        state,
        price=offer.price,
        detail=f"{source}: {offer.raw_availability} from {seller}",
        url=watch.target,
    )


def check_bestbuy_api(watch: Watch, api_key: str) -> Result:
    """Best Buy via the official Products API.

    Best Buy rejects impersonated HTTP at the connection layer (HTTP/2 stream
    reset, HTTP/1.1 timeout) regardless of TLS fingerprint, so scraping it is
    a losing game. The official API is free, sanctioned, and returns exactly
    the field we want — no adversarial relationship at all.

    `watch.target` is the SKU.

    The API key is interpolated into the request URL, which makes it a secret
    that must never reach the returned Result. `boty.status.write` copies both
    `Result.url` and `Result.detail` verbatim into `served/boty/status.json`,
    and that file is served over HTTP — so a credentialed URL in either field
    is a published credential, in flat contradiction of the constraint that
    they live only in ~/.config/boty/env at mode 600. REQ-04 records HTTP 403
    as Best Buy's normal answer, so the error paths are the common case here,
    not the rare one. Every Result below therefore carries `product_url`, and
    anything derived from an exception goes through `_redact` first: curl error
    strings routinely echo the URL they were given.
    """
    product_url = f"https://www.bestbuy.com/site/-/{watch.target}.p"
    api_url = (
        f"https://api.bestbuy.com/v1/products(sku={watch.target})"
        f"?apiKey={api_key}&format=json&show=sku,name,salePrice,onlineAvailability"
    )

    def _redact(text: str) -> str:
        return text.replace(api_key, "***") if api_key else text

    try:
        page = get(api_url)
        data = page.json
    except (Blocked, FetchError) as exc:
        return Result(watch, Availability.UNKNOWN, detail=_redact(f"api error: {exc}"), url=product_url)
    except ValueError as exc:
        return Result(watch, Availability.UNKNOWN, detail=_redact(f"bad api json: {exc}"), url=product_url)

    products = data.get("products") or []
    if not products:
        return Result(
            watch, Availability.UNKNOWN, detail=f"sku {watch.target} not found", url=product_url
        )

    p = products[0]
    available = bool(p.get("onlineAvailability"))
    return Result(
        watch,
        Availability.IN_STOCK if available else Availability.OUT_OF_STOCK,
        price=p.get("salePrice"),
        detail=f"bestbuy api: onlineAvailability={available}",
        url=product_url,
    )
