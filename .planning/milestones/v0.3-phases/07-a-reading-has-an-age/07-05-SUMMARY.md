---
phase: 07-a-reading-has-an-age
plan: 05
subsystem: monitor
tags: [rendering, cli, dashboard, staleness, mutation-testing, req-21, cross-surface]

# Dependency graph
requires:
  - phase: 07-a-reading-has-an-age
    plan: 01
    provides: "`Result.read_at` — the attribute `_age_tag` subtracts from, and the `null`-never-`0` rule its absent form renders"
  - phase: 07-a-reading-has-an-age
    plan: 02
    provides: "the ledger stamp that survives a restart, which is what makes an age worth rendering at all"
  - phase: 07-a-reading-has-an-age
    plan: 03
    provides: "`cli._current_intervals` and `status.json`'s `current_interval_seconds` — the threshold BOTH consumers judge against, read and never re-derived"
  - phase: 07-a-reading-has-an-age
    plan: 04
    provides: "`checked` on every row, and the `storeTag` register defect measured and handed here"
provides:
  - "`cli._age(seconds)` — the CLI's duration formatter, deliberately the dashboard's three bands, without `' ago'`"
  - "`cli._age_tag(r, *, now, interval) -> str` — four forms, module-level, pure, never returns `None`"
  - "`cli._report(results, health, *, intervals)` — `intervals` REQUIRED, one wall-clock read per report"
  - "`served/boty/index.html`: `fmtDur` holding the bands, `fmtAge` defined through it, `.tag.age` / `.tag.age.warn`, and `ageTag` rendering the CLI's same four forms"
  - "`storeTag`'s early return on `w.checked === false` — 07-04's carried-forward register defect, closed"
  - "a `not checked` label at the plain `.tag` weight, argued rather than defaulted"
  - "M36 (an undated reading rendered as current) and M37 (a recorded age judged against a fixed clock) — registry risen 31 -> 33"
  - "the proof that `status.json` needs no staleness key: a join test deriving a verdict from three published facts and nothing else"
affects: [07-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "a required keyword whose gate is mypy for the DROPPED case and an AST test for the NULLED case — two different failure directions, two different instruments"
    - "a formatter extracted rather than copied, with byte-identical output over the old one asserted in a real runtime before the extraction is believed"
    - "a mutation pair spanning two FILES because the criterion names three surfaces — a gate on one surface is not a gate on the criterion"
    - "a killer test that asserts a COUNT rather than an absence, because the legitimate occurrence must stay on the page"

key-files:
  created: []
  modified:
    - boty/cli.py
    - served/boty/index.html
    - scripts/mutation_check.py
    - tests/test_status.py
    - tests/test_dashboard.py

key-decisions:
  - "the stale form prints BOTH numbers (`[age 7h > 6h]`), because a bare word `stale` cannot say which threshold produced the verdict and criterion 3's entire content is WHICH threshold was used"
  - "`>` and not `>=`: a reading exactly one cadence old is due to be replaced this instant, not overdue — asserted to the float on both sides"
  - "`_age_tag` never returns `None` where `_store_tag` does: five of six retailers can never produce a store, but every reading has an age or a stated absence of one, so an absent tag would MEAN fresh"
  - "`intervals` is REQUIRED on `_report` rather than defaulted — one production call site means mypy can be the gate for a dropped keyword, and the AST test closes the `intervals=None` direction mypy cannot see"
  - "`fmtAge` is defined through `fmtDur` rather than copied, and the equivalence was EXECUTED in node over 16 inputs rather than asserted by inspection"
  - "`storeTag` returns early on `w.checked === false` and not `!w.checked`, so a pre-07-04 `status.json` on disk during a deploy keeps its store tags"
  - "the `not checked` label uses the plain `.tag` weight: a paced-out retailer is an ordinary, expected and CORRECT state, and the warning — if any — is the age beside it"
  - "the CSS comment writes the banner constant with a space (`1 800`) because its own killer test counts digits over the whole file and cannot tell prose from code"

patterns-established:
  - "Pattern 1: when a plan's own comment must quote a forbidden code shape, DESCRIBE the shape instead — a source-scanning test reads comments too, and going red on an explanation is the check being coarse in the safe direction"
  - "Pattern 2: a red-watch that kills ONE test is not thin if the comment names why the others cannot fire; the alternative — writing the predicted list — publishes a larger catch than the one that happened"
  - "Pattern 3: render the real payload AND a clearly-labelled synthetic one; the real page proves shape-tolerance, the synthetic one proves the branches nobody's data can reach today"

requirements-completed: []

# Metrics
duration: 34min
completed: 2026-08-14
---

# Phase 7 Plan 05: Say the Age Out Loud — Summary

**Both consumers now print how old every reading is, in the same four forms, judged against the
retailer's own current cadence and never against the page's 30-minute banner constant — and on this
host today all thirteen rows render `age ?` as a warning, because `state.json` holds thirteen
availabilities and zero stamps. M36 and M37 were each applied by hand ALONE, watched turning their
named killer red, reverted to an empty porcelain, and then observed CAUGHT at 33/33.**

## Performance

- **Duration:** ~34 min (13:06Z to 13:40Z), including three full `make verify-offline` runs, two
  by-hand red-watches, and two headless renders
- **Tasks:** 3
- **Files modified:** 5
- **Commits:** 5 task commits + this metadata commit

## Accomplishments

- **A row can no longer imply freshness by staying quiet.** The age tag is appended
  **unconditionally** on both surfaces. That is the whole plan in one design decision: if fresh rows
  carried no tag, an absent tag would *mean* fresh, and an implicit claim is exactly what this
  milestone removes.
- **The stale form shows its work.** `[age 7h > 6h]` on the CLI, `7h ago > 6h` on the page. A bare
  word `stale` cannot say which threshold produced the verdict, and criterion 3's entire content is
  that the threshold is the retailer's own current cadence.
- **One formatter, not two, and the equivalence was executed rather than asserted.** `fmtDur` holds
  the three bands and `fmtAge` is `fmtDur(s) + ' ago'`. Run in node against the pre-07-05 formatter
  over 16 inputs including `0`, both band boundaries, a negative and `NaN`: **zero differ**.
- **07-04's carried-forward register defect is closed.** `storeTag` returns early on
  `w.checked === false`, so a row nobody read stops carrying a warn tag whose sentence is about a
  page that was never fetched.
- **`status.json` got no key, and that is a result rather than an omission** — see § *What criterion
  3's `status.json` third actually got*.
- **The page was LOOKED AT, twice, not inferred from source.** Both renders are below.

## Task Commits

1. **Task 1: `boty check` says how old each reading is, in four forms**
   - `dfbcf7b` (test) — RED at **20 failed / 30 passed**
   - `c5bdc95` (feat) — `_age`, `_age_tag`, `_report`'s required `intervals`, the check path
2. **Task 2: The dashboard renders the age at two weights**
   - `09d3e14` (test) — RED at **6 failed / 9 passed**
   - `4d91d26` (feat) — `fmtDur`/`fmtAge`, the two CSS weights, `ageTag`, `storeTag`'s early return
3. **Task 3: Register M36 and M37, on two different surfaces**
   - `9f7232f` (chore) — both registered with pre-counts and **measured** killer lists

## Files Created/Modified

- `boty/cli.py` — `_age` and `_age_tag` between `_store_tag` and `_current_intervals`; `_report`
  gains a docstring, a required `intervals` keyword, one `time.time()` read and the unconditional
  tag append; `main`'s check path passes 07-03's local.
- `served/boty/index.html` — `fmtDur` + `fmtAge`; `.tag.age` / `.tag.age.warn` under a comment
  carrying § *Finding 9*'s arithmetic; `ageTag` after `storeTag`; `storeTag`'s early return with its
  argument hoisted into the existing comment block above the function; `tick()`'s hoisted `nowS`,
  its one-per-tick cadence Map, and the two new row tags.
- `scripts/mutation_check.py` — M36 and M37 under one pair comment block.
- `tests/test_status.py` — the `# REQ-21: boty check says how old each reading is` section (11
  tests); `_tags` gains `intervals`; `_payload` gains `paced` on the `_OMITTED` sentinel.
- `tests/test_dashboard.py` — the `# REQ-21: the row has to say how old the reading is` section (6
  tests); `w.read_at` added to `UNTRUSTED` with its reason; `w.checked` deliberately not.

## Evidence

### `make verify-offline`, verbatim

```
=== verify: identity, lint, tests, types, fixtures, controls, mutation ===
identity check: PASS — 219 file(s), no host identity found
All checks passed!
865 passed in 11.00s
Success: no issues found in 18 source files
fixtures: 11 fixture(s) under /home/dan/CodeProjects/pokemongoplusplus/tests/fixtures
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 33 mutation(s), sandboxed (the working tree is never touched)
  ...
  CAUGHT    M34 boty/status.py: 4 test(s) failed — test_every_configured_watch_has_a_row_while_only_the_due_ones_are_fetched, test_every_configured_watch_has_a_row_whether_or_not_it_was_read, test_remembered_rows_come_after_every_fresh_row_and_are_ordered_by_key (+1 more)
  CAUGHT    M35 boty/status.py: 2 test(s) failed — test_every_configured_watch_has_a_row_while_only_the_due_ones_are_fetched, test_a_remembered_row_refuses_the_authority_a_derived_value_would_grant
  CAUGHT    M36 boty/cli.py: 1 test(s) failed — test_report_says_unknown_for_a_reading_nobody_dated
  CAUGHT    M37 served/boty/index.html: 1 test(s) failed — test_the_row_threshold_is_the_retailers_own_cadence_and_not_a_fixed_clock
mutation check: 33/33 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
EXIT=0
```

**33 of 33 mutations caught.** The ratio is **exactly two above the 31/31 `07-04-SUMMARY.md`
recorded** — **no discrepancy**; `grep -c 'ident="M' scripts/mutation_check.py` read **31** before
either ident was registered and reads **33** after. **Survivor list empty**: `grep -c SURVIVED` over
the captured run returns **0**. **865 passed**, above 07-04's recorded **848** by exactly the 17
tests this plan added (11 in `tests/test_status.py`, 6 in `tests/test_dashboard.py`). mypy clean over
**18** source files. Controls **SKIPPED** — **no live retailer read was made and none was planned.**

### M36 watched going red BY HAND, alone, before the harness was ever asked

```
M36 APPLIED at the only occurrence
201:    age = 0.0 if r.read_at is None else now - r.read_at
=== pytest tests/ -q ===
E   AssertionError: assert '[age ?]' in '  ● bestbuy   goplusplus   $   54.99  synthetic [age 0s]\n'
FAILED tests/test_status.py::test_report_says_unknown_for_a_reading_nobody_dated
1 failed, 864 passed in 11.56s
EXIT=1
```

**The revert, proved rather than assumed:** `git status --porcelain` printed nothing before M37 was
applied.

### M37 watched going red BY HAND, alone — the first mutation in this registry under `served/`

```
M37 APPLIED at the only occurrence
218:  const interval = 1800;
=== pytest tests/ -q ===
FAILED tests/test_dashboard.py::test_the_row_threshold_is_the_retailers_own_cadence_and_not_a_fixed_clock
1 failed, 864 passed in 11.84s
EXIT=1
```

**The revert, proved:** `git status --porcelain` printed nothing after it. The two mutations were
never applied at the same time. **M37 is the first mutation in this registry targeting a file under
`served/`**, and the third outside `boty/` after M25 and M26; `served` has been in
`SANDBOX_CONTENTS` since before this phase, so nothing was added there.

**The by-hand lists and the harness's lists agree exactly** — one test each, by name. That agreement
is the only thing that makes "CAUGHT" mean anything.

### Every measured anchor count, taken BEFORE registration

```
$ python -c "src.count('    age = None if r.read_at is None else now - r.read_at')"
M36 anchor count: 1
$ grep -o 'read_at' boty/cli.py | wc -l
3
$ python -c "src.count('  const interval = intervals.get(w.retailer) ?? null;')"
M37 anchor count: 1
$ grep -o 'intervals' served/boty/index.html | wc -l
4
```

**The competing counts are what make the anchors safe rather than lucky**, for the fourth time in
this phase. `apply_mutation` replaces the FIRST occurrence: M36 anchors on the whole conditional
expression rather than the bare name `read_at`, which also appears in `_remembered`; M37 anchors on
the whole lookup line rather than `intervals`, which appears four times on the page.

### THE FOUR FORMS AS THEY ACTUALLY RENDERED

**`boty check`'s printer, verbatim.** This is real `cli._report` output over real `Result` objects —
**no retailer was contacted**; the readings are constructed by subtraction from the real clock, this
phase's established method. Ansi colour codes stripped:

```
  ● walmart   goplusplus                    $    1.00  synthetic [age 4s]
  ○ walmart   goplusplus                               synthetic [age 7h > 6h]
  ? walmart   goplusplus                               synthetic [age ?]
```

and the fourth form, with the cadence withheld: `[age 7h, cadence ?]`.

**The page, LOOKED AT with headless Chromium**, served from `127.0.0.1` over a copy directory so the
running daemon's own `served/boty/status.json` was never written to. Both renders succeeded — no
blank page, no lost GPU context.

*Render 1, the REAL payload* (this host's `config/products.yaml`, `state.json` and `pacer-state.json`
through the current code): **13 rows, and every single one carries `AGE ?` as an amber warn tag
beside a dim `NOT CHECKED`.** No store tags at all — every row is remembered, so `store` is `null`,
and `WALMART_STORE_ID` is unset. That is the honest output and it is what this host has to show.

*Render 2, a CLEARLY SYNTHETIC payload* — stamps written by hand onto the same rows, because no
branch but `age ?` is reachable from this host's data today. All four forms appeared, at the two
weights:

| Row | Rendered | Weight |
|---|---|---|
| bestbuy control, 300 s cadence | `17S AGO` | dim label |
| gamestop control, 900 s override | `25M AGO > 15M` | **amber warn** |
| nintendo control, cadence withheld | `3H AGO · CADENCE ?` | **amber warn** |
| target control, 21 600 s cap | `7H AGO > 6H` | **amber warn** |
| every undated row | `AGE ?` | **amber warn** |

**The GameStop row is the argument made visible.** `25M AGO > 15M` — a 25-minute-old reading on a
900-second cadence, correctly warned. The banner's 1 800-second constant would have rendered that row
as an ordinary dim label. One screenshot, one row, § *Finding 9* in a picture.

### Walmart's row, as it renders today

`out_of_stock` · **`AGE ?` (warn)** · **`NOT CHECKED` (dim)** · no store tag.

**It will render exactly that, indefinitely, until a store is pinned**, and that is the honest output
rather than a defect. `state.json` holds `walmart:Pokémon GO Plus + -> "out_of_stock"` as a bare
pre-07 string with no stamp; `WALMART_STORE_ID` is unset (`QUESTIONS.md` § 0f, open), so every
Walmart reading is `Availability.UNKNOWN` and `State.transitioned_to_stock` returns before it writes.
The value cannot be updated by anything and the age genuinely is not established. Inventing one would
be this phase's own defect. **07-06's checkpoint material, and the second time this milestone has put
`QUESTIONS.md` § 0f in front of Dan.**

### The cycle-unchanged evidence

```
$ .venv/bin/python -m pytest tests/test_pacing.py tests/test_monitor.py tests/test_cli_watch.py -q
164 passed in 0.31s
```

Unchanged from 07-04's recorded 164. **Nothing about what is fetched, when, or by whom moved.**
`git diff --stat` over this plan's five task commits touches exactly the five files in
`files_modified`:

```
 boty/cli.py               | 131 +++++++++++++++-
 scripts/mutation_check.py | 103 +++++++++++++
 served/boty/index.html    | 124 ++++++++++++++-
 tests/test_dashboard.py   | 162 +++++++++++++++++++
 tests/test_status.py      | 275 ++++++++++++++++++++++++++++++++-
 5 files changed, 787 insertions(+), 8 deletions(-)
```

**`boty/status.py`, `boty/monitor.py`, `boty/pacing.py`, `boty/models.py` and `boty/retailers.py`
were NOT touched.** No key was added to or removed from `status.json`; no staleness flag is computed
at write time; `Pacer.current_interval` is neither called nor re-derived; no clock was frozen,
injected or monkeypatched.

### The two surfaces agree

```
$ .venv/bin/python -m pytest tests/test_status.py tests/test_dashboard.py -q
65 passed in 0.10s
```

## WHAT CRITERION 3's `status.json` THIRD ACTUALLY GOT

**No code and no key, and a test proving that is correct rather than a gap.** A reader looking at
`files_modified` will see no `boty/status.py` and should read this paragraph instead of concluding a
third of criterion 3 was skipped.

A `stale` flag computed inside `status.write` fails the way `pacing.py:196-199` already records for
itself: *"stamping at write time would refresh the record forever and the age-out would never fire
once — a bound that cannot bind is worse than no bound, because it reads like one in the file."* A
row written fresh carries `stale: false` and goes on carrying `stale: false` for exactly the interval
during which it becomes stale.

So the file publishes raw facts and every consumer subtracts against its own `now`.
`test_status_json_carries_everything_a_consumer_needs_to_judge_staleness` writes a payload and
derives a staleness verdict for a remembered row using **only** `w["read_at"]`, `w["checked"]` and
the `current_interval_seconds` joined out of the `retailers` array by `retailer` — then asserts no
watch row carries a `stale` key. **That test passed the moment it was written, on the RED commit,
before any implementation existed**, which is the strongest form the claim can take: the three
published facts were already jointly sufficient, and this plan measured it rather than asserting it.

## WHAT IS NOT REACHABLE IN PRODUCTION, AND WHY THAT IS NOT A HOLE

`boty check` builds no pacer for `run_once` and re-reads every watch, so every `Result` it prints was
constructed seconds before `_report` runs. **Its stale form is not reachable in production, by
construction.** Stated plainly here so nobody later notices it and calls the gate decorative:

- The stale branch is reachable **from a test to the float**, because `_age_tag` is a module-level
  pure function taking `now` and `interval` as required keywords. That purity is the entire reason no
  clock is frozen anywhere in this phase.
- The `[age ?]` form **is** reachable in production, today, on this host — and stronger than the plan
  predicted. The plan expected five of thirteen rows; **measured, it is thirteen of thirteen**, since
  `state.json` holds 13 availabilities and **0** stamps.
- The `cadence ?` form is reachable only when `_report` is called without cadence facts, which the
  AST gate forbids at the one production call site.

## Corrections recorded beside the planning documents, never edited into them

Same footing as 07-01's nine-arms note, 07-02's two-extra-comments note, 07-03's five and 07-04's
eight. **No planning document was edited.**

### 1. The "~97-minute cadence" is `skipped_reason`'s time REMAINING, and the threshold is 21 600 s

`07-PLAN-OUTLINE.md` § *Finding 9* and `07-PATTERNS.md` both say *"a retailer at seven refusals is
legitimately on a ~97-minute cadence"*. `min(300 · 2⁷, 21600)` = **21 600 s**, the six-hour cap.
07-03 recorded the correction; this plan **uses** it, and M37's `breaks=` sentence is built on it.

### 2. The idents were M36/M37, not the outline's M35/M36

Confirmed before registering, exactly as the plan required: `grep -c 'ident="M'` read **31**, and
07-04's registry comment stated *"M36/M37 are 07-05's"*. No renumbering was needed and none was done.
**The registry ends this phase at 33, the phase added SEVEN idents (M31–M37) rather than the
outline's six, 07-06 still records the count rising FROM 26, and M21–M24 remain the intentional gap
and were not filled.** Fifth statement of that lesson in this phase.

### 3. The per-retailer cadence table moved AGAIN, and this is now the third reading

Re-measured off `pacer-state.json` at **13:06:36Z today**, through `Pacer.current_interval`:

| Retailer | Plan's table (09:41) | **Measured here (13:06Z)** |
|---|---|---|
| target | 7 refusals -> 21 600 s | **11 refusals -> 21 600 s** |
| walmart | 7 refusals -> 21 600 s | **0 refusals -> 300 s** |
| amazon | 0 refusals -> 1 800 s | **4 refusals -> 21 600 s** |
| gamestop | 900 s (override) | **900 s** |
| bestbuy, nintendo | 300 s | **300 s** |

**Walmart and amazon swapped ends of the range between two readings of the same file.** The plan
argued from one such move; this is a second, larger one, and it is the sharpest possible defence of
criterion 3's *"derived from the retailer's own pacing rather than a fixed clock"*. It also means
M37's `breaks=` was written with the conditional *"while they are refusing us"* rather than a
timestamped claim — deliberately, and it is still accurate at both readings.

### 4. `_report`'s call sites have moved since the plan measured them

The plan's § *Measurement note 2* names `boty/cli.py:595`, `tests/test_status.py:214` and `:280`.
Measured today: **`boty/cli.py:707`, `tests/test_status.py:729` (the `_tags` helper) and `:795`.** The
COUNT — one production, two test — is what the argument rested on and it is unchanged, so the
required keyword cost exactly three lines as predicted.

### 5. The denominator is 13, reproduced through the loader

`Config.load('config/products.yaml') -> 13 watches`, and the live render shows 13 rows. 07-04's
correction stands; the fourteenth `grep -c "retailer:"` match is a comment at
`config/products.yaml:309`. **07-06's checkpoint must say 13.**

## Residuals carried forward

### THE RUNNING DAEMON PREDATES THIS ENTIRE PHASE — 07-06 needs this

Measured, not inferred. The live `served/boty/status.json` was 111 seconds old when read, so the
daemon is alive and writing. Its watch rows carry **13 keys and none of the phase's four**:

```
has read_at: False | has checked: False | has current_interval_seconds: False
rows: 5
```

The writing process is `boty watch`, PID 547119, **started Wed Aug 12 17:28:29 2026** — before 07-01
landed. It holds pre-phase code in memory, and an editable install does not reach a process that is
already running.

**So the rendering is complete in the tree and invisible on the live page until that process is
restarted.** Nothing in this plan can fix that, and nothing should: restarting the daemon is an
operational act on a service that is paging a human. Recorded for 07-06, whose checkpoint is the
right place to put it in front of Dan — and note that the *page itself* handles the old file
correctly, which is the next entry.

### The page tolerates the pre-phase file, verified against the real one

Run against the LIVE daemon's own `status.json` — the one with no `read_at`, no `checked` and no
`current_interval_seconds` — using the page's own `ageTag` and `storeTag` lifted verbatim out of the
template:

- every row rendered **`age ?`**, correctly, because `w.read_at == null` catches `undefined` as well
  as `null`. No `NaN ago`, no `0s ago`, no crash.
- every row **kept its store tag**, because `w.checked === false` is `false` when the key is
  `undefined`. That is precisely the `=== false`-not-`!w.checked` decision, measured against the file
  it was written for rather than argued in the abstract.

One row of that live file carries a real store number in `store` with `store_pinned: null`, so it
renders the *unpinned* warn form. **The number is not reproduced here** — this file is tracked and
`identity_check` runs over it. The row is pre-existing and outside this plan's scope.

### `pacer-state.json` is still written non-atomically

Unchanged from 07-03's T-07-03b and 07-04's residual, and deliberately not touched: the failure
direction over-reports staleness, which is the safe direction. **07-06's judgement.**

### The idents, closed

**M36/M37 consumed here. The registry stands at 33. The phase added seven idents. 07-06 records the
rise FROM 26. M21–M24 unfilled.** 07-06 depends on this paragraph and on nothing else for its count.

## Deviations from Plan

Four, all recorded rather than quietly absorbed. None changed what shipped.

**1. [Rule 3 — the escaping test went red on this plan's own COMMENT]**

- **Found during:** Task 2, first run after the dashboard edit.
- **Issue:** the plan's action text instructs the comment above `ageTag` to explain why the whole Map
  is passed by quoting the forbidden form `${ageTag(w, intervals.get(w.retailer), nowS)}`. Written
  that way, `test_every_retailer_controlled_string_is_escaped_before_innerhtml` goes **red on the
  comment** — it scans every `${...}` in the FILE and cannot tell prose from code.
- **Fix, following the tree over the plan:** the comment DESCRIBES the offending form instead of
  quoting it, and records in place that the test reads comments too, calling that the check being
  coarse in the safe direction. The test was **not** edited.
- **Committed in:** `4d91d26`.

**2. [Rule 3 — M37's killer test went red on this plan's own CSS comment]**

- **Found during:** Task 2, same run.
- **Issue:** the plan requires the CSS comment to carry § *Finding 9*'s arithmetic — which names the
  banner's constant — and separately requires a test asserting `\b1800\b` occurs exactly once on the
  page. Three prose mentions plus the code constant made it four.
- **Fix:** the comment writes the number **with a space** (`1 800`), matching this repo's own house
  style for `21 600`, and says in place that the spacing is load-bearing and must not be "tidied".
  The assertion keeps its full strength. Same class of error as `grep -c 'ident="M'` counting prose,
  which § *Finding 1* records one file over — **second occurrence in this phase, and the first on a
  non-Python surface.**
- **Committed in:** `4d91d26`.

**3. [Rule 3 — `storeTag`'s register argument had to move ABOVE the function]**

- **Found during:** Task 2.
- **Issue:** the plan puts the early return first inside `storeTag` with its three-sentence argument
  above it, and separately specifies a test regex of
  `const storeTag[\s\S]{0,400}?w\.checked === false`. The argument runs to roughly 700 characters, so
  the two requirements are not simultaneously satisfiable.
- **Fix:** the argument was hoisted into the comment block that already sits above `const storeTag`,
  which is where the plan says the next reader will look anyway, and the early return is now the
  literal first statement. The 400-character window was **not** widened — weakening a gate to fit a
  comment is the wrong direction.
- **Committed in:** `4d91d26`.

**4. [Recorded, not a rule — M36's measured catch is ONE test, not the three the plan predicted]**

- **Found during:** Task 3, at the by-hand red-watch, before the harness was ever run.
- **Issue:** the plan names the `[age ?]` capsys test, the boundary test AND the join test as M36's
  killers. Only the first fires. The boundary test constructs a stamp, so `read_at is None` is never
  reached in it; the join test reads `status.json`, which `_age_tag` does not touch.
- **Fix, following the tree over the plan:** the registry comment names the **one measured killer**
  and states why the other two cannot fire, plus what to check first if M36 ever survives. Writing
  the predicted list would have published a larger catch than the one that happened — 07-04's
  deviation 1, second occurrence, and 07-02's Pattern 3.
- **Committed in:** `9f7232f`.

**Total deviations:** 4. **Impact on scope:** none. No package was installed, no dependency added, no
clock frozen, injected or monkeypatched, and no live retailer read was made.

## Scope fence, honoured

`identity_check` -> **PASS — 219 file(s), no host identity found**. No real store number and no host
identity was written into a tracked file; the live file's store value is referred to and not
reproduced. `served/boty/status.json`, `state.json` and `pacer-state.json` are all gitignored, so the
running daemon never disturbed a `git status --porcelain` check. The two headless renders were served
from a scratch copy on `127.0.0.1` — **no network egress, and the daemon's own served file was never
written to.**

**REQ-21 is NOT marked complete here**, on the outline's rule and 07-01's, 07-02's, 07-03's and
07-04's precedent: *a requirement is not marked complete by the plan that ships its code.* **07-06
closes it by measuring what landed.** `requirements-completed` is `[]` deliberately.

## Next Phase Readiness

**07-06 can start.** What it inherits:

- **All three of criterion 3's surfaces rendering**, judged against 07-03's per-retailer cadence:
  `status.json` (proved sufficient, no key added), `boty check` (`_age_tag`), the dashboard
  (`ageTag`).
- **Criterion 2's rendering half**, on both consumers, pinned by M36.
- **A registry at 33** with survivors 0, and the ident arithmetic written down in
  `scripts/mutation_check.py` so it does not need re-deriving.
- **Two open items for its judgement:** `pacer-state.json`'s non-atomic write, and the running
  daemon's pre-phase process.
- **Its checkpoint's numbers, measured:** 13 configured watches, 13 rows, 13 of them rendering
  `age ?` today, and `QUESTIONS.md` § 0f still open.

## Self-Check: PASSED

Every claim above re-measured against the tree after this SUMMARY was written:

- **5 modified files** all present; this SUMMARY present.
- **5 task commits** all resolvable: `dfbcf7b`, `c5bdc95`, `09d3e14`, `4d91d26`, `9f7232f`.
- `def _age` and `def _age_tag` present in `boty/cli.py`; `age = None if r.read_at is None else now -
  r.read_at` present and counting **1**; `_report(results, health, intervals=intervals)` present at
  the one production call site.
- `.tag.age.warn`, `const fmtDur`, `const ageTag`, `intervals.get(w.retailer)` and
  `w.checked === false` all present in `served/boty/index.html`; `\b1800\b` counts **1**; `\b5400\b`
  counts **1**.
- `ident="M36"` and `ident="M37"` present; `grep -c 'ident="M'` -> **33**.
- `make verify-offline` -> **EXIT=0**, 865 passed, **33/33**, survivors **0**.
- `.venv/bin/mypy` -> clean over 18 source files.
- `git status --porcelain` empty, proving both by-hand red-watches were reverted.

---
*Phase: 07-a-reading-has-an-age*
*Completed: 2026-08-14*
