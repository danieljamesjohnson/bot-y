# State: bot-y

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-08-02)

**Core value:** A stock reading you can trust — never "out of stock" when the truth is "I couldn't tell", never "in stock" when the truth is "a reseller has one at 4x MSRP."
**Current focus:** Phase 1 — Detector Safety Net (autonomous run, phases 1–3)

## Status

**Milestone:** v1.0
**Phase:** 1 of 4 — not started
**Next command:** `/gsd-plan-phase 1` — running autonomously through Phase 3, halting before Phase 4 (PyPI publish and v1.0.0 tag are outward-facing and Dan's to trigger)

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
