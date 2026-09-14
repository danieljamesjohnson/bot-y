# 11-02 — SUMMARY

**Landed 2026-09-14.** Criteria 1 (completion), 3, 4, 5. **Live requests made: 0.**

---

## Rule 7, and the allowance it reverses

`11-01` needed somewhere to write Walmart's verdict and there was nowhere. `grep -n "^## "
docs/retailer-evidence.md` returned five retailer sections out of seven; **GameStop and Walmart —
both configured, both control-verified, both advertised in `README.md` as ✅ Working — had none.**

**It was not an oversight.** `scripts/evidence_check.py` rule 5's comment block named both
retailers and argued for letting them be: *"Demanding one here would redden the shipped tree over a
gap that is not a lie."* `tests/test_evidence_check.py` pinned it in a test literally named
`…_is_deliberately_clean`.

**Reversed, with the three reasons written into the script beside the original argument:** its
stated cost (reddening the tree) stops existing once the sections are written; phase 11's criterion
1 *requires* Walmart's verdict and a requirement to fill a gap outranks a rule saying it need not
be; and *"a tree cannot contradict a claim nobody made"* was true of rule 5's subject and false of
the tree — the README made the claim the whole time.

**THE OLD TEST'S OBJECTION IS THE SERIOUS ONE AND IT IS ANSWERED BY WHAT WAS WRITTEN.** It warned
the fastest green would be *"two hand-written sections for retailers nobody re-probed — inventing
records to satisfy a gate, the Phase 2 failure with the sign flipped."* Both new sections are built
from measurements already in the tree, each carrying its own date, plus three days of the daemon's
own readings — **which are more current than anything any other retailer section in that file
holds.** Somebody looked.

**AND RULE 7'S LIMIT IS RECORDED RATHER THAN GLOSSED.** Rule 6 makes a REFUSED section cite an
observation; nothing makes a REACHABLE one do so. A section invented out of nothing with a
REACHABLE verdict still passes. The rule buys *"somebody had to write a heading and a verdict"* —
a low bar, and higher than silence. The old worry is narrowed, not eliminated.

### Watched red before the sections existed

At `052f35d`, with rule 7 added and nothing else: **2 problems, naming GameStop and Walmart** — the
exact two the allowance named. Green only after both sections were written.

**And it cost 27 test failures, which is the part worth recording.** The synthetic trees throughout
`tests/test_evidence_check.py` configure `_SHIPPED` and write sections for nobody in it, so rule 7
fired in 27 cases about rules 1–6. Fixed by splicing `_SHIPPED_SECTIONS` into the tree builders —
**not** by exempting test trees inside `check_phase`, because a rule that exempts its own tests is
not the rule the shipped tree runs under. Three trees needed per-case reasoning (the configured set
differs), and one needed rewriting outright: the rule-4 case appended `## GameStop` / `## Walmart`
to the real document, which now already has them, producing duplicates and a rule-2 red about
something that case does not test. It flips the real verdict lines in place instead.

**One real-document count moved and is named rather than silently updated:** `verdicts == 5` → `7`.

## The matrix — criteria 3 and 4

`README.md`'s support matrix and the paragraph under it. **The gate is two-directional and passed
throughout: `tests/test_support_matrix.py`, 44 passed.**

| row | was | now |
|---|---|---|
| Walmart | ✅ Working | ⚠️ **NOT READING** — zero resolved readings in three days, `checked: false`, rung 1 **and** rung 3 refused |
| Target | ⚠️ Working | ⚠️ **NOT READING** — zero resolved readings, in cool-off since 2026-09-14 02:00:00 |
| Amazon | ⚠️ Working | ⚠️ Working **intermittently** — 14 refusals, counter reset, both watches stamped 2026-09-14 |
| GameStop | ✅ Working | ✅ Working — and 39 refusals with 16 resets, which is what "working" looks like under this backoff |

**The count sentence was the padding, and it was the part criterion 4 is actually about.** It read
*"Six working retailers — read them as a four and a two."* **Three of six read.** It is corrected in
place with the old sentence quoted and named as *a count of retailers that had once worked* —
because that substitution is the thing this project exists to refuse, and it had been sitting in the
README under the heading that advertises the project's honesty.

**Nothing was measured to have broken on 2026-09-14. Somebody finally looked**, and the README now
says which two can page you today (GameStop, Nintendo) rather than which six once could.

## Not padded downward either — the rung-4 question, decided rather than drifted into

**Target and Walmart are NOT recorded as rung 4.** Rung 4 here means **dropped, with evidence**, and
the precedent is Pokémon Center: dropped on a **Terms** finding, a permanent property of the
retailer. Target and Walmart are refusing **a client**. That is a reputational state which can end
without anybody doing anything, and recording it as rung 4 would assert a permanence nothing
measured supports. **Overstating a refusal is the same error as overstating a success.**

**Dropping either is Dan's call and was not taken here.** `config/products.yaml` is byte-unchanged.
`REQUIREMENTS.md` already says it: *"REQ-25 produces the evidence that decision needs; the decision
itself is Dan's and is out of scope."*

## Criterion 5 — the budget, accounted for

| | |
|---|---|
| **Authorised** | **0 per retailer**, stated in `COVERAGE.md` before the first plan ran |
| **Navigations that left this host** | **0** |
| **Unspent** | **0** — there was nothing to spend |
| **Retailers contacted** | **none** |

`boty check` was **not** run. `scripts/control_check.py` was run only as `--offline --fixtures`.
`state.json`, `pacer-state.json` and `served/boty/status.json` were **read and never written** —
the reads went through `json.load` and `journalctl`, and no `boty.status.write` or
`monitor.run_once` was imported or called. No `systemctl restart`.

**The method that replaced the budget is named rather than implied:** observation of already-spent
requests. It is not a loophole and the difference is real — a probe adds a request to a retailer
already refusing us, which is the exact thing phases 8 and 9 exist to stop doing. Reading a ledger
adds nothing to anyone's view of us.

## An ident that was NOT registered, and why — `M45` is still free

Rule 7 is gated by two tests and by no mutation. `M45` on its guard is available and **was not
taken**, because pricing an ident properly on this project means measuring its kill set against all
40 existing idents — one sandbox each, the measurement M44's block records as the standard — and
that was not done here. **Phase 11's criteria do not require a new mutation** (criterion 6 asks only
that `make verify-offline` exits 0), so registering one on a partial measurement would have bought a
denominator rather than a defence. Recorded as an **open, priced hole**: the anchor is
`if len(sections_for(display, sections)) == 1:` in rule 7, it is unique in the file, and `scripts/`
is already in `SANDBOX_CONTENTS` so nothing needs adding to reach it.

---

## VERIFIED 2026-09-14, `gaps_found` at 8/12 — two findings land on this plan

**Nothing above is edited.**

### CRITERION 4 IS MET ONLY IN PART: THE README PADDED INSIDE ITS OWN ANTI-PADDING CORRECTION

This plan's whole subject was that *"Six working retailers"* counted retailers that had **once**
worked. The paragraph that replaced it said **"TWO CAN PAGE YOU TODAY: GameStop and Nintendo."**

**Nintendo's GO Plus + watch — the only first-party listing of this product anywhere in the table —
has had no resolved reading since 2026-09-09 15:25.** Its *control* reads every few minutes, which
is what made the row look fresh. **A control reading proves the detector works. It does not prove
the watch you care about is being read**, and counting a retailer as able to page you on the
strength of its control is the same substitution one paragraph up, committed while correcting it.

**One retailer can page you with confidence today: GameStop.** The matrix and the count paragraph
both now say so, and Nintendo's row is `⚠️ Working — its CONTROL only` with the date.

**Nothing here was measured to have broken.** Nintendo was **never refused** in the window — zero
refusals logged — so this is not a block and **nothing establishes what it is.** Recorded as
unexplained rather than diagnosed.

### CRITERION 3 IS MET LITERALLY, AND THE VERIFIER PRICED WHAT THAT IS WORTH

`tests/test_support_matrix.py` passes 44, and corrupting Walmart's **rung** cell reddens 14 tests.
**But this plan changed no gated cell** — the Status cells and the count paragraph are prose, and
the verifier measured that **putting `✅ Working` and "Six working retailers" straight back still
passes 119 tests.** So the gate is real about rungs, extraction axes and the disagreement marker,
and says **nothing** about whether the Status column tells the truth.

**That is not a defect in this plan and it is a hole in the gate**, recorded here rather than
quietly fixed: the honest options are a gate that binds a Status cell to a `read_at` staleness
threshold, or leaving it ungated and saying so. **It is left ungated and said.**

### AND THE PHASE-11 COMMIT DID CHANGE PRODUCTION CODE

`2508f3c` also carries the phase-10 re-verification's fixes to
`boty/retailers.py::_verdict_from_html`. Describing that commit as *"changed no production code"*
was reading a two-part commit by one of its parts. **Three things are now in the tree and not on the
daemon, not two.**
