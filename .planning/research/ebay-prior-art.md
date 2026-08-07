# eBay prior art: integrate, borrow, or build?

**Researched:** 2026-08-07
**Question:** Dan — *"I imagine something like this already exists, so let's do our research and see if there's an open source option we can integrate or whatever."*
**Scope of the milestone this informs:** alert-only, Buy It Now only, GO Plus + first.

---

## Verdict

**Build it, on eBay's own Browse API, called with the `curl_cffi` transport this
repo already has. Take no new runtime dependency.**

Three findings force that answer, and each one is measured rather than argued.

1. **There is nothing to integrate.** The entire open-source eBay-monitor field
   is three small scrapers, the largest of which has 29 stars and a README in
   which its own author writes *"This project hasn't been updated in 3 years, so
   I cannot guarantee it will still work."* Not one of them has a three-state
   availability model, a control product, or any concept of a reading it does not
   trust. § 3.

2. **The one library worth considering costs 289,045 lines to save about 120.**
   `ebay-rest` is real, MIT, and actively maintained — and it is 1,246 generated
   modules, 14.0 MB of Python, pulling seven runtime dependencies including
   `requests` and `cryptography`. bot-y's entire `boty/` package is 3,520 lines.
   The library is **82× the size of the project that would import it**, to wrap
   two HTTP calls. § 2.

3. **Everything credential-free is off the table before trustworthiness even
   comes up.** eBay's `robots.txt` says `Disallow: /sch/` in the `*` group —
   the search path every one of those scrapers fetches, and the only path that
   answers "is *anyone* selling a GO Plus + near MSRP right now". This project's
   own standard (README § *Being a good citizen*, and the three paths it refuses
   to request at Amazon) makes that a closed door, not a risk to weigh. § 4.

So eBay is a **rung-2 retailer or nothing** — reached by its sanctioned API or
not watched. That is the Best Buy shape (REQ-04) with one difference in each
direction, both of which matter and are stated in § 6.

**The build is small**: an OAuth client-credentials POST, one authenticated GET,
and a reader over JSON that is already structured. `boty.fetch.get()` takes a
`headers=` argument today, so the GET needs no new transport at all. What is
*not* small is the trust model, because eBay breaks two of bot-y's three
defences — § 5 is the part of this document worth arguing about.

---

## 1. What was measured, and what was not

Everything in this file that carries a number was retrieved on **2026-08-07**
from this machine, with the status code recorded. Where a claim rests on a
search engine rather than a primary document it is marked, because
`gsd-tools query classify-confidence` rates every provider available to this
agent at **LOW** — there is no provider id in that seam for "fetched the vendor's
own document and recorded the HTTP status", which is most of what is below.
Per-claim confidence is therefore stated in the tables rather than inherited
from a tool.

**Deliberately not measured — these are gaps, not omissions:**

| Not measured | Why | Consequence |
|---|---|---|
| Any `https://www.ebay.com/sch/...` request | `robots.txt` `*` group carries `Disallow: /sch/`. **Zero requests were made to it**, in line with the rule this repo already applies to Amazon's three disallowed paths | We do not know, and did not try to find out, whether eBay serves search HTML to `curl_cffi`. That question is not load-bearing — see § 4 |
| A live authenticated Browse API call | No keyset was obtained. Unauthenticated probes only: `POST /identity/v1/oauth2/token` → **HTTP 401** `{"error":"invalid_client"}`; `GET /buy/browse/v1/item_summary/search` → **HTTP 403** | **The single biggest gap.** Nobody here has seen a `200` from this API. Whether a plain developer keyset is accepted in production is contested *in eBay's own documentation* (§ 6.2) and can only be settled by a request |
| Whether a GO Plus + is on eBay today, and at what price | Answering it needs either the API (no key) or `/sch/` (disallowed) | The milestone's premise — that eBay has units near MSRP — is **assumed, not established**. Worth being the first thing the first plan proves |
| `ebay-rest` behaviour at runtime | Not installed; measured from the published wheel only | Size and dependency claims are solid; correctness claims are not made |

**Read in full or grepped, with status:** eBay `robots.txt` (HTTP 200, 18,810 B,
232 rules in the `*` group, parsed programmatically); eBay User Agreement (HTTP
200, 400,961 B); eBay API License Agreement (HTTP 200, 123,729 B → 76,235 chars
of text, **grepped, not read end to end**); `buy-requirements.html`,
`buy-overview.html`, `api-browse.html`, `ref-buy-browse-filters.html`,
`api-call-limits`, `api-deprecation-status` (all HTTP 200 via
`www.developer.ebay.com`).

**One measurement worth recording for whoever writes the adapter:**
`developer.ebay.com` (no `www.`) returns **HTTP 403, 1,831 bytes** to plain
`curl` on every path tried, and so do several `www.developer.ebay.com` paths
(`/api-docs/buy/browse/overview.html`, `/api-docs/static/oauth-client-credentials-grant.html`,
the `item_summary/search` reference). The *docs site* is behind a wall even
though the API is not. Do not read a 403 from the docs host as a signal about
the API host.

---

## 2. Python eBay API clients

| Candidate | Licence | Last release | Last commit | Maintenance signal | What it would do for us | What it would cost us | Verdict |
|---|---|---|---|---|---|---|---|
| **`ebay-rest`** (PyPI `ebay-rest` 1.1.4, `matecsaj/ebay_rest`) | **MIT** ✅ | **2026-02-15** | 2026-02-15 | **Alive.** 71★, 14 forks, 15 open issues, not archived. Recent commits are real maintenance ("Removed deprecated models and API for eBay Marketing…", unit tests for `ApplicationToken`/`UserToken`) | Wraps the **current** REST APIs including Buy/Browse; handles OAuth token lifecycle; `Development Status :: 5 - Production/Stable`; `requires-python >=3.10` matches ours | **2.99 MB wheel · 1,246 `.py` modules · 14.0 MB uncompressed · ~289,045 LOC** of OpenAPI-generated code. Seven runtime deps: `authlib`, `certifi`, `cryptography`, `requests`, `python-dateutil`, `six`, `urllib3` — including a compiled crypto dep, a vendored `six` in 2026, and `requests`, the library this project deliberately does **not** use | ❌ **Reject on size.** Not on quality — this is the best-maintained thing in the field. It is 82× `boty/` for two HTTP calls |
| **`ebaysdk`** (PyPI 2.2.0, `timotheus/ebaysdk-python`) | **CDDL-1.0** ⚠️ (GitHub reports `NOASSERTION`) | **2020-04-20** | **2021-11-23** | **Dead.** 856★ but 166 open issues and no commit on `master` in 4½ years | — | Would drag `lxml` in, and a CDDL-1.0 file-level copyleft into an MIT tree for no benefit | ❌ **Reject twice over.** It wraps the **Finding** and **Shopping** APIs, and eBay's own deprecation table lists *Finding API — All — 2025/02/04 — replaced by the Browse API* and the same line for Shopping. **The APIs it exists to call were decommissioned 18 months ago.** Its 856 stars are a trap for anyone searching PyPI |
| `ebayfeed` | MIT | **2018-11-05** | — | Dead, 9 releases, all in one month of 2018 | — | — | ❌ Wraps the Feed API, which is EPN-gated and not what an alert needs |
| `python-ebay` | Apache-2.0 | **2014-01-20** | — | Dead. One release, `0.2.0b5dev` | — | — | ❌ |
| `eBay/ebay-oauth-python-client` (GitHub, no PyPI record — `pypi.org/pypi/ebay-oauth-python-client/json` → **404**) | `NOASSERTION` | not on PyPI | 2024-05-09 | 102★, 11 open issues; eBay's own | Token fetch + refresh | An undeclared-licence dependency, not installable by name, for ~30 lines | ❌ Fails "small dependency surface" and the licence audit in one go |

**PyPI as a whole was enumerated** (865,857 names; 63 match `ebay`). After
removing Naive-Bayes false positives, Pirate Bay packages and one-off scrapers,
the four rows above plus `ebay-mcp` (0.1.0, single release 2026-06-26, an MCP
server, not a library) are the entire field. There is no maintained
*lightweight* Browse-API client in Python. `ebay-rest` or hand-rolled are the
only two real options.

**Confidence: HIGH.** Every figure is from the PyPI JSON API, the GitHub API, or
the published wheel, all fetched directly.

---

## 3. Existing open-source monitors — the honest picture

GitHub's search API, sorted by stars, for eBay monitors / price trackers / deal bots:

| Project | Stars | Licence | Language | Last push | Approach | Does it solve our problem? |
|---|---|---|---|---|---|---|
| `samjmck/ebay-monitor` | 29 | MIT | Go | 2023-09-12 | Scrapes eBay **search pages**, notifies on new results via Telegram | **No.** Its README: *"This project hasn't been updated in 3 years, so I cannot guarantee it will still work… I don't really have an incentive to update the project. The goal of this project was for me to experiment with and learn a new programming [language], Go."* Also: only ever tested against eBay BE and UK |
| `Igor-Kaminski/ebay-price-monitor` | 9 | MIT | Python | 2025-12-21 | Scrapes search HTML with `requests` + `beautifulsoup4` + **`fake-useragent`**; alerts a *seller* when undercut | **No**, and it is the anti-pattern. `fake-useragent` is precisely the header spoofing bot-y's README calls "theatre" — it leaves the TLS fingerprint untouched. Its own feature list claims *"Smart HTML parsing - Adapts to eBay's changing structure"*, which is the confident-wrong-answer failure mode this project exists to refuse |
| `henryecw/ebay-monitor` | 3 | none | — | 2020-09-12 | Search scrape | No |
| `mattmeisinger/ebay-watcher` | 6 | none | — | **2017** | Search scrape + price history | No |
| `dgtlmoon/changedetection.io` | **32,971** | Apache-2.0 | Python | **2026-08-07** | Generic page-diff watcher, genuinely alive | **No** — and it is the tool bot-y's README already names: *"a general-purpose page watcher pointed at the most defended pages on the consumer web."* It diffs bytes. It has no notion of stock, seller, price ceiling or "I could not read this page", and pointing it at eBay points it at `/sch/` |

Every eBay-specific project above fetches the search path. **All of them are
therefore fetching a path eBay's `robots.txt` disallows** (§ 4) — which is very
likely *why* the field is a graveyard: they break, and there is no sanctioned
way to fix them without an API key, so the authors stop.

### 3.1 The honest framing question, answered plainly

> Does any existing tool have bot-y's trust model — three-state availability with
> a guaranteed UNKNOWN, control products, seller filtering, a price ceiling,
> mutation-tested extractors?

**No. Not one, and not partially.** Across the eBay-specific field and
`changedetection.io`, the count of projects with *any* of those five is **zero**.
The nearest thing to a control product anywhere in this search is
`tomekx/mydealz-scraper` comparing scraped deals against sold-item medians —
which is a reference-price idea, not a health check.

That is a real finding and not a flattering one to state, so state the caveat
with it: this is a search over public GitHub by stars, and a small unstarred
project could have been missed. What can be said with confidence is that
**nothing popular enough to be discoverable does this**, which is the same
conclusion the README already reached for retail monitors, arrived at
independently for eBay.

**Confidence: MEDIUM-HIGH.** Repo metadata and README text are directly
measured; "nothing exists" is always a negative claim over a search.

---

## 4. Why the credential-free path is closed

eBay's `robots.txt` was fetched (HTTP 200, 18,810 bytes) and the `*` group — 232
rules — was parsed programmatically rather than eyeballed. Matching this
project's convention (`robots.txt` is a deny-list; silence is permission):

| Path | Verdict | Matching rules |
|---|---|---|
| `/sch/i.html?_nkw=<query>` | **Disallowed** | `Disallow: /sch/i.html?_nkw=`, `Disallow: /sch/i.html?*_nkw=*&`, `Disallow: /sch/` |
| `/sch/` anything | **Disallowed** | `Disallow: /sch/` |
| `/itm/<id>` (a specific listing) | **permits** — no rule in the `*` group matches | (`/itm/` has 20 rules, all narrower: `/itm/*_nkw`, `/itm/addToCart`, `/itm/watch/`, `/itm/fetchmodules`, …) |

So eBay draws exactly the line the milestone cares about: **watching a listing
you already know is permitted; searching for listings you don't is not.** The
milestone needs the second one — "tell me when *anyone* lists a GO Plus + under
$80" is a search, by definition.

The terms agree with the robots file rather than contradicting it, so **this row
would not carry `⚠ disagree`**. eBay's User Agreement forbids

> "use any robot, spider, scraper, data mining tools, data gathering and
> extraction tools, or other automated means (**including, without limitation
> buy-for-me agents, LLM-driven bots, or any end-to-end flow that attempts to
> place orders without human review**) to access our Services for any purpose,
> **except with the prior express permission of eBay**"

Two things follow, and both are useful.

1. **The alert-only scope is not merely cautious, it is the clause.** eBay
   explicitly names buy-for-me agents and order placement without human review.
   A milestone that alerts and never buys sits on the right side of a sentence
   eBay wrote down. Keep it there.
2. **"Except with the prior express permission of eBay" is what an API keyset
   is.** The API License Agreement is that permission, granted in writing. This
   is not a loophole reading; it is the same structure as Best Buy, where the
   sanctioned API is rung 2 precisely because it has no adversarial relationship.

One clause of the API License Agreement is worth carrying into the design:
*"Developer is responsible for ensuring that Your Users comply with all terms
and conditions of this Agreement."* For an MIT tool that ships **no credential**
and requires each operator to bring their own keyset, each operator is their own
Developer under that agreement. That is an argument *for* the bring-your-own-key
design and against ever shipping a shared key, which nobody was proposing but
which is now written down.

**Confidence: HIGH** for robots.txt (parsed from the retrieved file, rules
quoted). **MEDIUM** for the licence-agreement reading — 76,235 characters were
retrieved and grepped, not read end to end, and this is a lawyer's document
being read by a monitor author.

---

## 5. What eBay does to bot-y's trust model

This is the section that should shape the roadmap, because integrating eBay is
not "add a seventh adapter". **Two of bot-y's three defences do not survive
contact with a marketplace that is *only* third-party sellers.**

| bot-y defence | On eBay | What has to replace it |
|---|---|---|
| **First-party seller filter** — the load-bearing idea in `retailers.py` | **Meaningless.** eBay has no first party. There is no `FIRST_PARTY['ebay']` that could be written honestly, and `_pick()` with `first_party_only=True` against a retailer absent from `FIRST_PARTY` returns the *"no first-party seller list is configured"* UNKNOWN — forever. The generic `check_html` path is not merely unsuitable here; it is guaranteed to read UNKNOWN | Nothing restores it. The replacement is **condition + delivered price + a seller-quality floor**, and each is weaker than what it replaces. This must be stated in the support matrix rather than papered over |
| **Price ceiling** (`max_price: 80`) | **Survives, but is trivially defeated as currently applied.** It reads `offer.price`. On eBay a $54.99 listing with $45 shipping is a flip wearing a costume | Ceiling the **delivered total** — `price` + `shippingOptions[].shippingCost` — not the item price. If shipping cost is absent or unresolvable for the destination, that is an **UNKNOWN**, not a pass. This is the single most likely way a first version sends the alert this project exists not to send |
| **Three-state availability with guaranteed UNKNOWN** | **Survives and is the reason to do this at all** — but the mapping changes shape. On a retail PDP, "no offer" means out of stock. On a search, **zero results is a legitimate answer**: nobody is listing one under the ceiling | Which makes the **control** load-bearing in a new way — see below |
| **Control products** | **Survive, and get easier.** A control on eBay is a *query* that must always return results (e.g. a common item, BIN, generous ceiling), not a product that must always be in stock | This is what separates "nobody is selling one" from "my query, my token, or my reader broke". Without it, an expired OAuth token and a drought are the same silent zero — **exactly the bug this project was built around, in a new costume** |
| **Mutation-tested extractors** | Survive unchanged, and are cheaper here: the Browse API returns JSON, so there is no `dom` reading and no `[degraded]` on the extraction axis | Extend the existing mutation set: corrupt the buying-option check, the delivered-total ceiling, the condition check, and the zero-results→UNKNOWN edge |

### 5.1 Where it lands on the ladder

**Rung 2 + `structured`.** A retailer's own sanctioned API, returning
machine-readable JSON. Not degraded on either axis — the *best* row in the
matrix on the rung/extraction columns, and simultaneously the one whose *verdict*
is least defended, because the seller filter is gone. That is a genuinely new
combination for this repo and the README's two-column story does not currently
have a way to say it. Worth a note in the matrix rather than a silent good-looking
row.

---

## 6. The Browse API, concretely

### 6.1 What it gives us

- **Endpoint** `GET https://api.ebay.com/buy/browse/v1/item_summary/search`,
  token from `POST https://api.ebay.com/identity/v1/oauth2/token` with
  `grant_type=client_credentials` (an **application** token — no eBay user
  account, no user consent flow, no credential belonging to Dan's eBay identity).
  Both probed live: 403 and 401 respectively without credentials, so both
  endpoints are up and answering.
- **Buy It Now is the default.** eBay's own reference: *"Only FIXED_PRICE (Buy
  It Now) items are returned by default."* The milestone's BIN-only scope is the
  API's default behaviour — no auction-handling code, exactly as scoped.
- **Filters that map onto our requirements**, from
  `ref-buy-browse-filters.html`: `price:[..80]` with `priceCurrency:USD`,
  `conditions:{NEW}` or `conditionIds:{1000}`, `itemLocationCountry:US`,
  `deliveryCountry:US`, `maxDeliveryCost:0`, `sellers` / `excludeSellers`,
  `buyingOptions:{FIXED_PRICE}`.
- **Rate limit: 5,000 calls/day** (all Browse methods except `getItems`). At the
  project's 5-minute cadence that is **288 calls/day per query** — 5.8% of
  budget, room for a product watch, a control, and ~15 more.

### 6.2 ⚠ The two things that can bite, both from eBay's own documents

**(a) `buyingOptions` silently does nothing without a leaf category.** Quoting
the filter reference verbatim:

> *"Note: This filter is defined at the leaf category level and should be used
> with a leaf category ID. If this filter is used with a top-level category ID,
> it won't work and the filtered results won't be included in the response body."*

A filter that is accepted and ignored is the exact species of bug this project
is built to catch — the request succeeds, the response looks fine, and an
auction leaks into a BIN-only watch. **Do not trust the filter: re-check
`buyingOptions` on each returned item summary and drop anything that does not
carry `FIXED_PRICE`.** Cheap, and it makes the filter an optimisation rather than
a safety property — the same move `check_bestbuy_browser` already makes by
binding its verdict to a SKU instead of trusting a search redirect.

**(b) eBay's docs contradict each other about whether we may use this in
production at all.** This is unresolved and must not be resolved by picking the
convenient sentence:

| Source | Says |
|---|---|
| `buy-requirements.html` | *"Many of the Buy APIs are a (Limited Release). **The use of eBay's Buy APIs in production is intended for eBay partners only. You must apply for production access through the eBay Partner Network.**… There is no guarantee that your application for production use of the APIs will be approved."* |
| API Call Limits page, footnote | *"\* Buy APIs require an additional license."* (the `*` is on the Browse API row) |
| `buy-overview.html` | Marks **Deal API**, **Marketing API**, **Offer API** and Browse's **`search_by_image`** as `(Limited Release)` — and does **not** mark Browse keyword search |
| API Call Limits page, body | Publishes a **5,000/day default** for "Browse API — all methods except `getItems`", under the heading *"After you join the eBay Developers Program and get your application keyset, you can start using eBay APIs immediately"* and *"Our default API call limits are designed for individuals and smaller businesses"* |

Two eBay documents, opposite implications. **This is a `⚠ disagree` row before a
line of code is written**, and this repository has a rule about exactly this
situation: the one written down in the Amazon reversal — *a retailer is dropped
only when it is technically unreachable, and the reason recorded is the
observation, not a policy reading.* Phase 3 dropped Amazon on a desk review of
its terms having made zero requests; `evidence_check` rule 6 exists so that
cannot happen again.

**So do not resolve this on paper. The first plan of the milestone should be a
probe**: register the free developer account, create a production keyset,
subscribe-or-opt-out of marketplace account deletion notifications, and make
**one** `item_summary/search` call for the GO Plus +. Record the status code and
the response. That single measurement decides the whole milestone, costs almost
nothing, and is the same shape as the three `/dp/` requests that reversed Amazon.

Registration itself is reported as free with ~1 business day for account
approval, and production keysets as self-serve — **but that is search-engine
sourced (LOW confidence per `classify-confidence`) and the primary docs above
disagree with it, which is the whole point of § 6.2.** Do not plan around it;
measure it.

### 6.3 Against "works from a fresh clone"

Stated plainly, because it is the constraint eBay fails: **there is no
credential-free path to eBay.** Unlike Best Buy — where rung 3 works for a fresh
clone and the API key is a bonus — eBay has *only* the credentialed rung. `/sch/`
is closed, and a browser rendering a disallowed path is still fetching a
disallowed path.

Per NFR *"Works from a fresh clone"*, a path requiring a credential can be an
**OPTIONAL enhancement, never the documented way a retailer works**. For eBay
there is no other way, so the honest resolution is:

> **eBay is an optional retailer.** It is registered only when
> `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` are present, it is skipped without
> them, and a fresh clone's `make verify` is `PASS (INCOMPLETE — no eBay
> credentials)` rather than a failure.

That mechanism already exists and already has this exact meaning — the
`INCOMPLETE` verdict introduced for the missing `browser` extra. Reusing it costs
nothing and keeps the promise: **the tool must work, and say what it could not
check, for someone who clones it and adds nothing.**

One point in eBay's favour against the Best Buy precedent: Best Buy's key needs
manual approval *and rejects free email domains*, which is what demoted it to a
footnote. eBay's keyset appears self-serve. If § 6.2's probe confirms that, eBay
is an **optional-but-obtainable** credential — a materially better position than
Best Buy's, and worth saying so in the matrix rather than filing both under
"needs a key".

---

## 7. The reference-price problem

> *"Anything that does the reference price problem — knowing what a GO Plus + is
> actually worth so 'low' means something."*

**Nothing free, licence-clean and credential-free exists. And for this product,
we do not need it.**

| Source | Status | Verdict |
|---|---|---|
| eBay **Marketplace Insights API** (90-day sold data) | **Limited Release**, approved developers only, *not open to new applicants* | ❌ Fails "works from a fresh clone" *and* "obtainable with effort". Harder to get than Best Buy's key |
| eBay **Terapeak** | Free only with an eBay **Store subscription** (from ~$7.95/mo); **UI only, no API** | ❌ A paid seller subscription, and not machine-readable |
| `LH_Sold=1&LH_Complete=1` on a search URL | Under `/sch/` | ❌ Disallowed (§ 4) |
| Third-party sold-comps APIs (SoldComps, Bright Data, etc.) | Commercial | ❌ Paid, and a dependency on a reseller of scraped data |
| **The MSRP** | **$54.99**, already in the README, already the basis of `max_price: 80` | ✅ |

**The reference price for this product is already known and already
implemented.** The GO Plus + has a fixed manufacturer price that Nintendo
publishes on its own store — this repo reads it there, first-party, every cycle.
For a milestone scoped to *this product*, sold-comps solve a problem the project
does not have. Trying to acquire them would import the exact thing the NFRs
reject: a credential most people cannot get, or a paid third party, to
re-derive a number Nintendo publishes.

**If a reference price is ever genuinely needed** — at generalisation, which is
explicitly deferred — the cheapest honest source is bot-y's own history: a
rolling median of the *delivered totals* it has already observed on live BIN
listings. Zero new dependencies, zero new credentials, and it can be labelled for
what it is: **an active-listing median, not sold comps.** Asking prices are not
sale prices, and a monitor that quietly presented one as the other would be
telling exactly the kind of confident lie the UNKNOWN state exists to prevent.

**Confidence: MEDIUM.** The Marketplace Insights and Terapeak positions are
search-engine sourced (LOW per the seam) and were not confirmed against eBay's
own docs — `marketplace-insights/overview.html` returned **HTTP 403** on both
host forms tried. Several independent sources agree, and the direction of the
finding (harder, not easier) is the safe one to be wrong about.

---

## 8. What the build actually is

For scale, against the "small dependency surface" constraint:

| | Lines |
|---|---|
| `boty/` today | **3,520** |
| `ebay-rest`, the library we would import | **~289,045** |
| Estimated eBay adapter, hand-rolled | **~150–250**, including the token cache |

The adapter needs, in order:

1. **A token fetch.** `curl_cffi` already exposes `post` (verified locally:
   `curl_cffi 0.16.0`, `has post: True`). `boty/fetch.py` currently exports a
   GET-only `get()`; this adds one small sibling. Cache the token in memory with
   its `expires_in` — it lasts ~2 hours, so a 5-minute cadence makes ~12
   token calls a day, not 288.
2. **The search call.** `boty.fetch.get()` already accepts `headers=`, so the
   authenticated GET needs **no new transport code at all** — the `Authorization:
   Bearer` and `X-EBAY-C-MARKETPLACE-ID: EBAY_US` headers go straight through the
   existing impersonated fetch.
3. **A reader** over `itemSummaries[]` producing `parse.Offer`-shaped values, and
   re-checking on each item what the filters were supposed to guarantee:
   `buyingOptions` contains `FIXED_PRICE` (§ 6.2a), condition is `NEW`, the
   **delivered total** is under the ceiling, `itemEndDate` has not passed.
4. **A dedicated verdict function** — *not* `_verdict_from_html`, whose
   first-party logic cannot be satisfied on eBay (§ 5). Same three-state
   contract, different trust rules, and the UNKNOWN paths enumerated explicitly:
   token refused, HTTP error, zero results **with a red control**, shipping cost
   unresolvable, `buyingOptions` missing from a summary.
5. **A control query**, mandatory per REQ-06, and here it is the thing that makes
   a zero-result reading mean anything at all.
6. **Fixtures**: saved JSON responses so the offline suite runs with no key —
   the pattern already used for retailer HTML, and the thing that keeps CI green
   for contributors who have no eBay account.

**Secrets:** `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` in
`~/.config/boty/env` at mode 600, per the existing NFR. Note the redaction
trap that already caught `check_bestbuy_api`: `boty.status.write` copies
`Result.url` and `Result.detail` verbatim into a file served over HTTP. The eBay
credential appears in a **POST body and an `Authorization` header** rather than
in a URL, which is safer — but `curl_cffi` error strings can echo request
detail, so route every failure path through a redactor from the first commit
rather than after the first leak.

---

## 9. Recommendation, in one paragraph

Build it. There is no open-source eBay monitor worth integrating — the field is
three abandoned search scrapers, all fetching a path eBay's `robots.txt`
disallows, none with any concept of a reading it does not trust — and the one
maintained API client, `ebay-rest`, is 289,045 lines of generated code and seven
runtime dependencies to wrap two HTTP calls, against a project that is 3,520
lines total. Call eBay's own Browse API directly with the `curl_cffi` transport
already in `boty/fetch.py`: Buy It Now is its default, its filters cover the
price ceiling and condition, and 5,000 calls/day is seventeen times the 5-minute
cadence. Take no new dependency. Ship eBay as an **optional** retailer that
`INCOMPLETE`s out of a fresh clone without credentials, exactly as the browser
extra already does. And **make the first plan a probe, not a build** — one real
`item_summary/search` call whose status code settles the contradiction eBay's own
documentation has left standing (§ 6.2), because this repository has already
learned once, expensively, what it costs to decide a retailer's fate on a reading
of its documents without ever sending a request.

---

## Sources

Primary documents, all retrieved 2026-08-07 with status recorded:

- eBay `robots.txt` — https://www.ebay.com/robots.txt (HTTP 200, 18,810 B)
- eBay User Agreement — https://www.ebay.com/help/policies/member-behaviour-policies/user-agreement?id=4259 (HTTP 200)
- eBay API License Agreement — https://www.developer.ebay.com/join/api-license-agreement (HTTP 200; grepped, not read in full)
- Buy APIs Requirements — https://www.developer.ebay.com/api-docs/buy/buy-requirements.html (HTTP 200)
- Buy APIs Overview — https://www.developer.ebay.com/api-docs/buy/buy-overview.html (HTTP 200)
- Browse API guide — https://www.developer.ebay.com/api-docs/buy/api-browse.html (HTTP 200)
- Buy API Field Filters — https://www.developer.ebay.com/api-docs/buy/static/ref-buy-browse-filters.html (HTTP 200)
- API Call Limits — https://www.developer.ebay.com/develop/get-started/api-call-limits (HTTP 200)
- API Deprecation Status — https://www.developer.ebay.com/develop/get-started/api-deprecation-status (HTTP 200)
- Live API probes — `POST https://api.ebay.com/identity/v1/oauth2/token` → HTTP 401; `GET https://api.ebay.com/buy/browse/v1/item_summary/search` → HTTP 403

Package and repository metadata (PyPI JSON API, GitHub API, published wheel):

- https://pypi.org/pypi/ebay-rest/json · https://github.com/matecsaj/ebay_rest
- https://pypi.org/pypi/ebaysdk/json · https://github.com/timotheus/ebaysdk-python
- https://pypi.org/pypi/ebayfeed/json · https://pypi.org/pypi/python-ebay/json
- https://github.com/samjmck/ebay-monitor · https://github.com/Igor-Kaminski/ebay-price-monitor
- https://github.com/dgtlmoon/changedetection.io · https://github.com/eBay/ebay-oauth-python-client
- https://pypi.org/simple/ (865,857 names enumerated; 63 matching `ebay`)

Secondary (search-engine sourced, LOW confidence per `gsd-tools query classify-confidence`):

- Marketplace Insights limited-release status and Terapeak Store requirement — https://sold-comps.com/alternatives, https://community.ebay.com/t5/eBay-APIs-Talk-to-your-fellow/Marketplace-Insights-API-access/td-p/34838736
- Developer program registration timing — https://developer.ebay.com/api-docs/static/gs_join-the-ebay-developers-program.html (via search summary; the page itself returned HTTP 403 to direct fetch)
- Finding/Shopping decommission announcement — https://developer.ebay.com/updates/newsletter/q3_2024 (corroborated by the deprecation-status page above, which **is** primary)
