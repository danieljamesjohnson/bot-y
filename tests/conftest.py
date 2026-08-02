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

import curl_cffi
import pytest

from boty.fixtures import load

_MESSAGE = "test attempted a live network request"


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any outbound HTTP during a test fail loudly.

    Function-scoped deliberately: pytest's built-in ``monkeypatch`` fixture is
    function-scoped, and requesting it from a session-scoped fixture raises
    ScopeMismatch at collection time.

    Patching the module attributes on ``curl_cffi.requests`` is sufficient
    because ``boty.fetch`` does ``from curl_cffi import requests`` and then
    calls ``requests.get(...)`` — a runtime attribute lookup on the shared
    module object, not a bound reference captured at import time.
    """

    def _blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError(_MESSAGE)

    monkeypatch.setattr(curl_cffi.requests, "get", _blocked)
    monkeypatch.setattr(curl_cffi.requests, "post", _blocked, raising=False)
    monkeypatch.setattr(curl_cffi.requests, "request", _blocked, raising=False)
    monkeypatch.setattr(curl_cffi.requests, "Session", _blocked)


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
