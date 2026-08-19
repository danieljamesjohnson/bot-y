---
phase: 06-claims-with-gates-under-them
plan: 03
subsystem: workflow-gates
tags: [req-19, github-actions, supply-chain, directory-rules, red-watch, no-mutation]

requires:
  - phase: 06-claims-with-gates-under-them
    plan: 02
    provides: "the 701-test baseline this plan raises to 711, and the 20-mutation registry it deliberately leaves at 20"
  - phase: 04-open-source-ready
    provides: "`tests/test_ci_workflow.py` itself — the two views (`_raw` / `_code`), `_pr_triggered_privilege`'s directory-rule shape, `NoTriggerBlock`'s raise-rather-than-report precedent, `_corrupt`'s derive-don't-retype idiom, and `TRUSTED_ACTION_OWNERS`' enumerated-pin convention"
provides:
  - "`DIRECTORY_RULES` — criterion 3's own four words (`pin`, `exit-code`, `timeout`, `runner`) mapped to four functions of `dict[str, str]` returning filename-prefixed findings"
  - "`_directory_unpinned_actions` / `_directory_flattened_exit_codes` / `_directory_missing_timeouts` / `_directory_floating_runners` — wrappers over the existing rules, fed `_all_workflow_texts()`"
  - "`_bad_timeouts` — the timeout family extracted from the two tests that had inlined it, bound copied verbatim"
  - "`UnreadableWorkflow` + `_parsed` — a workflow this gate cannot read raises, naming the file, instead of reporting clean through an empty mapping"
  - "`RED_WATCH_NAME` + `NONCOMPLIANT_WORKFLOW` — one definition of the deliberately broken third workflow, shared by the in-suite red-watch and the on-disk observation"
  - "`test_the_red_watch_workflow_is_not_in_this_directory` — the probe's removal as a permanent gate rather than a procedure"
affects: [06-04, 06-06]

tech-stack:
  added: []
  patterns:
    - "Key a gate to the DIRECTORY, never to a filename — a hand-maintained list of names is coverage that stops at the last name somebody remembered"
    - "Generalise by wrapping, not rewriting: the defect was what the rules were handed, not what they judged"
    - "Measure the gap BEFORE building the gate, with the same command, so the red afterwards is attributable"
    - "A gate reports every family at once — a gate that reveals a quarter of the problem per run is one people learn to distrust"
    - "A criterion's own words become the registry keys, quoted inline, so the count cannot drift by eye"

key-files:
  created: []
  modified:
    - tests/test_ci_workflow.py

key-decisions:
  - "Three of four families WRAPPED, not rewritten — the rules were already correct, measured; only iteration and a filename prefix were missing"
  - "The pin family keeps the RAW view and the exit-code family the comment-stripped one; the shipped tree detects either mistake for free, so the green side is the assertion"
  - "`_bad_timeouts`' bound copied character-for-character from the two tests it was extracted from; `ci.yml`'s test now reads every job instead of the first — a strengthening, noted in a comment"
  - "The on-disk probe names `actions/checkout@v4`, never a third-party owner — the untrusted-owner half is watched in-suite only"
  - "NO MUTATION REGISTERED, and M21-M22 left deliberately unallocated: `apply_mutation` cannot add a file, so the defect is outside the harness by construction"
  - "`REQUIREMENTS.md` not edited — REQ-19 stays Pending for 06-06 to close by measuring what landed"
  - "`06-PATTERNS.md` and `06-PLAN-OUTLINE.md` name a function that does not exist; recorded as a measurement note, neither document edited"

metrics:
  duration: 38min
  tasks: 3
  files: 1
  completed: 2026-08-10
---

# Phase 6 Plan 03: A Workflow File Added Under `.github/workflows/` Is Now Covered Summary

Criterion 3's four rule families — pin, exit-code, timeout, runner — were re-keyed from two
hard-coded filenames to the directory, so a third workflow file is guarded on arrival; the gap was
measured going green first (**exit 0, 701 passed**) and the gate then watched going red on the
identical file and command (**exit 1, 2 failed, 709 passed**), naming all four families and the file.

## The pre-gate measurement — the defect, executed on this tree

`NONCOMPLIANT_WORKFLOW` written into the real `.github/workflows/zzz-red-watch.yaml`, carrying one
violation per family (`uses: actions/checkout@v4`, `run: make verify-offline || true`, no
`timeout-minutes`, `runs-on: ubuntu-latest`), with the constant in place and **no directory rule in
the tree**. Verbatim:

```
PRE-GATE exit 0
701 passed in 10.78s
git: (clean)
```

Seven hundred and one tests watched a deliberately non-compliant workflow arrive in the one
directory in this repository that runs on somebody else's computer holding this repository's token,
and not one of them said anything. The file was removed in a `finally`; `git status --porcelain`
reported only the modified test file.

The plan's F1 measured the same shape at **667 passed** against the pre-06-01 tree. 06-01 and 06-02
raised it to 701. The number moved; the verdict did not.

## The post-gate observation — same file, same command, red

```
POST-GATE exit 1
FAILED tests/test_ci_workflow.py::test_every_workflow_in_this_directory_passes_every_directory_rule
FAILED tests/test_ci_workflow.py::test_the_red_watch_workflow_is_not_in_this_directory
2 failed, 709 passed in 10.48s
git: (clean)
```

The failure names the file, and — after the correction recorded below — names **all four families**
in one assertion:

```
E  AssertionError: {'pin': ["zzz-red-watch.yaml: actions/checkout: ref 'v4' is not a 40-character
   commit SHA"], 'exit-code': ["zzz-red-wa...ue'"], 'timeout': ['zzz-red-watch.yaml: sweep:
   timeout-minutes=None'], 'runner': ['zzz-red-watch.yaml: ubuntu-latest']}
E    {'exit-code': ['zzz-red-watch.yaml: an or-fallback that discards the exit '
E                   "zzz-red-watch.yaml: a pipe on the line invoking make: '- run: "
E     'pin': ["zzz-red-watch.yaml: actions/checkout: ref 'v4' is not a 40-character "...

E  AssertionError: zzz-red-watch.yaml is in /home/dan/CodeProjects/pokemongoplusplus/.github/workflows.
   It is a deliberately non-compliant workflow written for one measurement and must never survive
   it — delete it.
```

**The file was removed and the tree is clean.** `test -z "$(git status --porcelain .github/workflows/)"`
→ `workflows directory clean`, asserted after every run and enforced from now on by
`test_the_red_watch_workflow_is_not_in_this_directory`.

Green before, red after, same file, same command, and the only thing that changed between them is
this plan's gate. **F7 was honoured: `pytest` and nothing else ran while that file was on disk** — no
`make verify`, no `make verify-offline`, no `make mutation`, so no sandbox was ever built around it
and no `HarnessError` was manufactured.

## `make verify-offline` — the gate

Exit **0**, on a clean tree with the probe gone.

```
identity check: PASS — 193 file(s), no host identity found
All checks passed!                                        (lint)
711 passed in 10.58s                                      (tests)
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 20 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (710 passed, 1 skipped in 10.69s)
mutation check: 20/20 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

| | before this plan | after |
|---|---|---|
| `pytest tests/` | 701 passed | **711 passed** (+10) |
| `tests/test_ci_workflow.py` | 67 tests | **77 tests** (+10) |
| mutation ratio | 20/20 | **20/20 — unchanged, by design** |
| highest registered ident | M20 | **M20** |

`make verify` (live) was **not run**. It is not this plan's gate, no acceptance here depends on it,
and its three known failure classes are recorded in STATE.md as needing their own plan. **No CI run
was triggered.**

## Why this plan registers NO mutation, and why the M21-M22 gap is deliberate

The planning context reserved **M21-M22** for this plan. They are left **unallocated**, and
`scripts/mutation_check.py` is untouched (`git diff --stat 01df41a` names exactly one file,
`tests/test_ci_workflow.py`). Three measured reasons, in full:

1. **`apply_mutation` cannot add a file.** It performs `before.replace(search, replace, 1)` on an
   existing file inside the sandbox. The criterion is about *a workflow file that does not exist
   yet*, so the defect it names is outside the harness's reach **by construction**, not by
   oversight.
2. **Any workflow mutation a directory rule would catch is already caught by a per-file test that
   predates this plan.** All four families are asserted per-file on both shipped workflows and both
   are clean. A mutation such as `runs-on: ubuntu-24.04` → `ubuntu-latest` in `release.yml` would
   die against `test_the_publish_workflow_runs_on_a_pinned_image_within_a_time_limit`, which existed
   before 06-03 — it would raise the ratio while proving nothing this plan built. That is the exact
   opposite of M6/M7's recorded reasoning, where a second mutation exists precisely *because* it
   proves a different disjunct load-bearing.
3. **The red-watch available here is stronger than a mutation.** A mutation is a synthetic edit
   inside a temporary copy. This plan's red-watch is the criterion executed literally: a real file,
   in the real directory, turning the real suite red, against a green verdict measured on the same
   command minutes earlier.

**So the ident sequence carries a deliberate gap at M21-M22.** 06-04 and 06-05 should keep their own
reservations rather than renumbering into it, and **06-06 must not read the gap as a lost mutation**.
A mutation that SURVIVES is never explained away; a mutation that cannot exist is recorded as not
existing.

## What was built

**Four directory rules, each a pure function of `dict[str, str]` returning findings prefixed with
the filename** — `_pr_triggered_privilege`'s shape, copied rather than reinvented. Three of the four
wrap an existing rule and change nothing about its judgement:

| Family | Function | Wraps | View |
|---|---|---|---|
| `pin` | `_directory_unpinned_actions` | `_unpinned_actions(_action_pins(text))` | **RAW** — needs the trailing `# v7.0.1` |
| `exit-code` | `_directory_flattened_exit_codes` | `_flattening(_code(text))` | **comment-stripped** |
| `timeout` | `_directory_missing_timeouts` | `_bad_timeouts(_parsed(name, text))` | parsed |
| `runner` | `_directory_floating_runners` | `_floating_runners(_parsed(name, text))` | parsed |

`DIRECTORY_RULES` keys them on criterion 3's own four words, with the ROADMAP sentence quoted inline,
and `test_the_four_rules_the_criterion_names_are_the_four_directory_rules` pins the key set both
ways.

**The green side is the assertion, not a formality.** A pin wrapper reading `_code` would strip
`# vX` off all seven shipped pins and report every one as comment-less; an exit-code wrapper reading
raw text would match the `|| true` inside `ci.yml`'s own decision record. Either mistake reddens
`test_every_workflow_in_this_directory_passes_every_directory_rule` against the real tree
immediately. That is written into the module docstring and into the test's own docstring.

**`_bad_timeouts` extracted, strengthening only.** The timeout family was the one with no function at
all — it had been inlined in two tests. The bound is copied character-for-character
(`isinstance(t, int) and 0 < t <= 30`), the finding string is the one the release test already
produced, and both tests keep their names. For `release.yml` the rewrite is behaviour-identical; for
`ci.yml` it is strictly stronger, because the old body read `next(iter(_jobs(...).values()))` — the
first job only. That difference is called out in a comment so a reviewer can see it is a
strengthening and not a weakening.

**`UnreadableWorkflow` + `_parsed`.** `NoTriggerBlock`'s precedent one level out: `_jobs({})` is
`{}`, so a directory rule handed an unparseable file would iterate nothing and report nothing — a
clean verdict on a directory it never read. Both raise branches are exercised (not-a-mapping, and
`yaml.YAMLError`) across four shapes: empty, whitespace, a bare scalar, a list, and
`jobs: [unclosed`.

**Seven new red-watches**, every corruption derived from `NONCOMPLIANT_WORKFLOW` or the real files
via a third `_corrupt`-family helper, never retyped:

| Test | Watches |
|---|---|
| `test_a_non_compliant_workflow_added_to_this_directory_is_reported_by_every_rule` | criterion 3 as a test — all four families report the file **by name**, with the specific violation, **and the clean side asserted in the same test** |
| `test_every_directory_rule_reports_every_file_rather_than_only_the_first` | a `return` inside the loop — the criterion's defect one iteration along |
| `test_the_pin_rule_still_reads_the_raw_view_and_still_wants_the_version_comment` | the half a comment-stripped wrapper would destroy |
| `test_an_untrusted_action_owner_in_a_new_workflow_is_reported_across_the_directory` | the `tj-actions` half, **in-suite only** |
| `test_a_timeout_outside_the_bound_is_reported_not_only_a_missing_one` | `timeout-minutes: 360` — presence is not the rule |
| `test_a_workflow_this_gate_cannot_parse_raises_rather_than_reporting_it_clean` | the raise, with the filename in the message |
| `test_the_red_watch_workflow_is_not_in_this_directory` | the probe's removal, permanently |

**No existing test deleted, renamed or weakened — proven by command, not promised.**

```
01df41a: 67 -> now 77; removed or renamed: []
HEAD:    70 -> now 77; removed or renamed: []
```

## Deviations from Plan

### 1. [Measurement corrects the plan] The on-disk red-watch produced TWO failures, not "at least five"

The plan predicted the four families would fail through
`test_a_non_compliant_workflow_added_to_this_directory_is_reported_by_every_rule`, plus
`test_every_workflow_in_this_directory_passes_every_directory_rule` and the removal gate. Measured:
**2 failed, 709 passed.** Two reasons, both correct behaviour:

- **`test_a_non_compliant_workflow_added_to_this_directory_is_reported_by_every_rule` is on-disk
  invariant, by construction.** It builds `{**_all_workflow_texts(), RED_WATCH_NAME: NONCOMPLIANT_WORKFLOW}`.
  When the probe *is* on disk, `_all_workflow_texts()` already contains it under the same name with
  the same text, so the dict is identical either way and the test asserts exactly what it asserts on
  a clean tree — and passes. It is a statement about the rule set, not about the filesystem. That is
  the right property for it to have; it means the in-suite red-watch is not quietly dependent on a
  file nobody will ever create again.
- **The failing shipped-tree test originally reported one family and stopped** — see deviation 2.

The plan's own instruction was followed: *"Record what actually failed, not what was expected to."*

### 2. [Rule 2 — missing critical functionality] The shipped-tree test now reports every family at once

**Found during:** Task 3, from the first on-disk observation.
**Issue:** `test_every_workflow_in_this_directory_passes_every_directory_rule` asserted **inside**
the family loop, so it failed on `pin` and stopped. A contributor adding a workflow that violated
all four families would have been told about one, fixed it, re-run, and been told about the next.
The plan's own failure-shape guidance says coverage a contributor cannot attribute is coverage they
will work around; a gate that reveals a quarter of the problem per run is the same defect in a
different coat — and it is a close cousin of `test_every_directory_rule_reports_every_file_rather_than_only_the_first`,
which this plan wrote a test for at the *rule* level while leaving it at the *test* level.
**Fix:** collect findings across all four families, assert once. The on-disk observation was then
re-run and now reports all four families and the filename in a single assertion (quoted above).
**Files modified:** `tests/test_ci_workflow.py`. **Commit:** `8a29eb0`.

### 3. [Strengthening] `RULES` gained six entries, not the five the plan enumerated

The plan said *"add all five new functions to `RULES` (the four families and `_parsed`)"*.
`_bad_timeouts` is also a new rule function, and leaving it out would be precisely the silent escape
F4 warns about — this criterion's defect one level up, inside the file fixing it. It is in the tuple,
with a comment saying why the count differs from the plan.

### 4. [Procedure] The on-disk driver ran three times, not once

Once for the pre-gate measurement (Task 1, exit 0), once for the first post-gate observation (Task 3,
exit 1, one family reported), and once after deviation 2's fix to record the final gate's behaviour.
Every run was `pytest` and nothing else, every run removed the file in a `finally`, and
`git status --porcelain` was asserted clean after each. F7 was never at risk: no sandbox was built at
any point while the file existed. `NONCOMPLIANT_WORKFLOW`'s own comment says "written to disk exactly
once by 06-03's observation" — read that as *by 06-03's observation only*, which is what it is there
to prevent anyone else from doing.

### 5. [Correction to two planning documents, carried for 06-06 — F2]

**`06-PATTERNS.md` and `06-PLAN-OUTLINE.md` both name the exit-code rule `_flattened_exit_codes`.
No such function exists.** It is **`_flattening`**. Confirmed against the tree at 01df41a and at
HEAD. Neither document was edited, and no requirement text was touched — this is a measurement note
for 06-06 to carry, in the same way 06-02 recorded `06-CONTEXT.md`'s inaccurate claim about
`_extraction_mismatch` rather than editing it away. (The new *wrapper* is named
`_directory_flattened_exit_codes`, which is close enough to be a future trap: the underlying rule is
still `_flattening`.)

### 6. [Premise moved, verdict did not — F1]

F1's baseline was `667 passed`; this tree measured `701 passed` for the identical probe and command,
because 06-01 and 06-02 landed first exactly as the plan anticipated. The plan said to re-verify
counts against the tree rather than re-derive them, and that is what the numbers above are.

### 7. [F9 held] `.github/workflows/release.yml` needed no edit

Measured clean on all four families before and after. `git diff --stat 01df41a` names exactly one
file, `tests/test_ci_workflow.py`. **No directory rule bit on a shipped workflow, so nothing was
fixed and nothing was exempted.** The contingency in `files_modified` did not fire.

## What was NOT done, deliberately

- **`REQUIREMENTS.md` is not edited. REQ-19 stays Pending.** This plan ships the workflow half;
  06-04 ships the `CHANGELOG.md` half; **06-06 closes REQ-19 by measuring what landed.** That is
  04-05's and 05-01's recorded precedent.
- **No mutation registered; M21-M22 unallocated.** See above.
- **No file under `boty/` or `scripts/` was read or edited. No new dependency** — the one new import
  is `collections.abc.Callable`, stdlib, placed in the stdlib import block for ruff's isort rule.
- **No third-party action owner was ever written to disk.** The untrusted-owner red-watch derives
  `some-vendor/checkout@<40 zeros>` from the same constant with `.replace()` and lives in memory
  only. Writing a plausible third-party publisher into a public repository's real workflow
  directory, even for the seconds a pytest run takes, to test a rule about a supply-chain attack, is
  not a trade this project makes.
- **`make verify` (live) was not run and no CI run was triggered.**

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change at a trust boundary.
The one file this plan writes to disk is a workflow with `contents: read`, no pull-request trigger,
no secrets and no third-party action, and it does not survive the command that writes it.

## For the next plan

- **06-04 takes REQ-19's `CHANGELOG.md` half.** It must handle a hazard this plan did **not** have:
  `.github` is already in `SANDBOX_CONTENTS` and `REPO_ROOT` resolves to the sandbox root, so these
  rules read the sandbox's copy with no widening and no skip. `CHANGELOG.md` and `.planning/` are a
  different story — that is 06-04's and 06-05's `HarnessError` risk, not this plan's, and nothing
  here mitigated it for them.
- **Do not renumber into M21-M22.** The gap is deliberate and argued above.
- **The exit-code rule is `_flattening`.** Two planning documents say otherwise.
- **`tests/test_ci_workflow.py` is now 77 tests and 1,756 lines** (measured, `wc -l`), covering two shipped workflows
  and the directory they live in. A third real workflow added to this repository is now guarded on
  arrival, and it will be told so by name.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | `8ebc92e` | the gap measured at exit 0 / 701 passed, then the four families re-keyed to the directory |
| 2 | `1a0ac18` | six red-watches plus the removal gate; zero test names removed against 01df41a |
| 3 | `8a29eb0` | every family reported at once, from the on-disk observation |

## Self-Check: PASSED

- `tests/test_ci_workflow.py` — FOUND (1,756 lines, 77 `test_*` functions)
- `.planning/phases/06-claims-with-gates-under-them/06-03-SUMMARY.md` — FOUND
- commits `8ebc92e`, `1a0ac18`, `8a29eb0` — all three FOUND in `git log --all`
- `.github/workflows/zzz-red-watch.yaml` — correctly ABSENT; `git status --porcelain .github/workflows/` empty
- `scripts/mutation_check.py` — unmodified; 20 registered idents, highest `M20`
- `make verify-offline` — exit 0, 711 passed, 20/20 caught

One claim in an earlier draft of this file was wrong and is corrected above: the line count was
written as "~1,470" from memory and measures **1,756**. Recorded rather than quietly fixed, because
this milestone is about not stating what you have not measured.
