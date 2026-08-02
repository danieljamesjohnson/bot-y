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


def write(path: Path, results: list[Result], health: list[Health]) -> None:
    payload: dict[str, Any] = {
        "updated": int(time.time()),
        "healthy": all(h.ok for h in health),
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
