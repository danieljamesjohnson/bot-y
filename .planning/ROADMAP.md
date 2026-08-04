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
- [x] **Phase 3: The Hard Two** - Target and Amazon, both known to resist; escalate or document honestly (completed 2026-08-03)
- [x] **Phase 3.1: Target and Amazon, Supported** - INSERTED 2026-08-03. Reverses Phase 3's drop-on-terms decision at Dan's direction (completed 2026-08-03)
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

- [x] 03-01-PLAN.md — Amazon: read the Conditions of Use before touching the transport; build the unpaddable-count gate; settle Amazon's rung (wave 1)
- [x] 03-02-PLAN.md — Target: read the Terms first, then walk the ladder politely; register it or record rung 4 with per-rung evidence (wave 2)
- [x] 03-03-PLAN.md — Close the phase: publish and measure the pass duration (REQ-08), complete and gate the support matrix, prove it live under the service's own environment (wave 3)

### Phase 3.1: Target and Amazon, Supported — INSERTED 2026-08-03

**Goal**: Target and Amazon reporting trustworthy stock for the GO Plus +, control-verified, on whatever rung reaches them.
**Depends on**: Phase 3
**Requirements**: REQ-07a (revises REQ-07), REQ-13

**Why this reverses Phase 3.** Phase 3 dropped both retailers on a reading of their
Terms of Use, and recorded criterion 5 as permanently unmet. Dan's decision, 2026-08-03:
support them. His reasoning, recorded because it is the premise the phase rests on —
*"bot-y is a bot for humans. To take the power back from other bots."* The product is
bought out by resellers running exactly this kind of software; a person's own agent
reading the same public product pages, once every five minutes, is the counterweight.

The evidence Phase 3 gathered stays — it is real observation and none of it was wrong.
What changes is the conclusion drawn from it. Phase 3's own Target section already
recorded that the two signals disagree: `www.target.com/robots.txt` does **not** disallow
`/p/`, and Target publishes `sitemap_pdp-index.xml.gz`, a product-detail sitemap that
exists to be crawled. That is the path this phase takes.

**Success Criteria** (what must be TRUE):

  1. Target reports stock for the GO Plus +, with a control watch green. **Recorded UNMET, and deliberately not amended (Dan's call, 2026-08-03).** Target has *delisted* the product — TCIN `88714054` served HTTP 200 as late as 2025-05 and now 404s — so no amount of work can satisfy this. The planner proposed rewriting it to "reports trustworthy stock", which would have been achievable; Dan declined. Editing a success criterion after the fact to make it meetable is the move this project keeps catching in itself, and a criterion that stands unmet with the reason written down is worth more than one quietly moved. Target is still registered as a control-only retailer (the Best Buy shape) at rung 3 + DOM extraction — it ships zero structured data (`isProductDetailServerSideRenderPriceEnabled: false`), so the reading comes from the rendered add-to-cart control and is degraded on both axes
  2. Amazon reports stock for the GO Plus + if it carries it, with a control watch green; or the *technical* outcome is recorded with evidence, having actually been attempted
  3. `boty check` reports **five** or more retailers with no health warnings — six if Amazon lands. Five is the honest ceiling when Amazon is technically unreachable, and criterion 2 explicitly permits that. Do not raise the target to six: a gate that fires on the honest outcome is the Phase 2 rot in the opposite sign. The real number is recorded either way
  4. Every retailer's row in the support matrix states its rung, its robots.txt position and its terms position — a reader can see the disagreement rather than only the verdict
  5. No regression: the four Phase 2 retailers still green, `make verify` exits 0
  6. A single `boty check` still completes in under 2 minutes

**Outcome, recorded 2026-08-03 by 03.1-04 — five of six MET, one UNMET and not amended:**

| # | Verdict | Measurement or reason |
|---|---|---|
| 1 | **UNMET** | Target **delisted** the GO Plus + (TCIN `88714054`, HTTP 200 as late as 2025-05, now 404). Unsatisfiable by any amount of work. The rewrite that would have made it meetable was proposed and **Dan declined it**; the criterion stands as written. Target's *control* watch is green — IN_STOCK at $12.59 |
| 2 | **MET** | Actually attempted, which Phase 3 never did: three `/dp/<ASIN>` requests, three HTTP 200s, zero block-phrase matches. Amazon carries the product, so a real product watch ships beside the control; it reads OUT_OF_STOCK correctly, the sole offer being a used unit at $219 from a reseller |
| 3 | **MET at six** | Amazon landed, so the criterion's own upper form applies. `status.json`: 6 retailers, all `ok: true`, `healthy: true`, **zero** health warnings, 13 watches, 6/6 live controls. `TARGET_RETAILER_COUNT` deliberately left at 5 |
| 4 | **MET** | Seven rows, seven columns — `Extraction` added this phase — machine-checked by `tests/test_support_matrix.py`, both directions |
| 5 | **MET** | Bare `VERIFY: PASS` under the service's `EnvironmentFile`, not `INCOMPLETE`. All four Phase 2 controls IN_STOCK with unchanged extraction sources and seller strings |
| 6 | **MET** | **45.98 s** manual, **44.81 s** service cycle, **42.84 s** next cycle — read off `duration_seconds`, not hand-timed. Budget 120 s |

Full working in `docs/retailer-evidence.md` § *REQ-08* and § *Phase 3.1 closing record*.

**Politeness is now the only constraint, and it is a hard one.** Not as ToU compliance —
as self-interest and basic decency. A blocked IP costs a working monitor, and hammering
someone's origin is how a hobby project becomes a nuisance. 5-minute cadence with jitter,
unchanged. Probing budgets during development stay capped as in Phase 3.

**Plans**: 5 plans, replanned 2026-08-03 after 03.1-02's probe. Every plan runs
in its own wave — the two retailer plans both touch `boty/retailers.py`,
`config/products.yaml` and `tests/test_retailers.py`, so they serialize whatever
the numbers say. **Plan numbers are creation order, waves are execution order**:
03.1-05 was added after 03.1-02 had already run, and runs before its rewrite.

**What the replan responds to.** 03.1-02 probed Target and found it neither
refuses us nor gives us anything: HTTP 200, ~315 KB, no challenge, `"isBot":
false`, and zero structured data of any kind. Stock renders client-side. Dan's
answer is a new extraction axis — his original pre-bot-y script decided stock
from the **Add to Cart button**, and that method is what Target needs. It is
represented as a **second axis, not a new rung**: `Rung` keeps meaning transport,
`Extraction` is `structured` or `dom`, and `Result.degraded` widens to fire on
either a browser transport or a dom extraction. Nothing is renumbered.

Plans:

- [x] 03.1-01-PLAN.md — Both gates before either retailer moves: `evidence_check` rule 5 closes W-02, and REQ-13 becomes machine-checked matrix columns
- [x] 03.1-05-PLAN.md — The Extraction axis (wave 3): `structured` vs `dom`, `degraded` widened to fire on either, M6 re-anchored and M7 proving the new disjunct, and a matrix column with two-directional rules
- [x] 03.1-02-PLAN.md — Target at rung 3 + dom (wave 4), **control-only** because Target delisted the GO Plus +: the robots.txt decision written down first, a DOM add-to-cart reader with its own mutation, a green control, and the verdict revised. *Its first execution (`c79e8ce`) probed Target at rung 1 and escalated rather than registering; that probe is what this rewrite is built on*
- [x] 03.1-03-PLAN.md — Amazon, actually attempted (wave 5): one live `/dp/<ASIN>` read classified against four defined shapes — including the rung-1-plus-dom case Target made real — then registration or a refusal that cites an observation, plus rule 6, which makes REQ-07a mechanical
- [x] 03.1-04-PLAN.md — Close (wave 6): no regression, a measured pass under two minutes with two browser-rung retailers, both axes verified against the live payload, and the real count on the record

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

**Plans**: 6 plans, in 6 waves

Plans:

- [ ] 04-01: Contributor docs — adding a retailer, the control-product requirement, the UNKNOWN contract *(wave 1)*
- [ ] 04-02: The missing `LICENSE`, and packaging metadata that matches it *(wave 2, blocked on 04-01)*
- [ ] 04-03: A linter, from zero — `ruff`, the findings resolved, a `lint` stage inside `make verify` *(wave 3, blocked on 04-01, 04-02)*
- [ ] 04-04: GitHub Actions CI — one job per PR running `make verify-offline`, and a test that reads the workflow *(wave 4, blocked on 04-03)*
- [ ] 04-05: Release engineering, all of it local — 1.0.0, CHANGELOG, Trusted Publishing workflow, artifacts proven by a clean-venv wheel install *(wave 5, blocked on 04-02, 04-03, 04-04)*
- [ ] 04-06: Maintainer handoff — the PyPI Trusted Publisher, the `v1.0.0` tag push, and the five verdicts *(wave 6, blocked on 04-05, `autonomous: false`)*

### Why six plans, not the three sketched above

The original three were written before two facts were established first-hand
during planning, and neither is optional:

- **There is no `LICENSE` file.** The repo is public and `pyproject.toml`
  declares MIT, but `git ls-files` matches nothing and GitHub's API reports
  `license: None`. A public 1.0.0 asserting a licence with no licence text
  arguably grants no rights at all. → 04-02.
- **There is no linter at all** — no ruff, flake8, black or pylint anywhere —
  while REQ-10 names lint in its own wording. → 04-03.

The sixth plan exists because the phase's two maintainer-gated criteria
(3 and 5) must not share a plan with autonomous implementation work. Splitting
them is what lets waves 1–5 run to completion without waiting on Dan.

**Cross-cutting constraints:** every wave is serialised on file ownership —
`scripts/mutation_check.py` (04-01…04-04), `pyproject.toml` (04-02, 04-03,
04-05), `README.md` (04-01, 04-03, 04-05) and `MANIFEST.in` (04-02, 04-04,
04-05) are each contested across waves, never within one. Nothing in this
phase may weaken `make verify`, and every gate it adds is watched failing
before it is trusted.

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
