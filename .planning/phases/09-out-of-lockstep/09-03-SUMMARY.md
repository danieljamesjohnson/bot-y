---
phase: 09-out-of-lockstep
plan: 03
subsystem: pacing
tags: [pacing, scheduling, lockstep, criterion-1, criterion-2, independence, REQ-23]

requires:
  - phase: 09-out-of-lockstep
    plan: 02
    provides: "the mechanism — a 50 s tick from one expression, a per-retailer slot offset, and a `record` that advances on the retailer's own grid — handed over green"
provides:
  - "Criterion 1: a separation of 50.0 s, written out by hand, asserted on the recorded schedule at birth and at every cycle of a simulated day, under the construction `cli.watch_loop` ships"
  - "Criterion 2: independence in both directions, two tests, each comparing every untouched retailer field by field at EVERY wake"
  - "Proof the loop sleeps the tick inside its jitter band, and that the tick the sleep uses is the tick the pacer was given"
  - "Both terms of `scheduled_now += delay + cycle_duration` observed defended, each removed in turn with its failing tests counted"
  - "The daemon's new wake and write rates as DERIVED numbers, before and after, for 09-04 to price"
affects: [09-04, 09-05]

actuals:
  tokens: 47000
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "A trajectory comparison rather than an end-state comparison, because a defect that heals before the run ends is invisible to the latter — measured, not feared"
    - "A bound stated as a written-out literal in seconds and asserted against the schedule's own record, never against elapsed time"

key-files:
  created: []
  modified:
    - tests/test_pacing.py
    - tests/test_cli_watch.py

key-decisions:
  - "Criterion 1's bound is 50.0 s, written out at `_MIN_SEPARATION_SECONDS` rather than computed from `loop_tick_seconds` at test time — a test that recomputes its expectation from the code under test asserts only that the code agrees with itself"
  - "Criterion 2 is TWO tests, one per direction, because the interval direction fails at `_standing_interval`/`slot_offset` and the backoff direction fails at `current_interval`/the refusal arm, and a combined test would name the wrong one"
  - "The negative half compares every untouched retailer at EVERY wake, not at the end of the run. The end-state form was measured BLIND to a fleet-wide refusal counter"
  - "No production code was touched. `git diff 653bc80..HEAD -- boty/ scripts/ config/ served/` is empty"

patterns-established:
  - "A predicted red that does not appear is a finding about the prediction: the pre-09-02 `now + wait` advance leaves BOTH criterion-2 tests green, so the red this plan was told to expect for them does not exist"

requirements-completed: []

status: complete
---

# Phase 9 Plan 03: Out of Lockstep — The Shape of the Schedule

Criterion 1's separation is **50.0 seconds**, written out by hand and asserted on the recorded
next-attempt times — never on a clock. Criterion 2 is asserted in **both directions, as two tests**,
each comparing every untouched retailer field by field at **every one of 400 wakes**. The loop is
proved to sleep the tick inside its jitter band, both terms of the pacer clock were observed
defended, and the daemon's new wake and write rates are written down as derived numbers.
`make verify-offline` exits 0. **No production code moved.**

## Criterion 1: the number, and how it is asserted

**50.0 seconds**, at `_MIN_SEPARATION_SECONDS` in `tests/test_pacing.py`.

**Where it comes from, stated in the comment so a reader checks it once rather than trusts it:** six
retailers on a 300 s global `interval_seconds` give `loop_tick_seconds` a 50 s tick, and
`slot_offset` lays the slots at `index * tick` modulo each retailer's own standing cadence — so the
four that share the 300 s cadence are born at 50, 150, 200 and 250 s and the closest pair of them is
50 s apart.

| | |
|---|---|
| Bound | `_MIN_SEPARATION_SECONDS = 50.0`, a written-out literal |
| Asserted as | `>=`, because criterion 1 states a bound ("at least") |
| Asserted against | `p._for(r).due_at` — the schedule's own record of the next attempt |
| Asserted when | at birth (before anything is recorded) **and** after every wake of a simulated day |
| Construction | `roster` + `tick`, the way `cli.watch_loop` builds one |
| Subject | only pairs whose STANDING intervals coincide, derived from `_FLEET_INTERVALS` |

**Written out rather than computed, for `_CADENCE_AFTER_N_REFUSALS`'s reason.** Computing the
expected separation from `loop_tick_seconds` at test time would make the assertion a re-derivation of
the code it checks. Written out, an edit to the tick expression or the slot arithmetic has to change
this number by hand — and that is the moment somebody notices the guaranteed separation moved.

**Nothing in the test reads a clock.** No `time.time()`, no `time.monotonic()`, no elapsed
subtraction; `grep` over the new sections returns only the sentence in the docstring saying so. The
wake times are jittered by ±15% per cycle and the schedule does not move at all, so a bound read off
elapsed time would be a bound on the sleep's randomness — and would pass on an idle host and flake on
a loaded one.

**The measured separation is exactly 50.0 at every cycle**, not merely at least 50.0. The gate is
`>=` deliberately: a future fleet with more room in it may exceed the bound without being a
regression, and a schedule that fell below it is the lockstep coming back.

**The defaulted construction is included and is explicitly NOT a second gate.** A `Pacer` with no
roster gives every retailer a 0.0 offset by design, so that case is the *absence* of the mechanism.
It is asserted `== 0.0` with a docstring saying what it does and does not prove — it shows which
behaviour comes from which field, and it is not evidence for criterion 1.

## Criterion 2: both directions, and the negative half asserted field by field

Two tests, each with its own failure message:

- `test_changing_one_retailers_interval_moves_that_retailers_schedule_and_no_other` — `gamestop`
  moved 900 s → 600 s. **600 rather than an arbitrary number:** its slot is 100 s, which is inside
  both 900 and 600, so its *birth position* is identical under either interval and the only thing
  the test changes is the advance.
- `test_driving_one_retailer_into_backoff_moves_that_retailers_schedule_and_no_other` — `gamestop`
  refuses at every dispatch.

Both build the shipping construction, step **400 wakes** of the loop's jittered tick from an
identical seed, and compare `(due_at, interval, refusals, refused_at)` for every retailer.

**Why two tests and not one:** they fail at different places — `_standing_interval` and `slot_offset`
for the interval direction, `current_interval` and the refusal arm for the backoff — and a combined
test would report whichever assertion happened to be written first.

**Why they are not `test_an_override_does_not_affect_other_retailers` again**, stated in the section
header rather than left for a reader to wonder: that test asserts DUENESS at a moment rather than the
recorded next-attempt time, never runs the same scenario *without* the override (so it cannot tell
"walmart was unaffected" from "walmart would have looked like that either way"), and builds the
defaulted construction. It is untouched — it guards the coverage half, which these do not.

### The negative half compares a TRAJECTORY, and that was a measured correction

The first form captured each retailer's state **once, at the end of the run**. Perturbing `record` to
increment *every* retailer's refusal count — a fleet-wide counter, precisely the leak the negative
half exists to catch — left **both tests GREEN**:

```
=== RED G: a FLEET-WIDE refusal counter (end-state form) ===
2 passed, 101 deselected in 0.11s
```

The untouched retailers are dispatched often enough that their own next `record(refused=False)`
resets the count to 0 before the run ends. **The defect was live for most of the simulated day and
invisible at the single moment the test read.** An end-state comparison is blind to anything that
heals. Rewritten to compare every wake, the same perturbation fires at wake 2. The measurement is
recorded in `_trajectory`'s own docstring so the next reader does not weaken it back.

## Every red, with its count

All eleven perturbations were applied to a copy-restored file with `__pycache__` and `.pytest_cache`
cleared **between perturbation and revert** — the trap `09-01` found and `09-02` used throughout.
`git diff` confirmed clean after each.

### Criterion 1

| # | Perturbation | Assertion that fired | Count |
|---|---|---|---|
| A | `slot_offset` returns 0.0 | **birth** — `bestbuy and nintendo … born 0.0 s apart … against the 50.0 s` | 1 failed, 100 deselected |
| B | grid advance dropped (`now + wait`) | **day-long** — `the closest two … came was 0.0 s (nintendo and target)` | 1 failed, 100 deselected (file: 8 failed, 93 passed) |

**RED B is stronger than the tracer's own result and worth recording as its own number.** On the
two-retailer tracer, `09-02` measured the offset-only mechanism *eroding* to 142.5 s against 150. On
the six-retailer fleet it does not erode — it **merges completely, to 0.0 s**, inside one simulated
day. The tracer under-states what the second term buys.

### Criterion 2

| # | Perturbation | Assertion that fired | Count |
|---|---|---|---|
| C | `_standing_interval` ignores overrides | interval **positive** — `its schedule did not move at any of the 400 wakes` | 1 failed, 1 passed |
| D | refusal arm uses `st.interval`, not `current_interval` | backoff **positive** — `assert 20800.0 > 20800.0` | 1 failed, 1 passed |
| E | a **shared cursor** (advance from the fleet's latest due time) | interval **negative** — `moved amazon as well: at wake 36 … (5700.0,…) -> (5400.0,…)` | 2 failed |
| G | a **fleet-wide refusal counter** | backoff **negative** — `moved amazon as well: at wake 2 … refusals 0 -> 1` | 1 failed, 1 passed |

**Under RED E the backoff test fails at its POSITIVE assertion**, before its negative half is
reached — so E is *not* evidence that the backoff direction's negative half binds. G is, and that is
why both are recorded rather than one.

### The red this plan was told to expect, and did not get — a finding

The plan states: *"The honest red for these is a mechanism that re-anchors on the cycle clock — the
pre-09-02 behaviour — under which a change to one retailer moves every retailer that fires in the
same tick."* Measured:

```
=== PREDICTED RED F: the pre-09-02 advance, now + wait ===
2 passed, 101 deselected in 0.12s
```

**Both criterion-2 tests stay green under the rule this phase removed, and the plan's sentence is
wrong.** The pre-09-02 rule merged retailers onto one *position*, which is what criterion 1 is about;
it did not make one retailer's next-attempt time a function of another's. Under `due_at = now + wait`
each retailer's next attempt is still determined by the wake clock and its own interval alone, and
the wake clock is identical between the two runs by construction. **Criterion 2's negative half has
no historical subject in `Pacer`** — its subject is a shared-anchor mechanism, which is what E and G
supply.

That is stated rather than smoothed over. The tests are not weaker for it: E and G are real defect
shapes (a shared cursor, a fleet-wide counter), both fire, and G caught a genuine weakness in this
plan's own first draft. But a reader should not be told these tests re-prove something the phase
fixed, because they do not.

### The loop, and both clock terms

| # | Perturbation | What failed | Count |
|---|---|---|---|
| H | `delay = cfg.interval_seconds * uniform(...)` (the cadence again) | both new loop tests — `wake 0 slept 290.301s, outside the [42.5, 57.5] band` | 2 failed, 47 passed |
| I | the pacer built without `roster` and `tick` | `…tolerance_are_one_number` — `handed its pacer roster None` | 1 failed, 48 passed |
| **J** | **`scheduled_now += delay`** (duration term removed) | **`test_the_pacer_clock_advances_by_the_time_the_check_pass_really_took`** | **1 failed, 48 passed** |
| **K** | **`scheduled_now += cycle_duration`** (delay term removed) | **`test_the_pacer_clock_is_still_deterministic_under_a_fake_sleep`** + 6 others | **7 failed, 42 passed** |

**Both terms are load-bearing and the two are not equally guarded, which is the finding here.** The
DURATION term is defended by **exactly one test and nothing else** — remove it and 48 tests still
pass. That single test is the whole of what stands between this tree and CR-01's measured 4.93 h of
drift per cool-off window. The DELAY term is over-determined: removing it reddens seven tests,
including five that have nothing to do with the clock and simply need it to advance under a fake
sleep.

RED I initially failed with a `KeyError` rather than an assertion. Fixed by reading through `.get`,
so a loop that stops passing those fields fails with the sentence that explains why it matters; the
perturbation was re-run against the fixed form and the message above is from that run.

## The loop really sleeps the tick

`test_the_loop_sleeps_the_tick_and_not_the_standing_cadence` runs `watch_loop` over a **six-retailer**
fixture with a capturing `sleep` and asserts every delay inside `[42.5, 57.5]` — the
`[0.85, 1.15]` band around a written-out `_FLEET_TICK_SECONDS = 50.0`.

**The band, never an exact value.** The jitter is deliberate (*"we do not hammer on a fixed cadence,
which is itself a signal"*) and a test pinning one delay would forbid the property it exists to
preserve. A second assertion states that the tick band cannot overlap the standing cadence's band
(`57.5 < 255`), because a test that only checks "the delay is inside a band" would pass with the band
moved.

**The fixture is six retailers on purpose.** `09-02` recorded that `loop_tick_seconds` returns the
standing interval for a one-retailer roster, so every other `watch_loop` fixture in
`tests/test_cli_watch.py` wakes at exactly the rate it woke at before REQ-23 — *"a regression sweep
built on single-retailer fixtures cannot fail for the reason it exists."* This fixture is the answer
to that finding.

`test_the_loops_tick_and_its_pacers_tolerance_are_one_number` captures the `Pacer` the loop builds
and asserts it carries the sorted configured roster and the same 50.0 s the sleeps are drawn around —
one expression read twice, rather than two numbers that happen to agree today.

## The daemon's new rates — DERIVED, not observed

Recorded in `tests/test_cli_watch.py` beside the tests, and here. **Derived** from the day-long
simulation and from counting the call sites in `watch_loop`; **nothing in this phase ran on the
wire.**

| per day, six retailers, `interval_seconds` 300 | before | after |
|---|---|---|
| loop wake-ups (86 400 / tick) | 288 | **1728** |
| `served/boty/status.json` writes (1 per cycle) | 288 | **1728** |
| `pacer-state.json` writes (1 per cycle) | 288 | **1728** |
| retailer requests | 1296 | **1296** |
| retailers asked per wake, mean | 4.5 | **0.75** |
| wakes that ask NOBODY | 0 | **432** |
| most retailers a single wake asks | 6 | **1** |

**The request count is the row that did not move, and it is the one the retailers can see.** What
rose six-fold is how often this process wakes, writes two files, and asks nobody: a quarter of all
wakes now dispatch no retailer at all, and a wake that dispatches anybody dispatches **exactly one**
in the unjittered schedule. Pricing that — collision 4's empty tick publishing a vacuously green
document, and collision 5's two failure counters that count *cycles* rather than time — is
**09-04's**, and these numbers exist so 09-04 prices a recorded fact.

**`boty` was not restarted and the daemon is still running the pre-REQ-23 schedule.** This is an
editable install, so the code is in the tree and the restart is the user's call.

## The gate

`make verify-offline`, nvm sourced first. **Real exit code 0.** Verdict line, verbatim:

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

The OFFLINE pass — **not INCOMPLETE**, so no control was reported unverifiable on this host.

| Stage | Reading |
|---|---|
| identity check | PASS — 256 file(s), no host identity found |
| lint (ruff) | All checks passed! |
| tests | **928 passed** in 11.67 s, `-rs` on, **no skip summary at all** |
| types (mypy) | Success: no issues found in 18 source files |
| fixtures | 11 fixture(s) |
| mutation | **38/38 mutations caught**, sandbox baseline 899 passed / 29 skipped |

| Measurement | Before this plan | After |
|---|---|---|
| Suite collected | 923 | **928** |
| `tests/test_pacing.py` | 100 | **103** |
| `tests/test_cli_watch.py` | 47 | **49** |

## What did NOT move

**No production code at all.** `git diff 653bc80..HEAD -- boty/ scripts/ config/ served/` is
**empty**, and `git diff --name-only 653bc80..HEAD` lists exactly `tests/test_pacing.py` and
`tests/test_cli_watch.py` — this plan's `files_modified`, by equality.

The standing prohibitions, by command:

```
$ grep -n "MAX_BACKOFF_SECONDS = \|COOLOFF_SECONDS = " boty/pacing.py
156:MAX_BACKOFF_SECONDS = 6 * 60 * 60
224:COOLOFF_SECONDS = 3 * 24 * 60 * 60
$ grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py
2
$ grep -n "^STATE_VERSION" boty/pacing.py
321:STATE_VERSION = 2
$ grep -n "scheduled_now += " boty/cli.py
771:        scheduled_now += delay + cycle_duration
$ grep -c "INTENTIONAL GAP" scripts/mutation_check.py
8
```

No new persisted field; `roster` and `tick` remain unpersisted `Pacer` fields. The phase derivation
still uses sorted position in the roster and nothing host-derived — `grep` for `hash(`, `getpid` and
`time.time()` in `boty/pacing.py` returns only prose about why `hash()` is refused, and the two
pre-existing `refused_at`/`load` wall-clock sites, none of them in the derivation.

### One prohibition I could NOT verify the way I was asked to, stated rather than claimed

I was told `Pacer.current_interval`'s body must stay byte-unchanged, with the recorded SHA-256
`6da39ac5…449108`. **I could not reproduce that digest** — four plausible extractions of the method
(full source segment, body statements, body without the docstring, raw lines) all hash to something
else, and `09-02` records the digest without its recipe.

**What is proved instead is strictly stronger and is proved by command:**
`git diff 653bc80..HEAD -- boty/` is empty, so `boty/pacing.py` is byte-identical to the tree 09-02
left. `current_interval`'s body is byte-unchanged by construction, whatever recipe produced that
digest. **The digest as recorded is not re-checkable without its extraction recipe**, and a later
wave should either record the recipe beside it or drop it in favour of the diff — a hash nobody can
recompute is a claim, not a check.

## What this plan does NOT claim

- **Criterion 5 is NOT discharged.** No mutation was registered and none observed CAUGHT. **M43 is
  still free**, and `grep -c "INTENTIONAL GAP"` is still **8**. `make verify-offline` here is a
  regression check and is described as one.
- **Criterion 3 is 09-02's** and is untouched.
- **Criterion 4 is untouched.** No `boty check` budget was measured.
- **The rates above are DERIVED, not observed.** Nothing was read from
  `served/boty/status.json`; the whole-pass `duration_seconds: 20.43` figure is not re-read here
  either.
- **The jitter sequences are seeded and are one sequence each**, not a proof over all of them. That
  is why every assertion reads the schedule, where the numbers are exact, rather than the wake times.

## Deviations from Plan

**1. [Finding] The plan's predicted red for criterion 2 does not exist**

Documented in full above. The pre-09-02 `now + wait` advance leaves both criterion-2 tests green.
Replaced with two perturbations that do have the negative half as their subject (a shared cursor, a
fleet-wide refusal counter), both watched red with counts.

**2. [Rule 1 — bug in this plan's own first draft] The negative half was blind to a defect that heals**

The end-of-run snapshot form passed under a fleet-wide refusal counter. Rewritten to compare every
wake; the measurement is kept in `_trajectory`'s docstring rather than fixed silently.

**3. [Rule 1 — bug in this plan's own first draft] A red that arrived as a `KeyError`**

`built[0]["roster"]` raised rather than asserting when the loop stopped passing the field. Changed
to `.get`, and the perturbation re-run so the recorded message is the one a reader would actually
see.

**4. [Rule 3 — blocking, trivial] An unused `type: ignore`**

`super().__init__(**kwargs)  # type: ignore[arg-type]` was unnecessary and mypy said so. Removed.
`tests/` is not in the `make types` target (mypy runs over `boty/` and `scripts/`), so this never
reached the gate; it was fixed anyway. **One pre-existing `unused-ignore` remains** at
`tests/test_cli_watch.py:1832`, outside this plan's scope and left alone.

**5. [Recorded, deliberately NOT fixed] The stale-`.pyc` trap still is not in `CLAUDE.md`**

Handed forward by 09-01 and again by 09-02; this plan's `files_modified` excludes `CLAUDE.md` too, so
it is handed forward a third time. **It was used on all eleven perturbations here**, several of which
were same-length edits reverted within the same wall-clock second.

## Nothing live was touched

No live retailer request. **`boty check` was not run.** `make verify` — the unqualified target with
live controls — was not run. `state.json`, `pacer-state.json` and `served/boty/status.json` were
neither read nor written. No `systemctl restart boty`.

## STATE.md and ROADMAP.md were NOT updated

Deliberately, per this executor's instructions: the orchestrator owns those writes. **No `gsd-tools`
state or phase WRITE subcommand was invoked at any point.**

## Commits

| Commit | What |
|---|---|
| `18134dc` | `test(09-03): state criterion 1's separation in seconds, on the schedule` |
| `c9e570d` | `test(09-03): assert criterion 2 in both directions, negative halves and all` |
| `fe7f209` | `test(09-03): prove the loop sleeps the tick, and record the daemon's new rates` |

Git identity checked **before** committing:
`3347065+danieljamesjohnson@users.noreply.github.com`, the repo's configured no-reply identity.
**No commit used `--no-verify`**; the tracked pre-commit identity hook passed on every one.

## Self-Check: PASSED

- `tests/test_pacing.py` — FOUND; contains `_MIN_SEPARATION_SECONDS = 50.0`, `_coinciding_pairs`,
  `_trajectory`, `roster`; **103 passed**
- `tests/test_cli_watch.py` — FOUND; contains `_FLEET_TICK_SECONDS = 50.0`, `fleet_cfg`,
  `cycle_duration`; **49 passed**
- Commits `18134dc`, `c9e570d`, `fe7f209` — all FOUND in `git log`
- `make verify-offline` — real exit code **0**, verdict line quoted above
- Scope fence: `git diff --name-only 653bc80..HEAD` lists exactly the two test files, by equality;
  the production diff is empty
