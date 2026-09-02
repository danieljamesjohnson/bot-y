---
phase: 10
plan: 02
subsystem: detector-health
tags: [REQ-24, dead-control, is_unresolved, assess_health, criterion-2, mixed-group]
status: complete
requires:
  - "10-01 — Result.unresolved, Health.dead_control, DEAD_CONTROL_ACTION and the dead arm"
  - "10-DECISIONS.md § Collision 3 (the second producer) and § Collision 6 (the mixed group)"
provides:
  - "fetch.UNRESOLVED_STATUSES + fetch.is_unresolved — the status-level producer, the exact mirror of is_refusal, disjoint by assertion"
  - "the signal wired at all FIVE adapter arms that already ask the refusal question"
  - "the rung-3 gap named IN THE CODE at three sites, with the invent-a-status remedy refused in writing"
  - "assess_health's mixed arm — a group with more than one cause names every one and claims no single one"
  - "criterion 2's two halves, asserted in separate tests, each observed dying against a recorded perturbation"
affects:
  - "10-03 — Target's D5 column inherits the rung-3 gap exactly as named here"
  - "10-05 — M44's kill set now has a sixth assess_health arm to measure against"
tech-stack:
  added: []
  patterns:
    - "a predicate whose boundary is argued at its constant, and whose disjointness from its mirror is ASSERTED rather than commented"
    - "a health reason composed from the causes present, in the same order as the arms, so enumeration and precedence cannot drift"
    - "a superseded planning claim corrected BESIDE itself in the code that supersedes it"
key-files:
  created: []
  modified:
    - boty/fetch.py
    - boty/retailers.py
    - boty/monitor.py
    - tests/test_fetch.py
    - tests/test_retailers.py
    - tests/test_monitor.py
    - tests/test_pacing.py
    - tests/test_alert_text.py
decisions:
  - "404 and 410 in; 401/403/429 are the mirror's; 5xx and transport errors establish nothing"
  - "The mixed arm fires only when a refusal is present and is not the whole story — the narrowest form of Collision 6's rule"
  - "Health.refused keeps `all` and Health.dead_control keeps `any`; no flag moved, only the sentence"
  - "A mixed group still carries DEAD_CONTROL_ACTION: a remedy does not stop being one beside a refusal"
  - "The rung-3 gap is named at three code sites and closed nowhere; inventing a status in browser.py stays refused"
metrics:
  duration: "~2h"
  completed: 2026-09-02
actuals:
  tokens: 13169
  tasks: 3
  commits: 3
---

# Phase 10 Plan 02: The Second Producer, and Criterion 2 as a Conjunction — Summary

A control at a URL that no longer exists is now reported as a **dead control** at the five
URL-addressed retailers, instead of the probably-broken detector it was reported as. And a group of
controls that failed for **more than one reason** now names every cause it established and claims no
single one — so a real refusal can no longer be silenced by a dead control beside it.

**No live retailer request of any kind was made.** The wire is `10-04`'s.

---

## What shipped

| Artifact | What it does |
|---|---|
| `fetch.UNRESOLVED_STATUSES` | `{404, 410}`, declared beside `REFUSAL_STATUSES`, with the boundary argued at the constant |
| `fetch.is_unresolved` | the exact mirror of `is_refusal` — same shape, same argument type, never true at the same time |
| five wired arms in `boty/retailers.py` | `check_html`, `check_amazon`, `check_bestbuy_browser`, `check_target_browser`, `check_bestbuy_api` |
| `assess_health`'s mixed arm | the sixth arm: enumerates every established cause, in the arms' own order |
| `tests/test_monitor.py` | criterion 2's two halves, apart, plus the general form over all three shapes of mixed group |
| `tests/test_pacing.py` | the mixed-group test that lives in the pacer's file, renamed and its sentence moved |
| `tests/test_alert_text.py` | both partitions and the coverage gate extended to six arms |

---

## CRITERION 2, AND HOW THE TWO HALVES ARE ASSERTED APART

They are two tests because they fail for different reasons, and a single test covering both would
name the wrong one when it goes red.

**Half one — `test_criterion_2_half_one_a_dead_control_never_says_the_retailer_refused_us`.** One
dead control, alone, which is the shape the shipped configuration actually has. It asserts
`refused is False` and that the word `refus` appears nowhere in the reason. It holds **by
construction** today, which is exactly why it is asserted: "it cannot happen" is the claim that stops
being true after a refactor nobody re-checked.

**Half two — `test_criterion_2_half_two_a_dead_control_does_not_silence_a_refusal`.** One dead
control and one refused control in one group. It asserts the **facts first** — `refused is False`
(the `all` meaning is intact), `dead_control is True`, two `failing_controls` — and only then the
prose: `refus` present, `config/products.yaml` present, `"was not refused"` absent.

**And the general form —
`test_no_group_containing_a_refusal_is_ever_told_nothing_was_refused`**, parametrised over all three
shapes a mixed group can take (refusal + dead control, refusal + unestablished breakage, refusal +
store gap). Collision 6's rule is not about one pair; it is that a group **containing** a refusal is
never told nothing was refused.

---

## WHAT THE PLAN GOT WRONG, MEASURED RATHER THAN ASSUMED

**Collision 6 and this plan's objective both say the mixed group `{dead, refused}` "satisfies neither
`all`, falls through to the breakage arm, and is described with a sentence asserting that nothing was
refused." That was true when Collision 6 was written and it stopped being true when `10-01` shipped
the dead arm, four hours later.**

Measured on 2026-09-02 against `HEAD` before any of this plan's code moved:

```
group {one dead control, one refused control}, gamestop
  refused flag  : False     (all — correct)
  dead_control  : True      (any — so the DEAD arm fires, not the breakage arm)
  reason        : a control's target no longer resolves to a product — the page was read and
                  named no product matching what this watch asks for, which is a fact about
                  config/products.yaml rather than about the retailer or the extractor…
```

So the sentence that group receives does **not** contain "was not refused". It contains something
else that is just as wrong: it attributes the **whole group** to our config file and never mentions
that one of its controls was refused. The defect Collision 6 names is real; the mechanism it names is
one arm out of date.

The literal "falls to the breakage arm and says nothing was refused" description **is** still true of
the other mixed shape, `{refused, unestablished breakage}` — measured the same way:

```
group {one refused control, one plain breakage}, gamestop
  reason : a control product did not read IN_STOCK and was not refused, so readings from this
           retailer are unverified…
```

That is the group `tests/test_pacing.py` has pinned since 2026-08-04.

**Recorded beside, not edited away.** The correction is written into `assess_health`'s own comment at
the arm that supersedes it, in the dated form, rather than back-edited into `10-DECISIONS.md` — the
convention in `docs/retailer-evidence.md` § 6. Collision 6's *decision* is implemented unchanged; only
its description of today's code needed a note.

**Second, smaller correction:** the plan asks for half one to be observed dying against a **quantifier**
perturbation (`all` → `any` on the refusal arm). It does not die that way, and it cannot: a group of
one dead control contains no refusal for `any` to find. It dies against a different perturbation —
the refusal arm rewritten to `all(c.refused or c.unresolved …)`, which is the refactor a reader would
actually write. Both were run and both counts are below.

---

## THE DEFECT THIS FIXES AT FIVE RETAILERS, QUOTED FROM TODAY'S CODE

Before the wiring, a 404 at a URL-addressed control reached `assess_health`'s breakage arm:

```
Result.detail : fetch failed: HTTP 404
Health.reason : a control product did not read IN_STOCK and was not refused, so readings from this
                retailer are unverified and a real restock could be missed silently; the cause is
                not established
Health.action : ''
```

After: `dead_control is True`, the config-file sentence, and `DEAD_CONTROL_ACTION`.

---

## EVERY GATE'S RED, WITH ITS ACTUAL COUNT

The pycache was cleared between **every** perturbation and its revert
(`find . -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +; rm -rf .pytest_cache`).

### Task 1 — the predicate

| # | state of the code | result |
|---|---|---|
| T1-a | no constant, no function | **1 error, 0 tests run** — `AttributeError: module 'boty.fetch' has no attribute 'UNRESOLVED_STATUSES'` at collection. A weak red, so two stronger ones were taken |
| T1-b | constant present, `is_unresolved` stubbed to `return False` | **2 failed / 38 passed** — both 404/410 cases |
| T1-c | predicate widened to `exc.status is not None` | **7 failed / 33 passed** — 401/403/429, 500/502/503, and the two-predicate disjointness test |

Both boundaries bind. T1-c is the one that matters: a predicate that answered "yes" to every status
would have satisfied T1-b perfectly.

### Task 2 — the wiring

| # | state | result |
|---|---|---|
| T2-a | the health-arm tests, before any wiring | **2 failed / 62 passed** (`check_html`, `check_amazon`) |
| T2-b | the five adapter-arm tests, before any wiring | **10 failed / 150 passed** (5 arms × {404, 410}) |

**Existing tests reddened by the wiring: NONE.** The full suite ran **1015 passed** immediately after
it. The plan asked for every one to be named; the honest answer is that there were none, and it is
recorded as a measurement rather than as an absence of effort.

### Task 3 — criterion 2

| # | perturbation | result | what died |
|---|---|---|---|
| T3-a | the two halves + the general form, before the arm existed | **4 failed / 65 passed** | half two, and all three shapes of the general form. Half one passed — it holds by construction |
| P-M1 | refusal arm absorbs deadness: `all(c.refused or c.unresolved …)` | **12 failed / 182 passed** | **half one**, plus the tracer, both 404 health tests, state one, the three-reasons test, the precedence test, half two, and all three alert-text partitions |
| P-M2 | refusal arm's quantifier `all` → `any` | **9 failed / 185 passed** | half two, all three general-form shapes, the store-gap mixed test, all three partitions, and the pacing test. **Half one SURVIVED** — the measured finding above |
| P-M3 | the mixed arm's reason set equal to the dead arm's sentence | **7 failed / 187 passed** | half two, the general form, the pacing test — **and `test_the_partitions_cover_every_arm_this_module_can_produce`**, which is the one perturbation that proves that gate can still bite |
| P-M4 | the mixed arm never fires | **7 failed / 187 passed** | the same set as P-M3 |
| P-M5 | the mixed reason stops naming the refusal | **6 failed / 188 passed** | half two, the general form, the store-gap mixed test, the pacing test. The coverage gate does **not** fire here, correctly — the arm still produces a distinct sentence |

**No gate failed to go red.** There is no "could not be made to fail" finding among T1-a … P-M5.

---

## THREE GATES WERE FALSE WITHOUT GOING RED — AGAIN, AND ONE OF THEM WAS BUILT FOR THIS

This is the second occurrence in this phase and the more interesting one, because `10-01` added a
gate specifically to catch it and that gate did not catch it either.

**Measured:** with the sixth arm implemented and every new test passing, the full suite ran **1020
passed** while all three of these were false:

| gate | what it claimed | why it stayed green |
|---|---|---|
| `tests/test_pacing.py::test_one_non_refusal_among_refusals_is_treated_as_breakage` | that a `{refusal, breakage}` group "is treated as breakage" | it greps for `IN_STOCK` and `CAUSE_UNKNOWN`, and the **composed** mixed sentence happens to contain both — one of that group's two causes genuinely is unestablished, so the constant is honestly there |
| `test_exactly_the_two_unknown_causes_say_so` | "across all FIVE arms" | enumerates arms by name through `_every_arm`, which never constructed the sixth |
| `test_the_partitions_cover_every_arm_this_module_can_produce` | that the arms `assess_health` can reach equal the arms `_every_arm` builds | it counts `_every_arm`'s own dict — and `_every_arm` is precisely the thing that falls behind `monitor.py` |

`test_only_the_arms_with_a_measured_remedy_name_something_a_person_can_do` was false in the same way
(its "over the same five arms").

**The check that found all four was reading the new arm, not running them.** Green was the symptom
again.

**What was done:**

- the pacing test **renamed** to
  `test_one_non_refusal_among_refusals_is_not_swallowed_and_both_causes_are_named`, its withdrawn
  name and assertion quoted in full in its docstring, its `all`/`any` point kept and asserted, and
  **two new assertions added** — that the refusal in the group is named and that the group is never
  told nothing was refused. That is the assertion the withdrawn version could not make;
- `_every_arm()` extended to a sixth arm, and both partitions to six rows, with the dated form on
  both docstrings. `test_exactly_the_two_unknown_causes_say_so` **keeps its name**: there are six arms
  now and still exactly two carry `CAUSE_UNKNOWN`, so only the denominator moved;
- the coverage gate's **limit is recorded at the gate**: it did not fire for the very next arm, it
  said in its own docstring that it could not see `assess_health`'s branches, and P-M3 shows what it
  *does* still catch (two arms colliding on one sentence).

**The honest fix is named and deliberately not taken here.** A gate that reads `assess_health`'s
`reason` assignments directly — an `ast` walk, in the shape `test_alert_text.py` already uses on this
same module — would bind where this one cannot. It trades a red on refactors that change nothing a
person receives, which is a decision that belongs in a plan that argues it, not in a deviation at the
end of one. Written into the gate's docstring so the next reader meets it there.

---

## THE MIXED ARM, AS SHIPPED

Fires only when **a refusal is present and is not the whole story** — the narrowest form of
Collision 6's rule. A group of a dead control and an unestablished breakage keeps the dead arm,
because "at least one target does not resolve" stays true of it and `any` already says so.

Its reason is **built from the controls**, in the same order as the arms above (refused → unresolved
→ store gap → not established), so the enumeration and the precedence cannot drift apart. A control
is counted under the first class it satisfies, which is how the arms would have read it alone.

**No flag moved.** `Health.refused` keeps `all` for its three consumers (`status.write`,
`cli.watch_cycle`'s paging filter, `notify`); `Health.dead_control` keeps the `any` `10-01` gave it,
so a mixed group carries the fact **and** still carries `DEAD_CONTROL_ACTION` — a remedy does not stop
being one because a sibling control was refused. `failing_controls` still interpolates every failing
control's own `detail`.

**LATENT, NOT LIVE, AND THIS SUMMARY DOES NOT ROUND IT UP.** `assess_health` groups by retailer and
every retailer in `config/products.yaml` has **exactly one** control, so a mixed group is **not
reachable in the shipped configuration**. It is a defect in the code. It becomes reachable the moment
any retailer gains a second control, which `10-03`'s reserve-candidate clause makes more likely rather
than less. **No wrong alert is being produced today by this**, and nobody has received one.

---

## THE RUNG-3 GAP — NAMED IN THREE PLACES, CLOSED IN NONE

`boty/browser.py` returns `Page(status=200)` unconditionally, and its own comment argues why:
*"the simple API does not surface the main frame's response status, so there is no real status to
report and inventing one would be worse than saying so."*

So at rung 3 there is no status to read:

| retailer | rung | addressed by | covered by |
|---|---|---|---|
| gamestop, walmart, nintendo | 1 | URL | `is_unresolved` (this plan) |
| amazon | 1, dom | URL | `is_unresolved` (this plan) |
| bestbuy | 3 / API | SKU | the resolution producer (`10-01`), and `is_unresolved` on the API arm |
| **target** | **3, dom** | **URL** | **NEITHER** |

A delisted Target control renders Target's own not-found page, reads no offers, and is
indistinguishable from a reskin at this layer. Written where a reader meets it — at
`fetch.UNRESOLVED_STATUSES`, at `check_bestbuy_browser`'s arm in full, and at
`check_target_browser`'s arm — and in the test that covers all five arms, which states that the two
browser arms are wired for an arm's sake and cannot fire today.

**The remedy is refused in writing at the site:** no status is to be invented in `boty/browser.py`.
The honest route for a future phase is the response object. `10-03` carries the same gap into the
durability rule's own column so the two records agree.

---

## Deviations from Plan

### 1. [Rule 2 — a gate that would have shipped false] `tests/test_alert_text.py` was modified

- **Found during:** Task 3, after the mixed arm existed.
- **The plan says explicitly:** *"its two partitions were already extended to five arms by `10-01`;
  this plan must not re-open them"*, and the file is not in `files_modified`.
- **Why it was modified anyway:** the mixed arm is a **sixth** arm producing a sixth reachable reason.
  Leaving the file alone would have shipped three assertions that are false — the exact failure
  `10-01` spent a task repairing — and `test_the_partitions_cover_every_arm_this_module_can_produce`
  states the repair procedure in its own docstring: *"IF THIS GOES RED, DO NOT DELETE AN ARM FROM THE
  COUNT. Add the new arm to `_every_arm` and to both partitions, and correct both docstrings in the
  dated form."* It did not go red, which makes following that procedure more necessary rather than
  less.
- **What was NOT done:** `10-01`'s four→five corrections were not re-opened, rewritten or churned.
  One arm was added to one constructor, one row to each partition, and one dated paragraph to each of
  three docstrings.
- **Commit:** `b4e7b07`.

### 2. [Rule 1 — a claim in a planning document that stopped being true] Collision 6's mechanism

Recorded in full under *What the plan got wrong* above. The correction lives in `assess_health`'s
comment beside the arm, dated, with `10-DECISIONS.md` left as written.

### 3. [Rule 1 — an expectation that had to move] one pre-existing `test_monitor.py` test reddened

`test_a_refusal_beside_a_store_gap_falls_to_the_louder_arm` — **1 failed / 68 passed** when the mixed
arm landed. Its group is `{refused, store gap}`: **both** causes were established, so
`CAUSE_UNKNOWN in health.reason` had become a claim that discards two measurements. Renamed
`test_a_refusal_beside_a_store_gap_names_both_causes_and_claims_neither_alone`, withdrawn text quoted
in full, and the half that survives — `refused` stays `all`, the group is not the refusal arm's and
not the store arm's — kept and still asserted.

### 4. [process, and it cost real work] `git checkout` reverted an UNCOMMITTED implementation

- **What happened:** perturbation P-M1 was reverted with `git checkout boty/monitor.py` while Task 3's
  implementation was still uncommitted. That command does not distinguish the perturbation from the
  work; it restored `HEAD` and discarded the mixed arm entirely.
- **How it was caught:** the next perturbation's `str.replace` raised `AssertionError` on a missing
  anchor — and the test run in the same command still reported **7 failed**, which reads exactly like
  a perturbation that worked. `git status` showed `boty/monitor.py` unmodified, which is the tell.
- **Consequence for the record:** P-M2's first measurement was taken against a tree with **no mixed
  arm**, so it measured something else. It was **re-taken** against the correct tree after the
  implementation was restored. The number happened to come out identical (**9 failed / 185 passed**),
  and that coincidence is stated rather than used — the recorded figure is the re-taken one.
- **Fixed forward:** the remaining perturbations were reverted with `cp` from a copy taken before the
  first one, and the restore was verified with `diff` (byte-identical). A note was added to
  `CLAUDE.md`'s red-watch section, beside the stale-`.pyc` trap, because it is the same protocol and
  the same class of silent damage.

**Nothing else deviated.** No architectural change was needed; no Rule 4 checkpoint was reached.

---

## Prohibitions — held

- **No live retailer request of any kind.** No `boty check`, no browser started, no `fetch_rendered`
  against a real host. Every adapter exercise is a monkeypatched transport.
- **No write to** `state.json`, `pacer-state.json` or `served/boty/status.json`. No
  `systemctl restart boty`.
- **`.planning/STATE.md` and `.planning/ROADMAP.md` unedited.** No `gsd-tools` state or phase WRITE
  subcommand invoked.
- **Never `--no-verify`.** All commits went through the tracked pre-commit hook; identity check PASS
  on each.
- **`WALMART_STORE_ID` never printed, derived or inferred**, and never described as "deliberately
  unset": it is **set on disk since 2026-08-25 and not yet in effect** until the deferred restart.
- **`boty/pacing.py`, `boty/status.py`, `boty/browser.py`, `boty/models.py` and
  `served/boty/index.html` untouched** — `git diff --name-only b3e7795 HEAD` lists none of them.

### Standing invariants, re-measured

| invariant | measured |
|---|---|
| `Pacer.current_interval` body | **byte-unchanged by construction** — `boty/pacing.py` is not in the diff since the phase start. *The recorded digest was **not** recomputed: an ad-hoc span extraction here spans 7989 chars against the recipe's 7994, so it is a different recipe and its number is not comparable. Saying so beats publishing a mismatched hash.* |
| both `cli.watch_loop` clock terms | present — `time.monotonic()` at the cycle bracket, `time.time()` for the reading stamp; `boty/cli.py` untouched |
| `MAX_BACKOFF_SECONDS` | `6 * 60 * 60` = 21600 |
| `COOLOFF_SECONDS` | `3 * 24 * 60 * 60` = 259200 |
| `STATE_VERSION` | 2 |
| `grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py` | **2** |
| `grep -c "INTENTIONAL GAP" scripts/mutation_check.py` | **9** — M21–M24 unfilled |
| highest registered mutation ident | **M43**; next free is **M44** (`10-05`'s) — unchanged, none registered here |

---

## Final gate

```
make verify-offline
mutation check: 39/39 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

**1020 tests passed** · ruff clean · mypy clean (13 source files) · identity check PASS · mutation
39/39 caught, survivors 0.

---

## Known Stubs

**None.** No placeholder, no hardcoded empty value flowing to a UI, no TODO or FIXME added.

---

## Threat Flags

**None new.** This plan added no network endpoint, no auth path and no schema change at a trust
boundary. Of the plan's own register:

- **T-10-08** (a retailer-controlled status deciding a health state) — mitigated as planned: the
  boundary is 404/410 only, argued at the constant, disjoint from the refusal set **by assertion in
  two independent tests**, and the verdict names our config rather than making a claim about the
  retailer.
- **T-10-09** (the mixed-group reason as a false record) — mitigated: the group names every
  established cause, and the gate asserts the **flags** before the prose. Still rated for what it
  would do; it is latent.
- **T-10-10** (the rung-3 gap at Target) — **accepted and named**, in three code sites and in the
  table above. Not closed, not described as closed.

---

## Commits

| Commit | What |
|---|---|
| `526913e` | `feat(10-02)`: a deleted target is a resolution failure, not a broken detector |
| `6c1d1e0` | `feat(10-02)`: the second producer, wired at every arm that already asks about refusals |
| `b4e7b07` | `feat(10-02)`: a group with more than one cause names every one and claims no single one |

---

## What this plan does NOT claim

- **Not that Best Buy's control is dead.** Collision 10 stands untouched: the evidence is
  absent-then-stale. No test name, comment or commit message here says otherwise.
- **Not that a wrong alert is produced today by the mixed group.** One control per retailer; the
  defect is in the code and it is latent.
- **Not that every dead control is now detected.** Target is covered by neither producer, and the
  no-canonical-no-structure residual from `10-01` is still open. Both are named; neither is closed.
- **Not that criterion 2's second half was ever seen firing.** It is a property of the function,
  constructed in tests, and this document says so everywhere it is mentioned.

---

## Self-Check: PASSED

Every file and every commit hash claimed above was verified to exist, and every symbol claimed was
imported and inspected rather than asserted.

| checked | result |
|---|---|
| the eight modified files + `10-02-SUMMARY.md` | all **FOUND** |
| commits `526913e`, `6c1d1e0`, `b4e7b07` | all three **FOUND** in `git log --all` |
| `fetch.is_unresolved`, `fetch.UNRESOLVED_STATUSES` | both import; `{404, 410}` vs `{401, 403, 429}`, **disjoint** |
| the mixed arm in `assess_health` | present in `inspect.getsource` |
| `make verify-offline` | **PASS (OFFLINE)**, 39/39 mutations caught |
