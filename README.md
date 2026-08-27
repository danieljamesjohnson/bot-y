# bot-y

A self-hosted restock monitor for big US retailers that **tells you when it breaks.**

`boty check` prints a line per watch — retailer, product, price, and where the
reading came from. Beside every product watch sits a **control**, something known
to be in stock, and its line is why you can believe the product's one.

## Why another one

The big-retailer monitors on GitHub stopped getting real commits in 2021–22,
exactly when Akamai and PerimeterX got serious. bot-y is built around three
things they get wrong.

**1. "I don't know" is not "out of stock."** After a reskin, a selector-based
monitor stops matching, reports out-of-stock forever, and *looks perfectly
healthy*. So `Availability` has three values, a detector that cannot tell says
`UNKNOWN`, and every retailer carries a control product — a control that stops
verifying marks that retailer's readings unverified on the status page, in
`boty check` and in the log.

It does **not** page you for that, and the line above used to say it did ("a
broken detector pages you as loudly as a real restock"). Notifications are
reserved for what you can act on: a restock you could buy, or the one health
state you can close yourself — a Walmart `store_id` that is unset or answering
for the wrong store. Everything else is recorded rather than pushed, because an
alert that asks for a decision you cannot make is how a channel stops being read.

**2. "In stock" from a scalper is not a restock.** The $54.99 GO Plus + sits on
Walmart at $229.99 from a third-party seller while Walmart itself has none. bot-y
reads the seller on each offer, defaults to first-party only, and keeps a price
ceiling as a second, independent defence. That ceiling measures the **delivered
total** — item price plus shipping — where the retailer publishes a shipping cost
readably, and the item price alone where it does not. In that second case the
alert still goes out and the body says `shipping: unknown`, which means **a
listing with large unread shipping can reach you**: a deliberate choice, made on
2026-08-11, because missing a real restock was judged worse than being
disappointed at the checkout page.

**3. Fetching: TLS first, browser last.** Anti-bot systems read your TLS
ClientHello *before any HTTP header arrives*, so header spoofing is theatre and a
headless browser fixes the JavaScript fingerprint while leaving the TLS one
untouched. bot-y replays a real Chrome TLS stack with
[`curl_cffi`](https://github.com/lexiforest/curl_cffi) and reads stock from
**structured data** (schema.org JSON-LD, Next.js payloads) rather than CSS
selectors — retailers keep those accurate because Google Shopping depends on them.

## Retailer status

Every retailer lands on a **rung**: 1 impersonated HTTP, 2 a retailer's own
sanctioned API, 3 a real browser, 4 "dropped, with the evidence written down".
The rung says *how the bytes were obtained*; **Extraction** says *what was read
out of them* — `structured` for a feed the retailer maintains, `dom` for
presentation markup a redesign breaks without warning, `—` for a retailer nothing
watches. A reading marks itself `[degraded]` on either axis: a page we rendered
rather than an answer the retailer gave us, or markup rather than a feed.

| Retailer | Rung | Extraction | robots.txt | Terms | Method | Status |
|---|---|---|---|---|---|---|
| GameStop | 1 | structured | unread — `robots.txt` itself returned 403 | unread — not requested | `curl_cffi` + schema.org JSON-LD | ✅ Working |
| Walmart | 1 | structured | permits `/ip/` | unread — challenge page, not the terms | `curl_cffi` + `__NEXT_DATA__`, seller-aware | ✅ Working |
| Nintendo | 1 | structured | permits `/us/store/products/` | forbids automated means | `curl_cffi` + schema.org JSON-LD | ✅ Working — the only first-party GO Plus + here, at its $54.99 MSRP. ⚠ disagree — `robots.txt` is `Allow: /`; the Terms bar automated means |
| Best Buy | 3 (2 with a key) | structured | unread — refused at the connection layer | unread — same refusal | Headless browser + schema.org JSON-LD via SKU search redirect; official Products API when `BESTBUY_API_KEY` is set | ⚠️ Working, `[degraded]` — no credentials needed; a free but manually approved key upgrades it to rung 2 and drops the flag. Control-only: no GO Plus + listing |
| Pokémon Center | 4 | — | permits `/product/` | forbids data mining | none — Imperva refuses `/product/*` at rung 1 (HTTP **200** `Pardon Our Interruption`) and at rung 3 | ❌ Dropped, with the evidence written down. Not configured, not padded into the count. ⚠ disagree — `/product/*` is not disallowed, but the Terms prohibit data gathering |
| Amazon | 1 | dom | permits `/dp/` | forbids extraction | `curl_cffi` + the **add-to-cart control**, no browser — Amazon serves `/dp/<ASIN>` to impersonated HTTP and ships no structured data in it | ⚠️ Working, `[degraded]` `[dom]` — cheapest transport here, most fragile extraction: a buy-box redesign breaks it silently, so a control watch and mutation M8 both cover it. Its only GO Plus + offer is a **used** unit at **$219** from a reseller, suppressed twice over. ⚠ disagree — no rule matches `/dp/<ASIN>`; the Conditions of Use forbid extraction |
| Target | 3 | dom | permits `/p/` | forbids extraction | Headless browser + the **add-to-cart button** — Target ships no structured data on `/p/` and renders stock client-side | ⚠️ Working, `[degraded]` `[dom]` — control-only, and the most fragile row here: degraded on both axes. Target **delisted** the GO Plus + (TCIN `88714054`), a disproof rather than an omission. Rendering the page makes Target's own JavaScript fetch three hosts publishing `Disallow: /` — measured, and recorded in [`QUESTIONS.md`](QUESTIONS.md) § 0d. ⚠ disagree — `robots.txt` does **not** disallow `/p/` |

**Six working retailers — read them as a four and a two.** Best Buy and Target
are control-only: live and control-verified, but neither lists the GO Plus +, a
recorded disproof rather than an omission. **Four can page you:** GameStop,
Walmart, Nintendo and Amazon. Pokémon Center is dropped and not padded into the
count — walked down the whole ladder, refused at every rung. And a browser is not
a strict upgrade: the same headless Chrome that reads Best Buy is served a
Cloudflare wall by gamestop.com, so rung 3 is for a retailer that refuses HTTP
*at the connection layer*, not for a fetch that failed once.

Every probe, position and reversal behind this table — URLs, statuses, dates — is
in [docs/retailer-evidence.md](docs/retailer-evidence.md).
`scripts/evidence_check.py` and `tests/test_support_matrix.py` stop the table, the
count and the rungs drifting from the code, on every `make verify`.

## Install

**The distribution name is `bot-y`, with a hyphen**, while the import package and
console script are both `boty` — and `boty` on PyPI is a **different package
published by someone else**: version 0.1.1, two releases, the last on
**2012-03-10**. `pip install boty` succeeds and installs a stranger's
fourteen-year-old code. PyPI does not release a name that has files on it, so
this warning is the whole mitigation, which is why it sits above the command.

```bash
pip install bot-y
```

Publication happens from the `v0.4.0` tag. If pip reports no matching
distribution, the tag has not been pushed yet and the clone is the way in:

```bash
git clone https://github.com/danieljamesjohnson/bot-y
cd bot-y
python3 -m venv .venv && .venv/bin/pip install -e .
```

### The browser rung (only if you want Best Buy or Target)

Rung 3 needs an optional extra and a browser binary, kept separate so
contributors on rung-1 retailers never pull a browser stack:

```bash
.venv/bin/pip install -e '.[browser]'
export BOTY_BROWSER_PATH=/path/to/chrome    # only if none is on PATH
```

On Ubuntu 24.04 an *unpackaged* Chrome cannot build its sandbox and aborts on
startup; `BOTY_BROWSER_NO_SANDBOX=1` works around that, opt-in and per host, at a
real cost in isolation because this transport executes retailer JavaScript — a
distro Chrome package is the better fix. Chrome also drops its sandbox when run
as root whatever that variable says, so run bot-y unprivileged. **Under systemd,
put both variables in the unit's `EnvironmentFile`, not just your shell** —
exporting them interactively makes `make verify` pass while the deployed service
still cannot find a browser.

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
boty check                                      # one pass, print a table
boty watch                                      # loop, notify on transitions
export BOTY_NOTIFY_URL='tgram://<token>/<chat>' # Apprise: ntfy, Discord, Slack, ~100 more
```

**Pick controls carefully.** A grocery staple is ideal — first-party, restocked
daily, never contested. Don't use a console: on Walmart those are often held by
marketplace sellers, so an out-of-stock reading would be *correct* and you'd
chase a bug that isn't there.

## Adding a retailer

Usually not much more than adding a product — GameStop, Walmart and Nintendo have
**no adapter code at all**. [docs/adding-a-retailer.md](docs/adding-a-retailer.md)
walks Nintendo end to end on that basis, then Amazon as the opposite case.
[CONTRIBUTING.md](CONTRIBUTING.md) is the shorter one: setup, the commit hook,
and what a PR has to carry.

## Verifying it works

```bash
make verify           # everything, including live retailer checks
make verify-offline   # same minus the live check — for CI
```

It exits 0 only if every stage below passed. The three greens are kept apart
because "everything passed" and "we could not check some of it" must not look the
same: `VERIFY: PASS`, `PASS (INCOMPLETE — ...)` when some live controls could not
run *on this host*, `PASS (OFFLINE — ...)` when nothing live ran, or `FAIL
(<stage>)`. INCOMPLETE is the ordinary result of a fresh clone — the shipped Best
Buy control needs rung 3 — and it is a gap in *your machine*, not the detector.

| Stage | Proves |
|---|---|
| `identity` | No host identity — IP, coordinates, tokens — in **any** tracked file |
| `lint` | `ruff` is clean over `boty/`, `scripts/` and `tests/` |
| `test` | The offline suite still passes — no network touched, no browser started |
| `types` | `mypy` is clean over `boty/` and `scripts/` |
| `fixtures` | Warns about fixtures older than 90 days or missing a capture note. Never fails |
| `controls` | Live control products still read in stock |
| `mutation` | The suite would actually notice a broken extractor |

Fixtures catch *code* regressions offline but keep passing forever after a
redesign; live controls catch *reality*. `mutation` corrupts specific behaviours
in a throwaway copy and requires the tests to go red for each, because a green
suite is not evidence that it detects anything.

## Being a good citizen

Default cadence is 5 minutes with jitter, plenty for a drought that lasts weeks.
Polling every few seconds buys nothing and is what gets an IP blocked. This is a
personal notification tool: it does not add to cart, does not check out, and does
not run at a scale that would be unfair to anyone else shopping.

## License

MIT — the full text is in [LICENSE](LICENSE). Contributions are accepted under
the same licence; see [CONTRIBUTING.md](CONTRIBUTING.md).
