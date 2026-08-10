---
phase: 05-a-reading-means-something
plan: 02
subsystem: detector
tags: [walmart, store-identity, unknown-not-out-of-stock, alert-text, mutation-testing, ast-gate]

# Dependency graph
requires:
  - phase: 05-a-reading-means-something
    plan: 01
    provides: "Watch.store_id, Result.store on every check_html return path, parse.nextdata_store, and the identity rule that keeps a store number out of a tracked config key"
  - phase: 03.1-hard-two-and-honest-records
    provides: "Result.refused / fetch.is_refusal — the refusal-vs-breakage split assess_health's arms are built on"
provides:
  - "models.STORE_SCOPED — the one definition of which retailers a missing store pin is a gap for"
  - "two guards in retailers._verdict_from_html: an unpinned or unexpected store is Availability.UNKNOWN before any stock verdict can form"
  - "monitor.CAUSE_UNKNOWN — one constant, one spelling, for the arms whose cause is not established"
  - "a fourth assess_health arm for the store gap, detected from facts and not from detail prose"
  - "three rewritten Health.reason strings and a notification title that names no cause"
  - "mutations M9 and M10 — one per store guard, anchored on the verdict, never on prose"
  - "tests/test_alert_text.py — an ast gate on an absence, plus the CAUSE_UNKNOWN partition"
affects: [05-03, 05-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "a claim about ABSENCE is gated with ast.parse, docstrings excluded by node identity, never with grep — because this repo's own comments quote the withdrawn sentences"
    - "a negative gate is paired with a positive partition, so it cannot be satisfied by deleting every explanation"
    - "a guard's comment sits ABOVE its `if`, so the condition line and the verdict stay adjacent and a mutation can anchor on them without touching prose"
    - "one predicate in models.py read by both the verdict and the health message, so a guard cannot fire where the alert stays quiet"

key-files:
  created:
    - tests/test_alert_text.py
    - .planning/phases/05-a-reading-means-something/deferred-items.md
  modified:
    - boty/models.py
    - boty/retailers.py
    - boty/monitor.py
    - boty/notify.py
    - scripts/mutation_check.py
    - tests/test_retailers.py
    - tests/test_monitor.py
    - tests/test_pacing.py

key-decisions:
  - "STORE_SCOPED lives in boty/models.py, not boty/retailers.py: monitor.py would otherwise have to import the browser/curl_cffi stack to read the predicate it must agree with"
  - "The two guards sit after the extraction refinement and before the offer logic, so their returns are the FIRST returns in _verdict_from_html"
  - "store is None and store != store_id share one guard, not two: neither can be shown to come from the pinned store, which is the same fact for the purposes of a verdict"
  - "A refusal is never a store gap — _is_store_gap returns False for c.refused before anything else, so a refusal cannot be attributed to the store pin"
  - "The store arm deliberately does NOT carry CAUSE_UNKNOWN: it is the one failure in assess_health whose cause the code measured"
  - "The breakage arm keeps 'missed silently' — the consequence follows from what a control IS, unlike the cause, which was never measured"
  - "No new notification sender: the store gap rides send_health_warning and inherits watch_cycle's warned memory and its delivery rollback"
  - "The withdrawn-fragment list is short and contiguous-in-source (`probably broken`, not the full rendered sentence), so the gate cannot pass vacuously"

patterns-established:
  - "A gate on an absence is written and run BEFORE the edit it gates, and its red output is quoted verbatim in the summary"
  - "A test that a previous plan designed to go red is rewritten to pin the successor property, never deleted"

requirements-completed: [REQ-14, REQ-15]

# Metrics
duration: 20min
completed: 2026-08-10
---

# Phase 5 Plan 02: The Store Changes The Verdict, And The Alerts Stop Guessing Summary

**A Walmart reading that cannot be shown to come from the store the watch is about is now `Availability.UNKNOWN` before any stock verdict can form — proven by two new mutations, 8/8 → 10/10 — and the three alert sentences that named causes nobody measured are withdrawn behind an `ast` gate that was watched failing on all four fragments first.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-10T15:51Z
- **Completed:** 2026-08-10T16:11Z
- **Tasks:** 3 (5 commits — each TDD task RED then GREEN)
- **Files modified:** 8 modified, 2 created

## Accomplishments

- **The 2026-08-09 defect cannot ship again.** A page answering for another store, or a watch with nothing pinned, returns UNKNOWN from the first `return` in `_verdict_from_html`. M10 proves the *comparison* is load-bearing, not merely that a guard exists.
- **The alert channel stopped asserting causes.** *"we are asking too often"*, *"the detector is probably fine"*, *"the detector is probably broken"* and the hardcoded `"bot-y: detector problem"` title are gone from every string that can reach a person, and `tests/test_alert_text.py` was watched reporting all four before the edit.
- **Exactly two of four arms say "we do not know why."** The refusal and breakage arms carry `monitor.CAUSE_UNKNOWN`; the no-control and store-gap arms do not, because their cause was measured. Asserted as a partition, so the negative gate cannot be satisfied by deleting every explanation.
- **No verdict moved for any retailer that has no stores.** GameStop, Best Buy, Target and Amazon each assert their pre-plan availability, price and `detail` byte for byte.
- `make verify-offline` exits **0** with **595 passed** (was 568) and **10/10 mutations** (was 8/8).

## Task Commits

1. **Task 1 (RED): the store guards, watched red** — `e4adeae` (test)
2. **Task 1 (GREEN): unpinned or unexpected store is UNKNOWN** — `fba0370` (feat)
3. **Task 2 (RED): the absence gate, red on all four fragments** — `4622dd0` (test)
4. **Task 2 (GREEN): no alert names a cause the code did not measure** — `c1ef9b1` (feat)
5. **Task 3: M9 and M10, both observed CAUGHT** — `abd77d0` (test)

No refactor commit: neither task's green step left anything to clean up.

## Red-watch transcript 1 — the two guards

Previous count, recorded beside the new one so the rise is shown rather than
claimed: **8/8** (05-01-SUMMARY.md, "Mutations 8/8, unchanged — this plan
deliberately adds no mutation … The count rises in 05-02"). Now:

```
mutation check: 10 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (595 passed in 10.21s)
  CAUGHT    M9 boty/retailers.py: 3 test(s) failed — test_an_unpinned_walmart_watch_is_unknown_not_a_verdict, test_the_two_store_guards_say_different_things, test_the_store_guards_return_before_any_stock_verdict_can_form
  CAUGHT    M10 boty/retailers.py: 3 test(s) failed — test_a_page_answering_for_another_store_is_unknown_not_a_verdict, test_a_page_that_names_no_store_reaches_the_same_refusal, test_the_two_store_guards_say_different_things
mutation check: 10/10 mutations caught
```

Both mutations flip their guard's `Availability.UNKNOWN` to
`Availability.OUT_OF_STOCK` and nothing else. Neither `search` string contains
any part of a `detail` message — each anchors on its own condition line plus the
verdict, on M2's recorded lesson that "matching the message text would tie a
mutation to prose that is edited far more often than the verdict is." 05-04 may
still edit those sentences without touching this gate.

## Red-watch transcript 2 — the absence gate, before the edit

`tests/test_alert_text.py` was written and run **against the pre-edit text**,
before a single character of `monitor.py` or `notify.py` changed. Verbatim:

```
E       AssertionError: boty.monitor still carries 3 withdrawn claim(s):
E           'we are asking too often' in 'the retailer is refusing us — a challenge page or a 403. The detector is probably fine; we are asking too often. Backing off, and no action is needed unless this persists'
E           'probably fine' in 'the retailer is refusing us — a challenge page or a 403. The detector is probably fine; we are asking too often. Backing off, and no action is needed unless this persists'
E           'probably broken' in 'control product is not reading IN_STOCK — the detector is probably broken, so real restocks would be missed silently'
E       AssertionError: boty.notify still carries 1 withdrawn claim(s):
E           'detector problem' in 'bot-y: detector problem ('
E       assert not [('detector problem', 'bot-y: detector problem (')]
=========================== short test summary info ============================
2 failed in 0.03s
```

All four withdrawn fragments, in the two modules the gate is scoped to. Green
after the edit, along with the rest of `test_alert_text.py` (9 tests).

**A finding worth recording about the method.** The plan expected the detector
sentence to defeat a naive matcher because it is *split across two adjacent
string literals* in source (`"…the detector is "` / `"probably broken, so real
restocks…"`). That is true of **grep**, which reads lines — and it is precisely
why the fragments in `WITHDRAWN` are short and contiguous-in-source. It is *not*
true of `ast`: Python concatenates adjacent literals at parse time, so the tree
carries one `Constant` holding the whole sentence, which is why the transcript
above prints it rendered. The `ast` approach is therefore **stronger** than the
plan claimed, not merely equivalent — but the short fragments stay, because they
are what makes the gate survive a future rewording. The transcript also proves
the walk reaches inside an f-string: `'bot-y: detector problem ('` is a
`Constant` child of a `JoinedStr`, and a walk that missed it would have reported
`notify.py` clean.

## The three replacement alert strings, quoted in full

For 05-04's closing record, so it can cite what the system now says rather than
paraphrase it. `monitor.CAUSE_UNKNOWN` is `"the cause is not established"`.

**Refusal arm** (`refused=True`, carries `CAUSE_UNKNOWN`):

> the retailer is refusing us — a challenge page or a 403 came back instead of a
> product page, so the extractor was never reached and nothing here says whether
> it works; the cause is not established

**Breakage arm** (`refused=False`, carries `CAUSE_UNKNOWN`):

> a control product did not read IN_STOCK and was not refused, so readings from
> this retailer are unverified and a real restock could be missed silently; the
> cause is not established

**Store-gap arm** (`refused=False`, deliberately does **not** carry `CAUSE_UNKNOWN`):

> a control reading cannot be shown to come from the store this watch is about —
> store_id is unset in config/products.yaml, or the page answered for a different
> store. Each control below names what the page said and what is pinned

**The no-control arm is unchanged:** `"no control watch configured"`.

**The notification title:** `f"bot-y: {len(unhealthy)} retailer(s) unverified"`.
It names no cause and keeps the count, because the count is measured. The body is
still `h.reason` plus `h.failing_controls`, verbatim — asserted character for
character in `test_the_body_is_exactly_the_reason_and_the_failing_controls`.

**The two `detail` strings the guards write** (asserted unequal, so a later edit
cannot collapse them):

> no store_id pinned for this watch — set store_id in config/products.yaml. A
> walmart page answers for whichever store it chooses, so with nothing pinned
> this reading is about some store, not necessarily yours

> the page named store '0'; this watch pins store '00000' — a reading that cannot
> be shown to come from the pinned store is not a verdict about it

…and, when the page named nothing at all, the same guard renders the answered
side as *no store*:

> the page named no store; this watch pins store '0' — a reading that cannot be
> shown to come from the pinned store is not a verdict about it

## Four deviations from the outline, recorded rather than buried

### 1. `boty/models.py` — the contention table did not expect this plan there

`STORE_SCOPED` landed in `models.py` anyway, and the argument is in the code
beside it. The predicate has **two** readers — `retailers._verdict_from_html`
(the guard) and `monitor.assess_health` (the health arm) — and they must agree,
because a guard that fires where the health arm stays quiet produces an UNKNOWN
nobody is ever told about. A second copy is a second place to get it wrong, which
is the argument `_verdict_from_html`'s own docstring makes about the UNKNOWN
logic it was extracted to centralise. It could not live in `retailers.py`:
`monitor.py` would then have to import that module to read it, dragging
`curl_cffi` and the browser stack into a file that keeps even `Pacer` behind
`TYPE_CHECKING`. Safe because the waves are serial — 05-01 was wave 1, this is
wave 2, nothing ran concurrently.

### 2. `tests/test_alert_text.py` in place of the outline's `tests/test_notify.py`

REQ-15 is one requirement over two modules: `monitor.py` composes the sentence,
`notify.py` titles it, and the requirement is a claim about what reaches a
person — a property of the pair. A `test_notify.py` holding an `ast` scan of
`monitor.py` would be misfiled, and the positive and negative halves of one
requirement belong in one place, on `test_dashboard.py`'s precedent of one module
for one surface. The module's own docstring carries this argument.

### 3. `tests/test_pacing.py` — a real deviation, entered deliberately

The outline's per-plan sketch assigns that file to **05-03**. This plan entered
it because three of its assertions pinned the exact sentences REQ-15 withdraws:
`"probably fine" in health.reason` (line 61), `"probably broken"` +
`"missed silently"` (lines 72-73), and `"probably broken"` again (line 86).
Leaving them alone would have made this plan land red; deleting them would have
deleted the pin on a defect rather than update it.

Safe for two reasons: the waves are serial, and **05-03's own Task 1 already
carries the matching instruction** — *"`tests/test_pacing.py` also carries three
assertions that 05-02 rewrote; leave them exactly as 05-02 left them."*

**Nothing else in the file was touched**, and `git diff 943a52e..HEAD --
tests/test_pacing.py` proves it: the diff is exactly one import line, one
docstring item, and the three assertions. The persistence tests are untouched
and remain 05-03's.

### 4. `tests/test_monitor.py` — a table omission, not a deviation

The outline's per-plan file list for 05-02 names it; only the contention table
leaves it out. No other plan in this phase enters it, so there was no contention
to resolve — recorded here so the phase's closing audit reconciles the table
against what the plans actually touched rather than against what the table
claimed. (05-01 recorded `tests/test_fetch.py` and `tests/test_models.py` under
the same rule.)

## The `tests/test_pacing.py` finding — a fix pinned by its prose, not its property

Three assertions in the suite pinned the withdrawn claims **by quoting them**.
Each was a correct pin on 2026-08-04 and each had quietly become a pin on a
defect: the tests asserting that the 2026-08-04 fix was still in place were doing
so by requiring the exact sentences REQ-15 exists to remove. A suite written that
way makes the *next* correction land red for the right reason and the wrong one
at once — the red says "the sentence changed", not "the property broke".

**What they were rewritten to** — the property, in every case:

| Was | Is now |
|---|---|
| `"probably fine" in health.reason` | `"refus" in health.reason and CAUSE_UNKNOWN in health.reason` |
| `"probably broken"` + `"missed silently"` | `"IN_STOCK" in health.reason`, `CAUSE_UNKNOWN in health.reason`, and `"missed silently"` kept **because the breakage arm kept the consequence clause** |
| `"probably broken"` (mixed group) | `"IN_STOCK" in health.reason and CAUSE_UNKNOWN in health.reason` |

Every test's name and docstring is unchanged — the subject did not change, only
the sentence. The module docstring now records that the sentence it quotes as the
2026-08-04 defect was withdrawn in Phase 5 and is history rather than a live
claim.

## What 05-04 must know

**Both Walmart watches on this host now read UNKNOWN, and that is criterion 2
working rather than a regression.** Measured, not assumed — `Config.load` with
`WALMART_STORE_ID` unset:

```
config references ${WALMART_STORE_ID}, which is not set — substituting empty
config references ${WALMART_STORE_ID}, which is not set — substituting empty
Pokémon GO Plus +                | store_id= None | control= False
CONTROL — Great Value whole milk | store_id= None | control= True
```

So until 05-04's checkpoint sets `WALMART_STORE_ID` in
`/home/dan/.config/boty/env` and restarts the service:

- **Before:** every Walmart reading is `UNKNOWN` with the config-gap `detail`,
  and `boty check` / the dashboard show Walmart `ok=False` with the store-gap
  reason — *"store_id is unset in config/products.yaml…"*.
- **After:** the milk control should read `IN_STOCK` again with a `store` tag
  matching the pin, and Walmart should return to `ok=True` — assuming the live
  challenge block clears, which is a separate, pre-existing failure.

That gives the checkpoint a defined before/after that does not depend on
guessing. Do **not** "fix" the current UNKNOWN by inventing a default: no default
exists, deliberately, and the guard is what enforces it.

## `make verify-offline` — verdict verbatim

```
identity check: PASS — 175 file(s), no host identity found
All checks passed!
595 passed in 9.75s
control check: SKIPPED (--offline) — no live retailer request made.
  baseline  unmutated sandbox passes (595 passed in 10.31s)
mutation check: 10/10 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

Exit **0**. Test count **595**, strictly above 05-01's **568** (+27). Mutations
**10/10**, up from **8/8**. `mypy` clean (18 source files), `ruff check` clean,
`identity_check.py --all` PASS over 175 tracked files.

**`make verify` (live) was NOT run**, per the plan's evidence constraint: it has
read `VERIFY: FAIL (live controls)`, exit 2, since 2026-08-06 for reasons this
phase did not cause; Walmart is challenge-blocked at HTTP 200; and after this
plan both Walmart watches correctly read UNKNOWN for want of a pin. No acceptance
criterion here depended on a live read. The live verdict is 05-04's to record.

**Files this plan must not touch, proven untouched.** `git diff --stat
943a52e..HEAD --` for `boty/cli.py`, `boty/pacing.py`, `boty/config.py`,
`boty/status.py`, `config/products.yaml` and `served/boty/index.html` is **empty**.

## Files Created/Modified

- `boty/models.py` — `STORE_SCOPED` beside `Watch`, with what adding a retailer costs; `Result.store`'s "this plan adds no such guard" note updated to point at the guard that now exists; `Result.refused`'s withdrawn rate claim reversed in place
- `boty/retailers.py` — two guards in `_verdict_from_html`, ahead of every return, with the rejected pre-fetch placement recorded and its reason
- `boty/monitor.py` — `CAUSE_UNKNOWN`, `_is_store_gap`, a fourth `assess_health` arm, the refusal arm rewritten, the breakage arm narrowed, the module docstring's detector claim reversed in place
- `boty/notify.py` — a title that states the measured state; the "composes no diagnosis of its own" property written into the docstring
- `scripts/mutation_check.py` — M9 and M10, prose-free anchors, with why two and not one
- `tests/test_alert_text.py` — **new.** The `ast` gate on the absence, the `CAUSE_UNKNOWN` partition, and the `send_health_warning` body/title assertions against an injected fake
- `tests/test_retailers.py` — nine new store behaviours; seven pre-existing Walmart watches pinned to a redaction-vocabulary store; 05-01's structural test rewritten to pin guard placement
- `tests/test_monitor.py` — the four arms as behaviour, both mixed groups, and the refusal-takes-precedence case
- `tests/test_pacing.py` — three assertions rewritten from prose to property, plus the docstring item; nothing else
- `.planning/phases/05-a-reading-means-something/deferred-items.md` — **new.** Three out-of-scope findings, flagged not fixed

## Decisions Made

See `key-decisions` in the frontmatter. The three a later plan will reach for:

1. **A refusal is never a store gap, and the precedence is in code.**
   `_is_store_gap` returns `False` for `c.refused` before it checks anything
   else, and `refused` is evaluated first. A refusal produced no page, so the
   store could not have been established either.
2. **A mixed group falls to the breakage arm.** `refused` stays `all`-not-`any`,
   and the store arm uses the same rule. A refusal beside a store gap is neither
   arm's, so it lands on the breakage arm — the reading that claims least about a
   mixed group. Both mixed cases are pinned in `tests/test_monitor.py`.
3. **`"0"` is still never special-cased.** It appears in tests only as a *pinned
   value* and is never branched on, honouring 05-01's Finding 1 rather than
   re-implementing it.

## Deviations from Plan

The four outline deviations are documented in full in their own section above.
Beyond those, four adjustments were made during execution.

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Seven pre-existing Walmart test watches needed pinning, not five**

- **Found during:** Task 1
- **Issue:** The plan names five construction sites (`tests/test_retailers.py`
  lines 111, 131, 145, 199, 268). Two more exist, both added by 05-01 after the
  plan was written: `test_the_walmart_control_records_the_store_and_moves_no_verdict`
  and `test_every_verdict_path_carries_the_store_including_the_unknowns`. The
  second is the worse of the two — unpinned, all six of its branches would have
  collapsed into the single config-gap UNKNOWN and it would have stopped walking
  the six returns it exists to walk.
- **Fix:** Pinned to the store each fixture or payload answers for — `"0"` for
  the real captures, `"00000"` for the synthetic ones — with a comment recording
  why. **No guard was weakened and no test deleted.**
- **Verification:** `pytest tests/test_retailers.py` — 96 passed; M9/M10 both
  CAUGHT, which they could not be if a guard had been softened.
- **Committed in:** `e4adeae`

**2. [Rule 3 - Blocking] One synthetic payload had to gain a store**

- **Found during:** Task 1
- **Issue:** `test_walmart_offer_with_no_seller_recorded_is_unknown_not_a_verdict`
  serves a `_nextdata` payload carrying no `location` at all. Pinning its watch
  alone would have tripped the *mismatch* guard, and the test would have passed
  for the wrong reason — asserting a store gap while claiming to assert the
  seller question.
- **Fix:** Added `location={"storeIds": ["0"]}` to the payload and pinned the
  watch to `"0"`, so the guards pass and the test still exercises its own
  subject.
- **Verification:** The test's `"seller" in result.detail` assertion still
  passes, and M3 (the first-party filter mutation) still catches it.
- **Committed in:** `e4adeae`

**3. [Rule 1 - Bug] The plan's guard-placement anchor for M9/M10 did not exist as written**

- **Found during:** Task 3
- **Issue:** The plan specifies M9's `search` as `if watch.store_id is None:`
  followed immediately by `return Result(`, `watch,`,
  `Availability.UNKNOWN,`. As first written, each guard's explanatory comment sat
  *between* the condition and the return, so the only available anchor spanned
  comment prose — exactly what M2's comment warns against, and what would make
  these mutations drift on the next comment edit. The mismatch guard had the same
  problem plus an `answered = …` line carrying a `detail` fragment.
- **Fix:** Moved each guard's comment above its `if`, and hoisted the `answered`
  rendering above the branch, so both condition lines are immediately followed by
  their verdict. The reason is recorded in the code so the next reader does not
  "tidy" it back.
- **Verification:** Both `search` strings copied out of the file rather than
  retyped; the harness raises `HarnessError` on a missed anchor and did not. Both
  observed CAUGHT.
- **Committed in:** `abd77d0`

**4. [Rule 2 - Missing Critical] `Result.refused`'s docstring still asserted the withdrawn rate claim**

- **Found during:** Task 2
- **Issue:** `boty/models.py` documented `refused` as meaning "the extractor is
  very likely fine and we are asking too often" — both halves of the sentence
  REQ-15 withdraws, stated as fact, in the file that defines the field the arms
  branch on. Outside `test_alert_text.py`'s scope (it is a docstring, not text
  that reaches a person), but a reader taking it at face value would rebuild the
  defect.
- **Fix:** Reversal argued in place, house style: what it used to say, why it was
  withdrawn, and what `refused` still legitimately records ("no page came back").
  `models.py` is in this plan's `files_modified`.
- **Verification:** `pytest tests` 595 passed; the gate is unaffected either way,
  which is why this is recorded rather than assumed covered.
- **Committed in:** `c1ef9b1`

---

**Total deviations:** 4 auto-fixed (2 blocking, 1 bug, 1 missing critical), plus
the 4 outline deviations argued above. **Impact on scope:** none. No plan item
was dropped, simplified or deferred, and no guard was weakened to keep a test
green.

## Issues Encountered

**The plan's `if not offers:` was the wrong anchor for "the guards come first".**
The structural test initially asserted `body.index("STORE_SCOPED") <
body.index("if not offers:")`, which fails for an uninteresting reason: `if not
offers:` first appears at the *ld+json → `__NEXT_DATA__` fallback*, well before
any return. Rewritten to the property that actually matters — the guards precede
the **first `return Result(`** in the function, so nothing at all can be returned
ahead of the store check. Caught by the test going red for the wrong reason
during Task 1's green step, which is the failure mode the red-watch discipline
exists to expose.

**Three out-of-scope findings were logged, not fixed** — see
`deferred-items.md`: `README.md:327` quotes the withdrawn detector sentence as
live output; `boty/cli.py:~302` repeats the withdrawn rate claim in a comment
(05-03's file, which this plan is forbidden to touch); and
`scripts/mutation_check.py`'s module docstring still says "three mutations",
stale since M4.

## User Setup Required

None from this plan. The one setup step remains 05-04's checkpoint: set
`WALMART_STORE_ID` in `/home/dan/.config/boty/env` (mode 600) and restart
`boty.service`. See "What 05-04 must know" above for the measured before/after.

Note the standing warning in STATE.md: a restart currently resets every backoff
to zero, which is what 05-03 fixes — which is why 05-04's restart comes after it.

## Next Phase Readiness

05-03 has what it needs and nothing it does not:

- `boty/cli.py`, `boty/pacing.py` and `boty/config.py` are **untouched** by this
  plan, proven by an empty `git diff --stat`.
- `tests/test_pacing.py` carries exactly the three rewritten assertions 05-03's
  Task 1 was told to expect and to leave alone. Its persistence tests are
  unmodified.
- `monitor.CAUSE_UNKNOWN` and `models.STORE_SCOPED` are both importable
  module-level constants; nothing in `pacing.py`'s import graph changed.
- The store-gap arm is `refused=False`, so it flows through `watch_cycle`'s
  existing `pageable` filter unchanged — 05-03's persistence work does not have
  to account for a new sender, because there is not one.

No blockers. The live `make verify` failure and `QUESTIONS.md` § 0e both remain
open and are both pre-existing.

---
*Phase: 05-a-reading-means-something*
*Completed: 2026-08-10*

## Self-Check: PASSED

Every file named above exists on disk; all five task commits resolve in
`git log`. Load-bearing claims re-verified mechanically after writing this
summary: **1** definition of `STORE_SCOPED` in `boty/models.py`, read by both
`boty/retailers.py` and `boty/monitor.py`; **1** definition of `CAUSE_UNKNOWN`;
`ident="M9"` and `ident="M10"` both present in `scripts/mutation_check.py`;
`tests/test_alert_text.py` — 9 passed, so no withdrawn fragment survives in a
reachable string in either scanned module; and `git diff --stat` empty for all
six files this plan was forbidden to touch.
