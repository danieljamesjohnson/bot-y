"""The check loop, state, and detector health.

Two behaviours here are the reason this project exists.

1. Edge-triggered alerts. You want to be told when something *becomes*
   available, not once a minute for as long as it stays available.

2. Control watches. A restock monitor's worst failure is silent: a retailer
   reskins, the detector stops matching, and it reports out-of-stock forever
   while looking perfectly healthy. You find out weeks later, having missed
   the drop. So every retailer carries at least one control — a product known
   to be in stock. If a control stops reading IN_STOCK, the *detector* is
   broken and you get told that, loudly, instead of silence.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .models import Availability, Health, Result, Watch

log = logging.getLogger(__name__)


@dataclass
class State:
    """Last-seen availability per watch, so alerts fire on transitions."""

    path: Path
    seen: dict[str, str]

    @classmethod
    def load(cls, path: Path) -> State:
        try:
            return cls(path, json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError):
            return cls(path, {})

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.seen, indent=2, sort_keys=True))

    def transitioned_to_stock(self, result: Result) -> bool:
        """True if this is a *new* in-stock reading.

        UNKNOWN never overwrites a known state — otherwise one blocked fetch
        would reset the memory and re-alert on the next successful check.
        """
        if result.availability is Availability.UNKNOWN:
            return False
        key = result.watch.key
        previous = self.seen.get(key)
        self.seen[key] = result.availability.value
        return result.availability is Availability.IN_STOCK and previous != Availability.IN_STOCK.value


def assess_health(results: list[Result]) -> list[Health]:
    """Derive per-retailer detector health from control watches.

    A retailer with no control watch is reported as unhealthy — not because
    anything is known to be broken, but because nothing is known at all, and
    an unverified detector is exactly the failure mode this guards against.
    """
    by_retailer: dict[str, list[Result]] = {}
    for r in results:
        by_retailer.setdefault(r.watch.retailer, []).append(r)

    health: list[Health] = []
    for retailer, group in sorted(by_retailer.items()):
        controls = [r for r in group if r.watch.control]
        if not controls:
            health.append(Health(retailer, ok=False, reason="no control watch configured"))
            continue
        broken = [c for c in controls if c.availability is not Availability.IN_STOCK]
        if broken:
            health.append(
                Health(
                    retailer,
                    ok=False,
                    reason=(
                        "control product is not reading IN_STOCK — the detector is "
                        "probably broken, so real restocks would be missed silently"
                    ),
                    failing_controls=[f"{c.watch.name}: {c.availability.value} ({c.detail})" for c in broken],
                )
            )
        else:
            health.append(Health(retailer, ok=True))
    return health


def run_once(
    watches: list[Watch],
    checker: Callable[[Watch], Result],
    state: State,
) -> tuple[list[Result], list[Health], list[Result]]:
    """Check every watch once. Returns (results, health, alerts)."""
    results = [checker(w) for w in watches]
    for r in results:
        log.info(
            "%-9s %-26s %-13s %s",
            r.watch.retailer,
            r.watch.name[:26],
            r.availability.value,
            r.detail[:70],
        )

    health = assess_health(results)
    alerts = [
        r
        for r in results
        if not r.watch.control and r.alertable and state.transitioned_to_stock(r)
    ]
    # Controls still need their state recorded so they do not alert as products.
    for r in results:
        if r.watch.control:
            state.transitioned_to_stock(r)
    state.save()
    return results, health, alerts
