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

log = logging.getLogger(__name__)


def _client(urls: list[str]):
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


def send_restock(urls: list[str], results) -> bool:
    """Alert that something is buyable. Includes the price and a direct link."""
    if not urls or not results:
        return False
    client = _client(urls)
    if client is None:
        return False

    lines = []
    for r in results:
        price = f"${r.price:.2f}" if r.price is not None else "price unknown"
        lines.append(f"{r.watch.name} — {price} at {r.watch.retailer}\n{r.url}")
    body = "\n\n".join(lines)
    title = f"IN STOCK: {results[0].watch.name}" if len(results) == 1 else f"IN STOCK: {len(results)} items"
    log.info("sending restock alert: %s", title)
    return bool(client.notify(title=title, body=body))


def send_health_warning(urls: list[str], unhealthy) -> bool:
    """Alert that a detector looks broken.

    Deliberately as loud as a restock alert. A monitor you wrongly believe is
    working is worse than one you know is down.
    """
    if not urls or not unhealthy:
        return False
    client = _client(urls)
    if client is None:
        return False

    lines = []
    for h in unhealthy:
        lines.append(f"[{h.retailer}] {h.reason}")
        lines.extend(f"  • {c}" for c in h.failing_controls)
    log.warning("sending detector health warning for: %s", ", ".join(h.retailer for h in unhealthy))
    return bool(
        client.notify(
            title=f"bot-y: detector problem ({len(unhealthy)} retailer(s))",
            body="\n".join(lines),
        )
    )
