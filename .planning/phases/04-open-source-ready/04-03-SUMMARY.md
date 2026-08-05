---
phase: 04-open-source-ready
plan: 03
subsystem: build-and-verify
tags: [lint, ruff, makefile, verify, supply-chain]
requires: ["04-01", "04-02"]
provides:
  - "ruff in the dev extra, pinned >=0.16,<0.17, with a dated supply-chain audit note"
  - "[tool.ruff] / [tool.ruff.lint] — the committed rule set, with every exclusion recorded as a measurement"
  - "make lint, and a lint stage inside make verify that has been watched failing"
  - "README's stage table finally naming every stage verify runs"
  - "test_the_documented_stages_are_the_stages_verify_runs — the gate that keeps it true"
affects:
  - "04-04: CI's entry point is `make verify-offline`, which now lints. No separate lint step is needed."
tech-stack:
  added: ["ruff 0.16.1 (dev extra only, zero transitive dependencies, MIT)"]
  patterns:
    - "Rule selection committed in pyproject.toml, not passed as flags — the same idiom as [tool.mypy] files"
    - "Every deliberate exclusion recorded with the number that justified it"
    - "A new verify stage is not shipped until it has been observed going red from inside verify"
key-files:
  created: []
  modified:
    - pyproject.toml
    - .gitignore
    - Makefile
    - README.md
    - boty/cli.py
    - boty/monitor.py
    - boty/parse.py
    - scripts/identity_check.py
    - tests/test_verify_makefile.py
    - tests/test_control_check.py
    - tests/test_evidence_check.py
    - tests/test_fetch.py
    - tests/test_identity_check.py
    - tests/test_pacing.py
    - tests/test_retailers.py
    - tests/test_support_matrix.py
decisions:
  - "B905 resolved as strict=True, against ruff's own unsafe autofix, because a truncated alerts list is a missed restock that reads exactly like a quiet market"
  - "E501 not selected: 497 findings, all of them over the comment blocks that carry this project's recorded decisions"
  - "ruff format not adopted: 32 of 36 files would be rewritten immediately before a 1.0.0 tag"
  - "external = [E402] rather than deleting the seven noqa directives RUF100 calls unused"
  - "lint runs second in verify — cheapest check in the file, but identity's position is justified by consequence rather than cost"
metrics:
  duration: ~50m
  completed: 2026-08-04
  tasks: 3
  commits: 3
  tests_before: 460
  tests_after: 462
---

# Phase 04 Plan 03: Lint — Summary

REQ-10's lint half: `ruff` chosen, audited, configured with every exclusion recorded as a
measurement, all 20 findings resolved (four by hand, against ruff's own autofixes), and a
`lint` stage wired into `make verify` that was watched going red before it was shipped.

## Task 1 baseline — the linter watched failing

`ruff 0.16.1` reached the venv through `pip install -e '.[dev]'`, not a bare
`pip install ruff`. `python -m ruff check` exited **1** with **20 findings**, 10 safe-fixable
and 9 needing `--unsafe-fixes`.

```
6	RUF005	[ ] collection-literal-concatenation
3	I001  	[*] unsorted-imports
2	SIM114	[*] if-with-same-arms
1	B905  	[ ] zip-without-explicit-strict
1	C416  	[ ] unnecessary-comprehension
1	F401  	[*] unused-import
1	RUF021	[*] parenthesize-chained-operators
1	SIM102	[ ] collapsible-if
1	SIM103	[ ] needless-bool
1	SIM300	[*] yoda-conditions
1	UP035 	[*] deprecated-import
1	UP037 	[*] quoted-annotation
Found 20 errors.
```

Full listing (post-wave-2 tree):

```
boty/cli.py:8:1: I001            boty/monitor.py:16:1: I001
boty/monitor.py:120:12: UP037    boty/monitor.py:174:32: B905
boty/parse.py:246:13: SIM102     scripts/identity_check.py:59:5: SIM103
tests/test_control_check.py:28:1: UP035
tests/test_evidence_check.py:{494,516,597,892,1237,1261}:38: RUF005
tests/test_fetch.py:1082:16: RUF021    tests/test_fetch.py:1142:15: C416
tests/test_identity_check.py:78:12: SIM300
tests/test_pacing.py:27:25: F401       tests/test_retailers.py:18:1: I001
tests/test_support_matrix.py:{321,400}:9: SIM114
```

**Nothing was new relative to Task 2's 20-item table.** The plan expected wave 1's
`tests/test_contributor_docs.py` and wave 2's `tests/test_packaging_metadata.py` to push the
count above 20; they contributed **zero** findings. Neither file needed a lint fix, so no
wave-1 gate was reformatted, let alone weakened. Both remain green at 38 collected.

`git diff -U0 -- pyproject.toml | grep -c '^-[^-]'` returned **0** — the task removed no line
from the file 04-02 had just edited.

## Task 2 — findings resolved

`ruff check --fix` (safe only) fixed 13 of 23 (20 original + 3 that cascaded out of the
SIM114 combinations). **`--unsafe-fixes` was never run, as a bulk operation or otherwise.**
Every hunk of the resulting diff was read before anything else happened; none changed the
meaning of a conditional, moved a comment block, or edited a docstring quoting a measurement.

Hand-resolved, with the reason recorded next to each in the source:

| Finding | Disposition |
|---|---|
| **B905** `boty/monitor.py` | **`strict=True`**, not the permissive value ruff's unsafe autofix writes. `transitions` is a comprehension over `results` on the line directly above, so the two are the same length by construction; a divergence would make `zip` silently truncate `alerts`, and a truncated `alerts` is a missed restock that reads on the wire exactly like a quiet market. A crash is the better failure. M5's anchor (the `transitions = [...]` line) untouched. |
| **SIM102** `boty/parse.py` | Nested `if wanted is not None:` collapsed into one condition; the `str()` comment moved above it, wording unchanged. Both halves answer one question. M1's and M8's anchors verified byte-identical afterwards. |
| **SIM103** `scripts/identity_check.py` | Final condition returned directly. Ruff's unsafe fix wraps it in `bool(...)`; rejected — the `and`-chain of comparisons is already a `bool`, and the wrapper reads as though it might not be. mypy confirms against the declared `-> bool`. |
| **RUF005** ×6 `tests/test_evidence_check.py` | Rewritten as unpacking. `_SHIPPED` is a list literal (line 159), so the result is an equal list. |
| **C416** `tests/test_fetch.py` | `set(root.glob(...))`. |
| **SIM114** ×2 `tests/test_support_matrix.py` | Combined with `or` (both branches assign an identical value), then **hand-wrapped** — ruff's output for the first was a 110-character line. `E501` is not selected, so the reviewer is the driver, not the length. |

Pre-checks the plan required, all confirmed before accepting a fix:

- **F401** — `grep -c BACKOFF_FACTOR tests/test_pacing.py` returned `1`, the import itself. Genuinely unused, not an existence pin.
- **UP037** — `from __future__ import annotations` at line 16 and `Pacer` imported under `TYPE_CHECKING` at line 28, so the quotes were dead weight.
- **RUF021 precedence** — `and` binds tighter than `or`, so the original already read as *empty* **or** *(all-zero digits)* **or** *`XX`* **or** *contains REDACTED* **or** *a JS sentinel* **or** *TEST-NET-1* — six independent ways of being a placeholder. Ruff's parentheses freeze exactly that reading, which matches the assertion's own message ("Allow-listing a real value silently disables this gate for that value"). Confirmed before accepting; had the parenthesised form read differently, accepting it would have frozen a bug into a security gate.

### Two acceptance criteria that fought their own instructions

Both were adjudicated in favour of keeping the machine check meaningful, with the reasoning
written into the source next to each:

1. The plan told Task 2 to record the B905 reason in a comment **and** asserted
   `grep -F 'strict=False' boty/monitor.py` matches nothing. Quoting the token in the comment
   defeated the grep. Reworded to "the permissive value (`False`)".
2. The plan told Task 3 to comment that ruff's formatter is not adopted **and** asserted
   `! grep -qF 'ruff format' Makefile`. Same collision; reworded to "ruff's formatter", with
   the measurement (32 of 36) kept.

Neither changes what the comment says. Both keep the grep able to catch the thing it guards.

## Task 3 — the stage, watched going red

The `lint` target is `$(PYTHON) -m ruff check` with no rule flags. It is in `.PHONY`, in
`make help`, and wired into `verify` as a trap line after `identity` and before `test`, in the
identical form its neighbours use. The `=== verify: ... ===` echo names it.

README's stage table gained **two** rows: `lint`, and `identity` — which had run first for two
phases while the table never said so. That gap was the same defect this plan exists to
prevent, sitting in the table the plan was editing.

**Observed RED, then observed GREEN, for both new tests** — not inferred:

```
# lint trap line removed from the Makefile:
>       assert proc.returncode != 0
E       assert 0 != 0
E        +  where 0 = CompletedProcess(... "\nVERIFY: PASS\n..." ).returncode
FAILED tests/test_verify_makefile.py::test_a_failing_lint_fails_verify
# restored: 1 passed
```

`verify` printed **`VERIFY: PASS`** while lint was failing — exactly the silent devaluation
the test exists to catch.

```
# lint row deleted from README.md:
E  AssertionError: README's stage table and `make verify` disagree.
E  Runs but undocumented: ['lint']. Documented but never run: [].
FAILED tests/test_verify_makefile.py::test_the_documented_stages_are_the_stages_verify_runs
# restored: 1 passed
```

`tests/test_verify_makefile.py` now collects **8**. `_run` gained `lint_rc: int = 0`, so all
six pre-existing tests are behaviourally unchanged — the only removed lines in that file are
the `_STUB` docstring (extended), the `_run` signature (extended) and its `env` line. No
existing assertion was edited.

The stub matches `*-m\ ruff*`, verified against every stage invocation to confirm it catches
the ruff call and nothing else.

## Verification

| Check | Result |
|---|---|
| `make lint` | exits 0, "All checks passed!" |
| `python -m ruff check` | exits 0 |
| `pytest tests/ -q` | **462 passed** (pre-plan **460**; +2 new tests, none lost) |
| `python -m mypy` | Success: no issues found in 17 source files |
| `scripts/mutation_check.py` | **8/8 mutations caught**, no `HarnessError` |
| all 8 `MUTATIONS[*].search` anchors | present byte-for-byte, asserted programmatically |
| `grep -c 'noqa: E402'` | **7** (5 in `control_check.py`, 2 in `evidence_check.py`) — none deleted |
| `identity_check.py --all` | PASS — 144 files |
| `pytest test_support_matrix/test_identity_check/test_contributor_docs/test_packaging_metadata` | 73 passed |
| `make verify-offline` | exits 0, `lint` stage visible in the output |
| `git status --porcelain` | clean; no `.ruff_cache` entry |

Verdict line, verbatim:

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

The mutation sandbox baseline reports **462 passed**, which is the evidence that both new
tests actually run inside the sandbox rather than being silently skipped — `Makefile` and
`README.md` were already in `SANDBOX_CONTENTS` from wave 2, so no change there was needed.

Diffstat:

```
 .gitignore     |   8 ++++
 README.md      |   2 +     <- exactly two added rows, zero removed
 pyproject.toml | 113 +++++  <- zero removed
```

`grep -c '^| Retailer | Rung | Extraction |' README.md` returns `1` — the seven-column
support-matrix locator is untouched.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 — blocking] B007 in this plan's own new test helper**

- **Found during:** Task 3, first `make lint` after writing the two tests
- **Issue:** `_stage_table`'s `for i, line in enumerate(lines)` tripped `B007` — `i` is used
  *after* the loop, not inside it. Ruff's suggested fix (rename to `_i`) would have been
  wrong, since the variable is genuinely used.
- **Fix:** Restructured to `next((n for n, line in enumerate(lines) if ...), None)`. No
  behaviour change; the test still finds the table and still goes red when the row is missing
  (re-observed after the restructure).
- **Commit:** 319f7b0

**2. [Rule 3 — blocking] Two acceptance criteria contradicted their own action text**

Documented in full under "Two acceptance criteria that fought their own instructions" above.
Both resolved by rewording the comment rather than by weakening the grep.

### Not deviations, but worth stating

- **No rule was removed from `select`** to make a finding disappear, and **no new `# noqa`**
  was added.
- **No finding was left unresolved**, so the plan's "record it as a question for the phase
  gate" path was never taken.
- The scope note's Task 2/Task 3 split was **not** taken — context was not short.

## Known Stubs

None.

## Threat Flags

None. This plan adds no network endpoint, auth path, file-access pattern or schema change.
The one new dependency (`ruff`) is `dev`-only, runs at lint time, and is covered by
T-04-03-05 in the plan's own register.

## Handoff to 04-04

- **CI's entry point is `make verify-offline`**, which now runs `lint` as its second stage.
  The workflow needs **no separate lint step** — adding one would be a second definition of
  the rule set.
- **`pip install -e '.[dev]'` remains the only install line.** The `dev` extra is what brings
  `ruff`, and `ruff` has zero transitive dependencies.
- If CI ever needs to lint without the venv, `python -m ruff check` from the repo root checks
  the same 35 files, because `[tool.ruff] include` is committed.
- **REQ-11 was not touched.** It remains Pending.

## Self-Check

- `pyproject.toml` — FOUND (`[tool.ruff.lint]` present)
- `Makefile` — FOUND (`VERIFY: FAIL (lint)` present)
- `tests/test_verify_makefile.py` — FOUND (`LINT_RC` present)
- `README.md` — FOUND (`| \`lint\` |` present)
- `.gitignore` — FOUND (`.ruff_cache` present)
- Commit `2149349` — FOUND
- Commit `c8f5628` — FOUND
- Commit `319f7b0` — FOUND

## Self-Check: PASSED
