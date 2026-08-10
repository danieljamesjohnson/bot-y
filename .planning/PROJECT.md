# bot-y

## What This Is

A self-hosted restock monitor for big US retailers that tells you when it breaks.
It watches product pages for a hand-curated set of retailers and pushes a
notification the moment something is genuinely buyable — from the retailer
itself, at a sane price, verified by a detector that proves it still works.

It exists because the field is dead: the open-source big-retailer monitors on
GitHub stopped getting real commits in 2021–22, right when Akamai and
PerimeterX got serious. What survives either targets soft Shopify/sneaker
sites, or is a general-purpose page watcher aimed at the most defended pages
on the consumer web — and gets served a CAPTCHA.

## Core Value

**A stock reading you can trust.** Never report "out of stock" when the truth
is "I couldn't tell", and never report "in stock" when the truth is "a
reseller has one at 4x MSRP."

Everything else — breadth, speed, UI — is negotiable. This is not. A monitor
you wrongly believe is working is worse than no monitor, because you stop
looking yourself.

## Requirements

### Validated

<!-- Shipped and confirmed working against live retailer pages. -->

- ✓ Three-state availability (`in_stock` / `out_of_stock` / `unknown`) — a detector that cannot parse a page says UNKNOWN, never OUT_OF_STOCK
- ✓ Control products — known-in-stock items that prove each retailer's detector still works; a failing control raises a health alert
- ✓ Seller-aware detection + price ceiling — verified rejecting a $229.99 marketplace listing against a $54.99 MSRP, twice over
- ✓ TLS-impersonation fetching (`curl_cffi`) — reaches GameStop and Walmart, where a full Playwright browser got "Robot or human?" and 403
- ✓ Structured-data extraction — schema.org JSON-LD and Next.js hydration payloads instead of CSS selectors
- ✓ GameStop and Walmart adapters, both control-verified
- ✓ Apprise notifications (Telegram confirmed delivering end-to-end)
- ✓ YAML product config — adding a watch is editing a file, not a type union
- ✓ Deployed on danserver: `boty.service` + `boty-web.service`, status page behind the Mission Control `/tools/boty` proxy

### Active

<!-- v1 scope. Done = 5+ retailers with green controls, AND Dan gets a GO Plus +. -->

- [ ] Curated adapters for ~10 big US retailers, each with a control product
- [ ] Best Buy via a credential-free path (rung 3, browser, DEGRADED); official API optional on top
- [ ] Test suite covering the extraction layer — the place where a silent regression is most dangerous
- [ ] Type hints throughout
- [ ] Contributor-facing docs: how to add a retailer, why controls are mandatory
- [ ] Dan successfully buys a Pokémon GO Plus +

### Out of Scope

- **Generic "works on any URL" extraction** — chosen against deliberately. changedetection.io already does this well with a six-layer ladder, and its coverage collapses to layer one on exactly the retailers we care about. Ten provably-correct retailers beats a hundred maybes.
- **Async / concurrent checking** — ~10 retailers on a 5-minute interval takes seconds sequentially. Real complexity, zero present benefit. Revisit when watch count actually hurts.
- **A formal plugin API** — premature. Design it after ~10 adapters reveal the natural interface, not before.
- **Web UI beyond the read-only status page** — the CLI plus a phone-readable status page is enough; a settings UI is undifferentiated work changedetection.io already owns.
- **Auto add-to-cart / checkout** — this is a notification tool. Automated purchasing is a different product with different ethics.
- **Forking changedetection.io** — it's Apache-2.0 and actively maintained (last push 2 days ago, external PRs merged at a 2-day median). Forking means permanently diverging from a fast-moving upstream to add one concept — control products — that its per-watch architecture has no place for.
- **Aggressive polling** — 5-minute default with jitter. A drought lasts weeks; sub-minute polling buys nothing and is what gets an IP blocked.

## Current Milestone: v0.2 — Say Only What You Measured

**Goal:** every claim bot-y makes — in an alert, in a reading, in the README, in its
own version number — is backed by something it actually measured.

**Why this, and why now.** Four days of live operation after Phase 4 produced six
findings with one shape. Each is the system stating something it had not established:

| The claim | What was actually true |
|---|---|
| *"the detector is probably broken"* (Walmart control page) | It was not. Three live reads returned `IN_STOCK` at $2.42 and `nextdata_offers` gave `available=True` |
| *"we are asking too often"* (refusal page) | Falsified: after backing off to a 6-hour interval, the very next single request was still refused. Twice |
| A Walmart reading is about **Walmart** | It is about *some store*. Nothing is pinned, and the recorded price differed from the live one ($3.17 vs $2.42), which is what proved it |
| The price ceiling filters resellers | It reads `offer.price`. A $54.99 listing with $45 shipping walks straight through |
| The README support matrix states each retailer's rung | Not bound to code — mutating `check_amazon` to return `Rung.BROWSER` against a README saying rung 1 left **131 tests green** |
| The published changelog says what was written | Nothing reads its body. It shipped with leaked tool-call markup for a whole phase, on the path to PyPI |

**And the version number was the same error.** v1.0.0 was declared before the project
had shipped, published, or bought anything; the milestone audit then had to record that
its own definition of done was unmet. **Renumbering to v0.2 is not bookkeeping — it is
the version finally matching what was measured**, which is this milestone's whole thesis
applied to itself. Safe to do only because publishing was deferred: nothing was ever
tagged or uploaded, so no one can be pinned to a 1.0.0 that exists.

**The one that is not cosmetic.** Store pinning is not about a noisy milk control. The
same unpinned assignment governs the **GO Plus + watch on Walmart** — one of only four
retailers that can alert on the real product. A restock reading there is currently a
statement about an arbitrary store, not about Walmart. Never observed going wrong; also
never prevented.

**v1.0.0 stays open and untagged**, exactly as its audit recommended. Its definition of
done — *Dan has successfully bought a Pokémon GO Plus +* — is a market condition, and it
closes when the market moves rather than when we decide it has. Phase numbering continues
from 5.

**Explicitly not in scope:** eBay. Registration for the eBay Developers Program was
**rejected** on 2026-08-10 — see `.planning/research/ebay-CLOSED-registration-rejected.md`.
The one finding worth keeping from it is in scope above: the delivered-total ceiling.

## Context

**Origin.** Dan wanted a Pokémon GO Plus + (MSRP $54.99), which is out of stock
nearly everywhere; the only listings are marketplace resellers at $139–$229.
An existing Selenium + `undetected_chromedriver` script for Nintendo Switch 2
was the starting point.

**What we ruled out, with evidence:**

- **changedetection.io** — deployed it, and its Playwright fetcher was served "Robot or human?" by Walmart and a 403 by GameStop. Not a bad tool; a browser fixes the JavaScript fingerprint and leaves the TLS fingerprint untouched, which is the layer that actually gates access.
- **streetmerchant** (5.4k stars) — ran it. Its bundled Chromium no longer installs; with a modern Chrome symlinked in, it does work. But its whole product model is hardcoded TypeScript unions: adding one SKU meant editing `Series`, `Model`, a per-series price map, and three store files.
- **Everything else** — big-retailer monitors on GitHub last pushed 2021–22. The Pokémon-specific ones are 0–2 star personal scripts.

**The key technical insight.** Anti-bot systems read the TLS ClientHello before
a single HTTP header arrives, so header spoofing is theatre and a headless
browser doesn't help. `curl_cffi` replays a real Chrome TLS stack and reaches
pages a full browser cannot. Fingerprint and IP reputation are complementary —
danserver is on a residential connection, which is the expensive half of that
pair and the reason this works at all without paying for proxies.

**Prior art worth respecting.** changedetection.io cross-checks structured data
against page text and logs `"Lie detected in the availability machine data!!"`
when they disagree — retailers' JSON-LD does lie. Worth adopting.

## Constraints

- **Tech stack**: Python 3.10+, `curl_cffi`, PyYAML, Apprise — deliberately small. Every dependency added to a monitor is another thing that can silently break it.
- **Runtime**: danserver (Xubuntu 24.04), systemd, loopback-bound services reached over Tailscale. No public exposure.
- **Fetching**: no-browser-first. A browser is a last resort, not the default — it's slower, heavier, and empirically less effective here.
- **Ethics/rate**: personal-scale notification tool. No cart automation, no checkout, no polling rate that would be unfair to other shoppers.
- **Secrets**: credentials live in `~/.config/boty/env` (mode 600) via systemd `EnvironmentFile`, never in the repo. Set through `boty-secret`, which prompts hidden and verifies before writing.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build new rather than fork changedetection.io | Apache-2.0 and healthy, but control products need a cross-watch relationship its per-watch model has no place for. Forking a fast-moving 32.6k-star project to add one concept is a permanent tax | — Pending |
| Curated adapters over generic extraction | 10 provably-correct retailers beats 100 maybes. Generic ladders collapse on exactly the defended retailers that matter | — Pending |
| `curl_cffi` over browser automation | Empirically reached GameStop and Walmart where Playwright was blocked, same machine, same minute | ✓ Good |
| Structured data over CSS selectors | JSON-LD carries availability, price *and seller*; selectors rot silently, which is the documented cause of death for prior tools | ✓ Good |
| UNKNOWN as a first-class state | Conflating "can't parse" with "out of stock" is the silent failure that makes a monitor look healthy while missing every drop | ✓ Good |
| Control products mandatory per retailer | The only way to detect the above from outside. Already caught a missing-control gap on Walmart on its first run | ✓ Good |
| Skip async and a plugin API for now | "Only what is necessary." Neither earns its complexity at current scale | — Pending |
| Narrow to ~7 likely stockists | The list of ten was padded. Newegg, B&H and Micro Center are PC-parts stores that do not carry Pokémon accessories; watching them manufactures fake breadth and real maintenance | — Pending |
| Four-rung escalation ladder | TLS → official API → browser (flagged DEGRADED) → drop with evidence. Gets coverage without lying about confidence: a retailer reached only via a browser rests on the fragile path we moved away from, and the matrix says so | — Pending |
| Primary paths must work from a fresh clone | Best Buy's official API needs manual approval and a non-free email domain — most people cloning the repo cannot get one, so building Best Buy support on it would make the retailer a footnote rather than supported. Credential-gated paths are optional enhancements only | — Pending |
| Fixtures frozen, not auto-refreshed | Auto-refreshing in CI would let a real breakage land disguised as a fixture update — the exact silent failure this project exists to catch. Fixtures catch code regressions; live control products catch reality | — Pending |
| Tests + type hints in scope | Follows from choosing a real open-source project — a contributor's PR must not be able to silently break a detector | — Pending |

---
*Last updated: 2026-08-02 at project bootstrap, after shipping a working two-retailer MVP*
