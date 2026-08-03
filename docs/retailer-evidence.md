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
