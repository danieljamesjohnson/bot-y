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

Phases 1–4 and 3.1 belong to **v1.0.0** — their checklist and details are together
under *Milestone v1.0.0 — Phase Details* below. v1.0.0 remains open and untagged.

- ✅ **Milestone v0.2 — Say Only What You Measured** (scoped 2026-08-10, closed 2026-08-11) — Phases 5–6, 11 plans, complete **in the tree**; **not deployed, not tagged, not published**. Archived in full: [`milestones/v0.2-ROADMAP.md`](milestones/v0.2-ROADMAP.md) · [`milestones/v0.2-REQUIREMENTS.md`](milestones/v0.2-REQUIREMENTS.md) · [`milestones/v0.2-MILESTONE-AUDIT.md`](milestones/v0.2-MILESTONE-AUDIT.md)

### Milestone v0.3 — Say When You Measured It (scoped 2026-08-13)

- [ ] **Phase 7: A Reading Has an Age** - Stamp it, publish it, and show a stale reading as stale rather than as fact

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

## Milestone v1.0.0 — Phase Details

Open and untagged. Its definition of done includes *"Dan has successfully bought a
Pokémon GO Plus +"* — a market condition, not a work item — so the milestone audit
recommended against tagging it shipped. All five phases below are complete.

- [x] **Phase 1: Detector Safety Net** - Tests, fixtures and types, so new adapters can't silently break each other (completed 2026-08-02)
- [x] **Phase 2: Five Retailers Green** - Best Buy, Pokémon Center, Nintendo — the tractable ones; hits the MVP bar (completed 2026-08-03)
- [x] **Phase 3: The Hard Two** - Target and Amazon, both known to resist; escalate or document honestly (completed 2026-08-03)
- [x] **Phase 3.1: Target and Amazon, Supported** - INSERTED 2026-08-03. Reverses Phase 3's drop-on-terms decision at Dan's direction (completed 2026-08-03)
- [x] **Phase 4: Open Source Ready** - Contributor docs, CI, packaging, release (completed 2026-08-06)

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
  3. ~~`pip install bot-y` works from PyPI~~ — **DESCOPED from v1.0 on 2026-08-07**
  4. README documents the retailer support matrix with each one's method and status
  5. ~~A tagged v1.0.0 release exists~~ — **DESCOPED from v1.0 on 2026-08-07**

**Criteria 3 and 5 were descoped, not met and not quietly reworded.** Dan's decision,
2026-08-07: *"Let's kill those 2 since I wouldn't publish it without more real testing."*
Both were downstream of the same act — publishing — which he deferred on 2026-08-06 with
*"i don't think we need to host it yet. it's probably not quite ready for that."*

They are struck through rather than deleted because **v1.0 did promise a PyPI release and
that promise was withdrawn**, and a reader who cannot see that the promise was made cannot
judge the milestone. This is a scope revision — the criterion was wrong for v1.0 — and is
a different act from the one Phase 3.1 declined, which was rewording a criterion so that
work already done would satisfy it. Nothing here is reworded to pass.

**Nothing technical blocks them.** `make release-check` → 10/10: both artefacts built in a
clean venv, `twine check` PASSED on each, the wheel installed into a venv holding nothing
else, console script run from outside the checkout. The verifier re-ran that independently
rather than trusting the summary. `04-06-HANDOFF.md` stays on disk and still matches the
tree. Publishing later needs no replanning — it needs the real testing Dan named.

REQ-11 moves with them: it is **descoped from v1.0**, not complete.

**Outcome, recorded 2026-08-06 by 04-06 — three of five MET, two UNMET; the two unmet were
subsequently descoped (above) rather than closed. The original verdicts stand unedited:**

| # | Verdict | Measurement or reason |
|---|---|---|
| 1 | **MET** | `pytest tests/test_contributor_docs.py -q` → **19 passed**. `docs/adding-a-retailer.md`, 355 lines, walks **Nintendo** end to end in four numbered steps — probe and write the evidence (8 requests, 12–20 s apart, the 404-at-217,381 B and the product page at 416,346 B), one `FIRST_PARTY` line, the `MARKETPLACES` membership decision, then two YAML watches one of which is a control. The mandate is its own section: `## Why a control product is mandatory`, with `### The rule a control has to satisfy` and `### The rule biting, on a real candidate that was rejected` |
| 2 | **MET — one half observed, one half still asserted, and the difference is written down** | Shipped `on:` block, read back from `.github/workflows/ci.yml`: `pull_request:` with no branch or path filter, plus `push: branches: [main]`. `pytest tests/test_ci_workflow.py -q` → **67 passed**. **Observed on a real runner:** run [`31066215395`](https://github.com/danieljamesjohnson/bot-y/actions/runs/31066215395) — the first live CI run this repository has ever had — event `push`, branch `main`, sha `76d4156`, one job `verify`, conclusion **success**, 02:39:05Z→02:42:22Z (3m21s incl. queue). Its log carries `identity check: PASS — 153 file(s), no host identity found`, `531 passed in 16.54s`, `mutation check: 8/8 mutations caught`, and ends `VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)`. **NOT observed:** the `pull_request` trigger. `gh run list --workflow ci.yml` returns exactly one run — that push. The optional throwaway PR (handoff step 5) was not taken, so the PR trigger remains asserted by `tests/test_ci_workflow.py` and unwitnessed in production |
| 3 | **UNMET** | Dan deferred, 2026-08-06, verbatim: *"i don't think we need to host it yet. it's probably not quite ready for that"*. Re-measured here rather than assumed from Task 1: `https://pypi.org/pypi/bot-y/json` → **HTTP 404** and `https://pypi.org/pypi/bot-y/1.0.0/json` → **HTTP 404**. No trusted publisher was configured, no install was run and no network write was attempted. The criterion is **not amended** |
| 4 | **MET — preserved, not achieved** | It was verified cell-by-cell against live `boty check` output by 03.1-04 *before this phase opened*; Phase 4's job was to not break it, and the measurement is that nothing moved. `pytest tests/test_support_matrix.py -q` → **31 passed**. Across the whole phase — base `b0a272f` re-derived, 44 commits — `git diff -U0 b0a272f..HEAD -- README.md` contains **zero** lines matching `^[-+]\| (GameStop\|Walmart\|Nintendo\|Best Buy\|Pokémon Center\|Amazon\|Target\|Retailer) `. The only README table lines the phase touches at all are the two `\| Stage \| Proves \|` rows 04-03 adds on purpose (`identity`, `lint`) — expected, required by 04-03's own acceptance criterion, and not a support-matrix row. `grep -c '^\| Retailer \| Rung \| Extraction \|' README.md` = **1**, so no second seven-column table exists to hijack the locator `tests/test_support_matrix.py` finds the table by |
| 5 | **UNMET** | No tag exists, anywhere. `git tag -l` → empty (0 tags local); `git ls-remote --tags origin` → **0 refs**, so none on the remote either. No agent created one — this plan ran no `git tag`, no `git push`, no upload. `gh run list --workflow release.yml` → no runs; the publish workflow has never fired, because only a `v*` tag push starts it. Dan's reason is criterion 3's, same date. The criterion is **not amended** |

**What was and was not done, because provenance matters here.** Step 1 of the handoff card
*was* carried out — `git push -u origin main`, `b0a272f..76d4156`, upstream configured on `main`
for the first time — but it was run by **the orchestrator agent, not by Dan**, after he answered
"Sure go for it" to the checkpoint. Steps 2, 3 and 4 (the PyPI trusted publisher, the tag, the
publish) were not done at all. A free consequence of that push, worth recording because it is
GitHub's own detector agreeing with 04-02: `api.github.com/repos/danieljamesjohnson/bot-y` now
reports `license: {"key": "mit", "spdx_id": "MIT"}`, where it read `null` before this phase.

**Neither unmet criterion was reworded, shortened or merged**, and that is deliberate. Phase 3.1
was offered a rewrite of its criterion 1 that would have made it meetable and Dan declined it;
this plan does not get to do what that one refused. Criteria 3 and 5 stand as written, unmet,
with the reason and the date. `.planning/phases/04-open-source-ready/04-06-HANDOFF.md` stays on
disk, unaltered and still accurate, so publishing later needs no replanning.

**The phase gate, run once, live, at close:** `make verify` → **`VERIFY: FAIL (live controls)`**,
exit 2. Recorded verbatim rather than trimmed or re-run until green. Two distinct classes, and
`control_check.py` separates them itself: `2/6 control(s) could not run on THIS HOST` — Best Buy
and Target, both rung 3, `no Chrome/Chromium binary found` (nodriver 0.50.3 is installed here but
no browser is), which the tool states "says nothing about the DETECTOR"; and `2/6 control(s) not
reading IN_STOCK` — Walmart and Amazon, both `blocked: challenge page` at HTTP 200, which *is* a
statement about the detector. None of this touches Phase 4's five criteria, and none of it was
caused by this phase — no plan in Phase 4 changed a retailer, an extractor or a control. It is
recorded here because a closing record that omitted it would be the omission this project keeps
catching in itself. Detail in `.planning/phases/04-open-source-ready/deferred-items.md`.

**Plans**: 6 plans, in 6 waves

Plans:

- [x] 04-01: Contributor docs — adding a retailer, the control-product requirement, the UNKNOWN contract *(wave 1)*
- [x] 04-02: The missing `LICENSE`, and packaging metadata that matches it *(wave 2, blocked on 04-01)*
- [x] 04-03: A linter, from zero — `ruff`, the findings resolved, a `lint` stage inside `make verify` *(wave 3, blocked on 04-01, 04-02)*
- [x] 04-04: GitHub Actions CI — one job per PR running `make verify-offline`, and a test that reads the workflow *(wave 4, blocked on 04-03)*
- [x] 04-05: Release engineering, all of it local — 1.0.0, CHANGELOG, Trusted Publishing workflow, artifacts proven by a clean-venv wheel install *(wave 5, blocked on 04-02, 04-03, 04-04)*
- [x] 04-06: Maintainer handoff — the PyPI Trusted Publisher, the `v1.0.0` tag push, and the five verdicts *(wave 6, blocked on 04-05, `autonomous: false`)* — **closed on a deferred publish**: the card was written and presented, Dan deferred, criteria 3 and 5 stand UNMET and unamended

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

---

## Milestone v0.3 — Say When You Measured It (Phase Details)

**Scoped 2026-08-13, from a question the system could not answer.** Dan asked of the
Amazon and Walmart GO Plus + watches: *"so they are out of stock as of when?"* — and
there was no recorded answer. Not hard to find; **absent**.

v0.2 was *say only what you measured*. This is its unfinished half: **a reading with
no age is a claim about the past presented as the present.** Same shape as *"the
detector is probably broken"*, except the unestablished thing is *when*.

It has teeth rather than being tidiness. A retailer that refuses us backs off to
multi-hour intervals, so **the rows least likely to be current are exactly the ones
that look identical to the fresh ones.** Detail and the reconstruction in
`.planning/seeds/a-reading-does-not-carry-its-age.md`.

### Phase 7: A Reading Has an Age

**Goal**: Every reading says when it was taken, and a reading too old to trust is shown as stale rather than as fact — or says it does not know.
**Depends on**: Phase 6
**Requirements**: REQ-21
**Success Criteria** (what must be TRUE):

  1. Every `Result` records when it was read, and that time is published per watch in `status.json`
  2. A reading with no recorded time is shown as UNKNOWN age, never as current — watched going red
  3. A reading older than its retailer's current interval is presented as stale in `status.json`, `boty check` and the dashboard, and the staleness is derived from the retailer's own pacing rather than a fixed clock
  4. The age survives a service restart, so a restart cannot make a two-day-old reading look fresh
  5. `make verify-offline` exits 0, and every gate this phase adds has been watched going red

**Why the interval and not a fixed clock.** A retailer in backoff is *legitimately*
checked less often — Walmart at seven refusals is on a multi-hour interval and that
is the politeness rule working. What is dishonest is not the age; it is presenting
an age nobody recorded. So "stale" means *older than this retailer's own current
cadence*, which is a fact the `Pacer` already holds.

**The measurement that opened it**, reconstructed from refusal history because
nothing recorded it directly: Amazon's `out_of_stock` was from early 2026-08-13
(before ~06:37 — a refusal streak began then and the counter had reset, which only
happens on a successful read). **Walmart's could not be established at all**: no
later than 2026-08-12 16:49, plausibly 2026-08-11. A service restart at 16:49:57
zeroed the refusal counter and destroyed the evidence that would have settled it.

**Follow the `store` field's path.** It is the worked precedent four times over —
`rung`, `extraction`, the widened `degraded`, and `store` — and the groove is:
declare the field last with a default, write down what it is deliberately NOT folded
into, thread it through every `check_*` return including the error arms, publish it
in `status.write`, render it in `cli._report` and the dashboard, pin it with a
mutation anchored on behaviour rather than prose.

**Not to be confused with two things that already exist.** `status.json`'s
top-level `updated` is when the *cycle* ran — it is fresh even when every row in it
is stale. And `make verify`'s `fixtures` stage ages *captured test pages*, not live
readings.

**Plans**: 6 plans, in 6 waves — every wave serial, and for the plainest reason this
project has had: **no two plans own disjoint file sets.** The table is in
`.planning/phases/07-a-reading-has-an-age/07-PLAN-OUTLINE.md` § *Why every wave is serial*,
which is this phase's contract. Plans are written one at a time; a line below whose
`PLAN.md` does not exist yet is a plan scheduled, not a plan claimed.

Plans:

- [x] 07-01: A reading carries the moment it was taken, and a non-reading carries none — `Result.read_at`, all 20 construction sites, published as `null` never `0` *(wave 1)*
- [x] 07-02: The age survives the restart, and the file that survives it changes shape without breaking on Dan's disk *(wave 2, blocked on 07-01)*
- [x] 07-03: The retailer's current interval becomes one readable number, and both surfaces read the same one *(wave 3, blocked on 07-02)*
- [x] 07-04: Every configured watch has a row, and a remembered reading says it is remembered — 3 rows for 14 watches today *(wave 4, blocked on 07-03)*
- [x] 07-05: The three surfaces say the age out loud, and an absent one says UNKNOWN *(wave 5, blocked on 07-04)*
- [ ] 07-06: Close — no code; the gates measured, the count observed rising from 26, five verdicts *(wave 6, blocked on 07-01 … 07-05, `autonomous: false`)*

**Criteria 2 and 3 each span more than one plan, and that is structure rather than
dilution.** Criterion 2 splits across 07-01 (the datum: an absent stamp is `None`, never
`now`) and 07-05 (the rendering: it shows as UNKNOWN). Criterion 3 splits across 07-03
(the interval), 07-04 (a row that can be old) and 07-05 (the three renderings) — because
a paced-out watch does not have a *stale* row in `status.json` today; **it has no row at
all**, measured at 3 rows for 14 configured watches, so a staleness rule applied only to
the rows that exist would be a bound that cannot bind.
