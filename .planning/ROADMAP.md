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

- [x] **Phase 7: A Reading Has an Age** - Stamp it, publish it, and show a stale reading as stale rather than as fact (completed 2026-08-17 — three of five MET as written, criteria 3 and 5 MET IN PART, no criterion text amended)

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

**Outcome, recorded 2026-08-17 by 07-06 — three of five MET as written; criteria 3 and 5 MET IN
PART, each with the half that is met and the half that is not named separately. No criterion text
anywhere in this document was reworded, shortened, merged or amended, and that is asserted by
command rather than left to the eye.** The two partial rows are the two this phase had the most
pressure to round up, and the reasons are recorded rather than absorbed: criterion 3's `status.json`
third landed as three raw facts plus a join test rather than as a staleness verdict in the file, and
criterion 5's *"every gate"* is broader than *"every mutation"* — one gate this phase adds was never
observed failing, by construction, and is named below. **And as in Phases 5 and 6, none of this is
confirmed on the deployed daemon:** `boty watch` `MainPID=547119`, `ActiveEnterTimestamp=Wed
2026-08-12 17:28:29 CDT`, re-measured 2026-08-17 and unchanged — it predates 07-01 by ~15 hours and
the file it writes every cycle carries none of this phase's four keys. Full working in
`docs/retailer-evidence.md` § *Phase 7 closing record*.

**Post-review addendum, recorded 2026-08-18 by 07-07 — five figures in the table below are
superseded, and they are recorded here rather than edited.** A code review ran after the
phase closed and found one Critical and eight Warnings; all nine were fixed (nine `fix(07):`
commits, each carrying a `Watched going red:` count except `bc23a02`, a docstring rewrite
that adds no gate), and 07-07 then made the dashboard parse gate execute inside
`make verify-offline` for the first time. Re-measured 2026-08-18 at HEAD `85b337d`:

| Figure below | Claimed (2026-08-17, pre-review) | Measured 2026-08-18 |
|---|---|---|
| `Result(` construction sites | `all 20` | **21** (WR-07 added an arm) |
| read / non-read partition | `11 / 9` | **12 / 9** |
| offline suite | `865 passed` | **884 passed, 0 skipped** |
| mutation ratio | `33/33` | **34/34**, survivors 0 (M38 registered by the WR-01 fix) |
| identity check | `220 file(s)` | **224 file(s)** |

**No verdict changes.** Criterion 3 stays MET IN PART — `status.json` still publishes the
ingredients of a staleness verdict and no verdict, by Dan's explicit decision rather than by
oversight. Criterion 5 stays MET IN PART: its `every gate` half has **three** named reasons
and 07-07 closes the **third** only (a gate that skipped in the environment the project's own
gate runs in); the join test never observed failing and CR-01's gate that could not bite both
**stand**. Closing one of three reasons is not closing the criterion. No criterion text below
was reworded, shortened, merged or amended, and the `Plans:` list is left as written. The
mutation registry is untouched at `M1`-`M20` ∪ `M25`-`M38`, with **M39 still free**. Full
working, including why a superseded measurement is recorded beside while a description of
evidence that never existed is corrected in place, in `docs/retailer-evidence.md` §
*Phase 7 post-review addendum*.

**Non-vacuity measurement, recorded 2026-08-19 — criterion 5's verdict MOVES, and this is the
paragraph a reader meets before the row that carries the superseded one.** The 2026-08-17 and
2026-08-18 texts above are left exactly as written; nothing in them was edited. On 2026-08-19 Dan
chose to establish the join test's non-vacuity **by measurement rather than by the override
`07-VERIFICATION.md` had drafted**, and the measurement was taken: 07-05's
`test_status_json_carries_everything_a_consumer_needs_to_judge_staleness` was watched going red on
**five** separate breaks of the behaviour it joins, in a throw-away worktree at HEAD `bc31030`,
each applied alone against a baseline of 884 passed and each reverted to an empty
`git status --porcelain` — 3 failed / 881 passed (the cadence the join fetches, `EXIT=1`), 3 failed
/ 881 passed (the age), 4 failed / 880 passed (the provenance), and 2 failed / 882 passed twice for
the two forms of publishing the `stale` key the design refuses. **Criterion 5 moves from MET IN
PART to MET, qualified.** The qualification is not optional and is repeated in the row itself:
**this red was watched on 2026-08-19, after the fact, against an implementation that already
existed. The original RED was never observed and TDD ordering was NOT followed for this test.**
*The gate bites* and *the gate came first* are two different claims and **only the first is
established.** Criterion 3 is untouched and stays MET IN PART by Dan's explicit earlier decision;
no key was added to `status.json` and the tree ends the measurement byte-identical to `bc31030`.
The registry is untouched at `M1`-`M20` ∪ `M25`-`M38`, **`M39` still free** and deliberately not
spent on this. Full working, including the one unflattering finding — the test never goes red
*alone*, because every fact it joins carries its own gate — in `docs/retailer-evidence.md`
§ *Phase 7 non-vacuity measurement*.

| # | Verdict | Measurement or reason |
|---|---|---|
| 1 | **MET in the tree — NOT ON THE WIRE** | `Result.read_at` is stated at **all 20** `Result(` construction sites in `boty/retailers.py` — not inherited from a default — and completeness is proved by a **static AST gate over the source** (`20/20 sites name read_at`) rather than by covering arms one at a time, so an arm added later cannot silently omit it. The read/non-read partition is **11 / 9**, and the two Best Buy arms the naive rule gets wrong (`bad api json`, `sku not found`) are stamped **as reads**, because Best Buy answered. An arm that read nothing carries **`null`, never `0`** — epoch 1970 renders as maximally stale, which is the same lie one direction over. `status.json` publishes `read_at` per watch row, with `tests/test_status.py`'s exact-keyset assertion **updated by enumeration rather than loosened**. `CAUGHT M31 boty/retailers.py: 2 test(s) failed` — the mutation stamps a refusal that never received a page, which is the 2026-08-12 defect REQ-21 exists to fix, rebuilt inside the fix. Quoted from `07-01-SUMMARY.md`. **Live confirmation NOT OBTAINED, 2026-08-17:** the daemon's rows carry no `read_at` key at all |
| 2 | **MET in the tree — NOT ON THE WIRE. Spans two plans, and that is structure rather than dilution** | The criterion has a datum half and a rendering half, and the ROADMAP says so immediately below this table. **Datum, 07-01:** an unstamped reading is `None`, never `now` — red-watched by **M31**. **Rendering, 07-05:** `[age ?]` on `boty check` and an amber warn tag on the dashboard, both appended **unconditionally**, because if fresh rows carried no tag then an absent tag would *mean* fresh and the implicit claim would survive the fix. Red-watched by `CAUGHT M36 boty/cli.py: 1 test(s) failed — test_report_says_unknown_for_a_reading_nobody_dated`. **Measured on this host rather than argued:** the real payload renders **13 of 13 rows as `AGE ?`**, because `state.json` holds 13 availabilities and **0** stamps — re-confirmed 2026-08-17, still 13 bare pre-07 strings. The page was **looked at** with headless Chromium against a scratch copy, not inferred from source. Quoted from `07-01-SUMMARY.md` and `07-05-SUMMARY.md` |
| 3 | **MET IN PART — the `boty check` and dashboard thirds MET; the `status.json` third NOT SETTLED, recorded 2026-08-17** | **What is MET.** The threshold is the retailer's own current cadence, not a fixed clock: `Pacer.current_interval` is one number, `record` computes its own wait *through* it so the number shown and the schedule kept cannot drift apart, and `tests/test_pacing.py`'s schedule characterisation asserts **literal expected seconds** so it cannot pass by re-deriving them through the code under test (`CAUGHT M33 boty/pacing.py: 11 test(s) failed`). A row that *can* be old exists at all only because of 07-04 — **13 rows published while 3 were fetched**, `checked: false`, `alertable: false` stated (`CAUGHT M34`, `CAUGHT M35`). Both renderings judge against that published per-retailer number and never against `index.html`'s 30-minute banner constant, which was left exactly where it is (`CAUGHT M37 served/boty/index.html`). **What is NOT settled, and why it is not rounded up.** 07-05 deliberately added **no staleness flag and no new key** to `status.json`: a `stale` boolean computed at write time is written `false` and keeps saying `false` for exactly the interval during which it becomes true — `pacing.py:196-199`'s own recorded lesson, one file over — so it is *a bound that cannot bind, which is worse than no bound because it reads like one in the file*. Instead the file publishes three raw facts (`read_at`, `checked`, `current_interval_seconds`) and a join test derives the verdict from those three **and nothing else**, passing **on the RED commit before any implementation existed** — the strongest form that sufficiency claim can take. **The argument that this MEETS the criterion:** everything needed to present staleness is published, proved jointly sufficient by execution, and both consumers do present it. **The argument that it does not:** the criterion says *presented as stale in `status.json`*, and the file presents the **ingredients** of the verdict, not the verdict — a reader opening it sees three numbers and must subtract against their own clock. Those are different sentences, and this is the milestone that exists because a difference of exactly that size was published as if it were none. **Verdict reached: MET IN PART.** The criterion's text is **not edited**, and no key was added to make the row read MET |
| 4 | **MET in the tree — NOT ON THE WIRE, and the restart is the whole of what is missing** | `monitor.State` becomes a dated per-watch ledger, and the migration was measured against **the real pre-07 document on this disk** rather than a synthetic one: 13 bare strings loaded **without exception**, every availability preserved, every age **unknown**, and **alert behaviour byte-for-byte unchanged** — so nothing re-alerts on the migration itself. A stamp read back that is in the future, or a string, or a `True`, is **discarded rather than believed** (both ends of the bound validated). The age was observed surviving a restart **modelled as two `watch_loop` calls sharing one `state_path`**, each building its own `State` and its own `Pacer` so that **only the file crosses between them**, with **both ends asserted** — the bytes on disk and what a fresh `State.load` makes of them. **No process boundary was crossed, and no test in this phase crosses one** (corrected in place 2026-08-18; see the addendum above). `CAUGHT M32 boty/monitor.py: 7 test(s) failed` — the mutation defaults a missing stamp to `now`, which on this host's document dates all 13 entries at the instant the daemon starts and makes a two-day-old reading look four seconds old; that is this criterion's failure in one line. Quoted from `07-02-SUMMARY.md`. **NOT confirmed on the deployed daemon:** re-measured 2026-08-17, the running process is still the pre-phase one, so no service restart has yet exercised this path in production |
| 5 | **MET IN PART — the gate half MET; *"every gate"* NOT fully MET, recorded 2026-08-17** | **`make verify-offline` exits 0** — re-run at close on 2026-08-17 and **identical** to the 2026-08-14 run on every count: `identity check: PASS — 220 file(s)`, `865 passed`, `Success: no issues found in 18 source files`, `mutation check: 33/33 mutations caught`, `VERIFY: PASS (OFFLINE …)`, `EXIT=0`. Survivor list **empty**. **All seven new mutations were watched going red BY HAND, alone, before the harness was ever asked** — M31, M32, M33, M34, M35, M36, M37 — each reverted to an empty `git status --porcelain` before the next was applied, and in every case the by-hand killer list and the harness's list agree by name, which is the only thing that makes CAUGHT mean anything. **But *"every gate"* is broader than *"every mutation"*, and rounding this row up on the strength of 33/33 would be rewording a criterion one level in.** Enumerated: every TDD gate in the phase was observed failing first at a recorded RED count — 07-01 (3 failed / 33 passed, then 5 failed, then 4 failed), 07-02 (14 failed / 29 passed, then 2 failed / 45 passed), 07-03 (5 failed / 68 passed, then 5 failed / 25 passed), 07-04 (10 failed / 29 passed, then 3 failed / 39 passed), 07-05 (20 failed / 30 passed, then 6 failed / 9 passed) — **with exactly one named exception**: 07-05's join test, `test_status_json_carries_everything_a_consumer_needs_to_judge_staleness`, **passed the moment it was written, on the RED commit, and was therefore never observed failing.** That is not a weak test — it is the measurement that the three published facts were *already* jointly sufficient, and 07-05 recorded it as such rather than manufacturing a red — but the criterion says *every* gate, and this one was not watched going red. **Verdict reached: MET IN PART**, with the exception named rather than absorbed. **SUPERSEDED 2026-08-19 — see the next paragraph of this cell; the text above is the 2026-08-17 reading and is left unedited because it was true when written.** **UPDATED 2026-08-19 → MET, QUALIFIED.** The named exception is closed by measurement: the join test was watched going red on **five** separate breaks of the behaviour it joins, each applied alone in a throw-away worktree at HEAD `bc31030` and each reverted to an empty `git status --porcelain` — **3 failed / 881 passed** with `EXIT=1` (null the cadence the join fetches), **3 failed / 881 passed** (null the age), **4 failed / 880 passed** (invert the provenance), **2 failed / 882 passed** (publish the forbidden `stale` key on the remembered row) and **2 failed / 882 passed** (publish it on both row comprehensions, as somebody would actually ship it). Worktree baseline 884 passed; 884 passed again after the last revert. **THE QUALIFICATION, WHICH IS NOT OPTIONAL AND IS NOT A FORMALITY: this red was watched on 2026-08-19, after the fact, against an implementation that already existed. The original RED was never observed. TDD ordering was NOT followed for this test, and nothing here claims it was.** *The gate bites* and *the gate was written before the code it binds* are two different sentences and **only the first is now established** — which is the whole reason this row says MET **qualified** rather than MET. The verdict moves because the criterion's own text asks that a gate *have been watched going red* and does not say *first*, and because this repository's dominant instrument for that question is after-the-fact by construction — `mutation_check.py` breaks working code 34 times on every run and the phase calls those gates proven, and the 2026-08-17 verification re-applied three already-fixed defects by hand under the heading *"Gates re-watched going red"*. Reason (b), CR-01's escaping gate that could not bite, is also closed — `b1a3b88` widened `UNTRUSTED` to `w.availability` and the 2026-08-17 pass watched it red at 1 failed / 15 passed — but closing it does not erase that the phase shipped a bound that read like one and was not one for the span between 07-04 opening the sink and the fix, which is recorded in the qualification rather than in the verdict. **One finding recorded against interest: the join test never goes red alone.** All five breaks red at least one other test, because each of the three facts it joins carries its own gate; the test's contribution is the assertion that they *compose*, and a composition is reachable only through its parts. That is redundancy, not vacuity — a vacuous gate is one that cannot fail, and this one failed five times out of five. **No ident was registered and `M39` stays free**, because every break is already caught by a second test, so an ident would raise the denominator without defending anything new. Full working in `docs/retailer-evidence.md` § *Phase 7 non-vacuity measurement* |

**The phase gate, recorded 2026-08-17.** `make verify-offline`, run once at close and allowed to
finish, **exit 0**:

```
identity check: PASS — 220 file(s), no host identity found
All checks passed!
865 passed in 10.95s
Success: no issues found in 18 source files
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 33 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (836 passed, 29 skipped in 11.27s)
mutation check: 33/33 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
EXIT=0
```

**The ratio rose from 26/26 to 33/33**, and the arithmetic is stated once: **26 at phase start + 7
this phase = 33**. Read from the registry with comment lines filtered rather than counted with a bare
`grep -c`, which counts comment prose and is the self-invalidating class this phase had to correct
twice. The full ident list, in file order: `M1`–`M20`, `M25`–`M37`. **`M21`–`M24` ARE A DELIBERATE
GAP left by Phase 6 and are not four lost mutations** — 06-03: *"NO MUTATION REGISTERED, and M21-M22
left deliberately unallocated: `apply_mutation` cannot add a file, so the defect is outside the
harness by construction"*; 06-04: *"M23-M24 left unallocated, joining 06-03's M21-M22, so the
sequence carries a deliberate gap at M21-M24"*. The rise is **shown** rather than claimed: 531 / 8-8
(Phase 4 close) → 667 / 16-16 (Phase 5) → 768→769 / 24-24 (Phase 6) → **778 / 26-26 (Phase 7 start,
`dbc9d49`)** → 798 / 27-27 → 821 / 28-28 → 835 / 29-29 → 848 / 31-31 → 865 / 33-33.

**The live gate, run ONCE on 2026-08-14 and NOT repeated — its verdict is a 2026-08-14 observation
and is not restated as current.** Politeness is a hard constraint here and this close was budgeted
exactly one live pass, spent on 08-14 immediately after a daemon write so the two were not in flight
against the same six retailers. Verbatim, including the FAIL:

```
control check: FAIL — 2/6 control(s) not reading IN_STOCK
    walmart/CONTROL — Great Value whole milk: unknown — no store_id pinned for this watch
    amazon/CONTROL — Amazon Basics AA batteries (20-pack): unknown — blocked: challenge page
      matched 'to discuss automated access to amazon data' (HTTP 200)
control check: 2/6 control(s) could not run on THIS HOST
    bestbuy/… : fetch failed: no Chrome/Chromium binary found
    target/… : fetch failed: no Chrome/Chromium binary found
VERIFY: FAIL (live controls)
EXIT=2
```

The classes, separated, with **none of them this phase's**: (1) **2/6 cannot run on this host** —
Best Buy and Target, no Chrome/Chromium binary, pre-existing since 2026-08-06, and the tool itself
says this *"says nothing about the DETECTOR"*; (2) **the intermittent challenge class DID manifest on
2026-08-14**, on Amazon — it was absent on both 2026-08-10 and 2026-08-11, so the record now reads
present-absent-absent-present and *intermittent* remains the supported reading; (3) **Walmart through
Phase 5's config-gap guard**, because `make verify` runs in a shell with no `WALMART_STORE_ID` — that
one is Phase 5's and it is **correct**. The baseline's *"1/6 not reading IN_STOCK"* reads **2/6** here
because class 2 manifested, not because a new class appeared. **No control's verdict moved in a way
attributable to this phase**: GameStop and Nintendo both read `in_stock` as before, and no plan in
this phase touched a retailer, an extractor, a transport or a control. Recorded, not diagnosed, and
not re-run until green.

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
- [x] 07-06: Close — no code; the gates measured, the count observed rising from 26, five verdicts *(wave 6, blocked on 07-01 … 07-05, `autonomous: false`)*

**Correction recorded beside the two lines above, which are not edited (2026-08-17):** the 07-04
entry and the paragraph below this list both say *"14 configured watches"*. Measured through the
loader that actually builds them — `Config.load('config/products.yaml')` — the count is **13**
(gamestop 5, walmart 2, nintendo 2, amazon 2, bestbuy 1, target 1; 6 of them controls). The
fourteenth `grep -c "retailer:"` match is a **comment** at `config/products.yaml:309` — *"There is no
`retailer: pokemoncenter` entry and that is a finding, not a gap"* — a sentence about an **absent**
watch counted as a present one. First measured by 07-04. The lines stay as written on Phase 3.1's
precedent: a planning document is the record of what was believed when the work was scoped, and the
"3 rows" half of both sentences is a real measurement that still stands.

**Criteria 2 and 3 each span more than one plan, and that is structure rather than
dilution.** Criterion 2 splits across 07-01 (the datum: an absent stamp is `None`, never
`now`) and 07-05 (the rendering: it shows as UNKNOWN). Criterion 3 splits across 07-03
(the interval), 07-04 (a row that can be old) and 07-05 (the three renderings) — because
a paced-out watch does not have a *stale* row in `status.json` today; **it has no row at
all**, measured at 3 rows for 14 configured watches, so a staleness rule applied only to
the rows that exist would be a bound that cannot bind.
