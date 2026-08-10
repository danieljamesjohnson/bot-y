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
    paced: dict[str, str] | None = None,
) -> None:
    """Publish the current reading.

    `paced` maps a retailer that was NOT checked this cycle to the reason. It
    exists because pacing introduced a third state and neither of the first two
    describes it: the retailer is not healthy (nothing was verified) and not
    unhealthy (nothing failed) — it simply was not asked.

    Without this the retailer vanishes from the file entirely, and a reader
    counting rows sees five retailers where there are six and concludes one was
    dropped. Publishing it as `checked: false` with a reason is the same
    three-valued honesty `Availability` is built on, applied to a schedule.
    """
    payload: dict[str, Any] = {
        "updated": int(time.time()),
        # Only over retailers actually CHECKED. A paced retailer has not
        # failed anything; letting it flip this false would put the dashboard
        # permanently red and make the flag useless — the same "a gate that
        # fires on the honest outcome" defect the roadmap names.
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
                # `refused` distinguishes "the retailer is turning us away"
                # from "our detector stopped working". Both are ok=False; only
                # the second one wants a human.
                "refused": h.refused,
                "checked": True,
                "reason": h.reason,
                "failing_controls": h.failing_controls,
            }
            for h in health
        ]
        + [
            {
                "retailer": retailer,
                # NOT ok: nothing was verified this cycle, and claiming
                # otherwise is the green-dashboard failure one level up.
                "ok": False,
                "refused": False,
                "checked": False,
                "reason": reason,
                "failing_controls": [],
            }
            for retailer, reason in sorted((paced or {}).items())
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
                # HTTP and the page renders it verbatim, so these three keys
                # are a contract with the dashboard and with the support
                # matrix, which reads them to say which rung each retailer
                # landed on. `rung` is written rather than only `degraded`
                # because "we reached Best Buy through its official API" and
                # "we reached it through a browser" are both non-default and
                # only one of them is a lower-confidence reading.
                #
                # `extraction` is published beside it for the same reason one
                # axis along. `degraded` alone cannot tell a reader WHY to
                # discount a reading, and the two reasons need different
                # plans: a browser transport means expect it to be slow and
                # heavy, while a dom extraction means expect a reskin to break
                # the parser without anything going red. Publishing only the
                # derived flag would collapse those into one word.
                "rung": r.rung.value,
                "extraction": r.extraction.value,
                "degraded": r.degraded,
                # WHICH STORE. Two keys, and that is the point: `store` is what
                # the page said answered, `store_pinned` is what the operator
                # configured. Published together for the reason `rung` and
                # `extraction` are published beside `degraded` — the raw facts go
                # out alongside any derived flag, because a single value cannot
                # tell a reader WHY.
                #
                # Applied here: one key alone cannot distinguish "no store
                # recorded" from "store B answered and you pinned A", and those
                # are the two states this phase exists to tell apart. On
                # 2026-08-09 this monitor recorded the Walmart milk control out
                # of stock at one price while three live reads minutes later
                # returned in stock at another. Same URL, same parser — two
                # stores answered, and nothing in the file could say so.
                #
                # `None` for a non-Walmart watch is correct and permanent: no
                # other retailer here publishes a store on a product page.
                # Serialised as `null`, NEVER as `0` and never as `""` — the
                # `duration_seconds` argument above applies word for word, and
                # here it is sharper than an analogy, because `0` is this repo's
                # own redaction placeholder and the literal value both Walmart
                # fixtures carry. An absent store published as `0` would read off
                # the dashboard as a real store.
                "store": r.store,
                "store_pinned": r.watch.store_id,
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
