---
gsd_state_version: 1.0
milestone: v1.0.0
milestone_name: milestone
status: Phase complete — ready for verification
stopped_at: Completed 04-02-PLAN.md
last_updated: "2026-08-05T00:00:22.952Z"
last_activity: 2026-08-04
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 23
  completed_plans: 18
  percent: 60
---

# State: bot-y

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-08-02)

**Core value:** A stock reading you can trust — never "out of stock" when the truth is "I couldn't tell", never "in stock" when the truth is "a reseller has one at 4x MSRP."
**Current focus:** Phase 04 — open-source-ready

## Status

**Milestone:** v1.0
**Phase:** 03.1 of 5 (Target and Amazon, supported) — **COMPLETE**. INSERTED, reverses a Phase 3 decision
**Plan:** 5 of 5 complete (01, 05, 02, 03, 04 — all waves done)
**Last session:** 2026-08-05T00:00:22.947Z
**Stopped At:** Completed 04-02-PLAN.md

1. **The § 0e history purge (2026-08-04).** Dan chose option 2. `filter-repo` over all 170 commits, force-pushed, verified against a fresh clone. Backup bundle at `~/CodeProjects/bot-y-prefilter-20260803-1745.bundle` is the only remaining copy of the values. Prevention shipped with it: `scripts/identity_check.py` scans **every tracked file** (the leak that mattered was in `.planning/`, not `tests/fixtures/`) and runs at commit time via a tracked `hooks/pre-commit` + `make hooks`, as well as inside `make verify`.

2. **Pacing and backoff (2026-08-04), in response to a live alert.** Amazon and GameStop had been refusing us for a day. Not a detector bug: `interval_seconds` is per PASS, so load is `watches x 288/day` — Amazon 576, GameStop 1,440 — with no backoff at all. Worse, every failing control was reported as "the detector is probably broken", which is false for a refusal and sent 20 pages in 24 hours. Added `Result.refused` / `fetch.is_refusal`, split the health message, added `boty/pacing.py` (per-retailer cadence + exponential backoff, capped, reset on a good read), and stopped paging for refusals until they outlast the backoff. Verified live: 0 pages while both retailers refused, both published as `paced` rather than dropped.

**Last Activity:** 2026-08-04
**Last Activity Description:** Phase 04 execution started

3. **Two live detector failures (2026-08-04 evening), both caught by control products within a cycle, neither a broken detector.** Best Buy began serving its JSON-LD **JavaScript-escaped** — `\'` inside strings, literal `\n` outside them — so `json.loads` refused all three blocks, `parse.py` skipped them silently, and the control read UNKNOWN with a detail naming the wrong cause. Proven against the shipped fixture, which parses 3/3 on the same SKU with no backslashes at all. `ldjson_read` now parses strictly first and only then offers an already-failed block to a string-state-aware repair; it reports `blocks`/`unparseable`/`repaired`, and a repaired read publishes as `ld+json (repaired)` so it cannot look ordinary. **Not claimed:** that the repair restored the live reading — Best Buy was serving valid markup again by 17:45 and the live read carried no `(repaired)` marker. The escaping is intermittent; a clean probe does not disprove it. Separately, **Target's UNKNOWN was our own render race**: ~35 KB of markup carrying the add-to-cart control arrives between 1s and 3s (measured: absent at `settle=1.0`, present at 3.0 and 6.0), and `fetch_rendered`'s default is exactly 3.0. `check_target_browser` now re-renders once at 10.0s before concluding — in the adapter, because it is a layout question and `boty/browser.py` is deliberately ignorant of layout. **M2's anchor was re-pointed** because this change moved the line it named, and the harness refused to run rather than quietly drop to seven mutations. Verified: mypy clean, 419 passed, 8/8 mutations, `VERIFY: PASS (OFFLINE)`, both new gates watched failing in both directions (removing the repair reddens 3 tests, making it over-reach reddens 22), **service restarted onto the fixed code** and publishing **6/6 retailers healthy**, 13 watches, 47.1s of REQ-08's 120s.

**Previously:** 03.1-03 **asked Amazon the question Phase 3 never asked, and Amazon answered.** Three `/dp/<ASIN>` requests through `boty.fetch.get`: **HTTP 200 every time**, 1,893,079 / 3,189,747 / 3,223,370 B, **zero `BLOCK_PHRASES` matches**, correct product titles. So the rung-4 verdict that rested entirely on a reading of the Conditions of Use is now `**Verdict: REACHABLE (rung 1)**` — and **nothing behind the old verdict was retracted**: the six policy reads, the LICENSE AND ACCESS clause and the whole `robots.txt` analysis all stand, and the four sentences saying no product page had ever been requested are quoted, dated and marked historical rather than edited. **Shape C: rung 1 + `dom`.** Amazon publishes NO structured data on `/dp/` — zero `ld+json`, no `__NEXT_DATA__`, and not one JSON blob with a price, an availability or a seller — but it serves the add-to-cart control, the `#availability` line and a named buy-box seller in the plain HTTP response. So `check_amazon` is the cheapest transport in this project with the most fragile extraction in it, which is precisely what 03.1-05 widened `degraded` for. **The ASIN came from the Internet Archive CDX index; zero requests to amazon.com to find it.** `parse.add_to_cart_offers` was **widened, not duplicated** — Amazon's control is a void `<input>` labelled by its `value` attribute — and its seller default is now **per page family**, because carrying Target's first-party-by-absence rule to Amazon would have let a reseller alert off any buy box the parser could not read. Amazon **does** list the GO Plus +, and the only offer is a **USED unit at $219 from `LO Store (We Record Serial Numbers To avoid FRAUD)`** against $54.99 MSRP: both flipper defences suppress it, the seller filter first. **Amazon refused us exactly once, and it was our own fault** — two captures 12 s apart instead of 20 — and that wall **matched no `BLOCK_PHRASES` entry**, so `fixtures.capture` wrote a captcha gate to disk under a product's name. Deleted, phrase added, wall embedded verbatim as a test constant; the obvious phrase was rejected because *"something went wrong on our end"* appears in both real Amazon product pages. **Rule 6 landed too:** a REFUSED verdict must now cite a *measured* observation, HARD_TWO members need two including one at rung 3, and it is watched going red against the **verbatim pre-03.1 § Amazon and § Target text lifted from `339800e`** — 658 lines of accurate writing containing not one observation. Live: **6/6 controls**, `healthy: true`, 13 watches across 6 retailers in **48.9 s** of REQ-08's 120 s, `make verify` bare-PASS, 8/8 mutations, 377 tests.

**Previously:** 03.1-02 registered **Target — the fifth retailer**, at rung 3 with `dom` extraction, **control-only**. Its pages carry no structured data at all, so `parse.add_to_cart_offers` reads the rendered add-to-cart button: enabled means buyable, `disabled=""` means out of stock. That distinction is measured, not assumed — Target KEEPS the button and disables it — which is what lets the reader return `None` (UNKNOWN) for an absent control without trading anything away. `check_target_browser` labels `rung=browser` + `extraction=dom` on every path, and `_verdict_from_html` gained an opt-in `allow_dom` that carries `extraction=` on all six returns including the no-offers UNKNOWN (plan-check W-2 closed). `FIRST_PARTY['target']` stopped being an unverifiable guess and became a statement about our own reader's output. M8 mutates the availability decision; 8/8 caught. Live: **5/5 controls**, Target IN_STOCK $12.59, `[control] [degraded] [dom]`, full pass 40.1 s of REQ-08's 120 s, `make verify` bare-PASS. **The fixture nearly repeated the incident that destroyed this repo:** the raw capture carried a session token, a visitor id, Akamai's geolocation of this host and five nearby stores with street addresses — and the automated leak guard PASSED on it, because it knew EdgeScape's `lat=` form and Target writes JSON. Redacted by emptying every `<script>`; the guard was then widened and **found the same leak class already committed in two Walmart and two Best Buy fixtures**, including this host's own ZIP, public since Phase 2. All redacted. Target still cannot watch the GO Plus + — it delisted the product — so ROADMAP criterion 1 stands UNMET.

**Previously:** 03.1-05 shipped the **Extraction axis** — `Extraction` (`structured` | `dom`) beside `Rung` as a second independent axis, nothing renumbered, with `Result.degraded` widened to `self.rung is Rung.BROWSER or self.extraction is Extraction.DOM`. That closed a latent hole before the adapter that would have exposed it, and 03.1-02 is the adapter: Best Buy and Target are both "browser", and only the extraction axis says that one reads a schema.org feed and the other reads markup a reskin breaks silently. Before that, the rung-1 probe (`c79e8ce`, kept as `03.1-02-PROBE-RECORD.md`) found Target serving the page and withholding the data, and disproved that Target still lists the GO Plus +.
**Resume File:** None
**Next command:** **`/gsd-execute-phase 4`** — and NOT `/gsd-autonomous`. Phase 4 is already planned: 6 plans in 6 waves, committed, plan-checker passed at round 3 after two revision rounds (7 → 5 → 3 issues). `/gsd-autonomous` would re-enter plan-phase, find existing plans, and stop on the interactive add/view/replan prompt. Execution is authorised for **waves 1–5**; **wave 6 (`04-06`) is `autonomous: false`** and checkpoints for Dan — the PyPI Trusted Publisher is dashboard-only and the `v1.0.0` tag is his to push. After the phase closes: `/gsd-audit-milestone` → `/gsd-complete-milestone v1.0.0` → `/gsd-cleanup`. **`main` has NO upstream configured** (`fatal: no upstream configured for branch 'main'`, a side effect of the 0e `filter-repo` + force-push) and 19+ commits are unpushed — set it with `git push -u origin main` when Dan says so. The § 0e blocker that caused the previous halt is **closed and executed**; nothing blocks Phase 4.

**One correction to what 03.1-03 wrote here, and it matters.** That entry claimed *"ROADMAP criterion 1 is now MET and Amazon is what moves it."* It is not. Criterion 1 is specifically **"Target reports stock for the GO Plus +"**, and Target *delisted* the product — so it **stands UNMET**, exactly as the ROADMAP records it and exactly as Dan decided when he declined the rewrite that would have made it meetable. Amazon carrying a real product watch is criterion **2**, which is met. Conflating the two would have quietly closed the one criterion this phase deliberately left open.

Carried forward for whoever picks up Phase 4:

- **Six retailers, and now actually deployed.** The service ran pre-phase code for the whole of waves 3–5. **A restart is part of shipping a retailer** — `make verify` runs the tree, not the daemon, and the two can disagree silently. Confirm with `served/boty/status.json` carrying 13 watches and six `retailers` health entries.
- **Read the six as a four and a two.** Best Buy and Target are control-only — neither carries the GO Plus + — so only **four** of the six could ever alert on the product. Now stated in README prose rather than left to be worked out from the table.
- **`TARGET_RETAILER_COUNT` is 5.** Do not raise it without a commit that says so and a test attached.
- **Pokémon Center is the only retailer in scope still REFUSED**, and it clears rule 6's higher bar with four observations across two rungs.
- **`_SHIPPED` in `tests/test_evidence_check.py` is still the four retailers** and still feeds synthetic trees — widen at the call site, not the constant.
- **`QUESTIONS.md` § 0e is the only open decision:** four already-public fixtures carry this host's ZIP in pushed git history. Not blocking; Dan's call between leaving it, a `filter-repo` rewrite, or recreating the repo.

## What Exists

Working and deployed on danserver before this roadmap was written:

- `boty/` — 854 lines: models, fetch, parse, retailers, monitor, notify, status, config, cli
- GameStop (schema.org JSON-LD) and Walmart (`__NEXT_DATA__`, seller-aware) adapters, both control-verified
- `boty.service` + `boty-web.service`, both active and enabled at boot
- Status page on loopback :8821, reachable at `/tools/boty` through Mission Control
- Telegram notifications, delivery confirmed end to end
- Repo public at https://github.com/danieljamesjohnson/bot-y (Apache-compatible MIT)

## Blocked

- ~~**Best Buy API key** — needed for REQ-04.~~ **No longer blocking.** 02-01 proved
  the credential-free rung-3 path works (`docs/retailer-evidence.md`), and REQ-04 is
  satisfied without a key. A key remains an optional upgrade: set `BESTBUY_API_KEY`
  and Best Buy prefers the API and drops the DEGRADED flag. Nothing waits on it.

## Known Risks

- ~~**Amazon may be unreachable** without a browser or paid residential proxies.~~ ~~**Settled 2026-08-03 by 03-01, and not for the expected reason.**~~ **Re-settled 2026-08-03 by 03.1-03, and the concern was backwards.** Amazon needs neither a browser nor a proxy: it serves `/dp/<ASIN>` to plain impersonated HTTP — three requests, three HTTP 200s, 1.9–3.2 MB, zero `BLOCK_PHRASES` matches. What it does *not* serve is any structured data at all: zero `application/ld+json`, no `__NEXT_DATA__`, no JSON blob carrying a price, an availability or a seller. So Amazon is **rung 1 + `dom`** — the cheapest transport here with the most fragile extraction here — reading the server-rendered add-to-cart control, `#availability` and buy-box seller. Every reading is `degraded` on the extraction axis alone. **The real risk is now the opposite one:** an Amazon buy-box redesign breaks this silently, with no error and no 403, which is why a control watch on `B00NTCH52W` and mutation M8 both cover it. Amazon also **throttles on cadence** — two requests 12 s apart drew a captcha interstitial at HTTP 200 that matched no block phrase, so `fixtures.capture` wrote it to disk; the phrase was added and the file deleted. Evidence in `docs/retailer-evidence.md` under `## Amazon`.
- ~~**Target is unresolved.**~~ ~~**Settled 2026-08-03 by 03-02, and not for a technical reason.**~~ **Re-settled 2026-08-03 by 03.1-02, and now it IS a technical reason.** Dan reversed the Terms-of-Use call, Target was probed on the path its own `robots.txt` publishes, and it **did not refuse us**: three pages, all HTTP 200, no challenge, no `BLOCK_PHRASES` match, `"isBot": false`. It also gave us nothing — **zero** `application/ld+json`, `"price"`, `availability` or `"seller"` anywhere in ~315 KB, because Target ships the price module empty (`isProductDetailServerSideRenderPriceEnabled: false`) and renders stock from `redsky.target.com`, which is `Disallow: /` for every agent. Rung 1 is open and empty; rung 2 is closed in writing; rung 3 reaches the data only by making the rung-2 requests through a browser. Still rung 4, but the reason is now an observation. **Target also no longer lists the GO Plus +** — TCIN `88714054` served HTTP 200 as late as 2025-05 and now 404s. Not registered: a control would read UNKNOWN forever. Evidence under `## Target`, 2026-08-03 heading; the open decision is `QUESTIONS.md` 0d.
- **Fixtures go stale.** Saved HTML is a snapshot; a retailer can change its page and the fixtures will keep passing. Control products cover the live case, fixtures cover regression — neither substitutes for the other, and Phase 1 should make that split explicit.

## Decisions Pending Evaluation

- Building new rather than forking changedetection.io
- Curated adapters over generic extraction
- Deferring async and a plugin API

---
*Last updated: 2026-08-02 at project bootstrap*

## Performance Metrics

| Phase | Plan | Duration | Notes |
|-------|------|----------|-------|
| Phase 01 P01 | 8min | 4 tasks | 11 files |
| Phase 01 P02 | 4min | 6 tasks | 5 files |
| Phase 01 P03 | 5min | 3 tasks tasks | 10 files files |
| Phase 01 P04 | 25min | 6 tasks | 5 files |
| Phase 02 P01 | 62min | 3 tasks | 6 files |
| Phase 02 P02 | 34min | 3 tasks | 10 files |
| Phase 02 P03 | 71min | 3 tasks | 12 files |
| Phase 02 P04 | 35min | 3 tasks | 15 files |
| Phase 03 P01 | 34min | 3 tasks | 6 files |
| Phase 03 P02 | 19min | 3 tasks | 4 files |
| Phase 03 P03 | 47min | 3 tasks | 10 files |
| Phase 03.1 P01 | 62min | 3 tasks | 5 files |
| Phase 03.1 P02 | 78min | 1 tasks | 3 files |
| Phase 03.1 P05 | 8min | 2 tasks | 11 files |
| Phase 03.1 P02 | 35min | 3 tasks | 21 files |
| Phase 03.1 P03 | 47min | 3 tasks | 17 files |
| Phase 03.1 P04 | 21min | 2 tasks | 5 files |
| Phase Phase 04 PP01 | 16min | 3 tasks tasks | 5 files files |
| Phase 04 P02 | 30min | 3 tasks | 5 files |

## Decisions

- [Phase 01]: FIXTURE_ROOT anchors to the repo root, not cwd — A cwd-relative fixture path makes load() succeed or fail depending on where the test runner was invoked from — flakiness that fixtures exist to remove
- [Phase 01]: A blocked or failed fetch writes no fixture at all — A CAPTCHA interstitial saved under a product name would make the whole suite assert against a bot wall while looking green
- [Phase 01]: Walmart GO Plus + reseller fixture is real, not synthetic — The live buy box is still held by Clove Brothers LLC at $229.99, so the plan's synthetic-fixture contingency was not needed
- [Phase 01]: The network guard has its own self-test — a guard nobody verifies can rot after an upstream rename and the suite would start hitting live retailers with no visible symptom
- [Phase 01]: Offline-ness proved by running the suite in an interface-less network namespace, not just by trusting the monkeypatch
- [Phase 01]: REQ-03 left unchecked by 01-02 — type hints and mypy are 01-03's deliverable, and marking it here would be a false green in the traceability table
- [Phase 01]: The planned mypy config was a false green — non-strict mypy skips unannotated function bodies, so the whole package passed before a single annotation was written — disallow_untyped_defs makes the check enforce REQ-03 rather than decorate it
- [Phase 01]: The type check was proved to bite by deleting the offer-is-None branch and confirming mypy flags it — A Success line over an unannotated codebase asserts nothing
- [Phase 01]: dev extra mypy floor raised 1.8 -> 2.0 — mypy 2.x is meaningfully stricter by default, so a contributor resolving 1.x would run a weaker check than the one this config was verified against
- [Phase 01]: Any confined to the JSON boundary in boty — _as_float, _dig, Page.json and _expand sit where a retailer payload shape is not ours to promise; every one of boty's own types is named
- [Phase 02]: Best Buy is REACHABLE on rung 3 — A headless browser reads its product pages and they carry complete schema.org data — availability, price and a first-party seller
- [Phase 02]: Best Buy's legacy /site/<slug>/<sku>.p scheme is uniformly refused with ERR_HTTP2_PROTOCOL_ERROR — The live scheme is /product/<slug>/<ID> where <ID> is not the SKU, so an adapter cannot construct product URLs from a SKU
- [Phase 02]: MARKETPLACES needs no change for Best Buy — Best Buy sets offers[].seller.name to 'Best Buy', already in FIRST_PARTY, so its offers never fall into the unattributed-on-a-marketplace UNKNOWN path and a control can go green
- [Phase 02]: No evidence Best Buy carries the GO Plus + at all — Two searches returned only gift cards and unrelated titles; SKU 6577129 in test_retailers.py:316 appears nowhere in Best Buy results and is an unverified fixture value
- [Phase 02]: nodriver installed as an OPTIONAL extra only, after a supply-chain audit — It is AGPL-3.0 to this project's MIT, and a contributor working on the HTTP retailers must never be forced to pull a browser stack
- [Phase 02]: Chrome's sandbox stays on by default; BOTY_BROWSER_NO_SANDBOX is opt-in per host and logs a warning — Rung 3 executes attacker-controlled retailer JavaScript, so an isolation downgrade must be something a person chose rather than a silent default
- [Phase 02]: Rung is a separate enum beside Availability, not a fourth availability value — monitor.assess_health and transitioned_to_stock branch on Availability and cli.SYMBOL is indexed unconditionally, so a fourth member is a KeyError mid-report
- [Phase 02]: Result.degraded is derived from rung, never stored — one source of truth, so the support matrix claim and the runtime flag cannot drift apart
- [Phase 02]: Degradation does not feed Health.ok and does not suppress alerts — assess_health answers 'is this detector verified', not 'how confident is the transport'; feeding it in would make phase criterion 4 (five retailers with no health warnings) unreachable by construction
- [Phase 02]: Best Buy is supported credential-free on rung 3 (browser, DEGRADED); an API key upgrades the same watch to rung 2
- [Phase 02]: bestbuy_product_url resolves a SKU via Best Buy search — chosen because its MISS path was verified to carry no Product markup
- [Phase 02]: No Best Buy GO Plus + watch ships: Best Buy does not carry the product; SKU 6577129 disproved and removed from tests
- [Phase 03]: Target is rung 4, settled by its Terms & Conditions — The Unlawful or Prohibited Uses bullet forbidding data-gathering tools and storing prices carries NO commercial-use qualifier, unlike the bullet above it which does
- [Phase 03]: Zero requests were made to any Target product page — 4 curl requests total, all policy documents and robots.txt, so the evidence log states as a fact rather than a policy that bot-y makes no requests to target.com
- [Phase 03]: Target's robots.txt is BROADER than its ToU, the opposite direction to Amazon's — /p/ carries no Disallow and sitemap_pdp-index.xml.gz is published, so a naive reading would have been encouraging; the broader written document still governs
- [Phase 03]: Rung 2 (RedSky) closed four ways — redsky.target.com/robots.txt is Disallow: / for every agent; the key is Target's internal front-end constant not an issuable credential; the terms cover all hosts; and it is CAPTCHA-gated
- [Phase 03]: FIRST_PARTY['target'] stays a guarded guess, neither widened nor deleted — Widening needs a live page the terms forbid fetching; deleting would edit boty/retailers.py in a plan whose finding is that no code change is warranted. An offline test now fails the moment a target watch makes it live
- [Phase 03]: The five-retailer criterion is UNMET at four, and now final — Both Phase 3 candidates refused in writing and Phase 2's fifth-retailer search established no other US retailer stocks the GO Plus +, so there is no honest path to five
- [Phase 03]: Phase 3 criterion 5 recorded UNMET at four retailers, final: both hard-two retailers are rung 4 by written prohibition and nothing was added to config/products.yaml — Amazon and Target each refused in writing with zero product-page requests; there is no sixth US retailer stocking the GO Plus +, and a control-only fifth was declined in Phase 2
- [Phase 03]: REQ-08 measured rather than asserted: duration_seconds is published by every pass, 61.4s manual and 35.0s service-published against a 120s budget at 10 watches / 4 retailers — The only prior figure was hand-timed; a published key means the budget can be read after any pass instead of re-measured, and None distinguishes an untimed pass from a zero-length one
- [Phase 03]: CR-01 durability closed by elapsed time: zero zombie children and zero leaked browser profiles, flat across 41 minutes and 7 completed cycles — 02-VERIFICATION.md left it open because the teardown tests drive a fake nodriver and a one-shot make verify cannot measure a daemon-lifetime property

- [Phase 03.1]: W-02 closed by rule 5 (a configuration cannot outrank a refusal) — Rules 2 and 4 both `continue` on `retailer in configured`, so a tree shipping a detector for a retailer its own log records as REFUSED returned `PASS — phase` exit 0; `make verify` caught it only by accident of Imperva blocking a fixture capture, which is a property of one vendor rather than of any rule
- [Phase 03.1]: Rule 5 stays silent for a configured retailer with no evidence section at all — GameStop and Walmart have never had one, and demanding one would redden the shipped tree with the fastest green being invented records
- [Phase 03.1]: `unread` is a fourth position vocabulary word, pinned to five named cells — Three of four retailers refused their own policy documents on 2026-08-03; writing `permits` for an unread file would be inventing evidence, and `silent` on the robots side actively means permission
- [Phase 03.1]: No escalation to `curl_cffi` after plain `curl` was refused — GameStop's and Best Buy's positions stay `unread` rather than being obtained through the impersonating transport; that is a later plan's decision to take deliberately
- [Phase 03.1]: Nintendo is marked `⚠ disagree` although it ships — Its robots.txt is `Allow: /` with a published store sitemap while § 6 of its Terms of Use bars "any robot … spider, crawler, scraper or other automated means"; REQ-13 states the disagreement rather than resolving it by dropping a working retailer
- [Phase 03.1]: Target reached at rung 1 and NOT registered — its pages carry no price, availability or seller at all, so a control would read UNKNOWN forever and the detector could never detect
- [Phase 03.1]: Rung 3 not walked for Target — it reaches the stock data only by making the browser call redsky.target.com (Disallow:/ for every agent); Dan's reversal settled the Terms of Use, not robots.txt, so the question was escalated rather than answered
- [Phase 03.1]: FIRST_PARTY['target'] stays a guess because it is unverifiable, not unverified — Target's product pages carry no offers.seller.name at any permitted rung
- [Phase 03.1]: Target no longer lists the Pokemon GO Plus + — TCIN 88714054 was HTTP 200 as late as 2025-05 and now 404s; a disproof in the Best Buy shape, found via the Internet Archive CDX index after every general search engine refused us
- [Phase 03.1]: Extraction is a second axis, not a fifth rung — Rung keeps meaning transport, nothing is renumbered, and rung 4 keeps meaning 'dropped, with the evidence written down' — Folding extraction into the ladder would renumber a scale four phases of documents refer to by number, and make the support matrix and rung 4 say something they do not mean
- [Phase 03.1]: Result.degraded widened to fire on a browser transport OR a dom extraction, with a mutation per disjunct — It was derived from the rung alone, so a rung-1 DOM adapter — the most fragile thing this codebase could acquire — would have shipped looking fully trustworthy; M6 dying proves the flag exists, only M7 proves the new half is load-bearing
- [Phase 03.1]: Result.extraction declared LAST with a default of STRUCTURED, and Extraction fed into neither Availability nor Health — Every pre-existing construction site stays valid and keeps its meaning; a fourth Availability member is a KeyError in cli.SYMBOL mid-report, and a dom reading flipping Health.ok would raise a permanent health warning that never clears
- [Phase 03.1]: The README Extraction cell is tied to the Rung cell in BOTH directions — a rung-4 row must say '—' and a working-rung row never may — A '—' accepted unconditionally would be the REQ-13 escape hatch UNREAD_POSITIONS had to be pinned against: paste it into all seven rows and the column distinguishes nothing while looking filled in
- [Phase 03.1]: Target is the fifth retailer: rung 3 + dom extraction, control-only, every reading degraded. Its pages carry NO structured data, so the rendered add-to-cart button is the only stock signal there is.
- [Phase 03.1]: FIRST_PARTY['target'] is now a statement about our own reader's output (parse.TARGET_FIRST_PARTY_SELLER) rather than an unverifiable guess about Target's markup — Target publishes no seller name at any rung.
- [Phase 03.1]: The rung-3 Target fixture leaked this host's geolocation, a session token and nearby-store addresses, and the automated guard PASSED on it. Redacted by emptying every <script> body; the guard was widened and then found the same leak class already committed in 4 walmart/bestbuy fixtures.
- [Phase 03.1]: Criterion 3 recorded MET at SIX, not five — Amazon landed, so the criterion's own upper form applies; the arithmetic is an explanation rather than a confession, and TARGET_RETAILER_COUNT stays at 5 because a threshold of 6 would fire on the honest answer the next time Amazon walls
- [Phase 03.1]: ROADMAP criterion 1 recorded UNMET and deliberately not amended — Target delisted the GO Plus + so no work satisfies it, and Dan declined the rewrite that would have made it meetable; five-of-six with one honest failure is worth more than six-of-six with one quiet edit
- [Phase 03.1]: boty.service was still running pre-phase code and publishing 4 retailers with no extraction key while the tree shipped 6 — restarted before the service-cycle duration was taken, because make verify runs the tree and cannot see the daemon
- [Phase 03.1]: REQ-08 re-measured at six retailers with two browser rungs — 45.98 s manual and 44.81/42.84 s from the service's own cycles, all read off status.json duration_seconds rather than hand-timed, against a 120 s budget; healthy read in the same breath, because a permanently-UNKNOWN retailer satisfies a count while failing the criterion
- [Phase 04]: The contributor docs say THREE of six retailers need no adapter code, not five — _make_checker has arms for bestbuy, amazon and target and falls through to check_html for the rest; the plan's five was never measured
- [Phase 04]: A documentation gate in the shape of test_support_matrix.py — cited paths must exist, no citation may carry a line number (04-03 moves hundreds), and every pinned (file, symbol) pair holds in both directions; each rule watched failing against a corrupted copy of the real file
- [Phase 04]: A SANDBOX_CONTENTS entry lands in the same commit as the file it names, and is proven load-bearing by removal — both 'hooks' and 'CONTRIBUTING.md' were watched producing HARNESS ERROR at the baseline, not asserted to matter
- [Phase 04]: No test in 04-01 stats LICENSE — 04-02 creates it in wave 2, and a stat would make this gate pass or fail on another plan's completion order
- [Phase 04]: The non-repo question decided by giving the mutation sandbox a git index, not by skipping and not by returning an absence — and _tracked_top_level_dirs ALSO raises the named NotATrackedTree in both of git's failure shapes — Stripping the index out then makes make verify die naming the cause instead of going green having checked nothing; watched failing, exit 128, exactly 1 failed test and the 3 identity-check skips back
- [Phase 04]: setuptools does NOT check that a license-files target exists — it builds, emits License-Expression, silently drops License-File and says nothing — The build is not the gate. tests/test_packaging_metadata.py is, and it was watched failing against a real license = Apache-2.0 edit to pyproject.toml, not only against a synthetic copy
- [Phase 04]: MANIFEST.in prunes rather than grafts — eight prune lines, no exclude lines — Shipping tests/fixtures/ would put captured retailer HTML in a public artifact and this repo redacts fixtures by class rather than by value for exactly that reason; measured, the unmanifested sdist carried every tests/test_*.py and none of the fixtures or conftest they need. exclude lines are avoided because one naming a file that never entered warns on every build forever
- [Phase 04]: No Development Status classifier, no Changelog URL and no Typing :: Typed in 04-02 — The first two are claims about a version and a file that do not exist yet and land with 04-05's 1.0.0 bump; the third would advertise a typing contract no installed consumer can act on, since there is no boty/py.typed marker
- [Phase 04]: The sandbox git index costs make verify's mutation stage ~29s and that is accepted, not a defect — Sandbox suite 6.0s -> 9.2s across nine sandboxes, entirely from the un-skipped identity scan — git init plus git add -A are 0.09s. Recorded so 04-04 or a contributor meeting slower CI does not remove the index to get it back

### Blockers

- Some Best Buy product pages (the Best Buy essentials house brand) are reproducibly refused while others render — mechanism unexplained, so 02-03 control selection needs a fallback candidate
- ~~Target: rung 3 is the only remaining route to its stock data, and it reaches that data only by making requests to redsky.target.com, which is Disallow:/ for every agent. Dan's 2026-08-03 reversal settled the Terms of Use, not robots.txt. Two options in QUESTIONS.md 0d; notify-dan sent.~~ **Cleared 2026-08-03.** Dan answered 0d explicitly and took option 2 — render the page, read the add-to-cart control, record it in the open. The ruling was then *measured* rather than left as a forecast: `performance.getEntriesByType('resource')` inside one rendered PDP found **31 hosts**, and **three** Target-owned hosts publish `Disallow: /`, not the one 0d named. The prohibition widened to match — no code here addresses `redsky.target.com`, `api.target.com` or `sapphire-api.target.com` directly.

- **No open blockers.** The only thing still waiting on Dan is `QUESTIONS.md` § 0e (public git history carrying this host's ZIP in four fixtures), which is a decision rather than a blocker — nothing is stopped by it.
