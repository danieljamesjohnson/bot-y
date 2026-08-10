---
phase: 05-a-reading-means-something
plan: 03
subsystem: pacing
tags: [backoff, persistence, req-16, paging-memory, mutation-testing, restart]

# Dependency graph
requires:
  - phase: 05-a-reading-means-something
    plan: 01
    provides: "the store on every Result — untouched here, but it is what makes a Walmart control's health arm meaningful across the restart"
  - phase: 05-a-reading-means-something
    plan: 02
    provides: "the four assess_health arms and monitor.CAUSE_UNKNOWN; the refusal arm is the one every restart test below asserts on"
  - phase: 03.1-hard-two-and-honest-records
    provides: "Result.refused / fetch.is_refusal — the flag the backoff and the paging decision both branch on"
provides:
  - "Pacer.load / Pacer.save — the backoff depth and the paging memory in one document, defensively parsed"
  - "STATE_VERSION, STATE_MAX_AGE_SECONDS (derived from MAX_BACKOFF_SECONDS), MAX_PERSISTED_REFUSALS (measured)"
  - "_RetailerState.refused_at — wall clock, written down; the second clock in a file that already had one it could not persist"
  - "Config.pacer_state_path, documented in config/products.yaml and gitignored"
  - "watch_cycle's episode rule: a retailer the pacer SKIPPED keeps its paging memory"
  - "mutations M11-M14 — one per independent half of the persistence, none of which moves a verdict"
  - "five restart tests plus a permanent negative control that deletes the state file and asserts two pushes"
affects: [05-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "a reversed position is quoted, dated and answered IN PLACE, and the objection the withdrawn text raised is answered rather than ignored"
    - "an untrusted document is isinstance-guarded at every step and its bounds are checked on BOTH sides, because a stamp in the future is a clock that jumped backwards"
    - "a numeric bound read out of a file carries its MEASURED failure point in the comment, not a round number"
    - "a persistence test builds a BRAND-NEW object over the same path rather than reloading into the writer, or it passes for a load that does nothing"
    - "a corrupt-input table asserts on the method AFTER the parse as well as the parse, because the realistic crash sits one method along"
    - "a positive gate gets a permanent negative control in the suite rather than a transcript, because a control that lives in the suite cannot decay"

key-files:
  created: []
  modified:
    - boty/pacing.py
    - boty/cli.py
    - boty/config.py
    - config/products.yaml
    - .gitignore
    - scripts/mutation_check.py
    - tests/test_pacing.py
    - tests/test_cli_watch.py
    - tests/test_config.py

key-decisions:
  - "due_at is neither written nor read: it is measured against a synthetic clock that restarts at 0.0, so a persisted one either fires immediately or blocks a retailer for the age of the previous process"
  - "Not persisting due_at is also the ANSWER to the withdrawn docstring's objection, not a limitation — a restart still tries once at full rate, exactly as the withdrawn paragraph wanted"
  - "STATE_MAX_AGE_SECONDS is derived from MAX_BACKOFF_SECONDS rather than re-chosen, so the two cannot drift"
  - "MAX_PERSISTED_REFUSALS = 64, chosen from a measured OverflowError at 2.0 ** 1024, not from a preference"
  - "warned is passed THROUGH Pacer and never held: one document, one write, one load, because restoring refusals without it restores half a decision"
  - "The age bound is checked on both sides — a stamp in the future is a clock that jumped backwards and would otherwise hold state forever"
  - "watch_cycle now carries the paging memory of a retailer the pacer skipped, because 'not checked' is not 'recovered' (see Deviation 1)"
  - "The .gitignore rule skips inside the mutation sandbox on test_identity_check.py's needs_repo precedent, rather than widening SANDBOX_CONTENTS"

patterns-established:
  - "A gate that a plan's own headline test depends on is watched red BY the headline test: the carry-forward fix was measured, then observed red, then fixed, then mutated"

requirements-completed: [REQ-16]

# Metrics
duration: 27min
completed: 2026-08-10
---

# Phase 5 Plan 03: The Backoff Outlives The Process Summary

**`refusals` and the paging memory are now one gitignored document that a restart
reads back — proven by four new mutations (10/10 → 14/14) and a restart test with
a permanent negative control — and along the way the measurement showed that
"pushed once" was already broken *within* a single process, because a cycle the
backoff skipped was being read as the retailer recovering.**

## Performance

- **Duration:** 27 min
- **Started:** 2026-08-10T16:23Z
- **Completed:** 2026-08-10T16:50Z
- **Tasks:** 3 (5 commits — both TDD tasks RED then GREEN)
- **Files modified:** 9

## Accomplishments

- **A refusal count survives the process.** Five refusals, `save()`, a
  **brand-new** `Pacer` over the same path, and the next refusal produces the
  wait for the sixth — asserted as `300 * 2**6`, not as "it is bigger".
- **`due_at` is in neither `load` nor `save`.** Not a simplification: it is the
  answer to the objection the withdrawn docstring paragraph raised, because a
  restart still tries once at full rate.
- **"Pushed once" now means once** — across a restart *and* within one process.
  The second half was not in the plan and is the finding of this wave; see
  Deviation 1.
- **A corrupt, empty, absent, wrong-typed, clock-skewed or hostile state file
  produces a running monitor.** 19 malformed shapes are driven through `load`
  under `parametrize`, plus a directory and a missing file — 21 in all — and each
  asserts on both halves: nothing raised from `load`, and nothing raised from the
  `record()` that follows it.
- `make verify-offline` exits **0** with **642 passed** (was 595) and **14/14
  mutations** (was 10/10).

## Task Commits

1. **Task 1 (RED): the persistence behaviours, watched red** — `665f0a4` (test)
2. **Task 1 (GREEN): the backoff becomes a fact on disk** — `46a0768` (feat)
3. **Task 2 (RED): REQ-16's clauses across a restart, watched red** — `f90f39b` (test)
4. **Task 2 (GREEN): wired into the loop, and "once" made to mean once** — `ad05c7e` (feat)
5. **Task 3: M11-M14, all four observed CAUGHT** — `93c62c7` (test)

No refactor commit: neither green step left anything to clean up.

## Red-watch 1 — the four mutations, verbatim

Previous count recorded beside the new one so the rise is **shown** rather than
claimed: **10/10** (`05-02-SUMMARY.md`). Now **14/14**:

```
mutation check: 14 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (641 passed, 1 skipped in 10.11s)
  CAUGHT    M11 boty/pacing.py: 7 test(s) failed — test_a_refusal_the_backoff_is_handling_is_recorded_not_pushed_across_a_restart, test_a_refusal_past_the_cap_is_pushed_once_not_once_per_process, test_the_backoff_comes_back_deep_rather_than_shallow (+4 more)
  CAUGHT    M12 boty/pacing.py: 2 test(s) failed — test_state_older_than_the_backoff_cap_is_discarded, test_a_stamp_in_the_future_is_discarded
  CAUGHT    M13 boty/pacing.py: 2 test(s) failed — test_a_refusal_past_the_cap_is_pushed_once_not_once_per_process, test_the_paging_memory_round_trips
  CAUGHT    M14 boty/cli.py: 2 test(s) failed — test_a_refusal_past_the_cap_is_pushed_once_within_one_process_too, test_a_refusal_past_the_cap_is_pushed_once_not_once_per_process
mutation check: 14/14 mutations caught
```

| Ident | What it breaks | What ships if it survives |
|---|---|---|
| M11 | the restore — `st.refusals = 0` on load | every restart climbs the backoff again from 2x against a retailer that has already walled us |
| M12 | the age-out — restore regardless of the stamp | a file written before a week of downtime pins a retailer at the cap on startup |
| M13 | the paging memory crossing the **process** | REQ-16's headline clause reverts to "once per process" while the backoff keeps working perfectly |
| M14 | the paging memory surviving a paced-out **cycle** | a refusal past the cap is re-paged at every subsequent check — one notification every six hours, forever |

**Not one of the four moves an availability, a price or an alert verdict.** That
is why they exist: a verdict-only suite passes every one of them straight
through. `SANDBOX_CONTENTS` and `_IGNORE` are **unchanged** — `git diff` on
`scripts/mutation_check.py` is 56 insertions and zero deletions.

Every `search` was copied out of the file after Tasks 1 and 2 had landed, and
none contains a fragment of a docstring, a comment or a log-message format
string. Each anchors on the statement that does the work: the assignment applying
the restored count, the comparison bounding the age, the expression producing the
restored memory, the union that carries it forward.

## Red-watch 2 — the permanent negative control, both assertions quoted

This pair is the phase's proof for criterion 6, so it is quoted rather than
paraphrased. Both live in `tests/test_cli_watch.py`; the second does not decay,
because it is watched red *by construction, permanently*.

**One push across two processes** —
`test_a_refusal_past_the_cap_is_pushed_once_not_once_per_process`:

```python
    _run(restart_cfg, cycles=40)
    assert _refusals(restart_cfg) >= cli.REFUSALS_BEFORE_PAGING, "process 1 passed the cap"
    assert sent["health"] == [["gamestop"]], "process 1 pages exactly once"

    _run(restart_cfg, cycles=40)

    assert sent["health"] == [["gamestop"]], (
        "the retailer was paged again after the restart. REQ-16 says a refusal "
        "that outlasts the cap is pushed ONCE, and this is how that quietly "
        "became once per process"
    )
```

**Two pushes with the file deleted** —
`test_the_same_scenario_pushes_twice_when_the_state_file_is_deleted`:

```python
    _run(restart_cfg, cycles=40)
    assert sent["health"] == [["gamestop"]]

    restart_cfg.pacer_state_path.unlink()
    _run(restart_cfg, cycles=40)

    assert sent["health"] == [["gamestop"], ["gamestop"]], (
        "deleting the state file changed nothing, so the single push in the "
        "test above was not evidence of persistence"
    )
```

**The cycle counts are measured, not guessed.** Over 300 seeds of the loop's
`uniform(0.85, 1.15)` jitter: 10 cycles yields exactly 3 refusals, the fifth
refusal lands at cycle 30-32, and the sixth at 61-65. The resulting count is then
asserted **off the file** in every test rather than assumed.

**The control watch was checked before the assertions were written**, and it was
load-bearing exactly as the plan warned: `cfg`'s single watch is not a control,
so `assess_health` would have reported gamestop unhealthy for *no control watch
configured*, `Health.refused` would never have been set, and every assertion
above would have been testing the wrong arm. The restart tests use their own
`restart_cfg` fixture whose one watch is `control=True`.

## Red-watch 3 — the malformed-document table

21 shapes: 19 documents under `pytest.mark.parametrize` (ids naming each shape,
so a failure says *which* one broke), plus a `state_path` that is a directory and
a `state_path` that does not exist. Each asserts **both** halves of T-05-04:

```python
    p = _pacer(path)
    warned = p.load()  # must not raise

    assert warned == set(), f"{description}: restored a paging memory out of a broken file"
    assert p._for("a").refusals == 0, f"{description}: restored a count out of a broken file"
    p.record("a", refused=True, now=0.0)  # must not raise either
    p.record("a", refused=False, now=0.0)
```

The second half is the one that covers T-05-12: the realistic crash sits one
method along, in `record`, where a restored count reaches `BACKOFF_FACTOR **
refusals`. A table that only exercised `load` would pass while the monitor still
exited 1 on every cycle.

The shapes: not JSON at all; an empty file; a JSON list; a JSON string; a JSON
number; JSON null; `retailers` not a mapping; an entry not a mapping; `refusals`
a string, negative, `true` (a `bool` is an `int` subclass), and 1e9 with
`refused_at` absent; `refused_at` a string and null; `warned` a bare string, a
list of ints, and a number; an unrecognised `version`; no `version` at all; a
directory; a missing file.

## The measured overflow point

The plan asked for the bound's comment to carry a measurement rather than a round
number. Measured 2026-08-10 on this interpreter (**CPython 3.12.3**):

```
2.0**1023 = 8.98846567431158e+307  isfinite: True
2.0**1024 raises OverflowError: (34, 'Numerical result out of range')
300*2.0**1023 = inf
min(300*2.0**1023, 21600) = 21600
```

**The plan's own figure was slightly wrong and the code carries the corrected
one.** The plan states that `2.0 ** 1023` "returns `inf`"; it returns
8.99e307, which is finite. It is the *multiplication that follows* which
overflows to `inf` — and `min()` then clamps it to the cap harmlessly. The
conclusion is unchanged and in fact sharper: the failure is a **cliff at the
exponent**, not a slope, and the multiply never raises. `MAX_PERSISTED_REFUSALS =
64` — far below the crash point, far above where the cap binds (7 refusals at the
default 300 s interval), so the clamp costs nothing operationally. Asserted
`>= cli.REFUSALS_BEFORE_PAGING` by a test that imports both modules, because
`pacing` must not import `cli`.

## The withdrawn paragraph and its replacement, both quoted in full

This phase is about a system that stated things it had not established. A plan
that reverses a written position and does not record both sides in its own
summary would be repeating the defect in the record.

**Withdrawn** (`boty/pacing.py`, until 2026-08-10):

> Deliberately in-memory. A restart clears the backoff and tries once at full
> rate, which is the right trade: the alternative is a persisted penalty
> outliving the condition that caused it, and one extra request per restart is
> cheaper to reason about than a stale file.

**Its replacement**, in place, under the heading *IT IS PERSISTED NOW, AND THIS
FILE USED TO ARGUE THE OPPOSITE* — which quotes the paragraph above in full
before answering it:

> Two measured facts overruled it.
>
> 1. `boty.service` is a systemd unit with `Restart=` semantics, so a restart is
>    not a rare event — it is what a supervisor does whenever anything goes
>    wrong. "One extra request per restart" is the cost of a restart you can
>    count; against a flapping service it is a retailer that walled us being
>    asked at FULL rate indefinitely, which is exactly the behaviour the
>    politeness constraint calls a hard limit.
> 2. REQ-16 says a refusal that outlasts the cap is pushed ONCE. The counter that
>    defines "the cap" is `refusals`, and `cli._refusal_is_entrenched` reads it
>    and nothing else. If it resets, "once" silently becomes "once per process" —
>    and the page-once bookkeeping hanging off it resets with it, so a restart
>    re-pages a retailer somebody has already been told about. That is the
>    20-pages-in-24-hours failure this module exists to prevent, rebuilt from the
>    other end.
>
> THE STALE-FILE OBJECTION IS ANSWERED, NOT DROPPED. The withdrawn paragraph's
> objection was a persisted penalty outliving the condition that caused it, and
> it gets two answers — the second of which is the stronger:
>
> (a) Every record carries a wall-clock stamp and is discarded past
>     `STATE_MAX_AGE_SECONDS`, so a file written before a machine was off for a
>     week is ignored rather than applied; and a retailer at zero refusals is
>     never written at all, so the document self-cleans.
> (b) `due_at` IS STILL NOT PERSISTED, which keeps the withdrawn paragraph's own
>     concession intact. A restart still tries once, immediately, at full rate,
>     so the condition is re-tested at once. What is inherited is only the DEPTH
>     the penalty resumes at IF that one request is refused again, plus whether
>     a human has already been told. The withdrawn paragraph was right about the
>     request and wrong about the memory.
>
> SO: `refusals` and the wall-clock time it was last incremented are written,
> along with the caller's paging memory. `due_at` never is. `cli.watch_loop`
> drives this class with a synthetic clock (`scheduled_now`) that starts at 0.0
> in every process, so a persisted `due_at` would be a number with no referent:
> compared against a fresh 0.0 it either fires immediately or blocks a retailer
> for the entire age of the previous process. Neither is a schedule; both are an
> accident.

## The persisted document's exact shape

One real example, so 05-04 can recognise the file on the daemon's disk after the
restart without reading the code — six refusals against Walmart, already paged
about, and an Amazon that answered and therefore does not appear at all:

```json
{
  "retailers": {
    "walmart": {
      "refusals": 6,
      "refused_at": 1786380353.7236485
    }
  },
  "version": 1,
  "warned": [
    "walmart"
  ]
}
```

`sort_keys=True`, `indent=2` on `State.save`'s precedent. `warned` is a sorted
list because a set is not JSON and an unsorted one makes every write a spurious
diff. No `due_at` anywhere.

## What 05-04 must know

**Restarting `boty.service` is now safe with respect to the backoff.** The
standing instruction in STATE.md since 2026-08-04 — *do NOT restart while a
retailer is in backoff* — is **closed by this plan**. A restart now inherits the
refusal depth and the paging memory; what it does not inherit is the next
scheduled attempt, so it will ask each retailer once, immediately, at the normal
rate, and only resume the deep backoff if that one request is refused again. That
single request is deliberate and is the withdrawn docstring's concession, kept.

**Where the file will appear.** `deploy/boty.service` sets
`WorkingDirectory=/home/dan/CodeProjects/pokemongoplusplus` and the shipped
config now carries `pacer_state_path: pacer-state.json`, so the daemon will write
`/home/dan/CodeProjects/pokemongoplusplus/pacer-state.json`. It is gitignored.
**The checkpoint should confirm it appears after the first post-restart refusal**
— and equally, that it does *not* appear before one, because a retailer at zero
refusals is never written. An empty `retailers: {}` document with a `warned: []`
is the normal state of a healthy monitor and is not a fault.

**Both Walmart watches still read UNKNOWN on this host,** exactly as
`05-02-SUMMARY.md` records. Nothing in this plan changes it and nothing here
tried to.

**`make verify` (live) was NOT run**, per the plan's evidence constraint. No
acceptance criterion here depended on a live read; no live retailer request was
made by anything in this plan; no store number appears anywhere.

## `make verify-offline` — verdict verbatim

```
identity check: PASS — 177 file(s), no host identity found
All checks passed!
642 passed in 9.68s
control check: SKIPPED (--offline) — no live retailer request made.
  baseline  unmutated sandbox passes (641 passed, 1 skipped in 10.07s)
mutation check: 14/14 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

Exit **0**. Test count **642**, strictly above 05-02's **595** (+47). Mutations
**14/14**, up from **10/10**. `mypy` clean (18 source files), `ruff check` clean,
`identity_check.py --all` PASS over 177 tracked files. `git status --porcelain`
**empty** after the run — no `pacer-state.json` was left anywhere in the tree.

**The `1 skipped` in the sandbox baseline is deliberate and argued** — see
Deviation 3. It is the `.gitignore` rule, which the sandbox has nothing to say
about. Outside the sandbox that test runs and passes; the repo-root line above
reads `642 passed`, with no skip.

## Deviations from Plan

### 1. [Rule 1 — Bug] `warned` was not the once-per-episode gate the plan took it for, and persisting it alone would not have delivered criterion 6

**Found during:** Task 2, at the moment the wiring was complete and the headline
test went red anyway.

**The plan's non-negotiable #2 states that `warned` is "the once-per-episode gate
and is a `watch_loop` local".** The first half is not true of the tree. `warned`
is recomputed every cycle as `{h.retailer for h in pageable}`, and `health` is
derived from `results` — of which a retailer the pacer skipped has **none**, by
design, because "a synthetic UNKNOWN for a check we chose not to make" is the bug
one level up. So an unchecked retailer produced no health entry, which read as no
longer pageable, which erased the memory.

**Measured, before any fix**, at the end of process 1 for a range of cycle
counts:

```
cycles= 30  pushes=0  persisted warned=[]            refusals=4
cycles= 31  pushes=1  persisted warned=['gamestop']  refusals=5
cycles= 32  pushes=1  persisted warned=[]            refusals=5
cycles= 33  pushes=1  persisted warned=[]            refusals=5
cycles= 35  pushes=1  persisted warned=[]            refusals=5
cycles= 40  pushes=1  persisted warned=[]            refusals=5
```

The memory survived **exactly one cycle** — the cycle it was set on — and the
very next paced-out cycle erased it. Two consequences, and both are inside
REQ-16:

- **Persisting `warned` would have been decorative.** The empty set is what
  reached disk unless the process happened to die on the single cycle that paged.
  The plan's headline test was red for precisely this reason after the wiring
  landed, and its failure output is quoted below.
- **"Pushed once" was already false within one process.** Measured separately:
  **2 pushes in 120 cycles** for one retailer in one process — at refusals 5 and
  6 — climbing to one notification every six hours forever once the cap binds.
  That is the 20-pages-in-24-hours failure at a slower cadence, which is the
  failure `boty/pacing.py` exists to prevent.

**The red, verbatim, with the wiring in and the fix out:**

```
E       AssertionError: the retailer was paged again after the restart. REQ-16 says a refusal that outlasts the cap is pushed ONCE, and this is how that quietly became once per process
E       assert [['gamestop'], ['gamestop']] == [['gamestop']]
E         Left contains one more item: ['gamestop']
```

**Fix** — two lines in `watch_cycle`, with the measurement recorded beside them:

```python
    checked = {r.watch.retailer for r in results}
    still_unhealthy = {h.retailer for h in pageable} | (warned - checked)
```

An episode ends when a retailer is **checked** and found no longer pageable —
never merely because the pacer skipped it, which is a cycle in which we learned
nothing about it. `watch_cycle`'s signature, its rollback semantics on a failed
health send, and every other line of it are unchanged.

**This contradicts the plan's done-criterion** *"`git diff boty/cli.py` shows no
change to `watch_cycle`"*. Recorded rather than buried: the plan is wrong about
the tree here, and shipping the persistence without this would have closed
criterion 6 on a test that only passes when a process dies on one particular
cycle, while leaving criterion 5 false in the ordinary case. `_refusal_is_entrenched`,
`_report`, `_make_checker`, `REFUSALS_BEFORE_PAGING` and `main` **are** unchanged,
and `git diff` proves it — the only hunks in `cli.py` are `watch_cycle`'s
docstring, these two lines, and `watch_loop`.

**Verification:** `test_a_refusal_past_the_cap_is_pushed_once_within_one_process_too`
pins the in-process half at 120 cycles, and **M14** is its permanent red-watch.

### 2. [Deviation] Four mutations, not three

The plan scopes three. M14 is the fourth, and it exists because the fix in
Deviation 1 is a new mitigation on REQ-16's headline clause, and this repo's
standing constraint is that **a gate must be watched going red before it is
trusted** — "a mitigation nothing proves is a control nobody maintains", in the
plan's own words about the age-out. M13 and M14 are the M6/M7 relationship
exactly: M13 dying proves the memory crosses a **process** boundary, M14 dying
proves it survives a paced-out **cycle**. A tree that persisted `warned`
faithfully and dropped the union would write an empty set to disk and pass M13
while shipping the duplicate page intact. The printed total is therefore **four**
above 05-02's, not three.

### 3. [Rule 3 — Blocking] The `.gitignore` test broke the mutation harness, and neither tuple was widened

**Found during:** Task 3, first run — a `HarnessError`, exactly the shape the
plan told the executor to stop and record rather than paper over.

```
E       FileNotFoundError: [Errno 2] No such file or directory: '/tmp/boty-mutation-ji26yphl/.gitignore'
FAILED tests/test_config.py::test_the_default_pacer_state_file_is_gitignored
```

`test_the_default_pacer_state_file_is_gitignored` reads `.gitignore` off disk,
and `.gitignore` is **deliberately not in `SANDBOX_CONTENTS`** —
`scripts/mutation_check.py`'s `_IGNORE` comment considers adding it and rejects
it by name, on the grounds that it would leave a nondeterministic runtime
artifact in a harness whose entire claim is reproducibility and would widen the
paths the contributor-docs citation rule may resolve.

**Neither `SANDBOX_CONTENTS` nor `_IGNORE` was touched.** The test was fixed
instead, on the taxonomy `tests/test_packaging_metadata.py` already sets out for
this exact situation: *return an empty set* is rejected outright (a gate
reporting success where it could not run); *skip* is sound when the rule is about
**this repository's own tracked surface**, which a copy genuinely has nothing to
say about; *give the sandbox the file* is for rules about files the sandbox
carries. This rule is about whether **this repo** ignores a runtime artifact, so
it takes `tests/test_identity_check.py`'s `needs_repo` skip — with the reason
written into the `skipif` message rather than left to be rediscovered. It runs
and passes at the repo root, which is where `make verify-offline` runs it.

### 4. [Measurement] The plan's overflow figure was corrected in the code

Documented in full under *The measured overflow point* above. `2.0 ** 1023`
returns 8.99e307, not `inf`; the overflow to `inf` happens in the multiplication
that follows. The comment on `MAX_PERSISTED_REFUSALS` carries the measurement
that was taken, not the one the plan predicted.

### 5. [Deviation] Three extra tests beyond the plan's four

The plan specifies four restart tests. Five were written, plus the in-process
test from Deviation 1 and a `boty check` test:

- **`test_a_restored_paging_memory_does_not_silence_a_new_breakage`** — the plan
  says to add a test for REQ-16's "pushed immediately" clause "only if a restart
  changes it". It does change it, in the dangerous direction: the restore has to
  be checked for **over-reach**. A `load` that returned every retailer it had
  ever heard of would pass the pushed-once test and silence the alarm this
  project exists to raise. The test pins that a control which stopped reading
  IN_STOCK — not a refusal, so no cap to outlast — still pages on the first cycle
  of the new process.
- **`test_a_refusal_past_the_cap_is_pushed_once_within_one_process_too`** — see
  Deviation 1.
- **`test_boty_check_writes_no_pacer_state_at_all`** — the plan lists this as a
  behaviour; it is pinned rather than assumed, which is only meaningful because
  `_check_config` points the path at `tmp_path` and so can tell "nothing was
  written" from "written somewhere else".

### 6. [Note] `due_at` appears in prose in `load`'s docstring, deliberately

The plan's done-criterion asks that `grep -vn '^\s*#' boty/pacing.py | grep -c
'due_at'` show `due_at` only in `record`, `due` and `skipped_reason`. The same
task also instructs, twice, that the reason `due_at` is not persisted must be
said **in the code**. Those pull against each other, because a docstring is not a
`#` comment. The property the criterion is about holds exactly:

```
151:    due_at: float = 0.0                                     (the field)
207:        return now + self.default_interval * 0.5 >= ...     (due)
240:        st.due_at = now + wait                              (record)
250:        mins = max(0.0, st.due_at - now) / 60                (skipped_reason)
292:        `due_at` is not read, and the module docstring says why...  (load DOCSTRING)
```

**There is no `due_at` statement in `load` or `save`.** The occurrences at 292
and in the module docstring are the explanation the same task demanded. No
mutation anchor touches either.

### 7. [Note] STATE.md and REQUIREMENTS.md were edited after all, and `advance-plan` misfired a third time

The plan says *"No ROADMAP, REQUIREMENTS or STATE edits. 05-04 closes the
phase."* The orchestrator's own instruction for this run says the opposite —
*"You own STATE.md and ROADMAP.md updates for this plan"* and *"REQ-16 (this plan
closes it)"*. Resolved by separating bookkeeping from closure: the per-plan
bookkeeping was written (plan counter, progress, metric, two decisions, REQ-16
ticked), and **no ROADMAP criterion verdict was recorded** — criteria 5 and 6
have their evidence here, and writing the verdicts with the live evidence remains
05-04's.

`gsd-tools state advance-plan` again wrote `status: Phase complete — ready for
verification` at 3 of 4 plans, and this time also overwrote `stopped_at` with
Phase 4's stale `"Completed 04-06-PLAN.md — Phase 4 closed"`. Both corrected by
hand, and STATE.md's existing note about the same misfire after 05-01 and 05-02
was extended to record the third. The cause is unchanged and is documented there:
the tool reads a `Plan: 6 of 6 complete` line in the archived v1.0.0 block, which
is kept verbatim and so cannot be edited to fix it.

**One STATE.md entry was deliberately NOT struck.** The standing *"do NOT restart
while a retailer is in backoff"* warning still binds, because it is about the
**running process**, which has no persistence — the fix is in the tree, not in
the daemon, until 05-04 deploys it. The entry now says exactly that, and says to
strike it once the service has been restarted onto this tree.

---

**Total deviations:** 1 bug auto-fixed (Rule 1), 1 blocking auto-fixed (Rule 3),
5 recorded scope/measurement notes. **Impact on scope:** nothing was dropped,
simplified or deferred, and no guard was weakened to keep a test green. The plan
gained one two-line fix in a function it said not to touch, and that fix is the
difference between criterion 5 being true and being true only on the cycle a
process happens to die on.

## Issues Encountered

**The plan's `warned` premise was the only real obstacle**, and it was caught by
the plan's own headline test going red after the wiring landed — which is what
the red-watch discipline is for. It is documented as Deviation 1 rather than as
an issue, because it is now fixed, tested and mutated.

**No `SANDBOX_CONTENTS` / `_IGNORE` disagreement remains.** The harness's one
complaint was self-inflicted by a test written in this plan, and was resolved by
fixing the test on an existing precedent rather than by widening either tuple —
see Deviation 3.

## Files Created/Modified

- `boty/pacing.py` — the reversal argued in place; `STATE_VERSION`,
  `STATE_MAX_AGE_SECONDS` (derived) and `MAX_PERSISTED_REFUSALS` (measured);
  `_RetailerState.refused_at` with the two-clock distinction stated;
  `state_path` declared last with a default; `load`/`save` with the
  `warned`-is-a-pass-through argument in the section comment
- `boty/cli.py` — `watch_loop` builds one pacer with `state_path=`, restores
  `warned` from it, and saves once per cycle from a `finally`; the "one pacer for
  the life of the loop" comment **extended, not replaced**; `watch_cycle`'s
  episode rule corrected (Deviation 1)
- `boty/config.py` — `pacer_state_path` beside its two neighbours, with the
  naming decision and the rejected `state.json` alternative recorded
- `config/products.yaml` — the documented key, in the register of the
  `state_path` and `retailer_intervals` blocks
- `.gitignore` — one line beside `state.json`, with why it inherits nothing
- `scripts/mutation_check.py` — M11-M14 and the argument for four rather than one
- `tests/test_pacing.py` — docstring item 3, plus a new persistence section: 25
  tests including the 19-shape hostile table
- `tests/test_cli_watch.py` — the `cfg` fixture and `_check_config` pointed at
  `tmp_path` with the reason recorded; the `restart_cfg` control fixture; six
  restart/paging tests
- `tests/test_config.py` — the default, the override, the three-separate-files
  assertion, and the gitignore rule

## Decisions Made

See `key-decisions` in the frontmatter. The three 05-04 will reach for:

1. **A restart costs exactly one request at full rate, per retailer, and that is
   by design.** It is the withdrawn docstring's concession, kept on purpose. Do
   not "fix" it by persisting `due_at`.
2. **An empty `pacer-state.json` is healthy, not broken.** Retailers at zero
   refusals are never written, so a monitor with nothing in backoff produces
   `{"retailers": {}, "version": 1, "warned": []}`.
3. **Deleting the file is safe** and costs one repeated notification plus one
   shallow backoff. It is also what the negative-control test does, permanently,
   to keep the positive one honest.

## Next Phase Readiness

05-04 has what it needs:

- The restart it owns is **safe with respect to the backoff**, which is the
  reason it was sequenced after this plan.
- `make verify-offline` is green at 642/14-14, so any red 05-04 sees is its own
  or is live.
- `boty/models.py`, `boty/retailers.py`, `boty/monitor.py`, `boty/notify.py`,
  `boty/parse.py`, `boty/status.py`, `served/boty/index.html` and
  `tests/test_alert_text.py` are **untouched by this plan** — `git diff --stat
  eb7c54e..HEAD --` for all eight is empty.
- No ROADMAP criterion verdict has been written. Criteria 5 and 6 have their
  evidence here; recording the verdicts, and the live `make verify` outcome, is
  05-04's.

Two pre-existing items remain open and neither is this plan's: the live `make
verify` failure since 2026-08-06, and `QUESTIONS.md` § 0e.

---
*Phase: 05-a-reading-means-something*
*Completed: 2026-08-10*

## Self-Check: PASSED

Every file named above exists on disk; all five task commits resolve in
`git log`. Load-bearing claims re-verified mechanically after writing this
summary rather than asserted from memory:

- **`due_at` is in neither `load` nor `save`** — checked by parsing
  `boty/pacing.py` with `ast`, stripping each method's docstring node, and
  searching the unparsed remainder: `load` False, `save` False. This is the
  check the plan's `grep` was reaching for, and unlike the `grep` it is not
  confused by the docstrings the same task required (Deviation 6).
- **`M11`-`M14` are all present** in `MUTATIONS` (4 matches), and **no `ident`
  is duplicated** (`uniq -d` returns 0 lines) — the failure that would make the
  printed total a lie.
- **`SANDBOX_CONTENTS` and `_IGNORE` are unchanged**: `git diff
  eb7c54e..HEAD -- scripts/mutation_check.py` contains **zero** deletion lines.
- **The eight forbidden files are untouched**: `git diff --stat eb7c54e..HEAD`
  for `boty/models.py`, `boty/retailers.py`, `boty/monitor.py`,
  `boty/notify.py`, `boty/parse.py`, `boty/status.py`,
  `served/boty/index.html` and `tests/test_alert_text.py` is empty.
- **`make verify-offline` exits 0** at 642 passed / 14-14 mutations, and
  `git status --porcelain` is empty after the run — no runtime artifact left
  behind.
