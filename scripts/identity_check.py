#!/usr/bin/env python3
"""Refuse to commit this machine's identity into a public repo.

WHY THIS IS A SCRIPT AND NOT A TEST, WHICH IS THE WHOLE POINT
--------------------------------------------------------------
This rule existed as a test body for two days and leaked anyway — seven times,
including twice inside the commits written to fix it. Two defects, and neither
was in the rule:

1. **It was pointed at `tests/fixtures/**` only.** Three of the four worst leaks
   were somewhere else: a planning document carrying this host's public IP and
   full Akamai EdgeScape record, the evidence log naming a ZIP twice, and — the
   one that should settle the argument — the guard's OWN test file, seeded with
   the real IP by the commit that added the coverage grid.

2. **It ran at test time, not commit time.** `make verify` catches a leak after
   it is already in history, which is the expensive half. Nothing looked at a
   staged diff, so every leak entered a commit unopposed and was found later by
   somebody reading.

So: one rule, three callers — the pre-commit hook (staged files), `make verify`
(the whole tree), and the test suite (which watches the rule fail, per class,
per carrier). A guard that only runs where the last leak was is a guard aimed
at the past.

Exit 0 clean, 1 on a leak, 2 on a usage error.

    scripts/identity_check.py --staged     # what the hook runs
    scripts/identity_check.py --all        # what `make verify` runs
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

#: Ranges that cannot be a real host, so a match inside one is a placeholder
#: rather than a leak. Enumerable and finite, which is why this is a RULE and
#: not allow-list entries: allow-listing individual addresses is one line away
#: from allow-listing a real one, and that mutation has been silent here before.
_RESERVED_IP_PREFIXES = (
    "192.0.2.",      # RFC 5737 TEST-NET-1
    "198.51.100.",   # RFC 5737 TEST-NET-2
    "203.0.113.",    # RFC 5737 TEST-NET-3
    "10.", "127.", "0.", "255.", "169.254.",
)


def _is_reserved_ip(v: str) -> bool:
    if v.startswith(_RESERVED_IP_PREFIXES):
        return True
    a = v.split(".")
    if len(a) == 4 and a[0] == "192" and a[1] == "168":
        return True
    return len(a) == 4 and a[0] == "172" and a[1].isdigit() and 16 <= int(a[1]) <= 31


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
               "NOT-AVAILABLE", "NULL", "192.0.2.1", "ZZ"}
    leaks: list[str] = []

    # A CDN echoing the client's own address back into the page.
    for header in ("true-client-ip", "x-forwarded-for", "client-ip"):
        for match in re.finditer(
            # The gap allows `"true-client-ip":"<ip>"` — the JSON-quoted
            # form is the one that actually leaked in `02-REVIEW.md`, and both
            # synthetic cases used the bare `header: ip` form, so narrowing the
            # gap was silent. First octet is 1-3 digits: a 3-digit octet is the
            # commonest shape of a real address.
            rf"{re.escape(header)}[^0-9]{{0,12}}(\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}})",
            body,
            re.I,
        ):
            if not _is_reserved_ip(match.group(1)):
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
    # ZIP+4 stays fail-closed even though a `NNNNN-NNNN` SKU can trip it: a
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
    # `"pickupStore":"<n>"`, `"stateCode":"<ST>"`, `storeId=<n>` and a WIC agency
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
        # `data-` attributes. GameStop shipped `data-preferred-store-id="<n>"`
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
        # camelCase header names inside JSON. Best Buy writes `"xForwardedFor"`,
        # which the kebab-case header loop cannot see — two real Akamai hops
        # shipped in a fixture through seven rounds because of it.
        (r'"(?:xForwardedFor|trueClientIp|clientIp|xRealIp)"\s*:\s*"([^"]+)"', "client IP in a camelCase header"),
        (r'\bstore(?:_?[Ii]d|Number)\s*(?:=|%3D)\s*(\d+)', "store number in a URL"),
        (r'"(?:state|region|province)(?:Code|OrProvinceCode|_code)?"\s*:\s*"([A-Z]{2})"', "state or region"),
        (r'"(?:city|cityName|locality|town)"\s*:\s*"([A-Za-z][A-Za-z .\'-]{2,})"', "city"),
        (r'"(?:destinationZipCode|postCode|post_code|zip5|zipcode)"\s*:\s*"?(\d{4,})', "postal code"),
        (r'"(?:lat|lng|lon)"\s*:\s*"?(-?\d+\.\d+)', "coordinate"),
        (r'"(?:dma|dmaCode|fips|fipsCode|cbsa|metro|county|countyName)"\s*:\s*"?([A-Za-z0-9][A-Za-z0-9 ]*)', "metro or county code"),
        (r'"(?:address_?[Ll]ine(?:One|Two|[12])?|streetAddress|street1)"\s*:\s*"([^"]+)"', "street address"),
        (r'(?:WICAgencies|wicAgencies)"\s*:\s*\[\s*"([A-Z]{2})"', "state via WIC agency"),
    )
    # `re.I` here too: `Set-Cookie:` Title-Case is a real spelling, and
    # without the flag it is a free pass through every cookie rule.
    for pattern, what in keyed:
        for match in re.finditer(pattern, body, re.I):
            value = match.group(1)
            # Only `break` on a REPORTED leak. Falling through on an allowed
            # value is deliberate: the redacted placeholder appears before the
            # real value in both Walmart fixtures, so stopping at the first
            # match would disable the rule for the pages it exists for.
            if value.strip("0.- ") and value.upper() not in {a.upper() for a in allowed}:
                leaks.append(f"{name}: {what} {value[:40]}")
                break

    # `City, ST NNNNN` — the postal form, which the `City, NNNNN` rule below
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
    # `City, NNNNN` is the shape a US destination takes when a retailer prints
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
    "236cf465237bb69a",
    "4ea837ac2e51fbac",
    "64dbbaf3ea56ab46",
    "a53deaefbc39492b",
    "b217537a0c765b26",
    "bde3e8fc954e7690",
    "f02b0d63e8932b46",
})



def _is_known_real(value: str) -> bool:
    return hashlib.sha256(value.lower().encode()).hexdigest()[:16] in _SCRUBBED_VALUE_HASHES



#: Files whose CONTENT is examined. Binary and vendored paths are skipped
#: because they cannot carry a hand-written value and would only add noise.
_SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip",
                  ".gz", ".bundle", ".woff", ".woff2", ".ttf", ".lock"}
_SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache",
              ".pytest_cache", "served"}


#: Files that legitimately contain probe-shaped text, and what they are held to
#: INSTEAD — which is stricter, not weaker.
#:
#: `tests/test_fetch.py` carries one probe per leak class by construction, and
#: the phase records quote mutation output verbatim. Running the pattern rules
#: over them reports every probe as a leak, so a naive scan is unusable and the
#: obvious fix is to skip them by path.
#:
#: **Skipping by path is what let the `.json` provenance notes leak.** So these
#: files are not skipped: they are checked against `_is_known_real`, the exact
#: SHA-256 set of every value this repo has ever had to scrub. That is a harder
#: bar than the pattern rules, not an easier one — the pattern rules ask "does
#: this look like an identity?", and this asks "is this a value we have already
#: removed once?". It is precisely the check that would have caught the coverage
#: grid being seeded with this host's public IP.
#:
#: Adding to this set is a real decision. `tests/test_identity_check.py` pins
#: its size so it cannot quietly grow.
_PROBE_FILES = frozenset({
    "tests/test_fetch.py",
})
_PROBE_DIR_PREFIXES = (".planning/phases/",)


def _is_probe_file(rel: str) -> bool:
    return rel in _PROBE_FILES or rel.startswith(_PROBE_DIR_PREFIXES)


def _scrubbed_value_leaks(rel: str, body: str) -> list[str]:
    """The stricter check applied to probe-bearing files.

    Every whitespace/quote-delimited token is hashed against the set of values
    this repo has scrubbed. No pattern matching, no shape heuristics — an exact
    answer to "have we removed this exact string before?".
    """
    leaks = []
    for tok in set(re.findall(r"[A-Za-z0-9][A-Za-z0-9._:-]{3,}", body)):
        if _is_known_real(tok):
            leaks.append(f"{rel}: PREVIOUSLY-SCRUBBED VALUE reused ({len(tok)} chars)")
    return leaks


def _tracked_files(root: Path) -> list[Path]:
    """Every file git tracks — NOT just the fixtures.

    The scope defect this script exists to fix: the leak that mattered most was
    in `.planning/`, and the second-most was in `tests/`.
    """
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                         capture_output=True, text=True, check=True).stdout
    return [root / p for p in out.split("\0")
            if p and Path(p).suffix.lower() not in _SKIP_SUFFIXES
            and not set(Path(p).parts) & _SKIP_DIRS]


def _staged_files(root: Path) -> list[Path]:
    """Only what is about to be committed — what the pre-commit hook checks."""
    out = subprocess.run(
        ["git", "-C", str(root), "diff", "--cached", "--name-only",
         "--diff-filter=ACMR", "-z"],
        capture_output=True, text=True, check=True).stdout
    return [root / p for p in out.split("\0")
            if p and Path(p).suffix.lower() not in _SKIP_SUFFIXES
            and not set(Path(p).parts) & _SKIP_DIRS
            and (root / p).exists()]


def scan(paths: list[Path], root: Path) -> list[str]:
    leaks: list[str] = []
    for p in paths:
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except (OSError, IsADirectoryError):
            continue
        rel = str(p.relative_to(root))
        if _is_probe_file(rel):
            leaks.extend(_scrubbed_value_leaks(rel, body))
        else:
            leaks.extend(_identity_leaks(rel, body))
    return leaks


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--staged", action="store_true", help="scan staged files (pre-commit)")
    g.add_argument("--all", action="store_true", help="scan every tracked file")
    args = ap.parse_args(argv)

    root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                               capture_output=True, text=True, check=True).stdout.strip())
    paths = _staged_files(root) if args.staged else _tracked_files(root)
    leaks = scan(paths, root)

    if not leaks:
        print(f"identity check: PASS — {len(paths)} file(s), no host identity found")
        return 0

    where = "staged for commit" if args.staged else "tracked in this repo"
    print(f"identity check: FAIL — {len(leaks)} leak(s) in files {where}\n", file=sys.stderr)
    for leak in sorted(set(leaks)):
        print(f"  {leak}", file=sys.stderr)
    print(
        "\nThis repo is public. Each line above is a fact about the machine that\n"
        "captured the page — an IP, a postal code, a store, a session token.\n"
        "\n"
        "Redact the VALUE, not the key: the key has to stay real or the rule\n"
        "stops matching a real page. Replacements that read as placeholders:\n"
        "  00000  XX  REDACTED  0.0000  192.0.2.1 (RFC 5737)\n"
        "\n"
        "Do NOT add the value to the allow-list, and do NOT write it into the\n"
        "commit message or a redaction note — a record that names what it\n"
        "removed is a copy of it. That has happened here three times.\n",
        file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
