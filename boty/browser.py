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
import contextlib
import logging
import os
import shutil
from typing import Any

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

#: Set to `1`, `true`, `yes` or `on` to launch Chrome with `--no-sandbox`.
#:
#: Those four and nothing else — see `_sandbox_wanted`. `0`, `false`, `no` and
#: `off` mean what they say, and an unrecognised value is treated as no *and
#: warned about*. Merely being set is not enough, deliberately: this is the one
#: setting in the project where guessing wrong removes a security boundary.
#:
#: Off by default and it should stay that way: this transport *executes*
#: attacker-controlled JavaScript from a retailer, and Chrome's sandbox is the
#: thing standing between a renderer exploit and the host. Turning it off is a
#: real reduction in isolation, so it is opt-in, per-host, and never the
#: default — a security downgrade that happens silently is not one anybody
#: reviewed.
#:
#: The reason it exists at all: Ubuntu 24.04 ships
#: `kernel.apparmor_restrict_unprivileged_userns=1`, which denies unprivileged
#: user namespaces to binaries without an AppArmor profile. An unpackaged
#: Chrome (a Chrome-for-Testing download, say) then cannot build its namespace
#: sandbox and aborts on startup. The better fixes are a distro Chrome package,
#: an AppArmor profile for the binary, or a setuid `chrome_sandbox` helper; this
#: is the escape hatch for when none of those is available.
NO_SANDBOX_ENV = "BOTY_BROWSER_NO_SANDBOX"

#: Substrings that mark a failure as "this HOST cannot run rung 3", as opposed
#: to "the retailer refused us" or "our extractor broke".
#:
#: They live here, next to the messages they match, and are imported by
#: `scripts/control_check.py` rather than retyped there. The distinction is
#: load-bearing for the gate: a missing optional dependency reported as a
#: detector failure sends a contributor to re-capture a fixture for a page that
#: is fine. Duplicating the strings would let the two drift apart, and the
#: symptom of that drift is the wrong diagnosis coming back — silently, because
#: a classifier that stops matching just returns False.
MISSING_EXTRA = "the browser transport needs the optional extra"
MISSING_BINARY = "no Chrome/Chromium binary found"
HOST_GAPS = (MISSING_EXTRA, MISSING_BINARY)

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


#: The only values that mean "yes, disable the sandbox".
#:
#: An allow-list rather than a truthiness test, and the distinction is the whole
#: point. `not os.environ.get(...)` treats *any* non-empty string as yes —
#: including `0`, `false`, `no` and `off`, which are the four ways somebody
#: writes "I do not want this". Editing `~/.config/boty/env` to turn the
#: workaround off the obvious way used to turn it on.
_TRUTHY = frozenset({"1", "true", "yes", "on"})

#: Recognised as "no". Listed separately from "unrecognised" so that a value
#: nobody anticipated gets a warning while an ordinary `0` does not.
_FALSY = frozenset({"0", "false", "no", "off", ""})


def _sandbox_wanted() -> bool:
    """Whether to launch Chrome with its sandbox, and say so out loud if not.

    Chrome's sandbox is the boundary between a renderer exploit and this host,
    and this transport exists to execute a retailer's JavaScript. So the default
    is on, the opt-out is explicit, and anything ambiguous resolves toward on.
    """
    raw = os.environ.get(NO_SANDBOX_ENV, "").strip().lower()

    if raw and raw not in _TRUTHY and raw not in _FALSY:
        log.warning(
            "%s=%r is not a recognised yes/no value — treating it as NO and "
            "leaving Chrome's sandbox ON. Use 1/true/yes/on to disable it.",
            NO_SANDBOX_ENV,
            raw,
        )

    sandbox = raw not in _TRUTHY
    if not sandbox:
        log.warning(
            "%s is set — Chrome's sandbox is OFF and retailer JavaScript runs "
            "with this process's privileges",
            NO_SANDBOX_ENV,
        )

    # Independent of the variable, and the reason it is checked here rather than
    # trusted to the launch keyword: nodriver's `Config.__init__` silently
    # disables the sandbox when `is_root()` and logs it at INFO, below boty's
    # default WARNING level. As root — a container, or a unit with no `User=`,
    # and this repo's own docker-compose.yml runs its browser that way — we pass
    # `sandbox=True`, nodriver ignores it, and nothing above says a word. Whoever
    # reads the log would see a sandbox that is not there.
    if os.geteuid() == 0:
        log.warning(
            "running as root — Chrome disables its own sandbox in that case "
            "regardless of %s, so retailer JavaScript is executing unsandboxed "
            "as root. Run boty as an unprivileged user.",
            NO_SANDBOX_ENV,
        )

    return sandbox


#: How long the teardown waits for a terminated Chrome to actually die.
#:
#: Bounded because this runs on the way out of a render that may already have
#: timed out, and a monitor that hangs in its cleanup has failed in the same way
#: as one that hangs in its fetch. If the wait expires we have leaked a process —
#: but we have leaked exactly one, and the next cycle still runs.
_REAP_TIMEOUT = 10.0


async def _teardown(browser: Any, registry: set[Any] | None = None) -> None:
    """Stop a browser, reap its child, and delete its throwaway profile.

    `browser.stop()` is not teardown, and believing it was cost this project a
    production leak. nodriver's `stop()` sends SIGTERM and returns immediately:
    it never `wait()`s. `asyncio.run` then closes the loop before SIGCHLD is
    handled, so the Chrome process becomes a **zombie held by this process for
    as long as it lives** — and for `boty watch`, that is forever. Measured on
    the deployed unit: 13 defunct children after 71 minutes, one per poll cycle,
    with no ceiling short of `TasksMax`.

    The profile directory is the same defect wearing different clothes.
    nodriver's `Config` creates `/tmp/uc_*` per launch and only ever removes it
    from an `atexit` handler (`util.deconstruct_browser`), which a daemon that
    never exits never reaches. Same measurement: 204 MB, ~170 MB/hour, and the
    unit's `PrivateTmp` fills in days.

    Every step is defensive because this is cleanup: it runs on failure paths,
    including ones where the browser never finished starting, so a teardown that
    raises would replace a real diagnosis with an error about tidying up.
    """
    with contextlib.suppress(Exception):
        browser.stop()

    proc = getattr(browser, "_process", None)
    if proc is not None:
        # The actual reap. Also the reason the "Event loop is closed" tracebacks
        # went away: awaiting here lets the subprocess transports finalise while
        # the loop is still alive, instead of at interpreter shutdown when it is
        # not. That noise was logged as cosmetic; it was this leak surfacing.
        with contextlib.suppress(Exception):
            await asyncio.wait_for(proc.wait(), _REAP_TIMEOUT)

    cfg = getattr(browser, "config", None)
    data_dir = getattr(cfg, "user_data_dir", None)
    # `uses_custom_data_dir` is nodriver's record of who owns the directory.
    # Only the throwaway is ours to delete — rmtree'ing a caller-supplied
    # profile would be a far worse bug than the one this fixes.
    if data_dir and not getattr(cfg, "uses_custom_data_dir", False):
        shutil.rmtree(data_dir, ignore_errors=True)

    # Third instance of the same root cause: nodriver holds every Browser it
    # ever started in a module-level set and only clears it from `atexit`. A
    # daemon that never exits therefore accumulates one dead Browser — with its
    # Config and connection objects — per poll cycle, forever. Smaller than a
    # zombie and a 17 MB profile, and unbounded in exactly the same way.
    if registry is not None:
        registry.discard(browser)


def _render(url: str, executable: str | None, timeout: float, settle_seconds: float) -> str:
    """Launch a browser, navigate to `url`, and return the rendered HTML.

    The only function in this codebase that touches nodriver, and the only one
    that starts a browser process — which is what makes it the seam the offline
    test guard patches by name. Keep it that way.

    The launch-and-drive work is bounded by `asyncio.wait_for`, and every
    browser it started is torn down in a `finally` — stopped, reaped, and its
    profile removed. A hostile or merely slow page must not be able to wedge a
    monitor cycle or leak a Chrome process; a monitor that stops polling is as
    useless as one that lies, and one that fills its own disk stops polling.

    "Every browser it started" is doing real work in that sentence, and it is
    the part this docstring used to get wrong. It once said the browser was
    stopped on every path, while `nodriver.start()` sat outside the `try` — so a
    start that spawned Chrome and then failed its DevTools handshake, which is
    what a loaded box produces, leaked a *live* browser and nothing said so.
    Hence `_registered()`: the browser that never got returned is still findable.

    The timeout deliberately wraps the *inner* coroutine rather than the whole
    thing. Teardown has to `await` — reaping a child is an await — and an
    `await` inside a `finally` that is itself running under cancellation is not
    reliable. Bounding the work and then cleaning up outside that bound means
    the cleanup runs in an uncancelled context on every path, which is the only
    way it can be depended on. `_REAP_TIMEOUT` keeps the cleanup itself bounded.
    """
    # Lazy, and first: `browser` is an optional extra, so an ImportError here is
    # an ordinary "you did not install it" that `fetch_rendered` turns into an
    # actionable message rather than a traceback.
    import nodriver

    sandbox = _sandbox_wanted()

    def _registered() -> set[Any]:
        """nodriver's own registry of live Browser instances, defensively.

        The only handle on a browser whose `start()` never returned. nodriver
        adds the instance the moment Chrome is spawned — before the DevTools
        handshake that can raise — so a failed start is still findable here.
        Wrapped because this is an internal of an optional dependency: if a
        future nodriver moves it, the teardown of the *normal* path must not
        start throwing on the way past.

        Returns the live set, not a copy — `_teardown` discards from it.
        """
        try:
            got = nodriver.util.get_registered_instances()
            return got if isinstance(got, set) else set(got)
        except Exception:  # pragma: no cover - depends on nodriver internals
            log.debug("nodriver has no instance registry — cannot recover a failed start")
            return set()

    async def _run() -> str:
        # Every browser this call started, so the teardown has a handle on it
        # even when `_drive` did not get far enough to return one.
        started: list[Any] = []
        # `registry` is nodriver's live set; `preexisting` is a snapshot of it
        # from before this render, so the difference is exactly what we started.
        registry = _registered()
        preexisting = set(registry)

        async def _drive() -> str:
            browser = await nodriver.start(
                headless=True,
                browser_executable_path=executable,
                sandbox=sandbox,
                # No extensions, no persistent profile, no credentials: this
                # browser sees public product URLs and nothing else. nodriver
                # creates a throwaway user-data dir per run; deleting it again
                # is `_teardown`'s job, not nodriver's — see its docstring.
                browser_args=["--disable-extensions", "--disable-background-networking"],
            )
            started.append(browser)
            tab = await browser.get(url)
            # Client-side rendering: the interesting markup does not exist at
            # navigation-complete. Waiting a fixed beat is crude but honest —
            # there is no element we can wait *for* without assuming a page
            # layout this transport is deliberately ignorant of.
            await asyncio.sleep(settle_seconds)
            content = await tab.get_content()
            return str(content)

        try:
            return await asyncio.wait_for(_drive(), timeout)
        finally:
            # `started` is empty when `nodriver.start()` itself raised or was
            # cancelled — and that is the path that leaks a *live* Chrome with a
            # real RSS rather than a defunct one, because nodriver spawns the
            # process before the handshake it can fail on and does not terminate
            # it when it does. Fall back to whatever appeared in the registry on
            # our watch.
            for browser in started or (registry - preexisting):
                await _teardown(browser, registry)

    return asyncio.run(_run())


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
            f"{MISSING_EXTRA}: "
            f"pip install 'bot-y[browser]'  ({type(exc).__name__}: {exc})"
        ) from exc
    except FileNotFoundError as exc:
        raise FetchError(
            f"{MISSING_BINARY} — set {BROWSER_PATH_ENV} to one "
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
