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

- [x] **Phase 1: Detector Safety Net** - Tests, fixtures and types, so new adapters can't silently break each other (completed 2026-08-02)
- [x] **Phase 2: Five Retailers Green** - Best Buy, Pokémon Center, Nintendo — the tractable ones; hits the MVP bar (completed 2026-08-03)
- [ ] **Phase 3: The Hard Two** - Target and Amazon, both known to resist; escalate or document honestly
- [ ] **Phase 4: Open Source Ready** - Contributor docs, CI, packaging, release

## Retailer Scope

Deliberately narrowed from a padded list of ten. Newegg, B&H and Micro Center
are PC-parts retailers that do not carry Pokémon accessories; Costco and Sam's
Club are unlikely to stock a $55 peripheral. Watching stores that will never
list the product manufactures fake breadth and real maintenance.

Target list — places a GO Plus + could genuinely appear:

| Retailer | Status |
|---|---|
| GameStop | ✅ done, control-verified |
| Walmart | ✅ done, control-verified |
| Best Buy | Phase 2 — rung 3 (browser, DEGRADED); official API optional if you have a key |
| Pokémon Center | Phase 2 |
| Nintendo store | Phase 2 |
| Target | Phase 3 — RedSky CAPTCHA-gated |
| Amazon | Phase 3 — expected hostile |

## Escalation Ladder

When a retailer resists, work down this ladder and stop at the first rung that
works. Record which rung each retailer landed on in the support matrix.

1. **TLS impersonation** (`curl_cffi`) — the default
2. **Official / structured API** — but ONLY if a fresh clone can obtain the
   credential. Best Buy's API requires manual approval and a non-free email
   domain, so it fails this test and cannot be a primary path; it stays
   available as an optional enhancement for those who have a key

3. **Browser (`nodriver`), marked DEGRADED** — allowed, but that retailer is
   flagged lower-confidence, because it depends on the fragile path we
   deliberately moved away from

4. **Drop, with evidence** — documented as unreachable in the support matrix,
   including what was tried. Never left silently broken.

## Phase Details

### Phase 1: Detector Safety Net

**Goal**: A contributor (or I) can add a retailer adapter and be told immediately if it breaks an existing one — offline, without hitting a live site.
**Depends on**: Nothing (first phase)
**Requirements**: REQ-01, REQ-02, REQ-03, REQ-12
**Success Criteria** (what must be TRUE):

  1. Saved HTML fixtures for GameStop and Walmart drive tests that pass without network access
  2. A test proves each of the three availability states, including that an unparseable page yields UNKNOWN and never OUT_OF_STOCK
  3. A test proves a marketplace-seller offer above the price ceiling is not alertable
  4. `mypy` (or equivalent) runs clean over `boty/`
  5. Deliberately corrupting an extractor makes the suite fail, not pass quietly
  6. `make verify` exits 0 on a healthy tree and non-zero if ANY check fails — tests, types, live control products, and the mutation check

**Plans**: 4 plans

Plans:

- [x] 01-01: Fixture capture tooling — save a live page to `tests/fixtures/<retailer>/`, with a note on when and what state it captured
- [x] 01-02: Extraction tests over fixtures — the three states, seller filtering, price ceiling, and the UNKNOWN guarantee
- [x] 01-03: Type hints across `boty/` and `mypy` config
- [x] 01-04: `make verify` — one command, one exit code, covering offline tests + mypy + live control health + the mutation check

### Why `make verify` exists

GSD's verifier is an LLM forming a judgement, and a judgement can be
confidently wrong in the same direction as the code that produced it. The fix
is not a better prompt — it is success criteria that are *executable*, so the
verifier reads an exit code instead of forming an impression.

Every phase from here is verified as "`make verify` passes, plus these
specific observable facts." It also outlives the agents: Dan can run it
himself in six months and get a real answer.

### Phase 2: Five Retailers Green

**Goal**: Every retailer we can actually reach reporting trustworthy stock for the GO Plus +, each control-verified.
**Depends on**: Phase 1
**Requirements**: REQ-04, REQ-05, REQ-06
**Success Criteria** (what must be TRUE):

  1. Best Buy reports stock with NO credentials configured, flagged DEGRADED; and reports stock without the DEGRADED flag when an API key IS present
  2. The Nintendo store reports stock for a real product; Pokémon Center does the same or is documented as unreachable with the evidence
  3. Every retailer has at least one control watch, and `boty check` shows all controls in stock
  4. Each new adapter has fixture-backed tests from Phase 1
  5. The support matrix records which escalation rung each retailer landed on
  6. `make verify` exits 0

**The five-retailer count moved to Phase 3** (2026-08-02, Dan's call). It was written here
as the MVP bar on the assumption that a fifth reachable retailer existed. It does not: the
US retail set for this device is GameStop, Walmart, Nintendo, Pokémon Center, Target and
Amazon. Phase 2 settled four of them — Pokémon Center is rung 4 with four recorded
refusals — and the remaining two are Phase 3's by this roadmap's own scope.

A control-only fifth (Micro Center was probed and is viable, rung 1, config-only) would
have moved the counter without moving the goal, since it does not carry the GO Plus + and
could never alert on it. Adding it was declined for that reason. Target or Amazon landing
in Phase 3 makes five honestly. Evidence for every candidate probed is in
`docs/retailer-evidence.md`.

**Plans**: 4 plans, in 3 waves

Adapters are not as parallelizable as they look: all three touch `boty/retailers.py`,
`config/products.yaml` and `tests/test_retailers.py`, so they serialize. DEGRADED is
shared infrastructure rather than Best Buy-local, and the browser rung is unvalidated
(`nodriver` has no precedent here), so both are front-loaded into wave 1.

Plans:

- [x] 02-01-PLAN.md — Rung-3 browser transport, an offline guard that covers it, and a live spike answering whether Best Buy is reachable at all (wave 1)
- [x] 02-02-PLAN.md — The Rung/DEGRADED reading-method field on Result, surfaced in `status.json` and `boty check`, plus the IN-03 compound-`@type` fix (wave 1)
- [x] 02-03-PLAN.md — Best Buy: browser adapter flagged DEGRADED, optional API path when `BESTBUY_API_KEY` is set, control product, support-matrix row (wave 2)
- [x] 02-04-PLAN.md — Pokémon Center and Nintendo, their controls, and the five-retailers-green end-to-end proof (wave 3)

### Phase 3: The Hard Two

**Goal**: Target and Amazon either working, or documented as unreachable with the evidence that established it. No silent gaps.
**Depends on**: Phase 2
**Requirements**: REQ-07, REQ-08
**Success Criteria** (what must be TRUE):

  1. Target reports stock, or the support matrix records what was tried and why it failed
  2. Amazon reports stock, or the same
  3. Any retailer reached via rung 3 is flagged DEGRADED in the matrix and in `boty check` output
  4. All controls still green; no regression in the four from Phase 2
  5. `boty check` reports five or more retailers with no health warnings — carried over from Phase 2, which reached four because no fifth reachable retailer stocks the GO Plus +. Target or Amazon landing satisfies it. If both are rung 4, this criterion is unmet and recorded as such, never padded with a retailer that does not carry the product
  6. A single `boty check` completes in under 2 minutes
  7. `make verify` exits 0

**Plans**: 3 plans, in 3 waves

**Not parallelizable, and the ordering is deliberate.** Both retailer plans touch
`boty/retailers.py`, `config/products.yaml` and `tests/test_retailers.py` on the branch
where their retailer lands, so they serialize whatever the wave numbers say — the same
lesson Phase 2 learned. Amazon goes first because it is the cheap one: its Conditions of
Use are expected to settle it before any transport work, which is this section's own
instruction ("establish reachability cheaply *before* investing in an adapter"), and its
outcome tells the Target plan whether criterion 5 rests on Target alone.

The likely honest outcome is both refused, both documented, criterion 5 unmet. Every plan
is written so that verifies as complete rather than as a failure.

Plans:

- [ ] 03-01-PLAN.md — Amazon: read the Conditions of Use before touching the transport; build the unpaddable-count gate; settle Amazon's rung (wave 1)
- [ ] 03-02-PLAN.md — Target: read the Terms first, then walk the ladder politely; register it or record rung 4 with per-rung evidence (wave 2)
- [ ] 03-03-PLAN.md — Close the phase: publish and measure the pass duration (REQ-08), complete and gate the support matrix, prove it live under the service's own environment (wave 3)

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
