---
phase: 06-claims-with-gates-under-them
plan: 06
subsystem: closing-record
tags: [req-17, req-18, req-19, req-20, closing-record, mutation-idents, ident-gap, leaked-markup, reversal, no-code]

requires:
  - phase: 06-claims-with-gates-under-them
    plan: 01
    provides: "the delivered-total ceiling, the four-watch alertability table, M4's re-anchor and M17/M18"
  - phase: 06-claims-with-gates-under-them
    plan: 02
    provides: "the Rung binding across both joins, M19/M20, and the re-measured `131`"
  - phase: 06-claims-with-gates-under-them
    plan: 03
    provides: "the directory-keyed workflow rules, the exit-0-before/exit-1-after pair, and the deliberate M21-M22 gap"
  - phase: 06-claims-with-gates-under-them
    plan: 04
    provides: "the CHANGELOG contents gate, the byte-exact recovery of the shipped document, and the deliberate M23-M24 gap"
  - phase: 06-claims-with-gates-under-them
    plan: 05
    provides: "the version binding, M25/M26, and the STATE.md `milestone:` line becoming machine-read"
  - phase: 06-claims-with-gates-under-them
    plan: 07
    provides: "Dan's 2026-08-11 reversal implemented, the re-measured four-watch table, the rendered push bodies, and the REQ-17 revision block this plan applies to the record"
provides:
  - "The Phase 6 outcome table — five verdicts in Phase 4's and Phase 5's three-column shape"
  - "`docs/retailer-evidence.md` § *Phase 6 closing record* — the full working, in Phase 3.1's four-column shape"
  - "REQ-17 through REQ-20 closed with evidence-bearing traceability cells; REQ-18's two stale claims flagged and unedited"
  - "The Phase 6 `Plans:` list — seven plans, seven waves — which no earlier planner wrote"
  - "The M21-M24 ident gap recorded as deliberate in three places, with 06-03's and 06-04's own reasons quoted"
  - "The third COMMITTED instance of the REQ-19 leaked-markup class, established at close and removed"
affects: [milestone-v0.2-audit, future-leaked-markup-gate, future-deploy-plan]

tech-stack:
  added: []
  patterns:
    - "A closing record quotes the transcript it could have quoted, never summarises it — a summary of a measurement is a claim about a measurement"
    - "A criterion met only against a user's later revision is recorded MET IN PART, never rounded up"
    - "A mutation that SURVIVES is explained; a mutation that CANNOT EXIST is recorded as not existing, with the gap named"
    - "Re-measure the figure rather than repeat it, and state the difference rather than reconcile it away"

key-files:
  created:
    - .planning/phases/06-claims-with-gates-under-them/06-06-SUMMARY.md
  modified:
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
    - docs/retailer-evidence.md
    - .planning/phases/06-claims-with-gates-under-them/06-07-SUMMARY.md

key-decisions:
  - "Criterion 1 recorded MET IN PART AS WRITTEN — first half met, second half met only AS REVISED by Dan 2026-08-11 — rather than rounded up to MET"
  - "REQ-17's text NOT edited; the reversal recorded beside it in Phase 3.1's format, with the original quoted intact"
  - "REQ-18's `131` and its 'Routing and Extraction are already pinned' claim FLAGGED in two places and edited in neither"
  - "The M21-M24 gap recorded as deliberate in the ROADMAP, in STATE.md's decisions and in the closing record, each time with 06-03's and 06-04's own reasons quoted"
  - "The committed leaked markup in 06-07-SUMMARY.md was REMOVED and recorded, in its own commit, so the closing record's diff stays four files"
  - "The `gsd-tools` state verbs were deliberately NOT run — the hand-written cells carry measurements the tool would overwrite with the word 'Complete', and the tool has misfired nine consecutive times"
  - "No code was written; a criterion unmet at close is RECORDED unmet"

patterns-established:
  - "A user's reversal and an agent's rewording are kept apart in the record by the original criterion surviving verbatim beside the new sentence"
  - "Separate a defect from a document quoting the defect by applying the NARROWER rule (whole-line tag) rather than by reading the counts"

requirements-completed: [REQ-17, REQ-18, REQ-19, REQ-20]

metrics:
  duration: 42min
  tasks: 3
  files: 5
  completed: 2026-08-11
---

# Phase 6 Plan 06: Five Verdicts, And The One That Is Only Half True — Summary

**Phase 6 closed on four of five criteria MET as written and criterion 1 MET IN PART — its second
half met only against a revision Dan made on 2026-08-11, recorded with his words verbatim and
REQ-17's original sentence intact beside them — with the mutation ident gap at M21-M24 written down
as deliberate in three places, the leaked-markup sweep re-run rather than repeated, and the third
COMMITTED instance of the defect REQ-19 names found in this milestone's own documentation at the
moment of certifying its absence.**

## Performance

- **Duration:** ~42 min
- **Tasks:** 3 (one of them a checkpoint that was already answered — see below)
- **Files modified:** 5 (four record files, plus one leaked-markup removal in its own commit)
- **Code written:** none

## Commits

| Task | Commit | What |
|---|---|---|
| 1 (deviation) | `7355034` | `fix(06-06)`: the two committed tool-call tags removed from `06-07-SUMMARY.md`, recorded rather than quietly fixed |
| 3 | `54117d3` | `docs(06-06)`: the five verdicts, four requirement cells, the `Plans:` list, STATE.md, and the closing record — four files |

## Task 2 was ALREADY ANSWERED, and the card was stale

**The checkpoint was not presented, and this is the one thing in this SUMMARY that most needs its
reasoning on the record rather than only its outcome.**

06-06's plan carries a blocking checkpoint that puts the alertability cost of criterion 1 to Dan and
offers `accept` / `allowance` / `defer`. **Dan had already answered it on 2026-08-11, before this
plan ran, and he chose a fourth option none of the three offered.** Verbatim:

> *"I think where we don't know just send it. If the user gets there and it's 50 dollar shipping
> that's disappointing but it's worse to feel like you 'missed out'."*

And on the alert format, also his:

> *"Instead of 'unverified', why don't you say price: &lt;price&gt; shipping: &lt;unknown&gt;"*

**The card was also factually stale.** It names the lenient item-price rule as *"a rejection with
its reason rather than an option"* — a sentence that stopped being true the moment he chose a
variant of it. 06-07-SUMMARY had already flagged this: *"**06-06's blocking checkpoint card is now
stale**, and it was **not edited here**. It was written to ask Dan the question he has since
answered."*

**The decision was implemented and shipped as 06-07** (wave 6, `717015b`…`a71e79b`) before this
plan ran. So the checkpoint is recorded as **answered on 2026-08-11 with his words verbatim**, and
the outcome as what 06-07 landed. It was not re-asked and no notification was sent — re-presenting a
settled question as though it were open would have been its own small overclaim, in the plan that
closes a milestone about overclaiming.

**What was therefore NOT decided, stated so the record does not imply more than it has.** The
`allowance` path — a per-watch operator shipping declaration in Phase 5's `store_id` shape, required
config, no default, unset means unresolved — was **neither chosen nor rejected**. It was never put
to him, because his answer made the question it answers moot: the strict rule it would have sat on
top of is no longer the shipped rule. It stays where 06-01 left it, needing `boty/config.py`, which
this phase scoped out of every plan. **Nothing was built on any answer.**

**And criterion 1's verdict was decided by what 06-01 and 06-07 measured, not by the answer.** The
answer is a record of a cost being seen. That property was the point of the checkpoint and it
survives the checkpoint not being presented.

## The gate, offline — recorded verbatim, and the rise SHOWN

`make verify-offline`, run at close, **exit code 0**. Allowed to finish (24 sandboxes, each a
`copytree` plus `git init` plus `git add -A`); not killed, not narrowed to `make test`:

```
identity check: PASS — 199 file(s), no host identity found
All checks passed!
768 passed in 10.71s
Success: no issues found in 18 source files
mutation check: 24 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (740 passed, 28 skipped in 11.27s)
mutation check: 24/24 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

- **Verdict line:** `VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)`
- **Test count:** **768**
- **Mutation ratio:** **24/24**

**Run a SECOND time after the record was written** — because 3c and 3d both edit files that gates
now read — and it exits **0** again at **768 passed, 24/24**, `identity check: PASS — 199 file(s)`.
A closing record that reddened its own tree and committed anyway would be this milestone's defect in
its purest form.

**The rise, with every intermediate count read off the SUMMARY that took it rather than remembered:**

| Point | Tests | Mutations | Tracked files scanned |
|---|---|---|---|
| Pre-milestone (Phase 4's close) | 531 | **8/8** | 153 |
| Phase 5's close | 667 | **16/16** | 178 |
| After 06-01 | 688 | **18/18** | 190 |
| After 06-02 | 701 | **20/20** | 192 |
| After 06-03 | 711 | 20/20 — deliberately unchanged | 193 |
| After 06-04 | 737 | 20/20 — deliberately unchanged | 195 |
| After 06-05 | 759 | **22/22** | 196 |
| After 06-07 | 768 | **24/24** | 198 |
| **At close (06-06)** | **768** | **24/24** | **199** |

## The mutation idents, READ from the registry — and the deliberate gap

Read with comment lines filtered out, because `grep -c` over an unfiltered file counts comment prose
and this project has been bitten by exactly that self-invalidating class:

```
M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M13 M14 M15 M16 M17 M18 M19 M20 M25 M26 M27 M28
```

**24 idents. M21, M22, M23 and M24 are ABSENT, and the absence is DELIBERATE.** The plan expected
`M17, M18, M19, M20, M25, M26` present and 22 total; the tree has those **plus M27 and M28**, at 24,
because 06-07 landed after the plan was written. **The tree wins and the difference is recorded
rather than reconciled away.**

**The reasons, quoted from the SUMMARYs that recorded them at the time:**

- **06-03:** *"`apply_mutation` cannot add a file. It performs `before.replace(search, replace, 1)`
  on an existing file inside the sandbox. The criterion is about *a workflow file that does not
  exist yet*, so the defect it names is outside the harness's reach **by construction**, not by
  oversight."* And the alternative was worse than nothing: a workflow mutation a directory rule would
  catch *"would die against `test_the_publish_workflow_runs_on_a_pinned_image_within_a_time_limit`,
  which existed before 06-03 — it would raise the ratio while proving nothing this plan built."*
- **06-04:** *"The harness mutates `boty/`… This plan writes no production code; its deliverable
  **is** a gate over a data file. There is nothing in `boty/` for it to break."* And widening the
  sandbox to manufacture one was refused structurally: it *"would create an entry provable
  load-bearing only by the mutation that motivated it"*, failing Phase 4's own recorded rule for
  `SANDBOX_CONTENTS`.

Both state the same principle in the same words, and it is the one that belongs in the record:
**a mutation that SURVIVES is never explained away; a mutation that CANNOT EXIST is recorded as not
existing.** A reader meeting `… M20, M25 …` with no note goes looking for four deleted gates and
concludes the harness was weakened.

**Every new ident observed CAUGHT by name, from the harness's own output at close:**

```
  CAUGHT    M17 boty/models.py: 9 test(s) failed — test_a_shipping_cost_nobody_read_is_a_field_saying_so_and_no_total, test_a_refused_shipping_figure_never_reaches_a_phone, test_an_unreadable_price_uses_the_same_word_as_an_unreadable_shipping (+6 more)
  CAUGHT    M18 boty/models.py: 3 test(s) failed — test_the_delivered_total_is_the_price_plus_the_shipping, test_the_ceiling_bites_on_the_delivered_total_and_on_nothing_else, test_the_gamestop_capture_carries_its_shipping_cost_all_the_way_to_a_result
  CAUGHT    M19 boty/retailers.py: 9 test(s) failed — test_every_matrix_rung_cell_matches_the_rung_its_adapter_takes, test_an_adapter_taking_a_rung_the_readme_does_not_claim_fails, test_a_readme_rung_cell_contradicting_the_code_fails (+6 more)
  CAUGHT    M20 boty/cli.py: 8 test(s) failed — test_a_target_watch_is_dispatched_to_the_browser_and_dom_path, test_every_matrix_rung_cell_matches_the_rung_its_adapter_takes, test_a_readme_rung_cell_contradicting_the_code_fails (+5 more)
  CAUGHT    M25 pyproject.toml: 1 test(s) failed — test_the_readme_publication_instruction_names_the_declared_version
  CAUGHT    M26 README.md: 1 test(s) failed — test_the_readme_publication_instruction_names_the_declared_version
  CAUGHT    M27 boty/models.py: 4 test(s) failed — test_an_unresolved_shipping_cost_under_a_ceiling_is_alertable, test_a_negative_shipping_cost_never_lowers_a_delivered_total, test_a_number_in_a_field_never_observed_carrying_one_is_not_a_shipping_cost (+1 more)
  CAUGHT    M28 boty/models.py: 4 test(s) failed — test_an_item_price_over_the_ceiling_is_not_alertable_when_shipping_is_unknown, test_run_once_does_not_alert_above_the_price_ceiling, test_bestbuy_price_ceiling_still_bites_on_the_browser_rung (+1 more)
```

M4 is also in the run at `2 test(s) failed`, on the **narrowed** subject 06-07 gave it — it guarded
the claim that an unestablished *delivered total* cannot clear the ceiling, that claim is no longer
true, and its comment block says so with the date. **M17 is the one to read:** it pinned the
item-price fallback as **REJECTED**, Dan chose a version of it, and it was **re-pointed rather than
deleted**, because deleting a mutation to make a suite green is forbidden in this repository and
deletion was the easy move here.

## The four-watch alertability table, and Dan's answer

Quoted from 06-07-SUMMARY, which re-measured 06-01's table against the built tree at `b9e39bc`,
offline, by driving each shipped capture through its real adapter with `retailers.get`
monkeypatched. **No retailer was probed to obtain it.** Exactly four watches carry a `max_price`,
all four are the GO Plus + product watch, and every control carries none — re-confirmed at close.

| GO Plus + watch | Delivered total establishable? | Under 06-01's strict rule | **NOW, after the reversal** |
|---|---|---|---|
| **GameStop** | **Yes** — `shipping=6.99`; `54.99 + 6.99 = 61.98`, under 80 | **YES** | **YES** — on the **delivered total**, unchanged |
| **Walmart** | **Shape-dependent** — its only first-party capture resolves none (`speedDetails: null`) | **NOT DEMONSTRATED** | **YES** — on the **item price** |
| **Nintendo** | **No** — `shippingDetails` is prose | **NO — stopped being alertable** | **YES** — on the **item price** |
| **Amazon** | **No** — the reader is an add-to-cart button | **NO — stopped being alertable** | **YES** — on the **item price** |

**Dan's answer, verbatim, 2026-08-11**, and it is a fourth option none of the three on the card
offered:

> *"I think where we don't know just send it. If the user gets there and it's 50 dollar shipping
> that's disappointing but it's worse to feel like you 'missed out'."*

> *"Instead of 'unverified', why don't you say price: &lt;price&gt; shipping: &lt;unknown&gt;"*

**Say it plainly: this reopens the hole REQ-17 was written to close.** A $54.99 listing with $45 of
shipping the page does not publish readably now pages Dan, and the push will not warn him about the
$45 — it will show him an empty field. **What still stands:** a *resolvable* total above the ceiling
is still suppressed, an item price above the ceiling is still refused even when shipping is unknown,
an unreadable price is still refused in both branches, the seller filter is untouched, and **no
`Availability` verdict moved**.

**And the sentence that keeps the two kinds of reversal apart: 06-01's measurements were all right,
and only the conclusion drawn from them changed.** Not one was re-taken, softened or re-interpreted,
and the change was made by the person the tool pages.

## The gate, live — run ONCE, recorded verbatim including its FAIL

Started only after checking `served/boty/status.json` so a daemon cycle and this pass were not in
flight against the same six retailers at once: the daemon published at **2026-08-11T14:20:41Z** with
`duration_seconds: 43.4`, and `make verify` was started immediately after. Run **once**, not re-run
for a better answer, and deliberately **not** run under the service's `EnvironmentFile` — 05-04's
recorded departure from Phase 3.1's method, whose reason still binds.

```
control check: 6 control(s), live
  in_stock      gamestop  CONTROL — PS5 console                $549.99  ld+json: InStock from GameStop
  unknown       walmart   CONTROL — Great Value whole milk           —  no store_id pinned for this watch — set store_id in config/products.ya
  unknown       bestbuy   CONTROL — Pokémon Let's Go, Pikach         —  fetch failed: no Chrome/Chromium binary found — set BOTY_BROWSER_PATH
  in_stock      nintendo  CONTROL — Nintendo HDMI cable          $7.99  ld+json: InStock from Nintendo of America Inc.
  unknown       target    CONTROL — up&up microfiber dust cl         —  fetch failed: no Chrome/Chromium binary found — set BOTY_BROWSER_PATH
  in_stock      amazon    CONTROL — Amazon Basics AA batteri     $9.99  add-to-cart control: add-to-cart enabled from Amazon.com

control check: 2/6 control(s) could not run on THIS HOST
control check: FAIL — 1/6 control(s) not reading IN_STOCK
VERIFY: FAIL (live controls)
```

Exit **2**. **Three classes, and NOT ONE of them is this phase's:**

1. **Pre-existing since 2026-08-06.** `2/6 control(s) could not run on THIS HOST` — Best Buy and
   Target, `no Chrome/Chromium binary found`. `control_check.py`'s own output says this "says
   nothing about the DETECTOR". `BOTY_BROWSER_PATH` was deliberately not set: this run is a
   measurement, not an attempt to improve the number.
2. **Pre-existing, and it did NOT manifest again.** The Walmart/Amazon challenge class was absent on
   2026-08-10 and is absent here — Amazon read IN_STOCK at $9.99 and Walmart served a judgeable
   page. **Two consecutive passes now support "intermittent" rather than "permanent"**, which is
   more than the one pass Phase 5 had, and still short of establishing it.
3. **Phase 5's, and correct.** `FAIL — 1/6 control(s) not reading IN_STOCK` is Walmart reading
   UNKNOWN through 05-02's config-gap guard, because `make verify` runs in a shell with no
   `WALMART_STORE_ID`. That is criterion 2 executing in production conditions.

**Nothing new appeared, and that is a prediction CONFIRMED rather than an absence assumed.** 06-01's
F1 measured that every `max_price` in `config/products.yaml` sits on a GO Plus + product watch and
every control carries none, so `alertable` short-circuits at the watch level before any ceiling rule
is consulted. Re-counted at close: **exactly four `max_price: 80` entries and no others.** No
control's verdict could move under criterion 1 in either its strict or its reversed form, and none
did. **The mutation stage does not run inside a failing live invocation** — `make verify` exits at
the control stage — so mutations are evidenced by `make verify-offline` and never by this run.

## The leaked-markup sweep, RE-RUN at close

**Pattern used**, five shapes, named rather than reproduced: the closing `invoke` and `content`
tags, the opening `function_calls` tag, the `parameter` tag prefix, and the agent namespace prefix.

```
MEASURED: 21 matching lines in 7 files
    .planning/phases/04-open-source-ready/04-REVIEW.md                  3
    .planning/phases/06-claims-with-gates-under-them/06-04-SUMMARY.md   6
    .planning/phases/06-claims-with-gates-under-them/06-07-SUMMARY.md   2
    .planning/phases/06-claims-with-gates-under-them/06-CONTEXT.md      1
    .planning/phases/06-claims-with-gates-under-them/06-PATTERNS.md     3
    .planning/seeds/nothing-reads-the-changelog-body.md                 2
    tests/test_changelog.py                                             4
```

**Against the outline's 9-in-4, with the difference STATED rather than reconciled away.** The
outline's four files are **unchanged at exactly 9 lines** — 04-REVIEW 3, seeds 2, 06-CONTEXT 1,
06-PATTERNS 3. Twelve lines are new, and **ten of them are deliberate**:
`tests/test_changelog.py` (4) *must* carry the shapes it forbids or it could not forbid them —
06-04 made that argument executable rather than promising it — and `06-04-SUMMARY.md` (6) quotes its
own failure output. **The remaining two are a real hit**, and they are the finding below. The
pattern was **not adjusted until the number matched a remembered one**.

## THE FINDING THIS CLOSE PRODUCED: the third committed instance

**06-06's plan states that a third *committed* instance of the REQ-19 defect "is not established by
the tree". Measured at close, it is.**

Applying **06-04's own shape (a)** — a line whose *entire* content is a tool-call tag, the shape
that shipped in `CHANGELOG.md` — separates a defect from a document quoting one:

```
SHAPE (a) whole-line tool-call tag: 6 line(s) in 3 file(s)
   .planning/phases/04-open-source-ready/04-REVIEW.md:113-114     (inside a fence, quoting the incident)
   .planning/seeds/nothing-reads-the-changelog-body.md:15-16      (indented block, quoting the incident)
   .planning/phases/06-.../06-07-SUMMARY.md:416-417               <-- AT END OF FILE, the defect itself
```

`06-07-SUMMARY.md` was committed at **`a71e79b`** ending, at the byte level, with its closing
`*Completed: 2026-08-11*` line followed by two whole-line agent tool-call closing tags and nothing
else. Not inside a fence, introduced by no prose, after the file was otherwise complete. **That is
byte-shape for byte-shape the incident 06-04 built its gate for, in the plan that reversed REQ-17,
one day after the gate landed.**

**Removed at `7355034` and recorded rather than quietly fixed**, on 06-04's and 06-05's own
precedent, in its own commit so the closing record's diff stays four files. The evidence is
permanent at `a71e79b` and the record cites it there.

**The three instances, each with its own evidence:**

| Instance | Evidence | Committed? |
|---|---|---|
| `05-02-PLAN.md` | caught by a planning agent **before commit** (`06-CONTEXT.md` § *Specific Ideas*) | **No — a near-miss.** It leaves no trace in the tree, so the evidence is the note, not a sweep hit |
| `06-PATTERNS.md` | became a hit **in the act of measuring the sweep** (`06-PLAN-OUTLINE.md` § *Finding 3*) | **Yes**, 3 lines |
| `06-07-SUMMARY.md` | `a71e79b`, two whole-line tags at EOF | **Yes**, 2 lines — removed at `7355034` |

**06-04 § F4's counter-measurement is kept rather than smoothed over**, because it is true and it is
the useful half: *"`06-01-PLAN.md`, `06-02-PLAN.md` and `06-03-PLAN.md` were written since that
measurement and none became a hit."* The discipline of naming the tag shapes without reproducing
them worked, and it held for every document written *about* the gate. It failed on a document
written *by* a tool at the end of a long plan — a different failure mode needing a different
control.

**Nothing in this repository's gates would have caught any of it**, and that is the finding rather
than the count. `leaked_markup` is deliberately scoped to `CHANGELOG.md` (06-04 argued that scope
from a measurement), `.planning/` is covered by no contents rule at all, and
`scripts/identity_check.py` scans for host identity. **Three candidates of this shape are now logged
and unbuilt:** invisible characters (06-04), leaked markup outside `CHANGELOG.md` (06-05), and this
instance — which is the one that turns the class from a near-miss into a hit.

*(This SUMMARY and the closing record both name the shapes without reproducing them, and it was
verified by command rather than by eye: **0 hits** across all four record files and this one.)*

## The five verdicts, as written into the ROADMAP

Reproduced here so the SUMMARY and the ROADMAP can be diffed against each other.

**Outcome, recorded 2026-08-11 by 06-06 — four of five MET as written; criterion 1 MET IN PART as
written, its second half REVISED by Dan on 2026-08-11 and met as revised.**

| # | Verdict | The short form of the measurement or reason |
|---|---|---|
| 1 | **MET IN PART AS WRITTEN — first half MET, second half REVISED BY DAN 2026-08-11 and MET AS REVISED** | Met as written: the ceiling measures the delivered total wherever shipping can be read (`54.99 + 6.99 = 61.980000000000004`), a resolvable total over the ceiling is still suppressed, nothing is guessed, `Availability` untouched. Revised: an unresolvable cost now falls back to the item price and the alert goes out reading `shipping: unknown`, so the hole REQ-17's second sentence names is **reopened knowingly by the user** |
| 2 | **MET** | Re-measured before the gate existed at **exit 0, `687 passed, 1 skipped`**; both joins bound statically by AST, two-directionally; `CAUGHT M19` by nine tests all of them the new gate, `CAUGHT M20` by eight, one pre-existing. The code side was **new construction**, not a copy |
| 3 | **MET** | The criterion **executed**: `exit 0, 701 passed` before the gate, `exit 1, 2 failed, 709 passed` on the same file and command after, naming all four families. Three rules wrapped not rewritten; zero test names removed (67 → 77) |
| 4 | **MET** | The Phase 4 document recovered **byte-for-byte from `2ac965f^`**: `exit 0, 711 passed` before, `exit 1, 2 failed, 735 passed` on identical bytes after. Prohibitions paired with presence rules; not met by a skip line (`7 passed, 19 skipped` inside a real sandbox) |
| 5 | **MET** | The gate written **first** against a tree that disagreed with itself: `exit 1, 2 failed, 757 passed` (commit subject: `TREE IS DELIBERATELY RED`), `exit 0, 759 passed` after the roll. Four safety facts re-measured at execution; `CAUGHT M25`/`M26`, the first mutations outside `boty/` |

**No criterion text anywhere was reworded, shortened, merged or amended**, and it is asserted rather
than promised. Both controls in this plan's `<verify>` block were run and their exit codes honoured:

```
baseline: HEAD | criterion lines at baseline: 40 | now: 40
PASS — every criterion verbatim; additions: 0

PASS — Phase 5 closing table byte-identical to HEAD  (4248 bytes, 8 lines)
```

The first extracts every criterion body from the baseline and the working copy with the leading
numeral stripped and **exits non-zero naming any that no longer appears verbatim**; the second
slices Phase 5's eight-line closing table out of both and asserts byte-identity. **This phase's own
subject is gates that can go red, and the gate over its hardest constraint is one of them.**

## Every correction from waves 1-7, quoted from the SUMMARY that made it

- **`06-CONTEXT.md` was wrong twice, and both are drafting errors rather than withdrawn decisions** —
  it was auto-generated under `workflow.skip_discuss`, so nobody chose either sentence.
  (i) It claims `tests/test_support_matrix.py` *"already binds the README's Routing and Extraction
  cells to the code in both directions"*. Measured: *"`_extraction_mismatch` binds the README's
  Extraction cell to the README's **Rung cell**. Both of its directions are *inside the table*…
  There was **no README-cell → code binding of any kind** anywhere in `tests/`."* **The code side was
  new construction in 06-02.** (ii) It frames unresolvable shipping as the edge case; on Walmart it
  is the **common path**, and *"no payload this repo has ever captured shows Walmart's paid
  marketplace shipping shape."*
- **REQ-18's own text carries the same stale claim** — *"Routing and Extraction are already pinned;
  Rung is the gap"* — **flagged in two places and edited in neither**, on 06-02's rule: *"a criterion
  is never amended to make it meetable; the same rule points the other way — it is not amended to
  make it *accurate* either."* Its stale **`131`** was re-measured at **exit 0, `687 passed, 1
  skipped`** and recorded beside the criterion as a measurement note.
- **06-01's two near-inventions**, both the same class as 05-01's rejected `"0"` sentinel: a regex
  over Nintendo's prose *"produces a delivered total of **$61.98 for an item that ships free**"*, and
  Walmart's real `7.95` delivery fee, which *"would have **invented a $7.95 shipping charge out of a
  real field**. It is read nowhere."*
- **The outline's Walmart free-shipping rule resolves ONE fixture, not two** — `goplusplus` → `0.0`,
  `milk-control` unresolved — *"which is the correct fail-safe answer and costs nothing because milk
  carries no ceiling."* One refinement in the same direction: the agreeing key is absent on
  `milk-control` *"because its container is"* (`speedDetails` is `null`).
- **06-03 proved the workflow gap by EXECUTING it:** *"Seven hundred and one tests watched a
  deliberately non-compliant workflow arrive in the one directory in this repository that runs on
  somebody else's computer holding this repository's token, and not one of them said anything."*
- **`_flattened_exit_codes` does not exist; the rule is `_flattening`.** Two planning documents say
  otherwise and neither was edited. **The trap 06-03 warned of is now literally in the tree:** the
  wrapper is `_directory_flattened_exit_codes`, so grepping the remembered name returns three real
  hits and no definition of the rule.
- **06-04's sandbox run found a real defect rather than confirming a premise:** an "unconditional"
  fixture citing `CHANGELOG.md` *"is coupled to `SANDBOX_CONTENTS` while looking as though it is
  not"*, and *"the test whose entire job is to run where `CHANGELOG.md` does not exist **failed in
  the one place it was written for**."* Fixed in `MINIMAL`, **not** by widening the sandbox.
- **06-05 found the outline's pairing would have left BOTH rules skipping** under `make mutation` —
  *"the exact defect a pairing exists to prevent"* — re-confirmed by building a sandbox and stat-ing
  it (`CHANGELOG.md in sandbox: False`). Re-anchored on `README.md`. Its sharper sibling finding:
  the pairing pin **goes blind rather than red** when a rule is renamed out of the discovery
  convention — *"the pin itself **went quiet**"*.
- **`README.md` was cut 503 → 190 (`d6d16fe`) → 183 (`8b205fe`) after the plans were written**,
  standing at **189** at close after 06-07's one honest ceiling paragraph. Measured with
  `git show <ref>:README.md | wc -l`, not repeated from the commit subjects. Two of the three README
  paragraphs 06-07's plan targets no longer existed, and 06-07 *"followed the tree. Nothing was
  restored to make the plan's line numbers true."*
- **06-01 corrected its own plan on Walmart**, and the correction was load-bearing for what went to
  Dan: *"Claiming 'yes' would be the same unmeasured assertion this milestone exists to close."*

## What this phase did NOT establish

1. **Not one of these five gates is running on the deployed daemon.** `boty.service` has published
   2026-08-04 code since before Phase 4 and no plan in this phase restarted it. Everything above is
   a property of the tree.
2. **Walmart's paid-marketplace shipping shape remains UNOBSERVED**, so criterion 1's central case is
   **guarded by a refusal rather than demonstrated against a capture**. That gap is exactly why the
   lenient fallback was rejected as a *design* in 06-01 — *"publishes nothing"* and *"publishes
   something we did not read"* are indistinguishable on the one retailer that carries marketplace
   sellers. Dan then chose that fallback anyway, and **the gap it rests on has not closed because
   the decision changed.**
3. **The live `make verify` failure classes are recorded, not diagnosed.** None was fixed, and the
   run was not repeated.
4. **No retailer was probed and no fixture re-captured.** Every gate was watched going red offline.
5. **Criterion 2's binding is STATIC** — it asserts what the source *says*, not what *runs*. The cost
   is written into the module docstring rather than buried.
6. **`deploy/boty-secret` still has no store subcommand, `_identity_leaks` still exists twice and has
   drifted, and `QUESTIONS.md` § 0e and § 0f are both still open and untouched.**
7. **`scripts/mutation_check.py`'s module docstring still says "three mutations"** against a registry
   of 24 (`D-06-01-a`). Pre-existing drift, deliberately not fixed here — but it is exactly this
   milestone's subject, and the count has now drifted **seven** times unnoticed.
8. **The `allowance` option was neither chosen nor rejected** — see Task 2 above.

## Deviations from Plan

### 1. [Rule 1 — bug, and the finding of this plan] Committed leaked markup in `06-07-SUMMARY.md`

- **Found during:** Task 1e, the sweep.
- **Issue:** `06-07-SUMMARY.md` was committed at `a71e79b` ending in two whole-line agent tool-call
  tags — the exact defect class REQ-19 names, in this milestone's own documentation, one day after
  06-04's gate landed. No gate this repository ships covers it, and **no later plan would have caught
  it**, because this is the last plan in the phase.
- **Fix:** the two lines removed, in **its own commit** (`7355034`) so the closing record's diff
  stays four files, and recorded in this SUMMARY, in STATE.md and in the closing record with the
  pre-fix bytes quoted and `a71e79b` named as where the evidence lives permanently.
- **Files modified:** `.planning/phases/06-claims-with-gates-under-them/06-07-SUMMARY.md`.
- **Verification:** shape (a) sweep now returns 4 lines in 2 files, both deliberate quotations;
  `make verify-offline` exit 0 afterwards.

### 2. [Measurement corrects the plan] The mutation total is 24, not the expected 22

The plan expected `M17, M18, M19, M20, M25, M26` and **22 total**. The tree carries **24** — M27 and
M28 were added by 06-07, which was inserted after 06-06's plan was written. **The tree wins**, and
the expectation is recorded beside the measurement rather than replaced by it. The M21-M24 gap is
unchanged and still deliberate.

### 3. [Measurement corrects the plan] The four-watch table is 06-07's, not 06-01's

The plan's expected table has Nintendo and Amazon losing alertability and Walmart at *"yes, same
condition"*. **06-01 measured Walmart as "not demonstrated"**, correcting its own plan, and **06-07
then moved all four watches to YES.** Both tables are carried above with the transition shown,
because the strict rule's cost is what justified the reversal and dropping it would leave the
decision looking unmotivated.

### 4. [Plan superseded by the user] Task 2's checkpoint was not presented

Recorded in full above. Answered 2026-08-11, implemented as 06-07 before this plan ran, card
factually stale. Not re-asked, no notification sent, nothing built.

### 5. [Rule 3 — blocking] The `gsd-tools` state verbs were deliberately not run

STATE.md records nine consecutive misfires of `state advance-plan`, with a cause that is unfixable
in place (it reads `Plan: 6 of 6 complete` out of the archived v1.0.0 block, which is kept verbatim).
`record-metric` echoes a populated object and writes no row; `add-decision` prefixes every entry
`[Phase ?]`; `roadmap update-plan-progress` returned `{"complete": false}` at 06-04 and left the
progress line untouched. Running them here would have overwritten four evidence-bearing traceability
cells with the word `Complete` and re-broken the frontmatter this plan had just corrected. **Every
field was written by hand**, which is what every plan in Phases 5 and 6 has had to do, and the
`milestone:` line — now machine-read — was left untouched and re-verified green.

---

**Total deviations:** 5 (1 auto-fixed bug, 2 measurement corrections, 1 plan superseded by the user,
1 blocking tooling). **No scope creep:** the one edit outside the four record files is the removal of
a committed defect this phase's own subject demands be recorded.

## Known Stubs

None. Nothing is placeholdered, deferred out of this plan's scope without being named, or written as
a status line where a measurement was available. Pre-existing `D-06-01-a` is untouched and still out
of scope.

## Threat Flags

None. No code, no new network endpoint, auth path, file access pattern or schema change at a trust
boundary. No fixture captured or edited; no store number, postal code or host identity handled
anywhere. `scripts/identity_check.py --all` passed over all **199** tracked files after the record
was written and before the commit, and again inside `make verify-offline`.

Every `mitigate` disposition in this plan's threat register was applied. **T-06-60** (the record
itself is a claim): every row carries a measurement or a reason, transcripts quoted from the
SUMMARYs, idents read with comments filtered, the live FAIL verbatim, unmet recorded unmet, stale
figures re-measured, `verify-offline` re-run after the record. **T-06-61** (a criterion quietly
reworded): both extract-and-compare controls run and honoured — 40 criterion lines at baseline and
40 now, Phase 5's table byte-identical. **T-06-62** (a cost absorbed rather than shown): Dan saw the
measured table and answered in his own words, quoted verbatim in four places. **T-06-63** (reddening
a gate this phase built): `milestone: v0.2` untouched, `tests/test_packaging_metadata.py` re-run
green immediately after the STATE.md edit (**41 passed**), `make verify-offline` re-run green after
the record. **T-06-64** (becoming the next hit): shapes named, never reproduced; **0 hits** across
all five files, verified by command. **T-06-65** (six retailers): offline first, live pass started
after a published daemon cycle, run once. **T-06-66** (writing code to make a row read MET): none
written. **T-06-67** (four idents read as lost): the gap recorded in three places with both plans'
reasons quoted. **T-06-SC** did not arise — nothing was installed.

## Self-Check: PASSED

- `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`,
  `docs/retailer-evidence.md`,
  `.planning/phases/06-claims-with-gates-under-them/06-07-SUMMARY.md` — all present and modified.
- `.planning/phases/06-claims-with-gates-under-them/06-06-SUMMARY.md` — present.
- Commits `7355034` and `54117d3` — both found in `git log`.
- `grep -c 'Phase 6 closing record' docs/retailer-evidence.md` → **1**.
- `grep -c '^milestone: v0.2$' .planning/STATE.md` → **1** (unchanged).
- `.venv/bin/python -m pytest tests/test_packaging_metadata.py -q` → **41 passed**, after the edit.
- `.venv/bin/python scripts/identity_check.py --all` → PASS, 199 files, after the record was written.
- `make verify-offline` → exit **0**, 768 passed, 24/24 — before the record was written, again
  after it (199 tracked files), and once more on the fully committed tree including this SUMMARY
  (**200 tracked files**, `identity check: PASS`). Three runs, three exit zeros.
- Criterion-text control → 40 at baseline, 40 now, zero moved. Phase 5 table → byte-identical.

---
*Phase: 06-claims-with-gates-under-them*
*Completed: 2026-08-11*
