# Phase 9: Out of Lockstep — Plan Outline

**Drafted:** 2026-09-01 · **Granularity:** coarse · **Requirement:** REQ-23 (the only one)
**Mode:** chunked — this file is the outline and the authority on the breakdown.

`boty/pacing.py`, `boty/cli.py` and `tests/test_pacing.py` are contested files: every plan below
touches at least one of them, so **every plan is its own wave**. Phase 8 recorded the same shape for
the same reason — *"the serialization is the schedule, not a scheduling failure"* — and Phases 2 and
3 learned it before that. `files_modified` in each plan's frontmatter is the accurate list, so the
wave grouping is real rather than declared.

| Plan ID | Objective | Wave | Depends On | Requirements |
|---|---|---|---|---|
| `09-01` | **The number before, and eight collisions decided in writing.** Simulate a day of cycles over the six configured retailers against the **unmodified** scheduler and record the maximum number of retailers requested inside any 60-second window as a stated literal — criterion 3's *before* half, which is unobtainable once any scheduling code moves. Write `09-DECISIONS.md` resolving all eight collisions with reasoning, and assert `COVERAGE.md`'s single declaration line. **Changes no production code, deliberately.** | 1 | — | REQ-23 |
| `09-02` | **The mechanism lands and the tree comes back green — criterion 3-after.** A deterministic per-retailer **phase** (a position on the schedule, never a duration) plus a loop **tick** shorter than the shortest standing cadence, wired end-to-end by a tracer before anything is generalised. `record` advances on the retailer's own grid instead of re-anchoring to the cycle's `now` — **unconditionally**, which reddens ten existing tests that this plan enumerates by name and closes itself. | 2 | `09-01` | REQ-23 |
| `09-03` | **Criteria 1 and 2 — the shape of the schedule, asserted.** The separation as a stated literal read off the schedule and never off a clock; independence in both directions with the negative half compared field by field; both under the construction `cli.watch_loop` actually ships. Plus the loop's tick proved to reach the sleep, both clock terms observed defended, and the daemon's new wake and write rates written down for 09-04 to price. | 3 | `09-02` | REQ-23 |
| `09-04` | **What a shorter tick costs, paid rather than discovered.** A tick that asked nothing must not publish a vacuously green `healthy`. The two failure counters are counts of cycles and the cycle just got shorter. `config.py`'s *"the loop sleeps interval_seconds per CYCLE"* went false. Criterion 4's first half: per-retailer cadence and backoff still hold, and the aggregate request rate did **not** rise. | 4 | `09-03` | REQ-23 |
| `09-05` | **The budget, the gate and the verdict.** Criterion 4's second half — `boty check`'s two-minute budget, established offline and honestly, stated as **bounded** if it cannot be measured. Criterion 5 — **M43** registered and observed CAUGHT, anchored on behaviour. `make verify-offline` run and its **verdict line** read, not the exit code alone. The five-criterion verdict table. | 5 | `09-04` | REQ-23 |

---

## The five criteria, verbatim from `ROADMAP.md`, unedited

  1. Two retailers whose intervals coincide are **not** dispatched inside the same short window; the bound is a stated number of seconds and is asserted on the schedule, never on a wall clock
  2. Each retailer's next-attempt time is **independent**: changing one retailer's interval or backoff moves that retailer's schedule and no other's, asserted in both directions
  3. Over a simulated day, the maximum number of retailers requested within any 60-second window is a **stated number**, and it is smaller than the current six
  4. **No regression in what already works**: per-retailer cadence and backoff still hold, and `boty check` — a deliberate full pass, which is a different thing from the daemon's schedule — still completes inside REQ-08's 2-minute budget, re-measured rather than assumed
  5. `make verify-offline` exits 0, with at least one new mutation registered and observed CAUGHT

**Not one of them is reworded anywhere in this phase.** Where a criterion cannot be met as written,
the plan that owns it records **MET IN PART** with the half that is missing named — criterion 4's
budget is the one this outline already expects to land there, and `09-01` § *Collision 8* says so
before any code moves rather than after the measurement disappoints.

---

## Notes the plan writers must not rediscover

### The lockstep is structural, and one arithmetic fact settles the whole design

`config/products.yaml` configures six retailers: **walmart, nintendo, target and bestbuy at the
300 s default**, gamestop at 900, amazon at 1800. `cli.watch_loop` sleeps `cfg.interval_seconds`
(300 s) per cycle and `monitor.run_once` asks **every due retailer inside that one pass**, back to
back. So:

- Four retailers need a request inside every 300 s span.
- The loop makes requests only at a tick, and a 300 s tick gives **exactly one tick per 300 s span**.
- Therefore all four must be requested at that one tick, **whatever phase they are given**.

**Criterion 1 is unsatisfiable while the tick equals the cadence, and no offset can rescue it.**
That is a proof, not a preference, and it is why the phase changes `cli.watch_loop`'s tick as well
as `Pacer`'s schedule. The two alternatives were considered and are rejected in writing:

- **Lengthening the standing intervals** so fewer retailers coincide would meet criteria 1 and 3 by
  **halving coverage** — and criterion 4 forbids exactly that (*"per-retailer cadence still holds"*).
  It is the reduction-by-not-asking move this repository has caught itself making before.
- **Spacing the requests inside a pass** (a sleep between retailers) is a **wall-clock** mechanism,
  which criterion 1 rules out in its own words (*"asserted on the schedule, never on a wall clock"*),
  and it would spend the `boty check` budget criterion 4 protects.

### The shape: a phase is a POSITION, never a duration

This is the whole answer to the standing constraint that the phase must not create a second
scheduling expression. Phase 7 made `Pacer.current_interval` the single expression behind both the
fetch schedule and the published `current_interval_seconds`; Phase 8 put the cool-off **inside** its
`max()` rather than beside it, and argues that at three sites.

**Nothing in this phase touches `current_interval`.** A retailer's cadence is still one expression
and the published `current_interval_seconds` is still that same number, because the offset this
phase introduces answers a different question:

| | asks | lives in | published as |
|---|---|---|---|
| `current_interval` | **how long** between attempts | the accessor, one expression | `current_interval_seconds` |
| the phase | **where** on the schedule the attempts land | `_RetailerState.due_at`'s starting value | nothing — it is not a cadence |

A retailer at a 300 s cadence with a phase of 150 s is still asked every 300 s. Its long-run count
is unchanged, which is exactly what `09-02` asserts and `09-04` re-states as criterion 4's evidence.

### Two terms are required, and the second one is the non-obvious half

A planning-time viability check ran on 2026-09-01 in a **throwaway standalone script under `/tmp`**,
modelling the proposed rule. **It did not touch `boty/pacing.py` and every number it produced must
be re-measured against the real code before any of them is stated anywhere.** What it established
is a *shape*, and the shape is the thing the plan writers must not rediscover:

1. **A birth phase alone is not enough.** `record` currently sets `st.due_at = now + wait`, where
   `now` is the cycle's clock. Two retailers that fire at the same tick are therefore re-anchored to
   the **same** `due_at` and are in lockstep from then on — which is the mechanism, not a side
   effect. Worse, under the loop's ±15% sleep jitter the tolerance in `due` lets a retailer fire one
   tick early now and then, and a retailer that drifts into another's slot **stays there**: the
   merge is absorbing. The check saw a phased fleet collapse back to six-in-a-window within a
   simulated day with jitter on.
2. **So `record` must advance on the retailer's own grid** — the next due time derived from the
   previous one rather than from the cycle's `now`, stepped forward by whole waits until it is in
   the future. That is a fixed-rate scheduler and it has the property the birth phase needs: firing
   early or late does not move the phase, so the separation survives jitter indefinitely. It also
   has the property a naive `due_at += wait` does not: **no catch-up storm** when a pass runs long.

Both terms are `09-02`'s and neither is optional. `09-02`'s tracer is what proves they compose
before the tables are extended.

### The advance is UNCONDITIONAL, and that is what sets the wave boundaries

**Measured against the tree, not predicted.** The roster and tick defaults protect two of the three
moving parts — the tolerance in `due` and the birth phase in `_for` — so a `Pacer` built without them
keeps today's behaviour in both. **`record`'s advance is protected by nothing.** It changes for every
construction site in the tree, and it reddens ten existing tests:

| # | Test | Reddened by |
|---|---|---|
| 1 | `test_pacing::test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring` | the advance, both readings |
| 2 | `test_pacing::test_the_backoff_schedule_is_exactly_the_schedule_it_was[300.0]` | the advance, both readings |
| 3 | `test_pacing::test_the_backoff_schedule_is_exactly_the_schedule_it_was[1800.0]` | the advance, both readings |
| 4 | `test_pacing::test_one_good_read_clears_the_backoff_completely` | the advance, both readings |
| 5 | `test_pacing::test_a_retailer_that_answers_during_its_probe_is_back_on_its_standing_interval_at_once` | the advance, both readings |
| 6 | `test_cli_watch::test_a_retailer_in_cooloff_publishes_the_days_scale_cadence_it_is_actually_on` | the advance, both readings |
| 7 | `test_pacing::test_a_retailer_in_cooloff_says_so_rather_than_reporting_a_minute_count` | reading A only |
| 8 | `test_cli_watch::test_a_refusal_the_backoff_is_handling_is_recorded_not_pushed_across_a_restart` | reading A only |
| 9 | `test_pacing::test_a_retailer_at_the_default_cadence_is_due_every_cycle` | reading B only — collision A |
| 10 | `test_pacing::test_the_restored_pacer_starts_its_schedule_from_zero` | the birth phase — collision B |

**Three consequences the plan writers must not soften.**

1. **`09-02` repairs all ten itself.** No plan after it owns `tests/test_pacing.py`, so a deferred
   repair is not a bad habit here — it is impossible. Phase 8 recorded repairing another plan's red
   in a later wave as the thing not to do; the file ownership makes the rule structural.
2. **The advance rule has two readings and they redden different tests.** *Reading A* steps the
   previous due time forward in whole waits; *reading B* steps once and floors at the cycle clock.
   `09-02` names both, chooses one deliberately, and records the choice with its collateral. The
   table above covers both so whichever is taken the list is already written.
3. **Gating the advance behind a non-empty roster is REFUSED.** It would keep every old test green
   with no edits, and it would make every defaulted site — most of the suite — exercise a code path
   the daemon never takes, since `cli.watch_loop` always passes a roster. That buys a small diff by
   making the evidence describe something that does not ship. `09-02` carries it as a prohibition.

**`skipped_reason` is the collateral path behind items 6 and 7**, and it is named here so nobody
"fixes" it. That method renders `due_at - now`; an advance that changes where the next attempt lands
changes the prose it prints. Its cool-off arm's condition — `current_interval` and the refusal count
— does not move. If a repair looks like it needs `skipped_reason`'s logic to change, that is the
signal the mechanism moved a cadence rather than a position.

### Two comments inside `boty/pacing.py` go false, and both get a note beside them

Neither is edited over; `docs/retailer-evidence.md` § 6 is the convention. Both land in `09-02`,
which is already editing that region to add the two fields.

- **`_RetailerState` leg 2** argues no probe flag is owed, partly because *across a restart the next
  attempt resets to 0.0 by design, priced at one immediate request*. After this phase it resets to
  the retailer's **phase**, and the price is one request within one standing interval. **Leg 2's
  conclusion survives whole** — the probe cannot repeat inside a process because `record` re-schedules
  unconditionally on every outcome — so only the number beside it moved.
- **The `state_path` paragraph's count**: *"There are nine in `tests/test_pacing.py` alone and not one
  names a path."* **Exactly true when written** — `46a0768`, 2026-08-10, eleven sites minus two that
  name a path. Now: **24 of 26** in `tests/test_pacing.py`, and **31 tree-wide** (26 + 3 in
  `tests/test_cli_watch.py` + 2 in `boty/cli.py`) across **9 distinct call shapes**. The argument the
  sentence serves is strengthened, not weakened: the number of sites the default protects went up.

### The tick is CHOSEN BY MEASUREMENT, not by this outline

`09-02` must measure candidate ticks against the day-long simulation and take the number, rather
than assume one. Two bounds it has to respect, and both are stated here so the measurement has a
frame:

- **A floor.** The loop cannot keep up if one pass costs more than one tick. The only measurement
  available offline is the last published whole-pass figure — `served/boty/status.json`'s
  `duration_seconds: 20.43` for 13 watches across all six retailers, **read on 2026-08-31 by the
  phase-8 code review** and quoted rather than re-read. A tick's due set is a subset of that pass,
  so **any tick comfortably above ~20 s cannot be outrun by a single pass**. That is a bound off one
  reading of a live pass, not a guarantee, and it is to be written that way.
- **A ceiling.** The tick must divide the shortest standing cadence often enough to give the four
  coinciding retailers distinct slots: with four at 300 s, `tick <= 75`.

**No number is fixed here on purpose.** `MIN_TICK_SECONDS` and the slot arithmetic are `09-02`'s to
name and to defend at their definition site, the way `REFUSALS_BEFORE_COOLOFF` is defended at its.

### Eight collisions — how they resolve

These land in `09-DECISIONS.md` (`09-01`, Task 2) with the reasoning, before any code moves.

**Collision 1 — the tick must shrink.** Resolved by the elimination argument above. It is stated as
a proof so that a later reader meeting a 6× wake rate understands it was forced rather than chosen.

**Collision 2 — the module docstring's concession (b) goes false, and it is load-bearing.** It reads
*"A restart still tries once, immediately, at full rate, so the condition is re-tested at once."*
A birth phase means a retailer with a phase of 250 s is first asked 250 s after a restart. The
alternative — phase only from the **second** attempt, keeping the immediate probe — was considered
and is **not available**: it puts a six-retailer burst at t=0 of every process, criterion 3's
simulation counts a day from a cold start, and excluding that burst from the count would be a
reduction achieved by not counting. So: **the concession is withdrawn in the dated-reversal form**,
its price stated as *"each retailer is re-tested once within one standing interval rather than
immediately"*, and the compensating fact recorded beside it — under `Restart=` semantics a flapping
service previously re-probed every retailer at full rate on every restart, and now does not. What
survives untouched is the half that argument was really for: **`due_at` is still never persisted,
and the DEPTH is still what a restart inherits.**

**Collision 3 — `record` must stop re-anchoring to `now`.** Resolved as above. `09-02` must state
that this is a change to *where* the next attempt lands and **not** to *how long* the wait is:
`wait` still comes from `current_interval` and from nowhere else.

**Collision 4 — an empty tick must not publish a vacuously green verdict.** `boty/status.py:154` is
`"healthy": all(h.ok for h in health)`, and `all([])` is `True`. Today every 300 s cycle asks
somebody, so an empty pass is only reachable when every retailer is backed off. **After this phase
roughly half of all ticks ask nobody**, so a pass that checked nothing publishing `healthy: true` is
routine — *a green dashboard over a question nobody asked*, which is this project's own defect one
level up, rebuilt inside the fix for a different one. `09-04` owns it. The shape to prefer is the
one `boty/status.py` already argues for its per-retailer rows twelve lines up from the defect —
*"the retailer is not healthy (nothing was verified) and not unhealthy (nothing failed) — it simply
was not asked"* — so the aggregate gets the same third state rather than a new invention. Measured
while planning: **the dashboard does not read `healthy` at all** (`grep -n healthy
served/boty/index.html` returns nothing) and `boty/status.py:154` is its only producer, so the blast
radius is `tests/test_status.py:217` (the key-set assertion, which is unaffected) and `:249`.

**Collision 5 — the two failure counters are counts of cycles.** `FAILURES_BEFORE_WARNING = 3` and
`FAILURES_BEFORE_GIVING_UP = 10` were chosen against a 300 s cycle: ~15 minutes to a warning, ~50
minutes to giving up. At a shorter tick both fire proportionally sooner in wall time, and the
warning one **sends a notification**. `09-04` must either re-derive them as durations or accept the
change **in writing** — an accidental 6× increase in how fast this monitor pages a human is the
`notify-dan` bar failing in the direction this repository cares about most.

**Collision 6 — `boty/config.py`'s validation comment goes false.** Around line 253 it reads
*"`cli.watch_loop` sleeps `interval_seconds * uniform(0.85, 1.15)` per CYCLE"*, and it is the
argument for the `retailer_intervals[x] >= interval_seconds` rule. **The rule survives and its
reason changes**: `interval_seconds` stops being the loop's sleep and becomes the shortest standing
cadence, which is still the floor a per-retailer override must not go under. Dated-reversal
treatment, and the validator itself is untouched.

**Collision 7 — no persisted state, therefore no `STATE_VERSION` question, and that is confronted
rather than stepped around.** Phase 8 refused a bump with a three-legged argument written into
`boty/pacing.py`, whose decisive leg is that *"treated as absent"* discards exactly the state the
phase protects, on the day it ships. **This phase must not reopen it, and does not need to: the
phase offset is DERIVED from the retailer's name and the configured roster, and is therefore stable
across processes without being stored.** That is the same argument `STATE_MAX_AGE_SECONDS` and
`Result.degraded` make one level up — derive rather than store, because two copies only have to
disagree once. `09-02` must state this at the definition site and `09-04` must **confirm by
inspection of `save`/`load` that the document's shape is unchanged**, rather than predict it.
A consequence worth naming in the same breath: **`hash()` is not available for this** — CPython
randomises `str.__hash__` per process under `PYTHONHASHSEED`, so a phase derived from it would be a
different schedule in every process and would not be a schedule at all.

**Collision 8 — criterion 4's budget can be bounded, and probably not measured.** `boty check` makes
**live retailer requests** and writes the live `served/boty/status.json`, which the daemon owns, and
this phase makes no live request anywhere. So the honest instruments available offline are:
(a) the **structural** fact that `boty check`'s pacer is load-only and **is never passed to
`run_once`** — so no scheduling change this phase makes can reach that path — which is already
gated by `tests/test_cli_watch.py` (see the `boty check` section around lines 653 and 1363); and
(b) the last **published** `duration_seconds` from a real pass, **read and never written**.
`09-04` states the verdict as **MET IN PART** if that is what it is, names which half is unmeasured,
and does not run `boty check` to close the gap.

### Three collisions with tests that already exist

**A — `test_a_retailer_at_the_default_cadence_is_due_every_cycle` (`tests/test_pacing.py:430`).**
It drives 20 short-jitter 300 s cycles and asserts the retailer is due at *every* one. Its docstring
calls the failure it guards *"the regression that would make this change quietly halve coverage"*.
**After this phase the unit is wrong and the fear is still right.** A retailer at the default cadence
is due once per **cadence**, not once per **tick**, and being due every tick would now be the
defect. Rewrite with the dated-reversal treatment: quote the withdrawn assertion, record what
overruled it, and **keep the coverage half alive** — the retailer must still be asked the same
number of times per day, which is `09-02`'s gate. Do not delete the test and do not rename it away
from `git log -S`'s reach.

**B — `test_the_restored_pacer_starts_its_schedule_from_zero` (`tests/test_pacing.py:997`).**
It asserts `second._for("amazon").due_at == 0.0` and `second.due("amazon", 0.0)` with the message
*"a restart must still try once, immediately"*. **Both halves move**, and this is collision 2 wearing
an assertion. What must survive verbatim is the sentence the test exists for: *"a `due_at` came back
from disk. It was measured against a clock that no longer exists"* — nothing here persists `due_at`,
so re-point the assertion at *the phase, and only the phase*: a restored pacer's `due_at` is its
retailer's phase and nothing else, which is a number this process computed rather than one a
previous process left behind.

**C — `09-01`'s baseline test is consumed by `09-02`.** Exactly as `08-01`'s was: the *before* number
becomes a dated record in a docstring and the same simulation, unchanged in every other respect,
carries the *after* number. That is the test's second job, not a casualty. The denominator, the
per-retailer tallies and the window all stay put, so the two numbers are comparable rather than two
answers to two questions.

**And one that is half a collision, which is the half that matters.** **31 construction sites** build
a `Pacer` with no roster and no tick — 26 in `tests/test_pacing.py` (24 of them naming no path), 3 in
`tests/test_cli_watch.py`, 2 in `boty/cli.py`, across 9 distinct call shapes. An empty roster gives
every retailer a phase of 0.0 and a tolerance off `default_interval`, which is today's behaviour — the
same defaulting argument `Result.rung`, `Result.extraction` and `Pacer.state_path` already make in
this tree.

**What the default does NOT cover is `record`'s advance**, and the honest consequence has to be said
in the direction it actually points. It is tempting to write that the defaults keep the phase-8 tests
untouched and that their passing therefore proves the schedule is safe. **That is backwards.** If a
defaulted `Pacer` were today's behaviour in every respect, phase-8 gates passing would prove nothing
about the schedule the daemon runs, because `cli.watch_loop` **always** passes a roster and a tick.
Two obligations follow, and `09-04` carries both:

1. the advance is unconditional, so those tests do NOT come through untouched — ten of them redden
   and `09-02` repairs them, which is why predicting otherwise would have been a false claim; and
2. the regression sweep must additionally assert under the **shipping** construction — roster and
   tick present — or it is a sweep over a shape nobody runs.

### Prohibitions (author descriptor-less into `must_haves.prohibitions`)

- `09-01` — *the before-number is never made smaller by counting fewer requests.* The window is a
  full simulated day, the denominator is asserted, and every request the simulation makes is
  counted. A simulation that stops counting is the one unforgivable move wearing a measurement's
  clothes.
- `09-02` — *the de-lockstep is never achieved by asking less.* Spreading six retailers by checking
  each of them half as often satisfies criterion 3 and gives away the coverage this whole project
  exists to provide. The per-retailer daily count must be **unchanged**, and it is asserted rather
  than hoped.
- `09-02` — *a phase is a position, never a duration.* Nothing outside `current_interval` may compute
  a wait. A second scheduling expression would undo Phase 7's one-cadence property and Phase 8's
  widen-only rule in the same edit.
- `09-04` — *a pass that asked nothing never publishes a fresh verdict about anything.* A shorter
  tick must not turn `all([]) is True` into a routine green light.
- `09-05` — *a criterion is never reworded so that it passes.* MET IN PART and "not measured" are
  shippable outcomes here; a rounded-up claim is not.

### Threat model rows (ASVS L1, block on `high`) — honest, unpadded

This phase adds **no network surface**: it changes when local scheduling arithmetic fires and makes
no request. Three genuine rows, plus the reason there is no fourth.

| Threat ID | Category | Component | Severity | Disposition | Mitigation |
|---|---|---|---|---|---|
| `T-09-01` | Denial of Service | the shortened loop tick in `cli.watch_loop` | medium | mitigate | more wake-ups must not become more requests. The per-retailer daily request count is asserted unchanged over a simulated day (`09-04`), and the tick is floored so a single pass cannot outrun it — bounded by the last published `duration_seconds`, not assumed |
| `T-09-02` | Information Disclosure | the per-retailer phase derivation | low | mitigate | the phase is derived from the **retailer name and the configured roster only** — never from a hostname, a store id, a MAC, a wall clock or a process id. A phase derived from host identity would encode a stable host fingerprint in the request *timing*, and `scripts/identity_check.py` scans files, not timings, so nothing in this repository could ever see it |
| `T-09-03` | Tampering | `Pacer.load` over `pacer-state.json` | medium | mitigate | carried unchanged from Phase 8's `T-08-01`. This phase adds **no persisted field**, so no new `_HOSTILE` row is owed — and `09-04` must **confirm** that against `save`/`load` rather than assert it |

**There is no `T-09-SC` row, and that is stated rather than omitted.** The supply-chain row exists to
carry the package-legitimacy gate; this phase installs no package from npm, pip or cargo, so there is
nothing for the gate to audit.

**Residual carried, not fixed:** `pacer-state.json`'s write is a plain `write_text` rather than
temp-and-replace, so a second reader can catch a partial write. Carried v0.3 debt, failure direction
measured (it over-reports staleness, the safe way), explicitly not this phase's to fix.

### Standing constraints every plan inherits

1. **Watched red before trusted.** Each new gate: run it against the unfixed code, **record the
   actual failure count**, then fix and record the pass. `09-01`'s baseline simulation is the
   exception and must say so in its own words — it measures rather than gates, its subject is the
   code as it stands, and **that is the finding**, not a skipped formality. What carries the weight
   there instead is the asserted denominator, the independent tallies, and a literal transcribed
   from a run.
2. **Never round a claim up.** MET IN PART is shippable. Rewording a criterion so it passes is not.
3. **Superseded text is recorded beside, never edited away** — the module docstring's concession (b),
   `due`'s tolerance docstring, `config.py`'s cycle sentence and both colliding tests all take the
   dated-reversal form: quote the withdrawn text in full, then the measured facts that overruled it,
   then what survives.
4. **M43 is the next free ident. M21–M24 are never filled.** `grep -c "INTENTIONAL GAP"` is **8**
   today and must not fall. M43 anchors on **behaviour** — a line whose removal changes *when a
   request is made* — never on message text or a prose comment.
5. **Standing invariants that must not move:** `MAX_BACKOFF_SECONDS` stays `6 * 60 * 60`;
   `COOLOFF_SECONDS` stays `3 * 24 * 60 * 60` (259 200); `grep -c '<= STATE_MAX_AGE_SECONDS:'
   boty/pacing.py` stays exactly **2**.
6. **`cli.watch_loop`'s clock advances by `delay + cycle_duration`** as of `9ea42fe`, and **both
   terms survive this phase**. The delay term keeps the loop deterministic under the tests' fake
   `sleep`; the duration term stops the clock drifting behind wall clock. Each is defended by a named
   test (`test_the_pacer_clock_advances_by_the_time_the_check_pass_really_took`,
   `test_the_pacer_clock_is_still_deterministic_under_a_fake_sleep`). What this phase changes is the
   **size** of `delay`, never the shape of the sum.
7. **Never write `state.json`, `pacer-state.json` or `served/boty/status.json`.** Copy to a scratch
   dir. **Never run `boty check`. No live retailer request, at all.**
8. **No `systemctl restart boty` task.** That is Dan's call and is not a phase deliverable. Phase 8's
   deferred restart is still open and this phase adds to what that restart would carry.
9. `.venv/bin/python -m pytest`, never bare `python`. `export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh`
   before anything invoking `make`. `make verify-offline` exits 0 **and** its verdict line is read.
10. **Never invoke a `gsd-tools` state or phase WRITE subcommand.** Fourteen recorded corruptions of
    this repo's `STATE.md`, and the data-losing one survives on 1.11.0. Edit `STATE.md` by hand.
    **No plan in this phase edits `STATE.md` or `ROADMAP.md` at all.**

---

## Artifacts this phase produces

Every symbol, so the executor creates these and not near-misses. Names marked *(candidate)* are the
plan writer's to fix; the shape is not.

**`boty/pacing.py`**
- `MIN_TICK_SECONDS` *(candidate)* — the floor below which a tick cannot be outrun by one pass,
  defended at its definition site against the published `duration_seconds` bound
- `tick_for(default_interval, retailers)` *(candidate)* — **one expression**, read by both
  `cli.watch_loop`'s sleep and `Pacer`'s tolerance, on `_standing_interval`'s precedent
- `Pacer.roster` *(candidate)* — the configured retailer names; **declared last, defaulted empty**,
  so all 31 existing construction sites keep today's tolerance and today's birth phase (they do NOT
  keep today's advance — that change is unconditional)
- `Pacer.tick` *(candidate)* — same treatment, same reason
- `Pacer._phase_for(retailer)` *(candidate)* — deterministic from the name and the roster, never from
  `hash()`, never persisted
- `_RetailerState.due_at` — initialised to the retailer's phase in `_for` instead of `0.0`
- `Pacer.record` — the next attempt derived from the previous `due_at`, stepped by whole waits, never
  re-anchored to `now`
- `Pacer.due` — the tolerance re-anchored from `default_interval * 0.5` to the **tick**, with the
  original docstring's argument kept and its unit corrected
- **two dated notes, beside and never over** — one at `_RetailerState`'s leg 2 (a restart resets the
  schedule to 0.0; now it resets to the phase, at a price of one request within one standing interval
  rather than one immediate request) and one at the `state_path` paragraph's construction-site count
  (nine, exactly true at `46a0768` on 2026-08-10; now 24 of 26 in `tests/test_pacing.py` and 31
  tree-wide)
- **`Pacer.skipped_reason` — NOT edited.** It is collateral, not a site: it renders `due_at - now`, so
  its output moves with the advance while its logic must not. A repair that needs this method to
  change is the signal that the mechanism moved a cadence rather than a position
- **deliberately absent:** no new `_RetailerState` field, no `STATE_VERSION` bump, **no change to
  `current_interval`** — all three argued rather than merely not done

**`boty/cli.py`**
- `watch_loop` — one tick computed once through `tick_for`, passed to the pacer and slept; `delay +
  cycle_duration` untouched in shape
- `FAILURES_BEFORE_WARNING` / `FAILURES_BEFORE_GIVING_UP` — re-derived as durations or accepted in
  writing (`09-04`)

**`boty/status.py`**
- `"healthy"` — a pass that checked nothing must not publish `True` (`09-04`)

**`boty/config.py`**
- the `retailer_intervals >= interval_seconds` comment — dated reversal only; **the validator is
  untouched**

**`tests/`**
- `test_pacing.py` — the day-long six-retailer simulation (`09-01` before, `09-02` after), the ten
  enumerated tests closed in `09-02`, and in `09-03` the stated-seconds separation for criterion 1
  and the independence pair for criterion 2, both under the shipping construction
- `test_cli_watch.py` — two of the ten enumerated tests (`09-02`); the tick reaching the loop and
  both clock terms observed defended (`09-03`)
- `test_status.py` — a pass that asked nothing

**`scripts/mutation_check.py`**
- `Mutation(ident="M43", ...)` on the de-lockstep behaviour, with the prose block above it carrying
  what it rebuilds, why it earned an ident, and an `IF IT EVER SURVIVES:` paragraph

**New files**
- `.planning/phases/09-out-of-lockstep/09-DECISIONS.md` — the before-number, eight collisions, three
  test collisions, and the restart price
- `.planning/phases/09-out-of-lockstep/COVERAGE.md` — **already written at planning time**, one line.
  This departs from Phase 8, where `08-01` created it; it is stated here rather than left as a
  discrepancy. `09-01` **asserts** its content instead of creating it.

## OUTLINE COMPLETE
