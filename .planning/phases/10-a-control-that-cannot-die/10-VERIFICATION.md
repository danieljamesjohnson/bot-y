---
phase: 10-a-control-that-cannot-die
verified: 2026-09-14T13:32:35Z
verified_at_commit: 052f35d   # HEAD; boty/ executable code identical to c5b2fe4 (052f35d and c5b2fe4's retailers.py change are AST-equal ignoring docstrings/comments, measured)
status: gaps_found
score: 13/16 must-haves verified (3 PARTIAL — criterion 1, criterion 3, and "the prose does not outrun the flag")
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 8/11
  previous_verified: 2026-09-11T13:31:39Z   # that report is preserved below, under "PRIOR PASS", not deleted
  gaps_closed:
    - "Gap 1 (code): the 2026-09-02 read-2 shape, rendered and announcing a 308, no longer returns unresolved=True, and dead-control detection on the genuinely dead rendered fixture survives. Gated by tests that go red when the code is broken. Measured by this verifier, not taken from the commit"
    - "Gap 3 (record half): the § 0h reads are entered in docs/retailer-evidence.md; QUESTIONS.md § 0h, evidence L1250 and the ROADMAP's 'NOT SHIPPED' / 'NOT ON THE WIRE' all carry dated notes BESIDE the original text. The commit shows insertions only in those three files"
  gaps_remaining:
    - "Gap 2: narrowed, not closed. The two named not-established branches are honest, but a third reachable path still asserts non-resolution beside unresolved=False"
    - "Gap 3 (live half): no live confirmation of either fix. Not authorised; stays MET IN PART"
  regressions: []
gaps:
  - truth: "The detail text does not assert non-resolution when `unresolved` is False (prior gap 2)"
    status: partial
    reason: >
      57ea00b gates the sentence on `page_rendered and not announces_a_redirect`, but `unresolved` also
      needs `canonical_is_the_search_endpoint or markup_was_read`. A page that RENDERED, announces no
      redirect, and has neither a search-endpoint canonical nor cleanly parsed ld+json (the documented
      "RESIDUAL" at retailers.py, which includes a page with unparseable ld+json on a product canonical,
      i.e. the class of the 2026-08-04 false dead at evidence L960) gets
      "sku X did not resolve to a product page" with `unresolved=False`. Reproduced offline (spot-checks
      E and F). `assess_health` on E then emits reason "the cause is not established" while
      `failing_controls` says "did not resolve to a product page". That is exactly the two surfaces
      disagreeing that prior gap 2 described, on a different input. The 08-04 page itself is now repaired
      by `ldjson_read`'s escape repair, so no CURRENTLY measured wire page is known to land here. The
      path is reachable, and the code comment "THE PROSE MUST NOT OUTRUN THE FLAG" claims more than the
      code delivers.
    artifacts:
      - path: boty/retailers.py
        issue: "L547-557: the non-resolution sentence is conditioned on `page_rendered and not announces_a_redirect`, not on the same predicate as `unresolved` (L565-569)"
      - path: tests/test_retailers.py
        issue: "No test pins the rendered / no-redirect / no-search-canonical / unparseable-or-absent-ld+json path in either direction"
    missing:
      - "Condition the non-resolution sentence on the exact `unresolved` predicate (or compute it once and use it for both), with a third not-established wording for the residual"
      - "A test for the residual shape asserting `unresolved is False` AND `'did not resolve' not in detail`, watched red"
  - truth: "Criterion 1: three states distinct and asserted separately, with membership of state one neither over- nor under-inclusive on measured shapes"
    status: partial
    reason: >
      Separation holds and is mutation-gated (M44 re-measured at HEAD: 11 killers). Over-inclusion on
      BOTH measured wire shapes is now repaired (gap 1 closed). What remains: the residual path above
      describes a state-three reading (the cause is not established) in state one's words. That is
      criterion 1's own defect with the direction reversed, in the prose rather than the flag.
    artifacts:
      - path: boty/retailers.py
        issue: "same as the gap above"
    missing:
      - "Closes with the gap above; nothing further"
  - truth: "Criterion 3: Best Buy's control is repaired, measured against a real reading, or replaced"
    status: partial
    reason: >
      Premise false (Collision 10, re-verified at HEAD). There was nothing to repair. The transport defect
      the reads exposed now has two offline-gated fixes and ZERO live observations. served/boty/status.json
      (read-only, 2026-09-14T13:31:29Z) holds Best Buy's control as `in_stock`, `checked: False`,
      `read_at` 2026-08-25T20:53:56Z, ~28,358 min old. No live read is authorised (QUESTIONS.md § 0h: "Zero
      further reads are still authorised"). MET IN PART is the honest landing. It is not improvable by
      argument and no later milestone phase takes it up (Phase 11 is Amazon/Target/Walmart).
    artifacts:
      - path: served/boty/status.json
        issue: "Best Buy control row unread since 2026-08-25. Production has observed neither fix"
    missing:
      - "A live Best Buy read through the shipped path. Dan's authorisation is required first. Do not spend one without it"
warnings:
  - id: W1
    finding: "Any announced redirect disarms dead-control detection, not just a redirect to a product"
    detail: >
      `parse.announced_redirect`'s docstring says "whether it looks like a product URL is the caller's
      question". The caller (retailers.py L534) never asks it: `announces_a_redirect = ... is not None`.
      Reproduced offline: the genuinely dead shape plus `<meta http-equiv="refresh" content="0;url=/">`
      (G), plus `NEXT_REDIRECT` back to the search endpoint itself (G2), and `unresolved-sku.html` plus a
      300 s periodic refresh (G3) all return `unresolved=False`. So a real dead control can be kept out of
      its own health arm by a redirect that names no product. Unmeasured on the wire. The direction claims
      less (not-established rather than dead). And "dead stays dead" is proved only against the August
      `unresolved-sku.html`: § 0h's dead-SKU read was reallocated, so Best Buy's CURRENT dead-search shape
      has never been captured.
    remedy: "Offline: require the announced target's path to look like a product path (Best Buy: `/product/…/sku/<sku>`, which is exactly what read 2 recorded), or narrow the docstring to what the code does. Test with G/G2/G3-shaped inputs, watched red"
  - id: W2
    finding: "The test docstring's 'corrections placed beside' refer to words that were edited OVER"
    detail: >
      c5b2fe4 changed `WHY THE FIX WAS TO WITHDRAW CLAUSE A` → `…TO GATE CLAUSE A…`, and `That signal existed
      on 2026-09-02 and was gone eight days later` → `…was absent from this capture eight days after
      2026-09-02`. It then added "TWO CORRECTIONS TO THE PARAGRAPH ABOVE … placed beside it", which quote
      "It said **WITHDRAW**" and "gone eight days later". Neither phrase is in the paragraph any more. The
      correction describes an original that no longer exists. That is beside-and-over at once, and it
      contradicts itself.
    where: "tests/test_retailers.py, docstring of test_the_live_search_shell_is_not_reported_as_a_dead_control (~L3531-3555)"
  - id: W3
    finding: "Residual ROADMAP drift"
    detail: >
      L90's index line still reads "(COMPLETE 2026-09-02 — in the tree, NOT on the wire)" with no dated
      note. The body note at L446 says on the wire since 2026-09-11, and c5b2fe4's message says all
      three phases' "NOT ON THE WIRE" were noted. Verdict-table row 3 (L425) still says the transport
      defect is "recommended, not fixed". The SUPERSEDED block (L408-419) sits above the table but not
      beside that row.
  - id: W4
    finding: "An unmeasured claim in the new evidence entry"
    detail: >
      docs/retailer-evidence.md L1455: "Both false-dead shapes have been reproduced against fixtures every
      day since". The rendered-redirect fixture was created 2026-09-14 07:59 local. The only earlier offline
      reproduction of that shape in the record is the 2026-09-11 verifier's synthetic B. Nothing records
      reproductions on 09-12 or 09-13.
  - id: W5
    finding: "The in-flight gate transcript is not a clean measurement of HEAD for M34–M44"
    detail: >
      verify-after.txt (EXIT=0, 40/40) reports M34–M44 kill counts +27..+30 above the 08:09 run.
      mutation_check.py builds EACH mutation's sandbox by copying the LIVE working tree at that moment.
      Uncommitted phase-11 edits to docs/retailer-evidence.md (+292), scripts/evidence_check.py,
      tests/test_evidence_check.py and README.md landed 08:24–08:27 local, during the run, and are still
      uncommitted. Re-measured by this verifier against a frozen `git archive HEAD` copy: baseline 1015
      passed / 29 skipped; M34 → 4 killers; M44 → 11 killers, matching 08:09 and 2026-09-11. So the
      inflation is an artifact of a moving tree, not a vacuous gate. But the transcript's second half
      measured a tree that is not HEAD, and its test half (1044 passed) predates those edits.
---

# Phase 10: A Control That Cannot Die — Verification Report (RE-VERIFICATION)

**Goal:** A control that stops resolving is reported as a **dead control**, a fact about our configuration,
and never as a refusal or a broken detector.
**Verified:** 2026-09-14T13:32:35Z at `052f35d` · **Status:** gaps_found · **Re-verification:** Yes. The prior
pass (2026-09-11, 8/11) is preserved in full below.

## Headline

**Gap 1 is closed, and I measured that myself.** Read 2's shape no longer reads as a dead control. The
genuinely dead page still does. The new tests turn red when the code is broken. **Gap 3's record half is
closed**, beside and not over. **Gap 2 is narrowed, not closed.** A third not-established path still
prints "did not resolve" beside `unresolved=False`. **Criterion 3 stays MET IN PART**: the premise is
false and there has been no live confirmation. **Best Buy still does not read**: its control row is
`in_stock`, `checked: False`, last read 2026-08-25, so production has observed neither fix. New this
pass: the redirect predicate is broader than its own docstring (W1). A correction docstring quotes words
that were edited out (W2). The gate transcript's mutation half ran over a tree that changed underneath
it (W5).

**Constraints kept.** No live request, no `boty check`, no restart. No write to `state.json`,
`pacer-state.json` or `status.json` (the last was read once, read-only). No `gsd-tools` write. No `make
verify-offline`. Every perturbation ran in a `git archive HEAD` scratch copy with
`PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`. Caches were cleared between each perturbation and
its revert, and each revert was `cmp`-confirmed byte-identical. This file is the only one written in the
repository.

## Observable Truths

| # | Truth | Status | Evidence (this pass) |
|---|---|---|---|
| 1 | C1: three states distinct, asserted separately; state-one membership right on measured shapes | ⚠ PARTIAL | Separation holds. M44 at HEAD kills 11 tests, including `test_state_one…`, `test_the_three_states_produce_three_different_reasons` and both C2 halves. Over-inclusion on both measured shapes is repaired (row 9). The residual prose defect remains (row 12) |
| 2 | C2: the conjunction, both halves apart | ✓ VERIFIED | Regression: both half tests are in M44's 11 at HEAD. Suite green (1044 passed / 0 skipped at 08:15) |
| 3 | C3: control repaired against a real reading, or replaced | ⚠ PARTIAL | Premise false (row 6). Zero live observations: `status.json` Best Buy control `in_stock`, `checked: False`, `read_at` 2026-08-25T20:53:56Z. Live read not authorised |
| 4 | C4: D1–D5 applied to every control, failures named | ✓ VERIFIED (regression) | No config change touches the control. `HEAD:config/products.yaml` has `6216393` exactly once (L283, `control: true`) and `6577129` once, in a comment (L241). Suite green |
| 5 | C5: verify-offline 0, new mutation CAUGHT | ✓ VERIFIED | Transcript: `VERIFY: PASS (OFFLINE…)`, `EXIT=0`, 1044 passed, mypy clean on 18 files, identity PASS on 282 files, 40/40. **Because of W5, I re-measured M44 myself against frozen HEAD: CAUGHT, 11 killers** (listed in W5's source run) |
| 6 | Premise correction: offline, independent, unconditional; re-measured citations hold | ✓ VERIFIED | Every figure in 10-DECISIONS' 2026-09-14 table re-measured against `HEAD:docs/retailer-evidence.md` (5,500 lines): four transcripts at **L2127/2369/2771/2898**; L860, L960 unmoved; host failures **L3967/L4882**; `6577129` L822/868/901; config L241 / L283; `6216393` count **25**; the 7 originals are all still at their lines. `"did not resolve"` → **3 lines, L960/L1067/L1242**. L1067 is § 0g read 1's `Result.detail` transcription and L1242 is prose naming the branch, so the finding survives exactly as re-stated. ℹ Two of the "anchors that cannot drift" are not unique: `InStock from Best Buy` returns 7 lines and `no Chrome/Chromium` returns 8, so the reader must filter to the indented `CONTROL` rows |
| 7 | Fix (a): the `<body>` gate is real | ✓ VERIFIED | P4 (`page_rendered = True`) → 2 failed: `test_the_live_search_shell_is_not_reported_as_a_dead_control`, `test_every_verdict_path_carries_the_store_including_the_unknowns` |
| 8 | Fix (b): a genuinely dead rendered page is still detected | ✓ VERIFIED (scope caveat W1) | Spot-check D: `unresolved-sku.html` → `unresolved=True`, `assess_health` → `dead_control=True`. P5 (`announced_redirect` always returns a target) → 7 failed, including `test_a_rendered_search_page_with_no_product_is_still_a_dead_control`. `announced_redirect(unresolved-sku.html)` is `None`: its 6 `http-equiv` hits are all `origin-trial`. **Only the August fixture proves this** (W1) |
| 9 | Fix (c): **both** measured false-dead shapes are no longer dead | ✓ VERIFIED (was PARTIAL) | A (09-10 capture) → `False`, "the page did not render". **B (the reconstruction) → `False`**, "the page announced a redirect…". B1 (meta only) and B2 (`NEXT_REDIRECT` only) also → `False` each. C (real head + empty body) → `True`, with the detail consistent with the flag. P1, P2 (drop the flag term only), P6 (swap reasons) and P7 (`announced_redirect` always `None`) each turn red |
| 10 | Fix (d), RE-SCOPED: no speculative redirect-**following** code; what reads redirects is a gated reader | ✓ VERIFIED | The 2026-09-11 wording ("redirect helpers only in comments") is **false by design at HEAD**, and is superseded rather than failed: `announced_redirect` (parse.py L994) was restored on purpose. Non-comment redirect code in `boty/` is exactly `_META_REFRESH_RE`, `_NEXT_REDIRECT_RE` and `announced_redirect`, plus the call at retailers.py L534. None of it follows a redirect or fetches anything |
| 11 | Standing invariants from phases 8/9 | ✓ VERIFIED | `Pacer.current_interval` source span is **identical at `a58e7ac` (pre-phase-9), `57ea00b` and HEAD** (string equality). ℹ The `6da39ac5…449108` digest cited in the prior pass is recorded in 09-05-SUMMARY as **unreproducible, recorded without its recipe**. My extraction hashes to `6fc511b4…598b72` (7,993 chars / 8,017 B) at all three commits. Equality is the check. `COOLOFF_SECONDS` 259200, `REFUSALS_BEFORE_COOLOFF` 30. Post-restart `boty/` changes: `052f35d` pacing.py and `c5b2fe4` retailers.py are AST-equal to their parents ignoring docstrings and comments |
| 12 | NEW — gap 2: the detail does not assert non-resolution when `unresolved` is False | ⚠ PARTIAL | ✓ fragment path (`no_offers`, no `<body>`) → "could not establish…", `unresolved=False`, pinned by `test_every_verdict_path_carries_the_store…` (P3 reddens it). ✓ redirect path pinned (P1, P6). **✗ E: `<html><head></head><body>hello</body></html>` → `unresolved=False`, detail "sku 6216393 did not resolve to a product page…"; ✗ F: rendered, product canonical, unparseable ld+json → `unresolved=False`, same sentence plus "(1 ld+json block(s) present, 1 unparseable)".** `assess_health([E])`: reason "…the cause is not established"; `failing_controls` "…did not resolve to a product page…" |
| 13 | NEW — the reconstruction is faithful in everything the predicate reads, and declares what is synthetic | ✓ VERIFIED | Byte diff against `search-shell-2026-09-10.html`: identical through `</script></head>`. The only change is `</html>` → a `<body>` holding an HTML comment "RECONSTRUCTION, NOT A CAPTURE", the meta-refresh, a filler div, and `NEXT_REDIRECT;replace;/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ/sku/6216393;308;` twice. Those are the markers quoted at evidence L1219-1223, verbatim, and the evidence also says "twice more". `<body>` 1, `ld+json` 0, canonical `searchpage.jsp?id=pcat17071&st=6216393` (matches the read-2 table). Declared in the filename, sidecar (`"reconstruction": true`, no `captured_at`, "no claim rests on the byte count" at 23,923 B vs 150,974 B), the in-file comment and the test docstring. The gate warns "age unknown", which is true. ℹ The 09-10 sidecar's `T00:00:00Z` is a declared placeholder |
| 14 | NEW — the new tests bite (my red-watch, not the commit's) | ✓ VERIFIED | Scratch baseline: 221 passed. **P1** `announces_a_redirect = False` → 1 failed (the adapter test alone; matches the commit). **P7** returns `None` → 3 failed (adapter test + 2 parse tests; matches). **P2** drop `not announces_a_redirect` from the flag only → 1 failed. **P3** unconditional old prose → 2 failed. **P6** swap reasons → 1 failed. **P5** always a target → 7 failed. Final run: 221 passed |
| 15 | NEW — gap 3 record entries exist BESIDE, not OVER | ✓ VERIFIED (drift in W2–W4) | evidence **L1436** § "2026-09-10 — the two § 0h reads" (lateness recorded, transcribed-not-re-measured declared, "Best Buy still does not read" kept separate). **L1257** "NARROWED 2026-09-14" sits below the unedited L1250 sentence. QUESTIONS § 0h "CORRECTED 2026-09-11 and 2026-09-14" sits below the unedited OUTCOME, and both overstated claims are addressed. ROADMAP L408 "SUPERSEDED…" beside L404, and L446 "ON THE WIRE SINCE…" beside L443. c5b2fe4 is **insertions only** in ROADMAP, QUESTIONS, evidence and DECISIONS. Its 6 deletions are all in `tests/test_retailers.py` (see W2) |
| 16 | NEW — Collision 10 re-measurement is correct and its surviving finding is sound | ✓ VERIFIED | See row 6. ℹ "+485 each" holds for the four transcripts and two host failures. "The Best Buy section itself did not move" holds for L790–L972 |

**Score: 13/16 verified, 3 partial, 0 behavior-unverified.**

## Behavioral Spot-Checks (offline, `_verdict_from_html` direct, frozen HEAD copy)

| Input | unresolved | detail (abridged) | Meaning |
|---|---|---|---|
| A `search-shell-2026-09-10.html` | False | could not establish … did not render | ✓ |
| B `search-shell-rendered-redirect-2026-09-02.html` | **False** | could not establish … announced a redirect | ✓ gap 1 closed |
| B1 real head + body(meta only) | False | … announced a redirect | ✓ either spelling alone |
| B2 real head + body(`NEXT_REDIRECT` only) | False | … announced a redirect | ✓ |
| C real head + `<body></body>` | True | did not resolve | flag and prose agree |
| D `unresolved-sku.html` | **True** | did not resolve | ✓ dead stays dead |
| E rendered, no canonical, no ld+json, no redirect | False | **did not resolve** | ✗ prose outruns flag |
| F rendered, product canonical, unparseable ld+json | False | **did not resolve** (…1 unparseable) | ✗ prose outruns flag |
| G dead shape + meta refresh `url=/` | False | … announced a redirect | ⚠ W1 |
| G2 dead shape + `NEXT_REDIRECT` to the search endpoint | False | … announced a redirect | ⚠ W1 |
| G3 `unresolved-sku.html` + `content="300;url=…"` | False | … announced a redirect | ⚠ W1: a real dead page disarmed |
| H live shape, meta with `content` before `http-equiv` | True | did not resolve | ℹ attribute-order sensitive. Unmeasured on the wire, and read 2 also carried `NEXT_REDIRECT`, which B2 shows is sufficient |

`assess_health`: A and B → `dead_control=False`, "cause is not established", and `failing_controls` agrees.
D → `dead_control=True`. **E → reason "cause is not established" but `failing_controls` "did not resolve"** (gap 2).

## Red-Watch (frozen HEAD copy; caches cleared and a `cmp` restore after every perturbation)

| # | Perturbation | Result |
|---|---|---|
| — | baseline `test_retailers.py` + `test_parse.py` | 221 passed |
| P1 | `announces_a_redirect = False` | 1 failed: `test_a_rendered_page_that_announces_a_redirect_is_not_a_dead_control` |
| P2 | drop `and not announces_a_redirect` from `unresolved` only | 1 failed: same test |
| P3 | detail condition → `if True` (old unconditional prose) | 2 failed: `…carries_the_store_including_the_unknowns`, `…announces_a_redirect…` |
| P4 | `page_rendered = True` | 2 failed: `…live_search_shell…`, `…carries_the_store…` |
| P5 | `announced_redirect` always returns `"x"` | 7 failed: clause A, clause B, refused-and-unresolved, `…rendered_search_page_with_no_product_is_still_a_dead_control`, 3 parse negatives |
| P6 | swap the two not-established reasons | 1 failed: `…announces_a_redirect…` |
| P7 | `announced_redirect` always returns `None` | 3 failed: adapter test + `…two_measured_redirect_spellings…` + `…only_a_moved_status…` |
| — | final | 221 passed |
| M34 / M44 | harness functions, sandbox built from the frozen HEAD copy | baseline 1015 passed / 29 skipped · M34 **4** · M44 **11** |

## Requirements Coverage

| Req | Status | Evidence |
|---|---|---|
| REQ-24: dead control distinguishable, never a refusal or detector failure | ✓ SATISFIED for the flag on measured shapes · ⚠ prose residual | Rows 1, 2, 8, 9, 12 |
| REQ-24: "Best Buy's current dead control is repaired" | ✗ premise false | Row 6 |
| DoD 3: repair confirmed on a real reading · dead state reachable in a test | ✗ · ✓ | Row 3 · rows 1, 8 |

## Anti-Patterns / Record Drift

| Where | Finding | Severity | vs prior pass |
|---|---|---|---|
| `QUESTIONS.md` § 0h "The false dead is gone" | Dated correction beside it | — | **fixed** |
| `boty/retailers.py` clause-B comment | "not seen, not cannot happen" note beside it (comment-only, AST-equal) | — | **fixed** |
| `tests/test_retailers.py` "WITHDRAW" docstring | Fixed by editing OVER, then a "beside" correction that quotes the removed words | ⚠ W2 | **fixed, but introduced a new contradiction** |
| `boty/parse.py` `announced_redirect` docstring | "product URL is the caller's question", but the caller does not ask it | ⚠ W1 | **new** |
| `boty/retailers.py` "THE PROSE MUST NOT OUTRUN THE FLAG" | Claims the defect is gone; E/F show it is not | ⚠ gap 2 | **new** (overclaim) |
| ROADMAP L90, L425 | Stale "NOT on the wire" index line; row 3 "recommended, not fixed" | ⚠ W3 | partly carried |
| evidence L1455 "every day since" | Unmeasured | ℹ W4 | **new** |
| 10-DECISIONS anchors | Two anchors non-unique (7 and 8 lines) | ℹ | **new** |
| Debt markers (TBD/FIXME/XXX) in files touched by 57ea00b / c5b2fe4 | none found | — | — |

## Not Conflated

**Best Buy still does not read.** The tree's records keep this apart from "the monitor is honest":
evidence L1436's "What is NOT claimed", ROADMAP L417-418 and L456-458. I found no record in the tree
that blurs the two. The three claims stay separate. **In the tree:** both fixes. **On the wire:** only the
`<body>` gate. `57ea00b` and `17d3e5d` came after the 2026-09-11 restart, and every later `boty/`
change is comment- or docstring-only. **Observed:** neither.

## Gaps Summary

One root cause behind the remaining code gap: **the sentence and the flag are computed from different
predicates.** Fixing that closes gap 2 and criterion 1 together, offline, with one test. W1 is the same
kind of looseness on the other side. The reader accepts any redirect while its docstring promises a
product-path check. Also offline. Criterion 3 cannot move without a live read Dan has not authorised,
and it should not be argued upward.

---

## PRIOR PASS — 2026-09-11T13:31:39Z (superseded by the pass above; kept unedited beside it)

> Frontmatter of that pass, as it was: `status: gaps_found` · `score: 8/11 must-haves verified (3 PARTIAL —
> criteria 1 and 3, and the post-close "shell is no longer a false dead")` · `re_verification: null`.
> Its three gaps were: (1) the rendered-redirect false dead; (2) the detail text unconditional on
> `unresolved`; (3) the record: ROADMAP "NOT SHIPPED"/"NOT ON THE WIRE" undated, no § 0h entry in
> the evidence log, L1250 un-narrowed. Their dispositions are in `re_verification` above.

### Headline (2026-09-11)

The **partition is real and mutation-gated**. The **premise correction is sound and unconditional**. The
**09-10 fix is real and gated in both directions**. But the fix repairs **one of the two measured
false-dead shapes**, and the tree's own evidence log already holds the counterexample. **Criteria 1 and
3 stay MET IN PART. Neither moves up.**

### Observable Truths (2026-09-11)

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | C1: three states distinct, asserted separately | ⚠ PARTIAL | Separation holds: 7 named tests pass (`test_state_one/two/three…`, `test_the_three_states_produce_three_different_reasons`, both C2 halves, the mixed-group test ×3) and M44 kills them. Membership of state one is **still over-inclusive** for a measured wire shape (gap 1), and the prose it carries is too (gap 2) |
| 2 | C2: the conjunction, both halves apart | ✓ VERIFIED | `…half_one_…never_says_the_retailer_refused_us` and `…half_two_…does_not_silence_a_refusal` pass separately. Latent-only confirmed: the loader returns **6 controls over 6 distinct retailers**, so no mixed group is reachable today |
| 3 | C3: control repaired against a real reading, or replaced | ⚠ PARTIAL | Nothing to repair (row 6). Read ③ `IN_STOCK $59.99` is real. The follow-on fix has no live confirmation (gap 3) |
| 4 | C4: D1–D5 applied to every control, failures named | ✓ VERIFIED | Loader: 6 controls; `grep -c 'control: true'` = 7, and the 7th is the comment at `products.yaml:421`. `docs/adding-a-retailer.md:260-267` names all 6. **D4 fails 6/6.** Target's D5 is NOT SATISFIED. 13/30 cells fail. The "not circular" argument is at L353. `test_control_durability.py`: 16 pass |
| 5 | C5: verify-offline 0, new mutation CAUGHT | ✓ VERIFIED | **Run by me:** `VERIFY: PASS (OFFLINE…)`, EXIT=0, **1038 passed / 0 skipped**, mypy clean on 18 files, ruff clean, identity PASS on 276 files, **40/40 caught**. `M44 boty/monitor.py: 11 test(s) failed`. Anchor present exactly once |
| 6 | Premise correction: offline, independent, unconditional | ✓ VERIFIED | Re-opened in the evidence log: 4 transcripts `in_stock … $59.99 … InStock from Best Buy` (**now L2063/2305/2707/2834**; cited L1642… have drifted by +421). L960 is the 08-04 false dead. `6577129` is a product watch (L822/868/901) and appears in config only in a comment. Collision 10 was committed 2026-09-02 07:22 CDT, **before** read 1 (09:13 CDT), so it could not have been conditioned on the wire |
| 7 | Fix (a): the gate is real | ✓ VERIFIED | `retailers.py:495,510`. **Red-watched by me in a scratch copy:** removing the gate reddens `test_the_live_search_shell_is_not_reported_as_a_dead_control`, and `unresolved=False` reddens `test_a_rendered_search_page_with_no_product_is_still_a_dead_control`. Caches cleared between runs |
| 8 | Fix (b): a genuinely dead rendered page is still detected | ✓ VERIFIED | `unresolved-sku.html` → `unresolved=True` (named test + my spot-check) |
| 9 | Fix (c): the shell is no longer a false dead | ⚠ PARTIAL | **09-10 capture** → `unresolved=False` ✓. **09-02 read-2 shape** (body + 308 to a live product) → `unresolved=True` ✗ (gap 1) |
| 10 | Fix (d): no speculative redirect code left | ✓ VERIFIED | `NEXT_REDIRECT`/`http-equiv`/redirect helpers appear in `boty/` only in comments. Post-close diff of `boty/` touches `retailers.py` (the gate) and `cli.py` (7028b19, the clock) only |
| 11 | Standing invariants from phases 8/9 | ✓ VERIFIED | `current_interval` sha256 `6da39ac5…449108`, 7994 chars / 8018 B, **unchanged**. `MAX_BACKOFF` 6h. `COOLOFF` 259200. `STATE_VERSION` 2. Staleness grep = 2. `INTENTIONAL GAP` = 10. M21–M24 absent. Both clock terms present: 7028b19 (post-close) routes them through an injected `monotonic` whose default is `time.monotonic`. That changes the form, not production behaviour |

**Score (2026-09-11): 8/11 verified, 3 partial, 0 behavior-unverified.**

*Notes added 2026-09-14, beside the 2026-09-11 table, which is not edited:* row 6's "+421" was correct
when measured; it is +485 at HEAD. Row 10's claim became false by design on 2026-09-11 (`57ea00b`
restored `announced_redirect`) and is re-scoped in row 10 above. Row 11's digest is recorded in
09-05-SUMMARY as unreproducible; source-span equality is the check used above.

### Behavioral Spot-Checks (2026-09-11, offline, `_verdict_from_html` direct)

| Input | unresolved | Meaning |
|---|---|---|
| A: `search-shell-2026-09-10.html` as captured (no `<body>`) | **False** | fix works on this shape |
| B: same head + `<body>` carrying read 2's meta-refresh/`NEXT_REDIRECT;…;308` to the LIVE product | **True** | **false dead survives** |
| C: same head + empty `<body></body>` | **True** | the gate is exactly `"<body" in html` |
| D: `unresolved-sku.html` (genuinely dead, rendered) | **True** | dead stays dead |
| `assess_health([A])` | `dead_control=False`, reason "cause is not established" | but `failing_controls` says "did not resolve to a product page" (gap 2) |

B is synthetic in its content, but not in anything the predicate reads. The predicate reads three
things: `<body` presence, the canonical's path, and ld+json blocks/unparseable. B's values for all three
are the ones recorded for read 2 at `retailer-evidence.md:1204-1206`.

**A confound in the 09-10 rationale, recorded, not decisive.** "The redirect signal … was gone eight days
later" compares a 25 s-settle read (09-02 read 2) against a capture whose settle is **not recorded**.
That capture matches **09-02 read 1** (3 s): ~22 KB, no body, 10 stylesheets, `opt-targeting` still
`queryType: search`, and read 1 never recorded a `NEXT_REDIRECT` either. So the signal may not be gone.
It may simply not have arrived by 3 s. That doesn't change the fix. It does weaken "withdrawn because
transient", and it is why B is a live risk: the shipped 3 s settle avoids B only while Best Buy renders
slower than 3 s.

### Requirements Coverage (2026-09-11)

| Req | Status | Evidence |
|---|---|---|
| REQ-24: dead control distinguishable, never a refusal or detector failure | ✓ SATISFIED for true deads | Rows 1, 2, 8. M44 |
| REQ-24: "Best Buy's current dead control is repaired" | ✗ premise false | Row 6. There was nothing to repair |
| DoD 3: repair confirmed on a real reading · dead state reachable in a test | ✗ · ✓ | Gap 3 · rows 1, 8 |

### Anti-Patterns / Record Drift (2026-09-11)

| Where | Finding | Severity |
|---|---|---|
| `QUESTIONS.md` § 0h | "The false dead is gone": contradicted by evidence L1204 | ⚠ (gap 1) |
| `boty/retailers.py:493-494` | Comment says clause B "needs no gate and is untouched", but L510 gates it too. Also, "a document that never rendered cannot meet `ld.blocks > 0`" is unmeasured, since ld+json can sit in `<head>` | ⚠ prose ≠ code |
| `tests/test_retailers.py:3520` | Docstring "WHY THE FIX WAS TO **WITHDRAW** CLAUSE A", while the code, the commit and the sibling test all say withdrawal was **refused** | ⚠ prose ≠ code |
| ROADMAP closing record | "NOT SHIPPED" / "NOT ON THE WIRE" stale; cited evidence lines off by +421 | ⚠ (gap 3) |
| Debt markers (TBD/FIXME/XXX) in phase-touched files | none | — |

### Not Conflated (2026-09-11)

Deployed 2026-09-11 07:56:33 (PID 746345). **Best Buy still does not read.** Its control row is the
remembered `in_stock`, `checked=false`, and state.json holds only `availability`/`read_at`. So
**production has made zero observations of the fix.** Honesty about an unreadable retailer ≠ a readable
retailer. **Incidental, out of scope, but live:** since the deploy, every Walmart health warning fails
Telegram delivery (`Unsupported start tag "redacted"`, HTTP 400, retried every ~5 min). The cause is
`notify.py:73`'s `store <redacted>` under HTML parse mode, which is not phase-10 code. As a result a
health warning has not reached the phone since the restart.

### Gaps Summary (2026-09-11)

One root cause, three faces. The 09-10 fix chose `<body>` presence as the discriminator on **three
captures** and left out a **fourth measurement already in the tree**, which contradicts it. Everything
needed to close gaps 1 and 2 is offline: read 2's shape is fully recorded. Gap 3's record edits are
offline. Its live half (confirming anything on the wire) needs a read that is **not authorised**, and
stays MET IN PART until one is. **No live request, restart, or state write was made by this
verification. Only this file was written.**

_Verifier (both passes): Claude (gsd-verifier)_
