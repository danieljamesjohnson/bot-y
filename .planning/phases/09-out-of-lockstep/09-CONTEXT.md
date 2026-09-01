# Phase 9: Out of Lockstep - Context

**Gathered:** 2026-08-31
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

The six retailers stop presenting as one coordinated crawler — independent schedules, so a
single cycle does not fire six unrelated retailers inside one short window.

**Requirement:** REQ-23 — *"The retailers are **not checked in lockstep**. Each retailer's
schedule is independent, so a single cycle does not present six unrelated retailers requested
inside one short window from one origin. The fleet's aggregate request pattern is asserted by
test, not by inspection."*

**Depends on:** Phase 8 (both edit the scheduler; they serialize on `boty/pacing.py`).
Phase 8 is COMPLETE in the tree as of 2026-08-31.

**Definition of Done item 2 governs the evidence:** REQ-23 is proved by **offline tests over
the scheduler**, not by observing the live daemon — *"the daemon is evidence, never the gate."*

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — discuss was skipped per
`workflow.skip_discuss=true`. Use the ROADMAP goal, the five success criteria, `CLAUDE.md`'s
evidence standard, and the codebase's existing conventions.

### Fixed by the phase's own inheritance, not open to re-choosing

- **`boty/pacing.py` is the site.** Phase 8 established `Pacer.current_interval` as the single
  expression behind both the fetch schedule and the published `current_interval_seconds`. A
  de-lockstep mechanism that creates a second scheduling expression would undo Phase 7's
  one-cadence property and Phase 8's widen-only rule. Both are argued in that module at length.
- **`MAX_BACKOFF_SECONDS` stays 6 h and `COOLOFF_SECONDS` stays 259200.** Phase 8 fixed these
  and criterion 4 here forbids regressing what already works.
- **`grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py` must stay 2.** Phase 8's
  no-second-staleness-rule constraint is a standing property of the module, not a phase-local
  one.
- **The pacer's clock advances by `delay + cycle_duration`** as of `9ea42fe`. Any change to
  `cli.watch_loop`'s scheduling must keep BOTH terms: the delay term is what keeps the loop
  deterministic under the tests' fake `sleep`, and the duration term is what stops the clock
  drifting behind wall clock. Measured: dropping either breaks a named test.

</decisions>

<code_context>
## Existing Code Insights

Gathered during plan-phase research. Known starting points:

- `boty/pacing.py` — `Pacer.due`, `Pacer.record`, `Pacer.current_interval`, `Pacer.skipped_reason`,
  and the `_RetailerState` shape with its persistence in `save`/`load`.
- `boty/cli.py` — `watch_loop` (the cycle cadence, `cfg.interval_seconds`, the jittered `delay`,
  and `scheduled_now`) and `watch_cycle` / `run_once` (which dispatch a whole pass).
- `config/products.yaml` — `interval_seconds: 300` global, plus per-retailer
  `retailer_intervals` overrides.
- **The lockstep is structural, not accidental:** `watch_loop` runs one pass every ~300 s and
  `run_once` asks every DUE retailer inside that pass. Retailers whose intervals coincide
  therefore fire together, from one egress, with one client fingerprint family — which is the
  defect the milestone's opening measurement attributes the blocks to.

</code_context>

<specifics>
## Specific Ideas

The five criteria are the spec and each names its own evidence. Two carry a stated-number
obligation that cannot be satisfied by an inequality:

- **Criterion 1** — the anti-coincidence bound is *"a stated number of seconds"*, asserted **on
  the schedule, never on a wall clock**.
- **Criterion 3** — the max retailers requested in any 60 s window over a simulated day is a
  **stated number**, and must be **smaller than the current six**. Like Phase 8's criterion 3,
  the *before* number is perishable: it must be measured against the unmodified rule before the
  rule moves, or it is unobtainable.

**Criterion 4 requires a re-measurement, not an assumption:** `boty check` is a deliberate full
pass and is a different thing from the daemon's schedule; it must still complete inside REQ-08's
2-minute budget. Note `CLAUDE.md`'s warning that `boty check` makes **live retailer requests**
and writes the live `served/boty/status.json` — so this budget must be re-measured without
running the real thing against real retailers.

</specifics>

<deferred>
## Deferred Ideas

- **No live retailer request anywhere in this phase.** `STATE.md` records phases 8, 9 and 10 as
  the safe autonomous ground; phase 11 is where the probe budget is spent. Definition of Done
  item 2 makes offline scheduler tests the gate for REQ-23 regardless.
- **No `systemctl restart boty`.** Phase 8's deferred restart is Dan's call and is still open;
  this phase does not touch it. Nothing in v0.4 is on the wire.
- **No write to `state.json`, `pacer-state.json` or `served/boty/status.json`.** The running
  daemon owns them.

</deferred>
