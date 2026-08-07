# eBay access surface — what bot-y could read, and what nobody has measured yet

**Researched:** 2026-08-07, from danserver over a residential connection.
**Scope:** how bot-y could read eBay **Buy It Now** listings for a Pokémon GO Plus +.
**Requests made to eBay listing or search pages: zero.** Deliberately, per the
brief. Everything below that is a measurement came from `robots.txt`, published
policy documents, or `developer.ebay.com` documentation. Everything that is not
a measurement is labelled **UNMEASURED**, with the probe that would settle it.

This file is research, not evidence. It does not carry an anchored verdict line
and must not be read as one — `docs/retailer-evidence.md` is where a verdict
lives, and eBay has no row there yet. If one were opened today the honest line
would be the third form, `**Verdict: UNPROBED (scoped 2026-08-07)**`, because the
single question that decides eBay's rung — *does a production keyset issued to an
ordinary person actually serve `item_summary/search`?* — has not been asked of
eBay's servers by anybody in this repository.

---

## What was actually requested

Every row is a real request made while writing this file. The column that
matters is the last one: nothing in it is a listing or a search page.

| Target | Transport | Result |
|---|---|---|
| `https://www.ebay.com/robots.txt` | `curl`, 18:42:08Z | **HTTP 200**, **18,810 B**, `text/plain`, **808 lines**, **20** `User-agent` groups, **7** `Sitemap:` directives, **0** `Crawl-delay` |
| `https://www.ebay.com/help/policies/member-behaviour-policies/user-agreement?id=4259` | `curl`, 18:49:05Z | **HTTP 200** — but **redirected to `https://www.ebay.com/splashui/captcha?ap=1&appName=orch&ru=…`**, **39,100 B**, `<title>Security Measure \| eBay</title>`. See § *The captcha `BLOCK_PHRASES` would not catch* |
| the same URL, 27 s later | `boty.fetch.get` (curl_cffi Chrome impersonation), 18:49:32Z | **HTTP 200**, **400,878 B**, no redirect, `<title>User Agreement \| eBay</title>`, **no `BLOCK_PHRASES` match** |
| `https://developer.ebay.com/api-docs/buy/browse/overview.html` | `curl`, then `boty.fetch.get` | **HTTP 403** both times, **1,832 B** / **1,831 B**, `<title>Error Page \| eBay</title>` |
| `https://www.developer.ebay.com/api-docs/buy/static/buy-requirements.html` | `curl` | **HTTP 200**, **173,200 B** — the `www.` host served what the bare host refused |
| the same `www.developer.ebay.com` host, 7 further doc URLs at ~3 s spacing | `curl` | **HTTP 403 × 7**, 1,831–1,832 B each |
| 12 developer-doc URLs | `web.archive.org` `…id_/` raw snapshots | HTTP 200, 40 KB – 1.5 MB, snapshots dated 2025-11 to 2026-06 |

**Three requests total to `www.ebay.com`.** One to the file whose entire purpose
is to be fetched by an automated agent, and two to a published policy page — the
same shape as the Amazon and Pokémon Center policy reads. **Zero to `/itm/`,
zero to `/sch/`, zero to any sitemap.**

Two rows in that table are findings in their own right and are written up below:
eBay serves a captcha to plain `curl` on a *help* page, and `developer.ebay.com`
refuses both `curl` and this project's own impersonated transport while
`www.developer.ebay.com` does not.

---

## 1. The official API surface

### The Finding API is gone, and that matters for prior art

> The traditional Finding API and Shopping API are now deprecated as of
> 2024/01/04. They will be decommissioned on 2025/02/05.

— eBay Developers Program Q3 2024 newsletter, via the community alert thread
([community.ebay.com](https://community.ebay.com/t5/Traditional-APIs-Search/Alert-Finding-API-and-Shopping-API-to-be-decommissioned-in-2025/td-p/34222062),
[developer.ebay.com/updates/newsletter/q3_2024](https://developer.ebay.com/updates/newsletter/q3_2024)).

**Confidence: MEDIUM.** (`gsd-tools query classify-confidence --provider
websearch --verified` → `MEDIUM`; cross-checked against the Browse API
overview's own "Related Docs" list, which still links Finding and Shopping as
legacy.) This matters mainly as a warning about prior art: most "eBay stock
tracker" writing on the internet older than about two years is built on
`findItemsAdvanced` with a **bare App ID in a query string and no OAuth at all**.
That surface no longer exists. The `ebay-find-api` package on GitHub is
explicitly marked `DEPRECATED`. Any recipe that does not mention OAuth is
describing a dead API.

### The Browse API is the surface

Two calls do everything bot-y would need
([api-docs/buy/browse/overview.html](https://developer.ebay.com/api-docs/buy/browse/overview.html)):

| Call | What it answers |
|---|---|
| `GET /buy/browse/v1/item_summary/search` | *Is anyone selling a GO Plus + right now, and at what price* |
| `GET /buy/browse/v1/item/{item_id}` | *Is this specific listing still buyable* — carries `estimatedAvailabilityStatus` and `itemEndDate` |

**`search` returns Buy It Now by default, and that is stated as a restriction
rather than a convention.** Verbatim from the overview's *Search method
restrictions*:

> Only FIXED_PRICE (Buy It Now) items are returned by default. However, these
> methods do return items where both FIXED_PRICE and AUCTION are available as a
> buying option. After a bid has been placed, items become active auction items
> and are no longer returned by default, but they remain accessible by filtering
> for the AUCTION buying option.

So the "Buy It Now only" half of the brief is the API's *default behaviour*, not
something an adapter has to implement. Two further restrictions from the same
section: a result set caps at **10,000 items**, and wildcards (`q=*phones`) are
rejected outright.

### Auth: OAuth client-credentials, base scope, two-hour token

Both `item_summary/search` and `item/getItem` carry the identical scope
statement in their reference pages:

> This request requires an access token created with the client credentials
> grant flow, using one or more scopes from the following list (please check
> your Application Keys page for a list of OAuth scopes available to your
> application):
> `https://api.ebay.com/oauth/api_scope`

([item_summary/search](https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search),
[item/getItem](https://developer.ebay.com/api-docs/buy/browse/resources/item/methods/getItem))

**That is the base scope every keyset is issued.** No `buy.*` scope, no user
consent, no `authorization_code` round trip, no user token. Mechanically:

```
POST https://api.ebay.com/identity/v1/oauth2/token
Authorization: Basic <base64(AppID:CertID)>
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope
```

→ `{"access_token": "…", "expires_in": 7200, "token_type": "Application Access Token"}`

([oauth-client-credentials-grant.html](https://developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html))

**`expires_in` is 7200 — two hours.** An adapter must mint and cache; it cannot
mint per poll, because the token endpoint carries its own separate daily limit,
from the same page:

| grant_type | Limit |
|---|---|
| `client_credentials` | **1,000 requests/day** |
| `authorization_code` | 10,000 requests/day |
| `refresh_token` | 50,000 requests/day |

Minting once per 300 s pass would be 288/day — under the cap, but ~24× more
requests than the 12/day a 2-hour cache needs, and it burns a fifth of a limit
that exists for no other reason.

### Rate limits on the free tier

From [API Call Limits](https://developer.ebay.com/develop/apis/api-call-limits):

> **Browse API \*** — 5,000 API calls per day
>
> \* Buy APIs require an additional license. See the API documentation for details.

and, above the table:

> After you join the eBay Developers Program and get your application keyset,
> you can start using eBay APIs immediately. The default call limits on the eBay
> APIs allow you to test and explore the API capabilities. Many applications are
> able to perform all capabilities using the default limits. If you need higher
> call limits, you can complete our Application Growth Check…

**5,000/day against bot-y's own arithmetic.** `config/products.yaml` already
documents the sum that bit Amazon and GameStop on 2026-08-04: real load is
`watches × 288` per day at the 300 s default. One eBay search watch is
**288 calls/day — 5.8 % of the cap**; ten watches would be 58 %. This is the
first retailer in this project where the ceiling is a *published number* rather
than an unknown discovered by being refused.

### Fields returned — every one bot-y needs, in the *search* response

From the `item_summary/search` reference's own sample payload, unedited except
for eBay's own masking of the seller name and item ID:

```json
{
  "price":          { "value": "59.99", "currency": "USD" },
  "seller":         { "username": "m********e",
                      "feedbackPercentage": "98.6", "feedbackScore": 130000 },
  "condition":      "New",
  "conditionId":    "1000",
  "buyingOptions":  ["FIXED_PRICE", "BEST_OFFER"],
  "shippingOptions":[{ "shippingCostType": "FIXED",
                       "shippingCost": { "value": "0.00", "currency": "USD" } }],
  "itemWebUrl":     "https://www.ebay.com/itm/1**********1?hash=…",
  "itemHref":       "https://api.ebay.com/buy/browse/v1/item/v1******************0",
  "itemLocation":   { "postalCode": "0****", "country": "US" },
  "legacyItemId":   "1**********1",
  "marketingPrice": { "originalPrice": { "value": "74.99", "currency": "USD" },
                      "discountPercentage": "20", "priceTreatment": "LIST_PRICE" }
}
```

Mapped onto `boty.parse.Offer` and `boty.models.Result`:

| bot-y needs | eBay field | Note |
|---|---|---|
| `price` | `price.value` | **item price only — shipping is not in it** |
| currency | `price.currency` | |
| `available` | *presence in a `search` result set* | `search` returns live listings; an explicit status lives only on `getItem` |
| `seller` | `seller.username` | an eBay user ID, never a retailer name — see § 4 |
| Buy-It-Now vs auction | `buyingOptions[]` — `FIXED_PRICE` / `AUCTION` / `BEST_OFFER` / `CLASSIFIED_AD` | |
| condition | `condition` (string) **and** `conditionId` (numeric) | |
| item URL | `itemWebUrl` | a `/itm/<legacy id>` URL with a tracking `hash` query |

`item/getItem` adds the two fields that make an explicit stock verdict possible:

> `estimatedAvailabilityStatus` — An enumeration value representing the inventory
> status of this item. **Note: Be sure to review the `itemEndDate` field to
> determine whether the item is available for purchase.** Valid Values:
> `IN_STOCK`, `LIMITED_STOCK`, or `OUT_OF_STOCK`.

> To see if a listing is available for purchase, review the `itemEndDate` and
> `estimatedAvailabilityStatus` fields. If the item has an EndDate in the past,
> **or** the `estimatedAvailabilityStatus` is `OUT_OF_STOCK`, the item is
> unavailable for purchase.

That is a **two-field** availability contract, and an adapter reading only the
status enum will report a *finished* listing as in stock.

**Confidence on this whole section: HIGH.** Every quotation is from eBay's own
reference documentation retrieved verbatim (via `www.developer.ebay.com` and
`web.archive.org` raw `id_` snapshots), not summarised from a search result.

---

## 2. Where eBay lands on the ladder — and the sentence that decides it

**This is the decisive question and the research does not settle it. What
follows is the disagreement, stated as a disagreement.**

### The registration flow, step by step, from eBay's own page

[Create the eBay API keysets](https://developer.ebay.com/api-docs/static/gs_create-the-ebay-api-keysets.html),
verbatim:

> 1. Sign in to your eBay Developers Program account.
> 2. Go to the Application Keys page.
> 3. Enter your application name. Under either Sandbox or Production, click
>    **Create a keyset**.
>
> **Important!** Before you can use your Production keyset, you must subscribe to
> or opt out of **eBay marketplace account deletion/closure notifications**. If
> you see the "Your Keyset is currently disabled" message, click the link in the
> message to begin the compliance process.

and, from the developer-program landing page: *"Not a member? It's free to join
the eBay Developers Program!"*

So on this reading: **free, self-serve, no approval, no non-free email domain, no
commercial agreement.** Three clicks and a gate.

**The gate is real but it is also self-serve.** The
[marketplace account deletion](https://developer.ebay.com/develop/guides-v2/marketplace-user-account-deletion)
guide describes two ways past it:

> New third-party developers coming to the platform must subscribe to or opt out
> of eBay marketplace account deletion/closure notifications **before they make
> their first production API call**. Once the new developer's application is
> subscribed …, or they have successfully opted out …, the keyset/App ID is
> activated and they can begin making API calls.

Subscribing means standing up an **https endpoint that answers eBay's challenge
code with a SHA-256 of `challengeCode + verificationToken + endpoint`** — the doc
is explicit that `localhost` and internal IPs are rejected. A person cloning this
repo to watch one accessory has no such endpoint. But the *opt-out* is described
as a portal toggle:

> On the Marketplace Account Deletion page, slide the **Not persisting eBay data**
> toggle button to On. […] Select the Exemption reason radio button that applies
> to you. […] Click the Submit button to complete the exemption request.

No review, no waiting period and no counterparty is described. bot-y persists no
eBay user data — it reads a price and forgets it — so the exemption is the honest
one, not a dodge. **This is friction, not approval.**

### The sentence that says the opposite

The Browse API overview's own *eBay policies and rules* section:

> Although the eBay Buy APIs are available for anyone to use in eBay's sandbox
> environment, **use of the APIs in production is restricted. Users must meet
> standard eligibility requirements, get approvals from eBay support
> organizations, and sign contracts with eBay to access the Buy APIs in
> production.**

and, in more detail, [Buy APIs Requirements](https://developer.ebay.com/api-docs/buy/static/buy-requirements.html):

> Many of the Buy APIs are a **(Limited Release)**. The use of eBay's Buy APIs in
> production is intended for eBay partners only. **You must apply for production
> access through the eBay Partner Network.** Acceptance of applications is based
> on the proposed business model, as well as a formal agreement to abide by the
> policies and requirements stipulated by eBay.
>
> **Note:** There is no guarantee that your application for production use of the
> APIs will be approved.

The documented process is: join eBay Partner Network → submit a Buy API
Application → reply with mocks and data flows → **within 10 business days** EPN
approves or declines → open a Developer Support ticket → compliance review →
sign contracts. That is Best Buy's wall with an extra floor on top. Measured
against `.planning/REQUIREMENTS.md`'s *Works from a fresh clone*, it is a
disqualification: a commercial agreement and a discretionary approval is exactly
the class of credential that requirement names.

### The three things that cut against reading that sentence literally

1. **The scope.** If Browse `search` needed partner status, it would need a
   partner scope. It does not — the reference page names
   `https://api.ebay.com/oauth/api_scope`, the default scope on every keyset.
   Compare `Marketplace Insights`, which *is* gated: it is tagged
   **(Limited Release)** in its own title and eBay's own docs are quoted as
   saying it is "restricted and not open to new users at this time".
   **The Browse API reference pages carry no such tag anywhere I could find.**
2. **The hedge in the requirements page's own first word.** "**Many** of the Buy
   APIs are a (Limited Release)" — not *all*. The page then enumerates
   per-API sections for Browse, Charity, Deal, Feed, Marketing, Offer and Order.
   Everything else in the page is about *checkout*: the `guest_checkout_session`
   and `checkout_session` resources, EPN affiliate tracking, revenue share, UX
   requirements for a Buy button. It reads as a document about **transacting**,
   with a blanket header that also covers reading.
3. **The rate-limit table treats Browse as an ordinary self-serve API**: 5,000
   calls/day "designed for individuals and smaller businesses", raised via the
   Application Growth Check, sitting in the same table as the Sell APIs that
   anybody can call.

Community answers point the same way — that the client-credentials scope is
sufficient for Browse and that EPN membership is needed for *affiliate features
and guest checkout*, not for search
([RESTful Buy APIs: Browse forum](https://community.ebay.com/t5/RESTful-Buy-APIs-Browse/bd-p/RESTful-Buy-APIs-Browse)).
**Confidence on that: LOW** (`classify-confidence --provider websearch` → `LOW`,
un-cross-checked forum prose). It is a hypothesis, not a finding, and it is
recorded here as one.

### So: what the ladder says today

**UNMEASURED, and it is the only question that matters.** The two readings give
opposite rungs:

| If… | Then eBay is… | Precedent in this repo |
|---|---|---|
| a self-serve production keyset serves `item_summary/search` | **rung 2, `structured`** — the project's first true rung-2 PRIMARY path, and the most trustworthy adapter in the tree | none — nothing here has ever been rung 2 by default |
| production Browse genuinely requires EPN approval and signed contracts | **not rung 2 for a fresh clone.** An OPTIONAL enhancement at best, exactly as `check_bestbuy_api` is | REQ-04 / Best Buy |

**The probe that settles it**, and it is small:

1. Register a developer account with a free email address, create a **production**
   keyset, take the account-deletion exemption. Record every screen that asks for
   something a fresh-clone user could not give (a company, a domain, a tax form,
   an EPN membership). **If any screen does, that is the answer and no HTTP
   request is needed.**
2. Mint a `client_credentials` token against `api.ebay.com`. Record the HTTP
   status and, on failure, the `error`/`error_description` body.
3. `GET /buy/browse/v1/item_summary/search?q=pokemon+go+plus&limit=3` with
   `X-EBAY-C-MARKETPLACE-ID: EBAY_US`. Record the status, the byte count, and
   `total`.

A **200 with a populated `itemSummaries`** makes eBay rung 2. A **403 with
`Insufficient permissions to fulfill the request`** (the documented shape of an
unapproved Buy API call) makes it Best Buy's row. Either outcome is one
paragraph in `docs/retailer-evidence.md`; there is no third result that leaves
this open. **Doing this before roadmapping an eBay phase is worth more than any
further reading**, because the phase is a different phase in each branch.

---

## 3. Rung 1 — robots.txt, the terms, and what the page actually contains

### `robots.txt`, measured

`https://www.ebay.com/robots.txt`, **HTTP 200, 18,810 B, 808 lines, 20
`User-agent` groups, 0 `Crawl-delay`**, version marker `v29_COM_July_2026`.

**Its header comment is a policy statement, and it is stronger than Amazon's
file:**

```
# The use of robots or other automated means to access the eBay site
# without the express permission of eBay is strictly prohibited.
# Notwithstanding the foregoing, eBay may permit automated access to
# access certain eBay pages but solely for the limited purpose of
# including content in publicly available search engines.
#
# Robots & Agent Policy
#
# Checkouts are strictly for human users.
# * Automated scraping, buy-for-me agents, LLM-driven bots, or any
#   end-to-end flow that attempts to place orders without human review
#   is strictly prohibited.
# * Unauthorized use of automated agents in checkout may result in
#   legal action under our User Agreement: …
# * Approved enterprise integrations must use our official API and
#   comply with our API License Agreement: …
```

Amazon's `robots.txt` disagreed with its Conditions of Use in the *narrower*
direction — the directives permitted `/dp/` while the terms forbade collecting
prices. **eBay's file does not leave that gap open**: the prohibition is written
into the file itself, in a comment, above the directives. There is no reading of
eBay under which robots.txt is the permissive document.

**The directives, in the `User-agent: *` group (lines 29–262), on the two paths
that matter:**

| Path | Rule | Line |
|---|---|---|
| `/sch/` — **all keyword search** | `Disallow: /sch/` | 211 |
| `/sch/i.html?_nkw=` — the keyword-search URL form | `Disallow: /sch/i.html?_nkw=` | 209 |
| `/sch/i.html?*_nkw=*&` | `Disallow` | 210 |
| `/sch/*_sacat=` (category search) | `Disallow` | 212 |
| `/sch/ebayadvsearch`, `/sch/allcategories/`, `/sch/*_ul`, `/sch/*_fosrp`, `/sch/*_trksid`, `/sch/i.html?*&mkcid=2` | `Allow` | 203–208 |
| **`/itm/<id>` — the bare item page** | **no rule matches it** | — |

**Search is closed and item pages are open**, which is precisely the inverse of
what a search-shaped watch wants. Twenty `/itm/` rules exist and every one of
them is narrower than the bare path:

```
Disallow: /itm/*/browser.json      Disallow: /itm/addToCart
Disallow: /itm/*action=BESTOFFER   Disallow: /itm/fetchmodules
Disallow: /itm/*_nkw               Disallow: /itm/sellerInfoV2
Disallow: /itm/*_pgn=              Disallow: /itm/soi
Disallow: /itm/*?fits              Disallow: /itm/variationlogistics
Disallow: /itm/*&fits              Disallow: /itm/watch/
Disallow: /itm/*, /itm/*.jpg /itm/*/% /itm/*/[ /itm/*/%7B%7B /itm/:/ /itm/*boolp=
```

Two observations on that list. First, `Disallow: /itm/*action=BESTOFFER` closes
the *Best Offer* surface specifically — the one § 4 wants for the "is this a good
deal" question. Second, **`/itm/*/browser.json`, `/itm/fetchmodules` and
`/itm/sellerInfoV2` are the names of JSON endpoints**, which is circumstantial
evidence that an item page hydrates from a per-item JSON API — *inference, not
measurement*, and it is exactly the kind of thing that turned out to be true at
Target (`redsky.target.com`) and false at Amazon. Whatever they are, all three
carry a `Disallow` and bot-y must not touch them.

**Seven `Sitemap:` directives** — `AUCTION`, `BROWSE`, `KWSRP`, `NGS`, `PRP`,
`VIDEO`, `VIS` index files under `/lst/`. Unlike Amazon (no `Sitemap:` at all),
eBay publishes a sanctioned discovery path. **None of them was fetched.**

**One group worth naming.** `ClaudeBot`, `anthropic-ai`, `GPTBot`, `CCBot`,
`PerplexityBot`, `Bytespider`, `AmazonBot`, `meta-externalagent` and
`Applebot-Extended` share a group with `Disallow: /` and a short `Allow` list
that does **not** include `/itm/`. `Claude-User`, `Claude-SearchBot`,
`OAI-SearchBot` and `ChatGPT-User` are held to the same rules as `*`. bot-y sends
neither — `boty.fetch` impersonates Chrome — but the file's intent is not
ambiguous.

### The User Agreement, quoted in full on the operative clause

Retrieved 2026-08-07 at 18:49:32Z by `boty.fetch.get` from
`https://www.ebay.com/help/policies/member-behaviour-policies/user-agreement?id=4259`
(HTTP 200, 400,878 B). The clause appears **twice** in the document, identically
— the page serves two dated versions of the agreement, one *"effective as of
June 28, 2026"* and one *"effective … from February 20, 2026 for existing
users"*, and the wording below is the same in both:

> use any **robot, spider, scraper, data mining tools, data gathering and
> extraction tools, or other automated means** (including, without limitation
> **buy-for-me agents, LLM-driven bots**, or any end-to-end flow that attempts
> to place orders without human review) **to access our Services for any
> purpose, except with the prior express permission of eBay**;

and, in the same list:

> circumvent any technical measures used to provide our Services;

> interfere with the functioning of our Services, such as by imposing an
> unreasonable or disproportionately large load …

> harvest or otherwise collect or use information about users without their
> consent.

**Where this sits relative to the two clauses already in this repo.** Pokémon
Center forbids the *method*. Amazon forbids the method **and** independently
forbids "any collection and use of any product listings, descriptions, or
prices". eBay forbids the method **for any purpose** and, uniquely, names the
carve-out: *"except with the prior express permission of eBay"* — and then tells
you where that permission lives, in the robots.txt comment: *"Approved enterprise
integrations must use our official API and comply with our API License
Agreement."*

**That is the sharpest terms position of any retailer in this project, and it is
also the clearest.** eBay does not merely forbid scraping; it points at a
sanctioned door and says *use that one*. Which makes the § 2 question — is that
door actually open to an individual — the whole ballgame, and makes a rung-1
eBay adapter the one path this project should be least comfortable with. Note
also that "circumvent any technical measures" is a live clause given what the
next subsection measured.

The API License Agreement is not a way around it either. Its updated text
defines:

> "**Restricted APIs**" refers to any eBay APIs that provide information about
> market trends, pricing strategies, sales volumes, user behavior, or provide
> generated content (including content using artificial intelligence in response
> to your inputs). **Access is specially granted to select Developers.**

That definition reaches Marketplace Insights (§ 4) squarely. Whether it reaches
Browse `search` is not stated. **UNMEASURED.**

### The captcha `BLOCK_PHRASES` would not catch

**This is the finding most likely to cost somebody a day, and it is the fourth
time this repository has met the same defect.**

A plain `curl` GET to a *help* page — not a listing, not a search, a published
policy document — came back as:

**Refusal observed (rung 1):** `https://www.ebay.com/help/policies/member-behaviour-policies/user-agreement?id=4259` — **HTTP 200**, **39,100 B**, redirected to `https://www.ebay.com/splashui/captcha?ap=1&appName=orch&ru=…`, `<title>Security Measure | eBay</title>`, body reading "Please verify yourself to continue", **zero `boty.fetch.BLOCK_PHRASES` entries matched**.

(One line, deliberately, because `evidence_check` rule 6's regex is line-anchored
and a measurement that wraps is one it cannot read. That line is written in the
`**Refusal observed (rung N):**` form so it can be lifted into
`docs/retailer-evidence.md` unchanged — but it is **not** evidence of a refusal
of *bot-y*, because the very next request, impersonated, went straight through.
It is evidence that **eBay's wall is invisible to the current block-phrase
list**.)

Verbatim from the wall:

> To keep eBay a safe place to buy and sell, we will occasionally ask you to
> verify yourself. This helps us to block unauthorized users from entering our
> site.

`boty.fetch.get` would return that as an ordinary `Page`. Downstream it reads as
`no structured stock data found (page shape changed?)` — fail-safe in outcome,
and a diagnosis blaming our parser for eBay's refusal. **That is verbatim the
Imperva defect of 02-04, the Akamai defect of the fifth-retailer search, and the
Amazon defect of 03.1-03, on a fourth vendor.** `boty.fixtures.capture` would
write it to disk under a product's name.

**Candidate block phrases, and why none of them should be added yet.** The
durable structural marker is `splashui` — it appears 4× in the body
(`splashui-5.0.1_20260806054723987`, `splashui6cont`) as well as in the URL. The
human wording is `please verify yourself to continue`; the title is
`security measure | ebay`. **All three are unproven against a real eBay product
page, because this research made no request to one.** `BLOCK_PHRASES`'s own
docstring is explicit that a phrase must appear on the wall *and nowhere else*,
and this project has already burned that lesson twice — `datadome` was rejected
because it appears on working Pokémon Center pages, and Amazon's
`"something went wrong on our end"` was rejected because it appears on both real
Amazon product pages this repo has fetched. Note that eBay's **403 error page**
also reads *"Something went wrong on our end"* (measured, § *What was actually
requested*), which is the same trap a third time.

**The measurement that would settle it:** one `boty.fetch.get` to a single
`/itm/<id>`, and `grep -ci` for each candidate in the returned bytes. A phrase
with **zero** occurrences on a real product page is safe; a phrase with one is
the bad bet.

### Does eBay serve rung 1 at all?

**Partially measured, and the part measured is encouraging.** The same URL, 27 s
apart:

| Transport | Result |
|---|---|
| `curl` (default TLS fingerprint) | captcha splash, 39,100 B |
| `boty.fetch.get` (curl_cffi Chrome impersonation) | **HTTP 200, 400,878 B, correct page, no challenge** |

So eBay does *TLS-fingerprint* discrimination on `www.ebay.com`, and this
project's existing transport is already on the right side of it — for a help
page. **That is not the same claim as "eBay serves `/itm/` at rung 1", and this
document does not make that claim.** Retailers routinely defend product paths
harder than help paths; Best Buy refuses some product URLs and serves others.

`developer.ebay.com` is a useful counter-example measured here: it returned
**HTTP 403 to `curl` and HTTP 403 to `boty.fetch.get` alike** — impersonation did
not help — while `www.developer.ebay.com` served the same document at **HTTP 200,
173,200 B**. Then, after 7 more requests at 3 s spacing, the `www.` host began
returning **403 × 7**. Two lessons: **the block is per-host and per-cadence, not
per-fingerprint**, and eBay's infrastructure throttles on rate faster than
Amazon's did (Amazon needed 12 s spacing to trip; this tripped at 3 s).

### Is an item page `structured` or `dom`?

**UNMEASURED. This is the single biggest gap in this document and it is stated
as one rather than guessed at.**

What can honestly be said: eBay listings appear in Google with price and
availability rich results, which requires *some* machine-readable markup, and
generic industry writing describes eBay as using schema.org markup
([ryte.com](https://en.ryte.com/magazine/structured-data-changed-everything-ebay/)).
**Confidence: LOW** (`classify-confidence --provider websearch` → `LOW`). That is
a plausibility argument, not an observation, and by rule 6's standard it is
worth nothing. A Google rich result can be produced by microdata, by RDFa, by a
Merchant Center feed or by Google's own extraction — none of which is a
`<script type="application/ld+json">` a Python parser can read.

**The probe, and it is the same one 03.1-03 ran against Amazon:** one
`boty.fetch.get` to one `/itm/<id>`, then

| Reader | Question |
|---|---|
| `parse.ldjson_read` | does it return offers? |
| `parse.nextdata_offers` | is there a `__NEXT_DATA__`? |
| `count of application/ld+json` | how many blocks? |
| `count of schema.org` | any `Product` node? |
| `parse.add_to_cart_offers` | is there a readable buy control? |

Amazon's answers were `None / None / 0 / 1 (a CSS mention) / yes`, which is how
it landed at rung 1 + `dom`. Until the same table exists for eBay, **the
Extraction cell for an eBay row is `—`, not a guess.**

---

## 4. The "low price" problem — and the structural mismatch nobody has named

### eBay has no first party, and bot-y's core filter assumes one

**This is the finding that most changes what an eBay phase would have to build.**

`boty.retailers.FIRST_PARTY` maps a retailer to the seller strings that mean
"the retailer itself". `MARKETPLACES` names the retailers where a third party
can hold the buy box. Every existing entry works because the retailer *is* also a
seller: `amazon` → `"Amazon.com"`, `bestbuy` → `"Best Buy"`, `walmart` →
`"walmart.com"`.

**eBay is never a seller.** `seller.username` is always an eBay member's user ID.
There is no first-party string that could go in `FIRST_PARTY["ebay"]` and no page
state that could mean "sold by eBay". So:

- `FIRST_PARTY["ebay"] = set()` + `first_party_only=True` → `_pick` returns
  `None` on the `named` branch, `unattributed` is empty because eBay would be in
  `MARKETPLACES`, and `_verdict_from_html` falls to
  `Availability.OUT_OF_STOCK, "N offer(s) …, none first-party"`. **A confidently
  wrong OUT_OF_STOCK, which is the one outcome this project exists to prevent.**
- Omitting `ebay` from `FIRST_PARTY` entirely → the "no first-party seller list
  is configured" branch → permanent UNKNOWN, permanent health warning. Honest,
  but useless.

Neither is right. eBay needs a **third** shape: *no first party exists, so the
seller filter is an allow-list or a reputation floor rather than an identity
check.* That is new behaviour in `_pick`, not configuration, and it is the part
of an eBay phase most likely to be under-estimated. It should be planned as
adapter-plus-`_pick`-change, not adapter-only.

Note what this does to Target's precedent in reverse. Target's `FIRST_PARTY`
entry is a statement about *our own reader's output*
(`parse.TARGET_FIRST_PARTY_SELLER`), because Target publishes no seller name.
eBay publishes a seller name on every single offer and none of them is eBay. The
two are opposite problems and the same solution does not serve both.

### What eBay exposes that distinguishes a good deal from a bad one

All of these are `filter=` parameters on `item_summary/search`, from
[Buy API Field Filters](https://developer.ebay.com/api-docs/buy/static/ref-buy-browse-filters.html):

| Question | Filter | Verbatim note from the doc |
|---|---|---|
| Buy It Now only, exclude Best Offer | `filter=buyingOptions:{FIXED_PRICE}` | **"This filter is defined at the leaf category level and should be used with a leaf category ID. If this filter is used with a top-level category ID, it won't work and the filtered results won't be included in the response body."** |
| Price ceiling | `filter=price:[..80],priceCurrency:USD` | "This filter must be used with the `priceCurrency` filter." |
| New only | `filter=conditions:{NEW}` | "will not return items of a specific condition such as Good, Very Good, or Seller Refurbished. It will only return items … NEW and USED" |
| A precise condition | `filter=conditionIds:{1000}` | "New (1000), Good (5000), and Seller Refurbished (2500)" |
| Seller allow-list | `filter=sellers:{a\|b}` | "Valid Values: The sellers' eBay user ID." Max **250** sellers |
| Seller deny-list | `filter=excludeSellers:{a\|b}` | |
| Free shipping only | `filter=maxDeliveryCost:0` | "Only items with free shipping are returned." |
| Domestic only | `filter=deliveryCountry:US` | |
| Business vs individual seller | `filter=sellerAccountTypes:{BUSINESS}` | **Not supported on `EBAY_US`** — the supported list is AT, BE, CH, DE, ES, FR, GB, IE, IT, PL |

**How bot-y's two existing defences map on.**

- **The price ceiling (`max_price: 80`).** `Result.alertable` already returns
  False when a ceiling is set and `price is None` (the WR-01 hardening,
  `boty/models.py:73-75`). eBay always returns `price.value`, so that guard never
  fires — good. **But `price` is the item price and excludes shipping.** A $54.99
  listing with $29 shipping passes an `80` ceiling and is a flip. The correct
  reading is `price.value + shippingOptions[0].shippingCost.value`, and there are
  two traps in that sum: the container is **conditional**, and eBay's own
  documentation says accurate shipping needs a buyer postcode:

  > Note: This requires providing the buyer's US zip code in the
  > `X-EBAY-C-ENDUSERCTX` `contextualLocation` request header.

  i.e. `X-EBAY-C-ENDUSERCTX: contextualLocation=country%3DUS%2Czip%3D19406`.
  **That is a geolocation of the user, in a header, in a config file.** The
  Amazon fixture redaction of 03.1-03 exists because Amazon's own geolocation of
  this host leaked into a committed capture; an eBay adapter would put the ZIP
  there *on purpose*, so any eBay fixture needs it redacted by construction, and
  the value belongs in the env file rather than `config/products.yaml`.

  The alternative is `filter=maxDeliveryCost:0` — free shipping only — which
  sidesteps the sum entirely at the cost of missing genuine listings. It is the
  cheaper and more honest first cut.

- **The seller filter.** With no first party to check against, the eBay analogue
  is either `filter=sellers:{…}` (an allow-list of known-good sellers — but
  nobody knows them in advance for a GO Plus +) or a reputation floor read off
  `seller.feedbackPercentage` / `seller.feedbackScore`. The second is available
  on **every** search result with no extra call. Neither answers *"is this a
  reseller flipping at 4× MSRP"* — only the price ceiling does that.

### Best Offer

`buyingOptions` can contain `BEST_OFFER` alongside `FIXED_PRICE` — the sample
payload in § 1 shows exactly that combination. A Best Offer listing's `price` is
the asking price, and what a buyer would actually pay is unknown until an offer
is accepted. **For bot-y that is a reason to treat `BEST_OFFER` as noise**: the
displayed price is not a price the item can be bought at, and alerting on it
alerts on a negotiation. `filter=buyingOptions:{FIXED_PRICE}` does not exclude
it (the values are additive), so exclusion has to be done in the adapter by
checking `"BEST_OFFER" not in buyingOptions` — or, more honestly, by treating a
Best Offer listing's price as a ceiling rather than a price. Note also that the
web surface for Best Offer, `/itm/*action=BESTOFFER`, is `Disallow`ed, so there
is no rung-1 route to it either.

### A reference price from sold listings — effectively closed

The obvious "is $89 a good price for a GO Plus +" answer is the sold/completed
history. eBay has exactly one official surface for it and it is shut:

> The **Marketplace Insights API (Limited Release)** provides the ability to
> search for sold items on eBay by keyword, GTIN, category, and product and
> returns the sales history of those items. This method retrieves the sales
> history of items for the last 90 days.

It is documented as available "only to select developers approved by business
units", and eBay's documentation is reported to say it is "restricted and not
open to new users at this time"
([community thread](https://community.ebay.com/t5/eBay-APIs-Talk-to-your-fellow/Marketplace-Insights-API-access/td-p/34838736/)).
It also falls squarely inside the API License Agreement's **Restricted APIs**
definition — "information about market trends, pricing strategies, sales
volumes" — where "Access is specially granted to select Developers".
**Confidence: MEDIUM** (websearch, cross-checked against the ALA text retrieved
verbatim).

The web fallback is worse, not better: eBay's sold filter is
`/sch/i.html?…&LH_Sold=1`, and `/sch/` carries `Disallow: /sch/` **and**
`Disallow: /sch/i.html?_nkw=` in the `*` group. There is no permitted route to a
sold-price history.

**The honest conclusion: bot-y cannot compute an eBay reference price, and should
not pretend to.** It already has a better one — **MSRP $54.99, hard-coded as
`max_price: 80` in `config/products.yaml`, with the comment "MSRP is $54.99;
anything near $140 is a flip"**. That number came from the manufacturer, not from
a market, and it is exactly the right anchor for a project whose thesis is *never
"in stock" when the truth is "a reseller has one at 4× MSRP"*. Trying to derive a
market reference price from eBay would replace a fact with an average of the
behaviour the tool exists to resist.

---

## 5. Traps

Ordered by how likely each is to produce a *silently wrong* reading rather than a
loud failure — the project's own ordering.

### Silent-wrong

1. **`price` excludes shipping.** § 4. A ceiling comparison against `price.value`
   alone under-counts. Loud symptom: none. This is the trap most likely to send
   the alert this project exists not to send.
2. **Availability is two fields, not one.** `estimatedAvailabilityStatus ==
   IN_STOCK` on a listing whose `itemEndDate` is in the past is *not* buyable —
   eBay's own doc says so twice. An adapter reading one field reports ended
   listings as live.
3. **`buyingOptions` filter silently no-ops on a non-leaf category.** eBay's
   words: *"If this filter is used with a top-level category ID, it won't
   work and the filtered results won't be included in the response body."* No
   error. An adapter that thinks it is filtering to Buy It Now, is not.
4. **Search index lag.** Community reports put Browse `search` **10–15 minutes**
   behind the web index, with intermittent omissions of items that are genuinely
   listed
   ([thread](https://community.ebay.com/t5/RESTful-Buy-APIs-Browse/Ebay-Browse-API-finding-most-but-not-all-listings-Missing-items/td-p/34475520)).
   **Confidence: LOW** (websearch, un-cross-checked, and eBay publishes no SLA on
   freshness). For a restock monitor this is the difference between winning a
   drop and reading about it. It also means **absence from a search result set is
   not evidence of absence** — an eBay adapter must return UNKNOWN, never
   OUT_OF_STOCK, when a search comes back empty, and that is the opposite of the
   natural reading of an empty list.
5. **The captcha at HTTP 200.** § 3. No current `BLOCK_PHRASES` entry matches it.
6. **`shippingOptions` is a *conditional* container.** Absent means "eBay did not
   compute one", not "free". Defaulting a missing shipping cost to `0` turns
   trap 1 into a guarantee.
7. **Seller usernames are being replaced.** `developer.ebay.com` currently
   carries a site-wide banner: *"eBay's API integrations will be modified to
   address data handling requirements for select developers. **Usernames will be
   replaced with immutable user IDs**, and financial data will be protected for
   certain users."* Any `filter=sellers:{…}` allow-list or `seller.username`
   comparison is keyed on a value eBay has announced it will change. **UNMEASURED
   scope and date** — the banner links to a "Learn more" page not retrieved here.

### Loud

8. **Sandbox vs production are different hosts *and* different keysets.**
   `api.sandbox.ebay.com` vs `api.ebay.com`; a sandbox keyset against production
   is an auth failure, and sandbox has no real GO Plus + listings, so a green
   sandbox test proves nothing about the shipped monitor. A control watch must
   run against production or it is theatre — the same argument
   `config/products.yaml` already makes for control products.
9. **Marketplace ID.** `X-EBAY-C-MARKETPLACE-ID` defaults to `EBAY_US` when
   absent *or invalid* — eBay's getItem doc: *"If the marketplace ID value is
   invalid or missing, the default value of EBAY_US is used."* A typo therefore
   does not error, it silently succeeds against the wrong (right, here)
   marketplace. Send `EBAY_US` explicitly.
10. **Token expiry at 7200 s.** A long-running `boty.service` must refresh, and
    the refresh has its own **1,000/day** budget. Cache the token; do not mint
    per pass.
11. **Two IDs for one thing.** RESTful `itemId` is `v1|<legacy id>|<variation>`;
    `legacyItemId` is the number in the `/itm/` URL. `getItemByLegacyId` exists
    to bridge them. Storing the wrong one in `state.json` breaks the
    edge-triggered alert, not the fetch.
12. **Relisting.** An eBay listing that sells out is *ended*, and the seller
    relists under a **new item ID**. A watch pinned to `getItem(itemId)` decays
    to a permanent "ended" reading, exactly the way Best Buy's SKU `6577129`
    watch decayed to permanent UNKNOWN and had to be removed. **An eBay watch
    should be search-shaped, not item-shaped** — which is a shape
    `boty.models.Watch` does not currently have (`target` is a URL or a SKU;
    every adapter resolves it to one product).
13. **The 5,000/day cap and the 1,000/day token cap are separate meters.**
    Exhausting either produces a refusal; only one of them is the obvious one.
14. **`developer.ebay.com` refuses `curl` and impersonated HTTP alike (403,
    ~1,832 B) while `www.developer.ebay.com` serves the same documents.** A
    documentation link in a README that a contributor cannot open is a small,
    real papercut, and the `www.` host throttles hard (403 after ~3 requests at
    3 s spacing). Cite documentation by title as well as URL.
15. **eBay's 403 error page reads "Something went wrong on our end"** — the same
    string that was rejected as an Amazon block phrase for appearing on real
    product pages. Do not reach for it here either.

---

## What this changes about how an eBay phase should be planned

Three things, and none of them is "write an adapter".

1. **Run the § 2 probe before writing any plan.** Register a keyset with a free
   email, take the account-deletion exemption, mint a token, make one
   `item_summary/search` call, record the status and byte count. The result
   picks between two different phases: *rung 2, the most trustworthy adapter in
   the tree* and *rung 1-or-nothing under a terms clause sharper than Amazon's*.
   Everything else in an eBay plan is downstream of that one HTTP status.
2. **eBay needs a `Watch` shape this project does not have.** Every existing
   adapter answers *is this product buyable*. eBay's real question is *is any
   listing buyable, new, under $80, shipping included*. That is a search with
   filters, and it changes `Watch`, `_pick` and the alert key — not just
   `retailers.py`.
3. **`_pick`'s first-party model does not fit a retailer with no first party.**
   § 4. Configuring around it produces either a confident false OUT_OF_STOCK or a
   permanent UNKNOWN. This is a `_pick` change with a test, and it is the part
   most likely to be mis-scoped as "just add an entry to `FIRST_PARTY`".

And one thing that does **not** change: the price ceiling stays the anchor. eBay
offers no reference price a fresh clone can read, and MSRP is a better number
than a market average of exactly the behaviour bot-y exists to resist.

---

## Confidence summary

| Claim | Confidence | Basis |
|---|---|---|
| Browse API is the current surface; Finding/Shopping decommissioned 2025-02-05 | MEDIUM | websearch, cross-checked against eBay's own docs' "legacy" framing |
| Browse `search`/`getItem` need only `client_credentials` + base scope; token 7200 s | **HIGH** | eBay reference pages, quoted verbatim |
| Browse default limit 5,000 calls/day; token mints 1,000/day | **HIGH** | eBay API Call Limits page, quoted verbatim |
| Response carries price, currency, condition, seller, `buyingOptions`, `itemWebUrl`, shipping | **HIGH** | eBay's own sample payload |
| Keyset creation is self-serve; production needs the account-deletion opt-out | **HIGH** | eBay's Create-the-keysets and account-deletion guides, quoted verbatim |
| Buy APIs docs say production requires EPN approval + signed contracts | **HIGH** | Buy APIs Requirements page, quoted verbatim |
| **Whether that approval requirement actually gates Browse `search`** | **UNMEASURED** | the § 2 probe. Community prose suggesting it does not is LOW |
| `robots.txt` disallows `/sch/`, permits bare `/itm/<id>`, and its header forbids robots outright | **HIGH** | measured — HTTP 200, 18,810 B, 808 lines, line numbers cited |
| User Agreement forbids automated access "for any purpose, except with the prior express permission of eBay" | **HIGH** | measured — HTTP 200, 400,878 B, quoted verbatim |
| eBay serves a captcha at HTTP 200 that no `BLOCK_PHRASES` entry matches | **HIGH** | measured — 39,100 B, `Security Measure \| eBay` |
| Impersonated HTTP passes where `curl` does not, **on a help page** | **HIGH** | measured, 27 s apart |
| **Whether `/itm/<id>` serves at rung 1** | **UNMEASURED** | no listing page was requested |
| **Whether `/itm/<id>` carries JSON-LD / a hydration blob** | **UNMEASURED** | the § 3 reader table would settle it in one request |
| Marketplace Insights (sold history) is Limited Release and effectively closed | MEDIUM | websearch, cross-checked against the ALA "Restricted APIs" definition |
| Browse search lags the web index by 10–15 min and drops items | **LOW** | community reports only; no eBay SLA exists |

## Sources

- `https://www.ebay.com/robots.txt` — measured 2026-08-07 18:42:08Z, HTTP 200, 18,810 B
- [eBay User Agreement](https://www.ebay.com/help/policies/member-behaviour-policies/user-agreement?id=4259) — measured 2026-08-07 18:49:32Z, HTTP 200, 400,878 B
- [Browse API Overview](https://developer.ebay.com/api-docs/buy/browse/overview.html)
- [Browse API `item_summary/search`](https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search)
- [Browse API `item/getItem`](https://developer.ebay.com/api-docs/buy/browse/resources/item/methods/getItem)
- [Buy APIs Requirements](https://developer.ebay.com/api-docs/buy/static/buy-requirements.html)
- [Buy API Field Filters](https://developer.ebay.com/api-docs/buy/static/ref-buy-browse-filters.html)
- [The client credentials grant flow](https://developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html)
- [API Call Limits](https://developer.ebay.com/develop/apis/api-call-limits)
- [Create the eBay API keysets](https://developer.ebay.com/api-docs/static/gs_create-the-ebay-api-keysets.html)
- [Marketplace account deletion/closure notifications](https://developer.ebay.com/develop/guides-v2/marketplace-user-account-deletion)
- [eBay API License Agreement](https://developer.ebay.com/join/api-license-agreement)
- [Finding/Shopping API decommission alert](https://community.ebay.com/t5/Traditional-APIs-Search/Alert-Finding-API-and-Shopping-API-to-be-decommissioned-in-2025/td-p/34222062) · [Q3 2024 newsletter](https://developer.ebay.com/updates/newsletter/q3_2024)
- [Browse API missing listings thread](https://community.ebay.com/t5/RESTful-Buy-APIs-Browse/Ebay-Browse-API-finding-most-but-not-all-listings-Missing-items/td-p/34475520)
- [Marketplace Insights API access thread](https://community.ebay.com/t5/eBay-APIs-Talk-to-your-fellow/Marketplace-Insights-API-access/td-p/34838736/)
- [RESTful Buy APIs: Browse forum](https://community.ebay.com/t5/RESTful-Buy-APIs-Browse/bd-p/RESTful-Buy-APIs-Browse)
- [Structured data at eBay (background only, not evidence)](https://en.ryte.com/magazine/structured-data-changed-everything-ebay/)

Developer-documentation pages were read as `web.archive.org` raw (`…id_/`)
snapshots dated 2025-11 to 2026-06, and one live read from
`www.developer.ebay.com`, because `developer.ebay.com` returned HTTP 403 to both
`curl` and `boty.fetch.get`. Quotations are from those retrieved bytes, not from
search-result summaries.
