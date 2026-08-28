---
phase: 08-stop-knocking
plan: 03
subsystem: pacing
tags: [pacing, persistence, staleness-window, cooloff, req-22, dated-reversal, restart]

requires:
  - phase: 08-stop-knocking
    provides: "08-02's COOLOFF_SECONDS = 259200 and REFUSALS_BEFORE_COOLOFF = 30, and the one-wave staleness gap it recorded before it existed"
  - phase: 05-persistence
    provides: "`Pacer.load`'s two-sided window on `refused_at`, applied at two sites, and the persisted `refusals` counter the cool-off rides on"
provides:
  - "REQ-22 criterion 5: a three-day cool-off survives a restart as the DEPTH the penalty resumes at, and is discarded when stale by the existing two-sided window at its existing two sites rather than by a second rule"
  - "LONGEST_WAIT_SECONDS = max(MAX_BACKOFF_SECONDS, COOLOFF_SECONDS) — the expression, never its current winner — with STATE_MAX_AGE_SECONDS re-derived from it: 21600 -> 259200"
  - "A measured restart cost of exactly 1 probe over 864 simulated cycles, beside 08-DECISIONS.md's price of one"
  - "The two absences argued in the source they are about: no _RetailerState field, no STATE_VERSION bump"
  - "M38's kill set widened from 1 to 2 — the thinness 08-02 recorded and could not fix"
affects: [08-04]

actuals:
  tokens: 9434
  tasks: 3
  commits: 2

tech-stack:
  added: []
  patterns:
    - "A derived constant written as the EXPRESSION and never as its current winning arm, so a later change to either arm cannot silently outrun it"
    - "A hand-written literal table placed beside symbolic tests precisely because symbolic tests hold whatever the constant is and therefore cannot pin where it moved TO"
    - "A gate that cannot be made red is named as green-from-birth and recorded as a finding about the change's true scope"
    - "A masked red measured separately: when assertion A fires before assertion B, B's observed value is taken by direct measurement rather than left as a prediction"

key-files:
  created: []
  modified:
    - boty/pacing.py
    - tests/test_pacing.py
    - boty/monitor.py
    - tests/test_monitor.py

key-decisions:
  - "STATE_MAX_AGE_SECONDS = LONGEST_WAIT_SECONDS, written as max(MAX_BACKOFF_SECONDS, COOLOFF_SECONDS) rather than = COOLOFF_SECONDS: identical number today, silently wrong the day either arm moves"
  - "No _RetailerState field: the cool-off is a threshold on an already-persisted counter, there is no probe flag either because `due_at` already makes that decision, and a field would have cost the bump the next argument refuses"
  - "No STATE_VERSION bump: shape unchanged, the count's meaning unchanged, and the bump's own quoted price — 'treated as absent' — would discard the cool-off of exactly the retailers this phase protects, on the day it ships"
  - "The boundary residual (~0.12% of the window) is recorded and NOT fixed: a window with slack would re-choose a number the derivation forbids re-choosing"
  - "The four window tests whose names say 'the cap' keep their names; only the derivation test was renamed, because its name stated the specific claim being withdrawn"
  - "scripts/mutation_check.py is not edited here: M33's and M38's now-stale kill-set counts are handed to 08-04, which owns that file for M42"

requirements-completed: []

status: complete
---

# Phase 8 Plan 03: Stop Knocking — The Cool-off Survives a Restart

`STATE_MAX_AGE_SECONDS` stopped being derived from the ceiling this phase stopped applying and
started being derived from the longest wait the module can actually produce — 21600 → 259200 — so a
three-day cool-off is no longer thrown away after six hours on every restart, and it is thrown away
when genuinely stale by the **same two-sided window at the same two sites**, not by a second rule
written for the occasion.

**Criterion covered:** C5, and only C5. **Not claimed:** C6 (`08-04`'s). C1–C4 were met in `08-01`
and `08-02` and are re-run here as regression only.

**One production line moved and one constant was added.** Everything else in this plan is tests and
prose.

---

## The recorded one-wave gap is CLOSED

Stated in the same terms `08-02` opened it, because a reader should not have to infer it:

> **The tree no longer holds a three-day cool-off that a restart discards after six hours.**

`08-02` wrote that gap down before it existed, deliberately, so this plan's tests would be red
against unfixed code rather than red against a synthetic revert. That is exactly what happened —
four gates were red against the tree as `08-02` left it, with observed values recorded below, and
green after one line changed.

**What closing it cost, stated rather than absorbed.** The same constant ages **both** halves of
`pacer-state.json`, so widening it widened both:

1. **The refusal counts** now survive up to three days instead of six hours. That is the point.
2. **The paging memory (`warned`) now survives up to three days instead of six hours.** That is a
   real behavioural change to a different subsystem arriving as a side effect of a shared constant:
   a health warning about our own dead control can now be suppressed for up to three days rather
   than six. Bounded, never unbounded, and argued in `boty/pacing.py` beside the constant rather
   than only here. It carries this plan's third prohibition: **a cool-off is never a way to silence
   a failure that is ours.**

And the sharing is **required, not merely tidy** — which is why criterion 5 forbids a second rule
rather than discouraging one. A retailer in a three-day cool-off is not *checked* for three days,
`cli.watch_cycle`'s `still_unhealthy = {…} | (warned - checked)` keeps an unchecked retailer in
`warned` for exactly that reason, so a six-hour window against a three-day cool-off would have
**guaranteed** on every restart the split `Pacer.load`'s own comment names: a process that comes
back knowing the retailer is entrenched and not knowing it already said so.

---

## Criterion 5, in the words it actually holds in

**Do not read the line below as "the cool-off survives a restart" unqualified.** The qualification
is the honest form and `08-DECISIONS.md` recorded it in advance:

- The cool-off survives as **the DEPTH the penalty resumes at**, never as a position on the
  schedule. `due_at` is still not persisted. That depth-only guarantee is *exactly* what the
  existing backoff already carries, and criterion 5 asks for "the same guarantee the existing
  backoff already carries" — so this is the criterion met, not a weaker thing renamed.
- **A restart still costs one immediate probe at full rate.** Measured, not inferred: **1**, over
  864 simulated cycles of 300 s (one whole cool-off window), by the repo's own
  `if p.due(...): count += 1; p.record(...)` idiom over a plain float `now`.
- The discard is **the existing two-sided window at its existing two sites**. No new comparison, no
  new constant beside it, no cool-off-specific age-out.

### The measured probe count beside the price set in advance

| | Value | Provenance |
|---|---|---|
| `08-DECISIONS.md` § *Collision 2*, priced in advance | **1** | written 2026-08-28 before any code moved |
| Measured across an actual restart, this plan | **1** | `test_a_restart_mid_cooloff_is_probed_exactly_once_over_a_whole_window`, 864 cycles |

**They agree, and nothing is superseded.** This is the first place in the phase that the one-probe
cost is *observed across an actual restart* rather than decided. Had they differed the run would
have won and the decision record would have been superseded beside itself, dated; it did not.

**The same test's red observation is the number worth keeping**: against the unfixed derivation the
restart cost **17 probes**, not 1 — because the discarded record put the retailer back on the
climbing backoff. That 17 is what the gap actually cost.

---

## Every gate, watched red or named green-from-birth

**Five separate measured runs, each recorded at the moment it printed.** A predicted count is not a
measurement.

| Step | What was run | Observed | Expected |
|---|---|---|---|
| 0 | `pytest tests/test_pacing.py --collect-only -q` | **86 collected** | — |
| 1 | `LONGEST_WAIT_SECONDS` added alone, `pytest tests/test_pacing.py -q` | **86 passed, 0 failed** | unchanged |
| 2 | derivation test rewritten, same command | **1 failed, 85 passed** | 1 failure |
| 3 | four behavioural gates added, same command | **5 failed, 90 passed** | 5 failures, no sixth |
| 4 | the one line changed, same command | **95 passed, 0 failed** | all green |
| — | `pytest tests/ -q -rs` | **916 passed, zero skips** | green, no new skip |

**Step 1's zero is a measurement too, and it is what makes every later red attributable.** An
unreferenced module-level constant is not a behaviour change; saying so is what pins the reds at
steps 2 and 3 to the derivation and to nothing else.

### The five reds, per gate, with the value actually returned

| # | Gate | Observed | Expected |
|---|---|---|---|
| 1 | `_RESTORE_ACROSS_THE_STALENESS_WINDOW` row 2 (age `21601.0`) | `assert 0 == 30` — and `current_interval` **300** | 30 and `259200.0` |
| 2 | row 3 (age `259199.0`) | `assert 0 == 30` — and `current_interval` **300** | 30 and `259200.0` |
| 3 | `test_a_restart_mid_cooloff_is_probed_exactly_once_over_a_whole_window` | `assert 17 == 1` | 1 |
| 4 | `test_one_load_restores_the_count_and_the_paging_memory_together` | `assert set() == {'amazon'}` | `{'amazon'}` |
| 5 | `test_the_age_out_is_derived_from_the_longest_wait_the_module_can_produce` | `assert 21600 == 259200` | equal |

**The interval column of rows 2 and 3 was MASKED and was measured separately rather than predicted.**
The refusals assertion fires first, so pytest never reached the interval assertion and its red was
invisible in the transcript. Rather than write down a value the run had not printed, the five ages
were driven directly through `Pacer.load` and `current_interval` against the unfixed derivation:

```
STATE_MAX_AGE_SECONDS as it stands: 21600
age=       1.0  refusals= 30  current_interval=259200
age=   21601.0  refusals=  0  current_interval=300
age=  259199.0  refusals=  0  current_interval=300
age=  259201.0  refusals=  0  current_interval=300
age=      -1.0  refusals=  0  current_interval=300
```

So both columns of rows 2 and 3 are observed, not assumed. This is the repository's own rule applied
to a case it does not usually come up in: an assertion that never ran has not been watched red.

### Five gates were GREEN FROM BIRTH, and that is a finding about this change's true scope

Named rather than skipped past, because a green test inside a watched-red plan is a claim about what
the change does **not** repair:

| Green from birth | Why it could not be made red |
|---|---|
| Table row 1 (age `1.0`) | a fresh record was always inside the window |
| Table row 4 (age `259201.0`) | past the NEW window as well as the old — the upper bound bound before and binds now |
| Table row 5 (age `-1.0`, a future stamp) | the lower bound bound before and binds now |
| `test_a_cooloff_survives_into_a_brand_new_pacer_and_reaches_the_schedule` | its document is written and read in the same instant, so its age is ~0 |
| `test_a_standing_interval_above_the_window_makes_the_restored_depth_irrelevant` | reads no document and no clock; the window cannot reach it |

**What that tells you: the survival machinery already existed and was already right.** The counter,
the wall-clock stamp, the clamp, the round trip through a real `save`, the two-sided bound — all of
it was in the tree and working. The only thing wrong was **how long the window believed it**. This
plan repairs a window, not a persistence layer, and the five controls are the evidence for that
sentence. A control that had gone red would have meant this task broke something rather than found
something; none did.

**No expected-red gate came up green**, so there was nothing to halt on.

---

## The number, and why it is written as an expression

```
MAX_BACKOFF_SECONDS  = 6 * 60 * 60      = 21600     (unchanged, by all three plans)
COOLOFF_SECONDS      = 3 * 24 * 60 * 60 = 259200    (08-02's, not re-decided here)
LONGEST_WAIT_SECONDS = max(MAX_BACKOFF_SECONDS, COOLOFF_SECONDS) = 259200
STATE_MAX_AGE_SECONDS = LONGEST_WAIT_SECONDS = 259200            (up from 21600)
```

Verified: `.venv/bin/python -c "import boty.pacing as p; print(...)"` → `259200 259200 21600 259200`.

**`= COOLOFF_SECONDS` would be shorter, would give the identical number today, and would be wrong
tomorrow.** It says *the window is the cool-off*, where what the constant's own comment argues is
that the window is one full longest-wait-length window. A later phase raising `MAX_BACKOFF_SECONDS`
above the cool-off, or shortening the cool-off, would leave the short form silently understating a
wait the module actually produces — which is precisely the defect this plan removes, rebuilt from
the other end by the fix for it.

### The dated reversal, and the unusual thing about it

The withdrawn text is quoted **in full** beside the constant, dated 2026-08-28: both the derivation
sentence and the sentence arguing the cap already *is* this project's written answer to how long a
refusal stays evidence. They are one argument in two halves and quoting half would have made the
reversal look larger than it is.

**No conclusion fell, and the comment says so explicitly**, because a reader meeting a reversal
expects one to have. *Derived and never re-chosen, so the two cannot drift* is untouched. *"One full
cap-length window"* survives in substance as one full longest-wait-length window. What changed is
the **premise** that the cap was the longest wait. The constant survives as a name; only what it
derives from moved.

### The residual, measured rather than waved at

The window now **equals** the longest wait, so a record can age out only in the sliver between a
cool-off expiring and the next cycle actually probing — the loop's schedule carries jitter, so the
probe lands at or slightly after the wait. **Roughly one cycle: about 300 s in 259200, or ~0.12% of
the window.** It points the same direction the withdrawn six-hour window pointed **100% of the
time**, so this is a strict improvement rather than a trade.

**The option not taken, named so it reads as a decision:** a window with slack
(`LONGEST_WAIT_SECONDS * 2`) would remove the sliver and would **re-choose a number the derivation
forbids re-choosing** — buying 0.12% with the one property that keeps the two constants from
drifting apart. Recorded, not fixed. If it ever bites, the change to consider is to
`LONGEST_WAIT_SECONDS`' definition, never a second constant beside it.

---

## Criterion 5's second clause: there is no second rule, and barely a third use

The outline called a cool-off *"its third use, not a second rule."* **Reading the code, it is less
than that — it is not a new use at all.** The cool-off is carried entirely by `refusals`, which the
first guard site already governs, with the same stamp field, the same guard and the same constant.
This plan adds no site, no comparison and no constant beside it; it changes one right-hand side.
That is a stronger statement than the outline's and it is the one the source supports.

Proved three ways rather than asserted:

| Proof | Result |
|---|---|
| Source count of the guard sites | `grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py` = **2**, unchanged and un-added-to |
| A stamp one second in the FUTURE, at cool-off depth | still discarded (table row 5) — the window is still two-sided |
| One `load` restoring both halves at an age where both used to be thrown away | `test_one_load_restores_the_count_and_the_paging_memory_together` — only possible under **one** constant |

Confirmed by **reading** `Pacer.load` and not by trusting the diff: both guard lines are
byte-unchanged, and the full production diff for this plan is two hunks, both above the method.

```
+LONGEST_WAIT_SECONDS = max(MAX_BACKOFF_SECONDS, COOLOFF_SECONDS)
-STATE_MAX_AGE_SECONDS = MAX_BACKOFF_SECONDS
+STATE_MAX_AGE_SECONDS = LONGEST_WAIT_SECONDS
```

Step 4's diff alone, taken against a snapshot rather than reasoned about: **exactly one changed
line.**

---

## The two absences, argued rather than merely not done

### No `_RetailerState` field — three legs, written in the class it is about

1. **There is no fact a field would carry.** The cool-off is a *threshold* on `refusals`, which is
   already persisted, already stamped by `refused_at`, already aged by the window and already
   clamped at 64 — which sits above the threshold of 30 on purpose, so a restored count can cross
   it. An `in_cooloff` flag would store a value derived from a value already stored: the second copy
   of a number this module argues against three times over, and two copies only have to disagree
   once.
2. **There is no probe flag either, and that is the leg worth arguing.** `08-PATTERNS.md`
   § *No Analog Found* proposes copying `_warned_since`'s shape if a stamp distinct from
   `refused_at` were needed. It is not: "exactly once" is produced by `record` re-scheduling
   `due_at` **unconditionally on every outcome**, so the probe cannot repeat within a process; and
   across a restart `due_at` resets to 0.0 by design, which collision 2 decided and priced at one
   request. A stored flag would be a second memory of a decision `due_at` already makes.
3. **A field would have cost a version bump**, which the next argument refuses to pay — so these
   are one argument, and the honest order is no field first, no bump following from it.

Verified by **reading** the dataclass: still exactly four fields — `interval`, `refusals`, `due_at`,
`refused_at`.

### No `STATE_VERSION` bump — the rule APPLIED, not dodged

`08-02` handed this question forward explicitly. The paragraph added to the `STATE_VERSION` comment
is labelled an **application** of the bump rule, not a withdrawal of it; nothing above it is
reversed.

**The case FOR a bump, stated first and in its strongest form**, because a rule you only quote
against yourself is not a rule: the comment says this document carries a **count whose units are a
policy decision**, and REQ-22 changed exactly that policy — past 30 refusals the same stored number
now denotes a three-day wait where on 2026-08-27 it denoted six hours. That is precisely the shape
the rule points at.

**It resolves against a bump, on three legs:**

1. **The document's SHAPE is unchanged.** No new key, no changed type, no changed nesting. A
   pre-phase and a post-phase document are parse-compatible in *both* directions, so no misparse is
   possible either way — and a misparse is what the v1→v2 bump was actually bought for, when
   `warned` changed from a list to a mapping and the old shape could not be aged at all.
2. **The count's MEANING is unchanged; only the response to it moved.** `refusals` is still the
   number of consecutive refusals — a true fact about the retailer's history under either policy.
   The new policy gives *unchanged evidence* a new answer, in the direction of asking **less**. An
   old file read by new code produces a longer wait; a new file read by old code produces the
   six-hour cap. Both directions are safe and neither is a wait nobody chose.
3. **The bump's own quoted price is decisive here.** *Treated as absent* means every retailer's
   refusal count is discarded on the upgrade — so on the day this phase ships, every retailer at or
   past the threshold would lose its cool-off, be asked at full rate and climb from the bottom.
   **This phase's own defect, delivered by this phase's own safety mechanism, to exactly the
   retailers the phase exists to protect.** The price would be paid in the currency the phase is
   denominated in.

**The residual, named:** a *downgrade* — an older binary reading a post-phase document — is
unaffected by a version field for the same reason the comment already gives about `monitor.State`:
the code that would check it is the code that does not exist yet. What that binary does is apply the
six-hour cap to a count it understands, which is leg 2's safe direction.

**The rule is left standing unweakened.** A future change that alters the document's SHAPE, or that
*rescales what a stored count denotes* rather than what the module does about it, still owes a bump.

**`grep -c '^STATE_VERSION = 2$' boty/pacing.py` = 1** — the version did not move, and the argument
for that sits beside it in the source rather than only in a planning document.

---

## The `grep` discovery pass — what it looked at, and what was deliberately left

`grep -rn "six hours\|6 hours\|cap-length" --include=*.py --include=*.md --include=*.html . | grep -v '^./.planning'`
— every hit outside `.planning/` was read. A discovery pass whose result is "nothing else" is only
worth something if it says what it looked at.

**Edited (the four files in `files_modified`):**

| Site | What was wrong | What was done |
|---|---|---|
| `boty/pacing.py` `STATE_MAX_AGE_SECONDS` comment | derived the window from the cap and argued the cap *is* the answer | dated reversal, both sentences quoted in full, whole argument surviving; plus the shared-constant paragraph and the measured residual |
| `boty/pacing.py` `Pacer.load` × 2 guard comments | both said *"past the cap"* about a bound that is no longer the cap | plain correction (a label, not an argument), both-bounds and clock-jumped-backwards reasoning untouched |
| `boty/monitor.py` `EARLIEST_CREDIBLE_READING` | quoted the pacing window as *"six hours"* / *"one backoff window"* | the **number and derivation** corrected; the conclusion untouched, and noted as slightly *stronger* now — the two bounds are further apart and the argument never rested on the gap being small |
| `tests/test_monitor.py` round-trip docstring | called a two-day stamp *"well past `pacing.STATE_MAX_AGE_SECONDS` (6 hours)"* — now **false**, two days is inside a three-day window | rewritten to what is now true, and to make the point better: whether one bound sits inside the other was never what made reuse wrong; **the two bounds answer different questions** |
| `tests/test_pacing.py` × 4 window-test docstrings | names say "the cap" about a window that is not the cap | one dated line each; **names KEPT** — their assertions are symbolic and still exactly right, and a rename would cost `git log -S` history while changing nothing checked |
| `tests/test_pacing.py` × 2 assertion messages | said *"one full cap-length window"* | repaired — a failure message telling a future reader the wrong thing at the exact moment they are debugging is the worst place for stale prose |

**Read and deliberately NOT touched:**

| Site | Why |
|---|---|
| `boty/cli.py:597` — *"2 pages in 120 cycles, climbing to one every six hours forever at the cap"* | a **dated 2026-08-10 measurement**. True when written. `CLAUDE.md`: recorded beside, never edited away |
| `docs/retailer-evidence.md:3391, 3566` | dated v0.2 measurements of paging cadence. Same rule |
| `scripts/mutation_check.py:413` (M14's `breaks`) | describes a regression *at the cap*, which is still exactly right for every count below the threshold — and this plan does not edit that file at all |
| `tests/test_ci_workflow.py:214, 900` | the GitHub Actions **default job timeout** is six hours. Nothing to do with pacing |
| `tests/test_pacing.py:193` | 08-02's reversal docstring describing the **withdrawn** rule ("keep asking every six hours forever"). Accurate as a description of what was withdrawn |
| `tests/test_cli_watch.py:807` | describes the change correctly already |
| `.planning/**` | excluded by the pass's own filter; this plan edits no planning document but its own SUMMARY |

**Module-docstring concession (a) was CHECKED and survives unedited.** It says a file written before
a machine was off for **a week** is ignored rather than applied. A week is 604800 s and the window is
259200 s, so the sentence is still true and still says what it meant. Recorded in the source with
one line saying it was tested — this project has been bitten by prose that quietly went false.

---

## The mutation harness — a result, and one plan inaccuracy corrected by reading

`.venv/bin/python scripts/mutation_check.py` → **`mutation check: 37/37 mutations caught`, exit 0.**
Not 1 (a survivor) and not 2 (a harness error, which is not a result at all). Identical to the total
`08-02-SUMMARY.md` recorded, as it must be: **this plan registers no ident.**

`grep -c 'ident="M'` = **37**, unchanged. `grep -c "INTENTIONAL GAP"` = **7**, unchanged.
`grep -c 'ident="M42"'` = **0** — **M42 is still free for `08-04`**, and M21–M24 remain the
intentional gap.

**A plan inaccuracy, corrected by reading the registry rather than trusting the plan.** `08-03-PLAN.md`
names *"M12 and M13, the two idents that guard this window"* and calls M13 *"the paging-memory
guard's twin"*. It is **M16** that anchors the paging-memory guard line; M13 anchors
`return restored`, one statement further on. All three are reported CAUGHT, so nothing was missed —
but a summary that repeated the plan's pairing would have left the wrong map for `08-04`.

### Kill sets, measured alone in the harness's own sandbox — never carried over

Measured by applying each mutation alone via the harness's own `build_sandbox` / `apply_mutation` /
`run_suite` and reading the failures off the run — `08-02`'s protocol, unchanged.

| Ident | Anchors | Recorded in the registry | **Measured 2026-08-28, this tree** | Moved? |
|---|---|---|---|---|
| M12 | the refusal-count guard line | *no count recorded* | **4** | no prior to compare; 2 of the 4 are this plan's discard rows |
| M13 | `return restored` | *no count recorded* | **5** | no prior; 1 of the 5 is this plan's both-halves test |
| M16 | the paging-memory guard line | *no count recorded* | **2** | unchanged set — see below |
| M33 | `current_interval`'s return | **21** (2026-08-28, `08-02`) | **26** | **+5** |
| M38 | `current_interval`'s outer `max` floor | **1** (2026-08-28, `08-02`) | **2** | **+1** |

**M33's five additions are exactly this plan's tests that reach `current_interval` through a restored
depth**: table rows `1.0`, `21601.0` and `259199.0` (rows `259201.0` and `-1.0` restore zero
refusals, so the accessor answers the standing interval with or without the mutation and M33 is
invisible to them), the real-`save` round trip, and the one-probe restart simulation.

**M38's second killer matters more than its size, and it falsifies a sentence in the registry.**
M38's comment block, written by `08-02` on 2026-08-28, reads:

> "A ONE-TEST KILL SET IS STILL THIN AND IS STILL RECORDED AS THIN. The reason is unchanged and this
> phase did not improve it: no other test in this suite configures a standing interval above
> `MAX_BACKOFF_SECONDS`, and none of 08-02's new gates does either."

That is now **false**. `test_a_standing_interval_above_the_window_makes_the_restored_depth_irrelevant`
configures a standing interval of **259201.0** — above both wait arms — and kills M38. The thinness
`08-02` recorded and explicitly could not fix has been narrowed, by a test written for a different
purpose entirely.

**M16's set did not move, and the reason is worth writing down rather than reading as a miss.**
`test_one_load_restores_the_count_and_the_paging_memory_together` is a **restore** test at an age
*inside* the window; M16 disables aging altogether, so only a **discard** test can see it. The
new test kills M13 instead, which is the correct ident for what it asserts.

**No edit was made to `scripts/mutation_check.py`, and that is the plan's instruction rather than an
omission.** M33's `21` and M38's `1`, and M38's now-false thinness sentence, are **handed to
`08-04`**, which owns that file for M42 and can make every edit in one commit. Two plans in adjacent
waves editing the same registry is drift this phase has already paid for twice.

**M12's `breaks` prose — a deliberate decision, also handed to `08-04`.** It reads *"a file written
before a machine was off for a week pins a retailer **at the cap** on startup"*. With the guard
disabled and the window now three days, a restored count below 30 still pins at the cap and one at
or above 30 pins at the **cool-off**. So the clause has become **imprecise rather than false** — it
is still exactly right for every count this project has actually observed, and it understates the
case past the threshold. Judged, recorded, and not edited here.

---

## The gate

`make verify-offline`, nvm sourced first (`export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh`,
`node --version` → `v24.16.0`). **Exit code 0.** **Verdict line, verbatim:**

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

**Which of the three passes: the OFFLINE pass.** Not the unqualified `PASS`, and not
`PASS (INCOMPLETE — some controls could not run on this host)`. No control was reported unverifiable
on this box, and **nothing in this run says the retailers still work.**
`control check: SKIPPED (--offline) — no live retailer request made.`
`identity check: PASS — 240 file(s), no host identity found.`

### The nine new tests execute INSIDE the gate, proved rather than assumed

The gate's test stage is `$(PYTHON) -m pytest tests/ -q -rs` (`Makefile:76`) and reported
**`916 passed`** with **no skip summary at all, i.e. zero skips**. Deselecting exactly this plan's
nine from that same command gives **`907 passed, 9 deselected`** — and 907 is precisely the total
`08-02-SUMMARY.md` recorded. So the nine ran inside the gate, not beside it under a direct `pytest`.

**`tests/test_dashboard.py` BOUND rather than skipped**, which has silently failed here before
because `make` does not inherit nvm. Deselecting that module from the gate's own command drops the
total to **`895 passed`**, and the module alone runs **`21 passed`** — 916 − 895 = 21, so all 21
dashboard tests are among the 916 the gate executed.

| Measurement | Before this plan | After |
|---|---|---|
| `tests/test_pacing.py` collected | **86** | **95** |
| Delta | — | **+9**, exactly as planned; the derivation test is a rename and adds none |
| Suite under the gate's own invocation | 907 | **916** |
| Skips under the gate | 0 | **0** |

The 29 skips visible in the mutation harness's `baseline unmutated sandbox passes (887 passed, 29
skipped)` line are the **harness sandbox's**, not the gate's — the sandbox carries a subset of the
tree. `08-02` recorded the same 29. No new skip anywhere.

---

## The scope fence

`git diff --name-only 5ecc68f..HEAD` — exactly the four paths in `files_modified`:

```
boty/monitor.py
boty/pacing.py
tests/test_monitor.py
tests/test_pacing.py
```

**Not touched:** `scripts/mutation_check.py` (M42 is `08-04`'s; M21–M24 remain the intentional gap),
`served/boty/index.html` (collision B's `fmtDur` day band is `08-04`'s deliberate call),
`boty/cli.py`, `boty/status.py`, `.planning/ROADMAP.md`, `.planning/STATE.md`. Inside
`boty/pacing.py`: `Pacer.load`, `Pacer.save`, `Pacer.record`, `Pacer.due`, `Pacer.current_interval`,
`_RetailerState`'s four fields and `STATE_VERSION`'s value are all unchanged — only comments moved,
plus the one constant and the one right-hand side.

Source gates, all measured:

```
grep -c '^LONGEST_WAIT_SECONDS = ' boty/pacing.py          -> 1
grep -c '^STATE_MAX_AGE_SECONDS = ' boty/pacing.py         -> 1
grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py         -> 2
grep -c '^MAX_BACKOFF_SECONDS = 6 \* 60 \* 60$'            -> 1
grep -c '^COOLOFF_SECONDS = 3 \* 24 \* 60 \* 60$'          -> 1
grep -c '^STATE_VERSION = 2$' boty/pacing.py               -> 1
grep -c '2026-08-28' boty/pacing.py                        -> 16
grep -c '21601' tests/test_pacing.py                       -> 4
grep -c '259199\|259201' tests/test_pacing.py              -> 9
grep -c '^_TWO_DAYS = 172800.0$' tests/test_monitor.py     -> 1  (unchanged)
```

---

## What a green run does NOT mean

Four statements, each in its own sentence rather than folded into a verdict.

- **Criterion 6 is NOT discharged here.** No mutation ident was registered, none was observed CAUGHT
  for the first time, and **M42 is still free**. `08-04` owns it. The `37/37` above says the tree is
  still green with this change in it — a regression check — and nothing more.
- **Criteria 1, 2, 3 and 4 are re-run as regression, not re-claimed.** They were met in `08-01` and
  `08-02` and their numbers belong to those SUMMARYs.
- **The recorded one-wave gap is CLOSED**, in the terms `08-02` opened it, and the cost of closing it
  — a paging memory now aged on the same three-day schedule — is stated above and argued in the
  source rather than only here.
- **Criterion 5 is met, with its qualification.** The cool-off survives a restart as the **depth**
  the penalty resumes at and never as a position on the schedule; a restart still costs one
  immediate probe, measured at 1; and the discard is the existing two-sided window at its existing
  two sites. **Not rounded up to "the cool-off survives a restart" unqualified.**

## Nothing live was touched

No live retailer request was made by any task. **`boty check` was not run.** `make verify` — the
unqualified target with live controls — was deliberately not run. `state.json`, `pacer-state.json`
and `served/boty/status.json` were **neither read nor written**; every test builds its own document
in `tmp_path`, and `git status --porcelain` shows no modification to any of them. **No
`systemctl restart boty`** — a restart is Dan's call, and the irony is noted: this plan proves a
restart is survivable *by test*, never by performing one.

---

## Deviations from Plan

**1. [Rule 1 - Measurement gap in the plan's own method] A red the plan asked to be recorded was masked, and was measured separately rather than predicted**

- **Found during:** Task 1, step 3.
- **Issue:** The plan requires rows 2 and 3 of the table to be recorded red *"on both columns"*.
  pytest stops a test at its first failing assertion, so the refusals assertion fired and the
  `current_interval` assertion never ran. Its red existed but was never printed. Writing down a
  value the run had not produced would have been exactly the move `08-02` § *Deviation 5* caught
  itself making.
- **Fix:** Drove the five ages directly through `Pacer.load` and `current_interval` against the
  unfixed derivation and transcribed the output (reproduced above): rows 2 and 3 returned **300**
  where the table expects **259200.0**. Both columns are now observed.
- **Files modified:** none — a measurement, not an edit.

**2. [Plan inaccuracy, corrected by reading] The plan names M13 as the paging-memory guard's twin; it is M16**

- Documented in full under *The mutation harness* above. M12 anchors the refusal-count guard line,
  **M16** anchors the paging-memory guard line, and M13 anchors `return restored` one statement on.
  All three are CAUGHT, so no gate was missed — but the plan's pairing would have been the wrong map
  to hand `08-04`.

**3. [Recorded, deliberately NOT fixed — handed to `08-04`] M38's registry comment states a thinness this plan removed**

- M38's comment block asserts that *"this phase did not improve it: no other test in this suite
  configures a standing interval above `MAX_BACKOFF_SECONDS`."* This plan's
  `test_a_standing_interval_above_the_window_makes_the_restored_depth_irrelevant` does exactly that,
  and M38's kill set moved from **1** to **2**.
- **Not fixed here** because this plan does not edit `scripts/mutation_check.py` at all — that file
  is `08-04`'s for M42, and two adjacent waves editing one registry is drift this phase has already
  paid for twice. M33's `21` → `26` travels with it.

**4. [Recorded, deliberately NOT fixed — handed to `08-04`] M12's `breaks` prose has become imprecise**

- It says a week-old file *"pins a retailer at the cap on startup"*. Past the threshold it now pins
  at the cool-off. Judged **imprecise rather than false** — still exactly right below 30, which is
  every retailer this project has actually observed. Decision recorded; edit handed to `08-04`.

**5. [Plan defect, worked around — same one `08-01` hit] The `identity_check.py` verify command is missing its required flag**

- Task 2's `<verify>` gives `.venv/bin/python scripts/identity_check.py`, which exits **2** with
  `error: one of the arguments --staged --all is required`. Ran `--all`:
  `identity check: PASS — 240 file(s), no host identity found`, exit 0. `08-01` recorded the same
  plan defect; recording it again because it is still in the plans.

**6. [Carried forward from `08-02`, NOT fixed here, and handed on so it does not evaporate] `record`'s log line still reports a cool-off in minutes**

- At 30 refusals `boty/pacing.py`'s `record` logs
  `x refused us (30 in a row) — next attempt in ~4320 min, not 5`. That is the same
  units-that-hide-the-meaning problem `08-02` fixed one method over in `skipped_reason`.
- `08-02` observed it, deliberately left it (it is a log line and not the published page, and no
  task named it) and flagged it as a candidate for `08-04`. It is **not in this plan's
  `files_modified` either**, so it is left again — and carried forward here explicitly so `08-04`
  still sees it rather than having it disappear between waves.

**Total deviations:** 1 auto-fixed (a measurement method, no code), 2 recorded corrections to plan
statements, 3 recorded-and-deliberately-deferred hand-offs to `08-04`.
**Impact:** none on behaviour. Every deviation is either a measurement taken more carefully than the
plan's method allowed, or a fact written down for the next wave rather than acted on in this one.

---

## Hand-offs to `08-04`, in one place

1. **M33's kill set is 21 → 26 and M38's is 1 → 2**, both recorded in `scripts/mutation_check.py`'s
   comments at the old numbers. M38's comment additionally asserts a thinness that no longer holds.
2. **M12's `breaks` prose** says "at the cap" where it should now say "at the cap, or at the cool-off
   past the threshold". Imprecise, not false.
3. **`record`'s log line renders `~4320 min`** at 30 refusals — `08-02`'s hand-off, carried forward
   unchanged.
4. **M42 is free**, M21–M24 remain the intentional gap, and `grep -c 'ident="M'` is still 37.
5. **The number now reaching the dashboard is 259200**, and it survives a restart as of this plan —
   which is the input to collision B's `fmtDur` decision.

## STATE.md and ROADMAP.md were NOT updated

Deliberately, per this executor's instructions: the orchestrator owns those writes and edits them by
hand. **No `gsd-tools` state or phase WRITE subcommand was invoked at any point** —
`state.advance-plan`, `state.begin-phase` and `phase.complete` are banned in this repo on fourteen
recorded corruptions, the data-losing one is still present on 1.11.0, and an error return from one is
not evidence that nothing was written. `.planning/STATE.md` shows as modified in `git status`; **that
modification is not this plan's** — it was present before execution began and was never staged.

## Commits

| Commit | What |
|---|---|
| `44399e0` | `feat(08-03): derive the staleness window from the longest wait, not the cap` — Task 1 |
| `47b38ce` | `docs(08-03): argue the two absences, and repair the prose that named the cap` — Task 2 |

Task 3 writes no source file; it runs the gates and records their numbers here.

Git identity checked **before** committing: `3347065+danieljamesjohnson@users.noreply.github.com`,
the repo's configured no-reply identity. The tracked pre-commit hook ran and passed on both commits
(`PASS — 2 file(s)`, `PASS — 4 file(s)`). **No commit used `--no-verify`.**

## Self-Check: PASSED

- `boty/pacing.py` — FOUND. `grep -c '^LONGEST_WAIT_SECONDS = '` = 1;
  `grep -c '^STATE_MAX_AGE_SECONDS = '` = 1; `grep -c '<= STATE_MAX_AGE_SECONDS:'` = **2**;
  `grep -c '^STATE_VERSION = 2$'` = 1; `grep -c '2026-08-28'` = 16. `_RetailerState`'s four fields
  verified by reading the class, not by a count a comment could inflate.
- `tests/test_pacing.py` — FOUND. `grep -c '21601'` = 4; `grep -c '259199\|259201'` = 9;
  `_RESTORE_ACROSS_THE_STALENESS_WINDOW` present with five hand-written rows.
- `boty/monitor.py` — FOUND, `EARLIEST_CREDIBLE_READING`'s conclusion untouched.
- `tests/test_monitor.py` — FOUND, `_TWO_DAYS = 172800.0` unchanged.
- `scripts/mutation_check.py` — **unchanged by this plan** (`git diff 5ecc68f..HEAD --` empty for it);
  `grep -c 'ident="M'` = 37; `grep -c "INTENTIONAL GAP"` = 7; `grep -c 'ident="M42"'` = 0.
- Commit `44399e0` — FOUND in `git log`. Commit `47b38ce` — FOUND in `git log`.
- `.venv/bin/python -m pytest tests/ -q -rs` → **916 passed**, zero skips.
- `.venv/bin/python scripts/mutation_check.py` → **37/37 caught**, exit 0.
- `make verify-offline` → exit 0, `VERIFY: PASS (OFFLINE — …)`.
- `.venv/bin/python -c "import boty.pacing as p; print(p.LONGEST_WAIT_SECONDS, p.STATE_MAX_AGE_SECONDS, p.MAX_BACKOFF_SECONDS, p.COOLOFF_SECONDS)"` → `259200 259200 21600 259200`.
