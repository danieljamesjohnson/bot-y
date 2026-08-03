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

import hashlib
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
    fixture rendering this host's city and ZIP as visible markup — the values are
    not repeated here, for the same reason they were taken out of the page —
    because every pattern
    it had learned was keyed on a JSON key name or a query parameter.

    So: one function, two callers. The real tree must be clean, and a synthetic
    body carrying each leak class must be caught. A rule nobody has watched fail
    is not a gate.
    """
    # Values the redaction is allowed to leave behind. 192.0.2.0/24 is
    # TEST-NET-1 (RFC 5737), reserved for documentation.
    # The redaction vocabulary. Every entry is a placeholder this repo writes on
    # purpose, and each is obviously not a real value: `XX` is not a US state,
    # `00000` is not an assignable ZIP, `192.0.2.0/24` is RFC 5737 TEST-NET-1.
    # Nothing real is ever added here — allow-listing a real value is how a gate
    # gets quietly satisfied, and a mutation that does exactly that is pinned in
    # `test_the_allow_list_cannot_absorb_a_real_value`.
    allowed = {"REDACTED", "00000", "0.0000", "0.0", "0", "XX",
               "REDACTED SUPERCENTER", "REDACTED STORE", "REDACTED-CITY",
               "NOT-AVAILABLE", "NULL"}
    leaks: list[str] = []

    # A CDN echoing the client's own address back into the page.
    for header in ("true-client-ip", "x-forwarded-for", "client-ip"):
        for match in re.finditer(
            # The gap allows `"true-client-ip":"1.2.3.4"` — the JSON-quoted
            # form is the one that actually leaked in `02-REVIEW.md`, and both
            # synthetic cases used the bare `header: ip` form, so narrowing the
            # gap was silent. First octet is 1-3 digits: a 3-digit octet is the
            # commonest shape of a real address.
            rf"{re.escape(header)}[^0-9]{{0,12}}(\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}})",
            body,
            re.I,
        ):
            if not match.group(1).startswith("192.0.2."):
                leaks.append(f"{name}: {header} = {match.group(1)}")

    # Akamai EdgeScape geolocation of the *requesting* host.
    # `region_code` and `georegion` were missing until 2026-08-03 and were LIVE
    # in `bestbuy/unresolved-sku.html` — the repo asserted "a state is a leak
    # class" in the JSON rule below while shipping the state in the query form
    # three times. `network_type` names the ISP. Each marker gets its own case
    # in the leak-class test; they used to shadow each other two-at-a-time
    # behind a single `?city=…&zip=…` probe.
    for marker in ("city", "zip", "lat", "long", "county", "areacode", "fips",
                   "dma", "region_code", "georegion", "network_type",
                   "pmsa", "msa", "asnum", "timezone", "continent"):
        for value in re.findall(rf"\b{marker}=([A-Za-z0-9._+-]+)", body):
            if value.upper() not in {a.upper() for a in allowed}:
                leaks.append(f"{name}: geolocation {marker}={value}")
                break

    # `?state=ZZ` — a query-form state, uppercase. NOT folded into the marker
    # loop above: `state` is not an EdgeScape key, and adding it there fired on
    # GameStop's own TrustArc CCPA config (`&state=ca`, lowercase, about
    # California law rather than about us). The case distinction is the rule.
    for value in re.findall(r"[?&;,]state=([A-Z]{2})\b", body):
        if value.upper() not in {a.upper() for a in allowed}:
            leaks.append(f"{name}: geolocation state={value}")
            break

    # The same geolocation written as JSON, which is how Target's renderer
    # emits it. Anchored on the semantics (a coordinate, a postal code, a
    # street address, a phone number, a session token) rather than on one CDN's
    # spelling.
    json_markers = (
        (r'"(?:latitude|longitude)"\s*:\s*"?(-?\d+\.\d+)', "coordinate"),
        (r'"(?:zip|zipCode|postal_code|postalCode|shippingZipcode|shipping_zip)"\s*:\s*"?(\d{4,})', "postal code"),
        (r'"(?:refreshToken|accessToken|sessionId|session_id|deviceId)"\s*:\s*"([^"]{8,})"', "session token"),
        (r'"(?:visitor_id|visitorId|guest_id|guestId)"\s*:\s*"([^"]{8,})"', "visitor id"),
    )
    # `re.I` is load-bearing: `{"ZipCode":"…"}` is a real spelling, and
    # dropping the flag was a silent mutation. The loop falls through on an
    # allowed value rather than breaking, for the same ordering reason as the
    # two loops above — the Walmart fixtures put the placeholder first.
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

    # THE CLASSES REDACTED BY HAND, NOW ENFORCED — and this block is the point.
    #
    # Three rounds of this went: find a leak, redact the spellings in front of
    # me, ship. The verifier caught a survivor every time, and the third round
    # named why: the fixes added no RULE. `e871377` removed
    # `"pickupStore":"202"`, `"stateCode":"TX"`, `storeId=202` and a WIC agency
    # list by hand and then pinned only the guard's *scope* — so the same
    # capture taken tomorrow would ship every one of them again. Enforcement
    # that lives in somebody's attention only ever covers the list they were
    # handed.
    #
    # A store number IS a locator: it resolves publicly to one address. A state
    # is 1-in-50. Neither is a coordinate, and that is exactly why neither was
    # caught by rules written against coordinates.
    keyed = (
        (r'"(?:pickup|delivery|preferred|nearest|selected|home|fulfillment)?[Ss]tore(?:_?[Ii]d|Number|No|Code)?"\s*:\s*"?(\d+)', "store number"),
        # `data-` attributes. GameStop shipped `data-preferred-store-id="4242"`
        # through all five rounds of this — DIFFERENT values in the two
        # captures, so it is this host's preferred store, not GameStop's. No
        # store rule had ever looked at an HTML attribute.
        (r'data-[a-z-]*store[a-z-]*(?:-id|-number)?="(\d+)"', "store number in a data- attribute"),
        (r'data-[a-z-]*(?:city|zip|postal|state|region|store-name)[a-z-]*="([A-Za-z0-9][^"]{1,40})"', "geolocation in a data- attribute"),
        # The store NAME class had no rule at all — `REDACTED SUPERCENTER` sat
        # in the allow-list for a rule that did not exist, while 26 real store
        # names shipped in a Best Buy fixture.
        (r'"(?:storeName|store_name|locationName|locationDisplayName)"\s*:\s*"([^"]{2,40})"', "store name"),
        # COOKIES. `set-cookie: vt=<uuid>` — a Best Buy visitor token — shipped
        # live in `bestbuy/unresolved-sku.html` through six rounds. The
        # visitor-id class already HAD a rule; it was keyed to JSON, and a
        # cookie is neither a JSON key nor a query param nor an attribute.
        # Hence a carrier column, not another key spelling.
        (r'(?:set-cookie|x-middleware-set-cookie)[^a-zA-Z0-9]{0,8}(?:vt|visitor|guest|sid|sessionid)=([A-Za-z0-9._~-]{8,})', "visitor id in a cookie"),
        (r'(?:set-cookie|x-middleware-set-cookie)[^a-zA-Z0-9]{0,8}(?:zip|postal|city|store)=([A-Za-z0-9._~-]{2,})', "geolocation in a cookie"),
        (r'\bstore(?:_?[Ii]d|Number)\s*(?:=|%3D)\s*(\d+)', "store number in a URL"),
        (r'"(?:state|region|province)(?:Code|OrProvinceCode|_code)?"\s*:\s*"([A-Z]{2})"', "state or region"),
        (r'"(?:city|cityName|locality|town)"\s*:\s*"([A-Za-z][A-Za-z .\'-]{2,})"', "city"),
        (r'"(?:destinationZipCode|postCode|post_code|zip5|zipcode)"\s*:\s*"?(\d{4,})', "postal code"),
        (r'"(?:lat|lng|lon)"\s*:\s*"?(-?\d+\.\d+)', "coordinate"),
        (r'"(?:dma|dmaCode|fips|fipsCode|cbsa|metro|county|countyName)"\s*:\s*"?([A-Za-z0-9][A-Za-z0-9 ]*)', "metro or county code"),
        (r'"(?:address_?[Ll]ine(?:One|Two|[12])?|streetAddress|street1)"\s*:\s*"([^"]+)"', "street address"),
        (r'(?:WICAgencies|wicAgencies)"\s*:\s*\[\s*"([A-Z]{2})"', "state via WIC agency"),
    )
    for pattern, what in keyed:
        for match in re.finditer(pattern, body):
            value = match.group(1)
            # Only `break` on a REPORTED leak. Falling through on an allowed
            # value is deliberate: the redacted placeholder appears before the
            # real value in both Walmart fixtures, so stopping at the first
            # match would disable the rule for the pages it exists for.
            if value.strip("0.- ") and value.upper() not in {a.upper() for a in allowed}:
                leaks.append(f"{name}: {what} {value[:40]}")
                break

    # `City, ST 12345` — the postal form, which the `City, 12345` rule below
    # misses because of the state in the middle.
    found = re.search(r"\b([A-Z][a-z]{2,}(?: [A-Z][a-z]+){0,2}), ([A-Z]{2}) (\d{5})\b", body)
    if found and found.group(1).upper() not in {a.upper() for a in allowed}:
        leaks.append(f"{name}: rendered address {found.group(0)}")

    # A phone number written any of the ways a retailer writes one. The
    # hyphenated form is handled below; these are the rest.
    for pattern in (r"\((\d{3})\)\s?\d{3}[-.\s]?\d{4}", r"\b(\d{3})\.\d{3}\.\d{4}\b", r"tel:\+?1?(\d{3})\d{7}"):
        m = re.search(pattern, body)
        if m and m.group(1) not in {"800", "833", "844", "855", "866", "877", "888"}:
            leaks.append(f"{name}: phone number {m.group(0)}")
            break

    # FREE TEXT, and this is the class that got through after the widening.
    #
    # Walmart does not write the shipping destination as JSON. It renders it,
    # as `aria-label="<city>, <zip>, Change shipping address"` and as a button
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
            # `continue`, NOT `break`. A redacted `Redacted, 00000` appears
            # BEFORE the real value in both Walmart fixtures, so breaking here
            # would disable this rule for exactly the pages it was written for.
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
    # written to keep them out. `Exampleville` is not a place and `99001` is not
    # an assignable US ZIP; `203.0.113.0/24` is TEST-NET-3 and `555-01xx` is the
    # reserved fictional exchange.
    cases = {
        "true-client-ip: 203.0.113.7": "true-client-ip",
        "?city=Exampleville&zip=99001": "geolocation",
        '{"latitude":"12.345","longitude":"-98.765"}': "coordinate",
        '{"zipCode":"99001"}': "postal code",
        '{"refreshToken":"eyJhbGciOiJIUzI1NiJ9.abcdefgh"}': "session token",
        '{"visitor_id":"0193f2ab-8c1d-7e2a-b4f6-9a0c1d2e3f45"}': "visitor id",
        "Call the store on 555-555-0134": "phone number",
        'aria-label="Exampleville, 99001, Change shipping address"': "rendered destination",
        # One case per rule added after the third verification round. Without
        # these the rules were unwatched: deleting the store-number rule left
        # the suite green, which is how every previous round of this failed.
        '{"pickupStore":"202"}': "store number",
        '{"deliveryStore":"202"}': "store number",
        '{"storeId":"1234"}': "store number",
        "?storeId=202&pt=item": "store number in a URL",
        "?storeId%3D202": "store number in a URL",
        '{"stateOrProvinceCode":"ZZ"}': "state or region",
        '{"regionCode":"ZZ"}': "state or region",
        '{"city":"Exampleville"}': "city",
        '{"destinationZipCode":"99001"}': "postal code",
        '{"postCode":"99001"}': "postal code",
        '{"lat":"12.345","lng":"-98.765"}': "coordinate",
        '{"dma":"901"}': "metro or county code",
        '{"countyName":"Exampleshire"}': "metro or county code",
        '{"addressLineOne":"1 Example Way"}': "street address",
        '{"address_line2":"Suite 4"}': "street address",
        # Every EdgeScape marker gets its own case. They used to shadow each
        # other: one `?city=…&zip=…` probe covered two of eight, so deleting
        # any of the other six was silent — in the block that handles the exact
        # artefact `02-REVIEW.md` leaked.
        "?georegion=999&country_code=US": "geolocation georegion",
        "?region_code=ZZ": "geolocation region_code",
        "?network_type=examplenet": "geolocation network_type",
        "?lat=12.345": "geolocation lat",
        "?long=-98.765": "geolocation long",
        "?county=EXAMPLESHIRE": "geolocation county",
        "?areacode=555": "geolocation areacode",
        "?fips=99001": "geolocation fips",
        "?dma=901": "geolocation dma",
        "?pmsa=9999": "geolocation pmsa",
        "?msa=9998": "geolocation msa",
        "?asnum=99001": "geolocation asnum",
        "?timezone=XST": "geolocation timezone",
        "?continent=NA": "geolocation continent",
        "&state=ZZ": "geolocation state",
        # The two header spellings that had no case. `x-forwarded-for` is the
        # one that actually carried the IP three times in the real incident.
        'x-forwarded-for: 198.51.100.7, 203.0.113.8': "x-forwarded-for",
        'client-ip: 198.51.100.7': "client-ip",
        # ZIP+4 — the whole rule was unwatched, and it is the one carrying a
        # comment asking maintainers not to delete it.
        "Ships to 99001-1234": "ZIP+4",
        # A ZIP+4 that does not begin with 9, and a mixed-case JSON key. Both
        # were silent mutations: narrowing ZIP+4 to a leading 9, and dropping
        # `re.I` from the json_markers loop, each passed every other case.
        "Ships to 99002-1234": "ZIP+4",
        '{"ZipCode":"99002"}': "postal code",
        '{"VisitorID":"0193f2ab-8c1d-7e2a-b4f6-9a0c1d2e3f45"}': "visitor id",
        '{"shippingZipcode":"99001"}': "postal code",
        '{"store_id":"202"}': "store number",
        '{"deliveryWICAgencies":["ZZ"]}': "state via WIC agency",
        "Exampleville, ZZ 99001": "rendered address",
        # ORDERING. Both Walmart fixtures contain the redacted placeholder
        # BEFORE the real value, so a rule that stops at the first allowed
        # match is disabled for exactly the pages it was written for. Turning
        # the free-text rule's `continue` into a `break` was silent until this
        # case existed.
        'Redacted, 00000 ... later ... Exampleville, 99001': "rendered destination",
        '{"city":"Redacted"} ... {"city":"Exampleville"}': "city",
        "Call (555) 555-0134": "phone number",
        "Call 555.555.0134": "phone number",
        '<a href="tel:+15555550134">': "phone number",
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


def test_each_rule_fires_on_a_value_of_the_REAL_shape_not_just_the_synthetic_one() -> None:
    """The hole left by inventing the synthetic values, closed.

    Round 3 correctly stopped this file seeding its cases with the host's real
    city and ZIP. The side effect, which round 4 found: **no test tied any rule
    to the shape of the value it exists to catch.** Six regex-weakening
    mutations passed — requiring an 8-character city name, or a leading `9` on
    a ZIP — because every synthetic happened to satisfy the narrowed pattern
    while the real value did not.

    The fix is not to put real values back. It is to assert each rule against
    values that are *shaped* like the real one and differ from the synthetic:
    a short city, a ZIP that does not start with 9, a two-letter state, a
    three-digit store number. If a maintainer narrows a pattern to fit the
    synthetic, one of these goes red.
    """
    real_shaped = [
        # short city name — the synthetic `Exampleville` is 12 chars
        ('{"city":"Exampleton"}', "city"),
        ('aria-label="Exampleton, 99001, Change shipping address"', "rendered destination"),
        ("Exampleton, ZZ 99001", "rendered address"),
        # ZIPs that do not begin with 9, unlike the synthetic 99001
        ('{"zipCode":"99002"}', "postal code"),
        ('{"destinationZipCode":"99003"}', "postal code"),
        ("?zip=99004", "geolocation zip"),
        # a three-digit store number, and a two-digit one
        ('{"pickupStore":"202"}', "store number"),
        ('{"storeId":"07"}', "store number"),
        ("?storeId=1", "store number in a URL"),
        # states other than the synthetic
        ('{"stateCode":"ZZ"}', "state or region"),
        ("?region_code=CA", "geolocation region_code"),
        # coordinates with different precision
        ('{"latitude":"12.3"}', "coordinate"),
        ('{"lat":"-98.765012"}', "coordinate"),
        # a real-shaped area code and a 10-digit phone
        ("Store: 555-555-0100", "phone number"),
    ]
    for body, expected in real_shaped:
        found = _identity_leaks("synthetic.html", body)
        assert found, (
            f"the guard misses {body!r} — a value of the REAL shape. It passes "
            f"the synthetic case for {expected!r} and fails this one, which "
            f"means the pattern has been narrowed to fit the test rather than "
            f"the leak."
        )


#: The coverage grid: every identity CLASS this repo has ever leaked, against
#: every CARRIER a retailer has ever written one in. A cell is a probe whose
#: value is invented but whose *shape* is real; `None` means "no retailer has
#: been observed writing this class in this carrier, and no rule is claimed".
#:
#: WHY THIS EXISTS, AND IT IS THE ONLY REASON. Five verification rounds each
#: found a leak keyed to a spelling nobody had been shown yet: a free-text
#: `City, ZIP` after the JSON rules; a query-form `region_code=` after the JSON
#: `regionCode`; a `data-preferred-store-id` attribute after both. Every round
#: fixed the instances it was handed, and the class was always wider than the
#: instances. A grid does not stop that — nothing does — but it makes the
#: *unfilled cells visible as a failing test* instead of as a future discovery.
#: Adding a carrier column adds a row of red tests, which is the point.
IDENTITY_GRID: dict[str, dict[str, str | None]] = {
    # class      json key                                query param                     data- attribute                           free text                                        cookie
    "city":      {"json": '{"city":"Exampleton"}',       "query": "?city=Exampleton",    "data": 'data-city="Exampleton"',         "text": "Exampleton, 99001",                     "cookie": 'set-cookie":"city=Exampleton'},
    "state":     {"json": '{"stateCode":"ZZ"}',          "query": "?state=ZZ",           "data": 'data-region="ZZ"',               "text": "Exampleton, ZZ 99001",                  "cookie": None},
    # `zip/text` was declared None until round 6 — and a ZIP in free text is
    # this thread's FOUNDING leak. A wrong None is worse than a missing rule:
    # a missing rule is a gap, a wrong None is a claim that there is no gap.
    "zip":       {"json": '{"zipCode":"99002"}',         "query": "?zip=99002",          "data": 'data-postal-code="99002"',       "text": "Ships to Exampleton, 99002",            "cookie": 'set-cookie":"zip=99002'},
    "coord":     {"json": '{"latitude":"12.3"}',         "query": "?lat=12.3",           "data": None,                             "text": None,                                    "cookie": None},
    "store_no":  {"json": '{"storeId":"7"}',             "query": "?storeId=7",          "data": 'data-preferred-store-id="4242"', "text": None,                                    "cookie": 'set-cookie":"store=4242'},
    # `store_nm/text` was also a wrong None: Walmart renders the store name as
    # visible prose, which is how it reached six rounds without a rule.
    "store_nm":  {"json": '{"storeName":"Exampleton"}',  "query": None,                  "data": 'data-store-name="Exampleton"',   "text": "Pickup, today at Exampleton, ZZ 99001", "cookie": None},
    "street":    {"json": '{"addressLineOne":"1 Way"}',  "query": None,                  "data": None,                             "text": None,                                    "cookie": None},
    "phone":     {"json": None,                          "query": None,                  "data": None,                             "text": "Store: 555-555-0100",                   "cookie": None},
    "ip":        {"json": '{"true-client-ip":"203.0.113.7"}', "query": None,             "data": None,                             "text": "true-client-ip: 203.0.113.7",           "cookie": None},
    "isp":       {"json": None,                          "query": "?network_type=fiber", "data": None,                             "text": None,                                    "cookie": None},
    # Four classes that had rules but no grid row — so nothing asserted their
    # carrier coverage at all, and the cookie carrier for `visitor` was the
    # one shipping live.
    "session":   {"json": '{"refreshToken":"eyJhbGciOiJIUzI1NiJ9.abcdefgh"}', "query": None, "data": None,                         "text": None,                                    "cookie": None},
    "visitor":   {"json": '{"visitor_id":"0193f2ab-8c1d-7e2a-b4f6-9a0c1d2e3f45"}', "query": None, "data": None,                     "text": None,                                    "cookie": 'set-cookie":"vt=0193f2ab-8c1d-7e2a-b4f6-9a0c1d2e3f45'},
    "metro":     {"json": '{"countyName":"Exampleshire"}', "query": "?dma=901",          "data": None,                             "text": None,                                    "cookie": None},
    "wic_state": {"json": '{"deliveryWICAgencies":["ZZ"]}', "query": None,               "data": None,                             "text": None,                                    "cookie": None},
}


#: SHA-256 prefixes of values this repo has had to scrub out of a capture.
#:
#: **Hashed, not listed, and that is the entire design.** A deny-list of real
#: values written in plaintext is a copy of the leak wearing a safety label —
#: which is exactly what `amazon/goplusplus.json`'s redaction note and
#: `02-REVIEW.md`'s findings section each turned out to be. Hashes let the
#: check compare without the file ever holding the value.
#:
#: Harvested mechanically from the pre-redaction blobs in git
#: (`58e38ef`, `481d81d`, `22557af`) rather than retyped, so nobody had to
#: handle the values to build it.
#:
#: WHY IT EXISTS: the fixture corpus below cannot catch a value that has
#: ALREADY been scrubbed from the fixtures — and reusing one of those is
#: precisely what happened three times, most seriously when the coverage grid
#: was seeded with this host's public IP one commit after that IP was scrubbed
#: out of `02-REVIEW.md`.
_SCRUBBED_VALUE_HASHES = frozenset({
    "050a5a129d528beb",
    "075feae6c628be46",
    "0d3a86a22038cca7",
    "157ae3a816b8fa12",
    "236cf465237bb69a",
    "37fcff24bf62035b",
    "3c50106d5a57d43d",
    "4c6567ac41596467",
    "4ea837ac2e51fbac",
    "6136613447dcc6af",
    "6aa006809ea4f9c9",
    "6eb5f5d046d1d918",
    "9a4c65633fd6ae66",
    "a397e8ce3fc9fe12",
    "a521ff61b09f2055",
    "a53deaefbc39492b",
    "a6a7535e3c4d1344",
    "a9d25706623d487c",
    "b217537a0c765b26",
    "b4f20421d4c3c2e1",
    "b699ec5173deecf4",
    "ba1fe5f460fe0497",
    "bde3e8fc954e7690",
    "cb8199de78e1747e",
    "d8a638e00a71663b",
    "dc1c42d6da089f1b",
    "e01e994b82afdcd8",
    "eae6d77e26d53f8b",
    "eb113c09cc387eed",
    "f090dac4d3288093",
    "fa495e5d27180f1d",
    "fc8f7f487e852114",
})


def _is_known_real(value: str) -> bool:
    return hashlib.sha256(value.lower().encode()).hexdigest()[:16] in _SCRUBBED_VALUE_HASHES


def test_no_probe_value_in_this_file_appears_in_a_REAL_CAPTURE() -> None:
    """"Invented" is a claim, and this is the check that it is true.

    Three separate rounds of fixing this guard wrote a REAL value into this
    file while asserting the opposite twelve lines above. The worst was this
    host's public IP — the single most sensitive value in the whole thread —
    put back into a tracked file by the commit that added the coverage grid,
    under a docstring reading "EVERY value here is invented". It had been
    scrubbed out of `02-REVIEW.md` one commit earlier.

    Reading the file and asking "does that look invented?" has now failed three
    times, because a plausible-looking IP or store number is exactly what a
    real one looks like. So this asserts it mechanically instead: **every
    literal used as a probe must appear in NO captured fixture.** If a value
    is genuinely invented it cannot be in bytes a retailer sent us. If it is
    in those bytes, it was copied, whatever the comment says.

    Scoped to values long enough to be identifying — a two-letter state or a
    one-digit store number will collide with real bytes by chance.
    """
    root = Path(__file__).parent / "fixtures"
    corpus = "\n".join(
        f.read_text(encoding="utf-8", errors="replace") for f in _fixture_files(root)
    )

    # Take the VALUE the rule actually captured, not every token in the probe —
    # the KEY names (`zipCode`, `latitude`, `data-preferred-store-id`) are real
    # by construction, and must be, or the rule would not match a real page.
    probes: set[str] = set()
    for row in IDENTITY_GRID.values():
        for cell in row.values():
            if not cell:
                continue
            for leak in _identity_leaks("probe", cell):
                value = leak.rsplit(" ", 1)[-1].strip(",.\"'")
                # 4, not 5: the real GameStop store number is four digits, and
                # a five-char floor let it back in. The corpus check below is
                # still gated at 5 (a four-digit number collides with real
                # bytes by chance); the hash check is exact, so it is not.
                if len(value) >= 4:
                    probes.add(value)

    # Whole-token match: a five-digit probe collides with the middle of a real
    # price or product id by chance, and a guard that cries wolf gets deleted.
    copied = sorted(
        v for v in probes
        if (len(v) >= 5 and re.search(rf"(?<![\w.-]){re.escape(v)}(?![\w.-])", corpus))
        or _is_known_real(v)
    )
    assert not copied, (
        "these values are used as 'invented' probes but appear verbatim in a "
        "captured fixture, which means they were copied out of real retailer "
        "bytes:\n  " + "\n  ".join(copied) + "\n"
        "Invent a value that is not in any capture. A probe's SHAPE has to be "
        "real; its VALUE must not be."
    )


def test_the_grid_cannot_be_shrunk_without_a_red_test() -> None:
    """Coverage can only go up, and the floor is asserted here.

    Round 6 found the grid gutted silently: downgrading a filled cell to `None`
    was green, and deleting a whole row was green. A coverage assertion that is
    satisfied by declaring less coverage asserts nothing — the allow-list
    failure in a new place.

    Raise these numbers when you add coverage. Lowering one has to be argued
    for in a diff, not done by replacing a probe with `None` to go green.
    """
    classes = {"city", "state", "zip", "coord", "store_no", "store_nm", "street",
               "phone", "ip", "isp", "session", "visitor", "metro", "wic_state"}
    assert classes <= set(IDENTITY_GRID), (
        f"identity classes dropped out of the grid: "
        f"{sorted(classes - set(IDENTITY_GRID))}. Each has been leaked at least once."
    )
    filled = sum(1 for r in IDENTITY_GRID.values() for v in r.values() if v)
    assert filled >= 30, (
        f"grid has {filled} filled cells, floor is 30. Downgrading a cell to "
        f"`None` claims no retailer writes that class in that carrier — make "
        f"that claim in the diff, not by deleting a probe."
    )


def test_every_declared_grid_cell_is_actually_caught() -> None:
    """Each filled cell of `IDENTITY_GRID` must produce a leak. No exceptions.

    This is the assertion that turns "we fixed the spellings we were shown"
    into "the class is covered in every carrier we have declared". A cell that
    a maintainer fills in optimistically fails here until a rule exists.
    """
    misses = []
    for cls, carriers in IDENTITY_GRID.items():
        for carrier, probe in carriers.items():
            if probe is None:
                continue
            if not _identity_leaks("grid.html", probe):
                misses.append(f"{cls} / {carrier}: {probe!r}")
    assert not misses, (
        "the identity guard declares these class/carrier cells covered and "
        "catches none of them:\n  " + "\n  ".join(misses)
    )


def test_the_grid_declares_every_carrier_for_every_class_it_has_leaked() -> None:
    """An unfilled cell must be a deliberate `None`, never an omission.

    Every class here has been leaked by this repo at least once. The `None`s
    are claims — "no retailer has been observed writing this class in this
    carrier" — and a claim that turns out to be wrong shows up as a new leak,
    at which point the cell gets filled and a rule gets written. What must
    never happen is a cell simply missing, because then nobody is claiming
    anything and the gap is invisible again.
    """
    carriers = {"json", "query", "data", "text", "cookie"}
    for cls, row in IDENTITY_GRID.items():
        assert set(row) == carriers, (
            f"grid row {cls!r} does not declare every carrier — missing "
            f"{sorted(carriers - set(row))}. Write `None` with a reason rather "
            f"than leaving the cell out; an absent cell is an invisible gap, "
            f"which is what five rounds of this were."
        )


def test_the_allow_list_cannot_absorb_a_real_value() -> None:
    """`allowed` is a redaction vocabulary, not an exemption list.

    The verifier's third pass found that adding this host's real city and ZIP to
    `allowed` left the suite 380/380 green — the cheapest possible way to make
    this gate stop working, one line, no rule deleted, nothing red. This pins
    the shape of the set instead of trusting nobody will do that.

    Every legitimate entry is a value that cannot be real: a zero, a
    placeholder word, `XX` (not a US state), a documentation range. A real
    city, a real ZIP, a real state or a real store number is by construction
    not any of those.
    """
    import inspect

    src = inspect.getsource(_identity_leaks)
    start = src.index("allowed = {")
    literal = src[start : src.index("}", start) + 1]

    for entry in re.findall(r'"([^"]*)"', literal):
        bare = entry.replace("-", "").replace(" ", "").replace(".", "")
        assert (
            not bare
            or bare.isdigit() and set(bare) <= {"0"}          # 00000, 0, 0.0
            or entry.upper() == "XX"                           # not a state
            or "REDACTED" in entry.upper()                     # a placeholder word
            or entry.upper() in {"NOT-AVAILABLE", "NULL"}      # CDN / JS sentinels
        ), (
            f"{entry!r} is in the identity guard's allow-list but is not a "
            f"placeholder. Allow-listing a real value silently disables this "
            f"gate for that value — redact the value instead."
        )


def test_the_guard_scans_every_fixture_directory_not_just_some() -> None:
    """The scope cannot be narrowed to a subset of retailers without a red test.

    The verifier narrowed `_fixture_files` to `nintendo/*.html`, dropping BOTH
    Walmart fixtures — the ones this whole thread is about — out of the scan.
    380/380 green. A guard whose scope can be cut in half silently has the
    scope it happens to have, not the scope somebody chose.
    """
    root = Path(__file__).parent / "fixtures"
    scanned = set(_fixture_files(root))
    on_disk = {p for p in root.glob("*/*") if p.suffix in {".html", ".json"}}
    missing = on_disk - scanned
    assert not missing, (
        f"the identity guard does not scan every fixture — missing "
        f"{sorted(str(p.relative_to(root)) for p in missing)}. Pinned per FILE, "
        f"not per directory: returning one page per directory dropped half the "
        f"fixtures (including one of the two this whole thread is about) and "
        f"left the suite green."
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
