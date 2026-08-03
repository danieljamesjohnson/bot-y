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

Anything reached by browser is flagged DEGRADED in the support matrix and in
`boty check` output, per the locked decision in `.planning/phases/02-five-retailers-green/02-CONTEXT.md`.

---

## Amazon (amazon.com)

**Probed:** 2026-08-03, from danserver over a residential connection.
**Transport:** `curl` — a one-off, human-shaped read of public policy documents.
**`boty.fetch.get` was never pointed at amazon.com and no product page was
requested at any point in this phase.** That ordering is the finding rather than
a courtesy: the question "may we request this at all" was settled *before* any
request whose legitimacy would have depended on the answer, so this section can
make a claim the Pokémon Center one could only make retroactively.

**Verdict: REFUSED**

Rung 4, and the decisive reason is written rather than technical. Amazon's
Conditions of Use prohibit exactly what this monitor does, twice over — once by
naming the *data* and once by naming the *method*. No wall was ever reached
because none needed to be, and no transport work was spent on a retailer that
should not ship regardless of which transport won.

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

### What was NOT done, and why

- **No product page was ever requested.** Not at rung 1, not at rung 3, not
  once. The Conditions of Use were read first precisely so this sentence could
  be written: **bot-y makes no requests to amazon.com.** There is no watch in
  `config/products.yaml`, no `FIRST_PARTY["amazon"]` entry, no dispatch branch
  and no fixture under `tests/fixtures/amazon/`. `amazon` remains in
  `boty.retailers.MARKETPLACES` — it is the archetypal buy-box marketplace and
  that entry is a statement about the retailer, not a claim to support it.
- **No transport work at all.** This is the difference from Pokémon Center,
  which cost ten probes across two transports and two WAF vendors before a desk
  review of its Terms produced the reason that actually settled it. Here the
  reading came first, so nothing was spent finding out how well-defended a page
  is that we would not be entitled to read either way. `.planning/ROADMAP.md`
  asks for reachability to be established "cheaply *before* investing in an
  adapter"; six policy reads is as cheap as that gets.
- **The Creators API was not signed up for.** Rung 2 exists on paper and the
  fresh-clone rule closes it — see above. Obtaining the credential personally
  would have made *this host* able to read Amazon while every clone of this repo
  could not, which is a footnote in the README rather than support, and the
  clause forbidding collection of prices is not suspended by holding one anyway.
- **The `/dp/<ASIN>` gap in robots.txt was not walked through.** It is real: the
  bare product path carries no `Disallow`. Taking it because the narrower
  technical file omits it, while the broader written one names prices
  explicitly, is the posture `03-CONTEXT.md` locks this project out of.

### If somebody revisits this later

**Do not re-probe.** There is nothing to re-probe: no wall was measured, so
there is no wall that could weaken. Periodically retrying a retailer whose terms
forbid automated interaction — waiting for enforcement to lapse, or for a
fingerprint to start working — is exactly the behaviour this project should not
have, and here there is not even the excuse of a technical question left open.
A clean HTTP 200 from `/dp/<ASIN>` would prove only that we had been rude
successfully.

**What would actually change this** is Amazon saying something different. A
product-availability signal a non-commercial user can subscribe to; a Creators
API tier that does not require an affiliate relationship and whose licence
permits reading stock for personal use; or a revision of the LICENSE AND ACCESS
clause that stops naming prices. Any of those is a genuine rung 2 and would be
worth wiring up the same afternoon. The retrieval date and the `Last updated`
header above are recorded so a future reader can tell at a glance whether the
document they are looking at is the one this verdict was based on.

### Why this is the plan succeeding

The roadmap's criterion for this retailer is "Amazon reports stock, **or** the
support matrix records what was tried and why it failed." This is the second
branch, and it is the better one to land on: a written prohibition is a more
durable finding than a wall, because a wall can fall and this cannot. Nobody has
to re-derive it in six months, and nobody has to wonder whether a different TLS
fingerprint would have worked. It would have.

It costs the phase its fifth retailer unless Target lands — see `QUESTIONS.md`.
That is recorded rather than papered over: no Amazon watch, and no substitute
retailer added to move the count. `scripts/evidence_check.py`, added by this same
plan, is what makes that shortfall mechanically impossible to hide later.

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

**Verdict: REFUSED**

Rung 4, and — as with Amazon — the decisive reason is written rather than
technical. Target's Terms & Conditions prohibit this three separate ways, and
one of the three has no commercial-use qualifier to argue about. The ladder was
never walked, because the question "may we request this at all" was answered
before any request whose legitimacy would have depended on the answer.

This is the outcome that costs the phase its fifth retailer. It is recorded as
that rather than padded — see the bottom of this section, and `QUESTIONS.md`.

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

#### What this leaves in the code, unchanged and still a guess

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
