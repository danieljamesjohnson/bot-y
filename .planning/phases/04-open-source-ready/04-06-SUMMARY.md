---
phase: 04-open-source-ready
plan: 06
subsystem: release
tags: [pypi, trusted-publishing, github-actions, oidc, release, roadmap, phase-close]

# Dependency graph
requires:
  - phase: 04-05
    provides: "1.0.0, CHANGELOG, the Trusted Publishing workflow and `make release-check` — the artefacts this plan's card tells Dan how to publish"
  - phase: 04-04
    provides: ".github/workflows/ci.yml, whose first live run this plan measured"
  - phase: 04-02
    provides: "LICENSE and the PEP 639 packaging metadata GitHub's detector now reads as MIT"
provides:
  - "04-06-HANDOFF.md — the four-step publish card, every value read off the shipped tree, no credential anywhere in it"
  - "The Phase 4 five-criterion outcome table in ROADMAP.md — three MET, two UNMET and not amended"
  - "deferred-items.md — the live-control failures measured at close, separated by class, and the phase-base derivation note"
  - "A measured record that REQ-11 does NOT close, with the reason quoted verbatim"
affects: [publishing, phase-05, req-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A phase may close on an unmet criterion with the reason quoted verbatim, rather than on a criterion reworded to be meetable"
    - "Verdicts distinguish what was OBSERVED on a real runner from what remains ASSERTED by test"

key-files:
  created:
    - .planning/phases/04-open-source-ready/04-06-HANDOFF.md
    - .planning/phases/04-open-source-ready/deferred-items.md
  modified:
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Dan deferred publishing — criteria 3 and 5 recorded UNMET and NOT amended, on Phase 3.1's precedent"
  - "REQ-11 left Pending: both halves of its text (PyPI install, v1.0.0 tag) are unproven by measurement"
  - "Criterion 4 recorded as preserved, not achieved — the measurement is that nothing moved"
  - "make verify's live FAIL captured verbatim and deferred, not trimmed and not re-run until green"

patterns-established:
  - "Provenance in the record: an action taken by an agent is attributed to the agent, not to the maintainer"
  - "Re-measure at close rather than carry forward a Task 1 measurement — 404s and empty tag lists were re-checked"

requirements-completed: []  # REQ-11 was this plan's requirement and it did NOT close. Recorded UNMET, deliberately.

# Metrics
duration: ~35min
completed: 2026-08-06
---

# Phase 4 Plan 06: Maintainer Handoff Summary

**Phase 4 closes on five measured verdicts — three MET, two UNMET and left unamended — because Dan deferred publishing, and the honest close is the one that says so rather than the one that is green.**

## Performance

- **Duration:** ~35 min across two sessions (Task 1 on 2026-08-05, Tasks 2–3 on 2026-08-06)
- **Tasks:** 3 of 3
- **Files modified:** 4, all inside `.planning/`

## Accomplishments

- **The handoff card exists and is accurate** — 192 lines, every value (distribution name, owner, repo, workflow filename, the `pypi` environment name, the tag, the two git commands) read out of the shipped tree at execution time rather than copied from a plan. It carries no credential and says in writing that there is none to mint.
- **Phase 4's five criteria carry verdicts**, each with the command, count or run URL that produced it — or the named reason it could not be produced. Criteria wording untouched.
- **REQ-11 recorded as NOT closing**, by the plan that was supposed to close it. That is the outcome, measured, not a failure to execute.
- **The first live CI run this repository has ever had was measured** — green, and its limits stated precisely.

## Task Commits

1. **Task 1: Pre-flight — read the handoff off the shipped tree** — `76d4156` (docs)
2. **Task 2: Dan publishes — the four things no agent here may do** — checkpoint, no commit
3. **Task 3: Measure what came back, record five verdicts, close** — `a5762e6` (docs)

## The branch taken: B — deferred

Dan's reply, verbatim, **2026-08-06**:

> "i don't think we need to host it yet. it's probably not quite ready for that"

Classified **deferred**, not declined — he is saying not yet, not never. The card stays on
disk per its own § *If you decline, or defer*, so publishing later needs no replanning.

Per branch B: no install was run, no network write was attempted, and the publish state was
**re-measured here rather than assumed from Task 1**:

| Check | Command | Result |
|---|---|---|
| PyPI project | `curl https://pypi.org/pypi/bot-y/json` | **HTTP 404** |
| PyPI 1.0.0 | `curl https://pypi.org/pypi/bot-y/1.0.0/json` | **HTTP 404** |
| Local tags | `git tag -l` | empty, 0 tags |
| Remote tags | `git ls-remote --tags origin` | **0 refs** |
| Publish workflow | `gh run list --workflow release.yml` | no runs |

## Provenance — what was done, and by whom

This matters because the plan's own acceptance criteria distinguish an action taken by Dan
on this box from one taken by an agent, and the record must not blur them.

- **Step 1 of the card WAS carried out — by the orchestrator agent, not by Dan.**
  `git push -u origin main`, `b0a272f..76d4156`, upstream configured on `main` for the first
  time (it had none). Local and remote `main` both at `76d4156`, `git rev-list --left-right
  --count origin/main...HEAD` → `0 0`.
- **Steps 2, 3 and 4 were not done at all.** No trusted publisher, no tag, nothing published.
- **Step 5 (the optional throwaway PR) was not taken**, so CI's `pull_request` trigger is
  still unobserved.
- **This plan pushed, tagged, published and uploaded nothing.** Its whole diff is four files
  under `.planning/`.

**A free observation the push made available:** `api.github.com/repos/danieljamesjohnson/bot-y`
now reports `license: {"key": "mit", "spdx_id": "MIT"}`, where it read `null` before this
phase. That is GitHub's own detector agreeing with 04-02, at no cost — recorded because it is
the only place outside a downloaded artefact where the licence can be seen to have shipped.

## The five verdicts

Full table, with measurements, is in `.planning/ROADMAP.md` § *Phase 4*. In brief:

| # | Criterion | Verdict | Basis |
|---|---|---|---|
| 1 | Contributor doc walks a real adapter end to end | **MET** | `tests/test_contributor_docs.py` 19 passed; 355 lines walking **Nintendo**; `## Why a control product is mandatory` present with the rule and a real rejected candidate |
| 2 | CI runs the suite on every PR, offline, on fixtures | **MET**, one half observed | `tests/test_ci_workflow.py` 67 passed; shipped `on:` is `pull_request:` + `push: [main]`; run `31066215395` green on a real runner. PR trigger **not** witnessed |
| 3 | `pip install bot-y` works from PyPI | **UNMET** | HTTP 404, both URLs. Dan's words, verbatim, with the date. Not amended |
| 4 | README documents the support matrix | **MET — preserved, not achieved** | `tests/test_support_matrix.py` 31 passed; **0** matrix rows/header changed across the phase; locator count exactly **1** |
| 5 | A tagged v1.0.0 release exists | **UNMET** | 0 tags local, 0 refs on remote, no release-workflow runs. Not amended |

### Criterion 2's distinction, because it is the one that would be easy to overstate

**Observed:** run [`31066215395`](https://github.com/danieljamesjohnson/bot-y/actions/runs/31066215395),
read firsthand with `gh run view --log` rather than taken from the handoff context — event
`push`, branch `main`, sha `76d4156` (exactly the Task 1 commit), one job `verify`,
conclusion **success**, `2026-08-06T02:39:05Z` → `02:42:22Z`. Its log carries
`identity check: PASS — 153 file(s), no host identity found`, `531 passed in 16.54s`,
`mutation check: 8/8 mutations caught`, and ends:

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

That proves the job provisions its interpreter and reaches a green offline verdict on a real
runner. It does **not** prove the `pull_request` trigger — `gh run list --workflow ci.yml`
returns exactly one run, that push. The trigger contract remains asserted by
`tests/test_ci_workflow.py` and unwitnessed in production. One throwaway PR would close it.

### Criterion 4, and why the check is narrow on purpose

Recorded **preserved, not achieved**: 03.1-04 verified it cell-by-cell against live status
output *before this phase opened*, and Phase 4's job was to not break it. The measurement is
that nothing moved — across `b0a272f..HEAD` (44 commits), `git diff -U0 -- README.md`
contains **zero** lines matching the seven row labels plus the header cell.

The only README table lines this phase touches at all are two, both added by 04-03 on purpose:

```
+| `identity` | No host identity — IP, coordinates, tokens — in **any** tracked file, not only the fixtures |
+| `lint` | `ruff` is clean over `boty/`, `scripts/` and `tests/`, against the rule set committed in `pyproject.toml` |
```

Those are `| Stage | Proves |` rows, not support-matrix rows. The plan predicted them
(measured fact 12) and required that the check not fire on them. **They are expected, and
they are not a finding.** A wider check — "no README table row changed" — would have gone red
on correct, required work at the final step of the phase.

## The phase gate, run once, live

`make verify`, per Task 3 § C. Verdict line **verbatim, untrimmed**:

```
VERIFY: FAIL (live controls)
```

exit 2. The plan anticipated a `PASS` with one of two suffixes; it got a FAIL. Recorded as it
came back. Two distinct classes, which `control_check.py` separates itself:

- **2/6 could not run on THIS HOST** — Best Buy and Target, both rung 3:
  `no Chrome/Chromium binary found — set BOTY_BROWSER_PATH to one`. Measured: `nodriver 0.50.3`
  *is* in `.venv`, but no `google-chrome`/`chromium`/`chromium-browser`/`chrome` is on PATH and
  `BOTY_BROWSER_PATH` is unset. The tool states this "says nothing about the DETECTOR."
- **2/6 not reading IN_STOCK** — Walmart (`blocked: challenge page matched 'robot or human'`,
  HTTP 200) and Amazon (`blocked: challenge page matched 'to discuss automated access to
  amazon data'`, HTTP 200). Both retried once, both blocked again, both read **UNKNOWN** rather
  than OUT_OF_STOCK — the fail-safe working as designed. This one *is* a statement about the
  detector.

**Not a Phase 4 regression, and the claim is checkable:** no plan in this phase changed a
retailer, an extractor or a control. The phase's entire diff outside `.planning/` is docs,
licence, lint config, CI and packaging. Both retailers were green when 03.1-04 closed Phase
3.1 on 2026-08-03, so what changed is what those retailers serve this host. Written up in
`deferred-items.md` rather than diagnosed inside a closing plan — distinguishing a
reputation-flagged IP from a new unconditional challenge from a changed page shape needs
polite probing and a fixture re-capture, which is a plan, not a footnote.

## Decisions Made

1. **Criteria 3 and 5 stand as written, unmet.** Phase 3.1 was offered a rewrite of its
   criterion 1 that would have made it meetable and Dan declined it. This plan does not get to
   do what that one refused. The ROADMAP prose says so explicitly and cites the precedent.
2. **REQ-11 left Pending.** This was the plan carrying `requirements: [REQ-11]`, and the honest
   outcome is that it does not close. Its traceability note now records the measurement and the
   verbatim reason. No other requirement touched.
3. **Dan's words are quoted, never paraphrased.** Not into "declined", and not into a judgement
   about whether the tree is ready — the measurements speak to the tree, he spoke to the timing.
4. **The live `make verify` FAIL is recorded, not fixed.** Out of scope twice over: this plan may
   modify no file outside `.planning/`, and nothing in it caused the failure.

## Deviations from Plan

### 1. [Rule 1 — Bug] The plan's phase-base derivation recipe undershoots its own definition

- **Found during:** Task 3, criterion 4's measurement
- **Issue:** Task 3's verify block derives the phase base as
  `git log --diff-filter=A --format=%H -- docs/adding-a-retailer.md | tail -1` + `^`, which
  yields `4cfe2b2` — only 22 commits back, because 04-01 made two commits (`db85e41`,
  `4cfe2b2`) *before* the one that added the doc. The plan's stated **definition** is "the
  parent of the first execution commit", and the SHA it expected was `b0a272f`. The recipe is a
  proxy that measures a narrower window than the phase.
- **Fix:** Re-derived all three and measured criterion 4 across the **widest**, `b0a272f..HEAD`
  (44 commits), since a superset window is the stronger claim. Confirmed `b0a272f` is an
  ancestor of both candidates via `git merge-base --is-ancestor`.
- **Verification:** All three windows return the same answer — **0** changed lines matching
  `^[-+]\| (GameStop|Walmart|Nintendo|Best Buy|Pokémon Center|Amazon|Target|Retailer) `. The
  verdict does not depend on which base is chosen; the fix is about the claim being as wide as
  it says it is.
- **Files modified:** none — this is a measurement correction, recorded in `deferred-items.md`
  so the next plan copying that recipe knows it is a proxy.
- **Committed in:** `a5762e6`

### 2. [Rule 2 — Missing record] `deferred-items.md` created

- **Found during:** Task 3 § C
- **Issue:** The live gate failed and there was nowhere in the phase to put a finding that is
  real, out of scope, and would otherwise be lost between a ROADMAP table cell and a commit
  message.
- **Fix:** Created `.planning/phases/04-open-source-ready/deferred-items.md` — the executor's
  standard destination for out-of-scope discoveries — carrying both failure classes with their
  verbatim output, the host measurements behind them, and pointers to the two prior detector
  write-ups in `docs/retailer-evidence.md`.
- **Committed in:** `a5762e6`

### 3. [Rule 2 — Missing record] REQ-11's traceability note updated

- **Found during:** Task 3 § D
- **Issue:** REQ-11's note named 04-06 as "the plan that closes this". After this plan ran and
  did not close it, that note would read as a pending promise rather than a measured outcome.
- **Fix:** Appended the 04-06 result — still `[ ]`, still `Pending`, with the 404s, the empty
  tag lists, Dan's verbatim reason, and a pointer to the handoff card. **The checkbox was not
  ticked and no other requirement was touched.**
- **Committed in:** `a5762e6`

---

**Total deviations:** 3 (1 × Rule 1, 2 × Rule 2). **Impact:** none on scope — no source file
was touched, no criterion was reworded, and the one measurement correction made the claim
wider rather than weaker.

## Issues Encountered

**`make verify` failed live.** See § *The phase gate* above. Resolved by recording it verbatim
and deferring it, which is what the plan's own framing demands: *"The plan is complete when the
verdicts are honest, not when they are green."* Phase 4's five criteria do not include a green
live gate — that was Phase 3.1's criterion 5 — so this does not block the close, and saying so
is not the same as waving it past.

## Verification

| Gate | Result |
|---|---|
| Five gate test modules | **144 passed** in 0.51s |
| Outcome table: exactly 5 rows under the Phase 4 heading | **5** |
| ROADMAP diff is additions only (`grep '^-[^-]'`) | **no removed lines** |
| `scripts/identity_check.py --all`, edits staged | **PASS — 154 file(s)** |
| No file outside `.planning/` touched | **PASS** — 3 files, all `.planning/` |
| Nothing pushed, tagged or published by this plan | **PASS** — 0 tags, 0 remote refs, no release runs |

## User Setup Required

**Still outstanding, and that is the deferred item itself.** Whenever Dan wants to publish,
`.planning/phases/04-open-source-ready/04-06-HANDOFF.md` carries all four steps with the exact
strings — including the `pypi` environment name, which is the single most likely thing to get
wrong. Nothing on that card asks for a credential.

## Next Phase Readiness

Phase 4 is closed. Waves 1–5 are complete and independent of publishing: the tree builds,
installs, lints, type-checks, tests and has green CI.

**Two things carry forward:**

1. **REQ-11 is open**, and closing it is four steps on a card, not a replan.
2. **The live control failures in `deferred-items.md`** are the more interesting of the two.
   Walmart and Amazon are being turned away from this host right now, and Best Buy and Target
   cannot be read at all for want of a browser binary. Real restocks are being missed. That
   deserves its own plan, with probing at a polite cadence and fixture re-capture — the shape
   `docs/retailer-evidence.md` already uses for the Best Buy and Target write-ups.

## Self-Check: PASSED

All claimed artifacts exist on disk (`04-06-HANDOFF.md`, `deferred-items.md`,
`04-06-SUMMARY.md`, `ROADMAP.md`, `REQUIREMENTS.md`). Both claimed commits exist
(`76d4156`, `a5762e6`). REQ-11 verified still `- [ ]` unchecked and still `Pending` in
the traceability table — the one thing this plan most needed not to get wrong.

---
*Phase: 04-open-source-ready*
*Completed: 2026-08-06*
