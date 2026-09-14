---
phase: 11-the-honest-ladder-position
verified: 2026-09-14T14:00:00Z   # approximate (±5 min); journal/state readings taken 13:42–13:50Z
verified_at_commit: 2508f3c   # the phase commit. HEAD has since moved to 3210b57 (b5304c1 CLAUDE.md + 10-DECISIONS.md; 3210b57 ROADMAP/STATE gate record). Neither touches boty/, scripts/, tests/, README.md, docs/ or config/ (git diff --stat 2508f3c HEAD, empty), and neither closes a gap below
status: gaps_found
score: 8/12 must-haves verified (2 PARTIAL — criterion 4, figures re-derive; 2 FAILED — Walmart chronology, records of the commit's contents)
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Criterion 4: the count of working retailers is not padded"
    status: partial
    reason: >
      Padding DOWN is refused on sound grounds, and the "Six working retailers" sentence is gone. Padding UP
      survives in the paragraph that replaced it. README.md L79 lists Nintendo under "reading … fresh readings,
      minutes old", and L89 says "TWO CAN PAGE YOU TODAY: GameStop and Nintendo". Nintendo's only alertable watch,
      `nintendo:Pokémon GO Plus +`, has read_at 2026-09-09 15:25:05 CDT in state.json, both now and in the
      pre-restart copy taken 2026-09-11 07:56:23. So it produced ZERO resolved readings in the phase's own window,
      and none for two days before it. Only Nintendo's CONTROL is minutes old. The phase read the same state.json
      and did not look at this row. No phase-11 document mentions it. A watch that produces no reading cannot
      page. As measured, GameStop is the one retailer that can page today, and Amazon can when it answers.
    artifacts:
      - path: README.md
        issue: "L79 and L89 claim Nintendo reads and can page. Its GO Plus + watch has not resolved since 2026-09-09"
    missing:
      - "Correct L79/L89 to separate Nintendo's control (reading) from its GO Plus + watch (no resolved reading since 2026-09-09 15:25:05). Record the fix beside the old text, not over it"
      - "A § Nintendo 2026-09-14 note in docs/retailer-evidence.md with the stamp and the zero-cost method. The cause cannot be established offline: no refusal was logged and the journal carries no INFO lines"
  - truth: "The Walmart record's dated measurements are true of the sources they cite"
    status: failed
    reason: >
      The phase fixed its window's lower bound at the 2026-09-11 restart. It then read "first time" facts off
      that window without checking the same free ledger before the bound. The pin was NOT activated on
      2026-09-11. Measured: (1) the env file's mtime is 2026-08-25 08:32:26 (metadata only; contents not read).
      (2) boty was restarted 2026-08-27 07:23:34, and that process (PID 667833) ran until 2026-09-11. (3) The
      status.json copy taken just before the 2026-08-27 restart has 0 watches with store_pinned. The copy taken
      2026-09-11 07:56:23 was written by PID 667833 at 07:54:33. It has 2 pinned watches and a Walmart failing
      control reading "the page named store <another>; this watch pins store <pinned>". So the store-disagreement
      state was live under the OLD process. (4) The journal shows `sending health warning for: walmart` from
      2026-08-27 20:07:53, about 240–290 a day, without a break, to 2026-09-13 05:26:07. Every failed delivery
      failed at the identical `byte offset 353`: 3,759 before the restart and 546 after it.
      So these statements are false: evidence L3132 ("2026-09-11 07:56:33 | WALMART_STORE_ID reached the running
      process"); evidence L3151 (the warning was "unreachable until a store is pinned and became reachable for the
      first time with that morning's restart"); and "45 h answering with a store we did not ask about" in the
      README Walmart row, the evidence subsection, the commit message and the ROADMAP. That phase lasted about
      15.4 days (2026-08-27 20:07 → 2026-09-13 05:26). The 45 h is where the window started, not where the
      behaviour started. "546 health warnings, none delivered" is true of the window only: 4,305 went
      undelivered since 2026-08-27, so the notify defect was live for about 17 days, not 3. The CLAUDE.md
      bullet ("the restart that activated it happened 2026-09-11 07:56:33"; "fired 546 times … not one reached a
      phone") was committed AFTER the phase, in b5304c1 (2026-09-14 08:43), and is contradicted by the same
      measurements.
    artifacts:
      - path: docs/retailer-evidence.md
        issue: "L3132 dates the pin's activation to 2026-09-11. L3141–3155 describe a 45.4 h store-disagreement phase that began 2026-08-27 20:07"
      - path: README.md
        issue: "Walmart row: '45 h answering with a store we did not ask about'"
      - path: .planning/ROADMAP.md
        issue: "Phase 11 closing record and commit narrative repeat the 45 h / first-reachable framing"
      - path: CLAUDE.md
        issue: "Bullet committed in b5304c1, after the phase, dates activation to the 2026-09-11 restart and counts 546 undelivered warnings"
    missing:
      - "Dated corrections BESIDE L3132 and L3151 (and the README/ROADMAP/CLAUDE.md sentences), citing the 2026-08-27 07:23:34 restart, the two status.json copies and the journal's continuous stream since 2026-08-27 20:07:53"
      - "Restate the undelivered-warning count as 4,305 since 2026-08-27, keeping 546 as the in-window figure beside it"
  - truth: "The records accurately describe what the phase commit changed"
    status: failed
    reason: >
      ROADMAP L91 ("it changed no production code"), ROADMAP L547 ("phase 11 changed no production code") and
      STATE.md Current focus ("phase 11 changed no production code at all") are false of 2508f3c. That commit
      changes `boty/retailers.py::_verdict_from_html`: `announces_this_sku` replaces `announced is not None`, one
      `nothing_resolved` predicate now feeds both the detail and `unresolved`, and there is a third
      not-established wording. That is a behaviour change: it closes 10-VERIFICATION's W1 and gap 2. It is gated.
      I reverted the one line in a scratch copy and
      `test_a_redirect_that_names_no_product_does_not_silence_a_dead_control` went red (1 failed); restored, 3
      passed. The same commit also rewrites 10-VERIFICATION.md (288 lines). Because of the false sentence, the
      "NOT ON THE WIRE" lists name only 57ea00b and 17d3e5d. A third behaviour change, this one, is in the tree
      and not on the daemon: MainPID 746345 has run since 2026-09-11 07:56:33, and this code landed 2026-09-14.
    artifacts:
      - path: .planning/ROADMAP.md
        issue: "L91, L547: 'changed no production code'; NOT-ON-THE-WIRE list omits the 2508f3c retailers.py change"
      - path: .planning/STATE.md
        issue: "Current focus: same false sentence, same incomplete list"
    missing:
      - "Correct beside: 2508f3c carries the phase-10 re-verification fix to _verdict_from_html (W1 + gap 2), and it is a third tree-not-wire change the next restart carries"
  - truth: "The figures in the new evidence sections re-derive from the cited sources"
    status: partial
    reason: >
      Every figure re-derives except one. GameStop's "16 resets" (README row, evidence § GameStop, 11-01-SUMMARY)
      follows from no definition applied to the series the evidence doc itself prints
      (`1 1 2 3 1 1 1 2 1 2 3 4 5 1 1 1 2 3 1 2 3 4 5 1 1 2 1 1 2 3 1 2 3 1 2 1 1 1 2`). A `1` that follows any
      refusal proves an intervening reset. That happens 18 times inside the series, or 19 counting the pre-window
      refusal at 2026-09-11 01:51:05. Strict drops number 9. The conclusion (GameStop resets constantly and reads)
      is unaffected. The number is not a measurement.
    artifacts:
      - path: docs/retailer-evidence.md
        issue: "§ GameStop 2026-09-14 table: '16 resets'"
      - path: README.md
        issue: "GameStop row: 'resetting 16 times'"
    missing:
      - "Replace with the derivable figure and its definition (≥18 resets inside the window's series), noted beside the old figure"
warnings:
  - id: W1
    finding: "The new Walmart section's machine-readable verdict line is set by the gate, not by the measurement"
    detail: >
      `**Verdict: REACHABLE (rung 1)**` was written on 2026-09-14 for a retailer measured to have produced zero
      resolved readings and to be refusing at both rungs tried. The prose says the line "is about August". In a
      scratch copy, flipping it to the measured state (`REFUSED`) fires rule 5 (configured while refused) and
      rule 6. So the verdict vocabulary cannot express "configured, currently refused, not dropped". The honest
      state lives in prose that no gate reads, and the gate-readable surface says REACHABLE: two surfaces
      disagreeing. It is argued in the open (11-02-PLAN § "neither existing word fits"), so it is not hidden. It
      is a vocabulary gap that only Dan can decide (a new verdict term, or dropping the retailer).
  - id: W2
    finding: "Criterion 4's correction is ungated. Reverting it keeps the suite green"
    detail: >
      In a scratch copy I restored the Walmart Status cell to `✅ Working` and the count sentence to "Six working
      retailers". `tests/test_support_matrix.py` and `tests/test_evidence_check.py` gave 119 passed. None of the
      four moved rows changed a Rung or Extraction cell, so criterion 3's gate is not exercised by this phase's
      edits at all. It still binds what it binds: Walmart rung 1→3 gives 14 failed. "44 passed, both directions"
      is true, and it is true of cells the phase did not touch.
  - id: W3
    finding: "The Amazon reset inference says more than a reset measures"
    detail: >
      `pacing.record` resets on any non-refused cycle, "including a parse failure" (boty/pacing.py:985–988). So
      the reset proves Amazon refused no watch in some cycle. It does not prove "Amazon answered every watch it
      was asked" (evidence § Amazon). The conclusion (intermittently reachable) stands on the two resolved stamps
      (02:26:22 and 03:26:17 on 2026-09-14), not on the reset. The same applies to GameStop, where fresh stamps
      carry it.
  - id: W4
    finding: "Best Buy is weak evidence against uniform blindness"
    detail: >
      "Nintendo and Best Buy were never refused" is true: 0 journal lines in the window. But Best Buy has no
      resolved reading since 2026-08-25. Not refused is not answered. The narrowing still holds on Amazon's and
      GameStop's stamps and Nintendo's control, so this does not change criterion 2.
  - id: W5
    finding: "A cited line number is stale at the commit that ships it"
    detail: >
      Evidence § Amazon, 08-UAT and 11-01-SUMMARY cite `boty/retailers.py:718` for the refusal's `read_at=None`.
      That was correct at 052f35d. 2508f3c inserted 52 lines above it, so at HEAD the site is L766 and L718 is a
      comment about detail prose. The monitor.py citations (417–418, 441, 869) are correct at HEAD.
  - id: W7
    finding: "Criterion 6's ROADMAP row reads as vindication, and the gate cannot vindicate this phase"
    detail: >
      ROADMAP L524 lists the gate's figures (EXIT 0, 1047 passed, 40/40). Only its quoted verdict line says the live
      controls were not run. This phase's own finding is that Target and Walmart produced zero resolved readings
      for three days (in Walmart's case since 2026-08-27; gap 2) while every offline gate stayed green. The offline
      gate shows the tree is internally consistent. It shows nothing about any retailer, and it does not see the
      README's Status prose at all (W2). The row should say that beside the numbers.
  - id: W6
    finding: "Out of scope, recorded so it is not lost: the published payload carries the Walmart pin's value"
    detail: >
      `served/boty/status.json` has a `store_pinned` field holding the value itself on both Walmart watch rows.
      CLAUDE.md says the pin's presence "may only ever be measured as a count". The file is gitignored, and
      boty-web serves it on loopback, so no public leak was measured. The rule and the payload disagree. Not
      introduced by phase 11. The value is deliberately not reproduced here.
---

# Phase 11: The Honest Ladder Position — Verification Report

**Phase Goal:** What is actually true of Amazon, Target and Walmart is established by measurement and written
down, including *dropped* where that is the answer.
**Verified:** 2026-09-14 ~14:00Z, at `2508f3c`
**Status:** gaps_found
**Re-verification:** No. Initial verification.

## The question asked first: is "observation is not probing" sound?

**Yes, and it is not a dodge.** I checked it three ways.

1. **The distinction is real.** Criterion 5 exists to cap *politeness cost*: requests this project adds to a
   retailer's view of it. The daemon's requests happen on Dan's standing authority whether or not anyone reads
   the journal. Reading `journalctl`, `state.json` and `status.json` adds nothing, and the phase did not
   schedule, trigger or change a single request.
2. **Nothing claimed needs a request that was not made.** Criterion 1 (rung, axis, what was tried) is built from
   dated records already in the tree plus observed outcomes. Criterion 4 is a recording decision. The one
   question that *does* need a request, egress vs client, is recorded UNANSWERED with the decisive test named,
   and the phase's own context said at planning time that observation holds the independent variable fixed. The
   budget did not buy an answer the phase did not have.
3. **Where the method failed, it failed for a reason unrelated to requests.** Two of this report's gaps come
   from reading the free instrument *too narrowly*, not from lacking a live request. The window was fixed at the
   2026-09-11 restart and "first time" claims were read off it, but the same ledger before that bound is free
   and contradicts them (gap 2). And the phase read `state.json` for controls but not for Nintendo's alertable
   row (gap 1). The method is sound. How it was applied was incomplete.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence (my measurement) |
|---|---|---|---|
| 1 | SC1: Amazon, Target, Walmart each have a dated verdict stating rung, extraction axis, what was tried | ✓ VERIFIED | § Amazon 2026-09-14 (rung 1, `dom`), § Target 2026-09-14 (rung 3; `dom` stated in the section's existing text L23/L36), new § Walmart (rung 1, `structured`, rung-1 and rung-3 refusals dated). Every subsection states its window and method. *One Walmart row is dated wrongly: truth 9* |
| 2 | SC2: egress-vs-client answered or explicitly unanswered, naming what was tried and what could not be | ✓ VERIFIED | `## Phase 11 — the egress-vs-client question: EXPLICITLY UNANSWERED`. It names the decisive test (a second egress), why it was not run (no egress, zero budget, Dan's to arrange), and what the instrument cannot vary. The narrowing ("uniform blindness is dead") is supported by resolved stamps at Amazon and GameStop and Nintendo's control, and the section says in so many words that it "separates neither" answer. It is not doing the work of an answer. Best Buy is a weak witness (W4) |
| 3 | SC3: README matrix reflects changed rows and passes its two-directional gate | ✓ VERIFIED | `tests/test_support_matrix.py`: 44 passed (my run). README Walmart rung 1→3 in scratch: 14 failed. *But no moved row changed a gated cell, and reverting the correction stays green (W2)* |
| 4 | SC4: rung 4 recorded where honest; count of working retailers not padded | ✗ PARTIAL | **Down:** refusal of rung 4 holds. README defines rung 4 as "Dropped … Not configured", the matrix gate has `test_a_rung_four_row_whose_retailer_gains_an_adapter_fails`, and dropping config is Dan's under REQ-25. `config/products.yaml` is not in the commit. **Up:** "Six working" is gone, but Nintendo is still counted as reading and paging on a control-only stamp. Its GO Plus + watch has not resolved since 2026-09-09 15:25:05 (gap 1) |
| 5 | SC5: cap stated, actual count recorded | ✓ VERIFIED | `COVERAGE.md`: cap 0 per retailer. Session transcript: COVERAGE.md written 13:20:34Z, 11-01-PLAN at 13:21:02Z, first phase-11 evidence edit at 13:22:56Z. The earlier journal reads (13:17Z) cost no request. Scanned the main transcript and every subagent transcript modified 2026-09-14 for `boty check`, a networked `control_check.py`, retailer `curl`, `systemctl restart`, `run_once(`, `status.write(`, or redirects into the three daemon files: **none** from phase 11. The only restart hit is 2026-09-11 (Dan-instructed, pre-phase). The daemon files are gitignored and absent from the commit. `MainPID` 746345, `NRestarts=0` |
| 6 | SC6: `make verify-offline` exits 0 | ✓ VERIFIED | The lead's run, read and not run by me, per instruction. **Measured at `2508f3c`**: `tree-before-verify.txt` (written 08:40:05) and `tree-after-verify.txt` (08:51:32, the same mtime as the transcript) are both **0 bytes** of `git status --porcelain`, so the mutation sandboxes copied a committed tree. `b5304c1` landed at 08:43 mid-run, but it touches only `CLAUDE.md` and `10-DECISIONS.md`, and neither is in `SANDBOX_CONTENTS`. One residual: `served/` IS in `SANDBOX_CONTENTS`, so each sandbox also copied the daemon's live, gitignored `status.json` as it stood at that moment. That file is a runtime input, not a commit. Figures: `identity check: PASS — 288 file(s)`, `1047 passed`, `mutation check: 40/40 mutations caught`, `VERIFY: PASS (OFFLINE — live controls were NOT run …)`, `EXIT=0`. My targeted runs agree: test_evidence_check 75 passed, test_support_matrix 44 passed |
| 7 | `read_at` means a resolved reading happened; no refusal writes or removes a stamp | ✓ VERIFIED | `monitor.py:417-418` returns on UNKNOWN before `:441-444` (write, or pop). AST scan of every `Result(...)` in boty/: every `refused=True` site is `Availability.UNKNOWN` with `read_at=None` (L766, 840, 975, 1115, plus the API arm). Every resolved producer (L681, L724, L1340) passes a `time.time()` stamp. `pop` is reachable only for a *resolved* result with no stamp, and `State.load` drops a stamp only when validation fails. No refusal path touches a stamp. Behaviourally defended by M31 (40/40 caught in the verify run). Stale citation noted (W5) |
| 8 | The numbers re-derive | ✗ PARTIAL | Re-derived from the journal (2026-09-11 07:56:33 → now): **Amazon** 14, series 10…20 then 1, 2, 3, stamps 02:26:22 and 03:26:17 ✓. **Target** 12, 19→30 monotonic, `read_at` null, `(30 in a row) — next attempt in ~4320 min` at 02:00:00, `current_interval_seconds: 259200` ✓. **Walmart** 9, first 2026-09-13 05:30:33, null on all three rows, 546 in-window warnings 08:00:44 → 05:26:07 ✓. **GameStop** 39, max 5, stamps fresh (now 08:43) ✓, **"16 resets" ✗** (gap 4). The wider window moved no refusal count: the last refusals in all four series predate 08:18:35. Only stamps and "next attempt" times moved |
| 9 | The Walmart chronology is true of its sources | ✗ FAILED | The pin was active from 2026-08-27, not 2026-09-11. The store-disagreement stream ran about 15.4 days, not 45 h. 4,305 warnings went undelivered, not 546 (gap 2) |
| 10 | The corrections to other records hold | ✓ VERIFIED | **Walmart:** `read_at` null in the 2026-08-27 and 2026-09-11 pre-restart copies and now. By truth 7, and because a pinned-store disagreement is UNKNOWN (`_is_store_gap`), no resolved Walmart reading has been stamped since stamps reached the wire. STATE/08-UAT's "real verdicts after the restart" is correctly withdrawn, beside the original. *Scope note:* CLAUDE.md's unqualified "has ever been recorded" overreaches: the 08-03→08-17 control transcripts resolved Walmart outside `state.json`, which 08-UAT's "in `state.json`" wording correctly limits. **GameStop 410:** GO Plus + resolved `out_of_stock` at 08:13:22 (08:43:24 now). Both records kept, not edited |
| 11 | Rule 7 reverses the allowance for a real reason, was red first, and its stated limit is true | ✓ VERIFIED | Scratch copy of `git archive 2508f3c`, caches cleared between every perturbation and its revert, restores `cmp`-checked. GameStop and Walmart sections removed: **2 problems, both rule 7**. Same tree with rule 7 excised: **PASS** (the old allowance, reproduced). Guard `== 1` → `>= 0`: `…_now_fails_under_rule_seven` red (1 failed). **Limit:** Walmart section replaced by "Made up. Nobody looked." + REACHABLE: **PASS**, so the stated limit is true. **Is the old objection answered?** *For existence, yes*: both sections cite dated records with line references, and the three-day readings are genuinely new. *For accuracy, no*: the Walmart section, assembled to satisfy the rule, carries a wrongly dated measurement (gap 2), and its verdict line is gate-shaped (W1). Rule 7 cannot see either. The docstring's "narrowed rather than eliminated" is the honest description |
| 12 | The records accurately describe what the phase commit changed | ✗ FAILED | "Changed no production code" is false. `_verdict_from_html` behaviour changed in 2508f3c, and the NOT-ON-THE-WIRE lists omit it (gap 3) |

**Score:** 8/12 truths verified (0 present-but-behavior-unverified)

### The five "MET AS WRITTEN" rows, individually

| # | Phase's verdict | This report |
|---|---|---|
| 1 | MET AS WRITTEN | **Earned** on the criterion's text. The Walmart record under it needs a dated correction (gap 2), which the criterion does not itself test |
| 2 | MET AS WRITTEN (unanswered) | **Earned** |
| 3 | MET AS WRITTEN | **Earned literally.** The gate passes both ways, but the gate never saw this phase's edits (W2) |
| 4 | MET AS WRITTEN, in both directions | **Not earned. MET IN PART.** The "down" direction holds. The "up" direction still pads Nintendo (gap 1) |
| 5 | MET AS WRITTEN | **Earned**, by transcript ordering and scan, not by the summary's say-so |

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `docs/retailer-evidence.md` | Dated verdicts ×3, § GameStop, § Walmart, egress section | ⚠️ PRESENT, two figures wrong | Sections exist, one verdict line each (real-doc verdicts = 7). Walmart chronology and GameStop "16" are wrong |
| `scripts/evidence_check.py` rule 7 | Configured roadmap retailer must carry exactly one section | ✓ VERIFIED | Red-watched as above |
| `tests/test_evidence_check.py` | Reversed test and positive-direction test | ✓ VERIFIED | 75 passed. Old docstring quoted in full |
| `README.md` matrix and count paragraph | Four rows moved, "three of six read" | ⚠️ PARTIAL | Nintendo padding (gap 1), Walmart 45 h (gap 2), GameStop 16 (gap 4) |
| `COVERAGE.md` | Cap 0 stated before plans | ✓ VERIFIED | Transcript ordering |
| `boty/retailers.py` | *(the phase claims untouched)* | ⚠️ CHANGED | W1 fix, gated and red-watched, and undisclosed in the phase records (gap 3) |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| retailers refusal producers | `state.json` `read_at` | `transitioned_to_stock` early return | ✓ WIRED | Truth 7 |
| `pacing.record` | journal `refused us (N in a row)` | `any(x.refused)` at monitor.py:869 | ✓ WIRED | Reset semantics include non-refused failures (W3) |
| `config/products.yaml` configured set | evidence sections | rule 7 | ✓ WIRED | Red-watched |
| README Status cells and count prose | code / ledger | *(none)* | ✗ NOT GATED | W2. Informational, not a criterion |

### Behavioral Spot-Checks and Perturbations (all offline, scratch copy)

| Behavior | Command / perturbation | Result | Status |
|---|---|---|---|
| Rule 7 fires on the pre-phase shape | GameStop and Walmart sections removed, `evidence_check.py --phase` | 2 problems, both `rule 7` | ✓ PASS |
| Old allowance really was clean | Same, with rule 7 excised | `PASS — phase` | ✓ PASS |
| Rule 7's test binds | `== 1` → `>= 0` | 1 failed | ✓ PASS |
| Rule 7 limit | Invented REACHABLE Walmart section | `PASS — phase` (limit true) | ✓ PASS |
| Measured Walmart state expressible? | Walmart verdict → REFUSED | rule 5 + rule 6 FAIL | ⚠️ W1 |
| W1 production change is gated | `announces_this_sku = announced is not None` | 1 failed; restored 3 passed | ✓ PASS |
| Matrix gate binds rung | Walmart rung 1→3 | 14 failed | ✓ PASS |
| Criterion-4 prose gated? | Walmart `✅ Working` + "Six working retailers." | 119 passed | ⚠️ W2 |

### Probe Execution

No `scripts/*/tests/probe-*.sh` is declared by this phase. Step 7c: N/A. Live controls deliberately not run.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| REQ-25 | 11-01, 11-02 | Establish the honest ladder position of Amazon, Target, Walmart; decision to drop is Dan's | ⚠️ PARTIAL | Positions established and recorded, egress question recorded unanswered, no retailer dropped. Two recorded measurements need dated correction (gaps 2, 4). README still overstates Nintendo (gap 1) |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | No TBD/FIXME/XXX introduced in the phase's modified code or scripts | — | — |
| README.md / evidence | Walmart row, L3151 | Window-bounded "first time" claim | 🛑 Blocker (evidence standard) | Gap 2 |
| ROADMAP.md / STATE.md | L91, L547 | Claim about the commit contradicted by the commit | 🛑 Blocker (evidence standard) | Gap 3 |

### Human Verification / Decisions for Dan

Not a `human_needed` phase, because gaps take precedence. One item needs his decision, not a fix: **W1**. The
verdict vocabulary has no term for *configured, currently refused, not dropped*, so Target's and Walmart's
gate-readable lines say REACHABLE while their prose says "not reading". The options are a new verdict term or
dropping the retailer, and both are his.

### Gaps Summary

The phase's central move, reading the daemon's own ledger in place of a probe budget, is **sound**, and most of
what it established re-derives exactly: the first production cool-off, Amazon's intermittency, Target's and
Walmart's zero resolved readings, the `read_at` semantics, rule 7's red-first reversal and its stated limit, and
a clean offline gate.

The four gaps have **two root causes**:

- **The instrument was read too narrowly** (gaps 1, 2). The window's lower bound became the start of history
  for Walmart's store disagreement, which actually began 2026-08-27. The row-by-row reading stopped at
  controls, so Nintendo's non-reading alertable watch was advertised as able to page. Both corrections are free:
  same ledger, zero requests.
- **Record accuracy** (gaps 3, 4). A code change bundled into a "no production code" commit, and one figure
  that no definition produces.

None needs a live request. All are corrections beside existing text.

---

_Verified: 2026-09-14 ~14:00Z_
_Verifier: Claude (gsd-verifier)_
