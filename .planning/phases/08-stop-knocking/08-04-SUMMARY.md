---
phase: 08-stop-knocking
plan: 04
subsystem: testing
tags: [mutation-registry, req-22, criterion-6, verdict-table, dashboard-presentation, hand-offs]

requires:
  - phase: 08-stop-knocking
    provides: "08-02's cool-off branch inside Pacer.current_interval's single max(), and the re-pointed M33/M38 anchors that make the harness a result at all"
  - phase: 08-stop-knocking
    provides: "08-03's re-derived STATE_MAX_AGE_SECONDS, its measured restart cost of 1 probe, and the three hand-offs it refused to absorb silently"
provides:
  - "REQ-22 criterion 6: M42 registered on the cool-off branch, observed CAUGHT with a 14-test kill set read off the run; registry 37/37 -> 38/38, survivors 0"
  - "The measured finding that M42's kill set is a PROPER SUBSET of M33's — it localises a failure rather than closing a hole, and its comment block says so"
  - "Collision B decided against eight measured strings: the three fmtDur bands stay, and no production or served file moves"
  - "08-03's three hand-offs closed in writing — two edited with dated notes, one recorded with the measured reason no edit is owed"
  - "The six-criterion verdict table for phase 8, with nothing rounded up"
affects: []

actuals:
  tokens: 5377
  tasks: 3
  commits: 2

tech-stack:
  added: []
  patterns:
    - "An ident whose own comment block records that it closes no hole in the suite, because the alternative is a registry entry that reads as coverage it does not provide"
    - "A plan's argument for a change measured BEFORE the change is kept, and rewritten weaker when the measurement disagrees"
    - "A presentation decision settled by evaluating the real code against real inputs, with the rejected variant evaluated beside it"

key-files:
  created:
    - .planning/phases/08-stop-knocking/08-04-SUMMARY.md
  modified:
    - scripts/mutation_check.py
    - .planning/phases/08-stop-knocking/08-DECISIONS.md

key-decisions:
  - "M42 is kept on LOCALISATION alone, stated as narrower than the plan promised: its kill set is a proper subset of M33's, so it closes no hole in the suite and its comment block says the honest remedy for a reader who judges that insufficient is to delete it, not to reword it"
  - "No ident is registered for the divergence between skipped_reason's prose and record's schedule: no assertion holds that rule, so an ident on it would SURVIVE, which is exit 1"
  - "The fmtDur three bands stay; served/boty/index.html and boty/cli.py are untouched as the CONSEQUENCE of that decision rather than as an oversight"
  - "M38's kill-set thinness sentence is withdrawn beside itself with a dated note rather than deleted — it was true when 08-02 wrote it, and the interesting fact is that a later wave falsified it by accident"
  - "M12's breaks clause is repaired rather than rewritten: the destination moved with REQ-22, the mechanism did not, and 'at the cap' survives inside the repair because it is still literally correct below the threshold"
  - "record()'s ~4320 min log line is measured, still open, and deliberately NOT fixed here — it is under boty/ and this plan's scope fence asserts nothing under boty/ moved"

requirements-completed: [REQ-22]

coverage:
  - deliverable: "M42 registered on the cool-off branch and observed CAUGHT"
    verification:
      - kind: command
        ref: ".venv/bin/python scripts/mutation_check.py"
        status: pass
      - kind: test
        ref: "scripts/mutation_check.py#M42"
        status: pass
    human_judgment: false
  - deliverable: "The registry closes at 38/38 with survivors 0 and M21-M24 still empty"
    verification:
      - kind: command
        ref: "python -c 'load MUTATIONS; assert no M21..M24; len == 38'"
        status: pass
    human_judgment: false
  - deliverable: "make verify-offline exits 0 on the OFFLINE pass"
    verification:
      - kind: command
        ref: "make verify-offline"
        status: pass
    human_judgment: false
  - deliverable: "Collision B decided: the three fmtDur bands stay"
    verification:
      - kind: command
        ref: "node -e '<fmtDur extracted from served/boty/index.html:118>'"
        status: pass
    human_judgment: true
    rationale: "The measurement establishes what the four inputs render; whether 72h or 3d is the better thing for a person to read is a judgment, and it is argued rather than asserted"
  - deliverable: "The six-criterion verdict table"
    verification: []
    human_judgment: true
    rationale: "A verdict is not a measurement. Each cell cites one, but the reading of a criterion against its evidence is a human call and is offered for review rather than claimed as verified"

status: complete
---

# Phase 8 Plan 04: Stop Knocking — The Gate, and the Verdict

**M42** now gates the one line whose removal changes *when a request is made*, it was watched CAUGHT
with a **14-test kill set read off the run**, and the registry closes at **38/38, survivors 0**. Both
of the arguments `08-04-PLAN.md` wrote for M42 came back **weaker when measured**, and both are
recorded weaker — in the registry itself, not only here.

**Criterion covered:** C6, and the verdict on all six. **Not re-measured:** C1–C4 (`08-02`'s numbers)
and C5 (`08-03`'s). A verdict is not a measurement, and where a criterion's evidence is thin the
table below says thin.

**No production code moved.** `git diff --name-only b5746fa..HEAD` lists exactly two paths and
neither is under `boty/` or `served/`.

---

## Task 1 — M42

### Step 1: the baseline, which is a precondition and not a formality

```
mutation check: 37 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (887 passed, 29 skipped in 11.40s)
mutation check: 37/37 mutations caught
EXIT=0
```

**Exit 0, not exit 2.** No `HARNESS ERROR`, and M33 and M38 both reported CAUGHT — so `08-02`'s
collision-C re-point **landed**, confirmed rather than assumed. That is the whole precondition: on a
harness that was not producing results, every number below would have meant nothing.

**37 is the denominator M42 moves.** The 29 skips are the harness sandbox's, not the gate's; `08-02`
and `08-03` both recorded the same 29.

### Step 2: the anchor, copied out of the file and pre-counted

Copied from `Pacer.current_interval` in `boty/pacing.py` — located by symbol, because `08-02` and
`08-03` moved every line number in that method. `08-02` split the conditional expression across
lines, so the smallest whole source line carrying the comparison is:

```
            if st.refusals >= REFUSALS_BEFORE_COOLOFF
```

Twelve spaces of indent, **no trailing colon** — it is an arm of a conditional expression inside the
existing `max(...)`, not a statement.

**Pre-counted as a fixed substring over `Path("boty/pacing.py").read_text()`: exactly `1`.** Recorded
as the number rather than as "verified". Nothing had to be widened. `boty/pacing.py` mentions
`REFUSALS_BEFORE_COOLOFF` eleven times, but only one of those is this line; `skipped_reason`'s guard
reads the same constant at **eight** spaces of indent and **ends in a colon**, so it is a different
string and is unreachable by this replacement. `apply_mutation` replaces the first occurrence only,
which is why this count is taken rather than assumed.

### Step 3: M42 against M33 and M38 — three findings, and one of them contradicts the plan

Measured by applying each `search`-to-`replace` over the file text **in memory**, with no write to
the working tree.

| # | Question | Measured | Plan predicted |
|---|---|---|---|
| (a) | Is M42's anchor a substring of M33's `search`? | **Yes** | yes |
| (a) | Is M42's anchor a substring of M38's `search`? | **Yes** | yes |
| (b) | Does M33's `replace` remove the cool-off as collateral? | **Yes** | yes |
| (c) | Does M38's `replace` remove the cool-off as collateral? | **NO — it preserves it** | yes |

**(c) contradicts § *What it defends*, and the comment block now says the weaker true thing.** M38's
`replace` is not a bare `min(...)`; it is a `return (...)` that carries the cool-off arm through
**verbatim**, and M38's own block — written by `08-02` on 2026-08-28 — states the reason in as many
words: *"The cool-off arm is carried through into the replacement verbatim: removing it too would
make this a two-defect mutation and blur the line between what M38 gates and what M33 does."* So the
plan's claim that *"M33 and M38 both take the cool-off down as collateral"* is **half true**. Exactly
one existing ident takes it down, and it does so while destroying the accessor around it.

**(a) is the stated cost, now measured rather than anticipated:** M42's anchor sits inside the
nine-line block both other idents anchor on, so one edit to `current_interval`'s return drifts
**three** anchors. Accepted, because `apply_mutation` raises on a missing anchor and `main` turns
that into exit 2 and *"This is not a result"* — drift here is a stop, never a silent reduction.

### Step 4: the mutation is surgical

`replace` is `            if False` — the registry's own idiom (M12 and M16 use `if False:`), which a
conditional expression takes without the colon. Applied in memory:

| Property | Before | After |
|---|---|---|
| outer `return max(\n            st.interval,` | present | **present** |
| inner `MAX_BACKOFF_SECONDS,\n            ),` clamp | present | **present** |
| `Pacer.skipped_reason` | — | **byte-unchanged** |
| file parses (`ast.parse`) | yes | **yes** |

Driven directly at 30 refusals against a 300 s standing interval, unmutated and mutated:

```
ORIGINAL     current_interval at 30 refusals = 259200
ORIGINAL     skipped_reason at 30 refusals   = cooling off after 30 refusal(s) — …
M42-MUTATED  current_interval at 30 refusals = 21600
M42-MUTATED  skipped_reason at 30 refusals   = cooling off after 30 refusal(s) — …
```

The wait collapses from three days to six hours; the prose does not move.

### Step 6: watched CAUGHT, and the kill set MEASURED rather than carried over

```
  CAUGHT    M42 boty/pacing.py: 14 test(s) failed — test_a_retailer_in_cooloff_publishes_the_days_scale_cadence_it_is_actually_on, test_the_thirty_day_request_count_under_the_cooloff_is_a_stated_number, test_the_cadence_across_the_cooloff_threshold_is_the_literal_it_is[300.0-30-259200.0] (+11 more)
mutation check: 38/38 mutations caught
EXIT=0
```

**Exit 0. No `SURVIVED` line. No `HARNESS ERROR`.**

The harness prints only three names, so the full set was measured separately by applying M42 **alone**
through the harness's own `build_sandbox` / `apply_mutation` / `run_suite` — `08-02`'s protocol,
unchanged. **This is a measurement of this tree with M42 in it; not one number below is carried over
from M33, from M38, or from any prediction in the plan.**

**M42's kill set — 14 tests, pytest exit 1:**

| # | Test |
|---|---|
| 1 | `tests/test_cli_watch.py::test_a_retailer_in_cooloff_publishes_the_days_scale_cadence_it_is_actually_on` |
| 2 | `tests/test_pacing.py::test_a_cooloff_survives_into_a_brand_new_pacer_and_reaches_the_schedule` |
| 3 | `tests/test_pacing.py::test_a_refusal_record_is_restored_across_the_whole_staleness_window[1.0-30-259200.0]` |
| 4 | `tests/test_pacing.py::test_a_refusal_record_is_restored_across_the_whole_staleness_window[21601.0-30-259200.0]` |
| 5 | `tests/test_pacing.py::test_a_refusal_record_is_restored_across_the_whole_staleness_window[259199.0-30-259200.0]` |
| 6 | `tests/test_pacing.py::test_a_restart_mid_cooloff_is_probed_exactly_once_over_a_whole_window` |
| 7 | `tests/test_pacing.py::test_a_retailer_in_cooloff_is_probed_exactly_once_when_it_expires` |
| 8 | `tests/test_pacing.py::test_a_retailer_that_answers_during_its_probe_is_back_on_its_standing_interval_at_once` |
| 9 | `tests/test_pacing.py::test_the_cadence_across_the_cooloff_threshold_is_the_literal_it_is[300.0-30-259200.0]` |
| 10 | `tests/test_pacing.py::test_the_cadence_across_the_cooloff_threshold_is_the_literal_it_is[300.0-31-259200.0]` |
| 11 | `tests/test_pacing.py::test_the_cadence_across_the_cooloff_threshold_is_the_literal_it_is[1800.0-30-259200.0]` |
| 12 | `tests/test_pacing.py::test_the_cadence_across_the_cooloff_threshold_is_the_literal_it_is[1800.0-31-259200.0]` |
| 13 | `tests/test_pacing.py::test_the_persisted_count_is_clamped` |
| 14 | `tests/test_pacing.py::test_the_thirty_day_request_count_under_the_cooloff_is_a_stated_number` |

**Three of the fourteen are `08-03`'s** (rows 3, 4, 5 — the staleness-window rows at cool-off depth —
plus row 6, the restart simulation), which is the wave-3 work reaching a wave-4 gate.

#### The `skipped_reason` question: the prediction HELD

`test_a_retailer_in_cooloff_says_so_rather_than_reporting_a_minute_count` **exists**
(`tests/test_pacing.py:511` — checked, so that "not in the kill set" means something) and is **NOT in
M42's kill set**. The prose arm survives M42, exactly as § *What it defends* predicted. That is the
divergence, confirmed by measurement rather than by argument.

#### But the divergence is UNGATED, which is worse than the plan's claim being weak

The plan's second claim was that *"no existing ident covers a divergence between those two methods."*
Measured, that claim is aimed at the wrong thing: **nothing in the suite catches the divergence at
all.** M42 is caught for the *cadence*, by fourteen assertions about numbers — never for the
disagreement between what the monitor says and what it schedules. So the divergence belongs in
`breaks` as a description of what shipping this defect would look like, and it is **not what this
ident gates**. Registering an ident on the divergence itself would be a mutation on a rule the suite
does not hold, which is a SURVIVOR and a self-inflicted exit 1 — the same reasoning Task 2 applies to
the `_age`/`fmtDur` mirror.

#### The finding that decides whether M42 should exist at all

**M42's kill set is a PROPER SUBSET of M33's.** Measured by taking both sets in the harness's own
sandbox in one pass:

```
M33 size: 26   M42 size: 14
M42 is a proper subset of M33: True
in M42 but not M33: []
in M33 but not M42 (count): 12
```

**RE-MEASURED 2026-08-31 — the counts above moved, the conclusion did not.** The figures are left
unedited (they were right when written); this is the note beside them. The phase-8 code review added
three tests, two of which land in these sets:

```
M33 size: 28   M42 size: 16   M38 size: 3
M42 is a proper subset of M33: True
in M42 but not M33: []
in M33 but not M42 (count): 12
```

So M42 is **still** a proper subset — 14 -> 16 killers, all 16 still inside M33's 26 -> 28 — and it
still buys localisation rather than detection. `scripts/mutation_check.py`'s M42 block carries the
same note. M38 went 2 -> 3, widened for the third time by a test written about something else.

Every one of M42's fourteen killers already kills M33. **So M42 closes no hole in the test suite** —
a real code change deleting that comparison would be caught by those same fourteen assertions whether
or not this registry entry existed. `CLAUDE.md`'s rule is that an ident is never registered to raise
the denominator, so this is the question, not a footnote to it.

**M42 is kept, on a narrower ground than the plan promised, and its comment block says so in the
registry rather than only here:** what it adds is **localisation, not detection**. It is the only
entry whose failure signature says *the cool-off rule died* rather than *the accessor died*, and the
twelve tests that kill M33 and do not kill M42 are the standing proof that the sub-threshold backoff,
the cap and the clamp all survived. That is also what `T-08-02` asks of it — a mitigation nobody can
show would be noticed if it vanished is a mitigation on paper.

**And the block states the honest remedy if a reader disagrees:** delete M42, do not reword the
paragraph until it sounds like coverage. The measurements are written down so the question can be
re-asked rather than re-argued.

### Step 7: the count gate

| Gate | Before | After |
|---|---|---|
| `grep -c "INTENTIONAL GAP" scripts/mutation_check.py` | **7** | **8** |
| `grep -c 'ident="M' scripts/mutation_check.py` | **37** | **38** |
| `grep -c 'ident="M42"' scripts/mutation_check.py` | 0 | **1** |

The eighth marker **restates** the M21–M24 rule and does not weaken it, on M41's precedent: nothing
was added anywhere to make M42 reachable, because `boty/pacing.py` has been in `SANDBOX_CONTENTS`
since before this registry existed — which is exactly the test M21–M24 failed. The phrase is written
**once** in the block; a second use inside one block would have read as a ninth marker.

**M21–M24 confirmed still empty by loading `MUTATIONS` and reading the idents**, not by a grep a
comment could satisfy:

```
registry size: 38
M21-M24 present: []
highest/last ident: M42
```

### Step 8: `08-03`'s hand-offs, closed in writing

**The plan's own step 8(a) names the wrong idents, and this is the third such correction in this
phase.** It asks for *"M12's and M13's kill-set counts"*. `08-03` handed forward **M33's (21 → 26)
and M38's (1 → 2)**; M12 and M13 were reported in `08-03-SUMMARY.md`'s kill-set table as having **no
prior count recorded in the registry at all**. Both sets of idents are dealt with below, so nothing
evaporates either way.

**Related plan inaccuracy, carried in from `08-03-PLAN.md` and corrected again here.**
`08-04-PLAN.md`'s `<read_first>` calls **M13** *"the paging-memory guard's twin"*. It is not:
**M16** anchors the paging-memory guard line, M12 anchors the refusal-count guard line, and M13
anchors `return restored` one statement further on. `08-03` caught this and its correction did not
reach this plan's text. All three are CAUGHT — 4, 5 and 2 killers respectively — so no gate was ever
missed by the wrong map.

#### (a) The kill-set counts, all read off THIS plan's own step-6 run

| Ident | Recorded in the registry before | **Measured on this run** | Action taken |
|---|---|---|---|
| M12 | *no count recorded* | **4** | **None.** Nothing to update. Recorded here as the finding. |
| M13 | *no count recorded* | **5** | **None.** Same. |
| M16 | *no count recorded* | **2** | **None.** Same, and named because the plan mis-paired it. |
| M33 | **21** (2026-08-28, `08-02`) | **26** | **Updated**, dated, beside the 21 rather than over it. |
| M38 | **1** (2026-08-28, `08-02`) | **2** | **Updated**, dated, beside the 1 rather than over it. |

**M12, M13 and M16 got no edit, and that is the deliberate outcome rather than an omission.** Their
comment blocks record no count, so there is nothing that has gone stale; adding one now would be an
edit that records no change, which is noise in a registry that is read for its history. The counts
are recorded here instead. They also agree exactly with `08-03`'s independent measurement, which is
worth a sentence: two runs a wave apart produced the same three numbers.

**M33's and M38's updates state what moved them** — `08-03`'s staleness-window re-derivation and its
nine new tests — and state explicitly that the new count was **read off a run rather than carried
over**, which is M33's own 2026-08-17 protocol paragraph applied to itself. M33's five additions are
enumerated in the block: the staleness table's rows at ages `1.0`, `21601.0` and `259199.0`, the
real-`save` round trip, and the one-probe restart simulation. The `259201.0` and `-1.0` rows restore
**zero** refusals, so the accessor answers the standing interval either way and M33 is invisible to
them — which is why the move is +5 and not +7.

#### (a′) M38's thinness sentence, which had gone FALSE

`08-03` found that M38's block asserts *"this phase did not improve it: no other test in this suite
configures a standing interval above `MAX_BACKOFF_SECONDS`, and none of 08-02's new gates does
either"* — and that `08-03`'s own
`test_a_standing_interval_above_the_window_makes_the_restored_depth_irrelevant` configures **259201.0**,
above both wait arms, and kills M38.

**Repaired in the house dated form: the sentence is left standing and withdrawn beside itself**, not
deleted. It was true of `08-02` when `08-02` wrote it, and the fact worth keeping is that a later
wave falsified it **by accident**, with a test written to prove something else entirely. The note
also says what did *not* change: two tests is still thin, and it is still recorded as thin. What is
no longer true is the reason.

#### (b) M12's `breaks` prose — `08-03` DID record the decision, and it is executed here

`08-03-SUMMARY.md` § *Deviations* item 4 and § *Hand-offs* item 2 both carry it. Quoted:

> It says a week-old file *"pins a retailer at the cap on startup"*. Past the threshold it now pins
> at the cool-off. Judged **imprecise rather than false** — still exactly right below 30, which is
> every retailer this project has actually observed. Decision recorded; edit handed to `08-04`.

So `08-03` judged it **imprecise, not false**, *and* handed an edit forward naming the replacement
wording (*"should now say 'at the cap, or at the cool-off past the threshold'"*). Those are not in
tension — an imprecise sentence in a registry read at the moment of a survivor is still worth
repairing — and this plan **made the edit**, in `08-03`'s own suggested form:

> …pins a retailer at the cap on startup, **or at the three-day cool-off if the count it restores is
> at or past the threshold**, which is the exact objection the withdrawn docstring paragraph raised

**Repaired, not rewritten.** *"At the cap"* survives **inside** the repair rather than being replaced
by it, because below the threshold it is still literally correct. A dated comment block above M12
records what moved (the destination) and what did not (the mechanism — a week is 604800 s and the
window is 259200 s, so a week-old file is outside the window under the new derivation exactly as it
was under the old one).

#### Step 8 changed no measurement, which is how a comment edit proves it was one

Re-ran the harness after every step-8 edit. **Byte-identical to step 6** on every figure that matters:

| | Step 6 | After step 8 |
|---|---|---|
| ratio | `38/38 mutations caught` | `38/38 mutations caught` |
| exit code | 0 | **0** |
| M42 | 14 | **14** |
| M33 | 26 | **26** |
| M38 | 2 | **2** |
| M12 / M13 / M16 | 4 / 5 / 2 | **4 / 5 / 2** |

---

## Task 2 — Collision B, and the three consumer surfaces

### The measurement, taken before the decision

`fmtDur` was **extracted from the file** (`sed -n '118p' served/boty/index.html`) rather than
retyped, and evaluated under `node v24.16.0` beside a hypothetical four-band variant carrying an
`s < 86400` boundary:

```
259200   today=72h   four-band=3d
262800   today=73h   four-band=3d
21600    today=6h    four-band=6h
NaN      today=0h    four-band=0d
```

**All eight strings match the plan writer's 2026-08-28 projection**, so nothing had to be re-argued
against a surprise. Had they differed, the run would have won.

**`fmtDur` is handed a CADENCE in exactly one place, counted rather than assumed.**
`grep -n "fmtDur(" served/boty/index.html` returns **two** hits: line 119, where `fmtAge` is defined
through it and is always given an age, and line 223, `ageTag`'s warn branch. So this is a question
about one rendered string.

### The decision: keep the three bands, and change nothing

Recorded in `08-DECISIONS.md` § *Collision B*, **in the section that asked the question**, under an
`###` sub-heading — `grep -c "^## "` still prints **7**, so `08-01`'s pinned heading count is intact.

The four reasons are recorded there in full, each tied to something read or measured: the one site
collapsing `73h ago > 72h` into `3d ago > 3d` — a true `>` rendered as an apparent equality in the
one tag that exists to show a comparison; the recorded byte-identical `fmtAge` claim that would owe a
dated reversal; the measured `NaN → 0h` silent-failure analysis that a third boundary makes false in
its count *and* its outcome; and the unpinned Python mirror below. **The counter-argument is recorded
too** — `72h` makes a reader divide — and why it is accepted: the cadence renders only on a row
already older than its own cadence, which for a cool-off retailer is a row already carrying a warn
tag.

### The unpinned mirror, measured

`grep -rn "5400" tests/ --include=*.py`:

```
tests/test_dashboard.py:499:    argument, applied to a template. 5400 is the band boundary and it must occur
tests/test_dashboard.py:502:    assert len(re.findall(r"\b5400\b", page)) == 1, (
tests/test_dashboard.py:899:    `now - undefined` is `NaN`; `fmtDur`'s bands are `NaN < 90` and `NaN < 5400`,
```

Three hits, **all in `tests/test_dashboard.py`**, and the subject of the one assertion is the
**page** — it counts occurrences in `served/boty/index.html`. (An unfiltered `grep -rn "5400" tests/`
adds a fourth hit in `tests/fixtures/walmart/milk-control.html`; that is retailer markup and has
nothing to do with the bands.)

**In words: nothing in the suite pins `boty/cli.py`'s bands to the page's.** The two could diverge
with every gate green. Recorded as **pre-existing** (created in Phase 7 when `_age` was written to
mirror the page), **outside REQ-22**, **not fixed here**, and **deliberately given no mutation
ident** — an ident on a rule the suite does not hold would SURVIVE, and a survivor is exit 1.
Closing it needs an assertion first and an ident second, in that order, in a later phase.

### The three consumer surfaces, confirmed by READING — one paragraph each

**`boty/monitor.py` — `run_once`'s pacer block, lines 654–668, read.** Four calls and no fifth:
`pacer.due(...)` in a list comprehension, a set difference producing `skipped`,
`pacer.skipped_reason(...)` handed straight to `log.info`, and `pacer.record(...)` per retailer group.
**It never reads an interval, never formats one, and never branches on refusal depth.** The cadence
does not exist as a value anywhere in this function — `due` returns a bool and `skipped_reason`
returns a finished string. A days-scale number cannot reach it. **No edit needed, and the reason is
that the number never arrives here at all.**

**`boty/status.py` — the docstring at lines 84–111 and the two `current_interval_seconds` sites at
183 and 200, read.** Both sites publish `(intervals or {}).get(...)` — a raw float, passed through,
with no arithmetic, no formatting and no threshold. The docstring's contract is that the cadence is
*"the standing interval with whatever backoff is in force applied to it"*, that **the raw fact goes
out and the derived flag does not**, and that a missing cadence is `null` and **never `0`**. **All
three already cover a days-scale value** — the contract is about *provenance*, not magnitude, and
259200 is as raw a fact as 21600. The one sentence a large number could have falsified is the
`null`-never-`0` rule, and a cool-off produces a large number, never a zero. **No edit needed, and no
sentence in that docstring becomes false at three days.**

**`boty/cli.py` — four sites, and they do NOT all answer the same way.** `_current_intervals`
(225–246) builds `{retailer: pacer.current_interval(retailer)}` and passes floats through;
`watch_cycle`'s `intervals` line (498) does the same; both are magnitude-blind. The third and fourth
are not: `_report` (334) hands the float to `_age_tag`, which hands it to **`_age` (122–145)** — and
`_age` is the second home of the dashboard's three bands, by its own docstring's explicit statement.
**So `boty/cli.py` needs an edit if and only if the collision B decision adds a band.** It does not,
so it does not. Stated in that form deliberately: `cli.py`'s answer is a **consequence** of the
decision above, not an independent finding, and reporting it as an independent confirmation would be
claiming a check nobody made.

**None of the three needed an edit on the tree as it actually stands**, and the confirmation could
have come back negative — `cli.py`'s would have, under the other decision.

---

## Task 3 — the gate, and the closing figures

### The verdict LINE, verbatim

`make verify-offline`, with nvm sourced first (`export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh`,
`node --version` → `v24.16.0`). **Exit code 0.**

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

**Which of the three passes: the OFFLINE pass.** Not the unqualified `VERIFY: PASS`, and not
`VERIFY: PASS (INCOMPLETE — some controls could not run on this host; the detectors they cover are
unverified here)`.

**What that pass does and does not claim.** It says the code is internally consistent: identity,
lint, 916 tests, types over 18 source files, 11 fixtures and 38 mutations. It says **nothing** about
whether the retailers still work — the control stage printed
`control check: SKIPPED (--offline) — no live retailer request made.` followed by its own warning:
*"Nothing here says the retailers still work. Run `make controls` on a networked machine before
trusting a green run."* And INCOMPLETE would have meant a detector was unverifiable **on this host**;
no control reported that, because no control ran at all. The two are different claims and this run
made the second one.

**`make verify` — the unqualified target with live controls — was deliberately NOT run.**

### The closing figures, each read off that run

| Figure | Value | Where it came from |
|---|---|---|
| exit code | **0** | `make verify-offline` |
| pytest | **916 passed** | the gate's own stage, `$(PYTHON) -m pytest tests/ -q -rs` (`Makefile:76`) |
| skips | **zero** | `-rs` is on and **no skip summary printed at all** |
| mutation ratio | **38/38 mutations caught** | the gate's mutation stage |
| survivors | **0** | no `SURVIVED` line, no `HARNESS ERROR` |
| identity check | **PASS — 241 file(s)** | the gate's identity stage |
| types | no issues, 18 source files | mypy stage |
| fixtures | 11 fixtures, all `ok` | fixture stage |

**Every pre-existing skip recorded with its reason: there are none.** `-rs` prints a summary for
every skip and printed nothing, so the count is zero rather than unexamined. (The `887 passed, 29
skipped` line inside the mutation stage is the **harness sandbox's** baseline, not the gate's — the
sandbox carries a subset of the tree. `08-02` and `08-03` both recorded the same 29.)

**The identity check's denominator moved in the right direction: 232 pre-phase → 241 now.** The point
of recording it is that a scan whose denominator quietly *shrank* is a scan that stopped covering
something. It grew by the files this phase added. The checker did not trip on any prose this plan
wrote — which was a live risk, since this plan writes a great deal of prose *about* the file that
counts strings.

### `tests/test_dashboard.py` BOUND rather than skipped, proved rather than assumed

This has silently failed here before, because `make` does not inherit nvm and a skip is one character
from a pass in a transcript. Proved by subtraction against the gate's own command:

| Command | Result |
|---|---|
| `pytest tests/ -q -rs` (the gate's own stage) | **916 passed**, zero skips |
| the same, `--deselect tests/test_dashboard.py` | **895 passed, 21 deselected** |
| `pytest tests/test_dashboard.py -q -rs` | **21 passed** |

916 − 895 = 21, and the module alone runs 21. **All 21 dashboard tests are among the 916 the gate
executed**, and none of them skipped.

---

## The six-criterion verdict table

Each criterion is quoted **unedited** from `ROADMAP.md` § *Phase 8: Stop Knocking*. `ROADMAP.md` was
not modified by this plan. **Nothing in this table is rounded up**, and MET IN PART is a shippable
outcome here.

**One scope applies to the whole table and is stated once so no cell has to carry it twice: no live
retailer was contacted by any plan in this phase.** `boty check` was never run, `make verify` was
never run, and `COVERAGE.md`'s single declaration line says exactly this. Cells 2 and 3 additionally
carry their *simulation* scope in the cell itself, because for those two the method is load-bearing.

| # | Criterion (verbatim) | Verdict | Measured by | The measurement |
|---|---|---|---|---|
| 1 | *"After a bounded number of consecutive refusals, the wait returned for that retailer is measured in **days**, asserted against literal expected seconds — not against 'greater than the old ceiling'"* | **MET AS WRITTEN** | `08-02` | `test_the_cadence_across_the_cooloff_threshold_is_the_literal_it_is` — six parametrized rows against **hand-written literals**, not derivations: at 30 and 31 refusals it returns `259200.0` (three days) at both the 300.0 and 1800.0 standing intervals; at 29 refusals it returns `21600` at both. Watched red at `21600` where `259200.0` was expected. Four of those six rows are in M42's kill set today. |
| 2 | *"A retailer in cool-off is requested **exactly once** when the cool-off expires, not once per cycle. The single-probe behaviour is asserted over a simulated sequence of cycles, not inferred from the interval"* | **MET IN PART** — met **as written within a running process**; *"exactly once"* does **not** hold across a restart, which costs exactly one extra probe. Established in **simulation**, which is the method the criterion itself specifies. | `08-02`, with the restart half by `08-03` | `test_a_retailer_in_cooloff_is_probed_exactly_once_when_it_expires` — **13 probes** over 1000 simulated cycles before the branch, **1** after. The scope is not discovered here: `08-DECISIONS.md` § *Collision 2* priced it in advance at **one request per restart**, because `due_at` is deliberately never persisted, and `08-03` then measured a restart at **1** probe over 864 cycles (**17** against the unfixed derivation). |
| 3 | *"The total number of requests made to a retailer that **never** recovers, over a simulated 30 days, is a **stated number** and is strictly smaller than the same simulation under the current rule. Both numbers are recorded"* | **MET AS WRITTEN**, in **simulation** — both numbers come from driving a synthetic clock through a `Pacer`, and both are floors on real-world requests rather than predictions of them (zero restarts assumed, **+1 per restart**). | `08-01` (before), `08-02` (after) | **125 → 37** over the same 8640-cycle window, same retailer, same 300 s cadence, same counting idiom. A factor of 3.38, **70.4% fewer**. Both literals were **transcribed from failing assertions**, not predicted. `_THIRTY_DAYS_OF_CYCLES = 8640` did not move, so the two remain comparable, and the denominator assertion (`now == 2592000.0`) was itself **watched red** — the count alone read 125 over a shortened window and passed. |
| 4 | *"A retailer that answers during its probe returns to its normal cadence **immediately**, and the cool-off state is cleared — the failure mode where a recovered retailer stays throttled is asserted against"* | **MET AS WRITTEN**, with one thinness named rather than hidden. | `08-02` | `test_a_retailer_that_answers_during_its_probe_is_back_on_its_standing_interval_at_once`, in M42's kill set (row 8) and M33's. **The thinness:** what `08-02` recorded as watched red is the test's **setup** assertion (`21600`, expecting `259200.0`), not its recovery assertion — so what is proved is that the test cannot pass vacuously at the wrong depth, rather than that the recovery clause itself was ever observed failing. Recorded as a fact about the evidence, not softened. |
| 5 | *"The cool-off **survives a restart**, the same guarantee the existing backoff already carries, and is discarded when stale by the existing rule rather than a second one"* | **MET AS WRITTEN — carrying `08-03`'s qualification, which is not optional and is not a footnote.** The cool-off survives as the **DEPTH the penalty resumes at, never as a position on the schedule**, and **a restart still costs one immediate probe at full rate**. That depth-only guarantee is *exactly* what the existing backoff already carries, which is what the criterion asks for — so this is the criterion met, not a weaker thing renamed. | `08-03` | `STATE_MAX_AGE_SECONDS` re-derived from `LONGEST_WAIT_SECONDS = max(MAX_BACKOFF_SECONDS, COOLOFF_SECONDS)`: **21600 → 259200**, one changed line. Five gates watched red, including `assert 17 == 1` on the restart probe count and `assert 21600 == 259200` on the derivation. **"Rather than a second rule" is proved by count:** `grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py` = **2**, unchanged and un-added-to; both guard lines byte-unchanged. |
| 6 | *"`make verify-offline` exits 0, with at least one new mutation registered, observed CAUGHT, and anchored on **behaviour** rather than on message text"* | **MET AS WRITTEN**, with the measured finding that M42 buys **localisation and not detection** recorded beside it rather than folded into it. | `08-04` (this plan) | `make verify-offline` **exit 0**, verdict line the OFFLINE pass, transcribed verbatim above. **M42** registered (registry **37 → 38**, `ident="M42"` count 1), **observed CAUGHT with 14 killers read off the run**, ratio `38/38`, survivors **0**. Anchored on a source line whose removal changes *when a request is made* — `current_interval` drops 259200 → 21600 at 30 refusals — carrying **no message text, no rendered tag, no docstring fragment**. The honest qualification: M42's kill set is a **proper subset** of M33's, so it closes no hole in the suite; the criterion asks for a mutation registered, caught and behaviour-anchored, and all three are literally true. |

**CRITERION 5 IS AMENDED TO MET IN PART, 2026-08-31 — the row above is left unedited.** The verdict
word in that row was written on 2026-08-28 and was believed then; the code review of 2026-08-31
(`08-REVIEW.md` CR-01) established by measurement that the guarantee it asserts had a **systematic
hole in production at the moment it was written**, and a table that quietly agrees with itself
afterwards is worth less than one that shows the turn (`docs/retailer-evidence.md` § 6). The
verifier raised this as WV-01; this is the note it asked for, beside the word rather than over it.

**What was not established when the row said MET AS WRITTEN.** `cli.watch_loop` advanced the pacer's
synthetic clock by the delay it asked for and never by what a cycle cost, so that clock lagged wall
clock monotonically. `due_at` lives in the synthetic clock, `refused_at` in wall clock, and
`Pacer.load` compares wall against wall — so the cool-off probe fired *later* in wall terms than the
record aged out, and REQ-22 had made the two constants deliberately equal, leaving no slack. Measured
at the live `duration_seconds: 20.43`: **17 741 s of drift per window — 4.93 h, or 6.84% of every
cool-off window**. A restart landing there dropped the entry, the retailer returned at **0 refusals**,
and had to climb the backoff and re-earn thirty consecutive refusals. `target` sat at **46 refusals**
that day, so this bound on a real retailer.

**So the honest reading of the criterion has two halves.** *"Discarded when stale by the existing rule
rather than a second one"* — **MET AS WRITTEN**, unaffected, and it always was: there is one rule, and
`grep -c '<= STATE_MAX_AGE_SECONDS:'` is still 2. *"The cool-off survives a restart"* — **was MET only
outside a 6.84% window** on 2026-08-28, and is **MET now**, at a residual re-measured over 200 seeds
as mean 151 s (0.06%) / worst 346 s (0.13%), bounded by one cycle and no longer a function of cycle
duration. Fixed at the cause in `boty/cli.py` (`9ea42fe`); `LONGEST_WAIT_SECONDS` is deliberately
UNCHANGED, because the drift was a defect in the clock and not a property of the policy.

**Why this is MET IN PART and not simply MET.** The criterion is met in the tree today. But this
phase's closing record asserted it while it was false, and the qualification that matters to a future
reader is that *the assertion was not wrong about the test — it was wrong about production*. The
restart test 08-03 wrote was valid and still passes; what no test covered was the clock the test's
`now` argument stands in for. That gap is the finding, and rounding the row back up to MET AS WRITTEN
would delete it.

**Criterion 5's dependency was checked rather than assumed.** The verdict above is derived from
reading `08-03-SUMMARY.md`, not from the fact that `08-03` was planned to close the gap. It did:
§ *The recorded one-wave gap is CLOSED* states it in the terms `08-02` opened it, and the two-hunk
production diff (`+LONGEST_WAIT_SECONDS`, `-/+STATE_MAX_AGE_SECONDS`) is quoted there. Had the window
not been re-derived, this row would read **NOT MET**.

---

## Complete in the tree. NOT deployed.

Three different claims in this repository, and this SUMMARY makes exactly one of them:

- **Complete in the tree — YES.** All four plans have SUMMARYs, all six criteria carry a verdict, and
  `make verify-offline` exits 0 on this working tree.
- **Running on the daemon — NO.** `boty` is an **editable install**: the systemd unit runs this
  working tree's venv, so the daemon picks a code change up **only on a restart**. No restart was
  performed by any plan in this phase. **A restart is Dan's call and is not a phase deliverable.**
  Until one happens, the running daemon is executing the pre-phase rule.
- **Tagged / published — NOT CLAIMED, and out of scope.** This phase creates no tag and publishes
  nothing.

The irony `08-03` noted stands: this phase proves a restart is survivable **by test**, and never by
performing one.

## Nothing live was touched

No live retailer request was made by any task. **`boty check` was not run.** `make verify` — the
unqualified target with live controls — was deliberately not run. `state.json`, `pacer-state.json`
and `served/boty/status.json` were **neither read nor written** — the mutation harness copies the tree
into a throwaway sandbox by design, and `git status --porcelain` shows no modification to any of the
three. **No `systemctl restart boty`.**

## The scope fence

`git diff --name-only b5746fa..HEAD` — exactly the two paths in `files_modified`:

```
.planning/phases/08-stop-knocking/08-DECISIONS.md
scripts/mutation_check.py
```

`git diff --name-only -- boty served` prints **nothing — zero lines**. The plan closes a gate; it did
not move the code the gate is on.

**Not touched:** `boty/pacing.py`, `boty/monitor.py`, `boty/status.py`, `boty/cli.py`,
`served/boty/index.html`, every test module, `.planning/ROADMAP.md`, `.planning/STATE.md`. Inside
`scripts/mutation_check.py`, no `search` and no `replace` of any existing ident was altered — the M33,
M38 and M12 edits are **comments and one `breaks` string**, which is why the ratio and every kill-set
count are byte-identical across them.

---

## Deviations from Plan

**1. [Rule 1 — the plan's own argument was wrong, and the registry now says the weaker true thing] M38 does NOT remove the cool-off as collateral**

- **Found during:** Task 1, step 3(c).
- **Issue:** `08-04-PLAN.md` § *What it defends* claim 1 asserts that M33 **and** M38 both take the
  cool-off down as collateral, and instructs that if either preserves it, *"claim 1 is weaker than
  this plan states and M42's comment block must say the weaker true thing."*
- **Measured:** M38's `replace` carries the cool-off arm through **verbatim**. `08-02` chose it that
  way deliberately and M38's own block says so.
- **Fix:** M42's comment block states claim 1 in the half-true form — one existing ident takes the
  cool-off down, and it destroys the accessor around it while doing so.
- **Files modified:** `scripts/mutation_check.py`. **Commit:** `68ddda4`.

**2. [Rule 1 — a stronger contradiction than the plan anticipated] M42's kill set is a PROPER SUBSET of M33's, so M42 closes no hole in the suite**

- **Found during:** Task 1, step 6, on a measurement the plan did not ask for and that the
  raise-the-denominator prohibition required.
- **Issue:** All 14 of M42's killers also kill M33. So a real deletion of the cool-off comparison
  would already be caught whether or not M42 existed. Under `CLAUDE.md`'s rule — *register an ident
  only when it defends something new* — this is the question of whether M42 should exist at all, not
  a footnote.
- **Fix:** M42 is kept on **localisation** alone, and its comment block says so explicitly, names the
  subset relation, and states that the honest remedy for a reader who judges localisation
  insufficient is to **delete M42** rather than reword the paragraph. The plan's stronger sentence was
  not left standing.
- **Files modified:** `scripts/mutation_check.py`. **Commit:** `68ddda4`.

**3. [Rule 1 — a near-miss on this repository's one unforgivable rule, caught before commit] A kill-set count was written before it was measured**

- While drafting M42's comment block I typed *"12 test(s) failed"* into the kill-set paragraph
  **before running anything** — the precise move `08-02` § *Deviation 5* caught itself making, in the
  same file, eight days earlier.
- Caught immediately, replaced with `PENDING-MEASUREMENT`, and filled in only after the harness
  printed the real figure: **14**, not 12. **Nothing wrong was committed.** Recorded because a
  near-miss on the rule that matters most here is worth more than a clean-looking silence — and
  because it has now happened twice in this file, which suggests the failure mode is the *shape* of a
  comment block that has a number-shaped hole in it.

**4. [Plan inaccuracy, corrected by reading] Step 8(a) names the wrong idents for `08-03`'s kill-set hand-off**

- The plan asks for **M12's and M13's** counts. `08-03` handed forward **M33's (21 → 26) and M38's
  (1 → 2)**, plus M38's now-false thinness sentence. M12's and M13's blocks record **no count at
  all**, so there was nothing there to have gone stale.
- **Both** sets were dealt with — M33 and M38 edited with dated notes, M12/M13/M16 measured and
  recorded with the reason no edit is owed — so the hand-off closed regardless of which idents the
  plan meant.

**5. [Plan inaccuracy, carried in from `08-03-PLAN.md` and corrected for the second time] `read_first` calls M13 "the paging-memory guard's twin"; it is M16**

- `08-03` found and corrected this and the correction did not reach `08-04-PLAN.md`'s text. M12
  anchors the refusal-count guard line, **M16** anchors the paging-memory guard line, M13 anchors
  `return restored`. All three CAUGHT — 4, 5, 2 — so nothing was missed. Recorded again because a
  correction that does not propagate into the next plan is a correction that has to be made twice.

**6. [Recorded, deliberately NOT fixed — still open, and NOT evaporated] `record`'s log line still renders `~4320 min`**

- **Measured on this tree**, not carried over: driving a `Pacer` to 30 refusals at a 300 s standing
  interval logs

  ```
  walmart refused us (30 in a row) — next attempt in ~4320 min, not 5
  ```

  while `skipped_reason` one method over reports `cooling off after 30 refusal(s) — next attempt in
  ~3.0 days`. The same units-that-hide-the-meaning problem `08-02` fixed in `skipped_reason` and left
  in `record`; `08-03` carried it forward rather than let it disappear between waves.
- **The measured reason no edit is owed here:** `boty/pacing.py` is not in this plan's
  `files_modified`, and this plan's acceptance criteria assert that `git diff --name-only -- boty
  served` prints **nothing**. Fixing it would break the scope fence that criterion 6's whole record
  rests on — the same trade `08-01` refused when it found the stale `REFUSALS_BEFORE_PAGING` comment.
- **It is therefore still open, and it is now three waves old.** It is a log line and not the
  published page, so nothing a reader of the dashboard sees is wrong. **It is not handed to a later
  phase by this document** — Phase 8 ends here — so it is written down as an outstanding defect
  against `boty/pacing.py`, in one sentence a future reader can act on: *`record`'s warning renders a
  cool-off wait in minutes, where `skipped_reason` renders the same wait in days.*

**Total deviations:** 2 findings that made the registry's own prose weaker and truer, 1 self-caught
near-miss with nothing wrong committed, 2 plan inaccuracies corrected by reading, 1 measured
hand-off recorded as still open.
**Impact:** none on behaviour — no production code moved. Two of the six made the record *less*
flattering than the plan wrote it, which is the direction this repository's evidence standard points.

---

## What a green run does NOT mean

- **It does not say the retailers still work.** The verdict was the OFFLINE pass; no live control ran.
- **It does not say the cool-off is in force.** The daemon runs this working tree's venv and picks a
  change up only on a restart, which nobody performed.
- **It does not say M42 made the suite stronger.** M42's kill set is a subset of M33's. It made the
  *registry* more legible, and that claim is the one being made.
- **It does not say the `_age`/`fmtDur` mirror is safe.** It is measured unpinned and deliberately
  left that way, with no ident, for a stated reason.

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
| `68ddda4` | `test(08-04): gate the cool-off branch, and say what the gate does not buy` — Task 1 |
| `e3b286f` | `docs(08-04): decide collision B against four measured strings, not an intuition` — Task 2 |

Task 3 writes no source file; it runs the gates and records their numbers here.

Git identity checked **before** committing: `3347065+danieljamesjohnson@users.noreply.github.com`,
the repo's configured no-reply identity. The tracked pre-commit hook ran and passed on both commits
(`PASS — 1 file(s)` each). **No commit used `--no-verify`.**

## Self-Check: PASSED

- `.planning/phases/08-stop-knocking/08-04-SUMMARY.md` — FOUND (this file).
- `scripts/mutation_check.py` — FOUND. `grep -c 'ident="M'` = **38**; `grep -c 'ident="M42"'` = **1**;
  `grep -c "INTENTIONAL GAP"` = **8**. `MUTATIONS` loaded and read: **38 idents, M21–M24 absent, last
  ident M42** — asserted by loading the registry, not by a grep a comment could satisfy.
- `.planning/phases/08-stop-knocking/08-DECISIONS.md` — FOUND. `grep -c "^## "` = **7**, unchanged
  from `08-01`'s pinned count.
- Commit `68ddda4` — FOUND in `git log`. Commit `e3b286f` — FOUND in `git log`.
- `.venv/bin/python scripts/mutation_check.py` → **38/38 caught, exit 0**, no `SURVIVED`, no
  `HARNESS ERROR`.
- M42 anchor uniqueness — Python fixed-substring count over `boty/pacing.py`: **1**.
- M42 surgical — in-memory application leaves `return max(\n            st.interval,` present, the
  `MAX_BACKOFF_SECONDS` clamp present, `skipped_reason` **byte-unchanged**, and `ast.parse` succeeds.
- `make verify-offline` → **exit 0**,
  `VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)`.
- `.venv/bin/python -m pytest tests/ -q -rs` inside the gate → **916 passed**, zero skips;
  `tests/test_dashboard.py` proved binding by 916 − 895 = 21.
- `.venv/bin/python scripts/identity_check.py --all` → `identity check: PASS — 241 file(s), no host
  identity found`, exit 0.
- `git diff --name-only -- boty served` → **empty**.
</content>
</invoke>
