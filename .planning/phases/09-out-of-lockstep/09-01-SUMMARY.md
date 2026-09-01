---
phase: 09-out-of-lockstep
plan: 01
subsystem: testing
tags: [pacing, scheduling, lockstep, measurement, simulation, pytest]

requires:
  - phase: 08-stop-knocking
    provides: "`Pacer.record`/`Pacer.due` in their post-cool-off, pre-de-lockstep form — the unmodified rule this number measures"
provides:
  - "The `before` half of criterion 3: SIX of six configured retailers requested inside a single 60-second window over a simulated day, as a stated literal transcribed from a run against unmodified production code"
  - "A denominator, a fleet binding and two tallies, each watched red before it was trusted"
  - "09-DECISIONS.md — collisions 1-8 and test collisions A, B and C resolved in writing, plus one withdrawn concession and one newly-found trap"
  - "The construction-site count corrected from 31 to 32, with this plan named as what moved it"
affects: [09-02, 09-03, 09-04, 09-05]

actuals:
  tokens: 12400
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "A perishable measurement taken in its own wave, before the code it measures moves"
    - "A sliding window rather than fixed bins, so a burst straddling a boundary cannot be under-reported"
    - "A fleet table that is BOTH the simulation's input and the thing asserted against the tracked config, so a published number cannot re-point itself at a different fleet"

key-files:
  created:
    - .planning/phases/09-out-of-lockstep/09-DECISIONS.md
  modified:
    - tests/test_pacing.py

key-decisions:
  - "Collision 2: the module docstring's 'a restart still tries once, immediately' is withdrawn, priced at one standing interval, with due_at-never-persisted and DEPTH-is-what-a-restart-inherits named as surviving; 09-02 lands it"
  - "Collision 7: no STATE_VERSION bump is owed because the phase is DERIVED from the retailer name and roster, not stored — storing it would be a new key, which would discard every refusal count on ship day"
  - "Collision 8: criterion 4's budget half is expected at MET IN PART, stated BEFORE the measurement, and boty check will not be run to close the gap"
  - "Test collision C: this baseline test is one 09-02 necessarily turns red, which is its second job — it becomes 09-02's watched-red evidence for criterion 3"
  - "Found while executing: a stale .pyc can keep a reverted red-watch perturbation live; every remaining wave must clear the cache between perturbation and revert"

patterns-established:
  - "Rule 1's stated exception, applied a second time and confirmed a second time: a measuring test cannot be watched red, and the literal was measurably BLIND to both a shortened day and a changed fleet — which is what makes the other assertions load-bearing rather than decorative"

requirements-completed: []

status: complete
---

# Phase 9 Plan 01: Out of Lockstep — The Number Before

Recorded criterion 3's `before` half — **all SIX configured retailers requested inside one 60-second
window over a simulated day under the current rule** — as a stated literal transcribed from a run
against unmodified `boty/pacing.py` and `boty/cli.py`, and settled eight collisions and three test
collisions in writing, **without moving one line of production code**.

## The before-number

**6.** Measured with `.venv/bin/python -m pytest tests/test_pacing.py -q` at
`git rev-parse --short HEAD` = `87871b4`, with `git status --porcelain boty/` printing nothing
before the run.

| | |
|---|---|
| Fleet | `amazon` 1800 s, `gamestop` 900 s, `bestbuy`/`nintendo`/`target`/`walmart` on the 300 s global default — asserted against `config/products.yaml`, not hand-copied |
| Denominator | 288 cycles x 300 s = 86 400 s = one day, **asserted after the loop** |
| Total requests counted | 1296 = 48 + 96 + 4 x 288 |
| Window | a **sliding** 60 s window over the event times, never fixed bins |
| `git log -1 --format=%h -- boty/pacing.py` | `a58e7ac` |
| `git log -1 --format=%h -- boty/cli.py` | `9ea42fe` |

The HEAD and the last-modified revisions differ and that is not a discrepancy:
`git diff a58e7ac 87871b4 -- boty/pacing.py` is **empty**, so the file at the measured HEAD is
byte-identical to its last-modified revision.

The literal was **transcribed, not predicted**: the assertion was written with a placeholder
(`== -1`), run, and the number read out of the failure message.

```
$ .venv/bin/python -m pytest tests/test_pacing.py -q
>       assert max_in_any_60s == -1, (
E       AssertionError: the current rule put 6 of the six configured retailers (amazon, bestbuy, gamestop, nintendo, target, walmart) inside a single 60-second window at least once over a simulated day; the recorded before-number for criterion 3 is the literal in this assertion
E       assert 6 == -1

1 failed, 97 passed in 0.20s
```

With `6` transcribed in: `98 passed in 0.19s`.

**The window model and the direction of its residual.** `monitor.run_once` asks its due retailers
back to back with no sleep between them, so every request one pass makes is modelled as falling
inside one 60-second window. The measurement behind that: `duration_seconds: 20.43` for 13 watches
across all six retailers, read from `served/boty/status.json` on 2026-08-31 by the phase-8 code
review and **quoted rather than re-read**. If a pass ever exceeded 60 s the model would
**over**-count, so **6 is an upper bound on the before-number** — the safe direction for a number
this phase must come in under. It cannot flatter the change.

**It is a count of RETAILERS, not of requests.** The fleet carries 13 watches, so a window holding
six retailers holds more than six HTTP requests. **Zero restarts assumed, and a restart cannot make
it smaller** — `due_at` is never persisted, so every process starts with all six due at once.

**This is one count and nothing else.** No comparison, no reduction. The after-number and the word
*smaller* are 09-02's.

## The recorded reds

Rule 1's exception is argued in the plan and in the test's own docstring: **the literal has no
subject to be red against**, because its subject is the code as it stands rather than a defect.
Three assertions that *do* have subjects were watched red. Each perturbation was reverted and `diff`
confirmed the file back to the intended edit.

| Perturbation | Assertion that fired | Failure count |
|---|---|---|
| loop bound `_ONE_DAY_OF_CYCLES - 1` | the **denominator** (`86100.0 != 86400.0`) | **1 failed, 97 passed** |
| `_FLEET_INTERVALS["gamestop"]` 900 -> 600 | the **fleet** (`{'gamestop': 900} != {'gamestop': 600}`) | **1 failed, 97 passed** |
| one recorded event deleted | the **tally** (`1295 != 1296`) | **1 failed, 97 passed** |

Restored: `98 passed`.

**The finding is which assertion fired, not that one did — and it fired twice over.**

- Over the shortened day, **the literal still read 6 and passed.** A window that quietly shrank would
  have been invisible to the count alone. This reproduces `08-01`'s result on a different number,
  which makes it a repeated measurement rather than a one-off.
- Under the perturbed fleet, **the literal still read 6 and passed too** — at a 600 s gamestop cadence
  the coincidence survives, because 1800 is a multiple of 600. So the literal is blind to a fleet
  change as well.

That is the whole case for the other assertions existing. A fourth guard, not red-watchable, backs
them: each retailer's observed count is checked against `86400 // interval` derived from
`config/products.yaml` — a number the loop had no hand in producing.

## A trap found while executing: a stale `.pyc` kept a reverted perturbation live

RED 2 changed `"gamestop": 900` to `"gamestop": 600` — **byte-identical in length** — and the revert
landed within the same wall-clock second. CPython and pytest's rewrite cache validate a cached
`.pyc` on source **mtime at one-second resolution plus size**; both matched, so the reverted source
was never recompiled and the interpreter kept running the perturbed bytecode.

`diff` said IDENTICAL. `git status` was empty. `grep` showed `900` in the working tree **and** in
`HEAD`. And `make verify-offline` failed citing `{'gamestop': 600}` — **a value present in no file on
disk**. A per-file bisect then reported *every* test file as the trigger, which is what a
session-level cause looks like from inside a per-file bisect. Measured:
`tests/__pycache__/test_pacing.cpython-312-pytest-9.1.1.pyc` at `08:13:36.389` against a source at
`08:13:36.575`.

**All three red-watches were re-run from a cleared cache and all three reproduced** with the same
assertion firing and the same count. **The counts in the table above are the re-run ones** — the
originals agreed, but they were taken under a cache that had just been shown untrustworthy, so they
are not what is cited.

**This defeats the red-watch protocol silently, and every remaining wave in this phase red-watches
this file.** It is recorded in `09-DECISIONS.md` with the one-line fix. It belongs in `CLAUDE.md`
§ *Traps that have actually bitten*; **09-01 could not put it there** without breaking the scope
fence the before-number depends on, so it is handed forward in writing.

## The gate

`make verify-offline`, with nvm sourced first (`export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh`),
exited 0. **Verdict line, verbatim:**

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

The OFFLINE pass, as expected — **not INCOMPLETE**, so no control was reported unverifiable on this
host. `mutation check: 38/38 mutations caught` (M42 is the newest ident; **M43 is still free**).

### The new test executes inside the gate, not beside it

The gate's test stage is `$(PYTHON) -m pytest tests/ -q -rs` (`Makefile:76`) — `-rs` is on, and the
run reported **`921 passed` with no skip summary at all, i.e. zero skips**. No new skip; none
pre-existing in that stage either.

| Measurement | Before | After |
|---|---|---|
| `tests/test_pacing.py` collected | 97 | **98** |
| Suite collected | 920 | **921** |

**Proved rather than assumed**, because a pass under a direct `pytest` invocation would not have
established it: deselecting exactly the new test from the gate's own command drops the total to
**`920 passed, 1 deselected`**. The new test is one of the 921 that ran inside `make verify-offline`.

## The scope fence

`git diff --name-only 87871b4..HEAD` — two paths, and **not one under `boty/`, `scripts/` or
`served/`**:

```
.planning/phases/09-out-of-lockstep/09-DECISIONS.md
tests/test_pacing.py
```

## COVERAGE.md — asserted, not rewritten

`.planning/phases/09-out-of-lockstep/COVERAGE.md` **already existed**, tracked, written at planning
time by `4c18926`. `wc -l` = 1, and it carries its declaration line verbatim:

> No external API integration: this phase edits boty/pacing.py's and boty/cli.py's scheduling
> arithmetic and makes no live retailer request.

**This departs from Phase 8**, where `08-01` created that file. `09-01` asserted its content instead.
The departure is recorded in `09-DECISIONS.md` § *COVERAGE.md* rather than left as a discrepancy.

## What this plan does NOT claim

- **Criterion 5 is NOT discharged here.** No mutation was registered, none was observed CAUGHT, and
  **M43 is still free**. `grep -c "INTENTIONAL GAP" scripts/mutation_check.py` is still **8** and
  M21-M24 remain the intentional gap. The green `make verify-offline` above says the tree is still
  green with a new test in it — **a regression check**. It is not evidence for criterion 5.
- **No comparison and no reduction.** One number is stated. The thing it will be compared against
  does not exist yet, and the word *smaller* is 09-02's.
- **No tick value, no phase derivation, no `MIN_TICK_SECONDS`.** Only their bounds are recorded.
- **Criteria 1 and 2, all of criterion 4, and criterion 3's `after` half** are untouched.

## Deviations from Plan

**1. [Rule 2 - Missing critical functionality] The fleet assertion printed this machine's home directory**

- **Found during:** Task 1, while capturing the RED 2 transcript for `09-DECISIONS.md`.
- **Issue:** The three fleet assertions interpolated `_CONFIG`, a `Path` resolved from `__file__`, so
  a red transcript read `/home/<user>/.../config/products.yaml`. `scripts/identity_check.py` guards a
  public repository against exactly that shape — but it scans **tracked files**, and test *output* is
  not one. The leak arrives from the one direction the gate cannot see, and this plan was about to
  paste such a transcript into a planning document.
- **Fix:** Added `_CONFIG_SHOWN`, **derived** from `_CONFIG` (`"/".join(_CONFIG.parts[-2:])`) rather
  than written out, so the loader and the message cannot name different files. RED 2 was re-captured
  after the fix; the transcript in `09-DECISIONS.md` is the host-neutral one.
- **Files modified:** `tests/test_pacing.py`. **Commit:** `e1b099c`.

**2. [Rule 1 - Bug in this plan's own first draft] The test carried two copies of the fleet**

- **Found during:** Task 1, immediately after the first RED 2.
- **Issue:** The `Pacer` was constructed with a hand-written `overrides={"amazon": 1800, "gamestop":
  900}` while `_FLEET_INTERVALS` separately drove the assertions — **two statements of the fleet
  inside one test**, which is the "two copies only have to disagree once" defect `boty/pacing.py`
  argues against three times over. A table perturbation would have left the simulation running the
  old fleet.
- **Fix:** The `Pacer` now takes `overrides=dict(_FLEET_INTERVALS)` and `default_interval` from a
  named `_FLEET_DEFAULT_INTERVAL`, which is also the cycle step. RED 2 was re-run after the refactor
  and is the one recorded.
- **Files modified:** `tests/test_pacing.py`. **Commit:** `03e406c` (folded in before commit).

**3. [Recorded, deliberately NOT fixed] A stale count in production code**

- `boty/pacing.py`'s `state_path` paragraph reads *"There are nine in `tests/test_pacing.py` alone
  and not one names a path."* Exactly true at `46a0768` on 2026-08-10; now **25 of 27**. A genuine
  defect in a comment.
- **Not fixed here:** this plan's acceptance criteria assert the changed-file list by equality, and a
  production edit would poison the scope fence the before-number depends on. Recorded in
  `09-DECISIONS.md` and **handed to 09-02**, which is already editing that region.

**4. [Recorded, deliberately NOT fixed] The stale-`.pyc` trap belongs in `CLAUDE.md`**

- Same reason as above. Recorded in `09-DECISIONS.md` with its one-line fix and handed to a later
  wave.

**5. [Plan defect, worked around] The construction-site count the plan told this wave to state was already stale**

- Task 2's action instructs the executor to record **31 construction sites** (26 in
  `tests/test_pacing.py`, 24 naming no path) across **9 distinct call shapes**. That was measured
  before this plan ran. **09-01 adds one site — its own simulation's `Pacer`** — so the true figures
  at the end of this wave are **32 / 27 / 25-of-27 / 10 distinct call texts**.
- **Fix:** `09-DECISIONS.md` states the post-execution numbers, quotes the pre-execution ones beside
  them, and names this plan as what moved them. A wave that quotes 31 after this plan is quoting a
  pre-image of the tree it is standing in.

**6. [Measurement-method correction] "9 distinct call shapes" is not a count of API shapes**

- Measured by AST over every tracked `.py` file: **4** distinct *keyword signatures*, **10** distinct
  *normalised call texts*. The outline's 9 is the latter. Both are true of different questions;
  a reader taking 9/10 as a count of API shapes over-estimates how many ways `Pacer` is constructed.
  Recorded in `09-DECISIONS.md`; neither figure is edited away.

**7. [Plan defect, worked around] The `identity_check.py` verify command is missing its required flag**

- Task 2's `<verify>` gives `.venv/bin/python scripts/identity_check.py`, which exits **2** with
  `error: one of the arguments --staged --all is required`. **The same defect `08-01` recorded**, in
  the same position, one phase later. Ran `--all` instead: `identity check: PASS — 254 file(s), no
  host identity found`, exit 0.

**8. [Ownership ambiguity, flagged not resolved] Which wave owns criterion 4's budget and criterion 5**

- `09-01-PLAN.md` assigns criterion 5 to `09-04` and criterion 4 to `09-03`/`09-04`; the outline's
  plan table assigns the budget half and the final verdict to `09-05`. This document names the wave
  `09-01`'s own plan names, and says in `09-DECISIONS.md` § *Collision 8* that whichever wave
  actually owns it inherits the obligation rather than the number.

## Nothing live was touched

No live retailer request was made. **`boty check` was not run.** `make verify` — the unqualified
target with live controls — was deliberately not run. `state.json`, `pacer-state.json` and
`served/boty/status.json` were neither read nor written; the `duration_seconds: 20.43` figure is
**quoted** from the phase-8 record. No `systemctl restart boty`.

## STATE.md and ROADMAP.md were NOT updated

Deliberately, per this executor's instructions: the orchestrator owns those writes. **No `gsd-tools`
state or phase WRITE subcommand was invoked at any point** — `state.advance-plan`, `state.begin-phase`
and `phase.complete` are banned in this repo on fourteen recorded corruptions.

## Commits

| Commit | What |
|---|---|
| `03e406c` | `test(09-01): record the six-in-a-window the schedule is about to make unobtainable` |
| `e1b099c` | `test(09-01): keep the fleet assertion's failure message host-neutral` |
| `946f406` | `docs(09-01): settle eight collisions and three test collisions before any code moves` |
| `726c012` | `docs(09-01): record the stale-pyc trap that defeats this repo's red-watch protocol` |

Git identity checked **before** committing: `3347065+danieljamesjohnson@users.noreply.github.com`,
the repo's configured no-reply identity. **No commit used `--no-verify`**; the tracked pre-commit
identity hook passed on every one.

## Self-Check: PASSED

- `tests/test_pacing.py` — FOUND, carries `_ONE_DAY_OF_SECONDS` (7 occurrences), `_ONE_DAY_OF_CYCLES`
  (2) and the stated literal `max_in_any_60s == 6` (1, exactly once)
- `.planning/phases/09-out-of-lockstep/09-DECISIONS.md` — FOUND, `grep -c "^## "` = **17**, with
  `Collision 1`, `Collision 8`, `Test collision C` and the withdrawn `still tries once` all present
- `.planning/phases/09-out-of-lockstep/COVERAGE.md` — FOUND, `wc -l` = **1**, declaration line
  matched verbatim, tracked since `4c18926` (asserted, not rewritten)
- Commits `03e406c`, `e1b099c`, `946f406`, `726c012` — all FOUND in `git log`
- The before-number is consistent across all three artifacts: `== 6` in the test, "all SIX" in
  `09-DECISIONS.md` and in this summary
- Scope fence: `git diff --name-only 87871b4..HEAD` lists exactly two paths, neither under `boty/`,
  `scripts/` or `served/`
