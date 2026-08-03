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
