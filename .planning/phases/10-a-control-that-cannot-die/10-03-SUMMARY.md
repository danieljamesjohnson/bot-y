---
phase: 10
plan: 03
subsystem: control-durability
tags: [REQ-24, criterion-4, durability-rule, D1-D5, applied-table, gate]
status: complete
requires:
  - "10-01 — the resolution predicate and its pinned no-canonical-no-structure residual, which is Best Buy's D5 PARTIAL"
  - "10-02 — the rung-3 status gap named in the wiring, which is Target's D5 NOT SATISFIED"
  - "docs/adding-a-retailer.md § The rule a control has to satisfy — the one unnumbered sentence this extends"
provides:
  - "D1-D5 — the durability rule as numbered clauses with stable identifiers, extending the original sentence rather than replacing it"
  - "the applied table: six controls x five clauses, every failing cell named, in docs/adding-a-retailer.md"
  - "a durability verdict line beside every control entry in config/products.yaml"
  - "tests/test_control_durability.py — six rules, both directions, clause list read out of the document"
  - "the measured finding that D4 is failed by all six, is NOT circular, and duplicates D3 wherever a reserve exists"
affects:
  - "10-04 — Best Buy's replacement candidate is judged against D1-D3 before a read is spent on it"
  - "10-05 — criterion 4 closes on this table; M44's kill set has a new gate module to measure against"
tech-stack:
  added: []
  patterns:
    - "a rule written in ONE place and read out of it by its gate, rather than duplicated into the test"
    - "a non-vacuousness assertion on an applied table — thirty passing cells is what a fitted rule produces"
    - "a verdict written twice, in the document a contributor reads and beside the entry an operator edits, with the two compared cell for cell"
key-files:
  created:
    - tests/test_control_durability.py
  modified:
    - docs/adding-a-retailer.md
    - config/products.yaml
decisions:
  - "Five clauses D1-D5; D3 (not generation-bound) is the new one and generalises the original's 'not a console'"
  - "D4 bounds the reserve at D1-D3, not at D1-D4 — the stronger reading is an infinite regress"
  - "D4 is satisfied by a RECORD, not by a second control: a second control per retailer would make 10-02's mixed arm reachable"
  - "Target's D5 is NOT SATISFIED and stays so; inventing a status in boty/browser.py remains refused"
  - "The clause list is parsed out of the document; hard-coding it would make 'you may re-cut them' false"
  - "The contributor doc may not cite a .planning/ path — the mutation sandbox does not copy that directory"
metrics:
  duration: "~1h"
  completed: 2026-09-02
actuals:
  tokens: 11675
  tasks: 3
  commits: 4
---

# Phase 10 Plan 03: The Durability Rule, Written Down and Applied — Summary

The rule for what makes a control durable is now **five numbered clauses**, applied to **all six**
controls this project ships, with **twelve of thirty cells not satisfied and every one of the six
condemned on at least one clause** — including the three nobody wants named. A gate binds the naming
to the configuration in both directions, so it cannot be dropped by whoever adds the next control.

**No live retailer request of any kind was made. No control was changed.** The diff against
`config/products.yaml` is **insertions only**.

---

## THE RULE, AS SHIPPED

The original sentence is quoted whole and **kept** — *"first-party, evergreen, restocked routinely,
never the subject of a buy-box fight, and not a console"* — and the extension is dated 2026-09-02.

| id | clause | what it is |
|---|---|---|
| `D1` | **first-party by construction** | the retailer's own entity or house brand, so no buy-box rotation can take the listing away. Absorbs two of the original's clauses, which were one idea stated twice |
| `D2` | **replenished, not released** | a consumable or evergreen staple, restocked routinely; never a unit with a launch date and an end of life |
| `D3` | **not generation-bound** | **new.** Its existence must not depend on a hardware or software generation the manufacturer will end. Generalises *not a console*: a console is the archetype, not the whole |
| `D4` | **a recorded reserve that itself passes `D1`–`D3`** | the document already asked for a fallback; this checks it against the rule instead of merely requiring one |
| `D5` | **its death is legible** | a dead target reads as a dead control, not a refusal and not a broken detector. **Nothing here satisfied this before `10-01` and `10-02`** |

`D1`–`D4` are properties of the **product**; `D5` is a property of the **monitor**, and is the only
one a contributor can fix without changing the control.

**`D3`'s justification is the ROADMAP's own sentence, and its premise is corrected in the same
breath.** Criterion 4 says *"Best Buy's died because it was a specific game SKU; a control that can be
discontinued eventually will be."* That the control **died** is not established — Collision 10 shows
the evidence is absent-then-stale — so the document carries the rule half and explicitly does not
assert the control is dead. **Nothing in this plan says otherwise, in prose, in a test name or in a
commit message.**

---

## THE CONTROL COUNT CAME FROM THE LOADER

```
Config.load('config/products.yaml') -> 13 watches, 6 with control=True
grep -c 'control: true' config/products.yaml -> 7
```

**Six.** The seventh grep match is the comment above the transition watches saying they are
*deliberately not* controls. The gate asserts **both numbers** so the divergence is a measured fact
rather than a comment, and a future agent who replaces the loader call with a grep meets it there.

---

## THE APPLIED TABLE

| Control | Retailer | D1 | D2 | D3 | D4 | D5 |
|---|---|---|---|---|---|---|
| CONTROL — PS5 console | gamestop | SATISFIED | **NOT SATISFIED** | **NOT SATISFIED** | **NOT SATISFIED** | SATISFIED |
| CONTROL — Great Value whole milk | walmart | SATISFIED | SATISFIED | SATISFIED | **NOT SATISFIED** | SATISFIED |
| CONTROL — Pokémon Let's Go, Pikachu! (Switch) | bestbuy | SATISFIED | **NOT SATISFIED** | **NOT SATISFIED** | **NOT SATISFIED** | **PARTIAL** |
| CONTROL — Nintendo HDMI cable | nintendo | SATISFIED | SATISFIED | **NOT SATISFIED** | **NOT SATISFIED** | SATISFIED |
| CONTROL — up&up microfiber dust cloths | target | SATISFIED | SATISFIED | SATISFIED | **NOT SATISFIED** | **NOT SATISFIED** |
| CONTROL — Amazon Basics AA batteries (20-pack) | amazon | SATISFIED | SATISFIED | SATISFIED | **NOT SATISFIED** | SATISFIED |

**12 of 30 cells not SATISFIED. Six of six controls condemned on at least one clause.** Every failure
is recorded **named and unrepaired**; only Best Buy's is in scope for repair and only `10-04` can
confirm one.

**Every verdict is derived from what the control IS** — its product class and its addressing — not
from what a page says today. No page was fetched.

### The console finding, recorded plainly

The rule's own last clause forbade a console before this phase started. GameStop's control is a PS5
console. **Nothing in the suite noticed for the life of the project**, and the argument against it
was even written down — `config/products.yaml`'s Walmart block says *"Do not use a console here"* two
hundred lines above the GameStop entry, in prose, about a different retailer, gating nothing.

That is not an accusation. It is the entire argument for Task 3: an unapplied, ungated rule is a rule
that is already being broken, and the only question is when somebody finds out.

### The legibility column carries TWO gaps, and a clean sweep there would have been the failure

- **Target — NOT SATISFIED.** Rung 3, and `boty/browser.py` returns `Page(status=200)`
  unconditionally because the transport surfaces no main-frame status. A delisted Target control
  renders Target's own not-found page, reads no offers, and is indistinguishable from a reskin:
  neither producer can fire. **No status was invented to make this cell pass**, and the refusal is
  restated at the verdict.
- **Best Buy — PARTIAL.** Clauses A and B of the resolution predicate cover the search redirect and
  the foreign-product page. A page with neither a canonical link nor parseable structure is not
  distinguishable from a reskin, and that residual is pinned by
  `test_the_residual_no_canonical_and_no_structure_is_not_a_dead_control` in `tests/test_retailers.py`
  — cited by name, so the cell rests on a gate rather than on a sentence.

---

## `D4`: FAILED BY ALL SIX, NOT CIRCULAR, AND PARTLY REDUNDANT — ALL THREE MEASURED

**Both recorded reserves were checked against the rule, not counted.**

| control | recorded reserve | verdict |
|---|---|---|
| bestbuy | `Pokémon: Let's Go, Eevee!`, in `docs/retailer-evidence.md` § Best Buy | fails `D2` **and** `D3` — **the same pair the incumbent fails** |
| nintendo | the AC adapter, named in `config/products.yaml` beside the control | fails `D3` — **the same clause the cable fails** |
| gamestop, walmart, target, amazon | none recorded | not satisfied for absence — and the document asked for a fallback before this clause existed |

**Is `D4` circular? No — and the reason is worth stating, because the other reading of it is.** As
shipped, the reserve must pass `D1`–`D3`, *not* `D4`, so the check terminates at one level. The
natural stronger reading — *the reserve must pass every clause, including having a reserve of its
own* — is an infinite regress, and it is deliberately not the rule. The clause states the bound and
says why.

**What is true and does not flatter the clause, recorded rather than smoothed:**

- At the two retailers where a reserve **exists**, `D4` condemns nothing `D3` had not already
  condemned. It is `D3` restated one level down. Where a fallback comes off the same shelf, it
  inherits the same end of life, and that is the whole of what `D4` adds there.
- It carries **independent** information at exactly three retailers — walmart, target, amazon — whose
  controls pass `D1`–`D3` and where `D4` is the **only** clause that fails.
- **No control in this tree satisfies it.** A clause nothing satisfies is either a bar to grow into
  or a bar nobody can clear. This one is the first: clearing it costs one recorded line per control.
  It is left as written rather than softened to produce a pass.

**And `D4` is satisfied by a RECORD, not by a second watch.** That distinction is load-bearing:
every retailer here has exactly one control, which is the only reason `10-02`'s mixed-cause arm is
latent rather than live. A clause that quietly asked for a second `control: true` entry per retailer
would have made it reachable — which is the second-order effect `10-02` flagged and this clause
deliberately does not trigger.

---

## PREDICTION vs FINDING

The plan predicted the rule would condemn GameStop (`D2`, `D3`), Best Buy (`D2`, `D3`, `D4`) and
Nintendo (`D3`, `D4`). **All three predictions held.** What was found in addition:

| difference | what it is |
|---|---|
| **walmart, target and amazon also fail `D4`** | the plan did not predict these. Their controls pass every product clause and have **no recorded reserve at all**. Recording that they fail for absence is what stops `D4` from being a clause about two retailers |
| **`D4` is failed 6/6** | stronger than predicted, and the reason it is stated as a limit of the clause rather than as coverage |
| **the `D5` column came out exactly as predicted** | Target NOT SATISFIED, Best Buy PARTIAL. Two gaps, not one, and not a clean sweep |

Nothing was found that made a predicted failure disappear. **No clause was dropped, softened or
reworded to make a control pass.**

---

## THE GATE, AND ITS RED IN SIX DIRECTIONS

`tests/test_control_durability.py` — **16 tests**, six rules as pure functions over text so the
corruption tests run the *same* rules against broken copies of the real inputs, on
`tests/test_support_matrix.py`'s precedent.

Both directions:

- **config → document:** every loaded control has a table row **and** a verdict line beside its own
  config entry;
- **document → config:** every declared clause is a column, every row states a known verdict in every
  column, every row is a control the config configures, and the two records agree **cell for cell**.

**The clause list is parsed out of the document** (`declared_clauses`), never carried in the test. A
gate holding its own copy of the rule is a second place for the rule to live, and it would make the
document's *"you may re-cut the clauses"* false. **The control set is loaded, never grepped.** An
unparseable rule or a missing table **raises** rather than reporting clean — both asserted.

### The reds, on the real tree, with actual counts

Copies were taken **before the first perturbation** and every revert was `cp` from the copy, never
`git checkout` — the mistake `10-02` recorded losing real work to. Both restores were verified
**byte-identical** with `diff`. The pycache was cleared between every perturbation and its revert.

| # | perturbation | result | which tests died |
|---|---|---|---|
| P1 | a control's config verdict line removed (nintendo) | **2 failed / 14 passed** | the config-verdict rule and its corruption test |
| P2 | the `D5` clause declaration removed from the document | **2 failed / 14 passed** | the column/clause rule and its corruption test |
| P3 | a table row for a control that is not configured | **1 failed / 15 passed** | the unconfigured-row rule |
| P4 | a configured control with no table row (target) | **4 failed / 12 passed** | the missing-row rule, plus three whose anchors the deleted line carried |
| P5 | a blanked `D5` cell (target) | **4 failed / 12 passed** | the missing-verdict rule, the agreement rule, and two anchor-carrying corruption tests |
| P6 | target's `D5` softened to SATISFIED **in the document only** | **3 failed / 13 passed** | the agreement rule and two anchor-carrying corruption tests |

**No rule failed to go red.** There is no "could not be made to fail" finding among P1–P6.

P4, P5 and P6 also redden corruption tests whose `_drop_line` / `_replace_once` anchors were the very
line perturbed — those helpers assert a unique anchor and raise when it moves, which is the
ambiguity trap `apply_mutation` walks into and is deliberate rather than collateral noise.

### The non-vacuousness assertion

`test_the_rule_condemns_something_which_is_the_point_of_applying_it` exists because **every other
rule in the module is satisfied by a table of thirty SATISFIED cells** — and that is precisely the
table a rule fitted to its subjects produces. Its docstring states the repair procedure: if a future
phase genuinely repairs every control, **delete this test with the measurement that justified
deleting it**; do not reintroduce a failure to keep it green.

### Collection count elsewhere

**Unchanged.** 1020 tests before this plan, **1036 after**, and the new module contributes exactly
16. No existing test reddened at any point in this plan.

---

## THE WALMART PIN

Recorded **beside** the durability verdict, never as part of it. The milk control passes every
product clause; the pin is an **availability** fact about the reading.

`WALMART_STORE_ID` is **SET ON DISK since 2026-08-25**, in the daemon's owner-readable environment
file outside this repository, and **NOT YET IN EFFECT** — that file is read once at process start and
the restart is deferred. Any process that does not load it — a test, a developer shell — sees no pin
and the reading is UNKNOWN by design.

**Never described as unset** (true 2026-08-10 to 2026-08-25, stale since). Discussed **by key only**;
its presence is only ever measured as a count. The value was never read, derived, inferred or
printed, and no digits were added to `config/products.yaml`'s comments.

---

## Deviations from Plan

### 1. [Rule 3 — blocking, and it invalidated two of this plan's own commits] The contributor doc may not cite a `.planning/` path

- **Found during:** Task 3, on the first `make verify-offline`.
- **Issue:** Task 1 cited `.planning/ROADMAP.md` and Phase 10's decision record as backticked paths.
  Both exist, both passed `tests/test_contributor_docs.py` in the working tree, and both **failed the
  mutation baseline**: `build_sandbox()` rebuilds the tree from `SANDBOX_CONTENTS`, which
  deliberately excludes `.planning/`, so rule 1 resolves the citation against a temp root that has
  never held that directory. Measured: **2 failed / 1005 passed** in the sandbox, and
  `make verify-offline` exited `VERIFY: FAIL (mutation check)` — with a message that reads as a
  mutation regression rather than as a doc citation.
- **Fix:** the prose, not the gate. Both citations became prose references. **`SANDBOX_CONTENTS` was
  NOT widened** — Phase 4's rule for that constant requires an entry be proven load-bearing by
  removal, and a doc citation cannot do that; the file's own comments already refuse the widening for
  `.planning/` on cost grounds (2.9 MB, copied once per mutation).
- **Recorded where the next person meets it:** a dated parenthesis in the document itself, so the
  next writer who wants to cite a planning file learns why they cannot before paying the same
  red baseline.
- **Honest consequence:** commits `0799b7e` and `bacea1c` left `make verify-offline` red at the
  mutation stage. It is green at `c569b91`. Saying so beats claiming the plan was green throughout.

### 2. [process] The gate's doc citation was deferred one task

`docs/adding-a-retailer.md` was going to cite `tests/test_control_durability.py` in Task 2, and rule
1 correctly refused a citation of a file that did not exist yet — observed at **2 failed / 17
passed**. The subsection was moved into Task 3's commit rather than the path being written
un-backticked to evade the rule, which would have been dodging a gate by formatting.

### 3. [scope] `tests/test_contributor_docs.py` was NOT modified, and that is the answer to the plan's question

The plan asked which happened: the gate taught a new shape, or the gate weakened. **Neither.** No
`## ` heading was added — the new material sits under the existing `## Why a control product is
mandatory` as `###` and `####` sections — so the pinned heading list needed no extension, and nothing
in that module was loosened. The new sections are bound by `tests/test_control_durability.py`, which
locates the clause bullets and the table by their own shape and **raises** if either is gone.

**Nothing else deviated.** No architectural change was needed; no Rule 4 checkpoint was reached.

---

## Prohibitions — held

- **No live retailer request of any kind.** No `boty check`, no browser started, no fetch. Every
  verdict is derived from the product's class and addressing.
- **No write to** `state.json`, `pacer-state.json` or `served/boty/status.json`. No
  `systemctl restart boty`.
- **`.planning/STATE.md` and `.planning/ROADMAP.md` unedited.** No `gsd-tools` state or phase WRITE
  subcommand invoked.
- **Never `--no-verify`.** All four commits went through the tracked pre-commit hook; identity check
  PASS on each.
- **No control changed.** `git diff` against `config/products.yaml` is **73 insertions, 0 deletions**;
  the six controls' retailers and targets were re-read through the loader after the edit and are
  unchanged.
- **`WALMART_STORE_ID` never printed, derived or inferred**, and never called unset.
- **No clause dropped, softened or reworded** to make a control pass.

### Standing invariants, re-measured

| invariant | measured |
|---|---|
| `Pacer.current_interval` | **byte-unchanged by construction** — `boty/pacing.py` is not in `git diff --name-only b3e7795 HEAD` |
| `boty/pacing.py`, `boty/status.py`, `boty/cli.py`, `boty/models.py`, `served/boty/index.html` touched | **no**, none |
| both `cli.watch_loop` clock terms | present — `time.monotonic()` ×9, `time.time()` ×2 in `boty/cli.py`, untouched |
| `MAX_BACKOFF_SECONDS` | `6 * 60 * 60` |
| `COOLOFF_SECONDS` | `3 * 24 * 60 * 60` = 259200 |
| `STATE_VERSION` | 2 |
| `grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py` | **2** |
| `grep -c "INTENTIONAL GAP" scripts/mutation_check.py` | **9** — M21–M24 unfilled |
| highest registered mutation ident | **M43**; next free is **M44** (`10-05`'s). None registered here |

---

## Final gate

```
make verify-offline
mutation check: 39/39 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

**1036 tests passed** · ruff clean · mypy clean · identity check PASS (270 files) · mutation 39/39
caught, survivors 0.

---

## Known Stubs

**None.** No placeholder, no hardcoded empty value flowing to a UI, no TODO or FIXME added.

---

## Threat Flags

**None new.** This plan added no network endpoint, no auth path, no file-access pattern and no schema
change at a trust boundary. Of the plan's own register:

- **T-10-11** (an applied table as a repudiation surface) — mitigated as specified: 12 of 30 cells
  fail, every failing cell names its clause and reason, both reserve candidates were checked rather
  than counted, Target's `D5` is NOT SATISFIED, and the predictions are compared against the finding
  above so a softer result would have been visibly softer.
- **T-10-05** (tampering with the control set) — held: insertions only, no control changed, every
  failure named and unrepaired.
- **T-10-12** (a gate nobody watched fail) — mitigated: six broken copies, six recorded counts, the
  clause list derived from the document, and a non-vacuousness assertion for the failure mode the
  other five rules cannot see.
- **T-10-04** (the pin in new prose) — held: key only, count only, `identity_check.py --all` PASS on
  every commit and over all 270 files.

---

## Commits

| Commit | What |
|---|---|
| `0799b7e` | `docs(10-03)`: the durability rule, numbered, extending the sentence rather than replacing it |
| `bacea1c` | `docs(10-03)`: the rule applied to all six controls, with every failure named |
| `2993c31` | `test(10-03)`: the gate that makes the naming un-droppable, in both directions |
| `c569b91` | `docs(10-03)`: cite the gate, and stop citing paths the mutation sandbox has never seen |

---

## What this plan does NOT claim

- **Not that Best Buy's control is dead.** Collision 10 stands. The config comment beside that entry
  now says so explicitly.
- **Not that any control was repaired.** Every failure is named and unrepaired. `10-04` owns the only
  repair in scope, and only against a live reading.
- **Not that `D5` is closed anywhere it is not.** Target's gap is open and named; Best Buy's residual
  is open and pinned.
- **Not that `D4` is a well-earned clause everywhere.** It duplicates `D3` at the two retailers with a
  recorded reserve, and that is stated as a limit rather than as coverage.
- **Not that the `D5` SATISFIED cells were measured on the wire.** They record what the **monitor**
  does with a 404 or 410, which is gated by `10-02`'s tests. Whether a given retailer answers a
  removed product URL with a 404 rather than a 200 is a retailer fact, and this plan made no request
  to establish it.

---

## Self-Check: PASSED

| checked | result |
|---|---|
| `tests/test_control_durability.py` exists | **FOUND** |
| `docs/adding-a-retailer.md`, `config/products.yaml` modified | **FOUND** |
| commits `0799b7e`, `bacea1c`, `2993c31`, `c569b91` | all four **FOUND** in `git log` |
| six controls through the loader | **6**, grep **7** — both asserted by the gate |
| `make verify-offline` | **PASS (OFFLINE)**, 39/39 mutations caught |
