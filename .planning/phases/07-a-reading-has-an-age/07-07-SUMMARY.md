---
phase: 07-a-reading-has-an-age
plan: 07
subsystem: verification-record
tags: [gap-closure, documentation, test-infrastructure, gates]
gap_closure: true
requires:
  - "07-06 (the closing record this plan corrects)"
  - "07-VERIFICATION.md (the four gaps)"
provides:
  - "a dated post-review addendum beside the closing record, in three documents"
  - "a dashboard parse gate that EXECUTES inside make verify-offline"
  - "a gate transcript in which a skip states its own reason"
affects:
  - "docs/retailer-evidence.md"
  - ".planning/ROADMAP.md"
  - ".planning/REQUIREMENTS.md"
  - ".planning/STATE.md"
tech-stack:
  added: []
  patterns:
    - "runtime discovery past PATH via version-manager install roots (stdlib only)"
    - "a superseded measurement is recorded beside; a never-true description is corrected in place"
key-files:
  created: []
  modified:
    - "tests/test_dashboard.py"
    - "Makefile"
    - "docs/retailer-evidence.md"
    - ".planning/ROADMAP.md"
    - ".planning/REQUIREMENTS.md"
    - ".planning/STATE.md"
decisions:
  - "A superseded MEASUREMENT is dated and recorded beside; a description of evidence that never existed is corrected in place"
  - "A gate that skips in the project's own gate environment is not a gate; widen what it can FIND, never what the suite DEMANDS"
  - "A skip prints its reason in the gate transcript, so a bound that stops binding is loud the day it appears"
  - "No mutation for a runtime-conditional gate: it would be CAUGHT where node exists and SURVIVE where it does not"
  - "Criterion 5 closes one of three reasons and does not move"
  - "status.json still publishes no staleness verdict, by Dan's decision; criterion 3 stays MET IN PART"
metrics:
  duration: "~50 minutes"
  completed: "2026-08-18"
  tasks: 3
  commits: 3
requirements: [REQ-21]
---

# Phase 7 Plan 07: Gap Closure — Three of Four, and the Fourth Left Open on Purpose Summary

**Three of `07-VERIFICATION.md`'s four gaps closed: the dashboard parse gate now executes inside
`make verify-offline` (the suite's only skip became a pass — `883 passed, 1 skipped` → `884
passed, 0 skipped`) and was watched going red against deliberately broken JavaScript; five
superseded figures recorded in a dated addendum beside the closing record with not one of them
edited; and a never-true restart clause corrected in place in all three files that carried it.
No criterion verdict moved, no mutation ident was consumed, and criterion 3 stays MET IN PART by
Dan's explicit decision.**

---

## Gap 3 — the gate that could not fire

### The unfixed state, verbatim

```
$ command -v node
(no output — NOT FOUND)

$ ls -d "$HOME"/.nvm/versions/node/*/bin/node
/home/dan/.nvm/versions/node/v24.16.0/bin/node
```

**Node was NOT on PATH in the executor's shell**, so the off-PATH claim was measurable directly
and no `PATH` stripping was needed to observe it. The `make` half was measured by running the
check *inside a recipe* rather than inferring that the environments match:

```
$ make -f <scratch>.mk nodecheck
NO NODE IN MAKE RECIPE
make PATH=/home/dan/bin:/home/dan/.local/bin:/home/dan/development/flutter/bin:...:/usr/bin:/snap/bin
```

The suite before any edit:

```
$ .venv/bin/python -m pytest tests/ -q -rs
=========================== short test summary info ============================
SKIPPED [1] tests/test_dashboard.py:491: no JavaScript runtime on PATH; the parse check is opportunistic
883 passed, 1 skipped in 11.08s
```

**One skip in the entire suite, and it was this test** — the gate added at `9e7d302` on
2026-08-17 specifically to catch a page that had just stopped parsing.

### The fixed state, verbatim

```
$ .venv/bin/python -m pytest tests/ -q -rs
884 passed in 11.14s
```

**The pass count rose by exactly one from the 883 recorded above, and the skip count went to
zero.** That is the same test counted differently, not a new test. Nothing else moved.

### The red-watch, verbatim

Break applied: the single line `const gate_red_watch = ;` inserted immediately after the opening
`<script>` tag of `served/boty/index.html` (line 108). The shape carries no backtick and no HTML
comment, so the comment-shape test cannot be what kills it, and it touches no interpolation, no
`1800` and no `5400`.

```
$ .venv/bin/python -m pytest tests/test_dashboard.py -q
E       AssertionError: the dashboard's script does not parse, so the page renders nothing:
E         /tmp/tmpopaprrpn/dashboard.js:2
E         const gate_red_watch = ;
E                                ^
E         SyntaxError: Unexpected token ';'
E         Node.js v24.16.0
E        +  where 1 = CompletedProcess(args=['/home/dan/.nvm/versions/node/v24.16.0/bin/node', '--check', ...
FAILED tests/test_dashboard.py::test_the_dashboard_script_parses - AssertionE...
1 failed, 16 passed in 0.05s
EXIT=1
```

**Exit 1. Exactly one test failed** — which is what proves the parse gate and nothing else is
what bound. The failure names `test_the_dashboard_script_parses` and carries node's own parse
error. **And the `args=` line shows node resolved from `/home/dan/.nvm/...`, which is the direct
evidence that the new glob search is what found it** — that path is unreachable via `PATH`.

Revert proved:

```
$ git checkout -- served/boty/index.html
$ git status --porcelain
 M Makefile
 M tests/test_dashboard.py
```

`served/boty/index.html` is absent from the list; only the two intended files remain.

### The nodeless-host measurement, verbatim

```
$ TMPH=$(mktemp -d)
$ env -i HOME="$TMPH" PATH=/usr/bin:/bin .venv/bin/python -m pytest \
    tests/test_dashboard.py::test_the_dashboard_script_parses -q -rs
SKIPPED [1] tests/test_dashboard.py:560: SKIPPED, NOT PASSED: nothing below has been
checked, and the dashboard's script may or may not parse. No JavaScript runtime was found
in any of: `node` on PATH, `nodejs` on PATH, ~/.nvm/versions/node/*/bin/node,
~/.local/share/fnm/node-versions/*/installation/bin/node, ~/.volta/tools/image/node/*/bin/node,
~/.asdf/installs/nodejs/*/bin/node. If this host HAS a runtime somewhere else, that is a
missing entry in NODE_SEARCH_GLOBS and not an acceptable skip — add it, because a gate that
cannot fire reads exactly like one that passed.
1 skipped in 0.01s
```

**This is the evidence that a contributor without node is unaffected, rather than the claim that
they are.** The two cases are distinguished by execution, in the same task, one after the other:
the same test EXECUTES here and SKIPS there.

`tests/test_verify_makefile.py` after the flag change: **8 passed** (it runs the real Makefile
against a stub interpreter, so it is the gate on the change rather than a formality).

### What changed, and what it deliberately did not

`tests/test_dashboard.py` gained `NODE_SEARCH_GLOBS` (four real version-manager layouts — nvm,
fnm, volta, asdf) and `_js_runtime()`, which tries `node` then `nodejs` on `PATH` and only then
expands the globs. **Standard library only** — `shutil`, `glob`, `os.path` — so
`REQUIREMENTS.md` § Non-Functional's small-dependency-surface rule is untouched, **no package was
installed, and no legitimacy gate was triggered.** `Makefile`'s test stage reads `pytest tests/
-q -rs`; that is a **flag, not a stage**, so README's `| Stage | Proves |` table is correctly
untouched and `test_the_documented_stages_are_the_stages_verify_runs` still passes.

**The search widened; the requirement did not.** Nothing is installed and nothing is required.

---

## Gaps 1 and 2 — two wrong sentences, fixed in opposite ways

### Every figure re-measured, with the claimed figure beside it

Measured 2026-08-18 at HEAD `85b337d`, each by its own command. **Nothing was copied from
`07-VERIFICATION.md`, `07-REVIEW.md` or the plan.**

| Figure | Claimed (record, 2026-08-17 pre-review) | Measured 2026-08-18 | Command |
|---|---|---|---|
| `Result(` sites | `all 20` | **21** | AST walk over `boty/retailers.py`; the asserting gate passes standalone (2 passed) |
| read/non-read partition | `11 / 9` | **12 / 9** | same AST gate |
| offline suite | `865 passed` | **884 passed, 0 skipped** | `make verify-offline` |
| mutation ratio | `33/33`, "rose from 26/26 to 33/33" | **34/34**, survivors 0 | `make verify-offline`; registry read with comment lines filtered |
| identity check | `PASS — 220 file(s)` | **PASS — 224 file(s)** | `make verify-offline` |

**Two differ from `07-VERIFICATION.md`'s own 2026-08-17 reading, and both are recorded with
their dates rather than reconciled away.** That verifier measured `883 passed, 1 skipped` and
`identity 222 file(s)` at HEAD `9e7d302`:

- The suite figure moved because Task 1 made the skipping gate execute — the pass count rose by
  one and the skip count fell to zero. Same test, counted differently.
- The identity count moved 222 → 224 because two planning documents were committed between those
  heads (`07-VERIFICATION.md` at `bec5bd1` and `07-07-PLAN.md` at `f0cd4e3`). The count doing its
  job, not drift.

Registry read with comment lines filtered: **34 idents, `M1`–`M20` and `M25`–`M38`.** M38 was
already registered by the WR-01 fix, so the closing record's `33/33` was one behind.

### The nine review findings, established from `git log`

Nine `fix(07):` commits, one per finding: CR-01 `b1a3b88`, WR-01 `6879a6f`, WR-02 `1092940`,
WR-03 `bad7a63`, WR-04 `e986d01`, WR-05 `d140aa4`, WR-06 `a077b2e`, WR-07 `d34468a`, WR-08
`bc23a02`.

**Every one carries a `Watched going red:` paragraph with a failure count except `bc23a02`
(WR-08)**, which is a docstring rewrite that adds no gate and therefore has none to watch —
counted by grepping each commit message, not assumed.

**`9e7d302` is a follow-up to the CR-01 fix, not a tenth finding.** The CR-01 fix's own comment
went inside the row's template literal, a backtick closed the literal, and the page stopped
parsing while every structural assertion stayed green. That is the whole reason the gate Task 1
repaired exists at all — which is the sentence tying Gap 3 to Gaps 1 and 2.

### The two treatments, stated once

- **Gap 1 — recorded BESIDE, not one figure edited.** The five figures were *true when written*:
  a measurement taken 2026-08-17 before a code review existed. A measurement does not become
  false; it becomes **superseded**. Editing them would destroy the evidence that a review
  happened at all, which is the only reason anybody would later know to look. This file's settled
  practice (§ *Amazon*'s dated historical verdict; five closing records each sitting beside the
  last). **Asserted by command that each superseded token is still present verbatim.**
- **Gap 2 — corrected IN PLACE, in every file that carried it.** There is no instant at which the
  removed clause was accurate, so there is nothing to date and nothing to supersede. A false
  claim left standing with a note beside it is still a published false claim.

Both treatments now sit in one document, so the rule distinguishing them is **stated explicitly**
in the addendum rather than left for a reader to infer as an inconsistency.

### The restart correction

The clause occurred in **three** files — `.planning/ROADMAP.md`, `docs/retailer-evidence.md`, and
`.planning/REQUIREMENTS.md`'s REQ-21 traceability cell, **the third found by re-grepping rather
than from the verification report, which named two.** It now occurs **zero** times across all
three, asserted by command.

The replacement quotes `tests/test_cli_watch.py`'s own words: a restart **modelled** as two
`watch_loop` calls sharing one `state_path`, each building its own `State` and `Pacer` so only
the file crosses between them, with **both ends asserted** — the bytes on disk and what a fresh
`State.load` makes of them. It states explicitly that **no process boundary was crossed and no
test in this phase crosses one**, because a reader who remembers the old claim needs to see it
denied rather than merely absent.

**The behavioural claim is not weakened by one word.** The age survives a real file round-trip,
it is not invented on load, and a stamp read back in the future or as a string or as a `True` is
discarded rather than believed. `CAUGHT M32 boty/monitor.py: 7 test(s) failed` re-measured today
and intact. **No subprocess test was written** — the fix is honesty about the evidence, not new
evidence.

### Where the addendum landed

- `docs/retailer-evidence.md` — `## Phase 7 post-review addendum (2026-08-18)`, appended after § 7
  of the closing record, carrying the nine findings, the claimed-against-measured table, the gate
  progression with the skip count, the restart correction recorded as a correction, the stated
  rule, and what did not move. **No bare verdict-shaped line**; `tests/test_evidence_check.py`
  re-run immediately after writing: **74 passed**.
- `.planning/ROADMAP.md` — the same in short form, immediately below the outcome paragraph and
  **above** the verdict table, citing the evidence document for the full working.
- `.planning/REQUIREMENTS.md` — a fourth dated note below the traceability table, beside the
  three that already live there.

---

## What did NOT move

- **Criterion 3 stays MET IN PART.** `status.json` publishes `read_at`, `checked` and
  `current_interval_seconds` and **no staleness verdict**. No `stale` key, no `stale_after` key,
  no derived field, and **no inline suggestion of one** anywhere this plan wrote. Dan's explicit
  decision; the plan fenced it three ways and all three were respected.
- **Criterion 5 stays MET IN PART.** This plan closes the **third** of its three named reasons.
  **(a)** 07-05's join test never observed failing and **(b)** CR-01's escaping gate that existed
  and could not bite **both stand unchanged**. Closing one of three is not closing the criterion,
  and the addendum says so in those words.
- **No criterion text** anywhere in `ROADMAP.md` was reworded, shortened, merged or amended —
  asserted by command: **34 criterion bodies at baseline, 34 now, none removed, none added.**
- **REQ-21's body is byte-identical** after whitespace normalisation, asserted by command.
- **The mutation registry is untouched: 34 idents, `M1`–`M20` ∪ `M25`–`M38`. M39 is still free
  and M21–M24 are still Phase 6's deliberate gap.**

### Why a runtime-conditional gate gets no mutation

Argued rather than omitted. The obvious mutation would break the page's JavaScript and require
the parse gate to kill it. On a box with a runtime it would be **CAUGHT**; on a contributor's box
with none the test skips, the mutation **SURVIVES**, and `make verify-offline` fails for somebody
whose tree is perfectly correct. That converts an opportunistic gate into a **host-dependent
failure**, which is worse than the gap it was meant to close — and it is `mutation_check.py`'s
own rule that a gate whose verdict depends on the host is not a gate. Recorded here and in
STATE.md so the next plan reaching for M39 meets the argument rather than re-deriving it.

---

## `make verify-offline`, run AFTER the record was written

```
identity check: PASS — 224 file(s), no host identity found
All checks passed!
884 passed in 10.93s
Success: no issues found in 18 source files
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 34 mutation(s), sandboxed (the working tree is never touched)
mutation check: 34/34 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
EXIT=0
```

**It matches the Task 2 reading exactly** — identity 224, 884 passed, 0 skipped, 34/34, survivors
0 — so nothing moved between the two runs. `scripts/identity_check.py --all`: **PASS — 224
file(s), no host identity found**.

---

## Deviations from Plan

**1. [Rule 1 — Bug in the plan's own verification command] The ROADMAP placement assertion
compared against the wrong table.**

- **Found during:** Task 2 verification.
- **Issue:** The plan's check was
  `road.index('post-review addendum') < road.index('| # | Verdict | Measurement or reason |')`.
  `.index()` returns the **first** occurrence, and `ROADMAP.md` contains **three** identically
  headed verdict tables (lines 216, 290, 443) — one per phase. It compared the Phase 7 addendum
  against an **earlier phase's** table and failed despite correct placement.
- **Fix:** Scoped the assertion to the Phase 7 section before comparing. Measured: addendum at
  section offset 2005, verdict table at 3894 — **the correction is met before the figures it
  corrects**, which is what the plan actually required.
- **No document was changed to satisfy the flawed command.**

**2. [Rule 1 — my own prose broke a gate I had just written] The addendum quoted the removed
sentence verbatim, defeating the gate that keeps it gone.**

- **Found during:** Task 2 verification — the zero-occurrence assertion reported 2 hits in
  `docs/retailer-evidence.md`, both in my own new addendum, which quoted the removed clause in
  order to record the correction.
- **Tension:** the plan asked for the removed sentence to be **quoted**, and also asserted the
  phrase must occur **zero** times. Both cannot hold.
- **Fix: the prose was rewritten, not the gate weakened** (07-05 and the CR-01 fix set the
  precedent). The addendum now describes precisely what the clause claimed — a restart qualified
  as *real* and as *two-process* — names all three sites it stood in, and states **why** the
  exact phrase is not reproduced: a record quoting it verbatim would be a record that defeats the
  gate keeping it gone. The original wording remains recoverable from git history at `f0cd4e3`.

**3. [Observation, no action taken] A fourth occurrence of the phrase exists, in
`.planning/phases/07-a-reading-has-an-age/07-06-PLAN.md:661`.**

- Left **deliberately unedited**. The plan's scope fence protects planning documents — *"a
  planning document is the record of what was believed when the work was scoped"* — and names
  `07-CONTEXT.md`, `07-PATTERNS.md` and `07-PLAN-OUTLINE.md` in that class; `07-06-PLAN.md` is
  the same class. The plan's own verification command scopes the zero-occurrence assertion to
  exactly the three published documents, all three of which are clean. The remaining hits across
  the tree are `07-06-PLAN.md`, `07-07-PLAN.md` and `07-VERIFICATION.md` — all records of what
  was believed or found at a past instant. **Recorded here rather than silently absorbed**, since
  the plan's `must_haves` phrased this as "appears NOWHERE in the tree".

**4. [Plan expectation not borne out — recorded as measured] No `gsd-tools` misfire occurred,
because the tool was not invoked.**

- The plan warned to *"expect `gsd-tools state advance-plan` to misfire"*. It was **not invoked
  at all**, on 07-06's precedent and the thirteen recorded misfires. A `cp` of STATE.md was taken
  first regardless, and every delta was written by hand. Diffed after: only the intended lines
  changed, **all 54 frontmatter comment lines survive**, the `percent`-is-phase-based comment is
  intact, and `milestone: v0.3` is untouched (`tests/test_packaging_metadata.py` green after the
  edit). **The misfire count still stands at THIRTEEN.**

---

## Constraints honoured

No live retailer read and `make verify` (live) was not run. The daemon was not restarted and no
restart is recommended. `WALMART_STORE_ID` was never read, derived, inferred or printed, and
nothing ran under the service's `EnvironmentFile`. No package dependency was added. No Artifact
was built. `milestone: v0.3` untouched. Changed-file set inside the allow-list, asserted by
command against both the uncommitted diff and everything committed since `f0cd4e3`.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 | `85b337d` | `fix(07-07)`: the parse gate had never once fired inside make verify-offline |
| 2 | `bf64d58` | `docs(07-07)`: five superseded figures recorded beside, one never-true clause corrected in place |
| 3 | (this commit) | `docs(07-07)`: STATE.md by hand, and the phase's record now matches the tree |
