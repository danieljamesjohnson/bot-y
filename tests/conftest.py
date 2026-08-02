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

import socket

import curl_cffi
import pytest

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
    """

    def _blocked(*args: object, **kwargs: object) -> None:
        raise NetworkBlocked(_MESSAGE)

    for name in ("get", "post", "request", "head", "put", "delete", "Session"):
        monkeypatch.setattr(curl_cffi.requests, name, _blocked, raising=False)

    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)


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
