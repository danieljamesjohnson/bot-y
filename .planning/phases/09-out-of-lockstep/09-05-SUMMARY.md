---
phase: 09-out-of-lockstep
plan: 05
subsystem: mutation-registry
tags: [mutation, M43, criterion-4, criterion-5, REQ-08, REQ-23, verdict-table, T-09-06, T-09-07]

requires:
  - phase: 09-out-of-lockstep
    plan: 02
    provides: "the mechanism M43 mutates — the birth phase and the grid advance — and criterion 3's after-number 2"
  - phase: 09-out-of-lockstep
    plan: 03
    provides: "criterion 1's 50.0 s separation and criterion 2's two directions, which are three of M43's five killers"
  - phase: 09-out-of-lockstep
    plan: 04
    provides: "criterion 4's FIRST half, the idle-wake test that is M43's fifth killer, and the pre-M43 tally of 38/38"
provides:
  - "Criterion 5: M43 registered on the de-lockstep's BIRTH PHASE, observed CAUGHT at 5 killers, 39/39 mutations caught, survivors 0"
  - "Both candidate anchors broken and both kill sets recorded — the loser as evidence about what the suite covers, not a discarded draft"
  - "M43's kill set measured against ALL 38 pre-existing idents, one sandbox each: DISJOINT. M43 buys detection, not localisation — the opposite of M42's recorded finding, and measured rather than assumed"
  - "Criterion 4's BUDGET half recorded in docs/retailer-evidence.md beside the existing REQ-08 measurements, verdict MET IN PART, stated as BOUNDED and not re-measured"
  - "CLAUDE.md's registry counts ADVANCED in the same commit that moved what they describe: M25-M43, next free M44, marker count nine"
  - "The stale-`.pyc` red-watch trap recorded in CLAUDE.md — 09-DECISIONS.md handed it to a later wave in this phase and this was the last one"
  - "The five-criterion verdict table for Phase 9, with a per-row citation and nothing rounded up"
affects: []

actuals:
  tokens: 4900
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "A mutation's kill set measured against the WHOLE registry before the ident is defended, so 'it buys detection' and 'it buys localisation' are two answers to one measured question rather than one assumption"
    - "The rejected anchor is registered as evidence in the winner's own comment block, with its kill set, because a break the suite catches and the registry does not name is a fact about the suite"
    - "A budget claim written as a BOUND, with the word bounded in the heading, when the criterion asked for a re-measurement that was not taken"

key-files:
  created:
    - .planning/phases/09-out-of-lockstep/09-05-SUMMARY.md
  modified:
    - scripts/mutation_check.py
    - docs/retailer-evidence.md
    - CLAUDE.md

key-decisions:
  - "M43 anchors on the BIRTH PHASE, not on the grid advance, and the choice was measured twice over: A's five killers are all tests about WHEN a request is made ACROSS retailers, and B does not kill criterion 3's window maximum at all"
  - "The grid advance is measured, written down and DELIBERATELY LEFT UNREGISTERED. Its break is caught by eleven assertions, six already under M33 and two now under M43, so a second ident would raise the denominator without defending anything new — this registry's own rule, applied against my own work"
  - "Criterion 4 closes MET IN PART. The verdict was committed in 09-DECISIONS.md § Collision 8 BEFORE any measurement, and it is kept there rather than promoted after the fact"
  - "`boty check` was NOT run. The budget is bounded from two instruments that already existed; a fresh timed pass costs six live retailer requests and a write to the document the daemon owns"
  - "CLAUDE.md's counts were ADVANCED, not corrected. They were right when this plan started — repaired 2026-08-31 as WR-04 — and they moved because this commit moved M43"

patterns-established:
  - "Measure the kill set against the registry BEFORE writing the paragraph that defends the ident. The same measurement returned 'proper subset, localisation only' for M42 and 'disjoint, real detection' for M43; either answer is publishable and neither is predictable from the argument"

requirements-completed: []

status: complete
---

# Phase 9 Plan 05: Out of Lockstep — The Mutation, the Bound, and the Table

**M43 is registered on the de-lockstep's birth phase, observed CAUGHT at five killers, and its
kill set is DISJOINT from the union of all 38 idents that preceded it** — so it buys detection
and not merely localisation, which is the opposite of what the same measurement said about M42
and is exactly why the measurement is taken rather than argued. **Criterion 4's budget half
closes MET IN PART**, bounded from evidence that already existed, because `boty check` was not
run and this phase made no live retailer request. `make verify-offline` exits 0 at
**39/39 mutations caught, survivors 0**. **No production code moved.**

---

## Criterion 5: M43

| | |
|---|---|
| Ident | **M43**, `boty/pacing.py` |
| Anchor | `due_at=slot_offset(retailer, self.roster, self._tolerance_interval(), standing),` → `due_at=0.0,` |
| Occurrences of the anchor in the file | **1**, pre-counted before registration |
| Overlap with the other 38 `search` strings | **0** — neither substring nor superstring of any, so unlike M42 this entry adds no drift to an existing anchor |
| Observed | **CAUGHT — 5 test(s) failed**, 912 passed, 29 skipped |
| Registry after it | **39 idents, 39/39 caught, survivors 0** |
| Anything added to `SANDBOX_CONTENTS` to reach it | **none** — `boty/pacing.py` has been in it since before this registry existed |

**What it rebuilds is the lockstep itself.** Every retailer is born at `due_at = 0.0` again
instead of at its own slot, so a fresh process has all six due at one instant — 09-01's measured
before-number, **6 of six retailers inside a single 60-second window over a simulated day**,
against the **2** that 09-02 transcribed. And it does not decay: `record`'s grid advance is left
standing and does exactly what it was written to do, **preserving the position it is handed**, so
the four retailers sharing the 300 s cadence stay together for the life of the process and are
rebuilt together at every restart, because `due_at` is deliberately never persisted.

**It is anchored on behaviour and not on prose.** The comment three lines above the call — *BORN
AT ITS OWN POSITION* — is deliberately **not** part of the anchor, so a refactor that rewrites
every word around this call and preserves the call leaves M43 still caught. No message text, no
rendered tag, no docstring fragment, no version literal.

### Both candidate anchors were broken, and both kill sets are recorded

The plan required the anchor to be chosen **by measurement**, with the loser written down as
evidence about what the suite covers rather than discarded. Each was applied in its own sandbox on
2026-09-01 and the failures read off the run.

| | **A — the birth phase** (registered as M43) | **B — the grid advance** (measured, unregistered) |
|---|---|---|
| Mutation | `due_at=slot_offset(...)` → `due_at=0.0` | `st.due_at = _next_on_the_grid(st.due_at, wait, now)` → `st.due_at = now + wait` |
| Result | **5 failed, 912 passed, 29 skipped** | **11 failed, 906 passed, 29 skipped** |
| Killers already under another ident | **0** | **6 under M33, 3 under M42** |
| Kills criterion 3's window maximum | **yes** | **NO** |

**A's five killers, in full:**

| Test | File | What it guards |
|---|---|---|
| `test_two_retailers_at_one_cadence_are_separated_by_the_stated_number_of_seconds` | `tests/test_pacing.py` | criterion 1, the 50.0 s bound |
| `test_two_retailers_at_one_cadence_are_born_apart_and_stay_apart` | `tests/test_pacing.py` | criterion 1, at birth and over a day |
| `test_the_max_retailers_in_any_sixty_seconds_over_a_day_is_a_stated_number` | `tests/test_pacing.py` | criterion 3's after-number, 2 |
| `test_the_restored_pacer_starts_its_schedule_from_zero` | `tests/test_pacing.py` | the restart lands on the phase, not on 0.0 |
| `test_the_idle_wake_is_structural_on_the_configured_fleet_and_incidental_on_a_uniform_one` | `tests/test_cli_watch.py` | the idle wake through `cli.watch_loop` |

**Why A won, on two measured grounds and not on taste.** First, **its signature is unambiguous**:
all five killers are tests about *when a request is made across retailers*, so an M43 that
survives means one thing only — the de-lockstep's evidence has stopped working. Six of B's eleven
are single-retailer cadence arithmetic already carrying two idents, so B's failure signature says
*the schedule moved* and leaves a reader to work out which schedule, which is precisely the
accessor-versus-rule confusion M42 was registered to resolve one method along. Second, and
decisively: **B does not kill criterion 3's window maximum at all.** That simulation steps a fixed
tick, so at every dispatch `now` *is* the grid point and `now + wait` lands where
`_next_on_the_grid` would have; the after-number 2 comes out of a B-mutated tree unchanged. **An
ident on B would have left this phase's headline number with no mutation under it.**

**Neither candidate is a subset of the other** (A: 5, B: 11, shared: the two criterion-1 tests),
so registering A does not cover B. That is recorded in M43's own block as a **limit** rather than
left to be inferred: the grid advance is defended by the suite — eleven tests fail when it goes —
but it carries **no ident**, and a second ident for it was **refused** on this registry's own rule,
its break being already caught by eleven assertions. **The next free ident is therefore M44**, and
B is measured, written down and unregistered on purpose.

### The kill-set comparison against the registry — and it came back the OTHER way this time

This is the measurement Phase 8 paid for. **All 38 pre-existing idents were re-run on 2026-09-01,
one sandbox each, and their kill sets read off the runs.**

```
A n=5   supersets among the registry: []
largest overlap with any existing ident: 0 tests
killers no existing ident reaches: all 5
```

**M43's five killers are disjoint from the union of all thirty-eight.** Not one of the five is
killed by any existing mutation, and no existing mutation's kill set contains M43's. **So M43 buys
DETECTION, not localisation** — and that is the opposite of what this same measurement said about
M42, whose 16 killers are a proper subset of M33's 28 and which is kept on localisation alone.

Stated plainly, because the contrast is the useful part: **before this ident the registry had no
mutation that criterion 1's separation tests, criterion 3's window maximum, the restart-phase test
or the idle-wake test could kill.** Those four things were gated by tests and ungated by the
mutation harness. That is a hole, and it is what M43 closes.

**The remedy clause is carried forward unchanged, pointed at M43 itself:** if a later reader judges
otherwise, the honest move is to **delete the ident**, not to reword the paragraph until it sounds
like coverage. The numbers above are what decide it and they are written into the block so the
question can be re-asked rather than re-argued.

### M21–M24, restated and not weakened

`apply_mutation` still cannot ADD a file, so the defect they would have covered is outside this
harness by construction. **`boty/pacing.py` was already in `SANDBOX_CONTENTS`**, checked before the
block was written — exactly as M41 and M42 checked it — so **nothing was added anywhere** to make
M43 reachable. That is the test M21–M24 failed.

```
$ grep -c "INTENTIONAL GAP" scripts/mutation_check.py
9
```

**8 → 9, by restating the rule rather than weakening it.** The plan's floor was *not below 8*; the
count rose because M43's block repeats the argument, which is the same way M42 took it from seven
to eight.

---

## Criterion 4's budget half — MET IN PART, and the verdict predates the attempt

Recorded in `docs/retailer-evidence.md` as **`#### Amended 2026-09-01 (09-05) — BOUNDED, not
re-measured`**, inserted **beside** the existing REQ-08 measurements on that file's § 6 convention.
Neither the Phase 3 figures (35–61.4 s) nor the Phase 3.1 figures (44.81 / 45.98 / 45.09 / 42.84 s)
were touched, amended or reinterpreted.

**`boty check` was NOT run.** No live retailer request was made anywhere in this plan, and
`served/boty/status.json` was neither read nor written.

**Instrument (a) — structural, already gated, and narrow.** `boty check` builds a **load-only**
`Pacer` and **is never passed to `run_once`** (`boty/cli.py`'s `check` branch, clause 3). Cited
rather than re-argued, against four named tests in `tests/test_cli_watch.py`:
`test_both_surfaces_publish_one_cadence_from_one_document` (the document is byte-unchanged **and**
no watch was dropped), `test_a_check_publishes_every_watch_and_calls_none_of_them_remembered`,
`test_boty_check_writes_no_pacer_state_at_all`, and
`test_a_check_with_no_pacer_state_publishes_the_standing_interval`. **The claim it licenses is
narrow and is written narrowly: this phase cannot have made `boty check` slower THROUGH THE
SCHEDULE, because the schedule is not on that path.** It says nothing about any other way a pass
could get slower.

**Instrument (b) — observational, quoted rather than re-read.** `duration_seconds: 20.43`, 13
watches across all six retailers, read **2026-08-31** by the phase-8 code review and cited from
`08-VERIFICATION.md`. Written down as three things it is **not**: not a distribution (the same
configuration published 42.84–45.98 s within twenty minutes and 61.4 s on a day one watch timed
out — a factor of three), not a reading of *this* tree (it predates every Phase 8 and Phase 9
commit), and not a guarantee about any future pass. Against REQ-08's 120 s budget it sits at
roughly **17 %**.

**Verdict: MET IN PART.** *The half that holds is that no path this phase touched reaches
`boty check`, gated by the four named tests; the half that is missing is a fresh timed pass on this
tree, which this phase declines to spend.* **The criterion asked for a re-measurement and a bound
is not one.** What would close it: one `boty check` after the deferred daemon restart, whose
`duration_seconds` the pass publishes itself.

**This verdict was committed before the measurement, not after one disappointed.**
`09-DECISIONS.md` § *Collision 8* wrote *"criterion 4's budget half is expected to land at MET IN
PART"* on 2026-09-01, wave 1, **stated before any measurement is attempted, so a disappointing
result cannot be mistaken for a finding that arrived late**. It is kept there.

**Both gates passed on the new prose and neither was modified:** `tests/test_evidence_check.py`
**74 passed**, `scripts/identity_check.py --all` **PASS — 258 file(s)**.

---

## The gate

`export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh; make verify-offline`. **Real exit code 0.**

**Verdict line, verbatim — and it is the OFFLINE one, which is a different outcome from `PASS`:**

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

| Stage | Result |
|---|---|
| identity check | **PASS — 258 file(s)**, no host identity found |
| lint (ruff) | `All checks passed!` |
| tests | **946 passed in 12.68s**, 0 skipped |
| types (mypy) | `Success: no issues found in 18 source files` |
| fixtures | 11 fixture(s), all `ok` |
| control check | **SKIPPED (--offline) — no live retailer request made** |
| mutation baseline | 917 passed, 29 skipped (sandbox) |
| mutation | **39/39 mutations caught**, survivors 0 |
| EXIT | **0** |

**The verdict line is read, not the exit code.** `PASS`, `PASS (OFFLINE)` and `PASS (INCOMPLETE)`
are three different outcomes and exit 0 distinguishes none of them. This run is the **middle** one:
every retailer control was skipped, so **nothing in this transcript says the retailers still work**.

**The 946/917+29 difference is not a discrepancy.** The sandbox is a partial copy of the tree, so
29 tests that read files outside `SANDBOX_CONTENTS` skip in there and run in the working tree.

---

## The five-criterion verdict table

Verbatim from `ROADMAP.md`, in its order, **no criterion reworded**.

| # | Criterion (abridged to its testable clause) | Verdict | Where it was measured |
|---|---|---|---|
| **1** | Coinciding retailers not dispatched inside the same short window; the bound is a **stated number of seconds**, asserted on the schedule, never on a wall clock | **MET AS WRITTEN** | **50.0 s**, `_MIN_SEPARATION_SECONDS` written out by hand in `tests/test_pacing.py`. `test_two_retailers_at_one_cadence_are_separated_by_the_stated_number_of_seconds` and `test_two_retailers_at_one_cadence_are_born_apart_and_stay_apart`, asserted on `p._for(r).due_at` at birth and after every wake of a simulated day, under the construction `cli.watch_loop` ships. No clock is read (09-03) |
| **2** | Each retailer's next-attempt time is **independent**, asserted **in both directions** | **MET AS WRITTEN** | Two tests, one per direction: `test_changing_one_retailers_interval_moves_that_retailers_schedule_and_no_other` and `test_driving_one_retailer_into_backoff_moves_that_retailers_schedule_and_no_other`, `tests/test_pacing.py`. Every untouched retailer compared field by field at **every one of 400 wakes** — the end-state form was measured BLIND to a fleet-wide refusal counter and rejected (09-03) |
| **3** | Max retailers requested in any 60 s window over a simulated day is a **stated number**, and **smaller than six** | **MET AS WRITTEN** | **2**, transcribed from a run against 09-01's recorded **6**, asserted `< 6` in `test_the_max_retailers_in_any_sixty_seconds_over_a_day_is_a_stated_number` (`tests/test_pacing.py`). Same simulation, same denominator, same fleet assertion, same sliding window as the before-number (09-01, 09-02). **The dispatch figure under jitter is 3, also < 6, and is recorded beside it rather than folded in** |
| **4a** | **No regression**: per-retailer cadence and backoff still hold | **MET AS WRITTEN** | `test_each_retailer_is_asked_the_same_number_of_times_a_day_as_before` and `test_the_backoff_ladder_and_the_cooloff_hold_under_the_shipping_construction`, `tests/test_cli_watch.py` — driven through `cli.watch_loop` over a whole simulated day, under the construction the daemon ships rather than a defaulted one (09-04) |
| **4b** | …and `boty check` still completes inside REQ-08's 2-minute budget, **re-measured rather than assumed** | **MET IN PART** | **The half that holds:** no path this phase touched reaches `boty check` — its pacer is load-only and never passed to `run_once`, gated by four named tests in `tests/test_cli_watch.py`. **The half that is missing:** a fresh timed pass on this tree. The bound is `duration_seconds: 20.43` **quoted from 2026-08-31**, ~17 % of the budget, one reading of a live pass on a different tree. Recorded in `docs/retailer-evidence.md` § REQ-08, amendment of 2026-09-01 |
| **5** | `make verify-offline` exits 0, with **at least one new mutation registered and observed CAUGHT** | **MET AS WRITTEN** | `VERIFY: PASS (OFFLINE — …)`, exit 0. **M43** registered in `scripts/mutation_check.py` on `boty/pacing.py`, observed **CAUGHT at 5 killers**, **39/39 caught, survivors 0** |

**Phase verdict: four MET AS WRITTEN, one MET IN PART.** Criterion 4 is one criterion with two
halves and is split above rather than averaged, because averaging is how a missing measurement
disappears. **Nothing was rounded up and no criterion was reworded to make a row read better.**

---

## What this phase does not claim

**Nothing is on the wire.** `boty` is an editable install, so this phase reaches the daemon at the
**next restart** — the maintainer's call, deferred by his decision on 2026-08-31, **neither
performed nor recommended here**. That restart now carries **Phase 8 and Phase 9 together**, and
what it will do on the day it happens is:

- **every retailer re-phased**, so each is first asked at its own slot rather than at once;
- **some first checks delayed by up to one standing interval** — at most 300 s for the default
  group and 1800 s for amazon. Nothing is re-tested *less often*; only later within the same
  interval (09-DECISIONS.md, collision 2, with the price stated);
- **the loop waking 1728 times a day where it woke 288** — six times per cadence where it woke
  once, with `status.json` and `pacer-state.json` written at each, and **26.9 % of those wakes
  asking nobody** and publishing `healthy: null` rather than a vacuous green (09-04);
- **Phase 8's cool-off arriving at the same moment**, on retailers whose refusal counts survive
  the restart.

**Every number in this phase is simulated or structural.** No retailer was asked anything, in any
plan of this phase. A schedule that spreads six retailers in a simulation is a **floor on what the
real fleet will do, not a prediction of it** — and the gate's own verdict line says the same thing
about the whole suite: *live controls were NOT run, so nothing here says the retailers still work*.

**M43 proves the suite notices, not that the daemon is spread out.** A caught mutation is evidence
about the tests, one level below the behaviour.

**The milestone's own residual is unchanged by this phase.** `REQUIREMENTS.md`: *prevention lowers
the probability and the blast radius of a lockout and **cannot reduce either to zero**, so a
residual undetected-blindness window remains open at the end of this milestone by design, not by
oversight.* An alarm for lost coverage was proposed and deliberately not scoped. **Nothing here
closes it.**

**Criterion 4's budget half is not closed and this summary does not pretend otherwise.** It is
MET IN PART, the missing half is named, and what would close it is written down for whoever takes
the restart.

---

## Standing prohibitions, verified by command

**The strongest form first: `git diff 7c758e1..HEAD --name-only` is exactly `CLAUDE.md`,
`docs/retailer-evidence.md`, `scripts/mutation_check.py`.** No file under `boty/`, `tests/`,
`config/` or `served/` was touched by this plan at all, which is why every invariant below holds
by construction rather than by care.

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
9
```

`COOLOFF_SECONDS` is `3 * 24 * 60 * 60` = **259200**, and `MAX_BACKOFF_SECONDS` is `6 * 60 * 60`
= 6 h, both as the standing prohibitions state them. `cli.watch_loop` keeps **both** clock terms.
The `INTENTIONAL GAP` count is the one figure that moved, upward, by restatement.

**`Pacer.current_interval`, byte-unchanged — reproduced on 09-04's recipe, which is the point of
recording a recipe:**

```
recipe: ast body statements of Pacer.current_interval minus docstring, joined by "\n", sha256
  09-04 HEAD : bff13fdecb317b96f09ee15d027d71a984dde18f9030dc95c409842aa103e41d
  09-05 HEAD : bff13fdecb317b96f09ee15d027d71a984dde18f9030dc95c409842aa103e41d
  IDENTICAL  : True
```

The digest the phase originally carried (`6da39ac5…449108`) was recorded **without its recipe** and
neither 09-03 nor 09-04 could reproduce it with four plausible extractions. 09-04's advice was to
drop it in favour of the diff. **This plan takes that advice and does not carry the unreproducible
digest forward as though it had been checked** — the diff above is the check.

**Also not done:** `boty check` was not run; no live retailer request was made; `state.json`,
`pacer-state.json` and `served/boty/status.json` were neither read nor written; `boty.service` was
not restarted and no restart is recommended; `WALMART_STORE_ID` was not read, derived or printed;
no `gsd-tools` state or phase WRITE subcommand was invoked; `.planning/STATE.md` and
`.planning/ROADMAP.md` were **not edited** — closing the phase is the phase-completion step's
business, not this plan's; nothing was committed with `--no-verify`.

---

## Deviations from Plan

### Auto-fixed / carried obligations

**1. [Rule 2 — missing critical guidance] The stale-`.pyc` red-watch trap recorded in `CLAUDE.md`**

- **Found during:** Task 1, while preparing the CLAUDE.md registry edit.
- **Issue:** `09-DECISIONS.md` § *A trap that bit this wave* found on 2026-09-01 that a same-length
  perturbation reverted inside one wall-clock second leaves a cached `.pyc` valid, so the
  interpreter keeps running the perturbed bytecode while `diff`, `git status` and `grep` all say
  the source is clean. It explicitly states *"This belongs in `CLAUDE.md` § Traps that have
  actually bitten"*, records that 09-01 could not put it there (its scope fence asserted its
  changed-file list by equality), and hands it to **a later wave in this phase**. No wave took it.
  **This was the last wave**, and `CLAUDE.md` is in this plan's `files_modified`.
- **Fix:** added `### A stale .pyc can keep a reverted red-watch perturbation LIVE` to
  `CLAUDE.md` § *Traps that have actually bitten*, with the mechanism, the five misleading
  symptoms, the measured 186 ms gap and the one-line cache-clearing fix.
- **Files modified:** `CLAUDE.md`
- **Commit:** `ff3f5d3`

No other deviations. Rules 1, 3 and 4 did not fire; no architectural question arose; no
authentication gate was hit.

### Deferred

**Nothing deferred to `deferred-items.md`.** The one thing this plan leaves open is criterion 4's
budget half, which is a **recorded MET IN PART with a named closing action**, not a deferral.

---

## Threat model

| Threat ID | Disposition | How it was discharged |
|---|---|---|
| **T-09-06** — a bound written as a measurement in `docs/retailer-evidence.md` | mitigate | The word **BOUNDED** is in the heading, the verdict is **MET IN PART**, the quoted figure carries its date, its source record and three explicit statements of what it is not, and the existing measurements are untouched |
| **T-09-07** — the mutation sandbox | accept | M43 reached its target with **nothing added** to `SANDBOX_CONTENTS`, confirmed before the block was written. The harness copies the tree and mutates the copy; `git status` is clean after the run |
| T-09-01 … T-09-05 | — | carried from 09-02/03/04, mitigated there. This plan adds no production surface |

**No threat flags.** This plan added no network endpoint, no auth path, no file access pattern and
no schema change; it changed three documents, one of which is a script that only ever runs against
a temp-directory copy.

---

## Self-Check: PASSED

**Files claimed, checked on disk:**

```
FOUND: scripts/mutation_check.py       (M43 present, MUTATIONS len 39)
FOUND: docs/retailer-evidence.md       (#### Amended 2026-09-01 (09-05) present)
FOUND: CLAUDE.md                       (M25–M43 / M44 / nine present)
FOUND: .planning/phases/09-out-of-lockstep/09-05-SUMMARY.md
```

**Commits claimed, checked in `git log`:**

```
FOUND: 76b1fab  docs(09-05): criterion 4's budget half, bounded and not re-measured
FOUND: ff3f5d3  test(09-05): M43 registers the lockstep coming back, and it is disjoint
```

**Claims checked by re-running the command rather than by memory:** `39/39 mutations caught`
(twice — once bare, once inside `make verify-offline`), `grep -c "INTENTIONAL GAP"` = 9,
`identity check: PASS — 258 file(s)`, `74 passed` on `tests/test_evidence_check.py`, and the
`current_interval` digest reproduced against 09-04's recorded recipe.
