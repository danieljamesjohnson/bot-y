---
phase: 06-claims-with-gates-under-them
plan: 04
subsystem: shipped-document-gates
tags: [req-19, changelog, leaked-markup, red-watch, sandbox-skip, no-mutation, two-directional]

requires:
  - phase: 06-claims-with-gates-under-them
    plan: 03
    provides: "the 711-test baseline this plan raises to 737, the 20-mutation registry it leaves at 20, and the `spec_from_file_location` borrow idiom it reuses"
  - phase: 04-open-source-ready
    provides: "`tests/test_contributor_docs.py` itself — `missing_cited_paths` / `line_numbered_citations` borrowed rather than re-implemented, plus `_corrupt`'s derive-don't-retype idiom and the shipped-file-is-clean guard"
  - phase: 05-a-reading-you-can-locate
    provides: "`tests/test_config.py`'s file-absence skip, on `tests/test_identity_check.py`'s `needs_repo` — the precedent for not widening `SANDBOX_CONTENTS`"
provides:
  - "`tests/test_changelog.py` — eight rules as pure functions of text over the one shipped document in this repo with no gate over its body"
  - "`HISTORICAL_TAIL` — the exact two lines `2ac965f` removed, recovered from git and substituted mechanically, never retyped"
  - "`leaked_markup` — three shapes (whole-line tag on the RAW text, agent namespace prefix, tool-call vocabulary with inline-code stripped), shaped around the defect rather than around angle brackets"
  - "`needs_changelog` — the file-presence skip, paired with an unconditional half so the criterion is not met by a skip line"
  - "`MINIMAL` / `PREAMBLE_ONLY` — the unconditional half's subjects, read from no file, exercised inside a real `build_sandbox()`"
  - "`test_every_rule_is_exercised_where_the_shipped_file_is_absent` — an `ast` walk pinning the pairing, rules discovered from the module rather than a hand-maintained tuple"
affects: [06-05, 06-06]

tech-stack:
  added: []
  patterns:
    - "Pair every prohibition with a presence rule in the SAME commit — no markup, no placeholders and a trailing newline are all satisfied by an empty file"
    - "Recover the defect from git and substitute it mechanically; a retyped corruption is an impression of the incident, not the incident"
    - "Shape a rule around the defect, not around the character class the defect happens to use — the shipped file's one legitimate angle-bracket token is what makes the green side load-bearing"
    - "A skip is only sound if something still runs, and the pairing is pinned by an AST walk rather than promised in a docstring"
    - "An 'unconditional' fixture that cites an uncopied path is coupled to SANDBOX_CONTENTS while looking as though it is not"
    - "Argue a gate's scope from a measurement, then make the argument executable — this module must carry the shapes it forbids, so a tree-wide rule reddens its own definition"

key-files:
  created:
    - tests/test_changelog.py
  modified: []

key-decisions:
  - "HISTORICAL_TAIL substituted into the module from `git show 2ac965f^:CHANGELOG.md | tail -2` by a script, never typed — the red-watch is the incident"
  - "leaked_markup is THREE shapes, not one angle-bracket regex: a naive rule is red on the shipped file on arrival (measured: 1 hit, line 138)"
  - "Shape (a) reads the RAW text so a fenced block is covered; shape (c) strips inline code but NOT fences — a strengthening over the plan's wording"
  - "Presence rules landed in the same commit as the prohibitions, and the red-watches landed with them: a gate nobody has watched going red is the artefact this phase refuses"
  - "SANDBOX_CONTENTS NOT widened; the coupling the sandbox exposed was fixed in MINIMAL, not in the harness"
  - "Date validity checked with `date.fromisoformat`, not only the `\\d{4}-\\d{2}-\\d{2}` shape — a strengthening over the plan"
  - "NO MUTATION REGISTERED; M23-M24 left unallocated, joining 06-03's M21-M22, so the sequence carries a deliberate gap at M21-M24"
  - "`REQUIREMENTS.md`, `ROADMAP.md` and `CHANGELOG.md` all unedited — REQ-19 stays Pending for 06-06"

metrics:
  duration: 47min
  tasks: 3
  files: 1
  completed: 2026-08-10
---

# Phase 6 Plan 04: `CHANGELOG.md` Is Gated On Its Contents Summary

The byte-exact document that shipped with leaked agent tool-call markup for the whole of Phase 4
was restored to disk and measured **green — exit 0, 711 passed** — before this plan's gate existed,
and **red — exit 1, 2 failed, 735 passed** — after it, on the same bytes and the same command; eight
rules now read the body that `scripts/release_check.py` only ever asserted the existence of, every
prohibition is paired with a presence rule so a deletion cannot satisfy the set, and the
unconditional half was **observed passing inside a real `build_sandbox()`** so the criterion is not
met by a skip line.

## The pre-gate measurement — the defect, executed on this tree

`git show 2ac965f^:CHANGELOG.md` written over `CHANGELOG.md`, `pytest tests/ -q`,
`git checkout -- CHANGELOG.md` in a `finally`, with **no contents rule anywhere in the tree**.
Verbatim:

```
PRE-GATE exit 0
711 passed in 10.49s
git: (clean)
```

Seven hundred and eleven tests watched the exact document that shipped with two lines of leaked
agent tool-call markup arrive on disk — the document `MANIFEST.in` puts in the sdist and
`pyproject.toml`'s `[project.urls] Changelog` points every installer at — and not one of them said
anything.

The plan's F8 measured the same shape at **667 passed** against the pre-06-01 tree. 06-01, 06-02 and
06-03 raised it to 711, exactly as F8 anticipated. **The number moved; the verdict did not.**

## The post-gate observation — same bytes, same command, red

Re-run on the committed tree after both commits:

```
POST-GATE exit 1
FAILED tests/test_changelog.py::test_the_shipped_changelog_carries_no_leaked_markup
FAILED tests/test_changelog.py::test_the_shipped_file_is_clean_or_the_corruption_tests_prove_nothing
2 failed, 735 passed in 10.46s
git: (clean)
```

The failure names the file, the line numbers and both shapes that caught it:

```
>       assert not leaked_markup(_shipped())
E       assert not ["line 161: the whole line is a tag: '</content>'",
E                   "line 161: tool-call markup in the prose: '</content>'",
E                   "line 162: the whole line is a tag: '</invoke>'",
E                   "line 162: tool-call markup in the prose: '</invoke>'"]
```

**`CHANGELOG.md` was restored byte-for-byte and `git status --porcelain` was clean** after every one
of the four driver runs (one pre-gate, three post-gate — see deviation 4). The restore is
`git checkout --` inside a `finally` that runs even when the assertions fail.

Green before, red after, same document, same command, and the only thing that changed between them
is this plan's gate.

**No separate removal gate is needed, unlike 06-03.** The gate under construction *is* the removal
gate: commit the corrupted file and `make verify-offline` fails naming it. The plan's hard
constraint was honoured — **`pytest` and nothing else ran while that document was on disk.** No
`make verify`, no `make verify-offline`, no `make mutation`, no sandbox build and no commit, so
`hooks/pre-commit` was never handed a document this repository already fixed once.

### What actually failed, against what the plan predicted

The plan expected "the leaked-markup green-side test and the file-shape or clean-guard tests".
Measured: **the leaked-markup green-side test and the clean-guard, and not the file-shape test.**
`file_shape_problems` is correct to stay silent — `2ac965f^`'s document ends with `</invoke>\n`, a
single trailing newline, so its end-of-file shape is fine and only its *contents* are wrong. That is
the two rules doing different jobs rather than one of them missing.

## The sandbox run — the evidence that replaces the mutation this plan does not register

A real `scripts/mutation_check.build_sandbox()`, `pytest tests/test_changelog.py -v` inside it with
the harness's own `_env(sandbox)`:

```
CHANGELOG.md in sandbox: False
sandbox exit 0 PASSED 7 SKIPPED 19
7 passed, 19 skipped in 0.05s
```

`CHANGELOG.md` did **not** reach the sandbox, confirming `SANDBOX_CONTENTS` is unwidened. The 19
file-reading tests skip. **The seven that ran there:**

| Test | What it proves inside the sandbox |
|---|---|
| `test_every_rule_is_green_on_a_well_formed_changelog` | all eight rules clean on `MINIMAL`, including the markup rule despite its inline-code angle-bracket token |
| `test_the_markup_rule_does_not_fire_on_what_a_changelog_legitimately_carries` | the precision half — autolinks, `>=3.10`, `price <= max_price`, inline-code tags |
| `test_every_rule_bites_on_a_corruption_of_that_document` | all eight rules watched red, table-driven, naming the rule that went quiet |
| `test_the_markup_that_shipped_is_rejected_without_reading_the_shipped_file` | `HISTORICAL_TAIL` — the incident, watched red in the second of the two places this suite runs |
| `test_the_rule_set_is_not_satisfied_by_a_document_with_no_release_in_it` | the empty and preamble-only documents |
| `test_this_gate_would_redden_its_own_definition_if_it_were_scoped_to_the_tree` | the scope argument, executable |
| `test_every_rule_is_exercised_where_the_shipped_file_is_absent` | the pairing pin itself |

**`passed > 0` is the load-bearing number.** The criterion is not met by a skip line: every rule in
the module is exercised where `CHANGELOG.md` does not exist, and the pin fails if one ever stops
being.

## The pairing pin, watched going red

Two observations, and the first one is the more useful:

1. **Renaming a rule does not test the pin — it breaks collection.** Renaming
   `empty_release_sections` at its definition left `_CORRUPTIONS` and the green-side tests
   referencing a name that no longer existed: `NameError: name 'empty_release_sections' is not
   defined`, `1 error during collection`. A harder failure than the pin, but not the pin.
2. **The pin's actual subject is a rule ADDED without an unconditional exercise**, which is the
   defect it exists for. A ninth public rule `trailing_whitespace` was added with no test naming it:

```
FAILED tests/test_changelog.py::test_every_rule_is_exercised_where_the_shipped_file_is_absent
E   AssertionError: these rules are named by no unconditional test: ['trailing_whitespace'].
    They run only where CHANGELOG.md exists, which is not where `make mutation` runs, so the
    criterion would be met there by a skip line.
```

**Reverted**; `26 passed`, `git status --porcelain` showed only the (then untracked) new file.

The pairing command from the plan, on the committed tree:

```
rules: 8 ['leaked_markup', 'malformed_release_headings', 'unreplaced_placeholders',
          'file_shape_problems', 'missing_required_headings', 'empty_release_sections',
          'stale_path_citations', 'line_numbered_citations']
unconditional tests: 7
rules with no unconditional exercise: []
```

## `make verify-offline` — the gate

Exit **0**, on a clean tree.

```
identity check: PASS — 195 file(s), no host identity found
All checks passed!                                        (lint)
737 passed in 10.48s                                      (tests)
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 20 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (717 passed, 20 skipped in 10.85s)
mutation check: 20/20 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

| | before this plan | after |
|---|---|---|
| `pytest tests/` | 711 passed | **737 passed** (+26) |
| `tests/test_changelog.py` | did not exist | **26 tests, 979 lines** |
| mutation ratio | 20/20 | **20/20 — unchanged, by design** |
| highest registered ident | M20 | **M20** |
| sandbox baseline | 710 passed, 1 skipped | **717 passed, 20 skipped** (+7 passed, +19 skipped) |

The sandbox baseline line is worth reading beside the ratio: **+19 skipped and +7 passed.** The
skips are this plan's file-reading half doing what F5 said it would; the seven are the reason the
skips are sound.

`make verify` (live) was **not run.** It is not this plan's gate, no acceptance here depends on it,
and its three known failure classes are recorded in STATE.md as needing their own plan. **No network
request of any kind was made.**

## Why this plan registers NO mutation, and why the M21-M24 gap is deliberate

The planning context reserved **M23-M24** for this plan. They are left **unallocated**, and
`scripts/mutation_check.py` is untouched — `git diff --stat 5523316 --name-only` names exactly one
file, `tests/test_changelog.py`. Four measured reasons, in full:

1. **The harness mutates `boty/`.** Its own docstring says so, and all 20 registered idents target a
   file under `boty/`. This plan writes no production code; its deliverable **is** a gate over a data
   file. There is nothing in `boty/` for it to break.
2. **The subject is out of the harness's reach.** `apply_mutation` string-replaces inside a file the
   sandbox copied, and `CHANGELOG.md` is not copied — confirmed this run:
   `(sandbox / "CHANGELOG.md").exists()` is `False`.
3. **Making it reachable is self-justifying and lands in another plan's file.** Adding `CHANGELOG.md`
   to `SANDBOX_CONTENTS` so a mutation could exist would create an entry provable load-bearing only
   by the mutation that motivated it — failing Phase 4's recorded rule for that constant, *"a
   `SANDBOX_CONTENTS` entry lands in the same commit as the file it names, and is proven load-bearing
   by removal"* — and would put this plan into `scripts/mutation_check.py`, which is 06-01's and
   06-02's.
4. **What a mutation would have proved is proved better here.** The question a mutation answers is
   *does this gate actually bite where the suite runs?* The real `build_sandbox()` run above answers
   it directly, with a count rather than an inference — and it did not merely confirm the premise, it
   **found a defect** (deviation 1) that no in-tree run could have exposed.

**So the ident sequence carries a deliberate gap at M21-M24.** 06-05 should keep **M25-M26** rather
than renumbering into it, and **06-06 must not read four lost mutations.** A mutation that survives
is never explained away; a mutation that cannot exist is recorded as not existing.

## What was built

**Eight rules, each a pure function of text returning findings that name a line number.** Two are
borrowed from `tests/test_contributor_docs.py` through the `spec_from_file_location` idiom rather
than re-implemented, for the reason `tests/test_ci_workflow.py` records: *two readers drift.*

| Rule | Catches | Notes |
|---|---|---|
| `leaked_markup` | three shapes — see below | the criterion's own class |
| `malformed_release_headings` | a heading that is not `## [x.y.z] - YYYY-MM-DD` | **no ordering asserted**; date validity checked, not only its shape |
| `unreplaced_placeholders` | `TODO` `TBD` `FIXME` `x.y.z` `Lorem ipsum` | whole-token, case-sensitive; `XXX` deliberately excluded |
| `file_shape_problems` | no trailing newline, or a run of blank ones | the defect's own location: it arrived by being appended |
| `missing_required_headings` | no title / no `## [Unreleased]` / no release | **the presence half** |
| `empty_release_sections` | a release announced and not described | `## [Unreleased]` exempt |
| `stale_path_citations` | a cited repo path that does not exist | **borrowed** |
| `line_numbered_citations` | a `:N` / `:N-M` suffix | **borrowed** |

**`leaked_markup` is three shapes, not one regex over angle brackets, and the green side is what
proves it.** Measured on the shipped file this run: a naive any-tag rule produces **1 hit — line 138,
the backticked `<script>` token in the sentence about emptying script bodies in fixture captures.** A
rule written that way is red on the shipped tree on arrival, and the loosening that follows is how a
rule stops catching anything. So:

- **(a)** a line whose entire content is a tag — the exact shape that shipped — matched against the
  **RAW** text, so a fenced code block is covered. A fence is precisely where an agent's output
  lands;
- **(b)** the agent namespace prefix, anywhere;
- **(c)** the tool-call vocabulary (`function_calls`, `invoke`, `parameter`, `content`) as a tag,
  with inline-code spans removed first.

`MINIMAL` carries the same inline-code angle-bracket token on purpose, so the precision proof
survives into the sandbox as well as living on the shipped tree.

**`HISTORICAL_TAIL` was recovered, not retyped.** `git show 2ac965f^:CHANGELOG.md | tail -2` was read
by a script that substituted `repr()` of those bytes into a placeholder in the module, so no human
transcription sits between the incident and the constant. Recorded verbatim for re-verification:
`'</content>\n</invoke>\n'`. Confirmed alongside it that `git diff --stat 2ac965f -- CHANGELOG.md` is
**empty** — the shipped file has not moved since the fix — so today's `CHANGELOG.md` plus that tail
*is*, byte for byte, the document that shipped.

**Two rules were deliberately NOT written and the reasons are in the module docstring**, not only
here: version *ordering* (06-05's roll writes `## [0.2.0]` above `## [1.0.0]` because the roll is the
correction, so the rule would be wrong the day it landed) and any requirement that `## [Unreleased]`
carry entries (it reads "Nothing yet." and requiring otherwise would redden the shipped tree by
inventing an entry).

**The scope is `CHANGELOG.md` and the argument is executable.**
`test_this_gate_would_redden_its_own_definition_if_it_were_scoped_to_the_tree` runs `leaked_markup`
over this module's own source and asserts findings, including one naming the namespace prefix. The
file must contain the shapes it forbids or it could not forbid them, so a tree-wide rule is
self-invalidating by construction — not by accident of who quoted what.
`scripts/identity_check.py`'s `_PROBE_FILES` / `_PROBE_DIR_PREFIXES` is named in the docstring as the
mechanism a future widening would need.

## Deviations from Plan

### 1. [Rule 1 — bug, found by the plan's own measurement] `MINIMAL` cited a path the sandbox does not copy

**Found during:** Task 3, step 2 — the first real `build_sandbox()` run.
**Issue:** `MINIMAL`'s preamble named CHANGELOG.md, in backticks. `stale_path_citations`
resolves it in the repository and **cannot** resolve it inside the sandbox, because `CHANGELOG.md` is
absent from `SANDBOX_CONTENTS` — the very fact this plan is built around. So
`test_every_rule_is_green_on_a_well_formed_changelog`, the test whose entire job is to run where
`CHANGELOG.md` does not exist, **failed in the one place it was written for**. Measured:
`sandbox exit 1 PASSED 6 SKIPPED 19`, `1 failed`.

This is the criterion's own defect one step along: an "unconditional" fixture that cites an uncopied
path is coupled to `SANDBOX_CONTENTS` while looking as though it is not. It would have surfaced as a
`HarnessError` at the next `make verify`, attributable to nothing.

**Fix:** the citation dropped from `MINIMAL` — **not** `SANDBOX_CONTENTS` widened. The constraint is
written above the constant, and the assertion now carries a message naming this trap so a recurrence
is attributable rather than a bare `AssertionError` inside a harness error.
**Files modified:** `tests/test_changelog.py`. **Commit:** `d3fd940`.

**This is the finding that justifies Task 3's claim** that a real sandbox run is better evidence than
the mutation this plan does not register. It did not confirm a premise; it caught a defect.

### 2. [Rule 2 — strengthening] Three additions the plan did not enumerate

- **Date *validity*, not only date shape.** `\d{4}-\d{2}-\d{2}` is a shape: `2026-13-45` matches it.
  `malformed_release_headings` runs `date.fromisoformat` and reports "not a real calendar date",
  watched red by `test_a_release_heading_carrying_an_impossible_date_is_rejected`. F9's import list
  gains `datetime.date`.
- **`test_the_markup_rule_does_not_fire_on_what_a_changelog_legitimately_carries`** — the other half
  of the markup rule, on `test_the_path_extractor_skips_what_it_cannot_be_sure_about`'s precedent.
  Five shapes it must not report (an inline-code script tag, a markdown autolink, `>=3.10`,
  `price <= max_price`, a bolded inline-code identifier) and three it always must. This is
  **unconditional**, so F3's precision proof runs in the sandbox too.
- **Shape (c) does not exempt fenced blocks.** The plan said "the prose view", which in
  `tests/test_contributor_docs.py` means fences removed. Only inline-code spans are stripped here.
  Strictly stronger, still green on the shipped file, and consistent with the must-have that the
  markup be reported "wherever it sits… including inside a fenced block".

### 3. [Procedure] Tasks 1 and 2 landed in ONE commit, deliberately

The plan's three tasks map to two commits, not three. **The green side was never committed alone.** A
commit containing rules asserted only against the tree they guard is a gate nobody has watched going
red — which is precisely the artefact this phase exists to refuse, and it would have sat in this
repository's history as an example of it. The prohibitions, the presence rules and every red-watch
landed together in `b8ba76f` for the same reason non-negotiable 3 requires the presence rules to
land with the prohibitions. Task 3's discovery is `d3fd940`.

### 4. [Procedure] The on-disk driver ran four times, not twice

Once for the pre-gate measurement (exit 0), once for the first post-gate observation (exit 1), once
with `--tb=long` to capture the failure text quoted above, and once more on the committed tree after
deviation 1's fix. Every run was `pytest` and nothing else, every run restored `CHANGELOG.md` with
`git checkout --` in a `finally`, and `git status --porcelain` was asserted clean after each. No
sandbox was built and no commit was made at any point while the corrupted document existed.

### 5. [Renaming a rule is not how the pin bites]

The plan said to "temporarily rename one rule so no undecorated test names it". Measured: that
produces a `NameError` at collection, because `_CORRUPTIONS` and the green-side tests reference the
rule by name — a harder failure than the pin, and not the pin. The pin's real subject is a rule
**added** without an unconditional exercise, and it was watched red that way instead. Both
observations are recorded above; the second is the one that matters.

### 6. [Premise held] Every one of F1, F2, F3, F5, F8 and F10 re-measured true

| Fact | Re-measured on this tree |
|---|---|
| F1 — `git diff --stat 2ac965f -- CHANGELOG.md` | **empty**; the shipped file has not moved since the fix |
| F2 — 10,047 bytes, 160 lines, one trailing `\n`, no trailing whitespace | **all confirmed** |
| F2/F10 — `missing_cited_paths` / `line_numbered_citations` | **`[]` and `[]`; 17 backticked repo paths, all resolving** |
| F3 — the inline-code `script` tag is the only angle-bracket token | **confirmed**: a naive any-tag rule scores exactly 1 hit, line 138 |
| F5 — `CHANGELOG.md` absent from `SANDBOX_CONTENTS` | **confirmed** by building a real sandbox and stat-ing it |
| F8 — the pre-gate count | **711, not 667** — exactly as F8 predicted 06-01/02/03 would make it |
| F9 — `make lint` is this file's gate, `tests/` is not type-checked | **confirmed**; `make lint` green, one import beyond F9's list (`datetime.date`) |

**Nothing measured this run contradicts the plan's `<measured_facts>`.** The one plan statement
corrected by measurement is a procedural prediction, not a fact: which tests would fail on the
post-gate run (see above), and how the pin bites (deviation 5).

## What was NOT done, deliberately

- **`REQUIREMENTS.md`, `ROADMAP.md` and `STATE.md`'s requirement text are not edited. REQ-19 stays
  Pending.** 06-03 shipped the workflow half, this plan the `CHANGELOG.md` half, and **06-06 closes
  REQ-19 by measuring what landed.** 04-05's and 05-01's recorded precedent.
- **`CHANGELOG.md` is not edited.** It is written transiently four times and restored byte-for-byte
  every time; it is not in `files_modified` and `git status --porcelain CHANGELOG.md` is empty.
- **`SANDBOX_CONTENTS` is not widened and `scripts/mutation_check.py` is not opened.** No mutation
  registered; M23-M24 unallocated.
- **No file under `boty/` or `scripts/` is read or edited by the shipped test file.** The one
  `scripts/mutation_check.py` import lives in an execution-time measurement script, not in `tests/`.
- **`scripts/release_check.py` is untouched.** It needs the network and sits outside `make verify` by
  design, so a contents rule there would never run in `verify-offline` — which is this phase's gate.
  That is a finding, not a preference, and it is written into the module docstring.
- **No new dependency.** `ast`, `importlib.util`, `re`, `collections.abc.Callable`, `datetime.date`,
  `pathlib.Path`, `typing.Any` and `pytest` are all stdlib or already in use across `tests/`.
- **No network request, no live `make verify`, no CI run.**

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path, file-access pattern or schema change at a trust boundary.
The one document written to disk is one this repository already carries in its own history, and it
does not survive the command that writes it.

## For the next plan

**06-05 (`pyproject.toml` ↔ `CHANGELOG.md`, REQ-20) — two forward bindings:**

1. **The `## [0.2.0]` heading you write must carry a real ISO date and a non-empty body, or this gate
   bites.** `malformed_release_headings` checks the shape *and* that the date is a real calendar day;
   `empty_release_sections` requires at least one non-blank line before the next `## `. That is the
   gate working, not a collision. **No ordering rule exists**, so `## [0.2.0]` above `## [1.0.0]` is
   accepted — deliberately, because the roll is the correction rather than a bump.
2. **`CHANGELOG.md`'s preamble currently reads: *"`pyproject.toml` states the version;
   `scripts/release_check.py` binds this file's top heading to it, so the two cannot drift."*** That
   sentence becomes incomplete the moment 06-05 adds an offline binding in
   `tests/test_packaging_metadata.py`. **It was NOT edited here** — `CHANGELOG.md` is 06-05's file,
   not this plan's, and editing prose about another plan's mechanism before that mechanism exists is
   the overclaim this milestone is about. A note for the plan that owns the file.
3. **Keep M25-M26.** The ident gap at M21-M24 is deliberate and argued above.

**06-06:**

- **The measured citation count is 17** repo paths in `CHANGELOG.md`, all resolving on 2026-08-10,
  so the borrowed `stale_path_citations` rule is guarding seventeen live claims in the document every
  installer is pointed at. The green-side test asserts the count has not collapsed below 15, because
  a rule with nothing left to resolve passes by describing nothing.
- **REQ-19 is Pending, and both halves are now in the tree**: the directory-keyed workflow gate
  (06-03, `tests/test_ci_workflow.py`) and the changelog contents gate (this plan,
  `tests/test_changelog.py`).
- **`tests/test_changelog.py` is 979 lines and 26 tests**, measured with `wc -l` and
  `pytest --collect-only -q`, not from memory.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 + 2 | `b8ba76f` | the gap measured at exit 0 / 711 passed, then eight rules, the green side, and every red-watch — landed together on purpose |
| 3 | `d3fd940` | the sandbox coupling the real `build_sandbox()` run exposed, fixed in `MINIMAL` and not in the harness |

## Self-Check: PASSED

- `tests/test_changelog.py` — FOUND (979 lines, 26 tests collected, 8 rules discovered by the pin)
- `.planning/phases/06-claims-with-gates-under-them/06-04-SUMMARY.md` — FOUND
- commits `b8ba76f`, `d3fd940` — both FOUND in `git log --all`
- `CHANGELOG.md` — unmodified; `git status --porcelain CHANGELOG.md` empty
- `scripts/mutation_check.py` — unmodified; 20 registered idents, highest `M20`
- `git diff --stat 5523316 --name-only` — names exactly one file, `tests/test_changelog.py`
- `make verify-offline` — exit 0, 737 passed, 20/20 caught

One thing about this file itself, recorded rather than quietly fixed, because it is the same class
as the defect the plan is about. An earlier draft escaped a nested backtick with **zero-width
spaces** (`U+200B`), and a hook caught them on the way to disk. Invisible characters in a document
about a document that shipped invisible junk is exactly the accident this milestone exists to
notice. Removed, and the file is now confirmed free of `U+200B`, `U+200C`, `U+200D`, `U+FEFF`,
`U+00A0` and `U+2060` by a command rather than by eye.

**Worth carrying to 06-06:** nothing in this repository's own gates would have caught that.
`scripts/identity_check.py` scans for host identity, not for invisible characters, and
`tests/test_changelog.py` scopes its rules to `CHANGELOG.md`. A zero-width-space rule over shipped
documents is a candidate finding, **not** something added here: it is out of this plan's scope, it
would need its own sweep of the tracked tree first, and adding a rule nobody has swept for is how a
gate reddens on arrival. Logged as a candidate, not as work done.
