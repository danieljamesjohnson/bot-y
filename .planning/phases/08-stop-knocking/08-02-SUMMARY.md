---
phase: 08-stop-knocking
plan: 02
subsystem: pacing
tags: [pacing, backoff, cooloff, req-22, mutation-anchors, dated-reversal]

requires:
  - phase: 08-stop-knocking
    provides: "08-01's before-number (125) and the five collisions settled in 08-DECISIONS.md"
  - phase: 07-one-cadence
    provides: "`Pacer.current_interval` as the single expression behind both the fetch schedule and the published `current_interval_seconds`"
provides:
  - "REQ-22 criteria 1, 2, 3-after and 4: a retailer past 30 consecutive refusals waits three days rather than six hours, and the days-scale number reaches the schedule and the page as one expression"
  - "The `after` half of criterion 3: 37 requests over 30 simulated days, measured, beside 08-01's 125"
  - "One test carrying BOTH of criterion 3's numbers — the before withdrawn into a dated record, the after asserted live"
  - "M33 and M38 re-anchored with kill sets re-measured rather than carried over"
  - "A live gate on MAX_PERSISTED_REFUSALS > REFUSALS_BEFORE_COOLOFF, replacing a relationship whose subject was deleted 2026-08-12"
affects: [08-03, 08-04]

actuals:
  tokens: 14455
  tasks: 4
  commits: 2

tech-stack:
  added: []
  patterns:
    - "A flat literal wait reached through a conditional expression, so the exponential branch is not merely clamped past the threshold but unevaluated"
    - "A superseded test repaired in the plan that breaks it, never in a later wave — repairing another plan's red downstream launders it"
    - "A deliberately red boundary BETWEEN two tasks that share one commit, so no red state is ever committed"

key-files:
  created: []
  modified:
    - boty/pacing.py
    - tests/test_pacing.py
    - tests/test_cli_watch.py
    - scripts/mutation_check.py

key-decisions:
  - "REFUSALS_BEFORE_COOLOFF = 30, chosen because it makes the superseded cap test BIND rather than survive; 31 or more would leave the sentence REQ-22 overrules standing, unremarked, at the exact boundary criterion 1 is about"
  - "COOLOFF_SECONDS = 3 * 24 * 60 * 60, a literal and never a derivation; three days rests on the staleness-window argument alone and not on the request-count curve"
  - "The cool-off branch goes INSIDE current_interval's single max(), knowingly costing two mutation anchors, rather than in a guard clause that would create a second copy of the widen-only rule"
  - "MAX_BACKOFF_SECONDS' VALUE is untouched at six hours; what is replaced is that ceiling being applied indefinitely"
  - "M38's replace strips only the outer max and carries the cool-off arm through verbatim, so its meaning is unchanged rather than blurred into M33's"
  - "The outline's lower bound on the threshold is not restored: it cites cli.REFUSALS_BEFORE_PAGING, deleted 2026-08-12. The replacement argument is marked as an argument, not a measurement"

requirements-completed: []

status: complete
---

# Phase 8 Plan 02: Stop Knocking — The Rule Changes

Past 30 consecutive refusals a retailer stops being asked every six hours and is left alone for
three days, then probed once — and the days-scale number reaches `record`'s schedule and the
dashboard's `current_interval_seconds` as **one expression**, because the branch sits inside
`current_interval`'s single `max(...)` rather than beside it.

**Criteria covered:** C1, C2, C3-after, C4. **Not claimed:** C5 (`08-03`) and C6 (`08-04`).

---

## Criterion 3: both numbers, side by side

| Rule | 30-day requests to a retailer that never recovers | Status |
|---|---|---|
| Fixed 6-hour ceiling, applied indefinitely | **125** | measured 2026-08-27 by `08-01`, against unmodified `boty/pacing.py` at `85a8d9f`, with `.venv/bin/python -m pytest tests/test_pacing.py -q` |
| Threshold 30, cool-off 3 days | **37** | measured 2026-08-28, this branch, same 8640-cycle window, same retailer, same 300 s cadence, same counting idiom |

**Reduction: 37/125 — a factor of 3.38, or 70.4% fewer requests.** Strictly smaller, which is the
word criterion 3 uses and which the test asserts directly against the literal 125.

**The measured after-number is 37, which happens to equal the plan writer's projection of 37.**
That is a coincidence worth naming rather than a validation: the projection was computed against a
re-implementation of the scheduling arithmetic in a scratch script, and this number came out of the
real `Pacer` via a failing assertion. They agree; they were not the same measurement, and the run
would have won if they had differed.

**Zero restarts assumed, and each restart costs exactly one extra request.** `due_at` is
deliberately never persisted, so a restart re-tests the condition at once at full rate; what a
restart inherits is the DEPTH the penalty resumes at, never the position on the schedule. Under a
systemd unit with `Restart=` semantics that is not a rare event, so the honest form of both numbers
is *"N requests over 30 days, plus one per restart"*. Both are floors on real-world requests, not
predictions of them.

**The before-number is now a dated record rather than a re-runnable assertion.** `08-01`'s
`test_the_current_rule_asks_a_never_recovering_retailer_this_many_times_in_thirty_days` was
withdrawn in place and renamed to
`test_the_thirty_day_request_count_under_the_cooloff_is_a_stated_number`, so **one** test carries
both numbers: 125 quoted in its docstring with its date, its command and its revision, and 37
asserted live. Criterion 3 asks for both numbers *recorded*, not both re-runnable. Freezing a
hand-written reproduction of the old arithmetic to keep 125 re-runnable was rejected — it would be
a second copy of a number, and the copy would be of a rule that no longer exists, so nothing could
ever check it again.

### The after-number is a measurement, not a gate

Stated in those words because it matters. Like `08-01`'s baseline it **cannot be made to fail**: its
subject is the code as it stands rather than a defect, so writing a deliberately wrong literal and
watching `assert ==` reject it would prove that `assert ==` works and nothing else. That is a
finding, not a skipped formality.

What carries the weight instead is the same three things `08-01` named: the **denominator
assertion** (`now == 2592000.0`, watched red by `08-01` on 2026-08-28 by running the loop one cycle
short — the count assertion still read 125 over the shortened window and passed, so a window that
quietly shrank would have been invisible to the count alone), the **two independent tallies**
(`refusals == len(offsets)`, and offsets strictly increasing inside the window), and the fact that
the literal was **transcribed from a run** — it arrived as the "actual" side of a failure message
the moment the branch landed.

`_THIRTY_DAYS_OF_CYCLES = 8640` did not move, so the two counts remain comparable. That was the one
unforgivable move available in this step and it was not made.

---

## Every gate watched red first, with the counts and the values

Recorded at the moment each run printed them.

| # | Gate | Red run | Observed | Expected |
|---|---|---|---|---|
| 0 | Constants alone (step 1) | **76 passed, 0 failed** — unchanged | — | — |
| 1 | Tracer, `tests/test_cli_watch.py` | **1 failed, 44 passed** | published `21600` | `259200.0` |
| 2 | Boundary table, N=30 and N=31, both intervals | **6 failed, 78 passed** (4 of these) | `21600` | `259200.0` |
| 3 | Single-probe simulation | (same run) | **13 probes** over 1000 cycles | `1` |
| 4 | Recovery at depth, setup assertion | (same run) | `21600` | `259200.0` |
| 5 | `skipped_reason` cool-off arm | **1 failed, 84 passed** | `'backing off after 30 refusal(s) — next attempt in ~4320 min'` | prose naming the cool-off, wait in days |
| 6 | Clamp above threshold (new, see Deviations) | **1 failed** | `assert 64 > 100` | true |

**Step 1's zero is a measurement too, and it is what makes the rest attributable.** Two
unreferenced module-level constants are not a behaviour change, so the reds at steps 1-4 belong to
the branch and to nothing else.

**The boundary table's N=29 rows were GREEN at both standing intervals throughout** — 21600.0,
unchanged from before this phase. That is the half of criterion 1 that proves the threshold binds
**at** the step rather than somewhere near it.

### The three expected reds the branch opened, and what each actually saw

`.venv/bin/python -m pytest tests/test_pacing.py tests/test_cli_watch.py -q` →
**3 failed, 126 passed.** The failing set was **exactly** the three named, with no fourth:

| Collision | Test | Observed | Expected | At depth |
|---|---|---|---|---|
| A | `test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring` | **259200.0** | **21600** | **30 refusals** |
| D | `test_the_persisted_count_is_clamped` | **259200.0** | **21600** | **65 refusals** (64 restored by the clamp + 1 recorded) |
| C | `08-01`'s baseline | **37** | 125 | ~37 consecutive refusals over 8640 cycles |

**Collisions A and D are this phase's only DIRECT observation that the threshold binds at exactly
30, and they observe it from opposite sides of the clamp** — A from a live count driven to exactly
`range(30)`, D from a count restored off disk and clamped to 64. Neither is an assertion this plan
wrote to be satisfied; both are pre-existing assertions that changed their answer.

Collision C's observed value **is** the after-number, arriving as a failure message.

---

## The four collisions, each cleared in the dated-reversal form

**Collision A — the cap test.** Rewritten with the withdrawn assertion quoted in full and dated
2026-08-28, overruled by two measured facts (REQ-22 for a persistently refused retailer, and the
125→37 move). Its first assertion is **re-pointed**, not dropped, at `REFUSALS_BEFORE_COOLOFF - 1`
— the deepest count at which the cap is still the governing rule. Its second assertion,
`MAX_BACKOFF_SECONDS <= 6 * 60 * 60` / *"a cap beyond a few hours is not a monitor"*, is **alive and
unmodified**. The name is kept, because it is still true and `git log -S` reaches its history
through it.

**Collision D — the clamp test.** Only the `due_at` literal moved, to a hand-written `259200.0`
rather than `COOLOFF_SECONDS` (a symbolic literal would be a re-derivation of the constant under
test in the one place that proves a *restored* count crosses the threshold). `git diff` shows
**exactly one changed assertion line** in that function; the clamp assertion and the
`record(...)  # must not raise` line are **byte-unchanged**, and the `2.0 ** 1024` `OverflowError`
subject is untouched. Not renamed, `10**9` document not touched, no assertion added.

**Collision C — `08-01`'s baseline.** Withdrawn in place and renamed, per `08-DECISIONS.md`
§ *Collision C*'s written instruction, which this plan executed rather than re-decided. Verified
**not duplicated**, which is the primary evidence and depends on no total:

```
def <withdrawn name>          : 0     (the definition is gone)
<withdrawn name> anywhere     : 1     (survives in the new docstring, for git log -S)
def <new name>                : 1
```

**Mutation anchors — and the abort reason differed from the plan's prediction.** The plan expected
`scripts/mutation_check.py` to exit 2 with a `HarnessError` from M33's missing anchor. It exited 2,
but for a **different and earlier reason**:

```
mutation check: HARNESS ERROR
baseline FAILED in the unmutated sandbox (pytest exit 1: tests failed).
Without a passing baseline every 'mutation caught' below would really be
'sandbox broken', and this check would report success while proving nothing.
...
This is not a result. Nothing was proved about the test suite either way.
```

The three expected reds fail in the unmutated sandbox, so the harness aborted at the **baseline**
and the anchor miss was never reached — masked behind it. The anchor miss is real and was measured
**separately**, after Task 2 repaired the three reds and the baseline passed again
(`876 passed, 29 skipped`):

```
mutation check: HARNESS ERROR
M38: anchor not found in boty/pacing.py.
```

(M33's surfaced first and was repaired first; `main` aborts at the first miss, so M38's identical
miss was invisible until then.) Recording this rather than reporting "exit 2 as predicted" is the
point: the plan predicted the right verdict for the wrong reason, and a summary that smoothed that
over would have hidden the fact that **a red suite masks an anchor miss entirely**.

### Kill sets re-measured, never carried over

Measured by applying each mutation **alone** in the harness's own sandbox and reading the failures
off the run — the protocol M33's 2026-08-17 comment already records.

| Ident | Kill set 2026-08-17 | **Re-measured 2026-08-28** | Change |
|---|---|---|---|
| M33 | 11 | **21** | +10, all of them tests that did not exist in Phase 7 |
| M38 | 1 | **1** | unchanged, and it is the same test |

M33's ten additions are all gates this phase added over the same accessor: the boundary table's six
rows (including the 29-refusal ones — `return st.interval` answers 300.0/1800.0 where the cap should
still bind), the single-probe test, the recovery-at-depth test, the cross-surface tracer, and
`08-01`'s renamed baseline (which postdates the 2026-08-17 measurement, so its absence from the 11
is a date and not a hole). The original eleven are all still in the set.

**M38's kill set is still one test and is still recorded as thin.** This phase did not improve it,
and that is stated rather than glossed: none of the new gates configures a standing interval above
`MAX_BACKOFF_SECONDS` — they all sit at 300 s or 1800 s — so not one of them widens it.

**Drift ordinals, counted off the re-anchor notes already in the file rather than assumed.** Six
anchors had drifted before this plan: M2 (2026-08-04), M4 (2026-08-11), M25 and M26 (2026-08-13),
M33 (2026-08-17) and M36 (2026-08-17). So **M38 is the seventh anchor in this registry to drift**,
and **M33 is the first anchor to drift twice**. Both are code-shape drifts, the third and fourth of
that kind.

**Final ratio: `mutation check: 37/37 mutations caught`, exit 0**, no `SURVIVED` line.
`grep -c 'ident="M'` = **37**, unchanged — **37 is the IDENT COUNT, not the highest ident number.**
M41 is the highest. Anyone re-deriving 41 from M41 has counted M1–M41 inclusive and silently filled
the M21–M24 gap, which the seven `INTENTIONAL GAP` markers exist to prevent.
`grep -c "INTENTIONAL GAP"` = **7**, unchanged. **No new ident: M42 remains free for `08-04`.**

---

## The recorded one-wave gap — stated, not closed here

**The tree now holds a three-day cool-off that a restart discards after six hours.**
`STATE_MAX_AGE_SECONDS` is still `MAX_BACKOFF_SECONDS`, so `Pacer.load`'s two-sided window throws
away any refusal record stamped more than 6 h ago — which, once a retailer is in a three-day
cool-off, is every record it will ever have.

This is deliberate and it is `08-DECISIONS.md` § *Collision 1*'s decision, not an oversight. The
re-derivation lands in **`08-03`** so that plan's tests are genuinely red against unfixed code
rather than red against a synthetic revert. All three clauses are needed to call it a recorded gap
and not a shipped defect: **nothing is deployed mid-phase**; `boty` is an editable install so the
daemon picks up a change only on a restart; and **a restart is Dan's call, never a task** — no plan
in this phase restarts the daemon, and none did.

**Criterion 5 is therefore explicitly NOT met while this wave stands, and is not claimed.**
Criterion 6 is `08-04`'s and is not claimed either.

**Second hand-off to `08-03`, named rather than left to be found.** After this plan, `refusals` past
30 means something it did not mean before — the count now selects a *policy*, not just a depth —
which is exactly the kind of policy-units change `STATE_VERSION`'s own comment says a bump may be
owed for. This plan adds no persisted structure, no `_RetailerState` field and no `STATE_VERSION`
change, so it does not pre-empt the argument. `08-03` owes it, **including the argument for no bump
and no new field.** `T-08-01` (Tampering — `Pacer.load` over `pacer-state.json`) is likewise carried
by `08-03`, not dropped: this plan adds nothing for it to cover.

---

## The gate

`make verify-offline` with nvm sourced first (`export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh`,
`node --version` → `v24.16.0`). **Exit code 0.** **Verdict line, verbatim:**

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

**The OFFLINE pass — not `PASS`, and not `PASS (INCOMPLETE)`.** No control was reported unverifiable
on this host, and nothing in this run says the retailers still work.
`control check: SKIPPED (--offline) — no live retailer request made.`

**The dashboard tests BOUND rather than skipped**, proved rather than assumed. The gate's test stage
is `$(PYTHON) -m pytest tests/ -q -rs` (`Makefile:76`), and it reported **`907 passed`** with **no
skip summary at all, i.e. zero skips**. Deselecting `tests/test_dashboard.py` from that same command
drops the total to `886 passed, 21 deselected`, and the module alone runs `21 passed` — so the 21
dashboard tests are among the 907 that ran inside the gate.

| Measurement | Before this plan | After |
|---|---|---|
| `tests/test_pacing.py` collected | 76 | **86** |
| `tests/test_cli_watch.py` collected | 44 | 45 |
| Suite under the gate's own invocation | 896 | **907** |

**`C₁` — the hand-off count from Task 1 to Task 2 — was 84**, exactly the projected 84 (75 on this
tree + `08-01`'s one + this task's eight). It was **handed over, not recovered**: written down at
the moment the run printed it, before any of Task 2's edits. Task 2's own `--collect-only` reported
**exactly 84**, a delta of **zero** across a task that renames a test rather than adding one. `C₁+1`
would have been the duplication signature and did not appear. The final 86 is 84 plus Task 3's two
new tests.

The identity checker did not trip on any prose this plan wrote:
`identity check: PASS — 239 file(s), no host identity found`, and the tracked pre-commit hook passed
on both commits (`PASS — 4 file(s)`, `PASS — 2 file(s)`). No commit used `--no-verify`.

---

## The scope fence

`git diff --name-only a2761e4..HEAD` — exactly the four files the plan names:

```
boty/pacing.py
scripts/mutation_check.py
tests/test_cli_watch.py
tests/test_pacing.py
```

**Not touched:** `served/boty/index.html` (collision B's `fmtDur` day band stays `08-04`'s
deliberate call — this plan hands it the fact that the number now reaching the page is **259200**),
`boty/monitor.py`, `boty/status.py`, `boty/cli.py`. Inside `boty/pacing.py`, `Pacer.load`,
`Pacer.save`, `_RetailerState` and `STATE_VERSION` are unchanged; the only code edits are
`current_interval`'s return and `skipped_reason`'s new arm. `MAX_BACKOFF_SECONDS` is still
`6 * 60 * 60` and `MAX_PERSISTED_REFUSALS` is still `64` — only their comments moved.

---

## Nothing live was touched

No live retailer request was made by any task. **`boty check` was not run.** `make verify` — the
unqualified target with live controls — was deliberately not run. `state.json`, `pacer-state.json`
and `served/boty/status.json` were **neither read nor written**; every test builds its own `Pacer`
in `tmp_path`. **No `systemctl restart boty`.**

---

## Deviations from Plan

**1. [Rule 2 - Missing critical functionality] A comment claimed a test that did not exist, so the test was written**

- **Found during:** Task 3, step 4.
- **Issue:** Repairing `MAX_PERSISTED_REFUSALS`' stale cross-reference (deviation 3 below) produced a
  replacement sentence stating that the clamp must exceed `REFUSALS_BEFORE_COOLOFF` and that *"that
  relationship is asserted by a test rather than by this comment"*. **Nothing asserted it.** Writing
  the claim and leaving it unbacked would have rebuilt, in the same comment, the exact defect being
  repaired — a relationship stated only in prose, which is what let the previous one rot for sixteen
  days.
- **Fix:** Added `test_the_clamp_sits_above_the_cooloff_threshold_so_a_restored_count_can_cross_it`.
  It defends a real defect: a threshold at or above the clamp would be a cool-off no restart could
  ever reach, since `load` clamps every restored count to 64 — persistence silently defeating the
  clause it exists to serve. **Watched red** by temporarily setting `REFUSALS_BEFORE_COOLOFF = 100`:
  `1 failed`, `assert 64 > 100`. Restored from a copy and re-verified green.
- **Files modified:** `tests/test_pacing.py`. **Commit:** `b3b11d1`.

**2. [Instructed by the orchestrator, outside the plan's stated scope] Fixed `boty/pacing.py`'s stale `cli.REFUSALS_BEFORE_PAGING` cross-reference**

- The plan says twice that this pre-existing stale comment is **not** its to fix and that no task
  touches it. The executor's instructions override: *"Wave 1 also handed you a genuine stale
  comment... You edit that file anyway — fix it, with a dated note."*
- `08-01` found it and deliberately left it, because a production edit would have poisoned the scope
  fence its baseline number depended on. Both reasons are recorded; the conflict is real and is
  resolved in favour of the instruction, not silently.
- **Fix:** Withdrawn in the house dated form — the sentence quoted in full, dated 2026-08-28, with
  the deletion of `REFUSALS_BEFORE_PAGING` and `_refusal_is_entrenched` on 2026-08-12 named as what
  overruled it, and a **live** relationship in the same direction put in its place (see deviation 1).
- **Commit:** `b3b11d1`.

**3. [Recorded, deliberately NOT fixed] `record`'s log line still reports a cool-off in minutes**

- Observed: at 30 refusals `boty/pacing.py`'s `record` logs
  `x refused us (30 in a row) — next attempt in ~4320 min, not 5`. That is the same
  units-that-hide-the-meaning problem Task 3 fixed in `skipped_reason`, one method over.
- **Not fixed here:** it is a log line and not the published page; no task in this plan names it; and
  `record`'s log format is outside this plan's stated surface. Recorded so it is a decision rather
  than an oversight. A candidate for `08-04`, which owns the presentation decisions.

**4. [Plan prediction wrong, recorded rather than reconciled] The mutation harness aborted for a different reason than predicted**

- Documented in full under *Collision C* above. The plan predicted exit 2 from M33's anchor miss;
  the observed abort was at the **baseline**, because a red suite makes the unmutated sandbox fail
  first and masks the anchor miss entirely. The anchor miss was then measured separately once the
  baseline passed. Same verdict, different cause, and the cause is the finding.

**5. [Process, corrected before commit] Two kill-set figures were written before they were measured**

- While drafting M33's and M38's anchor-drift notes I wrote kill-set numbers from expectation
  ("13, up from 11") before running anything — the precise move this repository's evidence standard
  forbids. Caught immediately and corrected by measuring each mutation alone in the harness sandbox
  **before** committing: M33's real figure is **21**, not the 13 I had written; M38's is **1**, which
  happened to match. Nothing wrong was committed. Recorded because a near-miss on the one rule that
  matters most here is worth more than a clean-looking silence.

---

## What this plan does NOT claim

- **Criterion 5 is NOT met and is not claimed** — the recorded one-wave gap above. It is `08-03`'s.
- **Criterion 6 is NOT discharged.** No mutation ident was registered, none was observed CAUGHT for
  a new gate, and **M42 is still free**. The `37/37` above says the tree is still green with new
  tests and re-anchored mutations in it — a regression check, not evidence for criterion 6.
- **The 30-day after-number is a measurement, not a gate**, in those words, for the reasons given
  above.
- **No claim that the retailers still work.** The verdict line was the OFFLINE pass; no live control
  ran.

## STATE.md and ROADMAP.md were NOT updated

Deliberately, per this executor's instructions: the orchestrator owns those writes and edits them by
hand. **No `gsd-tools` state or phase WRITE subcommand was invoked at any point** —
`state.advance-plan`, `state.begin-phase` and `phase.complete` are banned in this repo on fourteen
recorded corruptions, and an error return from one is not evidence that nothing was written.
`.planning/STATE.md` shows as modified in `git status`; **that modification is not this plan's** — it
was present before execution began and was never staged.

## Commits

| Commit | What |
|---|---|
| `e0534af` | `feat(08-02): stop asking a retailer that has said no thirty times running` — Tasks 1 and 2 |
| `b3b11d1` | `docs(08-02): withdraw the two arguments the cool-off overruled, and say so on the page` — Task 3 |

**Tasks 1 and 2 share one commit deliberately.** Task 1 ends with the tree red in exactly three
named places, by construction: one branch turns four new gates green and three existing tests red in
the same instant, and no ordering of a single-branch change avoids that. The choice is between a red
commit and a commit spanning two tasks, and this repository's rule is that a claim must be tied to a
measurement — a commit whose own suite is red claims something it cannot support. The red boundary
was **asserted** by Task 2's precondition (exactly three reds, no fourth) and never committed.

Git identity checked **before** committing: `3347065+danieljamesjohnson@users.noreply.github.com`,
the repo's configured no-reply identity.

## Self-Check: PASSED

- `boty/pacing.py` — FOUND. `grep -c "^REFUSALS_BEFORE_COOLOFF = 30$"` = 1;
  `grep -c "^COOLOFF_SECONDS = 3 \* 24 \* 60 \* 60$"` = 1;
  `grep -c "^MAX_BACKOFF_SECONDS = 6 \* 60 \* 60$"` = 1 (value untouched);
  `grep -c "WITHDRAWN ON 2026-08-28"` = 3. `current_interval` holds exactly one `return max(` and one
  `min(`, verified by reading the method.
- `tests/test_pacing.py` — FOUND. `grep -c "2026-08-28"` = 6; `grep -c "_THIRTY_DAYS_OF_CYCLES = 8640"`
  = 1; `grep -c "MAX_BACKOFF_SECONDS <= 6 \* 60 \* 60"` = 2; withdrawn-name def-count = 0, new-name
  def-count = 1.
- `tests/test_cli_watch.py` — FOUND, contains the tracer and `259200.0`.
- `scripts/mutation_check.py` — FOUND. `grep -c 'ident="M'` = 37; `grep -c "INTENTIONAL GAP"` = 7.
- Commit `e0534af` — FOUND in `git log`.
- Commit `b3b11d1` — FOUND in `git log`.
- `.venv/bin/python -m pytest tests/ -q -rs` → **907 passed**, zero skips.
- `make verify-offline` → exit 0, `VERIFY: PASS (OFFLINE — ...)`.
