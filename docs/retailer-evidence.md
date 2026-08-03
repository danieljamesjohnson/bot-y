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
line is one of exactly two strings, because later work branches on it
mechanically:

- `**Verdict: REACHABLE (rung 3)**`
- `**Verdict: REFUSED**`

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
