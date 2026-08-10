"""Core types.

The important idea lives in `Availability`: a check has THREE outcomes, not two.

Most restock monitors treat "I could not find the add-to-cart button" as
"out of stock". That is why they fail silently — when a retailer reskins its
page, the monitor reports out-of-stock forever and never alerts again, while
looking perfectly healthy. It is the single most common bug in this category
of tool, and it is unobservable from the outside.

Here, a detector that cannot tell must say UNKNOWN. UNKNOWN is loud.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Availability(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    #: The fetch or the parse failed. Never treat this as out-of-stock.
    UNKNOWN = "unknown"


class Rung(str, Enum):
    """How a reading was obtained — which rung of the escalation ladder it took.

    `Availability` says what the retailer's page claimed. This says how much
    that claim is worth. They are separate questions, and this exists because
    "we can read this retailer" and "we can read this retailer *confidently*"
    are different claims that the support matrix has to be able to tell apart
    without a human remembering which retailer needed a browser.

    Deliberately NOT a fourth `Availability` member. `monitor.assess_health`
    and `monitor.transitioned_to_stock` branch on `Availability`, and
    `cli.SYMBOL` is a dict indexed unconditionally — a fourth member would be
    a KeyError in the middle of printing a report. Degradation is orthogonal
    to what the stock reading says.

    Deliberately NOT fed into `Health` either. `assess_health` answers "has
    this detector been verified by a control", not "how confident is the
    transport". If a degraded reading flipped `Health.ok`, a browser-read
    retailer would raise a permanent health warning and the phase criterion
    "five or more retailers with no health warnings" could never be met by
    construction — the warning channel would be full of a fact that is never
    going to change. So `boty.monitor` does not import this enum at all.

    There is no member for rung 4 ("dropped"): a dropped retailer produces no
    readings, so a `Rung` for it would be a value that can never appear on a
    `Result`.
    """

    #: Impersonated TLS against the public product page — the default path.
    TLS = "tls"
    #: The retailer's own sanctioned API. Strictly more reliable than TLS.
    API = "api"
    #: A real browser rendering the page. Works, but slowly and fragilely.
    BROWSER = "browser"


class Extraction(str, Enum):
    """What was read out of the page — the second axis, beside `Rung`.

    `Rung` says how the bytes were obtained. This says what was read out of
    them, and the two are independent. Best Buy is browser + `structured`: a
    browser renders the page, and what is then read off it is Best Buy's own
    schema.org feed — a machine-readable document they maintain because Google
    Shopping depends on it. Target would be browser + `dom`: presentation
    markup, which a reskin breaks silently, which is the exact failure mode
    this project exists to catch. Both are "browser", and lumping them together
    hides a real difference in what a reading is worth.

    Deliberately NOT a member of `Availability`. `cli.SYMBOL` is a dict indexed
    unconditionally by `r.availability`, and `monitor.assess_health` and
    `monitor.transitioned_to_stock` branch on it — a fourth member would be a
    KeyError in the middle of printing a report. What was extracted is
    orthogonal to what the reading says.

    Deliberately NOT a member of `Rung`, and nothing is renumbered. A rung is a
    fact about the TRANSPORT — how the bytes were obtained. An extraction is a
    fact about WHAT WAS READ OUT of them. They are independent: Best Buy is
    browser + structured, Target is browser + dom, and a rung-1 DOM adapter is
    perfectly possible. Folding one into the other would make the support
    matrix, the escalation ladder and rung 4's meaning all say something they
    do not mean, and would renumber a scale that four phases of documents refer
    to by number.

    Deliberately NOT fed into `Health`, for the same reason `Rung` records.
    `assess_health` answers "has this detector been verified by a control", not
    "how confident is the reading". A dom reading that flipped `Health.ok`
    would raise a permanent health warning that is never going to change, and
    the phase criterion "five or more retailers with no health warnings" could
    never be met by construction.
    """

    #: The retailer's own machine-readable feed — schema.org JSON-LD, a
    #: Next.js hydration payload, an API response. They maintain it.
    STRUCTURED = "structured"
    #: Presentation markup: a button's text, a class name. It works, and a
    #: reskin breaks it silently.
    DOM = "dom"


#: Which retailers a MISSING store pin is a gap for — the one definition, read
#: by `retailers._verdict_from_html` (the guard) and by `monitor.assess_health`
#: (the health arm that says why a reading went UNKNOWN).
#:
#: IT IS A CLAIM ABOUT THE RETAILER, NOT ABOUT THE PAGE, and that is measured
#: rather than assumed. Walmart's `__NEXT_DATA__` carries
#: `product.location.storeIds`, and `parse.nextdata_store` returns `None` for
#: every other retailer in the captured corpus — asserted across the whole
#: fixture tree in `tests/test_parse.py`, not inferred from one page.
#:
#: WHY A NAMED SET AND NOT `store is not None`. Keying on whether THIS PAGE
#: happened to name a store would let a Walmart page that stopped emitting the
#: field slip past the config gap entirely: no store on the page, nothing to
#: compare, verdict published. The whole point is that a missing pin can never
#: masquerade as a verdict, and a predicate that a retailer can switch off by
#: changing its own payload is not that.
#:
#: ONE DEFINITION, TWO READERS, AND WHY IT LIVES HERE. The guard and the health
#: arm must agree: a guard that fires where the health arm stays quiet produces
#: an UNKNOWN nobody is ever told about. A second copy is a second place to get
#: it wrong — the argument `_verdict_from_html`'s own docstring makes about the
#: UNKNOWN logic it was extracted to centralise. It cannot live in
#: `retailers.py`, because `monitor.py` would then have to import that module to
#: read it, dragging `curl_cffi` and the browser stack into a file that keeps
#: even `Pacer` behind `TYPE_CHECKING`. It belongs beside `Watch.store_id`
#: because *which retailers an absent pin is a gap for* is part of what that
#: field means.
#:
#: WHAT ADDING A RETAILER COSTS: every watch for it starts reading UNKNOWN until
#: somebody pins a store, including the control, which means the retailer goes
#: unhealthy on the status page the moment the entry lands. That is a decision
#: with a commit message behind it, not a list to grow casually.
STORE_SCOPED: frozenset[str] = frozenset({"walmart"})


@dataclass(frozen=True)
class Watch:
    """One product at one retailer."""

    name: str
    retailer: str
    #: Product URL, or a retailer-specific id (Best Buy SKU, Target TCIN).
    target: str
    #: Alert only at or below this price. Guards against reseller listings —
    #: a GO Plus + at $139 against a $54.99 MSRP is a scalper, not a restock.
    max_price: float | None = None
    #: Control watches are not products you want; they are canaries. See
    #: `boty.monitor` — a control must read IN_STOCK or the detector is broken.
    control: bool = False
    #: Which store this watch is ABOUT. Walmart assigns a store per request and
    #: prices and stock differ between them, so a Walmart reading with no store
    #: pinned is a statement about an arbitrary location. On 2026-08-09 the
    #: daemon recorded the milk control OUT_OF_STOCK at one price while three
    #: live reads minutes later returned IN_STOCK at a lower one — same URL,
    #: same parser. A parser bug does not change a price; two stores answered.
    #:
    #: Declared LAST, after `control`, with a default, for the reason `rung` and
    #: `extraction` record on `Result`: every pre-existing construction site
    #: stays valid and keeps its meaning. `control` is currently the last field,
    #: so inserting ahead of it would change the positional signature instead.
    #:
    #: THE ABSENCE OF A DEFAULT IS A DECISION, NOT AN OMISSION. `None` means
    #: "nobody pinned a store", which is a third state beside "your store" and
    #: "someone else's store" and must not collapse into either. Two
    #: alternatives were considered and rejected (Dan, 2026-08-10):
    #:
    #: - *Default to whatever Walmart assigns and flag only changes.* That
    #:   leaves a reading as a statement about an arbitrary store, which is the
    #:   bug itself rather than a fix for it.
    #: - *Geolocate from a postal code.* More moving parts, and the postal code
    #:   is precisely the value Phase 3.1's leak incident was about.
    #:
    #: The standing rule behind both: bot-y never guesses where the user lives,
    #: and a missing pin can never masquerade as a verdict. This costs every
    #: user one setup step, accepted deliberately.
    store_id: str | None = None

    @property
    def key(self) -> str:
        return f"{self.retailer}:{self.name}"


@dataclass(frozen=True)
class Result:
    watch: Watch
    availability: Availability
    price: float | None = None
    #: Human-readable evidence for the verdict — the matched button text, the
    #: API field, or the reason a parse failed. Shown in alerts and logs so a
    #: wrong verdict can be diagnosed without re-running.
    detail: str = ""
    url: str = ""
    #: Which rung produced this reading. Declared last, with a default, so
    #: every pre-existing construction site stays valid and keeps its meaning:
    #: they are all plain TLS fetches, and none of them names a rung.
    rung: Rung = Rung.TLS
    #: What was read out of the page. Declared last, after `rung`, with a
    #: default, for the same reason `rung` is: every pre-existing construction
    #: site stays valid and keeps its meaning, because every one of them reads
    #: a structured payload and none of them names an extraction.
    extraction: Extraction = Extraction.STRUCTURED
    #: True when the retailer REFUSED us — a challenge page, a 403, a 429 —
    #: rather than served us something we could not read.
    #:
    #: The distinction is the whole point and it was missing until 2026-08-04,
    #: when it cost 20 pages in 24 hours. Both cases produce
    #: `Availability.UNKNOWN`, which is correct: we do not know the stock. But
    #: they mean opposite things about the CODE. A page we cannot parse means
    #: the extractor has rotted and a human must look. A refusal means the
    #: extractor is very likely fine and we are asking too often — nobody needs
    #: waking, and the right response is to back off, which is something the
    #: monitor can do by itself.
    #:
    #: Reporting a refusal as "the detector is probably broken, so real
    #: restocks would be missed silently" is not just noisy, it is false, and
    #: it trains the reader to ignore the one alert this project exists to
    #: send.
    refused: bool = False
    #: Which store the PAGE said answered — read out of the retailer's own
    #: hydration payload, not inferred and not configured. `Watch.store_id` is
    #: what the operator asked for; this is what arrived.
    #:
    #: Declared last, after `refused`, with a default, for the same reason
    #: `rung` and `extraction` are: every pre-existing construction site stays
    #: valid and keeps its meaning, because none of them reads a store.
    #:
    #: WHAT THE DEFAULT MEANS: `None` is "the page did not tell us which store
    #: answered". It is never "store 0" — `0` is this repo's own redaction
    #: placeholder, sitting in `identity_check.py`'s allow-list beside `00000`
    #: and `XX`, and it is what `8dec2e0` wrote over the store number in both
    #: Walmart fixtures. For every non-Walmart retailer here `None` is the
    #: honest and permanent value: none of them publishes a store on a product
    #: page, so `parse.nextdata_store` finds nothing and claims nothing.
    #:
    #: Deliberately NOT folded into `degraded`. A reading from the wrong store
    #: is not a lower-confidence answer; it is an answer to a different
    #: question, and `degraded` means "discount this", which is a different
    #: instruction from "this does not apply to you".
    #:
    #: AND THE ASYMMETRY A READER WILL OTHERWISE TRY TO FIX. An unpinned or
    #: mismatched store WILL drive `Availability` to UNKNOWN, while `degraded`
    #: deliberately does not touch `alertable`. That is not an inconsistency.
    #: `rung` and `extraction` answer *how much is this reading worth* — a
    #: discounted reading is still a reading about your store, and suppressing
    #: alerts on it would defeat the point of supporting the retailer at all.
    #: A reading from a store that is not yours is not worth less; it is about
    #: something else, and the only honest availability for a question nobody
    #: asked is UNKNOWN.
    #:
    #: THE GUARD NOW EXISTS, and it is in `retailers._verdict_from_html`, not
    #: here. 05-01 shipped this field with the note "this plan adds no such
    #: guard … 05-02 is where it reaches a verdict"; 05-02 added it, ahead of
    #: every stock verdict in that function, under the `STORE_SCOPED` predicate
    #: above. This field is still only the RECORD of what arrived — it carries
    #: no verdict logic of its own, so a reader looking for the branch finds it
    #: in one place rather than two.
    store: str | None = None

    @property
    def degraded(self) -> bool:
        """True when this reading is lower-confidence — for either of two reasons.

        There are now two independent ways to be worth discounting, and they
        share one flag because the flag answers one question: *should a reader
        discount this?* A page we rendered ourselves is a yes, because it is a
        page we rendered rather than an answer the retailer gave us. A reading
        lifted out of presentation markup is also a yes, because a reskin
        breaks it silently. The two reasons are different, and they stay
        separately legible: `rung` and `extraction` are both published, so a
        reader can tell whether to expect a browser to be slow or a parser to
        rot.

        Derived rather than stored so there is exactly one source of truth:
        the support matrix's claim and the runtime DEGRADED flag cannot drift
        apart into disagreeing about the same reading.

        Note what this does NOT do: it does not touch `alertable`. A degraded
        reading is still a real reading, and suppressing alerts on it would
        defeat the point of supporting the retailer at all.
        """
        return self.rung is Rung.BROWSER or self.extraction is Extraction.DOM

    @property
    def alertable(self) -> bool:
        """In stock, and cheap enough to be a real restock rather than a flip."""
        if self.availability is not Availability.IN_STOCK:
            return False
        if self.watch.max_price is None:
            return True
        # A ceiling was configured and the price could not be read. "I could
        # not tell" must not resolve to "cheap enough" — that is the same
        # conflation as reporting out-of-stock for a page we failed to parse,
        # and it fails in the permissive direction: the alert goes out, with
        # `notify.send_restock` writing "price unknown" where the number
        # should be. Walmart's `priceInfo.currentPrice` has already been
        # reshaped once, so an unpriced IN_STOCK offer is a live possibility
        # rather than a hypothetical.
        if self.price is None:
            return False
        return self.price <= self.watch.max_price


@dataclass
class Health:
    """Per-retailer detector health, derived from control watches."""

    retailer: str
    ok: bool
    reason: str = ""
    failing_controls: list[str] = field(default_factory=list)
    #: True when the controls failed because the retailer REFUSED us, not
    #: because the detector stopped working.
    #:
    #: Both are `ok=False` — in neither case do we know the stock, and the
    #: status page should say so. What differs is whether a human is needed.
    #: A refusal is the monitor's own problem to solve, by asking less often;
    #: waking somebody for it is a false alarm, and 20 of them in 24 hours is
    #: how an alert channel stops being read.
    refused: bool = False
