---
phase: 08-stop-knocking
verified: 2026-08-31T14:10:00Z
status: passed
# status was `human_needed` from 2026-08-31 until 2026-09-11. Both human items are now
# resolved and `08-UAT.md` is closed, so the frontmatter is advanced to match the record.
#
# IT IS NOT A CLEAN "BOTH PASSED", AND SAYING SO IS THE POINT. Item 1 — restart the daemon
# and confirm the cool-off is in force — is PASSED in its load-bearing half: the restart
# happened 2026-09-11 07:56:33, state migrated 13 -> 13 with zero lost, and the new code is
# proved live (status.json rewritten twice inside 70 s, where the pre-phase-9 loop wrote
# every ~300 s). The cool-off ITSELF is still unobserved on the wire: it needs 30 consecutive
# refusals and the live counts are amazon 10 / target 18. Recorded as unobserved, not claimed.
#
# Item 2 — look at a live cool-off row on the dashboard — is NOT OBSERVABLE and is counted as
# SKIPPED rather than passed. Best Buy's control is not being read at all (remembered row,
# checked=false, ~24 000 min old: the unrendered-shell problem), so there is no live row to
# look at. 2026-09-10's fix makes the monitor honest about that without making Best Buy
# readable, and those are different claims.
#
# So `passed` here means "no human item is outstanding", which is what the field gates. It
# does NOT mean every item was observed, and the two that were not are named above rather
# than absorbed into the word.
human_verification_resolved: 2026-09-11
score: 6/6 must-haves verified — 4 MET AS WRITTEN, 2 MET IN PART (criteria 2 and 5)
behavior_unverified: 0
overrides_applied: 0
requirements:
  - id: REQ-22
    status: satisfied
    scope: "in simulation, over the scheduler — which is what Definition of Done item 2 specifies. Not observed on the live daemon, deliberately."
cross_cutting_constraints:
  - constraint: "MAX_BACKOFF_SECONDS stays 6 hours"
    status: verified
    evidence: "boty/pacing.py:154 `MAX_BACKOFF_SECONDS = 6 * 60 * 60`; the surviving assertion `MAX_BACKOFF_SECONDS <= 6 * 60 * 60` still runs in tests/test_pacing.py"
  - constraint: "No second staleness rule — grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py stays 2"
    status: verified
    evidence: "measured 2026-08-31: 2 (lines 1052, 1089); both guard lines are byte-unchanged across 85a8d9f..HEAD"
  - constraint: "M42 is the only new ident, M21-M24 stay empty, INTENTIONAL GAP 7 -> 8"
    status: verified
    evidence: "grep -c 'ident=\"M' = 38; grep -c 'INTENTIONAL GAP' = 8; grep 'ident=\"M2[1234]\"' = 0 hits; grep 'ident=\"M42\"' = 1 hit"
  - constraint: "No live retailer request, no `boty check`, no write to state.json / pacer-state.json / served/boty/status.json"
    status: verified_as_written_partial_on_the_stricter_plan_claim
    evidence: "control check: SKIPPED (--offline) — no live retailer request made. All three files are gitignored and absent from `git diff --name-only 85a8d9f..HEAD`; every pacer-state.json in the phase's tests is under tmp_path. The ROADMAP constraint is about WRITES and is intact. The plans' stricter wording — 'neither read nor written' — no longer holds phase-wide: the post-plan CR-01 investigation READ served/boty/status.json to obtain `duration_seconds: 20.43`."
  - constraint: "The recorded one-wave gap between waves 2 and 3 is closed"
    status: verified
    evidence: "STATE_MAX_AGE_SECONDS = LONGEST_WAIT_SECONDS = max(MAX_BACKOFF_SECONDS, COOLOFF_SECONDS) = 259200; test_a_refusal_record_is_restored_across_the_whole_staleness_window's 21601.0 row passes"
warnings:
  - id: WV-01
    severity: warning
    statement: "Criterion 5's row in the phase's closing verdict table (08-04-SUMMARY.md:574) still reads MET AS WRITTEN with no note beside it, although CR-01 later established by measurement that the guarantee it asserted had a systematic hole in production at the moment it was written."
    mitigating: "The correction IS in the tree in five places — boty/pacing.py:428-467, 08-03-SUMMARY.md:46 and :250, scripts/mutation_check.py:1671, CLAUDE.md, and 08-REVIEW.md § Resolution — and is reachable from the row via the plan it cites (08-03). What is missing is the note beside the verdict word itself."
    remedy: "One dated line beside row 5, in the form docs/retailer-evidence.md § 6 prescribes. No code change."
  - id: WV-02
    severity: warning
    statement: "scripts/mutation_check.py:1710 still reads '**14 test(s) failed**' for M42's kill set; the measured figure today is 16."
    mitigating: "The 14 -> 16 re-measurement IS present in the same comment block at lines 1671-1687, and the '14' is explicitly scoped to the run that registered the ident. The only defect is reading order — the correction precedes the claim it corrects rather than sitting beside it."
  - id: WV-03
    severity: warning
    statement: "Planning records are stale and say the phase is unexecuted."
    detail: "ROADMAP.md:116,120,124,128 — all four plan lines are still unchecked `- [ ]` and annotated '(PLAN written 2026-08-28, not executed)'. STATE.md:98 still reads 'NEXT ACTION is executing phase 8'. All four plans have SUMMARYs and their commits are in the tree."
    note: "Orchestrator-owned. Not modified by this verifier, per instruction and per this repo's gsd-tools write ban."
human_verification:
  - test: "Decide whether to `sudo systemctl restart boty`, and then confirm the cool-off is actually in force on the daemon."
    expected: "After a restart the daemon runs this working tree (editable install). A retailer past 30 consecutive refusals should publish `current_interval_seconds: 259200` and a `skipped_reason` of the form 'cooling off after N refusal(s) — next attempt in ~X days'. Until a restart happens the daemon is executing the PRE-phase rule and this phase has no effect on the wire."
    why_human: "A restart is Dan's call, not the agent's (CLAUDE.md), and the ROADMAP's own cross-cutting constraint forbids `systemctl restart boty` anywhere in this phase. The phase is complete IN THE TREE and is not deployed; those are two different claims."
  - test: "Look at the live dashboard once the daemon is restarted and a retailer is genuinely in cool-off."
    expected: "The row reads `72h` for the cadence, and the `ageTag` comparison reads e.g. `73h ago > 72h` rather than an apparent equality."
    why_human: "served/boty/index.html was deliberately not edited by this phase (Collision B, decided against four measured JS strings). Nothing in the test suite pins fmtDur's rendered output to skipped_reason's string — measured: `grep -rn 5400 tests/` finds it only in tests/test_dashboard.py. Whether the rendered row reads well is a visual judgement no gate can take."
---

# Phase 8: Stop Knocking — Verification Report

**Phase Goal:** *"A retailer that has refused 30-odd times in a row stops being asked twice a day, so the footprint that earns and sustains a block shrinks."*
**Verified:** 2026-08-31
**Status:** human_needed
**Re-verification:** No — initial verification
**Verifier's stance:** every number below was produced by a command run during this verification. Nothing is transcribed from a SUMMARY without being re-measured, and where my measurement differs from the record I say so and say which direction.

---

## Goal Achievement

The goal is achieved **in the tree** and is **not on the wire**. Those are two different claims and this report makes the first one.

A retailer that has refused 30 times consecutively now waits 259 200 s (three days) instead of 21 600 s (six hours), and over a simulated 30 days it is asked **37** times where the old rule asked **125** — a 70.4% reduction in the request footprint, measured over the same 8 640-cycle window, same retailer, same cadence, same counting idiom, with exactly one thing different: the rule.

---

## Observable Truths — the six ROADMAP Success Criteria

| # | Truth | Status | Verdict | Evidence (measured during this verification) |
|---|-------|--------|---------|----------------------------------------------|
| 1 | After a bounded number of consecutive refusals the wait is measured in **days**, asserted against literal expected seconds | ✓ VERIFIED | **MET AS WRITTEN** | `_CADENCE_ACROSS_THE_COOLOFF_THRESHOLD` — six hand-written rows. At 29 refusals `current_interval` returns `21600.0` on both a 300.0 and an 1800.0 standing interval; at 30 and at 31 it returns `259200.0` on both. Ran `test_the_cadence_across_the_cooloff_threshold_is_the_literal_it_is` — 6 rows pass. Literals, not derivations: `COOLOFF_SECONDS` appears nowhere in the table. `==` and not `pytest.approx`, which is correct because past the threshold the `st.interval * BACKOFF_FACTOR ** st.refusals` sub-expression is never evaluated — confirmed by reading `current_interval`'s conditional at pacing.py:858-866. |
| 2 | A retailer in cool-off is requested **exactly once** when the cool-off expires, asserted over a simulated sequence of cycles | ✓ VERIFIED | **MET IN PART** — as written *within a running process*; a restart costs one extra probe | Ran `test_a_retailer_in_cooloff_is_probed_exactly_once_when_it_expires`: **1** probe over 1 000 simulated 300 s cycles (300 000 s — longer than one window, shorter than two, so "exactly once" is bounded in both directions). The repo's own `if p.due(...): count += 1; p.record(...)` idiom over a plain float `now`; no clock library, no monkeypatched time. The restart scope is not a discovered caveat — `08-DECISIONS.md § Collision 2` priced it in advance at one request per restart because `due_at` is deliberately unpersisted, and `test_a_restart_mid_cooloff_is_probed_exactly_once_over_a_whole_window` then **measured** it at 1 probe over 864 cycles. |
| 3 | The 30-day request count against a never-recovering retailer is a **stated number**, strictly smaller than under the old rule; **both numbers recorded** | ✓ VERIFIED | **MET AS WRITTEN**, in **simulation** | Ran `test_the_thirty_day_request_count_under_the_cooloff_is_a_stated_number`. **After = 37**, asserted live. **Before = 125**, recorded as a dated withdrawn literal in the docstring with its date (2026-08-27), its command, and its revision (`85a8d9f`). The strict comparison is a live assertion (`len(offsets) < 125`). The denominator is asserted, not assumed (`now == 2592000.0`), and two independent tallies agree (`offsets` vs `Pacer.refusals`). **The honest scope:** the before-number is a RECORD, not a re-runnable assertion — the rule it measured no longer exists. Criterion 3 asks for both numbers *recorded*, and both are. |
| 4 | A retailer that answers during its probe returns to normal cadence **immediately** and the cool-off state is cleared | ✓ VERIFIED | **MET AS WRITTEN**, with one thinness carried forward rather than hidden | Ran `test_a_retailer_that_answers_during_its_probe_is_back_on_its_standing_interval_at_once`. Asserted at cool-off depth (setup gate: `current_interval == 259200.0` before the good read), then three assertions after it — the field (`refusals == 0`), the accessor (`current_interval == 1800.0`) and the schedule (`due_at == 1800.0`). **The thinness, restated because it is a fact about the evidence:** what 08-02 recorded as watched-red is the *setup* assertion, not the recovery assertion — so what was observed failing is that the test cannot pass vacuously at the wrong depth, not the recovery clause itself. |
| 5 | The cool-off **survives a restart**, the same guarantee the backoff carries, and is discarded when stale by the **existing** rule rather than a second one | ✓ VERIFIED (today) | **MET IN PART** — see the extended finding below | Both clauses verified. **Survival:** `_RESTORE_ACROSS_THE_STALENESS_WINDOW`, five hand-written rows, all pass — including the `21601.0` row that is the red-before/green-after transition, and the `-1.0` row proving the bound is still two-sided. **No second rule:** `grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py` = **2**, and both guard lines (1052, 1089) are byte-unchanged across the whole phase diff. `STATE_MAX_AGE_SECONDS = LONGEST_WAIT_SECONDS = max(MAX_BACKOFF_SECONDS, COOLOFF_SECONDS)` — the expression, not its current winner. **Why MET IN PART and not MET AS WRITTEN: below.** |
| 6 | `make verify-offline` exits 0, with at least one new mutation registered, observed CAUGHT, anchored on **behaviour** | ✓ VERIFIED | **MET AS WRITTEN**, with the localisation finding carried | Ran it myself. **EXIT 0.** Verdict line, verbatim: `VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)`. `mutation check: 38/38 mutations caught`, survivors **0**. `CAUGHT M42 boty/pacing.py: 16 test(s) failed`. M42's anchor is `"            if st.refusals >= REFUSALS_BEFORE_COOLOFF\n"` and its replace is `"            if False\n"` — a source line whose removal changes *when a request is made*; no message text, no rendered tag, no docstring fragment, no version literal. |

**Score: 6/6 truths verified — 4 MET AS WRITTEN, 2 MET IN PART.**

Nothing in this table is rounded up. MET IN PART is a shippable outcome in this repository and appears twice on its merits.

---

## Criterion 5, at length — because the phase's own closing record and the code review disagree about it

This is the one criterion where the honest verdict is not the one the phase closed on, so the reasoning is written out rather than compressed into a table cell.

### What the phase recorded

`08-04-SUMMARY.md:574` records criterion 5 as **MET AS WRITTEN**, evidenced by the one-line re-derivation `STATE_MAX_AGE_SECONDS: 21600 -> 259200`, five gates watched red, and the guard-site count of 2.

### What the code review then established

`08-REVIEW.md` CR-01 found that the guarantee had a hole the tests could not see. `refused_at` is stamped from wall clock; `due_at` is computed in `watch_loop`'s synthetic `scheduled_now`; `Pacer.load` compares wall against wall. `scheduled_now` advanced by the sleep delay **and never by what a check pass cost**, so the two clocks drifted apart monotonically and in one direction. Because REQ-22 made `STATE_MAX_AGE_SECONDS` and `COOLOFF_SECONDS` deliberately *equal*, there was no slack to absorb it: a restart landing in the drift window dropped the entry, the retailer returned at 0 refusals, and it had to climb the backoff and re-earn thirty consecutive refusals — REQ-22's result undone by REQ-22's persistence layer.

### I reproduced both halves rather than reading them

Simulating `watch_loop`'s clock arithmetic against wall clock over one whole cool-off window, 200 seeds, including `Pacer.due`'s 150 s half-interval tolerance:

```
                       mean residual              worst residual
pre-fix,  dur= 0.00s      -6.2s  (-0.002%)         164.4s (0.063%)
pre-fix,  dur=20.43s   17646.0s  ( 6.808%)       17892.1s (6.903%)
pre-fix,  dur=27.61s   23849.8s  ( 9.201%)       24153.0s (9.318%)
post-fix, dur=20.43s      20.3s  ( 0.008%)         191.6s (0.074%)
post-fix, dur=27.61s      20.0s  ( 0.008%)         220.1s (0.085%)
```

- The recorded pre-fix figure is **6.84%** at the live `duration_seconds: 20.43`. I measure **6.81%**. Reproduced.
- The review's alternate framing is **9.24%** at 27.61 s. I measure **9.20%**. Reproduced.
- Jitter alone (duration held at zero) is a random walk about zero, mean −6.2 s. **The originally recorded mechanism does not bite.** Reproduced.
- The post-fix residual I measure is **smaller** than the tree records (mean 20.3 s vs 151 s; worst 191.6 s vs 346 s). The difference is exactly `due`'s 150 s tolerance, which the tree's simulation omits. **The recorded figure is therefore conservative — larger than the real residual, not smaller.** It is not rounded up, which is the direction that matters here.

### The fix is real and is gated

`boty/cli.py:742` now reads `scheduled_now += delay + cycle_duration`, with `cycle_duration` read *before* the sleep and `cycle_started` stamped *before* the `try` so a raising cycle still pays. Two gates, both run and both passing:

- `test_the_pacer_clock_advances_by_the_time_the_check_pass_really_took` — injects a cycle that sleeps for real 0.05 s and asserts the clock advanced by at least `delay + 0.04`. This is a behavioural gate, not a presence check.
- `test_the_pacer_clock_is_still_deterministic_under_a_fake_sleep` — the guard that stops the shorter, wrong fix (`+= time.monotonic() - cycle_started`), which the record measures at 7 failing tests.

`LONGEST_WAIT_SECONDS` is deliberately **unchanged**: the drift was a defect in the clock, not a property of the policy, and widening the window would have hidden it at every other retailer's expense. The superseded paragraph in `boty/pacing.py:414-426` is kept **unedited** with the correction recorded beside it at 428-467, which is `docs/retailer-evidence.md` § 6's convention applied correctly.

### The verdict, and why it is MET IN PART

1. **The code satisfies criterion 5 today.** Both clauses verified, behaviourally, by tests I ran and by a simulation I wrote.
2. **A bounded residual remains, by design.** `STATE_MAX_AGE_SECONDS == COOLOFF_SECONDS`, so there is no slack, and a restart landing inside one cycle boundary of the probe still drops the entry. That residual is measured, recorded, and — importantly — is *the same residual the existing backoff always carried*, since the old derivation set the window equal to the cap for the same reason. So "the same guarantee the existing backoff already carries" is literally true, residual and all. That is the clause the criterion actually asks for.
3. **It was not true when the phase said it was.** At the moment `08-04-SUMMARY.md` recorded MET AS WRITTEN, the guarantee failed for ~6.8% of every cool-off window on this host, against a retailer (`target`, at 46 refusals that day) that was actually past the threshold. That is a fact about the phase's own record, and it is why the verdict is MET IN PART rather than MET AS WRITTEN.

**This is not a code gap and does not block the next phase.** It is a records finding — WV-01 below.

---

## Required Artifacts

| Artifact | Expected | Status | Details (measured) |
|---|---|---|---|
| `boty/pacing.py` | `REFUSALS_BEFORE_COOLOFF = 30` | ✓ VERIFIED | line 192 |
| `boty/pacing.py` | `COOLOFF_SECONDS = 3 * 24 * 60 * 60` | ✓ VERIFIED | line 222, = 259 200 |
| `boty/pacing.py` | cool-off branch INSIDE the existing `max(...)` in `current_interval` | ✓ VERIFIED | `return max(st.interval, COOLOFF_SECONDS if st.refusals >= REFUSALS_BEFORE_COOLOFF else min(...))` — one expression, so `record` and `cli._current_intervals` cannot diverge |
| `boty/pacing.py` | `LONGEST_WAIT_SECONDS`, and `STATE_MAX_AGE_SECONDS` re-derived from it | ✓ VERIFIED | lines 347, 473. The diff shows exactly `-STATE_MAX_AGE_SECONDS = MAX_BACKOFF_SECONDS` / `+STATE_MAX_AGE_SECONDS = LONGEST_WAIT_SECONDS` |
| `boty/pacing.py` | cool-off arm in `skipped_reason`, derived from the schedule | ✓ VERIFIED | lines 925-934. Guarded on `self.current_interval(retailer) == COOLOFF_SECONDS and st.refusals >= ...` — the WR-01 fix, so the label can no longer name a cause the code did not establish |
| `boty/pacing.py` | days/hours fallback in the cool-off label | ✓ VERIFIED | `f"~{remaining/86400:.1f} days" if remaining >= 0.05*86400 else f"~{remaining/3600:.1f} hours"` — the WR-03 fix |
| `boty/cli.py` | `watch_loop` charges the clock for the cycle's own cost | ✓ VERIFIED | line 742, `scheduled_now += delay + cycle_duration` — the CR-01 fix |
| `tests/test_pacing.py` | `_CADENCE_ACROSS_THE_COOLOFF_THRESHOLD` | ✓ VERIFIED | line 766, 6 hand-written rows |
| `tests/test_pacing.py` | `_RESTORE_ACROSS_THE_STALENESS_WINDOW` | ✓ VERIFIED | line 1324, 5 rows, both sides of the window pinned at the step |
| `tests/test_pacing.py` | `_THIRTY_DAYS_OF_CYCLES` and the both-numbers test | ✓ VERIFIED | lines 243, 246 |
| `tests/test_cli_watch.py` | the cool-off-depth end-to-end tracer | ✓ VERIFIED | line 801, asserts `_published_cadence(cfg) == 259200.0` off the **written bytes** of status.json, plus `checked is False` and `due_at == 259200.0` |
| `tests/test_cli_watch.py` | the two clock gates | ✓ VERIFIED | lines 1715, 1777 |
| `scripts/mutation_check.py` | `ident="M42"` on the cool-off branch, 8th INTENTIONAL GAP | ✓ VERIFIED | line 1727; `grep -c "INTENTIONAL GAP"` = 8 |
| `.planning/.../08-DECISIONS.md` | Collisions 1, 2, A, B, C, D settled in writing | ✓ VERIFIED | Collision B answered against four measured JS strings under node v24.16.0, not against an intuition |

---

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `Pacer.current_interval` | `Pacer.record`'s `due_at` | `record` computes its wait THROUGH the accessor | ✓ WIRED | `test_a_retailer_in_cooloff_publishes_the_days_scale_cadence_it_is_actually_on` asserts `pacer._for("gamestop").due_at == 259200.0` |
| `Pacer.current_interval` | `cli._current_intervals` -> `status.write`'s `current_interval_seconds` | one expression reaching both surfaces | ✓ WIRED | same test — `_published_cadence(cfg) == 259200.0`, read **off the written bytes** of status.json, not off a returned object. Ran it: passes |
| `boty/cli.py watch_loop`'s clock | `Pacer.load`'s `STATE_MAX_AGE_SECONDS` bound | `scheduled_now` -> `due_at` vs wall-clock `refused_at` | ✓ WIRED (this is the link CR-01 found broken) | `test_the_pacer_clock_advances_by_the_time_the_check_pass_really_took` — a real-sleeping cycle, asserted behaviourally. Ran it: passes |
| `STATE_MAX_AGE_SECONDS` | `Pacer.load`'s **two** guard sites | one constant read by both the refusal counts and the paging memory | ✓ WIRED, and still exactly two | lines 1052 and 1089, byte-unchanged; `test_one_load_restores_the_count_and_the_paging_memory_together` passes |
| `LONGEST_WAIT_SECONDS` | `current_interval`'s two wait arms | `max(MAX_BACKOFF_SECONDS, COOLOFF_SECONDS)` — the expression, not its winner | ✓ WIRED | `test_the_age_out_is_derived_from_the_longest_wait_the_module_can_produce` passes |
| `Pacer.skipped_reason` | `Pacer.current_interval` | the label is derived, no longer a second copy of the rule | ✓ WIRED (WR-01 fix) | `test_a_standing_interval_above_the_cooloff_is_not_published_as_a_penalty` passes |

---

## Data-Flow Trace (Level 4)

| Artifact | Value | Source | Produces real data | Status |
|---|---|---|---|---|
| `served/boty/status.json` `current_interval_seconds` | 259200.0 at cool-off depth | `cli._current_intervals` -> `Pacer.current_interval` | ✓ — asserted off written bytes in the tracer | ✓ FLOWING |
| `served/boty/status.json` `skipped_reason` | "cooling off after N refusal(s) — next attempt in ~X days\|hours" | `Pacer.skipped_reason`, guarded on `current_interval` | ✓ | ✓ FLOWING |
| `served/boty/index.html` `fmtDur` render | `72h` | status.json's cadence | ✓ — measured under node v24.16.0 (Collision B) | ✓ FLOWING; the *rendered page* at cool-off depth is a human item |
| `pacer-state.json` `refusals` / `refused_at` | restored depth at cool-off age | `Pacer.save` / `Pacer.load` | ✓ | ✓ FLOWING |

---

## Behavioural Spot-Checks (run during this verification)

| Behaviour | Command | Result | Status |
|---|---|---|---|
| The whole gate | `make verify-offline` (nvm sourced) | **EXIT 0**; `VERIFY: PASS (OFFLINE — live controls were NOT run…)` | ✓ PASS |
| Suite | (same run) | **920 passed**, **0 skipped** — `tests/test_dashboard.py` BINDING, not skipping | ✓ PASS |
| Identity | (same run) | `identity check: PASS — 243 file(s), no host identity found` | ✓ PASS |
| Types | (same run) | `Success: no issues found in 18 source files` | ✓ PASS |
| Mutation | (same run) | `mutation check: 38/38 mutations caught`, survivors **0** | ✓ PASS |
| M42 | (same run) | `CAUGHT M42 boty/pacing.py: 16 test(s) failed` | ✓ PASS |
| Live controls | (same run) | `control check: SKIPPED (--offline) — no live retailer request made.` | ✓ (constraint held) |
| Criteria 1-6 named tests | `.venv/bin/python -m pytest <12 named tests> -q` | **21 passed** (parametrised rows expand) | ✓ PASS |
| Cool-off end-to-end tracer | `pytest ...::test_a_retailer_in_cooloff_publishes_the_days_scale_cadence_it_is_actually_on` | 1 passed | ✓ PASS |
| Cross-surface tracer | `pytest ...::test_both_surfaces_publish_one_cadence_from_one_document` | 1 passed | ✓ PASS |
| CR-01 residual, independently simulated | `/tmp/residual_sim.py`, 200 seeds | pre-fix 6.81% @ 20.43 s, 9.20% @ 27.61 s; post-fix 0.008% mean / 0.074% worst | ✓ REPRODUCED |

**Measured deltas against the record, both stated rather than absorbed:**

- **Identity file count: 243 today vs 242 in `08-REVIEW.md` § Resolution.** Cause established, not guessed: `git ls-tree -r --name-only 0a67bf7^ \| wc -l` = 243 and at `0a67bf7` = 244, so the +1 is exactly `08-REVIEW.md` itself. The Resolution's gate run predates that file being tracked. Nothing else was added.
- **M42's kill set: 16 today vs 14 at registration.** The re-measurement is already in the tree (`scripts/mutation_check.py:1671-1687`, `08-04-SUMMARY.md:255`) and my figure matches it. The three review tests are the cause; two of them land in M42's set.

---

## Requirements Coverage

| Requirement | Source plan | Clause | Status | Evidence |
|---|---|---|---|---|
| REQ-22 | 08-01…08-04 | "after a bounded number of consecutive refusals the monitor stops requesting that retailer for a period measured in **days**" | ✓ SATISFIED | `REFUSALS_BEFORE_COOLOFF = 30`, `COOLOFF_SECONDS = 259200` (3 days), asserted against literals at 29/30/31 on two standing intervals |
| REQ-22 | 08-02 | "then probes **once**" | ✓ SATISFIED | 1 probe over 1 000 simulated cycles; 1 probe over a whole window after a restart |
| REQ-22 | 08-02 | "the fixed 6-hour ceiling applied indefinitely is replaced" | ✓ SATISFIED | The ceiling's **value** is untouched (`MAX_BACKOFF_SECONDS = 6 * 60 * 60`, and the `<= 6 * 60 * 60` assertion still runs); what is replaced is its indefinite application |
| REQ-22 | 08-01/08-02 | "the replacement is **proved** to reduce the request count against a retailer that never recovers" | ✓ SATISFIED, in simulation | 125 -> 37 over the same 8 640-cycle window; the strict comparison is a live assertion; the denominator is asserted |

**Definition of Done item 2** — *"REQ-22 … proved by offline tests over the scheduler, not by observing the live daemon"* — ✓ SATISFIED, and satisfied in the strong sense: no live retailer request was made anywhere in this phase or in this verification.

**Orphaned requirements:** none. `.planning/REQUIREMENTS.md` maps only REQ-22 to this phase, and every plan declares it.

---

## Anti-Patterns Found

| File | Pattern | Result |
|---|---|---|
| `boty/cli.py`, `boty/monitor.py`, `boty/pacing.py`, `scripts/mutation_check.py`, `tests/test_pacing.py`, `tests/test_cli_watch.py`, `tests/test_monitor.py` | `TBD` / `FIXME` / `XXX` | **0 matches** — the debt-marker gate is clean |
| same | `TODO` / `HACK` / `PLACEHOLDER` | **0 matches** |
| same | writes to `state.json` / `pacer-state.json` / `served/boty/status.json` outside `tmp_path` | **0** — every occurrence in the phase diff is either a `tmp_path` fixture or a comment quoting a *read* |

**No blockers. No stubs.** The production surface this phase moved is unusually small — two new constants, one derived constant, one re-derivation, one conditional inside an existing `max`, one arm in `skipped_reason`, and one `+ cycle_duration` in `watch_loop`. Everything else is tests and argued comments.

---

## Warnings

### WV-01 — Criterion 5's closing verdict has no note beside it (WARNING)

`08-04-SUMMARY.md:574` still reads **MET AS WRITTEN**, unqualified as to CR-01. The correction is in the tree in five places and is reachable from the row via the plan the row itself cites (`08-03`, whose SUMMARY carries the supersession at :46 and :250). What is missing is the note beside the *verdict word* — and the verdict table is, by 08-04's own description, "the one document in this phase whose only content is claims".

**Remedy:** one dated line beside row 5, in the § 6 form. No code change. This does not block Phase 9.

### WV-02 — M42's registration-run kill set reads 14; today it is 16 (WARNING, cosmetic)

`scripts/mutation_check.py:1710`. The 14 -> 16 correction is present at 1671-1687 in the same block, but it *precedes* the claim it corrects. Reading order only; the substance is recorded and my measurement matches it.

### WV-03 — The planning records still say the phase is unexecuted (WARNING, orchestrator-owned)

- `ROADMAP.md:116,120,124,128` — all four plan lines are `- [ ]` and annotated *"(PLAN written 2026-08-28, not executed)"*. All four executed; all four have SUMMARYs; the commits are in the tree.
- `STATE.md:98` — `stopped_at` still reads *"NEXT ACTION is executing phase 8"*.

Not modified by this verifier: the instruction forbids it, and this repo bans `gsd-tools` state/phase writes outright (fourteen recorded corruptions). **The orchestrator must close these before marking the phase complete.**

### WV-04 — A narrowing of the plans' "neither read nor written" claim (INFO)

`08-03` and `08-04` claim `state.json`, `pacer-state.json` and `served/boty/status.json` were *"neither read nor written"*. That held for the four plans. It no longer holds phase-wide: the post-plan CR-01 investigation **read** `served/boty/status.json` to obtain `duration_seconds: 20.43`, which is how the defect got a real magnitude instead of an argued one. The ROADMAP's cross-cutting constraint is about **writes** and is fully intact. Recorded because it is a difference between two records, and reading the live file was the right call.

---

## Human Verification Required

### 1. Restart the daemon — or decide not to

**Test:** `sudo systemctl restart boty`, then read `served/boty/status.json` for a retailer past the threshold.
**Expected:** `current_interval_seconds: 259200` and a `skipped_reason` of the form `cooling off after N refusal(s) — next attempt in ~X days`.
**Why human:** a restart is Dan's call, and the ROADMAP's own cross-cutting constraint forbids one anywhere in this phase. **Until it happens, the daemon runs the pre-phase rule and nothing in this phase is on the wire.** `boty` is an editable install, so the restart is the whole of the deployment. Copy `state.json`, `pacer-state.json` and `served/boty/status.json` first — the state document migrates shape on load.

### 2. Look at a cool-off row on the live dashboard

**Test:** once a retailer is genuinely in cool-off, open the dashboard and read its row.
**Expected:** cadence renders `72h`; the `ageTag` comparison reads `73h ago > 72h` rather than an apparent equality.
**Why human:** `served/boty/index.html` was deliberately not edited (Collision B, decided against four measured JS strings), and **nothing in the suite pins `fmtDur`'s rendered output to `skipped_reason`'s string**. Whether the row reads well is a visual judgement no gate here can take.

---

## Gaps Summary

**There are no gaps in the code.** All six ROADMAP success criteria are satisfied by the tree as it stands, all five cross-cutting constraints hold under direct measurement, REQ-22 is satisfied in the manner its own Definition of Done specifies, and `make verify-offline` exits 0 on this working tree with 920 passed, 0 skipped and 38/38 mutations caught — measured by this verifier, not transcribed.

**The status is `human_needed`, not `passed`, for two reasons and neither is a defect:**

1. The phase is **complete in the tree and not deployed**, by the ROADMAP's own design. The goal sentence — *"a retailer that has refused 30-odd times in a row stops being asked twice a day"* — is true of the code and false of the running daemon until Dan restarts it. That is his call.
2. One surface (the rendered dashboard row at cool-off depth) has no gate and cannot get one from here.

**The one substantive finding is a record, not a defect (WV-01):** criterion 5's closing verdict still reads MET AS WRITTEN, and CR-01 established by measurement — which I independently reproduced at 6.81% against the recorded 6.84% — that the guarantee had a systematic hole in production when that verdict was written. It is fixed at the cause, the correction is recorded in five places in the tree, and the residual that remains is bounded, measured, and conservatively recorded. What is owed is one dated line beside the verdict row, which is exactly what this repository's own convention asks for and exactly what it did in four other places on the same day.

**One thing worth saying plainly, because it is the finding a softer verification would have missed:** the phase's tests were green when the guarantee was broken. Nine tests pinned the staleness window at the step, on both sides, at cool-off depth — and every one of them passed while a restart on this host dropped the cool-off 6.8% of the time. The tests measured `Pacer` in isolation; the defect lived in the clock `watch_loop` handed it. That gap is now covered by `test_the_pacer_clock_advances_by_the_time_the_check_pass_really_took`, which is the only test in the phase that lets a cycle consume real wall time.

---

_Verified: 2026-08-31T14:10:00Z_
_Verifier: Claude (gsd-verifier). Every figure above was produced by a command run during this verification; where it differs from the record, both are stated and the direction is named._
