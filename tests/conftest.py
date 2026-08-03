"""Shared test setup: the network guard, and fixture-loading fixtures.

The guard is the reason this suite can be trusted. Without it, a test could
quietly start hitting a live retailer — passing on a developer's laptop, going
red in CI for reasons unrelated to the change, and hammering someone else's
servers on every run. Worse, a test that silently depends on the network stops
being a regression test of *our* code at all.

So every test runs with `curl_cffi`'s entry points replaced by something that
raises. Any live request is a loud, immediate failure with a message that says
exactly what happened.
"""

from __future__ import annotations

import asyncio
import socket

import curl_cffi
import pytest

import boty.browser
from boty.fixtures import load

_MESSAGE = "test attempted a live network request"


class NetworkBlocked(BaseException):
    """Raised when a test reaches for the network.

    Derived from BaseException on purpose, and that choice is the whole point
    of the guard. Every request in this codebase goes through ``boty.fetch.get``,
    which wraps the call in ``except Exception`` and re-raises as ``FetchError``
    — which ``check_html`` in turn converts into ``Availability.UNKNOWN``. An
    Exception-derived guard is therefore caught and downgraded into a verdict:
    a test that forgot to monkeypatch ``retailers.get`` passes green while
    asserting ``is Availability.UNKNOWN``, which is the single most common
    assertion in this suite. The failure it was supposed to make loud becomes
    indistinguishable from the thing under test.
    """


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any outbound network access during a test fail loudly.

    Function-scoped deliberately: pytest's built-in ``monkeypatch`` fixture is
    function-scoped, and requesting it from a session-scoped fixture raises
    ScopeMismatch at collection time.

    Patching the module attributes on ``curl_cffi.requests`` works because
    ``boty.fetch`` does ``from curl_cffi import requests`` and then calls
    ``requests.get(...)`` — a runtime attribute lookup on the shared module
    object, not a bound reference captured at import time.

    ``curl_cffi`` alone is not enough, though. ``boty.notify`` reaches the
    network through apprise (``requests``/``urllib3``) and
    ``scripts/control_check.have_connectivity`` opens a raw socket, so both
    bypass it entirely. Blocking at the socket layer as well closes every
    transport in the process, present and future.

    ``boty.browser`` breaks that "present and future" claim, which is why it is
    patched here explicitly. Rung 3 does not open a socket in this process at
    all: it forks a Chrome subprocess, and Chrome does the fetching. Every patch
    above would sit there untriggered while a test quietly launched a browser at
    bestbuy.com — passing green, hammering a live retailer, and hollowing out
    Phase 1's offline guarantee without a single red test to show for it. So the
    guard patches ``boty.browser._render``, the one seam every rendered byte
    comes through, and ``BaseEventLoop.create_connection`` as belt and braces
    for the CDP websocket. ``tests/test_browser.py`` proves both fire rather
    than trusting that they would.

    Note what is deliberately NOT patched: ``subprocess.Popen``.
    ``tests/test_verify_makefile.py`` and ``tests/test_control_check.py``
    legitimately shell out, and blocking that would break the suite for a reason
    that has nothing to do with the network.
    """

    def _blocked(*args: object, **kwargs: object) -> None:
        raise NetworkBlocked(_MESSAGE)

    for name in ("get", "post", "request", "head", "put", "delete", "Session"):
        monkeypatch.setattr(curl_cffi.requests, name, _blocked, raising=False)

    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)

    monkeypatch.setattr(boty.browser, "_render", _blocked)
    monkeypatch.setattr(asyncio.base_events.BaseEventLoop, "create_connection", _blocked)


@pytest.fixture
def gamestop_goplusplus() -> str:
    """GameStop GO Plus +: OutOfStock at $54.99, sold by GameStop."""
    return load("gamestop", "goplusplus")


@pytest.fixture
def gamestop_ps5() -> str:
    """GameStop PS5 control: three offers, at least one InStock at $549.99.

    The page also carries an OutOfStock $749.99 bundle, so tests must not
    assert on ``offers[0]``.
    """
    return load("gamestop", "ps5-control")


@pytest.fixture
def walmart_goplusplus() -> str:
    """Walmart GO Plus +: IN_STOCK at $229.99 from a marketplace reseller."""
    return load("walmart", "goplusplus")


@pytest.fixture
def walmart_milk() -> str:
    """Walmart milk control: IN_STOCK at $2.42, sold by Walmart.com."""
    return load("walmart", "milk-control")


@pytest.fixture
def target_dust_cloths() -> str:
    """Target control: IN_STOCK at $12.59, sold by Target, read off the DOM.

    A rung-3 capture, and the only fixture here with no structured data in it at
    all — Target ships none, which is why this retailer is read off its
    add-to-cart control. Every `<script>` body was emptied before commit: the
    raw capture carried a session token, a visitor id and Akamai's geolocation of
    the capturing host, and a DOM reader needs none of it. See the fixture's
    `.json` note.
    """
    return load("target", "control-dust-cloths")


@pytest.fixture
def bestbuy_pikachu() -> str:
    """Best Buy control: IN_STOCK at $59.99, sold by Best Buy (SKU 6216393).

    A rung-3 capture — rendered DOM, not what curl would have seen — reached by
    Best Buy's SKU search redirect, since Best Buy's product URLs are no longer
    derivable from a SKU.
    """
    return load("bestbuy", "pikachu-control")


@pytest.fixture
def nintendo_goplusplus() -> str:
    """Nintendo GO Plus +: OutOfStock at $54.99, sold by Nintendo of America Inc.

    The only first-party listing of this product anywhere in the config, and it
    is priced at MSRP to the cent — Nintendo makes the thing, so there is no
    marketplace and no markup to defend against here, only a drought to wait out.

    Its `@type` is the compound `["Product"]`, which is what makes this page the
    first live evidence that 02-02's IN-03 fix was load-bearing.
    """
    return load("nintendo", "goplusplus")


@pytest.fixture
def nintendo_hdmi() -> str:
    """Nintendo control: InStock at $7.99, sold by Nintendo of America Inc.

    A replacement HDMI cable — first-party by construction, restocked routinely,
    not a console and not a limited drop.
    """
    return load("nintendo", "hdmi-control")


@pytest.fixture
def bestbuy_unresolved_sku() -> str:
    """Best Buy's answer for a SKU that resolves to nothing: no Product markup.

    A search page listing a dozen unrelated products, none of them carrying
    schema.org Product data. The page it is a snapshot of is the reason the
    adapter can say UNKNOWN honestly instead of reading somebody's accessory as
    a restock.
    """
    return load("bestbuy", "unresolved-sku")
