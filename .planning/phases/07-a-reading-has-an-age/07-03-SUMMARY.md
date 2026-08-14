---
phase: 07-a-reading-has-an-age
plan: 03
subsystem: monitor
tags: [pacing, backoff, status-json, cross-surface, mutation-testing, cadence]

# Dependency graph
requires:
  - phase: 07-a-reading-has-an-age
    plan: 02
    provides: "a stamp that survives the process, so the cadence this plan publishes has a real age to be compared against later; and M33's reservation stated in `scripts/mutation_check.py` where this plan read it"
  - phase: 05-a-reading-is-about-a-store
    provides: "`Pacer.load`/`save` and the persisted `refusals` count, which is the half of the cadence that does NOT come from config"
provides:
  - "`Pacer.current_interval(retailer) -> float` — the standing interval with whatever backoff is in force applied to it, derived and never stored"
  - "`record` as a CALLER of that accessor, so the published cadence and the fetch schedule are one expression"
  - "`cli._current_intervals(cfg, pacer)` — the single reader `watch_cycle` and `boty check` both go through"
  - "a load-only `Pacer` on the check path: never saved, never passed to `run_once`, built inside the `check` branch"
  - "`status.json`'s `current_interval_seconds`, per retailer, on both branches of the `retailers` array, `null` never `0`"
  - "M33 — the accessor ignores the backoff — registry risen 28 -> 29"
  - "three falsified comments withdrawn in place, plus a fourth found during execution"
affects: [07-04, 07-05, 07-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "the published number and the behaviour it describes are ONE expression, so a mutation on it breaks both — the join is what the gate proves"
    - "a characterisation test written in LITERALS, green before the change and required to stay green through it, as the gate on 'nothing moved'"
    - "a second construction site permitted by a stated rule (neither saves nor schedules) rather than by a blanket prohibition"

key-files:
  created: []
  modified:
    - boty/pacing.py
    - boty/cli.py
    - boty/status.py
    - scripts/mutation_check.py
    - tests/test_pacing.py
    - tests/test_status.py
    - tests/test_cli_watch.py

key-decisions:
  - "`record` computes its wait THROUGH `current_interval` rather than beside it: one expression cannot drift from itself, and M33 breaking both halves at once is that design measured rather than claimed"
  - "the zero-refusal early return is kept even though it is indistinguishable from the general form at every interval configured today — it is there so a future config edit above the cap cannot make the accessor clamp a cadence the schedule would not"
  - "the key is `current_interval_seconds`, NOT `interval_seconds`: the latter is already the operator's own standing key in config/products.yaml, and publishing a different number under the same name on a served page is the drift this phase exists to remove"
  - "no `stale` flag is computed at write time — a flag written `false` stays `false` for exactly the interval during which the row becomes stale"
  - "per retailer, not per watch: a cadence is a per-retailer fact and a copy on fourteen watch rows is thirteen more copies that can drift"
  - "the check path's pacer is load-only, and the three constraints are ASSERTED (bytes, AST, watch-row count) rather than promised"
  - "M33's anchor is the multi-line `return min(...)` form because the single-line fragment occurs twice, the first inside a comment — measured before registration, not after a misfire"

patterns-established:
  - "Pattern 1: expose a number by making the behaviour compute through it, never by copying the arithmetic next to it"
  - "Pattern 2: a cross-surface equality test must also assert the shared value is the INTERESTING one, or it passes when both surfaces are equally wrong"
  - "Pattern 3: a schedule-characterisation test states its expected values as literals, so it cannot pass by re-deriving them through the code under test"

requirements-completed: []

# Metrics
duration: 24min
completed: 2026-08-14
---

# Phase 7 Plan 03: One Cadence, Read the Same Way by Both Surfaces — Summary

**The retailer's CURRENT interval stops being a four-line expression inside `record` and becomes
`Pacer.current_interval`, which `record` then calls for its own wait; `cli._current_intervals` is
the one reader `boty check` and the daemon both answer from, off one `pacer-state.json` that the
check never writes; `status.json` publishes the number per retailer as `null`-never-`0`; and M33
was watched turning eleven tests red by hand — four of which predate REQ-21 — before being observed
CAUGHT at 29/29.**

## Performance

- **Duration:** ~24 min (12:11:01Z to 12:35:24Z), including three full `make verify-offline` runs and one by-hand red-watch
- **Tasks:** 3
- **Files modified:** 7
- **Commits:** 7 task commits + this metadata commit

## Accomplishments

- **Criterion 3's threshold exists, and there is exactly one of it.** Before today the backed-off
  figure lived for four lines inside `record` before being folded into `due_at` — a position on a
  synthetic clock that restarts at 0.0 every process and is deliberately never persisted. So the
  criterion had nothing to compare against. It has one number now, and both surfaces read it.
- **The join is structural, and the mutation proves it.** `record` does not compute the backoff
  beside the accessor; it *calls* it. M33 replaces the accessor's backed-off return with the
  standing interval and **eleven** tests fail — including four written in 2026-08-04, before this
  phase existed, that only fail because the fetch schedule collapses with the published number. A
  version of this change that published a figure next to the schedule instead of through it would
  have left those four green.
- **`boty check` reads the daemon's document and does not touch it.** Asserted three ways rather
  than promised: the file's **bytes** are compared across a check, an AST check confirms `main`
  contains no `.save()` call and hands `run_once` no pacer, and a watch-row count confirms the
  check still reads every watch.
- **The cheap version was measured and refused.** With each surface computing its own cadence,
  `boty check` would compare a reading against `cfg.interval_seconds` while the daemon compared it
  against the backed-off figure. Measured on this host: four of six retailers on a cadence
  different from their configured one, by factors of up to 72. Two surfaces publishing different
  staleness verdicts about one reading is this project's own defect one level up.
- **Nothing about when anything is fetched changed**, and that is a claim with a test behind it
  rather than an assurance (see § *The schedule evidence*).

## Task Commits

1. **Task 1: The number exists, and the schedule is computed through it**
   - `94194d6` (test) — RED at **5 failed / 68 passed**
   - `4762987` (feat) — `current_interval`, `record` as its caller, `skipped_reason` re-expressed,
     `MAX_PERSISTED_REFUSALS`' citation re-pointed
2. **Task 2: Both surfaces read it — one helper, one published key, a load-only pacer**
   - `b22fc2c` (test) — RED at **5 failed / 25 passed**, one of which is the pinned whole-dict
     retailers assertion going red on purpose
   - `63f01f8` (feat) — `status.write`'s `intervals`, the key on both branches
   - `e8ba82c` (feat) — `_current_intervals`, `watch_cycle`, the check path's load-only pacer, and
     `pacing.py`'s two comment reversals
3. **Task 3: The two surfaces pinned to each other — register M33, and watch M33 go red**
   - `4cedc90` (test) — the cross-surface section and the two docstring rewrites
   - `314e735` (chore) — M33 registered with its pre-count and its **measured** killer list

## Files Created/Modified

- `boty/pacing.py` — `current_interval` between `record` and `skipped_reason`, with the
  derive-don't-store paragraph and the zero-refusal branch's measured argument; `record`'s refusal
  branch now calls it; `skipped_reason`'s standing branch reads it; `MAX_PERSISTED_REFUSALS`'
  citation re-addressed with its overflow analysis byte-unchanged; `save`'s and the `load`/`save`
  header's withdrawn sentences quoted and re-argued.
- `boty/cli.py` — `_current_intervals` beside `_store_tag`; `watch_cycle` computes it beside
  `paced`; `main`'s `check` branch builds and `load()`s a pacer under a four-clause comment block.
- `boty/status.py` — `intervals` keyword-only after `paced`; `current_interval_seconds` appended
  last on both retailer-row dicts; the docstring paragraph.
- `scripts/mutation_check.py` — M33.
- `tests/test_pacing.py` — the `# REQ-21: the retailer's CURRENT interval` section (5 tests, 4
  parametrisations) and `_CADENCE_AFTER_N_REFUSALS`.
- `tests/test_status.py` — the `# REQ-21` cadence section (4 tests); `_payload` builds its kwargs
  by omission; the whole-dict retailers assertion **enumerated**, still `==`.
- `tests/test_cli_watch.py` — the `# REQ-21: one cadence` section (3 tests) and two docstring
  rewrites.

## Evidence

### `make verify-offline`, verbatim

```
=== verify: identity, lint, tests, types, fixtures, controls, mutation ===
identity check: PASS — 217 file(s), no host identity found
All checks passed!
835 passed in 11.29s
Success: no issues found in 18 source files
fixtures: 11 fixture(s) under /home/dan/CodeProjects/pokemongoplusplus/tests/fixtures
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 29 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (806 passed, 29 skipped in 11.47s)
  CAUGHT    M33 boty/pacing.py: 11 test(s) failed — test_both_surfaces_publish_one_cadence_from_one_document, test_a_refusal_the_backoff_is_handling_is_recorded_not_pushed_across_a_restart, test_a_refusal_pushes_the_next_attempt_out_exponentially (+8 more)
mutation check: 29/29 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
EXIT=0
```

**29 of 29 mutations caught.** The ratio is **exactly one above the 28/28 `07-02-SUMMARY.md`
recorded** — **no discrepancy**; the number was read from that summary before the run and confirmed
against it, not assumed. **Survivor list empty**: `grep -c SURVIVED` over the captured run returns
**0**. **835 passed**, above 07-02's recorded **821** by the 14 tests and parametrisations this plan
added. mypy clean over **18** source files. Controls **SKIPPED** — **no live retailer read was made
and none was planned.**

### M33 watched going red BY HAND, before the harness was ever asked

Applied to the working tree with a `trap cleanup EXIT` holding `git checkout -- boty/pacing.py`:

```
M33 APPLIED at the only occurrence
--- mutated region ---
341-            # future config edit cannot make the two answers differ.
342:            return st.interval
343:        return st.interval
=== pytest tests/test_pacing.py tests/test_cli_watch.py -q ===
FAILED tests/test_pacing.py::test_a_refusal_pushes_the_next_attempt_out_exponentially
FAILED tests/test_pacing.py::test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring
FAILED tests/test_pacing.py::test_the_current_interval_widens_with_the_backoff[300.0-expected0]
FAILED tests/test_pacing.py::test_the_current_interval_widens_with_the_backoff[1800.0-expected1]
FAILED tests/test_pacing.py::test_a_retailer_that_answers_is_back_on_its_standing_interval_at_once
FAILED tests/test_pacing.py::test_the_backoff_schedule_is_exactly_the_schedule_it_was[300.0-expected0]
FAILED tests/test_pacing.py::test_the_backoff_schedule_is_exactly_the_schedule_it_was[1800.0-expected1]
FAILED tests/test_pacing.py::test_the_restored_count_is_load_bearing_on_the_next_wait
FAILED tests/test_pacing.py::test_the_persisted_count_is_clamped - AssertionE...
FAILED tests/test_cli_watch.py::test_both_surfaces_publish_one_cadence_from_one_document
FAILED tests/test_cli_watch.py::test_a_refusal_the_backoff_is_handling_is_recorded_not_pushed_across_a_restart
11 failed, 100 passed in 0.37s
EXIT=1
```

Exit **1**, eleven killers, and the harness later reported **exactly eleven**. The by-hand list and
the sandbox's list agree, which is the only thing that makes "CAUGHT" mean anything.

**Four of the eleven predate REQ-21 entirely** — `test_a_refusal_pushes_the_next_attempt_out_
exponentially`, `test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring`,
`test_the_restored_count_is_load_bearing_on_the_next_wait` and `test_the_persisted_count_is_
clamped` are all 2026-08-04/2026-08-10 backoff tests. They fail because `record` computes its wait
through the mutated accessor. That is the plan's central design claim showing up in a measurement
rather than in a sentence.

**The revert, proved rather than assumed:**

```
$ git status --porcelain
 M scripts/mutation_check.py          (the unregistered mutation itself; boty/pacing.py absent)
$ sed -n '343,346p' boty/pacing.py
        return min(
            st.interval * BACKOFF_FACTOR ** st.refusals,
            MAX_BACKOFF_SECONDS,
        )
```

and after the final commit, `git status --porcelain` is **empty**.

### M33's anchor, BOTH counts pre-measured before registration

```
$ python -c "...src.count(the four-line `return min(...)` form)..."
multi-line anchor count: 1
$ python -c "...src.count('st.interval * BACKOFF_FACTOR ** st.refusals')..."
single-line fragment count: 2
  line 156: #: `current_interval` computes `st.interval * BACKOFF_FACTOR ** st.refusals` —
  line 344: st.interval * BACKOFF_FACTOR ** st.refusals,
$ grep -c 'st.interval \* BACKOFF_FACTOR \*\* st.refusals' boty/pacing.py
2
```

The multi-line anchor is **1**. The single-line fragment is **2**, and **the first occurrence is
`MAX_PERSISTED_REFUSALS`' comment**, which quotes the expression to argue the float-overflow cliff.
`apply_mutation` replaces the FIRST occurrence, so a single-line anchor would have mutated **prose**
— changing no behaviour, SURVIVING, and being reported as a hole in the suite with no attribution.
That is M19's recorded trap, measured before it was walked into rather than after. This is the
record that it was measured.

### The cross-surface number, quoted

One `pacer-state.json` carrying `gamestop` at **3 consecutive refusals**. The daemon publishes it on
the **paced** branch (it is not due: `0.0 + 150.0 >= 2400.0` is false, so `run_once` records nothing
for it and the depth stays at 3); `boty check` publishes it on the **checked** branch.

- Both published **`2400.0`** — 300 x 2**3 — and the test asserts equality **and** that literal
  **and** `> cfg.interval_seconds`. Without the second and third assertions the test would pass if
  both surfaces silently returned the standing 300, which is exactly what M33 makes them do.
- `cfg.pacer_state_path.read_bytes()` is **identical** before and after the check.
- The check's `watches` array still contains the gamestop row, so the pacer never reached
  `run_once`.

### The schedule evidence

**No fetch timing changed.** The three schedule-sensitive suites, run together:

```
$ .venv/bin/python -m pytest tests/test_pacing.py tests/test_cli_watch.py tests/test_monitor.py -q
160 passed in 0.30s
```

- `tests/test_pacing.py` pins the backoff arithmetic and the cap — including
  `test_the_backoff_schedule_is_exactly_the_schedule_it_was`, added by this plan, which asserts
  `due_at` for 1-8 consecutive refusals at **both** configured intervals against **literal expected
  seconds** held in `_CADENCE_AFTER_N_REFUSALS`, never through `current_interval`. It was **green
  before the accessor existed** (it passed in the Task 1 RED run) and is green after, which is what
  makes it a statement about the schedule rather than a re-derivation of it.
- `tests/test_cli_watch.py`'s REQ-16-across-a-restart section pins **measured cycle counts** (10
  cycles yields exactly 3 refusals).
- `tests/test_monitor.py` pins which retailers `run_once` skips.

`skipped_reason`'s two printed forms are byte-identical: `tests/test_pacing.py`'s
`"paced at 30 min"` assertion passes untouched, which is an identity rather than a coincidence —
that branch is only reached when `st.refusals` is falsy, and at zero refusals the accessor returns
`st.interval`.

### The AST check on the check path

```
$ .venv/bin/python -c "...ast over boty/cli.py's main()..."
check path: load-only, and run_once still skips nothing
```

`main` contains **no** `.save()` call anywhere, and `run_once` is handed **no** `pacer` keyword.

## Measurement notes, recorded rather than edited into planning documents

### "A retailer at seven refusals is on a ~97-minute cadence" is wrong arithmetic — 07-05 needs this

The sentence appears in **`07-PLAN-OUTLINE.md`** and **`07-PATTERNS.md`**. Measured:

```
$ python -c "print(300*2**7, min(300*2**7, 21600))"
38400 21600
```

300 x 2**7 = **38 400 s**, which exceeds `MAX_BACKOFF_SECONDS` (**21 600 s**), so **target and
walmart at seven refusals are on the six-hour CAP**, not on ~97 minutes. The ~97 and ~53 minute
figures in those documents and in the live `pacer-state.json` are `skipped_reason`'s *time remaining
until the next attempt*, which is a different quantity from a cadence. ROADMAP's own sentence —
*"Walmart at seven refusals is on a multi-hour interval"* — agrees with the measurement.

**07-05's staleness threshold for those two retailers is 21 600 s, not 5 820.** Recorded beside
those documents on 06-02's and 07-02's footing: a measurement is recorded beside a planning
document, never edited into it. Neither document was edited.

### Reversals argued in place — three planned, one found

None is an edit. Each quotes the withdrawn sentence, names the date and what overruled it, and keeps
the argument that survives.

1. **`boty/pacing.py`'s `save` docstring.** Withdrawn: *"This file has exactly one reader, once, at
   startup, in the same process that writes it."* `boty check` now loads it, on a surface routinely
   run while the daemon is writing. **The decision survives and is re-argued:** the write stays a
   plain `write_text` because the new reader's worst case is bounded and points the safe way — see
   T-07-03b below.
2. **`boty/pacing.py`'s `load`/`save` block header.** Withdrawn: *"A classmethod would invite a
   second construction site, which is the thing that invariant forbids."* The invariant it names is
   `cli.watch_loop`'s and is untouched — one pacer for the life of the **loop**. The blanket
   prohibition is replaced by a rule the next case can be tested against: **a second pacer is
   allowed exactly when it neither saves nor schedules.**
3. **`tests/test_cli_watch.py`'s `_check_config` docstring.** Withdrawn: *"`pacer_state_path` is
   here even though `boty check` builds no pacer and so writes no such file."* Half false as of this
   plan — it builds one and still writes none. The line survives with a stronger reason: the defence
   used to be against a code path staying absent, and is now against one that exists and must stay
   read-only.
4. **Found during execution, not in the plan:** `test_boty_check_writes_no_pacer_state_at_all`'s
   docstring — *"`check` is one pass with no schedule, so it builds no pacer to persist."* Same
   falsification, same treatment. Recorded as a deviation below.

### `MAX_PERSISTED_REFUSALS`' citation

Re-addressed from `record` to `current_interval`, with the measured CPython 3.12.3 overflow figures,
the 64-vs-crash-point argument and the `REFUSALS_BEFORE_PAGING` relationship **byte-unchanged**. The
expression's reachability is unchanged and the comment says so: `record` still evaluates it on every
refusal, one call along.

## Residuals carried forward

### T-07-03b — `pacer-state.json` now has a second reader and is still written non-atomically

`Pacer.save` uses a plain `write_text`, and this plan gives the document a second reader that can
catch it mid-write. **Accepted, with the direction stated:** a truncated read raises
`JSONDecodeError`, `load` already turns that into empty state, every retailer then reads at its
**standing** interval — a **narrower** window than the real one — so the failure **over-reports**
staleness rather than under-reporting it, which is the direction REQ-21 prefers, and it self-heals
on the next check. Promoting the write to `status.write`'s temp-and-replace was **deliberately not
done here**: that is the daemon's persistence path, this plan's rule was that pacing behaviour does
not move, and the benefit accrues only to the reader. Priced in `save`'s rewritten docstring.
**07-06 carries this**; the promotion is available if it ever bites.

### T-07-03c — `current_interval` materialises state for an unseen retailer

It calls `_for`, which creates a `_RetailerState` in memory. Not a widening: `due` and
`skipped_reason` already do it every cycle, the check path never calls `save()`, and `Pacer.save`
omits retailers at zero refusals — so no reachable path lets this accessor add an entry to the
document. Recorded because a reader will otherwise see a mutating read and try to "fix" it into a
`.get`, which would return the wrong number for an override.

### M34's disposition — reserved, not lost

`07-PLAN-OUTLINE.md` assigns **M34 to 07-04** (a remembered row published as `checked: true`, or
with its stamp dropped). This plan consumed **M33 only**. The disposition is stated in
`scripts/mutation_check.py`'s M33 comment block, **where 07-04 will read it**.
`tests/test_support_matrix.py`'s own message governs: *"Idents are reserved across concurrent plans,
not renumbered."* **M21-M24 remain the intentional gap and were not filled.**

### The registry, for 07-06's arithmetic

**28 -> 29**, one ident. 07-06 must record the phase as rising **from 26** (07-01's § *CORRECTION
1*): 26 at phase start, +1 for M31, +1 for M32, +1 for M33.

## Deviations from Plan

Two, both recorded rather than quietly absorbed. Neither changed what shipped.

**1. [Rule 2 — a second docstring falsified by the same edit, corrected in the same house style]**

- **Found during:** Task 3, writing the cross-surface section.
- **Issue:** the plan names `_check_config`'s docstring as the one sentence in
  `tests/test_cli_watch.py` this edit falsifies. It is not the only one:
  `test_boty_check_writes_no_pacer_state_at_all`'s docstring opens *"`check` is one pass with no
  schedule, so it builds no pacer to persist"*, and after Task 2 it builds one. Its **assertion** is
  still exactly right — the check writes no such file — so the premise died and the conclusion
  survived, which is the same shape as the three reversals the plan does name. Leaving a false
  sentence standing because a plan did not predict it would be shipping a known defect.
- **Fix:** rewritten in place with the original quoted, the date named and the surviving claim
  re-argued, pointing at `test_both_surfaces_publish_one_cadence_from_one_document` as the stronger
  sibling that compares the document's bytes. No assertion changed.
- **Committed in:** `4cedc90`.

**2. [Rule 3 — the plan's M33 killer list was a prediction, and the measurement was larger]**

- **Found during:** Task 3, at the by-hand red-watch, before the harness was ever run.
- **Issue:** the plan's `breaks=` guidance names the REQ-21 accessor tests, the cross-surface test
  and the REQ-16-across-a-restart section as expected killers. Applied by hand, M33 kills **eleven**
  tests, including **four 2026-08-04/2026-08-10 backoff tests the plan does not mention**:
  `test_a_refusal_pushes_the_next_attempt_out_exponentially`,
  `test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring`,
  `test_the_restored_count_is_load_bearing_on_the_next_wait` and
  `test_the_persisted_count_is_clamped`. Writing the predicted list into the comment would have
  published a smaller catch than the one that happened — the mirror of 07-02's deviation 1, where
  the prediction was too large.
- **Fix, following the tree over the plan:** the comment names the **eleven measured killers**,
  grouped by section, and states in place why the four unexpected ones are the accessor/schedule
  join showing up in the measurement rather than an over-broad anchor. A gate is named after
  watching it fail, never after expecting it to — 07-02's Pattern 3, applied again.
- **Committed in:** `314e735`.

**Also recorded, though not a deviation:** the plan requires the schedule-characterisation test's
expected values to be literals so it cannot pass by re-derivation. It was watched behaving that way
— both parametrisations of `test_the_backoff_schedule_is_exactly_the_schedule_it_was` passed in the
**Task 1 RED run**, before `current_interval` existed at all (5 failed / 68 passed, and neither of
those two among the failures), and both fail under M33. Green before, green after, red on the
mutation is the whole of what that test is for.

**Total deviations:** 2. **Impact on scope:** none. No package was installed, no dependency added,
no clock frozen, injected or monkeypatched anywhere, and no live retailer read was made.

## Scope fence, honoured

`git diff --stat` over this plan's seven task commits touches exactly seven files, all of them in
this plan's `files_modified`. **`boty/models.py`, `boty/retailers.py`, `boty/monitor.py` and
`served/boty/index.html` were NOT touched** — confirmed per file with `git diff --quiet`. Measured
over the same range: **0** added lines in `boty/` mention `read_at`, and **0** mention a `stale` key
or `_age_tag`. Nothing here compares a stamp to anything, computes a staleness flag, or renders a
tag. The missing rows are **07-04's**; the three renderings are **07-05's**.

**REQ-21 is NOT marked complete here**, on the outline's own rule and 07-01's and 07-02's precedent:
*a requirement is not marked complete by the plan that ships its code.* **07-06 closes it by
measuring what landed.** `requirements-completed` is `[]` deliberately.

## Next Phase Readiness

**07-04 can start.** What it inherits:

- A per-retailer cadence in `status.json` that both surfaces agree on, so a row that can be old
  (07-04) and a rendering that calls it stale (07-05) now have a threshold to be judged against.
- **M34 is reserved for it and says so in `scripts/mutation_check.py`.** The next registered ident
  is M34; M21-M24 stay unfilled.
- The registry is at **29**, and the consumer-side join is confirmed reachable rather than assumed:
  `served/boty/index.html` already holds `d.retailers` and already interpolates `w.retailer`, so
  07-05 joins them with a lookup and no new payload shape.
- **The 6-hour figure, not the 97-minute one**, for target and walmart. See the measurement note
  above; 07-05's threshold for those two retailers is 21 600 s.

**Standing concern, unchanged:** `walmart:Pokémon GO Plus +` is frozen and will publish an unknown
age indefinitely (`WALMART_STORE_ID` unset, `QUESTIONS.md` § 0f, open). 07-05 must render that as
UNKNOWN rather than as stale — and note that this plan gives it a *cadence* regardless, which is
correct: the retailer has a pacing whether or not that watch has an age.

## Self-Check: PASSED

Every claim above re-measured against the tree after the SUMMARY was written:

- **7 modified files** all present; this SUMMARY present.
- **7 task commits** all resolvable: `94194d6`, `4762987`, `b22fc2c`, `63f01f8`, `e8ba82c`,
  `4cedc90`, `314e735`.
- `def current_interval` present in `boty/pacing.py`; `wait = self.current_interval(retailer)`
  present in `record`; `_current_intervals` present in `boty/cli.py` with `pacer.load()` on the
  check path; `"current_interval_seconds"` present in `boty/status.py`; `ident="M33"` present in
  `scripts/mutation_check.py`.
- M33's multi-line anchor still counts **1**; the single-line fragment still counts **2**. The
  registry counts **29** idents.
- `identity_check` -> `PASS — 217 file(s), no host identity found`. **No real store number and no
  host identity was written.** The retailer names used in tests are `gamestop`, `walmart` and
  `amazon`, all already present in tracked `config/products.yaml`; `pacer-state.json` and
  `served/boty/status.json` both stay gitignored.
- `tests/test_packaging_metadata.py` -> **41 passed**, so STATE.md's `milestone:` key and its
  warning comment both survived the eleventh state-writer misfire and the hand restoration.
- `git status --porcelain` empty.

---
*Phase: 07-a-reading-has-an-age*
*Completed: 2026-08-14*
