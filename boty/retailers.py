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
import os
from urllib.parse import quote_plus

from . import parse
from .browser import BROWSER_PATH_ENV, fetch_rendered
from .fetch import Blocked, FetchError, get
from .models import Availability, Result, Rung, Watch

log = logging.getLogger(__name__)

#: Seller names that mean "the retailer itself", per retailer.
FIRST_PARTY = {
    "walmart": {"walmart.com", "walmart"},
    "gamestop": {"gamestop", "gamestop.com"},
    "target": {"target"},
    "bestbuy": {"best buy", "bestbuy.com"},
}


#: Retailers where a third party can hold the buy box. These are in
#: FIRST_PARTY precisely *because* they are marketplaces, so on them an offer
#: with no seller recorded means "I do not know who is selling this" — which is
#: UNKNOWN territory, not an implicit first-party pass. Stated explicitly here
#: rather than left to fall out of the data, because the difference decides
#: whether a $229.99 flip listing can alert.
MARKETPLACES = {"walmart", "target", "amazon", "bestbuy"}


def _pick(offers: list[parse.Offer], retailer: str, first_party_only: bool) -> parse.Offer | None:
    """Choose the offer we care about, preferring first-party and cheapest."""
    candidates = offers
    if first_party_only:
        allowed = FIRST_PARTY.get(retailer, set())
        named = [o for o in offers if o.seller and o.seller.strip().lower() in allowed]
        # A page with no seller attribution at all (single-seller retailers
        # like GameStop) is implicitly first-party — but only where there is no
        # marketplace to be unattributed *on*. `nextdata_offers` reads
        # `sellerName`, which Walmart's payload simply omits sometimes, so on a
        # marketplace this fallback was handing the buy box to whoever held it.
        unattributed = [] if retailer in MARKETPLACES else [o for o in offers if o.seller is None]
        candidates = named or unattributed
    if not candidates:
        return None
    live = [o for o in candidates if o.available]
    pool = live or candidates
    return min(pool, key=lambda o: (o.price is None, o.price or 0))


def _verdict_from_html(
    watch: Watch,
    html: str,
    *,
    url: str,
    first_party_only: bool,
    rung: Rung,
) -> Result:
    """Turn one page's markup into a verdict. Does no I/O whatsoever.

    Split out of `check_html` so that every transport — impersonated HTTP,
    a rendered browser, and whatever rung 3 grows into next — reaches the same
    UNKNOWN logic instead of each reimplementing it. The two escape hatches
    below (a retailer with no first-party allow-list, and an unattributed offer
    on a marketplace) are the most load-bearing behaviour in this module: a
    second copy of them would be a second place to get them subtly wrong, and
    the failure would be silent by construction, because a wrong UNKNOWN and a
    wrong OUT_OF_STOCK look identical on a dashboard until a drop is missed.

    `url` and `rung` are passed in rather than derived, because only the caller
    knows them: `watch.target` is a URL for some retailers and a SKU for
    others, and how a page was obtained is a fact about the transport that no
    amount of reading the markup can recover.
    """
    offers = parse.ldjson_offers(html)
    source = "ld+json"
    if not offers:
        offers = parse.nextdata_offers(html)
        source = "__NEXT_DATA__"

    if not offers:
        # Neither structured source present. The page shape changed, or we got
        # a soft block that did not match a known challenge phrase. Either way
        # we do not know — say so loudly rather than implying out-of-stock.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail="no structured stock data found (page shape changed?)",
            url=url,
            rung=rung,
        )

    offer = _pick(offers, watch.retailer, first_party_only)
    if offer is None:
        if first_party_only and watch.retailer not in FIRST_PARTY:
            # `FIRST_PARTY.get(retailer, set())` yields an empty allow-list for
            # an unconfigured retailer, so nothing can ever match it and any
            # page that names its seller lands here. The truth is a config gap,
            # not a stock fact — reporting OUT_OF_STOCK would be the same
            # conflation UNKNOWN exists to prevent, and REQUIREMENTS targets
            # three more retailers that arrive through this door.
            return Result(
                watch,
                Availability.UNKNOWN,
                detail=(
                    f"{len(offers)} offer(s) via {source}, but no first-party seller list "
                    f"is configured for '{watch.retailer}' — cannot tell whose they are"
                ),
                url=url,
                rung=rung,
            )
        if first_party_only and watch.retailer in MARKETPLACES and any(o.seller is None for o in offers):
            # The page says something is buyable but does not say by whom, on a
            # site where that is a real question. OUT_OF_STOCK would be a
            # confident wrong answer; IN_STOCK could be a flipper's listing.
            return Result(
                watch,
                Availability.UNKNOWN,
                detail=(
                    f"{len(offers)} offer(s) via {source} with no seller recorded, and "
                    f"{watch.retailer} is a marketplace — cannot tell whose offer this is"
                ),
                url=url,
                rung=rung,
            )
        return Result(
            watch,
            Availability.OUT_OF_STOCK,
            detail=f"{len(offers)} offer(s) via {source}, none first-party",
            url=url,
            rung=rung,
        )

    state = Availability.IN_STOCK if offer.available else Availability.OUT_OF_STOCK
    seller = offer.seller or "first-party"
    return Result(
        watch,
        state,
        price=offer.price,
        detail=f"{source}: {offer.raw_availability} from {seller}",
        url=url,
        rung=rung,
    )


def check_html(watch: Watch, *, first_party_only: bool = True) -> Result:
    """Generic checker: fetch the product page and read its structured data."""
    try:
        page = get(watch.target)
    except Blocked as exc:
        return Result(watch, Availability.UNKNOWN, detail=f"blocked: {exc}", url=watch.target)
    except FetchError as exc:
        return Result(watch, Availability.UNKNOWN, detail=f"fetch failed: {exc}", url=watch.target)

    return _verdict_from_html(
        watch,
        page.text,
        url=watch.target,
        first_party_only=first_party_only,
        rung=Rung.TLS,
    )


def bestbuy_product_url(sku: str) -> str:
    """The URL that reaches Best Buy's page for `sku`. Shared by both rungs.

    Best Buy has no stable SKU-shaped product URL any more, and this function
    exists because that is not obvious and cost a whole spike to establish:

    - The legacy `/site/<slug>/<sku>.p` form is *uniformly refused* — HTTP/2
      stream reset, three attempts across two unrelated SKUs, browser and
      impersonated HTTP alike. It is a dead link, so publishing it as
      `Result.url` on a status page anybody clicks was a small lie.
    - The live form is `/product/<slug>/<ID>`, where `<ID>` is an opaque token
      (`J7GSL4G7GQ`) that is **not** the SKU and cannot be derived from it.

    What does work is Best Buy's own search: a bare SKU matches exactly one
    product and the site redirects to that product's page. Verified against SKU
    6216393 — the rendered result carries a single schema.org Product with
    `price: 59.99` and `seller.name: "Best Buy"`, and its canonical is
    `/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ/sku/6216393`.

    The miss path is the reason to prefer this over a guessed URL template, and
    it was verified too: when a SKU matches nothing, the search page that comes
    back carries **no** schema.org Product markup at all — no offers, from a
    page listing a dozen products — so `_verdict_from_html` says UNKNOWN rather
    than reading somebody's accessory as your restock. Both branches of this
    are evidence, not assumption; see `docs/retailer-evidence.md`.

    `watch.target` therefore stays the SKU for `bestbuy` on both rungs, which
    is what lets one YAML entry serve the browser path and the API path
    without the reader having to know which one is running.
    """
    return f"https://www.bestbuy.com/site/searchpage.jsp?st={quote_plus(sku)}"


def _redact_host_paths(text: str) -> str:
    """Strip local filesystem paths out of text destined for a Result.

    The browser rung handles no credential, so it has nothing of that kind to
    leak — but it is the only transport that reports failures in terms of *this
    machine*: a missing binary, a Chrome that would not start, a nodriver
    traceback naming the executable and its throwaway profile directory. Those
    strings land in `Result.detail`, which `boty.status.write` copies verbatim
    into `served/boty/status.json`, and that file is served over HTTP. A stock
    monitor has no business publishing somebody's home directory layout to
    anyone who can reach the dashboard.
    """
    home = os.path.expanduser("~")
    configured = os.environ.get(BROWSER_PATH_ENV)
    if configured:
        text = text.replace(configured, "<browser>")
    if home and home != "/":
        text = text.replace(home, "~")
    return text


def check_bestbuy_browser(watch: Watch, *, first_party_only: bool = True) -> Result:
    """Best Buy via a real browser — rung 3, and every reading is DEGRADED.

    Not because a browser is better. It is slower, heavier, drags a Chrome
    process onto the box, and is the *worse* transport for at least one
    retailer we already support (headless Chrome is served a Cloudflare wall by
    gamestop.com, which rung 1 reads on every `make verify`). This exists for
    the narrower reason `boty.browser` was built for: Best Buy refuses
    impersonated HTTP at the connection layer regardless of TLS fingerprint, so
    the choice here is not "cheap or heavy" but "heavy or nothing".

    It is the *documented* path anyway, ahead of the official API, because a
    path that needs a credential most people cannot get is a footnote rather
    than support: Best Buy's developer signup needs manual approval and rejects
    free email domains. `boty.cli._make_checker` prefers `check_bestbuy_api`
    when a key happens to exist — it is strictly more reliable and not degraded
    — and falls back here when one does not, which is the ordinary case.

    Everything returned carries `rung=Rung.BROWSER`, error paths included, and
    `Result.degraded` follows from that. A rung is a fact about the transport,
    not about the verdict: an UNKNOWN from a browser that could not start is
    still a browser reading, and labelling it a plain TLS fetch would make the
    support matrix quietly wrong about the one retailer it is most careful
    about.
    """
    product_url = bestbuy_product_url(watch.target)

    try:
        page = fetch_rendered(product_url)
    except Blocked as exc:
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact_host_paths(f"blocked: {exc}"),
            url=product_url,
            rung=Rung.BROWSER,
        )
    except FetchError as exc:
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact_host_paths(f"fetch failed: {exc}"),
            url=product_url,
            rung=Rung.BROWSER,
        )

    return _verdict_from_html(
        watch,
        page.text,
        url=product_url,
        first_party_only=first_party_only,
        rung=Rung.BROWSER,
    )


def check_bestbuy_api(watch: Watch, api_key: str) -> Result:
    """Best Buy via the official Products API — the upgrade, not the default.

    Best Buy rejects impersonated HTTP at the connection layer (HTTP/2 stream
    reset, HTTP/1.1 timeout) regardless of TLS fingerprint, so rung 1 is out.
    This path is sanctioned, returns exactly the field we want, and has no
    adversarial relationship at all — it is strictly better than driving a
    browser at the site, which is why `boty.cli._make_checker` prefers it.

    It is nonetheless *not* the documented path, and that is a deliberate
    reversal: the developer signup needs manual approval and rejects free email
    domains, so most people cannot get a key, and a path most people cannot
    take is a footnote rather than support. `check_bestbuy_browser` is what a
    fresh clone runs. Where this one runs, the reading is not degraded.

    `watch.target` is the SKU, the same value `check_bestbuy_browser` takes, so
    one YAML entry serves both rungs. `Result.url` comes from the shared
    `bestbuy_product_url` for the same reason it exists at all: the legacy
    `/site/-/<sku>.p` link this used to publish is refused by Best Buy now, so
    every Result here carried a URL that 404s for whoever clicked it.

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

    Every Result below also carries `rung=Rung.API` — the error paths as much
    as the success one. A rung is a fact about the transport, not about the
    verdict, so an UNKNOWN produced by a 403 from the official API is still an
    API reading. Leaving the `Rung.TLS` default in place on those paths would
    label a key-holder's Best Buy reading as a plain page fetch, which is
    exactly the claim the support matrix makes on this field's word.
    """
    product_url = bestbuy_product_url(watch.target)
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
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact(f"api error: {exc}"),
            url=product_url,
            rung=Rung.API,
        )
    except ValueError as exc:
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact(f"bad api json: {exc}"),
            url=product_url,
            rung=Rung.API,
        )

    products = data.get("products") or []
    if not products:
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=f"sku {watch.target} not found",
            url=product_url,
            rung=Rung.API,
        )

    p = products[0]
    available = bool(p.get("onlineAvailability"))
    return Result(
        watch,
        Availability.IN_STOCK if available else Availability.OUT_OF_STOCK,
        price=p.get("salePrice"),
        detail=f"bestbuy api: onlineAvailability={available}",
        url=product_url,
        rung=Rung.API,
    )
