---
phase: 07-a-reading-has-an-age
verified: 2026-08-18T13:22:30Z
verified_at_head: 580af4a
status: gaps_found
score: 4/5 must-haves verified (1 accepted by override, 1 MET IN PART with no override)
overrides_applied: 1
overrides:
  - must_have: "SC-3: A reading older than its retailer's current interval is presented as stale in `status.json`, `boty check` and the dashboard, and the staleness is derived from the retailer's own pacing rather than a fixed clock"
    reason: "`status.json` publishes `read_at`, `checked` and `current_interval_seconds` and no derived verdict, because a `stale` boolean computed at write time is written `false` and keeps saying `false` for exactly the interval during which it becomes true (`pacing.py:196-199`'s recorded lesson, argued at `boty/status.py:280-289`). Joint sufficiency is proved by `tests/test_status.py:1243`, which derives the verdict from those three keys and nothing else. Both rendering consumers do present the verdict — re-executed at this HEAD. The two rendering thirds are MET; the `status.json` third is deliberately left as ingredients."
    accepted_by: "dan"
    accepted_at: "2026-08-18"
    evidence_of_acceptance: "Recorded in the repository, not witnessed by this verifier: `.planning/STATE.md` § Status — `OPEN, BY DAN'S EXPLICIT DECISION — criterion 3's status.json third … Dan chose to leave this MET IN PART. It is not an oversight, not a TODO and not work queued for a later plan`; `07-07-SUMMARY.md` decisions — `status.json still publishes no staleness verdict, by Dan's decision; criterion 3 stays MET IN PART`. Date is day-precision because that is the precision the record carries."
re_verification:
  previous_status: gaps_found
  previous_score: 3/5
  previous_head: 9e7d302
  gaps_closed:
    - "Gap 3 — the dashboard parse gate could not fire inside `make verify-offline`. Independently re-executed: the gate now EXECUTES (1 passed) under the node-free PATH `make` inherits, was watched RED by this verifier against deliberately broken JavaScript (1 failed / 16 passed, EXIT=1, node resolved from `/home/dan/.nvm/...`), and still SKIPS with a reason naming all six search locations under `env -i HOME=<empty> PATH=/usr/bin:/bin`."
    - "Gap 1 — the closing record misstated the tree on five measurable numbers. All five superseded figures re-measured present VERBATIM and unedited (`all 20`, `11 / 9`, `865 passed`, `33/33`, `220 file(s)`), with dated 2026-08-18 addenda beside them in all three documents. The addendum's own figures re-measured true at this HEAD."
    - "Gap 4 — the `real two-process restart` clause. Zero occurrences in all three published documents, counted by this verifier: `.planning/ROADMAP.md` 0, `docs/retailer-evidence.md` 0, `.planning/REQUIREMENTS.md` 0."
  gaps_remaining:
    - "SC-5's `every gate` half — one of three named reasons closed; the join test never watched red still stands and is decisive on its own."
  regressions: []
  new_findings:
    - "The never-true clause still stands, unrecorded, at `.planning/phases/07-a-reading-has-an-age/07-06-PLAN.md:661` — and the published addendum names three sites without disclosing a fourth."
    - "`_js_runtime()` accepts the first glob match without asking whether it works. Measured: a two-line shell script named `node` in a fake `~/.nvm` root makes the gate report `1 passed` against deliberately broken JavaScript."
gaps:
  - truth: "SC-5: `make verify-offline` exits 0, and every gate this phase adds has been watched going red"
    status: partial
    reason: "The gate half is MET and re-measured at this HEAD by this verifier: identity PASS 225 file(s), 884 passed / 0 skipped, mypy clean over 18 source files, 34/34 mutations CAUGHT, survivors 0, `VERIFY: PASS (OFFLINE …)`, EXIT=0. The `every gate` half is not fully MET. 07-07 closes the THIRD of the three named reasons and the executor's claim that the criterion does not move is CORRECT — independently assessed: reason (a), 07-05's join test `test_status_json_carries_everything_a_consumer_needs_to_judge_staleness`, passed on the RED commit and was never observed failing. That is a historical fact about this phase that no later work can change except by manufacturing a red (which this project calls theatre) or by an accepted override. Reason (a) alone is decisive, so the verdict would not move even if reason (b) — CR-01's escaping gate that existed and could not bite — were scored as closed by the widened `UNTRUSTED` tuple (`w.availability` present at `tests/test_dashboard.py:173`, re-confirmed here)."
    artifacts:
      - path: "tests/test_status.py:1243"
        issue: "Join test exists and passes (re-run standalone: 1 passed, 51 deselected). Never watched red — recorded honestly by 07-05, not hidden."
    missing:
      - "A decision, not code: either an accepted override for the join test (the reason is already written and defensible), or the record left at MET IN PART. This is the only thing standing between this phase and a full pass."
  - truth: "The never-true restart clause appears NOWHERE in the tree (07-07-PLAN.md must_have, verbatim)"
    status: partial
    reason: "Counted by this verifier across the whole tree, not taken from the SUMMARY. The three PUBLISHED documents are clean: 0 occurrences each. Four files still carry the phrase: `07-07-PLAN.md` (10), `07-VERIFICATION.md` (5), `.planning/STATE.md` (1) — all records OF the correction, unavoidable and correct — and `07-06-PLAN.md:661` (1), which is a record of the DEFECT. The executor's argument that a planning document is a record of what was believed at scoping time is CORRECT and matches this project's five-times-applied convention (`docs/retailer-evidence.md:4355-4361`, and the `_flattened_exit_codes` precedent at 3890-3898). But that convention has TWO halves and only one was honoured: in both precedents the planning document was left unedited AND the error was named in the evidence record. The 07-07 addendum names three sites and does not disclose the fourth, so the published correction record claims more completeness than the tree supports. The occurrence is also not a superseded measurement — it is an INSTRUCTION (`read the SUMMARY and quote it: … the age observed surviving a real two-process restart`), i.e. the line that propagated the false claim into the three published documents, and the class 07-07's own stated rule assigns to correction rather than to dating."
    artifacts:
      - path: ".planning/phases/07-a-reading-has-an-age/07-06-PLAN.md:661"
        issue: "Instructs the closing-record writer to quote a claim that was never true. Unmarked, so a future closing-record plan using 07-06-PLAN as a template re-emits it."
      - path: "docs/retailer-evidence.md:4601-4607"
        issue: "The addendum's `Removed.` paragraph enumerates three sites the clause stood in and does not name the fourth occurrence that remains in the tree."
    missing:
      - "One sentence in `docs/retailer-evidence.md` § *Phase 7 post-review addendum* (or § 6, which is this project's own section for exactly this class) naming `07-06-PLAN.md:661` as a fourth site, left unedited on the planning-document convention. Do NOT edit `07-06-PLAN.md` — the convention against that is correct."
  - truth: "The repaired parse gate cannot report a pass it did not earn"
    status: partial
    reason: "WARNING, not a blocker — the gate is a real improvement on what it replaced and it bit correctly on this host. But `_js_runtime()` returns `sorted(glob.glob(...))[0]` and never asks whether the thing it found can answer `--check`. Measured by this verifier, not argued: with a fake `~/.nvm/versions/node/v99.0.0/bin/node` containing `#!/bin/sh\\nexit 0`, the gate reports `1 passed` against a dashboard whose script does NOT parse — a false green in the exact shape this phase exists to prevent. Two adjacent measurements for calibration: a non-executable file at the same path raises `PermissionError` and the test FAILS loudly (correct), and the sort is lexicographic, so a host with v9 and v10 selects `v10.0.0` before `v9.0.0` — a stale-runtime risk that fails in the safe direction (false RED). The pre-07-07 `shutil.which(\"node\")` had the same shim weakness, so this is an unhardened edge rather than a regression 07-07 introduced."
    artifacts:
      - path: "tests/test_dashboard.py:84-92"
        issue: "First match wins with no sanity check; nothing asserts the found runtime is a working JavaScript engine."
    missing:
      - "A one-line self-test before trusting the runtime — e.g. assert that `[node, '--check']` on a known-bad snippet returns non-zero, or that `[node, '--version']` exits 0 — so a shim on PATH or in a version-manager root cannot make the gate report a pass it did not earn"
deferred: []
human_verification:
  - test: "Decide SC-5's `every gate` half: accept the join test's never-red status as an override (the reason is already drafted in the superseded section below), or leave the record at MET IN PART"
    expected: "Either an `overrides:` entry, or an explicit restatement that MET IN PART is the settled verdict"
    why_human: "Not a code question. The join test passed on the RED commit, which IS the measurement that the three published facts were already jointly sufficient. Manufacturing a red would be theatre. Only Dan can decide which of those two records the phase closes with."
  - test: "Decide whether `sudo systemctl restart boty` happens. Re-measured 2026-08-18 13:22Z: `served/boty/status.json` (mtime 08:15 today) carries 5 watch rows, 0 with a `read_at` key, 0 with a `checked` key, and 6 retailer rows, 0 carrying `current_interval_seconds`. `state.json` still holds 13 bare pre-07 strings and 0 stamps."
    expected: "Either a restart, or the deferral restated with its date"
    why_human: "Deploy is the user's explicit decision, answered `keep defer` on 2026-08-17 and `defer` on 2026-08-10. Not performed and not recommended here. The row count moved 10 → 5 since yesterday, which is pacing, not decay."
  - test: "Look at the dashboard in a GPU-backed browser with a payload carrying mixed fresh/stale/undated rows"
    expected: "Dim `.tag.age` on fresh rows, amber `.tag.age.warn` on stale and undated rows, `not checked` beside remembered rows"
    why_human: "Visual weight and legibility. The markup and the branch logic are re-verified by execution below; how it LOOKS is not."
---

# Phase 7: A Reading Has an Age — Verification Report

**Phase Goal:** Every reading says when it was taken, and a reading too old to trust is shown as stale rather than as fact — or says it does not know.
**Re-verified:** 2026-08-18T13:22:30Z at HEAD `580af4a`
**Status:** gaps_found (4/5, one by override, one partial with no override)
**Re-verification:** Yes — after 07-07's gap closure. The 2026-08-17 pass at `9e7d302` is preserved **verbatim and unedited** at the foot of this file, marked superseded, on this project's own convention that a superseded measurement is recorded beside rather than edited away.

Every figure in this section came from a command run by this verifier on 2026-08-18. Nothing was
taken from `07-07-SUMMARY.md`, from `07-07-PLAN.md`, or from the orchestrator's re-confirmation.
Where the two disagree, both readings are printed with their heads.

## Goal Achievement

### Observable Truths — the ROADMAP's five Success Criteria

Criterion text re-read at `.planning/ROADMAP.md:397-401` and **unchanged** from the 2026-08-17 pass.

| # | Truth | Status | Evidence (measured at HEAD `580af4a`, 2026-08-18) |
|---|-------|--------|----------|
| 1 | Every `Result` records when it was read, and that time is published per watch in `status.json` | ✓ VERIFIED **in the tree**; NOT on the wire | Independent AST walk over `boty/retailers.py`: **21** `Result(` sites, **21/21 name `read_at`**, partition **12 read / 9 literal-`None`** — the addendum's figures, re-derived rather than read. Asserting gate standalone: **2 passed**. Executed `status.write` against the **real** `config/products.yaml` (13 watches) and the **real** `state.json`: **13 rows, 13/13 carry `read_at`**, `"read_at": 0` absent from the bytes, row keyset enumerated. Wire measured separately below |
| 2 | A reading with no recorded time is shown as UNKNOWN age, never as current — watched going red | ✓ VERIFIED | Re-executed `boty.cli._age_tag` at this HEAD: `undated → [age ?]`, `fresh → [age 4s]`, `stale → [age 7h > 6h]`, `no cadence → [age 3h, cadence ?]`. Re-executed `ageTag` lifted out of `served/boty/index.html` in node v24.16.0: `read_at: null → age ?` **warn**, **missing key → same warn**. `CAUGHT M36 boty/cli.py: 1 test(s) failed — test_report_says_unknown_for_a_reading_nobody_dated` in this verifier's own mutation run today |
| 3 | A reading older than its retailer's current interval is presented as stale in `status.json`, `boty check` **and** the dashboard, derived from the retailer's own pacing | ⚠️ **PASSED (override)** — MET IN PART, accepted by Dan | **Rendering thirds re-MET by execution:** `[age 7h > 6h]` from the CLI, `<span class="tag age warn">…7h ago > 6h</span>` from the page, both reading the cadence from `intervals.get(w.retailer)` and never from the banner constant — `CAUGHT M37 served/boty/index.html: 1 test(s) failed` today. **`status.json` third unchanged and deliberately so:** executed `status.write` shows **0 rows with a `stale` key and 0 with a `stale_after` key**. Nothing was added to make this row read MET. Override recorded in frontmatter; acceptance sourced from `STATE.md` and `07-07-SUMMARY.md`, not witnessed here |
| 4 | The age survives a service restart, so a restart cannot make a two-day-old reading look fresh | ✓ VERIFIED — behaviour **and** description now agree | Behaviour re-executed through real bytes: a stamp two days old written by `State.save` reads back **bit-identical** (`1786886154.2035534`), and the reload's own age computes to **2.000 days**. Hostile stamps re-executed against `_remembered_stamp`: `True` → `None`, `"1000000"` → `None`, `now + 10 000 000` → `None`, below-floor → `None`, **availability preserved in every case**. `CAUGHT M32 boty/monitor.py: 7 test(s) failed` today. **Description now matches:** `real two-process restart` occurs **0 times** in all three published documents (counted by this verifier); `grep -rn subprocess tests/test_monitor.py tests/test_cli_watch.py` still returns nothing and the corrected text now **says so in as many words** |
| 5 | `make verify-offline` exits 0, and every gate this phase adds has been watched going red | ⚠️ **MET IN PART** — one of three reasons closed | **Gate half MET, re-run once end-to-end today:** `identity check: PASS — 225 file(s)`, `884 passed in 11.34s` (**0 skipped**), `Success: no issues found in 18 source files`, `mutation check: 34/34 mutations caught`, survivors none, `VERIFY: PASS (OFFLINE …)`, `EXIT=0`. **`every gate` half still not MET.** Reason (c) — the parse gate that skipped — is genuinely closed and re-proved three ways below. Reason (a) — the join test never watched red — **stands and is decisive alone**. See gap 1 |

**Score:** 4/5 — three VERIFIED, one PASSED (override), one MET IN PART with no override.
The 2026-08-17 pass scored 3/5. The delta is criterion 4 (gap closed) and criterion 3 (override
accepted); criterion 5 is unmoved, which is what 07-07 itself claimed and what I independently
confirm below.

---

## The three closures, verified by execution rather than by reading the report

### G3 — the gate about gates. Three separate measurements, all reproduced

This is the one the prompt weighted highest, so it got three independent checks rather than one.

**First: does it EXECUTE in the environment `make` actually runs in?** My own shell is node-free,
the same condition the 2026-08-17 pass measured:

| Probe | Result |
|---|---|
| `command -v node` | **NOT FOUND** |
| `command -v nodejs` | **NOT FOUND** |
| the same check *inside a `make` recipe* (scratch makefile) | **`NO NODE IN MAKE RECIPE`** |
| `pytest tests/test_dashboard.py::test_the_dashboard_script_parses -q -rs` | **1 passed** (was `1 skipped` at `9e7d302`) |
| `_js_runtime()` called directly | `('/home/dan/.nvm/versions/node/v24.16.0/bin/node', '~/.nvm/versions/node/*/bin/node')` |

So the pass is genuinely produced by the glob and not by a PATH that happens to differ from the
one `make` sees. The whole-suite figure agrees: **884 passed, 0 skipped** inside `make
verify-offline`'s own transcript, against `883 passed, 1 skipped` at `9e7d302`. **Pass count +1,
skip count −1: the same test counted differently, not a new test.**

**Second: does it BITE?** Reproduced in a throw-away `git worktree` at `580af4a`. The working tree
was never touched — `git status --short` was empty before and is empty after, and the worktree is
removed and pruned.

```
break: `const gate_red_watch = ;` inserted immediately after <script> (line 108)

E         SyntaxError: Unexpected token ';'
E         Node.js v24.16.0
E        +  where 1 = CompletedProcess(args=['/home/dan/.nvm/versions/node/v24.16.0/bin/node',
                                             '--check', '/tmp/tmperpajsxf/dashboard.js'], ...)
FAILED tests/test_dashboard.py::test_the_dashboard_script_parses
1 failed, 16 passed
EXIT=1
```

**Exactly one test failed**, which is what proves the parse gate and nothing else is what bound —
the comment-shape test and the escaping test stayed green on a page the browser would refuse to
run, which is precisely the blindness this gate exists to end. The `args=` line is the direct
evidence that the nvm path — unreachable via `PATH` — is what answered.

**Third: does it still SKIP rather than pass green where no runtime exists?**

```
$ env -i HOME=<fresh empty dir> PATH=/usr/bin:/bin .venv/bin/python -m pytest \
    tests/test_dashboard.py::test_the_dashboard_script_parses -q -rs
SKIPPED [1] tests/test_dashboard.py:560: SKIPPED, NOT PASSED: nothing below has been checked …
No JavaScript runtime was found in any of: `node` on PATH, `nodejs` on PATH,
~/.nvm/versions/node/*/bin/node, ~/.local/share/fnm/…, ~/.volta/…, ~/.asdf/… If this host HAS a
runtime somewhere else, that is a missing entry in NODE_SEARCH_GLOBS and not an acceptable skip
1 skipped in 0.01s
```

All six search locations named, and the reason distinguishes *this host has none* from *this test
did not find the one it has* — which was the entire defect. `Makefile:76` carries `pytest tests/
-q -rs`, so that reason prints inside the gate's own transcript; `tests/test_verify_makefile.py`
**8 passed**, so the stage table is genuinely unaffected. `_js_runtime` uses `shutil`, `glob`,
`os.path` only — **no dependency added**, confirmed by reading the code rather than the claim.

**Where the glob CAN be fooled — measured, and this is a new finding.** The prompt asked, so it
was tested rather than reasoned about:

| Probe | Result | Verdict |
|---|---|---|
| `~/.nvm/versions/node/v99.0.0/bin/node` = `#!/bin/sh` + `exit 0`, against **broken** JS | **`1 passed`** | ⚠️ **false green** — the gate reports a pass it did not earn |
| same path, non-executable garbage file | `PermissionError` → **1 failed** | ✓ fails loudly, correct |
| `v9.0.0` and `v10.0.0` both present | selects **`v10.0.0`** (lexicographic sort) | ⚠️ a stale runtime can be chosen; fails in the **safe** direction (false red) |

The false-green case needs a file named `node` in a version-manager root that is not node, so it
is unlikely — and the pre-07-07 `shutil.which("node")` had the identical weakness, so 07-07 did
not introduce it. But *a gate that can report a pass it did not earn* is this phase's own subject,
and one line (`--version` exits 0, or a known-bad snippet returns non-zero) closes it. Recorded as
gap 3, WARNING, not a blocker.

### G1 — superseded figures present verbatim, addendum dated, addendum's own numbers re-measured

**The five superseded figures are unedited and still readable in place** — grepped for, not taken
on trust:

| Superseded token | Still present at | Edited? |
|---|---|---|
| `all 20` `Result(` sites | `ROADMAP.md:445`, `retailer-evidence.md:4097`, `REQUIREMENTS.md:29` | **No** |
| `11 / 9` | same three | **No** |
| `865 passed` | `ROADMAP.md:457`, `retailer-evidence.md:4126`, `:4155-4156` | **No** |
| `33/33`, `rose from 26/26 to 33/33` | `ROADMAP.md:462,467`, `retailer-evidence.md:4131,4155-4156`, `REQUIREMENTS.md:29` | **No** |
| `220 file(s)` | `ROADMAP.md:455`, `retailer-evidence.md:4124`, `:4587` | **No** |

The addenda are dated **2026-08-18**, name the HEAD they measured (`85b337d`), state *why* the
figures moved (a code review found one Critical and eight Warnings, all nine fixed, nine `fix(07):`
commits), and say in as many words that a measurement does not become false but superseded.
Placement checked: `ROADMAP.md:416` sits **above** the Phase 7 verdict table at `:443`, so a reader
meets the correction before the figures it corrects.

**The addendum's own numbers, re-derived at HEAD `580af4a` rather than inherited:**

| Addendum claims (at `85b337d`) | This verifier measures (at `580af4a`) | Agrees? |
|---|---|---|
| 21 `Result(` sites | **21** (own AST walk) | ✓ |
| partition 12 / 9 | **12 / 9** (own AST walk) | ✓ |
| 884 passed, 0 skipped | **884 passed in 11.34s, 0 skipped** | ✓ |
| 34/34, survivors 0 | **34/34 caught, survivors none**; registry reads **34 idents, M1-M20 ∪ M25-M38**, M39 free | ✓ |
| identity `PASS — 224 file(s)` | **PASS — 225 file(s)** | ⚠️ **one behind, and correctly so** |

The identity figure is **not** a defect: the addendum names the head it measured (`85b337d`), and
`07-07-SUMMARY.md` was committed afterwards at `580af4a`. That is the count doing exactly the job
the addendum says it does. Recorded here rather than reconciled away, on the same convention.

### G2 — zero in the three published documents; one still standing elsewhere, and unrecorded

Counted by this verifier across the whole tree, `.git`/`.venv`/caches excluded:

| File | Occurrences of `real two-process restart` | What the occurrence IS |
|---|---|---|
| `.planning/ROADMAP.md` | **0** | corrected in place; now `modelled as two watch_loop calls … No process boundary was crossed` |
| `docs/retailer-evidence.md` | **0** | same, with the correction recorded as a correction at `:4596-4626` |
| `.planning/REQUIREMENTS.md` | **0** | same, in the REQ-21 traceability cell — the third site the 2026-08-17 pass did not name |
| `07-07-PLAN.md` | 10 | the plan that removes it — a record OF the correction |
| `07-VERIFICATION.md` | 5 | this file's own superseded section — a record OF the finding |
| `.planning/STATE.md` | 1 | `CLOSED — the record claimed …` — a record OF the closure |
| **`07-06-PLAN.md:661`** | **1** | a record of the **DEFECT**, unmarked |

**Judging the executor's argument, as asked.** Its argument — *a planning document is the record of
what was believed when the work was scoped* — is **correct**, and it is this project's own
convention, stated at `docs/retailer-evidence.md:4355-4361` and applied five times in this phase
alone, with an earlier precedent at `:3890-3898` (`06-PATTERNS.md` and `06-PLAN-OUTLINE.md` both
name a function `_flattened_exit_codes` that does not exist; **neither document was edited**).
So **07-06-PLAN.md should NOT be edited**, and the executor was right to fence it.

**But that convention has two halves and only one was honoured.** In both precedents the planning
document was left unedited **and the error was named in the evidence record** — §6a and §6b of
`retailer-evidence.md` exist for exactly this. The 07-07 addendum's `Removed.` paragraph enumerates
**three** sites the clause stood in and does not disclose that a fourth occurrence remains in the
tree. `07-07-SUMMARY.md` discloses it honestly (Deviation 3) — but a SUMMARY is not the published
record, and the plan's own `must_haves` said *appears NOWHERE in the tree*.

Two further reasons this one is not quite like the five precedents:

- The `07-06-PLAN.md:661` occurrence is **not a superseded measurement**. It is an *instruction* —
  *"read the SUMMARY and **quote it**: … the age observed surviving a real two-process restart"* —
  i.e. the line that propagated the false claim into all three published documents. 07-07's own
  stated rule assigns that class (*a description of evidence that never existed*) to correction,
  not to dating; the boundary the executor actually drew (published vs planning) is a different
  boundary from the rule it wrote.
- `07-06-PLAN.md` is the template a future closing-record plan would copy. Copying that row
  re-emits the claim.

**Verdict: leaving the line unedited is defensible and correct. Leaving it unrecorded is not.** The
fix is one sentence in the published addendum, not an edit to the plan. Gap 2, WARNING.

### Does closing G3 move criterion 5? No — independently assessed, and the executor is right

Criterion 5's `every gate` half had three named shortfall reasons. Taking them one at a time:

| Reason | State at `580af4a` | Moves the verdict? |
|---|---|---|
| (a) 07-05's join test never observed failing | **Stands.** Test exists at `tests/test_status.py:1243`, re-run standalone: **1 passed**. It passed on the RED commit, before any implementation existed. That is a fact about a past instant; no later work can change it except by manufacturing a red, which this project's own record calls theatre | **No** — and this one is decisive alone |
| (b) CR-01's escaping gate existed and could not bite | The gate is now widened — `UNTRUSTED` at `tests/test_dashboard.py:165-176` includes `w.availability` (re-read at this HEAD), and the 2026-08-17 pass watched it red. Whether this counts as *closed* or as a permanent blemish on the phase's gate discipline is a matter of reading | **Immaterial** — (a) already holds the verdict |
| (c) the parse gate skipped in the project's own gate environment | **Closed**, re-proved three ways above | Not enough on its own |

So the executor's claim — *closing one of three is not closing the criterion* — **holds**, and I
reached it before reading its wording. One further check, because a repair can create the very
defect it fixes: **the newly-executing gate is itself a gate this phase adds, and it HAS been
watched going red** — by the executor, and independently by me at 1 failed / 16 passed. It does not
add a fourth reason. `Makefile`'s `-rs` is a flag, not a stage, so it adds no gate at all
(`tests/test_verify_makefile.py`: 8 passed).

Criterion 5 stays **MET IN PART**. It is now one decision away from full, and that decision is
Dan's, not a code change.

---

## Criteria 1, 2 and 4 re-confirmed by execution, not assumed to have survived

Nine review fixes and a gap-closure plan landed since these were last confirmed. Every check below
was re-run today at `580af4a`.

| Behaviour | Command | Result | Status |
|---|---|---|---|
| Full offline gate, run once end to end | `make verify-offline` | `identity 225 · 884 passed, 0 skipped · mypy 18 files clean · 34/34 · VERIFY: PASS · EXIT=0` | ✓ PASS |
| AST completeness + partition | own AST walk, then `pytest -k "read_at or partition"` | **21 sites, 21/21 name `read_at`, 12 / 9**; gate **2 passed** | ✓ PASS |
| Seven CLI age forms | executed `boty.cli._age_tag` | `[age ?]` · `[age 4s]` · `[age 7h > 6h]` · `[age 3h, cadence ?]` · `[age 5m]` · `[age 5m > 5m]` · `[age 0s]` | ✓ PASS |
| Strict `>` boundary (WR-03 neighbourhood) | exactly one cadence, then one ms past | `[age 5m]` then `[age 5m > 5m]` | ✓ PASS |
| Negative-age clamp (WR-03) | stamp 10 s in the future | `[age 0s]` on the CLI, `0s ago` **non-warn** on the page | ✓ PASS |
| Six dashboard age forms | `ageTag` lifted from `index.html`, node v24.16.0 | `age ?` warn (null **and** missing key) · `4s ago` · `7h ago > 6h` warn · `3h ago · cadence ?` warn | ✓ PASS |
| XSS payload at the dot sink (CR-01) | `esc` from `index.html` | `&quot; onmouseover=alert(1) x=&quot;` — stays inside the attribute | ✓ PASS |
| One row per configured watch | `status.write` with real config + real `state.json` | 13 configured → **13 rows**, 13 `checked: false`, 13 `read_at: null`, **0 `stale`**, **0 `stale_after`** | ✓ PASS |
| Stamp round-trip through real bytes | `State.save` then `State.load` | two-day-old stamp **bit-identical** on reload; age recomputes to **2.000 days** | ✓ PASS |
| Hostile stamps rejected, memory kept | `_remembered_stamp` via a real file | `True` / `"1000000"` / future / below-floor → **`read_at=None`, `seen='IN_STOCK'`** in all four | ✓ PASS |
| No subprocess boundary anywhere | `grep -rn subprocess tests/test_monitor.py tests/test_cli_watch.py` | **nothing** — the corrected wording is accurate | ✓ PASS |
| Restart-model tests | `pytest ::test_the_age_of_a_reading_survives_the_restart ::test_state_survives_a_save_and_reload` | 2 passed | ✓ PASS |
| Parse gate under make's PATH | `pytest ::test_the_dashboard_script_parses -q -rs` | **1 passed** (was 1 skipped) | ✓ PASS |
| Parse gate red-watch | worktree, broken JS | **1 failed / 16 passed, EXIT=1** | ✓ PASS |
| Parse gate on a nodeless host | `env -i HOME=<empty> PATH=/usr/bin:/bin` | **1 skipped**, reason names all six locations | ✓ PASS |
| Makefile stage table unaffected | `pytest tests/test_verify_makefile.py` | 8 passed | ✓ PASS |
| Mutation registry | own read, comment lines filtered | **34 idents, M1-M20 ∪ M25-M38**; M39 free, M21-M24 still Phase 6's gap | ✓ PASS |

### The wire, re-measured rather than assumed

| Artifact on disk | Measured 2026-08-18 13:22Z | Same day before |
|---|---|---|
| `served/boty/status.json` (mtime **08:15 today**, written by the running pre-phase daemon) | **5** watch rows; **0** carry `read_at`; **0** carry `checked`; **6** retailer rows, **0** carrying `current_interval_seconds` | 10 rows on 2026-08-17 |
| `state.json` | **13** entries, **13 bare strings**, **0** stamps | unchanged |

The 5-of-13 row count (down from 10 yesterday) is the phase's own Finding 4 re-confirming itself
live — the served row count is a function of pacing, not of decay. Deploy remains deferred by Dan's
explicit answer (`keep defer`, 2026-08-17). **No restart was performed or recommended here.**

### Requirements Coverage

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| REQ-21 | 07-01 … 07-07 (all seven declare `requirements: [REQ-21]`) | ✓ SATISFIED **in the tree**, criterion 3's `status.json` third accepted as partial by override | Every clause re-traced to executed code above. The requirement's opening measurement — *Walmart's age could not be established at all because a restart zeroed the evidence* — is closed by `State.read_at` + `_remembered_stamp`, re-proved today by a bit-identical two-day round trip and by `CAUGHT M32`. REQ-21's traceability cell now also carries the corrected restart wording and a dated fourth note |

No orphaned requirements: `grep -E "Phase 7" .planning/REQUIREMENTS.md` maps REQ-21 and nothing else.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `.planning/STATE.md` | 142 | the token `TODO` | ℹ️ Info | Inside the sentence *"It is not an oversight, not a **TODO** and not work queued for a later plan"* — a denial, not a debt marker |
| all other 07-07-modified files | — | `TBD` / `FIXME` / `XXX` / `HACK` / `TODO` | — | **0 hits** across `tests/test_dashboard.py`, `Makefile`, `docs/retailer-evidence.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`. Debt-marker gate clean |

### Commits claimed vs commits present

`85b337d`, `bf64d58`, `4826f3c`, `580af4a` all present in `git log`; HEAD is `580af4a`; working
tree clean before and after this verification. The SUMMARY's commit table names three and the
fourth (`580af4a`) is the self-check commit it says it was writing — consistent.

---

## Gaps Summary

Three items, none of them a code defect, and **one of them is a decision rather than work**:

1. **SC-5's `every gate` half.** 07-07 closed the third of three named reasons and correctly said
   so. The join test that was never watched red stands, and it is decisive on its own. This cannot
   be closed by code without manufacturing a red. **It needs an override or an explicit
   MET IN PART, from Dan.**
2. **The never-true clause still stands, unrecorded, at `07-06-PLAN.md:661`.** Not editing the
   plan is right. Not naming it in the published correction record is the gap — one sentence in
   `docs/retailer-evidence.md`.
3. **`_js_runtime()` trusts the first glob match.** Measured: a two-line shim makes the repaired
   gate report a pass on a page that does not parse. Unlikely, pre-existing, one line to close.

### Why the status is `gaps_found` and not `passed`

Stated plainly, because the prompt asked for the reasoning rather than the label.

**What would make it `passed`:** SC-3 is now an accepted partial with Dan's decision recorded in
two in-repo documents, so it counts toward the score as `PASSED (override)`. Criteria 1, 2 and 4
are VERIFIED by execution today. That is 4 of 5.

**What stops it:** SC-5 has **no accepted override**. Its shortfall is real, measurable and
recorded — a gate this phase adds was never watched going red — and the criterion says *every*.
Rounding it up would require me to invent an acceptance nobody has given, in the phase whose entire
thesis is that a claim must not exceed its measurement. Rounding it down to `gaps_found` for the
two WARNING items alone would also be wrong; they are noted as WARNINGs, not blockers, and neither
would hold the phase open by itself.

So: **`gaps_found`, by one item, and that item is a decision Dan can make in a sentence.** If he
accepts the join-test override, the honest re-score is 5/5 with two accepted partials, and the two
WARNINGs go to the next phase's docket rather than blocking this one.

Suggested override, if that is the decision — the reason is already written and already true:

```yaml
overrides:
  - must_have: "every gate this phase adds has been watched going red"
    reason: "07-05's join test passed on the RED commit — that IS the measurement that the three published facts were already jointly sufficient, and manufacturing a red would have been theatre. The other two named reasons are closed (the parse gate, 07-07) or fixed and re-gated (CR-01's escaping gate, now covering w.availability)."
    accepted_by: "dan"
    accepted_at: "{ISO timestamp}"
```

---

_Re-verified: 2026-08-18T13:22:30Z at HEAD `580af4a`_
_Verifier: Claude (gsd-verifier)_
_Method: goal-backward, adversarial. Every figure above came from a command run during this verification — including the ones that agree with `07-07-SUMMARY.md`, which were re-derived rather than accepted. `make verify-offline` was run once, end to end. The daemon was not restarted and no restart is recommended. `WALMART_STORE_ID` was never read, derived or printed. No `gsd-tools state` write subcommand was used._

---
---

# SUPERSEDED — the initial verification, 2026-08-17T14:11:17Z at HEAD `9e7d302`

**This section is the previous pass, preserved verbatim and unedited on this project's own
convention: a superseded measurement is recorded beside rather than edited away.** Everything below
was true when written. Three of its four gaps were closed by 07-07 on 2026-08-18 and one was left
open by Dan's decision; which is which is recorded in the `re_verification` block at the top of this
file. **Do not read the figures below as current** — in particular `883 passed, 1 skipped`,
`identity 222 file(s)` and the four `gaps:` entries have all been superseded above.

Its frontmatter, reproduced here because a file carries only one:

```yaml
phase: 07-a-reading-has-an-age
verified: 2026-08-17T14:11:17Z
verified_at_head: 9e7d302
status: gaps_found
score: 3/5 must-haves verified (2 MET IN PART, independently confirmed as partial)
overrides_applied: 0
gaps:
  - truth: "SC-3: A reading older than its retailer's current interval is presented as stale in `status.json`, `boty check` and the dashboard, and the staleness is derived from the retailer's own pacing rather than a fixed clock"
    status: partial
    reason: "Two of three surfaces verified by execution. `status.json` publishes the three ingredients of a staleness verdict (`read_at`, `checked`, `current_interval_seconds`) and no verdict. `presented as stale` and `sufficient to derive staleness` are different sentences. The phase's own MET IN PART is accurate and is NOT rounded up here."
    artifacts:
      - path: "boty/status.py"
        issue: "No `stale` key on any watch row — deliberate, argued at status.py:280-289 against a write-time flag that would be written `false` and keep saying `false` for exactly the interval during which it becomes true"
    missing:
      - "Either a consumer-computable verdict in `status.json` that cannot go stale at write time (e.g. `stale_after` = read_at + current_interval, a fact rather than a flag), or an accepted override recording that the ingredients-plus-join-test form is the settled answer"
  - truth: "SC-5: `make verify-offline` exits 0, and every gate this phase adds has been watched going red"
    status: partial
    reason: "`make verify-offline` EXIT=0 independently re-run at HEAD 9e7d302 (883 passed / 1 skipped, 34/34 mutations, identity 222 files). The `every gate` half is still not fully met, and the post-review evidence WIDENS the shortfall rather than narrowing it: (a) 07-05's join test `test_status_json_carries_everything_a_consumer_needs_to_judge_staleness` was never observed failing — the phase's own named exception; (b) CR-01 showed the phase's escaping gate could not bite on a sink 07-04 itself opened, i.e. a gate that existed and was blind; (c) `test_the_dashboard_script_parses` skips in the environment `make verify-offline` actually runs in on this host."
    artifacts:
      - path: "tests/test_status.py:1243"
        issue: "Join test never watched red (recorded honestly by 07-05, not hidden)"
      - path: "tests/test_dashboard.py:464-491"
        issue: "node --check gate SKIPS under the PATH `make verify-offline` inherits; measured `no JavaScript runtime on PATH` in this verifier's own run"
    missing:
      - "A decision on whether a gate that skips in the project's own gate environment counts as a gate this phase adds"
      - "Either an accepted override for the join test, or the record left as MET IN PART (current state, and defensible)"
  - truth: "The phase closing record states measurements that match the tree"
    status: failed
    reason: "Five measurable numbers in the closing record are now wrong at HEAD. Re-measured by this verifier at 9e7d302, not taken from any document."
    artifacts:
      - path: ".planning/ROADMAP.md:418-449"
        issue: "Cites `all 20 Result( construction sites`, partition `11 / 9`, `865 passed`, `33/33 mutations`, `identity check: PASS — 220 file(s)`, `the ratio rose from 26/26 to 33/33`. Measured at HEAD: 21 sites, partition 12 / 9, 883 passed + 1 skipped, 34/34, identity 222 file(s), registry M1-M20 + M25-M38."
      - path: ".planning/REQUIREMENTS.md:29"
        issue: "REQ-21 traceability cell repeats `all 20 Result( construction sites`, `11 / 9`, `Gate: 26/26 → 33/33`"
      - path: "docs/retailer-evidence.md:4097-4101"
        issue: "Phase 7 closing record table repeats `all 20`, `11 / 9`, `33/33`"
    missing:
      - "A dated post-review addendum beside the closing record (not over it, per this project's own convention) recording the nine review fixes and the re-measured figures: 883 passed / 1 skipped, 34/34, identity 222, 21 Result sites, 12/9 partition, M38 registered"
  - truth: "Criterion 4's evidence is described accurately"
    status: failed
    reason: "The closing record claims the age `was observed surviving a real two-process restart`. No such test exists. Grep for `subprocess` across tests/test_monitor.py and tests/test_cli_watch.py returns nothing; the restart is modelled as two in-process `watch_loop` calls sharing one `state_path`, which `tests/test_cli_watch.py:1331-1335` itself calls a model. The BEHAVIOUR is verified — the age survives a real file round-trip and is not invented — but `real two-process restart, not a mocked one` overstates the measurement, in a phase whose thesis is that a claim must not exceed what was observed."
    artifacts:
      - path: ".planning/ROADMAP.md:421"
        issue: "`observed surviving a **real two-process restart**, not a mocked one`"
      - path: "docs/retailer-evidence.md:4100"
        issue: "`The age was observed surviving a **real two-process restart**.`"
    missing:
      - "Correct the wording to what was measured: two `watch_loop` calls sharing one `state_path`, each building its own `State`/`Pacer`, with both ends asserted (bytes on disk and what a fresh `State.load` makes of them). Or add a genuine subprocess-boundary test."
deferred: []
human_verification:
  - test: "Decide whether to close the SC-3 gap with a non-staling fact in `status.json` (e.g. `stale_after`) or to accept the ingredients-plus-join-test form via an override"
    expected: "A recorded decision; the criterion text stays unedited either way"
    why_human: "This is a design judgement about what `presented as stale in status.json` should mean, not a fact discoverable in code"
  - test: "Decide whether `sudo systemctl restart boty` happens. Measured at 2026-08-17 14:11Z: `served/boty/status.json` (mtime 08:59 today) carries 10 watch rows, 0 with a `read_at` key, 0 with a `checked` key, and 6 retailer rows with no `current_interval_seconds`. `state.json` still holds 13 bare pre-07 strings and 0 stamps."
    expected: "Either a restart, or the deferral restated with its date"
    why_human: "Deploy is the user's explicit decision, answered `keep defer` on 2026-08-17 and `defer` on 2026-08-10. Not performed and not recommended here."
  - test: "Look at the dashboard in a GPU-backed browser with a payload carrying mixed fresh/stale/undated rows"
    expected: "Dim `.tag.age` on fresh rows, amber `.tag.age.warn` on stale and undated rows, `not checked` beside remembered rows"
    why_human: "Visual weight and legibility. The markup and the branch logic are verified by execution below; how it LOOKS is not."
```

# Phase 7: A Reading Has an Age — Verification Report

**Phase Goal:** Every reading says when it was taken, and a reading too old to trust is shown as stale rather than as fact — or says it does not know.
**Verified:** 2026-08-17T14:11:17Z at HEAD `9e7d302`
**Status:** gaps_found
**Re-verification:** No — initial verification
**Requirements:** REQ-21

Everything below was measured at HEAD by this verifier. Where a figure came from a
document rather than from a command, it says so. Where something could not be confirmed,
it says that instead of inferring.

## Goal Achievement

### Observable Truths — the ROADMAP's five Success Criteria

| # | Truth | Status | Evidence (measured at HEAD `9e7d302`) |
|---|-------|--------|----------|
| 1 | Every `Result` records when it was read, and that time is published per watch in `status.json` | ✓ VERIFIED **in the tree**; NOT on the wire | AST gate `tests/test_retailers.py::test_every_result_construction_in_retailers_names_read_at` run standalone: **2 passed**. It asserts **21** `Result(` call sites (not 20 — WR-07 added one) and that none inherits the default. Partition gate asserts **12 read / 9 non-read** (not 11/9). Executed `status.write` against the **real** `config/products.yaml` (13 watches) and the **real** `state.json`: **13/13 rows carry a `read_at` key**, `"read_at": 0` absent from the serialised bytes. Live served file measured separately — see the wire row below |
| 2 | A reading with no recorded time is shown as UNKNOWN age, never as current — watched going red | ✓ VERIFIED | Executed `boty.cli._age_tag` directly — `undated → [age ?]`, `fresh → [age 4s]`, `stale → [age 7h > 6h]`, `no cadence → [age 3h, cadence ?]`. Executed `ageTag` out of `served/boty/index.html` in node — `undated → <span class="tag age warn">age ?</span>`, missing key → same. Tag is appended **unconditionally** (`boty/cli.py:334`, inline at `index.html:296`), so an absent tag cannot mean fresh. `CAUGHT M36 boty/cli.py: 1 test(s) failed — test_report_says_unknown_for_a_reading_nobody_dated` in this verifier's own mutation run |
| 3 | A reading older than its retailer's current interval is presented as stale in `status.json`, `boty check` **and** the dashboard, derived from the retailer's own pacing | ⚠️ **MET IN PART** — independently confirmed as partial | **The two rendering surfaces are MET, by execution.** `_age_tag` prints `[age 7h > 6h]`; `ageTag` renders `<span class="tag age warn">7h ago > 6h</span>`. Both read the cadence from `retailers[].current_interval_seconds`, never from `index.html`'s banner constant — `CAUGHT M37 served/boty/index.html: 1 test(s) failed`. `Pacer.current_interval` is one number and `record` schedules **through** it (`boty/pacing.py:293`) — `CAUGHT M33: 11 test(s) failed`. **The `status.json` third is not settled:** the file publishes `read_at`, `checked`, `current_interval_seconds` and **no verdict** (`grep` for a `stale` key on a watch row: none; the design is argued at `boty/status.py:280-289`). A reader opening the file sees three numbers and must subtract against their own clock. I agree with 07-06: this is neither MET nor UNMET |
| 4 | The age survives a service restart, so a restart cannot make a two-day-old reading look fresh | ✓ VERIFIED (behaviour); ✗ the **description** of the evidence is wrong | Behaviour confirmed: `State.save` writes `{"availability": …, "read_at": self.read_at.get(key)}` (`boty/monitor.py:359`); `_remembered_stamp` bounds a restored stamp at **both** ends and rejects `bool` (`monitor.py:206-218`); `transitioned_to_stock` writes availability and stamp as one act or clears both (`monitor.py:397-400`). `CAUGHT M32 boty/monitor.py: 7 test(s) failed` — the mutation defaults a missing stamp to `now`. **But** no subprocess-boundary test exists (`grep -rn subprocess tests/test_monitor.py tests/test_cli_watch.py` → nothing); the restart is two in-process `watch_loop` calls sharing one `state_path`, which the test file itself calls a model. See gap 4 |
| 5 | `make verify-offline` exits 0, and every gate this phase adds has been watched going red | ⚠️ **MET IN PART** | **Gate half MET, re-measured by this verifier, not read from a document:** `identity check: PASS — 222 file(s)`, `883 passed, 1 skipped in 10.89s`, `Success: no issues found in 18 source files`, `mutation check: 34/34 mutations caught`, survivors none, `VERIFY: PASS (OFFLINE …)`, `EXIT=0`. **`every gate` half still not MET**, and for three reasons now rather than one — see gap 2 |

**Score:** 3/5 fully verified; 2 MET IN PART. Both partials are the ones 07-06 flagged, and I reached
them independently before reading its verdicts. **Neither was over-stated and neither was
under-stated** — the self-assessment is accurate in both directions on criteria 3 and 5.

### The wire, measured rather than assumed

The phase's `NOT ON THE WIRE` caveat is true and remains true:

| Artifact on disk | Measured 2026-08-17 14:11Z |
|---|---|
| `served/boty/status.json` (mtime 08:59 today, written by the running pre-phase daemon) | 10 watch rows for 13 configured watches; **0** rows carry `read_at`; **0** carry `checked`; 6 retailer rows, none carrying `current_interval_seconds` |
| `state.json` | 13 entries, **13 bare strings**, 0 dicts, 0 stamps |

The 10-of-13 row count is itself a live re-confirmation of the phase's own Finding 4 — the row
count is a function of pacing. Deploy is deferred by Dan's explicit answer (`keep defer`,
2026-08-17, recorded verbatim in `QUESTIONS.md` § 0f). No restart was performed or recommended here.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `boty/models.py` | `Result.read_at: float \| None = None` | ✓ VERIFIED | line 492, declared last |
| `boty/retailers.py` | stamp on all sites, partitioned | ✓ VERIFIED | 21 AST call sites, 12 variable / 9 literal-`None`, gate passes standalone |
| `boty/status.py` | `read_at` + `checked` per row, `current_interval_seconds` per retailer, one row per configured watch | ✓ VERIFIED | lines 183, 200, 290, 300, 374, 375; executed against real config + real ledger → 13 rows |
| `boty/monitor.py` | dated ledger, validated load, clock-free save | ✓ VERIFIED | `_remembered_stamp` 193-218, `save` 359, `transitioned_to_stock` 397-400 |
| `boty/pacing.py` | `Pacer.current_interval`, read-only, backoff may only widen | ✓ VERIFIED | 332-420; `.get` not `_for` (WR-04); outer `max` (WR-01) |
| `boty/config.py` | override held to floor **and** to the global interval | ✓ VERIFIED | 292-308 (WR-02) |
| `boty/cli.py` | `_age`, `_age_tag`, `_current_intervals`, `_remembered`, `commit=False` on the check path | ✓ VERIFIED | 122, 148, 225, 839; age clamped at 0 (WR-03, line 215) |
| `served/boty/index.html` | `.tag.age` / `.tag.age.warn`, `ageTag`, `fmtDur`/`fmtAge`, `esc(w.availability)` | ✓ VERIFIED | 118-119, 215-225, 294; executed in node |
| `scripts/mutation_check.py` | M31-M37 registered | ✓ VERIFIED — and **M38** beyond it | 34 idents: `M1`-`M20`, `M25`-`M38`. `M21`-`M24` remain Phase 6's deliberate gap |
| `tests/test_dashboard.py` | `UNTRUSTED` covers `w.read_at` **and** `w.availability` | ✓ VERIFIED | 106-117 |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `retailers._verdict_from_html` | `Result.read_at` | one wall-clock read, named at every return | ✓ WIRED | AST partition `_verdict_from_html: (0, 8)` |
| `status.write` | `r.read_at` | watch-row comprehension | ✓ WIRED | `status.py:290`, executed |
| `cli.watch_cycle` → `write_status` | `watches=`, `remembered=`, `intervals=` | keyword threading | ✓ WIRED | `cli.py:520-528` |
| `cli.main` check path → `write_status` | same three keywords | keyword threading | ✓ WIRED | `cli.py:896-903` |
| `pacing.record` | `Pacer.current_interval` | refusal branch computes its wait through the accessor | ✓ WIRED | `pacing.py:293` — one expression, so display and schedule cannot drift |
| `index.html ageTag` | `retailers[].current_interval_seconds` | `Map` built per tick, `intervals.get(w.retailer)` | ✓ WIRED | line 218 + 261; M37 kills the fixed-constant substitute |
| `index.html storeTag` | `w.checked === false` | early return | ✓ WIRED | line 167 |
| `monitor.State.load` | `_remembered_stamp` | one validated stamp per entry | ✓ WIRED | `monitor.py:314` |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| `status.json` watch rows | `read_at` | `Result.read_at` (fresh) / `State.read_at` (remembered) | Yes — executed against the real ledger; 13/13 rows carried the key, all `null` because this host's ledger is pre-07 | ✓ FLOWING (null is the correct, honest value here) |
| `status.json` retailer rows | `current_interval_seconds` | `cli._current_intervals` → `Pacer.current_interval` | Yes | ✓ FLOWING |
| `index.html` row | `w.read_at`, `intervals` | `status.json` | Yes, in the tree; **NOT** on the served file today | ⚠️ FLOWING in tree, DISCONNECTED on the wire (deploy deferred) |
| `index.html` dot class | `w.availability` | `state.json` via `_remembered_availability` | Yes, and now escaped at the sink | ✓ FLOWING |

### Behavioural Spot-Checks

| Behaviour | Command | Result | Status |
|---|---|---|---|
| Full offline gate | `make verify-offline` | `identity 222 · 883 passed, 1 skipped · 34/34 mutations · VERIFY: PASS · EXIT=0` | ✓ PASS |
| AST completeness gate | `pytest tests/test_retailers.py -k "read_at or partition"` | 2 passed | ✓ PASS |
| Four CLI age forms | executed `boty.cli._age_tag` | `[age ?]` · `[age 4s]` · `[age 7h > 6h]` · `[age 3h, cadence ?]` | ✓ PASS |
| Strict `>` boundary | `_age_tag` at exactly one cadence and one ms past | `[age 5m]` then `[age 5m > 5m]` | ✓ PASS |
| Negative age clamp (WR-03) | `_age_tag` with a stamp 10 s in the future | `[age 0s]` (was `[age -10s]`) | ✓ PASS |
| Four dashboard age forms | evaluated `ageTag` from `index.html` in node v24.16.0 | `age ?` warn · `4s ago` · `7h ago > 6h` warn · `3h ago · cadence ?` warn | ✓ PASS |
| XSS payload at the dot sink (CR-01) | evaluated `esc` from `index.html` | `&quot; onmouseover=alert(1) x=&quot;` — stays inside the attribute | ✓ PASS |
| One row per configured watch | executed `status.write` with real config + real `state.json` | 13 configured → **13 rows**, 13 `checked: false`, 13 `read_at: null`, **0 alertable** | ✓ PASS |
| Live wire state | read `served/boty/status.json`, `state.json` | 10 rows, 0 `read_at`; 13 bare strings, 0 stamps | ✓ PASS (confirms the NOT-ON-THE-WIRE claim) |
| Dashboard script parses | `pytest tests/test_dashboard.py` **with node on PATH** | 17 passed | ✓ PASS |
| Dashboard script parses | same, under the PATH `make verify-offline` inherits | 1 **skipped** — `no JavaScript runtime on PATH` | ⚠️ see gap 2(c) |

### Gates re-watched going red — independently, by this verifier

I did not take the fix commits' red counts on trust. Three regressions were re-applied in a
throw-away `git worktree` (the working tree was never touched; `git status --short` is empty and
the worktree is removed):

| Regression re-applied | Gate | Result |
|---|---|---|
| CR-01 — `${esc(w.availability)}` → `${w.availability}` | `test_every_retailer_controlled_string_is_escaped_before_innerhtml` | **RED** — 1 failed / 15 passed, offender named `w.availability in ${w.availability}` |
| WR-02 — delete the `seconds < global_interval` guard | `test_a_retailer_override_below_the_global_interval_is_refused` | **RED** — 1 failed / 35 passed |
| WR-03 — remove `max(0.0, …)` from `_age_tag` | `test_a_stamp_in_the_future_renders_as_no_age_rather_than_a_negative_one` | **RED** — 1 failed / 51 passed |

Every fix commit except `bc23a02` (WR-08, a docstring rewrite that adds no gate) carries a
`Watched going red:` paragraph with a failure count in its message. So the nine post-close fixes
were themselves gated to this project's standard.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| REQ-21 | 07-01, 07-02, 07-03, 07-04, 07-05, 07-06 (all six declare `requirements: [REQ-21]`) | A reading states when it was taken, and one too old to trust is presented as stale rather than as fact; staleness measured against the retailer's own current interval | ✓ SATISFIED **in the tree**, with criterion 3's `status.json` third partial | Every clause traced to executed code above. The requirement's own opening measurement — *Walmart's age could not be established at all because a restart zeroed the evidence* — is closed by `State.read_at` + `_remembered_stamp`, killed by M32 |

No orphaned requirements: `grep -E "Phase 7" .planning/REQUIREMENTS.md` maps REQ-21 and nothing else
to this phase, and all six plans claim it.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` / `HACK` / `TODO` across all nine phase-modified source files | — | **None found.** Debt-marker gate clean |

### Where the closing record no longer matches the tree

This is the finding the prompt asked to be judged plainly, and the answer is **yes, it misstates the
tree** — measured, not inferred:

| Claim in the closing record | Measured at HEAD `9e7d302` |
|---|---|
| `all 20 Result( construction sites` | **21** (WR-07 added the non-object-body arm) |
| read/non-read partition `11 / 9` | **12 / 9** |
| `865 passed` | **883 passed, 1 skipped** |
| `mutation check: 33/33` · `the ratio rose from 26/26 to 33/33` | **34/34**; M38 registered by the WR-01 fix |
| `identity check: PASS — 220 file(s)` | **222 file(s)** |

The drift is in the reassuring direction — the tree is stronger than its record — but the direction is
not the point. A closing record for *this* phase, of all phases, presenting a 2026-08-17-pre-review
reading as the current gate result is the milestone's own defect committed one level up, in the
document that certifies the defect removed. It is a documentation gap and it should be closed with a
dated addendum **beside** the record, on this project's own convention, rather than by editing the
record.

### Do WR-01 / WR-02 / WR-03 change a criterion verdict?

Judged rather than deferred:

- **WR-01** (a backoff above the cap inverted, shortening the wait) and **WR-02** (an override below
  the global interval published a cadence 3.4x tighter than the loop can keep) were both defects in
  the *one number* criterion 3 rests on. Both were **unreachable on the shipped `config/products.yaml`**
  (largest standing interval 1800 s against a 21 600 s cap; overrides are 900/1800 against a 300 s
  global). So criterion 3's verdict on the shipped configuration does not move. What they do change is
  the strength of the claim: before 2026-08-17 the "one number both surfaces read" invariant held by
  configuration rather than by construction. It now holds by construction, and M38 gates it.
- **WR-03** (`[age -10s]` on one surface where the other clamped) was a real divergence between the two
  surfaces criterion 3 requires to agree, on one input. Fixed and gated; criterion 3's rendering half
  is stronger than it was at close, not weaker.
- **CR-01** does bear on **criterion 5**. The escaping gate this phase relies on existed, was widened
  by 07-05 for `w.read_at`, and was still blind to `w.availability` — a sink 07-04 itself opened four
  plans earlier. That is not a gate that was never watched red; it is a gate that could not bite.
  This project's own recorded rule is that *a bound that cannot bind is worse than no bound*. It does
  not flip criterion 5 to UNMET — the criterion is about observing new gates fail, and every mutation
  was — but it is a third named reason the `every gate` half is not fully met, and it belongs in the
  record beside the join test.

### Gaps Summary

Four gaps, none of them a code defect and none blocking further work:

1. **SC-3, `status.json` third** — the file publishes the ingredients of a staleness verdict, not the
   verdict. Partial. The design reason is sound and demonstrated; the criterion's literal text is not
   satisfied. Rounding it up would be the exact act this milestone exists to prevent.
2. **SC-5, `every gate`** — one gate never watched red (the join test), one gate that could not bite
   (CR-01's escaping gate before it was widened), one gate that skips in the environment the project's
   own gate runs in (`node --check`). Partial.
3. **The closing record misstates the tree on five measurable numbers.** Actionable documentation gap.
4. **`real two-process restart` is not what was measured.** Actionable documentation gap; the
   behaviour it describes is verified, the description of the evidence is not.

Gaps 1 and 2 look **intentional and already recorded**. If they are the settled answer rather than
work to do, accept them explicitly rather than leaving them to be re-litigated at milestone audit:

```yaml
overrides:
  - must_have: "A reading older than its retailer's current interval is presented as stale in status.json"
    reason: "status.json publishes read_at, checked and current_interval_seconds and no derived flag, because a stale boolean computed at write time is written false and keeps saying false for exactly the interval during which it becomes true (pacing.py:196-199). Sufficiency is proved by tests/test_status.py:1243, which derives the verdict from those three keys and nothing else. Both rendering consumers do present the verdict."
    accepted_by: "dan"
    accepted_at: "{ISO timestamp}"
  - must_have: "every gate this phase adds has been watched going red"
    reason: "07-05's join test passed on the RED commit — that IS the measurement that the three published facts were already jointly sufficient, and manufacturing a red would have been theatre. The two later reasons (CR-01's blind gate, the opportunistic node --check skip) are recorded rather than absorbed."
    accepted_by: "dan"
    accepted_at: "{ISO timestamp}"
```

Gaps 3 and 4 should be **fixed, not overridden** — they are the phase's own standard applied to the
phase's own record.

---

_Verified: 2026-08-17T14:11:17Z at HEAD `9e7d302`_
_Verifier: Claude (gsd-verifier)_
_Method: goal-backward. Every figure above came from a command run during this verification. Nothing was taken from a SUMMARY, a PLAN or the ROADMAP._
