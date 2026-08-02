"""Rung 3 of the escalation ladder: read the page with a real browser.

`boty.fetch` argues against this, and it is right. A headless browser fixes the
JavaScript fingerprint and leaves the TLS one untouched, so it is not
automatically *less* detectable than impersonated HTTP — it is just heavier,
slower, and drags a Chrome process onto the box. Cheap and correct beats heavy
and detectable, which is why rung 1 is tried first and this module is last.

So this is not the good path. It is the path for a retailer that refuses
impersonated HTTP *at the connection layer* — Best Buy resets the HTTP/2 stream
and times out HTTP/1.1 regardless of the fingerprint offered — where the choice
is not "cheap or heavy" but "heavy or nothing". Anything read through here is
lower-confidence by construction and callers are expected to flag it DEGRADED:
we are executing a retailer's JavaScript and believing what it renders, with no
response status to sanity-check it against.

Two things follow from that, and both are load-bearing:

- `nodriver` is imported *inside* `_render`, never at module scope. Importing
  `boty.browser` therefore costs nothing and cannot reach the network, the same
  discipline `boty.fixtures` keeps around `boty.fetch`.
- `_render` is the single seam through which every byte of rendered HTML
  arrives. The test suite's autouse network guard patches exactly that name, so
  a test cannot silently launch Chrome at a live retailer. Route new browser
  work through it rather than around it, or that guarantee quietly stops being
  true.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil

from .fetch import BLOCK_PHRASES, Blocked, FetchError, Page

log = logging.getLogger(__name__)

#: Absolute path to a Chrome/Chromium binary, when one is not on PATH.
#:
#: Read straight from the environment rather than through `Config`, on purpose:
#: which browser this host has is a property of the *host*, like a PATH lookup,
#: not a per-monitor setting somebody would tune in `config/products.yaml`. It
#: also keeps machine-specific paths out of committed source — this repo has to
#: stay honest for a fresh clone on someone else's machine.
BROWSER_PATH_ENV = "BOTY_BROWSER_PATH"

#: Tried in order when the env var is unset. Covers the usual Debian/Ubuntu,
#: Fedora and upstream-Google package names.
_CANDIDATES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "chrome",
)


def find_browser() -> str | None:
    """Path to a usable browser binary, or None if this host has none.

    None is not an error here — it is handed to `_render` as-is so that
    nodriver gets its own chance to locate a browser, and so that the failure,
    when there is one, is raised from the one place that knows what it was
    trying to do.
    """
    override = os.environ.get(BROWSER_PATH_ENV)
    if override:
        return override
    for name in _CANDIDATES:
        found = shutil.which(name)
        if found:
            return found
    return None


def _render(url: str, executable: str | None, timeout: float, settle_seconds: float) -> str:
    """Launch a browser, navigate to `url`, and return the rendered HTML.

    The only function in this codebase that touches nodriver, and the only one
    that starts a browser process — which is what makes it the seam the offline
    test guard patches by name. Keep it that way.

    The whole coroutine is bounded by `asyncio.wait_for`, and the browser is
    stopped in a `finally` on every path including cancellation. A hostile or
    merely slow page must not be able to wedge a monitor cycle or leak a Chrome
    process; a monitor that stops polling is as useless as one that lies.
    """
    # Lazy, and first: `browser` is an optional extra, so an ImportError here is
    # an ordinary "you did not install it" that `fetch_rendered` turns into an
    # actionable message rather than a traceback.
    import nodriver

    async def _run() -> str:
        browser = await nodriver.start(
            headless=True,
            browser_executable_path=executable,
            # No extensions, no persistent profile, no credentials: this browser
            # sees public product URLs and nothing else. nodriver creates and
            # removes a throwaway user-data dir per run.
            browser_args=["--disable-extensions", "--disable-background-networking"],
        )
        try:
            tab = await browser.get(url)
            # Client-side rendering: the interesting markup does not exist at
            # navigation-complete. Waiting a fixed beat is crude but honest —
            # there is no element we can wait *for* without assuming a page
            # layout this transport is deliberately ignorant of.
            await asyncio.sleep(settle_seconds)
            content = await tab.get_content()
            return str(content)
        finally:
            browser.stop()

    return asyncio.run(asyncio.wait_for(_run(), timeout))


def fetch_rendered(url: str, *, timeout: float = 45.0, settle_seconds: float = 3.0) -> Page:
    """Fetch `url` through a real browser and return it as a `Page`.

    Raises `Blocked` if a challenge page rendered, `FetchError` if the browser
    could not be started, installed, or driven to completion. It never returns a
    Page it could not actually read — the whole point of this project is that a
    reading you get back is one you can act on.

    `except Exception`, deliberately not `except BaseException`: the test
    suite's network guard raises a BaseException so that it cannot be caught and
    downgraded into a FetchError (and from there into a bland UNKNOWN verdict)
    by exactly this handler. `boty.fetch.get` makes the same choice for the same
    reason.
    """
    executable = find_browser()

    try:
        html = _render(url, executable, timeout, settle_seconds)
    except ImportError as exc:
        raise FetchError(
            f"the browser transport needs the optional extra: "
            f"pip install 'bot-y[browser]'  ({type(exc).__name__}: {exc})"
        ) from exc
    except FileNotFoundError as exc:
        raise FetchError(
            f"no Chrome/Chromium binary found — set {BROWSER_PATH_ENV} to one "
            f"({type(exc).__name__}: {exc})"
        ) from exc
    except asyncio.TimeoutError as exc:
        raise FetchError(f"browser did not finish rendering within {timeout}s") from exc
    except Exception as exc:
        raise FetchError(f"{type(exc).__name__}: {exc}") from exc

    lowered = html.lower()
    for phrase in BLOCK_PHRASES:
        if phrase in lowered:
            raise Blocked(f"rendered challenge page matched {phrase!r}")

    log.debug("rendered %s (%d bytes) via %s", url, len(html), executable or "nodriver default")

    # 200 means "the browser navigated", NOT "the server said OK". nodriver's
    # simple API does not surface the main frame's response status, so there is
    # no real status to report and inventing one would be worse than saying so.
    # Block detection here is by phrase against the rendered DOM — the one part
    # of `boty.fetch.get` that genuinely transfers to a browser.
    return Page(url=url, status=200, text=html)
