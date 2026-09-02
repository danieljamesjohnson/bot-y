---
phase: 10
plan: 05
subsystem: mutation-registry
tags: [REQ-24, criterion-5, M44, kill-set-comparison, verdict-table, false-dead]
status: complete
requires:
  - "10-01 — Health.dead_control and the arm M44 anchors on; Collision 10's offline premise correction"
  - "10-02 — the 404/410 producer and the mixed arm, two of M44's killers"
  - "10-03 — the D1-D5 applied table criterion 4 closes on"
  - "10-04 — the three live reads, the false dead, and bestbuy/D5 NOT SATISFIED"
provides:
  - "M44 — the dead-control arm, observed CAUGHT by 11 tests, registry 40/40, survivors 0"
  - "the kill-set comparison against all 39 prior idents, one sandbox each, recorded either way it fell"
  - "the producer anchor measured, rejected and recorded as an OPEN HOLE rather than a refusal"
  - "CLAUDE.md's registry counts advanced in the same commit that moved them"
  - "the five-criterion verdict table, two rows MET IN PART, no criterion reworded"
affects:
  - "a future phase — M45 on the resolution predicate would defend three tests no ident reaches"
  - "a future phase — the transport remedy for Best Buy's client-side redirect is named and unshipped"
tech-stack:
  added: []
  patterns:
    - "two candidate anchors broken in separate sandboxes, both kill sets recorded, the loser kept as evidence"
    - "a mutation priced against the WHOLE registry before the ident is taken, not after"
    - "counts in a document that gates nothing moved in the same commit as the thing they count"
key-files:
  created: []
  modified:
    - scripts/mutation_check.py
    - CLAUDE.md
decisions:
  - "M44 anchors on the ARM, not the producer: the producer kills neither criterion-1 state test and neither half of criterion 2"
  - "The producer anchor is an OPEN HOLE, not a refusal — 3 of its 4 killers are reached by no ident, so M45 there would defend something new"
  - "Criterion 1 is MET IN PART, not MET AS WRITTEN: the separation holds, one route INTO the first state was measured over-inclusive on the wire"
  - "Criterion 3 carries Collision 10's offline premise correction unconditionally, above and independent of what the wire said"
  - "M42's subset relation re-measured rather than repeated: 18 inside 32 today, recorded beside 08-04's 16 inside 28"
metrics:
  duration: "~1h"
  completed: 2026-09-02
actuals:
  tokens: 34000
  tasks: 3
  commits: 2
---

# Phase 10 Plan 05: The Mutation, the Counts and the Verdict — Summary

The phase closes with **M44 registered on behaviour and observed CAUGHT by 11 tests**, a registry at
**40/40, survivors 0**, and a five-criterion table in which **two rows are MET IN PART and no
criterion was reworded to make a row read better**.

And the headline the table has to carry is not the one the phase set out to write. The phase set out
to repair a dead control. What `10-04` measured is that **the control is ALIVE** — `IN_STOCK $59.99`,
first-party — and that **the monitor, through the path it is actually configured to use, calls that
same live SKU a dead control.** Twice. This project's core defect — saying something false,
confidently — rebuilt inside this phase's own new code, within four weeks of it being designed.

---

## M44 — WHAT IT REBUILDS, AND THAT IT IS BEHAVIOUR

**Anchor** (`boty/monitor.py`, `assess_health`), one indented line, occurring once:

```
dead_control = not refused and any(c.unresolved for c in broken)   ->   dead_control = False
```

Not a message, not a comment, not a rendered tag. **Run in a sandbox on 2026-09-02**, one dead
bestbuy control through `assess_health`:

| | unmutated | mutated |
|---|---|---|
| `dead_control` | `True` | `False` |
| `action` | *the target this control names no longer resolves to a product — pick a replacement and set it in `config/products.yaml`* | `''` |
| `reason` | *a control's target no longer resolves to a product … a fact about `config/products.yaml` rather than about the retailer or the extractor* | *a control product did not read IN_STOCK and was not refused, so readings from this retailer are unverified … the cause is not established* |

**The mutated sentence is the one `10-01` transcribed off pre-phase code, word for word**, and the
action is empty again — the one repair a person could make stops being named at the moment it is
true. `Result.unresolved` is still set, `DEAD_CONTROL_ACTION` is still defined, the arm still carries
its forty lines of comment about a state nothing can reach, and every surface reads as though the
phase shipped. That is the misattribution REQ-24 exists to end, rebuilt by deleting eight words.

**Observed CAUGHT: 11 test(s) failed, 996 passed, 29 skipped.** Registry: **40/40 mutations caught,
survivors 0.**

---

## BOTH CANDIDATE ANCHORS WERE BROKEN, AND THE LOSER IS KEPT AS EVIDENCE

Each in its own sandbox, failures read off the run, both re-measured a second time with **identical
counts**. Named THE ARM and THE PRODUCER rather than A and B, because the predicate one file over
already has a clause A and a clause B.

| candidate | mutation | result |
|---|---|---|
| **THE ARM** (registered as M44) | `dead_control = … any(c.unresolved …)` → `False` | **11 failed / 996 passed** |
| **THE PRODUCER** (measured, NOT registered) | `unresolved=canonical_is_the_search_endpoint or markup_was_read,` → `unresolved=False,` | **4 failed / 1003 passed** |

**The arm's 11 killers:** criterion 1's `test_state_one_a_dead_control_is_a_fact_about_our_configuration`
and `test_the_three_states_produce_three_different_reasons`; criterion 2's
`test_criterion_2_half_one_a_dead_control_never_says_the_retailer_refused_us` and
`test_criterion_2_half_two_a_dead_control_does_not_silence_a_refusal`; `10-01`'s tracer
`test_a_captured_page_that_does_not_carry_our_sku_becomes_a_dead_control`; `10-02`'s
`test_a_404_at_a_url_addressed_control_is_a_dead_control` at both parametrisations;
`test_a_dead_walmart_control_with_no_pin_is_dead_and_not_a_store_gap`; and all three
`tests/test_alert_text.py` partition gates.

**The producer's 4 killers:** `test_clause_a_the_retailer_says_you_are_on_a_search_page`,
`test_clause_b_a_real_product_page_read_for_a_foreign_sku`,
`test_refused_and_unresolved_are_never_both_true_on_one_result`, and the same tracer.

**Why the arm, on measurement and not on taste.** It is the line whose removal changes **which health
arm a dead control reaches**, which is REQ-24's whole subject — the transcript above is the arm's.
And decisively: **the producer kills neither criterion-1 state test and neither half of criterion 2.**
Those four tests build `Result(..., unresolved=True)` directly, never reach `_verdict_from_html`, and
pass unharmed under it. An ident on the producer would have left this phase's two closed criteria
with no mutation under them at all.

---

## THE KILL-SET COMPARISON AGAINST THE WHOLE REGISTRY

**All 39 existing idents were re-run on 2026-09-02, one sandbox each**, and their kill sets read off
the runs — the measurement taken **before** the ident was priced, not after.

```
M44 n=11   supersets among the registry: []
           largest overlap with any existing ident: 1 test — M30
           killers no existing ident reaches: 10 of 11
```

**So M44 buys DETECTION, not merely localisation**, and no existing ident's kill set contains it.
Before it, the registry had **no** mutation that criterion 1's three-state separation, either half of
criterion 2, `10-02`'s 404 producer or the dead-before-store-gap precedence could kill: **ten
assertions gated by tests and ungated by this harness.** The single overlap is
`test_only_the_arms_with_a_measured_remedy_name_something_a_person_can_do`, which M30 also reddens,
because both mutations leave an arm carrying no action.

**It could have fallen the other way and the block says what it would have written then** — M42's
does exactly that. **M42's subset relation was re-measured here rather than repeated on trust:** it
still holds, and its numbers have moved. `08-04` recorded 16 killers inside M33's 28; on 2026-09-02
the same two mutations kill **18 and 32**, with M42's set still wholly inside M33's and nothing
outside it. The suite grew; the relation did not change. **Both figures are kept.**

### The rejected anchor is an OPEN HOLE, not a refusal — and the distinction is measured

Neither candidate is a subset of the other (arm 11, producer 4, shared: the tracer alone), so
registering the arm **does not cover the producer**. **Three of the producer's four killers are
reached by no ident in this registry**, so an `M45` on the resolution predicate **would defend
something new**. It is not taken here only because criterion 5 asks for one ident and the arm is the
more informative of the two.

**That is the opposite of M43's rejected candidate**, which was refused because eleven assertions and
two idents already carried it. The two cases are written out separately in the file so this
registry's rule is not read as *"always refuse the loser"*.

**Next free ident is M45.**

---

## THE INTENTIONAL GAP, RESTATED AND NOT WEAKENED

`grep -c "INTENTIONAL GAP" scripts/mutation_check.py` → **10** (was 9; M44's block adds the tenth by
restating the rule). **M21–M24 remain empty.** `apply_mutation` cannot add a file, so the defect they
would cover is outside the harness by construction.

**Nothing was added to `SANDBOX_CONTENTS`.** `boty/monitor.py` has been in it since before this
registry existed and already carries four idents (M5, M15, M30, M32) — checked before the block was
written, exactly as M41, M42 and M43 checked it. That is the test M21–M24 failed.

---

## THE GATE — VERDICT LINE READ, NOT THE EXIT CODE

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
exit=0
```

**PASS (OFFLINE)**, which is one of three verdicts exit 0 cannot distinguish. It means the live
retailer controls were **not** run — deliberately: the read budget is spent, and `make verify` makes
live requests to all six retailers.

| measurement | result |
|---|---|
| tests | **1036 passed, 0 skipped**, 12.96 s |
| mypy | Success: no issues found in **18 source files** |
| ruff | All checks passed |
| identity check | **PASS — 273 file(s)**, no host identity found |
| fixtures | 11 fixture(s), all ok |
| mutation | baseline passes (1007 passed, 29 skipped in the sandbox); **40/40 caught, survivors 0** |

**The JS-executing gate BOUND rather than skipped, and that was checked rather than assumed.**
`tests/test_dashboard.py` → **21 passed, 0 skipped**, and `_js_runtime()` resolves to
`~/.nvm/versions/node/v24.16.0/bin/node` through its own glob (so it binds even where `make` does not
inherit nvm; nvm was sourced anyway). The suite reports **zero skips in the working tree** — the 29
skips in the mutation baseline are sandbox-only, from tests keyed on files `SANDBOX_CONTENTS`
deliberately does not copy.

---

## THE FIVE-CRITERION VERDICT TABLE

Criteria quoted from `ROADMAP.md`, unedited. **Nothing reworded. Two rows MET IN PART, and each names
its missing half in the same sentence as the half that holds.**

### 1. *Three states are distinct and asserted separately: dead control, refused, detector broken. Today the first is reported as the third* — **MET IN PART**

**The half that holds.** The three states are distinct, separately asserted and now
mutation-gated. `tests/test_monitor.py::test_state_one_a_dead_control_is_a_fact_about_our_configuration`,
`::test_state_two_a_refusal_is_a_fact_about_the_retailer`,
`::test_state_three_a_page_that_could_not_be_read_is_a_fact_about_us` and
`::test_the_three_states_produce_three_different_reasons` assert them apart; `10-01` observed all of
them red against nine recorded perturbations (P1–P9), and
`tests/test_alert_text.py::test_the_partitions_cover_every_arm_this_module_can_produce` gates the
domain so a sixth arm cannot be added silently. **M44 kills the first, the fourth and eight others.**

**The half that is missing, named in the same breath.** The states are separate; **one route INTO the
first state was measured over-inclusive on the wire.** `10-04`'s reads 1 and 2 put a **live** Best Buy
SKU into state one through clause A, because Best Buy's SKU search now answers with a *client-side*
redirect and `fetch_rendered` snapshots the announcing search shell. So the partition is sound and
the membership test that feeds it is wrong for the one retailer this phase was about. Unrepaired, and
the remedy named in `10-04`'s Deferred Issues. Nothing offline could have caught it: the fixtures are
the August pages.

### 2. *A dead control does not describe the retailer as refusing us, and does not silence a real refusal if both are true at once* — **MET AS WRITTEN**

Both halves asserted **apart**, because they fail for different reasons:
`tests/test_monitor.py::test_criterion_2_half_one_a_dead_control_never_says_the_retailer_refused_us`
and `::test_criterion_2_half_two_a_dead_control_does_not_silence_a_refusal`, plus the general form
`::test_no_group_containing_a_refusal_is_ever_told_nothing_was_refused`, parametrised over all three
shapes a mixed group can take. `10-02` observed each red against a recorded perturbation, and **M44
kills both halves.**

**Stated beside, not as a qualification of the verdict:** the mixed group is **latent** in the shipped
configuration — every retailer has exactly one control (`10-03`, control count read from the loader:
6 of 13 watches). The criterion is asserted, not observed in production, and `10-03`'s `D4` clause was
deliberately written to be satisfiable by a **record** rather than by a second control so that it
stays that way.

### 3. *Best Buy's control is repaired — measured against a real reading, not a fixture — or replaced with one that reads, with the replacement's durability argued* — **MET IN PART**

**First, the premise correction, which is not conditional on anything the wire said.**
`10-DECISIONS.md` § Collision 10 established **offline**, from `docs/retailer-evidence.md` with eleven
line citations each re-opened individually: **Best Buy's control has never been shown dead.** It was
last shown **alive** in early August — `IN_STOCK … $59.99 … ld+json: InStock from Best Buy` in four
separate `make verify` transcripts — and had then been **unmeasured for roughly four weeks**; the two
most recent attempts were `no Chrome/Chromium binary found`, a fact about **this host**. The single
"did not resolve" for that SKU is the one this repository itself documented as the **2026-08-04 false
dead**, and `grep` returns exactly one such line. **SKU 6577129 — the one that genuinely resolves to
nothing — was a product watch, recorded as *unconfirmed and probably wrong*, already removed from
config, and never the control.** The evidence was **absent-then-stale, not contrary**. Reading REQ-24
as *"the control died"* is a conflation of two different SKUs. **This was established without a live
read and a live result cannot unestablish it** — it would have gone in this row on the refusal
branch, on the unresolved branch, and on the branch where all three reads failed on a host error.

**Second, what the wire said.** Measured against a real reading, not a fixture: **read 3 returned
`IN_STOCK`, `$59.99`, `seller: "Best Buy"`** — the control is alive, and the offline finding is
confirmed rather than established by it. **There was nothing to repair. The defect was in a record.**

**The half that is missing.** Through the **configured** path the control does **not** resolve and is
reported as a dead control — reads 1 and 2, `unresolved=True` twice, the second carrying Best Buy's
own `308` to the canonical this repository recorded on 2026-08-02. That is named and **unrepaired**:
the remedy lives in `boty/browser.py` or `boty/retailers.py`, the three authorised reads were spent
establishing the fault, and **a transport fix no live reading has confirmed is a recommendation, not
a repair.** No replacement control was chosen either — any replacement is reached through the same
search URL and meets the identical clause A, so swapping the product would have fixed nothing and
`config/products.yaml`'s Best Buy target is byte-unchanged. `bestbuy`/`D5` was downgraded **PARTIAL →
NOT SATISFIED** on that reading, in both records the gate binds.

### 4. *The rule for what makes a control durable is written down and applied to every existing control, with any control failing it named* — **MET AS WRITTEN**

`D1`–`D5` in `docs/adding-a-retailer.md`, extending the original sentence rather than replacing it,
applied to **all six** controls, bound to `config/products.yaml` **cell for cell in both directions**
by `tests/test_control_durability.py` (16 tests; `10-03` observed six perturbations red, P1–P6),
including `::test_the_rule_condemns_something_which_is_the_point_of_applying_it` — a non-vacuousness
assertion, because thirty SATISFIED cells is what a rule fitted to its subjects produces.

**The controls the rule condemned, all six of six, named:**

| control | retailer | fails |
|---|---|---|
| CONTROL — PS5 console | gamestop | `D2`, `D3`, `D4` |
| CONTROL — Great Value whole milk | walmart | `D4` |
| CONTROL — Pokémon Let's Go, Pikachu! (Switch) | bestbuy | `D2`, `D3`, `D4`, **`D5`** (PARTIAL → NOT SATISFIED, `10-04`) |
| CONTROL — Nintendo HDMI cable | nintendo | `D3`, `D4` |
| CONTROL — up&up microfiber dust cloths | target | `D4`, `D5` |
| CONTROL — Amazon Basics AA batteries (20-pack) | amazon | `D4` |

**13 of 30 cells not satisfied** (12 before `10-04`'s downgrade, kept beside). The rule's own last
clause forbade a console before this phase started and GameStop's control is a PS5 — nothing in the
suite noticed for the life of the project. `D4` is failed **6/6** and that is recorded as a **limit of
the clause**, not as coverage: where a reserve exists it condemns nothing `D3` had not.

**Criterion 4's own premise is corrected rather than repeated.** It says *"Best Buy's died because it
was a specific game SKU"*. That the control **died** is not established (Collision 10). `D3` carries
the rule half — a control that can be discontinued eventually will be — and the document explicitly
does not assert the control is dead.

### 5. *`make verify-offline` exits 0, with at least one new mutation registered and observed CAUGHT* — **MET AS WRITTEN**

`VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)`,
`exit=0`. **M44 registered on behaviour and observed CAUGHT by 11 tests**; harness **40/40 caught,
survivors 0**; kill set compared against all 39 prior idents; both candidate anchors broken and both
kill sets recorded; M21–M24 still empty with the gap-marker count at **10**.

---

## Deviations from Plan

### 1. [Rule 3 — the plan contradicted itself about commit boundaries, and the must-have won]

- **Found during:** the hand-off between Task 1 and Task 2.
- **Issue:** the plan's must-have says `CLAUDE.md`'s counts are advanced **"in the SAME commit that
  registers M44"**, while Task 2's precondition says **"Task 1 is committed"**. Both cannot hold. M44
  was committed alone first (`d1e1528`).
- **Fix:** the counts were written and the commit **amended** (`e01b482`), so exactly one commit
  carries the ident and the numbers that describe it — the must-have's requirement, and 09-05's
  precedent for M43. The amend is recorded here rather than left to be inferred from a hash that no
  longer exists: **`d1e1528` is not reachable in the final history.**
- **Why the must-have won:** the counts gate nothing. `10-03` and this section of `CLAUDE.md` both
  record that they were stale for three days once, and that *"next free ident is M42"* would have
  handed the next agent a collision. Two commits is two chances to stop after the first.

### 2. [Rule 1 — a number quoted on trust was wrong] M42's kill-set figures had moved

- **Found during:** Task 1's registry comparison.
- **Issue:** the M44 block first quoted `08-04`'s *"16 killers inside M33's 28"*. Re-measured on the
  same tree: **18 and 32**.
- **Fix:** the relation was re-verified (still a **proper subset**, nothing in M42 outside M33), and
  **both figures are kept** — the newer one written beside the older in the code and in `CLAUDE.md`,
  per `docs/retailer-evidence.md` § 6, never over it. `08-04`'s number was true when it was written.

**Nothing else deviated.** No architectural change was needed; no Rule 4 checkpoint was reached; no
criterion was reworded.

---

## Prohibitions — held

- **No live retailer request of any kind.** The three-read budget was **exhausted by `10-04`** and a
  fourth would have exceeded a limit the user set. No `boty check`, no browser started, no fetch. Every
  measurement here is a sandboxed test run.
- **`make verify` NOT run** — it makes live requests to all six retailers. `make verify-offline` only.
- **No write to** `state.json`, `pacer-state.json` or `served/boty/status.json`. **No
  `systemctl restart boty`.**
- **`.planning/STATE.md` and `.planning/ROADMAP.md` unedited.** No `gsd-tools` state or phase WRITE
  subcommand invoked.
- **Never `--no-verify`.** Both commits went through the tracked pre-commit hook.
- **`WALMART_STORE_ID` never read, derived, inferred or printed**, and never described as unset.
- **No production code changed.** `git diff` against `boty/` is empty; the working tree was never
  perturbed, so the stale-`.pyc` trap was never approached — every perturbation lived and died inside
  a mutation sandbox.

### Standing invariants, re-measured

| invariant | measured |
|---|---|
| `Pacer.current_interval` body digest | `6da39ac5…449108` — **unchanged**, re-derived through 09-DECISIONS' recorded recipe (7994 chars / 8018 bytes) |
| `boty/` touched at all | **no** — `git diff HEAD -- boty/` empty |
| both `cli.watch_loop` clock terms | present and untouched (`cycle_started`, `cycle_duration`, `time.monotonic()`) |
| `MAX_BACKOFF_SECONDS` | `6 * 60 * 60` = 21600 |
| `COOLOFF_SECONDS` | `3 * 24 * 60 * 60` = 259200 |
| `STATE_VERSION` | 2 |
| `grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py` | **2** |
| `grep -c "INTENTIONAL GAP" scripts/mutation_check.py` | **10** — M21–M24 unfilled |
| highest registered ident / next free | **M44** / **M45** |

---

## Known Stubs

**None.** No placeholder, no hardcoded empty value flowing to a UI, no TODO or FIXME added. The one
thing deliberately left unbuilt — an `M45` on the resolution predicate — is recorded as a measured
open hole in the file itself and in `CLAUDE.md`, not as a stub.

## Deferred Issues

- **`M45` on the producer.** Three of its four killers are reached by no ident. Deferred because
  criterion 5 asks for one ident and the arm was the more informative; the measurement is in the file
  so the next agent need not retake it.
- **The Best Buy transport remedy** (`10-04`) — follow the announced redirect or read the resolution
  off the `NEXT_REDIRECT` payload. Unshipped: the reads that would confirm it are spent.

## Threat Flags

**None.** This plan added no production code, no network surface, no endpoint, no auth path and no
schema change at a trust boundary. Of its own register: **T-10-14** (a rounded-up verdict table) is
mitigated — every row cites a file and a test name, both MET IN PART rows name their missing half in
the same sentence, and criterion 4's row names all six condemned controls with their clauses.
**T-10-15** (the sandbox) held: nothing was added to `SANDBOX_CONTENTS`. **T-10-16** (ungated counts)
is mitigated: they moved in the same commit as M44, with the gap count taken by command.

---

## Commits

| Commit | What |
|---|---|
| `e01b482` | `test(10-05)`: M44 registered, observed caught, honestly priced — **and `CLAUDE.md`'s counts advanced in the same commit** |
| *(this file)* | `docs(10-05)`: the verdict table, and what the phase does not claim |

---

## What this phase does NOT claim

- **Not that anything is on the wire.** `boty` is an editable install, so the running daemon is still
  on pre-phase code and everything here reaches production at the next `sudo systemctl restart boty` —
  **Dan's call, deferred, and now carrying Phases 8, 9 and 10 together.** On the day it happens: the
  dead-control health state becomes reachable in production, a dead control starts naming
  `config/products.yaml` instead of blaming the extractor, and — because no control was swapped — the
  health gate goes on vouching for the same Best Buy page it vouches for today, including its false
  dead. **Not run, and not run as a side effect of anything here.**
- **Not that a reading is a distribution.** `10-04` measured three navigations at three moments. Read
  3 is one reading; the false dead was reproduced twice, which is two.
- **Not that the false dead is fixed.** It is measured, named, and left in place with its remedy
  written down and unconfirmed.
- **Not that the controls this phase named are repaired.** All six fail at least one clause and every
  failure is still named and unrepaired: GameStop's console, Best Buy's game SKU, Nintendo's
  generation-bound cable, and `D4` at all six.
- **Not that the rung-3 legibility gap is closed.** Target's `D5` is still NOT SATISFIED — a delisted
  Target control is indistinguishable from a reskin because `boty/browser.py` surfaces no main-frame
  status — and **inventing a status to make the cell pass is still refused.**
- **Not that M44 covers the resolution predicate.** It does not; the producer is a measured open hole
  with three killers no ident reaches.
- **Not that the mutation registry measures production.** It measures the suite. `40/40 caught` says
  every registered break is noticed by a test, not that the monitor is correct — `10-04` is the
  standing proof that a suite can be green about a mechanism the wire disagrees with.

---

## Self-Check: PASSED

Every file and every commit claimed above was verified to exist, and the one claimed **not** to exist
was verified absent.

| checked | result |
|---|---|
| `scripts/mutation_check.py`, `CLAUDE.md`, `10-05-SUMMARY.md` | all three **FOUND** |
| commit `e01b482` | **FOUND** in `git log --all` |
| commit `d1e1528` (amended away) | **CONFIRMED unreachable**, as this summary states |
| `M44` importable from the registry, ident count | `len(MUTATIONS)` = **40**, last ident `M44` |
| `scripts/identity_check.py --all` | **PASS — 273 file(s)** |
