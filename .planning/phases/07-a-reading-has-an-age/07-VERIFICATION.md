---
phase: 07-a-reading-has-an-age
verified: 2026-08-17T14:11:17Z
verified_at_head: 9e7d302
status: gaps_found
score: 3/5 must-haves verified (2 MET IN PART, independently confirmed as partial)
overrides_applied: 0
gaps:
  - truth: "SC-3: A reading older than its retailer's current interval is presented as stale in `status.json`, `boty check` and the dashboard, and the staleness is derived from the retailer's own pacing rather than a fixed clock"
    status: partial
    reason: "Two of three surfaces verified by execution. `status.json` publishes the three ingredients of a staleness verdict (`read_at`, `checked`, `current_interval_seconds`) and no verdict. `presented as stale` and `sufficient to derive staleness` are different sentences. The phase's own MET IN PART is accurate and is NOT rounded up here."
    artifacts:
      - path: "boty/status.py"
        issue: "No `stale` key on any watch row — deliberate, argued at status.py:280-289 against a write-time flag that would be written `false` and keep saying `false` for exactly the interval during which it becomes true"
    missing:
      - "Either a consumer-computable verdict in `status.json` that cannot go stale at write time (e.g. `stale_after` = read_at + current_interval, a fact rather than a flag), or an accepted override recording that the ingredients-plus-join-test form is the settled answer"
  - truth: "SC-5: `make verify-offline` exits 0, and every gate this phase adds has been watched going red"
    status: partial
    reason: "`make verify-offline` EXIT=0 independently re-run at HEAD 9e7d302 (883 passed / 1 skipped, 34/34 mutations, identity 222 files). The `every gate` half is still not fully met, and the post-review evidence WIDENS the shortfall rather than narrowing it: (a) 07-05's join test `test_status_json_carries_everything_a_consumer_needs_to_judge_staleness` was never observed failing — the phase's own named exception; (b) CR-01 showed the phase's escaping gate could not bite on a sink 07-04 itself opened, i.e. a gate that existed and was blind; (c) `test_the_dashboard_script_parses` skips in the environment `make verify-offline` actually runs in on this host."
    artifacts:
      - path: "tests/test_status.py:1243"
        issue: "Join test never watched red (recorded honestly by 07-05, not hidden)"
      - path: "tests/test_dashboard.py:464-491"
        issue: "node --check gate SKIPS under the PATH `make verify-offline` inherits; measured `no JavaScript runtime on PATH` in this verifier's own run"
    missing:
      - "A decision on whether a gate that skips in the project's own gate environment counts as a gate this phase adds"
      - "Either an accepted override for the join test, or the record left as MET IN PART (current state, and defensible)"
  - truth: "The phase closing record states measurements that match the tree"
    status: failed
    reason: "Five measurable numbers in the closing record are now wrong at HEAD. Re-measured by this verifier at 9e7d302, not taken from any document."
    artifacts:
      - path: ".planning/ROADMAP.md:418-449"
        issue: "Cites `all 20 Result( construction sites`, partition `11 / 9`, `865 passed`, `33/33 mutations`, `identity check: PASS — 220 file(s)`, `the ratio rose from 26/26 to 33/33`. Measured at HEAD: 21 sites, partition 12 / 9, 883 passed + 1 skipped, 34/34, identity 222 file(s), registry M1-M20 + M25-M38."
      - path: ".planning/REQUIREMENTS.md:29"
        issue: "REQ-21 traceability cell repeats `all 20 Result( construction sites`, `11 / 9`, `Gate: 26/26 → 33/33`"
      - path: "docs/retailer-evidence.md:4097-4101"
        issue: "Phase 7 closing record table repeats `all 20`, `11 / 9`, `33/33`"
    missing:
      - "A dated post-review addendum beside the closing record (not over it, per this project's own convention) recording the nine review fixes and the re-measured figures: 883 passed / 1 skipped, 34/34, identity 222, 21 Result sites, 12/9 partition, M38 registered"
  - truth: "Criterion 4's evidence is described accurately"
    status: failed
    reason: "The closing record claims the age `was observed surviving a real two-process restart`. No such test exists. Grep for `subprocess` across tests/test_monitor.py and tests/test_cli_watch.py returns nothing; the restart is modelled as two in-process `watch_loop` calls sharing one `state_path`, which `tests/test_cli_watch.py:1331-1335` itself calls a model. The BEHAVIOUR is verified — the age survives a real file round-trip and is not invented — but `real two-process restart, not a mocked one` overstates the measurement, in a phase whose thesis is that a claim must not exceed what was observed."
    artifacts:
      - path: ".planning/ROADMAP.md:421"
        issue: "`observed surviving a **real two-process restart**, not a mocked one`"
      - path: "docs/retailer-evidence.md:4100"
        issue: "`The age was observed surviving a **real two-process restart**.`"
    missing:
      - "Correct the wording to what was measured: two `watch_loop` calls sharing one `state_path`, each building its own `State`/`Pacer`, with both ends asserted (bytes on disk and what a fresh `State.load` makes of them). Or add a genuine subprocess-boundary test."
deferred: []
human_verification:
  - test: "Decide whether to close the SC-3 gap with a non-staling fact in `status.json` (e.g. `stale_after`) or to accept the ingredients-plus-join-test form via an override"
    expected: "A recorded decision; the criterion text stays unedited either way"
    why_human: "This is a design judgement about what `presented as stale in status.json` should mean, not a fact discoverable in code"
  - test: "Decide whether `sudo systemctl restart boty` happens. Measured at 2026-08-17 14:11Z: `served/boty/status.json` (mtime 08:59 today) carries 10 watch rows, 0 with a `read_at` key, 0 with a `checked` key, and 6 retailer rows with no `current_interval_seconds`. `state.json` still holds 13 bare pre-07 strings and 0 stamps."
    expected: "Either a restart, or the deferral restated with its date"
    why_human: "Deploy is the user's explicit decision, answered `keep defer` on 2026-08-17 and `defer` on 2026-08-10. Not performed and not recommended here."
  - test: "Look at the dashboard in a GPU-backed browser with a payload carrying mixed fresh/stale/undated rows"
    expected: "Dim `.tag.age` on fresh rows, amber `.tag.age.warn` on stale and undated rows, `not checked` beside remembered rows"
    why_human: "Visual weight and legibility. The markup and the branch logic are verified by execution below; how it LOOKS is not."
---

# Phase 7: A Reading Has an Age — Verification Report

**Phase Goal:** Every reading says when it was taken, and a reading too old to trust is shown as stale rather than as fact — or says it does not know.
**Verified:** 2026-08-17T14:11:17Z at HEAD `9e7d302`
**Status:** gaps_found
**Re-verification:** No — initial verification
**Requirements:** REQ-21

Everything below was measured at HEAD by this verifier. Where a figure came from a
document rather than from a command, it says so. Where something could not be confirmed,
it says that instead of inferring.

## Goal Achievement

### Observable Truths — the ROADMAP's five Success Criteria

| # | Truth | Status | Evidence (measured at HEAD `9e7d302`) |
|---|-------|--------|----------|
| 1 | Every `Result` records when it was read, and that time is published per watch in `status.json` | ✓ VERIFIED **in the tree**; NOT on the wire | AST gate `tests/test_retailers.py::test_every_result_construction_in_retailers_names_read_at` run standalone: **2 passed**. It asserts **21** `Result(` call sites (not 20 — WR-07 added one) and that none inherits the default. Partition gate asserts **12 read / 9 non-read** (not 11/9). Executed `status.write` against the **real** `config/products.yaml` (13 watches) and the **real** `state.json`: **13/13 rows carry a `read_at` key**, `"read_at": 0` absent from the serialised bytes. Live served file measured separately — see the wire row below |
| 2 | A reading with no recorded time is shown as UNKNOWN age, never as current — watched going red | ✓ VERIFIED | Executed `boty.cli._age_tag` directly — `undated → [age ?]`, `fresh → [age 4s]`, `stale → [age 7h > 6h]`, `no cadence → [age 3h, cadence ?]`. Executed `ageTag` out of `served/boty/index.html` in node — `undated → <span class="tag age warn">age ?</span>`, missing key → same. Tag is appended **unconditionally** (`boty/cli.py:334`, inline at `index.html:296`), so an absent tag cannot mean fresh. `CAUGHT M36 boty/cli.py: 1 test(s) failed — test_report_says_unknown_for_a_reading_nobody_dated` in this verifier's own mutation run |
| 3 | A reading older than its retailer's current interval is presented as stale in `status.json`, `boty check` **and** the dashboard, derived from the retailer's own pacing | ⚠️ **MET IN PART** — independently confirmed as partial | **The two rendering surfaces are MET, by execution.** `_age_tag` prints `[age 7h > 6h]`; `ageTag` renders `<span class="tag age warn">7h ago > 6h</span>`. Both read the cadence from `retailers[].current_interval_seconds`, never from `index.html`'s banner constant — `CAUGHT M37 served/boty/index.html: 1 test(s) failed`. `Pacer.current_interval` is one number and `record` schedules **through** it (`boty/pacing.py:293`) — `CAUGHT M33: 11 test(s) failed`. **The `status.json` third is not settled:** the file publishes `read_at`, `checked`, `current_interval_seconds` and **no verdict** (`grep` for a `stale` key on a watch row: none; the design is argued at `boty/status.py:280-289`). A reader opening the file sees three numbers and must subtract against their own clock. I agree with 07-06: this is neither MET nor UNMET |
| 4 | The age survives a service restart, so a restart cannot make a two-day-old reading look fresh | ✓ VERIFIED (behaviour); ✗ the **description** of the evidence is wrong | Behaviour confirmed: `State.save` writes `{"availability": …, "read_at": self.read_at.get(key)}` (`boty/monitor.py:359`); `_remembered_stamp` bounds a restored stamp at **both** ends and rejects `bool` (`monitor.py:206-218`); `transitioned_to_stock` writes availability and stamp as one act or clears both (`monitor.py:397-400`). `CAUGHT M32 boty/monitor.py: 7 test(s) failed` — the mutation defaults a missing stamp to `now`. **But** no subprocess-boundary test exists (`grep -rn subprocess tests/test_monitor.py tests/test_cli_watch.py` → nothing); the restart is two in-process `watch_loop` calls sharing one `state_path`, which the test file itself calls a model. See gap 4 |
| 5 | `make verify-offline` exits 0, and every gate this phase adds has been watched going red | ⚠️ **MET IN PART** | **Gate half MET, re-measured by this verifier, not read from a document:** `identity check: PASS — 222 file(s)`, `883 passed, 1 skipped in 10.89s`, `Success: no issues found in 18 source files`, `mutation check: 34/34 mutations caught`, survivors none, `VERIFY: PASS (OFFLINE …)`, `EXIT=0`. **`every gate` half still not MET**, and for three reasons now rather than one — see gap 2 |

**Score:** 3/5 fully verified; 2 MET IN PART. Both partials are the ones 07-06 flagged, and I reached
them independently before reading its verdicts. **Neither was over-stated and neither was
under-stated** — the self-assessment is accurate in both directions on criteria 3 and 5.

### The wire, measured rather than assumed

The phase's `NOT ON THE WIRE` caveat is true and remains true:

| Artifact on disk | Measured 2026-08-17 14:11Z |
|---|---|
| `served/boty/status.json` (mtime 08:59 today, written by the running pre-phase daemon) | 10 watch rows for 13 configured watches; **0** rows carry `read_at`; **0** carry `checked`; 6 retailer rows, none carrying `current_interval_seconds` |
| `state.json` | 13 entries, **13 bare strings**, 0 dicts, 0 stamps |

The 10-of-13 row count is itself a live re-confirmation of the phase's own Finding 4 — the row
count is a function of pacing. Deploy is deferred by Dan's explicit answer (`keep defer`,
2026-08-17, recorded verbatim in `QUESTIONS.md` § 0f). No restart was performed or recommended here.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `boty/models.py` | `Result.read_at: float \| None = None` | ✓ VERIFIED | line 492, declared last |
| `boty/retailers.py` | stamp on all sites, partitioned | ✓ VERIFIED | 21 AST call sites, 12 variable / 9 literal-`None`, gate passes standalone |
| `boty/status.py` | `read_at` + `checked` per row, `current_interval_seconds` per retailer, one row per configured watch | ✓ VERIFIED | lines 183, 200, 290, 300, 374, 375; executed against real config + real ledger → 13 rows |
| `boty/monitor.py` | dated ledger, validated load, clock-free save | ✓ VERIFIED | `_remembered_stamp` 193-218, `save` 359, `transitioned_to_stock` 397-400 |
| `boty/pacing.py` | `Pacer.current_interval`, read-only, backoff may only widen | ✓ VERIFIED | 332-420; `.get` not `_for` (WR-04); outer `max` (WR-01) |
| `boty/config.py` | override held to floor **and** to the global interval | ✓ VERIFIED | 292-308 (WR-02) |
| `boty/cli.py` | `_age`, `_age_tag`, `_current_intervals`, `_remembered`, `commit=False` on the check path | ✓ VERIFIED | 122, 148, 225, 839; age clamped at 0 (WR-03, line 215) |
| `served/boty/index.html` | `.tag.age` / `.tag.age.warn`, `ageTag`, `fmtDur`/`fmtAge`, `esc(w.availability)` | ✓ VERIFIED | 118-119, 215-225, 294; executed in node |
| `scripts/mutation_check.py` | M31-M37 registered | ✓ VERIFIED — and **M38** beyond it | 34 idents: `M1`-`M20`, `M25`-`M38`. `M21`-`M24` remain Phase 6's deliberate gap |
| `tests/test_dashboard.py` | `UNTRUSTED` covers `w.read_at` **and** `w.availability` | ✓ VERIFIED | 106-117 |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `retailers._verdict_from_html` | `Result.read_at` | one wall-clock read, named at every return | ✓ WIRED | AST partition `_verdict_from_html: (0, 8)` |
| `status.write` | `r.read_at` | watch-row comprehension | ✓ WIRED | `status.py:290`, executed |
| `cli.watch_cycle` → `write_status` | `watches=`, `remembered=`, `intervals=` | keyword threading | ✓ WIRED | `cli.py:520-528` |
| `cli.main` check path → `write_status` | same three keywords | keyword threading | ✓ WIRED | `cli.py:896-903` |
| `pacing.record` | `Pacer.current_interval` | refusal branch computes its wait through the accessor | ✓ WIRED | `pacing.py:293` — one expression, so display and schedule cannot drift |
| `index.html ageTag` | `retailers[].current_interval_seconds` | `Map` built per tick, `intervals.get(w.retailer)` | ✓ WIRED | line 218 + 261; M37 kills the fixed-constant substitute |
| `index.html storeTag` | `w.checked === false` | early return | ✓ WIRED | line 167 |
| `monitor.State.load` | `_remembered_stamp` | one validated stamp per entry | ✓ WIRED | `monitor.py:314` |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| `status.json` watch rows | `read_at` | `Result.read_at` (fresh) / `State.read_at` (remembered) | Yes — executed against the real ledger; 13/13 rows carried the key, all `null` because this host's ledger is pre-07 | ✓ FLOWING (null is the correct, honest value here) |
| `status.json` retailer rows | `current_interval_seconds` | `cli._current_intervals` → `Pacer.current_interval` | Yes | ✓ FLOWING |
| `index.html` row | `w.read_at`, `intervals` | `status.json` | Yes, in the tree; **NOT** on the served file today | ⚠️ FLOWING in tree, DISCONNECTED on the wire (deploy deferred) |
| `index.html` dot class | `w.availability` | `state.json` via `_remembered_availability` | Yes, and now escaped at the sink | ✓ FLOWING |

### Behavioural Spot-Checks

| Behaviour | Command | Result | Status |
|---|---|---|---|
| Full offline gate | `make verify-offline` | `identity 222 · 883 passed, 1 skipped · 34/34 mutations · VERIFY: PASS · EXIT=0` | ✓ PASS |
| AST completeness gate | `pytest tests/test_retailers.py -k "read_at or partition"` | 2 passed | ✓ PASS |
| Four CLI age forms | executed `boty.cli._age_tag` | `[age ?]` · `[age 4s]` · `[age 7h > 6h]` · `[age 3h, cadence ?]` | ✓ PASS |
| Strict `>` boundary | `_age_tag` at exactly one cadence and one ms past | `[age 5m]` then `[age 5m > 5m]` | ✓ PASS |
| Negative age clamp (WR-03) | `_age_tag` with a stamp 10 s in the future | `[age 0s]` (was `[age -10s]`) | ✓ PASS |
| Four dashboard age forms | evaluated `ageTag` from `index.html` in node v24.16.0 | `age ?` warn · `4s ago` · `7h ago > 6h` warn · `3h ago · cadence ?` warn | ✓ PASS |
| XSS payload at the dot sink (CR-01) | evaluated `esc` from `index.html` | `&quot; onmouseover=alert(1) x=&quot;` — stays inside the attribute | ✓ PASS |
| One row per configured watch | executed `status.write` with real config + real `state.json` | 13 configured → **13 rows**, 13 `checked: false`, 13 `read_at: null`, **0 alertable** | ✓ PASS |
| Live wire state | read `served/boty/status.json`, `state.json` | 10 rows, 0 `read_at`; 13 bare strings, 0 stamps | ✓ PASS (confirms the NOT-ON-THE-WIRE claim) |
| Dashboard script parses | `pytest tests/test_dashboard.py` **with node on PATH** | 17 passed | ✓ PASS |
| Dashboard script parses | same, under the PATH `make verify-offline` inherits | 1 **skipped** — `no JavaScript runtime on PATH` | ⚠️ see gap 2(c) |

### Gates re-watched going red — independently, by this verifier

I did not take the fix commits' red counts on trust. Three regressions were re-applied in a
throw-away `git worktree` (the working tree was never touched; `git status --short` is empty and
the worktree is removed):

| Regression re-applied | Gate | Result |
|---|---|---|
| CR-01 — `${esc(w.availability)}` → `${w.availability}` | `test_every_retailer_controlled_string_is_escaped_before_innerhtml` | **RED** — 1 failed / 15 passed, offender named `w.availability in ${w.availability}` |
| WR-02 — delete the `seconds < global_interval` guard | `test_a_retailer_override_below_the_global_interval_is_refused` | **RED** — 1 failed / 35 passed |
| WR-03 — remove `max(0.0, …)` from `_age_tag` | `test_a_stamp_in_the_future_renders_as_no_age_rather_than_a_negative_one` | **RED** — 1 failed / 51 passed |

Every fix commit except `bc23a02` (WR-08, a docstring rewrite that adds no gate) carries a
`Watched going red:` paragraph with a failure count in its message. So the nine post-close fixes
were themselves gated to this project's standard.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| REQ-21 | 07-01, 07-02, 07-03, 07-04, 07-05, 07-06 (all six declare `requirements: [REQ-21]`) | A reading states when it was taken, and one too old to trust is presented as stale rather than as fact; staleness measured against the retailer's own current interval | ✓ SATISFIED **in the tree**, with criterion 3's `status.json` third partial | Every clause traced to executed code above. The requirement's own opening measurement — *Walmart's age could not be established at all because a restart zeroed the evidence* — is closed by `State.read_at` + `_remembered_stamp`, killed by M32 |

No orphaned requirements: `grep -E "Phase 7" .planning/REQUIREMENTS.md` maps REQ-21 and nothing else
to this phase, and all six plans claim it.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` / `HACK` / `TODO` across all nine phase-modified source files | — | **None found.** Debt-marker gate clean |

### Where the closing record no longer matches the tree

This is the finding the prompt asked to be judged plainly, and the answer is **yes, it misstates the
tree** — measured, not inferred:

| Claim in the closing record | Measured at HEAD `9e7d302` |
|---|---|
| `all 20 Result( construction sites` | **21** (WR-07 added the non-object-body arm) |
| read/non-read partition `11 / 9` | **12 / 9** |
| `865 passed` | **883 passed, 1 skipped** |
| `mutation check: 33/33` · `the ratio rose from 26/26 to 33/33` | **34/34**; M38 registered by the WR-01 fix |
| `identity check: PASS — 220 file(s)` | **222 file(s)** |

The drift is in the reassuring direction — the tree is stronger than its record — but the direction is
not the point. A closing record for *this* phase, of all phases, presenting a 2026-08-17-pre-review
reading as the current gate result is the milestone's own defect committed one level up, in the
document that certifies the defect removed. It is a documentation gap and it should be closed with a
dated addendum **beside** the record, on this project's own convention, rather than by editing the
record.

### Do WR-01 / WR-02 / WR-03 change a criterion verdict?

Judged rather than deferred:

- **WR-01** (a backoff above the cap inverted, shortening the wait) and **WR-02** (an override below
  the global interval published a cadence 3.4x tighter than the loop can keep) were both defects in
  the *one number* criterion 3 rests on. Both were **unreachable on the shipped `config/products.yaml`**
  (largest standing interval 1800 s against a 21 600 s cap; overrides are 900/1800 against a 300 s
  global). So criterion 3's verdict on the shipped configuration does not move. What they do change is
  the strength of the claim: before 2026-08-17 the "one number both surfaces read" invariant held by
  configuration rather than by construction. It now holds by construction, and M38 gates it.
- **WR-03** (`[age -10s]` on one surface where the other clamped) was a real divergence between the two
  surfaces criterion 3 requires to agree, on one input. Fixed and gated; criterion 3's rendering half
  is stronger than it was at close, not weaker.
- **CR-01** does bear on **criterion 5**. The escaping gate this phase relies on existed, was widened
  by 07-05 for `w.read_at`, and was still blind to `w.availability` — a sink 07-04 itself opened four
  plans earlier. That is not a gate that was never watched red; it is a gate that could not bite.
  This project's own recorded rule is that *a bound that cannot bind is worse than no bound*. It does
  not flip criterion 5 to UNMET — the criterion is about observing new gates fail, and every mutation
  was — but it is a third named reason the `every gate` half is not fully met, and it belongs in the
  record beside the join test.

### Gaps Summary

Four gaps, none of them a code defect and none blocking further work:

1. **SC-3, `status.json` third** — the file publishes the ingredients of a staleness verdict, not the
   verdict. Partial. The design reason is sound and demonstrated; the criterion's literal text is not
   satisfied. Rounding it up would be the exact act this milestone exists to prevent.
2. **SC-5, `every gate`** — one gate never watched red (the join test), one gate that could not bite
   (CR-01's escaping gate before it was widened), one gate that skips in the environment the project's
   own gate runs in (`node --check`). Partial.
3. **The closing record misstates the tree on five measurable numbers.** Actionable documentation gap.
4. **`real two-process restart` is not what was measured.** Actionable documentation gap; the
   behaviour it describes is verified, the description of the evidence is not.

Gaps 1 and 2 look **intentional and already recorded**. If they are the settled answer rather than
work to do, accept them explicitly rather than leaving them to be re-litigated at milestone audit:

```yaml
overrides:
  - must_have: "A reading older than its retailer's current interval is presented as stale in status.json"
    reason: "status.json publishes read_at, checked and current_interval_seconds and no derived flag, because a stale boolean computed at write time is written false and keeps saying false for exactly the interval during which it becomes true (pacing.py:196-199). Sufficiency is proved by tests/test_status.py:1243, which derives the verdict from those three keys and nothing else. Both rendering consumers do present the verdict."
    accepted_by: "dan"
    accepted_at: "{ISO timestamp}"
  - must_have: "every gate this phase adds has been watched going red"
    reason: "07-05's join test passed on the RED commit — that IS the measurement that the three published facts were already jointly sufficient, and manufacturing a red would have been theatre. The two later reasons (CR-01's blind gate, the opportunistic node --check skip) are recorded rather than absorbed."
    accepted_by: "dan"
    accepted_at: "{ISO timestamp}"
```

Gaps 3 and 4 should be **fixed, not overridden** — they are the phase's own standard applied to the
phase's own record.

---

_Verified: 2026-08-17T14:11:17Z at HEAD `9e7d302`_
_Verifier: Claude (gsd-verifier)_
_Method: goal-backward. Every figure above came from a command run during this verification. Nothing was taken from a SUMMARY, a PLAN or the ROADMAP._
