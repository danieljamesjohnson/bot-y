---
phase: 10
plan: 01
subsystem: detector-health
tags: [REQ-24, dead-control, assess_health, predicate, mutation-M30, partitions]
status: complete
requires:
  - "docs/retailer-evidence.md — the offline record Collision 10 is proved from"
  - "tests/fixtures/bestbuy/{pikachu-control,unresolved-sku}.html — the two captures the predicate is measured against"
provides:
  - "Result.unresolved — the dead fact as a FIELD, set only from measured facts"
  - "Health.dead_control + DEAD_CONTROL_ACTION — the fifth arm, between refusal and store gap"
  - "parse.canonical_url — the third discriminator"
  - "10-DECISIONS.md — ten collisions settled before any production code moved"
  - "the no-canonical-no-structure RESIDUAL, pinned by a test, for 10-03's D5 PARTIAL"
  - "M30 re-anchored; both alert-text partitions extended to five arms"
affects:
  - "10-02 — inherits Collisions 3 and 6 (is_unresolved, the mixed group) as settled"
  - "10-03 — cites the residual pin for Best Buy's D5 column"
  - "10-05 — carries Collision 10's premise correction unconditionally"
tech-stack:
  added: []
  patterns:
    - "a diagnosis carried on a field, never substring-matched out of Result.detail (M2's lesson)"
    - "a predicate stated as a measured disjunction, with both rejected one-clause readings recorded"
    - "a residual NAMED rather than closed, and pinned by a test"
key-files:
  created:
    - .planning/phases/10-a-control-that-cannot-die/10-DECISIONS.md
  modified:
    - boty/models.py
    - boty/parse.py
    - boty/retailers.py
    - boty/monitor.py
    - scripts/mutation_check.py
    - tests/test_models.py
    - tests/test_parse.py
    - tests/test_retailers.py
    - tests/test_monitor.py
    - tests/test_alert_text.py
    - .planning/phases/09-out-of-lockstep/09-DECISIONS.md
decisions:
  - "The dead fact is a FIELD on Result, not a substring match on detail prose"
  - "The predicate is a disjunction: canonical PATH is the search endpoint, OR markup was present and parsed and carried no matching sku — never unparseable markup"
  - "The no-canonical-no-structure case is a named residual; it keeps today's verdict"
  - "Health.dead_control is `any`; Health.refused stays `all`"
  - "Arm precedence: refused -> dead -> store gap -> breakage"
  - "The dead arm carries an action and therefore pages, on STORE_PIN_ACTION's precedent"
  - "Nothing new is published to status.json"
  - "Collision 10: Best Buy's control has never been shown dead — absent-then-stale, rounded neither way"
metrics:
  duration: "~2h"
  completed: 2026-09-02
actuals:
  tokens: 26890
  tasks: 3
  commits: 3
---

# Phase 10 Plan 01: A Control That Cannot Die — Summary

A Best Buy control whose SKU no longer resolves is now reported as a **dead control** — a fact about
`config/products.yaml` — instead of the broken detector it was reported as for four phases. Driven
end to end from a captured page, with **no live read**, on a predicate measured against both
fixtures rather than assumed. And the phase's premise was corrected offline: the control has never
been shown dead.

---

## What shipped

| Artifact | What it does |
|---|---|
| `10-DECISIONS.md` | ten collisions settled in writing before any production code moved |
| `Result.unresolved` | the dead fact as a field, declared last, `False` meaning *not established as unresolved* |
| `parse.canonical_url` | the retailer's own `rel="canonical"`; `None` is the residual, not an error |
| `_verdict_from_html` | the settled disjunction, with the 2026-08-04 date and the measured table in place |
| `Health.dead_control`, `DEAD_CONTROL_ACTION` | the fifth arm, between refusal and store gap, carrying a remedy naming `config/products.yaml` |
| `scripts/mutation_check.py` | M30 re-anchored, re-point recorded |
| `tests/test_alert_text.py` | both four-arm partitions extended to five, docstrings corrected in the dated form, plus a coverage gate that CAN fail |

---

## THE PREDICATE, as shipped

> A SKU-addressed reading is **unresolved** when
> **(A)** the page's canonical link's **path** equals the search endpoint the adapter requested — the
> retailer saying no product resolved; **or**
> **(B)** structured markup was present and parsed (`blocks > 0` and `unparseable == 0`) and no
> Product on it carries the requested sku.
>
> **Never** when markup was present and could not be parsed.

**Re-measured by this executor on 2026-09-02, not carried over from the plan** (the plan asked for
exactly this, and the numbers came out identical):

| page, read for | bytes | blocks | unparseable | our sku in offers | canonical points at | `unresolved` |
|---|---|---|---|---|---|---|
| `unresolved-sku.html`, 6577129 | 921,732 | **0** | 0 | no | `/site/searchpage.jsp?id=pcat17071&st=6577129` | **True** (clause A) |
| `pikachu-control.html`, 6577129 | 1,138,265 | 3 | 0 | no | `/product/…/sku/6216393` | **True** (clause B) |
| `pikachu-control.html`, 6216393 | 1,138,265 | 3 | 0 | **yes** | `/product/…/sku/6216393` | **False** (IN_STOCK, $59.99) |
| three blocks present, zero parsed | — | 3 | **3** | no | a product path | **False** — the 2026-08-04 false dead |
| no canonical, no structure | — | 0 | 0 | no | nothing | **False** — the residual |

Comparison is on **path**, against the URL the adapter itself built, because the canonical carries a
category parameter the request does not — a whole-string comparison would have been false the day it
was written.

**The residual is named and pinned.** A page with neither a canonical nor parseable structure is not
distinguishable from a reskin, keeps today's verdict, and `10-03` carries it into Best Buy's D5
column as **PARTIAL**. Its cost is stated in the code and in the test: a page whose markup is broken
*and* whose product is genuinely gone reads as a detector failure. That is the wrong answer in the
right direction, because it claims less.

---

## THE END-TO-END TEST, WATCHED RED FIRST

**Today's defect, quoted from a run of today's production code** — not from the ROADMAP:

```
Result.detail : sku 6577129 did not resolve to a product page — no schema.org Product on it carries that sku
Health.reason : a control product did not read IN_STOCK and was not refused, so readings from this
                retailer are unverified and a real restock could be missed silently; the cause is not established
Health.action : ''
```

The `Result` already knew. The `Health` said the opposite kind of thing — a fact about the retailer,
asserted from a fact about our own config — and carried no action, so nobody was ever told the one
thing they could do.

**The red:** `ImportError: cannot import name 'DEAD_CONTROL_ACTION' from 'boty.monitor'` — collection
error, **1 error, 0 tests run**. A collection error is a weak red, so the run above was taken
separately to capture what today's code actually produced.

**After:**

```
Health.dead_control : True
Health.reason : a control's target no longer resolves to a product — the page was read and named no
                product matching what this watch asks for, which is a fact about config/products.yaml
                rather than about the retailer or the extractor. Each control below names its target
                and what the page said
Health.action : the target this control names no longer resolves to a product — pick a replacement
                and set it in config/products.yaml
```

**Exactly one existing test reddened:** `test_read_at_is_declared_last_with_a_default_of_none`
(**1 failed / 35 passed**) — a test whose subject is the declared-last convention, not `read_at`. It
is closed in the same task, renamed `test_the_newest_field_is_declared_last_with_a_default`, with its
docstring recording in the dated form that the convention outlived the field it was written about.

---

## EVERY GATE'S RED, WITH ITS ACTUAL COUNT

The pycache was cleared between **every** perturbation and its revert
(`find . -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +; rm -rf .pytest_cache`), because
a same-length same-second revert leaves the perturbed bytecode live and the natural response is to
distrust the new test.

| # | perturbation | result | which tests died |
|---|---|---|---|
| P1 | `canonical_url` never matches | **4 failed / 50 passed** | all four canonical tests |
| P2 | one-order regex (rel before href only) | **1 failed / 53 passed** | the attribute-order test |
| P3 | discriminator dropped (`blocks > 0` alone) | **1 failed / 180 passed** | `test_the_2026_08_04_false_dead_is_not_a_dead_control` |
| P4 | clause A removed | **2 failed / 179 passed** | the clause-A test, and the invariant test's non-vacuousness assertion |
| P5 | clause B removed | **2 failed / 179 passed** | the clause-B test and the tracer |
| P6 | dead arm never fires | **4 failed / 75 passed** | tracer, state one, the three-reasons test, the precedence test |
| P7 | precedence inverted (store gap ahead of dead) | **1 failed / 78 passed** | `test_a_dead_walmart_control_with_no_pin_is_dead_and_not_a_store_gap` |
| P8 | dead arm carries no action | **3 failed / 76 passed** | tracer, state one, the precedence test |
| P9 | dead arm loses its own sentence | **5 failed / 75 passed** | both partitions' coverage gate, the CAUSE_UNKNOWN partition, and three monitor tests |

**P4 is the residual measurement the plan asked for, and it came out the interesting way.** With the
canonical clause removed, `unresolved-sku.html` — which carries **zero** `ld+json` blocks — falls back
to the **ambiguous** case rather than to a dead control. The residual is a real boundary in the code,
not a sentence in a comment.

**No gate failed to go red.** There is no "could not be made to fail" finding among P1–P9.

---

## THE PARTITIONS: FALSE WITHOUT GOING RED, AND HOW IT WAS DETECTED

This is the finding the plan flagged as the worst outcome available under this repository's standard,
and it happened exactly as predicted.

**They could not be made to fail by running them, and that is measured rather than asserted.** The
four-arm versions were taken from `HEAD` (`git show HEAD:tests/test_alert_text.py`) and run against
the five-arm code that had already falsified both docstrings:

```
2 passed, 19 deselected in 0.03s
```

**Two passed. Zero failed.** `test_exactly_the_two_unknown_causes_say_so` still said *"across all
four arms"* about five, and `test_exactly_one_arm_names_something_a_person_can_do` still said *"the
answer has to stay ONE"* about two. Both enumerated their arms by name and neither constructed the
fifth. The full suite was green at **953 passed** with both of them in it.

**The check that found it was mechanical**, as the plan required: the number of arms each partition
constructs must equal the number of arms `assess_health` can produce. Green was the symptom.

**What was done about it:**

- both extended to five arms, through **one shared `_every_arm()` constructor** rather than two
  inline lists — two lists that must agree with a third in `monitor.py` is two chances to fall behind
  it;
- both docstrings corrected in the dated form (withdrawn sentence quoted, what overruled it, what
  survives);
- `test_exactly_one_arm_names_something_a_person_can_do` **renamed** to
  `test_only_the_arms_with_a_measured_remedy_name_something_a_person_can_do`, because its old name
  asserted a number that moved. What survives there is the **rule** — a push costs somebody writing
  down what a person can DO, and a new arm is silent by default — not the count. The count is
  deliberately **not** asserted as a constant: pinning it to two would make the next honest arm a test
  failure, which is a blocklist wearing an assertion's clothes, and `Health.action`'s own docstring
  rejects that shape;
- `test_exactly_the_two_unknown_causes_say_so` **kept its name**, because it stayed true — there are
  five arms now and still exactly two carry `CAUSE_UNKNOWN`. Only the denominator moved;
- a new **`test_the_partitions_cover_every_arm_this_module_can_produce`** asserts the domain rather
  than the mapping. It is the gate that *can* fail (P9 kills it), and its docstring states the repair
  procedure so the next person meets it at the moment the message arrives.

---

## M30 RE-ANCHORED IN THIS WAVE

Collision 7 rewrote `action=STORE_PIN_ACTION if store_gap else "",` — M30's exact search literal.
`apply_mutation` raises on a missing anchor and the harness runs inside `make verify-offline`, so
leaving it would have broken criterion 5's own gate from wave 1 to wave 5 and read as this phase's
regression. **`make verify-offline` did fail with a missing anchor between Task 2 and Task 3. That
was expected and it is resolved.**

- **anchored on:** `                    action=STORE_PIN_ACTION if store_gap else "",`
- **anchors on now:** the `else STORE_PIN_ACTION / if store_gap / else ""` branch of the chained
  conditional it became — verified **1 occurrence** in `boty/monitor.py`, and the mutated source
  verified to `ast.parse` cleanly
- **nothing about what M30 tests changed.** Its `replace` leaves the dead-control arm's action intact,
  so it still destroys exactly one behaviour — the store-pin arm stops naming its remedy — rather than
  silently becoming a mutation about "actions in general"
- **its citation was re-checked rather than assumed.** M30's comment block names
  `test_exactly_one_arm_names_something_a_person_can_do`; that test was renamed here, so the citation
  was updated to the new name with the old one kept beside it for anyone searching the history

The re-point is recorded in the file as the **eighth** anchor in this registry to drift (after M2,
M4, M25, M26, M33 twice and M36) and the **fourth** to drift for a code-shape reason.

**Harness result: `mutation check: 39/39 mutations caught`, exit 0.** M30 caught by **10 tests**,
the first of them the renamed partition.

---

## Collision 10 — the premise correction, proved offline

**Every citation was re-opened and checked individually rather than copied on trust. All eleven check
out**, and two further measurements were taken because "the only" and "never the control" are the
assertions a single missed line would falsify.

| claim | citation | verified |
|---|---|---|
| the control read `in_stock … $59.99 … ld+json: InStock from Best Buy` in four `make verify` transcripts | L1642, L1884, L2286, L2413 | ✅ all four |
| its search redirect transcribed in full — 1,109,548 B, correct title, one first-party offer | L860 | ✅ |
| the **only** "did not resolve" for that SKU is the documented 2026-08-04 **false** dead | L960 | ✅ — and `grep -n "did not resolve"` over the whole log returns **exactly one line** |
| the two most recent attempts are `no Chrome/Chromium binary found` — a **host** failure | L3482, L4397 | ✅ both |
| SKU 6577129 was a **product** watch, *"unconfirmed and probably wrong"*, never the control | L822, L868, L901 | ✅ all three |

**Extra checks this executor ran:**

- `grep -n "6216393" docs/retailer-evidence.md` → **7 lines**; six describe successful resolution or
  the page's own markup, one is the false dead. No second unresolved reading exists.
- `grep -n "6577129" config/products.yaml` → **one line, L201, inside a comment** saying the SKU
  resolves to nothing. It is not a watch. Best Buy's only `control: true` entry is `target: "6216393"`
  at L208–211. So "already removed from config" is measured, not recalled.

**The conclusion, with both roundings refused in writing:**

> **Best Buy's control has never been shown dead. It was last shown ALIVE in early August, and it has
> been unmeasured for roughly four weeks. The evidence is ABSENT-THEN-STALE, not contrary.**

Not *"the control is dead"* — the one unresolved reading of `6216393` is the one this repository
documented as **false**, and the SKU that does resolve to nothing was never the control. Reading
REQ-24 as "the control died" is a conflation of two different SKUs. Not *"the control is fine"* — a
four-week-old reading is a reading about early August, and the two most recent attempts established
nothing about Best Buy at all.

**It survives read 1 whatever read 1 returns**, because it was established without one: a refusal
leaves it standing, a successful read confirms it, and an unresolved result dates the death inside a
window this record bounds.

---

## `COVERAGE.md` — asserted, not created

Quoted in full, and it **does** declare external calls, unlike Phases 8 and 9:

> External API integration: this phase makes up to THREE live requests, to Best Buy only,
> browser-rung and spaced, under the hard cap Dan authorised in QUESTIONS.md § 0g — every other
> criterion is closed offline, and an unspent read is recorded as unspent.

---

## Deviations from Plan

### 1. [Rule 2 — missing critical gate] A coverage gate the plan did not ask for

- **Found during:** Task 3, extending the two partitions.
- **Issue:** extending both partitions to five arms fixes today's falsehood and does nothing about
  the *shape* that produced it. The next arm added falsifies both docstrings again, silently, exactly
  as this one did.
- **Fix:** one shared `_every_arm()` constructor, plus
  `test_the_partitions_cover_every_arm_this_module_can_produce`, which asserts the domain (five arms,
  five distinct reasons, all unhealthy) rather than the mapping. It is imperfect — it counts distinct
  reasons, so two arms sharing a sentence would hide from it — and that limit is stated in its own
  docstring. It **can** fail, which is what the two partitions could not do.
- **Verified red:** P9 kills it.

### 2. [Rule 1 — a wrong number in a record] `09-DECISIONS.md`'s digest span

- **Found during:** the standing-invariant check.
- **Issue:** the digest recipe records the span as *"7994 bytes"*. It is **7994 characters and 8018
  bytes** — the block contains em dashes and an `é`. The digest itself is unaffected: `.encode()` is
  applied before hashing in the recorded recipe, and
  `6da39ac5d77ecd98cae80651c3b4d539253e88a1704fb4b1e814e6bf93449108` re-verified unchanged here.
- **Fix:** a dated note recorded **beside** the sentence, never over it, per
  `docs/retailer-evidence.md` § 6.
- **Why it mattered enough to fix:** the byte count is the cross-check a future verifier reaches for
  when the hash does *not* match. A reader who measured `len(...encode())`, got 8018 and concluded the
  span had drifted would go hunting a change to `boty/pacing.py` that never happened.
- **File:** `.planning/phases/09-out-of-lockstep/09-DECISIONS.md` — outside this plan's
  `files_modified`, and named here for that reason.

### 3. [documentation-only] The 2026-08-04 episode cannot be rebuilt byte-for-byte

- **Found during:** Task 3, writing the false-dead gate.
- **Issue:** `parse._repair_ldjson` now **rescues** the exact 08-04 escaping (`\'` inside strings, a
  literal `\n` outside them). Rebuilding the episode verbatim produces a **repaired** read, which
  tests the repair rather than the discriminator.
- **What was done:** the fixture uses markup of the same class — present, and unparseable even after
  repair — and the test's own comment states the substitution and why, rather than glossing it. This
  is recorded as a deviation because the test is named for an episode it does not reproduce byte for
  byte.

**Nothing else deviated.** No architectural change was needed; no Rule 4 checkpoint was reached.

---

## Prohibitions — held

- **No live retailer request of any kind.** No `boty check`, no `fetch_rendered` against a real host,
  no browser started. The conftest network guard was in force for every test run.
- **No write to** `state.json`, `pacer-state.json` or `served/boty/status.json`.
- **`.planning/STATE.md` and `.planning/ROADMAP.md` unedited.** No `gsd-tools` state or phase WRITE
  subcommand invoked.
- **Never `--no-verify`.** All three commits went through the tracked pre-commit hook.
- **`WALMART_STORE_ID` never printed, derived or inferred.** It is described throughout as *set on
  disk and not yet in effect* — never "deliberately unset", which has been stale since 2026-08-25.

### Standing invariants, re-measured

| invariant | measured |
|---|---|
| `Pacer.current_interval` body digest | `6da39ac5…449108` — **unchanged** |
| `boty/pacing.py` touched | **no** (`git diff` empty) |
| `boty/status.py`, `served/boty/index.html` touched | **no** |
| `_is_store_gap` body | **unedited** — only its call site's guard and a comment reference moved |
| `MAX_BACKOFF_SECONDS` / `COOLOFF_SECONDS` / `STATE_VERSION` | 21600 / 259200 / 2 |
| `grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py` | **2** |
| `grep -c "INTENTIONAL GAP" scripts/mutation_check.py` | **9** — M21–M24 unfilled |
| next free mutation ident | **M44** (unchanged; `10-05`'s) |

---

## Final gate

```
make verify-offline
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
exit 0
```

967 tests passed · ruff clean · mypy clean (18 source files) · identity check PASS (267 files) ·
mutation 39/39 caught.

---

## Known Stubs

**None.** No placeholder, no hardcoded empty value flowing to a UI, no TODO or FIXME added.

---

## Threat Flags

**None.** This plan added no network endpoint, no auth path, no file-access pattern and no schema
change at a trust boundary. `T-10-01`'s mitigation is implemented and gated (the false-dead test,
P3); `T-10-06`'s is implemented (one action, one constant, fired at most once per episode through the
existing `warned` memory, no new sender); `T-10-07`'s is this document's red-count table.

---

## Commits

| Commit | What |
|---|---|
| `0b4003b` | `docs(10-01)`: ten collisions settled before any production code moves |
| `cec967e` | `feat(10-01)`: a captured dead SKU becomes a dead control, end to end |
| `91cf3fb` | `test(10-01)`: gate the tracer, pin the residual, and repair the two gates that went false without going red |

---

## What this plan does NOT claim

- **Not that the control is dead.** See Collision 10. No test name, comment or commit message here
  says so.
- **Not that a wrong alert is produced today by the mixed group.** Every retailer has exactly one
  control, so that defect is latent. `10-02` owns it.
- **Not that the predicate covers every dead control.** It covers SKU-addressed Best Buy readings.
  The rung-3 status gap (Target) and the no-canonical-no-structure residual are both named, both
  open, and neither is described as closed.
- **Not that criterion 3 is met.** That needs the wire and it is `10-04`'s. This plan closes
  Definition of Done item 3's **second half** only — the dead-control state reachable in a test
  without a live read.

---

## Self-Check: PASSED

Every file and every commit hash claimed above was verified to exist, and every symbol claimed was
imported and inspected rather than asserted.

| checked | result |
|---|---|
| `10-DECISIONS.md` exists, ten `## Collision` sections | **FOUND**, 10 |
| `10-01-SUMMARY.md` exists | **FOUND** |
| commits `0b4003b`, `cec967e`, `91cf3fb` | all three **FOUND** in `git log --all` |
| `Result` last field | `unresolved` |
| `Health` last field | `dead_control` |
| `monitor.DEAD_CONTROL_ACTION`, `parse.canonical_url` | both import |
