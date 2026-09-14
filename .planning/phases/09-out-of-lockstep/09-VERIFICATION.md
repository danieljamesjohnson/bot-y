---
phase: 09-out-of-lockstep
verified: 2026-09-14T14:12:50Z
describes_commit: 570df66
status: gaps_found
score: 5/7 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification: true
previous_status: gaps_found
previous_score: 5/7
previous_verified: 2026-09-11T13:28:39Z
gaps_closed:
  - "Warning 3 (2026-09-11) — criterion 4a's day test was seed-pinned. CLOSED by e88a350: five of six counts exact at 21/21 seeds and 20/20 on a disjoint set; the amazon bound reddens every out-of-place 49th tried"
gaps_remaining:
  - "Gap 1 — criterion 1 at dispatch. Re-verdict taken (the first option) but applied to ONE of the two records the gap named, and the ROADMAP table row still reads MET AS WRITTEN with no pointer"
  - "Warning 2 (2026-09-11) — record corrections. PARTIAL: a fourth site of the floor argument exists and is uncorrected, and the correction beside the test calls itself 'the third and last'"
regressions: []
gaps:
  - truth: "Criterion 1 — two retailers whose intervals coincide are NOT dispatched inside the same short window; the bound is a stated number of seconds, asserted on the schedule"
    status: partial
    reason: "Unchanged in code: no mechanism was built, by choice. The dispatch residual re-measured at 570df66 through cli.watch_loop over [0, 86400) s: two 300 s-cadence retailers are asked at the SAME wake (minimum gap 0.0 s) 17 times a day at _IDLE_SEED (target+walmart 10, nintendo+target 7), 11–30 over _IDLE_SEED+0..20, 13–29 over 20260881..20260900. The re-verdict was the verifier's first option and is legitimate, but it is incompletely applied. ROADMAP.md:273-278 carries the MET IN PART note in a paragraph below the table. Row 1 (:218) still reads MET AS WRITTEN with no pointer, although row 3 (:220) got one. The headline (:211) still says 'Four MET AS WRITTEN, one MET IN PART'. 09-05-SUMMARY.md row 1 (:266) and its phase verdict (:273), which the gap named explicitly, carry no note at all. The note names the mechanism (jitter + 25 s grace), not the magnitude."
    artifacts:
      - path: ".planning/ROADMAP.md"
        issue: "Row 1 (:218) MET AS WRITTEN with no pointer to the :273 amendment; headline :211 count not annotated"
      - path: ".planning/phases/09-out-of-lockstep/09-05-SUMMARY.md"
        issue: "Row 1 (:266) MET AS WRITTEN and 'four MET AS WRITTEN, one MET IN PART' (:273), no dated note beside either"
      - path: "tests/test_pacing.py"
        issue: "Still no dispatch-level separation test (grep for dispatch/same-wake test names: none in the phase-9 scope)"
    missing:
      - "A dated note beside 09-05-SUMMARY.md row 1 and its phase-verdict line, and a pointer on ROADMAP.md row 1 and the :211 headline, naming the measured residual (17/day at _IDLE_SEED, 11–30 across 21 seeds, same-wake pairs of 300 s retailers)"
      - "OR the mechanism plus a watch_loop-level dispatch-gap test, watched red first"
      - "Once recorded, criterion 1 is an honest MET IN PART like 4b. Promoting it past gaps_found needs Dan's acceptance recorded as an override, not an orchestrator's"
  - truth: "Record corrections owed by the 2026-09-11 pass (the false floor argument withdrawn at every site it was written, original preserved beside)"
    status: partial
    reason: "The three sites the 2026-09-11 report named are corrected beside, originals intact: ROADMAP.md:220/:279, boty/pacing.py:623-624 with :626-643, tests/test_pacing.py:2168-2171 with :2173-2188. But grep finds a FOURTH, uncorrected: 09-02-SUMMARY.md:42 (frontmatter '2 is ... the arithmetic floor: 6 x 60 s > 300 s ... A claim of 1 would be unavailable') and :84-86 (body). The same file at :80 still carries the uncorrected 'stepped the way cli.watch_loop builds and steps one'. Two corrections now assert a false completeness: test_pacing.py:2173 calls its site 'The third and last of the three places', and pacing.py:629 'the second of the three places'. That is the same incomplete-sweep-called-done that 052f35d's own message names as forbidden."
    artifacts:
      - path: ".planning/phases/09-out-of-lockstep/09-02-SUMMARY.md"
        issue: ":42 and :84-86 assert the withdrawn floor argument; :80 the withdrawn 'steps one' claim; no dated note beside any of them"
      - path: "tests/test_pacing.py"
        issue: ":2173 'third and last of the three places' is false — there are at least four"
      - path: "boty/pacing.py"
        issue: ":629 'the second of the three places' — the count is wrong"
    missing:
      - "Dated withdrawal notes beside 09-02-SUMMARY.md:42, :84-86 and :80, originals unedited"
      - "A dated note beside test_pacing.py:2173 and pacing.py:629 recording that the count was four, not three (fix the prose; there is no gate on it)"
warnings:
  - "Criterion 4a — the repaired day test is LESS sensitive to an advancing injected clock than the records say, and the records were not updated. Re-measured in a scratch copy with the helper's _FROZEN_CLOCK replaced by a per-call creep: 0/1/2/5/10 ms PASS at the test's 4 seeds (and 21/21 seeds by probe); 20 ms red (13/21 seeds would pass); 50 ms red (0/21). With real time.monotonic it passes 3/3 on this host. boty/cli.py:732 and tests/test_cli_watch.py:2156 still say '5, 10, 20 and 50 ms all fail' of this named test, and :2173 cites only the 50 ms red. Not a regression: the pre-repair test's 5 ms red was the seed fragility, not clock discrimination (it failed at 18/21 seeds with NO creep). But the threshold moved from ≤5 ms to 10–20 ms per cycle, and the tree says it did not"
  - "tests/test_cli_watch.py:2591-2592 — '_WAKES_TO_CLEAR_A_DAY = 1800 ... Enough wakes to be SURE _DAY_SECONDS is crossed at any seed — the loop's slowest jitter is 42.5 s a wake' is false arithmetic: 1800 × 42.5 = 76,500 s < 86,400 s (a guarantee needs 2033). The span assertion beside it catches an under-run, so no gate is weakened. But this is the floor argument's error class, an impossibility claimed where only a probability holds (the under-run is ~19σ), written into the repair of the phase that withdrew the last one"
  - "M43's kill set is SIX at the clean gate (verify-clean.txt:79), not five. Measured here: the sixth is the REWRITTEN day test. Under M43 the pre-repair (e88a350^) day test PASSES and the rewritten one FAILS. So e88a350 added detection. Nobody recorded that: ROADMAP.md:223 '5-test kill set', CLAUDE.md 'its five killers are disjoint from the union of all 38' and scripts/mutation_check.py:1871 all still say five, and the sixth's overlap with the other 39 idents is unmeasured"
human_verification:
  - test: "Criterion 4b — a timed `boty check` pass on the phase-9 tree"
    expected: "duration_seconds < 120 (REQ-08). The only figure on record is 20.43 s, quoted from 2026-08-31, on a different tree"
    why_human: "boty check makes live retailer requests and writes the daemon's status.json. Prohibited here; running it is Dan's call"
---

# Phase 9: Out of Lockstep — Re-verification Report

**Goal:** The six retailers stop presenting as one coordinated crawler: independent schedules, so a single cycle does not fire six unrelated retailers inside one short window.
**Verified:** 2026-09-14T14:12:50Z. **Figures describe `570df66`.** `boty/`, `tests/` and `scripts/` are byte-identical between `2508f3c` (the clean-gate commit) and `570df66` (`git diff --quiet` exit 0).
**Status: gaps_found. Score 5/7, unchanged.** **Re-verification:** yes, after `57ea00b`, `e88a350` and `052f35d`.

**In one paragraph.** The code repair is real and better than claimed in one respect nobody noticed: the rewritten day test is now an M43 killer, and its predecessor was not. The five non-amazon counts are exact at every seed tried. The amazon bound is a bound. **The record repairs are each half-done:** criterion 1's re-verdict reached ROADMAP's prose but not its table row, and not the 09-05 table the gap named. The floor argument survives uncorrected at a fourth site, beside a correction that calls itself "the third and last". And the repair's own comments misstate how sensitive the test is to the clock, and how sure 1800 wakes are to cover a day.

## Gap and warning dispositions (the 2026-09-11 findings)

| 2026-09-11 finding | Disposition at `570df66` | Evidence |
|---|---|---|
| **Gap 1** — criterion 1 at dispatch | **OPEN (partial)** | Residual unchanged (below). MET IN PART note exists at ROADMAP.md:273-278, beside and not over: the original table is intact. It names the mechanism but not the magnitude. **Not applied to** ROADMAP row 1 (:218, no pointer; row 3 has one), the :211 headline, or 09-05-SUMMARY.md :266/:273 |
| **Warning 1** — jittered 3 dropped from the closing record | **CLOSED** | ROADMAP.md:283-285 "6 → 2 per wake, 3 per 60 s"; test_pacing.py:2284-2298 records the 3 as **ungated** |
| **Warning 2** — false floor argument in three places; "steps one" docstring | **PARTIAL** | The three named sites are corrected beside. **A fourth site, 09-02-SUMMARY.md :42 and :84-86, is uncorrected**, and so is its "steps one" at :80. The criterion-3 docstring *is* corrected (test_pacing.py:2284). test_pacing.py:2173 "third and last of the three places" is false |
| **Warning 3** — 4a day test seed-pinned | **CLOSED**, with three new warnings | See criterion 4a below |

## Observable Truths

| # | Criterion | Status | Evidence (by command, 2026-09-14, scratch copy of `570df66`) |
|---|---|---|---|
| 1 | Coinciding retailers not dispatched in one short window; bound in seconds, on the schedule | ✗ **FAILED as written (MET IN PART)**, gap open | `watch_loop` over `[0, 86400)` s, fresh fixture per seed: **max 2 per wake** at every seed. Pairs of 300 s-cadence retailers share a wake **17×/day at `_IDLE_SEED`** (target+walmart 10, nintendo+target 7, which reproduces 2026-09-11 exactly). **11–30** over `_IDLE_SEED+0..20`, **13–29** over `20260881..20260900`. **Minimum gap between two distinct 300 s retailers: 0.0 s at all 41 seeds.** The due_at tests still pass (5/5 named pacing tests). No dispatch-level test exists |
| 2 | Independence, both directions | ✓ VERIFIED (regression check) | Both named tests pass. `boty/pacing.py` changed since 2026-09-11 only by 19 docstring lines (`052f35d`); `boty/cli.py` is unchanged |
| 3 | Max retailers in any 60 s over a simulated day, stated, < 6 | ✓ VERIFIED | Named test passes (asserts 2, unjittered). **Jittered 3 re-measured: 3 at 21/21 and 20/20 `watch_loop` seeds**, using the suite's own `_max_in_any_window`. **Still ungated**: no window-max assertion in `tests/test_cli_watch.py` (grep). That is recorded at test_pacing.py:2293 and not hidden |
| 4a | Per-retailer cadence and backoff ladder unchanged | ✓ VERIFIED (3 warnings) | See the next section |
| 4b | `boty check` inside 2 min, **re-measured** | ✗ **MET IN PART**, human | Not re-measured, unchanged since 2026-09-11. Routed to human |
| 5 | verify-offline 0, new mutation CAUGHT | ✓ VERIFIED | Clean transcript at `2508f3c`: `VERIFY: PASS (OFFLINE …)`, `EXIT=0`, 1047 passed, identity PASS 288 files, **40/40 caught**. **M43 CAUGHT, 6 tests** (:79). Not re-run, by instruction. The code under test is identical at `570df66` |
| 6 | Standing invariants | ✓ VERIFIED (regression check) | No code change to `current_interval`, `watch_loop` or state shape since the 2026-09-11 digest check (diff stat above); the named backoff-ladder test passes |

**Score: 5/7** (criteria 1 and 4b not counted). No truth is PRESENT_BEHAVIOR_UNVERIFIED: every behavioural claim has a named test run or a probe.

## Criterion 4a: the `e88a350` repair, attacked

Probe: `watch_loop` driven with the suite's own fixtures (`configured_fleet_cfg`, `_checker`), 1800 wakes, cut on simulated seconds `[0, 86400)` read before the sleep, exactly as the test's helper does.

| Claim in the tree | Measured | Verdict |
|---|---|---|
| bestbuy/nintendo/target/walmart 288, gamestop 96, exact at **21 of 21** seeds | **21/21** over `_IDLE_SEED+0..20`; **20/20** over a disjoint set `20260881..900` | ✓ **True** |
| Before the repair, *none* of the five was exact at 21/21 | Old cut per retailer: bestbuy 12/21, gamestop 18/21, nintendo 16/21, target 14/21, walmart 10/21 | ✓ True |
| Amazon 48 or 49, and a 49th sits within one tick of 86 400 s | 48×14 / 49×7 (21 seeds). Every 49th falls in **86 385.1–86 399.2 s**; on the disjoint set, 10/10 49ths fall in 86 378.4–86 396.0 s. 49th at **86 393.2 s** under 20260902 and 86 426.0 s (outside) under 20260901, both reproduced | ✓ True |
| **A 49th from anywhere else still reddens** | Each red-watch in its own copy: amazon **doubled at t=0** (grid advance skipped once) → **RED** (49th at 84 602.7 s). Amazon cadence **1780 → RED, 1795 → RED, 1799 → RED** (seed 20260902, 62 s early). **1801 and 1810 → pass** (they give 48, which the membership check accepts) | ✓ **A bound, not a tolerance**, resolved to ~1 s/fire on the fast side. A *slower* amazon, up to the cadence that still yields 48, is invisible, as it was before |
| **Still RED under an advancing injected clock (50 ms creep)** | Helper's `_FROZEN_CLOCK` replaced by a per-call creep, HEAD test: **0, 1, 2, 5, 10 ms PASS · 20 ms RED · 50 ms RED**. By probe over 21 seeds, the share of seeds that would pass: 21/21 at 0/1/5/10 ms, **13/21 at 20 ms**, **0/21 at 50 ms**. With real `time.monotonic`: **pass 3/3** on this host. Pre-repair test under the same clocks: 0 ms pass, 5 ms RED, 50 ms RED | ⚠️ **True as stated, and incomplete.** The test reddens at 50 ms, but 5 and 10 ms, which `cli.py:732` and `test_cli_watch.py:2156` still list as failing *this test*, now pass. **Not a regression:** the old 5 ms red was the seed fragility, since the old cut fails 18/21 seeds with *zero* creep (it matches at 3/21 with no creep, 2/21 at 1 ms, 1/21 at 5 ms, 3/21 at 50 ms: no trend with creep). The new test has a real threshold between 10 and 20 ms per cycle, and the old one had none. **The record is wrong about which creeps redden it** |
| Commit's other red-watches | `MIN_TICK_SECONDS` 30→60 → **RED** (walmart 289, seed 20260901). Tick returned to the standing interval → **RED** (the four 300 s retailers 287) | ✓ Reproduced |
| **"3 of 21"** (commit) vs **"1 of 21"** (2026-09-11) under the old 1728-wake cut | Over `_IDLE_SEED+0..20`: **3/21, seeds 20260901/06/15**, span **86 099.7–86 565.4 s**, both exactly as the commit says. Over `20260881..900`: 2/20, span 86 031.0–86 750.2 s. The 2026-09-11 span (86 107–86 702) matches **neither** set, and its probe files are not recoverable | ✓ **Honest, not a dodge.** The two figures are over different, unrecorded-vs-recorded seed sets. The commit reproduces its own exactly, keeps both, and draws the same conclusion from both. *The 2026-09-11 report's failure to record its seed set is the defect here, and it was this verifier's predecessor's* |
| `_DAY_SEEDS` rationale | 20260920 is the shortest 1728-wake span (86 099.7); 20260916 is the **longest** (86 565.4; "near the longest" undersells it); amazon 48/49/49/48 as stated | ✓ True |
| "1800 wakes … enough to be SURE `_DAY_SECONDS` is crossed at any seed" (:2591-2592) | 1800 × 42.5 s = **76 500 s < 86 400 s**. A guarantee needs 2033 wakes. The span assertion catches it | ⚠️ **False as arithmetic**, harmless as a gate |
| Gate strength | M43 applied by hand in a copy: the **rewritten** day test **fails**; the **pre-repair** test **passes** | ✓ **Stronger, and unrecorded.** M43's kill set went 5 → 6. ROADMAP.md:223, CLAUDE.md and mutation_check.py:1871 still say five |

**Criterion 4a is VERIFIED:** the repair made the gate seed-independent without buying that by loosening the clock binding (the old binding was illusory). The warnings are about what the tree *says* the test does.

## Contradictions between the tree and this measurement

1. **test_pacing.py:2173** "the third and last of the three places" and **pacing.py:629** "the second of the three places". There is a fourth: **09-02-SUMMARY.md:42, :84-86**, uncorrected.
2. **09-02-SUMMARY.md:80** still says the criterion-3 pacer is "stepped the way `cli.watch_loop` builds and steps one", the claim corrected at test_pacing.py:2284.
3. **cli.py:732 / test_cli_watch.py:2156** "5, 10, 20 and 50 ms all fail". For the test they name, **5 and 10 ms now pass** (measured at 4/4 and 21/21 seeds).
4. **test_cli_watch.py:2591-2592**: "SURE … at any seed" — false arithmetic (76 500 < 86 400).
5. **ROADMAP.md:218 / :211 and 09-05-SUMMARY.md:266 / :273** still present criterion 1 as MET AS WRITTEN and the phase as four-and-one, with no pointer beside.
6. **ROADMAP.md:223 / CLAUDE.md / mutation_check.py:1871**: M43's kill set is six at the clean gate, not five. The sixth is the rewritten day test, and its disjointness from the other idents is unmeasured.

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Criterion 1/2/3 pacing tests | `pytest tests/test_pacing.py -k "two_retailers_at_one_cadence or changing_one_retailers_interval or driving_one_retailer_into_backoff or max_retailers_in_any_sixty"` | 5 passed | ✓ |
| 4a day test + ladder | the two named `test_cli_watch.py` tests | 2 passed | ✓ |
| M43 against the suite (one full run, in a mutated copy) | `pytest tests` | 7 failed. 6 are M43 killers; the 7th, `test_every_unpackaged_top_level_directory_is_pruned_from_the_sdist`, **also fails unmutated** in a `git archive` copy (`NotATrackedTree`), so it is a copy artefact | ✓ |

## Human Verification

**1. Timed `boty check` (criterion 4b).** Run it with Dan's authorization and record `duration_seconds` against 120 s. Why human: it makes live requests and writes the daemon's `status.json`.

## Suggested override (only Dan can accept it)

Once the criterion-1 notes are placed beside 09-05-SUMMARY row 1 and ROADMAP row 1, the remaining difference is a design choice, not a defect in the record. If Dan accepts dispatch-level coincidence (≤2 per wake, 11–30 same-wake pairs a day) as the cost of keeping the jitter:

```yaml
overrides:
  - must_have: "Criterion 1 — two retailers whose intervals coincide are NOT dispatched inside the same short window"
    reason: "Bound holds on due_at (50.0 s); at dispatch two 300 s retailers share a wake 11–30×/day under the deliberate ±15% jitter; accepted as MET IN PART"
    accepted_by: "Dan"
    accepted_at: "<ISO timestamp>"
```

## Method and compliance

No live retailer request, no `boty check`, no `make verify` / `verify-offline`, no restart. `state.json`, `pacer-state.json` and `status.json` were not touched; the only daemon fact used is `journalctl -u boty` (read-only), which confirms the 2026-09-11 07:56:33 restart. No gsd-tools write, and nothing in the repository written except this file. Every perturbation ran in **its own** `git archive 570df66` copy under the session scratchpad, with `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, and `__pycache__` cleared before runs. Perturbed copies were discarded rather than reverted. The pristine probe copy was `diff -rq`'d against a fresh archive of `570df66` afterwards: identical apart from the probe file (exit 0). `boty/pacing.py` and `tests/test_cli_watch.py` were `cmp`-confirmed against `git show 570df66:`. The probe imported the suite's own fixtures and `_max_in_any_window`.

---

## PRIOR PASS — 2026-09-11 (superseded where marked above, kept unedited)

> Status **gaps_found**, score **5/7**, verified 2026-09-11T13:28:39Z, on the tree of that date.
>
> **Gaps (frontmatter, verbatim):** criterion 1 partial: "The 50.0 s bound holds on due_at (the next-attempt position) and only there. At DISPATCH, under the loop's own ±15% jitter and due()'s half-tick (25 s) grace, two 300 s-cadence retailers are asked at the SAME wake: 17 times a day through cli.watch_loop at the suite's _IDLE_SEED (target+walmart 10, nintendo+target 7), 13–32 across 5 seeds, and 30 times on the criterion-1 test's OWN seed and stepping while that test passes. The closing record says MET AS WRITTEN. …" Missing: "EITHER re-verdict criterion 1 as MET IN PART (ROADMAP closing record + 09-05 table, dated note beside, never over), naming the dispatch residual" / "OR a mechanism … plus a cli.watch_loop-level test asserting the minimum dispatch gap for coinciding pairs, watched red first".
>
> **Warnings (verbatim):**
> 1. "Closing record reads '6 -> 2' and drops the jittered 3 that 09-02 and 09-05 recorded beside it"
> 2. "'2 is the arithmetic floor (6 x 60 > 300), so 1 was never available' is FALSE for the configured fleet: only four retailers are on 300 s. A schedule with max 1 and unchanged counts exists (measured). It is a floor only on the chosen 50 s grid. The claim appears in the closing record, boty/pacing.py loop_tick_seconds and tests/test_pacing.py _AFTER_MAX_IN_ANY_60S"
> 3. "Criterion 4a's watch_loop day test matches 48/96/288 at 1 of 21 seeds (its own). It has no denominator, and its 'day' is 1728 jittered wakes spanning 86107–86702 s. The equality depends on where one seed's last wake lands. This is the 2026-09-08 CI break with the host-timing cause removed"
>
> **Truth table (verbatim verdicts):** 1 ✗ FAILED as written (MET IN PART) · 2 ✓ VERIFIED · 3 ✓ VERIFIED (see warnings; "The 3 is ungated") · 4a ✓ VERIFIED (see warnings; "An advancing injected clock reproduces `amazon: 49`") · 4b ✗ MET IN PART, correctly verdicted · 5 ✓ VERIFIED ("1038 passed / 0 skipped … 40/40 caught … M43 CAUGHT, 5 tests failed") · 6 ✓ VERIFIED (`current_interval` digest `6da39ac5…49108` identical at `a58e7ac`, `87871b4` and HEAD).
>
> **Closing-record claims tested:** 457/1728 idle wakes reproduced; ≤2 per wake reproduced; "6 → 2" is the unjittered figure, the loop gives 3; the arithmetic floor is false (offsets 0/60/120/180, gamestop 240 mod 900, amazon 540 mod 1800 give max 1); 4b committed before the attempt: true; byte-unchanged `current_interval`: true.
>
> **Superseded by this pass, beside and not over:** its "1 of 21" is not reproducible, because its seed set was not recorded (this pass: 3/21 over `_IDLE_SEED+0..20`, 2/20 over `20260881..900`). Its "13–32 across 5 seeds" now reads **11–30 across 21** and **13–29 across a disjoint 20**. Its "M43 CAUGHT, 5 tests" is **6** at `2508f3c`. Its full text is in `git show 57ea00b:.planning/phases/09-out-of-lockstep/09-VERIFICATION.md`.

---
_Verifier: Claude (gsd-verifier), 2026-09-14, re-verification of `570df66`_
