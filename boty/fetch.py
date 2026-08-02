"""HTTP that survives retailer bot defenses.

Cloudflare, Akamai, DataDome and PerimeterX read the TLS ClientHello before a
single HTTP header arrives. A stock `requests` handshake produces a JA3/JA4
hash that identifies it as a script no matter what User-Agent it sends, so
header spoofing is theatre. curl_cffi replays a real Chrome TLS stack —
cipher order, extensions, HTTP/2 SETTINGS — so the connection is
indistinguishable at the network layer.

This is also why a headless browser is not automatically better: it fixes the
JavaScript fingerprint while leaving the TLS one untouched. Cheap and correct
beats heavy and detectable, so we try plain impersonated HTTP first and only
reach for a browser when a page genuinely needs JS to render stock state.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass

from curl_cffi import requests

log = logging.getLogger(__name__)

#: Pin a recent Chrome. Fingerprints rotate as browsers ship, so this needs
#: bumping periodically — an outdated impersonation target is itself a signal.
IMPERSONATE = "chrome"

#: Interstitials are served with HTTP 200, so status code alone cannot detect
#: a block. These are phrases that only appear on challenge pages.
BLOCK_PHRASES = (
    "robot or human",
    "verify you are human",
    "px-captcha",
    "access to this page has been denied",
    "request unsuccessful",
    "are you a human",
)


class Blocked(Exception):
    """A bot wall answered instead of the page."""


class FetchError(Exception):
    """The request did not complete."""


@dataclass(frozen=True)
class Page:
    url: str
    status: int
    text: str

    @property
    def json(self):
        import json

        return json.loads(self.text)


def get(
    url: str,
    *,
    timeout: int = 25,
    headers: dict[str, str] | None = None,
    jitter: tuple[float, float] = (0.4, 1.6),
) -> Page:
    """Fetch `url` with a browser TLS fingerprint.

    Raises Blocked if a challenge page came back, FetchError if the request
    failed. Neither is ever silently converted into an out-of-stock verdict.
    """
    # Human-ish spacing. Retailers rate-limit on cadence as well as volume,
    # and a monitor polling a drought does not need to be fast.
    time.sleep(random.uniform(*jitter))

    try:
        r = requests.get(url, impersonate=IMPERSONATE, timeout=timeout, headers=headers or {})
    except Exception as exc:  # curl_cffi raises a family of curl errors
        raise FetchError(f"{type(exc).__name__}: {exc}") from exc

    body = r.text
    lowered = body.lower()
    for phrase in BLOCK_PHRASES:
        if phrase in lowered:
            raise Blocked(f"challenge page matched {phrase!r} (HTTP {r.status_code})")

    if r.status_code >= 400:
        raise FetchError(f"HTTP {r.status_code}")

    log.debug("fetched %s (%d bytes)", url, len(body))
    return Page(url=url, status=r.status_code, text=body)
