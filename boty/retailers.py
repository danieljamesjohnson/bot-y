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
import time
from urllib.parse import quote_plus

from . import parse
from .browser import BROWSER_PATH_ENV, fetch_rendered
from .fetch import Blocked, FetchError, get, is_refusal
from .models import (
    STORE_SCOPED,
    Availability,
    Extraction,
    Result,
    Rung,
    Watch,
    established_shipping,
)

log = logging.getLogger(__name__)

#: Seller names that mean "the retailer itself", per retailer.
FIRST_PARTY = {
    "walmart": {"walmart.com", "walmart"},
    "gamestop": {"gamestop", "gamestop.com"},
    # `target` is the only entry here that is NOT a retailer's own string, and
    # the difference is the whole reason this comment exists.
    #
    # Every other value is an `offers.seller.name` read verbatim off a live page.
    # Target publishes no seller name anywhere, at any rung — not "we have not
    # looked", but measured and structural (docs/retailer-evidence.md § Target).
    # This entry was therefore an unverifiable guess for as long as it existed,
    # and it could not be fixed by looking harder.
    #
    # It is now a statement about OUR OWN READER'S OUTPUT.
    # `parse.add_to_cart_offers` emits the literal `parse.TARGET_FIRST_PARTY_SELLER`
    # when a PDP carries no Target Plus partner block, and this entry is the
    # matching half of that. The claim underneath it is checkable and checked:
    # *absence of a "Sold & shipped by" block on a Target PDP means Target is the
    # seller*. Zero occurrences of that block, or any wording of it, on the
    # first-party control page; unmissable on a partner-sold one.
    #
    # `target` stays in MARKETPLACES below, and that is not redundant. Removing
    # it would re-enable `_pick`'s unattributed-offer fallback, which is what
    # lets a Target Plus reseller listing alert — the flipper case the whole
    # first-party filter exists for.
    "target": {parse.TARGET_FIRST_PARTY_SELLER},
    # `Amazon.com` is the literal buy-box seller string, read verbatim off
    # https://www.amazon.com/dp/B00NTCH52W (Amazon Basics 20-pack AA) on
    # 2026-08-03 at rung 1, from the offer-display feature Amazon labels
    # `Shipper / Seller`:
    #
    #     <span class="…offer-display-feature-text-message">Amazon.com</span>
    #
    # The bare `amazon` is here for the same reason Nintendo's short forms are:
    # so a wording change does not silently demote the retailer to an
    # unrecognised third party. Nothing longer is guessed — the entry is one
    # observed string plus the obvious contraction of it.
    #
    # `amazon` stays in MARKETPLACES below and that is the load-bearing half.
    # Amazon's buy box is frequently a third party's, and on the Pokémon GO
    # Plus + it currently IS one: a USED unit from
    # `LO Store (We Record Serial Numbers To avoid FRAUD)` at $219 against a
    # $54.99 MSRP. Without the marketplace entry `_pick`'s unattributed-offer
    # fallback would hand the buy box to whoever holds it.
    "amazon": {"amazon.com", "amazon"},
    "bestbuy": {"best buy", "bestbuy.com"},
    # `Nintendo of America Inc.` is the literal `offers.seller.name` on every
    # nintendo.com/us/store product page seen (docs/retailer-evidence.md); the
    # shorter forms are here so a wording change does not silently demote the
    # manufacturer of the product to an unrecognised third party.
    "nintendo": {"nintendo of america inc.", "nintendo", "nintendo.com"},
}


#: Retailers where a third party can hold the buy box. These are in
#: FIRST_PARTY precisely *because* they are marketplaces, so on them an offer
#: with no seller recorded means "I do not know who is selling this" — which is
#: UNKNOWN territory, not an implicit first-party pass. Stated explicitly here
#: rather than left to fall out of the data, because the difference decides
#: whether a $229.99 flip listing can alert.
#:
#: `nintendo` is deliberately absent, and that absence is a claim backed by
#: evidence rather than an oversight: Nintendo's store has no third-party seller
#: surface at all — no buy box, no "other sellers", nobody but Nintendo of
#: America who can list on it. Adding it here "to be safe" would be the opposite
#: of safe, because it would strip `_pick`'s unattributed-offer fallback and turn
#: any future page that drops the seller node into a permanent UNKNOWN.
MARKETPLACES = {"walmart", "target", "amazon", "bestbuy"}

#: Settle time for `check_target_browser`'s single retry, in seconds.
#:
#: Not a tuned number — a deliberately unambitious one. The control was measured
#: absent at 1.0s and present at 3.0s and 6.0s on the live page, and the default
#: 3.0 is what raced under load. Retrying at 3.0 would just re-run the coin
#: toss, so this sits far enough past the observed boundary that the retry is
#: answering a different question than the first attempt did. It is bounded by
#: `fetch_rendered`'s own 45s timeout, and REQ-08 has budget: a full pass with
#: two browser renders measures 37-49s against 120s, and this only runs when
#: the first read already failed.
_TARGET_RETRY_SETTLE = 10.0


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
    sku: str | None = None,
    allow_dom: bool = False,
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

    `sku` is the same idea one step further. Where a retailer is addressed by
    URL, the page that came back *is* the product that was asked for and there
    is nothing to check. Where it is reached through a search redirect — Best
    Buy, which has no SKU-shaped product URL — those are two different claims,
    and passing the SKU here is what makes the second one checkable. See
    `parse.ldjson_offers`.

    `allow_dom` opts an adapter into `parse.add_to_cart_offers`, the presentation
    reader, after both structured sources have come back empty. Opt-in and not
    universal, deliberately: a GameStop page that lost its `ld+json` would
    otherwise fall through to a DOM read and change an existing retailer's
    behaviour without anybody deciding to. Every adapter that does not pass it
    behaves byte-identically to before.

    The label follows the reader that actually produced the answer, and the case
    worth stating is the one where nothing did. With `allow_dom=True` and all
    three readers empty, execution reaches the no-offers UNKNOWN below — and that
    is still a DOM reading, because the DOM reader is what ran and found nothing.
    It is also the single most likely path in production, since it is what a
    broken render looks like. Labelling it `structured` would tell a reader the
    DOM path was never involved in exactly the situation where it is the thing
    that failed.

    "DOES NO I/O WHATSOEVER" IS AMENDED RATHER THAN WITHDRAWN, on this repo's
    house style for a reversal (`models.py:335-342`, `pacing.py:29-53`): the
    original sentence stays because it is still true in the sense it was written
    — no NETWORK I/O, which is why every transport can reach the same UNKNOWN
    logic and why this function is testable with no fixtures and no monkeypatch.
    What it now also does, once, is READ THIS PROCESS'S OWN WALL CLOCK, to stamp
    `Result.read_at`. That is a fact about the reading rather than a fetch, but
    it is not nothing, and a reader who took the old sentence to mean "pure"
    should learn otherwise here rather than by surprise.
    """
    # WHEN THIS PAGE WAS READ. Taken ONCE, here, at the top of the function, for
    # the same reason `store` is read once below: every arm of one verdict must
    # agree on the moment, and eight clock reads would be eight slightly
    # different answers to a question with one answer.
    #
    # ENTERING THIS FUNCTION *IS* THE MOMENT THE PAGE WAS IN HAND. It is only
    # ever reached with markup a transport already obtained, so all eight returns
    # below follow a response that came back — they differ in what the page SAID,
    # not in whether it answered.
    #
    # THE IMPRECISION, STATED RATHER THAN HIDDEN: the stamp is taken within one
    # call of the fetch returning, so for a browser adapter it trails the actual
    # response by the settle time, and the LATER of the two moments is the one
    # recorded. That is acceptable here and the reason is a unit argument, not a
    # shrug — the thing this stamp is compared against is a retailer's cadence,
    # measured in minutes to hours (a retailer at seven refusals is on a
    # ~97-minute interval), and a difference measured in seconds cannot move a
    # verdict about it. Recording the later moment is also the conservative
    # direction: it can only make a reading look younger than it is by seconds,
    # never older by more.
    #
    # PASSED EXPLICITLY AT ALL EIGHT SITES BELOW, never inherited from the
    # dataclass default. The default means "no reading was taken", so an arm that
    # forgot to name this would silently claim the opposite of what happened —
    # and `tests/test_retailers.py`'s AST gate requires each site to say it.
    #
    # REJECTED, RECORDED SO IT IS NOT RE-PROPOSED AS A TIDY-UP: threading
    # `read_at` in from the four callers as a parameter, so the stamp is taken
    # where the fetch actually returned. It reads cleaner and it is wrong here.
    # `tests/test_retailers.py` calls this function directly at eleven sites and
    # `tests/test_alert_text.py` at one, so an optional parameter would default
    # those twelve readings to `None` — a reading that WAS taken reporting no age
    # at all, which is the dangerous direction — and the AST completeness gate
    # would stay green the whole time, because every site would still name the
    # field. A required parameter would break those twelve callers loudly, which
    # is honest, but it buys milliseconds of precision on a comparison whose unit
    # is a retailer's cadence in minutes.
    read_at = time.time()
    # `ldjson_read` rather than `ldjson_offers`: the verdict is the same, but a
    # malformed block and an absent one are different diagnoses and only this
    # call can tell them apart. See `LdJsonRead` — the distinction was bought
    # on 2026-08-04, when Best Buy served three unparseable blocks and the
    # detail below said the SKU had not resolved.
    # WHICH STORE ANSWERED. Read once, here, because this is where the html is,
    # and threaded onto every return below — including the UNKNOWNs, which are
    # the paths a human reads when something is wrong. That is the same "error
    # paths carry the same metadata as success paths" rule `check_target_browser`
    # commits to for `rung` and `extraction`.
    #
    # Called with no retailer predicate: the path is Walmart's own hydration
    # shape, so every other retailer here returns `None` because the path is
    # absent, which is measured against the whole captured corpus in
    # `tests/test_parse.py`. A predicate would be the claim "only Walmart has
    # stores", maintained in a second place.
    #
    # READ HERE, COMPARED BELOW. 05-01 shipped this line with the note that
    # nothing below branched on it and that turning an unpinned or mismatched
    # store into UNKNOWN was 05-02's guard. 05-02 added exactly that: the two
    # `STORE_SCOPED` returns further down, ahead of the offer logic. The read
    # stays a single call in a single place, and the comparison happens once.
    #
    # WHAT SHIPPING COSTS, threaded onto every Result below in the same ten
    # places `store` is — the eight here and the two refusal arms in
    # `check_html` — with `shipping=offer.shipping` on the one success return
    # that has an offer and an explicit `shipping=None` on the other nine.
    #
    # AND THE HONEST ASYMMETRY WITH `store`, written out rather than pretended
    # to be a gate: a site missed here would be behaviourally INVISIBLE.
    # `None` is the correct value on every offerless path, so forgetting one
    # would change no verdict and redden no test. This is a statement of intent
    # that nothing can watch go red, and the reason it is stated at all is that
    # the next person to add a return here will otherwise inherit the default
    # by accident and never learn whether they meant to.
    store = parse.nextdata_store(html)
    ld = parse.ldjson_read(html, sku=sku)
    offers = ld.offers
    # A repaired read is never silent. Naming it in `source` rather than
    # appending to `detail` keeps the healthy string byte-identical — 03.1-04
    # verified `ld+json: InStock from Best Buy` character-for-character against
    # live output — while every message that cites the source now says when the
    # markup had to be repaired to be read at all.
    source = "ld+json (repaired)" if ld.repaired else "ld+json"
    if not offers:
        offers = parse.nextdata_offers(html)
        source = "__NEXT_DATA__"

    # `extraction` tracks which reader spoke, not whether it liked what it saw.
    extraction = Extraction.DOM if allow_dom else Extraction.STRUCTURED
    if not offers and allow_dom:
        offers = parse.add_to_cart_offers(html)
        source = "add-to-cart control"
    elif offers:
        extraction = Extraction.STRUCTURED

    # WHICH STORE THIS READING IS ABOUT — two guards, ahead of every verdict.
    #
    # On 2026-08-09 the daemon recorded the Walmart milk control OUT_OF_STOCK at
    # $3.17 while three live reads minutes later returned IN_STOCK at $2.42. Same
    # URL, same parser. A parser bug does not change a price: two different
    # stores answered, and the system published one store's shelf as a fact about
    # another's. 05-01 made the store recordable; these two returns are what stop
    # a reading from the wrong store being a verdict at all.
    #
    # PLACEMENT. Here, after `extraction` is settled and BEFORE `if not offers:`,
    # so they are the first thing in this function that can return and no stock
    # verdict can form ahead of them — while the guarded Results still carry the
    # same `rung`, `extraction`, `url` and `store` as every other return on the
    # path. That is the "error paths carry the same metadata as success paths"
    # rule four adapter docstrings already commit to.
    #
    # REJECTED PLACEMENT, recorded so it is not re-proposed as an optimisation:
    # hoisting the config-gap check into `check_html` AHEAD of the fetch, which
    # would save a request. It loses two things worth more than the request. A
    # control watch that stops making its request stops proving the transport
    # works, which is the control's entire job. And `Pacer` records refusals off
    # the results of the requests actually made, so a retailer that silently
    # stopped being asked would drift out of the backoff accounting. Politeness
    # is a hard constraint here, but not at the price of blinding the control.
    #
    # THE COMMENTS BELOW SIT ABOVE THEIR `if`, NOT INSIDE IT, ON PURPOSE. Each
    # guard's condition line is immediately followed by its `return Result(` and
    # `Availability.UNKNOWN`, so M9 and M10 in `scripts/mutation_check.py` can
    # anchor on the condition and the verdict and on NOTHING ELSE. M2's comment
    # records why that matters: it was re-anchored once already when the prose on
    # its branch moved, and "matching the message text would tie a mutation to
    # prose that is edited far more often than the verdict is."
    if watch.retailer in STORE_SCOPED:
        # The config gap, reported as a config gap — the shape the
        # no-first-party-list UNKNOWN below uses, for the same reason: a
        # missing piece of configuration is not a stock fact, and laundering
        # one into the other is what UNKNOWN exists to prevent. The message
        # names the key by the name a user types and the file they type it
        # in, so it is a fix instruction rather than a complaint.
        if watch.store_id is None:
            return Result(
                watch,
                Availability.UNKNOWN,
                detail=(
                    f"no store_id pinned for this watch — set store_id in "
                    f"config/products.yaml. A {watch.retailer} page answers for "
                    f"whichever store it chooses, so with nothing pinned this "
                    f"reading is about some store, not necessarily yours"
                ),
                url=url,
                rung=rung,
                extraction=extraction,
                store=store,
                shipping=None,
                read_at=read_at,
            )
        # `store is None` is handled INSIDE the mismatch guard rather than as a
        # third one. "The page did not name a store" and "the page named a
        # different store" are the same fact for the purposes of the verdict:
        # neither can be SHOWN to come from the pinned store.
        #
        # `!r` and not bare interpolation: `store` is a string read out of a
        # retailer's own JSON and this sentence reaches a plain-text notification
        # body, so a value carrying whitespace or a newline could otherwise
        # silently restructure the message.
        #
        # Rendered before the branch, not inside it, so that the condition line
        # and the verdict are adjacent — see the anchoring note above.
        answered = f"store {store!r}" if store is not None else "no store"
        if store != watch.store_id:
            return Result(
                watch,
                Availability.UNKNOWN,
                detail=(
                    f"the page named {answered}; this watch pins store "
                    f"{watch.store_id!r} — a reading that cannot be shown to come "
                    f"from the pinned store is not a verdict about it"
                ),
                url=url,
                rung=rung,
                extraction=extraction,
                store=store,
                shipping=None,
                read_at=read_at,
            )

    if not offers:
        if sku is not None:
            # A distinct diagnosis, because it is a distinct and *evidenced*
            # branch: Best Buy's answer to a SKU that matches nothing is a
            # search page (docs/retailer-evidence.md). Reporting that as "page
            # shape changed?" sends the reader to debug an extractor that is
            # working perfectly — the same misattribution this phase already
            # fixed twice, for the Imperva and Akamai walls, one layer up.
            return Result(
                watch,
                Availability.UNKNOWN,
                detail=(
                    f"sku {sku} did not resolve to a product page — no "
                    f"schema.org Product on it carries that sku"
                    + (f" ({ld.summary})" if ld.summary else "")
                ),
                url=url,
                rung=rung,
                extraction=extraction,
                store=store,
                shipping=None,
                read_at=read_at,
            )
        # Neither structured source present. The page shape changed, or we got
        # a soft block that did not match a known challenge phrase. Either way
        # we do not know — say so loudly rather than implying out-of-stock.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=(
                "no structured stock data found (page shape changed?)"
                + (f" ({ld.summary})" if ld.summary else "")
            ),
            url=url,
            rung=rung,
            extraction=extraction,
            store=store,
            shipping=None,
            read_at=read_at,
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
                extraction=extraction,
                store=store,
                shipping=None,
                read_at=read_at,
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
                extraction=extraction,
                store=store,
                shipping=None,
                read_at=read_at,
            )
        return Result(
            watch,
            Availability.OUT_OF_STOCK,
            detail=f"{len(offers)} offer(s) via {source}, none first-party",
            url=url,
            rung=rung,
            extraction=extraction,
            store=store,
            shipping=None,
            read_at=read_at,
        )

    state = Availability.IN_STOCK if offer.available else Availability.OUT_OF_STOCK
    seller = offer.seller or "first-party"
    # WHAT THE CEILING MEASURED, which since 2026-08-11 is a live question
    # rather than a refusal. Where no shipping cost could be established the
    # ceiling is applied to the item price alone and the alert goes out (Dan's
    # decision), so the suffix says WHICH figure was measured instead of saying
    # the ceiling could not be evaluated — it can. Only when a ceiling is
    # configured: a watch with no `max_price` consults neither figure, so
    # telling its reader about one would be noise about a decision nobody makes.
    #
    # THE CONDITION NOW CATCHES A NEGATIVE SHIPPING COST TOO. It used to read
    # `offer.shipping is None`, which meant a negative figure produced no suffix
    # at all while the ceiling treated it as unestablished — the suffix and the
    # decision disagreeing about the same reading. `established_shipping` is the
    # one predicate all three consumers ask.
    #
    # The healthy string stays BYTE-IDENTICAL. 03.1-04 verified
    # `ld+json: InStock from Best Buy` character-for-character against live
    # output, and the `ld+json (repaired)` decision already respected that
    # constraint by naming the repair in `source` rather than appending here.
    #
    # NO MUTATION MAY ANCHOR ON THIS SENTENCE. It is prose, it will be reworded,
    # and Phase 5 had to re-anchor two mutations for exactly that — as did this
    # plan, for M4, M17 and M18. M4, M17, M18, M27 and M28 all anchor on control
    # flow or expressions in `boty/models.py`.
    detail = f"{source}: {offer.raw_availability} from {seller}"
    if watch.max_price is not None and established_shipping(offer.shipping) is None:
        detail += (
            " — no shipping cost was read, so the ceiling was applied to the "
            "item price alone and no delivered total is stated"
        )
    return Result(
        watch,
        state,
        price=offer.price,
        detail=detail,
        url=url,
        rung=rung,
        extraction=extraction,
        store=store,
        shipping=offer.shipping,
        read_at=read_at,
    )


def check_html(watch: Watch, *, first_party_only: bool = True) -> Result:
    """Generic checker: fetch the product page and read its structured data."""
    try:
        page = get(watch.target)
    except Blocked as exc:
        # `store=None` and `shipping=None` stated, not inherited: a refusal
        # produced no page, so nothing said which store answered or what
        # shipping would cost. Written out so this arm declares its metadata
        # the way the browser adapters declare theirs, rather than depending on
        # a dataclass default staying what it is today.
        #
        # `read_at=None` IS THE SAME RULE AND IT INVERTS THE OBVIOUS ONE, which
        # is why it is argued here rather than assumed. A refusal DOES happen at
        # a wall-clock moment — this line runs at a definite time — and stamping
        # it is still wrong, because the stamp dates a READING and no reading was
        # taken. Stamping refusals would refresh the age of a reading that never
        # happened, which is the 2026-08-12 Walmart failure rebuilt inside the
        # fix meant to prevent it. `pacing.py:196-199` wrote the lesson down for
        # `_warned_since` already: *"stamping at write time would refresh the
        # record forever and the age-out would never fire once — a bound that
        # cannot bind is worse than no bound, because it reads like one in the
        # file."* Amazon and Walmart have both refused this host for hours at a
        # stretch; under the stamped version they would publish a perpetually
        # fresh age while nothing was read at all. M31 rebuilds exactly that.
        #
        # STATED AT EVERY ARM AND NEVER INHERITED, in all four adapters, because
        # the entire purpose of this field is to distinguish "read" from "not
        # read" and a dataclass default cannot state which one an arm is.
        return Result(watch, Availability.UNKNOWN, detail=f"blocked: {exc}", url=watch.target, refused=True, store=None, shipping=None, read_at=None)
    except FetchError as exc:
        # Same inversion: the transport failed, so nothing came back to date.
        return Result(watch, Availability.UNKNOWN, detail=f"fetch failed: {exc}", url=watch.target, refused=is_refusal(exc), store=None, shipping=None, read_at=None)

    return _verdict_from_html(
        watch,
        page.text,
        url=watch.target,
        first_party_only=first_party_only,
        rung=Rung.TLS,
    )


def check_amazon(watch: Watch, *, first_party_only: bool = True) -> Result:
    """Amazon at rung 1, reading the add-to-cart control — the cheap/fragile corner.

    The same transport as `check_html` and a different reader, which is the
    whole of the difference and the reason this is a separate function rather
    than a flag on that one. Amazon serves its `/dp/<ASIN>` page to impersonated
    HTTP without complaint — three requests on 2026-08-03, three HTTP 200s, no
    `BLOCK_PHRASES` match, 1.9–3.2 MB each — and publishes **no** structured
    stock data in it: zero `application/ld+json`, no `__NEXT_DATA__`, and not one
    of its JSON script blobs carries a price, an availability or a seller.

    What it does serve, server-side and with no browser, is the add-to-cart
    control, the `#availability` line and a named buy-box seller. So Amazon is
    **rung 1 + `dom`**: the cheapest transport this project has with the most
    fragile extraction it has. That combination is exactly the one 03.1-05
    widened `Result.degraded` for — a DOM reading is discounted because of what
    was read, independently of how the bytes arrived — and Amazon is its first
    real user. Do not "upgrade" this to rung 3: the ladder says stop at the
    first rung that works, and starting a browser to obtain bytes curl already
    returned would spend a Chrome process to learn nothing.

    Every Result carries `extraction=Extraction.DOM`, the error paths included,
    for the reason `check_target_browser` gives about its rung: it is a fact
    about how a reading was obtained rather than about the verdict, and the
    support matrix makes its claim on this field's word. The rung stays the
    default `Rung.TLS`, because that is what it is.

    Failure strings go through `_redact_host_paths` on the same principle as the
    browser adapters — `status.write` copies `detail` into a file served over
    HTTP — even though rung 1 has no browser path to leak. It costs nothing and
    it means no adapter is the one that forgot.
    """
    try:
        page = get(watch.target)
    except Blocked as exc:
        # `read_at=None`: Amazon refused, so no page was read. The refusal has a
        # moment; the reading it did not produce does not — `check_html`'s arm
        # carries the full argument and `pacing.py:196-199` is the rule.
        #
        # `store` and `shipping` are NOT stated here, and that is left alone
        # deliberately: widening these arms is not this change's business.
        # `read_at` is stated at all twenty sites only because the completeness
        # gate in `tests/test_retailers.py` requires it of every one.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact_host_paths(f"blocked: {exc}"),
            url=watch.target,
            extraction=Extraction.DOM,
            refused=True,
            read_at=None,
        )
    except FetchError as exc:
        # `read_at=None`: the fetch failed, so there is no reading to date.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact_host_paths(f"fetch failed: {exc}"),
            url=watch.target,
            extraction=Extraction.DOM,
            refused=is_refusal(exc),
            read_at=None,
        )

    return _verdict_from_html(
        watch,
        page.text,
        url=watch.target,
        first_party_only=first_party_only,
        rung=Rung.TLS,
        # No `sku=`: Amazon is addressed by `/dp/<ASIN>`, so the page that came
        # back is self-evidently the product asked for. Best Buy's SKU binding
        # is a workaround for a search redirect this retailer does not have.
        allow_dom=True,
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

    That evidence is about Best Buy's search-results *template*, though, and a
    template is a third party's SEO decision rather than a property of this
    code. Adding Product markup to result cards is one of the most common
    changes a retailer makes, and the day Best Buy does it this function starts
    handing back pages full of offers for products nobody asked about. So the
    caller does not rely on it: `check_bestbuy_browser` passes the SKU down to
    `_verdict_from_html`, which reads offers only from the Product node carrying
    that SKU. The template staying as it is became a convenience rather than the
    safety property.

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
        # `read_at=None`: the browser was refused, so no page was read. The
        # refusal happened at a moment; the reading did not happen at all — see
        # `check_html`'s arm for the argument and `pacing.py:196-199` for the
        # rule it rests on.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact_host_paths(f"blocked: {exc}"),
            url=product_url,
            rung=Rung.BROWSER,
            refused=True,
            read_at=None,
        )
    except FetchError as exc:
        # `read_at=None`: the render failed, so there is no reading to date.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact_host_paths(f"fetch failed: {exc}"),
            url=product_url,
            rung=Rung.BROWSER,
            refused=is_refusal(exc),
            read_at=None,
        )

    return _verdict_from_html(
        watch,
        page.text,
        url=product_url,
        first_party_only=first_party_only,
        rung=Rung.BROWSER,
        # Bind the answer to the question. This adapter asks Best Buy's *search*
        # for a SKU and trusts the redirect, so the page that comes back is not
        # self-evidently the product that was requested. Without this the
        # verdict is whatever `_pick` finds cheapest on whatever page arrived —
        # and a confident reading of an unrelated product is the worst outcome
        # this project can produce. Safe today only because Best Buy's
        # search-results template happens to carry no Product markup, which is
        # a third party's SEO decision and not a property of this code.
        sku=watch.target,
    )


def check_target_browser(watch: Watch, *, first_party_only: bool = True) -> Result:
    """Target via a real browser, reading the add-to-cart control — rung 3 + dom.

    The fifth retailer, and the least trustworthy reading this project publishes.
    Both facts are stated on every Result it returns rather than left for someone
    to infer from the retailer's name.

    Target is the one retailer here whose page carries **no structured data at
    all**. Not "we could not find it" — measured: zero `application/ld+json`,
    zero `schema.org`, zero `"price"`, zero `"seller"`, an empty
    `ProductDetailPrice` module, and Target's own flag saying so
    (`isProductDetailServerSideRenderPriceEnabled: false`), on two unrelated PDPs
    and two archive snapshots. The numbers are rendered client-side from
    `redsky.target.com`. So `check_html` reads this page perfectly and returns
    UNKNOWN forever, and the only thing left to read is the button.

    That makes this adapter **rung 3 AND dom**, which is a different thing from
    Best Buy's rung 3. Best Buy needs a browser because it refuses impersonated
    HTTP at the connection layer, but what gets read off the rendered page is Best
    Buy's own schema.org feed — commercially load-bearing markup that a redesign
    does not casually break. Here it is presentation markup, and a Target reskin
    breaks this silently. `Result.degraded` fires on either disjunct; `rung` and
    `extraction` are both published so a reader can tell which.

    **Rendering this page causes the browser to fetch three Target-owned hosts
    that publish `Disallow: /`** — `redsky.target.com`, `api.target.com` and
    `sapphire-api.target.com` — measured with
    `performance.getEntriesByType('resource')` inside the page, not assumed.
    Dan's recorded decision (`QUESTIONS.md` § 0d) is that a browser rendering a
    page a human would render is not a crawler. It does **not** license
    addressing those hosts directly, and no code here does: this module reaches
    `www.target.com` and nothing else.

    Every Result below carries `rung=Rung.BROWSER` and `extraction=Extraction.DOM`,
    the error paths included, for the reason `check_bestbuy_browser` gives about
    its rung: both are facts about how a reading was obtained, not about the
    verdict. An UNKNOWN from a browser that would not start is still a
    browser-and-dom reading, and the support matrix makes its claim on these two
    fields' word.

    Failure strings go through `_redact_host_paths` for the same reason they do
    there — `status.write` copies `detail` into a file served over HTTP.

    **One retry, and why it lives here rather than in the transport.** Target
    renders the add-to-cart control client-side, and `fetch_rendered` waits a
    fixed beat before reading the DOM — "crude but honest", as its own comment
    says, because the transport is deliberately ignorant of page layout and has
    no element it can wait *for*. On 2026-08-04 that beat ran out under load and
    this control read UNKNOWN. Measured on the live page, same URL, minutes
    apart: at `settle_seconds=1.0` the document is 317,597 bytes and carries no
    control, so the reader correctly returns None; at 3.0 and 6.0 it is ~352,000
    bytes and reads `add-to-cart enabled`. Roughly 35 KB of markup, containing
    the control, arrives between one second and three — and production runs at
    exactly 3.0, on the edge.

    So the retry is a layout question — "the thing I know how to read was not
    there yet" — and only this module knows what it was looking for.
    `boty/browser.py` stays ignorant, which is the property that lets one
    transport serve two retailers that read completely different things.

    It costs one extra render on the failure path and nothing on the happy one.
    It does **not** convert an UNKNOWN into a guess: a page that genuinely has
    no control still returns None twice and still reads UNKNOWN. It only removes
    the case where the honest answer was "I looked too early".
    """
    try:
        page = fetch_rendered(watch.target)
        if parse.add_to_cart_offers(page.text) is None:
            # Re-render once, patiently, before concluding the page changed.
            # `_TARGET_RETRY_SETTLE` is well past the 3s where the control was
            # measured present, because the whole point is to stop racing.
            page = fetch_rendered(watch.target, settle_seconds=_TARGET_RETRY_SETTLE)
    except Blocked as exc:
        # `read_at=None`: Target refused the render, so no page was read — and
        # neither did the patient retry above, which raises out of this same
        # `try`. `check_html`'s arm carries the argument.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact_host_paths(f"blocked: {exc}"),
            url=watch.target,
            rung=Rung.BROWSER,
            extraction=Extraction.DOM,
            refused=True,
            read_at=None,
        )
    except FetchError as exc:
        # `read_at=None`: the render failed, so there is no reading to date.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact_host_paths(f"fetch failed: {exc}"),
            url=watch.target,
            rung=Rung.BROWSER,
            extraction=Extraction.DOM,
            refused=is_refusal(exc),
            read_at=None,
        )

    return _verdict_from_html(
        watch,
        page.text,
        url=watch.target,
        first_party_only=first_party_only,
        rung=Rung.BROWSER,
        # No `sku=`: Target is addressed by URL, so the page that came back is
        # self-evidently the product asked for. Best Buy's SKU binding is a
        # workaround for a search redirect this retailer does not have.
        allow_dom=True,
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

    # WHEN BEST BUY ANSWERED — and this is the one adapter where the obvious rule
    # is measurably wrong, so the PLACEMENT of the assignment below is the whole
    # argument rather than an implementation detail.
    #
    # Initialised to `None` HERE, before the `try`, as the fail-safe: if `get()`
    # itself were ever to raise `ValueError` — it does not today, but that is a
    # property of another module, not of this line — the `except ValueError` arm
    # below reads a stamp that was never set. `None` there means "no age
    # established", which is the direction every other unknown in this codebase
    # falls. The alternative, an unassigned name, is a `NameError` on a path that
    # only fires when something else already went wrong.
    read_at: float | None = None
    try:
        page = get(api_url)
        # *** THE LINE THE PARTITION TURNS ON. *** Everything after this point
        # had a response in hand: `get()` has returned. `page.json` below can
        # still raise, and that is a fact about the BYTES, not about whether any
        # arrived. So the stamp is taken between the two, and the three arms
        # downstream of it are reads.
        read_at = time.time()
        data = page.json
    except (Blocked, FetchError) as exc:
        # `read_at=None` AS A LITERAL, not the variable: nothing came back. `get`
        # raised, so control never reached the assignment above — passing the
        # variable would be correct today by accident, and this arm should say
        # what it means rather than depend on that. This is the ONLY non-read arm
        # of the four here.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact(f"api error: {exc}"),
            url=product_url,
            rung=Rung.API,
            refused=is_refusal(exc),
            read_at=None,
        )
    except ValueError as exc:
        # STAMPED, AND THIS IS ONE OF THE TWO ARMS THE OBVIOUS RULE GETS WRONG.
        # *"An `except` arm read nothing"* is false here: `get()` already
        # returned and `page.json` raised while parsing bytes Best Buy sent. A
        # response that could not be parsed is still a response, and marking it
        # unstamped would report a reading that DID happen as having no age —
        # the dangerous direction, and it would leave Best Buy permanently
        # UNKNOWN-aged on the one retailer this project reaches through an
        # official API.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=_redact(f"bad api json: {exc}"),
            url=product_url,
            rung=Rung.API,
            read_at=read_at,
        )

    products = data.get("products") or []
    if not products:
        # STAMPED, AND THIS IS THE SECOND ARM THE OBVIOUS RULE GETS WRONG — and
        # it is not even an `except` arm. An empty `products` list is Best Buy
        # ANSWERING: it read its catalogue and told us this SKU matches nothing.
        # That is a reading with an age, and the age is when it said so.
        return Result(
            watch,
            Availability.UNKNOWN,
            detail=f"sku {watch.target} not found",
            url=product_url,
            rung=Rung.API,
            read_at=read_at,
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
        read_at=read_at,
    )
