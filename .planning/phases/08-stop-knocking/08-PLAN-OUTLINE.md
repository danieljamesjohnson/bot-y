# Phase 8: Stop Knocking — Plan Outline

**Drafted:** 2026-08-28 · **Granularity:** coarse · **Requirement:** REQ-22 (the only one)
**Mode:** chunked — this file is the outline. No `PLAN.md` has been written yet.

`boty/pacing.py` and `tests/test_pacing.py` are contested files: every plan below touches at least
one of them, so **every plan is its own wave**. This repo has learned that lesson three times
(ROADMAP Phase 2 and Phase 3 notes); the serialization is not a scheduling failure, it is the
schedule.

| Plan ID | Objective | Wave | Depends On | Requirements |
|---|---|---|---|---|
| `08-01` | **The number before, and both collisions decided in writing.** Simulate 30 days of 300 s cycles against a never-recovering retailer on the **unmodified** `pacing.py` and record the request count as a stated literal — criterion 3's "before" half, which is unobtainable once any code moves. Write `08-DECISIONS.md` resolving collision 1 (the staleness derivation) and collision 2 (a restart costs one probe) with reasoning, and `COVERAGE.md`'s single declaration line. **Changes no production code, deliberately.** | 1 | — | REQ-22 |
| `08-02` | **The cool-off itself — criteria 1, 2, 3-after and 4.** Add `REFUSALS_BEFORE_COOLOFF` and `COOLOFF_SECONDS`, a cool-off branch inside `Pacer.current_interval` (never beside it) and its arm in `skipped_reason`; reverse the module docstring's and `MAX_BACKOFF_SECONDS`' superseded arguments in the house dated form. Extend the literal-seconds table across the threshold, assert the single probe over simulated cycles, state the 30-day "after" number, and assert recovery clears the cool-off at depth. Leads with the end-to-end tracer. | 2 | `08-01` | REQ-22 |
| `08-03` | **Criterion 5 — it survives a restart, and the rule that discards it is the one already there.** Re-derive `STATE_MAX_AGE_SECONDS` from the longest wait the module can now produce rather than from the ceiling this phase stopped applying indefinitely, with a dated note beside the old derivation. Prove the depth is restored *and* reaches the arithmetic, that a stale record is discarded by the existing two-sided window and no second one, and that a restart mid-cool-off costs exactly the one probe `08-01` decided it costs. Argue in writing why **no** `_RetailerState` field and **no** `STATE_VERSION` bump are owed. | 3 | `08-02` | REQ-22 |
| `08-04` | **Criterion 6 — the gate closes, and the surfaces are checked rather than assumed.** Register **M42** on the cool-off branch, observe it CAUGHT, and carry the eighth `INTENTIONAL GAP` marker restating why M21–M24 stay empty. Confirm `monitor.py` / `status.py` / `cli.py` needed no edit rather than predicting it, and decide deliberately what the dashboard does with a days-scale `current_interval_seconds`. Run `make verify-offline` and read the **verdict line**, not the exit code alone. | 4 | `08-03` | REQ-22 |

---

## Notes the plan writers must not rediscover

### Tracer placement

`08-01` changes no production code by design — criterion 3's "before" number cannot be measured
after the change, so the measurement has to be its own commit. **The tracer task is therefore the
first task of `08-02`**: one retailer, driven past the threshold, through `current_interval` →
`record`'s `due_at` → `due` saying "not due" → `skipped_reason`'s prose → `cli._current_intervals` →
`status.write`'s `current_interval_seconds`, verified end-to-end in one test before any table is
extended. That single path is what proves the cool-off reaches the published number and the fetch
schedule as **one expression**, which is the whole reason it goes inside the accessor.

### Two collisions the pattern map named — how they resolve

**Collision 1 — `STATE_MAX_AGE_SECONDS = MAX_BACKOFF_SECONDS` (`boty/pacing.py:151`).**
Resolve as option (a): the derivation carries the new number. The constant's own comment argues the
window should be "one full cap-length window", so it must become the longest wait this module can
produce, not the longest *backoff* — a named derived constant (e.g. `LONGEST_WAIT_SECONDS`) is the
honest shape, and `STATE_MAX_AGE_SECONDS` derives from that. **It lands in `08-03`, not `08-02`**,
so `08-03`'s tests are genuinely red before its one-line fix rather than red against a synthetic
revert. `08-02` must state the consequence out loud: between wave 2 and wave 3 the tree holds a
days-long cool-off that a restart discards after six hours. That is a recorded one-wave gap, not a
shipped defect — nothing is deployed mid-phase and a restart is Dan's call.

**Collision 2 — `due_at` is never persisted, so a restart probes once immediately.**
Keep it, and say so. The module docstring already argues this at length (concession (b), lines
62–75): what a restart inherits is the **depth** the penalty resumes at, never the position on the
schedule. Criterion 5 asks for "the same guarantee the existing backoff already carries" — that
guarantee *is* depth-only, so criterion 5 is met without touching `due_at`, and criterion 2's
"exactly once" is scoped to a running process. **Criterion 3's 30-day number must state its restart
assumption explicitly** (zero restarts in the simulation) and name the per-restart cost as one
request, rather than leaving the reader to infer a count that quietly depends on it.

### Two more collisions, found while reading the tree — neither is in `08-PATTERNS.md`

**A — an existing test drives exactly 30 refusals and asserts the old ceiling.**
`tests/test_pacing.py:176` `test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring`
runs `for _ in range(30)` and asserts `due_at - now == MAX_BACKOFF_SECONDS`, then asserts
`MAX_BACKOFF_SECONDS <= 6 * 60 * 60, "a cap beyond a few hours is not a monitor"`. The phase goal
says *"30-odd times"*, so at a threshold of 30 this test **breaks**, and that is the outcome to
choose. Picking 31+ would let it survive untouched — which sounds cheaper and is worse, because the
sentence REQ-22 exists to overrule would then still be standing, unremarked, at the exact boundary
criterion 1 is about. Rewrite it with the dated-reversal treatment: quote the withdrawn assertion,
record that REQ-22 overruled it for a *persistently* refused retailer, and keep the second assertion
alive — **`MAX_BACKOFF_SECONDS` stays 6 hours.** What this phase replaces is the ceiling being
applied *indefinitely*, not its value. Raising it instead would trip that same assertion and lose
the distinction.

**B — the dashboard's `fmtDur` tops out in hours.**
`served/boty/index.html:118` is `s < 90 ? s + 's' : s < 5400 ? m : h`, so a three-day cool-off
renders `72h`. Legible, but it is a presentation decision and must be made rather than discovered.
If `08-04` adds a day band, both dashboard gates re-enter: **no HTML comments inside the `<script>`
block**, `esc()` on every UNTRUSTED field, and `node --check` on the extracted script (which needs
`export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh` first — `make` does not inherit nvm).

### The spec-less probe items — 3 applicable, 0 resolved, all 3 authored

| # | Category | Lands in | Authored as |
|---|---|---|---|
| 1 | boundary | `08-02` | `must_haves.truths` string — literal expected seconds at `N-1`, `N` and `N+1` refusals, so the threshold is asserted at the step, not near it |
| 2 | precision | `08-02` | `must_haves.truths` string — the cool-off wait is an exact literal reached **without** exponentiation, so no rounding contract is entered; `skipped_reason`'s `:.0f` is presentation and never feeds the schedule; `MAX_PERSISTED_REFUSALS = 64` keeps the pre-threshold path below the `2.0 ** 1024` cliff |
| 3 | concurrency | `08-03` | structured flat-scalar marker `{ statement: "a restart mid-cool-off restores the depth and costs exactly one probe; a second, load-only Pacer reading a partially written document degrades to standing intervals", verification: backstop }` — the parallel-read half rests on `pacer-state.json`'s known non-atomic write, which is carried v0.3 debt and explicitly not this phase's to fix |

**Count equality holds: 3 surfaced == 3 authored + 0 flagged.** Nothing was dismissed.

### Prohibitions (recalled in-prompt; no SPEC `## Prohibitions` exists)

Author descriptor-less into `must_haves.prohibitions:` — no `check_*` scalar of any kind, so each
disposes flagged-unverified.

- `08-01` — *the reduction is never achieved by omitting requests from the count.* Criterion 3's
  number must count requests actually attempted; a simulation that stops counting is the one
  unforgivable move wearing a measurement's clothes.
- `08-02` — *a cool-off never becomes never-ask-again.* A retailer that is left alone for days is
  still on the schedule and still published; a wait that never expires is a silently dropped
  retailer with a row on the dashboard, which is this project's core defect one level up.
- `08-02` — *a cool-off is never used to silence a failure that is ours.* If the refusal is really a
  dead control or a broken detector, a days-long silence hides it for days. That is Phase 10's
  problem to fix and this phase's not to make worse.

Dropped as canon with a breadcrumb: hostile-document input validation and refusal-count DoS — both
already carried by the `isinstance` ladder, `MAX_PERSISTED_REFUSALS` and the 20-row `_HOSTILE` table.

### Threat model rows (ASVS L1, block on `high`) — honest, unpadded

This phase adds **no network surface**: it edits local scheduling arithmetic and makes no request.
Two genuine rows, plus the reason there is no third.

| Threat ID | Category | Component | Severity | Disposition | Mitigation |
|---|---|---|---|---|---|
| `T-08-01` | Tampering | `Pacer.load` over `pacer-state.json` | medium | mitigate | a corrupt or hand-edited document must not crash the daemon **or silently disable pacing** — the existing `isinstance` ladder plus `_HOSTILE` rows, and `08-03` must confirm no new persisted structure was added that would need its own row |
| `T-08-02` | Denial of Service | the new wait arithmetic in `current_interval` | medium | mitigate | the cool-off must not produce `inf`, a negative, or an absurd wait: it is a literal reached without exponentiation, `MAX_PERSISTED_REFUSALS = 64` clamps the pre-threshold path far below the measured `2.0 ** 1024` cliff, and the outer `max(st.interval, …)` keeps the "a backoff may only ever widen the wait" rule |

No `T-08-SC` row: this phase installs no package, so there is nothing for the legitimacy gate to
audit. Said rather than omitted.

### Standing constraints every plan inherits

1. **Watched red before trusted.** Each new gate: run against the unfixed code, **record the actual
   failure count**, then fix and record the pass. `08-01`'s baseline simulation is the exception and
   must say so in its own words — it measures rather than gates, cannot be made to fail, and *that
   is the finding*, not a skipped formality.
2. **Never round a claim up.** MET IN PART is shippable. Rewording a criterion so it passes is not.
3. **Superseded text is recorded beside, never edited away** — the module docstring, the
   `MAX_BACKOFF_SECONDS` comment, `STATE_MAX_AGE_SECONDS`' comment and the test at line 176 all take
   the dated-reversal form: quote the withdrawn text in full, then the measured facts that overruled
   it, then what survives.
4. **M42 is the next free ident. M21–M24 are never filled.** M42 anchors on the cool-off **branch**
   — a line whose removal changes *when a request is made*. A mutation on a constant's value would
   be caught by the literal-seconds table and defends less.
5. **Never write `state.json`, `pacer-state.json` or `served/boty/status.json`.** Copy to a scratch
   dir. Never run `boty check`. **No live retailer request, at all.**
6. **No `systemctl restart boty` task.** That is Dan's call and is not a phase deliverable.
7. `.venv/bin/python -m pytest`, never bare `python`. `make verify-offline` exits 0 **and** its
   verdict line is read.

### Assumption-delta detector — fired and dismissed

The detector flagged the token *"second"* in criterion 5's *"discarded when stale by the existing
rule rather than a second one"*. **False positive.** The criterion is not introducing a second case;
it is forbidding one. No identity-model question is open. Recorded here so a reader knows the
detector ran, and carried into `08-01`'s `08-DECISIONS.md` rather than raised as a question.

---

## Artifacts this phase produces

Every symbol, so the executor creates these and not near-misses. Names marked *(candidate)* are the
plan writer's to fix; the shape is not.

**`boty/pacing.py`**
- `REFUSALS_BEFORE_COOLOFF` — int, the bounded consecutive-refusal threshold *(candidate; ≤ 30 so
  collision A binds, and comfortably below `MAX_PERSISTED_REFUSALS = 64` and above
  `cli.REFUSALS_BEFORE_PAGING = 5`)*
- `COOLOFF_SECONDS` — the days-scale wait *(candidate)*
- `LONGEST_WAIT_SECONDS` — derived; the longest wait this module can produce *(candidate, `08-03`)*
- `STATE_MAX_AGE_SECONDS` — **re-derived** from the above; the constant survives, its derivation moves
- `MAX_BACKOFF_SECONDS` — **unchanged at 6 h**; only its comment gains the dated reversal
- a cool-off branch in `Pacer.current_interval`, inside the existing `max(st.interval, …)`
- a cool-off arm in `Pacer.skipped_reason`
- **deliberately absent:** no new `_RetailerState` field, no `STATE_VERSION` bump — both argued in
  `08-03` rather than merely not done

**`tests/test_pacing.py`**
- a baseline 30-day simulation recording the **current rule's** stated count (`08-01`)
- the same simulation under the new rule, recording the **new** stated count (`08-02`)
- a cool-off literal-seconds table extending `_CADENCE_AFTER_N_REFUSALS` across the threshold —
  hand-written literals, never re-derived through `current_interval` *(candidate name:
  `_CADENCE_ACROSS_THE_COOLOFF_THRESHOLD`)*
- a simulated-cycles single-probe test (criterion 2), a recovery-at-depth test (criterion 4)
- restart-survives + restored-value-is-load-bearing + discarded-when-stale tests (criterion 5)
- `test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring` — **rewritten** with the
  dated reversal, keeping its `MAX_BACKOFF_SECONDS <= 6 * 60 * 60` assertion alive
- `test_the_age_out_is_derived_from_the_backoff_cap` — **rewritten** to assert the new derivation

**`scripts/mutation_check.py`**
- `Mutation(ident="M42", target="boty/pacing.py", …)` on the cool-off branch, with the prose block
  above it carrying what it rebuilds, why it earned an ident, and an `IF IT EVER SURVIVES:` paragraph
- the **eighth** `INTENTIONAL GAP` marker restating M21–M24 (`grep -c "INTENTIONAL GAP"` → 8)

**`served/boty/index.html`** — `fmtDur` day band, **only if** `08-04` decides `72h` reads badly

**New files**
- `.planning/phases/08-stop-knocking/COVERAGE.md` — exactly one declaration line:
  `No external API integration: this phase edits boty/pacing.py's scheduling arithmetic and makes no live retailer request.`
- `.planning/phases/08-stop-knocking/08-DECISIONS.md` — the baseline number, both collisions, the
  restart cost, and the dismissed assumption-delta

## OUTLINE COMPLETE
