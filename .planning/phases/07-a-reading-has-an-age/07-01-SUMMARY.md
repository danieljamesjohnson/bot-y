---
phase: 07-a-reading-has-an-age
plan: 01
subsystem: models
tags: [read_at, staleness, timestamps, mutation-testing, ast-gate, status-json]

# Dependency graph
requires:
  - phase: 05-a-reading-is-about-a-store
    provides: "`Result.store` — the four-times-worn groove for appending a field last, and the `store`-published-as-`0` argument this field's `null`-never-`0` rule is one direction over from"
  - phase: 06-say-only-what-you-measured
    provides: "`Result.shipping`, the field `read_at` is declared after; and the M29/M30 comment shape M31 follows"
provides:
  - "`Result.read_at: float | None` — the wall-clock moment a retailer's answer was read, declared last after `shipping`, default `None` meaning UNKNOWN age"
  - "the stamp threaded onto all 20 `Result(` construction sites in `boty/retailers.py`, partitioned 11 read / 9 non-read, each site stating it"
  - "`status.json` publishes `read_at` per watch row, serialised as `null` when absent"
  - "a static AST completeness gate over `boty/retailers.py` that cannot be satisfied by covering nineteen arms"
  - "M31 — a non-read arm stamps the moment of its refusal — registry risen 26 -> 27"
  - "the measured partition itself: `check_bestbuy_api`'s `bad api json` and `sku not found` arms are READS"
affects: [07-02, 07-03, 07-04, 07-05, 07-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "the stamp INVERTS the `store`/`shipping` rule and the inversion is stated per arm, never inherited from a default"
    - "AST-over-source completeness gates for bulk field thread-throughs (tests/test_support_matrix.py's idiom applied to a construction-site census)"
    - "bracketed clock assertions (`before <= read_at <= after`) instead of a frozen or injected clock"

key-files:
  created: []
  modified:
    - boty/models.py
    - boty/retailers.py
    - boty/status.py
    - scripts/mutation_check.py
    - tests/test_models.py
    - tests/test_retailers.py
    - tests/test_status.py
    - tests/test_cli_watch.py

key-decisions:
  - "`read_at` is the field that answers 'was a page read' — not derivable from `refused` or `availability`, because a store-gap UNKNOWN and a parse-failure UNKNOWN both read a page and `bad api json` sets no `refused`"
  - "no derived `stale` key is published: a flag computed at write time carries `stale: false` for exactly the interval during which it becomes stale (pacing.py:196-199 in mirror image)"
  - "`_verdict_from_html`'s signature is NOT changed to take `read_at`: twelve direct test callers would default to `None` while the AST gate stayed green"
  - "the stamp in `check_bestbuy_api` is assigned between `page = get(api_url)` and `data = page.json`, so the placement is the argument"
  - "M32 consumed by nobody here — reserved for 07-02 per the outline, stated in mutation_check.py so it is not read as a second unallocated gap"

patterns-established:
  - "Pattern 1: a completeness claim over N construction sites is asserted statically over the SOURCE, with the count asserted alongside the property so a gate that finds zero cannot pass vacuously"
  - "Pattern 2: an absent measurement is `null` and never a value that reads as established — `0` for a store invents a real store, `0` for a stamp invents 1 January 1970"
  - "Pattern 3: a mutation is applied by hand and watched turning its NAMED killers red before the harness is ever asked whether it caught it"

requirements-completed: []

# Metrics
duration: 12min
completed: 2026-08-13
---

# Phase 7 Plan 01: A Reading Carries the Moment It Was Taken — Summary

**`Result.read_at` declared last with default `None` meaning UNKNOWN age; the stamp stated at all 20 `Result(` sites in `boty/retailers.py` partitioned 11 read / 9 non-read and proved by an AST census; published per watch row in `status.json` as `null`-never-`0`; M31 registered, watched red by hand, and observed CAUGHT at 27/27.**

## Performance

- **Duration:** ~12 min (first commit 10:16:10-05:00, M31 commit 10:24:26-05:00, plus two full `make verify-offline` runs)
- **Started:** 2026-08-13T15:16:10Z
- **Completed:** 2026-08-13T15:40:00Z
- **Tasks:** 3
- **Files modified:** 8 (766 insertions, 11 deletions)

## Accomplishments

- **Criterion 1 whole.** Every `Result` now records when it was read, and that time is published per watch in `status.json`. The datum did not exist before today; the answer to *"so they are out of stock as of when?"* was unreconstructible for Amazon and unestablishable at all for Walmart.
- **The DATUM half of criterion 2.** An absent stamp is `None` — never `time.time()`, never `0.0` — argued in the declaration, asserted in three tests, and pinned by M31. The rendering half is 07-05's.
- **The trap did not get rebuilt.** All 9 non-read arms state `read_at=None` explicitly, and `check_html`'s pair carries the full argument with `pacing.py:196-199` quoted at the arm.
- **The naive rule was refused where it is wrong.** `check_bestbuy_api`'s `bad api json` and `sku not found` arms are STAMPED, with the reason at each arm and the stamp's assignment placed between `get()` returning and `page.json` parsing, so the placement is structural rather than commentary.
- **A completeness gate that cannot be satisfied by nineteen arms.** Phase 5's identical bulk edit missed 2 of 8 and only the tests caught it; this one is a static AST census asserting both the count (20) and the property (every one names `read_at`).

## Task Commits

Each task was committed atomically, TDD tasks as test -> feat:

1. **Task 1: Declare the field, and settle the asymmetry in writing**
   - `3780c7e` (test) — the three REQ-21 model tests, RED at 3 failed / 33 passed
   - `3f8c286` (feat) — `Result.read_at`, six-paragraph `#:` block, 86 insertions and **0 deletions**
2. **Task 2: All twenty sites, stated not inherited — and the static gate that proves it**
   - `451dec0` (test) — AST census, AST partition, 8 refusal cases, 3 Best Buy read cases, RED at 5 failed
   - `41c693d` (feat) — `import time`, the single clock read in `_verdict_from_html`, all 20 sites
3. **Task 3: Publish it, register M31, and watch M31 go red**
   - `31c03ae` (test) — `read_at` enumerated into the exact-keyset assertion (went red exactly as § *Finding 10* predicted), three publication tests, RED at 4 failed
   - `b2c358d` (feat) — the row key, `null`-never-`0`, the `updated` distinction, the no-`stale`-key argument
   - `ccd3502` (style) — ruff I001 on the import block `import time` disturbed
   - `d91b883` (chore) — M31 registered with its pre-count, plus § *Finding 11*'s relabel

**Plan metadata:** see final commit below.

## Files Created/Modified

- `boty/models.py` — `read_at: float | None = None` declared last after `shipping`, with the six paragraphs (what it is; declared last; what the default MEANS; not folded into `degraded`; the asymmetry; not derivable from `refused`/`availability`) and the publication sentence. Purely additive: `git diff -U0 | grep -c '^-[^-]'` -> **0**, so `shipping`'s "Deliberately NOT published" paragraph is byte-unchanged.
- `boty/retailers.py` — `import time`; one clock read at `_verdict_from_html`'s entry threaded to 8 returns; 8 refusal arms at `read_at=None`; `check_bestbuy_api`'s four with the stamp assigned between `get()` and `page.json`.
- `boty/status.py` — `"read_at": r.read_at` appended last after `store_pinned`.
- `scripts/mutation_check.py` — M31, and M29's citation re-pointed.
- `tests/test_models.py`, `tests/test_retailers.py`, `tests/test_status.py` — REQ-21 sections.
- `tests/test_cli_watch.py` — the mislabelled section relabelled REQ-16, argued in place.

## Evidence

### `make verify-offline`, verbatim

```
=== verify: identity, lint, tests, types, fixtures, controls, mutation ===
identity check: PASS — 215 file(s), no host identity found
All checks passed!
798 passed in 10.83s
Success: no issues found in 18 source files
fixtures: 11 fixture(s) under /home/dan/CodeProjects/pokemongoplusplus/tests/fixtures
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 27 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (769 passed, 29 skipped in 10.99s)
  CAUGHT    M31 boty/retailers.py: 2 test(s) failed — test_the_read_and_non_read_arms_are_partitioned_exactly, test_a_transport_that_refused_took_no_reading[check_html-get-exc0]
mutation check: 27/27 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
EXIT=0
```

**27 of 27 mutations caught. Survivor list empty** — `grep -n "SURVIVED"` over the captured run
returns nothing. The registry rose by exactly one, **from 26 to 27**, and the idents in file order
are M1…M20, M25, M26, M27, M28, M29, M30, **M31**. **798 passed**, above the 778 baseline by the
20 tests this plan added. mypy clean over **18** source files. Controls SKIPPED — **no live
retailer read was made and none was planned.**

### M31 watched going red BY HAND, before the harness was ever asked

Applied to the working tree with a `trap cleanup EXIT` holding `git checkout -- boty/retailers.py`:

```
M31 APPLIED at first occurrence
--- mutated line ---
544:        return Result(watch, Availability.UNKNOWN, detail=f"blocked: {exc}", url=watch.target, refused=True, store=None, shipping=None, read_at=time.time())
=== pytest tests/test_retailers.py -q ===
E       AssertionError: check_html stamped an arm where nothing came back
E       assert 1786634675.987888 is None
=========================== short test summary info ============================
FAILED tests/test_retailers.py::test_the_read_and_non_read_arms_are_partitioned_exactly
FAILED tests/test_retailers.py::test_a_transport_that_refused_took_no_reading[check_html-get-exc0]
2 failed, 113 passed in 1.19s
PYTEST_EXIT=1
```

Exit **1**, and it named **both** expected killers — the behavioural refusal case and the static
partition — which is the pair M31's comment block predicts. The mutation landed on
`boty/retailers.py:544`, which is `check_html`'s `except Blocked` arm, which is exactly what the
`breaks=` sentence describes.

**The revert, proved rather than assumed:**

```
$ git status --porcelain
                                  (empty)
$ grep -c 'read_at=time.time()' boty/retailers.py
0
```

### M31's anchor, pre-counted before registration

```
$ grep -c 'refused=True, store=None, shipping=None, read_at=None' boty/retailers.py
1
$ grep -n 'refused=True, store=None, shipping=None, read_at=None' boty/retailers.py
544:        return Result(watch, Availability.UNKNOWN, detail=f"blocked: {exc}", url=watch.target, refused=True, store=None, shipping=None, read_at=None)
```

Exactly **1**, per M19's recorded trap — `apply_mutation` replaces the FIRST occurrence, so a
non-unique anchor mutates a line the `breaks=` sentence is not describing. The bare substring
`read_at=None` occurs **17** times in that file (9 construction sites plus the comments arguing
them), which is why the anchor is the arm's whole stated metadata rather than the field alone.
Re-measured after all comment edits landed and still 1.

### The AST census

```
$ .venv/bin/python -c "...ast over boty/retailers.py..."
20/20 sites name read_at
```

## Decisions Made

- **`read_at` becomes the field that answers "was a page read".** No existing field does:
  `availability is UNKNOWN` is true of a store-gap and of a parse failure, both of which read a
  page; `refused` is closer and still not identical, because `bad api json` sets no `refused` and
  still received a response. Recorded in the declaration so the "just derive it" simplification is
  answered where it will be proposed.
- **No derived `stale` key in `status.json`, and it is a decision rather than an omission.** A flag
  computed at write time carries `stale: false` for exactly the interval during which the row
  becomes stale — `pacing.py:196-199`'s trap in mirror image. The raw fact goes out; 07-05 is where
  each of the three consumers subtracts against its own `now`.
- **`_verdict_from_html`'s signature is NOT widened to take the stamp from its callers.** It reads
  cleaner and it is wrong here: `tests/test_retailers.py` calls that function directly at eleven
  sites and `tests/test_alert_text.py` at one, so an optional parameter would default twelve
  readings that DID happen to `None` — the dangerous direction — while the AST completeness gate
  stayed green throughout. The rejection is recorded in a comment at the function so it is not
  re-proposed as a tidy-up.
- **`check_amazon`'s and the browser adapters' arms were NOT widened to state `store`/`shipping`.**
  They do not state them today; that is out of this plan's scope. `read_at` is stated at all twenty
  sites only because the AST gate requires it of every one, and that asymmetry is noted in the code.
- **`_OMITTED` moved above `_result` in `tests/test_status.py`**, purely because Python needs a
  default's name to exist when the `def` runs. "Nobody stamped this reading" stays reachable through
  the helper by OMISSION, which is the call shape every non-read arm in `boty/retailers.py` actually
  makes.

## Measurement notes carried forward

### The § *Finding 1* correction: **nine** `read_at=None` arms, not eight

`07-PLAN-OUTLINE.md` § *Finding 1* says *"`read_at=None` will occur at eight arms in
`retailers.py` after 07-01"*. **Counted on this tree after the edit: it occurs at nine** — the four
adapters' `except` pairs (8) **plus** `check_bestbuy_api`'s `api error` arm, which the outline
classifies as a non-read arm one section later (§ *Finding 2*) and omits from that parenthetical.

**The outline's operative claim is unaffected, and this is the part 07-06 needs.** The first
occurrence in file order is still `check_html`'s `except Blocked` arm, which is what M31's anchor
and its `breaks=` sentence depend on — and it was pre-counted and confirmed at line 544 above.
Recorded on the same footing as 06-02's `_flattened_exit_codes` correction: **a measurement note,
never an edit to a planning document.**

### M32's disposition — reserved, not lost

The orchestrator reserved **M31-M32** for this plan. This plan consumed **M31 only**.
**M32 belongs to 07-02** (`State.load` defaulting a missing stamp to `time.time()` — criterion 4's
failure in one line), per `07-PLAN-OUTLINE.md`. It is stated in `scripts/mutation_check.py`'s M31
comment block, **where 07-02 will read it**, so it is not mistaken for a second unallocated gap
the way M21-M24 were nearly mistaken for one. `tests/test_support_matrix.py`'s own message governs:
*"Idents are reserved across concurrent plans, not renumbered."* **M21-M24 remain the intentional
gap and were not filled.**

### The § *Finding 11* relabel — a corrected cross-reference, and nothing more

`tests/test_cli_watch.py:774` carried the section header `# REQ-21: a push has to carry a human
action, and the default is silence`, written 2026-08-12 by Phase 6's paging work. REQ-21 was minted
nowhere in v0.2's archive and nowhere in Phase 6's planning: that ident was invented in a test file
and never existed as a requirement. The section's own subject is REQ-16's, and
`tests/test_cli_watch.py:510` already carries a `REQ-16 across a RESTART` section.

This plan writes real `# REQ-21` sections in three test files, which made
`scripts/mutation_check.py`'s citation of *"tests/test_cli_watch.py's REQ-21 section"* ambiguous the
moment it landed. The header is relabelled **REQ-16** and M29's citation re-pointed **in the same
commit** (`d91b883`), each with the correction argued in place rather than silently retyped.

**Explicitly NOT a criterion, requirement or measurement being changed.** No assertion in that
section was touched — a mistyped cross-reference now points at what it always meant.

## Deviations from Plan

Three, all recorded rather than quietly absorbed. **None changed any behaviour the plan specifies.**

**1. [Rule 3 - Blocking] `gsd-tools` was unreachable at executor start**

- **Found during:** context load, before Task 1
- **Issue:** `/usr/bin/env: 'node': No such file or directory` — this is a non-login shell and Node
  is nvm-only on this host.
- **Fix:** `export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh` before the call. Environment, not code.
- **Committed in:** nothing — no file changed.

**2. [Rule 3 - Blocking] ruff I001 on `tests/test_status.py`'s import block**

- **Found during:** Task 3, after adding `import time` for the constructed two-day-old stamp
- **Issue:** the new import left two blank lines before the module-level `_OMITTED` block; ruff's
  I001 wants one. `make verify-offline` runs lint, so this would have failed the gate.
- **Fix:** `ruff check --fix tests/test_status.py`. One blank line removed; no assertion changed.
- **Verification:** `ruff check scripts tests boty` -> `All checks passed!`
- **Committed in:** `ccd3502`, deliberately separate so M31's commit stays about M31.

**3. One extra test beyond the plan's enumerated list**

- **Found during:** Task 3
- **What:** `test_the_row_stamp_is_not_the_file_stamp` in `tests/test_status.py`, additional to the
  two the plan names.
- **Why:** the plan requires `status.py` to state in a comment that `read_at` is not `updated`. That
  sentence is the phase's central distinction and nothing measured it — a two-day-old row under a
  cycle stamp written this second is precisely the state REQ-21 exists to make visible, and it must
  be REPRESENTABLE rather than collapsed. Added under Rule 2 (a claim in a comment that nothing can
  watch go red is the defect this phase is about).
- **Committed in:** `31c03ae` (RED) / `b2c358d` (GREEN).

---

**Total deviations:** 3 (2 blocking-environment/lint, 1 added assertion under Rule 2)
**Impact on plan:** none on scope. No package was installed, no dependency added, no clock frozen,
injected or monkeypatched, and `boty/cli.py`, `boty/monitor.py`, `boty/pacing.py` and
`served/boty/index.html` were not touched.

## Issues Encountered

- **The `_verdict_from_html` return sites carry three different indentations** (16-, 12- and
  8-space argument bodies), so a single `replace_all` could not reach all eight. Counted each
  variant first (5 / 2 / 1 = 8) before editing, which is the same pre-count discipline M31's anchor
  required and the reason Phase 5's bulk edit is a cautionary tale in this plan's own text.
- **No issue with the `NetworkBlocked` guard.** Every new test patches `retailers.get` or
  `retailers.fetch_rendered` on the module, per `tests/test_retailers.py:38-49` and `:601`.

## Scope fence, honoured

Nothing in this plan compares a stamp to anything, computes a `stale` flag, or reads `now` at a
comparison. Persistence across a restart is **07-02's**. The retailer's current interval is
**07-03's**. The missing-row problem (3 rows for 14 configured watches) is **07-04's**. Rendering in
`boty check` and the dashboard is **07-05's**.

**REQ-21 is NOT marked complete here**, per the outline's own rule and 04-05's / 05-01's / 06-06's
precedent: *a requirement is not marked complete by the plan that ships its code.* **07-06 closes it
by measuring what landed.** `requirements-completed` is therefore `[]` deliberately, not by
omission.

## Next Phase Readiness

**07-02 can start.** What it inherits:

- `Result.read_at` exists and is honest at the source, so `monitor.State` has a real value to
  persist rather than one to invent.
- **M32 is reserved for it and says so in `scripts/mutation_check.py`.** The next registered ident
  is M32; M21-M24 stay unfilled.
- The registry is at **27**, and 07-06 must record it rising **from 26** (not 28 — § *CORRECTION 1*).
- The `null`-never-`0` / `None`-never-`now` rule is argued in three files now (`models.py`,
  `retailers.py`, `status.py`) and 07-02's `State.load` is the fourth place it has to hold — with
  the additional direction the outline names, that a bare pre-07 string loads as *availability with
  an UNKNOWN age*.

**Standing concern, unchanged by this plan and 07-06's checkpoint material:** Walmart's
`"walmart:Pokémon GO Plus +" -> "out_of_stock"` entry on this host is frozen — every Walmart reading
is UNKNOWN while `WALMART_STORE_ID` is unset (`QUESTIONS.md` § 0f), and `transitioned_to_stock`
returns on UNKNOWN before it writes. After this phase that row will publish `out_of_stock` with an
**UNKNOWN age**, indefinitely. That is the honest output; inventing an age would be the defect.

## Self-Check: PASSED

Every claim above re-measured against the tree after the SUMMARY was written:

- **8 modified files** all present; the SUMMARY itself present.
- **8 commits** all resolvable: `3780c7e`, `3f8c286`, `451dec0`, `41c693d`, `31c03ae`, `b2c358d`,
  `ccd3502`, `d91b883`.
- `read_at: float | None = None` present in `boty/models.py`; `"read_at": r.read_at` present in
  `boty/status.py`; `ident="M31"` present in `scripts/mutation_check.py`; the relabelled
  `# REQ-16: a push has to carry a human action` header present in `tests/test_cli_watch.py`.
- M31's anchor still counts **1**. The registry still counts **27** idents.
- **Stray-token scan clean.** `grep -rn 'antml:|</invoke>|</content>'` over `boty/`, `tests/`,
  `scripts/` and this SUMMARY returns hits **only** inside `tests/test_changelog.py`, which is the
  pre-existing gate that detects that leak class — no new occurrence anywhere.
- `identity_check.py --all` -> `PASS — 215 file(s), no host identity found`. **No real store number
  or host identity was written.** The only store literals used are `0` and `00000`, this repo's
  redaction vocabulary.

---
*Phase: 07-a-reading-has-an-age*
*Completed: 2026-08-13*
