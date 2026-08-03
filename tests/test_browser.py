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
import sys
import types
from pathlib import Path

import pytest

from boty import browser, fixtures
from boty.fetch import Blocked, FetchError

URL = "https://www.example.com/site/thing/6577129.p"

#: Captured at import time, before the autouse network guard replaces the module
#: attribute. Two tests below need the real launch path, driven against a fake
#: nodriver — the guard is doing its job by hiding it from everything else.
_REAL_RENDER = browser._render


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


def _fake_nodriver(monkeypatch: pytest.MonkeyPatch, seen: dict, explode: bool = False) -> None:
    """Stand in for nodriver so `_render`'s real body can be exercised offline.

    Nothing here opens a socket or spawns a process — it records the launch
    keywords and hands back a tab-shaped object. `explode=True` makes navigation
    raise, to exercise the failure path through the `finally`.
    """

    class _Tab:
        async def get_content(self) -> str:
            return "<html>fake</html>"

    class _Browser:
        async def get(self, url: str) -> _Tab:
            seen["url"] = url
            if explode:
                raise RuntimeError("navigation blew up")
            return _Tab()

        def stop(self) -> None:
            seen["stopped"] = True

    async def _start(**kwargs: object) -> _Browser:
        seen.update(kwargs)
        return _Browser()

    monkeypatch.setitem(sys.modules, "nodriver", types.SimpleNamespace(start=_start))


def test_the_chrome_sandbox_is_on_unless_explicitly_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """A security downgrade must be something somebody chose, not a default.

    This transport *executes* a retailer's JavaScript, so Chrome's sandbox is
    the boundary between a renderer exploit and this host. The unset case is the
    assertion that matters: nobody reviews a downgrade that happens silently.

    Calls the real `_render` (captured at import, before the autouse guard swaps
    it out) against a fake nodriver, so this tests the launch call rather than
    restating the env lookup.
    """
    seen: dict = {}
    _fake_nodriver(monkeypatch, seen)
    monkeypatch.delenv(browser.NO_SANDBOX_ENV, raising=False)

    assert _REAL_RENDER("https://example.com/", None, 5.0, 0.0) == "<html>fake</html>"
    assert seen["sandbox"] is True, "the Chrome sandbox must be on by default"
    assert seen["headless"] is True
    assert seen["stopped"] is True, "the browser must be stopped on the success path too"

    seen.clear()
    _fake_nodriver(monkeypatch, seen)
    monkeypatch.setenv(browser.NO_SANDBOX_ENV, "1")
    _REAL_RENDER("https://example.com/", None, 5.0, 0.0)
    assert seen["sandbox"] is False, "the opt-out did not reach the launch"


def test_the_browser_is_stopped_even_when_the_page_explodes(monkeypatch: pytest.MonkeyPatch) -> None:
    """A wedged or hostile page must not leak a Chrome process onto the box."""
    seen: dict = {}
    _fake_nodriver(monkeypatch, seen, explode=True)

    with pytest.raises(RuntimeError, match="navigation blew up"):
        _REAL_RENDER("https://example.com/", None, 5.0, 0.0)

    assert seen["stopped"] is True, "browser.stop() did not run on the failure path"


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


# --------------------------------------------------------------------------
# The CLI flag that reaches all of the above
# --------------------------------------------------------------------------


def _record_capture(monkeypatch: pytest.MonkeyPatch, seen: dict, tmp_path: Path) -> None:
    """Stand in for `fixtures.capture` and record the keywords it was handed."""
    written = tmp_path / "captured.html"
    written.write_text("<html>ok</html>", encoding="utf-8")

    def _fake(retailer: str, name: str, url: str, note: str = "", browser: bool = False) -> Path:
        seen.update(retailer=retailer, name=name, url=url, note=note, browser=browser)
        return written

    monkeypatch.setattr(fixtures, "capture", _fake)


@pytest.mark.parametrize(
    ("argv_extra", "expected"),
    [
        ([], False),
        (["--browser"], True),
    ],
)
def test_capture_fixture_routes_the_browser_flag_through(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, argv_extra: list[str], expected: bool
) -> None:
    """`--browser` is what makes a rung-3 retailer fixturable at all.

    Not Best Buy's flag alone: the escalation ladder needs it for every retailer
    that refuses impersonated HTTP, so it is wired independently of whether any
    particular retailer turned out to be reachable. Asserting the default is
    False matters as much as asserting the flag arrives — a capture that started
    launching Chrome for GameStop would be slower, more detectable, and would
    silently change what every existing fixture is a snapshot *of*.
    """
    from boty import cli

    seen: dict = {}
    _record_capture(monkeypatch, seen, tmp_path)

    rc = cli.main(
        ["capture-fixture", "bestbuy", "probe", URL, "--note", "in stock", *argv_extra]
    )

    assert rc == 0
    assert seen["browser"] is expected
    assert seen["note"] == "in stock"
