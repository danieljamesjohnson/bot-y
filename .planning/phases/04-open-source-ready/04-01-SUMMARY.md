---
phase: 04-open-source-ready
plan: 01
subsystem: docs
tags: [contributor-docs, req-09, pytest, mutation-sandbox, markdown-gate]

requires:
  - phase: 03.1-target-and-amazon
    provides: the six shipped retailers, the Extraction axis, the Target/Amazon evidence sections and the redaction incidents the docs cite as fact
  - phase: 03-hard-two
    provides: docs/retailer-evidence.md verdict forms and scripts/evidence_check.py, which the contributor docs teach against
provides:
  - "docs/adding-a-retailer.md — REQ-09: Nintendo walked end to end with no adapter code, Amazon as the case that needs a reader, the control-product rule and the UNKNOWN contract"
  - "CONTRIBUTING.md — setup, the commit hook before the first commit, what each verify verdict means, the PR contract"
  - "tests/test_contributor_docs.py — six rules over document text, each watched failing against a corrupted copy of the real file"
  - "README.md § Adding a retailer and a § License body that links the file"
  - "SANDBOX_CONTENTS carries hooks and CONTRIBUTING.md, so the new gate runs inside the mutation sandbox as well as on the host"
affects: [04-02 packaging and LICENSE, 04-03 the linter, 04-04 CI, any future retailer addition]

tech-stack:
  added: []
  patterns:
    - "A documentation gate in the shape of tests/test_support_matrix.py: rules as pure functions over text, each run against a deliberately broken copy"
    - "Citation by symbol name rather than by file:line, enforced by rule 2"

key-files:
  created:
    - tests/test_contributor_docs.py
    - docs/adding-a-retailer.md
    - CONTRIBUTING.md
  modified:
    - README.md
    - scripts/mutation_check.py

key-decisions:
  - "The plan's 'five of the six retailers needed no adapter code' was measured against the tree and is false — it is three of six (GameStop, Walmart, Nintendo fall through _make_checker to check_html). Both new documents and the README section state three"
  - "Rule 1 skips a leading-slash token: a URL path a retailer serves is not a repo-relative path, and both documents quote several"
  - "origin/main is written out in prose rather than backticked, because a git ref is a genuine rule-1 false positive and rewording the doc is cheaper than teaching the extractor about remotes"
  - "No test in this plan stats LICENSE — 04-02 creates it in wave 2, and a stat would make this gate depend on another plan's ordering"

patterns-established:
  - "Enumerated pins with the reasoning above them (REQUIRED_SYMBOLS, RETAILER_DOC_HEADINGS, CONTRIBUTING_HEADINGS), in the UNREAD_POSITIONS idiom"
  - "A SANDBOX_CONTENTS entry lands in the same commit as the file it names, and is watched being load-bearing by removing it and reading the HARNESS ERROR"

requirements-completed: [REQ-09]

duration: 16min
completed: 2026-08-04
---

# Phase 04 Plan 01: Contributor documentation Summary

**REQ-09 shipped as three documents plus a test that reads them: every cited path must exist, no citation may carry a line number, and every pinned (file, symbol) pair must hold in both directions — with the gate watched failing before the docs existed and each rule watched failing against a corrupted copy.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-08-04T18:20Z
- **Completed:** 2026-08-04T18:36Z
- **Tasks:** 3
- **Files modified:** 5 (3 created, 2 modified)

## Accomplishments

- `docs/adding-a-retailer.md` (355 lines) walks Nintendo end to end through four edits that all exist in this tree — the probe and its evidence, one `FIRST_PARTY` line, the `MARKETPLACES` absence-is-a-claim decision, and two YAML watches one of which is a control — then walks Amazon as the case where `check_html` reads the page perfectly and says UNKNOWN forever.
- `CONTRIBUTING.md` (122 lines) tells a contributor to run `make hooks` before their first commit and says what happens if they do not: this repository has already had to rewrite its own published history over a value that reached the public repo through a planning document, which is why `scripts/identity_check.py --all` scans every tracked file.
- `tests/test_contributor_docs.py` (492 lines) is the gate. Six rules, three enumerated pins, eleven tests against the real tree and eight corruption tests.
- The gate runs in both places the suite runs: `SANDBOX_CONTENTS` gained `hooks` and `CONTRIBUTING.md`, and **both entries were watched being load-bearing** rather than asserted to be.

## Task Commits

1. **Task 1: The gate, written first and watched failing** — `db85e41` (test)
2. **Task 1 follow-on: rule 1 skips a URL path** — `4cfe2b2` (fix, Rule 3 auto-fix)
3. **Task 2: docs/adding-a-retailer.md** — `cc8ac65` (docs)
4. **Task 3: CONTRIBUTING.md, README prose, SANDBOX_CONTENTS** — `bb65ef8` (docs)

## Files Created/Modified

- `tests/test_contributor_docs.py` — the gate: `missing_cited_paths`, `line_numbered_citations`, `symbol_disagreements`, `missing_headings`, `missing_links`, `missing_mentions`, plus `REQUIRED_SYMBOLS`, `RETAILER_DOC_HEADINGS`, `CONTRIBUTING_HEADINGS`
- `docs/adding-a-retailer.md` — REQ-09
- `CONTRIBUTING.md` — setup, the hook, the checks, the PR contract
- `README.md` — a `## Adding a retailer` section after `## Use`, and a `## License` body that links the file
- `scripts/mutation_check.py` — two `SANDBOX_CONTENTS` entries and a comment paragraph for each

## Measurements

### The Task 1 RED, before any document existed

`.venv/bin/python -m pytest tests/test_contributor_docs.py -q` → **18 failed, 1 passed**, exit 1.

Fifteen of the eighteen failed on the same assertion, which is the one the gate was written to make legible:

```
AssertionError: docs/adding-a-retailer.md does not exist. This gate was written
before the documents it guards, deliberately, so this failure is the expected
state between the test landing and the docs landing.
```

(and the same for `CONTRIBUTING.md`). The three that failed on a real rule rather than a missing file:

```
AssertionError: README.md no longer links: ['docs/adding-a-retailer.md', 'CONTRIBUTING.md'].
  A contributor doc nothing links to is a doc nobody finds.
AssertionError: README.md's License section no longer links the LICENSE file
AssertionError: assert ['docs/adding-a-retailer.md', 'LICENSE'] == ['docs/adding-a-retailer.md']
```

The one test that passed was `test_the_path_extractor_skips_what_it_cannot_be_sure_about`, which reads no document.

### The final GREEN

| Check | Result |
|---|---|
| `pytest tests/test_contributor_docs.py -q` | **19 passed** |
| `pytest tests/test_support_matrix.py -q` | **31 passed** — identical to the pre-plan baseline, criterion 4 preserved |
| `pytest tests -q` (inside `make verify`) | 441 passed |
| `mypy` | Success: no issues found in 17 source files |
| `scripts/identity_check.py --all` | PASS — **139** tracked files, no host identity found |
| `scripts/evidence_check.py --phase` | PASS — phase (unchanged; this plan adds no retailer) |
| `scripts/mutation_check.py` standalone | `mutation check: 8/8 mutations caught`, no HARNESS ERROR |

`make verify-offline` exits 0 and prints, verbatim:

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

### Both sandbox entries watched being load-bearing

With `"CONTRIBUTING.md"` temporarily removed from `SANDBOX_CONTENTS`:

```
mutation check: HARNESS ERROR
baseline FAILED in the unmutated sandbox (pytest exit 1: tests failed).
Without a passing baseline every 'mutation caught' below would really be
'sandbox broken', and this check would report success while proving nothing.
```

`5 failed, 433 passed, 3 skipped`, every failure a `_read` on `PosixPath('/tmp/boty-mutation-xbdxmb_f/CONTRIBUTING.md')` — the sandbox root, not the repository. Exit code 2.

With `"hooks"` temporarily removed instead, the same `HARNESS ERROR` and the same failed baseline, reported by rule 1 rather than by a missing read:

```
AssertionError: docs/adding-a-retailer.md cites paths that are not in this tree:
  ['hooks/pre-commit']. A contributor sent to a file that is not there loses the
  time it takes to find that out, and the doc looks authoritative while they do.
AssertionError: CONTRIBUTING.md cites paths that are not in this tree: ['hooks/pre-commit']
```

With the tuple restored: `mutation check: 8/8 mutations caught`.

That is the point of the exercise. A `HarnessError` here is never "the mutation check is flaky" — it is `SANDBOX_CONTENTS` disagreeing with what the suite reads, and this plan is the reason it would have disagreed.

### The diffs, read rather than assumed

```
 README.md                 | 23 ++++++++++++++++++++++-
 scripts/mutation_check.py | 18 ++++++++++++++++--
```

- `git diff -U0 README.md | grep -E '^[-+]\| ' | wc -l` → **0**. Not one changed line begins with `| `, so the seven matrix data rows, the header row, the verdict table and the stage table are all untouched. `grep -c '^| Retailer | Rung | Extraction |' README.md` → **1**; no second seven-column table was introduced, and the new section contains no table at all.
- README's one deletion is the single word `MIT` under `## License`, replaced by a sentence linking the file. The heading text is unchanged.
- `scripts/mutation_check.py`: two tuple entries and two comment paragraphs. The tuple's two lines are rewrapped to fit the added entries; no function in the file changed and the block was added to, not restructured.

### Not touched, deliberately

`test ! -e LICENSE` still holds — 04-02 owns it and runs next, in wave 2. `MANIFEST.in` does not exist. `pyproject.toml` is not in this plan's diff (`git diff --name-only HEAD~4 HEAD | grep -E 'pyproject.toml|MANIFEST.in|LICENSE'` → 0 lines). No test in this plan changed behaviour because `LICENSE` is absent: the README licence test is a link-text assertion and stats nothing.

## Decisions Made

- **"Three of the six", not "five of the six".** The plan text (and 04-PATTERNS) asserted that five of the six shipped retailers needed no adapter code. Measured against `_make_checker`: it carries an arm for `bestbuy`, `amazon` and `target` and falls through to `check_html` for the rest, so it is **three** — GameStop, Walmart and Nintendo. Writing five would have been the exact failure this plan's gate exists to prevent, one level up: a confident number that nothing checked. Both documents and the README section say three.
- **A git ref is a rule-1 false positive worth reworking prose for.** `origin/main` is backtick-quoted in most of this repo's prose and looks exactly like a path. Rather than teach the extractor about git remotes — a narrow special case that widens the rule for one token — the sentence was rewritten to say "had already been pushed to the public repository". The rule stays conservative.
- **The module docstring says "three documents off disk, plus whichever source files `REQUIRED_SYMBOLS` names"** rather than the plan's "four files off disk", because the gate reads seven files and neither number was right. In a file whose entire job is to stop documents making unchecked claims, an unchecked claim in its own docstring is the wrong place to start.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Rule 1 failed on a URL path, which is not a repo path**
- **Found during:** Task 2, while writing the Nintendo section
- **Issue:** `_looks_like_a_repo_path` accepted any token containing `/` whose first segment was not a hostname. A leading-slash token like `/us/store/products/` or `/gp/offer-listing/` — both of which the evidence log and README already quote — resolved against the filesystem root via `root / "/us/..."`, so a *correct* citation would have failed the gate and the natural fix would have been to weaken the rule.
- **Fix:** `_looks_like_a_repo_path` returns False for a token starting with `/`, with the reasoning in a comment; two cases added to `test_the_path_extractor_skips_what_it_cannot_be_sure_about`.
- **Files modified:** `tests/test_contributor_docs.py`
- **Verification:** `pytest -k path_extractor` → 1 passed; the full gate is green at 19 passed.
- **Committed in:** `4cfe2b2`

**2. [Rule 1 - Bug] The doc cited the wrong test file for the Amazon seller pin**
- **Found during:** Task 2, checking the doc's own citations by hand before committing
- **Issue:** `docs/adding-a-retailer.md` said `test_an_amazon_offer_with_no_seller_recorded_is_unknown_not_a_verdict` is in `tests/test_parse.py`. It is in `tests/test_retailers.py`. Rule 1 passed because both files exist — this is precisely the class of error a path-existence check cannot see, which is worth recording next to the gate that did not catch it.
- **Fix:** citation corrected.
- **Files modified:** `docs/adding-a-retailer.md`
- **Verification:** `grep -rln <test name> tests/` → `tests/test_retailers.py`
- **Committed in:** `cc8ac65` (part of the Task 2 commit)

**3. [Rule 1 - Bug] The plan's retailer count was wrong**
- **Found during:** Task 2, before writing the section that leads on it
- **Issue:** The plan and `CONTRIBUTING.md`'s brief both said "on five of the six retailers in this repo, adding one needed no adapter code". `_make_checker` has three special-case arms, so it is three of six.
- **Fix:** all three documents state three, and name them.
- **Files modified:** `docs/adding-a-retailer.md`, `CONTRIBUTING.md`, `README.md`
- **Verification:** `grep -n "^def check_" boty/retailers.py` and the three `if` arms in `_make_checker`, read directly.
- **Committed in:** `cc8ac65` and `bb65ef8`

---

**Total deviations:** 3 auto-fixed (3 bugs, 0 blocking, 0 architectural)
**Impact on plan:** All three are corrections of claims that would have shipped wrong in a document whose purpose is to be trustworthy. No scope creep — no file outside this plan's ownership was touched.

## Issues Encountered

None that required problem-solving beyond the three corrections above. The tree was legitimately red between Task 1 and Task 3 by design, and `make verify-offline` at the end of Task 3 is what closed it.

## Known Stubs

None. Every path cited by the two contributor documents resolves in the tree and inside the mutation sandbox, and every pinned symbol holds in both directions.

## User Setup Required

None — no external service configuration required. `make hooks` is a contributor instruction, not a setup step for this repository, and the hook was already installed on this machine (it ran on all four commits).

## Next Phase Readiness

**Handoff to 04-02 (wave 2).** `SANDBOX_CONTENTS` now reads:

```python
("boty", "tests", "scripts", "config", "served", "docs", "hooks", "pyproject.toml",
 "Makefile", "README.md", "CONTRIBUTING.md")
```

So **04-02 adds only `LICENSE` and `MANIFEST.in`** to it, in the same commit as the files it creates — `build_sandbox()` raises `HarnessError` for an entry with no file behind it, which is why the two plans were serialised in the first place. `README.md` already links `LICENSE`; that link is correct the moment 04-02 lands, and nothing in this plan's gate stats the file.

**For 04-03 (the linter).** `tests/test_contributor_docs.py` is annotated throughout but `mypy` covers `boty` and `scripts` only, so it is not currently type-checked. Rule 2 exists because 04-03 moves several hundred lines; the two contributor documents carry zero line-numbered citations today and the gate keeps it that way.

**For 04-04 (CI).** Neither document describes CI as existing. Both tell a contributor to run `make verify-offline`, which is the intended CI entry point, so the CI plan adds a workflow without contradicting anything already written.

## Self-Check: PASSED

All six files claimed above exist on disk; all four commit hashes resolve in `git log`.

---
*Phase: 04-open-source-ready*
*Completed: 2026-08-04*
