---
phase: 04-open-source-ready
plan: 02
subsystem: packaging
tags: [req-11, licence, pep-639, sdist, manifest, mutation-sandbox, packaging-gate]

requires:
  - phase: 04-open-source-ready
    plan: 01
    provides: "`hooks` and `CONTRIBUTING.md` in SANDBOX_CONTENTS — the `hooks` entry is load-bearing here, not merely prior: the git index un-skips a test that asserts hooks/pre-commit exists inside the sandbox"
provides:
  - "LICENSE — the canonical SPDX MIT text this repo has declared since Phase 1 and never shipped"
  - "pyproject.toml declaring PEP 639 `license = \"MIT\"` + `license-files = [\"LICENSE\"]`, six backed classifiers, four project URLs"
  - "MANIFEST.in — eight prune lines; the published sdist file surface is now a decision rather than a setuptools default"
  - "tests/test_packaging_metadata.py — 19 tests, two-directional licence rule, and NotATrackedTree so the sdist gate cannot pass by not running"
  - "A mutation sandbox that is a real git tree carrying LICENSE and MANIFEST.in, and skips nothing"
affects: [04-03 the linter, 04-04 CI, 04-05 the release]

tech-stack:
  added: []
  patterns:
    - "A packaging gate in the shape of tests/test_support_matrix.py: rules as pure functions over text, each watched failing against a corrupted copy of the real file"
    - "A rule that cannot run raises a named error rather than reporting an absence — NotATrackedTree, in both of git's failure shapes"
    - "The mutation sandbox is a git tree, so rules that read git run there instead of skipping or going vacuously green"

key-files:
  created:
    - LICENSE
    - MANIFEST.in
    - tests/test_packaging_metadata.py
  modified:
    - pyproject.toml
    - scripts/mutation_check.py

key-decisions:
  - "The non-repo question was decided by giving the sandbox a git index, not by skipping and not by returning an absence — and the rule ALSO raises NotATrackedTree, so if the index is ever stripped out make verify dies naming the cause instead of going green"
  - "_project_table was widened to read multi-line arrays, consciously and in a comment: the plan specified single-line values only, and the classifiers list this plan added spans lines"
  - "prune rather than graft: shipping tests/fixtures/ would put captured retailer HTML into a public artifact, and this repo redacts fixtures by class rather than by value for exactly that reason"
  - "No Development Status classifier and no Changelog URL — both are statements about a version and a file that do not exist yet; they belong with 04-05's 1.0.0 bump"
  - "No Typing :: Typed classifier — there is no boty/py.typed marker, so it would advertise a typing contract no installed consumer can act on"
  - "_IGNORE gained status.json rather than SANDBOX_CONTENTS gaining .gitignore — the alternative hides a nondeterministic runtime artifact from the index instead of keeping it out of a harness whose whole claim is reproducibility"

patterns-established:
  - "A gate whose input can be unavailable raises a named exception rather than reporting an empty result, and both failure shapes of the underlying tool are covered because only one of them is an error code"
  - "The mutation sandbox is a faithful copy of the git INDEX as well as of the files"

requirements-completed: [REQ-11]

duration: 30min
completed: 2026-08-04
---

# Phase 04 Plan 02: Packaging metadata and the licence Summary

**This repo shipped an MIT claim with no MIT text for three phases; it now ships the canonical text, declares it the way setuptools 77+ wants, has decided what a published sdist contains — and carries a gate that goes red in both directions, watched failing against the real tree rather than only against a synthetic one.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-08-04T23:27Z
- **Completed:** 2026-08-04T23:57Z
- **Tasks:** 3 (task 3 split RED/GREEN)
- **Files modified:** 5 (3 created, 2 modified) — 878 insertions, 4 deletions

## Task Commits

1. **Task 1: LICENSE + PEP 639 metadata** — `7220a13` (feat)
2. **Task 2: URLs, classifiers, MANIFEST.in** — `3fffc77` (feat)
3. **Task 3 RED: the gate** — `53f2ca6` (test)
4. **Task 3 GREEN: the sandbox harness** — `c8b753d` (feat)

## Accomplishments

- `LICENSE` (21 lines) — the canonical SPDX MIT text, unedited, `Copyright (c) 2026 Dan Johnson`. `git ls-files | grep -c LICENSE` → **1**.
- `pyproject.toml` — `license = { text = "MIT" }` → `license = "MIT"` + `license-files = ["LICENSE"]`, `[build-system]` floor 68 → 77, six classifiers each with what backs it named, four project URLs. **Exactly two lines removed** relative to `b0a272f`, as required; all six load-bearing comment fragments still `grep -F` clean.
- `MANIFEST.in` (40 lines) — eight `prune` lines, zero `exclude` lines.
- `tests/test_packaging_metadata.py` (651 lines) — 6 shipped-tree tests, 13 corruption tests, 19 total. Every rule is a pure function; every one has been watched failing.
- `scripts/mutation_check.py` — two `SANDBOX_CONTENTS` entries, `status.json` in `_IGNORE`, and a git index in `build_sandbox()`.

## The licence gate, watched failing against the real tree

`license = "MIT"` was temporarily edited to `license = "Apache-2.0"` in the real `pyproject.toml`. `pytest tests/test_packaging_metadata.py -q` → **4 failed, 15 passed**, exit 1. The headline failure, verbatim:

```
AssertionError: pyproject.toml declares 'Apache-2.0' in [project] license, but the
shipped LICENSE is the MIT text. The metadata moved and the file did not
assert "pyproject.toml declares 'Apache-2.0' in [project] license, but the shipped
LICENSE is the MIT text. The metadata moved and the file did not" is None
```

and, from the declaration rule one test up:

```
AssertionError: assert 'Apache-2.0' == 'MIT'
  - MIT
  + Apache-2.0
```

**Two of the four failures were an unplanned bonus and worth recording.** `_corrupt_line` refused to run:

```
AssertionError: no line 'license = "MIT"' to corrupt — the real file moved out from
under this test
```

That is the `_corrupt` idiom from `test_support_matrix.py` doing its job one level up: a corruption test that silently corrupts nothing would assert only that the rule passes on a healthy tree, which is already covered. So the corruption harness itself fails loudly when the shipped file moves.

After reverting: `grep -qx 'license = "MIT"' pyproject.toml` succeeds and the run is **19 passed** in 0.04s.

## The sdist, observed

Built with `setuptools.build_meta.build_sdist` in a `mktemp -d` throwaway venv (setuptools 83.0.0), from `git ls-files --cached --others --exclude-standard`. **No `SetuptoolsDeprecationWarning`. No `warning: no previously-included files`.** Nothing from `tests/`, `config/`, `docs/`, `scripts/`, `deploy/`, `hooks/`, `served/` or `.planning/`.

The full file list, 27 entries:

```
boty/  boty/__init__.py  boty/browser.py  boty/cli.py  boty/config.py
boty/fetch.py  boty/fixtures.py  boty/models.py  boty/monitor.py
boty/notify.py  boty/pacing.py  boty/parse.py  boty/retailers.py  boty/status.py
bot_y.egg-info/  bot_y.egg-info/PKG-INFO  bot_y.egg-info/SOURCES.txt
bot_y.egg-info/dependency_links.txt  bot_y.egg-info/entry_points.txt
bot_y.egg-info/requires.txt  bot_y.egg-info/top_level.txt
LICENSE  MANIFEST.in  PKG-INFO  README.md  pyproject.toml  setup.cfg
```

The PKG-INFO licence fields, which are the point of the whole exercise:

```
Metadata-Version: 2.4
License-Expression: MIT
License-File: LICENSE
```

Measured fact 2 confirmed end to end: the PEP 639 form emits the expression *and* the file reference, with no warning.

## The non-repo question, as shipped

**Option 3 was taken: give the sandbox a git index.** Options 1 (report an absence) and 2 (skip, following `tests/test_identity_check.py` § `needs_repo`) were rejected in writing, in the module docstring of `tests/test_packaging_metadata.py`, so the next person meets the argument before the code.

Both halves were watched failing. With the two `git init` / `git add -A` lines temporarily removed from `build_sandbox()`, `scripts/mutation_check.py` exited 2:

```
mutation check: HARNESS ERROR
baseline FAILED in the unmutated sandbox (pytest exit 1: tests failed).
Without a passing baseline every 'mutation caught' below would really be
'sandbox broken', and this check would report success while proving nothing.
```

with **exactly one** failing test, and this is the observation the whole decision rests on:

```
E  test_packaging_metadata.NotATrackedTree: git ls-files exited 128 in
   /tmp/boty-mutation-xy4is_6v: fatal: not a git repository (or any of the parent
   directories): .git. The sdist prune rule has no input, and reporting no unpruned
   directories here would make it pass by not running.

tests/test_packaging_metadata.py:374: NotATrackedTree
=========================== short test summary info ============================
SKIPPED [1] tests/test_identity_check.py:51: not a git checkout (mutation sandbox)
SKIPPED [1] tests/test_identity_check.py:86: not a git checkout (mutation sandbox)
SKIPPED [1] tests/test_identity_check.py:94: not a git checkout (mutation sandbox)

1 failed, 456 passed, 3 skipped in 5.58s
```

One observation proves three things at once: the loud-failure path fires, it fires with a message naming the cause, and the three identity-check skips come straight back the moment the index is gone. Had the rule reported an absence instead, that run would have been **457 passed, 3 skipped** and entirely green.

## The `SANDBOX_CONTENTS` entry, watched being load-bearing

With `"LICENSE"` temporarily removed from the tuple, `scripts/mutation_check.py` exited 2 with the same `HARNESS ERROR` header and a **9 failed, 451 passed** baseline — every failure in `tests/test_packaging_metadata.py`, reading `LICENSE` off a sandbox root that is the temp directory rather than the repository:

```
FAILED tests/test_packaging_metadata.py::test_the_repo_ships_the_licence_text_its_metadata_declares
FAILED tests/test_packaging_metadata.py::test_every_declared_licence_file_exists
FAILED tests/test_packaging_metadata.py::test_the_licence_file_is_the_licence_the_metadata_names
FAILED tests/test_packaging_metadata.py::test_the_licence_names_a_copyright_holder_and_a_year
FAILED tests/test_packaging_metadata.py::test_a_metadata_licence_swap_is_caught
FAILED tests/test_packaging_metadata.py::test_a_gutted_licence_file_is_caught_from_the_other_side
FAILED tests/test_packaging_metadata.py::test_a_licence_file_with_another_licences_title_is_caught
FAILED tests/test_packaging_metadata.py::test_the_deprecated_table_form_is_not_a_declaration
FAILED tests/test_packaging_metadata.py::test_a_licence_with_no_copyright_line_reports_nothing_found
9 failed, 451 passed in 9.04s
```

With the file byte-identical to its intended state afterwards (`cmp` clean), re-run standalone:

```
mutation check: 8 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (460 passed in 8.83s)
mutation check: 8/8 mutations caught
```

## The sandbox's counts, before and after — and a correction to the plan's numbers

| sandbox | result | suite time |
|---|---|---|
| before the git index (HEAD `5e57158`) | **438 passed, 3 skipped** | 5.9 s / 6.1 s |
| after the git index + this plan's 19 new tests | **460 passed, zero skipped** | 9.1 s / 9.2 s |

**The plan predicted `413 passed, 3 skipped` → `416 passed`.** Those absolute numbers were measured before 04-01 landed 22 tests, so the tree today starts 25 higher and this plan adds 19 more. **The load-bearing claim held exactly:** three tests un-skipped and nothing else changed — 438 + 3 + 19 = 460, and the removed-index run above independently confirms it at `1 failed, 456 passed, 3 skipped` (= 460).

The three that un-skipped, all `@needs_repo` in `tests/test_identity_check.py`:

- `test_the_scan_covers_every_tracked_file_not_just_the_fixtures`
- `test_the_repo_is_clean_right_now`
- `test_the_tracked_hook_exists_and_runs_the_staged_scan`

**The third passes only because 04-01 put `"hooks"` into `SANDBOX_CONTENTS`.** It asserts `hooks/pre-commit` exists relative to its own parent, which inside the sandbox is the temp directory. `"hooks"` was confirmed present in the tuple *before* the index was added, exactly as the plan required; without it this would have been `1 failed, 415 passed` and a `HarnessError`. This plan's git index is load-bearing on 04-01's tuple entry, not merely ordered after it.

## The cost, measured and accepted — do not "fix" this by removing the git index

The sandbox suite went from **~6.0 s to ~9.2 s**, a delta of **~3.2 s per sandbox**. `main()` builds nine sandboxes (one baseline + eight mutations), so `make verify`'s `mutation` stage gains roughly **+29 seconds**, on every run, on every contributor's machine, and in 04-04's CI job.

**`git init` plus `git add -A` are not the cost.** The entire `build_sandbox()` call — the whole copy loop *and* both git commands — measures **0.09 s**. The delta is the un-skipped identity scan walking every tracked file inside the sandbox. That is a real strengthening at a real price: the identity guard's scope test is exactly the kind of thing that should run wherever the suite runs, and it had been silently not running in one of the two places this suite executes.

This is expected and accepted. It is written here so that a contributor or 04-04 meeting a slower CI job finds the reason instead of concluding the index is dead weight — deleting it restores the vacuous-green hole this plan exists to close.

## `_IGNORE` gained `"status.json"`

`git add -A` in a directory with no `.gitignore` stages everything the copy loop brought in. Differencing the sandbox index against the real repo's `git ls-files` left exactly one entry: `served/boty/status.json`. It is `.gitignore`d here, but `.gitignore` is not in `SANDBOX_CONTENTS`, so git inside the sandbox has never heard of it.

That matters because the newly un-skipped `test_the_repo_is_clean_right_now` runs the identity scan over it *inside the sandbox*. It is clean today, but it is a runtime artifact rewritten by every live `make verify`, and its `reason` fields are populated from retailer-failure exception text — the string class that can pick up a local path or a host. A red `make verify` sourced from a file in neither the repository nor the diff is the least attributable failure this harness could produce.

**Why the sandbox's ignore set and the repo's `.gitignore` are allowed to differ:** they answer different questions. `.gitignore` says "do not track this in the repository". `_IGNORE` says "the suite does not read this, so a faithful copy does not need it". They overlap without either containing the other. The one place they must agree is a file the copy loop reaches that the repo does not track — and that set has exactly one member. Nothing reads the sandbox's copy: every test touching `status.json` writes to `tmp_path`.

The alternative — adding `.gitignore` to `SANDBOX_CONTENTS` — was considered and rejected in the comment: it hides a nondeterministic runtime artifact from the index rather than keeping it out of a harness whose whole claim is reproducibility, and it widens the set of paths 04-01's citation rule can resolve, which is that gate's decision to take.

The check asserts by **set difference**, not by naming the file:

```
sandbox is a git tree with 71 tracked files, none of them strays
```

## `scripts/mutation_check.py` — the diff, and 04-01's entries

```
 scripts/mutation_check.py | 87 +++++++++++++++++++++++++++++++++++++++++++++--
 1 file changed, 85 insertions(+), 2 deletions(-)
```

Four changes, as specified: the two tuple entries with a comment paragraph each, `"status.json"` in `_IGNORE` with its comment, and the `build_sandbox` git-index block with its comment (plus the small `_git_or_harness_error` helper that keeps the two argv lists literal and turns a git failure into a `HarnessError` carrying git's stderr). The two deletions are the tuple's last line rewrapped and the `_IGNORE` one-liner reformatted to multi-line — no function other than `build_sandbox` changed, and neither the tuple nor the comment block was restructured.

**04-01's entries survived unmodified.** The only line in the diff mentioning either:

```
-    "Makefile", "README.md", "CONTRIBUTING.md",
+    "Makefile", "README.md", "CONTRIBUTING.md", "LICENSE", "MANIFEST.in",
```

`"hooks"` does not appear in the diff at all — its line is untouched — and both of 04-01's comment paragraphs are intact.

The tuple now reads:

```python
("boty", "tests", "scripts", "config", "served", "docs", "hooks", "pyproject.toml",
 "Makefile", "README.md", "CONTRIBUTING.md", "LICENSE", "MANIFEST.in")
```

## Final verification

| Check | Result |
|---|---|
| `pytest tests/test_packaging_metadata.py -q` | **19 passed** (6 shipped-tree, 13 corruption) |
| `pytest tests/ -q` | **460 passed** |
| `mypy` | Success: no issues found in 17 source files |
| `scripts/mutation_check.py` standalone | `mutation check: 8/8 mutations caught`, no HARNESS ERROR |
| `make verify-offline` | `VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)` |
| `git ls-files \| grep -c LICENSE` | **1** |
| `git diff -U0 b0a272f -- pyproject.toml \| grep -c '^-[^-]'` | **2** |

## Decisions Made

- **`_project_table` reads multi-line arrays.** The plan specified single-line scalars and single-line arrays only, on the grounds that the `[project]` table uses nothing else. Task 2 then added a six-entry `classifiers` list that spans lines, and `_forbidden_classifiers` has to read it. The parser was widened deliberately with the reason in its docstring, plus a `_strip_comment` scanner so an inline `#` outside a quoted string cannot leak into a value. The narrow-on-purpose principle survives: it parses the two shapes this repository writes and nothing else.
- **`PACKAGED_DIRECTORY` rather than the plan's `UNPACKAGED_TOP_LEVEL`.** The rule is "every tracked top-level directory *other than* `boty` must carry a `prune` line", which is one name for a positive fact and a note. Naming the constant for the thing it holds (`"boty"`) and putting the rule in its `#:` comment reads better than naming it for the complement it does not contain.
- **The three sandbox behaviours in `<behavior>` are verified by standalone commands, never by a test in this suite.** A test here that called `build_sandbox()` would build a sandbox inside the sandbox, whose suite would build another, without bound. This is stated in the module docstring under `WHAT IS DELIBERATELY *NOT* TESTED IN THIS FILE` so nobody adds one later.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The specified `[project]`-table parser could not read this plan's own classifiers list**

- **Found during:** Task 3, writing `_forbidden_classifiers`
- **Issue:** The plan specified `_project_table` as single-line values only. Task 2's `classifiers` list spans eight lines, so the rule that guards a measured build error would have read `[` and reported nothing — a gate passing by not running, in a file whose entire subject is gates that pass by not running.
- **Fix:** `_project_table` accumulates a bracketed value until the brackets balance, with the reason and the two affected keys named in its docstring; `_strip_comment` handles `#` inside quoted strings.
- **Verification:** `test_a_license_classifier_is_reported` asserts the rule returns `["License :: OSI Approved :: MIT License"]` against a corrupted copy — watched failing before it was written to pass.
- **Committed in:** `53f2ca6`

**2. [Rule 1 - Correction] The plan's sandbox counts were measured against a pre-04-01 tree**

- **Found during:** Task 3, taking the "before" measurement the plan requires
- **Issue:** The plan states `413 passed, 3 skipped` → `416 passed` as the expected outcome and says "two or four is a finding". The tree at `5e57158` reports **438 passed, 3 skipped** — 04-01 landed 22 tests after fact 9a was measured. An executor holding the absolute numbers as the criterion would have escalated a false alarm.
- **Fix:** The criterion was read as what it actually asserts — **three** tests un-skipping, nothing else changing — and that held exactly, confirmed twice (460 passed with the index; 1 failed / 456 passed / 3 skipped without it). Both sets of numbers are recorded above.
- **Committed in:** `c8b753d`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 correction, 0 architectural)
**Impact on plan:** None on scope. No file outside this plan's ownership was touched — `README.md`, `docs/` and `CONTRIBUTING.md` are all absent from this plan's diff.

## Issues Encountered

None requiring escalation. The tree was legitimately red between `53f2ca6` (the gate) and `c8b753d` (the harness that lets it run inside the sandbox) — that is the RED/GREEN split, and the RED was observed and recorded rather than assumed: **11 failed, 446 passed, 3 skipped**, `HARNESS ERROR`, before the sandbox changes landed.

## Known Stubs

None. Every rule in `tests/test_packaging_metadata.py` runs against the shipped tree and against a corrupted copy of it, and `_tracked_top_level_dirs` has a positive control (`test_the_prune_rule_answers_for_real_inside_a_git_tree`) so `NotATrackedTree` cannot be raised unconditionally while both raise-tests still pass.

## User Setup Required

None.

## Next Phase Readiness

**Handoff to 04-05 (the release), three things:**

1. **The sdist above was observed with `setuptools.build_meta.build_sdist` in a scratch venv, not with `python -m build`.** 04-05 runs the real tool and must re-assert the file list there.
2. **`twine check dist/*` needs `twine>=6.1`.** The PEP 639 form emits `Metadata-Version: 2.4` (confirmed in the PKG-INFO above) and an older twine rejects it outright.
3. **`Development Status :: 4 - Beta` was deliberately left out**, and so was the `Changelog` project URL. Development status is a statement about the version, which is still `0.1.0` and which this plan did not touch; the Changelog URL would 404 until `CHANGELOG.md` exists. Both land with the 1.0.0 bump, in the same commit as the file they describe.

**Handoff to 04-04 (CI):**

- `SANDBOX_CONTENTS` now carries `CONTRIBUTING.md`, `hooks`, `LICENSE` and `MANIFEST.in`, so **04-04 adds only `.github`** — in the same commit as the workflow file it names, because `build_sandbox()` raises `HarnessError` for an entry with no file behind it.
- **The sandbox is a git tree now.** 04-04's `prune .github` line satisfies a rule that genuinely runs inside the sandbox rather than passing there for free — `test_every_unpackaged_top_level_directory_is_pruned_from_the_sdist` will go red for a missing `.github` line in both places the suite executes.
- **The `mutation` stage is ~29 s slower than it was**, for the reason written out above. Budget for it; do not remove the index to get it back.

**Handoff to 04-03 (the linter):** `tests/test_packaging_metadata.py` is fully annotated but `[tool.mypy] files = ["boty", "scripts"]` still excludes `tests/`, so it is not type-checked. It carries zero line-numbered citations.

## Self-Check: PASSED

All five files claimed above exist on disk (`LICENSE`, `MANIFEST.in`, `tests/test_packaging_metadata.py`, `pyproject.toml`, `scripts/mutation_check.py`); all four commit hashes (`7220a13`, `3fffc77`, `53f2ca6`, `c8b753d`) resolve in `git log`.

---
*Phase: 04-open-source-ready*
*Completed: 2026-08-04*
