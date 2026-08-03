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


def _fake_nodriver(
    monkeypatch: pytest.MonkeyPatch,
    seen: dict,
    explode: bool = False,
    profile: Path | None = None,
    start_explodes: bool = False,
) -> None:
    """Stand in for nodriver so `_render`'s real body can be exercised offline.

    Nothing here opens a socket or spawns a process — it records the launch
    keywords and hands back a tab-shaped object. `explode=True` makes navigation
    raise, to exercise the failure path through the `finally`.

    The `_process` and `config` shims are not decoration, and neither is the
    `util.get_registered_instances` registry. nodriver's real `Browser.stop()`
    terminates its Chrome and returns immediately; whether that child is
    *reaped* and whether its throwaway profile is *deleted* are properties of
    `_render`'s teardown, not of `stop()`, and both leaked in production for the
    life of the daemon because no test could see them. `seen["waited"]` and the
    profile directory on disk are how they get observed rather than assumed.
    """

    class _Process:
        pid = 4242
        returncode = None

        async def wait(self) -> int:
            seen["waited"] = True
            return 0

    class _Tab:
        async def get_content(self) -> str:
            return "<html>fake</html>"

    class _Browser:
        def __init__(self) -> None:
            self._process = _Process()
            # Shaped like nodriver's `Config`: a throwaway profile it made
            # itself (`uses_custom_data_dir` False) is ours to delete; one the
            # caller supplied is not.
            self.config = types.SimpleNamespace(
                user_data_dir=str(profile) if profile is not None else None,
                uses_custom_data_dir=False,
            )

        async def get(self, url: str) -> _Tab:
            seen["url"] = url
            if explode:
                raise RuntimeError("navigation blew up")
            return _Tab()

        def stop(self) -> None:
            seen["stopped"] = True

    instances: set = set()

    async def _start(**kwargs: object) -> _Browser:
        seen.update(kwargs)
        made = _Browser()
        # nodriver registers the instance the moment Chrome is spawned, before
        # the DevTools handshake that can fail — which is what makes the
        # registry the only handle on a browser whose `start()` never returned.
        instances.add(made)
        seen["instances"] = instances
        if start_explodes:
            raise RuntimeError("Failed to connect to browser")
        return made

    monkeypatch.setitem(
        sys.modules,
        "nodriver",
        types.SimpleNamespace(
            start=_start,
            util=types.SimpleNamespace(get_registered_instances=lambda: instances),
        ),
    )


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


@pytest.mark.parametrize(
    ("value", "sandbox"),
    [
        # The four ways a person writes "I do not want this". Every one of them
        # used to turn the sandbox OFF, because the check was `not
        # os.environ.get(...)` and any non-empty string is truthy.
        ("0", True),
        ("false", True),
        ("no", True),
        ("off", True),
        ("False", True),
        ("OFF", True),
        ("", True),
        ("   ", True),
        # Not a boolean at all. Ambiguity resolves toward the sandbox staying on.
        ("banana", True),
        # Explicit opt-in, the only thing that may downgrade isolation.
        ("1", False),
        ("true", False),
        ("TRUE", False),
        ("yes", False),
        ("on", False),
        (" on ", False),
    ],
)
def test_only_an_explicit_yes_disables_the_chrome_sandbox(
    monkeypatch: pytest.MonkeyPatch, value: str, sandbox: bool
) -> None:
    """`BOTY_BROWSER_NO_SANDBOX=0` must not disable the sandbox.

    The module's own argument for this variable is that "a security downgrade
    that happens silently is not one anybody reviewed" — and the truthiness
    check it shipped with was precisely a silent downgrade in the worst
    direction. Somebody editing `~/.config/boty/env` to turn the workaround
    *off*, the obvious way, by writing `=0`, turned it on instead and got a
    warning line telling them it was on that they had every reason to read as
    stale. On a transport whose entire job is executing a retailer's JavaScript,
    that is the sandbox gone for a typo.

    Parametrised over the wordings rather than over `bool()`'s behaviour,
    because the finding is about what a *person* writes, not about Python.
    """
    seen: dict = {}
    _fake_nodriver(monkeypatch, seen)
    monkeypatch.setenv(browser.NO_SANDBOX_ENV, value)

    _REAL_RENDER("https://example.com/", None, 5.0, 0.0)

    assert seen["sandbox"] is sandbox, (
        f"{browser.NO_SANDBOX_ENV}={value!r} produced sandbox={seen['sandbox']}; "
        "only an explicit yes may downgrade isolation"
    )


def test_an_unrecognised_sandbox_value_says_so(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Falling back to the safe answer silently is how the next one hides.

    Refusing to guess is right; refusing to guess *quietly* leaves somebody
    convinced they set a flag that is doing nothing. Say which value was not
    understood and which way it was resolved.
    """
    seen: dict = {}
    _fake_nodriver(monkeypatch, seen)
    monkeypatch.setenv(browser.NO_SANDBOX_ENV, "maybe")

    with caplog.at_level("WARNING", logger=browser.log.name):
        _REAL_RENDER("https://example.com/", None, 5.0, 0.0)

    assert seen["sandbox"] is True
    assert any("maybe" in r.getMessage() for r in caplog.records), (
        "an unrecognised value was ignored without a word"
    )


def test_running_as_root_warns_that_chrome_drops_its_own_sandbox(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The narrower hole in the same claim, and it is not hypothetical here.

    nodriver's `Config.__init__` auto-disables the sandbox when `is_root()`,
    logging at INFO — below boty's default WARNING level. Run boty as root (a
    container, or a systemd unit with no `User=`; this repo's own
    docker-compose.yml runs its browser as root) and retailer JavaScript
    executes unsandboxed as root, with `sandbox=True` in the launch call and
    boty's own warning line never firing. Whoever reads the log sees a sandbox
    that is not there.
    """
    seen: dict = {}
    _fake_nodriver(monkeypatch, seen)
    monkeypatch.delenv(browser.NO_SANDBOX_ENV, raising=False)
    monkeypatch.setattr(browser.os, "geteuid", lambda: 0)

    with caplog.at_level("WARNING", logger=browser.log.name):
        _REAL_RENDER("https://example.com/", None, 5.0, 0.0)

    assert any("root" in r.getMessage().lower() for r in caplog.records), (
        "running as root disables Chrome's sandbox and nothing said so"
    )


def test_the_browser_is_stopped_even_when_the_page_explodes(monkeypatch: pytest.MonkeyPatch) -> None:
    """A wedged or hostile page must not leak a Chrome process onto the box."""
    seen: dict = {}
    _fake_nodriver(monkeypatch, seen, explode=True)

    with pytest.raises(RuntimeError, match="navigation blew up"):
        _REAL_RENDER("https://example.com/", None, 5.0, 0.0)

    assert seen["stopped"] is True, "browser.stop() did not run on the failure path"


@pytest.mark.parametrize("explode", [False, True])
def test_a_render_reaps_its_chrome_and_deletes_its_profile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, explode: bool
) -> None:
    """`stop()` is not teardown. Reaping the child and deleting the profile is.

    This is the finding that shipped: `boty watch` ran for an hour and held 13
    defunct `chrome` children and 204 MB of `/tmp/uc_*` profiles, one of each
    per poll cycle, climbing forever. `browser.stop()` sends SIGTERM and returns
    — it does not `wait()`, so the loop closes before SIGCHLD is handled and the
    child stays a zombie held by this process for as long as it lives. The
    profile is nodriver's to delete and it only does so from an `atexit`
    handler, which a monitor that never exits never reaches.

    The existing `test_the_browser_is_stopped_even_when_the_page_explodes`
    asserted `stop()` was called and passed throughout, which is exactly why
    this was invisible: `stop()` *was* being called. Both halves are asserted
    here, on the success path and the failure path, because a leak that only
    happens when a page misbehaves is the one that compounds fastest.
    """
    profile = tmp_path / "uc_deadbeef"
    (profile / "Default").mkdir(parents=True)
    seen: dict = {}
    _fake_nodriver(monkeypatch, seen, explode=explode, profile=profile)

    if explode:
        with pytest.raises(RuntimeError, match="navigation blew up"):
            _REAL_RENDER("https://example.com/", None, 5.0, 0.0)
    else:
        assert _REAL_RENDER("https://example.com/", None, 5.0, 0.0) == "<html>fake</html>"

    assert seen.get("waited") is True, (
        "the Chrome child was never awaited — SIGTERM without wait() leaves a "
        "zombie held by this process for the life of the monitor"
    )
    assert not profile.exists(), (
        f"the throwaway profile {profile.name} survived the render — nodriver "
        "only removes it from an atexit handler `boty watch` never reaches"
    )


def test_a_chrome_spawned_by_a_failing_start_is_still_torn_down(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The worse half of CR-01: these are *live* Chromes, not zombies.

    nodriver's `Browser.start()` spawns Chrome and only then polls the DevTools
    endpoint five times over ~2.75 s before raising "Failed to connect to
    browser" — without terminating the process it just spawned. So the failure
    path leaks a full browser with a real RSS, where the success path leaked
    only a defunct one. On a loaded box (danserver runs several agents) missing
    that 2.75 s budget is an ordinary event, and `_render` turns it into a
    FetchError, Best Buy reads UNKNOWN correctly, and nothing reports the Chrome
    still sitting there.

    A browser whose `start()` never returned cannot be recovered from the return
    value, because there is no return value. nodriver registers the instance the
    moment the subprocess exists — before the handshake that fails — so the
    registry is the handle, and this test is what says so out loud.
    """
    profile = tmp_path / "uc_halfstarted"
    (profile / "Default").mkdir(parents=True)
    seen: dict = {}
    _fake_nodriver(monkeypatch, seen, profile=profile, start_explodes=True)

    with pytest.raises(RuntimeError, match="Failed to connect to browser"):
        _REAL_RENDER("https://example.com/", None, 5.0, 0.0)

    assert seen.get("stopped") is True, "a half-started browser was never stopped"
    assert seen.get("waited") is True, "a half-started browser's child was never reaped"
    assert not profile.exists(), "a half-started browser's profile survived"


def test_a_torn_down_browser_is_dropped_from_nodrivers_registry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The same never-exits root cause, third instance, smallest blast radius.

    nodriver keeps every Browser it ever started in a module-level set and only
    clears it from an `atexit` handler. `boty watch` therefore accumulates one
    dead Browser — with its Config and connection objects — per poll cycle, on
    top of the zombie and the profile directory, and for the same reason: this
    process never exits. Unbounded is unbounded regardless of the constant.
    """
    seen: dict = {}
    _fake_nodriver(monkeypatch, seen, profile=tmp_path / "uc_x")
    (tmp_path / "uc_x").mkdir()

    for _ in range(3):
        _REAL_RENDER("https://example.com/", None, 5.0, 0.0)

    assert seen["instances"] == set(), (
        f"{len(seen['instances'])} dead Browser instance(s) still registered after "
        "3 renders — this set is only cleared at interpreter exit, which a "
        "monitor never reaches"
    )


def test_a_caller_supplied_profile_is_not_deleted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Only the throwaway profile is ours to delete.

    `uses_custom_data_dir` is nodriver's own record of who owns the directory.
    Ignoring it would mean a future caller passing `user_data_dir=` — a logged
    -in profile, say — has it silently rmtree'd out from under them by a stock
    check. The teardown has to be aggressive about what it made and inert about
    what it was handed.
    """
    profile = tmp_path / "my-real-profile"
    (profile / "Default").mkdir(parents=True)
    seen: dict = {}
    _fake_nodriver(monkeypatch, seen, profile=profile)

    import nodriver  # the fake, installed above

    original_start = nodriver.start

    async def _start(**kwargs: object) -> object:
        made = await original_start(**kwargs)
        made.config.uses_custom_data_dir = True
        return made

    monkeypatch.setattr(nodriver, "start", _start)

    _REAL_RENDER("https://example.com/", None, 5.0, 0.0)

    assert profile.exists(), "a caller-supplied profile was deleted by the teardown"
    assert seen.get("waited") is True, "the child must still be reaped"


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
