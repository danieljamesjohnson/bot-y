---
phase: 08-stop-knocking
plan: 01
subsystem: testing
tags: [pacing, backoff, measurement, simulation, pytest]

requires:
  - phase: 05-persistence
    provides: "`Pacer.record`/`current_interval` with the persisted `refusals` counter the simulation drives"
provides:
  - "The `before` half of criterion 3: 125 requests to a never-recovering retailer over 30 simulated days, as a stated literal transcribed from a run against unmodified production code"
  - "A denominator that is asserted rather than assumed, watched red before it was trusted"
  - "08-DECISIONS.md — collisions 1, 2, A, B and C resolved in writing, plus one dismissed detector hit"
  - "COVERAGE.md — the single declaration line"
affects: [08-02, 08-03, 08-04]

actuals:
  tokens: 5670
  tasks: 3
  commits: 2

tech-stack:
  added: []
  patterns:
    - "A perishable measurement taken in its own wave, before the code it measures moves"
    - "An asserted denominator as the anti-omission guard on a simulated count"

key-files:
  created:
    - .planning/phases/08-stop-knocking/08-DECISIONS.md
    - .planning/phases/08-stop-knocking/COVERAGE.md
  modified:
    - tests/test_pacing.py

key-decisions:
  - "Collision 1: STATE_MAX_AGE_SECONDS' derivation carries the new number and lands in 08-03, not 08-02, so 08-03's tests are red against unfixed code — with the one-wave gap stated in all three of its clauses"
  - "Collision 2: due_at stays unpersisted; criterion 5 is met depth-only, and criterion 2's 'exactly once' is scoped to a running process at a price of one request per restart"
  - "Collision A: the existing cap test breaks deliberately at a threshold of 30 or below; the band is recorded and the value left to 08-02"
  - "Collision B: 72h on the dashboard is legible; keeping it is 08-04's deliberate call, not wave 1's to pre-empt"
  - "Collision C (found while writing 08-01): this baseline test is one 08-02 necessarily turns red, which is its second job — it becomes 08-02's watched-red evidence for criterion 3"
  - "The threshold's stated lower bound is withdrawn: it cites cli.REFUSALS_BEFORE_PAGING, deleted 2026-08-12"

patterns-established:
  - "Rule 1's stated exception: a test that measures rather than gates cannot be watched red, and that is a finding recorded in the test's own docstring — with the one assertion that does have a subject watched red instead"
  - "A simulated count carries its restart assumption in the same breath as the number, never in a footnote"

requirements-completed: [REQ-22]

status: complete
---

# Phase 8 Plan 01: Stop Knocking — The Number Before

Recorded criterion 3's `before` half — **125 requests to a never-recovering retailer over 30
simulated days under the current rule** — as a stated literal transcribed from a run against
unmodified `boty/pacing.py`, and settled five collisions in writing, without moving one line of
production code.

## The baseline number

**125.** Measured with `.venv/bin/python -m pytest tests/test_pacing.py -q` against
`boty/pacing.py` at `git rev-parse --short HEAD` = `85a8d9f`; `git diff 85a8d9f e986d01 --
boty/pacing.py` is empty, so that is byte-identical to the file's last-modified revision, and
`git status --porcelain boty/` printed nothing before the run.

Retailer `walmart`, 300 s standing interval, no override. Denominator 8640 cycles x 300 s =
2 592 000 s = 30 days. **Zero restarts assumed, one extra request per restart if there were any** —
so 125 is a floor on real-world requests, not a prediction of them.

The literal was **transcribed, not predicted**: the test was written with a placeholder (`== -1`),
run, and the count read out of the failure message.

```
$ .venv/bin/python -m pytest tests/test_pacing.py -q
>       assert len(offsets) == -1, (
E       AssertionError: the current rule asked a never-recovering retailer 125 times over a
E       simulated thirty days at the 300-second standing cadence; the recorded before-number
E       for criterion 3 is the literal in this assertion
E       assert 125 == -1
E        +  where 125 = len([0.0, 600.0, 1800.0, 4200.0, 9000.0, 18600.0, ...])
```

With `125` transcribed in: `76 passed in 0.11s`.

**This is one count and nothing else.** No comparison, no reduction, no threshold. The `after`
number and the word *strictly* are 08-02's.

## The recorded red

Rule 1's exception is argued in the plan and in the test's own docstring: the count assertion has no
subject to be red against, because its subject is the code as it stands rather than a defect. **The
one assertion that does have a subject — the denominator — was watched red**, per the plan's
requirement.

Loop bound temporarily reduced to `_THIRTY_DAYS_OF_CYCLES - 1`:

```
1 failed, 75 passed in 0.07s
>       assert now == 2592000.0, (
E       AssertionError: the simulated clock finished at 2591700.0 s, not the 2 592 000 s that are
E       thirty days — so the count above is a count over some other window...
E       assert 2591700.0 == 2592000.0
```

**Failure count: 1 failed, 75 passed. The assertion that fired was the denominator, not the count.**

That distinction is the finding, and it is the reason the denominator assertion exists: **the count
assertion still read 125 over the shortened window and passed.** A window that quietly shrank would
therefore have been invisible to the count alone — exactly the "reduction achieved by not asking"
this plan's prohibition names. Bound restored; `git diff` back to the intended edit.

## The gate

`make verify-offline`, with nvm sourced first (`export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh`),
exited 0. **Verdict line, verbatim:**

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

The OFFLINE pass, as expected — not INCOMPLETE, so no control was reported unverifiable on this
host. `mutation check: 37/37 mutations caught`. `control check: SKIPPED (--offline) — no live
retailer request made.`

### The new test executes inside the gate, not beside it

The gate's test stage is `$(PYTHON) -m pytest tests/ -q -rs` (`Makefile:76`) — `-rs` is on, and the
run reported **`896 passed in 11.17s` with no skip summary at all, i.e. zero skips**. No new skip;
none pre-existing in that stage either.

| Measurement | Before | After |
|---|---|---|
| `tests/test_pacing.py` collected | 75 | **76** |
| Suite collected under the gate's own invocation | — | 896 |

Proved rather than assumed, because a pass under a direct `pytest` invocation would not have
established it: deselecting exactly the new test from the gate's own command drops the total to
**`895 passed, 1 deselected`**. The new test is one of the 896 that ran inside `make verify-offline`.

## The scope fence

`git diff --name-only 85a8d9f..HEAD` — three paths, sorted, and **not one under `boty/`,
`scripts/` or `served/`**:

```
.planning/phases/08-stop-knocking/08-DECISIONS.md
.planning/phases/08-stop-knocking/COVERAGE.md
tests/test_pacing.py
```

## What this plan does NOT claim

- **Criterion 6 is NOT discharged here.** No mutation was registered, none was observed CAUGHT, and
  **M42 is still free**. The green `make verify-offline` above says the tree is still green with a
  new test in it — a regression check. It is not evidence for criterion 6, which is 08-04's.
- **No comparison and no reduction.** One number is stated. The thing it will be compared against
  does not exist yet.
- **No threshold value.** `REFUSALS_BEFORE_COOLOFF` is 08-02's to pick; only its band is recorded.
- **Criteria 1, 2 and 4 (08-02), criterion 5 (08-03) and criterion 3's `after` half (08-02)** are
  untouched.

## Nothing live was touched

No live retailer request was made. **`boty check` was not run.** `make verify` — the unqualified
target with live controls — was deliberately not run. `state.json`, `pacer-state.json` and
`served/boty/status.json` were neither read nor written, and `git status --porcelain` shows no
modification to any of them. No `systemctl restart boty`.

## Deviations from Plan

**1. [Rule 3 - Blocking] `zip(..., strict=...)` replaced with `itertools.pairwise`**
- **Found during:** Task 1, at the `make lint` gate.
- **Issue:** The plan states *"No new import should be needed."* The strictly-increasing tally was
  written with `zip(offsets, offsets[1:])`, which ruff rejects under RUF007 (`Replace zip() with
  itertools.pairwise()`). `make lint` exited 1.
- **Fix:** Used `itertools.pairwise`, ruff's own suggested form, and added `from itertools import
  pairwise` to the import block. The import IS used, so the plan's actual rule — *"nothing is
  imported that is not used"* — holds; only its prediction that no import would be needed did not.
  Fixed the code, not the gate.
- **Files modified:** `tests/test_pacing.py`. **Commit:** `d87386f`.

**2. [Rule 1 - Bug, in the planning documents] The threshold's stated lower bound cites a deleted constant**
- **Found during:** Task 2, reading the `read_first` range for the band.
- **Issue:** Both `08-PLAN-OUTLINE.md` and `08-01-PLAN.md` give the lower bound as *"comfortably
  above `cli.REFUSALS_BEFORE_PAGING = 5` (or persistence defeats the paging clause)"*. **That
  constant does not exist.** `REFUSALS_BEFORE_PAGING` and `_refusal_is_entrenched` were deleted on
  2026-08-12 (`boty/cli.py:432` carries the note), and
  `test_the_clamp_never_restores_a_shallower_wait_than_the_cap` was re-anchored off it the same day.
  A later wave reading only the outline would have preserved a bound whose reason is gone.
- **Fix:** Recorded in `08-DECISIONS.md` § *Collision A* as a withdrawal **beside** the original
  rather than an edit over it, with the replacement argument marked **provisional** and left to
  08-02 — this plan does not pick the number. The planning documents themselves were not edited:
  they are the record of what wave 1 was told, and `08-DECISIONS.md` is the wave's answer.
- **Commit:** `01c04dd`.

**3. [Recorded, deliberately NOT fixed] A stale comment in production code**
- `boty/pacing.py:175` still reads *"It must also stay comfortably above
  `cli.REFUSALS_BEFORE_PAGING`"*, naming the same deleted constant. A genuine defect.
- **Not fixed here:** this plan's acceptance criteria assert the changed-file list by equality, and
  a production edit would poison the scope fence the baseline number depends on. Handed to 08-02 or
  08-03, both of which edit `boty/pacing.py`.

**4. [Plan defect, worked around] The `identity_check.py` verify command is missing its required flag**
- Task 2's `<verify>` gives `.venv/bin/python scripts/identity_check.py`, which exits **2** with
  `error: one of the arguments --staged --all is required`. Ran `--all` instead: `identity check:
  PASS — 236 file(s), no host identity found`, exit 0. The tracked pre-commit hook also passed on
  both commits (`PASS — 1 file(s)`, `PASS — 2 file(s)`).

## A judgment call, flagged rather than silently made

Task 2's acceptance criteria require that § *The baseline number* "contains no second count". It
carries the decomposition `125 = 6 + 1 + 118` — six requests while the backoff climbs, one where the
cap first binds, 118 in the flat six-hour tail — read off the offsets the same run printed. **Read as
arithmetic on the one count rather than as a second count**, and labelled in the document as exactly
that. There is no comparison between counts, no threshold and no verdict in that section. Flagged
here because it is a reading judgment against a criterion checked by reading, and a later reviewer
should see the call rather than have to infer it.

## STATE.md and ROADMAP.md were NOT updated

Deliberately, per this executor's instructions: the orchestrator owns those writes and edits them by
hand. No `gsd-tools` state or phase WRITE subcommand was invoked at any point — `state.advance-plan`,
`state.begin-phase` and `phase.complete` are banned in this repo on fourteen recorded corruptions.
`.planning/STATE.md` shows as modified in `git status`, and that modification is not this plan's; it
was present before execution began and was never staged.

## Commits

| Commit | What |
|---|---|
| `d87386f` | `test(08-01): record the before-number the cool-off is about to make unobtainable` |
| `01c04dd` | `docs(08-01): settle five collisions in writing before any code moves` |

Git identity checked **before** committing: `3347065+danieljamesjohnson@users.noreply.github.com`,
the repo's configured no-reply identity. No commit used `--no-verify`.

## Self-Check: PASSED

- `tests/test_pacing.py` — FOUND, contains `_THIRTY_DAYS_OF_CYCLES = 8640` (1 match at module level)
  and the test function (1 match)
- `.planning/phases/08-stop-knocking/08-DECISIONS.md` — FOUND, `grep -c "^## "` = **7**, all 13
  required tokens present
- `.planning/phases/08-stop-knocking/COVERAGE.md` — FOUND, `wc -l` = **1**, exact-match grep = 1
- Commit `d87386f` — FOUND in `git log`
- Commit `01c04dd` — FOUND in `git log`
- Baseline literal byte-identical in both places: `assert len(offsets) == 125` /
  `asked 125 times in 30 simulated days`
