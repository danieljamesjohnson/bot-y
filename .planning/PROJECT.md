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

<!-- v0.2's seven requirements are complete and gated, but four of them are BEHAVIOURAL and
     none of those four is running. They are listed apart from the block above rather than
     folded into it, because that block says "confirmed working against live retailer pages"
     and these are confirmed against the tree. -->

**Built and gated in v0.2 — in the tree, NOT in effect on the deployed daemon:**

- ⧗ Walmart store pinning — required config, no default; an unpinned or unexpected store is UNKNOWN, never a verdict (REQ-14, v0.2) — *needs `WALMART_STORE_ID` and a restart*
- ⧗ No alert names a cause that was not measured; where the cause is unknown the alert says so (REQ-15, v0.2) — *needs a restart*
- ⧗ Notify only when a human decision changes the outcome; backoff and paging memory survive a restart (REQ-16, v0.2) — *needs a restart*
- ⧗ The price ceiling measures the delivered total wherever shipping can be read; where it cannot, the alert goes out showing `shipping: unknown` (REQ-17 **as revised by Dan, 2026-08-11**, v0.2) — *needs a restart*

**Built and gated in v0.2 — in effect, because they are test-suite gates:**

- ✓ The README support matrix's `Rung` cell bound to the code across both joins, two-directionally, by AST — v0.2
- ✓ `CHANGELOG.md` and `.github/workflows/` gated on their **contents**, watched going red against the byte-exact documents that shipped — v0.2
- ✓ One version, four records, `pyproject.toml` authoritative, compared component-wise — v0.2

### Active

<!-- v1 scope. Done = 5+ retailers with green controls, AND Dan gets a GO Plus +. -->

- [ ] Curated adapters for ~10 big US retailers, each with a control product
- [ ] Best Buy via a credential-free path (rung 3, browser, DEGRADED); official API optional on top
- [ ] Test suite covering the extraction layer — the place where a silent regression is most dangerous
- [ ] Type hints throughout
- [ ] Contributor-facing docs: how to add a retailer, why controls are mandatory
- [ ] Dan successfully buys a Pokémon GO Plus +
- [x] **Deploy v0.2** — DONE 2026-08-12 (`4609d95`), at Dan's direction, measured back off `status.json` rather than assumed. **REQ-14 is the exception and is still not in effect**: Walmart cannot alert on the GO Plus + until `WALMART_STORE_ID` is set (unset — measured as a count, `0`)
- [ ] **Deploy v0.3** — `sudo systemctl restart boty` migrates `state.json`, publishes `read_at` / `checked` / `current_interval_seconds`, and makes the age visible at all. **Verified safe by execution** against copies of all three live pre-phase documents. Deferred by Dan twice (`QUESTIONS.md` § 0f). Until then every published row is a reading with no age — the exact claim v0.3 exists to remove

### Out of Scope

- **Generic "works on any URL" extraction** — chosen against deliberately. changedetection.io already does this well with a six-layer ladder, and its coverage collapses to layer one on exactly the retailers we care about. Ten provably-correct retailers beats a hundred maybes.
- **Async / concurrent checking** — ~10 retailers on a 5-minute interval takes seconds sequentially. Real complexity, zero present benefit. Revisit when watch count actually hurts.
- **A formal plugin API** — premature. Design it after ~10 adapters reveal the natural interface, not before.
- **Web UI beyond the read-only status page** — the CLI plus a phone-readable status page is enough; a settings UI is undifferentiated work changedetection.io already owns.
- **Auto add-to-cart / checkout** — this is a notification tool. Automated purchasing is a different product with different ethics.
- **Forking changedetection.io** — it's Apache-2.0 and actively maintained (last push 2 days ago, external PRs merged at a 2-day median). Forking means permanently diverging from a fast-moving upstream to add one concept — control products — that its per-watch architecture has no place for.
- **Aggressive polling** — 5-minute default with jitter. A drought lasts weeks; sub-minute polling buys nothing and is what gets an IP blocked.

## Current State

_As of 2026-08-19, after milestone v0.3 closed and was archived._

**Milestone v0.3 — Say When You Measured It — is COMPLETE IN THE TREE, and NONE OF IT IS
RUNNING.** One phase (7), one requirement (REQ-21), 7 plans, **72 commits**, **+18,146/−104
across 41 files**, 2026-08-13 → 2026-08-19. The gate went from **778 passed / 26 mutations** at
the start (`dbc9d49`) to **884 passed / 0 skipped, 34/34 mutations, survivors 0** at close, mypy
clean over 18 source files, identity PASS over 225 files, `make verify-offline` **EXIT=0**.
Archived in [`.planning/milestones/v0.3-ROADMAP.md`](milestones/v0.3-ROADMAP.md),
[`v0.3-REQUIREMENTS.md`](milestones/v0.3-REQUIREMENTS.md) and
[`v0.3-MILESTONE-AUDIT.md`](milestones/v0.3-MILESTONE-AUDIT.md) (audit status `tech_debt` — no
blockers, no unsatisfied requirements, six residuals carried forward).

**NOT DEPLOYED, and the running code is OLDER THAN THE MILESTONE. This is the sentence that
matters.** `boty watch` `MainPID=547119`, `ActiveEnterTimestamp=Wed 2026-08-12 17:28:29 CDT` —
roughly **fifteen hours before v0.3's first commit**, so the deployed daemon has never at any
moment held a line of this milestone's code. Measured on the live documents rather than inferred:
`served/boty/status.json` carries **none** of the four keys v0.3 added and publishes **10** rows
for 13 configured watches; `state.json` still holds **13 bare pre-07 strings** with no version
field. **The gap is one command wide** — `boty` is an editable install, so
`sudo systemctl restart boty` migrates `state.json` to its dated shape, starts publishing
`read_at` / `checked` / `current_interval_seconds`, makes the dashboard show 13 rows instead of a
varying 3–10, and makes the age visible at all. **That restart is verified SAFE BY EXECUTION**,
not argued: the new code was run against copies of all three live pre-phase documents — 13/13
availabilities survive, 0 ages invented, the pacer document round-trips, and the real
`config/products.yaml` does not trip the new WR-02 config guard — with rollback cost bounded at 2
duplicate restock pushes. It is deferred by Dan's decision recorded twice (`QUESTIONS.md` § 0f,
2026-08-10 and 2026-08-17, the second verbatim `keep defer`), and it is **his action**.

**Two of v0.3's five criteria did not close clean, and neither was rounded up.** Criterion 3 is
**MET IN PART by Dan's explicit decision of 2026-08-17** — `status.json` publishes the
*ingredients* of a staleness verdict (`read_at`, `checked`, `current_interval_seconds`) and **no
verdict**; both rendering surfaces do present one. Criterion 5 is **MET, QUALIFIED**: 07-05's join
test was watched going red 5/5 on 2026-08-19, establishing non-vacuity, **but after the fact
against an implementation that already existed — the original RED was never observed and TDD
ordering was not followed for that test.** No criterion text was amended at any point.

**A post-close code review found 1 Critical + 8 Warnings; all nine were fixed.** The Critical was
a reproduced XSS sink — `served/boty/index.html` interpolated `w.availability` into a
`class="dot ${...}"` attribute unescaped, reachable because v0.3 publishes any string from
`state.json`, and the gate that should have caught it named a sibling field and omitted this one.
Three Info findings were recorded and **not** fixed; the one worth a plan is IN-03, an unguarded
dashboard render that freezes the page silently on a malformed payload.

**v0.2, by contrast, IS on the wire.** It was deployed on 2026-08-12 (`4609d95`) at Dan's
direction and measured back off `status.json` rather than assumed. **Two statements in
§ Requirements above are therefore one revision behind and are corrected here rather than
silently:** the block headed *"Built and gated in v0.2 — in the tree, NOT in effect on the
deployed daemon"* is true only of **REQ-14** now, which still needs `WALMART_STORE_ID` (unset —
measured as a count, `0`, never a value); REQ-15, REQ-16 and REQ-17 have been in effect since
2026-08-12.

**NOT TAGGED, NOT PUBLISHED — and that is now a recorded decision rather than a deferral.**
`git tag -l` → **0**, re-measured at the v0.3 archival; PyPI returns 404 for `bot-y`. **Dan chose
no tag explicitly on 2026-08-12, matching v1.0.0.** `pyproject.toml` reads **`0.3.0`**, bound
component-wise to `STATE.md`'s `milestone:` key and to three other records with `pyproject`
authoritative. The `Development Status` classifier is `4 - Beta`, bound to the version in both
directions.

**v1.0.0 is still open and untagged, and was NOT archived by either close.** Its definition of
done includes *"Dan has successfully bought a Pokémon GO Plus +"* — a market condition, not a work
item — and its audit recommended against tagging it shipped. Its phases (1–4 and 3.1) and their
details stay in `.planning/ROADMAP.md`, untouched. REQ-11 (`pip install bot-y` from PyPI, plus a
v1.0.0 tag) remains **descoped from v1.0**, not complete.

**Codebase:** 18 source files under `boty/` (mypy clean), six retailers registered and
control-verified, **13** configured watches (not the 14 a `grep` reports — the fourteenth match is
a comment), a full `boty check` pass in ~43 s of REQ-08's 120 s budget.
**Known live-gate state:** `make verify` exits 2 on this host for three pre-existing reasons —
two controls cannot run at all (no Chrome/Chromium binary on PATH: Best Buy and Target), Walmart
reads UNKNOWN for want of a store pin, and Amazon's challenge class is intermittent
(present-absent-absent-present across four passes). None is a detector defect; none is owned yet.

## Milestone v0.2 — Say Only What You Measured (closed 2026-08-11)

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
| Store pinning is required config with no default (Dan, 2026-08-10) | A default leaves a reading as a statement about an arbitrary store, which is the bug. Geolocating from a ZIP was rejected too: bot-y never guesses where the user lives | ✓ Good — one setup step, deliberately accepted |
| Renumber v1.0.0 → v0.2 | The v1.0 numbering was itself the overclaim this milestone corrects — declared before the project had shipped, published or bought anything. Safe only because publishing was deferred and nothing was ever tagged or uploaded | ✓ Good |
| Defer the deploy (Dan, 2026-08-10) | Answered `defer` at the store-pin checkpoint. Priced as one decision — later measured to be two, with three of four requirements deployable by a plain restart | ⚠️ Revisit — the running monitor still makes every claim v0.2 fixed |
| REQ-17 reversed: alert even when shipping is unresolvable (Dan, 2026-08-11) | *"where we don't know just send it … it's worse to feel like you 'missed out'."* Recorded beside the original, never over it, after the cost was measured and shown to him | ⚠️ Revisit — the hole REQ-17 names is knowingly reopened; the mitigation is a visible empty field |
| A criterion is never amended to make it meetable — and by the same rule not to make it accurate either | Established when Phase 3.1 declined a rewrite; upheld through Phase 4's two UNMET, Phase 5's NOT OBTAINED rows and Phase 6's MET IN PART. Stale figures inside REQ-18 were flagged and left unedited | ✓ Good |
| Verification is an exit code, not a judgement | `make verify` / `make verify-offline`. 531 passed / 8 mutations at v0.2's start, 769 / 24 at its close, every new gate watched going red before it was trusted | ✓ Good |

---
*Last updated: 2026-08-19 at the v0.3 milestone close — v0.3 complete in the tree and NOT on the wire (the running daemon predates its first commit); v0.2 deployed 2026-08-12 except REQ-14; v1.0.0 still open and untagged; zero git tags, by Dan's explicit choice*
