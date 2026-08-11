---
gsd_state_version: 1.0
# `milestone:` is MACHINE-READ by tests/test_packaging_metadata.py against pyproject.toml's
# version (0.2.0), component-wise. It STAYS at v0.2 through this archival: v0.2 is the version
# in the tree, nothing was tagged or published, and no next milestone has been scoped. Change
# it only together with pyproject.toml, and re-run that test file.
milestone: v0.2
milestone_name: — Say Only What You Measured
status: Milestone v0.2 ARCHIVED 2026-08-11 — 2 of 2 phases, 11 of 11 plans, complete IN THE TREE; not deployed, not tagged, not published
stopped_at: Archived milestone v0.2 — ROADMAP and REQUIREMENTS extracted to .planning/milestones/, REQUIREMENTS.md removed for the next milestone, no git tag created
last_updated: "2026-08-11T16:00:00.000Z"
last_activity: 2026-08-11
progress:
  total_phases: 2
  completed_phases: 2
  total_plans: 11
  completed_plans: 11
  # percent is PHASE-based, not plan-based: 2 of 2 phases in v0.2 are complete.
  # (Phase 5 = 4 plans, Phase 6 = 7 plans, so 11 of 11 plans agree with it here.)
  percent: 100
---

# State: bot-y

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-08-11, with a `## Current State` section)

**Core value:** A stock reading you can trust — never "out of stock" when the truth is "I couldn't tell", never "in stock" when the truth is "a reseller has one at 4x MSRP."
**Current focus:** Nothing in flight. v0.2 is archived; the next milestone is unscoped. The one
outstanding action from v0.2 is not planning work — it is `sudo systemctl restart boty`.

## Status

**Milestone v0.2 — ARCHIVED 2026-08-11.** 2 of 2 phases, 11 of 11 plans, 84 commits from the
scoping commit `79e0c84`, 75 files changed, +30,483 / −568. Audit status `passed` (it opened
`gaps_found` on one item — `CHANGELOG.md` still asserting the rule Dan reversed — closed at
`0d6d1b8`). Archive:

- `.planning/milestones/v0.2-ROADMAP.md` — both phases, both closing outcome tables, intact
- `.planning/milestones/v0.2-REQUIREMENTS.md` — REQ-14…REQ-20 with outcomes, and REQ-17's
  revision recorded beside its unedited original
- `.planning/milestones/v0.2-MILESTONE-AUDIT.md` — moved here from `.planning/`

`.planning/REQUIREMENTS.md` was **removed** at close; a fresh one comes with the next
milestone. `.planning/ROADMAP.md` now carries v0.2 as one line with a link, and **v1.0.0's
material is untouched** — it is open, untagged and not archived.

**NO GIT TAG WAS CREATED, and none exists.** `git tag -l` → 0; `git ls-remote --tags origin`
→ 0 refs. That decision is being handled separately and this archival did not touch it.

**"Archived" is not "shipped", and the distinction is the whole milestone.** None of the
eleven criteria this milestone met is in effect on the deployed daemon. `boty.service` still
runs 2026-08-04 code (`MainPID=3059142`) because Dan answered `defer` on 2026-08-10 — so the
process actually watching for restocks still says *"the detector is probably broken"*, still
holds Amazon's backoff in memory, and still publishes a Walmart GO Plus + verdict about a
store nobody chose. **The audit's one new fact reframes the price of fixing that:** `boty` is
an **editable install** (`.pth` → this working tree; the unit runs that tree's venv from that
tree's directory), so **`sudo systemctl restart boty` deploys REQ-15, REQ-16 and REQ-17 today
with no store pin needed**. Only REQ-14 additionally needs `WALMART_STORE_ID` (still unset —
measured as a count, `0`, never a value). The deferral was priced as one decision; it is two,
and three of four requirements sit on the cheap side.

**Next command:** `/gsd-new-milestone` when there is a next milestone to scope.
`QUESTIONS.md` § 0e and § 0f are both still open and untouched.

## Deferred Items

Acknowledged and deferred at milestone close on 2026-08-11:

| Category | Item | Status |
|---|---|---|
| deploy | Restart `boty.service` onto this tree (REQ-15/16/17) | Open — one command, no prerequisite |
| deploy | `WALMART_STORE_ID` in the EnvironmentFile (REQ-14) | Open — Dan's to give or not (`QUESTIONS.md` § 0f) |
| verification | Phase 05 — `05-VERIFICATION.md` | `human_needed` — all three items are the deferred deploy above |
| verification | Phase 02 — `02-VERIFICATION.md` | `human_needed` — **v1.0.0**, not this milestone |
| verification | Phase 03 — `03-VERIFICATION.md` | `human_needed` — **v1.0.0**, not this milestone |
| verification | Phase 03.1 — `03.1-VERIFICATION.md` | `gaps_found` — **v1.0.0**, not this milestone |
| verification | Phase 04 — `04-VERIFICATION.md` | `human_needed` — **v1.0.0**, not this milestone |
| security | `QUESTIONS.md` § 0e — pushed public history carries host geolocation and this host's public IP | Open, untouched by v0.2. The working tree is clean; the history is not |
| tech-debt | Seven items carried in the audit's `tech_debt` block — no `.planning/` contents gate, `identity_check` has no `store '<n>'` prose rule, `mutation_check.py`'s "three mutations" docstring, `README.md:327`, `boty/cli.py`'s comment, `M21`–`M24` (by design, not debt), the unowned live-`make verify` classes | Open — see `.planning/milestones/v0.2-MILESTONE-AUDIT.md` |

Four of the five open verifications belong to **v1.0.0**, which is not being archived; they
are listed so the count is not read as v0.2's.

**Phase 6 closed on four of five criteria MET AS WRITTEN, and criterion 1 MET IN PART.** Its
second half — *"an unresolvable shipping cost is UNKNOWN, not a pass"* — is met only against a
**revision Dan made on 2026-08-11**, and the closing record says so rather than rounding it up.
Nothing anywhere was reworded to pass, and that is asserted by command rather than by eye: every
criterion body in `ROADMAP.md` was extracted from `HEAD` and from the working tree with the
leading numeral stripped (**40 lines at baseline, 40 now, zero removed**), and Phase 5's eight-line
closing table came out **byte-identical**. `make verify-offline` exits **0** at **768 passed** and
**24/24**, up from **667 / 16/16** at Phase 5's close and **531 / 8/8** pre-milestone. Full working
in `docs/retailer-evidence.md` § *Phase 6 closing record*.

**THE ONE FINDING THIS PHASE'S OWN CLOSE PRODUCED, because no later plan would have caught it.**
06-06's plan states that a third *committed* instance of the REQ-19 leaked-markup class "is not
established by the tree". Measured at close, **it is**: `06-07-SUMMARY.md` was committed at
`a71e79b` ending in two whole-line agent tool-call tags after its closing metadata line — not in a
fence, introduced by no prose — which is byte-shape for byte-shape the `CHANGELOG.md` incident
06-04 built its gate for, **in the plan that reversed REQ-17, one day after that gate landed**.
Removed at `7355034` and recorded rather than quietly fixed, on 06-04's and 06-05's precedent; the
evidence is permanent at `a71e79b`. **Nothing in this repository's gates would have caught it** —
`leaked_markup` is deliberately scoped to `CHANGELOG.md`, `.planning/` is covered by no contents
rule at all, and `identity_check.py` scans for host identity. There are now **three** candidates of
this shape logged and unbuilt: invisible characters (06-04), leaked markup outside `CHANGELOG.md`
(06-05), and this instance, which is the one that turns the class from a near-miss into a hit.

**THIS FILE IS NOW MACHINE-READ, and editing it is a gate-visible act.** As of `30cb977`,
`tests/test_packaging_metadata.py` reads the `milestone:` key in the frontmatter above; changing it
without changing `pyproject.toml`'s version turns `make verify-offline` red naming both files. The
comparison is lenient in exactly one way — a milestone names a *minor line*, so `v0.2` agrees with
`0.2.0` and would agree with a future `0.2.7`, but **not** with `0.21.0`, because the rule compares
component lists rather than string prefixes. 06-06 edited this file and re-ran
`tests/test_packaging_metadata.py` immediately afterwards; it was green.

**06-07 REVERSED 06-01, BECAUSE DAN DID, AND THE HOLE REQ-17 NAMES IS DELIBERATELY REOPENED.**
His words, verbatim, 2026-08-11: *"I think where we don't know just send it. If the user gets
there and it's 50 dollar shipping that's disappointing but it's worse to feel like you 'missed
out'."* So where a shipping cost cannot be established the ceiling now measures the **item price**
and the alert goes out; where it CAN be established the ceiling still measures the delivered total
and a resolvable total above it is still suppressed — 06-01's main win is intact. **A $54.99
listing with $45 of unread shipping now pages him, and he will not be told the $45.** The whole
mitigation is a field: the push reads `price: $54.99   shipping: unknown`, two labelled fields in
the same shape either way, and **no delivered total is stated in any body** — you cannot add a
number to `unknown`. `REQUIREMENTS.md` was **not edited**; REQ-17's text stands and the revision is
recorded beside it in `06-07-SUMMARY.md` in Phase 3.1's format, for 06-06 to apply.

**Re-measured against the built tree, and all four product watches move.** GameStop **YES**
(unchanged, on the delivered total); **Nintendo YES** and **Amazon YES** — the two 06-01 silenced,
back on the item price; and **Walmart moves off "not demonstrated" to YES**, on the same unchanged
measurement (its only first-party capture resolves no shipping, which is no longer a reason it
cannot alert). **06-01's measurements were all right; only the conclusion drawn from them changed.**
`make verify-offline` exits 0 at **768 passed** and **24/24**, with **M4 and M17 re-pointed, M18
re-anchored, and M27/M28 added**. M17's re-point is the one to read: it pinned the item-price
fallback as *REJECTED*, Dan chose a version of it, and it was **re-pointed rather than deleted** —
onto `established_shipping` collapsing an unread cost into `$0.00`, the one reading of his decision
he did not choose. It now guards the CLAIM where it used to guard the VERDICT. **M21–M24 are still
unallocated.**

**And the first assertions ever made about `send_restock`'s body landed with it.** Every reference
to it under `tests/` was a monkeypatch until 2026-08-11, so the one push a person receives when
this project SUCCEEDS was the only unguarded surface in the alerting path.

**06-05 landed criterion 5, and this project's version is no longer a claim only one file makes.**
`pyproject.toml` reads **`0.2.0`**, and the roll is recorded in the file as **the correction, not a
bump** — the v1.0 numbering was itself the overclaim this milestone corrects everywhere else.
Rolling *down* is safe only because nothing was ever tagged or uploaded, and all four facts were
**re-measured at execution** rather than inherited: `git tag -l` 0 tags, `git ls-remote --tags
origin` 0 refs against a remote that answered, and HTTP 404 for both `bot-y` and `bot-y/1.0.0` on
PyPI. No tag was created and nothing was published. The gate was written **first**, against a tree
that disagreed with itself: `pytest tests/` at **exit 1, 2 failed, 757 passed** with nothing rolled
— `pyproject.toml` saying `1.0.0` while this file said `milestone: v0.2`, a disagreement that had
been sitting here since the milestone was scoped with nothing offline reading either one — then
**exit 0, 759 passed** after the roll, same command. `make verify-offline` exits 0 at **759 passed**
and **22/22**, the ratio risen by exactly 2 with **M25 and M26** — this repository's first mutations
outside `boty/` — both observed CAUGHT by the always-on `pyproject` <-> `README` binding.

**Two things from 06-05 that bind future edits to THIS file.** (1) The `milestone:` key in the
frontmatter above is **machine-read** as of `30cb977`; changing it without changing
`pyproject.toml`'s version turns `make verify-offline` red naming both files. (2) The
`Development Status` classifier is now **`4 - Beta`**, argued in place with Phase 4's rejection of
Beta kept verbatim, and bound to the version in both directions — so it cannot go stale at the next
change. What would move it back to `5` is written into `pyproject.toml`: a published release
somebody other than the maintainer has installed, and a live `make verify` that passes.

**06-04 landed criterion 4, and the defect was executed on disk before the gate existed.**
`CHANGELOG.md` shipped with two literal lines of leaked agent tool-call markup for the whole of
Phase 4 — `MANIFEST.in` puts the file in the sdist and `[project.urls] Changelog` points every
installer at it — because nothing read the body: `scripts/release_check.py` asserts the file
*exists*, reads one heading, and needs the network, so it sits outside `make verify` by design.
Measured on this tree, not inferred: `git show 2ac965f^:CHANGELOG.md` restored to disk with no
contents rule anywhere left `pytest tests/` at **exit 0, 711 passed**. `tests/test_changelog.py`
now carries **eight rules as pure functions of text** (two borrowed from
`tests/test_contributor_docs.py` rather than re-implemented), and the identical bytes and command
afterwards give **exit 1, 2 failed, 735 passed**, naming both offending lines and both shapes that
caught them. The file was restored with `git checkout --` in a `finally` after every run and
`git status --porcelain` was clean each time. `make verify-offline` exits 0 at **737 passed** and
**20/20**.

**Three things about that gate worth carrying rather than rediscovering.** (1) **The green side is
an assertion, not a formality:** `CHANGELOG.md` line 138 carries a backticked `<script>` token —
measured as the *only* angle-bracket token in the file — so a markup rule written over angle
brackets is red on the shipped tree on arrival. The rule is three shapes around the *defect*
instead. **Never fix a red green-side by editing `CHANGELOG.md`.** (2) **Every prohibition is
paired with a presence rule in the same commit**, because no markup, no placeholders and a single
trailing newline are all satisfied by an *empty* file — the rule set is watched biting on the empty
and preamble-only documents. (3) **The criterion is not met by a skip line.** `CHANGELOG.md` is
absent from `SANDBOX_CONTENTS` and was **not** added to it; the file-reading half skips there and
an unconditional half runs, **observed** inside a real `build_sandbox()` at **7 passed, 19
skipped**. That run was not a formality either — it caught a defect no in-tree run could have
shown, recorded as deviation 1 in `06-04-SUMMARY.md`.

**06-04 registers NO mutation, and M23-M24 are deliberately UNALLOCATED — joining 06-03's
M21-M22, so the sequence now carries a gap at M21-M24.** The harness mutates `boty/` and this plan
writes no production code; `apply_mutation` cannot reach a file the sandbox does not copy; and
adding `CHANGELOG.md` to `SANDBOX_CONTENTS` so a mutation could exist would create an entry
provable load-bearing only by the mutation that motivated it, failing Phase 4's own rule for that
constant. **06-05 should keep M25-M26 rather than renumbering into the gap, and 06-06 must not read
four lost mutations.** The full four-reason argument is in `06-04-SUMMARY.md`.

**Two forward bindings 06-05 is on the hook for.** The `## [0.2.0]` heading it writes must carry a
real ISO date (validity, not just `\d{4}-\d{2}-\d{2}` — `2026-13-45` is checked) and a non-empty
body, or the new gate bites. **No ordering rule exists**, deliberately, so `## [0.2.0]` above
`## [1.0.0]` is accepted — the roll is the correction, not a bump. And `CHANGELOG.md`'s preamble
still says `scripts/release_check.py` is what binds its top heading to `pyproject.toml`; that
sentence becomes incomplete the moment 06-05 adds an offline binding. **It was deliberately not
edited by 06-04** — `CHANGELOG.md` is 06-05's file, and editing prose about a mechanism before that
mechanism exists is the overclaim this milestone corrects.

**06-03 landed criterion 3, and the gap was executed before the gate was written.** Every rule in
`tests/test_ci_workflow.py` but `_pr_triggered_privilege` was keyed to a filename —
`CI = WORKFLOWS / "ci.yml"`, then the same four families written out again for `RELEASE` — so a
**third** workflow file was guarded by nothing. Measured on this tree, not inferred: a workflow
carrying a floating action tag, a swallowed exit code, no `timeout-minutes` and
`runs-on: ubuntu-latest`, written into the real `.github/workflows/`, left `pytest tests/` at
**exit 0, 701 passed**. The four families are now `DIRECTORY_RULES` over `_all_workflow_texts()`,
findings prefixed with the filename, and the identical file and command afterwards give **exit 1,
2 failed, 709 passed**, naming all four families and the file. The probe was removed in a `finally`,
`git status --porcelain` is clean, and its absence is now a permanent test rather than a habit.
`make verify-offline` exits 0 at **711 passed** and **20/20**.

**06-03 registers NO mutation, and M21-M22 are deliberately UNALLOCATED.** `apply_mutation`
string-replaces inside an existing file and **cannot add one**, so a criterion about a workflow file
*that does not exist yet* is outside the harness by construction. 06-04 and 06-05 should keep their
own reservations rather than renumbering into the gap, and **06-06 must not read it as a lost
mutation.** The full three-reason argument is in `06-03-SUMMARY.md`.

**A correction 06-06 must carry, and neither document was edited to make it go away.**
`06-PATTERNS.md` and `06-PLAN-OUTLINE.md` both name the exit-code rule `_flattened_exit_codes`.
**No such function exists** — it is `_flattening`. Confirmed against the tree before and after this
plan. Same handling as 06-02's `06-CONTEXT.md` correction: a measurement note, never an edit to a
planning document or a requirement.

**06-02 landed criterion 2 — the one that was literally a report that an existing gate could
not go red.** The README support matrix's Rung cell is now bound to the code across **both**
joins: retailer→adapter out of `cli._make_checker`'s if-chain and adapter→rung out of
`boty/retailers.py`, statically by AST, two-directionally, with nine red-watches and two new
mutations. **M19 and M20 are both observed CAUGHT by ident** — M19 by nine tests, every one of
them the new gate. `make verify-offline` exits 0 at **701 passed** and **20/20**.

**REQ-18's `131` was RE-MEASURED before the gate was written and NOT edited.** The criterion's
own mutation, applied inside the harness's own sandbox to a tree with no Rung binding in it,
left pytest at **exit 0, `687 passed, 1 skipped`**. The 131 is a pre-Phase-5 figure; the newer
number is recorded beside it as a measurement note, never as an amendment. **REQ-18 stays
Pending** for 06-06.

**A correction 06-06 must carry, and `REQUIREMENTS.md` was deliberately not edited to make it
go away.** `06-CONTEXT.md` says `tests/test_support_matrix.py` "already binds the README's
Routing and Extraction cells to the code in both directions", and REQ-18's own parenthetical
says "Routing and Extraction are already pinned; Rung is the gap." **Both are measured false.**
`_extraction_mismatch` binds one README cell to another README cell — both of its directions
are inside the table — and before 06-02 nothing in `tests/` imported `boty.models` or bound a
README cell to `boty/` at all. So both joins were new construction, not a column copy, and a
rung-only gate would have stayed green the day `_make_checker` stopped routing amazon to
`check_amazon`. A criterion is never amended to make it meetable, and by the same rule it is
not amended to make it *accurate* either.

**One measured contradiction of 06-02's own plan, recorded rather than hidden.** Its F6 claimed
no existing test routes a target watch through `_make_checker`, so M20 would be killed by the
new gate and nothing else. Measured:
`tests/test_retailers.py::test_a_target_watch_is_dispatched_to_the_browser_and_dom_path` does
exactly that and is in M20's kill list. F6's grep was for `check_target_browser`, which that
test never names. M20 is still not redundant — it pins the README row, and the pre-existing
test pins the dispatch — but the record says which gates killed it.

**06-01 landed criterion 1, and it landed a bill with it.** The `max_price` ceiling now measures
the delivered total — item price plus shipping — and refuses to authorise an alert where that
total cannot be established. Measured against the built tree: **Nintendo and Amazon stop being
able to page**, because one publishes its shipping cost as an English sentence and the other's
reader is a button. **Walmart is "not demonstrated"** — the plan predicted it keeps its
alertability, and the measurement corrected that: the only first-party Walmart capture in this
repo resolves no shipping at all. GameStop is unaffected ($54.99 + $6.99 = $61.98, under 80).
No ceiling was raised and no watch edited to hide any of it; the four-watch table in
`06-01-SUMMARY.md` is **06-06's blocking-checkpoint material**, and REQ-17 is deliberately left
Pending for 06-06 to close by measuring what landed.

**The most useful thing anyone can do to this project right now is restart `boty.service`.**
Everything Phase 5 built is in the tree, gated and green offline; **none of it is running.**
Dan was asked for his Walmart store number at 05-04's closing checkpoint and answered
`defer` — verbatim, *"Defer — no restart"* — which was one of the three offered answers and is
recorded rather than worked around. So: no pin was set (`grep -c '^WALMART_STORE_ID=' env` → `0`,
a count and never a value), and no restart was made. Until one is, Walmart readings are still
statements about an arbitrary store, the withdrawn *"the detector is probably broken"* sentence
still reaches a person, and the backoff is still in-memory with the once-per-process paging
defect. The work needed is `systemctl restart boty.service` — plus the pin first, if Walmart is
to be alertable at all.

**`gsd-tools state advance-plan` misfired a FOURTH time, and this run captured the mechanism in
the tool's own words.** It returned `{"advanced": false, "reason": "last_plan", "current_plan": 6,
"total_plans": 6, "status": "ready_for_verification"}` — Phase 5 has **four** plans, not six, so
the 6-of-6 it read is the `Plan: 6 of 6 complete` line in the archived v1.0.0 block at the bottom
of this file, which is kept verbatim and therefore cannot be edited to fix the tool. It again
wrote `status: Phase complete — ready for verification` and again overwrote `stopped_at` with
Phase 4's stale value; both corrected by hand, as after 05-01, 05-02 and 05-03. Two smaller
misfires observed the same run and worth recording with it: `state update-progress` returned
`{"updated": true, "percent": 75}` while leaving frontmatter `percent` at `0`, and
`state record-metric` rejected the documented positional form with `phase, plan, and duration
required`, so the Phase 05 P04 row below was written by hand. Recorded because a milestone about
not overclaiming should not have its own state file claiming a phase closed at the halfway mark.

**A FIFTH misfire, at 06-01, identical in all three parts.** `advance-plan` returned the same
`{"reason": "last_plan", "current_plan": 6, "total_plans": 6, "status":
"ready_for_verification"}` — after the FIRST plan of a six-plan phase — and again wrote
`status: Phase complete — ready for verification` and again overwrote `stopped_at` with Phase
4's stale value. `record-metric` again rejected the documented positional form. `update-progress`
did write frontmatter this time (`percent: 50`) but on a plan basis, silently replacing the
comment recording that this figure is phase-based; the comment is restored above. All corrected
by hand, for the fifth time. The pattern is now stable enough to state plainly: **`gsd-tools`
reads `Plan: 6 of 6 complete` out of the archived v1.0.0 block at the bottom of this file**, that
block is kept verbatim and cannot be edited to fix the tool, so every plan in this phase should
expect to correct these three fields by hand and should not trust the tool's own summary line.

**A SIXTH misfire, at 06-02, identical in all three parts.** `advance-plan` returned the same
`{"reason": "last_plan", "current_plan": 6, "total_plans": 6, "status":
"ready_for_verification"}` after the SECOND plan of a six-plan phase, and again wrote `status:
Phase complete — ready for verification` and again overwrote `stopped_at` with Phase 4's stale
value. `record-metric` again rejected the documented positional form. `update-progress` again
stripped the comment recording that `percent` is phase-based, this time reporting `60%` on a
plan basis while leaving the frontmatter field at `50`. All corrected by hand, for the sixth
time. **One new, environmental note worth carrying:** `gsd-tools` is not reachable from a
non-login shell on this host — every call returns `/usr/bin/env: 'node': No such file or
directory` until `export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh` is sourced first. A run that
forgets that gets three silent no-ops instead of three misfires, which is the worse failure of
the two because nothing looks wrong.

**A SEVENTH misfire, at 06-03 — and this run found the invocation that WORKS.** `advance-plan`
returned the same `{"reason": "last_plan", "current_plan": 6, "total_plans": 6, "status":
"ready_for_verification"}` after the THIRD plan of a six-plan phase, again wrote `status: Phase
complete — ready for verification`, and again overwrote `stopped_at` with Phase 4's stale value.
`update-progress` again stripped the comment recording that `percent` is phase-based, reporting
`70%` on a plan basis while leaving the frontmatter field at `50`. All corrected by hand, for the
seventh time. **The new and useful part:** the documented POSITIONAL form fails
(`state.record-metric "Phase 06" "P03" "38min" ...` → `phase, plan, and duration required`;
`state.add-decision "<text>"` → `summary required`) but the **flag form is accepted** —
`state.record-metric --phase "Phase 06" --plan "P03" --duration "38min" --tasks "3 tasks" --files
"1 file"` returns a populated object, and `state.add-decision --summary "<text>"` returns
`{"added": true}`. Two caveats measured with it: `record-metric` echoed the values but **wrote no
row** to the Performance Metrics table, and `add-decision` prefixes every entry `[Phase ?]`
regardless of input, which is why this file's decisions are still written by hand. Six prior plans
wrote these fields by hand assuming the verbs were simply broken; they are broken in a narrower way
than that, and the next plan should not waste the same twenty minutes rediscovering it.

**An EIGHTH misfire, at 06-04, identical in all three parts, and this run adds one more data
point.** `advance-plan` returned the same `{"reason": "last_plan", "current_plan": 6,
"total_plans": 6, "status": "ready_for_verification"}` after the FOURTH plan of a six-plan phase,
again wrote `status: Phase complete — ready for verification`, and again overwrote `stopped_at`
with Phase 4's stale value. `update-progress` again stripped the comment recording that `percent`
is phase-based, reporting `80%` on a plan basis while leaving the frontmatter field at `50`. **The
flag form 06-03 discovered does get accepted and still does not write:**
`state.record-metric --phase "Phase 06" --plan "P04" --duration "47min" --tasks "3 tasks" --files
"1 file"` returned a populated object echoing every value and wrote **no row** to the Performance
Metrics table — the row below was written by hand, as after 06-03. **New this run:**
`roadmap.update-plan-progress 6` returned `{"status": "In Progress", "complete": false}` and left
the ROADMAP's *"Progress: 3 of 6 plans complete"* line untouched; that was corrected by hand too.
All fields corrected by hand, for the eighth time. Nothing about this pattern has changed since
06-01 and the cause is still the archived `Plan: 6 of 6 complete` line in the v1.0.0 block at the
bottom of this file, which is kept verbatim and therefore cannot be edited to fix the tool.

**REQ-14 and REQ-15 are CLOSED by 05-02.** 05-01 shipped REQ-14's *recording* half — the pin,
the reading, the publication. 05-02 shipped the *verdict* half (unpinned or mismatched ⇒
UNKNOWN, with a health message that names `store_id`) and withdrew the two alert sentences
REQ-15 exists because of. Mutations rose 8/8 → 10/10; `make verify-offline` exits 0 at 595
passed.

**REQ-16 is CLOSED by 05-03.** The backoff and the paging memory now survive the process in one
gitignored `pacer-state.json` (`refusals` plus a wall-clock stamp; never `due_at`, so a restart
still asks once at full rate). Measured along the way and fixed: "pushed once" was already false
*within* one process — a cycle the pacer skipped was read as the retailer recovering, so a
refusal past the cap was re-paged at every subsequent check. Mutations rose 10/10 → 14/14;
`make verify-offline` exits 0 at 642 passed.

**Both Walmart watches read UNKNOWN in the tree, and the pin was deferred, so they stay that
way.** `store_id: ${WALMART_STORE_ID}` is unset on this host, so the config-gap guard fires and
`boty check` shows Walmart unhealthy with the store-gap reason. That is criterion 2 working, not
a regression — **do not "fix" it by inventing a default.** Confirmed live on 2026-08-10 at 12:07:
`make verify` runs in a shell with no `WALMART_STORE_ID`, Walmart **answered** rather than
challenge-blocking, and the milk control read `unknown — no store_id pinned for this watch — set
store_id in config/products.yaml`. The guard firing against a real page is the one live
confirmation this phase obtained, and it came from the tree, not from the daemon.

**Phase 5's six verdicts, in one line each** (full working: `docs/retailer-evidence.md`
§ *Phase 5 closing record*; the table is in `ROADMAP.md`):

| # | Verdict |
|---|---|
| 1 | MET in the tree — NOT DEPLOYED (the daemon's watch rows carry no `store` key) |
| 2 | MET — the one criterion with a live confirmation |
| 3 | MET — M9/M10 watched going red, 8/8 → 10/10 |
| 4 | MET in the tree — demonstrably NOT YET TRUE ON THE WIRE |
| 5 | MET — and it was already false *within* one process before 05-03 measured it |
| 6 | MET — and explicitly NOT demonstrated by any restart, because there was none |

**Nothing was reworded to reach that.** The ROADMAP's Phase 5 criteria list was renumbered
`1, 0, 2, 3, 4, 5` → `1`–`6` on 2026-08-10 — a typing slip, not an amendment — and it was proved
mechanically: both extractions yielded exactly six criterion bodies and the `diff` between them
was empty.

**v1.0.0 is open, untagged, and stays that way.** Its definition of done includes *"Dan has
successfully bought a Pokémon GO Plus +"* — a market condition, not a work item — and the
milestone audit (`.planning/v1.0.0-MILESTONE-AUDIT.md`) recommended against tagging it as
shipped. 0 integration blockers, 2 warnings, both carried into v0.2 as REQ-18 and REQ-19.

**Why v0.2 after v1.0.0.** The v1.0 numbering was itself an overclaim — declared before the
project had shipped, published or bought anything. Renumbering down is the same correction
this milestone makes everywhere else, applied to the version number. Safe only because
publishing was deferred: nothing was tagged or uploaded, so nobody can be pinned to a 1.0.0
that exists. `pyproject.toml` rolls 1.0.0 → 0.2.0 in Phase 6 (REQ-20).

## What v0.2 is

Six live findings, one shape — the system stating something it had not established:

| The claim | What was actually true |
|---|---|
| "the detector is probably broken" | It was not. Three live reads: `IN_STOCK` at $2.42, `available=True` |
| "we are asking too often" | Falsified — a 6-hour backoff was still refused on the next single request, twice |
| A Walmart reading is about Walmart | It is about *some store*. The differing price ($3.17 vs $2.42) is what proved it |
| The price ceiling filters resellers | It reads `offer.price`; $45 shipping walks through |
| The matrix states each rung | Not bound to code — mutating `check_amazon`'s rung left 131 tests green |
| The changelog ships what was written | Nothing reads its body; leaked markup shipped for a whole phase |

**Phase 5 is the only one that changes what a *product* reading means** — Walmart is one of
four retailers that can alert on the GO Plus +. Phase 6 is gates over claims.

## Carried into this milestone

- **`Pacer._state` is in-memory only IN THE RUNNING DAEMON, and persisted in the tree.** Phase 5 criterion 6. **FIXED IN THE TREE by 05-03 (2026-08-10):** `refusals`, a wall-clock stamp and the paging memory round-trip through one gitignored `pacer-state.json` at the repo root (`settings.pacer_state_path`, resolved against the unit's `WorkingDirectory`); `due_at` is deliberately never persisted, so a restart still asks each retailer once at full rate. **Not in use anywhere on this host** — the file does not exist yet, because the daemon that would write it has never been started. An empty `{"retailers": {}, "version": 1, "warned": []}` is the healthy state of a monitor with nothing in backoff, not a fault.
- **`boty.service` has been running pre-Phase-4 code since 2026-08-04 17:48:52 CDT, and 05-04 did NOT change that.** Re-measured at close on 2026-08-10: `MainPID=3059142`, `ActiveEnterTimestamp=Tue 2026-08-04 17:48:52 CDT`, `ActiveState=active` — identical before and after the plan, because Dan answered the restart checkpoint `defer`. **The do-NOT-restart-while-a-retailer-is-in-backoff warning therefore STILL BINDS, and must not be struck.** It is a statement about the *running process*, which has no persistence; 05-03 fixed the tree, not the daemon. What the first restart will cost, stated now so it is not a surprise later: the old code never wrote a state file, so there is nothing on disk to restore from and **that first restart loses the current backoff outright** — Amazon at 11 refusals and GameStop at 4 as of 12:00:34 on 2026-08-10 — and both retailers get asked at full rate again. That is a real, one-time politeness cost, bounded by the `retailer_intervals` floors that stay in force (`amazon: 1800`, `gamestop: 900` — 30 and 15 minutes, not 5). Every restart *after* that one inherits the depth. Strike this entry once the service has actually been restarted onto this tree, and not before.
- **A browser IS available on this host, and nobody knew.** `boty/browser.py` searches PATH and finds nothing, but Playwright's Chromium is at `~/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome` (Chrome for Testing 149.0.7827.55) and `BOTY_BROWSER_PATH` accepts it. With it set, `make verify` **runs all six controls** instead of skipping two — measured 2026-08-10. It still FAILS 3/6, but for diagnosable reasons rather than a missing binary: Best Buy and Target now throw a bare `fetch failed: Exception:` with an **empty message** (sandbox? nodriver vs Chrome 149?), and Amazon hits a challenge page. Worth chasing — the empty exception is itself a reporting defect, and this milestone is about not saying things you have not measured.
- **`.planning/STATE.md` is an INPUT TO AN EXECUTABLE GATE as of `30cb977`.** `tests/test_packaging_metadata.py` reads the `milestone:` key in this file's frontmatter and compares it component-wise against `pyproject.toml`'s version. It is the first time a planning file has been machine-read in this project, so an edit here is no longer free: change that line without changing the package version and `make verify-offline` goes red naming both files. Re-run `.venv/bin/python -m pytest tests/test_packaging_metadata.py -q` after editing this file, and if it is red, fix the edit rather than the gate.
- **`make verify` fails live** (`VERIFY: FAIL (live controls)`, exit 2). **Re-measured once at Phase 6's close, 2026-08-11 14:21, and the composition is UNCHANGED from Phase 5's close — three classes, and NOT ONE of them is Phase 6's.** (1) *Pre-existing since 2026-08-06:* `2/6 control(s) could not run on THIS HOST` — Best Buy and Target, `no Chrome/Chromium binary found`; `control_check.py`'s own output says this "says nothing about the DETECTOR". (2) *Pre-existing, and it did NOT manifest again:* Amazon read IN_STOCK at $9.99 and Walmart served a judgeable page, exactly as on 2026-08-10 — **two consecutive passes now support "intermittent" rather than "permanent"** for the challenge-blocking class. (3) *Phase 5's, and correct:* `FAIL — 1/6 control(s) not reading IN_STOCK` is Walmart through 05-02's config-gap guard, because `make verify` runs in a shell with no `WALMART_STORE_ID`. **Nothing new appeared, and that is a prediction confirmed rather than an absence assumed:** 06-01's F1 measured that every `max_price` in `config/products.yaml` sits on a GO Plus + product watch and every control carries none — re-confirmed at close (**exactly four `max_price: 80` entries and no others**) — so `alertable` short-circuits before any ceiling rule and no control's verdict could move under criterion 1 in either its strict or its reversed form. Run **once**, after a daemon cycle had published, not re-run for a better answer, and deliberately **not** run under the service's `EnvironmentFile` (05-04's recorded departure; the reason still binds). The mutation stage does not run inside a failing live invocation, so mutations come from `make verify-offline`, which exits **0** at **768 passed** and **24/24**. *Phase 5's own reading of this line, kept for the history it records:* **Re-measured once at Phase 5's close, 2026-08-10 12:07, and its composition had CHANGED — three classes and one of them ours.** (1) *Pre-existing:* `2/6 control(s) could not run on THIS HOST` — Best Buy and Target, `no Chrome/Chromium binary found`; the tool's own output says this "says nothing about the DETECTOR". (2) *Pre-existing, and it did NOT manifest this pass* — Amazon's control read IN_STOCK at $9.99 and Walmart served a page the store guard could judge, so **the challenge-blocking is intermittent, not permanent**; Walmart also answered normally at 09:22 the same morning. (3) **Caused by Phase 5 and CORRECT:** `FAIL — 1/6 control(s) not reading IN_STOCK` is Walmart reading UNKNOWN through 05-02's config-gap guard, because `make verify` runs in a shell with no `WALMART_STORE_ID`. Named separately here rather than folded in with the other two. The mutation stage does not run inside a failing live invocation — `make verify` exits at the control stage — so mutations are evidenced by `make verify-offline`, which exits **0** at **642 passed** and **14/14** (pre-phase baseline: 531 passed, 8/8). None of these classes is diagnosed here; classes 1 and 2 are pre-existing since 2026-08-06 and need their own plan.
- **eBay is closed.** Developers Program registration was **rejected** 2026-08-10. See `.planning/research/ebay-CLOSED-registration-rejected.md`. The delivered-total ceiling finding survived it and is REQ-17.
- **Do not put a real postal code or store id in a fixture or config without redaction.** Phase 3.1 spent seven re-verification rounds on that leak class, and Phase 5 works directly with store identifiers.

## Seeds feeding this milestone

- `.planning/seeds/walmart-store-assignment-is-unpinned.md` → REQ-14
- `.planning/seeds/notify-only-when-a-decision-changes-the-outcome.md` → REQ-15, REQ-16
- `.planning/seeds/nothing-reads-the-changelog-body.md` → REQ-19

---

# Previous milestone — v1.0.0 (open, untagged)

<!-- Kept verbatim below. v1.0.0 was not archived, because it was not completed. -->

# State: bot-y

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-08-02)

**Core value:** A stock reading you can trust — never "out of stock" when the truth is "I couldn't tell", never "in stock" when the truth is "a reseller has one at 4x MSRP."
**Current focus:** Phase 04 — open-source-ready

## Status

**Milestone:** v1.0
**Phase:** 04 of 5 (Open Source Ready) — **COMPLETE 2026-08-06**, closed on three of five criteria MET; 3 and 5 UNMET and deliberately not amended (Dan deferred publishing)
**Plan:** 6 of 6 complete (04-01 … 04-06, all waves done)
**Last session:** 2026-08-10T23:03:51.942Z
**Stopped At:** Completed 06-05-PLAN.md — criterion 5 built, red before the roll and green after

1. **The § 0e history purge (2026-08-04).** Dan chose option 2. `filter-repo` over all 170 commits, force-pushed, verified against a fresh clone. Backup bundle at `~/CodeProjects/bot-y-prefilter-20260803-1745.bundle` is the only remaining copy of the values. Prevention shipped with it: `scripts/identity_check.py` scans **every tracked file** (the leak that mattered was in `.planning/`, not `tests/fixtures/`) and runs at commit time via a tracked `hooks/pre-commit` + `make hooks`, as well as inside `make verify`.

2. **Pacing and backoff (2026-08-04), in response to a live alert.** Amazon and GameStop had been refusing us for a day. Not a detector bug: `interval_seconds` is per PASS, so load is `watches x 288/day` — Amazon 576, GameStop 1,440 — with no backoff at all. Worse, every failing control was reported as "the detector is probably broken", which is false for a refusal and sent 20 pages in 24 hours. Added `Result.refused` / `fetch.is_refusal`, split the health message, added `boty/pacing.py` (per-retailer cadence + exponential backoff, capped, reset on a good read), and stopped paging for refusals until they outlast the backoff. Verified live: 0 pages while both retailers refused, both published as `paced` rather than dropped.

**Last Activity:** 2026-08-11
**Last Activity Description:** Phase 6 execution started

3. **Two live detector failures (2026-08-04 evening), both caught by control products within a cycle, neither a broken detector.** Best Buy began serving its JSON-LD **JavaScript-escaped** — `\'` inside strings, literal `\n` outside them — so `json.loads` refused all three blocks, `parse.py` skipped them silently, and the control read UNKNOWN with a detail naming the wrong cause. Proven against the shipped fixture, which parses 3/3 on the same SKU with no backslashes at all. `ldjson_read` now parses strictly first and only then offers an already-failed block to a string-state-aware repair; it reports `blocks`/`unparseable`/`repaired`, and a repaired read publishes as `ld+json (repaired)` so it cannot look ordinary. **Not claimed:** that the repair restored the live reading — Best Buy was serving valid markup again by 17:45 and the live read carried no `(repaired)` marker. The escaping is intermittent; a clean probe does not disprove it. Separately, **Target's UNKNOWN was our own render race**: ~35 KB of markup carrying the add-to-cart control arrives between 1s and 3s (measured: absent at `settle=1.0`, present at 3.0 and 6.0), and `fetch_rendered`'s default is exactly 3.0. `check_target_browser` now re-renders once at 10.0s before concluding — in the adapter, because it is a layout question and `boty/browser.py` is deliberately ignorant of layout. **M2's anchor was re-pointed** because this change moved the line it named, and the harness refused to run rather than quietly drop to seven mutations. Verified: mypy clean, 419 passed, 8/8 mutations, `VERIFY: PASS (OFFLINE)`, both new gates watched failing in both directions (removing the repair reddens 3 tests, making it over-reach reddens 22), **service restarted onto the fixed code** and publishing **6/6 retailers healthy**, 13 watches, 47.1s of REQ-08's 120s.

**Previously:** 03.1-03 **asked Amazon the question Phase 3 never asked, and Amazon answered.** Three `/dp/<ASIN>` requests through `boty.fetch.get`: **HTTP 200 every time**, 1,893,079 / 3,189,747 / 3,223,370 B, **zero `BLOCK_PHRASES` matches**, correct product titles. So the rung-4 verdict that rested entirely on a reading of the Conditions of Use is now `**Verdict: REACHABLE (rung 1)**` — and **nothing behind the old verdict was retracted**: the six policy reads, the LICENSE AND ACCESS clause and the whole `robots.txt` analysis all stand, and the four sentences saying no product page had ever been requested are quoted, dated and marked historical rather than edited. **Shape C: rung 1 + `dom`.** Amazon publishes NO structured data on `/dp/` — zero `ld+json`, no `__NEXT_DATA__`, and not one JSON blob with a price, an availability or a seller — but it serves the add-to-cart control, the `#availability` line and a named buy-box seller in the plain HTTP response. So `check_amazon` is the cheapest transport in this project with the most fragile extraction in it, which is precisely what 03.1-05 widened `degraded` for. **The ASIN came from the Internet Archive CDX index; zero requests to amazon.com to find it.** `parse.add_to_cart_offers` was **widened, not duplicated** — Amazon's control is a void `<input>` labelled by its `value` attribute — and its seller default is now **per page family**, because carrying Target's first-party-by-absence rule to Amazon would have let a reseller alert off any buy box the parser could not read. Amazon **does** list the GO Plus +, and the only offer is a **USED unit at $219 from `LO Store (We Record Serial Numbers To avoid FRAUD)`** against $54.99 MSRP: both flipper defences suppress it, the seller filter first. **Amazon refused us exactly once, and it was our own fault** — two captures 12 s apart instead of 20 — and that wall **matched no `BLOCK_PHRASES` entry**, so `fixtures.capture` wrote a captcha gate to disk under a product's name. Deleted, phrase added, wall embedded verbatim as a test constant; the obvious phrase was rejected because *"something went wrong on our end"* appears in both real Amazon product pages. **Rule 6 landed too:** a REFUSED verdict must now cite a *measured* observation, HARD_TWO members need two including one at rung 3, and it is watched going red against the **verbatim pre-03.1 § Amazon and § Target text lifted from `339800e`** — 658 lines of accurate writing containing not one observation. Live: **6/6 controls**, `healthy: true`, 13 watches across 6 retailers in **48.9 s** of REQ-08's 120 s, `make verify` bare-PASS, 8/8 mutations, 377 tests.

**Previously:** 03.1-02 registered **Target — the fifth retailer**, at rung 3 with `dom` extraction, **control-only**. Its pages carry no structured data at all, so `parse.add_to_cart_offers` reads the rendered add-to-cart button: enabled means buyable, `disabled=""` means out of stock. That distinction is measured, not assumed — Target KEEPS the button and disables it — which is what lets the reader return `None` (UNKNOWN) for an absent control without trading anything away. `check_target_browser` labels `rung=browser` + `extraction=dom` on every path, and `_verdict_from_html` gained an opt-in `allow_dom` that carries `extraction=` on all six returns including the no-offers UNKNOWN (plan-check W-2 closed). `FIRST_PARTY['target']` stopped being an unverifiable guess and became a statement about our own reader's output. M8 mutates the availability decision; 8/8 caught. Live: **5/5 controls**, Target IN_STOCK $12.59, `[control] [degraded] [dom]`, full pass 40.1 s of REQ-08's 120 s, `make verify` bare-PASS. **The fixture nearly repeated the incident that destroyed this repo:** the raw capture carried a session token, a visitor id, Akamai's geolocation of this host and five nearby stores with street addresses — and the automated leak guard PASSED on it, because it knew EdgeScape's `lat=` form and Target writes JSON. Redacted by emptying every `<script>`; the guard was then widened and **found the same leak class already committed in two Walmart and two Best Buy fixtures**, including this host's own ZIP, public since Phase 2. All redacted. Target still cannot watch the GO Plus + — it delisted the product — so ROADMAP criterion 1 stands UNMET.

**Previously:** 03.1-05 shipped the **Extraction axis** — `Extraction` (`structured` | `dom`) beside `Rung` as a second independent axis, nothing renumbered, with `Result.degraded` widened to `self.rung is Rung.BROWSER or self.extraction is Extraction.DOM`. That closed a latent hole before the adapter that would have exposed it, and 03.1-02 is the adapter: Best Buy and Target are both "browser", and only the extraction axis says that one reads a schema.org feed and the other reads markup a reskin breaks silently. Before that, the rung-1 probe (`c79e8ce`, kept as `03.1-02-PROBE-RECORD.md`) found Target serving the page and withholding the data, and disproved that Target still lists the GO Plus +.
**Resume File:** None
**Next command:** **`/gsd-execute-phase 4`** — and NOT `/gsd-autonomous`. Phase 4 is already planned: 6 plans in 6 waves, committed, plan-checker passed at round 3 after two revision rounds (7 → 5 → 3 issues). `/gsd-autonomous` would re-enter plan-phase, find existing plans, and stop on the interactive add/view/replan prompt. Execution is authorised for **waves 1–5**; **wave 6 (`04-06`) is `autonomous: false`** and checkpoints for Dan — the PyPI Trusted Publisher is dashboard-only and the `v1.0.0` tag is his to push. After the phase closes: `/gsd-audit-milestone` → `/gsd-complete-milestone v1.0.0` → `/gsd-cleanup`. **`main` has NO upstream configured** (`fatal: no upstream configured for branch 'main'`, a side effect of the 0e `filter-repo` + force-push) and 19+ commits are unpushed — set it with `git push -u origin main` when Dan says so. The § 0e blocker that caused the previous halt is **closed and executed**; nothing blocks Phase 4.

**One correction to what 03.1-03 wrote here, and it matters.** That entry claimed *"ROADMAP criterion 1 is now MET and Amazon is what moves it."* It is not. Criterion 1 is specifically **"Target reports stock for the GO Plus +"**, and Target *delisted* the product — so it **stands UNMET**, exactly as the ROADMAP records it and exactly as Dan decided when he declined the rewrite that would have made it meetable. Amazon carrying a real product watch is criterion **2**, which is met. Conflating the two would have quietly closed the one criterion this phase deliberately left open.

Carried forward for whoever picks up Phase 4:

- **Six retailers, and now actually deployed.** The service ran pre-phase code for the whole of waves 3–5. **A restart is part of shipping a retailer** — `make verify` runs the tree, not the daemon, and the two can disagree silently. Confirm with `served/boty/status.json` carrying 13 watches and six `retailers` health entries.
- **Read the six as a four and a two.** Best Buy and Target are control-only — neither carries the GO Plus + — so only **four** of the six could ever alert on the product. Now stated in README prose rather than left to be worked out from the table.
- **`TARGET_RETAILER_COUNT` is 5.** Do not raise it without a commit that says so and a test attached.
- **Pokémon Center is the only retailer in scope still REFUSED**, and it clears rule 6's higher bar with four observations across two rungs.
- **`_SHIPPED` in `tests/test_evidence_check.py` is still the four retailers** and still feeds synthetic trees — widen at the call site, not the constant.
- **`QUESTIONS.md` § 0e is the only open decision:** four already-public fixtures carry this host's ZIP in pushed git history. Not blocking; Dan's call between leaving it, a `filter-repo` rewrite, or recreating the repo.

## What Exists

Working and deployed on danserver before this roadmap was written:

- `boty/` — 854 lines: models, fetch, parse, retailers, monitor, notify, status, config, cli
- GameStop (schema.org JSON-LD) and Walmart (`__NEXT_DATA__`, seller-aware) adapters, both control-verified
- `boty.service` + `boty-web.service`, both active and enabled at boot
- Status page on loopback :8821, reachable at `/tools/boty` through Mission Control
- Telegram notifications, delivery confirmed end to end
- Repo public at https://github.com/danieljamesjohnson/bot-y (Apache-compatible MIT)

## Blocked

- ~~**Best Buy API key** — needed for REQ-04.~~ **No longer blocking.** 02-01 proved
  the credential-free rung-3 path works (`docs/retailer-evidence.md`), and REQ-04 is
  satisfied without a key. A key remains an optional upgrade: set `BESTBUY_API_KEY`
  and Best Buy prefers the API and drops the DEGRADED flag. Nothing waits on it.

## Known Risks

- ~~**Amazon may be unreachable** without a browser or paid residential proxies.~~ ~~**Settled 2026-08-03 by 03-01, and not for the expected reason.**~~ **Re-settled 2026-08-03 by 03.1-03, and the concern was backwards.** Amazon needs neither a browser nor a proxy: it serves `/dp/<ASIN>` to plain impersonated HTTP — three requests, three HTTP 200s, 1.9–3.2 MB, zero `BLOCK_PHRASES` matches. What it does *not* serve is any structured data at all: zero `application/ld+json`, no `__NEXT_DATA__`, no JSON blob carrying a price, an availability or a seller. So Amazon is **rung 1 + `dom`** — the cheapest transport here with the most fragile extraction here — reading the server-rendered add-to-cart control, `#availability` and buy-box seller. Every reading is `degraded` on the extraction axis alone. **The real risk is now the opposite one:** an Amazon buy-box redesign breaks this silently, with no error and no 403, which is why a control watch on `B00NTCH52W` and mutation M8 both cover it. Amazon also **throttles on cadence** — two requests 12 s apart drew a captcha interstitial at HTTP 200 that matched no block phrase, so `fixtures.capture` wrote it to disk; the phrase was added and the file deleted. Evidence in `docs/retailer-evidence.md` under `## Amazon`.
- ~~**Target is unresolved.**~~ ~~**Settled 2026-08-03 by 03-02, and not for a technical reason.**~~ **Re-settled 2026-08-03 by 03.1-02, and now it IS a technical reason.** Dan reversed the Terms-of-Use call, Target was probed on the path its own `robots.txt` publishes, and it **did not refuse us**: three pages, all HTTP 200, no challenge, no `BLOCK_PHRASES` match, `"isBot": false`. It also gave us nothing — **zero** `application/ld+json`, `"price"`, `availability` or `"seller"` anywhere in ~315 KB, because Target ships the price module empty (`isProductDetailServerSideRenderPriceEnabled: false`) and renders stock from `redsky.target.com`, which is `Disallow: /` for every agent. Rung 1 is open and empty; rung 2 is closed in writing; rung 3 reaches the data only by making the rung-2 requests through a browser. Still rung 4, but the reason is now an observation. **Target also no longer lists the GO Plus +** — TCIN `88714054` served HTTP 200 as late as 2025-05 and now 404s. Not registered: a control would read UNKNOWN forever. Evidence under `## Target`, 2026-08-03 heading; the open decision is `QUESTIONS.md` 0d.
- **Fixtures go stale.** Saved HTML is a snapshot; a retailer can change its page and the fixtures will keep passing. Control products cover the live case, fixtures cover regression — neither substitutes for the other, and Phase 1 should make that split explicit.

## Decisions Pending Evaluation

- Building new rather than forking changedetection.io
- Curated adapters over generic extraction
- Deferring async and a plugin API

---
*Last updated: 2026-08-02 at project bootstrap*

## Performance Metrics

| Phase | Plan | Duration | Notes |
|-------|------|----------|-------|
| Phase 01 P01 | 8min | 4 tasks | 11 files |
| Phase 01 P02 | 4min | 6 tasks | 5 files |
| Phase 01 P03 | 5min | 3 tasks tasks | 10 files files |
| Phase 01 P04 | 25min | 6 tasks | 5 files |
| Phase 02 P01 | 62min | 3 tasks | 6 files |
| Phase 02 P02 | 34min | 3 tasks | 10 files |
| Phase 02 P03 | 71min | 3 tasks | 12 files |
| Phase 02 P04 | 35min | 3 tasks | 15 files |
| Phase 03 P01 | 34min | 3 tasks | 6 files |
| Phase 03 P02 | 19min | 3 tasks | 4 files |
| Phase 03 P03 | 47min | 3 tasks | 10 files |
| Phase 03.1 P01 | 62min | 3 tasks | 5 files |
| Phase 03.1 P02 | 78min | 1 tasks | 3 files |
| Phase 03.1 P05 | 8min | 2 tasks | 11 files |
| Phase 03.1 P02 | 35min | 3 tasks | 21 files |
| Phase 03.1 P03 | 47min | 3 tasks | 17 files |
| Phase 03.1 P04 | 21min | 2 tasks | 5 files |
| Phase Phase 04 PP01 | 16min | 3 tasks tasks | 5 files files |
| Phase 04 P02 | 30min | 3 tasks | 5 files |
| Phase 04 P03 | 50m | 3 tasks | 16 files |
| Phase 04 P04 | 80m | 3 tasks | 4 files |
| Phase 04 P05 | 22m | 3 tasks | 10 files |
| Phase 04 P06 | 35 | 3 tasks | 4 files |
| Phase 05 P01 | 25min | 4 tasks | 19 files |
| Phase 05 P02 | 20min | 3 tasks | 10 files |
| Phase 05 P03 | 27min | 3 tasks | 9 files |
| Phase 05 P04 | 20min | 3 tasks (1 checkpoint answered `defer`, 1 not entered) | 5 files |
| Phase 06 P01 | 44min | 3 tasks (2 TDD, so 5 code commits) | 11 files |
| Phase 06 P02 | 41min | 3 tasks | 3 files |
| Phase 06 P03 | 38min | 3 tasks | 1 file |
| Phase 06 P04 | 47min | 3 tasks (2 commits — the green side was never committed alone) | 1 file |
| Phase Phase 06 PP03 | 38min | 3 tasks tasks | 1 file files |
| Phase Phase 06 PP04 | 47min | 3 tasks tasks | 1 file files |
| Phase 06 P05 | 31min | 3 tasks | 6 files |
| Phase 06 P07 | 32min | 3 tasks (2 TDD, so 5 code commits) | 11 files |
| Phase 06 P06 | 42min | 3 tasks (1 checkpoint, already answered 2026-08-11 and shipped as 06-07) | 5 files |

## Decisions

- [Phase 01]: FIXTURE_ROOT anchors to the repo root, not cwd — A cwd-relative fixture path makes load() succeed or fail depending on where the test runner was invoked from — flakiness that fixtures exist to remove
- [Phase 01]: A blocked or failed fetch writes no fixture at all — A CAPTCHA interstitial saved under a product name would make the whole suite assert against a bot wall while looking green
- [Phase 01]: Walmart GO Plus + reseller fixture is real, not synthetic — The live buy box is still held by Clove Brothers LLC at $229.99, so the plan's synthetic-fixture contingency was not needed
- [Phase 01]: The network guard has its own self-test — a guard nobody verifies can rot after an upstream rename and the suite would start hitting live retailers with no visible symptom
- [Phase 01]: Offline-ness proved by running the suite in an interface-less network namespace, not just by trusting the monkeypatch
- [Phase 01]: REQ-03 left unchecked by 01-02 — type hints and mypy are 01-03's deliverable, and marking it here would be a false green in the traceability table
- [Phase 01]: The planned mypy config was a false green — non-strict mypy skips unannotated function bodies, so the whole package passed before a single annotation was written — disallow_untyped_defs makes the check enforce REQ-03 rather than decorate it
- [Phase 01]: The type check was proved to bite by deleting the offer-is-None branch and confirming mypy flags it — A Success line over an unannotated codebase asserts nothing
- [Phase 01]: dev extra mypy floor raised 1.8 -> 2.0 — mypy 2.x is meaningfully stricter by default, so a contributor resolving 1.x would run a weaker check than the one this config was verified against
- [Phase 01]: Any confined to the JSON boundary in boty — _as_float, _dig, Page.json and _expand sit where a retailer payload shape is not ours to promise; every one of boty's own types is named
- [Phase 02]: Best Buy is REACHABLE on rung 3 — A headless browser reads its product pages and they carry complete schema.org data — availability, price and a first-party seller
- [Phase 02]: Best Buy's legacy /site/<slug>/<sku>.p scheme is uniformly refused with ERR_HTTP2_PROTOCOL_ERROR — The live scheme is /product/<slug>/<ID> where <ID> is not the SKU, so an adapter cannot construct product URLs from a SKU
- [Phase 02]: MARKETPLACES needs no change for Best Buy — Best Buy sets offers[].seller.name to 'Best Buy', already in FIRST_PARTY, so its offers never fall into the unattributed-on-a-marketplace UNKNOWN path and a control can go green
- [Phase 02]: No evidence Best Buy carries the GO Plus + at all — Two searches returned only gift cards and unrelated titles; SKU 6577129 in test_retailers.py:316 appears nowhere in Best Buy results and is an unverified fixture value
- [Phase 02]: nodriver installed as an OPTIONAL extra only, after a supply-chain audit — It is AGPL-3.0 to this project's MIT, and a contributor working on the HTTP retailers must never be forced to pull a browser stack
- [Phase 02]: Chrome's sandbox stays on by default; BOTY_BROWSER_NO_SANDBOX is opt-in per host and logs a warning — Rung 3 executes attacker-controlled retailer JavaScript, so an isolation downgrade must be something a person chose rather than a silent default
- [Phase 02]: Rung is a separate enum beside Availability, not a fourth availability value — monitor.assess_health and transitioned_to_stock branch on Availability and cli.SYMBOL is indexed unconditionally, so a fourth member is a KeyError mid-report
- [Phase 02]: Result.degraded is derived from rung, never stored — one source of truth, so the support matrix claim and the runtime flag cannot drift apart
- [Phase 02]: Degradation does not feed Health.ok and does not suppress alerts — assess_health answers 'is this detector verified', not 'how confident is the transport'; feeding it in would make phase criterion 4 (five retailers with no health warnings) unreachable by construction
- [Phase 02]: Best Buy is supported credential-free on rung 3 (browser, DEGRADED); an API key upgrades the same watch to rung 2
- [Phase 02]: bestbuy_product_url resolves a SKU via Best Buy search — chosen because its MISS path was verified to carry no Product markup
- [Phase 02]: No Best Buy GO Plus + watch ships: Best Buy does not carry the product; SKU 6577129 disproved and removed from tests
- [Phase 03]: Target is rung 4, settled by its Terms & Conditions — The Unlawful or Prohibited Uses bullet forbidding data-gathering tools and storing prices carries NO commercial-use qualifier, unlike the bullet above it which does
- [Phase 03]: Zero requests were made to any Target product page — 4 curl requests total, all policy documents and robots.txt, so the evidence log states as a fact rather than a policy that bot-y makes no requests to target.com
- [Phase 03]: Target's robots.txt is BROADER than its ToU, the opposite direction to Amazon's — /p/ carries no Disallow and sitemap_pdp-index.xml.gz is published, so a naive reading would have been encouraging; the broader written document still governs
- [Phase 03]: Rung 2 (RedSky) closed four ways — redsky.target.com/robots.txt is Disallow: / for every agent; the key is Target's internal front-end constant not an issuable credential; the terms cover all hosts; and it is CAPTCHA-gated
- [Phase 03]: FIRST_PARTY['target'] stays a guarded guess, neither widened nor deleted — Widening needs a live page the terms forbid fetching; deleting would edit boty/retailers.py in a plan whose finding is that no code change is warranted. An offline test now fails the moment a target watch makes it live
- [Phase 03]: The five-retailer criterion is UNMET at four, and now final — Both Phase 3 candidates refused in writing and Phase 2's fifth-retailer search established no other US retailer stocks the GO Plus +, so there is no honest path to five
- [Phase 03]: Phase 3 criterion 5 recorded UNMET at four retailers, final: both hard-two retailers are rung 4 by written prohibition and nothing was added to config/products.yaml — Amazon and Target each refused in writing with zero product-page requests; there is no sixth US retailer stocking the GO Plus +, and a control-only fifth was declined in Phase 2
- [Phase 03]: REQ-08 measured rather than asserted: duration_seconds is published by every pass, 61.4s manual and 35.0s service-published against a 120s budget at 10 watches / 4 retailers — The only prior figure was hand-timed; a published key means the budget can be read after any pass instead of re-measured, and None distinguishes an untimed pass from a zero-length one
- [Phase 03]: CR-01 durability closed by elapsed time: zero zombie children and zero leaked browser profiles, flat across 41 minutes and 7 completed cycles — 02-VERIFICATION.md left it open because the teardown tests drive a fake nodriver and a one-shot make verify cannot measure a daemon-lifetime property

- [Phase 03.1]: W-02 closed by rule 5 (a configuration cannot outrank a refusal) — Rules 2 and 4 both `continue` on `retailer in configured`, so a tree shipping a detector for a retailer its own log records as REFUSED returned `PASS — phase` exit 0; `make verify` caught it only by accident of Imperva blocking a fixture capture, which is a property of one vendor rather than of any rule
- [Phase 03.1]: Rule 5 stays silent for a configured retailer with no evidence section at all — GameStop and Walmart have never had one, and demanding one would redden the shipped tree with the fastest green being invented records
- [Phase 03.1]: `unread` is a fourth position vocabulary word, pinned to five named cells — Three of four retailers refused their own policy documents on 2026-08-03; writing `permits` for an unread file would be inventing evidence, and `silent` on the robots side actively means permission
- [Phase 03.1]: No escalation to `curl_cffi` after plain `curl` was refused — GameStop's and Best Buy's positions stay `unread` rather than being obtained through the impersonating transport; that is a later plan's decision to take deliberately
- [Phase 03.1]: Nintendo is marked `⚠ disagree` although it ships — Its robots.txt is `Allow: /` with a published store sitemap while § 6 of its Terms of Use bars "any robot … spider, crawler, scraper or other automated means"; REQ-13 states the disagreement rather than resolving it by dropping a working retailer
- [Phase 03.1]: Target reached at rung 1 and NOT registered — its pages carry no price, availability or seller at all, so a control would read UNKNOWN forever and the detector could never detect
- [Phase 03.1]: Rung 3 not walked for Target — it reaches the stock data only by making the browser call redsky.target.com (Disallow:/ for every agent); Dan's reversal settled the Terms of Use, not robots.txt, so the question was escalated rather than answered
- [Phase 03.1]: FIRST_PARTY['target'] stays a guess because it is unverifiable, not unverified — Target's product pages carry no offers.seller.name at any permitted rung
- [Phase 03.1]: Target no longer lists the Pokemon GO Plus + — TCIN 88714054 was HTTP 200 as late as 2025-05 and now 404s; a disproof in the Best Buy shape, found via the Internet Archive CDX index after every general search engine refused us
- [Phase 03.1]: Extraction is a second axis, not a fifth rung — Rung keeps meaning transport, nothing is renumbered, and rung 4 keeps meaning 'dropped, with the evidence written down' — Folding extraction into the ladder would renumber a scale four phases of documents refer to by number, and make the support matrix and rung 4 say something they do not mean
- [Phase 03.1]: Result.degraded widened to fire on a browser transport OR a dom extraction, with a mutation per disjunct — It was derived from the rung alone, so a rung-1 DOM adapter — the most fragile thing this codebase could acquire — would have shipped looking fully trustworthy; M6 dying proves the flag exists, only M7 proves the new half is load-bearing
- [Phase 03.1]: Result.extraction declared LAST with a default of STRUCTURED, and Extraction fed into neither Availability nor Health — Every pre-existing construction site stays valid and keeps its meaning; a fourth Availability member is a KeyError in cli.SYMBOL mid-report, and a dom reading flipping Health.ok would raise a permanent health warning that never clears
- [Phase 03.1]: The README Extraction cell is tied to the Rung cell in BOTH directions — a rung-4 row must say '—' and a working-rung row never may — A '—' accepted unconditionally would be the REQ-13 escape hatch UNREAD_POSITIONS had to be pinned against: paste it into all seven rows and the column distinguishes nothing while looking filled in
- [Phase 03.1]: Target is the fifth retailer: rung 3 + dom extraction, control-only, every reading degraded. Its pages carry NO structured data, so the rendered add-to-cart button is the only stock signal there is.
- [Phase 03.1]: FIRST_PARTY['target'] is now a statement about our own reader's output (parse.TARGET_FIRST_PARTY_SELLER) rather than an unverifiable guess about Target's markup — Target publishes no seller name at any rung.
- [Phase 03.1]: The rung-3 Target fixture leaked this host's geolocation, a session token and nearby-store addresses, and the automated guard PASSED on it. Redacted by emptying every <script> body; the guard was widened and then found the same leak class already committed in 4 walmart/bestbuy fixtures.
- [Phase 03.1]: Criterion 3 recorded MET at SIX, not five — Amazon landed, so the criterion's own upper form applies; the arithmetic is an explanation rather than a confession, and TARGET_RETAILER_COUNT stays at 5 because a threshold of 6 would fire on the honest answer the next time Amazon walls
- [Phase 03.1]: ROADMAP criterion 1 recorded UNMET and deliberately not amended — Target delisted the GO Plus + so no work satisfies it, and Dan declined the rewrite that would have made it meetable; five-of-six with one honest failure is worth more than six-of-six with one quiet edit
- [Phase 03.1]: boty.service was still running pre-phase code and publishing 4 retailers with no extraction key while the tree shipped 6 — restarted before the service-cycle duration was taken, because make verify runs the tree and cannot see the daemon
- [Phase 03.1]: REQ-08 re-measured at six retailers with two browser rungs — 45.98 s manual and 44.81/42.84 s from the service's own cycles, all read off status.json duration_seconds rather than hand-timed, against a 120 s budget; healthy read in the same breath, because a permanently-UNKNOWN retailer satisfies a count while failing the criterion
- [Phase 04]: The contributor docs say THREE of six retailers need no adapter code, not five — _make_checker has arms for bestbuy, amazon and target and falls through to check_html for the rest; the plan's five was never measured
- [Phase 04]: A documentation gate in the shape of test_support_matrix.py — cited paths must exist, no citation may carry a line number (04-03 moves hundreds), and every pinned (file, symbol) pair holds in both directions; each rule watched failing against a corrupted copy of the real file
- [Phase 04]: A SANDBOX_CONTENTS entry lands in the same commit as the file it names, and is proven load-bearing by removal — both 'hooks' and 'CONTRIBUTING.md' were watched producing HARNESS ERROR at the baseline, not asserted to matter
- [Phase 04]: No test in 04-01 stats LICENSE — 04-02 creates it in wave 2, and a stat would make this gate pass or fail on another plan's completion order
- [Phase 04]: The non-repo question decided by giving the mutation sandbox a git index, not by skipping and not by returning an absence — and _tracked_top_level_dirs ALSO raises the named NotATrackedTree in both of git's failure shapes — Stripping the index out then makes make verify die naming the cause instead of going green having checked nothing; watched failing, exit 128, exactly 1 failed test and the 3 identity-check skips back
- [Phase 04]: setuptools does NOT check that a license-files target exists — it builds, emits License-Expression, silently drops License-File and says nothing — The build is not the gate. tests/test_packaging_metadata.py is, and it was watched failing against a real license = Apache-2.0 edit to pyproject.toml, not only against a synthetic copy
- [Phase 04]: MANIFEST.in prunes rather than grafts — eight prune lines, no exclude lines — Shipping tests/fixtures/ would put captured retailer HTML in a public artifact and this repo redacts fixtures by class rather than by value for exactly that reason; measured, the unmanifested sdist carried every tests/test_*.py and none of the fixtures or conftest they need. exclude lines are avoided because one naming a file that never entered warns on every build forever
- [Phase 04]: No Development Status classifier, no Changelog URL and no Typing :: Typed in 04-02 — The first two are claims about a version and a file that do not exist yet and land with 04-05's 1.0.0 bump; the third would advertise a typing contract no installed consumer can act on, since there is no boty/py.typed marker
- [Phase 04]: The sandbox git index costs make verify's mutation stage ~29s and that is accepted, not a defect — Sandbox suite 6.0s -> 9.2s across nine sandboxes, entirely from the un-skipped identity scan — git init plus git add -A are 0.09s. Recorded so 04-04 or a contributor meeting slower CI does not remove the index to get it back
- [Phase 04]: B905 resolved as strict=True, against ruff's own unsafe autofix — a truncated alerts list is a missed restock that reads exactly like a quiet market — 04-03 Task 2
- [Phase 04]: E501 not selected and ruff format not adopted: 497 findings over the comment blocks carrying this project's recorded decisions, and 32 of 36 files reformatted immediately before a 1.0.0 tag — 04-03 Task 1
- [Phase 04]: external = [E402] rather than deleting the seven noqa directives RUF100 calls unused — ruff's own E402 enforcement stays on — 04-03 Task 1
- [Phase ?]: 04-04: CI delegates to the Makefile — one job, one step, make verify-offline, so there stays one definition of the check order and one of the verdict
- [Phase ?]: 04-04: both GitHub Actions pinned to 40-char commit SHAs (actions/checkout v7.0.1 = 3d3c42e5, actions/setup-python v7.0.0 = 5fda3b95), never to a mutable tag
- [Phase ?]: 04-04: no caching in CI, including setup-python's cache: input — the saving is seconds against a 1m05s check, and a cache restore is unreviewed content the next steps execute
- [Phase 04]: 04-05: the wheel test found a real packaging bug and this plan fixed it rather than filing it — boty check on a clean-venv wheel install raised FileNotFoundError at config/products.yaml, a path only a git checkout has; make verify runs from the repo root where it resolves, so nothing else in this project would ever have seen it
- [Phase 04]: 04-05: packaging a default config was considered and REJECTED — the watches, price ceilings and control products are the operator's decisions; shipping config/products.yaml would publish this maintainer's list to every installer and teach a new user those watches are the tool's
- [Phase 04]: 04-05: build and twine go into an ephemeral venv, never the dev extra — building inside .venv cannot detect a missing Requires-Dist because the imports resolve anyway from packages lying around; a release extra was rejected because it publishes a Provides-Extra claim and still builds wherever the caller stands
- [Phase 04]: 04-05: release-check is a Makefile target, not a verify stage and not a README stage-table row — it needs the network and CI runs verify-offline on every PR; a README row would break 04-03's test_the_documented_stages_are_the_stages_verify_runs, which asserts set equality with the stages verify invokes
- [Phase 04]: 04-05: PyPI Trusted Publishing over OIDC, never an API token in repository secrets — a long-lived upload token in a public repo is reachable by any future workflow edit and outlives everyone who remembers it was created; OIDC removes the secret and scopes the grant to one repo, one workflow and one environment
- [Phase 04]: 04-05: two jobs in release.yml, with the claim stated SMALL — splitting stops build-backend code obtaining a mintable PyPI token; it does NOT stop a malicious tag publishing a malicious package, and a control whose limits nobody knows is a control nobody maintains
- [Phase 04]: 04-05: Development Status :: 5 - Production/Stable, with 4 - Beta rejected in writing — tagging 1.0.0 while classifying the package Beta is exactly the asserted-versus-real disagreement this phase exists to close, and leaves a reader to decide which number to believe
- [Phase 04]: 04-05: the action-owner rule was WIDENED to TRUSTED_ACTION_OWNERS = (actions, pypa), never deleted — pypa already publishes setuptools, which build-system requires executes on every build here; two corruption tests still watch the rule bite on an owner in neither entry
- [Phase 04]: 04-05: the boty/bot-y name confusion is ACCEPTED, with documentation as the only mitigation — PyPI does not release a name that has files, so the neighbour cannot be defensively claimed; boty is Time Flies by Bart Thate, 0.1.1, last released 2012-03-10, homepage on dead googlecode
- [Phase 04]: 04-05: REQ-11 deliberately NOT marked complete — this plan bumped the version and proved a wheel locally; neither is a PyPI publish nor a pushed tag, and 04-06 closes REQ-11 by measuring what Dan actually publishes
- [Phase 4]: Phase 4 closed 2026-08-06 on three of five criteria MET. Dan deferred publishing — verbatim: "i don't think we need to host it yet. it's probably not quite ready for that" — so criteria 3 (pip install from PyPI) and 5 (a tagged v1.0.0) stand UNMET and were NOT reworded, on Phase 3.1 criterion 1's precedent. REQ-11 stays Pending. 04-06-HANDOFF.md is on disk with all four publish steps and exact strings, so closing it later needs no replan.
- [Phase 4]: The main branch WAS pushed (b0a272f..76d4156, upstream configured) but by the orchestrator agent, not by Dan. Steps 2-4 of the handoff card — trusted publisher, tag, publish — were not done. Nothing is on PyPI (HTTP 404) and zero tags exist locally or on origin.
- [Phase ?]: 05-01: the real Walmart store number reaches the daemon as ${WALMART_STORE_ID} from the mode-600 EnvironmentFile, never as a literal in the tracked public config and never via a second overlay file — ${VAR} substitution already exists in config.py and already argues this exact case, and an unset variable degrades to unpinned, which is the behaviour REQ-14 asks for anyway
- [Phase ?]: 05-01: parse.nextdata_store reads product.location.storeIds, NOT contentLayout.pageMetadata.location.storeId — the rejected path is page-layout metadata, a fact about the chrome the page rendered; the chosen one sits under the very node the offer comes from, so a price and a store cannot come from different subtrees and disagree
- [Phase ?]: 05-01: NO 0 special case anywhere in the parser — 0 in both Walmart fixtures is this repo's own redaction placeholder from 8dec2e0, sitting in identity_check's allow-list beside 00000 and XX, not Walmart's no-store sentinel; 05-PATTERNS.md inferred otherwise and is wrong
- [Phase ?]: 05-01: an absent store_id LOADS and is carried as data on the Watch while a bool REFUSES the file — _sub's idiom for the absence (crashing would take down five healthy retailers over one Walmart watch, and the health message needs a running daemon), _price's for the typo
- [Phase ?]: 05-01: the identity guard was measurably blind to every YAML spelling of store_id and was widened and watched going red on all four spellings BEFORE the key was written into the tracked config; the new rule's character classes must not be simplified to a lowercase-only form, which does not catch storeId without re.I doing the work
- [Phase ?]: 05-01: REQ-14 deliberately NOT marked complete — this plan shipped the recording half; the verdict half is 05-02, which the outline's own traceability table names as the closer. Same reasoning that left REQ-11 Pending after 04-05
- [Phase ?]: 05-01: _identity_leaks exists TWICE (scripts/identity_check.py and tests/test_fetch.py) and the copies have drifted in two behavioural ways — ZZ in the allow-list, and _is_reserved_ip vs a bare 192.0.2. prefix. Only the shipped script was widened; reconciling would redden a grid cell and is a decision of its own, flagged for a later plan
- [Phase 05]: REQ-14 and REQ-15 close together in 05-02: the store guard and the alert-text withdrawal both rewrite the same function, so splitting them would have been contention disguised as parallelism
- [Phase 05]: A claim about ABSENCE is gated with ast.parse (docstrings excluded by node identity), never grep — this repo's own comments quote the withdrawn sentences, so a text gate rots into a vacuous pass
- [Phase 05]: monitor.CAUSE_UNKNOWN is carried by exactly the refusal and breakage arms and by neither the no-control nor the store-gap arm — saying 'the cause is not established' about a gap we can name is the same dishonesty pointed the other way
- [Phase 05]: due_at is never persisted; refusals plus a wall-clock stamp are — watch_loop drives Pacer with a synthetic clock starting at 0.0 every process, so a persisted due_at either fires immediately or blocks a retailer for the age of the previous process. Not persisting it also KEEPS the withdrawn docstring's concession: a restart still tries once at full rate.
- [Phase 05]: A cycle the pacer skipped does not end a failure episode — Measured 2026-08-10: warned was recomputed from health, and a paced-out retailer has no result and so no health entry, so it read as recovered. The paging memory survived exactly one cycle and a refusal past the cap was re-paged at every subsequent check - 2 pages in 120 cycles. watch_cycle now carries warned forward for retailers it did not check.
- [Phase 05]: 05-04: Dan answered the store-pin checkpoint `defer` on 2026-08-10 — verbatim "Defer — no restart" — and the phase closed on offline evidence with every live row marked NOT OBTAINED, carrying its date and its reason. Not worked around, not softened, and no criterion reworded to absorb the gap. Deferring was one of three answers the card offered; the card also stated what it costs, which is that Walmart cannot alert until a store is pinned.
- [Phase 05]: 05-04: `make verify` was NOT re-run under the service's EnvironmentFile, breaking with Phase 3.1's closing method deliberately — that recipe (systemd-run --property=EnvironmentFile=...) is still right for a browser-path question, but it would pull the real store number into a process Claude launched and reads, which is the one thing the checkpoint exists to prevent. The consequence is a feature: the pinless run's output is safe to quote verbatim, because the config-gap detail names a key rather than a number.
- [Phase 05]: 05-04: the live `make verify` FAIL is recorded in THREE separated classes, with the one this phase caused named as ours — folding a self-caused failure in with two pre-existing ones is the omission this milestone exists to close, and the class we caused (Walmart UNKNOWN through the config-gap guard in a pinless shell) is criterion 2 working rather than a defect
- [Phase 05]: 05-04: the ROADMAP's `1, 0, 2, 3, 4, 5` criteria numbering was fixed as a TYPO, proved mechanically rather than asserted — the six bodies were extracted from HEAD and from the working tree with the numeral stripped, both extractions were confirmed to yield exactly six lines (so the diff could not pass over an empty extraction), and the diff was empty. The instruction was to revert the whole edit if the diff showed anything beyond the numeral
- [Phase 05]: 05-04: no code was written in the closing plan, deliberately — a criterion unmet at close is RECORDED unmet, because a closing plan that implemented its way to a green table would be a phase measuring work it did in the act of measuring
- [Phase 05]: 05-04: `deploy/boty-secret` has no store subcommand (only telegram and bestbuy) although the store number needs the same three protections its docstring names — shell history, scrollback, chat transcript — for an identity reason rather than a credential one. Flagged for a later plan, NOT grown here: a closing plan adding a shell subcommand would ship code with nothing gating it
- [Phase 05]: 05-04: the real store number was never obtained and commit 95f84a6 was explicitly not read — the pre-redaction Walmart capture in public history does carry a real store number, and reading it out would have been the exact leak QUESTIONS.md § 0e exists to close. bot-y never guesses where the user lives, and neither does the agent closing its phases
- [Phase 06]: 06-01: the price ceiling measures the DELIVERED TOTAL (item price + shipping), and where that total cannot be established it refuses to authorise an alert rather than guessing — the lenient fallback to the item price was rejected because "publishes nothing" and "publishes something we did not read" are indistinguishable on the retailer the defence exists for
- [Phase 06]: 06-01: the REQ-17 refusal lands on `alertable`, never on `Availability` — a pricing question must not erase a page's own stock statement, and it would strand Nintendo and Amazon at a permanent UNKNOWN with no path back. `alertable is False` resolves nothing and moves in the fail-safe direction
- [Phase 06]: 06-01: no shipping figure is parsed out of prose anywhere — Nintendo publishes `shippingDetails` as a sentence under the identical key GameStop publishes an object under, and a regex over it returns $6.99 for an item that ships free, i.e. a wrong VERDICT rather than a missing feature
- [Phase 06]: 06-01: Walmart shipping resolves to 0.0 only when two INDEPENDENT fields agree, selected by `type` and never by index; `fulfillmentOptions[*].speedDetails.fulfillmentPrice` is not read at all, because its only non-null instance in the corpus is a $7.95 from-store DELIVERY fee on a pickup item
- [Phase 06]: 06-01: a negative shipping cost is refused in `Result.delivered_total` and in exactly one place — the single point where an untrusted number becomes a decision, rather than N readers with N chances to get it wrong (T-06-01)
- [Phase 06]: 06-01: `alertable`'s redundant `price is None` guard was DELETED so M4 stays load-bearing — with both guards present, flipping the first would change no verdict, the mutation would SURVIVE, and the harness would report a hole that is not there
- [Phase 06]: 06-02: the Rung binding is STATIC AST over BOTH joins — retailer→adapter from cli._make_checker's if-chain and adapter→rung from the literal `rung=Rung.X` keywords — because a binding to check_amazon's rung alone stays green the day amazon stops being routed to check_amazon, which is the same false claim one join along. The cost is written into the module docstring rather than buried: it asserts what the source SAYS, not what RUNS, and tests/test_retailers.py already covers the other half
- [Phase 06]: 06-02: RUNG_NUMERALS lives in tests/test_support_matrix.py, not boty/models.py — a numeral is a documentation fact about the ladder README publishes, models.Rung deliberately keeps itself out of monitor and Health, and the package has no consumer for it. It is a PIN in UNREAD_POSITIONS' sense, with rung 4's deliberate absence of a member quoted from models.Rung's own docstring
- [Phase 06]: 06-02: the rule asserts set EQUALITY, not containment, so Best Buy's `3 (2 with a key)` needs no special case and an adapter taking a rung the cell does not name is caught too — a conditional cell falls out of a set comparison, and an exemption is a row that stops being checked
- [Phase 06]: 06-02: _routing RAISES rather than returning an empty mapping when it cannot find _make_checker, the check closure or the fallthrough return — a static rule handed {} reports seven clean rows and every gate above it keeps passing. Watched raising all three ways
- [Phase 06]: 06-02: "an adapter that states no rung" is reported as a DIFFERENT finding from "no adapter at all" — an empty set is exactly what a rung-4 row wants to see, so collapsing them would let an adapter this gate cannot read masquerade as a retailer nothing reads
- [Phase 06]: 06-02: M19's anchor is the shortest UNIQUE extension of the naive one and its uniqueness is bound by a test, not observed once — the bare `rung=Rung.TLS,` occurs twice with check_html (GameStop, Walmart, Nintendo) first, so 06-PATTERNS.md's proposed anchor would have mutated three retailers while its breaks= sentence said Amazon
- [Phase 06]: 06-02: REQ-18's `131` was RE-MEASURED (exit 0, 687 passed 1 skipped) and recorded beside the criterion rather than replacing it; REQ-18's inaccurate "Routing and Extraction are already pinned" parenthetical was NOT edited either — a criterion is not amended to make it meetable, and by the same rule not to make it accurate
- [Phase 06]: 06-01: the re-measurement CORRECTS 06-01's own plan on Walmart — the plan predicted the watch keeps its alertability, but the only first-party Walmart capture in this repo resolves no shipping at all, so the honest answer for 06-06's checkpoint is "not demonstrated", not "yes". Two watches confirmed lost, a third unproven
- [Phase 06]: 06-03: the four workflow rule families are keyed to the DIRECTORY, not to a filename — `CI = WORKFLOWS / "ci.yml"` written out a second time for RELEASE left a THIRD workflow guarded by nothing, measured on this tree at exit 0 with 701 tests green
- [Phase 06]: 06-03: three of four families are WRAPPED, not rewritten — the rules were already correct when called by hand; the defect was what they were handed, so no rule's judgement changed and the timeout bound was copied character-for-character out of the two tests it was extracted from
- [Phase 06]: 06-03: the pin family keeps the RAW view and the exit-code family the comment-stripped one, and the shipped tree detects either mistake for free — a pin rule reading `_code` reports all seven shipped pins, an exit-code rule reading raw reports the workflows' own decision records. The green side of that gate is the assertion, not a formality
- [Phase 06]: 06-03: the on-disk probe names `actions/checkout@v4` (trusted owner, mutable ref) and never a third-party owner — writing `some-vendor/...` into a public repo's real workflow directory to test a rule about `tj-actions` is not a trade this project makes; that half is watched in-suite only, derived with `.replace()`
- [Phase 06]: 06-03: NO mutation registered and M21-M22 left deliberately UNALLOCATED — `apply_mutation` string-replaces inside an existing file and cannot add one, so a criterion about a file that does not exist yet is outside the harness by construction. 06-04/06-05 keep their reservations; 06-06 must not read the gap as a lost mutation
- [Phase 06]: 06-03: the shipped-tree directory test reports EVERY family at once rather than asserting inside the loop — measured with the probe on disk, the in-loop form failed on `pin` and stopped, telling a contributor about one violation per run
- [Phase 06]: 06-05: pyproject.toml rolled 1.0.0 -> 0.2.0 as a CORRECTION, not a bump — safe only because nothing was ever tagged or uploaded, re-measured at execution (0 tags, 0 refs, PyPI 404, 404)
- [Phase 06]: 06-05: four statements of one version bound to pyproject.toml as the referent; the always-on rule is pyproject <-> README, correcting the outline's false 'runs everywhere' claim for CHANGELOG.md
- [Phase 06]: 06-05: Development Status 5 - Production/Stable -> 4 - Beta, argued in place with Phase 4's rejection kept verbatim, and made a two-directional rule so it cannot go stale at the next bump
- [Phase 06]: 06-07: where a shipping cost cannot be established the ceiling measures the ITEM PRICE and the alert goes out — Dan's reversal of 06-01, 2026-08-11, verbatim; the delivered-total ceiling is unchanged where shipping resolves
- [Phase 06]: 06-07: the mitigation for the reopened hole is a visible field, not a suppressed alert — 'price: <x>   shipping: unknown', same shape either way, and NO delivered total stated in any body
- [Phase 06]: 06-07: M17 was re-pointed rather than deleted when its subject reversed — deleting a mutation to make a suite green is forbidden here; it now guards the claim where it guarded the verdict
- [Phase 06]: 06-06: **THE M21-M24 IDENT GAP IS DELIBERATE AND IS NOT FOUR LOST MUTATIONS** — the registry runs M1-M20, M25-M28, read from the file with comment lines filtered rather than counted. 06-03 registers none because `apply_mutation` string-replaces inside an existing file and CANNOT ADD ONE, so a criterion about a workflow file that does not exist yet is outside the harness by construction; 06-04 registers none because the harness mutates `boty/` while its deliverable is a gate over a data file the sandbox does not copy, and widening `SANDBOX_CONTENTS` to manufacture one would create an entry provable load-bearing only by the mutation that motivated it. A mutation that SURVIVES is never explained away; a mutation that CANNOT EXIST is recorded as not existing. Anyone meeting `… M20, M25 …` should stop looking for four deleted gates
- [Phase 06]: 06-06: criterion 1 is recorded MET IN PART AS WRITTEN with its second half met only AS REVISED, rather than rounded up to MET — Phase 3.1 declined a rewrite that would have made its criterion 1 meetable, Phase 4 recorded two UNMET, Phase 5 marked every live row NOT OBTAINED, and a closing plan that rounded a half-met criterion up would be the defect this milestone exists to close, committed in the document that certifies its absence
- [Phase 06]: 06-06: Dan's REQ-17 reversal is recorded in Phase 3.1's format — original quoted intact, reversal beside it, never over it — because a USER reversing a decision and an AGENT rewording a criterion so finished work looks successful are different acts, and the only thing that keeps them apart in the record is the original surviving verbatim beside the new sentence
- [Phase 06]: 06-06: the live `make verify` FAIL was recorded verbatim with its three classes separated and NONE claimed as this phase's — 06-01's F1 predicted no control could move under criterion 1 (no control carries a `max_price`), and the live run CONFIRMED the prediction rather than being read as confirming it, with the four ceiling-carrying watches re-counted at close
- [Phase 06]: 06-06: no code was written to close the phase, on 05-04's precedent — a closing plan that implemented its way to a green table would be a phase measuring work it did in the act of measuring. The one edit outside the four record files is the removal of committed leaked markup from `06-07-SUMMARY.md`, which is the defect REQ-19 names sitting in this milestone's own documentation, and it was committed separately (`7355034`) so the closing record's own diff stays four files
- [Phase 06]: 06-06: the leaked-markup sweep was RE-RUN at close rather than its remembered figure repeated — 21 matching lines in 7 files, against the outline's 9-in-4. The outline's four files are UNCHANGED at 9; of the twelve new lines, ten are `tests/test_changelog.py` (4) and `06-04-SUMMARY.md` (6) carrying the shapes on purpose, and two are the real hit in `06-07-SUMMARY.md`. Repeating a number nobody re-measured is the defect this milestone exists to close
- [Phase 06]: 06-06: REQ-18's two stale claims (`131`, and "Routing and Extraction are already pinned") are FLAGGED in the requirement's own entry and in its traceability cell, and NEITHER IS EDITED — a requirement's text is the record of why the work was done and must survive it; a criterion is not amended to make it meetable, and by the same rule not to make it accurate

### Blockers

- Some Best Buy product pages (the Best Buy essentials house brand) are reproducibly refused while others render — mechanism unexplained, so 02-03 control selection needs a fallback candidate
- ~~Target: rung 3 is the only remaining route to its stock data, and it reaches that data only by making requests to redsky.target.com, which is Disallow:/ for every agent. Dan's 2026-08-03 reversal settled the Terms of Use, not robots.txt. Two options in QUESTIONS.md 0d; notify-dan sent.~~ **Cleared 2026-08-03.** Dan answered 0d explicitly and took option 2 — render the page, read the add-to-cart control, record it in the open. The ruling was then *measured* rather than left as a forecast: `performance.getEntriesByType('resource')` inside one rendered PDP found **31 hosts**, and **three** Target-owned hosts publish `Disallow: /`, not the one 0d named. The prohibition widened to match — no code here addresses `redsky.target.com`, `api.target.com` or `sapphire-api.target.com` directly.

- **No open blockers.** The only thing still waiting on Dan is `QUESTIONS.md` § 0e (public git history carrying this host's ZIP in four fixtures), which is a decision rather than a blocker — nothing is stopped by it.
- make verify FAILS live, first recorded 2026-08-06 and **re-measured once at Phase 5's close on 2026-08-10**: 'VERIFY: FAIL (live controls)', exit 2, in THREE classes now rather than two. Unchanged: Best Buy and Target cannot run at all (no Chrome/Chromium binary on this host, though nodriver 0.50.3 is installed, and STATE.md's 2026-08-10 entry records that Playwright's Chromium works when BOTY_BROWSER_PATH points at it). CHANGED: the Walmart/Amazon challenge-page class did NOT manifest on the 2026-08-10 pass — Amazon read IN_STOCK at $9.99 and Walmart served a judgeable page — so that class is intermittent rather than permanent. NEW, caused by Phase 5 and correct: 1/6 not reading IN_STOCK is Walmart through the config-gap guard, because make verify runs with no WALMART_STORE_ID. Everything still reads UNKNOWN rather than OUT_OF_STOCK, so the fail-safe is working, but real restocks are being missed. NOT a Phase 4 regression and NOT a Phase 5 regression — no plan in either phase touched a retailer, extractor or control. Still needs its own plan: polite probing plus fixture re-capture. Detail in .planning/phases/04-open-source-ready/deferred-items.md and docs/retailer-evidence.md § Phase 5 closing record
