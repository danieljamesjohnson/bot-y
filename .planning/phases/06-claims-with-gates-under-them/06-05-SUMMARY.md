---
phase: 06-claims-with-gates-under-them
plan: 05
subsystem: version-binding
tags: [req-20, version, correction-not-a-bump, red-watch, sandbox-skip, two-directional, m25, m26, first-mutation-outside-boty]

requires:
  - phase: 06-claims-with-gates-under-them
    plan: 04
    provides: "the 737-test baseline this plan raises to 759, the 20-mutation registry it raises to 22, `tests/test_changelog.py`'s heading-shape and body gate over the `## [0.2.0]` entry this plan writes, and the `needs_changelog` skip idiom copied here for `needs_state`"
  - phase: 05-a-reading-you-can-locate
    provides: "`tests/test_config.py`'s file-absence skip, on `tests/test_identity_check.py`'s `needs_repo` — the precedent for not widening `SANDBOX_CONTENTS`"
  - phase: 04-open-source-ready
    provides: "`_project_table` / `_string` / `_string_list` / `_corrupt_line` in this same file, and `scripts/release_check.py`'s `_changelog_version`, all borrowed rather than re-implemented"
provides:
  - "`_version_declared` / `_version_in_readme` / `_version_in_changelog` / `_version_in_state` — four readers of one number, each returning a value OR a named absence"
  - "`_version_components` — component-wise normalisation, with the `\"0.21.0\".startswith(\"0.2\")` trap pinned by its own test"
  - "`_version_disagreements` — the single comparator, `pyproject.toml` named authoritative and the direction written down"
  - "`_version_status_disagreement` — the Development Status classifier bound to the version in BOTH directions, so Phase 4's reasoning is executable rather than prose"
  - "`needs_changelog` / `needs_state` — file-presence skips paired with an always-on rule, not a shrug"
  - "`FILE_ABSENT` / `_FileAbsent` — the sentinel that keeps *file absent* distinct from *file present and silent*, because only one of those is not a finding"
  - "M25 and M26 — this repository's first mutations outside `boty/`"
affects: [06-06]

tech-stack:
  added: []
  patterns:
    - "A version is bound to a referent, never voted on: `pyproject.toml` is authoritative and every finding says which record moved"
    - "Compare version component LISTS, never string prefixes — a prefix comparison accepts `0.21.0` for a `v0.2` milestone and looks like it is working"
    - "Absence is a finding: three of four bindings are satisfied by deleting the statement, so every deletion case is watched biting"
    - "Pair every skipping rule with an always-on one whose two files BOTH reach the mutation sandbox — and observe it passing there by name, as a count rather than an inference"
    - "Discover rules by naming convention and pin the discovery; a rule named outside the convention becomes INVISIBLE to the pin rather than reddening it (measured here)"
    - "A corruption derived from the real file rots into a loud `_corrupt_line` failure; a corruption that names a literal line rots into a silent pass or a misleading red"
    - "Roll a version down only against a re-measured absence of tags and uploads, and record the measurement beside the number"

key-files:
  created: []
  modified:
    - tests/test_packaging_metadata.py
    - pyproject.toml
    - README.md
    - CHANGELOG.md
    - scripts/mutation_check.py
    - tests/test_changelog.py

key-decisions:
  - "The roll is the CORRECTION, not a bump — said in `pyproject.toml` beside the version, in the `## [0.2.0]` entry, and here"
  - "All four safety rows re-measured at execution 2026-08-10: 0 tags, 0 refs, 404, 404 — unchanged, so the pre-decided PROCEED branch was taken"
  - "`Development Status :: 5 - Production/Stable` -> `4 - Beta`, argued in place with Phase 4's rejection kept VERBATIM and marked right-for-1.0.0"
  - "The always-on rule is `pyproject` <-> `README`, NOT `pyproject` <-> `CHANGELOG` — the outline's *runs everywhere* claim measured false"
  - "The classifier rule is named `_version_status_disagreement`, not the plan's `_status_version_disagreement`, because a rule outside the `_version_` convention is invisible to the pairing pin — measured, not assumed"
  - "`SANDBOX_CONTENTS` NOT widened; two rules skip and the always-on rule is what makes the skips sound"
  - "M25/M26 registered in the reserved range; the M21-M24 gap is deliberate and stays"
  - "`REQUIREMENTS.md`, `ROADMAP.md` and `.planning/STATE.md` all unedited — REQ-20 stays Pending for 06-06"

metrics:
  duration: 31min
  tasks: 3
  files: 6
  completed: 2026-08-10
---

# Phase 6 Plan 05: `pyproject.toml` Reads 0.2.0 And Cannot Silently Diverge Summary

The gate was written first against a tree that disagreed with itself and went **red on
exactly the binding that was already broken — exit 1, 2 failed, 757 passed**; the roll from
`1.0.0` to `0.2.0` turned the same command **green at exit 0, 759 passed**; four statements
of one version are now bound to `pyproject.toml` as the referent with every rule watched red
in both directions including all three deletion cases; and **M25 and M26 — this repository's
first mutations outside `boty/`** — were observed CAUGHT by name, both by the one version rule
whose two files reach the mutation sandbox.

## The pre-roll red — the divergence, measured on the tree

`pytest tests/ -q` with the gate committed and **nothing rolled**. Verbatim:

```
PRE-ROLL exit 1
FAILED tests/test_packaging_metadata.py::test_the_projects_own_milestone_names_the_declared_version
FAILED tests/test_packaging_metadata.py::test_all_four_statements_of_the_version_agree_right_now
2 failed, 757 passed
```

Both failures carry the same finding:

```
AssertionError: ['.planning/STATE.md states 'v0.2' in its frontmatter milestone but
pyproject.toml declares '1.0.0'. A milestone names a minor line, so it is compared only on
the 2 component(s) it states — and those do not match [1, 0]. Compared as component lists
rather than as a string prefix, because "0.21.0".startswith("0.2") is True']
```

`pyproject.toml` said `1.0.0`. This project's own state file said `milestone: v0.2`. Both
tracked, both this project's statement about itself, disagreeing since the milestone was
scoped — and **757 other tests had nothing to say about it**, because until that commit
nothing offline read either one. That is criterion 5's defect, sitting in a repository whose
entire subject is claims with nothing checking them.

The plan's F4 predicted exactly one red rule (the STATE binding) and the agreement guard
beside it. **Both predicted; nothing else moved.** The two green-on-arrival bindings
(`README`, `CHANGELOG`) and the classifier rule passed before the roll, as F4 said they
would — asserted rather than assumed: `pytest -k "readme or changelog or classifier or
status"` -> `12 passed, 29 deselected`.

The commit carrying that red says so in its subject line — **`TREE IS DELIBERATELY RED`** —
and names Task 2 as what closes it. A silent red commit in a phase about claims with gates
under them would have been the defect committed inside the plan closing it.

## The four safety rows, re-measured at execution

Taken on **2026-08-10, immediately before the roll**, not inherited from Phase 4 and not
inherited from the plan's own planning-time measurement:

| Fact | Measured at execution | Phase 4's record | Plan § F1 |
|---|---|---|---|
| `git tag -l` | **0 tags** | 0 tags | 0 tags |
| `git ls-remote --tags origin` | **0 refs**, exit 0 | 0 refs | 0 refs |
| `https://pypi.org/pypi/bot-y/json` | **HTTP 404** | 404 | 404 |
| `https://pypi.org/pypi/bot-y/1.0.0/json` | **HTTP 404** | 404 | 404 |

**All four unchanged, so the pre-decided PROCEED branch was taken.** No row was NOT
OBTAINED; the network answered every time.

One extra check the plan did not ask for, because "0 refs" and "the remote refused" look
identical in a line count: `git ls-remote --heads origin` was run alongside and returned
`03520af... refs/heads/main` at exit 0. **The remote answered and listed no tags**, rather
than failing quietly into a zero.

Nobody can be pinned to a `1.0.0` that exists, because no `1.0.0` of this package exists
anywhere. **No tag was created, nothing was pushed, nothing was uploaded, and
`make release-check` was not run.**

## The post-roll green — same command, both verdicts

```
POST-ROLL exit 0
(no FAILED lines)
759 passed in 10.83s
```

Red before, green after, same command, and the only thing that changed between them is the
roll and the classifier reversal.

## Both directions, observed on disk

06-04's driver shape, run on the committed tree, each write restored with `git checkout --`
inside a `finally`:

```
--- pyproject moved away from the milestone exit 1
FAILED tests/test_packaging_metadata.py::test_the_readme_publication_instruction_names_the_declared_version
FAILED tests/test_packaging_metadata.py::test_the_changelog_top_release_heading_names_the_declared_version
FAILED tests/test_packaging_metadata.py::test_the_projects_own_milestone_names_the_declared_version
FAILED tests/test_packaging_metadata.py::test_all_four_statements_of_the_version_agree_right_now
['4 failed, 755 passed in 10.87s']

--- the milestone moved away from pyproject exit 1
FAILED tests/test_packaging_metadata.py::test_the_projects_own_milestone_names_the_declared_version
FAILED tests/test_packaging_metadata.py::test_all_four_statements_of_the_version_agree_right_now
FAILED tests/test_packaging_metadata.py::test_a_pyproject_version_that_moves_away_from_all_three_records_is_caught
['3 failed, 756 passed in 10.94s']

git: (clean)
BOTH DIRECTIONS OBSERVED, TREE RESTORED
```

Direction one moves the declaration and reddens **all three** records at once. Direction two
moves one record and reddens it alone. Both files restored byte-exact —
`git status --porcelain` clean, and `git diff --stat pyproject.toml .planning/STATE.md` empty
after each. **No `make` target, no sandbox build and no commit ran while either file was
modified.**

**The third failure in direction two is a finding worth keeping, not noise.**
`test_a_pyproject_version_that_moves_away_from_all_three_records_is_caught` asserts three
findings; with the milestone forced to `v9.9` and the version forced to `9.9.9`, those two
now *agree*, so only two findings exist. That is the corruption test correctly refusing to
claim three when the document it derives from is itself broken — which is precisely why the
agreement guard sits above it.

## The sandbox — a count, not an inference

A real `scripts/mutation_check.build_sandbox()`, `pytest tests/test_packaging_metadata.py -v`
inside it under the harness's own `_env(sandbox)`:

```
sandbox exit 0 PASSED 33 SKIPPED 8
CHANGELOG.md in sandbox: False | .planning in sandbox: False
```

**`SANDBOX_CONTENTS` is unwidened** — neither `CHANGELOG.md` nor `.planning/` reached the
sandbox, confirmed by stat rather than by reading the constant. The eight that skipped are
exactly the eight that read one of those two files.

**The nine version tests that ran there:**

| Test | What it proves inside the sandbox |
|---|---|
| `test_the_declared_version_is_readable_at_all` | the referent parses |
| **`test_the_readme_publication_instruction_names_the_declared_version`** | **the always-on binding — the load-bearing one** |
| `test_a_readme_that_moves_away_from_pyproject_is_caught` | that binding watched red, where M26 needs it |
| `test_deleting_the_readme_publication_instruction_is_a_finding_not_a_pass` | deletion is a finding, in the sandbox too |
| `test_the_development_status_classifier_does_not_contradict_the_version` | the classifier rule |
| `test_a_production_status_beside_a_major_zero_version_is_caught` | classifier direction one |
| `test_a_prerelease_status_beside_a_major_one_version_is_caught` | classifier direction two |
| `test_a_milestone_that_is_only_a_string_prefix_of_the_version_is_a_disagreement` | the `startswith` trap |
| `test_every_version_rule_is_green_on_documents_this_module_owns` / `..._bites_on_a_corruption_...` / `..._is_exercised_where_the_absent_files_are_absent` | all seven rules, no file read, plus the pin |

**`PASSED 33` is the number that matters.** Criterion 5 is not met by a skip line: the README
binding ran there, by name, and so did every rule's unconditional exercise.

Also proved there, and it was a real risk rather than a formality: **the borrowed
`scripts/release_check.py` import resolved inside the sandbox.** `scripts` is in
`SANDBOX_CONTENTS`, the module-scope `sys.path.insert` and its `identity_check` import both
worked, exit 0, no collection error. **The § F6 fallback was NOT needed and did not ship.**

## The pairing pin, watched going red — and a sharper finding than expected

**The pin bites on a rule ADDED without an unconditional exercise.** A throwaway
`_version_trailing_slop` was appended with no test naming it:

```
FAILED tests/test_packaging_metadata.py::test_every_version_rule_is_exercised_where_the_absent_files_are_absent
E   AssertionError: these version rules are named by no unconditional test:
    ['_version_trailing_slop']. They run only where CHANGELOG.md or .planning/ exists,
    which is not where `make mutation` runs, so criterion 5 would be met there by a skip line.
```

**Reverted.** The suite returned to `2 failed, 39 passed` (the deliberate pre-roll red).

**The rename experiment produced the more useful result, and it is not what the plan
expected.** Renaming `_version_status_disagreement` out of the `_version_` prefix produced
**8 failures — and the pin was not one of them.** Every caller broke with `NameError`, which
is louder than the pin, but the pin itself **went quiet**: with the rule renamed out of the
convention, the discovery walk simply stopped seeing it.

That is the convention's own trap, executed. It is also why this plan named the classifier
rule `_version_status_disagreement` rather than the plan's `_status_version_disagreement` —
see deviation 3. The comment above the rule block in the module says all of this, so the next
person to add a version rule reads it before naming one.

The pairing command on the committed tree:

```
version rules: 7 ['_version_declared', '_version_in_readme', '_version_in_changelog',
                  '_version_in_state', '_version_components', '_version_disagreements',
                  '_version_status_disagreement']
unconditional tests: 33
rules with no unconditional exercise: []
```

No `tomllib` import — asserted by AST, not by eye.

## M25 and M26 — the first mutations in this repository outside `boty/`

| | M25 | M26 |
|---|---|---|
| target | `pyproject.toml` | `README.md` |
| anchor | `version = "0.2.0"` | ``Publication happens from the `v0.2.0` tag`` |
| uniqueness count, taken BEFORE writing it | **1** | **1** |
| replacement | `version = "0.3.0"` | ``…from the `v0.9.0` tag`` |
| direction | the declaration moves away from all three records | a record moves away from the declaration |

Uniqueness was counted first for M19's recorded reason: `apply_mutation` replaces the **first**
occurrence, so a non-unique anchor mutates a line the `breaks=` sentence is not describing —
a harness reporting a result about work it did not do.

**Observed CAUGHT, from the harness's own output rather than from the prediction:**

```
CAUGHT M25 pyproject.toml: 1 test(s) failed — test_the_readme_publication_instruction_names_the_declared_version
CAUGHT M26 README.md: 1 test(s) failed — test_the_readme_publication_instruction_names_the_declared_version
mutation check: 22/22 mutations caught
```

Both caught by the **always-on binding**, exactly as predicted, and by nothing else — which
is the point. It is the only version rule whose two files both reach the sandbox, and without
it neither mutation could exist.

| | before this plan | after |
|---|---|---|
| registered mutations | 20 (`M1`..`M20`) | **22** (`M25`, `M26` added) |
| mutation ratio | 20/20 | **22/22** |
| highest registered ident | M20 | **M26** |
| mutations outside `boty/` | **0** | **2** |

**The M21-M24 gap is deliberate and is NOT four lost mutations.** 06-03 and 06-04 each
registered none by design and each recorded why in their own SUMMARY. This plan kept the
reserved M25-M26 rather than renumbering into the gap, as 06-04 asked.

## `make verify-offline` — the gate

Exit **0**, on a clean tree.

```
identity check: PASS — 196 file(s), no host identity found
All checks passed!                                        (lint)
759 passed in 10.81s                                      (tests)
Success: no issues found in 18 source files               (types)
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 22 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (731 passed, 28 skipped in 11.05s)
mutation check: 22/22 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

| | before this plan | after |
|---|---|---|
| `pytest tests/` | 737 passed | **759 passed** (+22) |
| `tests/test_packaging_metadata.py` | 651 lines, 20 tests | **1752 lines, 41 tests** |
| mutation ratio | 20/20 | **22/22** (+2, exactly as reserved) |
| sandbox baseline | 717 passed, 20 skipped | **731 passed, 28 skipped** (+14 passed, +8 skipped) |

The sandbox baseline line is the criterion read as arithmetic: **+8 skipped and +14 passed.**
The eight are this plan's two file-absent rules doing what F3 said they would; the fourteen
are why those skips are sound.

`make verify` (live) was **not run.** It is not this plan's gate, no acceptance here depends
on it, and its three known failure classes are recorded in `STATE.md` as needing their own
plan. **No test in this plan makes a network request.** The only network in the whole plan is
the four-row safety read above, which is a one-time execution observation and is in no test,
no `make` target and no CI job.

## The classifier decision, as it was written

`Development Status :: 5 - Production/Stable` -> **`Development Status :: 4 - Beta`**, and
the comment block was **rewritten in place** rather than replaced.

**Phase 4's rejection of `4 - Beta` is kept VERBATIM** — quoted in an indented block inside
the new argument, introduced with *"Phase 4 wrote the following, and it was RIGHT — for
1.0.0"*, with its whole `5 - Production/Stable` backing paragraph kept beside it. Nothing was
deleted. This is `boty/models.py`'s and `boty/pacing.py`'s house style for a reversal: argue
it where the old argument lives, name what overruled it, keep the original.

**What overruled it:** not a change of mind but a change of the number the classifier is a
statement about. At `0.2.0`, Production/Stable is the same asserted-versus-real disagreement
Phase 4 refused, pointed the other way.

**What refuses `5`** (measured 2026-08-10): nothing published — 404 for both `bot-y` and
`bot-y/1.0.0`; no tag locally or on the remote; nobody but the maintainer has installed it;
and `make verify` has failed live since 2026-08-06 in three classes.

**What refuses `3 - Alpha`:** the monitor has run as a service against six live retailers
publishing per-cycle status; `make verify-offline` has been the phase gate since Phase 1; and
the control-product mechanism catches a broken detector rather than reporting a confident
false verdict.

**What would move it back to `5`, written into the file so the next reader does not have to
guess:** a published release that somebody other than the maintainer has installed, and a
live `make verify` that passes.

**And it is no longer prose anybody has to remember.** `_version_status_disagreement` refuses
Production/Stable and Mature below major 1, and Planning, Pre-Alpha, Alpha and Beta at major
1 and above. The second direction is Phase 4's own reasoning made executable — without it a
rule that only stopped Production/Stable at 0.x would be perfectly satisfied by a 2.0.0
classified Alpha. The classifier list stayed alphabetically sorted; `4 - Beta` sorts to the
position `5 - Production/Stable` held, so nothing else moved, and the two deliberate absences
recorded in that block (`License ::`, `Typing :: Typed`) stay absent.

## Which changelog reader shipped

**The borrowed one.** `_version_in_changelog` is one line delegating to
`scripts/release_check._changelog_version`, loaded through the `spec_from_file_location`
idiom. § F6's fallback was **not** needed: the import resolved at collection, under
`make lint`, under `make types`, and — the one that was genuinely uncertain — **inside a real
`build_sandbox()`**, where the module-scope `sys.path.insert(0, <scripts dir>)` and its
`identity_check` import both worked at exit 0.

The measured cost is named in the helper's docstring rather than discovered later: `scripts/`
is now on `sys.path` for the rest of every pytest session, which nothing else in this suite
does today.

## The correction to the outline, stated plainly for 06-06

`06-PLAN-OUTLINE.md` § *Finding 7* says this plan should pair the STATE rule with a
`pyproject.toml` <-> `CHANGELOG.md` binding that is *"entirely inside the shipped tree and
runs everywhere"*.

**That claim is false, and it was re-confirmed false by building a sandbox and stat-ing it:
`CHANGELOG.md in sandbox: False`.** The outline's proposed pairing would have had **both** of
its rules skipping under `make mutation` — exactly the defect a pairing exists to prevent, and
criterion 5 would have been met by two skip lines.

**The always-on rule is `pyproject.toml` <-> `README.md` instead**, because `README.md` is in
`SANDBOX_CONTENTS`, it states the version in exactly one sentence, and that sentence had to be
edited by this plan anyway. That single fact is also what makes M25 and M26 possible at all.

## Deviations from Plan

### 1. [Rule 1 — bug in the plan's own verification command] The sandbox driver crashed before it built anything

**Found during:** Task 3, step 4.
**Issue:** the plan's third `<verify>` command loads `scripts/mutation_check.py` with
`spec_from_file_location` but never registers it in `sys.modules`. Python 3.12's
`@dataclass` resolves annotations through `sys.modules[cls.__module__]`, so it crashed at
import with `AttributeError: 'NoneType' object has no attribute '__dict__'` — before a
sandbox existed, and with nothing to do with this plan's subject.
**Fix:** `sys.modules["mc"] = mc` before `exec_module`, in the driver only. **No tracked file
was changed** — this is a one-off measurement script, and the `Mutation` dataclass is fine.
**Commit:** none (execution-time script).

### 2. [Rule 1 — bug, caused by this plan's own CHANGELOG edit] 06-04's gutting corruption rotted

**Found during:** Task 2, step 5.
**Issue:** `tests/test_changelog.py::test_a_changelog_with_its_only_release_deleted_is_rejected`
deleted the literal line `## [1.0.0] - 2026-08-05` and asserted `missing_required_headings`
reported a document with no release. This plan adds `## [0.2.0]` above it, so that deletion
left a release standing, the rule correctly reported nothing, and the assertion failed.
**The rule was right; the corruption had rotted.**
**Fix:** derive **every** released heading through that module's own `_release_headings`
reader rather than naming one, and rename the test to
`test_a_changelog_with_every_release_deleted_is_rejected`. **No rule and no assertion was
softened.** This is the plan's own instruction — *"fix the entry, never the gate"* — applied
one level along: the gate was fine and its corruption input was stale.
**Files modified:** `tests/test_changelog.py`. **Commit:** `4de5f9a`.

### 3. [Deviation from the plan's naming, justified by measurement] `_version_status_disagreement`, not `_status_version_disagreement`

The plan names the classifier rule `_status_version_disagreement`. Shipped as
`_version_status_disagreement`, and the reason is a measurement rather than taste: the plan's
own pairing pin discovers rules by the `_version_` prefix, and the rename experiment above
showed that **a rule outside the convention does not redden the pin — it becomes invisible to
it.** Naming the classifier rule outside the prefix would have left the one rule this plan
adds *because prose goes stale* as the one rule the anti-staleness pin cannot see. The
docstring records the plan's name and why it changed.

Consequence: the pin discovers **7** rules rather than the plan's 6, and the plan's own
`<verify>` assertion `len(rules) >= 5` still holds.

### 4. [Rule 2 — strengthening] The classifier corruptions restate BOTH lines, derived

The plan's Step 7 asks for "a major-0 version beside a Production/Stable classifier, and a
major-1 version beside a Beta one". Written naively — corrupt one line of the real file — each
test's verdict would depend on which side of this plan's roll the tree happened to be on, and
the first draft was red before the roll and green after for reasons unrelated to any rule. So
`_restated()` derives the real version line **and** the real classifier line and replaces both
together. A red-watch whose verdict depends on the day is not a red-watch.

Same idiom applied to the deletion test for `CHANGELOG.md`: it removes **every** released
heading rather than the top one, because after the roll there are two and removing one leaves
`_version_in_changelog` answering with the other.

### 5. [Rule 1 — lint] `RUF036` on the sentinel union

`str | None | _FileAbsent` put `None` mid-union; ruff rejects it. Reordered to
`str | _FileAbsent | None`. Caught by `make lint` before the commit.

### 6. [Procedure] The both-directions driver ran twice

The first run tripped its own closing `git status --porcelain` assertion — **not** because a
file failed to restore, but because `scripts/mutation_check.py` was still uncommitted at that
point. Confirmed at the time with `git diff --stat pyproject.toml .planning/STATE.md`, which
was **empty**: both targets were restored byte-exact. Re-run after the registry commit, on a
fully clean tree, and both runs produced identical verdicts. The clean run is the one quoted
above.

### 7. [Premise held] Every counted fact in `<measured_facts>` re-measured true

| Fact | Re-measured on this tree |
|---|---|
| F1 — the four safety rows | **all four unchanged** (see above) |
| F2 — `README.md` states the version in exactly one line | **confirmed**, before and after the edit: `grep -c 'v[0-9]\+\.[0-9]\+\.[0-9]\+' README.md` = 1 |
| F3 — `CHANGELOG.md` absent from the sandbox | **confirmed** by building a real sandbox and stat-ing it |
| F4 — exactly one rule red on arrival | **confirmed**: the STATE binding, plus the agreement guard that shares its subject |
| F5 — the classifier argument inverts at 0.2.0 | **confirmed**, and Phase 4's rejection text was found verbatim in the file and kept |
| F6 — the `release_check` borrow puts `scripts/` on `sys.path` | **confirmed** by diffing `sys.path` around the import; the fallback was not needed |
| F10 — counts on arrival | **737 tests / 20 mutations / highest M20** — F10 predicted "roughly 20" mutations and F10's 667 was a pre-06-01 figure, exactly as it said |

**Nothing measured this run contradicts the plan's `<measured_facts>`.** The three plan
statements corrected by measurement are all procedural: the sandbox verify command's own bug
(deviation 1), how the pin bites (it goes blind, it does not go red), and the classifier
corruption construction (deviation 4).

### 8. [Recorded rather than quietly fixed] THIS DOCUMENT arrived with leaked tool-call markup

**Found during:** writing this SUMMARY, by checking for it on purpose.
**Issue:** the first write of this file ended with two lines of leaked agent tool-call markup
— a closing content tag and a closing invoke tag, each alone on its own line, the file
otherwise complete. **That is the incident 06-04 exists for, byte-shape for byte-shape**, in
the plan that closes the same milestone, one document over.
**Fix:** the two lines were removed and the file re-scanned by command rather than by eye —
zero whole-line tags, zero tool-call vocabulary, and zero `U+200B` / `U+200C` / `U+200D` /
`U+FEFF` / `U+00A0` / `U+2060`. **Files modified:** this file only. **Commit:** the final
metadata commit.

**Nothing in this repository's gates would have caught it, and that is the finding.**
`tests/test_changelog.py`'s `leaked_markup` is deliberately scoped to `CHANGELOG.md` — 06-04
argued that scope from a measurement and made the argument executable. `.planning/` is not
covered by any contents rule at all, and `scripts/identity_check.py` scans for host identity,
not for markup. The class recurred within a day of the gate that catches it landing, in a
directory the gate does not cover.

**Logged as a candidate for 06-06, not fixed here**, on 06-04's own reasoning about its
zero-width-space finding: widening `leaked_markup` to `.planning/` needs a sweep of the whole
directory first, and adding a rule nobody has swept for is how a gate reddens on arrival. It
is also out of this plan's scope and in another plan's file. **06-06 now has two candidates of
the same shape** — invisible characters (06-04) and leaked markup outside `CHANGELOG.md`
(here), both found by hand in documents this project writes about itself.

## What was NOT done, deliberately

- **`REQUIREMENTS.md`, `ROADMAP.md` and `.planning/STATE.md` are not edited. REQ-20 stays
  Pending.** 06-06 closes it by measuring what landed — 04-05's and 05-01's recorded
  precedent. `git diff --stat 163337e..HEAD -- .planning/STATE.md` is **empty**.
- **No tag, no push of a tag, no upload, no `make release-check`.** The safety measurement is
  a read.
- **`SANDBOX_CONTENTS` is not widened**, and `scripts/mutation_check.py` gained two registry
  entries and nothing else.
- **No Makefile stage added.** Every gate here arrives through `make test`, so
  `test_the_documented_stages_are_the_stages_verify_runs` is untouched.
- **`scripts/release_check.py` is untouched.** One function is borrowed from it; nothing in it
  changed.
- **No file under `boty/` is read or edited.**
- **No new dependency.** `ast`, `importlib.util`, `re`, `subprocess`, `pathlib.Path`,
  `typing.Any` and `pytest` are all stdlib or already in use across `tests/`.
- **No network call in any test.** The four-row safety read was a shell command, run once.
- **No version-ordering rule was added** to `tests/test_changelog.py`. 06-04 refused it in
  writing precisely so `## [0.2.0]` could sit above `## [1.0.0]`, which is permanently correct
  here.

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path or schema change at a trust boundary. One new
file-access pattern **is** introduced and it is in the plan's own threat register rather than
a surprise: `tests/` now reads `.planning/STATE.md`, which nothing under `tests/` or
`scripts/` had ever done. It is a read, it is behind a presence skip, and its consequence —
that the `milestone` line is now machine-read — is recorded beside the constant and carried to
06-06 below.

## For the next plan

**06-06, three things this plan hands you:**

1. **`.planning/STATE.md`'s `milestone:` line is now MACHINE-READ by
   `tests/test_packaging_metadata.py`, as of commit `30cb977`.** Editing it is a gate-visible
   act: change it without changing `pyproject.toml`'s version and `make verify-offline` goes
   red naming both files. 06-06 edits that file. The comparison is lenient in exactly one way
   — a milestone names a *minor line*, so `v0.2` agrees with `0.2.0` and would agree with a
   future `0.2.7`, but **not** with `0.21.0`.
2. **Two files were touched beyond the outline's ownership table for 06-05, both deliberately.**
   `README.md` — one sentence in the install section, disjoint from 06-01's ceiling prose and
   06-02's matrix rows, edited because the roll made it false and gated because it is the only
   version statement the sandbox can see. `scripts/mutation_check.py` — two appended registry
   entries and nothing else, because M25-M26 are reserved for this plan and cannot be
   registered without opening the file. Waves here are strictly serial, so neither is a
   concurrency hazard.
3. **REQ-20 is Pending and criterion 5's code is all in the tree.** The measurements 06-06
   needs are in this document: 759 passed, 22/22, `tests/test_packaging_metadata.py` at 1752
   lines and 41 tests (measured with `wc -l` and `pytest --collect-only -q`), the sandbox at
   33 passed / 8 skipped with the README binding named among the passed, and both new idents
   CAUGHT by name.

**Also worth carrying:** the M21-M24 ident gap is deliberate — 06-03 and 06-04 each registered
none by design. **06-06 must not read four lost mutations.** The registry now runs
`M1`..`M20`, `M25`, `M26`.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | `30cb977` | four bindings, the comparator, the classifier rule, every red-watch — committed **deliberately red** on the STATE binding, with the subject line saying so |
| 2 (blocker) | `4de5f9a` | 06-04's gutting corruption derived instead of named, so this plan's second release heading could not rot it |
| 2 | `ac8155b` | the roll: `0.2.0`, the classifier reversal argued in place, the README sentence, the `## [0.2.0]` entry and the widened preamble |
| 3 | `1096f0a` | M25 and M26 — the first mutations in this repository outside `boty/`, both observed CAUGHT |

## Self-Check: PASSED

- `tests/test_packaging_metadata.py` — FOUND (1752 lines, 41 tests, 7 `_version_` rules discovered by the pin, contains `_version_disagreements`)
- `pyproject.toml` — FOUND, contains `version = "0.2.0"` (exactly 1 occurrence) and `Development Status :: 4 - Beta`
- `README.md` — FOUND, contains `v0.2.0`, still exactly one version-tag line
- `CHANGELOG.md` — FOUND, contains `## [0.2.0] - 2026-08-10` with a real ISO date and a body; `## [Unreleased]` still reads "Nothing yet."
- `scripts/mutation_check.py` — FOUND, contains `M25` and `M26`, 22 registered idents
- `.planning/phases/06-claims-with-gates-under-them/06-05-SUMMARY.md` — FOUND
- commits `30cb977`, `4de5f9a`, `ac8155b`, `1096f0a` — all FOUND in `git log`
- `.planning/STATE.md` — unmodified across the whole plan
- `make verify-offline` — exit 0, 759 passed, 22/22 caught
