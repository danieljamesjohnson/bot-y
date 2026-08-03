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

Read that top-to-bottom: the product is out of stock everywhere, and the four
green lines below it are why you can believe that. `[degraded]` says Best Buy's
reading came from a page we rendered rather than an answer the retailer gave us.

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
browser, rung 4 "dropped, with the evidence written down". Anything read on rung
3 is flagged `[degraded]` in `boty check` and in the status JSON — it works, and
it is a page we rendered rather than an answer the retailer gave us. What was
actually tried against each one, and what came back, is in
[`docs/retailer-evidence.md`](docs/retailer-evidence.md).

| Retailer | Rung | Method | Status |
|---|---|---|---|
| GameStop | 1 | `curl_cffi` + schema.org JSON-LD | ✅ Working |
| Walmart | 1 | `curl_cffi` + `__NEXT_DATA__`, seller-aware | ✅ Working |
| Nintendo | 1 | `curl_cffi` + schema.org JSON-LD | ✅ Working — first-party for the hardware, and the only place in this config that lists the GO Plus + at its $54.99 MSRP with no marketplace attached |
| Best Buy | 3 (2 with a key) | Headless browser + schema.org JSON-LD, reached by SKU search redirect. Official Products API when `BESTBUY_API_KEY` is set | ⚠️ Working, `[degraded]` — needs no credentials; a free-but-manually-approved API key upgrades it to rung 2 and drops the flag. Best Buy does not appear to stock the GO Plus + itself, so only a control is configured |
| Pokémon Center | 4 | none — Imperva refuses `/product/*` at rung 1 (HTTP **200** `Pardon Our Interruption`) and at rung 3 (headless Chrome, twice); its `robots.txt` forbids the API endpoints that would answer the stock question | ❌ Dropped, with the evidence written down. Not configured, and deliberately not padded into the count — it stocks the product, so a watch here would have looked plausible and read nothing forever |
| Amazon | 4 | none — its Conditions of Use forbid it. The licence to use the site excludes "any collection and use of any product listings, descriptions, or prices" and "any use of data mining, robots, or similar data gathering and extraction tools" | ❌ Dropped, and dropped without ever fetching a product page. The terms were read first, so the reason is a written prohibition rather than a wall we could not get past — a wall can fall and this cannot. Not configured |
| Target | 4 | none — its Terms & Conditions forbid it. `Unlawful or Prohibited Uses` bars "any use of data extraction, scraping, mining or other data gathering tools" and "otherwise scrape, collect, store or use any Content … product listings, descriptions, prices or images", with no commercial-use qualifier. Rung 2 (RedSky) is closed separately: `redsky.target.com/robots.txt` is `Disallow: /` for every agent | ❌ Dropped, without ever fetching a product page. Note the direction of the disagreement: `www.target.com/robots.txt` does **not** disallow `/p/`, and Target publishes a product-detail sitemap — robots.txt is broader than the terms here, and the terms govern. Not configured |

**Four working retailers, not five — and that is now the final answer, not a
pending one.** The roadmap's MVP bar was five, and this is what the bar actually
bought: a retailer that cannot be read is dropped and documented rather than
shipped as a detector with nothing behind it. **Three** fell out, for reasons
worth telling apart — Pokémon Center was walked down the whole ladder and
refused at every rung, while Amazon and Target were never probed at all, because
each one's terms answer the question before a request would. None has been
padded into the count. The number did not move in Phase 3 because both of the
retailers that could have moved it refused **in writing**, and the US retail set
for this device holds no sixth candidate that stocks the product;
[`QUESTIONS.md`](QUESTIONS.md) records that shortfall as a decision for the
maintainer rather than a task somebody can close.
[`docs/retailer-evidence.md`](docs/retailer-evidence.md) carries all three
records, including which two probes would establish whether anything has changed
at Pokémon Center, and why the answer for Amazon and Target is that nobody
should look.

That is the whole of the gap, incidentally: with Target settled, every retailer
in the roadmap's scope is now either shipped or refused in writing. The bar is
missed by one, and nothing about which retailer or why is left unrecorded.

`scripts/evidence_check.py` is what stops that number drifting, **and it runs on
every `make verify`** — the offline suite invokes it against this tree, so it is
not a script somebody has to remember. It fails if a retailer outside the
roadmap's scope is ever configured to make the count read five, and it fails if
a retailer in scope is neither shipped nor recorded with a written refusal.
`tests/test_support_matrix.py` holds the table above to the same standard: every
retailer in scope needs a rung of 1–4 here, and anything on rung 3 has to say
`degraded` in its own row.

**A browser is not a strict upgrade.** The same headless Chrome that reads Best
Buy is served a Cloudflare wall by gamestop.com, which rung 1 reads on every
`make verify`. Rung 3 fixes the JavaScript fingerprint and leaves the TLS one
untouched, so it is for a retailer that refuses HTTP *at the connection layer* —
not something to reach for because a fetch failed once.

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
