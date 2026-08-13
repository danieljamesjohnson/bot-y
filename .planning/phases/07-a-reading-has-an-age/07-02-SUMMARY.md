---
phase: 07-a-reading-has-an-age
plan: 02
subsystem: monitor
tags: [read_at, persistence, migration, state-json, mutation-testing, restart]

# Dependency graph
requires:
  - phase: 07-a-reading-has-an-age
    plan: 01
    provides: "`Result.read_at: float | None` — the value this plan persists, honest at the source, and M32's reservation stated in `scripts/mutation_check.py` where this plan read it"
  - phase: 05-a-reading-is-about-a-store
    provides: "`transitioned_to_stock`'s UNKNOWN early return, inherited rather than rebuilt, and the store-gap guard that froze `walmart:Pokémon GO Plus +`"
provides:
  - "`State.read_at: dict[str, float]` — the wall clock each remembered availability was read, declared last with a default, absence meaning UNKNOWN age"
  - "a `load` that accepts BOTH shapes of `state.json` — the pre-07 bare string and the dated entry — with every stamp validated at both ends"
  - "`EARLIEST_CREDIBLE_READING` — a credibility floor, deliberately NOT `pacing.STATE_MAX_AGE_SECONDS`"
  - "a `save` that contains no clock read at all, writes `null` never `0`, and is wrapped so a failed write cannot take a cycle down before its alerts are delivered"
  - "M32 — `load` defaults a missing stamp to now — registry risen 27 -> 28"
  - "two falsified comments withdrawn in place (`pacing.STATE_VERSION`, `config.pacer_state_path`) with the originals quoted"
affects: [07-03, 07-04, 07-05, 07-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "per-entry shape tolerance instead of a version field, chosen because it round-trips BOTH directions where a version could not"
    - "validation that drops the AGE and keeps the MEMORY — the deliberate divergence from `pacing.load`, which drops a bad entry whole"
    - "a mutation's expected killers are MEASURED by applying it, never predicted — four non-killers argued in the comment so they do not read as a gap"

key-files:
  created: []
  modified:
    - boty/monitor.py
    - boty/pacing.py
    - boty/config.py
    - scripts/mutation_check.py
    - tests/test_monitor.py
    - tests/test_cli_watch.py
    - tests/test_config.py

key-decisions:
  - "no version field on `state.json`: epoch seconds have no policy constant to drift against, a version is priced in ALERTS here (13 forgotten availabilities), and it does not answer the actual hazard, which is a downgrade"
  - "`pacing.STATE_MAX_AGE_SECONDS` is NOT reused as the far bound — a refusal count expires, a reading's age never does; a 6-hour cap would delete this phase's own datum twice a day"
  - "a failed stamp check drops only the AGE; `pacing.load`'s drop-the-entry-whole would forget an availability, and a forgotten availability re-alerts"
  - "`save` reads no clock, asserted end to end by a save/load/save round trip rather than by reading the source"
  - "the stamp is written beside `self.seen[key] = …`, inheriting the UNKNOWN early return; no second guard added"
  - "M32's expected killers were measured by hand, which falsified the plan's prediction and produced one new test"

patterns-established:
  - "Pattern 1: a shape change that reaches a live file is migrated per entry, and the LIVE document is the test input"
  - "Pattern 2: a comment whose premise died is withdrawn in place with the original quoted, the date named, and the surviving conclusion re-argued — never silently retyped"
  - "Pattern 3: a mutation is named after the tests watched failing, and the tests that did NOT fail are argued in the same comment"

requirements-completed: []

# Metrics
duration: 38min
completed: 2026-08-13
---

# Phase 7 Plan 02: The Age Survives the Process — Summary

**`monitor.State` becomes a dated per-watch ledger that loads the 13-bare-string document on
Dan's disk without losing a single availability or inventing a single age; `save` contains no
clock read at all; two comments falsified by the edit are withdrawn in place; M32 registered,
watched turning seven named tests red by hand, and observed CAUGHT at 28/28.**

## Performance

- **Duration:** ~38 min, including three full `make verify-offline` runs and two by-hand red-watches
- **Tasks:** 3
- **Files modified:** 7
- **Commits:** 6 task commits + this metadata commit

## Accomplishments

- **Criterion 4 whole.** Two `watch_loop` calls sharing one `state_path` — a restart in every
  respect these criteria are about — and the age the first process wrote is the age the second
  loads, to the float. REQ-21's opening measurement was that Walmart's age could not be
  **established at all**, because a restart at 2026-08-12 16:49:57 zeroed the evidence. That is
  the thing that no longer happens.
- **The persistence half of criterion 2.** A document that never recorded a moment loads as
  UNKNOWN — never `0.0`, never `now`. Absence is the representation, so there is no `None` in the
  map to accidentally do arithmetic against.
- **The migration was measured, not approximated.** The real 13-entry document on this host is
  reproduced entry-for-entry in `tests/test_monitor.py` and asserted for **alert behaviour**, not
  merely for "no exception": a remembered `out_of_stock` still transitions on a new IN_STOCK
  reading, and a remembered `in_stock` still does not.
- **The fossil was not papered over.** `walmart:Pokémon GO Plus +` writes `"read_at": null` on
  every cycle and a test asserts it after two saves, which is the only honest output while the
  store pin is unset.
- **The trap was refused in both directions.** `save` reads no clock (measured: 0 occurrences of
  `time.` inside the method) and `load`'s fall-through returns `None` rather than `now` — the two
  ways this phase's own defect could have been rebuilt inside its fix, and M32 pins the second.

## Task Commits

1. **Task 1: The ledger, the migration, and a stamp validated at both ends**
   - `239c789` (test) — RED at **14 failed / 29 passed**
   - `efc354c` (feat) — `State.read_at`, `EARLIEST_CREDIBLE_READING`, the two helpers, `load`, `save`
2. **Task 2: Only a reading is stamped — and two comments this edit falsifies**
   - `685b617` (test) — RED at **2 failed / 45 passed**
   - `70535b4` (feat) — the stamp beside `self.seen[key]`, plus both comment reversals
3. **Task 3: Across a real restart — register M32, and watch M32 go red**
   - `46c7f64` (test) — the restart tests, the real pre-07 document, the save/load/save round trip
   - `6eae30f` (test) — the restart-side test added when M32's killers were **measured**
   - `881e85f` (chore) — M32 registered with its pre-count and its measured killer list

## Files Created/Modified

- `boty/monitor.py` — `import time`, `field`, `datetime/timezone`;
  `EARLIEST_CREDIBLE_READING` with its four-part argument; `_remembered_availability` and
  `_remembered_stamp`; `State.read_at` declared last with a default; `load` tolerant per entry;
  `save` built FROM `seen`, wrapped, clock-free; the stamp write in `transitioned_to_stock`.
- `boty/pacing.py` — the `STATE_VERSION` comment's withdrawn claim quoted and re-argued.
  `BACKOFF_FACTOR`'s argument and the 2026-08-10 bump record are byte-unchanged.
- `boty/config.py` — `pacer_state_path`'s first objection recorded as half-spent, the second
  named as decisive on its own. The decision is unchanged.
- `tests/test_monitor.py` — the `# REQ-21` section (11 tests + 9 parametrisations).
- `tests/test_cli_watch.py` — the `# REQ-21 across a RESTART` section (3 tests), `_stamped`, and
  one assertion added inside the existing rollback test.
- `tests/test_config.py` — docstring corrected; **the assertion is byte-unchanged**
  (`git diff | grep -E "^[-+]\s+assert "` returns nothing).
- `scripts/mutation_check.py` — M32.

## Evidence

### `make verify-offline`, verbatim

```
=== verify: identity, lint, tests, types, fixtures, controls, mutation ===
identity check: PASS — 216 file(s), no host identity found
All checks passed!
821 passed in 10.78s
Success: no issues found in 18 source files
fixtures: 11 fixture(s) under /home/dan/CodeProjects/pokemongoplusplus/tests/fixtures
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 28 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (792 passed, 29 skipped in 13.63s)
  CAUGHT    M32 boty/monitor.py: 7 test(s) failed — test_a_reading_the_first_process_could_not_date_comes_back_undated, test_a_pre_07_document_loads_as_availability_with_an_unknown_age, test_a_stamp_that_cannot_be_believed_loses_the_age_and_keeps_the_memory[null-this-program-wrote-itself] (+4 more)
mutation check: 28/28 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
EXIT=0
```

**28 of 28 mutations caught.** The ratio is **exactly one above the 27/27 `07-01-SUMMARY.md`
recorded** — no discrepancy; the number was read from that summary and confirmed against the run,
not assumed. **Survivor list empty**: `grep -n "SURVIVED"` over the captured run returns nothing.
**821 passed**, above 07-01's recorded **798** by the 23 tests and parametrisations this plan
added. mypy clean over **18** source files. Controls **SKIPPED** — **no live retailer read was
made and none was planned.**

### M32 watched going red BY HAND, before the harness was ever asked

Applied to the working tree with a `trap cleanup EXIT` holding `git checkout -- boty/monitor.py`:

```
M32 APPLIED at first occurrence
--- mutated lines ---
179:    if not isinstance(stamp, (int, float)) or isinstance(stamp, bool):
180-        return now
=== pytest tests/test_monitor.py tests/test_cli_watch.py -q ===
E       AssertionError: the restart dated a reading nobody stamped, so a frozen row comes back looking as though it had just been taken
E       assert {'gamestop:go...36241.8050463} == {}
=========================== short test summary info ============================
FAILED tests/test_monitor.py::test_a_pre_07_document_loads_as_availability_with_an_unknown_age
FAILED tests/test_monitor.py::test_a_stamp_that_cannot_be_believed_loses_the_age_and_keeps_the_memory[null-this-program-wrote-itself]
FAILED tests/test_monitor.py::test_a_stamp_that_cannot_be_believed_loses_the_age_and_keeps_the_memory[a-string]
FAILED tests/test_monitor.py::test_a_stamp_that_cannot_be_believed_loses_the_age_and_keeps_the_memory[a-bool-which-is-an-int-subclass]
FAILED tests/test_monitor.py::test_the_real_pre_07_document_loads_with_its_alert_behaviour_unchanged
FAILED tests/test_monitor.py::test_saving_the_migrated_document_twice_never_invents_an_age
FAILED tests/test_cli_watch.py::test_a_reading_the_first_process_could_not_date_comes_back_undated
7 failed, 77 passed in 0.26s
```

Exit **1**, seven killers, and the harness later reported **exactly those seven**. The by-hand
list and the sandbox's list agree, which is the only thing that makes "CAUGHT" mean anything.

**The revert, proved rather than assumed:**

```
$ git status --porcelain
 M scripts/mutation_check.py          (the unregistered mutation itself; boty/monitor.py absent)
$ grep -n -A1 'if not isinstance(stamp, (int, float)) or isinstance(stamp, bool):' boty/monitor.py
179:    if not isinstance(stamp, (int, float)) or isinstance(stamp, bool):
180-        return None
```

and after the final commit, `git status --porcelain` is **empty**.

### M32's anchor, pre-counted before registration

```
$ grep -c 'if not isinstance(stamp, (int, float)) or isinstance(stamp, bool):' boty/monitor.py
1
$ python -c "...src.count(two_line_anchor)..."
two-line anchor count: 1
bare "return None" count: 3
```

Exactly **1**, per M19's recorded trap. The bare `return None` occurs **3** times in that file,
which is why the guard is carried into the anchor rather than the fall-through alone.

### `time.time()` in `boty/monitor.py`, every occurrence accounted for

```
$ grep -c 'time.time()' boty/monitor.py
3
211:    #: WALL clock (`time.time()`), never `time.monotonic()`, citing the      <- COMMENT
249:        `time.time()` is read here and that is not a staleness comparison    <- DOCSTRING
261:        now = time.time()                                                    <- the only READ
```

**One actual clock read, in `load`**, which is a VALIDATION bound exactly as `pacing.load:323`'s
is, and not a staleness comparison. Measured over the `save` method's own text:

```
time.time() inside save(): 0
time. inside save(): 0
```

### Stray-token scan

`grep -rn 'antml:|</invoke>|</content>'` over `boty/`, `tests/` and `scripts/` returns hits only
inside `tests/test_changelog.py`, which is the pre-existing gate that detects that leak class.
No new occurrence.

## The migration, as a user-visible consequence — 07-06 carries this to Dan

**`state.json` on Dan's box changes shape at the next restart.** The daemon runs this tree through
an editable install, so there is no staging environment between this commit and his disk.

1. **The 13 entries come back undated, and honestly so.** Every availability is preserved — the
   alert history is intact, and nothing re-alerts on the migration itself. Every `read_at` is
   `null`, because those readings were taken before a reading had a moment. The first cycle after
   the restart dates each watch as it is re-read.
2. **`walmart:Pokémon GO Plus +` will publish `"read_at": null` indefinitely.** That row has been
   frozen since 2026-08-12: `WALMART_STORE_ID` is unset (`QUESTIONS.md` § 0f, open), so every
   Walmart reading is `Availability.UNKNOWN`, and `transitioned_to_stock` returns on UNKNOWN
   *before* it writes. The value cannot be updated by anything until a store is pinned. It will
   keep saying `out_of_stock` with an **unknown age**, forever, and that is the correct output —
   inventing an age for it would be the defect, and a `save` that read the clock would have dated
   it at the instant of every write.
3. **The downgrade cost, priced rather than described.** If an older binary ever reads the new
   document it compares a mapping against `"in_stock"`, finds them unequal, and re-alerts. Measured
   against today's document: 8 of 13 entries are `in_stock`, 6 of those are controls, and controls
   never alert — so the whole cost is **at most two duplicate restock pushes** (the two GameStop
   `TRANSITION —` watches, which `config/products.yaml:330` records as deliberately not controls).
   It is also not one-way: an old binary rewrites the file mixed, and per-entry tolerance reads a
   mixed document without loss in **either** direction, which a version field could not do. That
   pricing lives in `monitor.State.load`'s docstring, not only here.

## Two reversals, argued in place

Neither is an edit. Both quote the withdrawn sentence, name the date and what overruled it, and
keep the argument that survives.

1. **`boty/pacing.py`'s `STATE_VERSION` comment.** Withdrawn: *"`monitor.State` has no version and
   needs none: its document is a flat map of strings whose meaning cannot drift."* REQ-21 falsified
   the premise on 2026-08-13, not the conclusion — `monitor.State` still has no version, now on
   three measured grounds (units that cannot drift, a bump priced in **alerts** rather than in one
   repeated notification, and a version field that does not answer the downgrade). The
   `BACKOFF_FACTOR` argument and the 2026-08-10 bump record are byte-unchanged.
2. **`boty/config.py`'s `pacer_state_path` comment.** Withdrawn: *"That file's document is
   `State.seen` in its entirety — `monitor.State.load` parses the whole thing as the map."* The
   decision does not change; that objection is now **half-spent**, because the migration it warned
   about has since been done per entry. The second objection — *`run_once` saves it BEFORE delivery
   is attempted* — is untouched and decisive on its own. `tests/test_config.py:275-286`'s docstring
   repeats the same falsified sentence and is corrected the same way, **with the assertion
   byte-unchanged**.

## Measurement notes carried forward

### The file-table addition is a correction to `07-PLAN-OUTLINE.md`, NOT an edit to it

`boty/config.py` and `tests/test_config.py` appear in no other plan's row of the outline's file
table, and this plan added them to `files_modified` for **comment and docstring only**. Recorded on
06-02's `_flattened_exit_codes` footing: a measurement is recorded beside a planning document,
never edited into it. Leaving a false sentence standing because a table did not predict it would be
shipping a known defect. No ownership conflict — every wave in this phase is serial regardless.

### M33's disposition — reserved, not lost

`07-PLAN-OUTLINE.md` assigns **M33 to 07-03** (`current_interval` ignoring the backoff). This plan
consumed **M32 only**, which 07-01 reserved for it. The disposition is stated in
`scripts/mutation_check.py`'s M32 comment block, **where 07-03 will read it**.
`tests/test_support_matrix.py`'s own message governs: *"Idents are reserved across concurrent
plans, not renumbered."* **M21-M24 remain the intentional gap and were not filled.**

### The registry, for 07-06's arithmetic

**27 -> 28**, one ident, and 07-06 must record the phase as rising **from 26** (07-01's
§ *CORRECTION 1*): 26 at phase start, +1 for M31, +1 for M32.

## Deviations from Plan

Three, all recorded rather than quietly absorbed, and **the first one changed the code**.

**1. [Rule 1 — the plan's predicted killer does not bind, so a test was added]**

- **Found during:** Task 3, at the by-hand red-watch, before the harness was ever run.
- **Issue:** the plan requires M32's comment block to name *"the restart test in
  `tests/test_cli_watch.py`"* as an expected killer. Applied by hand, M32 did **not** turn
  `test_the_age_of_a_reading_survives_the_restart` red, and the reason is structural rather than
  incidental: that test's stamp is a real two-day-old float, so `_remembered_stamp` returns at the
  bounds check and never reaches the fall-through M32 mutates. Writing the plan's predicted list
  into the comment would have published a catch that did not happen — the same defect as a
  `breaks=` sentence describing the wrong line, and precisely the class of unmeasured claim this
  phase exists to remove.
- **Fix, following the tree over the plan:** (a) the comment names the **seven killers measured by
  applying it**, and argues the four non-killers in place — the `in-the-future`, `zero` and
  `lost-a-thousand` parametrisations pass the type guard and are rejected by the bound one line
  below, which M32 does not touch; (b) a restart-side test that **does** bind was added —
  `test_a_reading_the_first_process_could_not_date_comes_back_undated`, which is the claim the plan
  wanted `tests/test_cli_watch.py` to carry: a restart must not INVENT an age either. That is
  `walmart:Pokémon GO Plus +` on this host in miniature, and it is criterion 4's other half.
- **Committed in:** `6eae30f` (the test) and `881e85f` (the corrected comment).

**2. [Rule 3 — an assertion the plan specifies would have been vacuous as written]**

- **Found during:** Task 3, extending `test_a_failed_restock_notification_rolls_the_memory_back`.
- **Issue:** the plan adds one assertion to that test — that the persisted document carries no
  stamp for the rolled-back key. As written the test drives `_checker`, which builds **unstamped**
  results, so nothing would ever have written an age and the new assertion would have been green
  about a field the test never exercised.
- **Fix:** that one test now drives `_stamped(time.time() - _TWO_DAYS)` instead, with the reason in
  its docstring. **`_checker` itself is untouched**, exactly as the plan requires — every other test
  in the file still exercises the no-stamp path, which is the path
  `transitioned_to_stock` has to CLEAR a stale stamp on.
- **Committed in:** `46c7f64`.

**3. [Rule 3 — `gsd-tools state advance-plan` was not run at all]**

- **Found during:** close.
- **Issue:** the plan says to *expect* the misfire and correct `status`, `stopped_at` and `percent`
  by hand afterwards. Measured against STATE.md's own record, that command has now misfired **nine
  times** for a cause that cannot be fixed — it reads `Plan: 6 of 6 complete` out of an archived
  v1.0.0 block that is deliberately kept verbatim — and on its ninth run it additionally **deleted
  the `milestone:` key's warning comment**, which is the comment that stops a
  machine-read-by-`tests/test_packaging_metadata.py` key being edited casually, plus inserted a
  stray blank line into the v0.2 archive and wrote today's date into the verbatim block.
- **Fix:** the frontmatter and the session block were written by hand directly, which is what the
  previous nine runs ended up doing anyway — after paying for the damage first. Running a command
  whose only measured effect on this repo is damage that must then be repaired is not a step, it is
  a cost. `gsd-tools roadmap update-plan-progress 07` **was** run and worked correctly (07-02
  checked off); it is the one verb here with a clean record.
- **Verification:** `tests/test_packaging_metadata.py` → **41 passed**, so the `milestone:` key and
  its warning comment both survived; `percent: 0` still carries its phase-based convention comment.

**Also recorded, though not a deviation:** the plan's Task 2 warned that the "clears the stamp"
test could pass vacuously against an implementation that writes stamps but never removes them. It
was watched binding: the naive half (`if result.read_at is not None: self.read_at[key] = ...`) was
committed to the working tree first and produced **1 failed / 46 passed**, naming
`test_a_resolved_reading_with_no_moment_clears_the_stamp_the_key_was_holding`, before the `pop`
branch was added.

**Total deviations:** 3 (2 in the code, 1 in the close procedure). **Impact on scope:** none. No package was installed, no dependency added,
no clock frozen, injected or monkeypatched anywhere, and no live retailer read was made.

## Scope fence, honoured

Nothing in this plan compares a stamp to anything, computes a `stale` flag, or publishes a key.
`boty/status.py`, `boty/cli.py`, `boty/models.py`, `boty/retailers.py` and `served/boty/index.html`
were **not touched** — confirmed by `git diff --stat` over the six task commits. The retailer's
current interval is **07-03's**; the missing-row problem is **07-04's**; rendering is **07-05's**.

**REQ-21 is NOT marked complete here**, on the outline's own rule and 07-01's precedent: *a
requirement is not marked complete by the plan that ships its code.* **07-06 closes it by measuring
what landed.** `requirements-completed` is `[]` deliberately.

## Next Phase Readiness

**07-03 can start.** What it inherits:

- A stamp that survives the process, so `current_interval` has a real age to compare against.
- **M33 is reserved for it and says so in `scripts/mutation_check.py`.** The next registered ident
  is M33; M21-M24 stay unfilled.
- The registry is at **28**, and the rule that a staleness comparison takes `now` as a **parameter**
  is now unbroken: the single clock read this plan added is a validation bound in `load`, argued as
  such in the docstring, and `07-PLAN-OUTLINE.md` § *Finding 6* already settled that `load` does not
  grow a parameter.

**Standing concern, unchanged and sharpened:** `walmart:Pokémon GO Plus +` is frozen and will
publish an unknown age indefinitely. 07-05 must render that as UNKNOWN rather than as stale, and
07-06 must put it in front of Dan as the checkpoint it is — the answer is *"we cannot establish
when this was read, and we cannot until a store is pinned"*, which is a true sentence and an
actionable one.

## Self-Check: PASSED

Every claim above re-measured against the tree after the SUMMARY was written:

- **7 modified files** all present; this SUMMARY present.
- **6 task commits** all resolvable: `239c789`, `efc354c`, `685b617`, `70535b4`, `46c7f64`,
  `6eae30f`, `881e85f` (7 including the second Task 3 test commit).
- `read_at: dict[str, float] = field(default_factory=dict)` present in `boty/monitor.py`;
  `EARLIEST_CREDIBLE_READING` present; `_remembered_stamp(entry, now)` present;
  `ident="M32"` present in `scripts/mutation_check.py`.
- M32's anchor still counts **1**. The registry counts **28** idents.
- `identity_check` -> `PASS — 216 file(s), no host identity found`. **No real store number and no
  host identity was written.** The 13 reproduced keys are watch names already present in tracked
  `config/products.yaml`; `state.json` itself stays gitignored (`.gitignore:21`).
- `git status --porcelain` empty.

---
*Phase: 07-a-reading-has-an-age*
*Completed: 2026-08-13*
