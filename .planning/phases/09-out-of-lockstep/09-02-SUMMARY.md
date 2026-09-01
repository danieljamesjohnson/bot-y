---
phase: 09-out-of-lockstep
plan: 02
subsystem: pacing
tags: [pacing, scheduling, lockstep, tick, phase-offset, REQ-23]

requires:
  - phase: 09-out-of-lockstep
    plan: 01
    provides: "criterion 3's before-number (6), and 09-DECISIONS.md's eight collisions and three test collisions settled in writing"
provides:
  - "The mechanism: a deterministic per-retailer offset, a 50 s loop tick derived from one expression, and a `record` that advances on the retailer's own grid"
  - "Criterion 3's AFTER half: 2 of six retailers in any 60-second window over a simulated day, transcribed from a run and asserted strictly smaller than 09-01's recorded 6"
  - "The per-retailer daily counts asserted UNCHANGED against 09-01's tallies, with that assertion watched red"
  - "All seven reds this plan created, closed by name in the plan that broke them; three predicted reds recorded as findings for not appearing"
  - "A green tree for wave 3: make verify-offline exits 0"
affects: [09-03, 09-04, 09-05]

actuals:
  tokens: 74000
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "A schedule POSITION derived from config (name + roster) rather than stored, so it survives a restart without a STATE_VERSION bump"
    - "A fixed-rate advance stepped from the previous due time, so grace is never compounded into drift"
    - "A candidate sweep with a disqualifier (per-retailer counts must not move) rather than a preference"

key-files:
  created: []
  modified:
    - boty/pacing.py
    - boty/cli.py
    - tests/test_pacing.py
    - tests/test_cli_watch.py

key-decisions:
  - "READING A of the advance rule, chosen deliberately: step from the previous due time to the first grid point strictly in the future. Reading B re-anchors to the cycle clock in exactly the case a fixed-rate schedule exists to survive"
  - "The tick is 50 s — `default_interval / len(roster)`, floored at MIN_TICK_SECONDS = 30 — chosen from a ten-row measured sweep. It is the largest tick whose slots are all distinct, and every smaller one costs more wake-ups for a smaller separation"
  - "2 is criterion 3's after-number AND the arithmetic floor: 6 x 60 s > 300 s, so some 60-second window must hold two retailers. A claim of 1 would be unavailable"
  - "The plan's ten-test enumeration is 7 right of 10: six exactly right, one right under the wrong reading, three that did not redden. Recorded as findings rather than smoothed over"
  - "boty/config.py's two superseded sentences are NOT landed here — this plan's files_modified excludes that file, and the outline assigns it to 09-04. Recorded as a discrepancy between 09-DECISIONS.md collision 6 and the outline"

patterns-established:
  - "A defaulted construction site can keep a measuring test GREEN against code that changed under it: 09-01's simulation still read 6 against the landed mechanism until its pacer was given a roster and a tick"

requirements-completed: []

status: complete
---

# Phase 9 Plan 02: Out of Lockstep — The Mechanism, and the Number After

The six retailers now sit at **distinct positions on their own cadences** — a 50-second loop tick,
an offset derived from the retailer's name and the configured roster, and a `record` that steps from
the retailer's own previous due time instead of re-anchoring every retailer that fires together to
one clock. **Criterion 3's after-number is 2**, transcribed from a run, against 09-01's recorded 6,
with every retailer asked exactly as often as before. `make verify-offline` exits 0.

## The after-number

**2.** Transcribed from the failure message the moment the mechanism reached 09-01's own simulation,
not reasoned and then written down:

```
$ .venv/bin/python -m pytest tests/test_pacing.py -q -k max_retailers
>       assert max_in_any_60s == 6, (
E       AssertionError: the current rule put 2 of the six configured retailers (amazon, bestbuy,
E       gamestop, nintendo, target, walmart) inside a single 60-second window at least once over a
E       simulated day; the recorded before-number for criterion 3 is the literal in this assertion
E       assert 2 == 6

1 failed, 99 deselected in 0.12s
```

**Rewritten in place, not beside.** The fleet table, the denominator assertion, the sliding-window
computation, both tallies and the window model are byte-unchanged. What changed: the pacer is built
and stepped the way `cli.watch_loop` builds and steps one, and `_ONE_DAY_OF_CYCLES` moved 288 → 1728
(86 400 / 50 rather than 86 400 / 300) with the old value recorded beside it. The denominator
assertion is what holds the two apart — 1728 × 50 s must still be 86 400 s.

**2 is the arithmetic floor, not merely the best result measured.** Six retailers cannot be spread
more than 60 s apart inside a 300 s cadence, because 6 × 60 = 360 > 300. A plan claiming 1 would be
claiming something unavailable, and that is stated at `_AFTER_MAX_IN_ANY_60S` rather than left for a
later reader to wonder about.

**And it is smaller, written out as a comparison rather than as a claim about one number:**
`assert max_in_any_60s < _BEFORE_MAX_IN_ANY_60S` — the left side measured by the run, the right side
a dated record. A change that pushed the maximum back up fails there even if somebody edited the
after-literal to match it.

### The before-number is now a dated record rather than a re-runnable assertion

Stated plainly, per `09-DECISIONS.md` § *Test collision C*. The rule it describes no longer exists in
this tree. Freezing a hand-written reproduction of the old arithmetic to keep 6 re-runnable was
considered and rejected on 08-02's precedent: a re-runnable assertion over dead arithmetic looks like
evidence and is not.

## The advance rule: READING A, and why

**Chosen: reading A** — step the previous due time to the first grid point strictly in the future.

| | Reading A (taken) | Reading B (rejected) |
|---|---|---|
| Rule | `previous_due + ceil-to-future(wait)` | `previous_due + wait`, floored at `now + wait` |
| Under early firing | position preserved | position preserved (identical) |
| After a long or failed pass | position preserved | **re-anchors to the cycle clock** |
| Catch-up storm | none — arrears spent, not banked | none |

**The reason, written at `_next_on_the_grid`:** the only case that distinguishes them is a retailer
that has fallen behind — and re-anchoring a fallen-behind retailer to the cycle's clock *is* the
lockstep mechanism this phase removes. So B differs from A precisely where A exists.

**The collateral it carries.** The plan predicted reading A would additionally redden two tests
(items 7 and 8). **Neither reddened** — see the findings below. Reading A's actual collateral is the
six both-readings tests plus item 9, which the plan attributed to reading B alone.

## The tick: 50 seconds, chosen by measurement

Swept against the day-long six-retailer simulation, 2026-09-01, `interval_seconds` 300.
`max` is the most retailers in any 60 s window; `separation` is the smallest gap between two
**different** retailers over the day; the jittered column re-runs the same day with
`tick * uniform(0.85, 1.15)` under a fixed seed.

| tick | wakes/day | max in 60 s | max, jittered | min separation | per-retailer counts |
|---|---|---|---|---|---|
| 300 | 288 | 5 | 5 | **0 s** | unchanged |
| 150 | 576 | 3 | 5 | **0 s** | unchanged |
| 100 | 864 | 2 | 4 | **0 s** | unchanged |
| 75 | 1152 | 2 | 3 | **0 s** | unchanged |
| **50** | **1728** | **2** | **3** | **50 s** | **unchanged** |
| 37.5 | 2304 | 2 | 3 | 37.5 s | unchanged |
| 30 | 2880 | 2 | 3 | 30 s | unchanged |
| 25 | 3456 | 3 | 4 | 25 s | unchanged |
| 20 | 4320 | 3 | 4 | 20 s | unchanged |

**No candidate was disqualified for asking less** — every row left the per-retailer daily counts
unchanged, so the table is a choice between spreads and not between coverages.

**50 is the only row not beaten on some axis.**

- **Every larger tick has a separation of ZERO.** `slot_offset` lays slots at `index * tick` modulo
  the standing cadence, so `len(roster) * tick > default_interval` wraps two retailers onto the same
  position — at a 75 s tick, target sits exactly on amazon and walmart exactly on bestbuy. That still
  reads as a maximum of 2 in the window column, and it is exactly the coincidence this phase exists
  to remove. **A tick chosen on the window maximum alone would have picked 75 and shipped the
  defect.**
- **Every smaller tick** costs strictly more wake-ups for a smaller separation and no better
  maximum, and at 25 s and below the slots crowd into the head of the cadence and the maximum rises
  again.

The rule shipped is `default_interval / len(roster)` clamped at `MIN_TICK_SECONDS`, not the literal
50 — so a config with a different fleet gets the same argument rather than the same number.

**`MIN_TICK_SECONDS = 30.0`**, defended at its definition against the only instrument available
offline: the last published whole-pass figure, `duration_seconds: 20.43` for 13 watches, read
2026-08-31 by the phase-8 code review and **quoted rather than re-read**. That is one reading and not
a guarantee, and it is written that way. A tick's due set is a subset of that pass, so 20.43 s
over-estimates what a tick costs. The clamp is reachable — past ten configured retailers at a 300 s
default the slots wrap — and what happens there is named as degradation rather than left to be
discovered.

## The enumeration, measured before anything was repaired

```
7 failed, 916 passed in 12.48s
```

**Seven reds against ten predicted. All seven were on the list. No unlisted red appeared.**

| # | Test | Predicted | Observed |
|---|---|---|---|
| 1 | `test_pacing::test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring` | both readings | **RED** — `534600.0 == 21600` |
| 2 | `test_pacing::test_the_backoff_schedule_is_exactly_the_schedule_it_was[300.0]` | both readings | **RED** — `1800.0 == 1200.0` |
| 3 | `test_pacing::…[1800.0]` | both readings | **RED** — `10800.0 == 7200.0` |
| 4 | `test_pacing::test_one_good_read_clears_the_backoff_completely` | both readings | **RED** — `18900.0 == 300` |
| 5 | `test_pacing::test_a_retailer_that_answers_during_its_probe_is_back_on_its_standing_interval_at_once` | both readings | **RED** — `847800.0 == 1800.0` |
| 6 | `test_cli_watch::test_a_retailer_in_cooloff_publishes_the_days_scale_cadence_it_is_actually_on` | both readings | **RED** — `793800.0 == 259200.0` |
| 7 | `test_pacing::test_a_retailer_in_cooloff_says_so_rather_than_reporting_a_minute_count` | reading A | **GREEN — finding** |
| 8 | `test_cli_watch::test_a_refusal_the_backoff_is_handling_is_recorded_not_pushed_across_a_restart` | reading A | **GREEN — finding** |
| 9 | `test_pacing::test_a_retailer_at_the_default_cadence_is_due_every_cycle` | reading **B only** | **RED under reading A — finding** |
| 10 | `test_pacing::test_the_restored_pacer_starts_its_schedule_from_zero` | the birth offset | **GREEN — finding** |

### Findings, each with its cause

**Item 7 stayed green** because its assertions are on *prose*, not on a number. The grid advance
makes the remaining wait much larger at a frozen clock, and a larger days-scale wait still renders as
`days` and still contains `cooling off` and `30 refusal(s)`. `skipped_reason`'s output moved and none
of its assertions were about the part that moved.

**Item 8 stayed green** for a structural reason worth carrying to 09-03 and 09-04:
**`loop_tick_seconds` returns the standing interval for a one-retailer roster**, so every
single-retailer fixture in `tests/test_cli_watch.py` wakes at exactly the rate it woke at before.
The `_run(restart_cfg, cycles=10)` fixture still yields its measured 3 refusals for that reason, not
by luck. **A regression sweep built on single-retailer fixtures cannot fail for the reason it
exists.**

**Item 9 reddened under reading A**, not "reading B only" as the plan and the outline both state.
The two readings are *identical* in that test's regime: it steps `now` forward by 258 s while the
grid steps 300 s, so `previous_due + wait` is never in the past and B's floor never fires. The
distinguishing case for A vs B does not occur there. **The plan's attribution is wrong; its list is
still right, which is what mattered.**

**Item 10 stayed green** because `_pacer()` passes no roster, so the offset is 0.0 and `== 0.0`
passed **vacuously**. It was repaired anyway, exactly as `09-DECISIONS.md` § *Test collision B*
requires, and the repair moved it to `walmart` — because `amazon` sorts first in the six-retailer
roster and its offset *is* 0.0, against which `== 0.0` and `== slot_offset(...)` are the same
assertion and neither has a subject.

### And 09-01's own simulation stayed green too, which is the finding worth keeping

`test_the_max_retailers_in_any_sixty_seconds_over_a_day_is_a_stated_number` **still read 6 against
the landed mechanism.** `09-DECISIONS.md` § *Test collision C* predicted it would go red on its own
and be this plan's watched-red evidence. It did not: it built a defaulted `Pacer` and stepped once
per cadence, which reproduces the old schedule exactly on the new code. It went red only once its
pacer was given a roster and a tick.

**That is `09-DECISIONS.md`'s own "a green defaulted site proves nothing about the schedule the
daemon runs", arriving as a number rather than as an argument** — and it is a direct instruction to
09-04, whose sweep must assert under the shipping construction or it is a sweep over a shape nobody
runs.

## How each red was closed

**Re-pointed assertions (items 1–6)** — the behaviour is unchanged and only the arithmetic's anchor
moved. Every one of these tests drives `record` repeatedly at a **frozen `now`**, which is not a
schedule the loop can produce; under the grid advance the waits accumulate instead of re-anchoring.
Each assertion is re-pointed at the **increment** from the retailer's own previous due time, which is
the same number the test always asserted, read from the anchor the schedule now uses.

**No repair weakens a Phase 8 claim.** The cap's ceiling assertion `MAX_BACKOFF_SECONDS <= 6*60*60`
survives untouched; the cool-off's 259200.0 literal survives untouched at every site; the backoff
depth literals in `_CADENCE_AFTER_N_REFUSALS` are unchanged. **`skipped_reason`'s logic was not
touched** — `09-DECISIONS.md` names that as the signal that the mechanism moved a cadence rather than
a position, and it did not fire.

Item 6 additionally now builds its pacer with a roster and a tick, because its own comment claims it
is *"built exactly as `watch_loop` builds one"* and that claim had gone false.

**Dated reversals (items 9 and 10)** — the withdrawn assertion is quoted in full, what overruled it
is named with its measurement, what survives is stated, and both names are kept so `git log -S`
still reaches their history.

- **Item 9 (collision A):** *the unit went wrong and the fear did not.* A retailer at the default
  cadence is due once per **cadence**, not once per **wake** — being due every wake would now mean
  asking a 300 s retailer six times per cadence. The coverage half is carried forward as a **count
  over a day of short-jitter wakes** (the adversarial case, kept verbatim in its new unit): 288, the
  number a 300 s cadence implies.
- **Item 10 (collision B):** re-pointed at the offset and only the offset — *a number this process
  computed from the retailer's name, not one a previous process left behind*. Strictly stronger than
  `== 0.0`, since 0.0 is also what a truncated document produces. Two further assertions carry
  collision 2's withdrawn *"tries once, immediately"*: **not** due at t=0, and due within one
  standing interval.

## The per-retailer counts are unchanged, and that assertion was watched red

```
assert per_retailer == _BEFORE_PER_RETAILER
```

against 09-01's recorded tallies as literals (`amazon` 48, `gamestop` 96, the default group 288
each), **beside** the pre-existing check derived from `86400 // interval`. Two independent statements
of the same expectation.

**Watched red on purpose**, by perturbing the mechanism to spread by lengthening a wait rather than
by moving a position (`_standing_interval` doubled), from a cleared bytecode cache:

```
>       assert per_retailer == _BEFORE_PER_RETAILER, (
E       AssertionError: over the same simulated day each retailer was asked {'amazon': 24,
E       'bestbuy': 144, 'gamestop': 48, 'nintendo': 144, 'target': 144, 'walmart': 144}, against the
E       {'amazon': 48, 'bestbuy': 288, 'gamestop': 96, 'nintendo': 288, 'target': 288,
E       'walmart': 288} the OLD rule produced. A smaller maximum bought with a smaller count is
E       coverage sold for a number
E       assert {'amazon': 24, ...} == {'amazon': 48, ...}

1 failed, 99 deselected in 0.13s
```

**The finding is which assertion fired.** The maximum literal sits four assertions earlier in the
same test and **still read 2 and passed** while every retailer was asked half as often. This
reproduces 09-01's result — the count is blind to a reduction achieved by not asking — on the after
side of the same test. Full file under the perturbation: **27 failed, 73 passed**. Reverted, cache
cleared, `100 passed` restored.

## The tracer's two reds

Both from a cleared bytecode cache, per the trap `09-01` recorded.

| Perturbation | Assertion that fired | Observed |
|---|---|---|
| `slot_offset` returns 0.0 (no offset, advance kept) | the birth separation | `assert 0.0 == 150.0` — 1 failed, 1 passed |
| grid advance dropped (`now + wait`), offset kept | the after-five-requests separation | `assert 142.5140080407059 == 150.0` — 1 failed, 1 passed |

**The second red is collision 3's evidence and it corrected the planning-time claim.** The outline
said a birth offset alone *"collapsed back to six-in-a-window within a simulated day"* in a throwaway
`/tmp` model, and said every number from that model had to be re-measured against real code. Measured
here against the real `Pacer`:

| Mechanism | max in 60 s, unjittered | max in 60 s, jittered |
|---|---|---|
| offset only, `now + wait` advance | 2 | **4** |
| offset + grid advance (shipped) | **2** | **3** |

**The offset-only fleet does not collapse all the way to 6 — it collapses to 4**, and on the
two-retailer tracer over a day it does not merge at all (separation random-walked between 127.6 s and
170.5 s, never reaching zero). The erosion is real and measurable at five requests each (142.5 s
against 150), and the six-retailer figure is the honest statement of what the second term buys:
**4 → 3 under jitter, and the difference between a schedule that holds and one that wanders.**

## The jittered figure, recorded beside the criterion-3 number rather than hidden

Criterion 3's simulation steps a fixed tick, exactly as 09-01's stepped a fixed 300 s — that is what
makes 2 and 6 comparable. **Under the loop's real ±15% wake jitter the same day measures 3**, because
two retailers 50 s apart on the schedule can occasionally be dispatched at the same wake when a sleep
runs long. The schedule separation is 50 s at every point regardless; the dispatch figure is 3.
**Both are smaller than 6**, and the comparable pair is 2 against 6.

## The two falsified comments, dated beside and never over

Per `docs/retailer-evidence.md` § 6.

**(a) `_RetailerState`'s leg 2.** The withdrawn clause is quoted in full — *"and across a restart
`due_at` resets to 0.0 by design, which is decided and priced at one immediate request"*. After this
phase a restart resets to the retailer's **offset**, priced at one request within one standing
interval (≤ 300 s for the default group, ≤ 1800 s for amazon). Nothing is re-tested less often, only
later within the same interval. The compensating fact is recorded beside it. **Leg 2's conclusion
survives whole** — `record` re-schedules unconditionally on every outcome, so the probe still cannot
repeat inside a process and no flag is owed. Only the number beside it moved.

**(b) The `state_path` paragraph's construction-site count.** *"There are nine in
`tests/test_pacing.py` alone and not one names a path."* — **exactly true when written**, at
`46a0768` on 2026-08-10: eleven sites, two naming a path, nine not.

Measured by AST over every tracked `.py` file (`ast.Call` with `func.id == "Pacer"`, `.venv`
excluded), **after this plan's commits**:

| | |
|---|---|
| Tree-wide | **35** — 30 in `tests/test_pacing.py`, 3 in `tests/test_cli_watch.py`, 2 in `boty/cli.py` |
| Naming no `state_path` | **27**, all in `tests/test_pacing.py` (27 of 30) |
| Distinct keyword signatures | **8** |
| Distinct normalised call texts | **16** |

The argument the sentence serves is **strengthened**: the number of sites a default protects went up,
and this plan adds two more defaulted fields on the strength of it.

**And this note went stale inside its own plan, which is recorded rather than quietly fixed.** It was
first written quoting 32 / 27 / 25-of-27 — true after 09-01 and before this plan's own test edits —
and corrected to the post-plan figures in a separate commit (`8ec3b12`) once they were measured.
Both earlier measurements are kept beside the current one.

## What did NOT move

- **`Pacer.current_interval`'s body is byte-unchanged**, proved against the recorded digest rather
  than by a diff:
  `6da39ac5d77ecd98cae80651c3b4d539253e88a1704fb4b1e814e6bf93449108` — **MATCH**. A phase is a
  position, never a duration.
- **`save` and `load` are untouched.** `git diff 8bebb63..HEAD -- boty/pacing.py` contains no hunk
  inside either method, no `STATE_VERSION` change, and **no new `_RetailerState` field** — the two
  new fields are on `Pacer` and both are defaulted. Phase 8's refused bump is not reopened. 09-04
  must still CONFIRM this by inspection rather than inherit the claim.
- **The standing invariants, by command:**
  ```
  $ grep -n "MAX_BACKOFF_SECONDS = \|COOLOFF_SECONDS = " boty/pacing.py
  156:MAX_BACKOFF_SECONDS = 6 * 60 * 60
  224:COOLOFF_SECONDS = 3 * 24 * 60 * 60
  $ grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py
  2
  ```
- **Both terms of the pacer clock.** `scheduled_now += delay + cycle_duration` is unchanged; only the
  size of `delay` moved, and the comment block says so rather than leaving it to inheritance.
  `cycle_started` is still before the `try`, and the sleep is still not folded into the duration.
  `tests/test_cli_watch.py::test_the_pacer_clock_is_still_deterministic_under_a_fake_sleep` passes.
- **The grid advance is not gated on a non-empty roster** — horn 2 refused, and the `Pacer` fields'
  own comment says plainly what the defaults do and do not cover.
- **Nothing host-derived and no `hash()`** enters the offset. Sorted position in the roster only,
  argued at `slot_offset` with the `PYTHONHASHSEED` reason stated as a measured fact.

## The gate

`make verify-offline`, nvm sourced first. **Real exit code 0.** Verdict line, verbatim:

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

The OFFLINE pass, as expected — **not INCOMPLETE**, so no control was reported unverifiable on this
host.

| Stage | Reading |
|---|---|
| identity check | PASS — 255 file(s), no host identity found |
| lint (ruff) | All checks passed! |
| tests | **923 passed** in 11.58 s, `-rs` on, **no skip summary at all — zero skips** |
| types (mypy) | Success: no issues found in 18 source files |
| fixtures | 11 fixture(s) |
| mutation | **38/38 mutations caught** |

| Measurement | Before this plan | After |
|---|---|---|
| Suite collected | 921 | **923** |
| `tests/test_pacing.py` | 98 | **100** |
| `tests/test_cli_watch.py` | 47 | 47 |

**No red is handed to wave 3.**

## What this plan does NOT claim

- **Criterion 5 is NOT discharged.** No mutation was registered and none was observed CAUGHT.
  **M43 is still free**, and `grep -c "INTENTIONAL GAP" scripts/mutation_check.py` is still **8**.
  The green gate above is a regression check.
- **Criteria 1 and 2 are 09-03's.** The 50 s separation is measured here and asserted only
  incidentally (the tracer asserts 150 s on a two-retailer roster); the stated separation literal and
  the independence-in-both-directions assertions are wave 3's.
- **Criterion 4 is untouched.** No `boty check` budget was measured, and no aggregate-request-rate
  claim is made beyond the per-retailer counts above.
- **The wake rate rose six-fold and its costs are NOT paid here.** 288 → 1728 wakes/day. Collision 4
  (an empty tick publishing a vacuously green `healthy`), collision 5 (the two failure counters are
  counts of cycles) and the write rate are **09-04's**, and they are now live rather than latent:
  at a 50 s tick most wakes ask nobody.

## Deviations from Plan

**1. [Finding, not a defect] The plan's ten-test enumeration is 7 right of 10**

Documented in full in *The enumeration* above: six exactly right, item 9 right but attributed to the
wrong reading, items 7, 8 and 10 predicted red and observed green. Every red observed was on the
list; nothing unlisted appeared. The plan's own instruction — *"a test on the list that did NOT go
red is also a finding"* — is what this discharges.

**2. [Plan/decisions discrepancy, flagged not resolved] Who lands `boty/config.py`'s two notes**

`09-DECISIONS.md` § *Collision 6* says **"`09-02` lands both notes"** for `_retailer_intervals`'
withdrawn *"the loop sleeps `interval_seconds` per CYCLE"* sentence and its 750 s magnitude. The
outline's plan table assigns that file to **09-04** (*"`config.py`'s 'the loop sleeps
interval_seconds per CYCLE' went false"*), and **this plan's `files_modified` does not include
`boty/config.py`** — so landing it here would have broken the plan's own scope fence. **Not landed.**
The magnitude half is recorded at `Pacer.due`'s docstring instead, where it belongs, with a pointer
saying the `config.py` note is 09-04's.

**3. [Rule 1 - measurement correction] The under-report magnitude in collision 6 needed restating**

Collision 6 says this phase *"shrinks"* the 900-vs-750 under-report. Measured: it does not shrink it,
it **removes the sustained part of it**. The old under-report compounded because `record` re-anchored
to `now`, so each cycle's 150 s of grace became the next cycle's starting point. The grid advance
steps from the previous **grid point**, so the long-run count is exactly the published cadence and
the residual is one early firing of at most half a tick. Stated that way at `Pacer.due` rather than
inheriting the weaker word.

**4. [Rule 1 - bug in this plan's own first draft] A day's request count is not a whole number unless the day is cut where the schedule is**

The tracer first counted requests by **wake** and read `{'bestbuy': 289, 'walmart': 288}` — an
asymmetry produced entirely by where the final wake landed under the seed, because `due`'s grace can
dispatch day two's first grid point inside the last half-tick of day one. Fixed by counting the
**grid point served** rather than the wake that serves it, with the measured 289 recorded at the site
so the next reader does not rediscover it. The same rule is applied in the collision-A rewrite.

**5. [Rule 3 - blocking] `make verify-offline` failed on lint before it could run**

`ruff` C416: `names = {r for r in roster}` in `loop_tick_seconds`. Rewritten as `set(roster)`. Caught
by the gate, fixed, gate re-run green.

**6. [Recorded, deliberately NOT fixed] The stale-`.pyc` trap still is not in `CLAUDE.md`**

`09-01` handed it forward; this plan's `files_modified` does not include `CLAUDE.md` either, so it is
handed forward again. **It was used throughout this plan** — every perturbation and revert cleared
`__pycache__` and `.pytest_cache` first — and it earned its keep: three of this plan's four
red-watches were same-length or near-same-length edits reverted within seconds, which is exactly the
shape the hole swallows. A later wave in this phase should land it.

## Nothing live was touched

No live retailer request was made. **`boty check` was not run.** `make verify` — the unqualified
target with live controls — was deliberately not run. `state.json`, `pacer-state.json` and
`served/boty/status.json` were neither read nor written; the `duration_seconds: 20.43` figure is
**quoted** from the phase-8 record. No `systemctl restart boty`. **`boty` was not restarted, and the
daemon is still running the pre-REQ-23 schedule** — this is an editable install, so the code is in
the tree and a restart is the user's call.

## STATE.md and ROADMAP.md were NOT updated

Deliberately, per this executor's instructions: the orchestrator owns those writes. **No `gsd-tools`
state or phase WRITE subcommand was invoked at any point** — `state.advance-plan`, `state.begin-phase`
and `phase.complete` are banned in this repo on fourteen recorded corruptions.

## Commits

| Commit | What |
|---|---|
| `1329d24` | `feat(09-02): give each retailer its own position on the schedule` |
| `8df700d` | `docs(09-02): choose the tick by measurement, not by preference` |
| `ffeafa3` | `test(09-02): close every red this plan created, and state the after-number` |
| `8ec3b12` | `docs(09-02): date the construction-site count against the tree this plan leaves` |

Git identity checked **before** committing: `3347065+danieljamesjohnson@users.noreply.github.com`,
the repo's configured no-reply identity. **No commit used `--no-verify`**; the tracked pre-commit
identity hook passed on every one.

## Self-Check: PASSED

- `boty/pacing.py` — FOUND; `current_interval` body digest **MATCHES** the recorded literal;
  `roster` and `tick` present as the last two `Pacer` fields; `MIN_TICK_SECONDS`,
  `loop_tick_seconds`, `slot_offset`, `_next_on_the_grid` all present
- `boty/cli.py` — FOUND; contains `cycle_duration`, and `scheduled_now += delay + cycle_duration`
  intact
- `tests/test_pacing.py` — FOUND; contains `_ONE_DAY_OF_SECONDS`, `_AFTER_MAX_IN_ANY_60S = 2`,
  `_BEFORE_MAX_IN_ANY_60S = 6`, `_BEFORE_PER_RETAILER`; **100 passed**
- `tests/test_cli_watch.py` — FOUND; contains `cooloff`; **47 passed**
- Commits `1329d24`, `8df700d`, `ffeafa3`, `8ec3b12` — all FOUND in `git log`
- `make verify-offline` — real exit code **0**, verdict line quoted above
- Scope fence: `git diff --name-only 8bebb63..HEAD` lists exactly `boty/cli.py`, `boty/pacing.py`,
  `tests/test_cli_watch.py`, `tests/test_pacing.py` — this plan's `files_modified`, by equality
