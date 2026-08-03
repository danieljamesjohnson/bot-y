---
gsd_state_version: 1.0
milestone: v1.0.0
milestone_name: milestone
status: Ready to execute
stopped_at: Completed 03-01-PLAN.md
last_updated: "2026-08-03T04:05:11.794Z"
last_activity: 2026-08-03
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 11
  completed_plans: 9
  percent: 50
---

# State: bot-y

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-08-02)

**Core value:** A stock reading you can trust — never "out of stock" when the truth is "I couldn't tell", never "in stock" when the truth is "a reseller has one at 4x MSRP."
**Current focus:** Phase 03 — The Hard Two

## Status

**Milestone:** v1.0
**Phase:** 3 of 4 (the hard two)
**Plan:** 2 of 3
**Last session:** 2026-08-03T04:05:11.790Z
**Stopped At:** Completed 03-01-PLAN.md
**Last Activity:** 2026-08-03
**Last Activity Description:** 03-01 complete — Amazon is rung 4 by its Conditions of Use (zero product-page requests), and `scripts/evidence_check.py` replaces Phase 2's vacuous count clause
**Resume File:** None
**Next command:** `/gsd-execute-phase 3` — 03-02 (Target) is next and now carries the whole weight of phase criterion 5. Still halting before Phase 4 (PyPI publish and v1.0.0 tag are outward-facing and Dan's to trigger)

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
- **Target is unresolved.** RedSky is CAPTCHA-gated even with a warmed cookie session; product pages fetch clean but we could not find a valid `www` TCIN. Stopped at three strikes.
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

### Blockers

- Some Best Buy product pages (the Best Buy essentials house brand) are reproducibly refused while others render — mechanism unexplained, so 02-03 control selection needs a fallback candidate
