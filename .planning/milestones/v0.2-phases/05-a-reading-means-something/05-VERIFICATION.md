---
phase: 05-a-reading-means-something
verified: 2026-08-10T13:05:00Z
status: human_needed
score: 6/6 must-haves verified in the tree
overrides_applied: 0
re_verification: null
human_verification:
  - test: "Set the Walmart store pin, then restart the daemon: put WALMART_STORE_ID=<your store number> in the service EnvironmentFile (mode 600, outside this repo), then `sudo systemctl restart boty.service`. Confirm the new PID differs from 3059142."
    expected: "After one cycle, `served/boty/status.json` watch rows carry `store` and `store_pinned` keys, the two Walmart rows show the pinned number in both, and the Walmart product watch can be alertable on a real reading rather than UNKNOWN."
    why_human: "Requires the real store number, which no agent may obtain or read (QUESTIONS.md § 0e; the pre-redaction capture in commit 95f84a6 was deliberately not read), and requires a privileged service restart. Dan answered the blocking checkpoint `defer` on 2026-08-10 — verbatim 'Defer — no restart' — so this is a chosen outcome, not a phase failure."
  - test: "After the restart above, re-read `served/boty/status.json` and grep the published health prose for the four withdrawn fragments: `probably broken`, `we are asking too often`, `probably fine`, `detector problem`."
    expected: "None of the four appears. Today the deployed file still publishes `control product is not reading IN_STOCK — the detector is probably broken, so real restocks would be missed silently` for `target`."
    why_human: "The tree is gated and green; only a deploy can change what the running daemon publishes. Requires the same privileged restart."
  - test: "After the restart, stop and start the service again a second time and check `pacer-state.json` at the configured `pacer_state_path`."
    expected: "The file exists, carries `retailers` with per-retailer `refusals` plus a `refused_at` stamp and a `warned` list, and a retailer already past the paging cap is not re-paged by the second process."
    why_human: "Criterion 6 is proved by tests and mutations M11–M14 in the tree, but no restart has occurred on the deployed unit. The running process (MainPID 3059142, up since 2026-08-04 17:48:52 CDT) still holds its backoff in memory and `pacer-state.json` is not yet in use anywhere."
deferred:
  - truth: "Live confirmation of criteria 1, 3, 4, 5 and 6 on the deployed daemon"
    addressed_in: "Outstanding deployment, not a later phase"
    evidence: "Dan answered the store-pin checkpoint `defer` on 2026-08-10. Recorded in STATE.md, ROADMAP.md closing table and REQUIREMENTS.md rows 132-134, each live row marked NOT OBTAINED with its date and reason. Routed to human_verification above rather than filtered away."
---

# Phase 5: A Reading Means Something — Verification Report

**Phase Goal:** A Walmart reading is a statement about a known store, and every alert names
only what was measured — or says it does not know.

**Verified:** 2026-08-10
**Status:** human_needed
**Re-verification:** No — initial verification

Everything below was measured by running commands against this working tree. Where a
SUMMARY or the closing record made a claim, the claim was re-derived independently rather
than quoted. Two claims were singled out for adversarial re-proof because they are the
ones most able to flatter the phase — the criteria renumbering, and the absence of a real
store number — and both survived.

## The phase gate

```
$ make verify-offline
=== verify: identity, lint, tests, types, fixtures, controls, mutation ===
identity check: PASS — 179 file(s), no host identity found
All checks passed!
642 passed in 9.66s
Success: no issues found in 18 source files
fixtures: 11 fixture(s) under /home/dan/CodeProjects/pokemongoplusplus/tests/fixtures
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 14 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (641 passed, 1 skipped in 10.13s)
  CAUGHT    M9  boty/retailers.py: 3 test(s) failed — test_an_unpinned_walmart_watch_is_unknown_not_a_verdict, test_the_two_store_guards_say_different_things, test_the_store_guards_return_before_any_stock_verdict_can_form
  CAUGHT    M10 boty/retailers.py: 3 test(s) failed — test_a_page_answering_for_another_store_is_unknown_not_a_verdict, test_a_page_that_names_no_store_reaches_the_same_refusal, test_the_two_store_guards_say_different_things
  CAUGHT    M11 boty/pacing.py: 7 test(s) failed — test_a_refusal_the_backoff_is_handling_is_recorded_not_pushed_across_a_restart, ...
  CAUGHT    M12 boty/pacing.py: 2 test(s) failed — test_state_older_than_the_backoff_cap_is_discarded, test_a_stamp_in_the_future_is_discarded
  CAUGHT    M13 boty/pacing.py: 2 test(s) failed — test_a_refusal_past_the_cap_is_pushed_once_not_once_per_process, test_the_paging_memory_round_trips
  CAUGHT    M14 boty/cli.py: 2 test(s) failed — test_a_refusal_past_the_cap_is_pushed_once_not_once_per_process, test_a_refusal_past_the_cap_is_pushed_once_within_one_process_too
mutation check: 14/14 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
EXIT_CODE=0
```

Exit 0, **642 passed**, **14/14 mutations** — matching the claimed figures exactly. M1–M8
also CAUGHT; the full transcript is in the log. Live retailer reads were deliberately not
re-run: 05-04 already spent that budget once and recorded the result verbatim.

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP success criterion, verbatim) | Status | Evidence |
|---|---|---|---|
| 1 | Every Walmart `Result` records the store it came from, and that store is published in `status.json` | ✓ VERIFIED (tree) | AST audit: **8 of 8** `return Result(...)` in `_verdict_from_html` carry `store=`, plus **2 of 2** refusal arms in `check_html`. `status.py:142-143` publishes `store` and `store_pinned`. Independent red-watch below. |
| 2 | Store pinning is required config with no default; unset means UNKNOWN with a health message saying so | ✓ VERIFIED (tree) | `config/products.yaml:117` and `:150` — `store_id: ${WALMART_STORE_ID}` on both Walmart watches. Grep for any numeric or defaulted `store_id` anywhere in `config/` and `boty/` returned **nothing**. `retailers.py:260` is the first return in the function; `monitor.py:107` is the fourth `assess_health` arm. |
| 3 | A reading from an unpinned or unexpected store is UNKNOWN, never a verdict — **watched going red** | ✓ VERIFIED | `CAUGHT M9` and `CAUGHT M10`, three failing tests each, in this verifier's own run. Both mutations flip only `Availability.UNKNOWN` → `OUT_OF_STOCK`. |
| 4 | No alert text names a cause the code has not established; where the cause is unknown the alert says so | ✓ VERIFIED (tree) | `ast` gate in `tests/test_alert_text.py`, docstrings excluded by node identity. **Independently watched red by this verifier** (below). Positive half: `CAUSE_UNKNOWN` partition asserts exactly the refusal and breakage arms carry it and the no-control and store-gap arms do not. |
| 5 | A refusal the backoff is handling is recorded but not pushed; one that outlasts the cap is pushed once | ✓ VERIFIED (tree) | Four restart tests in `tests/test_cli_watch.py:522-649` plus `test_the_same_scenario_pushes_twice_when_the_state_file_is_deleted` — a real negative control that deletes `pacer-state.json` and asserts the second page returns. `CAUGHT M14` proves the paced-out-cycle half. |
| 6 | The page-once state survives a service restart | ✓ VERIFIED (tree) | `cli.py:378` `warned = pacer.load()`, `cli.py:429` `pacer.save(warned)`; `pacing.py` `load`/`save` round-trip `refusals`, `refused_at` and `warned` through one gitignored `pacer-state.json` (`.gitignore:26`). `due_at` deliberately not persisted. `CAUGHT M11`, `M12`, `M13`. |

**Score: 6/6 truths verified against the tree.** **0/6 confirmed on the deployed daemon** —
see *What is not true on the wire*.

### Independent red-watches (run by this verifier, not quoted from a SUMMARY)

Criterion 3 demands "watched going red" in as many words, and the project's standing rule
is that a test which cannot fail is not evidence. M9–M14 were re-run above. Two further
gates carry no mutation of their own, so this verifier injected the defect itself.

**REQ-15 absence gate — injected `probably broken` into a live `Health.reason` string:**

```
$ python3 -c "...replace('a control reading cannot be shown to come from the store this ',
                         'a control reading is probably broken and cannot be shown ...')"
$ pytest tests/test_alert_text.py -q
E  AssertionError: boty.monitor still carries 1 withdrawn claim(s):
E      'probably broken' in 'a control reading is probably broken and cannot be shown to come
E      from the store this watch is about — store_id is unset in config/products.yaml, ...'
FAILED tests/test_alert_text.py::test_no_withdrawn_claim_survives_in_any_reachable_string[boty.monitor]
1 failed, 8 passed in 0.03s
```

The gate goes red against the **real module**, not merely against the synthetic string in
`test_the_gate_can_go_red`. That distinction mattered: the in-suite red-watch tests the
matcher, this one tests the scan.

**Criterion 1 publication — removed `"store": r.store,` from `status.write`:**

```
$ pytest tests/test_status.py tests/test_dashboard.py -q
FAILED tests/test_status.py::test_publishing_a_duration_does_not_disturb_any_existing_key
FAILED tests/test_status.py::test_both_stores_are_published_because_one_cannot_tell_the_states_apart
FAILED tests/test_status.py::test_a_watch_with_no_store_publishes_null_rather_than_zero
FAILED tests/test_status.py::test_each_store_key_is_published_independently_of_the_other
4 failed, 28 passed in 0.11s
```

### The two claims most able to flatter the phase

**Claim: the ROADMAP renumbering touched no criterion text.** Re-proved here rather than
taken on trust, because this project has twice declined to reword a criterion to make it
meetable and a silent reword would be the exact defect the milestone exists to close.

```
$ git show 1c7cd71:.planning/ROADMAP.md > before.md      # last ROADMAP state before 05-04
$ awk '/^### Phase 5: A Reading/{f=1} f&&/^### Phase 6/{exit} f&&/^  [0-9]+\. /{sub(/^  [0-9]+\. /,""); print}'
before lines: 6  after lines: 6
$ diff crit_before.txt crit_after.txt
(no output)
$ sha256sum crit_before.txt crit_after.txt
e9f136ac0949d7dada837bea0f4f56763a68b59e84970d94fc9718aeaac91bca  crit_before.txt
e9f136ac0949d7dada837bea0f4f56763a68b59e84970d94fc9718aeaac91bca  crit_after.txt
```

Identical hash over the six criterion bodies with the leading numeral stripped, and both
extractions yielded exactly six lines so the diff could not pass over an empty file.
`git diff 3d99d58 HEAD -- .planning/ROADMAP.md` shows the only changed characters on those
lines are the numerals `0→2, 2→3, 3→4, 4→5, 5→6`; criterion 1 is untouched. **Claim holds.**

**Claim: no real store number entered the repo.**

```
$ python3 scripts/identity_check.py --all
identity check: PASS — 179 file(s), no host identity found
IDENTITY_CHECK_EXIT=0
```

**Claim holds.** The guard also ran inside `make verify-offline` over the same 179 files.

### Mutations are anchored on behaviour, not prose

The concern was that M9–M14 might match message text and rot the moment the prose is
edited — which would matter especially in a phase that rewrote the prose. Checked
mechanically by parsing every `Mutation(...)` out of `scripts/mutation_check.py` and
testing each `search` string against every string constant of length > 15 in
`retailers.py`, `monitor.py`, `pacing.py` and `cli.py`:

```
14 mutations defined: ['M1'...'M14']
  M9:  code-anchored  search='        if watch.store_id is None:\n            return Result(\n ...'
  M10: code-anchored  search='        if store != watch.store_id:\n            return Result(\n ...'
  M11: code-anchored  search='                st.refusals = min(refusals, MAX_PERSISTED_REFUSALS)'
  M12: code-anchored  search='                if not 0.0 <= now - float(refused_at) <= STATE_MAX_AGE_SECONDS:'
  M13: code-anchored  search='        return {w for w in warned if isinstance(w, str)}'
  M14: code-anchored  search='    still_unhealthy = {h.retailer for h in pageable} | (warned - checked)'
```

Not one of the six contains a fragment of a message, docstring or comment. M9/M10 flip only
`Availability.UNKNOWN`; M11–M14 anchor on the statement doing the work. The alert rewrite
in the same phase could not have made any of them pass vacuously.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `boty/parse.py::nextdata_store` | Reads the store off the same `__NEXT_DATA__` node as the offer | ✓ VERIFIED | Reads `product.location.storeIds`, accepted only as a one-element list of `str`; empty, multi-entry or non-string all return `None`. No regex over raw HTML — `storeId` appears 15 times in the milk fixture. Called unconditionally, no retailer predicate. |
| `boty/models.py::Result.store` / `Watch.store_id` / `STORE_SCOPED` | Store identity on the shared shape, no default | ✓ VERIFIED | `store_id: str | None = None` (`models.py:181`); `STORE_SCOPED = frozenset({"walmart"})` (`models.py:138`) consumed by both `retailers.py:253` and `monitor.py:105`, so guard and health arm cannot drift. |
| `boty/retailers.py` store guards | UNKNOWN before any verdict can form | ✓ VERIFIED | Both guards sit after `extraction` is settled and **before** `if not offers:`. `store is None` is folded into the mismatch guard by design. `{store!r}` used, so a value with a newline cannot restructure a notification body. |
| `config/products.yaml` | `store_id` on both Walmart watches, no default | ✓ VERIFIED | Lines 117 and 150. Comment block explicitly routes the number to the EnvironmentFile and warns that the identity guard does not scan commented lines. |
| `boty/status.py` | `store` + `store_pinned` published, null-not-zero | ✓ VERIFIED | Lines 142-143, asserted at both ends (`test_status.py`, `test_dashboard.py` with `w.store` / `w.store_pinned` in the required-key list). |
| `boty/monitor.py::CAUSE_UNKNOWN` + fourth health arm | One spelling, correct partition | ✓ VERIFIED | `CAUSE_UNKNOWN = "the cause is not established"` (`monitor.py:53`), single constant, asserted to appear exactly once per reason. Store-gap arm deliberately does **not** carry it — naming a gap we can name is not an unknown cause. |
| `boty/pacing.py` load/save | Backoff + paging memory on disk, age-bounded, clamped | ✓ VERIFIED | `STATE_MAX_AGE_SECONDS = MAX_BACKOFF_SECONDS`, `MAX_PERSISTED_REFUSALS = 64`, hostile-file and future-stamp tests present. |
| `tests/test_alert_text.py` | `ast` gate, not grep | ✓ VERIFIED | Docstrings excluded by `id()` identity, not by value; f-string `JoinedStr` children covered and asserted directly. Independently watched red above. |
| `scripts/mutation_check.py` M9–M14 | Six new behavioural mutations | ✓ VERIFIED | All six CAUGHT in this verifier's run. |
| `.planning/ROADMAP.md` closing table | Six verdicts, live rows honest | ✓ VERIFIED | Every non-obtained live row carries its date and reason; no criterion reworded (proved above). |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `_verdict_from_html` | `parse.nextdata_store` | unconditional call, `store=` on every return | ✓ WIRED | 8/8 returns; `check_html` refusal arms 2/2. |
| `Watch.store_id` | `config/products.yaml` | `_store_id()` + `${VAR}` substitution | ✓ WIRED | `config.py:230`; absent pin loads as data (`None`), a bool `store_id: true` raises — the typo case is refused, the absence case degrades. |
| `Result.store` | `status.json` | `status.write` | ✓ WIRED | `store` and `store_pinned` both published; red-watched above. |
| `status.json` | dashboard | `w.store`, `w.store_pinned` | ✓ WIRED | `test_dashboard.py` pins both keys with a regex that will not match `w.store` inside `w.store_pinned`. |
| store guard | `assess_health` | shared `STORE_SCOPED` | ✓ WIRED | `monitor.py:105-107`; refusal short-circuits first, so a refusal is never misreported as a store gap. |
| `assess_health` | `notify.send_health_warning` | `Health.reason` verbatim | ✓ WIRED | `test_the_body_is_exactly_the_reason_and_the_failing_controls` pins the exact body; `notify.py` composes no diagnosis of its own, which is what keeps REQ-15 checkable in one place. |
| `Pacer.load/save` | `watch_loop` | `cfg.pacer_state_path` | ✓ WIRED | `cli.py:372, 378, 429`; committed once per cycle. |
| `watch_cycle` | paging memory | `{h.retailer for h in pageable} | (warned - checked)` | ✓ WIRED | The union is the fix for the measured defect; `CAUGHT M14`. |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| `status.json` `store` | `r.store` | `parse.nextdata_store` off live HTML | Yes — read from `storeIds[0]`, `None` when the page is silent | ✓ FLOWING (tree) |
| `status.json` `store_pinned` | `r.watch.store_id` | `config/products.yaml` → `${WALMART_STORE_ID}` | Yes when the env var is set; `None` when unset, which is the required behaviour | ⚠️ **Env var unset on this host** — flows as `None`, which is criterion 2 working, but means Walmart cannot produce a verdict until pinned |
| dashboard row | `w.store` / `w.store_pinned` | `status.json` | Yes | ✓ FLOWING (tree) |
| `pacer-state.json` | `refusals`, `refused_at`, `warned` | `Pacer.save` per cycle | Yes in tests | ⚠️ **File does not exist on this host** — no restart happened, so the deployed loop has never written one |

### Behavioural Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full offline gate | `make verify-offline` | exit 0, 642 passed, 14/14 caught | ✓ PASS |
| No host identity in repo | `python3 scripts/identity_check.py --all` | `PASS — 179 file(s)` exit 0 | ✓ PASS |
| Criteria text unchanged | `diff` + `sha256sum` over extracted criterion bodies | identical hash, 6 lines each | ✓ PASS |
| REQ-15 gate can fail on the real module | inject `probably broken`, `pytest tests/test_alert_text.py` | 1 failed | ✓ PASS (red-watch) |
| Criterion 1 gate can fail | remove `"store": r.store`, `pytest tests/test_status.py tests/test_dashboard.py` | 4 failed | ✓ PASS (red-watch) |
| Mutations are prose-free | AST cross-check of `search` strings vs module string constants | 0 prose hits across M9–M14 | ✓ PASS |
| Deployed daemon vintage | `systemctl show boty.service -p MainPID -p ActiveEnterTimestamp` | `MainPID=3059142`, `Tue 2026-08-04 17:48:52 CDT` | ✓ PASS (confirms *not deployed*) |
| Deployed `status.json` carries `store` | `python3 -c "json.load(open('served/boty/status.json'))"` | keys: `alertable, availability, control, degraded, detail, extraction, name, price, retailer, rung, url` — **no `store`** | ✗ FAIL on the wire, as recorded |
| Deployed prose free of withdrawn claims | grep the published JSON for four fragments | `'probably broken': PRESENT`; other three absent | ✗ FAIL on the wire, as recorded |
| Live retailer reads | `make verify` (full) | **NOT RUN** — deliberately | ? SKIP (budget capped; 05-04 ran it once and recorded it verbatim) |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist in this repository; this project's executable gate is
`make verify` / `make verify-offline`, which was run above.

| Probe | Command | Result | Status |
|---|---|---|---|
| (none declared) | — | — | N/A |

### Requirements Coverage

| Requirement | Source | Description | Status | Evidence |
|---|---|---|---|---|
| REQ-14 | 05-01, 05-02 | Walmart reading states its store; unpinned or unexpected is UNKNOWN | ✓ SATISFIED (tree) / deployment outstanding | 8/8 return paths carry `store`; guards return UNKNOWN first; M9, M10 CAUGHT; identity guard PASS. Not on the daemon. |
| REQ-15 | 05-02 | No alert names an unmeasured cause; unknown cause says so | ✓ SATISFIED (tree) / deployment outstanding | `ast` gate independently watched red; `CAUSE_UNKNOWN` partition across all four arms. Deployed daemon still publishes `probably broken`. |
| REQ-16 | 05-03 | Recorded-not-pushed; pushed once past the cap; wrong verdict pages immediately | ✓ SATISFIED (tree) / deployment outstanding | Four restart tests + permanent negative control; M11–M14 CAUGHT. `pacer-state.json` not yet in use on the host. |

No orphaned requirements: REQUIREMENTS.md maps exactly REQ-14, REQ-15 and REQ-16 to Phase 5,
and all three are claimed by plans in this phase.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `scripts/mutation_check.py` | 7, 10 | Module docstring still says the harness "corrupts three specific things" and "The three mutations are not arbitrary" — there are now **14** | ℹ️ Info | Stale prose in the gate's own docstring. Recorded in this phase's `deferred-items.md` item 3 as pre-existing (stale since M4) and left rather than folded into a store-guard commit. Affects no behaviour and no mutation `search` string. |
| `boty/cli.py` | 306-307 | Comment asserts "nothing is broken and the monitor is already fixing it by asking less often" — the same unmeasured-cause class REQ-15 withdrew | ℹ️ Info | A **comment**, so outside REQ-15's subject (strings that reach a person) and outside the `ast` gate by design. `deferred-items.md` item 2 suggested 05-03 as owner; 05-03 did not take it. Not a criterion failure. |
| `README.md` | 327 | Quotes the withdrawn `the detector is probably broken` sentence | ℹ️ Info | `deferred-items.md` item 1. True as history but reads as live output; a reader who greps for it will not find it in the code. Suggested owner was 05-04 or a Phase 6 docs plan; still open. |
| ROADMAP closing table row 1, REQUIREMENTS.md row 132 | — | States `Result.store` is carried on "**6 of 6**" return paths in `_verdict_from_html`; the tree has **8**, all carrying `store` | ℹ️ Info | Count is stale (6 was true after 05-01; 05-02 added two guard returns, both carrying `store`). The *coverage* claim is intact and understated rather than overstated — verified 8/8 by AST. |

No `TBD`, `FIXME` or `XXX` markers were found in the files this phase modified. No stub
returns, no empty handlers, no hardcoded-empty props.

## What is not true on the wire

This section exists because the phase's own record insists on it and the record is correct.

```
$ systemctl show boty.service -p MainPID -p ActiveEnterTimestamp -p ActiveState
MainPID=3059142
ActiveEnterTimestamp=Tue 2026-08-04 17:48:52 CDT
ActiveState=active

$ python3 -c "print(sorted(json.load(open('served/boty/status.json'))['watches'][0].keys()))"
['alertable', 'availability', 'control', 'degraded', 'detail',
 'extraction', 'name', 'price', 'retailer', 'rung', 'url']       # no 'store'

$ grep -o 'probably broken' <published status.json>
probably broken                                                   # still being published
```

Re-measured by this verifier, unchanged from what 05-04 recorded: the daemon runs
**2026-08-04 code**, its published rows carry **no `store` key**, and it is **still
publishing the exact sentence REQ-15 withdrew**. One further observation worth naming: the
deployed file shows a `walmart` row reading `in_stock` with `alertable=True` — an unpinned
Walmart reading that can still fire an alert. That is precisely the 2026-08-09 defect,
still live, and it stays live until the pin and the restart.

**This is a deliberate, user-chosen outcome and not a gap this phase failed to close.** Dan
was presented the blocking checkpoint and answered `defer` — verbatim "Defer — no restart".
The alternative would have been for the phase to quietly reword a criterion to absorb the
gap, which is the one thing this project has twice refused to do. Every live row in the
closing table reads NOT OBTAINED with its date and its reason.

The consequence is stated plainly rather than implied away: **the phase is complete in the
tree and outstanding on the wire.** Status is `human_needed`, not `gaps_found`.

## Gaps Summary

No gaps. Six of six criteria are met in the working tree, each verified by running
something rather than by reading a SUMMARY: the offline gate at exit 0 with 642 tests and
14/14 mutations caught, two additional red-watches injected by this verifier against gates
that carry no mutation of their own, an AST audit proving all eight verdict return paths
carry the store, a hash-equality proof that no criterion was reworded, and a clean identity
check over 179 files.

Three documentation items remain open, all of them recorded in this phase's own
`deferred-items.md` before this verification ran, none of them touching a criterion: a
stale count in the mutation harness docstring, an unmeasured-cause claim surviving in a
`cli.py` comment, and a README passage quoting withdrawn text as though it were live
output. Item 2 was assigned to 05-03 and 05-03 did not take it — worth carrying into
Phase 6's docs work rather than losing.

What a human must do to close the phase on the wire: set `WALMART_STORE_ID` in the
service's EnvironmentFile, then `sudo systemctl restart boty.service`, then confirm the
three checks in the `human_verification` block above. Until the pin is set, restarting
alone will make Walmart read UNKNOWN rather than alertable — which is criterion 2 working
as designed, but is not the same as a working Walmart watch.

---

_Verified: 2026-08-10_
_Verifier: Claude (gsd-verifier)_
