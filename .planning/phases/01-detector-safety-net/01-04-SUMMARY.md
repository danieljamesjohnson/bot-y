---
phase: 01-detector-safety-net
plan: 04
subsystem: verification
tags: [makefile, mutation-testing, control-products, exit-codes, fixture-staleness]

# Dependency graph
requires:
  - "01-01: boty/fixtures.py (list_fixtures, age_days, metadata) and the four frozen fixtures"
  - "01-02: the 36-test offline suite — the thing the mutation check proves has teeth"
  - "01-03: [tool.mypy] in pyproject.toml, so `types` is a flagless command"
provides:
  - "`make verify` — one command, one exit code, covering tests, types, fixture staleness, live controls and mutation"
  - "`make verify-offline` — the CI variant, no live retailer request"
  - "scripts/control_check.py — live control health, --offline and --fixtures modes"
  - "scripts/mutation_check.py — three sandboxed mutations the suite must catch"
  - "mypy now covers scripts/ as well as boty/"
affects: [every later phase — success criteria are stated in terms of make verify]

# Tech tracking
tech-stack:
  added:
    - "GNU make (no new Python dependency; every check is stdlib + the existing dev extra)"
  patterns:
    - "Per-stage failure traps in the verify recipe, so the verdict prints AND the exit code survives"
    - "Mutation testing in a mkdtemp copy with a mandatory unmutated baseline and PYTHONPATH pinning"
    - "Connectivity pre-flight separating 'no internet' (skip) from 'retailer refused us' (fail)"

key-files:
  created:
    - Makefile
    - scripts/control_check.py
    - scripts/mutation_check.py
  modified:
    - pyproject.toml
    - README.md

key-decisions:
  - "Live controls skip on no connectivity and fail on a retailer refusal — a verify that goes red on dropped wifi gets ignored within a week, but being blocked by Walmart is the monitor not working"
  - "Only pytest exit code 1 counts as a caught mutation; 2/3/4/5 abort as harness errors, so a sandbox with no tests cannot score 3/3"
  - "An unmutated baseline runs first, because without it every 'caught' is really 'sandbox broken' and the check reports success while proving nothing"
  - "scripts/ added to mypy files — the verifier itself was the one thing outside the net it applies to everything else"
  - "The control check never calls monitor.run_once, because run_once unconditionally calls state.save() and would discard the live service's remembered product state"
  - "Fixture staleness warns and never fails; failing on age trains people to re-capture blindly, converting a signal about the retailer into a chore"

patterns-established:
  - "Every check was proved to bite by breaking it deliberately and observing the exit code, not by observing a green run"

requirements-completed: [REQ-12]

# Metrics
duration: 25min
completed: 2026-08-02
---

# Phase 1 Plan 04: `make verify` Summary

**One command that answers "is bot-y still working" with an exit code — and
every stage of it was proved to fail by breaking that stage on purpose, including
the case that matters most: a fully green 36-test suite that `make verify` still
rejects because the mutation check found a hole in it.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 6 (5 producing commits, 1 verification-only)
- **Files:** 3 created, 2 modified

## Accomplishments

- **`Makefile`** — `help` (default), `test`, `types`, `fixtures`, `controls`,
  `mutation`, `verify`, `verify-offline`, plus a `check-venv` guard that names
  the fix instead of emitting `No such file or directory`. `verify` runs
  test → types → fixtures → controls → mutation. `verify-offline` delegates to
  `verify` with `CONTROL_FLAGS=--offline`, so there is exactly one definition of
  the order and one of the verdict.
- **`scripts/control_check.py`** — checks only `control: true` watches, live.
  Builds its checker with `boty.cli._make_checker`, the same function `boty
  watch` uses, so it exercises the routing the running monitor actually uses
  rather than a parallel code path. Also carries `--fixtures` (staleness
  warnings) and `--offline`.
- **`scripts/mutation_check.py`** — corrupts three specific things in a
  throwaway copy and requires the suite to go red for each:

  | | Mutation | Caught by |
  |---|---|---|
  | M1 | `in BUYABLE` → `not in BUYABLE` in `parse.py` | 4 tests |
  | M2 | unreadable page → `OUT_OF_STOCK` instead of `UNKNOWN` | `test_unparseable_page_is_unknown_not_out_of_stock` |
  | M3 | `if first_party_only:` → `if False:` | `test_walmart_reseller_rejected_by_first_party_filter` |

- **`pyproject.toml`** — `files = ["boty", "scripts"]`.
- **`README.md`** — "Verifying it works", with the fixtures-vs-controls
  distinction stated plainly.

## Task Commits

| Task | Name | Commit | Type |
|---|---|---|---|
| 1 | Live control-product check | `effc2cc` | feat |
| 2 | Mutation check | `5e897fb` | feat |
| 3 | Fixture staleness warning | `de48d26` | feat |
| 4 | The Makefile | `ba3b502` | feat |
| 5 | Document it | `20d1eed` | docs |
| 6 | Restart the live services | — | verification only, no file change |

## Verification — every check proved to bite

`make verify` on the healthy tree: **exit 0**, `VERIFY: PASS`, 6.1s live /
1.5s offline. Then each stage was broken in turn and restored:

| Broken | Observed exit | Verdict line |
|---|---|---|
| a test asserts `False` | **2** | `VERIFY: FAIL (tests)` |
| an annotation removed from `_as_float` | **2** | `VERIFY: FAIL (types)` |
| `scripts/control_check.py` moved aside | **2** | `VERIFY: FAIL (fixtures)` |
| an out-of-stock product marked `control: true` | **2** | `VERIFY: FAIL (live controls)` |
| the one test that catches M2 deleted | **2** | `VERIFY: FAIL (mutation check)` |
| `PYTHON=/nonexistent/python` | **2** | `VERIFY: FAIL (tests)` via `check-venv` |

**Exit code 2, not 1** — that is make's own status for a failed recipe. The
contract is "non-zero", and it holds in every case; nothing should test for
`== 1`.

**The mutation row is the important one.** With that single test deleted, the
`test` stage printed `35 passed` and went green, and `make verify` still failed,
naming the survivor and what it means: *"an unreadable page becomes
OUT_OF_STOCK instead of UNKNOWN — the silent-failure bug itself"*. That is the
whole argument for the mutation check, demonstrated rather than asserted.

**The mutation harness's own guards were each proved to fire**, by driving
`mutation_check` with a stubbed `run_suite`:

| Scenario | Result |
|---|---|
| baseline does not pass | exit 2, `HARNESS ERROR`, no mutation results reported |
| pytest exits 5 (no tests collected) | exit 2, `HARNESS ERROR` — **not** counted as caught |
| mutation anchor not found in source | exit 2, `HARNESS ERROR` — not silently skipped |
| a mutation survives | exit 1, names the survivor |

**No pipes in any recipe.** The classic Makefile trap (`cmd | tee` taking the
last command's status) cannot occur here; the failure traps use `||` with an
explicit `exit 1`, and there is no `-` prefix or discarded-failure fallback
anywhere in the file.

**Gates unchanged:** `.venv/bin/python -m pytest tests/ -q` → **36 passed in
0.06s**. `.venv/bin/python -m mypy` → **Success: no issues found in 13 source
files** (11 `boty` + 2 `scripts`).

**Working tree never mutated:** `git status --porcelain` is empty after a
mutation run, and no `/tmp/boty-mutation-*` sandbox is left behind.

**`state.json` and `served/boty/status.json` never written by the control
check:** mtimes identical across a live run measured immediately before and
after, and the script contains no reference to `State`, `run_once`, `save(` or
`write_status` outside its docstring. (Both files *do* change every ~300s —
that is the live `boty.service` doing its job, which is exactly why this script
had to stay out of them.)

## Decisions Made

- **Offline behaviour is a deliberate split, not a shrug.** A pre-flight TCP
  probe to two neutral IPs (`1.1.1.1`, `8.8.8.8` — raw addresses, so a broken
  resolver is caught too) decides which of two very different things happened.
  No connectivity at all → the live check is **skipped**, exit 0, printing "This
  is not a pass … nothing was learned about them here." Connectivity present but
  a control does not read IN_STOCK — including a fetch failure or a bot wall →
  **fail**. Being turned away by Walmart is the monitor not working, not an
  infrastructure hiccup, and hiding it would defeat the only check that can
  detect a retailer redesign. Empirically confirmed: run under `sudo unshare -n`
  the check skips and exits 0.
- **One retry, and only for transport failures.** Retailers rate-limit
  intermittently, so a `fetch failed` / `blocked` / `api error` result is retried
  once after 3s. A control that parsed cleanly and said OUT_OF_STOCK will say it
  again; retrying that is just a slower route to the same true answer.
- **The control check reuses `boty.cli._make_checker`.** Importing a private
  name is a small cost against the alternative: a control check with its own
  copy of the routing would keep passing after `boty watch` started doing
  something different, which is precisely the divergence controls exist to
  catch.
- **Only pytest exit 1 counts as caught.** pytest exits 2 on collection error, 4
  on usage error, 5 when nothing was collected. A sandbox missing
  `tests/fixtures/` would otherwise score a flawless 3/3 while running no
  assertions at all.
- **`--fixtures` warns and never fails.** A stale fixture is a prompt to
  re-capture and see whether the expected values *changed* — and if they did,
  that is real news about the retailer. Failing on age would train people to
  re-capture blindly on a deadline, which turns that signal into a chore and
  leaves the suite asserting against whatever the page happens to say today.
- **Stage order follows the plan** (test, types, fixtures, controls, mutation).
  The mutation check is offline and takes 1s, so an argument exists for putting
  it before the network round-trip; the difference is one second and the plan
  was explicit, so the plan won.
- **Explicit `sys.stdout.flush()` before the failure explanations.** stdout is
  block-buffered to a pipe while stderr is not, so under `make` the "here is why
  this matters" block printed *above* the per-control lines it was explaining.
  Caught by reading actual piped output rather than terminal output.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] mypy did not cover `scripts/`**

- **Found during:** Task 4
- **Issue:** `[tool.mypy] files = ["boty"]`, so the two scripts `make verify`
  trusts to tell the truth about everything else were themselves outside the
  type check. The one part of the tree nobody re-reads — because it is the thing
  that does the reading — had the weakest guarantees in the repo.
- **Fix:** `files = ["boty", "scripts"]`, with the reason in a config comment.
  Free at HEAD: both scripts were written fully annotated and mypy passes over
  13 files.
- **Files modified:** `pyproject.toml`
- **Commit:** `ba3b502`

**2. [Rule 2 - Missing Critical] `make` with no `.venv` failed uninformatively**

- **Found during:** Task 4
- **Issue:** Every target hard-codes `.venv/bin/python`. On a fresh clone that
  produces `/bin/sh: 1: .venv/bin/python: not found` — a message that tells a
  contributor nothing, on the one command the README points them at.
- **Fix:** A `check-venv` prerequisite that names the fix
  (`python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'`) and a
  `PYTHON ?=` override. Verified: `make PYTHON=/nonexistent/python verify` prints
  the guidance and exits non-zero.
- **Files modified:** `Makefile`
- **Commit:** `ba3b502`

**3. [Rule 1 - Bug] `IndexError` in the mutation baseline on empty pytest output**

- **Found during:** Task 2 guard testing
- **Issue:** `proc.stdout.strip().splitlines()[-1]` raised `IndexError` when
  pytest produced no stdout. A harness that crashes with a traceback instead of
  its own diagnostic is a harness whose failure mode nobody can read.
- **Fix:** Guarded the index, falling back to `"no pytest output"`.
- **Files modified:** `scripts/mutation_check.py`
- **Commit:** `5e897fb`

**4. [Rule 1 - Bug] Failed-test names reported as the literal string `FAILED`**

- **Found during:** Task 2
- **Issue:** `line.split(" ")[0]` on `FAILED tests/x.py::test_y - msg` returns
  `FAILED`, so the output read `caught by FAILED, FAILED, FAILED`. Cosmetic, but
  it destroyed the single most useful piece of information the check produces:
  *which* test is holding that line.
- **Fix:** Index `[1]`. Output now names the tests.
- **Files modified:** `scripts/mutation_check.py`
- **Commit:** `5e897fb`

**5. [Rule 1 - Bug] Failure explanation printed above the results it explained**

- **Found during:** Task 1
- **Issue:** Under a pipe, the stderr explanation appeared before the stdout
  per-control lines.
- **Fix:** `sys.stdout.flush()` before the stderr block, with a comment saying
  why.
- **Files modified:** `scripts/control_check.py`
- **Commit:** `effc2cc`

### Scope Notes (not deviations)

- **Task 6 produced no commit.** `deploy/boty.service` needed no change; the
  task was a restart plus verification. Both units are `active` /
  `SubState=running` with `NRestarts=0`, and `served/boty/status.json` was
  rewritten 8 seconds after the restart — so the new process is cycling, not
  crash-looping inside the `StartLimitBurst=5` budget.
- The control check gained exit code **2** for "no control watches configured",
  distinct from **1** for "a control is not in stock". The two mean different
  things: one is a misconfiguration, the other is a broken detector.

---

**Total deviations:** 5 auto-fixed (2 missing-critical, 3 bugs). None
architectural.

## Issues Encountered

- **`state.json` mtime changes during a control-check run — but not because of
  it.** The first mtime comparison showed a change and looked like a violation
  of the "never write state" requirement. It was the live `boty.service` on its
  own ~300s cycle. Re-measured in a tight window around a run: unchanged. Worth
  recording because the naive check would have sent someone chasing a bug that
  is not there, which is the same failure mode as picking a contested product as
  a control.
- **`make` exits 2, not 1, on a failed recipe.** Anything downstream should test
  for non-zero, never `== 1`.

## Known Stubs

None.

## User Setup Required

None. `make verify` works from a checkout with `.venv` present, and says how to
create one if it is not.

## Next Phase Readiness

Phase 1 is complete. Later phases can state success criteria as "`make verify`
exits 0" and mean something by it:

- `make verify` → exit 0, `VERIFY: PASS` (6s, live)
- `make verify-offline` → exit 0 (1.5s, no network)
- Every stage demonstrated to fail the whole run when broken
- A new retailer adapter in Phase 2 inherits all of it: the network guard from
  01-02, `disallow_untyped_defs` from 01-03, and this. It will also need a
  control watch, since `assess_health` reports a retailer with no control as
  unhealthy.
- The three mutations are anchored to exact source strings. If Phase 2 refactors
  `parse.py` or `retailers.py`, the check aborts as a HARNESS ERROR naming the
  drifted anchor rather than silently dropping to 2/3 — update the anchors when
  that happens.

No blockers.

## Self-Check: PASSED

All 5 claimed files exist on disk (`Makefile`, `scripts/control_check.py`,
`scripts/mutation_check.py`, `pyproject.toml`, `README.md`); all 5 task commits
(`effc2cc`, `5e897fb`, `de48d26`, `ba3b502`, `20d1eed`) present in git history.

---
*Phase: 01-detector-safety-net*
*Completed: 2026-08-02*
