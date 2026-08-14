---
phase: 07-a-reading-has-an-age
plan: 04
subsystem: monitor
tags: [status-json, provenance, ledger, mutation-testing, req-21, cross-surface]

# Dependency graph
requires:
  - phase: 07-a-reading-has-an-age
    plan: 01
    provides: "`read_at` already on the watch row, so this plan appends one key rather than restructuring the comprehension"
  - phase: 07-a-reading-has-an-age
    plan: 02
    provides: "`State.read_at`, the per-watch stamp that survives the process — the half of a memory this plan pairs with the availability"
  - phase: 07-a-reading-has-an-age
    plan: 03
    provides: "`status.write`'s `intervals` keyword, which this plan appends after and passes through untouched; and M34's reservation stated in `scripts/mutation_check.py` where this plan read it"
provides:
  - "`status.write(watches=, remembered=)` — one row per CONFIGURED watch instead of one row per reading taken this cycle"
  - "`status._remembered_rows` — the partition, sorted by watch key, defaulting an unresolved key to `(UNKNOWN, None)`"
  - "a remembered row: config facts published, the remembered reading published, `null` for every fact about the act of reading, a STATED `alertable: false`, `checked: false` last"
  - "`cli._remembered(state)` — the one reader pairing an availability with its age in one act, called by both `write_status` call sites"
  - "a static AST gate in `tests/test_cli_watch.py` on both call sites — the teeth behind the permissive `watches=None` default"
  - "M34 (a memory published as an observation) and M35 (a memory given an observation's authority) — registry risen 29 -> 31"
affects: [07-05, 07-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "a keyword that maps a key to a PAIR rather than two parallel keywords, so half a memory is unrepresentable at the call site"
    - "a permissive default paid for with a STATIC gate, because a behavioural test cannot see a call site that dropped a keyword while every other assertion stays green"
    - "a killer test that measures its own fixture — it publishes the same watch on the other branch and asserts the values differ — so it cannot pass vacuously"

key-files:
  created: []
  modified:
    - boty/status.py
    - boty/cli.py
    - scripts/mutation_check.py
    - tests/test_status.py
    - tests/test_cli_watch.py

key-decisions:
  - "`remembered` maps a key to a PAIR, not two parallel dicts: a caller passing one and forgetting the other would publish a remembered availability with no age, silently, with every test green — this plan's own defect rebuilt in the plumbing that delivers the fix"
  - "fresh and remembered rows carry the SAME keys in the SAME order, so `checked` and `read_at` are the only two fields carrying the difference — REQ-21's *byte-identical in shape* converted from the defect into a stated property"
  - "`alertable` is a literal `False` on a remembered row and the claim about it is scoped: this key sends nothing, so what is refused is a PUBLISHED claim on a served page, not a push"
  - "a watch read UNKNOWN this cycle keeps the FRESH row rather than falling back to the memory — `checked: true` on a two-day-old verdict is the exact conflation this phase removes"
  - "remembered rows are ordered after the fresh ones and sorted by key, mirroring `sorted((paced or {}).items())` — the file's own established shape preferred over the cosmetic win of config order, which would have meant rewriting the commented fresh-row comprehension"
  - "M34's anchor is two lines because the single-line fragment counts 2 and the FIRST is the retailers array's paced branch — measured before registration, not after a misfire"
  - "no third ident for the manufacture-an-age direction: M31 and M32 already gate it one and two layers up, and two gates on one rule means neither can be shown to bite"

patterns-established:
  - "Pattern 1: when a plan changes what is REPORTED, assert the cycle did not move in the same test that asserts the report changed — separated, each half passes while the pair is false"
  - "Pattern 2: a fixture-critical killer test states in its own body which fixture makes it non-vacuous, and asserts that property, so a later drift fails loudly instead of quietly disarming a mutation"
  - "Pattern 3: a compatibility default is named as such in the docstring, together with the gate that stops it becoming a production regression"

requirements-completed: []

# Metrics
duration: 25min
completed: 2026-08-14
---

# Phase 7 Plan 04: Every Configured Watch Has a Row — Summary

**`status.json` stops publishing one row per reading taken this cycle and starts publishing one row
per configured watch: measured against the real `config/products.yaml` and this host's real
`state.json`, **13 rows published while 3 were fetched**, ten of them carrying the availability the
ledger remembers, the stamp it holds (five of them `null`), `alertable: false` stated rather than
inherited, and `checked: false` — with M34 and M35 each watched turning their named tests red by
hand before the harness was ever asked, then observed CAUGHT at 31/31.**

## Performance

- **Duration:** ~25 min (12:39:10Z to 13:04Z), including two full `make verify-offline` runs and two by-hand red-watches
- **Tasks:** 3
- **Files modified:** 5
- **Commits:** 5 task commits + this metadata commit

## Accomplishments

- **A paced-out watch stops vanishing.** Before today `status.write` rebuilt its `watches` array from
  `results` and `run_once` filtered the watches down to the due ones, so a watch nobody asked about
  had no row at all — not a stale row, no row. *"Not watched this cycle"* and *"watched, and out of
  stock"* were indistinguishable when one of them was simply missing.
- **The headline is a measurement, not a slogan.** One `watch_cycle` against `config/products.yaml`'s
  real shape, this host's real 13-entry ledger, and a `pacer-state.json` with four retailers paced
  out: **13 rows published, 3 watches fetched.** Both halves are asserted in ONE test, because split
  apart each passes while the pair is false — thirteen rows because thirteen were fetched is
  precisely the change this plan must not make.
- **A remembered row cannot pass for an observation.** `checked: false`, the ledger's stamp rather
  than the cycle's clock, `null` for every fact about the act of reading, and `alertable` refused
  outright. M34 and M35 are the gates, and each was watched failing by hand before registration.
- **The permissive default has teeth.** `watches=None` keeps every pre-07-04 caller valid, and a
  static AST gate over `boty/cli.py` asserts both `write_status` call sites pass both keywords —
  because a call site that dropped one would keep every behavioural assertion in the suite green
  while the served page went back to publishing five rows out of thirteen.
- **Nothing about the cycle moved**, and that is a claim with three suites behind it rather than an
  assurance (see § *The cycle-unchanged evidence*).

## Task Commits

1. **Task 1: One row per configured watch, and a remembered row that says so**
   - `d80775b` (test) — RED at **10 failed / 29 passed**
   - `3e32416` (feat) — `_remembered_rows`, the second comprehension, `checked` on both branches
2. **Task 2: Both surfaces thread the ledger — and the cycle is proved unchanged**
   - `eb2e827` (test) — RED at **3 failed / 39 passed**
   - `f4bdb83` (feat) — `cli._remembered`, both `write_status` call sites
3. **Task 3: Register M34 and M35, and watch each of them go red by hand**
   - `07d51ae` (chore) — both registered with their pre-counts and their **measured** killer lists

## Files Created/Modified

- `boty/status.py` — `_remembered_rows` above `write`; two keyword-only parameters after 07-03's
  `intervals`; `"checked": True,` appended last on the fresh watch row; the remembered comprehension
  concatenated to it under a comment block carrying the measurement, the three-way partition, the
  `null`-never-a-default rule and the scoped `alertable` argument; three new docstring paragraphs.
- `boty/cli.py` — `_remembered` beside `_current_intervals`; `watch_cycle`'s call gains both
  keywords under the ordering comment; `main`'s check path gains the same two under a two-reason
  comment.
- `scripts/mutation_check.py` — M34 and M35 under one pair comment block.
- `tests/test_status.py` — the `# REQ-21: every configured watch has a row` section (9 tests);
  `_result` gains `name`; `_payload` gains `watches` and `remembered` on the `_OMITTED` sentinel;
  the exact-keyset assertion **enumerated** with `checked`, still `==`.
- `tests/test_cli_watch.py` — the `# REQ-21: every configured watch has a row, on both surfaces`
  section (4 tests) with `_paced_config`, `_backed_off_pacer` and `_published_watches`.

## Evidence

### `make verify-offline`, verbatim

```
=== verify: identity, lint, tests, types, fixtures, controls, mutation ===
identity check: PASS — 218 file(s), no host identity found
All checks passed!
848 passed in 10.94s
Success: no issues found in 18 source files
fixtures: 11 fixture(s) under /home/dan/CodeProjects/pokemongoplusplus/tests/fixtures
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 31 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (819 passed, 29 skipped in 11.13s)
  CAUGHT    M34 boty/status.py: 3 test(s) failed — test_every_configured_watch_has_a_row_while_only_the_due_ones_are_fetched, test_every_configured_watch_has_a_row_whether_or_not_it_was_read, test_remembered_rows_come_after_every_fresh_row_and_are_ordered_by_key
  CAUGHT    M35 boty/status.py: 2 test(s) failed — test_every_configured_watch_has_a_row_while_only_the_due_ones_are_fetched, test_a_remembered_row_refuses_the_authority_a_derived_value_would_grant
mutation check: 31/31 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
EXIT=0
```

**31 of 31 mutations caught.** The ratio is **exactly two above the 29/29 `07-03-SUMMARY.md`
recorded** — **no discrepancy**; that number was read from the summary and confirmed against
`grep -c 'ident="M' scripts/mutation_check.py` -> **29** before either ident was registered, and it
reads **31** after. **Survivor list empty**: `grep -c SURVIVED` over the captured run returns **0**.
**848 passed**, above 07-03's recorded **835** by the 13 tests this plan added. mypy clean over **18**
source files. Controls **SKIPPED** — **no live retailer read was made and none was planned.**

### M34 watched going red BY HAND, alone, before the harness was ever asked

```
M34 APPLIED at the only occurrence
                "store": None,
                "store_pinned": w.store_id,
                "read_at": read_at,
                "checked": True,
            }
=== pytest tests/test_status.py tests/test_cli_watch.py -q ===
FAILED tests/test_status.py::test_every_configured_watch_has_a_row_whether_or_not_it_was_read
FAILED tests/test_status.py::test_remembered_rows_come_after_every_fresh_row_and_are_ordered_by_key
FAILED tests/test_cli_watch.py::test_every_configured_watch_has_a_row_while_only_the_due_ones_are_fetched
3 failed, 78 passed in 0.27s
EXIT=1
```

**The revert, proved rather than assumed:** `git status --porcelain` printed nothing before M35 was
applied.

### M35 watched going red BY HAND, alone

```
M35 APPLIED at the only occurrence
212:                "alertable": r.alertable,
367:                "alertable": availability == Availability.IN_STOCK.value,
=== pytest tests/test_status.py tests/test_cli_watch.py -q ===
FAILED tests/test_status.py::test_a_remembered_row_refuses_the_authority_a_derived_value_would_grant
FAILED tests/test_cli_watch.py::test_every_configured_watch_has_a_row_while_only_the_due_ones_are_fetched
2 failed, 79 passed in 0.26s
EXIT=1
```

**The revert, proved:** `git status --porcelain` printed nothing after it. The two mutations were
never applied at the same time — two simultaneous mutations cannot show which test killed which.

**The by-hand lists and the harness's lists agree exactly**, 3 and 2 respectively, by name. That
agreement is the only thing that makes "CAUGHT" mean anything.

### Every measured anchor count, taken BEFORE registration

```
$ python -c "src.count('                \"read_at\": read_at,\n                \"checked\": False,')"
M34 two-line anchor count: 1
$ python -c "src.count('                \"checked\": False,')"
single-line fragment count: 2
$ grep -c '"checked":' boty/status.py
4
$ python -c "src.count('                \"alertable\": False,')"
M35 anchor count: 1
$ grep -n '"checked":' boty/status.py
177:                "checked": True,      <- fresh watch row (this plan)
193:                "checked": False,     <- RETAILERS array, paced branch (2026-08-04)
299:                "checked": True,      <- retailers array, checked branch
374:                "checked": False,     <- remembered watch row (this plan)
```

**The second count is the reason the first has the shape it has.** `apply_mutation` replaces the
FIRST occurrence, and the first single-line `"checked": False,` is **line 193, the retailers array's
paced branch** — a different rule entirely. A single-line anchor would have mutated that, been killed
by `tests/test_pacing.py:320`'s paced-retailer test, and stood in the registry as a gate on something
it does not gate. That is M19's recorded trap and 07-03's M33 trap, **third occurrence in this
phase**, measured before it was walked into rather than after.

M35's anchor counts **1** because the fresh branch reads `r.alertable` and the literal exists only on
the remembered branch — so no extension to two lines was needed, and none was made.

### THE ROW NUMBERS, QUOTED AS THE CLAIM THEY ARE — 07-06 NEEDS THESE

One `watch_cycle` against `config/products.yaml`'s real shape, this host's real `state.json` loaded
verbatim, and a `pacer-state.json` driven to gamestop 3 / amazon 4 / target 7 / walmart 7 refusals,
at `now=0.0`:

```
configured watches: 13
FETCHED this cycle: 3   ["bestbuy:CONTROL — Pokémon Let's Go, Pikachu! (Switch)",
                         'nintendo:CONTROL — Nintendo HDMI cable',
                         'nintendo:Pokémon GO Plus +']
PUBLISHED rows:     13
checked true: 3    checked false: 10
```

**13 rows published while 3 were fetched.** The denominator is **13**, from `Config.load`, and it is
**not the 14 the planning documents carry** — see § *Corrections recorded beside the planning
documents* below. **07-06's checkpoint must tell Dan the dashboard goes to 13 rows, not 14.**

The row count *before*, on the live file this daemon was writing when execution started
(2026-08-14 07:36:57 CDT, 78 seconds old at the time it was read, so the daemon was live):
**5 watch rows, 4 604 bytes**, with amazon, gamestop and target `checked: false`. The eight absent
watches were all five gamestop watches, both amazon watches and the target control.

### Walmart's row, written out in full as it will publish

```json
{
  "name": "Pokémon GO Plus +",
  "retailer": "walmart",
  "availability": "out_of_stock",
  "price": null,
  "detail": null,
  "url": "https://www.walmart.com/ip/Pok-mon-GO-Plus-for-Nintendo-Switch/1203950273",
  "control": false,
  "alertable": false,
  "rung": null,
  "extraction": null,
  "degraded": null,
  "store": null,
  "store_pinned": null,
  "read_at": null,
  "checked": false
}
```

**It will publish exactly that, indefinitely, until a store is pinned**, and that is the honest
output rather than a defect. `state.json` holds `walmart:Pokémon GO Plus + -> "out_of_stock"` as a
bare pre-07 string with no stamp; `WALMART_STORE_ID` is unset (`QUESTIONS.md` § 0f, open), so every
Walmart reading is now `Availability.UNKNOWN`; and `State.transitioned_to_stock` returns on UNKNOWN
**before** it writes. So the value can no longer be updated by anything, and the age genuinely is not
established. Inventing one would be this phase's own defect.

**And when Walmart IS due, the same watch publishes a DIFFERENT row** — `availability: "unknown"`,
`checked: true`, with its own stamp — because a reading we took always beats a reading we remember.
It must not fall back to the memory there: `checked: true` would then be true of a row whose
availability came from two days ago. Both rows are honest, and the row says which it is. **07-06's
checkpoint material.**

### The cycle-unchanged evidence

**Nothing about what is fetched, when, or by whom moved.** The three fetch-sensitive suites, run
together:

```
$ .venv/bin/python -m pytest tests/test_pacing.py tests/test_monitor.py tests/test_cli_watch.py -q
164 passed in 0.30s
```

- `tests/test_monitor.py` pins which retailers `run_once` skips.
- `tests/test_pacing.py` pins the backoff arithmetic, the cap and the paced-retailer payload —
  including 07-03's `test_the_backoff_schedule_is_exactly_the_schedule_it_was`, whose expected
  seconds are literals rather than re-derivations.
- `tests/test_cli_watch.py`'s REQ-16-across-a-restart section pins **measured cycle counts**.

Beyond the suites, the headline test asserts it directly: `asked == ["walmart:goplusplus"]` in a
cycle that published three rows. `run_once` is called with the same arguments it was, `paced` is
computed the same way, the alert and health blocks are untouched, and the pacer is still never passed
to `run_once` on the check path.

### The static gate on both call sites

```
$ .venv/bin/python -c "...ast over boty/cli.py..."
both write_status call sites thread the configured watches and the ledger
```

Exactly two `write_status` calls exist in `boty/cli.py` and each passes `watches=` and `remembered=`.
The same assertion lives in `tests/test_cli_watch.py` rather than only in this plan's `<verify>`, so
it runs on every future edit.

### The published payload size, so T-07-12 is priced rather than described

| | rows | bytes |
|---|---|---|
| live file at execution start (pre-07-04, daemon running) | 5 | **4 604** |
| one cycle under 07-04, real config, 4 retailers paced out | 13 | **8 402** |

**The plan's own estimate was wrong and is corrected here rather than repeated.** T-07-12 predicted
*"2 838 bytes at 8 rows today; 13 rows, five of them mostly `null`, put it under 4 KB."* The 2 838
figure predates 07-01's and 07-03's keys, and the measured file was already 4 604 bytes at 5 rows
before this plan touched anything. Measured after: **8 402 bytes**, roughly double. The disposition
is unchanged and the reason is unchanged — one dashboard polls it every 30 seconds over a tailnet
with no public exposure — but it is now the measured number rather than an under-estimate.

## THE IDENT ARITHMETIC, IN FULL, BECAUSE TWO LATER PLANS DEPEND ON IT

- **The orchestrator's brief for this plan named M35–M36. It was off by one**, on the belief that
  07-03 consumed M33 and M34. Measured: 07-03 consumed **M33 only**, and stated M34's reservation in
  `scripts/mutation_check.py`'s M33 comment block — *"M34 IS NOT A NEW GAP … This plan consumes M33
  only"* — read there before either ident was taken here.
- **This plan consumed M34 and M35**, the next two free idents. Taking M35–M36 would have left M34 an
  orphan beside M21–M24, an unallocated hole three plans had already written into the registry as
  *reserved, not a gap*.
- **07-05's pair is therefore M36/M37**, one higher than `07-PLAN-OUTLINE.md` assigns it (M35/M36).
  The outline is **not edited**; this is recorded beside it.
- **The registry ends this phase at 33, and the phase adds seven idents, not six.** M31, M32, M33,
  M34, M35, M36, M37.
- **07-06 still records the count rising FROM 26** — `07-PLAN-OUTLINE.md` § *CORRECTION 1* is
  unaffected by any of the above and still governs.
- **M21–M24 remain the intentional gap and were not filled**, on `mutation_check.py:669` and
  `tests/test_support_matrix.py`'s message: *"Idents are reserved across concurrent plans, not
  renumbered."* Fourth statement of that lesson in this phase.

## Corrections recorded beside the planning documents, never edited into them

Same footing as 07-01's nine-arms note, 07-02's two-extra-comments note, 07-03's five and Phase 3.1's
precedent. **No planning document was edited.**

### 1. The denominator is 13, not 14

`07-PLAN-OUTLINE.md`, `07-PATTERNS.md` and 07-01/02/03 all say **14 configured watches**, sourced
from `grep -c "retailer:" config/products.yaml`. Measured through the loader that actually builds
them:

```
Config.load('config/products.yaml') -> 13 watches
gamestop 5, walmart 2, nintendo 2, amazon 2, bestbuy 1, target 1;  6 of them controls
```

The fourteenth `grep` match is a **comment** at `config/products.yaml:309` — *"There is no `retailer:
pokemoncenter` entry and that is a finding, not a gap"* — a sentence about an ABSENT watch counted as
a present one. Same class of error as `grep -c 'ident="M'` counting prose, which
`07-PLAN-OUTLINE.md` § *Finding 1* records one file over. **It matters concretely: 07-06's checkpoint
tells Dan the dashboard goes to 13 rows.**

### 2. The row count is a function of pacing — three readings now, and they disagree

| when | rows | source |
|---|---|---|
| 2026-08-13 08:25:10 | 3 | `07-PLAN-OUTLINE.md` § *Finding 4* |
| 2026-08-13 09:24:54 | 8 | `07-04-PLAN.md` § *The measurement, re-taken today* |
| **2026-08-14 07:36:57** | **5** | **measured at the start of this execution** |

An unchanged config every time. **The sharper statement is not any one of those numbers: it is that
the watch list changed size three times without the configuration changing once.** A reader who
checked the page twice in a morning had no way to tell a watch that had been removed from a watch
that had not been asked. The plan's own framing of this is correct and this measurement is a third
data point for it, not a contradiction of it.

### 3. `store` is not republishable and half of the outline's sentence is not achievable

`07-PLAN-OUTLINE.md` § *Evidence constraint* says this plan *"republishes `store` and `store_pinned`
on carried-forward rows"*. **`store` is what a page said answered; the ledger holds no such thing**,
so a remembered row publishes `store: null`. Only `store_pinned` is carried, and it comes from
tracked `config/products.yaml` rather than from any reading. The threat's substance survives in
T-07-05 and is sharpened there: the one place this phase widens a served file is `store_pinned`
reaching rows that were not checked. On this host it is `null` anyway.

### 4. Two of the plan's predicted M34 killers do not fire

`07-04-PLAN.md` expects M34 to be caught by `test_a_check_publishes_every_watch_and_calls_none_of_
them_remembered` and by Task 1's key-order test. **Neither does**, and both for good reasons: `boty
check` re-reads every watch, so its remembered branch emits no rows at all and there is nothing on
that surface for M34 to flip; and the key ORDER is untouched by a mutation that changes only a value.
The registry names the **three measured** killers. A gate is named after watching it fail, never
after expecting it to — 07-02's Pattern 3, and the mirror of 07-03's deviation 2 where the
measurement was larger than the prediction rather than smaller.

## Residuals carried forward

### The latent `storeTag` consequence — 07-05's to resolve

`served/boty/index.html`'s `storeTag` renders `store: null` with a **non-null** `store_pinned` as a
`store ? · pinned X` **warn** tag. On this host it cannot fire today: `WALMART_STORE_ID` is unset, so
`store_pinned` is `null` too and the tag renders nothing. **But the moment Dan pins a store, every
remembered Walmart row carries a warning that is literally true** — there was no page, so no store
answered — **on a row whose actual story is "not checked this cycle".** True in the letter,
misleading in the register.

**Recorded here rather than fixed**, because `served/boty/index.html` is **07-05's file** and reaching
into it would break this phase's serial file ownership for a latent case. 07-05 owns it.

### The dashboard tolerates every `null` this plan introduces — verified, not assumed

Checked against `served/boty/index.html` rather than hoped: `esc(null)` is `''` (line 97,
`String(s ?? '')`), `w.price != null` guards the price (158), `w.degraded` and `w.extraction ===
'dom'` are both falsy on `null` (155), `w.url` is always a config string so the link survives, and
`.dot.unknown` is a styled class already (38). **No dashboard edit was required by this plan and none
was made.** `checked`'s consumer lands in 07-05, the same producer/consumer sequencing `read_at`
already has.

### `pacer-state.json` is still written non-atomically

Unchanged from 07-03's T-07-03b, and deliberately not touched here: the failure direction
over-reports staleness, which is the safe direction, and the promotion belongs to 07-06's judgement
rather than to a plan whose rule was that pacing behaviour does not move.

### M36/M37's disposition — reserved, not lost

**07-05's pair is M36/M37.** Stated in `scripts/mutation_check.py`'s M34/M35 comment block, where
07-05 will read it, and in § *The ident arithmetic* above. M21–M24 stay unfilled.

## Deviations from Plan

Three, all recorded rather than quietly absorbed. None changed what shipped.

**1. [Rule 3 — the plan's M34 killer list was a prediction, and the measurement was smaller]**

- **Found during:** Task 3, at the by-hand red-watch, before the harness was ever run.
- **Issue:** the plan names `test_a_check_publishes_every_watch_and_calls_none_of_them_remembered`
  and Task 1's key-order and partition tests as M34's expected killers. Applied by hand, M34 kills
  **three** tests and neither of those two is among them. Writing the predicted list into the comment
  would have published a larger catch than the one that happened.
- **Fix, following the tree over the plan:** the registry comment names the **three measured
  killers**, and states in place why each predicted-but-absent one is absent for a good reason rather
  than because a test is weak.
- **Committed in:** `07d51ae`.

**2. [Rule 2 — the `alertable` killer test measures its own fixture rather than asserting it]**

- **Found during:** Task 1, writing the RED tests.
- **Issue:** the plan requires M35's killer to use *"exactly the configuration under which a derived
  value would be True"* — a remembered `in_stock` on a watch with no `max_price` — and warns that any
  other fixture lets M35 survive. Written as specified, that property is a *claim in a docstring*: if
  the fixture later drifted to a watch with a ceiling, the test would keep passing and M35 would
  quietly stop being gated, which is this phase's own T-07-07 failure mode.
- **Fix:** the test publishes the **same watch on the fresh branch** in the same body and asserts
  that row comes back `alertable: true`, plus `assert no_ceiling.max_price is None`. The fixture's
  non-vacuity is now measured inside the test that depends on it.
- **Committed in:** `d80775b`.

**3. [Recorded, not a rule — where the new `tests/test_status.py` section was placed]**

- The plan says the new section goes *"after the served-payload section"*. Taken literally that puts
  it between the served-payload section and REQ-08, ahead of two REQ-21 sections written before it.
  It was appended after the REQ-21 cadence section instead, keeping the file's chronological
  ordering, which is what 07-01 and 07-03 both did. No assertion, helper or name is affected.

**Total deviations:** 3. **Impact on scope:** none. No package was installed, no dependency added, no
clock frozen, injected or monkeypatched anywhere, and no live retailer read was made.

## Scope fence, honoured

`git diff --stat` over this plan's five task commits touches exactly the five files in
`files_modified`. **`boty/models.py`, `boty/retailers.py`, `boty/monitor.py`, `boty/pacing.py` and
`served/boty/index.html` were NOT touched.** Nothing here compares a stamp to anything, computes a
`stale` flag, renders a tag, or reads a threshold: 07-03's `intervals` keyword is passed through
untouched and **`Pacer.current_interval` is neither called nor re-derived by this plan**. No clock is
frozen, injected or monkeypatched; the aged ledgers are constructed by subtraction from the real
clock, `tests/test_pacing.py:585-591`'s method, as every plan in this phase has used.

`identity_check` -> **PASS — 218 file(s), no host identity found**. No real store number and no host
identity was written into a tracked file. `served/boty/status.json` (`.gitignore:31`) and `state.json`
(`.gitignore:21`) are both gitignored, confirmed with `git check-ignore -v` today. The watch names and
target URLs this plan publishes are already in tracked `config/products.yaml`.

**REQ-21 is NOT marked complete here**, on the outline's rule and 07-01's, 07-02's and 07-03's
precedent: *a requirement is not marked complete by the plan that ships its code.* **07-06 closes it
by measuring what landed.** `requirements-completed` is `[]` deliberately.

## Next Phase Readiness

**07-05 can start.** What it inherits:

- **A row that can be old**, for every configured watch, on both surfaces — which is what criterion 3
  needed to exist before staleness could be *presented* at all. Its threshold is 07-03's
  `current_interval_seconds`, already in the `retailers` array; its renderings are 07-05's.
- **`checked`**, a new boolean key whose consumer 07-05 writes. No `UNTRUSTED` entry is needed: that
  list covers interpolated **string** keys, and this is a boolean beside existing keys widened to
  `null`.
- **M36/M37**, not the outline's M35/M36.
- **The `storeTag` warn-tag consequence above**, which becomes live the moment `WALMART_STORE_ID` is
  set.
- **The 6-hour figure, not the 97-minute one**, for target and walmart — 07-03's measurement note,
  unchanged and still governing.

**Standing concern, unchanged and now published:** `walmart:Pokémon GO Plus +` will carry
`out_of_stock` with `read_at: null` and `checked: false` on every cycle it is paced out, indefinitely,
until a store is pinned. 07-05 must render that as UNKNOWN age rather than as stale — those are
different sentences, and the row already carries enough to tell them apart.

## Self-Check: PASSED

Every claim above re-measured against the tree after this SUMMARY was written:

- **5 modified files** all present; this SUMMARY present.
- **5 task commits** all resolvable: `d80775b`, `3e32416`, `eb2e827`, `f4bdb83`, `07d51ae`.
- `def _remembered_rows` and `"checked": False` present in `boty/status.py`; `def _remembered`
  present in `boty/cli.py`; `remembered=_remembered(state)` present at both `write_status` call
  sites; `ident="M34"` and `ident="M35"` present in `scripts/mutation_check.py`.
- `grep -c 'ident="M' scripts/mutation_check.py` -> **31**. M34's two-line anchor still counts **1**;
  the single-line `"checked": False,` fragment still counts **2**; `grep -c '"checked":'` -> **4**;
  M35's anchor counts **1**.
- `make verify-offline` -> **EXIT=0**, 848 passed, **31/31**, survivors **0**.
- `.venv/bin/mypy` -> clean over 18 source files.
- `git status --porcelain` empty, proving both by-hand red-watches were reverted.

---
*Phase: 07-a-reading-has-an-age*
*Completed: 2026-08-14*
