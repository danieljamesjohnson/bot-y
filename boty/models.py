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
