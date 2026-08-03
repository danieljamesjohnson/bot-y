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

    @property
    def degraded(self) -> bool:
        """True when this reading came from a lower-confidence transport.

        Derived rather than stored so there is exactly one source of truth:
        the support matrix's "which rung" and the runtime DEGRADED flag cannot
        drift apart into disagreeing about the same reading.

        Note what this does NOT do: it does not touch `alertable`. A degraded
        reading is still a real reading, and suppressing alerts on it would
        defeat the point of supporting the retailer at all.
        """
        return self.rung is Rung.BROWSER

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
