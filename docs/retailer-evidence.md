# Retailer evidence log

What was actually tried against each retailer, and what actually came back.

`.planning/ROADMAP.md` defines an escalation ladder — rung 1 impersonated HTTP,
rung 2 a documented API, rung 3 a real browser, rung 4 "drop, with evidence".
This file is where that evidence lives. It exists because "we tried and it did
not work" is a claim, not a finding: without the concrete observation behind it,
nobody six months from now can tell whether a retailer is worth retrying, or
whether the wall we hit was ever really the retailer's.

So each section records the observation — the error code, the byte count, the
URL form, the binary used — rather than the conclusion drawn from it. A verdict
line is one of exactly three forms, character for character, because later work
branches on it mechanically:

- `**Verdict: REACHABLE (rung N)**` for N in 1–3
- `**Verdict: REFUSED**`
- `**Verdict: UNPROBED (scoped YYYY-MM-DD)**`

There is deliberately no rung-4 REACHABLE form: rung 4 **is** refused.

The third form is the only temporary one, and it exists because the honest
answer needed a spelling. `scripts/evidence_check.py` runs on every `make
verify` and requires every retailer in scope to be shipped or refused in
writing — so from the moment a retailer is added to scope until the day it is
settled, the tree is red, and the one-line way to green it would be writing
`**Verdict: REFUSED**` for a store nobody has touched. That is the same padding
this file exists to prevent, in the opposite direction. `UNPROBED` says "in
scope, nobody has looked yet", carries the date it entered scope, and **expires
after 60 days**, after which the gate goes red again. `evidence_check --phase
--strict` refuses it outright: a phase does not get to close on a retailer
nobody read.

There is a fourth anchored line form, and unlike the three above it is not a
verdict — it is the evidence a verdict of REFUSED has to rest on:

```
**Refusal observed (rung N):** <what came back>
```

for N in 1–3, one whole line, and **the body must carry a measurement**: an HTTP
status code, a byte count, or one of `boty.fetch.BLOCK_PHRASES` quoted. A body
that is only prose is rejected with its own message, because the point of the
line is the part that could only have come from an attempt. `scripts/evidence_check.py`
rule 6 requires **at least one** wherever a `**Verdict: REFUSED**` stands, and
**at least two including one at rung 3** for the two retailers in `HARD_TWO`
(`target` and `amazon`) — those are the two whose landing takes the count to
five, so dropping one takes a walked ladder rather than one failed request.

That rule exists because REQ-07a — *a retailer is dropped only when it is
technically unreachable, and the reason recorded is the observation, not a
policy reading* — was a sentence in a requirements document and nothing read it.
Phase 3 dropped **two** retailers on a desk review of their written terms, made
zero product-page requests to either, and every gate in this tree stayed green.

Two things rule 6 deliberately does **not** do. It says nothing about REACHABLE
sections, which may legitimately carry refusal observations from a rung that
failed on the way to one that worked — § Target carries two and § Amazon one,
and all three are historical. And it says nothing about UNPROBED sections, which
are *already* saying nobody has looked; demanding an observation from one would
make the honest state unrepresentable, which is the failure this file's third
verdict form exists to prevent.

Note that a refusal observation is evidence about a request, not a verdict about
a retailer: § Target's rung-1 line reads *"not a block — **HTTP 200**"* and
records that Target did **not** refuse us. The body predicate cannot catch that
— it has a status code and two byte counts — and nothing except rule 6's
REFUSED-only scope keeps it harmless. Widen that scope and it becomes a shipped
falsehood; a test in `tests/test_evidence_check.py` pins exactly this.

Anything reached by browser is flagged DEGRADED in the support matrix and in
`boty check` output, per the locked decision in `.planning/phases/02-five-retailers-green/02-CONTEXT.md`.

---

## Amazon (amazon.com)

**Probed:** 2026-08-03 twice — first with `curl` for the policy documents, then
with `boty.fetch.get` for three `/dp/<ASIN>` product pages. Both from danserver
over a residential connection.
**Transport:** `curl` for the policy reads; impersonated HTTP (rung 1) for the
product pages. No browser was ever started against amazon.com.

**Verdict: REACHABLE (rung 1)**

**That verdict replaces a REFUSED one recorded earlier the same day, and nothing
behind the REFUSED is retracted.** Read the whole section rather than this line.

- **Phase 3, 03-01 (2026-08-03, earlier):** REFUSED, on Amazon's Conditions of
  Use, with **zero** product-page requests ever made. Every quoted clause, every
  byte count and the whole `robots.txt` analysis below stand exactly as written.
- **03.1-03 (2026-08-03, this verdict):** REACHABLE at **rung 1 with `dom`
  extraction**, after Dan reversed the terms reasoning and the question nobody
  had asked was finally asked. Amazon serves `/dp/<ASIN>` to impersonated HTTP:
  three requests, three HTTP 200s, no challenge, correct product titles.

**What REACHABLE means here, precisely.** Amazon's product pages are reachable
and carry a readable stock signal — but **not a structured one**. There is no
`application/ld+json` on a `/dp/` page, no `__NEXT_DATA__`, and no JSON blob
carrying a price, an availability or a seller. What is server-rendered is the
add-to-cart control, the `#availability` line and a named buy-box seller, and
that is what `boty.retailers.check_amazon` reads.

**So this is Target's fragility on GameStop's transport, and the matrix says
so.** Rung 1 + `dom`, `degraded=True` on every result, a `[dom]` tag in `boty
check`. Cheap to run and silent to break: an Amazon buy-box redesign produces no
error, only a control that stops reading. That is the combination 03.1-05
widened `Result.degraded` for, and Amazon is its first real user.

**Amazon is the one retailer of the hard two that does list the product** — and
the listing is the exact thing this project exists not to alert on. See the
2026-08-03 subsection: a **used** unit at **$219** from a third-party reseller
against a $54.99 MSRP.

The Conditions of Use quotations, the `robots.txt` analysis and the PA-API
deprecation all remain below, in full. They are still true and they still feed
the REQ-13 Terms cell; what changed is that they are no longer the *decisive*
reason for a rung, because that decision was Dan's to make and he made it.

### 2026-08-03, 03.1-03 — the request Phase 3 never made

**The conclusion above is being revised at Dan's direction.** His words, the
same ones that reversed the Target reading earlier the same day:

> bot-y is a bot for humans. To take the power back from other bots.

**Everything Phase 3 observed stands, and none of it is retracted.** The six
policy reads and their byte counts, the LICENSE AND ACCESS clause quoted in
full, the whole `robots.txt` analysis and the PA-API deprecation are all exactly
as written above and below. What changed is not an observation; it is which
document decides. The Conditions of Use reading was the *decisive* reason for
rung 4 and it no longer is, which left a question nobody in Phase 3 had asked:
**can we read the page at all?**

**This subsection is the answer, and it is the first time this repository has
ever requested an Amazon product page.** That matters for reading the rest of
this section, because four passages elsewhere in it state the opposite, and they
were true when they were written:

1. the **Probed** header at the top — *"`boty.fetch.get` was never pointed at
   amazon.com and no product page was requested at any point in this phase"*;
2. *"**Six requests in total** … **Zero to a product page. Zero from bot-y.**"*
   under **What was retrieved**;
3. the first two bullets of **What was NOT done, and why** — *"No product page
   was ever requested. Not at rung 1, not at rung 3, not once"* and *"No
   transport work at all"*;
4. **If somebody revisits this later** — *"Do not re-probe … A clean HTTP 200
   from `/dp/<ASIN>` would prove only that we had been rude successfully."*

**All four are historical as of 2026-08-03 and none of them is current.** They
describe Phase 3's conduct accurately and are left standing for that reason; the
live figures are in this subsection.

#### Step 1 — the ASIN, from a public source that is not amazon.com

The Pokémon GO Plus + is **ASIN `B0BX2P43PX`**, found through the Internet
Archive's CDX index — the same route that worked for Target in 03.1-02, and the
one that costs Amazon nothing:

```
https://web.archive.org/cdx/search/cdx?url=www.amazon.com/Pokemon-GO-Plus
    &matchType=prefix&collapse=urlkey&limit=400&fl=original,timestamp,statuscode
```

Five `/dp/` ASINs came back under that slug prefix and four more under the
`Pok%C3%A9mon-GO-Plus` one. The candidate was settled without asking Amazon
either: the archived capture `20240303065820` of
`www.amazon.com/Pokemon-Go-Plus/dp/B0BX2P43PX`, served by **web.archive.org**,
carries `<title>Amazon.com: Pokemon Go Plus + : Electronics</title>` and
`id="productTitle"` → `Pokemon Go Plus +`. Two CDX queries and one archived page
read, all to `web.archive.org`, none to `amazon.com`.

Two notes worth keeping. A CDX `url=` value must not contain a trailing `*` when
`matchType=prefix` is given — the asterisk is matched literally and the query
returns nothing, which reads exactly like "the product was never archived". And
a domain-wide `matchType=domain` scan of `amazon.com` with a `filter=urlkey`
regex is refused: **HTTP 504 from the CDX front end after 60 s**. Prefix queries
on a guessed slug are the route that works.

#### Step 2 — the control candidate

**`B00NTCH52W` — Amazon Basics 20-Pack AA Alkaline Batteries**, chosen and
recorded before it was fetched. The rule is unchanged from every other control
in this project: first-party, evergreen, never a buy-box fight. Amazon-owned
brands are the safe class here specifically because Amazon's buy box rotates
between sellers — an Amazon Basics line is sold by Amazon's own entity by
construction, so there is no rotation to lose to. A household consumable rather
than an electronics item, for the same reason the Walmart control is a gallon of
milk.

The first candidate was **`B014I8SIJY`** (Amazon Basics HDMI Cable, 3 ft) and it
was fetched and then **rejected**, which is recorded rather than hidden: its
`#availability` region reads *"Only 2 left in stock - order soon."* A control
that can plausibly sell out is a control that reddens `make verify` for a reason
that is not a defect. The batteries read a flat *"In Stock"*.

What would make either a bad control later: Amazon delisting the pack size, or
the buy box moving to a third-party seller, both of which the control itself
detects within a cycle by reading UNKNOWN or a foreign seller string.

#### Step 3 — what came back

Every request below was made by **`boty.fetch.get`** — the real curl_cffi Chrome
impersonation and the real `BLOCK_PHRASES` check — not by `curl`. `requests.get`
inside `boty.fetch` was wrapped only so the raw response survived a `Blocked` or
a `FetchError` for the record; the fetch itself is unmodified, one request per
row.

| Requested | Result |
|---|---|
| `https://www.amazon.com/dp/B0BX2P43PX` — Pokémon GO Plus + | **HTTP 200**, **1,893,079 B**, `text/html;charset=UTF-8`, no redirect. **No `BLOCK_PHRASES` entry matched.** `<title>` = `Amazon.com: Pokemon Go Plus + : Electronics`; `id="productTitle"` = `Pokemon Go Plus +` |
| `https://www.amazon.com/dp/B014I8SIJY` — Amazon Basics HDMI cable (rejected control candidate) | **HTTP 200**, **3,189,747 B**, `text/html;charset=UTF-8`, no redirect, **no `BLOCK_PHRASES` match** |
| `https://www.amazon.com/dp/B00NTCH52W` — Amazon Basics 20-pack AA (the control) | **HTTP 200**, **3,223,370 B**, `text/html;charset=UTF-8`, no redirect, **no `BLOCK_PHRASES` match** |

**Three requests, all to `www.amazon.com/dp/<ASIN>`, all HTTP 200, none
refused.** No `/gp/product/product-availability`, no `/dp/product-availability/`
and no `/gp/offer-listing/` — the three paths Amazon's `robots.txt` disallows
were not touched, then or now.

**What the readers found — and did not.**

| Reader | GO Plus + `B0BX2P43PX` | Control `B00NTCH52W` |
|---|---|---|
| `parse.ldjson_offers` | `None` | `None` |
| `parse.nextdata_offers` | `None` | `None` |
| `application/ld+json` blocks | **0** | **0** |
| `schema.org` occurrences | 1 (a CSS/JS mention, no Product node) | 0 |

**Amazon publishes no structured stock data on a `/dp/` page.** Every
`<script>` carrying JSON is session or layout state — `a-wlab-states`,
`detail-page-device-type`, `atc-page-state` (`{"shouldUseNatcUsed":true}`),
`acState` (`{"acAsin":"B0BX2P43PX"}`), `oas-offer-refresh-page-state` (which
carries a **`csrfToken`**) — and none of them carries a price, an availability
or a seller. The one genuinely interesting blob is
`<script type="application/agent+json" id="agent-semantic-map">`, an
`https://agent.schema.org` `AgentInterfaceMap` declaring `"pageType":
"product-listing"` and a single `search_agent` primary action pointing at
`#nav-search-submit-button-agent`. It describes how Amazon would like an agent
to *search*; it publishes no offer.

**The add-to-cart control is in the served HTML at rung 1, with no browser.**
Verbatim, from the GO Plus + page:

```html
<input id="add-to-cart-button-ubb" name="submit.add-to-cart-ubb"
       title="Add to Shopping Cart" data-ref="" class="a-button-input"
       type="submit" formaction="/cart/add-to-cart/ref=dp_start-ubbf_1_glance"
       value="Add to cart" aria-labelledby="submit.add-to-cart-ubb-announce"/>
```

and from the control page:

```html
<input id="add-to-cart-button" name="submit.add-to-cart"
       title="Add to Shopping Cart" data-ref="" class="a-button-input"
       type="submit" formaction="/cart/add-to-cart/ref=dp_start-bbf_1_glance"
       value="Add to cart" aria-labelledby="submit.add-to-cart-announce"/>
```

Three differences from Target's control matter and all three are structural:
the element is a **void `<input>`** rather than a `<button>`, its label lives in
the **`value` attribute** rather than in child text, and its `id` is an **exact
string** rather than a per-product prefix — with a second form, `-ubb`, for a
used buy box. Neither carried `disabled` or `aria-disabled`.

**The strings the ladder asked about:**

| String | GO Plus + | Control |
|---|---|---|
| `In Stock` | 0 | 8 |
| `Currently unavailable` | 2 | 2 — **both inside JavaScript string tables** (`"currentlyUnavailableMessage"`, `"currentlyUnavailablePopOverStringValue"`), neither rendered |
| `Ships from` | 0 | 2 — in the *frequently-bought-together* module, not the buy box |
| `Sold by` | 1 — the used buy box | 1 — likewise a related-items module |

`#availability` is the region that actually answers the question, and both pages
render it server-side:

- GO Plus +: `Only 10 left in stock - order soon.`
- control: `In Stock`
- rejected HDMI candidate: `Only 2 left in stock - order soon.`

**No explicit unavailable marker was observed on any of the three**, because all
three were available. That is recorded as a gap rather than papered over: this
plan never saw an unavailable Amazon page, so absence of the control is read as
UNKNOWN, never as out-of-stock. Amazon's `#availability` blob also carries
`"isRobot":false` — the same self-report Target's page makes.

**The buy-box seller string, verbatim, and it is the whole reason the seller
filter exists.** The control page states it through the offer-display feature
`odf-feature-text-desktop-merchant-info`, labelled `Shipper / Seller`:

> Amazon.com

The GO Plus + page states it through a **used** buy box instead:

```html
Sold by <a id="sellerProfileTriggerId" data-is-ubb="true" class="a-link-normal"
   href="/gp/help/seller/at-a-glance.html?ie=UTF8&seller=A1N4D4JHZX5QJK"
>LO Store (We Record Serial Numbers To avoid FRAUD)</a>
```

with `id="usedbuyBox"`, `usedMerchantID` `A1N4D4JHZX5QJK`, and a `priceToPay` of
**$219**. The Pokémon GO Plus + has an MSRP of **$54.99**. So the only offer
Amazon currently shows for the product this project exists to watch is a
**used unit from a third-party reseller at four times MSRP** — verbatim, the
alert this project exists not to send, and the reason `amazon` is in
`MARKETPLACES` and the `max_price: 80` ceiling is not decorative.

The control page's price is **$8.49**; the rejected HDMI candidate's was $4.40.

#### Step 4 — the classification

**Shape (C): REACHABLE, dom — at rung 1.**

The four shapes 03.1-03 defines are exhaustive, and the observations pick one:

- **not (A) REFUSED.** Nothing refused anything. Three `/dp/` requests, three
  HTTP 200s, zero `BLOCK_PHRASES` matches, correct product titles on all three.
  There is no wall to record and no rung-3 attempt is warranted: the refusal
  branch requires an observed refusal at rung 1 before a browser is reached for,
  and there was none.
- **not (B) REACHABLE, structured.** Both structured readers returned `None` on
  both pages, and there are zero `ld+json` blocks. The page embeds no offer
  payload in any form.
- **(C) REACHABLE, dom.** HTTP 200, readable product HTML, no structured data,
  and an add-to-cart control that can be read **out of the rung-1 bytes**. This
  is Target's shape, and since 03.1-05 and 03.1-02 it is a supported outcome
  rather than a failure.
- **not (D) REACHABLE, no signal.** There *is* a signal: the control, the
  `#availability` text and a named buy-box seller, all server-rendered.

**The rung is 1, and it stays 1.** The ladder says stop at the first rung that
works, and rung 1 works: the control is in the impersonated-HTTP response with
no browser started. Reaching for rung 3 to make Amazon look more like Target
would be spending a Chrome process to obtain bytes we already have. Amazon is
therefore **rung 1 + `dom`** — the cheapest transport with the most fragile
extraction, which is precisely the combination 03.1-05 widened `degraded` to
catch, three days before anything needed it.

#### The politeness budget

| | Cap | Spent |
|---|---|---|
| `*.amazon.com` requests | 6 | **3** in this task — 13:31:16Z, 13:32:48Z, 13:34:13Z |
| of which rendered | 2 | **0** |
| Spacing | ≥ 20 s | 89 s and 85 s |
| Retries | none | **none** — nothing failed, so nothing was retried |

Requests to `web.archive.org` (two CDX queries and one archived page) and the
timed-out domain-wide CDX scan are not counted against it: none of them reaches
amazon.com.

**Controls, bracketing the whole task.** `scripts/control_check.py` run under
the service `EnvironmentFile` before the first Amazon request and again after
the last:

- **before**, 13:24Z — `PASS — 5/5 controls in stock`, exit **0**
- **after**, 13:35:42Z — `PASS — 5/5 controls in stock`, exit **0**

Both runs read all five live, browser rung included; neither was an
`INCOMPLETE` (exit 4) green.

### 2026-08-03, 03.1-03 — what was then built, and the wall we walked into on the way

#### Amazon refused us exactly once, and it was our own fault

Two `boty capture-fixture` calls were made **12 s apart** rather than the ≥ 20 s
the budget above requires. The second came back like this, from the same URL
that had served 1.89 MB of product page eight minutes earlier:

**Refusal observed (rung 1):** `https://www.amazon.com/dp/B0BX2P43PX` — **HTTP 200**, **3,781 B**, `<title>Amazon.com</title>`, body reading "Click the button below to continue shopping" over a form posting to `/errors_page/validateCaptcha`, plus Amazon's own notice "To discuss automated access to Amazon data please contact api-services-support@amazon.com."

(One line, for the reason § Pokémon Center records below: rule 6's regex is
line-anchored, so a measurement that wraps is a measurement it cannot read.)

**That line is historical, and it records a cadence throttle rather than a
policy wall.** It is kept because it is a measurement and because it is the only
refusal this repository has ever seen from Amazon. It does not describe the
current state of this retailer: the same path served a full page before it and
has served one on every control run since.

**Two things follow, and the second one is the serious one.**

First, the spacing rule is not decoration. 12 s is enough to trip it and 85 s is
not.

Second — **no `BLOCK_PHRASES` entry matched that wall.** So `boty.fetch.get`
returned a captcha gate as an ordinary `Page`, and `boty.fixtures.capture`
wrote it to disk under a product's name, which is verbatim the outcome
`capture`'s own docstring says it exists to prevent: *"a capture that swallowed
them would write a CAPTCHA interstitial to disk under a product's name and
poison every test that reads it."* Downstream it would have read as
`no structured stock data found (page shape changed?)` — fail-safe in outcome,
and a diagnosis blaming our parser for Amazon's refusal. **This is the Imperva
defect of 02-04 and the Akamai defect of the fifth-retailer search, on a third
vendor, and this time it actually bit.**

The file was deleted rather than committed and
`"to discuss automated access to amazon data"` was added to `BLOCK_PHRASES` in
the same task, with the wall embedded verbatim in `tests/test_fetch.py` as
`AMAZON_AUTOMATED_ACCESS_WALL` so the phrase is asserted against Amazon's bytes
rather than against our transcription of them.

**The obvious phrase was checked and rejected, and that check is the point.**
The wall's human-readable heading is *"Click the button below to continue
shopping"*, and the wording a search would have suggested — *"something went
wrong on our end"* — appears **once in each of the two real Amazon product pages
this plan fetched**. Adding it would have reported a working retailer as blocked
forever, which is the bad-bet failure `BLOCK_PHRASES`'s own docstring warns
about, one grep away from being shipped.
`test_a_real_product_page_is_not_mistaken_for_a_challenge` is now parametrised
over both Amazon fixtures for exactly that reason.

#### What landed

| | |
|---|---|
| Adapter | `boty.retailers.check_amazon` — `boty.fetch.get` + `_verdict_from_html(rung=Rung.TLS, allow_dom=True)`. `extraction=Extraction.DOM` on every path, error paths included |
| Reader | `boty.parse.add_to_cart_offers`, **widened rather than duplicated**. Amazon's control is a void `<input>` whose label is in its `value` attribute and whose id is fixed per layout (`add-to-cart-button`, or `-ubb` on a used buy box); Target's is a `<button>` with a per-product id prefix. One parser, two page families, one availability decision — and mutation M8 still covers it |
| Allow-list | `FIRST_PARTY["amazon"] = {"amazon.com", "amazon"}`, from the verbatim `Amazon.com` read off `/dp/B00NTCH52W`. `amazon` stays in `MARKETPLACES` |
| Watches | a control on `B00NTCH52W` and a **real product watch** on `B0BX2P43PX` with `max_price: 80` — Amazon is the only one of the hard two that lists the GO Plus + |
| Block phrase | `"to discuss automated access to amazon data"` added to `boty.fetch.BLOCK_PHRASES` |
| Fixtures | `tests/fixtures/amazon/control-aa-batteries.html` and `goplusplus.html`, both redacted by class before commit |

**The seller default is per page family, and that is the single most dangerous
line in this plan had it gone the other way.** On Target, *absence* of a seller
block is the first-party signal — measured, § Target. Carrying that default
across to Amazon would have meant every Amazon buy box the parser could not read
would report as sold by Amazon, so a reseller whose block failed to parse would
alert. On Amazon the default is `None`, which on a marketplace is UNKNOWN.
`test_an_amazon_offer_with_no_seller_recorded_is_unknown_not_a_verdict` pins it.

**The fixtures were redacted before commit, by class rather than by value** —
03.1-02's lesson applied *before* a leak rather than after one. The raw captures
carried Amazon's geolocation of this host (`Redacted` ×3 and ×3, `00000` ×6 and
×3), a `session-id`, an `anti-csrftoken-a2z`, ten offer-listing tokens, an
`x-amz-rid` request id and request timestamps. Every `<script>` body, every
`<style>` body and every HTML comment was emptied or dropped, session/csrf/
offer-listing/timestamp input values blanked, and every host marker replaced:
3.2 MB → 1.77 MB and 1.89 MB → 1.08 MB, with the control, the seller, the price
and the availability line all still reading. A hand scan for the host's public
IP, its city, its ZIP, coordinates, phone numbers, ZIP+4, session tokens and
request ids comes back clean, and the widened automated guard passes.

**One redaction bug is worth recording because it is the same shape as the
guard's.** The first pass matched secret input names with an *anchored* pattern
ending in `offerlistingid`, and Amazon writes `items[0.base][offerListingId]` —
so the token survived, silently, in a file that looked redacted. Containment
rather than anchoring fixed it, and the by-hand rescan is what found it. A guard
that only knows the exact spelling it was taught keeps passing until the shape
changes.

#### Live, after registration

`scripts/control_check.py` under the service `EnvironmentFile`, 13:58:05Z:

```
control check: 6 control(s), live
  in_stock  amazon  CONTROL — Amazon Basics AA batteri  $9.99  add-to-cart control: add-to-cart enabled from Amazon.com
control check: PASS — 6/6 controls in stock
```

Exit **0**, six live controls, not an `INCOMPLETE` green. **Six configured
retailers.**

#### The budget, finally

**5 of 6 requests spent**, and the sixth was deliberately not spent. Three
probes (Task 1) plus two `capture-fixture` calls, one of which returned the wall
above. Rather than re-request the product page, the fixture was written from the
**bytes of the 13:31:19Z probe** — a live `boty.fetch.get` response this
repository already held, saved outside the repo at the time — and its `.json`
sidecar records that provenance in full. **Zero rendered loads**, against a cap
of two.

Control-check requests are counted separately and deliberately: they are the
shipped monitor's ordinary behaviour, one request per pass, mandated by this
plan's own gates and by `boty.service` every 300 s from here on. Folding them
into a probing budget would make the budget meaningless the moment the retailer
was registered.

### What was retrieved

| Target | Result |
|---|---|
| `https://www.amazon.com/gp/help/customer/display.html?nodeId=508088` | **HTTP 200**, 344,140 B, `text/html;charset=UTF-8`, after a redirect to the current canonical URL `https://www.amazon.com/gp/help/customer/display.html?nodeId=GLSBYFE9MGKKQXXM`. Document header reads `Last updated: May 30, 2025` |
| `https://www.amazon.com/robots.txt` | **HTTP 200**, 7,887 B, `text/plain`, 436 lines, 100 `User-agent` blocks |
| `https://webservices.amazon.com/paapi5/documentation/register-for-pa-api.html` | **HTTP 200**, 52,744 B, after a redirect to `affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation` — the rung-2 API this repo would have reached for no longer exists |
| `https://affiliate-program.amazon.com/creatorsapi/docs/en-us/onboarding-request-access` | **HTTP 404**, 48,137 B — a guessed slug. Recorded rather than hidden; the correct URL was then read out of the previous page's own links instead of being guessed a second time |
| `https://affiliate-program.amazon.com/creatorsapi/docs/en-us/onboarding` | **HTTP 200**, 52,996 B |
| `https://affiliate-program.amazon.com/creatorsapi/docs/en-us/frequently-asked-questions` | **HTTP 200**, 52,829 B |

**Six requests in total, spaced 22–24 s apart, no retries, no refusals.** Two to
`www.amazon.com` — a public policy page, and the one file on the internet whose
entire purpose is to be fetched by an automated agent. Four to Amazon's developer
documentation hosts. **Zero to a product page. Zero from bot-y.**

### The operative clause, quoted in full

From the `LICENSE AND ACCESS` section of the Conditions of Use, retrieved
2026-08-03 from the URL in the table above. The whole sentence is reproduced so a
future reader can judge its scope for themselves rather than trusting this
document's reading of it:

> Subject to your compliance with these Conditions of Use and any Service Terms,
> and your payment of any applicable fees, Amazon or its content providers grant
> you a limited, non-exclusive, non-transferable, non-sublicensable license to
> access and make personal and non-commercial use of the Amazon Services. **This
> license does not include any resale or commercial use of any Amazon Service, or
> its contents; any collection and use of any product listings, descriptions, or
> prices; any derivative use of any Amazon Service or its contents; any
> downloading, copying, or other use of account information for the benefit of
> any third party; or any use of data mining, robots, or similar data gathering
> and extraction tools.**

And, two sentences later in the same paragraph:

> No Amazon Service, nor any part of any Amazon Service or its contents, may be
> reproduced, duplicated, copied, sold, resold, visited, or otherwise exploited
> for any commercial purpose without express written consent of Amazon.

> You may not misuse the Amazon Services. You may use the Amazon Services only as
> permitted by law.

**This is stronger than the Pokémon Center clause, and it is worth being precise
about why.** Pokémon Center's Terms forbid "data gathering or extraction methods
designed to scrape or extract data" — a prohibition on the *method*, which leaves
a reader room to argue about what counts as one. Amazon's clause forbids the
method *and independently* forbids "any collection and use of any product
listings, descriptions, or **prices**". Availability and price are the only two
fields bot-y reads. There is no reading of that sentence under which a stock
monitor is collecting something else, and no transport — impersonated HTTP, a
real browser, a residential proxy — changes which side of it we are on.

The licence Amazon grants is to "access and make personal and non-commercial use"
of the service. bot-y's use is personal and non-commercial, and that is not the
question: the carve-out for product listings and prices is written as an
exclusion *from* that same personal licence, not as a restriction on commercial
users only.

### robots.txt — narrower than the Conditions of Use, and the disagreement is the finding

The same shape as Pokémon Center, and worth stating explicitly because reading
robots.txt alone would have produced the opposite answer.

`https://www.amazon.com/robots.txt` is 436 lines and defines **100** `User-agent`
groups: one `*` group and 99 named ones. Almost every named group is the same two
lines —

```
User-agent: Scrapy
Disallow: /

User-agent: Crawl4AI
Disallow: /
```

— covering AI crawlers (`GPTBot`, `ClaudeBot`, `CCBot`, `Bytespider`,
`PerplexityBot`…) and, notably, **general-purpose scraping frameworks by name**:
`Scrapy` and `Crawl4AI` are each shut out of the entire site. That is not a
prohibition bot-y's user-agent string trips, but it is a clear statement of
intent from the same file.

The `*` group is a long, specific deny-list rather than a blanket refusal. What
matters for a stock read:

```
Disallow: /gp/product/product-availability
Disallow: /dp/product-availability/
Disallow: /gp/offer-listing/
Allow: /gp/offer-listing/B000
Allow: /gp/offer-listing/9000
```

The bare product page path — `/dp/<ASIN>` — carries **no** `Disallow`, and there
is no rule matching `/dp/` or `/dp/$` anywhere in the `*` group. So a naïve
robots.txt reading says the product page is fair game. But the two paths that most
directly answer *"is this in stock, and from whom"* — `product-availability` and
the buy-box `offer-listing` — are explicitly closed, with a narrow legacy
exception for two ASIN prefixes.

**So robots.txt is narrower than the Conditions of Use, and the two disagree.**
robots.txt would permit fetching `/dp/<ASIN>` and reading whatever it contains;
the Conditions of Use forbid collecting product listings and prices by any means.
Where they disagree, the Conditions of Use are the document Amazon asks you to
agree to by using the site, and the narrower technical file does not license what
the broader written one refuses. Reading `/dp/` because robots.txt forgot to
mention it, while the ToU names prices explicitly, is precisely the "respects
robots.txt while working around the ToU" posture that
`.planning/phases/03-the-hard-two/03-CONTEXT.md` locks this project out of.

There is no `Sitemap:` directive in the file, so there is not even a sanctioned
discovery path of the kind Nintendo publishes.

### Rung 2 evaluated against the fresh-clone rule — and it has moved since anyone last looked

`.planning/REQUIREMENTS.md`'s non-functional requirement is that a retailer's
PRIMARY path must work for someone who clones this repo and adds no credentials;
a credential needing manual approval, a paid domain or a commercial agreement is
a footnote, not support. Best Buy's row is the precedent — its API is real, works
well, and is documented as an *optional* upgrade for exactly this reason.

Amazon fails that test harder than Best Buy does, and the first thing to record
is that **the API this repo would have reached for no longer exists**:

> The Amazon Product Advertising API 5.0 (PA-API 5) has been deprecated and is
> being replaced by the Creators API. […] Applications that continue to call
> PA-API 5 receive an HTTP 403 Forbidden response with an
> `AccessDeniedException`.

The successor, the Creators API, states its onboarding in two steps:

> **1. Sign up as an Amazon Associate.** First, you need to become an Amazon
> Associate. The Associates Program is free to join and enables you to monetize
> your traffic through affiliate commissions.
>
> **2. Register for Creators API.** Once you have an Amazon Associates account,
> you can register for the Creators API to get your API credentials (Access Key
> and Secret Key).

And access is regional and approved rather than issued:

> You will need a valid Partner Tag for the target marketplace and **Creators API
> access approved** in that region.

The FAQ's own account-verification advice names what an Associates account
entails — "if you can access payment method update and **tax interview** pages
for selected store then you are primary owner of the store".

So the rung-2 credential requires: an affiliate account governed by the
Associates Operating Agreement (a commercial agreement), a completed tax
interview, a payment method, a Partner Tag, and a per-region approval. A person
cloning this repo to watch one $54.99 accessory cannot obtain that, and should
not have to enter a commercial relationship with a retailer to check whether it
has something in stock. **Rung 2 is closed against the fresh-clone rule** — and
it would be closed even for someone who had all of it, because the Conditions of
Use above are not suspended by holding an Associates account. The Creators API is
a sanctioned path for affiliate publishers to *promote* products, not a
back-channel around the clause that forbids collecting prices.

### What was NOT done, and why — revised 2026-08-03 by 03.1-03

The four bullets this heading used to carry were Phase 3's, and the first two of
them said no product page had ever been requested. **Both are now historical**;
they are quoted and dated in the 2026-08-03 subsection above rather than edited
into something they never said. What follows is what is *not* done as of this
verdict.

- **Still no rung 2, and the reason is unchanged.** The Creators API was not
  signed up for. It needs an Associates account governed by a commercial
  operating agreement, a completed tax interview, a payment method, a Partner Tag
  and a per-region approval — see the fresh-clone analysis above. A person
  cloning this repo to watch one $54.99 accessory cannot obtain that. Nothing in
  this plan changes that assessment; rung 1 works, so rung 2 was never needed.
- **Still no browser.** Amazon serves the add-to-cart control in the rung-1
  bytes, so rung 3 would spend a Chrome process to obtain something curl already
  returned. The ladder says stop at the first rung that works.
- **The three disallowed paths were not touched.**
  `/gp/product/product-availability`, `/dp/product-availability/` and
  `/gp/offer-listing/` carry a `Disallow` in Amazon's `robots.txt` and this
  repository has never requested any of them. `/dp/<ASIN>` — which carries no
  `Disallow` and no matching rule anywhere in the `*` group — is the only path
  read. That distinction is the whole of the robots.txt position and it is
  unchanged from Phase 3's reading of the same file.
- **No unavailable Amazon page was ever seen.** All three pages fetched were
  available, so this repository has no observation of what Amazon renders when an
  item cannot be bought. `parse.add_to_cart_offers` therefore returns `None`
  (UNKNOWN) when the control is absent and will never say OUT_OF_STOCK on
  Amazon's word from an absence. That is a gap, recorded as one.
- **The politeness budget was not spent.** 5 of 6 requests, 0 of 2 permitted
  rendered loads.

### If somebody revisits this later

**The instruction here used to be "do not re-probe", and it was right when it
was written** — there was no wall to weaken and nothing to learn. It is quoted
in the 2026-08-03 subsection above as one of the four passages this plan
supersedes. What replaces it:

**Do re-read the Conditions of Use, and read them as a person rather than as a
gate.** The LICENSE AND ACCESS clause quoted in full above still says what it
says, and this project still reads two of the fields it names. That tension is
not resolved by this verdict; it is *decided*, by the maintainer, on the record,
in these words: *"bot-y is a bot for humans. To take the power back from other
bots."* Somebody inheriting this repository is entitled to decide differently,
and everything they would need to is above: the clause verbatim, the retrieval
date, the `Last updated` header, and the robots.txt analysis that disagrees with
it in the narrower direction.

**Do expect this detector to break quietly.** It reads presentation markup on a
retailer that A/B-tests its buy box continuously. The control watch on
`B00NTCH52W` and mutation M8 are the two things that will tell you; there is no
third.

**What would still be a genuine upgrade** is Amazon publishing something
structured a non-commercial user may read — a product-availability signal, or a
Creators API tier without the affiliate relationship. Either would move this off
`dom` and drop the `degraded` flag, and would be worth wiring up the same
afternoon.

### Why this is the plan succeeding

The roadmap's criterion for this retailer is "Amazon reports stock, **or** the
support matrix records what was tried and why it failed." **This is now the
first branch**, and getting there cost three product-page requests.

That is worth being precise about, because the second branch had already been
recorded and it looked complete: quoted clauses, a full `robots.txt` analysis,
six policy reads with byte counts, a coherent argument. Everything in it was
true. What it did not contain was a single observation about whether the page
could be read — and it had a section explaining why nobody should ever find out.
A finding that forecloses its own disproof is the shape worth recognising here;
REQ-07a and `evidence_check` rule 6 exist so the tree can recognise it
mechanically rather than relying on somebody re-reading the prose.

The count is now **six retailers configured**, and Amazon is the only one of the
six that both lists the Pokémon GO Plus + and is a marketplace — which makes it
the only place the seller filter and the price ceiling have anything to defend
against. They are defending against something today: a used unit at $219.

---

## Best Buy

**Probed:** 2026-08-02, from danserver over a residential connection.
**Transport:** `boty.browser.fetch_rendered` (rung 3), nodriver 0.50.3 driving
Chrome for Testing 149 headless. ~16 requests total, spaced 12–22s apart, with
a 90s backoff partway through.

### Why rung 3 at all

Rung 1 was already ruled out before this phase: Best Buy refuses impersonated
HTTP at the connection layer regardless of TLS fingerprint — HTTP/2 stream
reset, HTTP/1.1 timeout — verified across `chrome` and `safari` impersonation
(`QUESTIONS.md`). Rung 2, the official API, requires manual approval and rejects
free email domains, so it cannot be the path a fresh clone depends on.

**Verdict: REACHABLE (rung 3)**

A headless browser reads Best Buy product pages, and the pages carry complete,
first-party schema.org data — availability, price *and* seller. But reachability
is **per-URL-form and not uniform across products**, and that qualification is
the load-bearing part of this section.

### What was observed

| Target | Result |
|---|---|
| `https://www.bestbuy.com/` | Rendered, 467,391 B, title `Best Buy \| Official Online Store` |
| `/site/searchpage.jsp?st=…` (×4) | Rendered, 1.45–1.55 MB, real titles |
| `/site/-/6577129.p` | **`ERR_HTTP2_PROTOCOL_ERROR`** — Chromium's own error page, 185,232 B |
| `/site/-/6577129.p?skuId=6577129` | **`ERR_HTTP2_PROTOCOL_ERROR`**, 185,274 B |
| `/site/apple-airtag/6483542.p?skuId=6483542` | **`ERR_HTTP2_PROTOCOL_ERROR`**, 185,307 B |
| `/product/pokemon-go-50-gift-card-…/JJG34YWLWJ` | Rendered ×2, 1.04/1.05 MB, 3 ld+json blocks |
| `/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ` | Rendered, 1,166,375 B, 3 ld+json blocks |
| `/product/best-buy-essentials-6-4k-…-hdmi-cable-black/J2FPJKPLWS` | **`ERR_HTTP2_PROTOCOL_ERROR`** ×2, 185,391 B |
| `/product/…-digital/JCQ6HSSXJH` (bad ID) | Rendered, 597,478 B, `Best Buy: Page Not Found` |

Three things follow from that table, and each one changes what 02-03 should build:

1. **The legacy `/site/<slug>/<sku>.p` URL scheme is uniformly refused.** Three
   attempts across two unrelated SKUs, every one an `ERR_HTTP2_PROTOCOL_ERROR`.
   Best Buy has moved to `/product/<slug>/<ID>`, where `<ID>` is an alphanumeric
   token (`J7GSL4G7GQ`) that is **not** the SKU. An adapter built around `.p`
   URLs or around SKU-to-URL construction will not work.
2. **A refusal is distinguishable from a 404.** A wrong product ID returned a
   genuine, rendered Best Buy "Page Not Found" (597 KB); a refusal returns
   Chromium's error page at a consistent ~185 KB with `ERR_HTTP2_PROTOCOL_ERROR`.
   These must not be conflated — one means "no such product", the other means
   "we were blocked", and only the second is UNKNOWN territory.
3. **Some product pages are reproducibly refused while others reproducibly
   render.** The Best Buy essentials HDMI cable failed twice, 90 s apart; the
   gift card succeeded twice across the same window. So this is not rate
   limiting and not intermittent — it is per-product, and the mechanism is
   unexplained. A first hypothesis of "physical vs digital" was tested and
   **falsified**: a physical Nintendo Switch game rendered fine.

Note that `BLOCK_PHRASES` matched **nothing** in any of these responses. The
refusal happens below HTTP, so there is no challenge page to phrase-match — it
surfaces as a `FetchError`, not a `Blocked`. The block-phrase scan in
`boty/browser.py` is still worth having, but it is not what catches this.

### The two load-bearing questions

**Is a price readable? — YES.** From the physical-product page
(`Pokémon: Let's Go, Pikachu! - Nintendo Switch`, SKU `6216393`):

```json
{ "@type": "Offer", "priceCurrency": "USD", "price": 59.99,
  "availability": "https://schema.org/InStock",
  "seller": { "@type": "Organization", "name": "Best Buy" } }
```

This matters because `Result.alertable` returns False when a ceiling is
configured and `price is None` (`boty/models.py:73-75`, the WR-01 hardening). An
adapter that read availability and skipped price could never alert on the
GO Plus + watch. It does not have to: the price is right there.

**Is a seller readable? — YES, and it resolves first-party.**
`offers[].seller.name` is `"Best Buy"`, which lowercases to `"best buy"` and is
already in `FIRST_PARTY["bestbuy"]` (`boty/retailers.py:29`). The rendered DOM
carries an explicit `Sold by` / `Best Buy` attribution too. So the concern that
`bestbuy` being in `MARKETPLACES` (`boty/retailers.py:39`) would make every
offer UNKNOWN — because unattributed offers are deliberately not treated as
first-party on a marketplace — **does not bite**: these offers are attributed,
so `_pick` finds them via the `named` branch and a control can go green.
No change to `MARKETPLACES` is needed.

The `@type` is the plain string `"Product"`, not a compound list, so the IN-03
compound-`@type` issue does not arise on Best Buy.

### Does Best Buy even sell the GO Plus +?

**No evidence that it does.** Two searches — `pokemon go plus` and
`pokemon go plus + nintendo` — returned only gift cards, membership cards and
unrelated Switch titles. No GO Plus + hardware appeared in either.

**SKU `6577129` is unconfirmed and probably wrong.** `tests/test_retailers.py:316`
uses it as the GO Plus + target. That string does not appear anywhere in Best
Buy's search results for the product, and its legacy `.p` URL is refused, so it
could not be resolved to a product page by any route tried here. It should be
treated as unverified: it is a fixture value nobody has ever seen resolve, not
an established fact.

This is the finding most likely to matter to the phase's five-retailer count.
Best Buy is *reachable*, but a Best Buy watch for a product Best Buy does not
carry is not worth much.

### Control product

The obvious pick — a Best Buy essentials house-brand cable, exactly the
"first-party, restocked routinely, never a buy-box fight" shape that
`config/products.yaml:49-51` prescribes — is **reproducibly refused**, so it
cannot be the control.

Best candidate observed, and it satisfies the same rule:

- **`Pokémon: Let's Go, Pikachu! - Nintendo Switch`**, SKU `6216393`
- `https://www.bestbuy.com/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ`
- Read as `InStock`, `$59.99`, `seller: Best Buy` — first-party, evergreen
  catalogue title, not a console, not a buy-box fight.

02-03 should confirm it still renders before wiring it in, and keep a second
candidate in reserve: given finding 3 above, "this product page renders" is not
currently predictable from any property we understand.

### What was built on it (2026-08-02, second session)

The verdict above left one thing unresolved that the adapter could not be built
without: **`bestbuy_product_url(sku)` has no template to use.** The legacy `.p`
form is refused, and the live `/product/<slug>/<ID>` form's `<ID>` cannot be
derived from a SKU. Two more probes settled it.

| Target | Result |
|---|---|
| `/site/searchpage.jsp?st=6216393` (a bare SKU) | **Redirected to the product page.** 1,109,548 B, title `Pokémon: Let's Go, Pikachu! Nintendo Switch HACPADW2A - Best Buy`, canonical `https://www.bestbuy.com/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ/sku/6216393`, `ldjson_offers` → exactly **one** offer: `available=True, price=59.99, seller='Best Buy'` |
| `/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ` | Rendered, 1,160,922 B, identical single offer — the control still renders four hours after the first spike |

So **Best Buy's own search is the SKU-to-URL resolver**, and that is what
`boty.retailers.bestbuy_product_url` returns. It is preferred over guessing a
URL template for a reason that is about the *miss* path rather than the hit
path, and the miss path was checked too:

- A search that matches nothing (SKU `6577129`, and the two GO Plus + searches
  from the first session) returns a search page carrying **no schema.org
  Product markup at all** — `ldjson_offers` → `None` — despite listing a dozen
  products with prices on screen. So a SKU that stops resolving reads UNKNOWN,
  loudly, instead of reporting an unrelated accessory as a restock. A guessed
  product-URL template had no such guarantee: Best Buy's own 404 page is a
  fully rendered 597 KB Best Buy page, and what it carries in `ld+json` was
  never established.

Both pages are frozen as fixtures with capture sidecars —
`tests/fixtures/bestbuy/pikachu-control.html` and
`tests/fixtures/bestbuy/unresolved-sku.html` — so the hit and the miss are both
regression-tested offline.

`Result.url` moved to this form as well, on **both** rungs. `check_bestbuy_api`
previously published `https://www.bestbuy.com/site/-/<sku>.p`, which is the form
this spike proved is refused: every Best Buy row on the served status page
carried a link that does not load.

### Does Best Buy sell the GO Plus +? — settled: no watch shipped

Re-checked against the two saved search pages from the first session. Every
product link they contain:

```
/product/go-50-gift-card-7000-pokecoins/JJG34YWLH6
/product/pokemon-go-50-gift-card-7000-pokecoins-digital/JJG34YWLWJ
/product/nintendo-switch-online-12-month-individual-membership-card/JJG34YK66Q
/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ   (+ -digital)
/product/pokemon-lets-go-eevee-nintendo-switch/J7GSL4G7L4     (+ -digital)
```

Gift cards, a membership card, and four Let's Go titles. **No GO Plus +
hardware.** And SKU `6577129`, which this repo used as Best Buy's GO Plus + SKU,
now has a direct disproof rather than an absence of evidence: searched on the
path that redirects a real SKU straight to its product page, it redirects
nowhere and matches nothing.

So **`config/products.yaml` ships a Best Buy control and no Best Buy GO Plus +
watch.** A watch on a product the retailer does not carry would sit at UNKNOWN
forever and raise a permanent health warning — the monitor reporting itself
broken for correctly observing that something is not there. The unverified SKU
was removed from `tests/test_retailers.py` at the same time; a fixture value
nobody has seen resolve should not be sitting in a test looking like a fact.

This does **not** cost the phase its retailer count: Best Buy is supported and
verified by a live control, which is what "supported" is defined as here. It
does mean Best Buy will never alert on the product this project was built for.

### Control product — confirmed and wired in

- **`Pokémon: Let's Go, Pikachu! - Nintendo Switch`**, SKU `6216393`
- Reached as `https://www.bestbuy.com/site/searchpage.jsp?st=6216393`
- Read live as `InStock`, `$59.99`, `seller: "Best Buy"` — twice, four hours
  apart, on two different URL forms.

It satisfies `config/products.yaml`'s control rule: first-party, an evergreen
catalogue title restocked routinely, not a console, and not subject to a
marketplace buy-box fight. `seller.name` is `"Best Buy"`, which is already in
`FIRST_PARTY["bestbuy"]`, so `_pick` finds it through the `named` branch and
`MARKETPLACES` needed no change.

The house-brand cable the rule would ordinarily point at is one of the
reproducibly-refused pages, and the mechanism behind that refusal is still
unexplained — so if this control starts reading UNKNOWN with a transport
failure rather than a parse failure, suspect the refusal before suspecting the
extractor. Reserve candidate: `Pokémon: Let's Go, Eevee! - Nintendo Switch`
(`/product/pokemon-lets-go-eevee-nintendo-switch/J7GSL4G7L4`), observed in the
same search results.

### Host facts, not repo facts

danserver has no system Chrome. These probes used the Chrome for Testing binary
at `/home/dan/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome` via
`BOTY_BROWSER_PATH`. That path is deliberately **not** in committed source — a
fresh clone resolves the browser from `BOTY_BROWSER_PATH` or `shutil.which`.

Chrome also could not start at all at first, and this had to be ruled out before
any verdict could be recorded: Ubuntu 24.04 ships
`kernel.apparmor_restrict_unprivileged_userns=1`, which denies unprivileged user
namespaces to binaries with no AppArmor profile, so an unpackaged Chrome cannot
build its sandbox and dumps core. That is a **host** problem and had nothing to
do with Best Buy. Worked around with `BOTY_BROWSER_NO_SANDBOX=1`, which is
opt-in per host and logs a warning, because this transport executes retailer
JavaScript and turning the sandbox off is a real reduction in isolation. The
better fixes, in order: a distro Chrome package, an AppArmor profile for the
binary, or a setuid `chrome_sandbox` helper.

---

## Nintendo (store.nintendo.com / nintendo.com/us/store)

**Probed:** 2026-08-02, from danserver over a residential connection.
**Transport:** `boty.fetch.get` — `curl_cffi` with `chrome` impersonation. Rung 1.
8 requests, spaced 12–20 s apart. No refusal, no rate limiting, no retry needed.

**Verdict: REACHABLE (rung 1)**

Nintendo's store is the cheapest retailer in this repo to support. It needs **no
new adapter code at all** — no extractor, no `_make_checker` branch, no
`MARKETPLACES` entry. `check_html` reads it as shipped; the only change is one
`FIRST_PARTY` line and two YAML watches. `02-PATTERNS.md` §1 predicted exactly
this, and it is worth stating plainly because the instinct on adding a retailer
is to write a class.

### What was observed

| Target | Result |
|---|---|
| `/us/store/products/nintendo-switch-pro-controller/` (a guessed slug) | HTTP **404**, 217,381 B, a genuine rendered `Whoops! - Nintendo Official Site` page. A wrong slug is a clean 404, not a refusal |
| `/us/store/hardware/accessories/` | Rendered, 584,321 B, `__NEXT_DATA__` carrying `urlKey` for every product in the category |
| `/us/store/products/hdmi-cable-104947/` | Rendered, 384,351 B, **1** `ld+json` block, `ldjson_offers` → 1 offer, `price=7.99`, `seller='Nintendo of America Inc.'`, `InStock` |
| `/robots.txt` | `User-agent: * / Allow: /`. Only named AI/scraper bots are disallowed; nothing here forbids what we do |
| `/us/store/sitemap.xml` | 36,530 `<loc>` entries — the store's full product catalogue, published deliberately |
| `/us/search/?q=pokemon%20go%20plus` | Renders, but results are client-side (Algolia). Not a usable discovery path at rung 1 — **the sitemap is** |
| `/us/store/products/pokemon-go-plus-plus-112387/` | Rendered, 416,346 B, `ldjson_offers` → 1 offer, `price=54.99`, `seller='Nintendo of America Inc.'`, **`OutOfStock`** |

### Does Nintendo sell the GO Plus +? — yes, and at MSRP

Unlike Best Buy, this is a positive finding rather than a disproof. The store
sitemap lists exactly two GO Plus + entries:

```
https://www.nintendo.com/us/store/products/pokemon-go-plus-plus-112387/
https://www.nintendo.com/us/store/products/pokemon-go-plus-plus-strap-119138/
```

The first is the hardware. It reads `OutOfStock` at **$54.99** — MSRP to the
cent, from the manufacturer, with no marketplace anywhere near it. That is the
single most credible restock signal this project has: a first-party listing that
cannot be held by a flipper and cannot be marked up.

### The structured data, and the first live confirmation of the IN-03 fix

```json
{"@context": "https://schema.org/", "@graph": [
  {"@type": ["Product"], "name": "Pokémon™ GO Plus+", "sku": "112387",
   "offers": {"@type": "Offer", "priceCurrency": "USD", "price": "54.99",
     "availability": "https://schema.org/OutOfStock",
     "seller": {"@type": "Organization", "name": "Nintendo of America Inc."}}}]}
```

Three things about that payload, each one a piece of existing machinery earning
its keep:

1. **`@type` is a compound list, `["Product"]`, not the plain string `"Product"`.**
   02-02 fixed IN-03 for precisely this case, and this is the first time it has
   been seen on a live retailer. Before that fix, `ldjson_offers` compared
   `@type` for exact equality, `saw_product` stayed False, and this page — a
   page carrying complete, correct, first-party availability and price — would
   have read as an unexplained UNKNOWN forever. The fix is not hypothetical
   cover for a shape nobody emits. It is what makes Nintendo readable at all.
2. **The Product node is inside an `@graph`,** which `parse._iter_nodes` already
   walks.
3. **`offers` is a single dict, not a list,** which `ldjson_offers` already
   normalises (`offers if isinstance(offers, list) else [offers]`).

`nextdata_offers` returns `None` on both pages — Nintendo has a `__NEXT_DATA__`
blob but not at Walmart's product path, and it is never reached because ld+json
answers first. **No new extractor was added**, and `_WALMART_PRODUCT_PATH` was
not generalised into a searcher.

### Seller attribution and marketplace status

`offers.seller.name` is the literal string `"Nintendo of America Inc."` on every
page seen, which lowercases to `nintendo of america inc.`. That is the value
that goes in `FIRST_PARTY["nintendo"]`.

**Nintendo's store has no marketplace.** There is no third-party seller surface,
no buy box, no "other sellers" section — Nintendo of America is the only party
who can sell on it. So `nintendo` goes in `FIRST_PARTY` and stays **out** of
`MARKETPLACES`, which also means `_pick`'s unattributed-offer fallback covers a
future page that omits the seller node, the same way it covers GameStop.

### Control product

- **`HDMI Cable (Nintendo Switch™/NES Classic Edition)`**, urlKey `hdmi-cable-104947`
- `https://www.nintendo.com/us/store/products/hdmi-cable-104947/`
- Read live as `InStock`, **$7.99**, `seller: Nintendo of America Inc.`

It satisfies `config/products.yaml`'s control rule on every clause: first-party
by construction, a replacement accessory restocked routinely, not a console, not
a limited drop, and not subject to a buy-box fight because there is no box to
fight over. Reserve candidate if it is ever discontinued: the AC adapter
(`ac-adapter-104900`), seen in the same category listing.

---

## Pokémon Center (pokemoncenter.com)

**Probed:** 2026-08-02, from danserver over a residential connection.
**Transports:** `boty.fetch.get` (rung 1, `curl_cffi`/`chrome`) and
`boty.browser._render` (rung 3, nodriver 0.50.3 driving Chrome for Testing 149
headless). 10 requests total, spaced 12–25 s apart with a 120 s backoff before
the final one. Stopped after the ladder was exhausted, not after a budget was.

**Verdict: REFUSED**

This is the finding that costs the phase its fifth retailer, and it is recorded
as a finding rather than worked around. Pokémon Center is Imperva/Incapsula-
protected **on product pages specifically**, and neither impersonated HTTP nor a
real headless browser gets past it.

### What was observed

| Target | Transport | Result |
|---|---|---|
| `/` (homepage) | rung 1 | **Rendered, 671,021 B**, title `Pokémon Center Official Site`, `__NEXT_DATA__` present, 0 `ld+json` |
| `/product/716E11935/detective-pikachu-returns` | rung 1, cold | **HTTP 403**, 858 B, `server: CloudFront`, a DataDome JS challenge (`var dd={'rt':'i','cid':…}`) |
| `/` then the same product, one `curl_cffi` Session, with `Referer` | rung 1, warmed | **HTTP 200**, 6,183 B, `Pardon Our Interruption` — Imperva. Session cookies (`visid_incap_2682446`, `nlbi_2682446`, `incap_ses_69_2682446`) were set by the homepage and did not help |
| `/product/715e10557/pokemon-go-plus` | rung 1, cold | **HTTP 200**, 6,183 B, `Pardon Our Interruption` again — byte-identical size, a different product |
| `/product/715e10557/pokemon-go-plus` | rung 3 | **Blocked**, rendered challenge matched `'request unsuccessful'`; `boty capture-fixture` refused to write it to disk |
| `/product/715e10557/pokemon-go-plus` | rung 3, after 120 s backoff | **Refused again**, 1,085 B, `_Incapsula_Resource` iframe, `distil_referrer`, no title, 0 `ld+json`, no `__NEXT_DATA__` |

Four separate refusals across two products, two URL forms, two transports and
two different WAF vendors. This is not rate limiting and not a one-off: the
homepage passed rung 1 **twice**, before and between the refusals, so this host
is not IP-banned. The wall is on `/product/*` and it is deliberate.

#### The same four refusals, in the anchored form rule 6 reads

Added 2026-08-03 by 03.1-03. **Nothing new is recorded here** — every status
code, byte count and matched phrase below is lifted from the table directly
above, which has been in this document since 2026-08-02. What changed is that
`scripts/evidence_check.py` rule 6 now requires a retailer recorded `REFUSED` to
carry at least one machine-readable observation, and Pokémon Center's were
prose. A finding a gate cannot read is a finding the next gate will not check.

Each is a single line, deliberately: rule 6's regex is line-anchored, so a
measurement that wraps onto the next line is a measurement the gate cannot see.

**Refusal observed (rung 1):** `/product/716E11935/detective-pikachu-returns` cold — **HTTP 403**, 858 B, `server: CloudFront`, a DataDome JS challenge (`var dd={'rt':'i','cid':…}`).

**Refusal observed (rung 1):** `/product/715e10557/pokemon-go-plus` cold — **HTTP 200**, 6,183 B, matched the `pardon our interruption` block phrase. Imperva. Byte-identical to the warmed attempt on a different product, which is what makes it a wall rather than a hiccup.

**Refusal observed (rung 3):** `/product/715e10557/pokemon-go-plus` rendered under headless Chrome — matched the `request unsuccessful` block phrase, and `boty capture-fixture` refused to write it to disk.

**Refusal observed (rung 3):** the same URL after a 120 s backoff — refused again, 1,085 B, an `_Incapsula_Resource` iframe, no title, zero `ld+json`, no `__NEXT_DATA__`.

Pokémon Center is **not** one of the `HARD_TWO`, so rule 6 asks it only for one
observation. It clears the higher bar those two are held to anyway — four
observations across both rungs, two of them at rung 3 — which is worth saying
out loud, because it is the standard the hard two's refusal branches were
written to and the only retailer in this file that has ever actually met it.

### The decisive reason is the Terms of Use, not the wall

Added 2026-08-02 after a desk review of prior art. This supersedes the technical
argument below as the *primary* reason, because a wall can fall and a written
prohibition does not.

Pokémon Center's Terms of Use prohibit "any data mining, robots or similar data
gathering or extraction methods designed to scrape or extract data from our
Service," and separately prohibit developing or using "any applications that
interact with our Services without our prior written consent." That language is
identical across the US, Canadian and Australian storefronts.

It is **broader than the robots.txt finding below.** robots.txt closes `/cortex`,
`/availabilities`, `/prices`, `/offers` and `/items` — which leaves the implicit
reading that `/product/` and `/category/` are fair game because they are not
disallowed. The ToU says otherwise, and read plainly it also covers the homepage
GET performed during this ladder walk.

So Pokémon Center is not "a wall we could not get past." It is a retailer that
has said no in writing. For a project whose entire positioning is that its
readings can be trusted, that distinction is the one that matters: a README
claiming we respect robots.txt while the code works around the ToU would be
worse than not supporting the retailer at all.

bot-y makes **no requests to pokemoncenter.com** — there is no watch, no
`FIRST_PARTY` entry, and no dispatch branch. The name survives only in comments.

### Why there is no rung 2

Pokémon Center publishes no documented public API, and its internal Elastic Path
Cortex endpoints are **explicitly forbidden by its own `robots.txt`**:

```
User-agent: *
Disallow: /availabilities
Disallow: /cortex
Disallow: /items
Disallow: /offers
Disallow: /prices
Disallow: /site/*/resourceapi/
```

Those are exactly the endpoints that would answer "is this in stock and at what
price". Reading them would mean taking data the retailer has asked us in writing
not to take, to power a monitor whose entire pitch is that its readings are
trustworthy. So rung 2 is not merely unavailable here — it is closed, and by the
retailer's own stated wishes. `/product/*` and `/sitemap.xml` are **not**
disallowed, which is why the probes above were fair game and the API was not.

### What was NOT done, and why

- **No Pokémon Center watch is in `config/products.yaml`.** The product exists
  (`/product/715e10557/pokemon-go-plus`, found via the allowed sitemap), so a
  watch would have looked plausible and made `boty check` report five retailers.
  It would also have been a detector that can never read anything, a control
  that can never go green, and a permanent health warning. The five-retailer
  criterion is not worth a retailer that does not work.
- **No fixture was captured.** `boty.fixtures.capture` propagates `Blocked`, and
  `boty/cli.py` printed *"refusing to save a challenge page as a fixture"* and
  exited 1 — the T-02-22 mitigation working live rather than in a test. A
  6 KB Imperva interstitial saved as `pokemoncenter/goplusplus.html` would have
  made a test suite assert against a bot wall while looking perfectly green.
- **No further escalation.** Rung 4 is the last rung. Beyond it are residential
  proxies and CAPTCHA-solving services, which are out of scope for this project
  by design and would not survive the "a fresh clone can do this" test anyway.

### The interstitial that HTTP 200 hides

Worth recording separately, because it is a defect this probe found in *our*
code rather than in Pokémon Center's:

Imperva serves `Pardon Our Interruption` with **HTTP 200**, and none of
`boty.fetch.BLOCK_PHRASES` matched it. So `get()` returned it as a successful
`Page`, and `_verdict_from_html` reported
`no structured stock data found (page shape changed?)` — a fail-safe UNKNOWN
with a **wrong reason attached**. The truthful reading is "we were blocked", and
the two send a reader to completely different places: one says re-capture the
fixture and see which assertions moved, the other says this retailer is turning
us away.

Nothing about this is Pokémon Center-specific — Imperva sits in front of a great
many retailers, and the next one probed will hit the same silent
misclassification. So it gets fixed rather than noted: `pardon our interruption`
and `incapsula incident` join `boty.fetch.BLOCK_PHRASES` in 02-04 task 2, pinned
by `tests/test_fetch.py` against the bytes recorded above.

### If somebody revisits this later

**Do not re-probe to see whether the wall weakened.** The technical observation
still stands — the homepage reads at rung 1, so the Imperva rule on `/product/*`
is narrower than a site-wide policy and could be re-scoped — but the ToU makes
that irrelevant. Periodically retrying a site whose terms forbid automated
interaction, waiting for enforcement to lapse, is exactly the behaviour this
project should not have. A clean 200 would no longer be sufficient on its own.

**What would actually change this: Pokémon Center publishing a signal.** An API,
a partner or affiliate product feed, or a per-SKU back-in-stock notification.
Any of those is a genuine rung 2 and would be worth wiring up the same
afternoon. None exists today.

### Prior art, reviewed 2026-08-02

~17 public projects claim to read Pokémon Center. Exactly **one** has a written
record of reading a per-product stock value, and it did so from a
**human-attended, non-headless Chrome session** where a person cleared the
DataDome challenge by hand before the profile could be reused — which is not a
thing an unattended monitor can do. Everything else reads the *catalog* (new
products, no availability), reads the *homepage* to detect a Queue-it waiting
room, or is abandoned with an empty state file.

The most heavily-resourced project found — 100 residential proxies, Bézier mouse
paths, up to 50 proxy rotations per check — reads strictly **less** than bot-y
already reads for free: it only determines whether a queue is live.

Two findings worth keeping:

- **Bloomreach (`core.dxpapi.com`) is a real, unwalled endpoint that returns
  catalog only** — no availability field, per its own docs and per the one
  project polling it every 5 minutes. It answers "a new product appeared,"
  never "this is back in stock." Wrong signal, and the ToU covers the data
  regardless of which host serves it.
- **Do not add `datadome` to `BLOCK_PHRASES`.** Real Pokémon Center product
  pages reference DataDome assets while serving genuine content; a project that
  tried it had to revert a false-positive block classification. If a DataDome
  tell is ever wanted, `captcha-delivery.com` together with the `var dd={`
  marker is the safer pair.

The strongest negative signal: four actively-maintained multi-retailer Pokémon
TCG monitors from 2026 were checked. Their configs cover Fantasia Cards, Card
Corner, Smyths, Argos, ASDA, pokemonstore.co.kr, Lazada and Norli. **None
includes pokemoncenter.com.** People building this exact thing, who want that
data most of all, are shipping without it.

---

## Target (target.com)

**Probed:** 2026-08-03, from danserver over a residential connection.
**Transport:** `curl` — a one-off, human-shaped read of two public policy pages
and two `robots.txt` files. **`boty.fetch.get` was never pointed at target.com,
no browser was ever started against it, and no product page was requested at any
point in this phase.**

**Verdict: REACHABLE (rung 3)**

**That verdict is the third answer this section has given, and everything behind
all three is still here.** Read the whole section rather than this line: it is a
record of a conclusion revised twice, on Dan's direction, with the observations
underneath it untouched each time.

- **Phase 3 (2026-08-03, earlier):** REFUSED, on Target's Terms & Conditions,
  with zero product-page requests ever made. Every quoted clause below stands.
- **03.1-02 first execution (2026-08-03):** still REFUSED, but the basis was
  rewritten from a written prohibition to a **measured technical wall** — Dan
  reversed the terms reasoning, and the probe then found that Target serves the
  page and withholds the data. Every byte count and zero-count below stands.
- **03.1-02 rewrite (2026-08-03, this verdict):** REACHABLE at **rung 3 with
  `dom` extraction**, after Dan answered the `robots.txt` question the probe
  escalated (`QUESTIONS.md` § 0d, option 2). Nothing above was retracted to get
  here. What changed is that a rung nobody had walked was walked.

**What REACHABLE does and does not mean here.** Target's *pages* are reachable
and always were — rung 1 returns HTTP 200 with no challenge. What was never
reachable is Target's *stock data*, at rung 1 or rung 2. It is reachable at rung
3 only in a specific and lossy sense: a browser renders the page, Target's own
JavaScript fetches the numbers from hosts that publish `Disallow: /`, and bot-y
reads the resulting **add-to-cart button**. There is no structured feed behind
that reading.

**So this is the least confident reading this project publishes, and the matrix
says so.** Rung 3 + `dom`, `degraded=True` on every result, and a `[dom]` tag in
`boty check`. A Target reskin breaks this silently — no error, no exception,
just a control that stops reading — which is why Target is registered
**control-only** and why mutation M8 exists.

**Target is control-only, and that is a disproof rather than a shortfall.**
Target delisted the Pokémon GO Plus +: TCIN `88714054` served HTTP 200 as
recently as 2025-05-09 and 404s now. There is no product watch to add.

Two anchored `**Refusal observed (rung N):**` lines survive further down this
section. **They are historical, not current**, and they are left in place
deliberately rather than deleted — they are the measurements this verdict was
revised *through*. Note especially that the rung-1 line's own body says *"not a
block — **HTTP 200**"*: it records that Target did **not** refuse the request,
only the data. Neither line describes the current state of this retailer.

### What was retrieved

| Requested | Result |
|---|---|
| `https://www.target.com/c/terms-conditions/-/N-4sr7p` | **HTTP 200**, 374,015 B, `text/html; charset=utf-8`. **The wrong document** — node `4sr7p` is the *Privacy Policy* (`"canonical_url":"/c/target-privacy-policy/-/N-4sr7p"`, `"seo_h1":"Target Privacy Policy"`), despite the `terms-conditions` slug in the requested path. Recorded rather than quietly dropped; the correct node id was then read out of this page's own `children` list instead of guessed a second time |
| `https://www.target.com/c/terms-conditions/-/N-4sr7l` | **HTTP 200**, 471,173 B, `text/html; charset=utf-8`, no redirect. `"seo_h1":"Terms & Conditions"`, `"canonical_url":"/c/terms-conditions/-/N-4sr7l"`. Document header reads `LAST UPDATED: April 15, 2026` |
| `https://www.target.com/robots.txt` | **HTTP 200**, 3,226 B, `text/plain`, 122 lines, **one** `User-agent` group |
| `https://redsky.target.com/robots.txt` | **HTTP 200**, 41 B, `text/plain;charset=UTF-8`. The whole body is three lines |

**Four requests in total, spaced ≥15 s apart, no retries, no refusals, and every
one of them HTTP 200.** Two to a public policy page, two to the files on the
internet whose entire purpose is to be fetched by an automated agent. **Zero to
a product page. Zero from bot-y.** The politeness budget for this plan was 12
requests; 4 were spent, all on documents, and the remaining 8 were not needed
because the first document settled it.

Note the first row: the URL `03-02-PLAN.md` names as the starting point,
`/c/terms-conditions/-/N-4sr7p`, serves Target's Privacy Policy. The Terms &
Conditions live one node over at `N-4sr7l`. Both are recorded because a future
reader following the plan's URL would otherwise quote the wrong document and
find no prohibition in it.

### The operative clauses, quoted in full

All from the Terms & Conditions at
`https://www.target.com/c/terms-conditions/-/N-4sr7l`, retrieved **2026-08-03**,
document header `LAST UPDATED: April 15, 2026`. Whole sentences are reproduced
so a future reader can judge their scope rather than trusting this document's
reading of them.

**1. The Introduction, which is what makes a bot a party to these terms at all:**

> BY ACCESSING OR OTHERWISE USING THE SITE YOU AGREE TO THESE TERMS &
> CONDITIONS. **Any person or entity who interacts with the Site through the use
> of crawlers, robots, browsers, data mining or extraction tools, or other
> functionality, whether such functionality is installed or placed by such person
> or entity or a third party, is considered to be using the Site.** If at any
> time you do not accept all of these Terms & Conditions, you must immediately
> stop using the Site.

That sentence is unusually direct and it forecloses the obvious objection. A
scraper does not click "I agree"; Target has written down that operating one *is*
using the Site, and using the Site *is* agreeing. There is no version of pointing
bot-y at target.com that is outside these terms.

**2. `Unlawful or Prohibited Uses` — three of the "YOU MAY NOT" bullets:**

> Whether on behalf of yourself or on behalf of any third party, YOU MAY NOT:
> Make any commercial use of the Site or its Content, including making any
> collection or use of any product listings, descriptions, prices or images; […]
> **Use or attempt to use any engine, software, tool, agent, data or other device
> or mechanism (including browsers, spiders, robots, avatars or intelligent
> agents) to navigate or search the Site other than the search engine and search
> agents provided by Target, generally publicly available browsers, or approved
> Agentic Commerce Agents;** […] **Make any use of data extraction, scraping,
> mining or other data gathering tools, or create a database by systematically
> downloading or storing Site content, or otherwise scrape, collect, store or use
> any Content, account information, product listings, descriptions, prices or
> images, except pursuant to the limited license granted by these Terms &
> Conditions;**

**3. The `Agentic Commerce and Delegated Access` section**, which is new since
anyone last looked at this file and which closes the one door a 2026 reader might
think had opened:

> The terms in this section apply if you expressly authorize an agent powered
> through AI ("Agentic Commerce Agent") to access and perform certain functions
> in your Target account on your behalf. **Only Agentic Commerce Agents expressly
> approved by you and by Target are considered Agentic Commerce Agents. Other
> automated or unauthorized agentic tools are expressly prohibited.**

### Reading those clauses honestly, including where they do not bite

Two of the three prohibitions have arguable edges, and this record is worth more
if it says so rather than stacking everything up as decisive.

- **The commercial-use bullet does not obviously reach bot-y.** It forbids
  "**any commercial use** of the Site or its Content, including making any
  collection or use of any product listings, descriptions, prices or images". A
  personal restock monitor is not commercial use, so that bullet is not the one
  that settles this. (Amazon's equivalent clause *is* decisive, because Amazon
  writes the listings-and-prices carve-out as an exclusion *from* the personal,
  non-commercial licence rather than as a commercial-use prohibition. The two
  read similarly and are structured differently.)
- **The navigation bullet has a carve-out that might cover rung 3.** It permits
  "generally publicly available browsers", and rung 3 drives a real, publicly
  available Chrome. A determined reading could put headless Chrome inside that
  carve-out — though the same bullet names "robots" and "intelligent agents" in
  its prohibition, and an unattended process polling a product page every five
  minutes is plainly the thing being described. Call it arguable rather than
  settled.

**The third bullet has no such edge, and it is the one that decides this.** It is
not qualified by commercial use, it names no permitted-tool carve-out, and it
prohibits four things bot-y does by definition:

1. "Make any use of **data extraction, scraping, mining or other data gathering
   tools**" — that is a description of this program.
2. "create a database by **systematically downloading or storing Site content**"
   — `boty.fixtures.capture` writes retailer HTML to disk; `state.json` stores a
   per-watch availability and price history.
3. "otherwise **scrape, collect, store or use any Content** […] **product
   listings, descriptions, prices or images**" — availability and price are the
   only two fields bot-y reads, and it stores both.
4. The verb "**use**" in that list is the widest of them. Even a read that
   persisted nothing at all would still be *using* a price.

**The `except pursuant to the limited license` carve-out closes rather than
opens.** The licence it points at is granted in the `License and Access` section
immediately above:

> Target grants you a limited license to access and make personal use of the Site
> and the Content for NONCOMMERCIAL PURPOSES ONLY and **only to the extent such
> use does not violate these Terms & Conditions including, without limitation,
> the prohibitions listed in the "UNLAWFUL OR PROHIBITED USES" section of these
> Terms & Conditions**. You may download, print and copy Content for personal,
> noncommercial purposes only, provided you do not modify or alter the Content in
> any way, delete or change any copyright or trademark notice, or violate these
> Terms & Conditions in any way.

So the exception is circular by construction: the prohibition permits what the
licence allows, and the licence allows nothing the prohibition forbids. The
circle closes against us. bot-y's use being personal and non-commercial gets it
past the *first* condition of that licence and straight into the second.

### robots.txt — permissive, and it disagrees with the Terms

The same shape as Amazon and Pokémon Center, and the disagreement is sharper here
than at either: reading `www.target.com/robots.txt` alone would have produced not
just a different answer but an *encouraging* one.

The file is 122 lines with exactly **one** `User-agent` group — `*`. There are no
named-bot blocks at all: no `GPTBot`, no `ClaudeBot`, no `Scrapy`, nothing of the
kind Amazon lists 99 of. The `Disallow` list is a long, specific set of legacy
WebSphere endpoints, checkout and account paths, and search/facet URLs:

```
Disallow: /s?
Disallow: /cart
Disallow: /account/
Disallow: /shop/
Disallow: /pl/
Disallow: /p/premium-registry
```

**The product-detail path `/p/` is not disallowed.** The only `/p/` rule in the
file is `/p/premium-registry`, and `/p/<slug>/-/A-<TCIN>` — the exact URL form a
stock read needs — carries no rule matching it anywhere in the group. Target goes
further and *publishes the map*:

```
Sitemap: https://www.target.com/sitemap_pdp-index.xml.gz
Sitemap: https://www.target.com/sitemap_keywords-index.xml.gz
Sitemap: https://www.target.com/sitemap_taxonomy-categories-index.xml.gz
Sitemap: https://www.target.com/sitemap_taxonomy-brand-index.xml.gz
Sitemap: https://www.target.com/sitemap_facet-categories-index.xml.gz
Sitemap: https://www.target.com/sitemap_stores-index.xml.gz
```

`sitemap_pdp-index.xml.gz` is a product-detail-page index — a sanctioned
discovery path of exactly the kind Nintendo publishes and Amazon does not, and
the very thing that would have solved the TCIN-discovery problem
`.planning/STATE.md` records Phase 2 stopping on.

**So robots.txt is materially broader than the Terms & Conditions, and the two
disagree.** robots.txt would permit fetching `/p/<slug>/-/A-<TCIN>`, and hands
you an index to find them with; the Terms forbid using data-gathering tools on
the Site and forbid collecting, storing or using prices at all. Where they
disagree, the Terms are the document Target says you agree to by operating a
crawler against the Site, and a narrower technical file does not license what the
broader written one refuses. Taking the `/p/` gap because robots.txt omits it,
while the Terms name prices explicitly, is precisely the "respects robots.txt
while working around the ToU" posture that
`.planning/phases/03-the-hard-two/03-CONTEXT.md` locks this project out of — and
it is the same call this repo already made for Amazon's `/dp/<ASIN>` gap eight
hours earlier.

### Rung 2 — RedSky, settled here rather than left to a ladder walk

`redsky.target.com` is Target's own internal aggregation API
(`/redsky_aggregations/v1/web/pdp_client_v1?tcin=…&key=…`). It is not a
documented public product, has no signup, no terms of service of its own and no
published contract. It is closed **four** separate ways, and the first one is
mechanical:

**1. Its `robots.txt` disallows the entire host, for every agent.** The whole
file, all 41 bytes of it:

```
User-agent: *
Crawl-delay: 1
Disallow: /
```

No `Allow`, no exceptions, no named groups. This is the same standard Pokémon
Center's `/cortex` endpoints were held to, and Target's version is broader than
Pokémon Center's — that file closed five specific paths, this one closes the
host. Reading it would mean taking data the retailer has asked in writing not to
take, to power a monitor whose entire pitch is that its readings are
trustworthy.

**2. The `key` parameter fails the fresh-clone rule.** `.planning/REQUIREMENTS.md`
requires a retailer's PRIMARY path to work for someone who clones this repo and
adds no credentials. RedSky's `key` is not issued to anybody: there is no
developer portal, no application, no approval. The only way to obtain one is to
lift the constant out of Target's own front-end JavaScript. That is not "a
credential a fresh clone cannot get" in the way Best Buy's API key or Amazon's
Partner Tag are — it is worse. Best Buy's key is a real credential this project
could hold and chose to document as optional; RedSky's is Target's internal
secret, and using it means presenting yourself to Target's API as Target's own
website. There is no reading under which that is sanctioned access.

**3. The Terms above cover it regardless of host.** They govern "the Target
website located at www.target.com **and all other sites, mobile sites, services,
applications, platforms and tools where these Terms & Conditions appear or are
linked** (collectively, the 'Site')", and the prohibition is on collecting prices
by any means, not on a particular hostname.

**4. It is CAPTCHA-gated in practice.** `.planning/STATE.md` records from earlier
work that RedSky answers with a CAPTCHA even when driven from a warmed cookie
session. That is a separate, technical fact and it belongs in the record — but it
is the least important of the four, because it is the only one that could change.
The other three cannot.

### The decision this leaves for the ladder walk

Written down explicitly, because the next step branches on it mechanically and a
reader should be able to check the branch was taken correctly.

**The Terms contain a written prohibition on automated access.** The bullet that
establishes it is quoted in full above and is not qualified by commercial use:
*"Make any use of data extraction, scraping, mining or other data gathering
tools, or create a database by systematically downloading or storing Site
content, or otherwise scrape, collect, store or use any Content, account
information, product listings, descriptions, prices or images…"*

So the verdict is `**Verdict: REFUSED**`, the primary reason is that clause, and
**no request may be made to any target.com product page at any rung** — not at
rung 1 to see whether Akamai answers, not at rung 3, not to discover a TCIN, and
not "just to record an observation". Rung 1 is closed by the Terms; rung 2 is
closed four ways above; rung 3 is closed by the same Terms as rung 1 and adds
nothing a prohibition can be argued out of. There is no rung left to walk.

### The ladder walk, and the fact that it did not happen

That branch was taken. **No rung was walked, because the branch above closed all
three of them before any transport work began.**

The request count for this retailer across the whole of Phase 3 is therefore
**4**, every one of them a policy document or a `robots.txt`, all listed in the
table at the top of this section. The plan's politeness budget was 12 requests at
≥15 s spacing with a 120 s backoff before any single retry and a hard stop after
two consecutive refusals. None of the retry machinery was reached: there were no
refusals, because there was nothing to be refused from. **`boty.fetch.get` was
never called with a target.com URL, `boty.browser.fetch_rendered` was never
called at all, and `boty capture-fixture` was never run.**

**Controls before and after.** There was no probing to bracket — the REFUSED
branch makes no product requests — but both runs are recorded anyway, the same
way `03-01` recorded them, because "we would have noticed" is not a control:

```
control check: PASS — 4/4 controls in stock
  in_stock      gamestop  CONTROL — PS5 console                $549.99  ld+json: InStock from GameStop
  in_stock      walmart   CONTROL — Great Value whole milk       $2.42  __NEXT_DATA__: IN_STOCK from Walmart.com
  in_stock      bestbuy   CONTROL — Pokémon Let's Go, Pikach    $59.99  ld+json: InStock from Best Buy
  in_stock      nintendo  CONTROL — Nintendo HDMI cable          $7.99  ld+json: InStock from Nintendo of America Inc.
```

Byte-identical before and after — two standalone runs under the service's own
`EnvironmentFile`, and a third inside `make verify` at the close of this plan.
The GameStop control needed one retry on the *first* run only
(`fetch failed: HTTP 403`, retried automatically and read `InStock`), which is
the script's ordinary backoff behaviour and not a Target finding; the second run
needed none. Dan's monitor was never at risk: no defended endpoint was touched.

**`BLOCK_PHRASES` was not exercised, and that is worth saying out loud.** Phase 2
added `sec-if-cpt-container` and `scf-akamai-protected-by` to
`boty.fetch.BLOCK_PHRASES` *specifically* because Akamai fronts Target and a
Target refusal at HTTP 200 would otherwise have surfaced as "no structured stock
data found (page shape changed?)". Those markers were re-verified against live
Kohl's bytes on 2026-08-03 and they remain correct — but this section provides
**no** evidence for or against them, because no Target page was ever fetched to
put them in front of. Their justification is still the Kohl's re-probe recorded
at the bottom of this file, and nothing here strengthens or weakens it.

### What was NOT done, and why

- **No product page was ever requested.** Not at rung 1, not at rung 3, not
  once. The Terms were read first precisely so this sentence could be written:
  **bot-y makes no requests to target.com.** Four `curl` requests to policy
  documents and `robots.txt`, and nothing else, ever.
- **No TCIN discovery was attempted**, even though robots.txt publishes the PDP
  sitemap that would have made it easy and even though this is the exact problem
  `.planning/STATE.md` records Phase 2 giving up on. Finding the GO Plus +'s TCIN
  would have been a satisfying answer to a question that stopped mattering the
  moment the Terms were read. Whether Target stocks the product is therefore
  **not established here** — and it does not need to be, because a watch could
  not ship either way. This is a deliberate non-finding, unlike Best Buy's, which
  is a disproof.
- **`FIRST_PARTY["target"]` was NOT widened**, and the live `offers.seller.name`
  string was not observed, because observing it would have required fetching a
  product page. See the note below on what that leaves in the code.
- **No fixture was captured**, so `tests/fixtures/target/` does not exist and the
  CR-02 identity-leak guard had nothing new to inspect. Target is Akamai-fronted,
  the same echo shape that froze this repo's public IP and EdgeScape geolocation
  into a committed fixture in Phase 2, so the safest number of rung-3 Target
  captures in a public repo is the one this plan produced.
- **No watch is in `config/products.yaml`.** No `retailer: target` entry, no
  control, no `check_html_browser`, and no new arm in `boty.cli._make_checker`.
- **`target` remains in `boty.retailers.MARKETPLACES`.** Target Plus is a real
  third-party marketplace; that entry is a statement about the retailer, not a
  claim to support it — the same call `03-01` made for `amazon`.

### The sharp edge left in the code, and why it is safe to leave

> **SUPERSEDED 2026-08-03 by the rung-3 walk at the end of this section.** The
> hazard described below was real and is now **closed**, by a different route
> than the one this subsection anticipated. It said the entry "must be replaced
> with the real `offers.seller.name` string before a control can go green" —
> there is no such string, at any rung, so that was impossible. What replaced it
> instead: `FIRST_PARTY['target']` is no longer a guess about Target's markup but
> a statement about **our own reader's output**, matched against the literal
> `parse.TARGET_FIRST_PARTY_SELLER` that `add_to_cart_offers` emits when a PDP
> carries no Target Plus partner block. The entry is also no longer dormant —
> a Target control watch now dispatches through it. Nothing below is retracted;
> the reasoning about `_pick`, `MARKETPLACES` and the confident-OUT_OF_STOCK
> failure mode is exactly why it was closed the way it was.

`boty/retailers.py:31` carries `"target": {"target"}` in `FIRST_PARTY` and
`:54` lists `target` in `MARKETPLACES`. That combination has a real hazard: if
Target's markup names its seller anything other than exactly `target` once
lowercased — `"Target Corporation"`, `"Target.com"` — then `_pick`'s `named` list
is empty, `unattributed` is forced empty by the `MARKETPLACES` membership, and
`_verdict_from_html` falls through to `:177` and returns a **confident
OUT_OF_STOCK** with detail `"N offer(s) via ld+json, none first-party"` on a page
it read perfectly.

That hazard is **unreachable in this tree**, because nothing dispatches a Target
watch: `Config.load` yields no watch with `retailer == 'target'`, so no code path
ever passes `"target"` to `_pick`. The entry is dormant, not live. It was left in
place rather than deleted for the same reason `amazon` stays in `MARKETPLACES` —
it records a true fact about the retailer — and removing it would have been a
change to `boty/retailers.py` in a plan whose whole finding is that no code
change is warranted.

If somebody ever does register Target, **that allow-list entry is a guess**,
never observed on a live page, and it must be replaced with the real
`offers.seller.name` string before a control can go green. Note that the failure
would be loud rather than silent: `boty.monitor.assess_health:78` fails any
retailer whose control does not read IN_STOCK, so seller-string drift on a Target
control reddens the `controls` stage and takes `make verify` non-zero within a
cycle. The control path is the drift detector, and it already works.

### Was Target reachable? — unknown, and deliberately so

> **SUPERSEDED TWICE, and it is now ANSWERED.** This subsection recorded a
> deliberate non-observation, which was the correct shape for a rung-4-by-terms
> finding. It has since been measured at every rung: rung 1 returns HTTP 200 with
> no challenge and no product data; rung 2 is closed in writing; **rung 3 renders
> the page and the add-to-cart control reads cleanly.** The verdict line at the
> top of this section is now `REACHABLE (rung 3)`. Nothing below is retracted —
> it was an honest statement of what had not been looked at, and the answer is
> now further down rather than here.

This section records no HTTP status from a product page, no byte count from one,
and no observation about Akamai, because none was collected. The two policy pages
and both `robots.txt` files returned clean HTTP 200s from `curl` with no
challenge, which says something about `www.target.com`'s posture toward a plain
document fetch and **nothing** about `/p/`. `.planning/STATE.md`'s note that
"product pages fetch clean but no valid `www` TCIN was ever found" is prior work,
not an observation from this phase, and it is not promoted to one here.

That gap is the correct shape for a rung-4-by-terms finding, and it is the same
shape as Amazon's. A REACHABLE verdict needs observations; a REFUSED-by-written-
prohibition verdict needs the prohibition, and manufacturing transport evidence
to make the section look fuller would mean making exactly the requests the
section's own conclusion says we should not make.

### If somebody revisits this later

> **SUPERSEDED 2026-08-03.** Somebody did revisit it, twice, on Dan's direction.
> The instruction below — *"Do not re-probe"* — no longer holds and has not held
> since the probe recorded further down. It is kept because its **second half is
> still live and still correct**: the list of things that would genuinely change
> this verdict, and the `Agentic Commerce` section being the one to watch, are
> unaffected by anything since. Target is now REACHABLE at rung 3, which is not
> the same as Target having changed its mind about anything.

**Do not re-probe.** There is nothing to re-probe: no wall was measured, so there
is no wall that could weaken. A clean HTTP 200 from `/p/<slug>/-/A-<TCIN>` would
prove only that we had been rude successfully. This is the same instruction the
Amazon section carries, for the same reason.

**What would actually change this** is Target saying something different: a
product-availability signal a non-commercial user can subscribe to; a RedSky tier
with published terms and an issued key; an "approved Agentic Commerce Agent"
programme that a personal restock monitor can join; or a revision of the
`Unlawful or Prohibited Uses` section that stops naming prices and data-gathering
tools. Any of those is a genuine rung 2 and would be worth wiring up the same
afternoon. The retrieval date and the `LAST UPDATED: April 15, 2026` header are
recorded so a future reader can tell at a glance whether the document they are
looking at is the one this verdict was based on.

**The `Agentic Commerce` section is the one to watch.** It is the newest text in
the document and it is the only place Target contemplates an automated agent
acting for a person at all. Today it is scoped to authenticated account actions —
carts, orders, returns — and it explicitly prohibits everything else. If that
scope ever widens to reading a public product page on a person's behalf, this
verdict should be revisited on purpose rather than by accident.

### Why this is the plan succeeding

The roadmap's criterion for this retailer is "Target reports stock, **or** the
support matrix records what was tried and why it failed." This is the second
branch. It is the branch that was under the most pressure to be the first one:
`03-01` settled Amazon at rung 4 the same day, so criterion 5 — five working
retailers — rested on Target alone, and a REACHABLE here was the only thing that
would have met it.

> **SUPERSEDED 2026-08-03 — and the reasoning here is worth keeping precisely
> because it was right at the time.** It argued that the honest branch was to
> record the shortfall rather than pad the count, under pressure to do the
> opposite. That was correct then and is not withdrawn. What changed is not the
> standard but the evidence: Target now has a **live, control-verified** reading
> and is registered on its merits, not to move a number. **The count is five** —
> gamestop, walmart, bestbuy, nintendo, target — so the sentence immediately
> below describes the tree before the rung-3 walk.
>
> This did **not** rescue the roadmap criterion the shortfall was about. Target
> still cannot watch the Pokémon GO Plus +, because Target delisted it, so
> criterion 1 stands UNMET — Dan's recorded call.

It is met by not being met. **The count stays at four** — gamestop, walmart,
bestbuy, nintendo — and phase criterion 5 is recorded unmet in `QUESTIONS.md`
rather than padded with a retailer whose own terms forbid the reading.
`scripts/evidence_check.py`, shipped by `03-01` for exactly this moment, is what
makes that shortfall mechanically impossible to hide later: rule 2 requires every
roadmap retailer to be configured *or* to carry `**Verdict: REFUSED**` in this
file, and rule 3 requires a short count to be consistent with the verdicts behind
it.

### 2026-08-03 — the conclusion above is revised at the maintainer's direction, and Target was probed for the first time

**Everything above this heading stands. Nothing in it is retracted, softened or
deleted** — every byte count, every quoted clause, the RedSky `Disallow: /`, the
robots.txt analysis. What changed is the *conclusion drawn from it*, and it was
changed by a decision rather than by a discovery.

**The decision is Dan's, taken 2026-08-03**, in his words:

> "bot-y is a bot for humans. To take the power back from other bots."

Phase 3 dropped Target on a reading of its Terms of Use without ever fetching a
product page. Dan reversed that. The consistency argument that settled it is
recorded one section down and is worth restating here: **Nintendo has the same
robots-permits / terms-forbid disagreement as Target** — § 6 of Nintendo's Terms
of Use bars "any robot … spider, crawler, scraper or other automated means" —
and Nintendo is this project's best retailer, the only one that lists the GO
Plus + at its $54.99 MSRP with no marketplace attached. The terms argument was
never applied consistently, and the honest fix was to stop applying it rather
than to drop Nintendo.

So the subsections above titled *"The decision this leaves for the ladder walk"*,
*"Was Target reachable? — unknown, and deliberately so"* and *"If somebody
revisits this later"* are **superseded by this one**. In particular the
instruction *"Do not re-probe"* no longer holds, and the sentence *"bot-y makes
no requests to target.com"* stopped being true at 2026-08-03. The ladder was
walked. What follows is what it found.

**The verdict line at the top of this section is unchanged, and that is the
finding.** It is no longer held up by the Terms of Use. It is held up by a
technical wall that was measured rather than read, and the wall is a shape this
project had not met before: **Target serves the product page and withholds the
product data.**

#### What was requested, and the politeness budget

**11 requests of the 12 budgeted, ≥ 15 s apart, no retries, no request to
`redsky.target.com` at any point.** `boty.fetch.get` (curl_cffi) was used for
every product page, so `BLOCK_PHRASES` was in front of Target's bytes each time.
The sitemap and `robots.txt` reads were plain `curl`.

| # | Requested | Result |
|---|---|---|
| 1 | `https://www.target.com/sitemap_pdp-index.xml.gz` | **HTTP 200**, 8,921 B, `application/xml`. Served **uncompressed** despite the `.gz` name. Names **110** PDP shards |
| 2 | `https://www.target.com/pdp/sitemap_20-0001.xml.gz` | **HTTP 200**, 8,550,438 B, 22,806 URLs, TCIN `1000000074` → `1009852919` |
| 3 | `https://www.target.com/robots.txt` | **HTTP 200**, 3,226 B, `text/plain`. Re-read to check the paths below; identical in substance to the Phase 3 reading |
| 4 | `https://www.target.com/sitemap_taxonomy-brand-index.xml.gz` | **HTTP 200**, 196 B. Names one shard |
| 5 | `https://www.target.com/b/sitemap_0001.xml.gz` | **HTTP 200**, 2,820,427 B, 37,504 brand URLs |
| 6 | `https://www.target.com/b/pokemon-go/-/N-q643lez1n7g` | **HTTP 200**, 138,984 B. **No `BLOCK_PHRASES` match.** `__NEXT_DATA__` present, **zero product TCINs** — the grid loads from RedSky |
| 7 | `https://www.target.com/pdp/sitemap_19-0003.xml.gz` | **HTTP 200**, 7,252,922 B, 15,328 URLs, TCIN `88337078` → `9999999350` |
| 8 | `https://www.target.com/p/pok-233-mon-go-plus/-/A-88714054` | **HTTP 404** |
| 9 | `https://www.target.com/p/pokemon-go-plus/-/A-88714054` | **HTTP 404** |
| 10 | `https://www.target.com/p/microfiber-dust-cloths-6pk-up-38-up-8482/-/A-90377926` | **HTTP 200**, 314,757 B. **No `BLOCK_PHRASES` match.** No offers of any kind — see below |
| 11 | `https://www.target.com/p/premium-plastic-spoons-48ct-up-38-up-8482/-/A-89685884` | **HTTP 200**, 318,690 B. Identical shape |

`robots.txt` confirms `/b/` and `/c/` carry no rule; the only `/p/` rule is
`/p/premium-registry`; `/pl/`, `/shop/` and `/s?` are disallowed and were not
requested. Every request above is to a path Target's own `robots.txt` permits.

**Controls before and after, both under the service `EnvironmentFile`:**

```
control check: PASS — 4/4 controls in stock      (before, 2026-08-03)
  in_stock  gamestop  CONTROL — PS5 console               $549.99  ld+json: InStock from GameStop
  in_stock  walmart   CONTROL — Great Value whole milk      $2.42  __NEXT_DATA__: IN_STOCK from Walmart.com
  in_stock  bestbuy   CONTROL — Pokémon Let's Go, Pikach   $59.99  ld+json: InStock from Best Buy
  in_stock  nintendo  CONTROL — Nintendo HDMI cable         $7.99  ld+json: InStock from Nintendo of America Inc.

control check: PASS — 4/4 controls in stock      (after, byte-identical)
```

No retries were needed on either run. Dan's monitor was never at risk.

#### How the GO Plus + TCIN was found — and the sitemap is not the index it looks like

The PDP sitemap was expected to answer the TCIN-discovery problem Phase 2
abandoned Target over. **It cannot, and the reason is structural rather than a
matter of spending more requests.**

The 110 shards are sorted by TCIN *as a string*, in **two independent runs**:
shard `20-0001` opens at the lexicographic minimum (`1000000074`) while shard
`19-0003` closes at the lexicographic maximum (`9999999350`). So prefixes `00`–`19`
are one full-range sorted partition and `20`–`39` are another. That ordering is
useful for looking a **known** TCIN up and useless for the opposite job: a search
by product *slug* has no locality at all, so finding one product by name means
grepping all 110 shards — roughly 900 MB. Two shards were fetched and grepped for
`go-plus` and `pokemon-go`; both came back empty, which under this structure is
uninformative rather than a disproof.

The brand sitemap looked like a shortcut and was not one:
`https://www.target.com/b/pokemon-go/-/N-q643lez1n7g` exists and reads cleanly at
rung 1, but its product grid is client-side and carries no TCINs (request 6).

**The public-source fallback was attempted and every general search engine
refused it**, which is worth recording because it is the same wall this repo hit
at GameStop and Walmart in `03.1-01`, from the same host:

| Source | Result |
|---|---|
| `html.duckduckgo.com` / `lite.duckduckgo.com` | HTTP **202** challenge |
| `ecosia.org` | HTTP **403** |
| `search.yahoo.com` | HTTP **500** |
| `reddit.com/search.json` | HTTP **403** |
| 5 SearXNG instances | 1 anti-bot interstitial, 4 × HTTP **429** |
| Bing, Google, DuckDuckGo via headless Chrome | CAPTCHA on all three ("Please solve the challenge below", "Our systems have detected unusual traffic") |

**What worked was the Internet Archive's CDX index** —
`web.archive.org/cdx/search/cdx`, a public index that exists to be queried and
that costs Target nothing. A prefix scan of `www.target.com/p/pok` filtered to
`go-plus` returns exactly two products, and it also revealed Target's slug
encoding: **`é` is written `-233-`**, so the GO Plus + slug is
`pok-233-mon-go-plus` and no guess at `pokemon-go-plus-plus` would ever have hit
it.

```
https://www.target.com/p/pok-233-mon-go-plus/-/A-88714054
https://www.target.com/p/pokemon-go-plus/-/A-52162697
```

The archived snapshot of the first, `20230522181904`, carries
`<title>Pokémon Go Plus + : Target</title>`. **TCIN 88714054 is the Pokémon GO
Plus +**, settled by observation rather than inference. `52162697` is the 2016
original device.

#### Does Target list the Pokémon GO Plus +? — no, not any more, and this is a disproof

**It did, and it does not.** TCIN 88714054 was archived returning HTTP 200 as
recently as **2025-05-09**. Today both URL forms answer **HTTP 404** (requests 8
and 9), and the TCIN appears in neither PDP shard searched — consistent with a
delisted product being dropped from the sitemap. The 2016 device's TCIN
(`52162697`) 404s as well.

This is the Best Buy shape — a **disproof**, not the "deliberate non-finding" the
subsection above recorded — and it means that even a Target adapter would have
had nothing to point at the product this project exists to watch. It changes only
whether a GO Plus + watch could ship. It is **not** the reason Target stays
unregistered.

#### The wall: Target serves the page and withholds the data

This is the load-bearing observation of this probe and it was not the outcome the
plan expected.

Both live control candidates (requests 10 and 11) returned a **complete, correct,
unchallenged product page**: HTTP 200, ~315 KB, the right `<title>`, and **no
`BLOCK_PHRASES` entry matched** — not the Akamai markers Phase 2 added
*specifically because Akamai fronts Target*, not Imperva, nothing. Target did not
refuse the request and did not classify us as one to refuse: the page's own
`__NEXT_DATA__` carries `"isBot": false` and `"isAiAgent": false`.

And there is nothing on the page to read:

```
boty.parse.ldjson_offers(html)   -> None
boty.parse.nextdata_offers(html) -> None
```

Measured across the whole 314,757-byte document:

| Signal | Occurrences |
|---|---|
| `application/ld+json` | **0** |
| `schema.org` | **0** |
| `"price"` | **0** |
| `availability` (any case) | **0** |
| `"seller"` | **0** |
| `InStock` / `OutOfStock` / `current_retail` | **0** |
| `<meta property="og:type" content="product">` | 1 — the only product metadata on the page |

`__NEXT_DATA__` is present and large (137,816 B) and carries page scaffolding and
RedSky endpoint configuration, not product state. The price module ships as an
empty hole:

```json
{"module_type": "ProductDetailPrice", "version": 0, "module_data": {}}
```

```html
<div data-module-type="ProductDetailPrice">
  <div data-test="price-module-placeholder"></div>
</div>
```

and Target's own flag says so out loud, on both pages:

```json
"isProductDetailServerSideRenderPriceEnabled": false
```

**That flag is the reason this was probed twice.** A feature flag can be
cohort-based, and a cohort-based wall would fall on a retry — so a second,
unrelated PDP was fetched (request 11). Same flag, same empty placeholder, same
zero counts. Two archived snapshots, from **2023-05** and **2025-05**, carry no
`application/ld+json` either. The wall is structural and long-standing, not a
cohort we happened to land in.

**So `_verdict_from_html` would read this page perfectly and return
`UNKNOWN — "no structured stock data found (page shape changed?)"`, forever.**
That is the UNKNOWN contract working exactly as designed; it is also a detector
that can never detect.

#### Why there is no rung left, and what is being asked of the maintainer

- **Rung 1 is open and empty.** The page is permitted by `robots.txt`, is served
  without a challenge, and contains no price, no availability and no seller.
- **Rung 2 (RedSky) is unchanged.** `redsky.target.com/robots.txt` is 41 bytes of
  `Disallow: /` for every agent. **No request was made to that host at any point
  in this probe.**
- **Rung 3 was not attempted, and that is a decision rather than an omission.** A
  headless browser would render the numbers — by executing Target's JavaScript,
  whose entire job on this page is to call `redsky.target.com`. Reaching the data
  through rung 3 means causing exactly the requests rung 2 is closed over. This
  project respects `robots.txt` — it is the standard it applied to Pokémon
  Center's `/cortex` endpoints — so that path is closed by the same rule, and
  `03.1-02-PLAN.md` forbids it in terms.

**This is where the plan hands the question back.** Dan's 2026-08-03 decision
settled the *Terms of Use*: a written prohibition is a fact to state, not an
instruction this project takes. It did not settle `robots.txt`, and this is a
`robots.txt` question — a different one, and the only remaining route to Target's
stock data. It is recorded in `QUESTIONS.md` rather than answered here.

**Refusal observed (rung 1):** not a block — **HTTP 200**, 314,757 B and 318,690 B
on two unrelated PDPs, **no `BLOCK_PHRASES` match**, `"isBot": false`. What was
refused is the *data*, not the request: zero `application/ld+json`, zero
`"price"`, zero `availability`, zero `"seller"`, an empty
`ProductDetailPrice` module and `isProductDetailServerSideRenderPriceEnabled: false`.

**Refusal observed (rung 2):** `redsky.target.com/robots.txt` — 41 B,
`User-agent: *` / `Disallow: /`. Closed by the retailer in writing to every
agent. Not requested.

**Rung 3 not attempted (recorded as a non-observation, not a refusal):** a
rendered page reaches the data only by making the rung-2 requests through a
browser. Closed by this project's own `robots.txt` rule, not by anything Target
did to us. Nobody has measured whether Target would serve it.

> **ANSWERED 2026-08-03 — this non-observation is no longer one.** Dan settled
> the `robots.txt` question it was escalating (`QUESTIONS.md` § 0d, option 2),
> rung 3 was then walked, and **Target serves it**: HTTP 200 to a headless
> browser, no `BLOCK_PHRASES` match on any of three rendered pages, and a
> readable add-to-cart control. The measurement is at the end of this section.
> Recording it as a non-observation rather than inventing a refusal is what made
> it answerable later, which is the whole argument for the distinction.

#### What this leaves in the code, unchanged and still a guess

> **CLOSED 2026-08-03 by the rung-3 walk below.** The diagnosis here was exact
> and it is what made the fix possible: the guess could not be replaced with a
> live `offers.seller.name`, because no such string exists at any rung. So it was
> replaced with something else — see *"The seller question, decided"* at the end
> of this section. The two bullets below both still hold: the guess *was*
> unverifiable rather than merely unverified, and `target` *is* still in
> `MARKETPLACES`. Only the words "unchanged" and "still dormant" have expired.

**`FIRST_PARTY["target"] = {"target"}` was NOT widened, and it could not be.**
The whole point of this probe was to replace that guess with the literal
`offers.seller.name` off a live page — and **Target's pages carry no
`offers.seller.name` at all**, at any rung this project will use. The hazard the
subsection above describes is therefore intact and still dormant: nothing
dispatches a Target watch, so nothing passes `"target"` to `_pick`.

Two things follow, and they are the useful ones:

- **The guess is now known to be unverifiable rather than merely unverified.** Any
  future plan that registers Target must obtain that string from whatever
  transport it decides to use, and the answer cannot come from `/p/` HTML.
- **`target` stays in `MARKETPLACES`.** Target Plus is a real third-party
  marketplace; that entry is a statement about the retailer, not a claim to
  support it.

**No watch, no control and no fixture were added**, and that is deliberate. A
`retailer: target` control would read UNKNOWN on every pass; `control_check.py`
and `monitor.assess_health` would redden `make verify` within a cycle, and the
support matrix would advertise a retailer the monitor cannot read. Registering
Target on the strength of a page that carries no stock data would be exactly the
"detector with nothing behind it" the matrix exists to prevent. **The retailer
count stays at four.**

### 2026-08-03 — rung 3 walked: what the render contacted, and what its DOM says

**Nothing above is retracted.** Every byte count, every quoted clause, the
`Disallow: /` on RedSky, the zero-structured-data measurement and the delisting
disproof all stand exactly as written. What this subsection adds is the one thing
the probe above deliberately did not collect: **observations from rung 3**, taken
after Dan answered `QUESTIONS.md` 0d.

The decision was recorded **before** anything was rendered, and it was already in
the tree when this work began — `QUESTIONS.md` § 0d, `ANSWERED 2026-08-03 (Dan)`,
commit `3558806`. So this was a re-read rather than an interlock, and it is worth
saying so plainly rather than presenting a settled question as a gate that could
have fired. Dan took **option 2**: a browser rendering a page a human would render
is not a crawler, so rung 3 is allowed even though the page's own XHRs land on a
disallowed host. What it does **not** license is `boty.fetch.get` or `curl`
against those hosts.

#### The hosts the rendered page contacted — measured, not inferred

**Method, stated because a robots.txt claim is worth exactly what its evidence is
worth:** one rendered load of the control candidate, then
`performance.getEntriesByType('resource')` evaluated **inside the page** and each
entry's URL mapped to a hostname. This is the browser's own record of the requests
it actually issued. It is the strong form of the measurement — *not* the fallback
of grepping the rendered HTML for hostnames it happens to mention, which would
have recorded intentions rather than requests.

**31 hosts, from one product page.** In full, because a list that summarises away
its own tail is not evidence:

```
www.target.com              api.target.com             carts.target.com
redsky.target.com           sapphire-api.target.com    assets.targetimg1.com
target.scene7.com           assets.adobedtm.com        cdn.attn.tv
target-us.attn.tv           events.attentivemobile.com cdn.speedcurve.com
client.px-cloud.net         ift.px-cloud.net           collector-pxgwpp4wus.px-cloud.net
dpm.demdex.net              target.demdex.net          cm.everesttech.net
edge.fullstory.com          rs.fullstory.com           edge.curalate.com
pub.doubleverify.com        vtrk.dv.tech               securepubads.g.doubleclick.net
cm.g.doubleclick.net        ep1.adtrafficquality.google ep2.adtrafficquality.google
www.google.com              22392fba1859b607494a8e560a71ac91.safeframe.googlesyndication.com
ponos.zeronaught.com        resources.digital-cloud.medallia.com
```

**Which of them publish `Disallow: /`** — checked directly, one `robots.txt` read
each:

| Host | `robots.txt` | How the page reached it |
|---|---|---|
| `redsky.target.com` | **`User-agent: * / Crawl-delay: 1 / Disallow: /`**, 41 B | `fetch`, `iframe` |
| `api.target.com` | **`User-agent: * / Disallow: /`**, 25 B | `fetch` |
| `sapphire-api.target.com` | **`User-agent: * / Disallow: /`**, 25 B | `fetch` |
| `carts.target.com` | HTTP **401**, no retrievable policy | `fetch` |
| `www.target.com` | permits `/p/`; only `/p/` rule is `/p/premium-registry` | the navigation itself |

**The measurement changed the answer's scope, which is the whole reason for taking
it.** 0d was answered naming `redsky.target.com` alone. Rendering one product page
in fact contacts **three** Target-owned hosts that publish `Disallow: /` for every
agent. The reasoning is unaffected — the distinction between *requesting an API*
and *rendering a page that requests it* applies identically to all three — but the
ruling is now on record as covering what it actually covers, and 0d has been
amended with this table.

**Stated plainly, because it is the sentence that matters:** `redsky.target.com`,
`api.target.com` and `sapphire-api.target.com` were contacted **by the browser
while rendering the page**, at our instruction, and by **no code in this
repository**. `boty.fetch.get` was never pointed at any of them and neither was
`curl`, except at their `robots.txt` files — which are the one resource on the
internet whose entire purpose is to be read by an automated agent.

The remaining 26 are third-party advertising, analytics and bot-detection vendors
Target chose. They are the same set a human visitor's browser loads, and bot-y
neither reads nor stores anything from them.

#### The add to cart control, verbatim

The extractor this plan builds keys on this element, so its exact markup is
recorded rather than described. From the control candidate, in stock:

```html
<button class="styles_btn__1hjpW styles_ndsButton__XOOOH styles_md__Yc3tr styles_filled___MOAP styles_fullWidth__8m0Wc"
        type="button"
        aria-label="Add to cart for Microfiber Dust Cloths - 6pk - up&amp;up™: Reusable, Hanging Loop"
        data-test="orderPickupButton"
        id="addToCartButtonOrTextIdFor90377926">Add to cart</button>
```

- **Tag:** `button`. **Visible text:** `Add to cart`. **Not disabled.**
- **The stable anchor is the `id`**, which is `addToCartButtonOrTextIdFor` + the
  TCIN.
- **`data-test` is NOT stable and must not be keyed on.** Three pages, three
  values: `orderPickupButton` on the control, `shippingButton` on a
  ship-only item, and **no `data-test` attribute at all** on the out-of-stock
  page. An extractor anchored on `data-test` would have read the out-of-stock
  page as "no control found".
- The id name is Target's own and it is a warning label: `addToCartButtonOrText`.
  Target considers this slot capable of rendering **text** instead of a button.

#### What an unavailable item renders — the question the extractor's honesty depends on

**Target keeps the button and disables it.** Observed live, on
`/p/200-pcs-2-3-easter-printed-plastic-eggs-…/-/A-90984792`, an item Target's own
variation chip labels `Count, 200  - Out of Stock`:

```html
<button class="styles_btn__1hjpW styles_ndsButton__XOOOH styles_md__Yc3tr styles_filled___MOAP styles_fullWidth__8m0Wc"
        type="button"
        aria-label="Add to cart for Joyfy 200 Pcs Easter Eggs, 2.4'' Plastic Printed Easter Eggs for Easter Hunt, Basket Easter Stuffers Fillable, Basket Easter Stuffer Toy"
        disabled=""
        id="addToCartButtonOrTextIdFor90984792">Add to cart</button>
```

Same tag, same id prefix, **same visible text** — and `disabled=""`. The text does
**not** change to "Out of stock" or "Sold out"; neither phrase appears anywhere on
the page. So the availability signal is the `disabled` attribute and nothing else,
and matching on button text alone would report an out-of-stock item as buyable.

**This is the branch that lets the extractor be honest.** Because the control is
*present-and-disabled* when unavailable, its **absence means the render failed**,
not that the item is out of stock. The reader therefore returns `None` — UNKNOWN —
when it finds no control, and there is no ambiguity to trade off. Had Target
removed the button instead, absence would have been indistinguishable from a
broken render and the reader would have needed a separate positive out-of-stock
marker to say anything at all.

The out-of-stock page also carries a price (`$25.99`), so price and availability
are independent signals and an unreadable one does not block the other.

#### Price, and the Target Plus partner block

**Price** is `data-test="product-price"`, inside `data-test="@web/Price/PriceFull"`:

```html
<span class="styles_currentPriceFontSize__Xps20  " data-test="product-price">$12.59</span>
```

It appears twice on an in-stock page — the main module and the sticky
add-to-cart bar — with the same value.

**The partner block exists, it is unambiguous, and this is what keeps a Target
Plus reseller from reading as first-party.** On a partner-sold item:

```html
<a aria-label="Sold &amp; shipped by Joyin. View partner details"
   data-test="targetPlusExtraInfoSection"
   href="/sp/joyin/-/N-10006960">
  …
  <span class="…PrimaryText…">Sold &amp; shipped by </span>
  <span class="…Subtext…">Joyin</span>
</a>
```

Note the exact wording: **"Sold & shipped by"**, with an ampersand, not "Sold and
shipped by". The partner name is available three ways — the `aria-label`, the
`Subtext` span, and the `/sp/<partner>/-/N-…` href — which is useful redundancy
for an extractor that has to survive a reskin.

**On the first-party control page, `targetPlusExtraInfoSection` occurs zero
times**, as do the strings `Sold & shipped by`, `Sold by`, `shipped by` and
`Target Plus`. So **absence of the partner block is what a Target-sold item looks
like**, and that absence is what the reader treats as first-party. That claim is
now an observation rather than an assumption, and it is what
`FIRST_PARTY['target']` means from here on.

#### Requests spent

**Rendered loads of `www.target.com/p/…`: 3 of the 4 budgeted**, all ≥ 30 s apart,
no retries — the control candidate (`A-90377926`), a ship-only partner item
(`A-1001649986`, which Target redirected to `A-90984669`), and the out-of-stock
sibling (`A-90984792`). The fourth is reserved for the fixture capture. One
further rendered load went to a `/b/` brand page rather than a `/p/` PDP; its grid
did not hydrate and it yielded nothing, and it is recorded rather than dropped.

**Rung-1 requests: 1 of the 4 budgeted** — `sitemap_20-0001.xml.gz` (HTTP 200,
8,550,438 B, 22,806 URLs), fetched to find candidate slugs without touching the
`/s?` search paths `robots.txt` disallows. Two `web.archive.org` CDX prefix queries
were attempted first and returned nothing; they cost Target nothing.

Four `robots.txt` reads, counted separately and listed in the table above. **Zero
requests from this repo to `redsky.target.com`, `api.target.com` or
`sapphire-api.target.com` other than their `robots.txt`.**

**Controls, before:**

```
control check: PASS — 4/4 controls in stock
  in_stock  gamestop  CONTROL — PS5 console               $549.99  ld+json: InStock from GameStop
  in_stock  walmart   CONTROL — Great Value whole milk      $2.42  __NEXT_DATA__: IN_STOCK from Walmart.com
  in_stock  bestbuy   CONTROL — Pokémon Let's Go, Pikach   $59.99  ld+json: InStock from Best Buy
  in_stock  nintendo  CONTROL — Nintendo HDMI cable         $7.99  ld+json: InStock from Nintendo of America Inc.
```

run under the service's own `EnvironmentFile`, exit 0, before the first render.
The after-run is recorded at the close of this plan's registration subsection.

**No `BLOCK_PHRASES` entry matched on any of the three rendered pages.** Target
served an ordinary page to a headless browser exactly as it served one to rung 1.

#### The seller question, decided

The probe established that `FIRST_PARTY["target"] = {"target"}` could not be
verified against Target's markup, because Target's markup has no seller name in
it. That is still true, and it is why the entry could not simply be "fixed".

**It is now a statement about our own reader's output rather than a guess about
Target's.** `parse.add_to_cart_offers` emits the literal
`parse.TARGET_FIRST_PARTY_SELLER` when a PDP carries no Target Plus partner
block, and `FIRST_PARTY['target']` is the matching half of that. The claim
underneath is checkable, and it was checked: `data-test="targetPlusExtraInfoSection"`
and every wording of "sold by" occur **zero** times on the first-party control
page, and unmissably on a partner-sold one.

`target` **stays in `MARKETPLACES`**, which is not redundant. Removing it would
re-enable `_pick`'s unattributed-offer fallback and let a Target Plus reseller
listing hold the verdict — the flipper case the first-party filter exists for. A
partner block whose name cannot be read yields `seller=None`, which on a
marketplace is UNKNOWN. Both directions fail away from first-party.

#### The fixture, and what had to be cut out of it before it could be committed

**This is the part of the plan that came closest to repeating the incident that
destroyed this repo**, and it is recorded in full because the near-miss is more
useful than the outcome.

`tests/fixtures/target/control-dust-cloths.html` is the control page captured at
rung 3. The raw capture carried, all of it frozen for anyone who cloned the repo:

- a per-session `visitor_id` Target minted for this render on this host;
- an OAuth-shaped `refreshToken`;
- Target's RedSky `key` constant — the very constant this project refused to lift
  when it closed rung 2, so publishing it would have been inconsistent as well as
  unkind;
- Akamai's geolocation of this host, as `"zipCode"`, `"latitude"`, `"longitude"`
  and `"state"`;
- the **five nearest Target stores, with street addresses and phone numbers**,
  and the store name rendered as visible page text.

**The automated guard caught none of it.** `test_no_fixture_leaks_the_capturing_hosts_identity`
knew EdgeScape's `lat=` / `zip=` query form; Target writes JSON keys. It passed.
That is the failure mode the plan warned about in the abstract — *"the automated
guard only knows the markers it was taught"* — occurring for real, and it is why
the by-hand grep is not optional.

**Redaction:** every `<script>` body was emptied. A DOM reader needs element
markup, not the retailer's hydration state, so this costs the fixture nothing it
is used for and removes the entire session-and-identity class in one move — the
file went from 348 KB to 157 KB. The ZIP and store name that render as visible
markup were replaced separately. The fixture still reads IN_STOCK at $12.59 with
`seller="target"`, which is the property it exists to pin.

**The guard was then widened** to match on semantics rather than on one CDN's
spelling: coordinates, postal codes, street addresses, phone numbers, ZIP+4 and
session/visitor tokens, in JSON form. Applied to the raw capture it now reports
six leaks. **Applied to the fixtures already in the repo it found four more** —
`walmart/goplusplus.html` and `walmart/milk-control.html` carried postal code
`00000`, which is this host's own geolocation and had been public since Phase 2,
and both Best Buy fixtures carried session visitor ids. All four were redacted in
the same commit. Those are Walmart and Best Buy fixtures, found by a Target
change; the leak class is the browser rung's, not any one retailer's.

#### Registration

- `config/products.yaml` gains **one** `retailer: target` watch, a control, and
  **no** GO Plus + watch — Target delisted the product.
- `boty/cli.py` `_make_checker` dispatches a `target` watch to
  `check_target_browser`. `scripts/control_check.py` builds its checker through
  the same function, so the gate and the monitor cannot route differently.
- Every Target `Result` carries `rung=browser`, `extraction=dom` and therefore
  `degraded=true`, on every path including the error paths and including the one
  where the render succeeded and every reader came back empty — which is what a
  broken render looks like, and which would otherwise have published as
  `structured`.

**Controls after registration, under the service's own `EnvironmentFile`:**

```
control check: 5 control(s), live
  in_stock      gamestop  CONTROL — PS5 console                $549.99  ld+json: InStock from GameStop
  in_stock      walmart   CONTROL — Great Value whole milk       $2.42  __NEXT_DATA__: IN_STOCK from Walmart.com
  in_stock      bestbuy   CONTROL — Pokémon Let's Go, Pikach    $59.99  ld+json: InStock from Best Buy
  in_stock      nintendo  CONTROL — Nintendo HDMI cable          $7.99  ld+json: InStock from Nintendo of America Inc.
  in_stock      target    CONTROL — up&up microfiber dust cl    $12.59  add-to-cart control: add-to-cart enabled from target
control check: PASS — 5/5 controls in stock
```

and the same reading through `boty check`, which is where the two axes become
visible to a reader rather than only to the gate:

```
● target    CONTROL — up&up microfiber dus$   12.59  add-to-cart control: add-to-cart enabled from target [control] [degraded] [dom]
```

`served/boty/status.json` carries `"rung": "browser"`, `"extraction": "dom"` and
`"degraded": true` for that watch, with `healthy: true` and a full pass in
**40.1 s** against REQ-08's 120 s budget — 11 watches across 5 retailers, two of
them now on the browser rung.

**The retailer count is five.** It is five because Target reads, not to make the
number — and the roadmap criterion the shortfall was really about (Target reports
stock *for the GO Plus +*) stands UNMET regardless, because Target no longer
lists the product.

---

## What was built on both of these (2026-08-02, 02-04 tasks 2 and 3)

### Nintendo — shipped, and the diff is the finding

One line in `FIRST_PARTY` and two watches in `config/products.yaml`. That is the
whole of it: no extractor, no `_make_checker` branch, no `MARKETPLACES` entry,
no change to `boty/parse.py` at all. `nextdata_offers` was not generalised and
`_WALMART_PRODUCT_PATH` was not touched.

Confirmed live, with `boty.service` stopped:

```
○ nintendo  Pokémon GO Plus +             $   54.99  ld+json: OutOfStock from Nintendo of America Inc.
● nintendo  CONTROL — Nintendo HDMI cable $    7.99  ld+json: InStock from Nintendo of America Inc. [control]
```

`served/boty/status.json` records `"rung": "tls"` and `"degraded": false` on both
rows — rung 1, no credentials, no browser, nothing added to the systemd unit's
`EnvironmentFile`. That last point is deliberate: 02-03 shipped a green that
depended on `BOTY_BROWSER_PATH` being exported in an interactive shell, and the
service, which starts with almost no environment, paged half an hour later.
Nintendo needs no environment at all, and `make verify` was re-run under
`systemd-run --property=EnvironmentFile=…` to confirm that rather than assume it.

### Pokémon Center — not shipped, and not padded

No watch, no fixture, no `FIRST_PARTY` entry. The count is four.

Three separate mechanisms now make that shortfall hard to paper over later, and
they are worth naming because "we would notice" is not a control:

1. `scripts/control_check.py` computes `configured - verified` before any
   request, so a Pokémon Center watch with no control fails `make verify`
   offline.
2. `boty.monitor.assess_health` fails a retailer whose control cannot be read,
   so a watch *with* a control fails `healthy` instead.
3. `test_no_retailer_is_configured_without_a_page_we_have_actually_read` asserts
   that every configured retailer has a captured page under `tests/fixtures/`.
   `boty.fixtures.capture` only writes one after a live fetch that was not
   blocked — it refused outright here — so this is an offline, unfakeable claim
   that the site has been read at least once, and it is the one that fires
   fastest.

### The block-phrase fix this cost us, and what it is worth

`pardon our interruption` and `_incapsula_resource` are now in
`boty.fetch.BLOCK_PHRASES`, pinned by `tests/test_fetch.py` — including a
parameterised test that runs the shipped 380–420 KB product fixtures back
through `get()`, because a phrase broad enough to match a real page would report
a working retailer as blocked forever, which is a worse failure than the one the
list prevents.

Imperva sits in front of a great many retailers. Phase 3's two are prime
candidates, and when one of them refuses us it will now say so.

---

## Cross-cutting observation: a browser is not a strict upgrade

Not a verdict — GameStop is green on rung 1 and stays there — but it was
observed during this spike and it should stop somebody reaching for rung 3 as a
general escalation.

`https://www.gamestop.com/` fetched through the **same headless browser**
returned 5,674 bytes of `Attention Required! | Cloudflare` — *"Sorry, you have
been blocked. You are unable to access gamestop.com"*. The same site is read
successfully by rung 1 (`curl_cffi` impersonation) on every `make verify` run.

This is exactly the argument `boty/fetch.py:1-14` makes: a browser fixes the
JavaScript fingerprint and leaves the TLS one untouched, and a headless one
carries its own detectable footprint. Rung 3 is not "rung 1 but stronger" — for
at least one retailer we already support, it is strictly worse. Escalate to it
because a page genuinely needs JS or refuses HTTP at the connection layer, not
because a page failed once.

---

## Fifth-retailer search (2026-08-02) — candidates probed, none adopted

Phase 2 reached four retailers. Before deciding whether to add a fifth, seven
candidates were probed with the real adapter stack. **Nothing was adopted**, and
the reason is a market fact rather than a technical one:

**No fifth US retailer stocks the Pokémon GO Plus +.** The set is GameStop,
Walmart, Nintendo, Pokémon Center, Target and Amazon. Four are settled here; the
last two are Phase 3's. Every remaining candidate could only ever be a
*control-only* retailer like Best Buy — proving its own detector works while
being permanently unable to alert on the product this project exists for.

| Candidate | Verdict | Notes |
|---|---|---|
| Micro Center | **REACHABLE (rung 1)** | Config-only; `check_html` reads it as shipped. Verified twice 20 min apart. Availability is a real signal, not a constant — an RTX 5070 Ti read OUT_OF_STOCK at $999.99 in a session where six other products read IN_STOCK. Miss path (bogus id, search page) correctly yields UNKNOWN. Viable control: Inland HDMI cable, $9.99, house brand. **Not adopted — does not carry the GO Plus +.** |
| Adorama | REACHABLE (rung 1) | Explicit `seller: "Adorama"`; needs one `FIRST_PARTY` line. No evergreen control verified — the page read was `Discontinued` — so it would fail `control_check.py` today. |
| Kohl's | **REFUSED** | Akamai Bot Manager, behavioural challenge at HTTP 200. Found a defect in *our* code — see below. |
| B&H | REFUSED | Product pages 403 while search returns 200; robots disallows the search path. |
| Books-A-Million | REFUSED | Same shape as B&H. |
| Meijer | REFUSED | AEM SPA shell — rung 3 only. |
| Barnes & Noble | REFUSED (structural) | Now Shopify, but both product-URL forms 404 and product data is a bespoke Nuxt hydration array. |
| Newegg | not established | One 404 on a dead listing, then stopped. It is a marketplace anyway. |

### The Kohl's probe found a defect in our own code

Akamai Bot Manager serves a behavioural challenge at **HTTP 200** carrying no
human-readable "are you a robot" wording at all — the markers are structural.
`BLOCK_PHRASES` matched nothing, so the wall came back as an ordinary page and
the refusal surfaced as `no structured stock data found (page shape changed?)`,
pointing at our own parser for a problem that has nothing to do with it.

This is the third instance of one defect class: **a bot wall that returns 200.**
DataDome answered 403 (honest), but Imperva and now Akamai both answer 200.

Fixed the same way the Imperva case was, with both directions pinned:
`sec-if-cpt-container` (structural, durable) and `scf-akamai-protected-by`
(wording-dependent). `tests/test_fetch.py` asserts the challenge raises
`Blocked`, and the existing fixture-replay test asserts no shipped fixture
became newly "blocked" — an over-broad phrase would report a working retailer as
refused forever, which is worse than the bug it fixes.

#### Re-probe, 2026-08-03 — the markers verified against live bytes

The original probe's raw output was not saved, which made this the only entry in
this document with no URL, no byte count and no excerpt — and the test constant
`AKAMAI_CHALLENGE` was a hand-written reconstruction, so
`test_an_akamai_challenge_at_http_200_is_blocked_not_a_page` was asserting our
phrase against our own transcription of it. It would have passed identically if
a marker were a typo, and the phrase would then simply never fire in production:
Phase 3 walks the ladder at Target, Akamai-fronted, and the refusal would have
surfaced as "no structured stock data found (page shape changed?)" — someone
sent to debug a working extractor, which is the exact outcome the phrase was
added to prevent.

Re-probed to close that. **Both markers appear verbatim; neither needed
correcting.**

```
URL:     https://www.kohls.com/product/prd-4351200/nintendo-switch-2.jsp
STATUS:  200                      <- again: a wall, not an error
BYTES:   2,377 (2,499 on a second fetch — the nonce length varies)
CTYPE:   text/html
```

`sec-if-cpt-container` — 1 occurrence, at byte 213. The structural marker, and
the durable one: it is the id of the container Akamai's own challenge script
mounts into.

```html
...t3e30oTwx8?v=<REDACTED-NONCE>&amp;t=155122144"></script>
<div id="sec-if-cpt-container" role="main" style="display: none">
    <div class="behavioral-content">
```

`scf-akamai-protected-by` — 1 occurrence, at byte 849. Wording-dependent, hence
secondary. Note the space before `=`, which is why the phrase is the bare class
name and not `class="scf-akamai-protected-by"`:

```html
<div class="scf-akamai-logo-msg">
    <p class ="scf-akamai-protected-by">Powered and protected by</p>
</div>
```

The whole document is 2.4 KB of behavioural-challenge scaffolding with a
`display: none` container, an Akamai logo, and two script tags — no product
markup and no human-readable "are you a robot" copy anywhere, which is what makes
the structural markers the only thing that can catch it.

`tests/test_fetch.py`'s `AKAMAI_CHALLENGE` was replaced with these real bytes
(nonce redacted). The test is no longer self-referential: a typo in either
phrase now fails it, because the constant is the retailer's markup rather than
ours. Verified by deliberately corrupting a marker and watching it go red.

The bare vendor name `akamai` occurs 10 times in this body and would look like an
attractive third marker. It is not: `docs/retailer-evidence.md` records 33
occurrences of `akamai` on Best Buy's *working* search page and 15 in Walmart's
CSP header, so it would report both retailers as permanently blocked.

**This matters for Phase 3 more than for Kohl's.** Akamai fronts a large share of
US retail *including Target*. Without this, a Target refusal would have been
misattributed to our extractor, and someone would have spent the phase debugging
code that was working.

## Where robots.txt and the terms disagree, per retailer (REQ-13)

**Written 2026-08-03, Phase 3.1 plan 01.**

The `README.md` support matrix states a robots.txt position and a terms position
for every row, and this section is where those cells come from. REQ-13 exists
because at Target the two signals point in opposite directions — `robots.txt`
permits `/p/` and publishes a product-detail sitemap, while the Terms &
Conditions forbid using data-gathering tools on the Site at all — and a matrix
that printed only the resolved verdict would hide the very thing a reader needs
in order to reach their own conclusion from the same facts. So both are stated,
side by side, and where they conflict the row says so.

**The two `silent`s are not the same claim, and conflating them is the easiest
mistake to make here.**

- `robots.txt` is a **deny-list**. A path with no matching rule in the `*` group
  is *permitted* — silence there is permission, and that is why the matrix cell
  says `permits` for a path nothing disallows rather than hedging.
- A terms document is **prose**. Silence there is only the absence of a
  prohibition. It is not a licence, and it can be read as one only by someone who
  wants to.

**A fourth position exists, and it is the honest one: `unread`.** Three of the
four retailers approached for this section refused the policy document itself.
Writing `permits` or `silent` for a document nobody has read would be inventing
evidence to fill a column — the same failure the retailer count was gated against
in Phase 2, one table over. `unread` states what is actually known: which URL was
requested, on what date, and exactly how it was refused. Which rows may carry it
is pinned literally in `tests/test_support_matrix.py`
(`UNREAD_POSITIONS`), so it cannot spread to a new row without a deliberate edit
to a red test.

### The seven, at a glance

| Retailer | Path this repo fetches | robots.txt | Terms | Disagree? |
|---|---|---|---|---|
| GameStop | `/…/products/…` (PDP) | unread — `robots.txt` refused, HTTP 403 Cloudflare, 2026-08-03 | unread — not requested; the no-escalation rule moved on after the refusal above | no position to compare |
| Walmart | `/ip/<slug>/<id>` | permits — no rule in the `*` group matches `/ip/`, and item-page sitemaps are published, 2026-08-03 | unread — the terms URL served a `Robot or human?` challenge, 2026-08-03 | no position to compare |
| Best Buy | `/site/searchpage.jsp`, `/site/…/….p` | unread — connection-layer refusal, HTTP/2 `INTERNAL_ERROR`, 2026-08-03 | unread — same refusal, same day | no position to compare |
| Nintendo | `/us/store/products/<slug>/` | permits — `User-agent: * / Allow: /`, nothing matches the store path, store sitemap published, 2026-08-03 | forbids — § 6 bars "any robot … spider, crawler, scraper or other automated means", 2026-08-03 | **yes** |
| Pokémon Center | `/product/<id>/…` | permits — `/product/*` is explicitly not disallowed (the API paths are), Phase 2 | forbids — bars "any data mining, robots or similar data gathering or extraction methods", Phase 2 | **yes** |
| Target | `/p/<slug>/-/A-<TCIN>` | permits — the only `/p/` rule is `/p/premium-registry`; `sitemap_pdp-index.xml.gz` published, 2026-08-02 | forbids — `Unlawful or Prohibited Uses` bars data extraction and bars using prices at all, 2026-08-02 | **yes** |
| Amazon | `/dp/<ASIN>` | permits — no rule matches `/dp/<ASIN>`; `/dp/product-availability/` and `/gp/offer-listing/` ARE disallowed, 2026-08-02 | forbids — the licence excludes "any use of data mining, robots, or similar data gathering and extraction tools", 2026-08-02 | **yes** |

Amazon, Target and Pokémon Center are **cited, not re-derived**: their
`robots.txt` files and terms documents were read in Phase 2 and Phase 3, the
observations are recorded in their sections above, and nothing about them was
re-requested for this section. Phase 3.1 revises the *conclusions* drawn from
that evidence; the evidence itself stands.

Four rows disagree and three have no position to compare. **No row agrees** —
that is a fact about today's tree rather than a property of the rule, and
`tests/test_support_matrix.py` builds the agreeing case by corruption so the
`⚠ disagree` marker is watched coming off as well as going on.

### The row contract grew a fourth field on 2026-08-03: Extraction

**Written 2026-08-03, Phase 3.1 plan 05.** REQ-13's row contract was three
things — a rung, a `robots.txt` position and a terms position. It is now four.
Every README row also states **what was read out of the page**.

- **`structured`** — the retailer's own machine-readable feed: schema.org
  JSON-LD, a Next.js hydration payload, an API response. They maintain it
  because Google Shopping depends on it, so it rots slowly and it breaks
  loudly.
- **`dom`** — presentation markup. A button's text, a class name. It works, and
  **a reskin breaks it silently**: no error, no 403, no red control until the
  next control cycle. That is the exact failure mode this project exists to
  catch, so the cell is a warning rather than a label.
- **`—`** — a rung-4 retailer, where nothing is extracted because nothing is
  watched. Tied to the Rung cell in both directions by `_extraction_mismatch`
  in `tests/test_support_matrix.py`, so it is a claim rather than a blank.

**What motivated it is the Best Buy / Target contrast, and it is a real
distinction today's rung alone could not express.** Best Buy is rung 3 +
`structured`: a headless browser renders the page, and what is then read off it
is Best Buy's own schema.org feed — the retailer's own answer, obtained the hard
way. Target at rung 3 would be `dom`: its pages carry **zero** `ld+json`, zero
`"price"`, zero `availability` and zero `"seller"` (measured 2026-08-03,
recorded under `## Target` above), so the only thing left to read is the button
that renders. Both are "browser". One is the retailer telling us; the other is
us reading their layout.

`Result.degraded` widened in the same change, and this is the half worth
recording: it used to be derived from the rung alone, so a rung-1 DOM adapter —
cheap to write, and the most fragile thing this codebase could acquire — would
have been published as a first-class reading in `boty check`, on the status page
and in the support matrix. Mutation **M7** now reverts only that new disjunct
and the suite goes red, so the second half of the flag is proved load-bearing
rather than decorative.

### What was requested for this section, and what it cost

**Budget: 8 requests, ≥ 15 s apart, no retries, no escalation. 7 were spent**,
all at 16 s spacing, every one of them a `robots.txt` or a public policy
document. No product page was fetched, no fixture was captured, and no request
was repeated.

`scripts/control_check.py`, before the first request and after the last:

```
before  2026-08-03T10:32Z   control check: PASS — 4/4 controls in stock
after   2026-08-03T10:36Z   control check: PASS — 4/4 controls in stock
             retrying gamestop/CONTROL — PS5 console: fetch failed: HTTP 403
```

**Read that second line rather than the PASS on the end of it.** The GameStop
control needed a retry after a 403 — the first time this repo has recorded one
on a control — and it happened minutes after plain `curl` was refused 403 by
`gamestop.com/robots.txt` from the same host. The retry succeeded and the
monitor is fine, so this is a near miss and not a failure. It is also exactly the
cost the politeness budget exists to avoid: a blocked IP costs a working monitor,
and the retailer that pushed back is one of the four this repo actually watches.
It is the reason no eighth request was spent going back to GameStop for its
terms page.

**One deviation from the budget, recorded because it was a real slip.** The rule
is "on a refusal, record it and move to the next *retailer*". The refusal guard
was written against HTTP ≥ 400 and Best Buy refused at the transport layer with
no status code at all, so the guard did not fire and the Best Buy terms request
went out after the Best Buy `robots.txt` request had already been refused. One
request too many to a retailer that had just said no. It was not a retry — a
different document — and the total stayed under the cap, but the instruction was
"move on" and it did not.

### GameStop — `robots.txt` refused, terms not reached

| Request | Result |
|---|---|
| `https://www.gamestop.com/robots.txt` | **HTTP 403**, 4,572 B, `text/html`. Not a `robots.txt` at all: a Cloudflare interstitial titled `Attention Required! | Cloudflare` |
| GameStop terms of use | **not requested.** After the refusal above, the no-escalation rule moves to the next retailer |

The refusal page says, in full sentences:

> Sorry, you have been blocked
>
> You are unable to access gamestop.com
>
> This website is using a security service to protect itself from online attacks.
> The action you just performed triggered the security solution.

**Nothing else from that page is transcribed here, and that is deliberate.** The
body also carried a Cloudflare Ray ID and *this host's public IPv6 address*.
Committing either into a public repository is the leak that cost this project a
whole repository on 2026-08-03 (`03.1-CONTEXT.md`, "rung-3 captures leak the
capturing host's identity"), and a refusal page is a fixture by another name.
Only the vendor's own boilerplate is quoted.

Worth stating plainly, because it is the finding rather than a footnote:
**GameStop serves this repo product pages at rung 1 on every `make verify`, and
refused it the `robots.txt` that would say whether it wants to.** The difference
is the transport — `boty.fetch.get` replays a real Chrome TLS ClientHello via
`curl_cffi`, and plain `curl` does not. Re-requesting through the impersonating
transport would be escalation, which the phase forbids, so GameStop's position is
`unread` and stays there until somebody decides that question deliberately.

### Walmart — `robots.txt` read, terms refused behind an HTTP 200

| Request | Result |
|---|---|
| `https://www.walmart.com/robots.txt` | **HTTP 200**, 3,584 B, `text/plain`. One `*` group, ~60 `Disallow` lines, 40 `Sitemap:` lines |
| `https://www.walmart.com/terms-of-use` | **HTTP 200**, 15,195 B — but redirected to `https://www.walmart.com/blocked?url=…&uuid=…` and titled `Robot or human?`. A challenge page, not the terms |

**The path this repo fetches is `/ip/<slug>/<id>`, and no rule in the `*` group
matches it.** The `Disallow` list is checkout, account, internal APIs, search and
store-locator paths:

```
User-agent: *
Disallow: /account/
Disallow: /api/
Disallow: /search
Disallow: /orders
Disallow: /typeahead/
Disallow: */api/wpa
```

There is no `/ip/` rule, and Walmart publishes item-page sitemaps by name:

```
Sitemap: https://www.walmart.com/sitemap_hi_ip.xml
Sitemap: https://www.walmart.com/sitemap_itp_01.xml
Sitemap: https://www.walmart.com/sitemap_itp_02.xml
Sitemap: https://www.walmart.com/sitemap_product_03.xml
```

Note `Disallow: /search` — a discovery path this repo does not use for Walmart
and now has a written reason not to. `Crawl-delay: 5` is set, but only for
`Slurp`.

**The terms are `unread`, and the shape of that refusal is the one this project
already has a name for.** HTTP 200 with a challenge body is exactly the Pokémon
Center interstitial pattern recorded above — a status code that says yes over a
page that says no. Recorded as a refusal, not as a document, and not retried.

### Best Buy — refused at the connection layer, both documents

| Request | Result |
|---|---|
| `https://www.bestbuy.com/robots.txt` | **no HTTP status**, 0 B. `curl: (92) HTTP/2 stream 1 was not closed cleanly: INTERNAL_ERROR (err 2)` |
| `https://www.bestbuy.com/site/help-topics/terms-and-conditions/pcmcat204400050067.c?id=pcmcat204400050067` | **no HTTP status**, 0 B. Identical `curl: (92)` reset |

This corroborates the Best Buy finding already in this document rather than
adding a new one: *"Best Buy refuses impersonated HTTP at the connection layer
regardless of TLS fingerprint — HTTP/2 stream reset, HTTP/1.1 timeout"*. That was
recorded for product pages; it holds for `/robots.txt` and for the terms page
too, and plain `curl` is refused the same way `curl_cffi` was. Best Buy is read
here at rung 3, through a real browser, and the two policy documents are the one
thing nobody has pointed a browser at.

Both positions are `unread`. Best Buy is the only retailer in scope with neither
signal recorded.

### Nintendo — both read, and they disagree

| Request | Result |
|---|---|
| `https://www.nintendo.com/robots.txt` | **HTTP 200**, 5,167 B, `text/plain`, 2026-08-03 |
| `https://www.nintendo.com/us/terms-of-use/` | **HTTP 200**, 260,998 B, `text/html`, 2026-08-03. The document carries `Last Updated: May 24, 2016` |

**robots.txt permits the path this repo fetches.** The file opens with the `*`
group, and it is one line:

```
User-agent: *
Allow: /
```

Every `Disallow: /` below it is scoped to a *named* crawler — `Kangaroo Bot`,
`Nutch`, `Omgili`, `PanguBot`, `PetalBot`, `Timpibot` and others. A second `*`
group near the end adds four rules, none of which matches a store path:

```
User-agent: *
Disallow: /sg/support/qa-list
Disallow: /my/support/qa-list
Disallow: /th/support/qa-list
Disallow: /ph/support/qa-list
```

Nothing in the file matches `/us/store/products/<slug>/`, and the store
catalogue is published as a sitemap:

```
Sitemap: https://www.nintendo.com/us/store/sitemap.xml
```

This corroborates the Phase 2 reading in the Nintendo section above
(`User-agent: * / Allow: /`, only named bots disallowed) from a different
transport, ten months of site changes later.

**The same file ends with a prohibition that is not a directive.** The last four
lines are `#` comments — mechanically inert, and a statement of the operator's
wishes all the same:

> Nintendo Co., Ltd. and its affiliated companies ("Nintendo") therefore
> explicitly reserve all their rights in any content made available […] Any use
> of such content for the development, training, programming, improvement and/or
> enhancement of artificial intelligence (including, but not limited to,
> generative AI systems), web scraping, machine learning, or any form of text or
> data mining by any means, is strictly prohibited, unless specifically and
> explicitly authorized in writing by the Nintendo company that owns the
> respective rights.

A parser sees `Allow: /`. A reader sees "web scraping … is strictly prohibited".
The matrix cell reports the directive, because that is what the column is for,
and this paragraph is why the row is not the whole story.

**The Terms of Use forbid automated access, in the same words as Amazon's and
Target's.** § 6, *Acceptable Use of the Services*, under "You further agree not
to":

> Use any robot, iframe, spider, crawler, scraper or other automated means or
> interface not provided by us to access the Services, including, without
> limitation, for the purpose of copying, extracting, aggregating, displaying,
> publishing or distributing any content or data made available via Services.

The same list also bars any use that "could interfere with, disrupt, negatively
affect or inhibit other users" or that "could damage, disable, overburden or
impair the functioning of the Services" — the load-shape clause, which a 5-minute
cadence against one URL does not come close to, and which is the only clause here
that turns on *how much* rather than *by what means*.

**So Nintendo's two signals point in opposite directions, and Nintendo is a
retailer this repo ships.** That is a sharper instance of the same disagreement
recorded at Target, Amazon and Pokémon Center, and it is recorded here in the
same words rather than softened because this one is already in
`config/products.yaml`. Phase 3.1's premise (`03.1-CONTEXT.md`) is that a written
prohibition is a fact to state rather than an instruction this project takes —
"bot-y is a bot for humans" — so the row says `⚠ disagree` and the watch stays.
A reader who weighs it differently now has the clause, the URL and the date to
weigh it with, which is the whole of REQ-13.

## Phase 3 closing record (2026-08-03) — what shipped, what did not, and the count

This is the phase's own summary, written where a reader looking for "so which
retailers actually work" will find it. The per-retailer sections above are the
evidence; this is what they add up to.

**What shipped: nothing new, and that is the finding.** Phase 3 was scoped to
two retailers — Target and Amazon — and both were settled at **rung 4 by their
own written terms**, without a single request being made to a product page at
either one. No adapter was written, no fixture was captured, no watch was added
to `config/products.yaml`, and `boty/retailers.py` was not touched across the
whole phase. The two additions are gates rather than detectors:
`scripts/evidence_check.py` (03-01) and `tests/test_support_matrix.py` (03-03).

**What did not ship, and why each one is a different kind of refusal:**

| Retailer | Rung | What settled it | Product-page requests |
|---|---|---|---|
| Amazon | 4 | `LICENSE AND ACCESS` in its Conditions of Use forbids the **method** and independently names the **data** — "any collection and use of any product listings, descriptions, or prices" | **0** |
| Target | 4 | `Unlawful or Prohibited Uses` in its Terms & Conditions forbids data extraction with **no commercial-use qualifier**, and the "limited license" carve-out closes rather than opens | **0** |
| Pokémon Center | 4 | Settled in Phase 2 by a ladder walked to exhaustion: Imperva refuses `/product/*` at rung 1 and at rung 3, and `robots.txt` closes the API endpoints | n/a (Phase 2) |

Amazon and Target are refusals of a different kind from Pokémon Center's. A wall
can fall — Pokémon Center's section carries the two probes that would establish
whether it has. A written prohibition does not, and the correct action for both
of the hard two is that **nobody should look again**.

### The retailer count: four, and criterion 5 is UNMET

`boty check` reports **four** retailers — GameStop, Walmart, Nintendo and Best
Buy — all control-verified and healthy. The roadmap's Phase 3 criterion 5 asks
for five or more. It is **unmet**, and it is recorded rather than padded.

This is the outcome the roadmap explicitly anticipated: *"If both are rung 4,
this criterion is unmet and recorded as such, never padded with a retailer that
does not carry the product."* It is also now **final rather than pending**:

- Every retailer in the roadmap's Retailer Scope table is now either shipped or
  carries a `**Verdict: REFUSED**` section in this document. There is no
  seventh candidate; the US retail set for this device is the seven listed.
- A control-only fifth was available and was declined. Micro Center was probed
  in Phase 2, found viable at rung 1 with a real control and a real fixture, and
  turned down because it does not carry the Pokémon GO Plus + and could never
  alert on it. Adding it would have moved the counter without moving the goal.
- Of the four that work, **three** carry the GO Plus + itself (GameStop, Walmart,
  Nintendo). Best Buy is control-only: it does not appear to stock the product,
  which is a disproof backed by two searches rather than an omission.

`scripts/evidence_check.py --phase` now runs inside the offline suite, so
`make verify` fails if a later edit configures a retailer outside that scope or
leaves one inside it with no verdict. The only way to move this number is the
honest one.

### REQ-08: how long a full pass actually takes

Measured, not asserted. `boty.status.write` now publishes a `duration_seconds`
key, so the figure is readable off `served/boty/status.json` after any pass
rather than being re-timed by hand.

**61.4 s against a 120 s budget**, at **10 watches across 4 retailers, one of
them on rung 3** — measured 2026-08-03T05:12Z under the service's own
`EnvironmentFile` via `systemd-run`, with `boty.service` stopped so the run was
not racing a live cycle.

| Measurement | Watches | Retailers | Result |
|---|---|---|---|
| 02-04 (Phase 2, hand-timed) | 10 | 4 (one rung 3) | ~40 s |
| 03-02 (`time`, service env) | 10 | 4 (one rung 3) | 36.8 s |
| 03-03 (published `duration_seconds`) | 10 | 4 (one rung 3) | **61.4 s** |

The configuration did not change between these three — no watch was added or
removed, and both hard-two retailers are rung 4, so nothing was ever configured
for them. What changed in the third measurement is a **transient network
failure**: `TRANSITION — Mega Evolution Booster Bundle` hit
`Timeout: Failed to perform, curl: (28)` and went through `boty.fetch.get`'s
retry and backoff before returning **UNKNOWN**. That single watch accounts for
essentially all of the ~25 s difference from 03-02's run of the same config.

Two things are worth reading off that rather than rounding away:

- **The budget has real headroom, and the headroom is what absorbed the
  timeout.** A retailer timing out is ordinary, and the pass still finished at
  roughly half the budget.
- **The timed-out watch read UNKNOWN, not OUT_OF_STOCK.** That is the core
  promise of this project holding under exactly the condition that breaks it in
  other monitors — a fetch that never completed did not become a stock verdict.

REQ-08's wording is "at ~7 retailers". Four is what shipped, so four is what was
measured; extrapolating a number for a seven-retailer configuration that was
never run, and can never be run because three of the seven are refused in
writing, would be inventing the measurement this section exists to avoid.

**Confirmed a second time, by the deployed service itself.** `watch_cycle`
publishes a duration too, so the number stays current on the dashboard rather
than being whatever a human last measured. The first cycle after the restart —
`updated` 2026-08-03T05:13:56Z — published **35.0 s**, `healthy: true`, four
retailers, one `rung: browser` reading correctly flagged `degraded: true`, and
**no UNKNOWN readings at all**. That is the same configuration as the 61.4 s
measurement twelve minutes earlier, which settles what the difference was: a
transient retailer timeout, not a cost this phase added. The budget figure to
carry forward is therefore roughly **35–61 s at 10 watches and 4 retailers**,
where the upper end already includes one retailer failing to answer.

#### Amended 2026-08-03 (03.1-04) — re-measured at six retailers, with two browser rungs

The Phase 3 measurement above is **not replaced**. It was taken at four
retailers; this phase shipped six, and the comparison between the two is the
useful part. Both figures below were **read off `served/boty/status.json`'s
`duration_seconds`**, not re-timed by hand — that key exists precisely so the
budget can be read after any pass instead of estimated.

**Environment.** Everything below ran under the service's own `EnvironmentFile`,
via
`sudo systemd-run --pipe --quiet --uid=dan --property=EnvironmentFile=/home/dan/.config/boty/env --property=WorkingDirectory=/home/dan/CodeProjects/pokemongoplusplus …`.
A bare shell strips `BOTY_BROWSER_PATH` / `BOTY_BROWSER_NO_SANDBOX` and yields
`VERIFY: PASS (INCOMPLETE — …)` at exit 0, with both browser-rung controls never
run — which is blind to exactly the retailers this phase added.

| Measurement | Watches | Retailers | Browser rungs | `duration_seconds` | `healthy` |
|---|---|---|---|---|---|
| 03-03 (Phase 3, manual) | 10 | 4 | 1 | 61.4 s | true |
| 03-03 (Phase 3, service cycle) | 10 | 4 | 1 | 35.0 s | true |
| **03.1-04 (manual, `updated` 2026-08-03T14:19:15Z)** | **13** | **6** | **2** | **45.98 s** | **true** |
| **03.1-04 (service cycle, `updated` 2026-08-03T14:20:49Z)** | **13** | **6** | **2** | **44.81 s** | **true** |

Against REQ-08's 120 s budget both figures sit at roughly **37 %**. `boty check`
printed `13 watches across 6 retailers in 46.0s` as its last line, which is the
same `elapsed` the published key carries. This plan's own gate re-ran the whole
thing a third time a few minutes later and published **45.09 s**, `healthy:
true`, 13 watches — recorded because it was run, not because it was the number
wanted.

**`healthy` was read at the same moment as the duration, deliberately.** It is
the half of the count criterion a count cannot see: a retailer stuck on permanent
UNKNOWN satisfies a total while raising a health warning. All **six** retailer
health entries read `ok: true` with an empty `reason` and no `failing_controls` —
`amazon`, `bestbuy`, `gamestop`, `nintendo`, `target`, `walmart`. Zero health
warnings.

**The rung mix, which is what would have moved the figure.** Of 13 watches, **2
are rendered** (the Best Buy control and the Target control) against Phase 3's
one, and **3 read `dom`** (Target's control and both Amazon watches). Four of the
thirteen are `degraded`.

| Retailer | `rung` | `extraction` | `degraded` | Watches |
|---|---|---|---|---|
| gamestop | `tls` | `structured` | `false` | 6 |
| walmart | `tls` | `structured` | `false` | 2 |
| nintendo | `tls` | `structured` | `false` | 2 |
| bestbuy | `browser` | `structured` | `true` | 1 |
| target | `browser` | `dom` | `true` | 1 |
| amazon | `tls` | `dom` | `true` | 2 |

Every one of those six triples was compared cell-by-cell against its row in the
README support matrix and **all six agree**. That comparison is the one thing no
test performs: `tests/test_support_matrix.py` reads the table and
`tests/test_status.py` reads the payload, and nothing puts the two side by side
against a live run.

**Amazon is the row that makes the two axes worth having.** It is rung 1 —
`tls`, the cheapest transport here — and it is `degraded: true` anyway, on the
extraction disjunct alone. Under the pre-03.1-05 definition, where `degraded`
was derived from the rung, Amazon would have shipped looking as trustworthy as
GameStop.

**Why the duration barely moved, when the retailer count went up by half.**
Six retailers and 13 watches take *less* time than Phase 3's four retailers and
10 watches. The second browser render costs about 20 s — the two
`BOTY_BROWSER_NO_SANDBOX` warnings in the manual run are 23 s apart, which brackets
the Best Buy render and the Target render — but Phase 3's 61.4 s included a
`curl: (28)` timeout and its retry-and-backoff on a single GameStop watch. Read
against the *service* figures instead, which is the like-for-like comparison,
this phase cost **35.0 s → 44.81 s**: roughly **+10 s for the second browser
render plus two extra rung-1 fetches**, and Amazon adds no render at all.
No figure was averaged and no run was repeated to find a faster one.

**The deployment was observed, and observing it found something an exit code
could not.** `boty.service` was still running the process started at
2026-08-03T05:13Z — *before* any of this phase's three feature commits
(`44ec45c` 12:28Z, `a4f2847` 13:14Z, `7caeaf2` 14:00Z). It was publishing **10
watches across 4 retailers with no `extraction` key at all**. The tree shipped
six retailers; the deployed monitor was watching four, and nothing in
`make verify` looks at the deployed monitor. Restarted at 2026-08-03T14:20:05Z;
its first cycle on the shipped code is the 44.81 s row above.

**Zombie-process observation, before and after.** The browser transport leaked
`<defunct>` children on this deployment once, and this phase **doubled** the
render count per pass. Counted immediately before the work (14:16:47Z) and after
a manual `boty check` plus a full service cycle on the new code (14:22:44Z):

| | Before | After |
|---|---|---|
| `chromium` processes owned by `dan` | 4, all `<defunct>` | **4, all `<defunct>` — the same four PIDs** |
| …parented to `boty.service` | **0** | **0** |
| children of `boty.service`'s MainPID | **0** | **0** |
| `/tmp/uc_*` browser profiles | 23 | **23** |

The four zombies are PIDs 976451, 976548, 980375 and 980378, every one of them
parented to Mission Control's `python3 ./server.py` (PID 3741873) and every one
of them older than this plan. `boty.service`'s MainPID has no children at all,
and the unit runs `PrivateTmp=true`, so the 23 stale profiles are not its either.
**Two renders per pass leaked nothing.**

Held for a second service cycle to be sure: `updated` 2026-08-03T14:26:03Z,
**42.84 s**, `healthy: true`, 13 watches, six retailer health entries. Counted
again at 14:30:43Z — still the same four zombies, still zero children under
`boty.service`, still 23 profiles, across roughly **ten renders** since the
restart (two per service cycle, two per manual pass).

## Phase 3.1 closing record (2026-08-03) — two conclusions revised, no observation retracted

The Phase 3 closing record above is left exactly as it was written. This one sits
beside it rather than over it, because the interesting thing about this phase is
not what it shipped — it is that it reversed two published verdicts **without
retracting a single observation**, and a reader who cannot see both records
cannot check that claim.

### What shipped

| Retailer | Rung | Extraction | `degraded` | Watches | Can it alert on the GO Plus +? |
|---|---|---|---|---|---|
| Target | **3** (browser) | **`dom`** | true | 1 (control) | **No** — Target delisted the product |
| Amazon | **1** (`curl_cffi`) | **`dom`** | true | 2 (control + product) | **Yes** — and it is the only one of the hard two that lists it |

**The count is six**: gamestop, walmart, bestbuy, nintendo, target, amazon. All
six control-verified, `healthy: true`, zero health warnings. Read that as a four
and a two: **Best Buy and Target are control-only**, each because the retailer
does not carry the product — a disproof in both cases, not an omission — so four
of the six can actually page a person.

**What did not ship: Pokémon Center, and it is the only one left.** It is also
the only retailer in scope refused by an *actual wall* rather than by a reading
of a document, which is the distinction this phase turned out to be about.

### The three things no earlier document holds together

**1. Target serves its page and withholds its data, and that is a third refusal
shape.** Before this phase the vocabulary had two words for a retailer that does
not work: a **wall** (Pokémon Center — Imperva turns away `/product/*` at rung 1
and at rung 3) and a **policy** (Amazon's and Target's written terms). Target is
neither. It refused nothing: HTTP 200, ~315 KB, no challenge, no `BLOCK_PHRASES`
match, and the page's own hydration state reads `"isBot": false`. It also
carries no product data whatsoever — zero `application/ld+json`, zero
`schema.org`, zero `"price"`, zero `availability`, zero `"seller"` — because
Target ships the price module empty and says so in its own flag,
`"isProductDetailServerSideRenderPriceEnabled": false`, confirmed on two
unrelated PDPs and on 2023 and 2025 archive snapshots. **Open and empty.** A
rung-1 watch there would have returned UNKNOWN forever while every gate in the
tree stayed green, which is the failure mode this project is least equipped to
notice from the outside: a page that reads perfectly and says nothing.

**2. The `Extraction` axis exists because the rung number could not tell Best
Buy's rendered `ld+json` from Target's rendered button.** Both are rung 3. One
reads the retailer's own structured feed — a contract Best Buy publishes on
purpose — and the other reads presentation markup that a reskin breaks silently:
no error, no 403, just a control that stops being found. Folding that into the
ladder would have renumbered a scale four phases of documents refer to by number,
so it landed as a **second axis**: `Rung` keeps meaning transport, `Extraction`
is `structured` or `dom`, and nothing was renumbered.

Widening `degraded` to fire on **either** disjunct closed a hole **no adapter had
yet opened**. `degraded` was derived from the rung alone, so a rung-1 `dom`
adapter — cheap to write, and the most fragile thing this codebase could acquire
— would have shipped looking exactly as trustworthy as GameStop, in `boty
check`, on the status page and in the support matrix. That was written on
2026-08-03 as a precaution. **Amazon is that adapter, and it landed the same
day**: rung 1, `dom`, `degraded: true` on the extraction disjunct alone. Mutation
M7 exists to prove the new half is load-bearing rather than decorative — M6
dying only proves the flag exists.

**3. Target's `robots.txt` question was answered by Dan, not inferred by an
agent.** Rendering a Target product page makes Target's own JavaScript fetch
hosts that publish `Disallow: /` to every agent. bot-y does not issue those
requests; its browser does, at bot-y's instruction. That is a real distinction
and it is not obviously decisive, so it was **escalated rather than resolved** —
written into `QUESTIONS.md` § 0d, pushed to Dan, and left open while the phase
worked on what was unblocked. He took it explicitly, and his reason is the
premise the whole phase rests on:

> *"bot-y is a bot for humans. To take the power back from other bots."*

The ruling was then **measured rather than left as a forecast**: one rendered
load, `performance.getEntriesByType('resource')` evaluated inside the page, and
the browser's own record of what it fetched. It contacted **31 hosts**, and the
answer was right but incomplete — **three** Target-owned hosts publish
`Disallow: /`, not one (`redsky.target.com`, `api.target.com`,
`sapphire-api.target.com`). The prohibition the ruling does not license widened
accordingly: no code in this repo addresses any of the three directly, by
`boty.fetch.get`, by `curl`, or by any other means.

### What was revised, and what was not

Two verdicts moved: § Amazon from `**Verdict: REFUSED**` to
`**Verdict: REACHABLE (rung 1)**`, and § Target from `**Verdict: REFUSED**` to
`**Verdict: REACHABLE (rung 3)**`. **Nothing behind either was deleted.**
§ Amazon still carries its six policy reads with byte counts, the LICENSE AND
ACCESS clause in full, the complete `robots.txt` analysis and the PA-API
deprecation; the four sentences stating that no product page had ever been
requested are quoted, dated and marked historical rather than edited. § Target
still carries its terms, its `robots.txt`, the RedSky analysis and both
historical `**Refusal observed (rung N):**` lines — one of which records a
*non*-refusal in an anchored refusal line, and is retained precisely because it
is the measurement the verdict was revised *through*.

**The reversal was a maintainer decision, not a new technical finding, and the
records say so.** Phase 3's reasoning was accurate about the documents it read.
What it never did was ask the retailer. The record it produced was complete,
internally consistent, and contained **not one observation** about whether either
page could be read — plus a section explaining why nobody should find out. That
is the defect `evidence_check` **rule 6** now makes mechanical: a `REFUSED`
verdict must cite an anchored refusal observation whose body carries a
measurement, and the two hard-two retailers need two of them including one at
rung 3. It is watched going red against the verbatim pre-03.1 text of both
sections, lifted out of commit `339800e` — 658 lines of accurate writing that
rule 6 fails outright.

### Where the phase landed against the ROADMAP's six criteria

| # | Criterion | Verdict | What settles it |
|---|---|---|---|
| 1 | Target reports stock for the GO Plus +, control green | **UNMET — deliberately not amended** | Target **delisted** the product (TCIN `88714054`, HTTP 200 as late as 2025-05, now 404). No amount of work satisfies it. A rewrite to "reports trustworthy stock" was proposed and **Dan declined it** — editing a criterion after the fact to make it meetable is the move this project keeps catching in itself. Target's control watch *is* green |
| 2 | Amazon reports stock if it carries it, or the **technical** outcome is recorded, having actually been attempted | **MET** | Attempted for real. Three `/dp/<ASIN>` requests, three HTTP 200s, zero block-phrase matches. Amazon carries it, so there is a real product watch; it reads OUT_OF_STOCK correctly, because the only offer is a used unit at $219 from a reseller |
| 3 | Five or more retailers, no health warnings — six if Amazon lands | **MET at six** | Amazon landed, so the bar is its own upper form. `status.json`: six retailers, all `ok: true`, `healthy: true`, zero warnings, 13 watches, 6/6 live controls |
| 4 | Every row states rung, robots.txt position and terms position | **MET** | Seven rows, now **seven columns** — `Extraction` was added this phase — machine-checked by `tests/test_support_matrix.py`, including that a rung-3 **or** `dom` row must declare `degraded` and that the Extraction cell is tied to the Rung cell in both directions |
| 5 | No regression: four Phase 2 retailers still green, `make verify` exits 0 | **MET** | Bare `VERIFY: PASS` under the service's `EnvironmentFile` — not `INCOMPLETE`. All four Phase 2 controls IN_STOCK with their extraction sources unchanged: `ld+json: InStock from GameStop`, `__NEXT_DATA__: IN_STOCK from Walmart.com`, `ld+json: InStock from Best Buy`, `ld+json: InStock from Nintendo of America Inc.` |
| 6 | A single `boty check` under two minutes | **MET** | **45.98 s** manual and **44.81 s** from the service's own cycle, both read off `duration_seconds`. See § REQ-08 above |

**Five of six met; criterion 1 stands unmet with its reason written down.** That
is the honest shape of this phase and it is not tidied. `TARGET_RETAILER_COUNT`
in `scripts/evidence_check.py` was **left at 5** — with Target and Amazon both
configured the count is 6 and rule 3 is silent, and raising the threshold to
match would arm a gate to fire the next time the honest answer is five. A gate
that goes red on the truthful answer is a gate that pressures the next person
into padding, which is the precise behaviour that file exists to prevent.
