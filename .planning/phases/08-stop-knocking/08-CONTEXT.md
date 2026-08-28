# Phase 8: Stop Knocking - Context

**Gathered:** 2026-08-28
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via `workflow.skip_discuss=true`)

<domain>
## Phase Boundary

A retailer that has refused 30-odd times in a row stops being asked twice a day, so the footprint
that earns and sustains a block shrinks.

**Requirements:** REQ-22 — *A retailer that has refused persistently is left alone, not knocked on
forever. After a bounded number of consecutive refusals the monitor stops requesting that retailer
for a period measured in days, then probes once. The current behaviour — a fixed 6-hour ceiling
applied indefinitely — is replaced, and the replacement is proved to reduce the request count
against a retailer that never recovers.*

**Depends on:** Nothing.

**In scope:** `boty/pacing.py` — the backoff ceiling, a cool-off state that outlives it, the
single-probe-on-expiry behaviour, clearing on recovery, and persistence across a restart through
the existing `pacer-state.json` document and its existing staleness rule.

**Out of scope, and each for a reason recorded in `REQUIREMENTS.md` § *What is deliberately NOT in
this milestone*:** a lost-coverage alarm (declined by Dan 2026-08-27 — *"we don't want to inform
the user it's broken, really. we want to prevent a broken state"*), an egress change, rung-2 API
credentials, and escalating any retailer's rung (measured on 2026-08-27 to not be an available
fix). Phase 9's independent scheduling is a **separate** phase that edits the same file; do not
pre-empt it here.

**No live retailer requests.** This phase is provable entirely offline over the scheduler, and
`REQUIREMENTS.md` § *Definition of Done* item 2 says so explicitly: REQ-22 is proved by offline
tests over the scheduler, *"the daemon is evidence, never the gate."*

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — the discuss phase was skipped per
`workflow.skip_discuss=true`. Use the ROADMAP phase goal, the six success criteria, and the
codebase conventions in `CLAUDE.md` to guide decisions.

### Constraints that are NOT discretionary

These come from the repository's standing rules and from the phase's own criteria, and a plan that
ignores one will fail its gate:

1. **Every gate is watched red before it is trusted.** Write the test, run it against the unfixed
   code, record the actual failure count, then fix and record the pass. A test that has never
   failed is not a gate — and if it cannot be made to fail, that is a finding to record, not a
   formality to skip.
2. **Criterion 1 forbids a relative assertion.** The days-scale wait is asserted against *literal
   expected seconds*, never against "greater than the old ceiling."
3. **Criteria 2 and 3 are simulations, not inferences.** The single-probe behaviour is asserted
   over a simulated sequence of cycles; the 30-day request count is a *stated number* for both the
   new rule and the current one, and both are recorded.
4. **Criterion 5 forbids a second staleness rule.** The cool-off is discarded when stale by the
   rule `pacer-state.json` already carries.
5. **Criterion 6 requires a new mutation**, registered, observed CAUGHT, and anchored on
   *behaviour* rather than on message text or a comment. Next free ident is **M42**;
   **M21–M24 are an intentional gap and must never be filled.**
6. **`make verify-offline` must exit 0**, and the verdict line is read rather than the exit code
   alone.
7. **Never write to `state.json`, `pacer-state.json` or `served/boty/status.json`** — the running
   daemon owns them. Copy to a scratch dir to exercise anything.
8. **A restart is Dan's call**, not a side effect of this phase.

</decisions>

<code_context>
## Existing Code Insights

`boty/pacing.py` owns cadence and backoff and is the file this phase edits. Two facts about it are
already recorded and load-bearing:

- `Pacer.current_interval` (landed 07-03) is the standing interval with the backoff in force
  applied to it, and it is the **single expression** behind both the published number in
  `status.json` and the fetch schedule. A cool-off that changes the wait without going through it
  would split them again.
- The current rule this phase replaces is a **fixed 6-hour ceiling applied indefinitely**. Measured
  on the live daemon 2026-08-20: gamestop 14400 s and walmart 21600 s, both on backoff.

Two open tech-debt items in the same file, carried from the v0.3 audit, are **not** this phase's to
fix but are worth not making worse: W1 (`Pacer.due`'s tolerance ignores per-retailer overrides,
under-reporting staleness by ≤150 s) and `pacer-state.json`'s non-atomic write (failure direction
confirmed *over*-reporting).

Remaining codebase context will be gathered during plan-phase research.

</code_context>

<specifics>
## Specific Ideas

None beyond the ROADMAP phase description and its six success criteria — the discuss phase was
skipped. The criteria are unusually prescriptive for this project and should be read as the spec.

</specifics>

<deferred>
## Deferred Ideas

None — discuss phase skipped.

</deferred>
