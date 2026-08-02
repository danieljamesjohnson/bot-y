---
gsd_state_version: 1.0
milestone: v1.0.0
milestone_name: milestone
status: unknown
stopped_at: Completed 01-01-PLAN.md
last_updated: "2026-08-02T16:53:03.362Z"
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 4
  completed_plans: 1
  percent: 0
---

# State: bot-y

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-08-02)

**Core value:** A stock reading you can trust — never "out of stock" when the truth is "I couldn't tell", never "in stock" when the truth is "a reseller has one at 4x MSRP."
**Current focus:** Phase 01 — Detector Safety Net

## Status

**Milestone:** v1.0
**Phase:** 1 of 4 — in progress
**Plan:** 2 of 4 in current phase
**Last session:** 2026-08-02T16:53:03.303Z
**Stopped At:** Completed 01-01-PLAN.md
**Resume File:** None
**Next command:** `/gsd-execute-phase 1` — running autonomously through Phase 3, halting before Phase 4 (PyPI publish and v1.0.0 tag are outward-facing and Dan's to trigger)

## What Exists

Working and deployed on danserver before this roadmap was written:

- `boty/` — 854 lines: models, fetch, parse, retailers, monitor, notify, status, config, cli
- GameStop (schema.org JSON-LD) and Walmart (`__NEXT_DATA__`, seller-aware) adapters, both control-verified
- `boty.service` + `boty-web.service`, both active and enabled at boot
- Status page on loopback :8821, reachable at `/tools/boty` through Mission Control
- Telegram notifications, delivery confirmed end to end
- Repo public at https://github.com/danieljamesjohnson/bot-y (Apache-compatible MIT)

## Blocked

- **Best Buy API key** — needed for REQ-04. Free from developer.bestbuy.com. Adapter written and waiting. `boty-secret bestbuy` sets it. See `QUESTIONS.md`.

## Known Risks

- **Amazon may be unreachable** without a browser or paid residential proxies. Phase 2 should establish this cheaply and early rather than sinking a plan into it.
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

## Decisions

- [Phase 01]: FIXTURE_ROOT anchors to the repo root, not cwd — A cwd-relative fixture path makes load() succeed or fail depending on where the test runner was invoked from — flakiness that fixtures exist to remove
- [Phase 01]: A blocked or failed fetch writes no fixture at all — A CAPTCHA interstitial saved under a product name would make the whole suite assert against a bot wall while looking green
- [Phase 01]: Walmart GO Plus + reseller fixture is real, not synthetic — The live buy box is still held by Clove Brothers LLC at $229.99, so the plan's synthetic-fixture contingency was not needed
