# bot-y

A self-hosted restock monitor for big US retailers that **tells you when it breaks.**

```
○ gamestop  Pokémon GO Plus +             $   54.99  ld+json: OutOfStock from GameStop
○ walmart   Pokémon GO Plus +                        1 offer(s) via __NEXT_DATA__, none first-party
○ nintendo  Pokémon GO Plus +             $   54.99  ld+json: OutOfStock from Nintendo of America Inc.
● gamestop  CONTROL — PS5 console         $  549.99  ld+json: InStock from GameStop [control]
● walmart   CONTROL — Great Value whole mi$    2.42  __NEXT_DATA__: IN_STOCK from Walmart.com [control]
● bestbuy   CONTROL — Pokémon Let's Go, Pi$   59.99  ld+json: InStock from Best Buy [control] [degraded]
● nintendo  CONTROL — Nintendo HDMI cable $    7.99  ld+json: InStock from Nintendo of America Inc. [control]
```

Read that top-to-bottom: the product is out of stock everywhere, and the green
control lines below it are why you can believe that. `[degraded]` says the
reading is one to discount — Best Buy's came from a page we rendered rather than
an answer the retailer gave us, and Target's adds `[dom]`, meaning it was lifted
out of presentation markup that a redesign can break without warning.

## Why another one

The existing tools are mostly dead. The big-retailer monitors on GitHub stopped
getting real commits in 2021–22, which is exactly when Akamai and PerimeterX got
serious. What's left either targets soft Shopify/sneaker sites, or is a
general-purpose page watcher pointed at the most defended pages on the consumer web.

bot-y is built around three things those tools get wrong.

### 1. "I don't know" is not "out of stock"

This is the bug that matters. When a retailer reskins its page, a selector-based
monitor stops matching, reports out-of-stock forever, and **looks perfectly
healthy.** You find out weeks later, having missed the drop. Silence and "no
stock yet" are indistinguishable.

So `Availability` has three values, and a detector that can't tell must say
`UNKNOWN`. Then every retailer carries a **control product** — something known to
be in stock. If the control stops reading in-stock, the detector is broken and
you get paged about *that*, as loudly as a real restock.

### 2. "In stock" from a scalper is not a restock

On marketplaces a sold-out item is nearly always available from resellers at a
markup. The Pokémon GO Plus + has a $54.99 MSRP and sits on Walmart at $229.99
from a third-party seller, while Walmart itself has none.

bot-y reads the seller on each offer and defaults to first-party only, with an
independent price ceiling as a second line of defence. Either alone suppresses
that listing.

### 3. Fetching: TLS first, browser last

Anti-bot systems read your TLS ClientHello **before any HTTP header arrives**. A
stock `requests` handshake is identifiable as a script no matter what User-Agent
it sends — header spoofing is theatre, and a headless browser fixes the
JavaScript fingerprint while leaving the TLS one untouched.

bot-y uses [`curl_cffi`](https://github.com/lexiforest/curl_cffi) to replay a real
Chrome TLS stack. In practice this reaches pages that a full Playwright browser
gets served a CAPTCHA on — at a fraction of the cost, with no browser at all.

Stock state is then read from **structured data** — schema.org JSON-LD, Next.js
hydration payloads — rather than CSS selectors. Retailers keep those accurate
because Google Shopping depends on them, so they rot far more slowly than class
names.

## Retailer status

Every retailer lands on a **rung** of an escalation ladder, and bot-y says which
one rather than presenting them all as equally trustworthy. Rung 1 is
impersonated HTTP, rung 2 a retailer's own sanctioned API, rung 3 a real
browser, rung 4 "dropped, with the evidence written down". What was actually
tried against each one, and what came back, is in
[`docs/retailer-evidence.md`](docs/retailer-evidence.md).

**A rung is only half of what a reading is worth, so there is a second column
beside it.** The rung says *how the bytes were obtained*. The **Extraction**
says *what was read out of them* — `structured` for the retailer's own
machine-readable feed (schema.org JSON-LD, a Next.js hydration payload, an API
response), `dom` for presentation markup, and `—` for a rung-4 retailer, where
nothing is read at all because nothing is watched.

The two are independent, and Best Buy is why the distinction had to exist. It is
rung 3 + `structured`: a browser renders the page, and what is then read off it
is Best Buy's own schema.org feed — a document they maintain because Google
Shopping depends on it. A rung-3 + `dom` retailer would be a different animal on
the same rung, and a rung-1 + `dom` adapter is perfectly possible and would be
the most fragile thing in this repo.

`[degraded]` fires on **either** — a page we rendered, or a reading lifted out of
presentation markup — because both mean *discount this*. It is worth being blunt
about what a `dom` row costs you: **a reskin breaks it silently.** No error, no
403, no red control until the next control cycle; the parser simply stops
finding the button and the reading goes quiet. That is precisely the failure this
whole project exists to catch, so the column is a warning, not a label.

| Retailer | Rung | Extraction | robots.txt | Terms | Method | Status |
|---|---|---|---|---|---|---|
| GameStop | 1 | structured | unread — `robots.txt` itself returned 403 | unread — not requested | `curl_cffi` + schema.org JSON-LD | ✅ Working |
| Walmart | 1 | structured | permits `/ip/` | unread — challenge page, not the terms | `curl_cffi` + `__NEXT_DATA__`, seller-aware | ✅ Working |
| Nintendo | 1 | structured | permits `/us/store/products/` | forbids automated means | `curl_cffi` + schema.org JSON-LD | ✅ Working — first-party for the hardware, and the only place in this config that lists the GO Plus + at its $54.99 MSRP with no marketplace attached. ⚠ disagree — `robots.txt` is `Allow: /` and publishes a store sitemap, while § 6 of the Terms of Use bars "any robot … spider, crawler, scraper or other automated means" |
| Best Buy | 3 (2 with a key) | structured | unread — refused at the connection layer | unread — same refusal | Headless browser + schema.org JSON-LD, reached by SKU search redirect. Official Products API when `BESTBUY_API_KEY` is set | ⚠️ Working, `[degraded]` — needs no credentials; a free-but-manually-approved API key upgrades it to rung 2 and drops the flag. Best Buy does not appear to stock the GO Plus + itself, so only a control is configured |
| Pokémon Center | 4 | — | permits `/product/` | forbids data mining | none — Imperva refuses `/product/*` at rung 1 (HTTP **200** `Pardon Our Interruption`) and at rung 3 (headless Chrome, twice); its `robots.txt` forbids the API endpoints that would answer the stock question | ❌ Dropped, with the evidence written down. Not configured, and deliberately not padded into the count — it stocks the product, so a watch here would have looked plausible and read nothing forever. ⚠ disagree — `/product/*` is not disallowed, but the Terms of Use prohibit data gathering outright |
| Amazon | 1 | dom | permits `/dp/` | forbids extraction | `curl_cffi` + the **add-to-cart control**, with no browser. Amazon serves `/dp/<ASIN>` to impersonated HTTP — three requests on 2026-08-03, three HTTP 200s, no challenge — and ships **no** structured data in it: zero `application/ld+json`, no `__NEXT_DATA__`, and no JSON blob on the page carrying a price, an availability or a seller. What is server-rendered is the control (`id="add-to-cart-button"`, or `-ubb` on a used buy box), the `#availability` line and a named buy-box seller, read verbatim: `Amazon.com` on a first-party offer. The three paths `robots.txt` disallows — `/gp/product/product-availability`, `/dp/product-availability/`, `/gp/offer-listing/` — are never requested | ⚠️ Working, `[degraded]` `[dom]` — **the cheapest transport here with the most fragile extraction here.** A buy-box redesign breaks it silently: no error, no 403, just a control that stops reading, which is why a control watch and mutation M8 both cover it. Amazon is the one retailer of the hard two that **does** list the GO Plus + — and the only offer on it is a **used** unit at **$219** from `LO Store (We Record Serial Numbers To avoid FRAUD)` against a $54.99 MSRP, which is verbatim the alert this project exists not to send. Both defences suppress it independently. Rung 4 stood here until 2026-08-03 on a reading of the Conditions of Use; every clause of that reading is still in the evidence log and none of it was retracted — the maintainer reversed which document decides. ⚠ disagree — no rule matches `/dp/<ASIN>`, while the Conditions of Use forbid extraction |
| Target | 3 | dom | permits `/p/` | forbids extraction | Headless browser + the **add-to-cart button**. Target ships no structured data on `/p/` at all — zero `application/ld+json`, zero `"price"`, zero `"seller"`, an empty price module and its own `isProductDetailServerSideRenderPriceEnabled: false` — and renders stock client-side. So there is nothing to read but presentation markup: the control at `id="addToCartButtonOrTextIdFor<TCIN>"`, buyable when enabled and out of stock when `disabled`. A `Sold & shipped by` block marks a Target Plus partner and is not treated as first-party | ⚠️ Working, `[degraded]` `[dom]` — **control-only, and the most fragile detector here.** A reskin breaks it silently: no error, no 403, just a control that stops reading, which is why one exists and why mutation M8 pins it. There is no GO Plus + watch because Target **delisted** the product (TCIN `88714054`, HTTP 200 as late as 2025-05, now 404) — a disproof, not an omission. Rendering the page makes Target's own JavaScript fetch three Target hosts that publish `Disallow: /`; that is recorded in the open in `QUESTIONS.md` § 0d, measured rather than assumed, and no code here addresses them directly. ⚠ disagree — `robots.txt` does **not** disallow `/p/` and Target publishes a product-detail sitemap, so it is broader than the terms here |

**Six working retailers.** The roadmap's MVP bar was five, and the number is
worth reading with its history attached, because it sat at four for most of this
project's life and the difference is not that the bar was lowered. **One**
retailer is still dropped: Pokémon Center, walked down the whole ladder and
**refused at every rung**. It has not been padded into the count.

Amazon was the seventh row and the second dropped one until 2026-08-03, on a
reading of its Conditions of Use rather than on a wall — and with **zero**
product-page requests ever made, which is the part worth pausing on. The record
was complete and internally consistent: quoted clauses, a full `robots.txt`
analysis, six policy reads with byte counts. It contained no observation about
whether the page could be read, and a section explaining why nobody should find
out. When the maintainer reversed which document decides, the question took
three requests to answer: HTTP 200, every time, with the add-to-cart control
sitting in the response. Nothing in the old record was retracted to get there.

**Target is the fifth, and it is the one worth reading**, because it is the
failure mode this project is least equipped to notice from the outside: a page
that reads *perfectly* and says *nothing*. Probed on 2026-08-03 it was **refused
at no rung** — permitted by its own `robots.txt`, served without a challenge —
and carried no price, no availability and no seller, because Target renders all
of that client-side. At rung 1 a watch there would have returned UNKNOWN forever,
which is why one was not added then.

What changed is not Target and not the standard. A headless browser reaches the
rendered page, and the **add-to-cart button** on it is a real stock signal. That
route was held open as a `robots.txt` decision for the maintainer rather than
taken quietly — rendering the page makes Target's own JavaScript call hosts that
publish `Disallow: /` — and it is recorded, answered and dated in
[`QUESTIONS.md`](QUESTIONS.md) § 0d, with the hosts **measured** rather than
assumed. Target is registered **control-only** and every reading it produces is
flagged `[degraded] [dom]`: this is the least confident reading here, and it says
so on every line it prints.

Target still cannot watch the GO Plus + itself, and that is a **disproof**:
Target listed it (TCIN `88714054`, HTTP 200 as late as 2025-05) and delisted it.
So the fifth retailer does not move the thing the count was a proxy for — the
same disproof already recorded for Best Buy.

**So read the six as a four and a two.** Two of the six rows — Best Buy and
Target — are **control-only**: they are real, live, control-verified retailers
whose detectors are checked every pass, and neither one can ever alert on the
Pokémon GO Plus +, because neither one lists it. That is a disproof in both
cases rather than an omission, and it is stated here rather than left to be
worked out from the table, because a reader counting rows should not have to
reconstruct which of them could actually page you. **Four retailers can:**
GameStop, Walmart, Nintendo and Amazon. Target is additionally the most fragile
row here — rung 3 **and** `dom`, degraded on both axes, so a reskin breaks it
silently — which is exactly why it has a control and why mutation M8 pins the
decision its reader makes.

**Amazon is the sixth, and it is the only one that moves it.** Amazon does list
the GO Plus +, so there is a real product watch there rather than a control
alone. What that watch reads today is the reason both flipper defences exist: a
**used** unit at **$219** from a third-party reseller, four times the $54.99
MSRP. The seller is not in `FIRST_PARTY['amazon']` and `amazon` is in
`MARKETPLACES`, so the offer is suppressed before the `max_price: 80` ceiling is
even consulted — two independent refusals of the same listing. The watch reads
OUT_OF_STOCK, which is the correct answer: there is no first-party Amazon offer.
It flips the day Amazon itself sells one.

[`docs/retailer-evidence.md`](docs/retailer-evidence.md) carries every record,
including which two probes would establish whether anything has changed at
Pokémon Center.

`scripts/evidence_check.py` is what stops that number drifting, **and it runs on
every `make verify`** — the offline suite invokes it against this tree, so it is
not a script somebody has to remember. It is **six rules**, and they do not all
point the same way:

1. **In scope.** A retailer outside the roadmap's own scope table may not be
   configured to make the count read higher.
2. **Configured or refused.** A retailer inside it must be either shipped or
   carrying a written verdict. `UNPROBED` is a third, *dated* state that expires
   after 60 days, and `--strict` refuses it outright.
3. **Count consistency.** A short count is honest only when neither of the hard
   two landed.
4. **A refusal cannot outrank a capture.** If a retailer is not configured but
   `tests/fixtures/<retailer>/` still holds a page this repo really fetched, the
   gate fails — a retailer we have read is not a retailer that refused us.
5. **A configuration cannot outrank a refusal.** The mirror of rule 4, and it
   exists because rule 4 alone was half a rule: rules 2 and 4 both skipped any
   configured retailer, so a tree shipping a detector for a retailer its own
   evidence log records as REFUSED passed clean.
6. **A refusal must cite an observation.** REQ-07a, made mechanical. A `REFUSED`
   verdict has to be backed by anchored `**Refusal observed (rung N):**` lines
   whose bodies carry an actual *measurement* — a status code, a byte count, a
   matched block phrase — and the two hard-two retailers need two of them,
   including one at rung 3. This is the rule Phase 3 would have failed: it
   dropped Target and Amazon on a desk review of their written terms, made zero
   product-page requests to either, and every gate in this tree stayed green.
   The anchored line *alone* is satisfiable by typing the sentence, which is why
   the rule is shape **plus** measurement rather than shape alone.

Rules 1–3 are a **ceiling** on the count. Rules 4–6 are the **floor**, and it
needs one: a written refusal is one line, so nothing about "five or more" stops
the number falling. `tests/test_support_matrix.py` closes the same gap in
the table: every retailer in scope needs a rung of 1–4 here, anything on rung 3
**or reading `dom`** has to say `degraded` in its own row, and **no row may claim
a working rung (1–3) for a retailer nothing watches**. Rung 4 — dropped, with the
evidence written down — is the only honest rung for a retailer the monitor does
not read.

The Extraction cell is held to the rung beside it in **both** directions, for the
same reason `⚠ disagree` is: a rung-4 row must say `—`, and a working-rung row
must never say it. Otherwise `—` would become a blank that means nothing and
answers everything — the escape hatch `unread` had to be pinned against, one
column over.

There is one temporary third state, for the same reason: a gate that makes the
honest answer unrepresentable pressures the padding it was built to stop. A
retailer newly brought into scope and not yet probed records
`**Verdict: UNPROBED (scoped YYYY-MM-DD)**` in the evidence log and `—` in the
rung column — a written, dated claim that **expires after 60 days**, after which
the gate goes red again. `.venv/bin/python scripts/evidence_check.py --phase
--strict` refuses it outright; that is the bar at the close of a phase, and it
is why "not yet" cannot become a way of never answering.

**A browser is not a strict upgrade.** The same headless Chrome that reads Best
Buy is served a Cloudflare wall by gamestop.com, which rung 1 reads on every
`make verify`. Rung 3 fixes the JavaScript fingerprint and leaves the TLS one
untouched, so it is for a retailer that refuses HTTP *at the connection layer* —
not something to reach for because a fetch failed once.

**Every row states four things, not one: a rung, what was extracted off the
page, where that retailer's `robots.txt` stands on the exact path bot-y fetches,
and where its terms stand.**
A row whose two signals point in opposite directions is marked `⚠ disagree`, and
one whose signals agree is not — the marker is a finding, so a table where every
row carried it would say nothing. Four rows carry it today, and one of them is a
retailer this repo actively watches, which is the point: you are shown the
disagreement rather than only the verdict somebody resolved it to.

The positions come from
[`docs/retailer-evidence.md`](docs/retailer-evidence.md), where each one is
backed by a URL, an HTTP status and the date it was retrieved. Two of the words
in those columns are worth reading precisely. `permits` means no rule in the
`*` group matches the path — `robots.txt` is a deny-list, so silence there really
is permission. `unread` means the policy document itself refused us, and it is
written rather than guessed: three retailers turned away a plain `robots.txt` or
terms request on 2026-08-03, and inventing a `permits` for a file nobody has read
would be exactly the kind of filled-in-looking cell the rest of this section
exists to prevent. `tests/test_support_matrix.py` pins which rows may say
`unread`, so it cannot quietly spread to a fourth.

## Install

```bash
git clone https://github.com/danieljamesjohnson/bot-y
cd bot-y
python3 -m venv .venv && .venv/bin/pip install -e .
```

### The browser rung (only if you want Best Buy)

Rung 3 needs an extra and a browser binary. Both are optional — every rung-1
retailer works without them, and the extra is kept separate so contributors on
those retailers never pull a browser stack:

```bash
.venv/bin/pip install -e '.[browser]'
export BOTY_BROWSER_PATH=/path/to/chrome    # only if none is on PATH
```

`BOTY_BROWSER_PATH` is read from the environment rather than the config file
because which browser a machine has is a property of the *machine*. Discovery
tries `google-chrome`, `chromium` and friends on `PATH` first. On Ubuntu 24.04 an
*unpackaged* Chrome cannot build its sandbox — the kernel denies unprivileged
user namespaces to binaries with no AppArmor profile — and aborts on startup;
`BOTY_BROWSER_NO_SANDBOX=1` works around that, opt-in and per host, but it is a
real reduction in isolation because this transport executes retailer JavaScript.
A distro Chrome package is the better fix.

It accepts `1`, `true`, `yes` or `on` — and nothing else. `0`, `false`, `no`,
`off` and an empty value all mean *keep the sandbox*, and anything unrecognised
is treated as "no" with a warning naming the value. This is the one setting here
where guessing wrong removes a security boundary, so merely being set is
deliberately not enough to disable it.

Note that Chrome disables its own sandbox when it runs as **root**, whatever
this variable says. Run bot-y as an unprivileged user; if you do not, it warns
on every render, because a log that reports `sandbox=True` while Chrome quietly
dropped it is worse than no log line at all.

**If you run bot-y under systemd, put both variables in the unit's
`EnvironmentFile`, not just your shell.** Exporting them interactively makes
`make verify` pass while the deployed monitor still cannot find a browser — the
service starts with almost no environment. That combination is worse than a
plain failure, because the green check reads as proof the thing works. It has
happened here: a verify run passed in a shell with `BOTY_BROWSER_PATH` exported,
and the service paged half an hour later with *"control product is not reading
IN_STOCK — the detector is probably broken"*. Check it the way the service sees
it before you trust a green:

```bash
sudo systemd-run --pipe --quiet --uid="$USER" \
  --property=EnvironmentFile=/home/$USER/.config/boty/env \
  --property=WorkingDirectory="$PWD" \
  "$PWD/.venv/bin/python" scripts/control_check.py
```

(`env -i` is *not* the right check here — it strips the `EnvironmentFile` too,
so it fails for a reason systemd would not.)

## Use

Adding a product is editing `config/products.yaml`. No code, no rebuild:

```yaml
watches:
  - name: Pokémon GO Plus +
    retailer: gamestop
    target: https://www.gamestop.com/.../pokemon-go-plus-plus/20003961.html
    max_price: 80

  - name: CONTROL — Great Value whole milk
    retailer: walmart
    target: https://www.walmart.com/ip/.../10450114
    control: true
```

```bash
boty check    # one pass, print a table
boty watch    # loop, notify on transitions
```

Notifications go through [Apprise](https://github.com/caronc/apprise), so Telegram,
ntfy, Discord, Slack and ~100 others work out of the box:

```bash
export BOTY_NOTIFY_URL='tgram://<bot-token>/<chat-id>'
```

**Pick controls carefully.** A grocery staple is ideal — first-party, restocked
daily, never contested. Don't use a console: on Walmart those are often held by
marketplace sellers, so an out-of-stock reading would be *correct* and you'd
chase a bug that isn't there.

## Verifying it works

```bash
make verify           # everything, including live retailer checks
make verify-offline   # same minus the live check — for CI
```

That is how you answer "is bot-y still working" without reading any code. It
exits **0** only if every check below passed, and prints `VERIFY: PASS` or
`VERIFY: FAIL (<stage>)`.

A green run comes in three flavours, because "everything passed" and "we could
not check some of it" must not look the same:

| Verdict | Exit | Means |
|---|---|---|
| `VERIFY: PASS` | 0 | Every check ran and passed |
| `VERIFY: PASS (INCOMPLETE — ...)` | 0 | Some live controls could not run **on this host** — no `browser` extra, or no Chrome. The detectors they cover are unverified here; nothing is known to be broken |
| `VERIFY: PASS (OFFLINE — ...)` | 0 | No outbound connectivity, so *no* live control ran. Nothing here says the retailers still work |
| `VERIFY: FAIL (<stage>)` | non-zero | Something is actually wrong |

**INCOMPLETE is the ordinary result of a fresh clone.** `config/products.yaml`
ships a mandatory Best Buy control, and Best Buy's only credential-free path is
rung 3 — which needs the optional `browser` extra and a Chrome binary that
`pip install -e '.[dev]'` deliberately does not bring (nodriver is AGPL-3.0;
see "The browser rung" above). That is a gap in *your machine*, not in the
detector, and the gate says so instead of telling you the extractor broke.
Install the extra if you want Best Buy covered; ignore it if you do not.

| Stage | Proves |
|---|---|
| `test` | The offline suite still passes — no network touched, no browser started |
| `types` | `mypy` is clean over `boty/` and `scripts/` |
| `fixtures` | Warns about fixtures older than 90 days or missing a capture note. Never fails |
| `controls` | Live control products still read in stock |
| `mutation` | The suite would actually notice a broken extractor |

**Fixtures and controls answer different questions, and neither substitutes for
the other.** Fixtures are frozen copies of real retailer pages: they catch
*code* regressions, deterministically and offline, but they will keep passing
forever after a retailer redesigns its site. Live control products — a gallon of
milk, a console that never sells out — catch *reality*: if one stops reading
in stock, the detector is broken, because a control is chosen precisely because
it is always available.

`mutation` exists because a green suite is not evidence that it detects
anything. It corrupts specific things in a throwaway copy of the package — the
buyable check, "I could not read this page" becoming out-of-stock, the seller
filter, the price ceiling, the restock edge detector, the degraded flag — and
requires the tests to go red for each. A survivor names a real hole: that
breakage could ship with every test green.

If you have no internet, the live check **skips** and says so rather than
failing. A verify that goes red because someone's wifi dropped gets ignored
within a week. But if the network is up and a retailer turns us away, that is a
failure — being blocked is the monitor not working, not an infrastructure hiccup.

## Being a good citizen

Default cadence is 5 minutes with jitter, which is plenty for a drought that
lasts weeks. Polling every few seconds buys nothing and is what gets an IP
blocked. This is a personal notification tool — it does not add to cart, does not
check out, and does not run at a scale that would be unfair to anyone else
shopping.

## License

MIT
