---
status: passed
phase: 08-stop-knocking
source: [08-VERIFICATION.md]
started: 2026-08-31
updated: 2026-09-11
---

## Current Test

number: 1
name: Decide whether to `sudo systemctl restart boty`, then confirm the cool-off is in force on the daemon
expected: |
  After a restart the daemon runs this working tree (editable install). A retailer
  past 30 consecutive refusals should publish `current_interval_seconds: 259200`
  and a `skipped_reason` of the form
  `cooling off after N refusal(s) — next attempt in ~X days`.

  `target` sat at 46 refusals on 2026-08-31, so it is the retailer to look at.

  Until a restart happens the daemon executes the PRE-phase rule and this phase
  has no effect on the wire.
awaiting: nothing — both items resolved 2026-09-11

## Tests

### 1. Restart the daemon, then confirm the cool-off is in force — **DONE 2026-09-11**

expected: `target` (46 refusals as of 2026-08-31, past the threshold of 30) publishes
`current_interval_seconds: 259200` and a days-scale `skipped_reason`.
why_human: A restart is Dan's call, not the agent's (CLAUDE.md), **and Phase 8's own
cross-cutting constraint in ROADMAP.md forbids `systemctl restart boty` anywhere in
this phase.** So this item could not have been discharged inside the phase even in
principle. The phase is complete IN THE TREE and is not deployed; those are two
different claims and this project has kept them apart across three milestones.
result: PASSED (restart) / NOT OBSERVABLE YET (cool-off)
  **Restarted 2026-09-11 07:56:33 on Dan's instruction.** `MainPID` 667833 -> 746345,
  `ExecMainStatus=0`, `NRestarts=0`. `state.json` migrated **13 -> 13 entries, zero lost**;
  `pacer-state.json` preserved (`amazon` 9 -> 10 because it refused again during the first wake,
  `target` 18 unchanged). **The new code is live, proved rather than assumed:** `status.json` was
  rewritten twice inside 70 s, which only happens at phase 9's ~50 s tick — the pre-phase-9 loop
  wrote every ~300 s.
  **THE COOL-OFF COULD NOT BE OBSERVED, and that is not a failure.** It needs 30 consecutive
  refusals; the live counts are `amazon` 10 and `target` 18, both BELOW the threshold. `target` was
  at 46 on 2026-09-02 and has answered since, which reset it. So the item is discharged as *the
  restart happened and the code is live*, and the days-scale cadence remains unobserved on the wire
  until some retailer reaches 30 again. Recorded as unobserved rather than claimed.
  **THE UNPLANNED WIN:** the Walmart store pin, deferred since v0.2 (REQ-14), is now IN EFFECT.
  Both Walmart rows read `unknown` before the restart and carry real verdicts after it — control
  `in_stock`, GO Plus + `out_of_stock`. A verdict where there was none.

### 2. Look at the live dashboard once a retailer is genuinely in cool-off

expected: the row reads `72h` for the cadence, and the `ageTag` comparison reads
e.g. `73h ago > 72h` rather than an apparent equality.
why_human: `served/boty/index.html` was deliberately not edited by this phase
(Collision B, decided against four measured JS strings). Nothing in the suite pins
`fmtDur`'s rendered output to `skipped_reason`'s string — measured: `grep -rn 5400
tests/` finds it only in `tests/test_dashboard.py`. Whether the rendered row reads
well is a visual judgement no gate can take.
result: NOT OBSERVABLE — Best Buy still does not read
  The row cannot be looked at because Best Buy's control is not being read at all: its row is a
  **remembered** one, `checked: false`, ~24,000 minutes old. That is the unrendered-shell problem,
  and 2026-09-10's fix makes the monitor HONEST about it (no longer a false dead) without making
  Best Buy readable. So there is no live cool-off row to judge. Recorded as not observable rather
  than passed.

## Summary

total: 2
passed: 1
issues: 0
pending: 0
skipped: 1
blocked: 0

## Gaps

Neither item is a defect and neither blocks the tree. Both are deployment
observations, and both were foreseeable at planning time — the ROADMAP forbade the
restart that would discharge them.

**What a restart would additionally carry, and it is no longer only Phase 8's
work:** `9ea42fe` changed `cli.watch_loop`'s clock, so a restart also stops the
pacer's clock drifting behind wall clock. That fix removes a 6.84%-per-window hole
in the cool-off's restart guarantee — and, as a direct consequence, returns the
loop to the configured cadence rather than running ~6.8% slower than it. The
request rate goes **up** slightly. That was a decision taken with the trade named
(2026-08-31), not an accident.
