---
phase: 09-out-of-lockstep
plan: 04
subsystem: status
tags: [status, pacing, scheduling, health-verdict, criterion-4, REQ-23, T-09-04]

requires:
  - phase: 09-out-of-lockstep
    plan: 02
    provides: "the 50 s tick, the per-retailer slot offset and the grid advance — the change whose costs this plan prices"
  - phase: 09-out-of-lockstep
    plan: 03
    provides: "the daemon's new wake and write rates as DERIVED numbers, for this plan to re-measure and correct"
provides:
  - "T-09-04 mitigated: a pass that asked nobody publishes `healthy: null`, not a vacuous green — proved reachable through `cli.watch_loop`, and proved not to over-reach into either ordinary case"
  - "Both failure thresholds re-derived from DURATIONS, so 15 minutes to a push and 50 to a give-up survive the tick change instead of becoming 2.5 and 8.3"
  - "Two dated reversals in `boty/config.py`, validator proved untouched by an AST body hash across the whole phase"
  - "Criterion 4's FIRST HALF: per-retailer daily counts asserted through `cli.watch_loop` over a full simulated day, and Phase 8's backoff/cool-off asserted under the construction the daemon ships"
  - "No persisted structure added, CONFIRMED by byte-comparing `save`/`load` across the phase and by round-tripping a document in both directions"
  - "The tick's cost MEASURED before and after, correcting two rows of 09-03's derived table"
affects: [09-05]

actuals:
  tokens: 14745
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "A three-valued aggregate: `null` for 'nobody was asked', taking the shape the module already argued for its per-retailer rows rather than inventing one"
    - "A threshold stated as a DURATION with the count derived from the loop's tick, so a scheduling change cannot silently multiply how fast a monitor pages a human"
    - "A regression sweep bound to the loop's own construction by a helper the loop is asserted against, so the sweep cannot drift onto a shape nobody runs"

key-files:
  created: []
  modified:
    - boty/status.py
    - boty/cli.py
    - boty/config.py
    - tests/test_status.py
    - tests/test_cli_watch.py

key-decisions:
  - "`healthy: null` rather than a new key. The published key set is unchanged; what the existing key can SAY changed. A consumer forced to learn a new key is a bigger change than this problem needs"
  - "The two failure counters are RE-DERIVED, not accepted. The warning pushes to a phone and 09-02 made a restart more expensive, so the two changes push the same way and inheriting the count would have compounded them"
  - "The durations are derived FROM the two count literals times a named reference cycle, so the counts stay the authority and there is nothing to keep in step"
  - "Phase 8's three numbers are written out in the sweep rather than imported. Measured: reading them from `boty.pacing` left the gate green under a perturbation of the very constant it was checking"
  - "The empty-wake reachability test needed its own fixture. `fleet_cfg` is left exactly as 09-03 built it — re-pointing a fixture underneath somebody else's evidence is how a green suite stops describing what it described"

patterns-established:
  - "An unseeded jitter measurement read once is a flake shipped as a gate. A 20-seed sweep licenses the seed rather than the seed hiding behind it"

requirements-completed: []

status: complete
---

# Phase 9 Plan 04: Out of Lockstep — Paying for the Tick

`boty/status.py` computed `healthy` as `all(h.ok for h in health)` and **`all([]) is True`**. Before
09-02 an empty pass needed the whole fleet backed off at once; after it, **26.4% of wakes ask
nobody**. A quarter of every day's documents were about to assert the fleet healthy on the strength
of a pass that ran no check. That is fixed, proved reachable, and proved not to over-reach.

Both failure counters are re-derived from durations. Two dated reversals landed in `boty/config.py`
with the validator's body hashing byte-identical across the phase. Criterion 4's first half is
asserted through `cli.watch_loop` over a whole simulated day. `make verify-offline` exits 0.

---

## What `healthy` publishes now

| The pass | `healthy` | Why |
|---|---|---|
| asked somebody, all fine | `true` | unchanged |
| asked somebody, something failed | `false` | unchanged |
| **asked nobody** | **`null`** | not healthy (nothing verified), not unhealthy (nothing failed) — simply not asked |

**The third state is this module's own, not a new invention.** `status.write`'s docstring already
argues it twelve lines above the defect, for the per-retailer rows: *"the retailer is not healthy
(nothing was verified) and not unhealthy (nothing failed) — it simply was not asked."* The comment ON
the flag already said it is *"Only over retailers actually CHECKED"* — which is exactly why an empty
checked-set has no verdict to give. `duration_seconds` and `current_interval_seconds` already publish
`null` for "never established", in the same payload.

**`null` and NOT `false`,** which is the half a reader in a hurry gets wrong and the plan's second
prohibition. `false` on an idle tick reports the fleet broken 457 times a day, and a flag that cries
wolf on an idle tick is a flag nobody reads. Asserted as its own test.

**The key set does not move.** `test_publishing_a_duration_does_not_disturb_any_existing_key` is
untouched, and a second assertion pins the same enumerated set on the EMPTY pass — the case that
would have been the tempting place to add `checked_any` and change the contract on 1728 documents a
day.

### The blast radius, measured — and PLANNING'S COUNT WAS ONE SHORT

`grep -rn healthy` over `boty/`, `scripts/`, `served/`, `tests/`, `docs/`, `config/`, `Makefile`,
`README.md`:

| Site | What | Effect |
|---|---|---|
| `boty/status.py:154` | the only PRODUCER | changed |
| `served/boty/index.html` | **no match, `grep` exit 1** | the dashboard does not read the flag — confirmed, not trusted |
| `tests/test_status.py:217` | the key-set assertion | unaffected, the key stays |
| `tests/test_status.py:249` | `assert payload["healthy"] is True` | unaffected, health is non-empty there |
| **`tests/test_pacing.py:1037`** | **`assert payload["healthy"] is True`** | **NOT in planning's list.** Unaffected — its pass checks walmart — but it is a third reader |
| `tests/test_dashboard.py:763` | a fixture BUILDING a `status.json` with `healthy: True` | not a reader of the semantics; recorded so the next grep is not surprised |

**Planning on 2026-09-01 named two readers and there are three.** The resolution did not have to
widen — the third asserts the ordinary green case with a non-empty health list — but the count was
wrong and a plan that had needed the count to be right would have been wrong with it.

`served/boty/status.json` also matched (`"healthy": false`, line 3). That file was **read by a
recursive grep and never written**; it is a published artifact and the match is a value, not a
consumer.

### Reachability: proved through the loop, and the fixture question was measured twice

A guard nobody can reach is a guard with no subject.
`test_a_wake_that_asks_nobody_is_reachable_at_the_shipping_tick` drives `cli.watch_loop` and reads
each wake's published document through the loop's own `sleep`.

**The first two answers this section gave were both wrong, and the corrections are the finding.**

**Wrong answer 1.** The test used `fleet_cfg` — six retailers, all on the 300 s global cadence — for
24 wakes, and every wake asked exactly one:

```
E  AssertionError: no wake in 24 asked nobody … retailers asked per wake was
   [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
```

Six retailers at 300 s on a 50 s grid fill 6 × 50 = 300 s **exactly**: the grid is saturated. The
idle wakes come from the LONGER cadences — `amazon` at 1800 s and `gamestop` at 900 s hold a slot
each and use it once every 36 and 18 wakes. **The idle tick is a consequence of the fleet's SHAPE,
not of the tick alone** — the same finding 09-02 recorded about single-retailer fixtures, one level
along.

**Wrong answer 2, and it was written down before it was measured.** *"Under a uniform fleet the idle
wake does not exist"* survived one unseeded run and died on the next:

```
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1]
```

The loop jitters every wake ±15%, so a wake can drift past a slot's 25 s tolerance and the next
collects two. An `== [1] * 24` assertion would have been **a flake shipped as a gate**.

**The measurement that replaced both**, 20 seeds × 200 wakes each:

| fleet | idle-rate min | max | mean | first idle wake |
|---|---|---|---|---|
| uniform (all six at 300 s) | 0.015 | 0.075 | **0.035** | 7 to 122, varies by seed |
| configured (`products.yaml`'s cadences) | 0.250 | 0.285 | **0.269** | **6 in 19 seeds of 20**, else 7 |

Structural on one, accidental on the other, by an order of magnitude. `configured_fleet_cfg` was
added; **`fleet_cfg` is left exactly as 09-03 built it**, because re-pointing a fixture underneath
somebody else's evidence is how a green suite stops describing what it described. Both new tests are
seeded (`_IDLE_SEED = 20260901`) and the sweep above is what licenses the seed rather than what it
hides behind.

---

## Every red, with its count

Every perturbation was applied to a `cp`-restored file with `__pycache__` and `.pytest_cache`
**cleared between perturbation and revert** — the trap 09-01 recorded and 09-02 and 09-03 used.
`git diff --stat` confirmed the file restored after each.

### Task 1 — the empty-pass verdict

| # | Perturbation | Assertion that fired | Count |
|---|---|---|---|
| **A** | **none — the UNFIXED code** | `a pass that produced no health entries published the ordinary GREEN verdict … published 432 times a day` | **2 failed, 56 passed** |
| **B** | **the unfixed flag, seen through the LOOP** | `wake 6 asked none of the six configured retailers and published healthy=True` | **1 failed, 50 passed** |
| C | `None if (not health or paced) else all(...)` | over-reach, healthy side — `stopped publishing the ordinary green verdict` | 1 failed, 57 passed |
| D | `True if (health and all(...)) else None` | over-reach, unhealthy side — `stopped publishing the ordinary red verdict` | 1 failed, 57 passed |
| E | `bool(health) and all(...)` — the opposite lie | `an empty pass published the ordinary UNHEALTHY verdict` | 3 failed, 55 passed |
| F | a fourth key `"asked"` instead of a third state | the key-set assertion | 2 failed, 56 passed |
| G | `configured_fleet_cfg` loses the overrides | `the configured fleet idled on 1.0% of 200 wakes, under the 20% floor` + reachability | 2 failed, 49 passed |
| H | `loop_tick_seconds` returns the standing cadence | the tick assertion + both idle assertions | 4 failed, 47 passed |

**RED A is the only one whose subject is the code as it stood.** C, D, E and F have no subject
against the unfixed code — their subject is an over-reaching FIX, which is why each was watched red
against a deliberately over-reaching version rather than counted as evidence for the fix itself.
Stated plainly rather than folded into a total.

### Task 2 — the two thresholds

| # | Perturbation | Assertion that fired | Count |
|---|---|---|---|
| **E2** | **the counters INHERITED as counts (the pre-fix behaviour)** | `the monitor pushed before 15 minutes of blindness had passed — 17 cycles at a 50s tick is 14 minutes` | **2 failed, 54 passed** |
| F2 | `round` instead of `ceil` | `2.25 cycles must round UP to 3` | 1 failed, 55 passed |
| I | `int()` truncation instead of `ceil` | the same assertion | 1 failed, 55 passed |
| **H2** | **the durations re-sized against the NEW tick (accepting the acceleration)** | four assertions, including two PRE-EXISTING single-retailer tests | **5 failed, 51 passed** |
| **G2** | **the `max(1, ...)` floor removed** | **NOTHING — 56 passed** | **finding, below** |

**H2 is the one worth reading twice.** Re-sizing the durations to the new tick — the "accept it in
writing" option — reddens `test_a_transient_failure_is_tolerated` and
`test_a_recovery_resets_the_failure_count`, two tests written long before this phase. The identity
property at the 300 s reference cycle is defended by tests nobody wrote for it.

### Task 3 — criterion 4's sweep

| # | Perturbation | Assertion that fired | Count |
|---|---|---|---|
| J | `_standing_interval` doubled — spread by lengthening a wait, not by moving a position | `test_each_retailer_is_asked_the_same_number_of_times_a_day_as_before` + 9 others | 10 failed, 50 passed |
| L | the pre-09-02 tolerance (`default_interval`, not the tick) | the day-long counts + the idle-rate comparison | 2 failed, 58 passed |
| M | the loop stops handing its pacer a roster | `test_the_shipping_pacer_is_built_the_way_the_loop_builds_one` + 2 | 3 failed, 57 passed |
| **K** | **`REFUSALS_BEFORE_COOLOFF` 30 → 31, FIRST DRAFT** | **NOTHING — 60 passed** | **finding, below** |
| K | the same, after the literals were written out | the binding test + the ladder + the probe | 3 failed, 58 passed |
| K2 | `COOLOFF_SECONDS` 3 days → 2 | 4 tests including a pre-existing one | 4 failed, 57 passed |
| K3 | `MAX_BACKOFF_SECONDS` 6 h → 12 | the binding test + the ladder | 2 failed, 59 passed |

---

## Three findings that cost a rewrite each

### 1. The cool-off sweep read the constant it was checking

The first draft of `test_the_backoff_ladder_and_the_cooloff_hold_under_the_shipping_construction` and
`test_a_cooled_off_retailer_is_probed_exactly_once_over_a_window_at_the_new_tick` imported
`REFUSALS_BEFORE_COOLOFF` and `COOLOFF_SECONDS` from `boty.pacing`. Perturbing the threshold 30 → 31:

```
=== RED K (first draft) ===
60 passed in 1.55s
```

**Every assertion moved with the constant it was supposed to be checking.** That is
`_CADENCE_ACROSS_THE_COOLOFF_THRESHOLD`'s own rule — *"a number derived from the constant under test
cannot contradict it"* — rediscovered by measurement rather than inherited. Rewritten with
`_COOLOFF_THRESHOLD_REFUSALS = 30`, `_COOLOFF_SECONDS_LITERAL = 259200.0` and
`_MAX_BACKOFF_LITERAL = 21600.0` written out, plus one separate test binding them to the module
constants so the two cannot drift apart silently. The same perturbation now reddens 3.

### 2. The `max(1, ...)` floor was unreachable and is deleted, not commented

`failures_before` was written `max(1, math.ceil(seconds / tick))`. Removing the floor:

```
=== RED G2 ===
56 passed in 0.88s
```

`ceil` over any positive duration already returns at least 1 — `ceil(900 / 100000) == 1`. The floor
defended nothing `ceil` was not already defending, which is `scripts/mutation_check.py`'s own rule
about a break already caught by a second independent test. **Deleted rather than left as a comment
that will be believed**, on `REFUSALS_BEFORE_PAGING`'s precedent in the same file, with the
measurement recorded at the site. The `== 1` assertions are kept and now bind `ceil`'s floor
directly, where they do fire (under both `round` and `int()`).

### 3. 09-02 was assigned collision 6's two `config.py` notes and landed NEITHER

`git log --oneline -1 -- boty/config.py` at the start of this plan read `1092940 fix(07)` — **before
this phase began.** `09-DECISIONS.md` § *Collision 6* says *"`09-02` lands both notes"*. The
pacing-side half of the same collision WAS landed by 09-02, at `pacing.due`, so **the two halves of
one decision sat one commit apart and disagreed with each other for the length of the phase**: one
file said the tolerance is half a tick, the other still said half the default interval.

Both landed here. Recorded as a deviation below.

---

## The two thresholds: what was preserved and what it cost

**Resolution taken: RE-DERIVED, not accepted.** The reasoning is at `cli.failures_before`, not in a
planning document.

| | count | wall clock |
|---|---|---|
| at the 300 s reference cycle (`FAILURES_BEFORE_WARNING`) | **3** | **15 min** |
| at the 300 s reference cycle (`FAILURES_BEFORE_GIVING_UP`) | **10** | **50 min** |
| at the fleet's 50 s tick, warning | **18** | **15 min** |
| at the fleet's 50 s tick, give-up | **60** | **50 min** |
| what INHERITING the counts would have given, warning | 3 | **2.5 min** |
| what INHERITING the counts would have given, give-up | 10 | **8.3 min** |

**Why not acceptance.** Two reasons that push the same way:

- **The warning pushes to a phone.** `_warn_monitor_is_stuck`'s docstring earns that send by arguing
  it is *"RARE BY CONSTRUCTION"* — and rare was doing real work in that sentence. Three raising
  cycles at 300 s is a quarter-hour of total blindness, a fact about the service. Three at 50 s is
  150 seconds, which a transient DNS failure produces. Multiplying the paging rate by six as a side
  effect of a scheduling change is the `notify-dan` bar failing in the direction this repository
  cares about most.
- **Giving up costs MORE than it used to**, and this is the half a reader misses. The exit is so the
  supervisor restarts — and since 09-02 a restart **re-phases every retailer**, delaying some first
  checks by up to one standing interval (300 s for the default group, 1800 s for amazon;
  `09-DECISIONS.md` § *Collision 2* prices it). So a restart is a more expensive event after this
  phase, at exactly the moment the threshold would have started firing six times sooner.

**Single-sourced.** `WARN_AFTER_SECONDS` and `GIVE_UP_AFTER_SECONDS` are DERIVED from the two count
literals × a named `_REFERENCE_CYCLE_SECONDS = 300.0`. The counts stay the authority; editing either
moves its duration; there is nothing to keep in step. At the 300 s reference the derivation is the
**identity**, which is why every single-retailer test in `tests/test_cli_watch.py` still exercises
the exact thresholds it was written against — 09-02's finding that `loop_tick_seconds` returns the
standing interval for a one-retailer roster, put to work.

`_warn_monitor_is_stuck`'s "three consecutive raising cycles" sentence is **kept and dated**, not
edited away.

---

## `boty/config.py`: two dated reversals, and the validator proved untouched

**The withdrawn sentence, quoted in full** (and left in place above its reversal):

> `cli.watch_loop` sleeps `interval_seconds * uniform(0.85, 1.15)` per CYCLE, not per retailer, so
> no watch can be polled more often than roughly the global interval whatever its override says.

**What overruled it:** collision 1's elimination argument. The loop now sleeps
`loop_tick_seconds(...) * uniform(0.85, 1.15)` — 50 s here — so it wakes six times per default
cadence.

**What survives, and it is the whole rule:** `interval_seconds` stopped being the loop's sleep and
became **the shortest standing cadence**, which is still the floor a per-retailer override must not
go under. An override below it would still publish a cadence no retailer is scheduled at — still
REQ-21's defect, still the 3.4× drift measured in the same docstring. `EQUAL IS ACCEPTED` untouched.

**Second note (collision 6's other half, which 09-02 never landed):** the tolerance paragraph's
number moved and its direction did not. `Pacer.due`'s grace is now half the TICK, so the
900-second-override retailer on a 300 s global is asked roughly every **875 s** while 900 is
published — not every 750 s. The under-report survives and **shrinks by a factor of six**.

### The validator is untouched, and that is proved by command

```
$ git diff --numstat -- boty/config.py
59	0	boty/config.py
```

**Zero deletions.** And the body statements themselves, across the whole phase:

```
recipe: ast body statements of `_retailer_intervals` minus docstring, joined by "\n", sha256
  87871b4: 4183a4e0098eeb702e6476676f50396b02784d8b44a4220c7ad8be368680daa1
  HEAD   : 4183a4e0098eeb702e6476676f50396b02784d8b44a4220c7ad8be368680daa1
  IDENTICAL: True
```

**One thing this plan could NOT reach, recorded rather than left to be found.** The same withdrawn
sentence appears a **second** time, in the `ValueError` this function raises — *"The loop sleeps
interval_seconds per cycle, so a shorter override cannot be kept"* — and that copy is **user-facing**
rather than a comment. Changing it would be a validator change, which this plan's scope and its
`git diff` proof both forbid. Handed forward: until it is fixed, an operator who trips this rule
reads a true verdict argued from a false sentence.

---

## No persisted structure was added — CONFIRMED, not predicted

Across the whole phase, `87871b4..HEAD`:

```
Pacer.save: base sha256 17444365bc3a7d06  HEAD 17444365bc3a7d06  IDENTICAL=True
Pacer.load: base sha256 3b1f7ce8cb607a4b  HEAD 3b1f7ce8cb607a4b  IDENTICAL=True
_RetailerState fields base: ['interval', 'refusals', 'due_at', 'refused_at']
_RetailerState fields HEAD: ['interval', 'refusals', 'due_at', 'refused_at']
```

**And round-tripped in both directions**, `boty/` at `87871b4` extracted to a scratch tree, documents
written to a scratch dir — the live `pacer-state.json` was neither read nor written:

```
--- PRE-phase (87871b4) writes, HEAD reads ---
  loaded OK: warned= ['amazon']  refusals(amazon)= 1  interval= 1800
--- HEAD writes, PRE-phase (87871b4) reads ---
  loaded OK: warned= ['amazon']  refusals(amazon)= 1  interval= 1800
base keys: ['retailers', 'version', 'warned']   head keys: ['retailers', 'version', 'warned']
retailer row keys base: ['refusals', 'refused_at']   head: ['refusals', 'refused_at']
version base/head: 2 2
```

So the document's shape is unchanged, a pre-phase and a post-phase document are parse-compatible both
ways, and **Phase 8's refused `STATE_VERSION` bump is not reopened.** The diff was empty, so
Phase 8's three-legged argument is inherited rather than re-run.

---

## Criterion 4, first half: per-retailer cadence and backoff still hold

### Phase 8's gates, re-measured across the whole phase rather than quoted

Each test's source segment compared at `87871b4` against HEAD by AST, not trusted from 09-02's list:

| Gate | Edited in phase 09? |
|---|---|
| cool-off literal-seconds table (`test_the_cadence_across_the_cooloff_threshold_is_the_literal_it_is`) | **UNCHANGED — byte-identical** |
| exactly-one-probe over a window | **UNCHANGED — byte-identical** |
| restart: cool-off survives into a new pacer | **UNCHANGED — byte-identical** |
| restart mid-cool-off, probe count | **UNCHANGED — byte-identical** |
| restart: the restored depth is load-bearing | **UNCHANGED — byte-identical** |
| restart: a refusal is recorded not pushed | **UNCHANGED — byte-identical** |
| staleness: discarded / restored | **UNCHANGED — byte-identical** |
| 30-day request count under the cool-off | **UNCHANGED — byte-identical** |
| recovery clears the backoff completely | ADJUSTED |
| recovery during the probe | ADJUSTED |
| the 6 h cap | ADJUSTED |
| the literal-seconds backoff table `[300.0]` / `[1800.0]` | ADJUSTED |
| cool-off cadence published (`test_cli_watch`) | ADJUSTED |
| `test_a_retailer_at_the_default_cadence_is_due_every_cycle` | ADJUSTED |
| `test_the_restored_pacer_starts_its_schedule_from_zero` | ADJUSTED |

**Seven adjusted, exactly matching 09-02's enumeration**, and **three of the four gates this plan was
told to check came through byte-identical.** 09-02's own classification, quoted rather than
re-derived:

- **Re-pointed assertions (items 1–6)** — the behaviour is unchanged and only the arithmetic's anchor
  moved, because `record` steps the grid instead of re-anchoring on the cycle clock. Quoted from
  `test_one_good_read_clears_the_backoff_completely`:
  ```
  -    assert p._for("amazon").due_at == 300
  +    previous = p._for("amazon").due_at
  +    assert p._for("amazon").due_at - previous == 300
  ```
- **Dated reversals (items 9 and 10)** — a withdrawn claim quoted in full with what overruled it.

**No repair weakens a Phase 8 claim**, confirmed by command below: the `MAX_BACKOFF_SECONDS <= 6h`
ceiling, the 259200.0 cool-off literal and the `_CADENCE_AFTER_N_REFUSALS` depth literals are all
untouched.

### The tautology, named before it was run — and answered

Most of `tests/test_pacing.py` builds a `Pacer` with **no roster and no tick**: phase 0.0 for every
retailer, tolerance off the standing default. `cli.watch_loop` **always** passes both. 09-02 measured
what that costs — its day-long simulation *"still read 6 against the landed mechanism … it went red
only once its pacer was given a roster and a tick."*

**`record`'s grid advance is UNCONDITIONAL** — not gated behind a non-empty roster — which is exactly
why the defaulted sites DID redden and why 09-02 had to repair seven of them. So those sites exercise
half the mechanism honestly. What they cannot reach is the other half, and this plan is that half:
every new assertion builds the pacer via `_shipping_pacer`, which is itself **asserted equal to what
the loop constructs** (`test_the_shipping_pacer_is_built_the_way_the_loop_builds_one`) so it cannot
drift off it, or drives `watch_loop` directly.

### Per-retailer cadence, driven through `cli.watch_loop` over a whole simulated day

Not a `Pacer` simulation — the daemon's own loop, 1728 wakes, counting what reached `status.json` as
`checked: true`:

| retailer | before (recorded at `87871b4`) | after (measured through the loop) |
|---|---|---|
| amazon | 48 | **48** |
| bestbuy | 288 | **288** |
| gamestop | 96 | **96** |
| nintendo | 288 | **288** |
| target | 288 | **288** |
| walmart | 288 | **288** |
| **total** | **1296** | **1296** |

**Every count identical.** The literals are `09-DECISIONS.md`'s recorded BEFORE-numbers, so this is a
comparison against the old schedule and not a re-derivation from the new one. 09-02 recorded that the
max-in-60s literal is **blind** to a fleet asked half as often — it still read 2 while every count
halved — so the per-retailer counts are what answers criterion 4 and the maximum is not.

### Phase 8's backoff and cool-off, under the shipping construction

`test_the_backoff_ladder_and_the_cooloff_hold_under_the_shipping_construction`: one refusal on the
300 s group → 600 s; climbing to and holding the 21600.0 s ceiling; 259200.0 s past the thirtieth
consecutive refusal; one good read → refusals 0, cadence 300.0, next attempt one standing interval on.

`test_a_cooled_off_retailer_is_probed_exactly_once_over_a_window_at_the_new_tick`: stepped at the
loop's own 50 s tick on a roster-and-tick pacer, driven to 30 refusals by asking only when the
schedule says to, then **exactly one probe** across 1.15 cool-off windows.

**Why that one is not driven through `watch_loop`, stated as the measurement it is.** Climbing to the
thirtieth refusal takes ~700 000 simulated seconds and a further window is 259 200 more — roughly
20 000 wakes, each a full check pass and a `status.json` write. Measured at 6000 wakes: **3.9 s, and
it had reached only 19 refusals**. The day-long cadence test above is the loop-driven evidence; this
is the schedule's.

### The three standing invariants, by command, raw output

```
$ grep -n "MAX_BACKOFF_SECONDS = " boty/pacing.py
156:MAX_BACKOFF_SECONDS = 6 * 60 * 60
$ grep -n "COOLOFF_SECONDS = " boty/pacing.py
224:COOLOFF_SECONDS = 3 * 24 * 60 * 60
$ grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py
2
$ grep -n "^STATE_VERSION" boty/pacing.py
321:STATE_VERSION = 2
$ grep -n "scheduled_now += " boty/cli.py
873:        scheduled_now += delay + cycle_duration
$ grep -c "INTENTIONAL GAP" scripts/mutation_check.py
8
```

### `Pacer.current_interval` — byte-unchanged, and this time WITH the recipe

```
recipe: ast body statements of Pacer.current_interval minus docstring, joined by "\n", sha256
  87871b4: bff13fdecb317b96f09ee15d027d71a984dde18f9030dc95c409842aa103e41d
  HEAD   : bff13fdecb317b96f09ee15d027d71a984dde18f9030dc95c409842aa103e41d
  IDENTICAL: True
```

**09-03 could not reproduce the digest it was handed** (`6da39ac5…449108`) with four plausible
extractions, because 09-02 recorded the digest without its recipe. Nor could this plan. The recipe is
recorded here **beside** the digest, so this one is re-checkable; the older digest remains a claim
rather than a check, and a later wave should drop it in favour of the diff rather than carry it
forward again.

---

## The tick's cost, MEASURED — and two rows of 09-03's derived table were wrong

The **before** column is not a quote and not a forced-tick approximation: `boty/` at `87871b4` was
extracted to a scratch tree and its own `watch_loop` run for a full simulated day. Same seed, same
fleet, same config, both columns.

| per day, six retailers, `interval_seconds` 300 | 09-03 derived (before) | **measured** before | 09-03 derived (after) | **measured** after |
|---|---|---|---|---|
| loop wake-ups | 288 | **288** | 1728 | **1728** |
| `served/boty/status.json` writes | 288 | **288** | 1728 | **1728** |
| `pacer-state.json` writes | 288 | **288** | 1728 | **1728** |
| retailer requests | 1296 | **1296** | 1296 | **1296** |
| retailers asked per wake, mean | 4.5 | **4.50** | 0.75 | **0.75** |
| wakes that ask NOBODY | 0 | **0** | 432 (25.0%) | **457 (26.4%)** |
| most retailers a single wake asks | 6 | **6** | **1** | **2** |

**Two corrections, recorded BESIDE 09-03's numbers and not over them.** 09-03's after-column was
derived over the **unjittered** schedule. Under the loop's real ±15% jitter a wake can drift past a
slot and the next collects two, so:

- **empty wakes are 457 (26.4%), not 432 (25.0%)** — 09-03 slightly UNDER-stated how often the
  monitor wakes and asks nobody, which is the number this plan exists to price;
- **the most retailers one wake asks is 2, not 1** — 09-03's row is the unjittered floor, not the
  bound. It does not affect criterion 3 (a 60-second window, not a wake) and it is not a regression;
  it is a derived number that a measurement corrected.

09-03's before column was exactly right, confirmed against the real old code.

### What this phase considers acceptable, and why

- **The request rate did not move.** 1296 a day, unchanged per retailer. That is the only row the
  retailers can see, and it is criterion 4's subject.
- **Six-fold more wake-ups, `status.json` writes and `pacer-state.json` writes is accepted.** 1728
  of each per day is one every 50 seconds: two small JSON writes to local disk, which is nothing
  against a process that already makes 1296 HTTPS requests a day. It is the price collision 1 proved
  unavoidable — criterion 1 is unsatisfiable while the tick equals the cadence.
- **26.4% of wakes asking nobody is accepted, and it is what T-09-04 exists for.** An idle wake is
  cheap; an idle wake that publishes a green verdict is not, and that is fixed here rather than
  tolerated.
- **A wake asking 2 retailers instead of 1 is accepted.** Two is still a sixth of six, and criterion
  1's 50 s separation is asserted on the schedule (09-03), which jitter does not move.

### The residual, stated in the terms it deserves

**These are simulated and structural numbers, not observations of the daemon.** Nothing in this phase
ran on the wire. `boty` is an editable install, so **none of this reaches the running service until a
restart, which is Dan's call and is deliberately not part of this phase** — the daemon is still on
the pre-REQ-23 schedule and still publishing a `healthy` computed the old way. A green suite here is
evidence about the tree, never about the service.

---

## The gate

`make verify-offline`, nvm sourced first. **Real exit code 0.** Verdict line, verbatim:

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

The OFFLINE pass — **not INCOMPLETE**, so no control was reported unverifiable on this host.

| Stage | Reading |
|---|---|
| identity check | PASS — **257** file(s), no host identity found |
| lint (ruff) | All checks passed! |
| tests | **946 passed**, `-rs` on, **no skip summary at all** |
| types (mypy) | Success: no issues found in 18 source files |
| fixtures | 11 fixture(s) |
| mutation | **38/38 mutations caught** |

| Measurement | Before this plan | After |
|---|---|---|
| Suite collected | 928 | **946** |
| `tests/test_status.py` | 52 | **58** |
| `tests/test_cli_watch.py` | 49 | **61** |

**M42 and M33 both now kill the two new cool-off tests.** That does not change CLAUDE.md's recorded
finding that M42's kill set is a proper subset of M33's — both grew by the same tests. **No mutation
was registered. M43 is still free** and `grep -c "INTENTIONAL GAP"` is still **8**.

---

## What this plan does NOT claim

- **Criterion 4's SECOND half is untouched, and is expected to close MET IN PART.** `boty check`'s
  2-minute budget was **not measured**, `boty check` was **not run**, and this is stated here BEFORE
  09-05 measures it rather than after — `09-DECISIONS.md` § *Collision 8*. That half is 09-05's.
- **Criterion 5 is NOT discharged.** No mutation registered, none observed CAUGHT. `make
  verify-offline` here is a regression check and is described as one.
- **Criteria 1, 2 and 3 are untouched** — 09-02's and 09-03's.
- **The cost table is simulated**, and the "after" column is one seeded jitter sequence per row, not
  a proof over all of them. The idle-rate sweep is 20 seeds; nothing else here is.
- **Nothing was read from the live `served/boty/status.json`** except one line matched incidentally
  by a recursive `grep`. The `duration_seconds: 20.43` figure is not re-read.

---

## Deviations from Plan

**1. [Finding] The plan's blast-radius count was one short**

Planning named `tests/test_status.py:217` and `:249`. There is a third reader,
`tests/test_pacing.py:1037`, plus a `status.json`-shaped fixture at `tests/test_dashboard.py:763`.
The resolution did not have to widen — documented above rather than smoothed over.

**2. [Finding, and a rewrite] The empty wake is unreachable on `fleet_cfg`, and the first correction was also wrong**

Documented in full above. Cost two rewrites of the section and produced the 20-seed idle-rate sweep.

**3. [Rule 1 — a bug in this plan's own first draft] The cool-off sweep read the constant it checked**

`REFUSALS_BEFORE_COOLOFF` 30 → 31 left **60 passed**. Rewritten with the three numbers written out
and a separate binding test. Recorded at the site.

**4. [Rule 1 — a bug in this plan's own first draft] An unreachable guard**

`max(1, ...)` beside `ceil`. Removed and measured: **56 passed**. Deleted with the measurement at the
site rather than kept as a comment that will be believed.

**5. [Rule 2 — landing a decision the assigned wave missed] `config.py`'s SECOND note**

`09-DECISIONS.md` § *Collision 6* assigned two notes to 09-02, which landed neither; the pacing-side
half of the same collision WAS landed there, so the two halves disagreed for the length of the phase.
Both landed here. This is comment-only and leaves the validator untouched — proved by 59 additions,
0 deletions and the AST body hash — so it does not breach this plan's stated scope for the file.

**6. [Scope conflict, recorded and NOT resolved by me] `09-DECISIONS.md` § Collision 5's dated note**

The plan's Task 2 says *"`09-DECISIONS.md` § *Collision 5* gets a dated note recording which was taken
and why."* **That file is not in this plan's `files_modified`**, and the executor's instructions
restate that list as a scope fence. The plan's own must-have is explicit that the reasoning belongs
*"at the constant, not in a planning document"*, and it is there in full. So the fence was honored
and the conflict is recorded rather than silently resolved either way. **Collision 5's answer is:
re-derived, with the numbers in the table above.**

**7. [Recorded, deliberately NOT fixed] The stale-`.pyc` trap still is not in `CLAUDE.md`**

Handed forward by 09-01, 09-02 and 09-03; this plan's `files_modified` excludes `CLAUDE.md` too, so
it is handed forward a **fourth** time. It was used on all sixteen perturbations here. Four waves is
enough evidence that it will keep costing time — a later wave should widen its `files_modified` by
one file rather than hand it on again.

**8. [Recorded] `boty/config.py`'s `ValueError` message still carries the withdrawn sentence**

User-facing, out of this plan's reach by its own diff proof. Documented above.

---

## Nothing live was touched

No live retailer request. **`boty check` was not run.** `make verify` — the unqualified target with
live controls — was not run. **`state.json` and `pacer-state.json` were neither read nor written**;
every simulation used `tmp_path` or a `tempfile.mkdtemp()` scratch dir. `served/boty/status.json` was
**not written**; one line of it was matched by the recursive blast-radius `grep`, which is the only
contact. No `systemctl restart boty`. `WALMART_STORE_ID` was not read, derived, inferred or printed.

## STATE.md and ROADMAP.md were NOT updated

Deliberately, per this executor's instructions: the orchestrator owns those writes. **No `gsd-tools`
state or phase WRITE subcommand was invoked at any point.**

## Commits

| Commit | What |
|---|---|
| `f4d0562` | `fix(09-04): a wake that asked nobody publishes no verdict about anybody` |
| `15dab24` | `fix(09-04): two thresholds re-derived as durations, and one dated reversal` |
| `cda5bd8` | `test(09-04): criterion 4's first half, on the construction the daemon ships` |

Git identity checked **before** committing:
`3347065+danieljamesjohnson@users.noreply.github.com`, the repo's configured no-reply identity.
**No commit used `--no-verify`**; the tracked pre-commit identity hook passed on every one.

## Self-Check: PASSED

- `boty/status.py` — FOUND; contains `all(h.ok for h in health) if health else None`
- `boty/cli.py` — FOUND; contains `failures_before`, `WARN_AFTER_SECONDS`, `GIVE_UP_AFTER_SECONDS`,
  `FAILURES_BEFORE_WARNING`, `FAILURES_BEFORE_GIVING_UP`
- `boty/config.py` — FOUND; contains `retailer_intervals`; 59 additions, **0 deletions**
- `tests/test_status.py` — FOUND; **58 passed**
- `tests/test_cli_watch.py` — FOUND; **61 passed**
- Commits `f4d0562`, `15dab24`, `cda5bd8` — all FOUND in `git log`
- `make verify-offline` — real exit code **0**, verdict line quoted above
- Scope fence: `git diff --name-only f8ebd6f..HEAD` lists exactly the five files in
  `files_modified`, by equality
</content>
</invoke>
