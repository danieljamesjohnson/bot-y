"""Block detection, and why HTTP 200 is not evidence that a page is a page.

`boty.fetch.get` raises `FetchError` on a 4xx/5xx, which is the easy case. The
case that matters is the one a status code cannot see: a bot wall served with
**HTTP 200**, carrying no product markup, which sails through the status check
and arrives at `_verdict_from_html` looking exactly like a retailer that
redesigned its site.

The verdict is UNKNOWN either way, so nothing here is about a wrong stock
reading — it is about the *reason* attached to one. Those two UNKNOWNs send a
reader to opposite ends of the problem: "no structured stock data found (page
shape changed?)" means go re-capture the fixture and see which assertions
moved, while "blocked" means this retailer is turning us away and no amount of
parser work will help. A monitor whose whole pitch is that it tells you when it
breaks owes you the right reason.

The phrases pinned below came off pokemoncenter.com during 02-04's ladder walk
(`docs/retailer-evidence.md`): rung 1 returned a 6,183-byte Imperva
`Pardon Our Interruption` page at HTTP 200, and rung 3 returned a 1,085-byte
`_Incapsula_Resource` iframe. Neither is Pokémon Center-specific — Imperva sits
in front of a great many retailers, and Phase 3's two are prime candidates.

Deliberately NOT captured as fixtures: `boty.fixtures.capture` refuses to write
a challenge page to disk, and the rung-3 body embeds the probing machine's
public IP in a query string. Short literal excerpts, with the provenance written
down, are the honest way to pin this.
"""

from __future__ import annotations

from typing import Any

import curl_cffi
import pytest

from boty import browser, fetch
from boty.fetch import Blocked

#: Verbatim from the rung-1 refusal. Imperva ships this under `<noscript>` with
#: a 200, so `r.status_code >= 400` never fires.
IMPERVA_INTERSTITIAL = (
    "<!DOCTYPE html><html><head><noscript>"
    "<title>Pardon Our Interruption</title></noscript>"
    '<meta name="robots" content="noindex, nofollow">'
    "<script>window.reeseSkipExpirationCheck = true;</script>"
    "</head><body><div class=\"container\"><h1>Pardon Our Interruption</h1>"
    "<p>As you were browsing something about your browser made us think you were a bot.</p>"
    "</div></body></html>"
)

#: Verbatim shape from the rung-3 refusal, with the incident id and client IP
#: stripped. `_Incapsula_Resource` is the durable marker: it appeared in BOTH
#: refusals, where `Pardon Our Interruption` appeared in only one.
INCAPSULA_IFRAME = (
    '<html style="height:100%"><head>'
    '<meta name="ROBOTS" content="NOINDEX, NOFOLLOW">'
    "<script>sessionStorage.setItem('distil_referrer', document.referrer);</script>"
    "</head><body>"
    '<iframe id="main-iframe" src="/_Incapsula_Resource?SWUDNSAI=31&amp;mth=GET">'
    "</iframe></body></html>"
)


class _FakeResponse:
    """Just enough of a curl_cffi response for `fetch.get` to read."""

    def __init__(self, text: str, status: int = 200) -> None:
        self.text = text
        self.status_code = status
        self.headers: dict[str, str] = {}


def _answer(monkeypatch: pytest.MonkeyPatch, html: str, status: int = 200) -> None:
    """Replace the transport, not the guard's target's meaning: this test *is*
    about what `get` does with a body, so the body has to come from somewhere."""

    def _get(*args: Any, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(html, status)

    monkeypatch.setattr(curl_cffi.requests, "get", _get)


def _render(monkeypatch: pytest.MonkeyPatch, html: str) -> None:
    monkeypatch.setattr(browser, "_render", lambda *a, **k: html)


# --------------------------------------------------------------------------
# The 200-status wall
# --------------------------------------------------------------------------


def test_an_imperva_interstitial_at_http_200_is_blocked_not_a_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact failure this phase's ladder walk uncovered.

    Before `pardon our interruption` was a block phrase, this body came back
    from `get()` as a perfectly ordinary `Page`, and the retailer's refusal was
    reported to the user as "page shape changed?" — a diagnosis pointing at our
    own parser for a problem that has nothing to do with it.
    """
    _answer(monkeypatch, IMPERVA_INTERSTITIAL)

    with pytest.raises(Blocked) as caught:
        fetch.get("https://www.pokemoncenter.com/product/715e10557/pokemon-go-plus", jitter=(0, 0))

    assert "pardon our interruption" in str(caught.value).lower()
    assert "200" in str(caught.value), "the status is the point — say it out loud"


def test_an_incapsula_iframe_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """`_Incapsula_Resource` is the marker that survived both refusals.

    The user-facing wording of a bot wall is cosmetic and gets reskinned; the
    resource path the vendor's own JavaScript loads does not.
    """
    _answer(monkeypatch, INCAPSULA_IFRAME)

    with pytest.raises(Blocked):
        fetch.get("https://www.pokemoncenter.com/product/715e10557/pokemon-go-plus", jitter=(0, 0))


def test_the_browser_rung_recognises_the_same_walls(monkeypatch: pytest.MonkeyPatch) -> None:
    """`boty.browser` scans `BLOCK_PHRASES` too, so a phrase added for rung 1
    has to protect rung 3 without anybody remembering to do it twice.

    That shared list is the only part of `fetch.get`'s block detection that
    genuinely transfers to a browser — there is no status code to check and no
    TLS fingerprint to have got right.
    """
    for wall in (IMPERVA_INTERSTITIAL, INCAPSULA_IFRAME):
        _render(monkeypatch, wall)
        with pytest.raises(Blocked):
            browser.fetch_rendered("https://www.pokemoncenter.com/product/715e10557/pokemon-go-plus")


# --------------------------------------------------------------------------
# The other direction: a phrase broad enough to eat a real page
# --------------------------------------------------------------------------


@pytest.mark.parametrize("fixture_name", ["nintendo_hdmi", "nintendo_goplusplus", "gamestop_ps5"])
def test_a_real_product_page_is_not_mistaken_for_a_challenge(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, fixture_name: str
) -> None:
    """The cost of a false positive is a retailer that silently stops working.

    A block phrase is a substring match against a whole rendered page, and these
    pages are 380–420 KB of retailer marketing copy. Every phrase added to that
    list is a bet that no product page anywhere contains it, and a bad bet
    reports a working retailer as blocked forever. So the shipped fixtures are
    run back through `get()` — if a future phrase eats one of them, this goes
    red at the moment it is added rather than in production a week later.
    """
    html: str = request.getfixturevalue(fixture_name)
    _answer(monkeypatch, html)

    page = fetch.get("https://example.test/product", jitter=(0, 0))

    assert page.status == 200
    assert page.text == html


def test_every_block_phrase_is_lowercase() -> None:
    """`get` lowercases the body once and then matches raw phrases against it.

    An upper-case character anywhere in `BLOCK_PHRASES` is therefore a phrase
    that can never match — a block detector with a silent hole in it, added in
    good faith and impossible to spot by reading the list.
    """
    for phrase in fetch.BLOCK_PHRASES:
        assert phrase == phrase.lower(), f"{phrase!r} can never match a lowercased body"
