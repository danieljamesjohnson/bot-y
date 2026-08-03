---
gsd_state_version: 1.0
milestone: v1.0.0
milestone_name: milestone
status: In progress
stopped_at: Completed 03.1-01-PLAN.md
last_updated: "2026-08-03T11:18:00.000Z"
last_activity: 2026-08-03
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 19
  completed_plans: 13
  percent: 68
---

# State: bot-y

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-08-02)

**Core value:** A stock reading you can trust — never "out of stock" when the truth is "I couldn't tell", never "in stock" when the truth is "a reseller has one at 4x MSRP."
**Current focus:** Phase 03.1 — Target and Amazon, Supported

## Status

**Milestone:** v1.0
**Phase:** 03.1 of 5 (Target and Amazon, supported) — INSERTED, reverses a Phase 3 decision
**Plan:** 1 of 4 complete
**Last session:** 2026-08-03T11:18:00.000Z
**Stopped At:** Completed 03.1-01-PLAN.md
**Last Activity:** 2026-08-03
**Last Activity Description:** Rule 5 closes W-02; REQ-13 shipped as six machine-checked matrix columns; robots/terms positions recorded for all seven roadmap retailers
**Resume File:** None
**Next command:** `/gsd-execute-phase 03.1` for plan 02 — Target on the robots-clean path. Both gates are now in place: registering Target requires flipping its evidence verdict in the same commit (rule 5) and its matrix row already states `permits /p/` + `forbids extraction` + `⚠ disagree`

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

- ~~**Amazon may be unreachable** without a browser or paid residential proxies.~~ **Settled 2026-08-03 by 03-01, and not for the expected reason.** Reachability was never tested: Amazon's Conditions of Use forbid "any collection and use of any product listings, descriptions, or prices", so it is rung 4 with zero product-page requests ever made. No browser, no proxies, no transport work. Evidence in `docs/retailer-evidence.md` under `## Amazon`.
- ~~**Target is unresolved.**~~ **Settled 2026-08-03 by 03-02, and not for a technical reason.** Target's Terms & Conditions forbid "any use of data extraction, scraping, mining or other data gathering tools" and "otherwise scrape, collect, store or use any Content … product listings, descriptions, prices or images" with no commercial-use qualifier, so it is rung 4 with zero product-page requests ever made. The old RedSky/TCIN notes are superseded: RedSky is closed by `redsky.target.com/robots.txt` (`Disallow: /`, every agent) before the CAPTCHA matters, and TCIN discovery was never attempted even though `www.target.com/robots.txt` publishes a PDP sitemap. Evidence in `docs/retailer-evidence.md` under `## Target`.
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

### Blockers

- Some Best Buy product pages (the Best Buy essentials house brand) are reproducibly refused while others render — mechanism unexplained, so 02-03 control selection needs a fallback candidate
