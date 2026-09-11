---
phase: 09-out-of-lockstep
verified: 2026-09-11T13:28:39Z
status: gaps_found
score: 5/7 must-haves verified
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Criterion 1 — two retailers whose intervals coincide are NOT dispatched inside the same short window; the bound is a stated number of seconds, asserted on the schedule"
    status: partial
    reason: "The 50.0 s bound holds on due_at (the next-attempt position) and only there. At DISPATCH, under the loop's own ±15% jitter and due()'s half-tick (25 s) grace, two 300 s-cadence retailers are asked at the SAME wake: 17 times a day through cli.watch_loop at the suite's _IDLE_SEED (target+walmart 10, nintendo+target 7), 13–32 across 5 seeds, and 30 times on the criterion-1 test's OWN seed and stepping while that test passes. The closing record says MET AS WRITTEN. 09-02-SUMMARY already recorded 'two retailers 50 s apart on the schedule can occasionally be dispatched at the same wake', and 09-04 accepted '2 per wake' by pointing at the due_at assertion. Nobody noticed that the pair sharing the wake is a coinciding pair, which is the subject of criterion 1."
    artifacts:
      - path: "tests/test_pacing.py"
        issue: "test_two_retailers_at_one_cadence_are_separated_by_the_stated_number_of_seconds asserts on due_at only; no test asserts a dispatch-level separation for coinciding pairs"
      - path: "boty/pacing.py"
        issue: "loop_tick_seconds docstring calls a zero separation 'two retailers dispatched at the same instant ... exactly the coincidence this phase exists to remove', but its sweep's 50 s row is unjittered; under jitter the shipped row also dispatches a coinciding pair at one instant"
    missing:
      - "EITHER re-verdict criterion 1 as MET IN PART (ROADMAP closing record + 09-05 table, dated note beside, never over), naming the dispatch residual"
      - "OR a mechanism that stops two same-cadence retailers being asked at one wake, plus a cli.watch_loop-level test asserting the minimum dispatch gap for coinciding pairs, watched red first"
human_verification:
  - test: "Criterion 4b — a timed `boty check` pass on the phase-9 tree"
    expected: "duration_seconds < 120 (REQ-08). The only figure on record is 20.43 s, quoted from 2026-08-31, on a different tree"
    why_human: "boty check makes live retailer requests and writes the daemon's status.json. Prohibited here; running it is Dan's call"
warnings:
  - "Closing record reads '6 -> 2' and drops the jittered 3 that 09-02 and 09-05 recorded beside it"
  - "'2 is the arithmetic floor (6 x 60 > 300), so 1 was never available' is FALSE for the configured fleet: only four retailers are on 300 s. A schedule with max 1 and unchanged counts exists (measured). It is a floor only on the chosen 50 s grid. The claim appears in the closing record, boty/pacing.py loop_tick_seconds and tests/test_pacing.py _AFTER_MAX_IN_ANY_60S"
  - "Criterion 4a's watch_loop day test matches 48/96/288 at 1 of 21 seeds (its own). It has no denominator, and its 'day' is 1728 jittered wakes spanning 86107–86702 s. The equality depends on where one seed's last wake lands. This is the 2026-09-08 CI break with the host-timing cause removed"
---

# Phase 9: Out of Lockstep — Verification Report

**Goal:** The six retailers stop presenting as one coordinated crawler: independent schedules, so a single cycle does not fire six unrelated retailers inside one short window.
**Verified:** 2026-09-11, independently and late, because the phase closed without a verifier. **Status: gaps_found.** **Re-verification:** No.

**The goal as worded is met:** six-in-a-window is gone (at most 2 per wake, at most 3 per 60 s, measured through `cli.watch_loop`). **Criterion 1 as worded is not met**, and the closing record's MET AS WRITTEN overstates it. Everything else survived attack.

## Observable Truths

| # | Criterion | Status | Evidence (all taken by command on 2026-09-11) |
|---|---|---|---|
| 1 | Coinciding retailers not dispatched in one short window; bound stated in seconds, on the schedule | ✗ **FAILED as written (MET IN PART)** | `_MIN_SEPARATION_SECONDS = 50.0` is a hand-written literal. The pacer is built with `loop_tick_seconds`, but the bound is never recomputed from it. It is asserted on `due_at`, not a clock, and goes red when `slot_offset` returns 0 and when the advance re-anchors to `now`. **But** coinciding pairs are dispatched at the same wake: 17/day via `watch_loop` at `_IDLE_SEED`, 13–32 over 5 seeds, and 30 on the test's own seed while it passes. See the gap |
| 2 | Independence, both directions | ✓ VERIFIED | Two tests, each carrying a positive and a negative half, compared at every wake. **Red-watched independently:** leaking gamestop's interval into bestbuy reddens only the interval test; a refusal that bumps every retailer reddens only the backoff test |
| 3 | Max retailers in any 60 s window over a simulated day, stated, < 6 | ✓ VERIFIED (see warnings) | Test asserts `== 2` and `< _BEFORE_MAX_IN_ANY_60S` (6, transcribed from 09-01's red run at `87871b4`). Red with the tick at 300 s. **The test steps an unjittered tick. The daemon's loop measures 3** (20/20 pacer seeds, 5/5 `watch_loop` seeds). 3 < 6, so the criterion holds either way. The 3 is ungated |
| 4a | Per-retailer cadence and backoff ladder unchanged | ✓ VERIFIED (see warnings) | 13 named tests pass. Ladder literals are 600 / 21600 / 259200. Counts exact with the denominator asserted in the pacer-level test (1296 = 48+96+4×288). **CI fix is real:** with `_FROZEN_CLOCK` injected, 0/5/50/100 ms per `time.monotonic` call leaves the counts unchanged. An advancing injected clock reproduces `amazon: 49` |
| 4b | `boty check` inside 2 min, **re-measured** | ✗ **MET IN PART, correctly verdicted** | Not re-measured. The structural half holds: its 4 named tests pass. **Ordering confirmed:** collision 8 ("expected to land at MET IN PART") landed in `946f406` at 08:17, before the first code change (`1329d24`, 08:50) and before the 4b verdict (`76b1fab`, 11:03). Routed to human |
| 5 | verify-offline 0, new mutation CAUGHT | ✓ VERIFIED | `VERIFY: PASS (OFFLINE — live controls were NOT run…)`, EXIT 0. Identity check PASS over 276 files, **1038 passed / 0 skipped**, mypy clean over 18 files, **40/40 caught**, 0 survivors. **M43 CAUGHT, 5 tests failed.** Registered `ff3f5d3` 2026-09-01. M21–M24 absent |
| 6 | Standing invariants | ✓ VERIFIED | `current_interval` digest `6da39ac5…49108` is **identical at `a58e7ac` (pre-phase), `87871b4` and HEAD**. The span is 7994 chars / 8018 bytes, as corrected. `watch_loop` keeps `delay + cycle_duration`. MAX_BACKOFF 6 h, COOLOFF 259200, REFUSALS 30, STATE_VERSION 2, staleness grep = 2. `save()` key set identical to pre-phase: `refusals, refused_at, retailers, version, warned` |

**Score: 5/7** (4b not counted: MET IN PART).

## Closing-record claims tested

| Claim | Result |
|---|---|
| 457/1728 (26.4%) wakes ask nobody | **Reproduced exactly** through `watch_loop` at `_IDLE_SEED` |
| At most 2 retailers per wake | **Reproduced**, 5/5 seeds. They are coinciding pairs, which is gap 1 |
| "6 → 2" | 2 is the **unjittered** figure. The shipping loop gives **3**. 09-02/09-05 recorded that and the closing record dropped it |
| "2 is the arithmetic floor; 1 was never available" | **False.** Offsets 0/60/120/180 (the 300 s four), gamestop 240 mod 900, amazon 540 mod 1800 give max **1** under the suite's own `_max_in_any_window`, with counts 288×4/96/48 |
| 4b committed before the attempt | **True** (see row 4b) |
| Byte-unchanged `current_interval` | **True**, and against the pre-phase revision, not only against 09-02's literal |

## Warnings (not blocking the goal; blocking under this repo's record rule)

1. **4a's `watch_loop` gate is seed-pinned.** At 20 other seeds the counts read 287–289 / 48–49 / 96–97, tracking the span (86 107–86 702 s). That is the right cadence over the wrong "day". Any added `random` draw in the loop shifts the sequence and turns it red with no regression. Fix: cut the count on grid points or assert the span, as `born_apart_and_stay_apart` already does.
2. **Record corrections owed**, dated and placed beside the originals: the jittered 3 in the closing record; the false floor argument in three places; and the claim in the criterion-3 docstring that the test is "stepped the way `cli.watch_loop` … steps one", which is untrue for jitter.

## Human Verification

**1. Timed `boty check` (criterion 4b).** Run it with Dan's authorization and record `duration_seconds` against 120 s. Why human: it makes live requests and writes the daemon's `status.json`.

## Deployment is not evidence

Phase 9 is live since the 2026-09-11 restart. Per DoD item 2 that proves nothing about the schedule, and nothing above relies on it. The cool-off has never fired in production (refusals 10/18 against 30), so the ladder is proved offline only.

## Method and compliance

No live retailer request, no `boty check`, no `make verify`, no restart, no write to `state.json`/`pacer-state.json`/`status.json`, and no STATE.md, ROADMAP.md or gsd-tools write. Perturbations ran only in a `git archive HEAD` copy under the session scratchpad with bytecode writes off, restored and `cmp`-confirmed. Probes imported the suite's own fixtures and helpers. The only file written in the repo is this one.

---
_Verifier: Claude (gsd-verifier), 2026-09-11_
