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

import re
from pathlib import Path
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


#: **Verbatim bytes** from kohls.com, re-fetched 2026-08-03, with only the
#: per-session challenge nonce redacted. Akamai Bot Manager serves this
#: behavioural challenge at HTTP 200 with no human-readable "are you a robot"
#: wording at all — the only markers are structural. It matters well beyond
#: Kohl's: Akamai fronts a large share of US retail including Target, which
#: Phase 3 walks the ladder at.
#:
#: This used to be a hand-written *reconstruction*, and that made the test below
#: worthless in the one way that mattered. Asserting our phrase against our own
#: transcription of the challenge passes identically whether the marker is
#: right or a typo — and a typo'd marker never fires in production, so the wall
#: comes back as an ordinary page and the refusal is reported as "page shape
#: changed?", sending someone to debug an extractor that is working perfectly.
#: A green test would have said nothing either way.
#:
#: Now that these are the retailer's bytes rather than ours, a wrong phrase in
#: `BLOCK_PHRASES` fails the test. Full provenance — URL, status, byte count and
#: both matched substrings in context — is in `docs/retailer-evidence.md`.
#:
#: Note `class ="scf-akamai-protected-by"`: the space before `=` is Akamai's,
#: reproduced exactly, and is why the phrase is the bare class name.
AKAMAI_CHALLENGE = """<!DOCTYPE html>
<html lang="en">
<body><script type="text/javascript" src="/Borx/KBSP/bWL9/cO/vKew/LQiNt8aN5ku5/Zy90Gm97dAw/XS/t3e30oTwx8?v=<REDACTED-NONCE>&amp;t=155122144"></script>
<div id="sec-if-cpt-container" role="main" style="display: none">
    <div class="behavioral-content">
        <div id="sec-bc-text-container"></div>
        <div id="sec-bc-tile-parent">
            <div id="sec-bc-tile-container"></div>
        </div>
        <div class="sec-bc-button-parent">
            <div class="behavioral-button progress-btn-disabled">
                <div class="btn" id="progress-button" role="button" disabled></div>
                <div class="progress"></div>
            </div>
        </div>
        </div>
        <div class="scf-akamai-logo-sec-abc">
            <div class="scf-akamai-logo-msg">
                <p class ="scf-akamai-protected-by">Powered and protected by</p>
            </div>
            <div class="scf-akamai-logo-img">
                <img src="https://www.akamai.com/site/ko/images/logo/akamai-logo1.svg" class="scf-akamai-logo" loading="lazy" alt="Akamai">
            </div>
            <div class="akamai-privacy" ><a href="https://www.akamai.com/privacy" target="_blank">Privacy</a></div>
        </div>
    </div>
</div>
<script type="text/javascript" src="https://www.kohls.com/public/40b35110c9d4347948c85e668a2ed087f723b7604ced"  ></script>
</body></html>"""


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


def test_an_akamai_challenge_at_http_200_is_blocked_not_a_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Imperva defect again, different vendor, found before it cost us.

    Akamai's challenge carries no "are you a robot" wording — a phrase list
    built only from human-readable copy would miss it entirely and report the
    refusal as "page shape changed?", sending someone to debug an extractor
    that is working perfectly. Added while probing a fifth retailer, ahead of
    Phase 3 walking the ladder at Target, which Akamai also fronts.
    """
    _answer(monkeypatch, AKAMAI_CHALLENGE)

    with pytest.raises(Blocked) as caught:
        fetch.get("https://www.kohls.com/product/prd-1234/some-product.jsp", jitter=(0, 0))

    assert "200" in str(caught.value), "the status is the point — say it out loud"


@pytest.mark.parametrize("phrase", ["sec-if-cpt-container", "scf-akamai-protected-by"])
def test_each_akamai_marker_appears_in_the_retailers_own_bytes(phrase: str) -> None:
    """Points the assertion at the retailer's markup instead of at our copy of it.

    The defect this replaces was not that the marker was wrong — it was
    re-probed and both are verbatim — but that nothing could have told us if it
    were. `AKAMAI_CHALLENGE` was a hand-written reconstruction, so the block
    test asserted our phrase against our own transcription and would have gone
    green over a typo. The phrase would then never fire in production, and an
    Akamai refusal at Target would surface as "page shape changed?".

    Stated as its own test rather than left implicit in the `Blocked` assertion
    because the two say different things: that one says "this body is refused",
    this one says "the string we refuse it *by* is a string the retailer
    actually emits". Provenance in `docs/retailer-evidence.md`.
    """
    assert phrase in fetch.BLOCK_PHRASES, f"{phrase!r} is no longer a block phrase"
    assert phrase in AKAMAI_CHALLENGE.lower(), (
        f"{phrase!r} does not appear in the captured Kohl's challenge — either "
        "the phrase is a typo, or the constant is no longer the retailer's bytes"
    )


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


# --------------------------------------------------------------------------
# Fixtures must not carry the capturing host's identity
# --------------------------------------------------------------------------


def test_no_fixture_leaks_the_capturing_hosts_identity() -> None:
    """A rung-3 capture froze this repo's own public IP and Akamai EdgeScape
    geolocation — city, ZIP, lat/long — into a committed fixture, and it was
    pushed to a public repo before anyone noticed.

    Rung 1 does not do this: `curl_cffi` returns the response body. A *browser*
    renders the page, and CDNs echo the client's IP and geolocation into the DOM
    for their own edge logic. So the risk arrived with the browser rung and
    applies to every future rung-3 capture.

    Scoped to the markers that carry *client* identity rather than any
    IP-shaped string: retailer pages are full of version numbers like `3.3.6.4`
    and Akamai's own server addresses, and a test that cries wolf on those gets
    disabled within a week.
    """
    root = Path(__file__).parent / "fixtures"
    # Values the redaction is allowed to leave behind. 192.0.2.0/24 is
    # TEST-NET-1 (RFC 5737), reserved for documentation.
    allowed = {"REDACTED", "00000", "0.0000", "0.0", "0"}  # a zero DMA/FIPS is the
    # "unknown" sentinel these fields carry when the edge could not place the
    # client — it identifies nothing, and excluding it keeps the check honest
    # rather than making the assertion pass by widening what counts as a leak.
    leaks: list[str] = []

    for page in sorted(root.glob("*/*.html")):
        body = page.read_text(encoding="utf-8", errors="replace")

        # A CDN echoing the client's own address back into the page.
        for header in ("true-client-ip", "x-forwarded-for", "client-ip"):
            for match in re.finditer(
                rf"{re.escape(header)}[^0-9]{{0,12}}(\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}})",
                body,
                re.I,
            ):
                if not match.group(1).startswith("192.0.2."):
                    leaks.append(f"{page.relative_to(root)}: {header} = {match.group(1)}")

        # Akamai EdgeScape geolocation of the *requesting* host.
        for marker in ("city", "zip", "lat", "long", "county", "areacode", "fips", "dma"):
            for value in re.findall(rf"\b{marker}=([A-Za-z0-9._+-]+)", body):
                if value.upper() not in {a.upper() for a in allowed}:
                    leaks.append(f"{page.relative_to(root)}: geolocation {marker}={value}")
                    break

    assert not leaks, (
        "committed fixtures carry the capturing host's identity — this repo is "
        "public:\n  " + "\n  ".join(sorted(set(leaks)))
    )
