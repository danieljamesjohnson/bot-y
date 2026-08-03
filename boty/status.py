"""Status snapshot for the dashboard.

Written after every cycle so the page shows what the monitor actually last
saw, including detector health. The page is deliberately dumb — it renders
this file and nothing else — so the monitor stays the single source of truth.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from .models import Health, Result

log = logging.getLogger(__name__)


def write(
    path: Path,
    results: list[Result],
    health: list[Health],
    *,
    duration_seconds: float | None = None,
) -> None:
    payload: dict[str, Any] = {
        "updated": int(time.time()),
        "healthy": all(h.ok for h in health),
        # How long the pass that produced this file took, in seconds. Published
        # so REQ-08's two-minute budget can be READ rather than re-measured by
        # hand — the only figure this project had before it existed was a
        # stopwatch number in a plan summary, which is a budget asserted rather
        # than measured.
        #
        # `None` means "nobody timed this pass", which is not "it took no
        # time": the same three-valued honesty `Availability` is built on,
        # applied to a number. A missing measurement serialised as 0 would read
        # off the dashboard as the fastest check ever recorded.
        #
        # Callers must time with `time.monotonic()`, never `time.time()`. This
        # file is served over HTTP, and a wall clock stepping backwards during
        # an NTP correction would publish a negative duration.
        "duration_seconds": duration_seconds,
        "retailers": [
            {
                "retailer": h.retailer,
                "ok": h.ok,
                "reason": h.reason,
                "failing_controls": h.failing_controls,
            }
            for h in health
        ],
        "watches": [
            {
                "name": r.watch.name,
                "retailer": r.watch.retailer,
                "availability": r.availability.value,
                "price": r.price,
                "detail": r.detail,
                "url": r.url,
                "control": r.watch.control,
                "alertable": r.alertable,
                # Public API, not an internal detail: this file is served over
                # HTTP and the page renders it verbatim, so these two keys are
                # a contract with the dashboard and with the support matrix,
                # which reads them to say which rung each retailer landed on.
                # `rung` is written rather than only `degraded` because "we
                # reached Best Buy through its official API" and "we reached
                # it through a browser" are both non-default and only one of
                # them is a lower-confidence reading.
                "rung": r.rung.value,
                "degraded": r.degraded,
            }
            for r in results
        ],
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(path)  # atomic, so the page never reads a half-written file
    except OSError:
        log.exception("could not write status to %s", path)
