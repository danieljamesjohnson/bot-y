"""Rung 3's transport contract, and proof that the offline guard covers it.

The first test here is the important one and it is not testing `boty.browser`
at all — it is testing `tests/conftest.py`. A browser transport does its
networking in a *subprocess*, so every socket patch the guard already had would
sit idle while a test launched Chrome at a live retailer. Asserting that the
guard actually fires, rather than assuming it does because a line was added to
it, is the difference between an offline suite and a suite that believes it is
offline.

Everything else here pins the promise `fetch_rendered` makes: it returns a Page
it genuinely read, or it raises. There is no third outcome where a challenge
page or a dead browser quietly becomes a stock verdict.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from boty import browser, fixtures
from boty.fetch import Blocked, FetchError

URL = "https://www.example.com/site/thing/6577129.p"


def _render_returns(monkeypatch: pytest.MonkeyPatch, html: str) -> None:
    """Replace the one seam that starts a browser with canned HTML."""

    def _fake(url: str, executable: str | None, timeout: float, settle_seconds: float) -> str:
        return html

    monkeypatch.setattr(browser, "_render", _fake)


def _render_raises(monkeypatch: pytest.MonkeyPatch, exc: BaseException) -> None:
    def _fake(url: str, executable: str | None, timeout: float, settle_seconds: float) -> str:
        raise exc

    monkeypatch.setattr(browser, "_render", _fake)


def test_guard_blocks_the_browser_transport() -> None:
    """The autouse guard fires, and `except Exception` does not swallow it.

    Both halves matter. If the guard were an ordinary Exception,
    `fetch_rendered` would catch it and re-raise a FetchError — which callers
    turn into Availability.UNKNOWN, the single most common assertion in this
    suite. A test that forgot to patch `_render` would then pass green while
    silently launching a browser. So this asserts the raw BaseException escapes,
    not merely that "something was raised".
    """
    with pytest.raises(BaseException, match="test attempted a live network request") as caught:
        browser.fetch_rendered(URL)

    assert not isinstance(caught.value, FetchError), (
        "the network guard was downgraded into a FetchError — "
        "fetch_rendered must catch Exception, never BaseException"
    )
    assert not isinstance(caught.value, Exception), "the guard must not be Exception-derived"


def test_rendered_html_becomes_a_page(monkeypatch: pytest.MonkeyPatch) -> None:
    _render_returns(monkeypatch, "<html><body>Add to Cart</body></html>")

    page = browser.fetch_rendered(URL)

    assert page.text == "<html><body>Add to Cart</body></html>"
    assert page.url == URL
    # 200 means "the browser navigated", not "the server said OK" — there is no
    # response status available through this transport.
    assert page.status == 200


def test_rendered_challenge_page_raises_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """A bot wall that renders is still a bot wall.

    This is the failure mode a browser makes *easier* to miss: the challenge
    arrives as a fully rendered, HTTP-200 page that a naive extractor reads as
    "no add-to-cart button" and reports as out of stock.
    """
    _render_returns(monkeypatch, "<html><body><h1>Robot or human?</h1></body></html>")

    with pytest.raises(Blocked, match="robot or human"):
        browser.fetch_rendered(URL)


def test_browser_failure_raises_fetch_error_with_a_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    """A transport failure must always say why. "It didn't work" is not a finding."""
    _render_raises(monkeypatch, RuntimeError("chrome exited with status 127"))

    with pytest.raises(FetchError) as caught:
        browser.fetch_rendered(URL)

    detail = str(caught.value)
    assert detail.strip(), "FetchError carried no detail"
    assert "chrome exited with status 127" in detail


def test_missing_extra_names_the_install_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """`browser` is an optional extra, so not having it is an expected state."""
    _render_raises(monkeypatch, ImportError("No module named 'nodriver'"))

    with pytest.raises(FetchError, match=r"bot-y\[browser\]"):
        browser.fetch_rendered(URL)


def test_missing_binary_names_the_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """A host with no Chrome gets told which knob to turn, not a traceback."""
    _render_raises(monkeypatch, FileNotFoundError("could not find a valid chrome browser binary"))

    with pytest.raises(FetchError, match=browser.BROWSER_PATH_ENV):
        browser.fetch_rendered(URL)


def test_find_browser_prefers_the_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(browser.BROWSER_PATH_ENV, "/opt/whatever/chrome")

    assert browser.find_browser() == "/opt/whatever/chrome"


def test_find_browser_returns_none_when_nothing_is_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    """None, not an exception: nodriver gets its own go at locating a browser."""
    monkeypatch.delenv(browser.BROWSER_PATH_ENV, raising=False)
    monkeypatch.setattr(browser.shutil, "which", lambda name: None)

    assert browser.find_browser() is None


def test_importing_browser_does_not_import_nodriver() -> None:
    """The heavyweight dependency stays behind the function call.

    `boty.cli` imports transitively into everything; if this module pulled in
    nodriver at import time, a contributor without the optional extra could not
    run `boty` at all.
    """
    import sys

    assert "nodriver" not in sys.modules


def test_capture_through_the_browser_writes_html_and_sidecar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _render_returns(monkeypatch, "<html>rendered</html>")
    monkeypatch.setattr(fixtures, "FIXTURE_ROOT", tmp_path)

    written = fixtures.capture("bestbuy", "probe", URL, note="rendered probe", browser=True)

    assert written.read_text(encoding="utf-8") == "<html>rendered</html>"
    meta = json.loads(fixtures.meta_path("bestbuy", "probe").read_text(encoding="utf-8"))
    assert meta["note"] == "rendered probe"
    assert meta["transport"] == "browser", "a rendered capture must record that it was rendered"


def test_capture_without_the_flag_still_uses_http(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The default path is byte-for-byte what it was before rung 3 existed.

    Asserted by proving the browser seam is never reached: if `capture()` had
    silently started routing through rung 3, the guard on `fetch.get` below
    would not be the thing that fires.
    """
    _render_raises(monkeypatch, AssertionError("capture() used the browser without being asked"))
    monkeypatch.setattr(fixtures, "FIXTURE_ROOT", tmp_path)

    from boty import fetch

    monkeypatch.setattr(fetch, "get", lambda url, **kw: fetch.Page(url=url, status=200, text="<html>http</html>"))

    written = fixtures.capture("gamestop", "probe", URL, note="http probe")

    assert written.read_text(encoding="utf-8") == "<html>http</html>"
    meta = json.loads(fixtures.meta_path("gamestop", "probe").read_text(encoding="utf-8"))
    assert meta["transport"] == "http"


def test_blocked_capture_writes_no_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The whole reason `capture` does not catch Blocked.

    A capture that swallowed it would write a CAPTCHA interstitial to disk under
    a product's name, and every test reading that fixture would then be
    asserting against a bot wall while looking perfectly green.
    """
    _render_returns(monkeypatch, "<html>Verify you are human</html>")
    monkeypatch.setattr(fixtures, "FIXTURE_ROOT", tmp_path)

    with pytest.raises(Blocked):
        fixtures.capture("bestbuy", "blocked", URL, note="should never be written", browser=True)

    assert not fixtures.html_path("bestbuy", "blocked").exists()
    assert not fixtures.meta_path("bestbuy", "blocked").exists()
    assert list(tmp_path.rglob("*")) == [], "a blocked capture left files behind"


def test_failed_capture_writes_no_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _render_raises(monkeypatch, RuntimeError("browser died"))
    monkeypatch.setattr(fixtures, "FIXTURE_ROOT", tmp_path)

    with pytest.raises(FetchError):
        fixtures.capture("bestbuy", "failed", URL, note="should never be written", browser=True)

    assert list(tmp_path.rglob("*")) == [], "a failed capture left files behind"
