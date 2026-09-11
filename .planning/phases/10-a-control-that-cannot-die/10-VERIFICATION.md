---
phase: 10-a-control-that-cannot-die
verified: 2026-09-11T13:31:39Z
status: gaps_found
score: 8/11 must-haves verified (3 PARTIAL — criteria 1 and 3, and the post-close "shell is no longer a false dead")
behavior_unverified: 0
overrides_applied: 0
re_verification: null   # first verifier on this phase; it was closed without one
gaps:
  - truth: "Criterion 1 / post-close fix (c): a LIVE Best Buy control is not reported as a dead control"
    status: partial
    reason: >
      The 2026-09-10 fix (clause A gated on `<body>` presence) repairs ONE of the two false-dead shapes
      measured on the wire, not both. 2026-09-02 read 2 (docs/retailer-evidence.md:1198-1206) was a
      RENDERED document — 150,974 B, `<body>` present, 0 ld+json, canonical on the search endpoint,
      SKU alive (308 to its product page). Those are the only inputs to the predicate, and all three
      satisfy the shipped code. Reproduced offline: that shape still returns `unresolved=True`.
      QUESTIONS.md § 0h's "The false dead is gone" and the fix commit's "discriminator ... separates the
      two cases" are rounded up. The claim holds only for the head-only shape seen at the shipped 3 s
      settle, which was observed twice (09-02 read 1, 09-10 read ②).
    artifacts:
      - path: boty/retailers.py
        issue: "L495/L510: `page_rendered and (A or B)`. A rendered search shell mid-redirect for a live SKU is still clause A."
      - path: QUESTIONS.md
        issue: "§ 0h OUTCOME: 'The false dead is gone' contradicts a measurement already in docs/retailer-evidence.md:1204"
      - path: tests/test_retailers.py
        issue: "No test pins the read-2 (rendered, redirecting) shape in either direction"
    missing:
      - "Record, beside § 0h and beside the retailers.py comment, that the rendered-redirect shape measured 2026-09-02 is still a false dead under the fix"
      - "An offline test that pins read 2's recorded shape: either xfail/strict documenting the defect, or a fix that makes it pass. Nothing further needs a live read"
  - truth: "Criterion 1: a reading that establishes nothing does not assert non-resolution"
    status: partial
    reason: >
      After the fix, the unrendered shell reaches the health arm that says "the cause is not
      established", which is honest. But the per-control line in the same Health still reads
      "sku 6216393 did not resolve to a product page — no schema.org Product on it carries that sku".
      That is a sentence of deadness about a live SKU. The flag was fixed and the prose it travels
      with was not.
    artifacts:
      - path: boty/retailers.py
        issue: "L499-503: the `detail` text is unconditional on `unresolved`"
    missing:
      - "A detail that does not assert non-resolution when `unresolved` is False (e.g. 'the page did not render; nothing established about sku …')"
  - truth: "Criterion 3: Best Buy's control is repaired, measured against a real reading, or replaced"
    status: partial
    reason: >
      Premise false (Collision 10, verified). There was nothing to repair, and the criterion cannot be
      met as written. The transport defect the reads exposed has a partial fix with ZERO live
      confirmation: 0h read ① tested the withdrawn NEXT_REDIRECT fix, and read ② was a capture. The
      daemon has taken no Best Buy reading since the deploy (control row read_at is ~24,000 min old,
      checked=false). DoD item 3's first half ("repair confirmed against a real Best Buy control
      reading") is NOT MET. Its second half (dead-control state reachable in a test) is MET.
    artifacts:
      - path: .planning/ROADMAP.md
        issue: "The closing record still says 'THE FIX IS NOT SHIPPED' and 'NOT ON THE WIRE', with no dated note beside either (both false since 09-10 and 09-11)"
      - path: docs/retailer-evidence.md
        issue: "No entry for the two § 0h reads, and none for the 09-10 fix. L1250 ('clause A now fires on every Best Buy SKU') has no dated note, though it is now narrower"
    missing:
      - "Dated notes beside the ROADMAP closing record and evidence L1250; a § 0h entry in the evidence log (the gated record), not only in QUESTIONS.md and a commit message"
---

# Phase 10: A Control That Cannot Die: Verification Report

**Goal:** A control that stops resolving is reported as a **dead control**, a fact about our configuration, and never as a refusal or a broken detector.
**Verified:** 2026-09-11T13:31:39Z · **Status:** gaps_found · **Re-verification:** No (the phase closed without a verifier; this is the first)

## Headline

The **partition is real and mutation-gated**. The **premise correction is sound and unconditional**. The
**09-10 fix is real and gated in both directions**. But the fix repairs **one of the two measured
false-dead shapes**, and the tree's own evidence log already holds the counterexample. **Criteria 1 and
3 stay MET IN PART. Neither moves up.**

## Observable Truths

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

**Score: 8/11 verified, 3 partial, 0 behavior-unverified.**

## Behavioral Spot-Checks (offline, `_verdict_from_html` direct)

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

## Requirements Coverage

| Req | Status | Evidence |
|---|---|---|
| REQ-24: dead control distinguishable, never a refusal or detector failure | ✓ SATISFIED for true deads | Rows 1, 2, 8. M44 |
| REQ-24: "Best Buy's current dead control is repaired" | ✗ premise false | Row 6. There was nothing to repair |
| DoD 3: repair confirmed on a real reading · dead state reachable in a test | ✗ · ✓ | Gap 3 · rows 1, 8 |

## Anti-Patterns / Record Drift

| Where | Finding | Severity |
|---|---|---|
| `QUESTIONS.md` § 0h | "The false dead is gone": contradicted by evidence L1204 | ⚠ (gap 1) |
| `boty/retailers.py:493-494` | Comment says clause B "needs no gate and is untouched", but L510 gates it too. Also, "a document that never rendered cannot meet `ld.blocks > 0`" is unmeasured, since ld+json can sit in `<head>` | ⚠ prose ≠ code |
| `tests/test_retailers.py:3520` | Docstring "WHY THE FIX WAS TO **WITHDRAW** CLAUSE A", while the code, the commit and the sibling test all say withdrawal was **refused** | ⚠ prose ≠ code |
| ROADMAP closing record | "NOT SHIPPED" / "NOT ON THE WIRE" stale; cited evidence lines off by +421 | ⚠ (gap 3) |
| Debt markers (TBD/FIXME/XXX) in phase-touched files | none | — |

## Not Conflated

Deployed 2026-09-11 07:56:33 (PID 746345). **Best Buy still does not read.** Its control row is the
remembered `in_stock`, `checked=false`, and state.json holds only `availability`/`read_at`. So
**production has made zero observations of the fix.** Honesty about an unreadable retailer ≠ a readable
retailer. **Incidental, out of scope, but live:** since the deploy, every Walmart health warning fails
Telegram delivery (`Unsupported start tag "redacted"`, HTTP 400, retried every ~5 min). The cause is
`notify.py:73`'s `store <redacted>` under HTML parse mode, which is not phase-10 code. As a result a
health warning has not reached the phone since the restart.

## Gaps Summary

One root cause, three faces. The 09-10 fix chose `<body>` presence as the discriminator on **three
captures** and left out a **fourth measurement already in the tree**, which contradicts it. Everything
needed to close gaps 1 and 2 is offline: read 2's shape is fully recorded. Gap 3's record edits are
offline. Its live half (confirming anything on the wire) needs a read that is **not authorised**, and
stays MET IN PART until one is. **No live request, restart, or state write was made by this
verification. Only this file was written.**

_Verifier: Claude (gsd-verifier)_
