---
phase: 03-the-hard-two
plan: 03
subsystem: testing
tags: [req-08, runtime-budget, evidence-gate, support-matrix, cr-01, durability, phase-close, tdd]

requires:
  - phase: 03-the-hard-two
    provides: 03-01's scripts/evidence_check.py and ROADMAP_RETAILERS, and 03-02's Target verdict — the precondition that made evidence_check --phase exit 0 on the real tree
  - phase: 02-five-retailers-green
    provides: Rung/degraded on Result, the status.json dashboard contract, the mutation harness, and 02-VERIFICATION.md's open CR-01 durability item
provides:
  - duration_seconds published by every pass, so REQ-08's budget is read rather than re-measured by hand
  - The honesty gate running inside make verify via the offline suite, rather than inside one plan's verify block
  - tests/test_support_matrix.py — the README retailer table held to the same standard as the runtime flag, sharing one retailer set with the evidence gate
  - A measured runtime budget (61.4 s manual, 35.0 s service-published, 120 s budget) with the configuration it was measured at
  - CR-01 closed with two daemon readings 41 minutes and 7 cycles apart, zero and flat
  - Phase criterion 5 recorded UNMET at four, in four places, with nothing padded
affects: [04-01 contributor docs, 04-02 CI]

tech-stack:
  added: []
  patterns:
    - "A published number beats an asserted one: the budget lives in the served payload, so anyone can read what the last pass cost without re-running it"
    - "None means unmeasured, not zero — the three-valued honesty Availability is built on, applied to a number"
    - "A gate belongs in the always-run stage, not in the plan that created it: a check that only runs inside one plan's verify block dies with the plan"
    - "Each rule is a function over parsed input, so the corruption tests run the SAME rule against a deliberately broken copy of the real document"
    - "Two gates that describe one set import that set from one place rather than retyping it"

key-files:
  created:
    - tests/test_support_matrix.py
    - .planning/phases/03-the-hard-two/03-03-SUMMARY.md
  modified:
    - boty/status.py
    - boty/cli.py
    - tests/test_status.py
    - tests/test_cli_watch.py
    - tests/test_evidence_check.py
    - scripts/mutation_check.py
    - README.md
    - docs/retailer-evidence.md
    - QUESTIONS.md

key-decisions:
  - "duration_seconds defaults to None, not 0.0: a pass nobody timed is a different fact from a pass that took no time, and 0 would read off the dashboard as the fastest check ever recorded"
  - "time.monotonic(), never time.time(): this file is served over HTTP and an NTP correction mid-pass would publish a negative duration"
  - "run_once is timed, not the process: interpreter startup and config load are not what REQ-08 is about, and a number that drifts with Python's import time is not a retailer measurement"
  - "The gate went into the offline suite, not into a new Makefile stage — the stage list and its four exit codes are pinned by tests/test_verify_makefile.py, so a stage would be a large change for no extra signal"
  - "The support matrix rules are functions over parsed rows so the corruption tests exercise the SAME code path the real assertions do; a gate proved only against the tree it guards has never been watched failing"
  - "The 61.4 s measurement was reported as measured rather than re-run until it looked better; the service's own 35.0 s cycle twelve minutes later is what identifies the difference as a transient timeout"
  - "Criterion 5 recorded UNMET at four in four places (summary, evidence log, README, QUESTIONS.md) and config/products.yaml gained nothing"

requirements-completed: [REQ-07, REQ-08]

duration: 47min
completed: 2026-08-03
---

# Phase 3 Plan 03: Closing the Phase Summary

**The runtime budget stopped being an assertion and became a published number — 61.4 s against 120 s, then 35.0 s from the service itself — the honesty gate moved from one plan's verify block into every `make verify`, the README's table got a test behind it, and the one durability question no exit code could answer was answered by sitting still for 41 minutes and counting.**

## Performance

- **Duration:** ~47 min (of which ~34 min was the CR-01 window, deliberately spent)
- **Started:** 2026-08-03T04:29:58Z (reading A, taken before anything else)
- **Completed:** 2026-08-03T05:16:00Z
- **Tasks:** 3, in 5 commits
- **Files modified:** 10 (2 created, 8 modified)
- **Tests:** 238 → **253** (+6 task 1, +9 task 2)

## The two daemon readings, side by side (CR-01)

`02-VERIFICATION.md` left this open as the one gap `make verify` structurally
cannot close: the three teardown tests drive a **fake** nodriver, and a one-shot
process cannot measure a daemon-lifetime property. Only elapsed time closes it.

| | **Reading A** | **Reading B** |
|---|---|---|
| Timestamp (UTC) | **2026-08-03T04:29:58Z** | **2026-08-03T05:11:24Z** |
| MainPID | 287281 | **287281** — same process, no restart |
| Uptime | 6,189 s (103.2 min) | 8,675 s (144.6 min) |
| Child processes | 0 | 0 |
| **Zombie children** | **0** | **0** |
| **`uc_*` profile dirs** | **0** | **0** |

- **Window: 41 min 26 s** (requirement: ≥40 min).
- **7 completed cycles** inside that window (requirement: ≥6), observed
  empirically rather than inferred — a sampler read `served/boty/status.json`'s
  `updated` field every 30 s and recorded seven distinct values: `04:35:15`,
  `04:41:32`, `04:47:25`, `04:52:44`, `04:57:48`, `05:03:03`, `05:07:57`.
  Period ≈ 6 min (a ~35 s pass plus a jittered 300 s sleep).
- Reading B was taken **before** anything in this plan stopped the service. The
  restart in task 3 step 3 came afterwards, so the window was never reset.
- The profile count was taken inside the unit's **private** tmp
  (`PrivateTmp=yes`, confirmed), i.e. `/tmp/systemd-private-*boty.service*/tmp`,
  not the host `/tmp`. That directory was **empty**, not merely free of `uc_*`.

**Verdict: zero and FLAT, not merely low.** The original leak reached 13 zombies
and 204 MB in 71 minutes at roughly one per 5-minute cycle; seven cycles at that
rate would have produced ~7 zombies and a visibly growing profile directory.
Neither moved off zero. Combined with the independent watch that sampled 28→63
minutes of uptime, this daemon has now been observed zombie-free from 28 minutes
to 145 minutes of continuous running. **CR-01 is closed.**

## The `boty check` output, verbatim

Run at 2026-08-03T05:12Z with `boty.service` stopped, under
`sudo systemd-run --pipe --quiet --uid=dan --property=EnvironmentFile=/home/dan/.config/boty/env --property=WorkingDirectory=/home/dan/CodeProjects/pokemongoplusplus /home/dan/CodeProjects/pokemongoplusplus/.venv/bin/boty check -c config/products.yaml`
(colour codes stripped):

```
2026-08-03 00:12:06,553 WARNING BOTY_BROWSER_NO_SANDBOX is set — Chrome's sandbox is OFF and retailer JavaScript runs with this process's privileges
  ○ gamestop  Pokémon GO Plus +             $   54.99  ld+json: OutOfStock from GameStop
  ○ walmart   Pokémon GO Plus +                        1 offer(s) via __NEXT_DATA__, none first-party
  ○ nintendo  Pokémon GO Plus +             $   54.99  ld+json: OutOfStock from Nintendo of America Inc.
  ● gamestop  CONTROL — PS5 console         $  549.99  ld+json: InStock from GameStop [control]
  ● walmart   CONTROL — Great Value whole mi$    2.42  __NEXT_DATA__: IN_STOCK from Walmart.com [control]
  ● bestbuy   CONTROL — Pokémon Let's Go, Pi$   59.99  ld+json: InStock from Best Buy [control] [degraded]
  ● nintendo  CONTROL — Nintendo HDMI cable $    7.99  ld+json: InStock from Nintendo of America Inc. [control]
  ● gamestop  TRANSITION — Pitch Black Boost$   59.99  ld+json: InStock from GameStop
  ● gamestop  TRANSITION — Ascended Heroes M$   24.99  ld+json: InStock from GameStop
  ? gamestop  TRANSITION — Mega Evolution Bo           fetch failed: Timeout: Failed to perform, curl: (28) Con

  10 watches across 4 retailers in 61.4s
```

Exit 0. **No `!` health-warning lines.** Best Buy is the only rung-3 reading and
it carries `[degraded]`, next to `[control]`, both tags at once.

## The measured budget (REQ-08)

**61.4 s against a 120 s budget**, at **10 watches across 4 retailers, one of
them on rung 3** — `duration_seconds: 61.37750405189581` in
`served/boty/status.json`, published by the run above rather than timed by hand.

| Measurement | Watches | Retailers | Result |
|---|---|---|---|
| 02-04 (Phase 2, hand-timed) | 10 | 4 (one rung 3) | ~40 s |
| 03-02 (`time`, service env) | 10 | 4 (one rung 3) | 36.8 s |
| **03-03 (published, manual run)** | 10 | 4 (one rung 3) | **61.4 s** |
| **03-03 (published, `boty.service` cycle)** | 10 | 4 (one rung 3) | **35.0 s** |

**What changed, and what did not.** The configuration is identical across all
four rows — no watch was added or removed, and both hard-two retailers are rung
4, so nothing was ever configured for them. What made the third row 25 s slower
than the second was a **transient network failure**: `TRANSITION — Mega
Evolution Booster Bundle` hit `Timeout: Failed to perform, curl: (28)` and went
through `boty.fetch.get`'s retry and backoff.

That reading was reported as measured rather than re-run until it looked better.
The fourth row is what settles it: twelve minutes later, the **restarted service
published its own cycle at 35.0 s** for the same config, `healthy: true`, one
`rung: browser` reading flagged `degraded: true`, and **no UNKNOWN readings at
all**. The difference was the timeout, not a cost this phase added. The figure
to carry forward is **35–61 s at 10 watches and 4 retailers**, where the upper
end already includes a retailer failing to answer.

Two things worth not rounding away:

- **The budget's headroom is what absorbed the timeout.** A retailer timing out
  is ordinary; the pass still finished at roughly half the budget.
- **The timed-out watch read UNKNOWN, not OUT_OF_STOCK.** The core promise of
  this project holding under exactly the condition that breaks other monitors: a
  fetch that never completed did not become a stock verdict.

REQ-08's wording is "at ~7 retailers". Four is what shipped, so four is what was
measured. Extrapolating a number for a seven-retailer configuration that was
never run — and can never be run, because three of the seven are refused in
writing — would be inventing the measurement the `duration_seconds` key exists
to avoid.

## `make verify` verdict line, verbatim

```
VERIFY: PASS
```

Exit 0, under
`sudo systemd-run --pipe --quiet --uid=dan --property=EnvironmentFile=/home/dan/.config/boty/env --property=WorkingDirectory=/home/dan/CodeProjects/pokemongoplusplus /usr/bin/make verify`
— **not** `PASS (OFFLINE)` and **not** `PASS (INCOMPLETE)`, so the live control
stage actually ran under the environment the service gets. Controls:

```
control check: PASS — 4/4 controls in stock
  in_stock      gamestop  CONTROL — PS5 console                $549.99  ld+json: InStock from GameStop
  in_stock      walmart   CONTROL — Great Value whole milk       $2.42  __NEXT_DATA__: IN_STOCK from Walmart.com
  in_stock      bestbuy   CONTROL — Pokémon Let's Go, Pikach    $59.99  ld+json: InStock from Best Buy
  in_stock      nintendo  CONTROL — Nintendo HDMI cable          $7.99  ld+json: InStock from Nintendo of America Inc.
```

## Phase criterion 5: the count, stated plainly

**Four retailers. Criterion 5 is UNMET. It is not met by a retailer that cannot
alert on the product, and it was not rounded.**

`served/boty/status.json` reports **4** retailers — `bestbuy`, `gamestop`,
`nintendo`, `walmart` — with `healthy: true` and an empty unhealthy list. The
criterion asks for five or more. Read off the file, not off an expectation.

This is the outcome the roadmap explicitly anticipated — *"If both are rung 4,
this criterion is unmet and recorded as such, never padded with a retailer that
does not carry the product"* — and it is now **final rather than pending**:

- Both hard-two retailers are **rung 4** by written prohibition, with **zero
  product-page requests** between them. Amazon's `LICENSE AND ACCESS` forbids
  the method *and* independently names the data; Target's `Unlawful or
  Prohibited Uses` forbids data extraction with no commercial-use qualifier.
- Every retailer in the roadmap's scope is now shipped or carries its own
  `**Verdict: REFUSED**` section. There is no sixth candidate.
- A control-only fifth was available and declined: Micro Center is reachable at
  rung 1 with a real control and a real fixture, and does not carry the product.
- Of the four that work, **three** carry the GO Plus + itself. Best Buy is
  control-only, which is a disproof backed by two searches, not an omission.

Recorded in four places: this summary, `docs/retailer-evidence.md`'s closing
record, `README.md`, and `QUESTIONS.md` §0b (which contains `rung 4`). **Nothing
was added to `config/products.yaml`** — `git diff` over this plan's five commits
shows it untouched. `notify-dan` delivered: *"bot-y: Phase 3 lands at four
retailers"*.

## Accomplishments

- **The budget is now a published fact.** `status.write` gained a keyword-only
  `duration_seconds`, serialised top-level, `null` when the pass was not timed.
  Both callers time `run_once` with `time.monotonic()` — not `time.time()`,
  because this file is served over HTTP and an NTP correction mid-pass would
  publish a negative duration. `boty check` prints the same number as its last
  line, so the human surface and the machine one agree.
- **The honesty gate outlives its plan.** `evidence_check.py --phase` now runs
  in the `test` stage of every `make verify`, via a test in the offline suite
  rather than a new Makefile stage (the stage list and its four exit codes are
  pinned by `tests/test_verify_makefile.py`). **Proved it bites**: padding
  `config/products.yaml` with an out-of-scope `microcenter` watch produced
  `VERIFY: FAIL (tests)` at non-zero exit, naming the stage; deleting Target's
  evidence section produced the rule-2 failure. Both reverted, tree clean.
- **The support matrix has a test behind it for the first time.** Criterion 3
  requires DEGRADED in the matrix *and* in `boty check`. The runtime half was
  pinned in three places; the matrix half was prose nothing checked — the exact
  shape of WR-04. `tests/test_support_matrix.py` now requires a rung of 1–4 for
  every retailer in scope, `degrad` in any rung-3 row, and a row for every
  configured retailer. It imports `ROADMAP_RETAILERS` from
  `scripts/evidence_check.py` rather than retyping it, so the two gates cannot
  drift into disagreeing about which stores exist.
- **CR-01 is closed by elapsed time, which was the only thing that could close
  it.** See the table above.
- **The mutation harness caught its own blind spot, twice in two plans.** Adding
  a test that reads `README.md` broke the sandbox; the harness refused to score
  anything rather than reporting a false 6/6.

## Task Commits

1. **Task 1 (RED): failing tests for the published pass duration** — `43d96ae` (test)
2. **Task 1 (GREEN): publish how long each pass took** — `6ec6adb` (feat)
3. **Task 2: wire the honesty gate into `make verify`, pin the support matrix** — `399c6b6` (test)
4. **Task 2 (fix): copy `README.md` into the mutation sandbox** — `a926318` (fix)
5. **Task 3: record the measured budget, the daemon readings, the honest count** — `df47035` (docs)

## TDD Gate Compliance

**Task 1** ran a clean RED → GREEN cycle. Six tests were written and watched
failing for the right reasons — `TypeError: unexpected keyword argument`,
`KeyError: 'duration_seconds'`, and a missing elapsed-time line in `capsys`
output — then `43d96ae` committed the RED and `6ec6adb` the GREEN. No REFACTOR
commit: the implementation went green without needing one.

**Task 2 needs an honest note.** Its tests **passed on their first run**, which
is normally a fail-fast signal. It was investigated rather than waved through,
and the reason is benign and documented: 03-01 and 03-02 each kept the README
row current as part of their own work, and 03-02's Target verdict is what made
`evidence_check --phase` exit 0 on the real tree — 03-02's summary names that as
the precondition it was leaving for this plan. So the shipped tree was already
compliant, and a test asserting compliance had nothing to fail against.

RED was therefore performed by **corrupting the real tree** and watching each
rule go red, which is what the plan's behaviour list actually asks for:

| Corruption | Result |
|---|---|
| Blank GameStop's Rung cell | `test_every_roadmap_retailer_carries_a_rung_of_one_to_four` FAILED |
| Strip `[degraded]` from Best Buy's rung-3 row | `test_a_rung_three_retailer_is_flagged_degraded_in_the_matrix` FAILED |
| Add an out-of-scope `microcenter` watch | `test_the_shipped_tree_passes_the_whole_phase_gate` FAILED; **`make verify` → `VERIFY: FAIL (tests)`**, exit non-zero |
| Delete Target's `## Target` evidence section | `test_the_real_shipped_evidence_document_passes_per_retailer` and the phase-gate test both FAILED |

Every corruption was reverted and the tree confirmed clean (`git status --short`
showed only the intended new/modified test files). Four further corruption cases
are permanently pinned as tests at the bottom of
`tests/test_support_matrix.py`, driven against in-memory copies of the real
README, so the rules stay watched rather than having been watched once.

## Files Created/Modified

- `boty/status.py` — keyword-only `duration_seconds`, published top-level, with
  the comment block explaining why `None` ≠ `0` and why callers must use
  `monotonic`.
- `boty/cli.py` — both callers time `run_once`; the `check` branch prints the
  watch count, distinct retailer count and elapsed seconds.
- `tests/test_status.py` — 3 tests (+`_OMITTED` sentinel so the unmeasured path
  is reached by omission, exactly as pre-existing callers reach it).
- `tests/test_cli_watch.py` — 3 tests, all offline via a monkeypatched
  `_make_checker` and a `tmp_path` `status_path` so the suite cannot clobber the
  deployed dashboard's file.
- `tests/test_support_matrix.py` — **new**, 8 tests.
- `tests/test_evidence_check.py` — the shipped-tree `--phase` test (the line
  that puts the gate in `make verify`), and Target added to the per-retailer
  loop.
- `scripts/mutation_check.py` — `README.md` added to `SANDBOX_CONTENTS`.
- `README.md` — count paragraph now says "final, not pending" and explains why
  the number did not move; the gate paragraph now states that it runs on every
  `make verify` and names the matrix test.
- `docs/retailer-evidence.md` — `## Phase 3 closing record`: what shipped, what
  did not, the three refusals told apart, the count with its reason, and the
  REQ-08 measurement table.
- `QUESTIONS.md` — §0b closed out with the live numbers and the CR-01 result.

## Verification gates

| Gate | Result |
|---|---|
| `.venv/bin/python -m pytest tests/ -q` | **253 passed** (was 238; +15) |
| `.venv/bin/python -m mypy` | `Success: no issues found in 15 source files` |
| `.venv/bin/python scripts/mutation_check.py` | `6/6 mutations caught` |
| `.venv/bin/python scripts/evidence_check.py --phase` | exit 0, `evidence check: PASS — phase` |
| `make verify` (`systemd-run`, service `EnvironmentFile`) | exit 0, **`VERIFY: PASS`** — unqualified |
| `make verify` (corrupted config) | exit non-zero, **`VERIFY: FAIL (tests)`** |
| `served/boty/status.json` `healthy` | `true`, 4/4 retailers ok |
| `served/boty/status.json` `duration_seconds` | `61.38` manual / `35.04` service — both < 120 |
| every `rung: browser` watch is `degraded` | 1/1 (bestbuy) |
| README matrix complete | 7/7 retailers carry a rung of 1–4; the rung-3 row says `degraded` |
| daemon zombies / profiles, A→B | 0 → 0, flat, over 41 min and 7 cycles |
| `notify-dan` | `sent: bot-y: Phase 3 lands at four retailers` |

## Decisions Made

Recorded in the frontmatter. The three that will matter to Phase 4:

- **`duration_seconds` is `None` when unmeasured, never `0.0`.** The dashboard
  renders this file verbatim; a missing measurement serialised as zero would
  read as the fastest check ever recorded.
- **The gate went into the offline suite, not into a new Makefile stage.**
  `tests/test_verify_makefile.py` pins the stage list and the four exit codes, so
  a stage would have been a large change for no extra signal. Phase 4's CI work
  inherits a gate that runs wherever the suite runs.
- **The 61.4 s reading was published as measured.** The temptation was to re-run
  until the number looked like 03-02's 36.8 s. What was done instead is cheaper
  and more honest: report it, then let the service's own next cycle (35.0 s) say
  what the difference was.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `README.md` missing from the mutation sandbox**

- **Found during:** Task 3 step 2, on the first `make verify` under the service
  environment.
- **Issue:** `tests/test_support_matrix.py` parses the real `README.md`, but
  `SANDBOX_CONTENTS` did not copy it, so all 8 tests raised `FileNotFoundError`
  inside the sandbox. The baseline failed, so the harness aborted with
  *"This is not a result. Nothing was proved about the test suite either way."*
  and `make verify` exited `VERIFY: FAIL (mutation check)`. Correct behaviour —
  a test failing in the sandbox for want of a file is indistinguishable from a
  mutation being caught — but the run was dead.
- **Fix:** added `"README.md"` to `SANDBOX_CONTENTS` with the reason, which is
  what that constant's own comment prescribes. Noted in the comment that M6 is
  precisely the mutation that clears the runtime `degraded` flag, so a sandbox
  without the README would break the matrix half of criterion 3 inside the run
  meant to score the runtime half.
- **Files modified:** `scripts/mutation_check.py`
- **Verification:** `6/6 mutations caught`, baseline `253 passed`; the
  subsequent `make verify` printed `VERIFY: PASS`.
- **Committed in:** `a926318`
- **Note:** this is the same defect 03-01 fixed for `docs/`, one layer along —
  the second time in two plans that adding a test which reads a real document
  has broken the sandbox. Worth a Phase 4 look at deriving `SANDBOX_CONTENTS`
  rather than maintaining it.

**2. [Rule 2 - Missing Critical] Alert-edge safety around the manual live check**

- **Found during:** Task 3 step 3, before running it.
- **Issue:** the plan has `boty check` run against the real config, and
  `run_once` commits transitions to `state.seen` and saves — but the `check`
  branch never sends notifications. A genuine restock landing during that single
  pass would therefore have had its edge **consumed silently**, and the next
  service cycle would have found it already remembered and stayed quiet. This is
  pre-existing behaviour, not something this plan introduced, and out of scope
  to change.
- **Fix:** `state.json` was copied before the run and diffed after, with an
  explicit check for any watch that moved to `in_stock` — the rollback that
  `watch_cycle` performs on a failed send was ready to be applied by hand.
- **Verification:** `state changes across the manual check: none`;
  `alert edges consumed without a notification: none`. Nothing needed restoring.
- **Files modified:** none (procedure, not code).

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical).
**Impact on plan:** none on scope. The first was caught by `make verify` doing
its job; the second was a hazard in the plan's own instructions that cost one
`cp` and one diff to make safe.

## Issues Encountered

- **A retailer timed out during the measurement run.** `TRANSITION — Mega
  Evolution Booster Bundle` returned `curl: (28)` and added ~25 s of retry and
  backoff. Recorded rather than re-rolled. It is also the most useful thing in
  the run: the watch read **UNKNOWN**, not OUT_OF_STOCK, which is the promise
  this project exists for, observed under live failure rather than against a
  fixture.
- **The plan's task 2 could not fail on first run.** See TDD Gate Compliance.
  The honest reading is that 03-01 and 03-02 did their jobs; the risk is that a
  future reader sees green tests and assumes they were never watched failing,
  which is why the corruption table is in this document and four corruption
  cases are pinned as tests.
- **One corruption test cascades.** `test_a_planned_rung_cell_fails_too` asserts
  `_rungless(rows) == {"Target": "Planned"}` exactly, so blanking a *different*
  retailer's rung fails it too. That is correct — the tree really is broken in
  that state — but a future reader debugging one blanked cell will see two
  failures, and the second is downstream of the first.

## User Setup Required

None. Dan was notified (`notify-dan`, delivered) because criterion 5 is recorded
unmet; nothing is blocked on him. `boty.service` was stopped for 96 seconds
(05:11:48Z → 05:13:24Z) for the measurement run and is `active` again on PID
446442, publishing cycles normally.

## Known Stubs

None. Nothing was stubbed, mocked or left half-wired. The one place a stub could
hide — `duration_seconds` defaulting to `None` — is deliberate three-valued
honesty, is asserted in both directions by
`test_an_unmeasured_pass_publishes_null_rather_than_zero` and
`test_a_measured_pass_publishes_its_duration`, and is `float` in both live
callers.

## Next Phase Readiness

- **Phase 3 is complete and every criterion has an answer.** 1 and 2: Target and
  Amazon both documented at rung 4 with the evidence. 3: DEGRADED in the matrix
  and in `boty check`, both now tested. 4: 4/4 controls green, no Phase 2
  regression. 5: **UNMET at four**, recorded in four places, nothing padded. 6:
  61.4 s against 120 s, measured under the service's environment. 7:
  `VERIFY: PASS`, unqualified.
- **REQ-07 and REQ-08 both flip Complete here**, which is the rule 03-01 and
  03-02 each deliberately deferred to: a requirement flips when its *phase*
  completes, and this is the phase's last plan.
- **CR-01 is closed**, so `02-VERIFICATION.md`'s open human item can be marked
  answered. Phase 4 inherits no open durability question.
- **Phase 4 (Open Source Ready) inherits three gates that run themselves:**
  `evidence_check --phase`, `test_support_matrix.py` and the mutation harness
  all run inside `make verify`, so a CI job that runs `make verify` inherits the
  honesty rules without restating them.
- **Two things Phase 4 should look at:** deriving `SANDBOX_CONTENTS` from what
  the suite actually opens (this is twice now), and whether `boty check`
  consuming an alert edge without notifying is worth fixing before contributors
  start running it by hand.

## Self-Check: PASSED

- All 10 claimed files exist on disk.
- All 5 claimed commit hashes resolve in `git log`.
- `config/products.yaml` is **untouched** across this plan's commits.
- `served/boty/status.json` carries a numeric `duration_seconds`, `healthy:
  true`, 4 retailers, and `degraded: true` on its one `rung: browser` watch.
- `boty.service` is `active`.

---
*Phase: 03-the-hard-two*
*Completed: 2026-08-03*
