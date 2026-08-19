---
phase: 07-a-reading-has-an-age
plan: 06
subsystem: planning
tags: [closing-record, verdicts, req-21, mutation-testing, checkpoint, no-code]

# Dependency graph
requires:
  - phase: 07-a-reading-has-an-age
    plan: 01
    provides: "`Result.read_at` at all 20 sites, the static AST completeness gate, M31 — criterion 1's evidence and criterion 2's datum half"
  - phase: 07-a-reading-has-an-age
    plan: 02
    provides: "the dated ledger, the real pre-07 document loading unchanged, M32 — criterion 4's evidence"
  - phase: 07-a-reading-has-an-age
    plan: 03
    provides: "`Pacer.current_interval` and the schedule asserted unmoved against literal seconds, M33 — criterion 3's threshold"
  - phase: 07-a-reading-has-an-age
    plan: 04
    provides: "a row that can be old — 13 rows where the file had 3-10 — M34/M35, and the 13-not-14 correction"
  - phase: 07-a-reading-has-an-age
    plan: 05
    provides: "the four rendered forms on both surfaces, M36/M37, and the join test that made criterion 3's status.json third arguable at all"
provides:
  - "five criterion verdicts in `.planning/ROADMAP.md` — three MET as written, criteria 3 and 5 MET IN PART"
  - "REQ-21 closed with an evidence-bearing traceability cell and two measurement notes below the table"
  - "`docs/retailer-evidence.md` § Phase 7 closing record, beside the Phase 6 record"
  - "Dan's `keep defer`, verbatim and dated 2026-08-17, in STATE.md, QUESTIONS.md § 0f and the closing record"
  - "the ident arithmetic written once and correctly: 26 + 7 = 33, with M21-M24 named as Phase 6's deliberate gap"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "a closing record whose measurements carry INDIVIDUAL dates, because a blocking checkpoint held the plan open across three days and the phase's own thesis forbids calling any of them 'today'"
    - "re-measuring a gate at close and reporting 'identical' as the finding, rather than silently reusing the earlier run"
    - "declining to spend a second live pass purely to attach a fresher date, and labelling the older verdict instead"
    - "not invoking a tool with thirteen recorded deterministic misfires, and recording the non-invocation as the reason the count did not rise"

key-files:
  created:
    - .planning/phases/07-a-reading-has-an-age/07-06-SUMMARY.md
  modified:
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
    - docs/retailer-evidence.md
    - QUESTIONS.md

key-decisions:
  - "criterion 3 closed MET IN PART: `status.json` publishes the INGREDIENTS of a staleness verdict and not the verdict, and *sufficient to derive* is a different sentence from *presented as*"
  - "criterion 5 closed MET IN PART: one gate this phase adds — 07-05's join test — was never observed failing, and naming it is the point"
  - "the live `make verify` was NOT re-run after the checkpoint; its verdict is labelled a 2026-08-14 observation rather than restated as current, because a second live pass against six retailers for a cosmetic date is not a trade this project makes"
  - "`make verify-offline` WAS re-run at close, and 'identical on every verdict line' is reported as the measurement rather than the 08-14 numbers being silently reused"
  - "`gsd-tools state` write subcommands were not invoked at all; every delta was hand-written after a `cp`, so the misfire count stands at THIRTEEN rather than fourteen"
  - "no follow-up plan was logged for a dashboard collapse/filter affordance, because Dan answered `keep` and not `note-it`"

patterns-established:
  - "Pattern 1: when a checkpoint holds a plan open across days, every measurement in the record carries its own date and the record says which were re-measured, which were identical, and which were deliberately not repeated"
  - "Pattern 2: a verdict table that could read five-for-five and does not is the only kind worth writing in a milestone about undated claims"

requirements-completed: [REQ-21]

# Metrics
duration: ~45min of execution across 3 days (blocking checkpoint 2026-08-14 → 2026-08-17)
completed: 2026-08-17
---

# Phase 7 Plan 06: Close — Five Verdicts, Two of Them Partial — Summary

**Phase 7 closed on three of five criteria MET as written, with criteria 3 and 5 recorded MET IN
PART rather than rounded up; the registry shown rising from 26/26 to 33/33 with M21-M24 named as
Phase 6's deliberate gap; the live `make verify` FAIL recorded verbatim with its three classes
separated and none of them this phase's; and Dan's `keep defer` recorded verbatim with its date.
No code was written, no criterion text was touched, and no store number was read, derived,
inferred, requested or printed.**

## Performance

- **Duration:** ~45 min of execution, spread across 3 days. Task 1 measured 2026-08-14; the
  blocking checkpoint held the plan open until Dan answered on 2026-08-17; Task 3 wrote the
  record that day. **Wall-clock elapsed and execution time are recorded separately, because
  conflating them is this milestone's own defect.**
- **Tasks:** 3 (1 measurement, 1 blocking checkpoint, 1 record)
- **Files modified:** 5, plus this SUMMARY
- **Commits:** 1

## THE DATES ARE NOT ALL THE SAME, AND THIS RECORD SAYS SO

This is the first thing in this file because it is the thing this phase, of all phases, could
most easily have got wrong.

| What | When measured | Status at close |
|---|---|---|
| `make verify-offline` | 2026-08-14 **and** 2026-08-17 | **Re-measured — identical on every verdict line** |
| The mutation registry and all seven CAUGHT idents | 2026-08-14 and 2026-08-17 | Re-measured, identical |
| `Config.load` watch count (13) | 2026-08-14 | Not re-measured; config unchanged, nothing committed in the gap |
| Live row counts (5 / 5 / 10) | 2026-08-14 | **Dated 08-14 throughout; not restated as current** |
| `systemctl show boty` | 2026-08-14 **and** 2026-08-17 | **Re-measured — same PID, same start time, unchanged** |
| `state.json` Walmart entry | 2026-08-14 **and** 2026-08-17 | **Re-measured — still `out_of_stock`, still frozen** |
| Store-pin presence count (`0`) | 2026-08-14 **and** 2026-08-17 | Re-measured, still `0` |
| Live `make verify` | 2026-08-14 only | **Deliberately NOT repeated — labelled a 08-14 observation** |
| The leaked-markup sweep | 2026-08-14 | Dated 08-14 |
| Dan's answer | **2026-08-17** | Recorded verbatim with that date |

**Why the live pass was not repeated.** Politeness is a hard constraint here and this close was
budgeted exactly one live pass, spent on 08-14 immediately after a daemon write. Re-running a
probe against six retailers to attach a fresher date to an unchanged verdict is a real cost for
a cosmetic gain. The verdict is therefore **labelled** rather than refreshed, which is the same
discipline the phase built into the code.

**Nothing landed in the gap.** `git log --since=2026-08-14T14:00` is empty, so no commit moved
between Task 1 and Task 3.

## Task Commits

1. **Task 1: Measure what landed** — *no commit, and that is correct.* The task's own `<files>`
   is `(no files modified)` and its `<done>` requires `git status --porcelain` clean. It was.
   Manufacturing a commit would have breached Task 3's changed-file allow-list.
2. **Task 2: The two consequences, put to Dan** — *no commit.* Blocking checkpoint; nothing was
   built while waiting and nothing was restarted.
3. **Task 3: Five verdicts, one requirement, the closing record** — **one commit**, carrying all
   five closing files plus this SUMMARY. `git config user.email` was checked against the repo's
   own history first (`3347065+danieljamesjohnson@users.noreply.github.com`, matching the last
   five commits), because author identity has silently gone wrong here before. The pre-commit
   hook re-ran `identity_check` over the staged set: **PASS — 6 file(s)**.

## Evidence

### `make verify-offline` at close, 2026-08-17, verbatim

```
identity check: PASS — 220 file(s), no host identity found
All checks passed!
865 passed in 10.95s
Success: no issues found in 18 source files
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 33 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (836 passed, 29 skipped in 11.27s)
mutation check: 33/33 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
EXIT=0
```

**Re-measured, not inherited.** The 2026-08-14 run of the same command agrees on **every**
verdict line — identity 220, `865 passed`, mypy over 18 source files, `33/33`, `EXIT=0`,
survivors 0. The only byte that differs in the whole comparison is the pytest wall-clock:
`865 passed in 10.87s` (08-14) versus `865 passed in 10.95s` (08-17). **Reporting "identical"
is the honest claim; substituting one run for the other silently would not have been.**

### The rise, shown rather than claimed

| Point | Tests | Mutations | Identity |
|---|---|---|---|
| Phase 4 close (pre-milestone) | 531 | 8/8 | — |
| Phase 5 close | 667 | 16/16 | — |
| Phase 6 close | 768 → 769 | 24/24 | — |
| **Phase 7 start** (`dbc9d49`, 2026-08-13) | **778** | **26/26** | 208 files |
| 07-01 | 798 | 27/27 | 215 |
| 07-02 | 821 | 28/28 | 216 |
| 07-03 | 835 | 29/29 | 217 |
| 07-04 | 848 | 31/31 | 218 |
| 07-05 | 865 | 33/33 | 219 |
| **07-06 close (2026-08-17)** | **865** | **33/33** | **220** |

`865` unchanged from 07-05 and identity `220` one above it: correct, because this plan wrote no
code and the one new tracked file was its own PLAN.

### The full ident list, READ from the registry with comment lines filtered

```
M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M13 M14 M15 M16 M17 M18 M19 M20
M25 M26 M27 M28 M29 M30 M31 M32 M33 M34 M35 M36 M37
count: 33 | M21-M24 absent: True
```

**The arithmetic, stated once: 26 at phase start + 7 this phase = 33.** A bare
`grep -c 'ident="M'` happens to agree at **33** on this tree, but it is not what was used and
it is not what should be used — it counts comment prose, and it is the class that produced
both the wrong registry figure and the wrong watch count this phase had to correct.

Each of the seven, CAUGHT by ident, from the close-time run:

```
CAUGHT M31 boty/retailers.py: 2 test(s) failed — test_the_read_and_non_read_arms_are_partitioned_exactly, ...
CAUGHT M32 boty/monitor.py: 7 test(s) failed — test_a_reading_the_first_process_could_not_date_comes_back_undated, ...
CAUGHT M33 boty/pacing.py: 11 test(s) failed — test_both_surfaces_publish_one_cadence_from_one_document, ...
CAUGHT M34 boty/status.py: 4 test(s) failed — test_every_configured_watch_has_a_row_while_only_the_due_ones_are_fetched, ...
CAUGHT M35 boty/status.py: 2 test(s) failed — test_every_configured_watch_has_a_row_while_only_the_due_ones_are_fetched, ...
CAUGHT M36 boty/cli.py: 1 test(s) failed — test_report_says_unknown_for_a_reading_nobody_dated
CAUGHT M37 served/boty/index.html: 1 test(s) failed — test_the_row_threshold_is_the_retailers_own_cadence_and_not_a_fixed_clock
```

**Survivor list empty** — `grep -c SURVIVED` over the captured run returns **0**.

**`M21`-`M24` ARE A DELIBERATE GAP LEFT BY PHASE 6 AND ARE NOT FOUR LOST MUTATIONS.** 06-03:
*"NO MUTATION REGISTERED, and M21-M22 left deliberately unallocated: `apply_mutation` cannot add
a file, so the defect is outside the harness by construction."* 06-04: *"M23-M24 left
unallocated, joining 06-03's M21-M22, so the sequence carries a deliberate gap at M21-M24."*
The governing rule is `tests/test_support_matrix.py`'s own message — *"Idents are reserved
across concurrent plans, not renumbered"* — and `scripts/mutation_check.py` restates the gap
three separate times in its own comments.

### The measured numbers the checkpoint card quoted

**Configured watches, through the loader and not a grep:**

```
Config.load('config/products.yaml') -> 13 watches
by retailer: gamestop 5, walmart 2, nintendo 2, amazon 2, bestbuy 1, target 1
controls: 6
grep -c "retailer:" config/products.yaml -> 14
```

The fourteenth match is a **comment** at `config/products.yaml:309` — *"There is no
`retailer: pokemoncenter` entry and that is a finding, not a gap"*. **The card said 13, and it
was measured before it was said.**

**The live row count, measured three times in eleven minutes on 2026-08-14**, against 13
configured watches and an unchanged config:

| when | rows | bytes |
|---|---|---|
| 2026-08-13 08:25:10 | 3 | — |
| 2026-08-13 09:24:54 | 8 | — |
| 2026-08-14 07:36:57 | 5 | 4 604 |
| **2026-08-14 08:43:44** | **5** | 4 603 |
| **2026-08-14 08:48:32** | **5** | — |
| **2026-08-14 08:54:14** | **10** | 7 192 |
| 2026-08-17 07:20:39 (at close) | 10 | 7 159 |

**The count moved 5 → 10 between two consecutive cycles of the same daemon, five minutes
apart.** That is the third and fourth data point for the same statement: the row count is a
function of pacing.

**`systemctl show boty`, measured 2026-08-14 and re-measured 2026-08-17:**

```
MainPID=547119
ActiveEnterTimestamp=Wed 2026-08-12 17:28:29 CDT
ActiveState=active / SubState=running
EnvironmentFiles=/home/dan/.config/boty/env (ignore_errors=no)
ps: /home/.../.venv/bin/boty watch -c config/products.yaml
```

**Unchanged across the whole checkpoint.** The first commit of this phase is 2026-08-13
08:56:00, so the running process predates 07-01 by ~15 hours, and the `status.json` it writes
carries `has read_at: False | has checked: False | has current_interval_seconds: False`.
**Nothing was restarted.**

**Walmart's frozen entry, confirmed without reading a store number.** `boty/monitor.py:342-343`
returns on `Availability.UNKNOWN` **before** `self.seen[key] = ...` at line 346. `state.json`
holds **13 entries, all 13 bare pre-07 strings** on 08-14 and again on 08-17, with
`walmart:Pokémon GO Plus +` reading `'out_of_stock'` both times — **unchanged through five days
of the daemon rewriting that file every cycle.** That is the freeze demonstrated over time
rather than argued from the code path alone.

**The pin's absence, as a COUNT and never as a value**, on 08-14 and again on 08-17:

```
grep -c 'WALMART_STORE_ID' /home/dan/.config/boty/env  ->  0
```

Nothing was run under the service's `EnvironmentFile`. **No store number was read, derived,
inferred, requested or printed at any point in this plan.**

## DAN'S ANSWER, VERBATIM, WITH THE DATE

**`keep defer`** — 2026-08-17, at the blocking checkpoint. `autonomous: false`,
`gate="blocking"`. `workflow.auto_advance` is `true` on this project and was **not** applied.

- **`keep`** — the constant 13 rows stand as shipped, remembered ones labelled as memories.
  **Recorded as seen and accepted.** He did **not** choose `note-it`, so **no follow-up plan for
  a dashboard collapse/filter affordance was logged**, and none should be inferred from this
  record. Nothing was built on the answer.
- **`defer`** — no store pin now. **§ 0f stays open.** Walmart's GO Plus + row publishes
  `out_of_stock · age ? · not checked` **indefinitely, until a store is pinned** — the honest
  output, because the age genuinely is not established and inventing one would be the exact
  failure REQ-21 exists to remove.

**What was therefore NOT decided:** whether the dashboard ever gets a way to collapse or filter
remembered rows (not asked for, not logged); whether or when the daemon is restarted; and
whether a store is ever pinned. All three remain Dan's, and § 0f stays on the page because the
action stays available, not because anything is blocked.

**How many deferrals — measured rather than repeated.** `07-06-PLAN.md` and two SUMMARYs call
this *the third*. Measured against the record: § 0f was created 2026-08-10 (`e55f733`) and has
been put to Dan **twice** — 05-04's checkpoint on 2026-08-10 and 07-06's on 2026-08-17 — so this
is the **second time he has answered it himself**, and the **third time it has been deferred by
any means**, counting the acknowledged deferral at v0.2's milestone close on 2026-08-11 which
carried no new answer from him. **Both readings are recorded in QUESTIONS.md, STATE.md and the
closing record; neither is reconciled away.**

## THE FIVE VERDICTS AS WRITTEN INTO THE ROADMAP

Reproduced here so the SUMMARY and the ROADMAP can be diffed against each other.

| # | Verdict |
|---|---|
| 1 | **MET in the tree — NOT ON THE WIRE** |
| 2 | **MET in the tree — NOT ON THE WIRE. Spans two plans** |
| 3 | **MET IN PART** — `boty check` and dashboard thirds MET; the `status.json` third NOT SETTLED |
| 4 | **MET in the tree — NOT ON THE WIRE, and the restart is the whole of what is missing** |
| 5 | **MET IN PART** — the gate half MET; *"every gate"* NOT fully MET |

**Three of five MET as written; criteria 3 and 5 MET IN PART.** No criterion text anywhere in
`ROADMAP.md` was reworded, shortened, merged or amended — **34 criterion bodies at baseline, 34
now, none removed, none added**, asserted by command with a `HEAD~1` fallback. REQ-21's body is
byte-identical after whitespace normalisation, also asserted.

### Criterion 3's argument, in full, because this is the row that must not be rounded up

**What landed.** 07-05 added **no staleness flag and no new key** to `status.json`. Quoted from
`pacing.py:196-199`'s own recorded lesson, one file over: *"stamping at write time would refresh
the record forever and the age-out would never fire once — a bound that cannot bind is worse
than no bound, because it reads like one in the file."* A `stale` boolean computed inside
`status.write` is written `false` and goes on saying `false` for exactly the interval during
which the row becomes stale.

**What was measured instead of asserted.** A join test derives a staleness verdict for a
remembered row using **only** `read_at`, `checked`, and `current_interval_seconds` joined out of
the `retailers` array — then asserts no watch row carries a `stale` key. Quoted from 07-05:
*"That test passed the moment it was written, on the RED commit, before any implementation
existed, which is the strongest form the claim can take."*

**The argument that it MEETS the criterion.** Everything required to present staleness is
published; sufficiency is proved by execution rather than inspection; both other surfaces
present it from those same values with no second source of truth; and a `stale` key would have
been demonstrably wrong.

**The argument that it does NOT.** The criterion says *"presented as stale in `status.json`"*.
The file presents the **ingredients** of the verdict, not the verdict. A person opening it sees
three numbers and must subtract against their own clock. *Sufficient to derive* and *presented
as* are different sentences, and the gap between them is exactly the size of gap this milestone
exists because somebody published across.

**Verdict reached: MET IN PART.** Two of three named surfaces present staleness; the third
publishes what is needed and does not present it. The criterion's text is **not edited**, no key
was added to make the row read MET, and it is not marked MET on the strength of the other rows.

### Criterion 5's enumeration, because seven mutations are not "every gate"

Every TDD gate in the phase was observed failing before its implementation existed, at a RED
count recorded at the time: 07-01 (3 failed / 33 passed, then 5 failed, then 4 failed), 07-02
(14 failed / 29 passed, then 2 failed / 45 passed), 07-03 (5 failed / 68 passed, then 5 failed /
25 passed), 07-04 (10 failed / 29 passed, then 3 failed / 39 passed), 07-05 (20 failed / 30
passed, then 6 failed / 9 passed). Beyond the mutations the phase adds static AST completeness
gates (07-01's 20-site census, 07-04's both-call-site gate), producer/consumer pairs, a
cross-surface equality test and a join test.

**The one gate never watched going red, named rather than absorbed:** 07-05's
`test_status_json_carries_everything_a_consumer_needs_to_judge_staleness`. It passed on the RED
commit. That is a measurement, not a weak test — but the criterion says *every* gate.
**MET IN PART.**

## THE LIVE `make verify` VERDICT — 2026-08-14, verbatim, NOT re-run

```
control check: FAIL — 2/6 control(s) not reading IN_STOCK
    walmart/CONTROL — Great Value whole milk: unknown — no store_id pinned for this watch
    amazon/CONTROL — Amazon Basics AA batteries (20-pack): unknown — blocked: challenge page
      matched 'to discuss automated access to amazon data' (HTTP 200)
control check: 2/6 control(s) could not run on THIS HOST
    bestbuy/CONTROL — Pokémon Let's Go, Pikachu! (Switch): fetch failed: no Chrome/Chromium binary found
    target/CONTROL — up&up microfiber dust cloths: fetch failed: no Chrome/Chromium binary found
VERIFY: FAIL (live controls)
EXIT=2
```

Started 08:54:19 on 2026-08-14, immediately after the daemon's own 08:54:14 write, so the two
were not in flight against the same six retailers. Run **once**, in a shell with no
`WALMART_STORE_ID`, and **not** under the service's `EnvironmentFile`.

**The classes, separated, with none of them this phase's:**

1. **2/6 could not run on THIS HOST** — Best Buy and Target, no Chrome/Chromium binary.
   Pre-existing since 2026-08-06; the tool itself says this *"says nothing about the DETECTOR"*.
2. **The intermittent challenge class DID manifest**, on Amazon. Absent on both 2026-08-10 and
   2026-08-11, so across four passes the record reads present-absent-absent-present and
   *intermittent* remains the supported reading rather than *permanent*.
3. **Walmart through Phase 5's config-gap guard** — Phase 5's, and **correct**.

The baseline reads *"1/6 not reading IN_STOCK"*; this reads **2/6** because class 2 manifested,
**not** because a new class appeared. **No control's verdict moved in a way attributable to this
phase** — GameStop and Nintendo both read `in_stock` as before, and no plan in this phase touched
a retailer, extractor, transport or control. Recorded, **not diagnosed**, and **not re-run until
green**.

## THE LEAKED-MARKUP SWEEP, RE-MEASURED AT CLOSE

**Pattern used:** the two closing tag forms, the opening call form, the parameter-open form and
the namespace prefix, joined as alternatives and **assembled at runtime** so this file does not
become the fifth instance in the list it is describing.

**Measured 2026-08-14: 29 matching lines in 9 files.**

| File | lines |
|---|---|
| `.planning/phases/04-open-source-ready/04-REVIEW.md` | 3 |
| `.planning/phases/06-claims-with-gates-under-them/06-04-SUMMARY.md` | 6 |
| `.planning/phases/06-claims-with-gates-under-them/06-CONTEXT.md` | 1 |
| `.planning/phases/06-claims-with-gates-under-them/06-PATTERNS.md` | 3 |
| `.planning/phases/06-claims-with-gates-under-them/06-VERIFICATION.md` | 8 |
| `.planning/phases/07-a-reading-has-an-age/07-01-SUMMARY.md` | 1 |
| `.planning/phases/07-a-reading-has-an-age/07-02-SUMMARY.md` | 1 |
| `.planning/seeds/nothing-reads-the-changelog-body.md` | 2 |
| `tests/test_changelog.py` | 4 |

Classified structurally without reproducing any shape: the whole-line tag shapes sit at
`04-REVIEW.md:113-114`, `06-VERIFICATION.md:267-268` and `:386-387` — **all four inside fenced
code blocks**, i.e. deliberate recorded evidence of the class — and at
`.planning/seeds/nothing-reads-the-changelog-body.md:15-16`, which is **not** fenced. The
remaining 23 are prose naming the class or `tests/test_changelog.py`'s own gate fixtures.

**29 and "four instances" are different quantities, and both are recorded rather than
reconciled.** The sweep pattern matches records-of-leaks as well as leaks. **The pattern was NOT
adjusted to make its number match a remembered one.**

**The four instances, each with its own evidence:**

1. **`05-02-PLAN.md`** — a stray tag pair at its end, **caught by a planning agent before
   commit**. A near-miss: no trace in the tree, and the evidence is the note.
2. **`06-PATTERNS.md`** — a committed sweep hit, produced **in the act of measuring the sweep**.
3. **`06-07-SUMMARY.md` at `a71e79b`** — committed, two whole-line closing tags after its
   metadata line, **one day after the gate for that exact byte-shape landed**. Removed at
   `7355034` and recorded rather than quietly fixed; the evidence is permanent at `a71e79b`.
4. **`07-01-PLAN.md`, 2026-08-13** — caught before commit while the file was being written. The
   **fourth** instance, the **second** produced by an agent writing a PLAN into `.planning/`, and
   the second near-miss.

**No gate this repository ships covers `.planning/`.** Flagged for the fourth time, fixed
nowhere.

## EVERY CORRECTION FROM WAVES 1-5, QUOTED FROM THE SUMMARY THAT MADE IT

**`07-CONTEXT.md`, `07-PATTERNS.md`, `07-PLAN-OUTLINE.md` and REQ-21's text are flagged where
they are wrong and edited nowhere.**

**1. Three documents, three different wrong registry figures.** `07-CONTEXT.md` says *"26
mutations at M1–M20, M25–M28 … New idents start at M29"* — the set is wrong **and counts to
24**, and M29/M30 already existed as Phase 6's paging pair, so new idents actually started at
**M31**. `07-PATTERNS.md` § 6 corrects the set to `M1-M20, M25-M30` and calls it **28** in the
same sentence — twenty plus six is **26**. `07-PLAN-OUTLINE.md` assigns **six** new idents with
M35/M36 to 07-05; **seven** landed. 07-04: *"This plan consumed M34 and M35, the next two free
idents. Taking M35–M36 would have left M34 an orphan beside M21–M24."* **`07-CONTEXT.md` was
auto-generated under `workflow.skip_discuss`, so its errors are drafting errors and nothing Dan
decided is being re-opened.**

**2. The denominator is 13, not 14.** 07-04: *"`Config.load('config/products.yaml') -> 13
watches`; gamestop 5, walmart 2, nintendo 2, amazon 2, bestbuy 1, target 1; 6 of them
controls."* The fourteenth `grep` match is a comment at `config/products.yaml:309` — *"a
sentence about an ABSENT watch counted as a present one. Same class of error as `grep -c
'ident=\"M'` counting prose."* Reproduced through the loader again by 07-05 and by this plan.

**3. "~97-minute cadence" is a remaining-time figure, not a cadence.** 07-03: *"`300 x 2**7` =
38 400 s, which exceeds `MAX_BACKOFF_SECONDS` (21 600 s), so target and walmart at seven
refusals are on the six-hour CAP, not on ~97 minutes. The ~97 and ~53 minute figures … are
`skipped_reason`'s time remaining until the next attempt, which is a different quantity from a
cadence."* A 1 800 s threshold would have painted every one of their rows stale while they
behaved exactly as the politeness rule requires; M37's `breaks=` rests on the corrected number.

**4. The absent-row finding, which reframed the phase.** 07-04: *"the watch list changed size
three times without the configuration changing once … a reader who checked the page twice in a
morning had no way to tell a watch that had been removed from a watch that had not been asked."*
**REQ-21's own sentence *"the page presents both as current"* is one direction off** — the stale
row was not presented at all, which is worse rather than better, and Dan's opening question
cannot be answered by a missing row either. Recorded below REQ-21's **unedited** text.

**5. Three near-miss mutation anchors, each measured before it was walked into, with numbers.**

- **M33** (07-03): *"The multi-line anchor is 1. The single-line fragment is 2, and the first
  occurrence is `MAX_PERSISTED_REFUSALS`' comment"* — at **line 156**, with the real code at
  **line 344**. A single-line anchor would have mutated **prose**, changed no behaviour and
  **SURVIVED**.
- **M34** (07-04): the single-line `"checked": False,` fragment counts **2**, and *"the first
  single-line … is line 193, the retailers array's paced branch — a different rule entirely. A
  single-line anchor would have mutated that, been killed by `tests/test_pacing.py:320`'s
  paced-retailer test, and stood in the registry as a gate on something it does not gate."*
  `grep -c '"checked":'` reads **4**; the two-line anchor counts **1**. **M35**'s anchor counts
  **1** without extension.
- **M36/M37** (07-05): both anchors count **1**, while *"`read_at` … also appears in
  `_remembered`"* (3 occurrences in `boty/cli.py`) and `intervals` *"appears four times on the
  page"*. **Fourth pre-count in the phase.**

**A gate that cannot go red is this phase's own subject wearing the fix's clothes.**

**6. Two gates went red on this phase's own prose** (07-05). The escaping test scans every
interpolation in the file and *"cannot tell prose from code"*, so a comment quoting the
forbidden form reddened it — the comment now **describes** the shape, *"the check being coarse
in the safe direction"*. M37's killer counts the digits `1800` over the whole file, so the CSS
comment writes it **with a space** (`1 800`). **Both fixed in the prose, never in the gate.**

## WHAT THIS PHASE DID NOT ESTABLISH

1. **None of it is on the wire.** Re-measured 2026-08-17: `MainPID=547119`, started 2026-08-12
   17:28:29, unchanged across the checkpoint and predating 07-01. Its published rows carry none
   of this phase's four keys. It reaches Dan's dashboard at the next `sudo systemctl restart
   boty` — **his action, neither performed nor recommended here.**
2. **Walmart's GO Plus + row publishes an UNKNOWN age indefinitely**, until a store is pinned.
   § 0f stays open on its second answer from Dan and its third deferral by any means.
3. **The live `make verify` classes are recorded and NOT diagnosed.** Two cannot run on this
   host, one is intermittent and manifested on 08-14, one is Phase 5's guard working correctly.
   Each still needs its own plan: polite probing plus fixture re-capture.
4. **No retailer was probed and no fixture re-captured.** Every red-watch in this phase was
   offline **by construction**, and no clock was frozen, injected or monkeypatched anywhere.
5. **`boty check`'s stale form is not reachable in production**, and that is a property of the
   surface rather than a hole — it re-reads every watch, so every `Result` it prints is seconds
   old. Reachable **from a test to the float**, because `_age_tag` is a module-level pure
   function taking `now` and `interval` as required keywords.
6. **`pacer-state.json` is still written non-atomically** with a second reader. The failure
   direction **over-reports** staleness, which is the safe direction, and it self-heals on the
   next check. Priced in `Pacer.save`'s docstring; promotion available if it ever bites.
7. **A latent register defect becomes live the moment a store is pinned:** `storeTag` would
   render remembered Walmart rows as a `store ? · pinned X` **warn** tag — literally true,
   misleading in register. 07-05 closed the `checked === false` half; the pinned-and-remembered
   case is recorded, not fixed.
8. **`.planning/` is covered by no contents gate.** Fourth flagging.
9. **The `keep` half of Dan's answer decided nothing about a future affordance**, because he was
   not asked to and did not choose `note-it`.

## Deviations from Plan

**1. [Recorded, not a rule — Task 1 produced no commit, and could not]**

The plan's `<files>` for Task 1 is `(no files modified)` and its `<done>` requires
`git status --porcelain` clean. Both held. The orchestrator's brief said "execute Task 1 fully
and commit it"; committing anything would have breached Task 3's changed-file allow-list, which
this plan's own `<verify>` asserts. **Recorded rather than papered over with an empty commit.**

**2. [Rule 3 — the live `make verify` was NOT re-run after the three-day checkpoint]**

- **Found during:** Task 3, reconciling the date discipline against the politeness constraint.
- **Issue:** the plan budgets exactly **one** live pass and forbids re-running until green. The
  checkpoint then held the plan open for three days, so the 08-14 verdict is not a statement
  about 08-17.
- **Fix, honouring both:** the verdict is **labelled a 2026-08-14 observation** everywhere it
  appears, with an explicit sentence saying it was not repeated and why. Attaching a fresher
  date by spending a second pass against six retailers was judged a real cost for a cosmetic
  gain.

**3. [Recorded, not a rule — the "third deferral" figure in the plan is off by one reading]**

- **Found during:** Task 1.
- **Issue:** `07-06-PLAN.md`, 07-04-SUMMARY and 07-05-SUMMARY all call a `defer` here *the
  third*. Measured: § 0f was created 2026-08-10 and has been put to Dan **twice**.
- **Fix:** **both** readings recorded — second time Dan has answered it himself, third time it
  has been deferred by any means (counting the 2026-08-11 milestone-close acknowledgement, which
  carried no answer from him). **Recorded rather than resolved silently**, per the plan's own
  rule that a disagreement with a SUMMARY is recorded rather than reconciled.

**4. [Recorded, not a rule — `gsd-tools state` was not invoked at all]**

- **Issue:** the plan's `<output>` says to *expect* `state advance-plan` to misfire and correct
  it by hand. STATE.md's own frontmatter says *"It is not worth invoking again here."*
- **Fix:** the tool was **not invoked**. The `cp` was still taken, and every delta was written by
  hand. **So the misfire count stands at THIRTEEN rather than fourteen**, and the frontmatter
  records why the fourteenth entry is a non-invocation rather than a restoration.

**Total deviations:** 4. **Impact on scope:** none. No package was installed, no code was
written, no clock was touched, and no live retailer read was made after 2026-08-14.

## Scope fence, honoured

`git diff --name-only` over this plan's commit touches exactly the five files in
`files_modified` plus this SUMMARY — asserted against an explicit allow-list that **exits
non-zero naming any stray path**. **`boty/`, `tests/`, `scripts/`, `config/`, `served/`,
`.github/`, `pyproject.toml`, `README.md`, `CHANGELOG.md` and `Makefile` are untouched, and
`.planning/milestones/` is byte-identical.** `07-CONTEXT.md`, `07-PATTERNS.md` and
`07-PLAN-OUTLINE.md` were read and edited nowhere.

`.planning/STATE.md`'s `milestone: v0.3` line is **byte-identical** to its pre-edit copy, and
`tests/test_packaging_metadata.py` was re-run **green** after the edit.
`scripts/evidence_check.py`'s vocabulary was respected — no bare verdict-shaped line was written
into the new section — and `tests/test_evidence_check.py` is green after it.

`identity_check.py --all` → **PASS — 220 file(s), no host identity found**, at the checkpoint and
again before the commit.

**REQ-21 is marked complete here**, by the plan that measured what landed rather than by any
plan that shipped code — the rule 07-01 through 07-05 each deferred to.

## Next Phase Readiness

**Phase 7 is closed and v0.3 has one phase in it.** No milestone close, no tag, no version roll:
`pyproject.toml` stays at `0.3.0` and STATE.md's `milestone: v0.3` is unchanged. `git tag -l`
remains 0.

Open, and each flagged rather than closed: `QUESTIONS.md` § 0e and § 0f; the three live
`make verify` classes; `pacer-state.json`'s non-atomic write; the latent `storeTag` register
defect that becomes live on a pin; and the absence of any contents gate over `.planning/`.

**The most useful thing anyone can do to this project right now is still `sudo systemctl restart
boty`** — and it is now doing four things rather than three.

## Self-Check: PASSED

Every claim above re-measured against the tree after this SUMMARY was written.

- **All five modified files present**, plus this SUMMARY. `git status --short` clean, no
  untracked files.
- **The commit resolves**, and `git diff --diff-filter=D HEAD~1 HEAD` names **no deleted file** —
  all 18 deleted *lines* are the intended replacements (two checkboxes, the `Plans:` line,
  seven frontmatter lines, the superseded live-`make verify` line which is **kept below its
  replacement rather than discarded**, and § 0f's old heading).
- **`make verify-offline` exits 0 AFTER the record was written** — `identity check: PASS — 220
  file(s)`, `865 passed in 10.82s`, mypy clean over 18 source files, `33/33`, survivors 0. **The
  closing record did not redden the tree it certifies.** (Post-commit the tracked count is
  **221**, because this SUMMARY is now tracked; the record's `220` is what the gate read when it
  ran, and is dated accordingly.)
- `tests/test_packaging_metadata.py` + `tests/test_evidence_check.py` → **115 passed**, run after
  the STATE.md and evidence-doc edits.
- **`milestone: v0.3` is byte-identical** to the pre-edit copy — verified by diffing the
  `^milestone` lines against the `cp` taken before any edit.
- **34 criterion bodies in `ROADMAP.md` at baseline, 34 now**, none removed and none added.
  **REQ-21's body byte-identical** after normalisation. Both asserted by command.
- **Changed-file set inside the allow-list**, asserted; no stray path.
- **Registry asserted** `M1`-`M20` ∪ `M25`-`M37` at **33**; the closing record states `26`, `33`,
  `M21`, `M24`, `M31` and `M37`.
- `.planning/ROADMAP.md` mentions `07-06` twice; `docs/retailer-evidence.md` carries exactly one
  `## Phase 7 closing record`; `keep defer` appears in STATE.md (4), QUESTIONS.md (1) and the
  closing record (1).
- **`QUESTIONS.md` § 0e is byte-identical** — 23 005 chars, compared section-to-section against
  `HEAD~1`, not eyeballed.
- **`identity_check.py --all` → PASS**, no host identity found, before the commit and again
  after.
- **This SUMMARY is NOT the fifth leaked-markup instance:** scanned with the same runtime-built
  pattern the sweep used — **0 matches**.

---
*Phase: 07-a-reading-has-an-age*
*Completed: 2026-08-17*
