---
phase: 01-detector-safety-net
verified: 2026-08-02T18:23:39Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
method: execution — every criterion was proved by running a command and reading its exit code, and every gate was proved to BITE by deliberately breaking the thing it guards and observing a non-zero exit
warnings:
  - id: W-01
    severity: warning
    title: "The mutation gate has no teeth over boty/monitor.py — the layer where CR-01 lived"
    evidence: "Deleting BOTH tests/test_monitor.py and tests/test_restock_replay.py (20 tests, all monitor/state coverage including the CR-01 pin) leaves `make verify-offline` printing VERIFY: PASS at exit 0. All three mutations target boty/parse.py and boty/retailers.py; none targets boty/monitor.py or boty/models.py."
    impact: "Does not violate any Phase 1 success criterion — SC5 is scoped to 'an extractor', and adapter work (the phase goal) lands in the mutated files. But the mutation check is the mechanism that proves the suite bites, and its proof does not extend to the state machine."
    recommendation: "Add M4 (boty/models.py price ceiling — already specified in REVIEW IN-04) and M5 (boty/monitor.py run_once transition recording — the CR-01 shape) before Phase 2 adds three adapters."
    decision_requested: true
deferred:
  - truth: "Six Info findings from 01-REVIEW.md remain open by design"
    addressed_in: "Phase 2 / Phase 4"
    evidence: "01-REVIEW-FIX.md frontmatter: deferred: 6, status: all_fixed for the 11 in-scope Critical+Warning findings. IN-03 (@type as a list) is explicitly flagged as a Phase 2 adapter hazard; IN-04 (mutation set does not cover the price ceiling) is the same concern as W-01."
---

# Phase 1: Detector Safety Net — Verification Report

**Phase Goal:** A contributor (or I) can add a retailer adapter and be told immediately if it breaks an existing one — offline, without hitting a live site.
**Verified:** 2026-08-02T18:23:39Z
**Status:** passed (6/6), with one documented warning
**Re-verification:** No — initial verification

## How this was verified

This phase's own thesis is that verification should be an exit code, not a
judgement. So no criterion below is marked satisfied because a SUMMARY.md says
so. Each was proved twice:

1. **The healthy path** — run the command, record the exit code.
2. **The bite** — break the specific thing the check guards, confirm the exit
   code goes non-zero, restore, confirm the tree is clean again.

A check that only ever passes proves nothing, which is the same argument the
phase makes for its own mutation step. Every deliberate breakage below was
reverted with `git checkout --`, and `git status --porcelain` was empty at the
end.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Saved HTML fixtures for GameStop and Walmart drive tests that pass without network access | VERIFIED | 4 real captures, 421–486 KB each, with `.json` sidecars carrying `captured_at`, `status`, `bytes`, `note`. `tests/conftest.py` installs an autouse guard that replaces `curl_cffi.requests.{get,post,request,head,put,delete,Session}` AND `socket.create_connection` / `socket.socket.connect` / `connect_ex`. `.venv/bin/python -m pytest tests/ -q` → **99 passed in 0.23s, exit 0** |
| 2 | A test proves each of the three availability states, including that an unparseable page yields UNKNOWN and never OUT_OF_STOCK | VERIFIED | `test_gamestop_out_of_stock_is_not_alertable` (OUT_OF_STOCK), `test_gamestop_control_is_in_stock_and_alertable` (IN_STOCK), `test_unparseable_page_is_unknown_not_out_of_stock` asserts both `is UNKNOWN` **and** `is not OUT_OF_STOCK`. Plus `test_blocked_fetch_is_unknown`, `test_fetch_error_is_unknown`, `test_retailer_with_no_first_party_list_is_unknown_not_out_of_stock`, `test_walmart_offer_with_no_seller_recorded_is_unknown_not_a_verdict` |
| 3 | A test proves a marketplace-seller offer above the price ceiling is not alertable | VERIFIED | Both defences pinned **independently**, as REQ-02 requires: `test_walmart_reseller_rejected_by_first_party_filter` (filter on), and `test_walmart_reseller_rejected_by_price_ceiling_alone` which runs with `first_party_only=False`, asserts `availability is IN_STOCK`, `price > 80`, `alertable is False`. Fixture is the real capture: `Clove Brothers LLC`, $229.99, against an $80 ceiling |
| 4 | `mypy` (or equivalent) runs clean over `boty/` | VERIFIED | `.venv/bin/python -m mypy` → **Success: no issues found in 13 source files, exit 0**. Config is committed (`[tool.mypy] files = ["boty", "scripts"]`), so the check does not depend on invocation flags. `disallow_untyped_defs = true` — without it non-strict mypy skips unannotated function bodies entirely and the package would pass with zero annotations |
| 5 | Deliberately corrupting an extractor makes the suite fail, not pass quietly | VERIFIED | **Executed.** Inverted `raw.rsplit("/", 1)[-1] in BUYABLE` → `not in BUYABLE` in `boty/parse.py`: **8 failed, 91 passed**, `make verify-offline` → `VERIFY: FAIL (tests)`, **exit 2**. Independently, the shipped mutation harness caught 3/3 in sandboxed copies (M1 parse, M2/M3 retailers) |
| 6 | `make verify` exits 0 on a healthy tree and non-zero if ANY check fails — tests, types, live control products, and the mutation check | VERIFIED | Healthy: `make verify` → live controls both in stock, 3/3 mutations caught, `VERIFY: PASS`, **exit 0** (run twice, before and after all experiments). All four failure branches executed individually — see the bite table below |

**Score: 6/6 truths verified**

### Proof that each gate bites

Every row is a command I ran, not a claim I read.

| Stage broken | How | Observed output | Exit |
|---|---|---|---|
| **tests** | Inverted the `BUYABLE` check in `boty/parse.py` | `8 failed, 91 passed` → `VERIFY: FAIL (tests)` | **2** |
| **types** | Appended `def _type_error_probe(x: int) -> str: return x` to `boty/status.py` | `boty/status.py:58: error: Incompatible return value type (got "int", expected "str")` → `VERIFY: FAIL (types)` | **2** |
| **live controls** (config error, exit 2) | `make verify CONTROL_FLAGS="-c <config with no control watch>"` | `control check: no control watches in ...` → `VERIFY: FAIL (live controls)` | **2** |
| **live controls** (control not IN_STOCK, exit 1) | Control watch pointed at `https://example.com/` (no structured data → UNKNOWN) | `control check: FAIL — 1/1 control(s) not reading IN_STOCK` | **1** |
| **mutation check** | Blinded the two tests that catch M2 (`pytest.skip` inserted into `test_unparseable_page_is_unknown_not_out_of_stock` and `test_an_unknown_reading_neither_alerts_nor_erases_what_is_known`) | Suite still green — `97 passed, 2 skipped`, exit 0 — but: `SURVIVED M2 boty/retailers.py: the suite passed anyway` … `mutation check: 2/3 mutations caught` → `VERIFY: FAIL (mutation check)` | **2** |
| **healthy** | Nothing broken, live network | `control check: PASS — 2/2 controls in stock` … `3/3 mutations caught` … `VERIFY: PASS` | **0** |

The mutation row is the load-bearing one. A **fully green 97-test suite** still
produced `VERIFY: FAIL`, because the gate does not ask "did the tests pass", it
asks "would the tests have noticed". That is the property the phase was built
to deliver and it demonstrably works.

Also worth recording: the Makefile refuses to launder a skip into a pass.
`make verify-offline` on a healthy tree prints
`VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the
retailers still work)` — a qualified verdict with its own exit-code path
(control_check exit 3), so a CI run that verified nothing about any retailer is
distinguishable from a fully green one.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `boty/fixtures.py` | capture/load/age_days/list_fixtures, no module-level network import | VERIFIED | 153 lines. `from . import fetch` appears **only** at line 82, indented inside `capture()`. `FIXTURE_ROOT` anchors to the repo via `pyproject.toml`, not cwd, with a `BOTY_FIXTURE_ROOT` override the mutation sandbox explicitly strips |
| `boty/cli.py` capture-fixture | subcommand, no config required | VERIFIED | `.venv/bin/boty capture-fixture --help` → exit 0, `usage: boty capture-fixture [-h] [--note NOTE] [-v] retailer name url`, "Needs no config file" |
| `tests/fixtures/gamestop/*.html+.json` | real captures with metadata | VERIFIED | `goplusplus` 421,964 B, `ps5-control` 486,481 B. Both sidecars carry ISO-8601 `captured_at` and a non-empty `note`. The ps5 note warns that the page has three offers and tests must not assert on `offers[0]` |
| `tests/fixtures/walmart/*.html+.json` | ditto, incl. the reseller case | VERIFIED | `goplusplus` 483,194 B — the real marketplace capture landed (`Clove Brothers LLC`, $229.99, IN_STOCK), so the plan's synthetic-fixture contingency was not needed and correctly not used. `milk-control` 471,690 B |
| `tests/conftest.py` | network guard + fixture fixtures | VERIFIED | Guard derives from `BaseException`, not `Exception` — deliberate, because `fetch.get`'s blanket `except Exception` would otherwise downgrade the guard into `Availability.UNKNOWN`, the single most common assertion in the suite. Three tests prove the guard itself fires |
| `tests/test_parse.py` | 14 tests | VERIFIED | ld+json and `__NEXT_DATA__` contracts, malformed-JSON, missing-node, empty-input paths |
| `tests/test_retailers.py` | 3 states + both flipper defences | VERIFIED | See truths 2 and 3 |
| `tests/test_monitor.py` | 16 tests | VERIFIED | Includes the CR-01 pins: `test_run_once_records_state_for_every_result_not_just_alertable_ones`, `test_run_once_alerts_again_on_the_restock_after_a_sellout`, `test_run_once_records_a_control_exactly_once` |
| `tests/test_restock_replay.py` | multi-cycle CR-01 replay | VERIFIED | 4 tests. Drives `run_once` → `check_html` → parser → frozen HTML across a persistent `State`. The unit is a session, not a call |
| `pyproject.toml` | mypy + pytest config committed | VERIFIED | `[tool.mypy] files = ["boty", "scripts"]`, `disallow_untyped_defs = true`. `[tool.pytest.ini_options] addopts = "-ra"` so skipped tests surface |
| `Makefile` | one command, one exit code | VERIFIED | No recipe line prefixed `-`, no pipes (a pipeline takes its last command's status), each stage traps and re-raises. `check-venv` gives a fresh clone an actionable message |
| `scripts/control_check.py` | live control health as an exit code | VERIFIED | 3-way outcome: 0 pass / 1 control not IN_STOCK / 2 config gap / 3 SKIPPED. Does not call `monitor.run_once` (would clobber `state.json`); does use `boty.cli._make_checker` so it exercises the same path `boty watch` does |
| `scripts/mutation_check.py` | prove the suite bites | VERIFIED | Sandboxed copy, never the working tree (confirmed: `git status` empty after every run). Baseline gate, `assert_imports_from_sandbox`, and only pytest exit **1** counts as caught — so a sandbox with no tests cannot score 3/3 |
| `tests/fixtures/README.md` | the fixtures-vs-controls distinction | VERIFIED | 102 lines. "**A green fixture suite does not mean a retailer still works.**" Documents `capture-fixture` with a worked example and the 90-day staleness warning |
| `README.md` | documents `make verify` | VERIFIED | "That is how you answer 'is bot-y still working' without reading any code." |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `boty/cli.py` | `boty/fixtures.py::capture` | `capture-fixture` subcommand | WIRED | `--help` returns 0 without a config file |
| `tests/*` | `boty.fixtures.load` | conftest fixtures | WIRED | Four named fixtures; zero HTTP in the suite, enforced by the autouse guard |
| `Makefile verify` | pytest / mypy / control_check / mutation_check | sequenced recipe with traps | WIRED | All four failure paths executed and observed non-zero |
| `Makefile verify` | control_check exit 3 | `case $rc in 0|3|*)` | WIRED | Skip survives into the verdict as a qualified PASS, not a bare one |
| `mutation_check` | sandbox `PYTHONPATH` | `assert_imports_from_sandbox` | WIRED | Guards against the editable install importing the real, unmutated `boty` |
| `tests/test_verify_makefile.py` | the Makefile itself | stub interpreter | WIRED | 5 tests, including `test_a_failing_live_check_fails_verify` and `test_a_skipped_live_check_does_not_produce_an_unqualified_pass` — the gate is itself under test |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Offline suite passes | `.venv/bin/python -m pytest tests/ -q` | `99 passed in 0.23s` | PASS |
| Types clean | `.venv/bin/python -m mypy` | `Success: no issues found in 13 source files` | PASS |
| Full gate green | `make verify` | `control check: PASS — 2/2 controls in stock`; `3/3 mutations caught`; `VERIFY: PASS` | PASS (exit 0) |
| Offline gate qualifies its verdict | `make verify-offline` | `VERIFY: PASS (OFFLINE — live controls were NOT run …)` | PASS (exit 0) |
| CLI subcommand exists | `.venv/bin/boty capture-fixture --help` | usage printed | PASS (exit 0) |
| Fixtures load with no network | `boty.fixtures.load` under the autouse socket guard | all 4 load | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| **REQ-01** | 01-01, 01-02 | Extraction logic testable offline against saved HTML fixtures, no network | SATISFIED | 4 real captures + `load()` with no module-level `fetch` import + a socket-level autouse guard + 3 tests proving the guard itself fires. 99 tests, 0.23s, no network |
| **REQ-02** | 01-02 | Three-state contract asserted explicitly (unparseable → UNKNOWN, never OUT_OF_STOCK), and seller filter + price ceiling each **independently** suppress a marketplace listing | SATISFIED | `test_unparseable_page_is_unknown_not_out_of_stock` asserts both directions; `test_walmart_reseller_rejected_by_first_party_filter` and `test_walmart_reseller_rejected_by_price_ceiling_alone` (`first_party_only=False`) prove independence |
| **REQ-03** | 01-02, 01-03 | `boty/` carries type hints and passes a static type check | SATISFIED | mypy exit 0 over 13 files; `disallow_untyped_defs = true` makes it enforced rather than a snapshot; config committed so it is reproducible |
| **REQ-12** | 01-04 | One `make verify` runs every mechanical check and exits non-zero if any fails | SATISFIED | All five stages present and sequenced; **all four failure branches executed and observed non-zero**; healthy run observed exit 0 twice |

No orphaned requirements: ROADMAP maps exactly REQ-01, REQ-02, REQ-03, REQ-12 to
Phase 1, and all four are claimed by plan frontmatter (01-01 → REQ-01; 01-02 →
REQ-01/02/03; 01-03 → REQ-03; 01-04 → REQ-12).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` / `PLACEHOLDER` | — | **None found** across `boty/`, `scripts/`, `tests/*.py`, `Makefile`, `pyproject.toml`, `README.md` |
| `tests/__pycache__/test_guard_bypass.*.pyc` | — | orphaned bytecode for a source file that never existed in git history | Info | Stale artifact from a transient file during the review-fix run. `__pycache__` is not tracked; harmless. `test_the_network_guard_is_not_downgraded_to_a_verdict` in `test_retailers.py` covers that behaviour |

## The CR-01 question — an honest assessment

The prompt asks the right question. The phase goal is that a contributor is
"told immediately if it breaks an existing one", and the original 36-test suite
did **not** tell anyone about CR-01 — a bug that silently dropped every restock
after the first, in a tool whose entire purpose is alerting on restocks. So:
does the net as it now stands catch that class, or does it only "catch" it
because a human found it by hand?

**I tested this directly rather than reasoning about it.** I reintroduced the
exact pre-fix code — collapsing the unconditional
`transitions = [state.transitioned_to_stock(r) for r in results]` back into the
short-circuiting `and` chain inside the `alerts` comprehension — and ran the
suite:

```
FAILED tests/test_monitor.py::test_run_once_records_state_for_every_result_not_just_alertable_ones
FAILED tests/test_monitor.py::test_run_once_alerts_again_on_the_restock_after_a_sellout
FAILED tests/test_monitor.py::test_run_once_records_a_control_exactly_once
FAILED tests/test_restock_replay.py::test_a_product_watch_alerts_on_every_rising_edge_not_just_the_first
FAILED tests/test_restock_replay.py::test_an_unknown_reading_neither_alerts_nor_erases_what_is_known
FAILED tests/test_restock_replay.py::test_a_control_watch_records_state_but_never_alerts
FAILED tests/test_restock_replay.py::test_the_price_ceiling_suppresses_the_alert_without_freezing_the_memory
8 failed, 91 passed
```

**The good news is structural, not incidental.** `test_restock_replay.py` is
not a regression test for one bug — it changes the *unit* from a call to a
session. It replays `out → in → out → in` through the real stack against one
persistent `State` and asserts on the whole sequence of verdicts, alerts and
remembered states. CR-01 was invisible to 36 tests precisely because it was a
property of the sequence and every test asserted on a single verdict. Any
future bug of that shape — bookkeeping that gets skipped, filtered, or
double-applied — lands in the same trap. `test_the_price_ceiling_suppresses_the_alert_without_freezing_the_memory`
is exactly that: the same class, one step along, caught in advance rather than
after the fact.

**The honest limitation (W-01).** The mutation check is the mechanism that
proves the suite would notice anything at all — and its proof does not extend
to the layer where CR-01 lived. All three mutations target `boty/parse.py` and
`boty/retailers.py`. Nothing mutates `boty/monitor.py` or `boty/models.py`. I
proved the consequence by deleting **all** monitor/state coverage — both
`tests/test_monitor.py` and `tests/test_restock_replay.py`, 20 tests including
every CR-01 pin — and re-running the gate:

```
baseline  unmutated sandbox passes (79 passed in 0.26s)
CAUGHT    M1 boty/parse.py: 4 test(s) failed
CAUGHT    M2 boty/retailers.py: 1 test(s) failed
CAUGHT    M3 boty/retailers.py: 5 test(s) failed
mutation check: 3/3 mutations caught
VERIFY: PASS (OFFLINE — …)          exit 0
```

Twenty tests gone, the CR-01 defence entirely removed, and `make verify` is
still green. So the correct statement is narrow and worth stating precisely:

- **The suite catches the CR-01 bug today.** Proved by reintroducing it.
- **The gate does not protect that fact.** A refactor that weakens or deletes
  the monitor tests passes `make verify` in silence — the same shape of failure
  the project exists to eliminate, one level up in the tooling.

This does **not** fail Success Criterion 5, which is scoped to "an extractor",
and it does not fail the phase goal, which is about adapters: a Phase 2 adapter
lands in `parse.py` / `retailers.py` / `config`, all of which the mutation set
covers and all of which I proved bite. It is a warning about the gate's
coverage boundary, and the reviewer already saw a version of it — IN-04 asks
for an M4 over the price ceiling for the same reason.

**Recommendation before Phase 2:** add M4 (`boty/models.py`:
`return self.price <= self.watch.max_price` → `return True`, already specified
verbatim in IN-04) and M5 (`boty/monitor.py`: the CR-01 short-circuit shape).
Both are ~8 lines in `MUTATIONS`. Phase 2 is about to add three adapters; the
gate should cover the state machine those adapters feed before that happens,
not after.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|---|---|---|
| 1 | Six Info findings from the code review (IN-01 unused logger, IN-02 stale docstring rationale, IN-03 `@type` as a list, IN-04 no price-ceiling mutation, IN-05 mutation-harness robustness, IN-06 fixture path sanitisation) | Phase 2 / Phase 4 | `01-REVIEW-FIX.md`: `deferred: 6`, all Critical (3) and Warning (8) fixed and test-pinned. I confirmed all six are still open in the code: `log` at `retailers.py:22` is declared and never used; `parse.py:71` is still `node.get("@type") != "Product"`; `MUTATIONS` is still 3 entries; `fixtures.py` `html_path`/`meta_path` still take raw argv segments |

Of these, **IN-03 is the one with teeth for Phase 2**: a retailer publishing
`"@type": ["Product", "ProductModel"]` will read as a mysterious UNKNOWN rather
than an obvious bug. It fails safe, so it costs coverage rather than
correctness — but Pokémon Center and the Nintendo store are exactly the kind of
first-party sites that use compound `@type`. **IN-04 is subsumed by W-01.** The
rest are cosmetic or defence-in-depth on a local-only write primitive.

### Human Verification Required

None. Every success criterion in this phase is mechanically checkable by
construction — that is the point of `make verify` — and all six were checked by
execution, including all four of the gate's failure branches. No PLAN file
contained a deferred `<human-check>` block.

The one thing genuinely wanting a human is a **decision, not a test**: whether
W-01's mutation-coverage gap is closed before Phase 2 or accepted. That is
recorded in `warnings[0].decision_requested` rather than manufactured as a
verification item, because inventing a human check to avoid saying "passed"
would be its own kind of dishonesty.

### Gaps Summary

No gaps. Six of six success criteria verified by execution, not inspection.

What makes this phase unusually solid is that the gate is adversarial about
itself, and I could confirm each of those guards independently:

- The mutation check refuses to score a broken sandbox (a baseline run must
  pass first), refuses to count anything but pytest exit 1 (so a sandbox with
  no tests cannot score 3/3), refuses to run against the editable install
  (`assert_imports_from_sandbox`), and never touches the working tree — `git
  status --porcelain` was empty after every run I made, including the failing
  ones.
- The control check separates "no connectivity" (exit 3, SKIPPED, nothing
  learned) from "a retailer turned us away" (exit 1, FAIL), and the Makefile
  carries that third outcome all the way to a qualified verdict instead of
  flattening it to green.
- The Makefile has no `-` prefixes, no pipes, and traps per stage — and is
  itself under test in `tests/test_verify_makefile.py`.
- The network guard derives from `BaseException` specifically so it cannot be
  laundered into `Availability.UNKNOWN` by `fetch.get`'s blanket handler, and
  three tests prove the guard fires, including at the raw socket layer that
  apprise and the connectivity probe use.

The single reservation is W-01, documented above at length: the gate proves the
suite bites over the extraction layer, and only over the extraction layer. That
is what Criterion 5 asked for and it is what the phase goal needs for adapter
work, so the phase passes — but the mutation set should grow to cover the state
machine before Phase 2 lands three more adapters on top of it.

**Final state of the tree:** clean (`git status --porcelain` empty), `make
verify` → `VERIFY: PASS`, exit 0, with both live controls reading in stock.

---

_Verified: 2026-08-02T18:23:39Z_
_Verifier: Claude (gsd-verifier)_

---

## W-01 resolved after verification

The verifier flagged that all three mutations targeted `parse.py`/`retailers.py`,
leaving the price ceiling and the state machine — the layer CR-01 lived in —
outside the gate. Reproduced: deleting `test_monitor.py` and
`test_restock_replay.py` (20 tests, every CR-01 pin) still gave `VERIFY: PASS`
at exit 0.

Closed by adding two mutations:

| ID | Target | Breaks |
|----|--------|--------|
| M4 | `boty/models.py` | an unreadable price clears the ceiling — a flip at any price becomes alertable |
| M5 | `boty/monitor.py` | restores the CR-01 short-circuit — every restock after the first is silently missed |

Healthy tree: `5/5 mutations caught`, `VERIFY: PASS`, exit 0.
Same deletion experiment now: 79 tests still pass, but `VERIFY: FAIL (mutation
check)` at exit 2 naming `SURVIVED M5`. The gate now protects the tests that
catch the bug that nearly shipped.
