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


#: Amazon's automated-access interstitial, verbatim, minus one per-request token.
#:
#: Retrieved 2026-08-03 from `https://www.amazon.com/dp/B0BX2P43PX` — a URL that
#: had served the full 1.9 MB product page eight minutes earlier — when two
#: `boty capture-fixture` calls were made 12 s apart instead of the 20 s the
#: politeness budget requires. **HTTP 200, 3,781 B.** It matched no block phrase
#: at the time, so `fetch.get` returned it as an ordinary `Page` and
#: `fixtures.capture` wrote a bot wall to disk under a product's name.
#:
#: Note what it posts to: `/errors_page/validateCaptcha`. It is a captcha gate,
#: not an error page, whatever the heading says. The `amzn` value is a
#: per-request token and is the one thing replaced here.
AMAZON_AUTOMATED_ACCESS_WALL = """<!DOCTYPE html>
<html class="a-no-js" lang="en-us"><head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<title dir="ltr">Amazon.com</title>
</head>
<body>

<!--
        To discuss automated access to Amazon data please contact api-services-support@amazon.com.
        For information about migrating to our APIs refer to our Marketplace APIs at https://developer.amazonservices.com/ref=rm_c_sv, or our Product Advertising API at https://affiliate-program.amazon.com/gp/advertising/api/detail/main.html/ref=rm_c_ac for advertising use cases.
-->

<!--
Correios.DoNotSend
-->

<div class="a-container a-padding-double-large" style="min-width:350px;padding:44px 0 !important">
    <div class="a-row a-spacing-double-large" style="width: 350px; margin: 0 auto">
        <div class="a-row a-spacing-medium a-text-center"><i class="a-icon a-logo" alt="Amazon logo"></i></div>
        <div class="a-box a-alert a-alert-info a-spacing-base">
            <div class="a-box-inner">
                <i class="a-icon a-icon-alert" alt="Alert icon"></i>
                <h4>Click the button below to continue shopping</h4>
                </div>
            </div>
            <div class="a-section">
                <div class="a-box a-color-offset-background">
                    <div class="a-box-inner a-padding-extra-large">
                        <form method="get" action="/errors_page/validateCaptcha" name="">
                            <input type="hidden" name="amzn" value="<REDACTED-TOKEN>" /><input type="hidden" name="amzn-r" value="&#047;" />
                            <input type="hidden" name="field-keywords" value="UNMUNG" />
                            <div class="a-section a-spacing-extra-large">
                                <div class="a-row">
                                    <span class="a-button a-button-primary a-span12">
                                        <span class="a-button-inner">
                                            <button type="submit" class="a-button-text" alt="Continue shopping">Continue shopping</button>
                                        </span>
                                    </span>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        <div class="a-text-center a-size-mini a-color-base">
          &copy; 1996-2025, Amazon.com, Inc. or its affiliates
        </div>
    </div>
</body></html>
"""


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


def test_amazons_automated_access_wall_at_http_200_is_blocked_not_a_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Imperva defect a third time, on the retailer where it actually bit.

    This one is not a near miss. `boty.fixtures.capture` is documented never to
    write a fixture from a refused fetch — "a capture that swallowed them would
    write a CAPTCHA interstitial to disk under a product's name and poison every
    test that reads it" — and on 2026-08-03 it did precisely that, because no
    phrase matched Amazon's wall and `get()` therefore handed `capture` an
    ordinary `Page`. The file was deleted rather than committed and the phrase
    was added in the same task.
    """
    _answer(monkeypatch, AMAZON_AUTOMATED_ACCESS_WALL)

    with pytest.raises(Blocked) as caught:
        fetch.get("https://www.amazon.com/dp/B0BX2P43PX", jitter=(0, 0))

    assert "200" in str(caught.value), "the status is the point — say it out loud"


def test_the_amazon_marker_appears_in_amazons_own_bytes() -> None:
    """Same reasoning as the Akamai pair: assert the phrase against the retailer.

    And one thing the Akamai pair did not have to check — that the phrase was
    the RIGHT one of the candidates. The human-readable heading on Amazon's wall
    is "Click the button below to continue shopping", and the wording a search
    would suggest, "something went wrong on our end", appears in real Amazon
    product pages. `test_a_real_product_page_is_not_mistaken_for_a_challenge` is
    parametrised over both Amazon fixtures for exactly that reason.
    """
    phrase = "to discuss automated access to amazon data"
    assert phrase in fetch.BLOCK_PHRASES, f"{phrase!r} is no longer a block phrase"
    assert phrase in AMAZON_AUTOMATED_ACCESS_WALL.lower(), (
        f"{phrase!r} does not appear in the captured Amazon wall — either the "
        "phrase is a typo, or the constant is no longer the retailer's bytes"
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


@pytest.mark.parametrize(
    "fixture_name",
    [
        "nintendo_hdmi",
        "nintendo_goplusplus",
        "gamestop_ps5",
        # Both Amazon fixtures, and they earn their place rather than padding
        # the list: the phrase added for Amazon's wall in 03.1-03 was chosen
        # over the obvious one *because* the obvious one — the visible wording
        # "something went wrong on our end" — appears once in each of these two
        # real product pages. This parametrisation is what would have caught it.
        "amazon_aa_batteries",
        "amazon_goplusplus",
    ],
)
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


def _fixture_files(root: Path) -> list[Path]:
    """Everything the identity guard must read.

    A named function rather than an inline glob so the SCOPE is pinnable —
    see `test_the_guard_scans_the_json_provenance_notes_not_only_the_pages`.
    The `.json` notes are not incidental: one of them has already leaked.
    """
    return sorted([*root.glob("*/*.html"), *root.glob("*/*.json")])


def _identity_leaks(name: str, body: str) -> list[str]:
    """The rule, extracted so it can be watched failing.

    It was a test body until 2026-08-03, which meant the only way to know it
    worked was to read it. That is precisely the gate this repo does not accept
    anywhere else — and it was not academic: this rule PASSED a Target capture
    carrying a session token, an OAuth-shaped `refreshToken`, a vendor API key,
    Akamai's geolocation of this host and five store addresses with phone
    numbers. It was widened afterwards, and one turn later it passed a Walmart
    fixture rendering `Redacted, 00000` as visible markup, because every pattern
    it had learned was keyed on a JSON key name or a query parameter.

    So: one function, two callers. The real tree must be clean, and a synthetic
    body carrying each leak class must be caught. A rule nobody has watched fail
    is not a gate.
    """
    # Values the redaction is allowed to leave behind. 192.0.2.0/24 is
    # TEST-NET-1 (RFC 5737), reserved for documentation.
    allowed = {"REDACTED", "00000", "0.0000", "0.0", "0", "REDACTED SUPERCENTER"}
    leaks: list[str] = []

    # A CDN echoing the client's own address back into the page.
    for header in ("true-client-ip", "x-forwarded-for", "client-ip"):
        for match in re.finditer(
            rf"{re.escape(header)}[^0-9]{{0,12}}(\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}})",
            body,
            re.I,
        ):
            if not match.group(1).startswith("192.0.2."):
                leaks.append(f"{name}: {header} = {match.group(1)}")

    # Akamai EdgeScape geolocation of the *requesting* host.
    for marker in ("city", "zip", "lat", "long", "county", "areacode", "fips", "dma"):
        for value in re.findall(rf"\b{marker}=([A-Za-z0-9._+-]+)", body):
            if value.upper() not in {a.upper() for a in allowed}:
                leaks.append(f"{name}: geolocation {marker}={value}")
                break

    # The same geolocation written as JSON, which is how Target's renderer
    # emits it. Anchored on the semantics (a coordinate, a postal code, a
    # street address, a phone number, a session token) rather than on one CDN's
    # spelling.
    json_markers = (
        (r'"(?:latitude|longitude)"\s*:\s*"?(-?\d+\.\d+)', "coordinate"),
        (r'"(?:zip|zipCode|postal_code|postalCode)"\s*:\s*"?(\d{4,})', "postal code"),
        (r'"(address_line1|address_line2)"\s*:\s*"([^"]+)"', "street address"),
        (r'"(?:refreshToken|accessToken|sessionId|session_id|deviceId)"\s*:\s*"([^"]{8,})"', "session token"),
        (r'"(?:visitor_id|visitorId|guest_id|guestId)"\s*:\s*"([^"]{8,})"', "visitor id"),
    )
    for pattern, what in json_markers:
        for match in re.finditer(pattern, body, re.I):
            value = match.group(match.lastindex or 0)
            if value.strip("0.-") and value.upper() not in {a.upper() for a in allowed}:
                leaks.append(f"{name}: {what} {value[:40]}")
                break

    # A US phone number or a ZIP+4 in a fixture is a geolocation of the
    # capturing host by another name: retailers render the *nearest stores*.
    # Toll-free prefixes are excluded: a 1-800 customer-service number is
    # printed on every page of a national retailer and locates nobody. A
    # geographic area code beside a store listing is the thing that does.
    for match in re.finditer(r"\b(\d{3})-\d{3}-\d{4}\b", body):
        if match.group(1) in {"800", "833", "844", "855", "866", "877", "888"}:
            continue
        leaks.append(f"{name}: phone number {match.group(0)}")
        break
    # ZIP+4 stays fail-closed even though a `12345-6789` SKU can trip it: a
    # false positive costs one redaction, a false negative costs a public
    # address. If it ever fires on real product data, narrow it deliberately
    # and say so here rather than deleting it.
    found = re.search(r"\b\d{5}-\d{4}\b", body)
    if found:
        leaks.append(f"{name}: ZIP+4 {found.group(0)}")

    # FREE TEXT, and this is the class that got through after the widening.
    #
    # Walmart does not write the shipping destination as JSON. It renders it,
    # as `aria-label="Redacted, 00000, Change shipping address"` and as a button
    # label — visible markup, no key name anywhere near it. Every rule above is
    # keyed on a key name or a query parameter, so all of them were blind to it,
    # and two fixtures carrying it had been public since Phase 1.
    #
    # `City, 12345` is the shape a US destination takes when a retailer prints
    # it for a human. It is deliberately narrow: a capitalised word or two, a
    # comma, exactly five digits.
    for match in re.finditer(r"\b([A-Z][a-z]{2,}(?: [A-Z][a-z]+){0,2}), (\d{5})\b", body):
        place, code = match.group(1), match.group(2)
        if place.upper() in {a.upper() for a in allowed} or code in allowed:
            continue
        leaks.append(f"{name}: rendered destination {place}, {code}")
        break

    return leaks


def test_the_fixture_identity_guard_catches_every_leak_class() -> None:
    """The gate, watched failing — one synthetic body per class.

    Added because the guard had no such test and twice shipped a fixture it
    should have stopped. Each case is a leak that actually occurred in this
    repo, not an invented one.
    """
    # EVERY value here is invented. The first version of this test seeded these
    # cases with the real city and ZIP that had just been redacted out of the
    # fixtures — which put them straight back into a tracked file, in the test
    # written to keep them out. `Exampleville` is not a place and `99999` is not
    # an assignable US ZIP; `203.0.113.0/24` is TEST-NET-3 and `555-01xx` is the
    # reserved fictional exchange.
    cases = {
        "true-client-ip: 203.0.113.7": "true-client-ip",
        "?city=Exampleville&zip=99999": "geolocation",
        '{"latitude":"12.345","longitude":"-98.765"}': "coordinate",
        '{"zipCode":"99999"}': "postal code",
        '{"refreshToken":"eyJhbGciOiJIUzI1NiJ9.abcdefgh"}': "session token",
        '{"visitor_id":"0193f2ab-8c1d-7e2a-b4f6-9a0c1d2e3f45"}': "visitor id",
        "Call the store on 555-555-0134": "phone number",
        'aria-label="Exampleville, 99999, Change shipping address"': "rendered destination",
    }
    for body, expected in cases.items():
        found = _identity_leaks("synthetic.html", body)
        assert found, f"the guard does not catch {expected!r}: {body!r} passed clean"
        assert any(expected in f for f in found), (
            f"{body!r} was caught but classified as {found!r}, not {expected!r}"
        )

    # And it must stay quiet on what redaction legitimately leaves behind, AND
    # on real retailer content — or it gets disabled within a week, which is the
    # failure mode that ends with no guard at all.
    #
    # The first version of this set was too easy: several entries matched no
    # rule under any circumstances, so passing them proved nothing. These are
    # the shapes that actually sit next to a leak in a captured page.
    for benign in (
        # what redaction leaves behind
        '{"zipCode":"00000"}',
        '{"visitor_id":"00000000-0000-0000-0000-000000000000"}',
        "true-client-ip: 192.0.2.1",
        "?city=REDACTED&zip=00000",
        "Redacted, 00000",
        '"city":"Redacted"',
        '"stateOrProvinceCode":"XX"',
        # real retailer content that is NOT a geolocation of this host
        "jQuery 3.3.6.4 loaded",
        '{"price":12345.00,"currency":"USD"}',
        '{"gtin13":"0819338020563"}',
        '"sku":"6577129"',
        '{"itemId":"00000000"}',              # a ZIP-shaped substring inside a longer id
        "Customer service: 1-800-925-6278",   # toll-free — a corporate number, not a store
        '"releaseDate":"2026-08-04"',
        '<path d="M12.345,67.89 L98.765,43.21"/>',
        "Nintendo of America Inc., Redmond, Washington",  # a company address in a listing
    ):
        assert not _identity_leaks("synthetic.html", benign), (
            f"the guard cries wolf on {benign!r} — a guard that fires on redacted "
            f"output or on ordinary retailer content is one nobody keeps: "
            f"{_identity_leaks('synthetic.html', benign)}"
        )


def test_the_guard_scans_the_json_provenance_notes_not_only_the_pages() -> None:
    """The `.json` half of the glob is pinned, because deleting it was silent.

    `amazon/goplusplus.json`'s note once recorded its own redaction by naming the
    values it removed — republishing, in the file documenting the removal, the
    city and ZIP just stripped from the page beside it. The guard could not see
    it because it globbed `*/*.html` and nothing else.

    That was fixed by widening the glob, and then the phase verifier deleted the
    `.json` half as a mutation and the suite stayed **379/379 green** — the notes
    were clean by then, so nothing kept the widening honest. A guard whose scope
    can be narrowed without a red test has the scope it happens to have, not the
    scope somebody chose.
    """
    root = Path(__file__).parent / "fixtures"
    scanned = _fixture_files(root)
    suffixes = {p.suffix for p in scanned}

    assert ".json" in suffixes, (
        "the identity guard is not scanning the .json provenance notes. It is "
        "the file that describes what was redacted, and it has already been the "
        "one that leaked."
    )
    assert ".html" in suffixes, "the identity guard is not scanning the pages"

    # And every note on disk is actually reached — a glob that matches one
    # directory would satisfy the suffix check above while missing the rest.
    on_disk = {p for p in root.glob("*/*.json")}
    assert on_disk <= set(scanned), (
        f"provenance notes exist that the guard does not scan: "
        f"{sorted(str(p.relative_to(root)) for p in on_disk - set(scanned))}"
    )


def test_no_fixture_leaks_the_capturing_hosts_identity() -> None:
    """A rung-3 capture froze this repo's own public IP and Akamai EdgeScape
    geolocation — city, ZIP, lat/long — into a committed fixture, and it was
    pushed to a public repo before anyone noticed.

    Rung 1 does not do this: `curl_cffi` returns the response body. A *browser*
    renders the page, and CDNs echo the client's IP and geolocation into the DOM
    for their own edge logic. So the risk arrived with the browser rung and
    applies to every future rung-3 capture.

    The rule itself lives in `_identity_leaks`, which
    `test_the_fixture_identity_guard_catches_every_leak_class` watches failing
    on one synthetic body per class. It was a test body until 2026-08-03, which
    meant nobody had ever seen it go red.

    **`.json` notes are scanned too, and that is not incidental.** Only
    `*/*.html` was checked until 2026-08-03, and in that window a fixture's own
    provenance note recorded its redaction by *naming the values it removed* —
    republishing, in the file documenting the removal, the city and ZIP just
    stripped from the page beside it. A redaction note that spells out what it
    redacted is not a note, it is a copy.
    """
    root = Path(__file__).parent / "fixtures"
    leaks: list[str] = []

    for page in _fixture_files(root):
        body = page.read_text(encoding="utf-8", errors="replace")
        leaks.extend(_identity_leaks(str(page.relative_to(root)), body))

    assert not leaks, (
        "committed fixtures carry the capturing host's identity — this repo is "
        "public:\n  " + "\n  ".join(sorted(set(leaks)))
    )
