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

    @property
    def alertable(self) -> bool:
        """In stock, and cheap enough to be a real restock rather than a flip."""
        if self.availability is not Availability.IN_STOCK:
            return False
        if self.watch.max_price is None or self.price is None:
            return True
        return self.price <= self.watch.max_price


@dataclass
class Health:
    """Per-retailer detector health, derived from control watches."""

    retailer: str
    ok: bool
    reason: str = ""
    failing_controls: list[str] = field(default_factory=list)
