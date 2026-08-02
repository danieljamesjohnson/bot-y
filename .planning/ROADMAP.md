# Roadmap: bot-y

## Overview

Two retailers work today, both control-verified. The journey to v1 is getting
to ~10 curated retailers without losing the property that makes the project
worth existing: every detector is provably correct, and when one isn't, you
find out. That ordering matters — we build the safety net *before* the
five-fold increase in adapters, because the failure mode we're guarding
against is invisible by construction. Then we make it a project other people
can contribute to.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Detector Safety Net** - Tests, fixtures and types, so 8 more adapters can't silently break each other
- [ ] **Phase 2: Five Retailers Green** - Best Buy, Target, Amazon, Pokémon Center — hits the MVP bar
- [ ] **Phase 3: Ten Retailers Green** - Costco, Sam's Club, Newegg, B&H, Micro Center
- [ ] **Phase 4: Open Source Ready** - Contributor docs, CI, packaging, release

## Phase Details

### Phase 1: Detector Safety Net
**Goal**: A contributor (or I) can add a retailer adapter and be told immediately if it breaks an existing one — offline, without hitting a live site.
**Depends on**: Nothing (first phase)
**Requirements**: REQ-01, REQ-02, REQ-03
**Success Criteria** (what must be TRUE):
  1. Saved HTML fixtures for GameStop and Walmart drive tests that pass without network access
  2. A test proves each of the three availability states, including that an unparseable page yields UNKNOWN and never OUT_OF_STOCK
  3. A test proves a marketplace-seller offer above the price ceiling is not alertable
  4. `mypy` (or equivalent) runs clean over `boty/`
  5. Deliberately corrupting an extractor makes the suite fail, not pass quietly

**Plans**: 3 plans

Plans:
- [ ] 01-01: Fixture capture tooling — save a live page to `tests/fixtures/<retailer>/`, with a note on when and what state it captured
- [ ] 01-02: Extraction tests over fixtures — the three states, seller filtering, price ceiling, and the UNKNOWN guarantee
- [ ] 01-03: Type hints across `boty/`, `mypy` config, and a `make check` entry point

### Phase 2: Five Retailers Green
**Goal**: Five retailers reporting trustworthy stock for the GO Plus +, each with a control product proving its detector is alive.
**Depends on**: Phase 1
**Requirements**: REQ-04, REQ-05, REQ-06
**Success Criteria** (what must be TRUE):
  1. Best Buy reports stock through the official API, given a key
  2. Target, Amazon and Pokémon Center each report stock for a real product
  3. Every retailer has at least one control watch, and `boty check` shows all controls in stock
  4. `boty check` reports five or more retailers with no health warnings
  5. Each new adapter has fixture-backed tests from Phase 1

**Plans**: 4 plans (parallelizable — adapters are independent)

Plans:
- [ ] 02-01: Best Buy — official API adapter, key handling, control product
- [ ] 02-02: Target — resolve the TCIN/URL problem that blocked us (RedSky is CAPTCHA-gated; product pages fetch clean)
- [ ] 02-03: Amazon — likely the hardest; establish whether it is reachable at all before investing
- [ ] 02-04: Pokémon Center — first-party for Pokémon goods, plausibly the most likely restock source

### Phase 3: Ten Retailers Green
**Goal**: Roughly ten curated retailers, each control-verified, covering where a GO Plus + would realistically appear.
**Depends on**: Phase 2
**Requirements**: REQ-07, REQ-08
**Success Criteria** (what must be TRUE):
  1. Costco, Sam's Club, Newegg, B&H and Micro Center report stock for real products
  2. All controls green; `boty check` shows ~10 retailers healthy
  3. Retailers that cannot be reached are documented as such with evidence, not left silently broken
  4. A single `boty check` completes in under 2 minutes at this watch count

**Plans**: 3 plans (parallelizable)

Plans:
- [ ] 03-01: Micro Center + Newegg — Micro Center already works via the generic JSON-LD path; Newegg publishes no Product markup and needs investigation
- [ ] 03-02: Costco + Sam's Club — membership warehouses, likely to need session handling
- [ ] 03-03: B&H — returned 403 on first contact; determine whether a different approach reaches it

### Phase 4: Open Source Ready
**Goal**: Someone who isn't me can install bot-y, add a retailer, and open a PR that I can trust.
**Depends on**: Phase 3
**Requirements**: REQ-09, REQ-10, REQ-11
**Success Criteria** (what must be TRUE):
  1. `docs/adding-a-retailer.md` walks through a real adapter end to end, and states why a control product is mandatory
  2. CI runs the test suite on every PR, offline, against fixtures
  3. `pip install bot-y` works from PyPI
  4. README documents the retailer support matrix with each one's method and status
  5. A tagged v1.0.0 release exists

**Plans**: 3 plans

Plans:
- [ ] 04-01: Contributor docs — adding a retailer, the control-product requirement, the UNKNOWN contract
- [ ] 04-02: GitHub Actions CI — lint, mypy, tests on fixtures, no network
- [ ] 04-03: Packaging and v1.0.0 release

## Out of Roadmap

Deliberately excluded — see PROJECT.md for reasoning:

- Generic "any URL" extraction ladder (changedetection.io owns this)
- Async/concurrent checking (no benefit at this scale)
- Formal plugin API (premature until ~10 adapters reveal the interface)
- Auto add-to-cart / checkout (different product, different ethics)
- Web UI beyond the read-only status page

## Open Questions

- **Amazon** may be unreachable without a browser or paid proxies. Phase 2 should establish that early and cheaply rather than sinking a plan into it. If it's out, say so in the support matrix with evidence.
- **The upstream `curl_cffi` fetcher contribution to changedetection.io** is tracked separately from this roadmap. Their maintainer asked for exactly the proof we now have (issue #1730); worth doing, but it is not bot-y's critical path.
