"""Notifications, via Apprise.

Apprise speaks Telegram, ntfy, Discord, Slack, email and ~100 others through
one URL syntax, so bot-y does not implement any of them:

    tgram://<bot-token>/<chat-id>
    ntfy://<topic>
    discord://<webhook-id>/<webhook-token>

Tokens come from the environment or the config file, never from source.
"""

from __future__ import annotations

import logging
from typing import Any

from .models import Health, Result

log = logging.getLogger(__name__)


def _client(urls: list[str]) -> Any | None:
    """An Apprise instance, or None if apprise is missing.

    Typed `Any` because apprise ships no stubs — see the ignore_missing_imports
    override in pyproject.toml.
    """
    try:
        import apprise
    except ImportError:  # pragma: no cover
        log.error("apprise not installed — run: pip install apprise")
        return None
    client = apprise.Apprise()
    for url in urls:
        if not client.add(url):
            log.error("apprise rejected notification url: %s", url.split("://")[0] + "://…")
    return client


def send_restock(urls: list[str], results: list[Result]) -> bool:
    """Alert that something is buyable. Includes the price and a direct link."""
    if not urls or not results:
        return False
    client = _client(urls)
    if client is None:
        return False

    lines: list[str] = []
    for r in results:
        price = f"${r.price:.2f}" if r.price is not None else "price unknown"
        lines.append(f"{r.watch.name} — {price} at {r.watch.retailer}\n{r.url}")
    body = "\n\n".join(lines)
    title = f"IN STOCK: {results[0].watch.name}" if len(results) == 1 else f"IN STOCK: {len(results)} items"
    log.info("sending restock alert: %s", title)
    return bool(client.notify(title=title, body=body))


def send_health_warning(urls: list[str], unhealthy: list[Health]) -> bool:
    """Alert that one or more retailers are no longer verified.

    Deliberately as loud as a restock alert. A monitor you wrongly believe is
    working is worse than one you know is down.

    THIS FUNCTION COMPOSES NO DIAGNOSIS OF ITS OWN, and must not start. The body
    is `h.reason` plus `h.failing_controls`, verbatim — `monitor.assess_health`
    is the one place that decides what a failure may be said to mean, and a
    second opinion written here would be unreachable by the gate that checks it.
    Until 2026-08-10 the exception was the hardcoded title, `"bot-y: detector
    problem (N retailer(s))"`, which asserted a problem with the detector over a
    body that might be saying the detector was never reached — the same defect as
    the two withdrawn sentences in `monitor.py`, on the one surface a phone
    actually shows. Withdrawn under REQ-15. What `ok=False` establishes is stated
    by `assess_health`'s own docstring — "not because anything is known to be
    broken, but because nothing is known at all" — so the measured word is
    UNVERIFIED. The count stays, because the count is measured.
    """
    if not urls or not unhealthy:
        return False
    client = _client(urls)
    if client is None:
        return False

    lines: list[str] = []
    for h in unhealthy:
        lines.append(f"[{h.retailer}] {h.reason}")
        lines.extend(f"  • {c}" for c in h.failing_controls)
    log.warning("sending health warning for: %s", ", ".join(h.retailer for h in unhealthy))
    return bool(
        client.notify(
            title=f"bot-y: {len(unhealthy)} retailer(s) unverified",
            body="\n".join(lines),
        )
    )
