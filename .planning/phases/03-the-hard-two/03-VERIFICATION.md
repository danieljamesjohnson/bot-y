---
phase: 03-the-hard-two
verified: 2026-08-03T06:02:50Z
status: human_needed
score: 7/7 must-haves verified
overrides_applied: 0
method: >
  Execution, against the AMENDED ROADMAP. Every criterion was proved by running a
  command — `make verify` under systemd-run with the service EnvironmentFile, the
  live `served/boty/status.json` the daemon itself published, and direct readings
  of the running unit. SUMMARY.md numbers were treated as claims and re-measured,
  not quoted. Five gates were driven RED by corrupting the thing they guard,
  observing a non-zero exit, then restoring; `git status --porcelain` is empty and
  `284 passed` after every one.
scope_note: >
  Criterion 5 ("five or more retailers") is UNMET at four. The amended ROADMAP
  gives that criterion an explicit "or it is recorded, never padded" branch, so
  the recorded branch is a PASS of the criterion as written. The count itself is
  still four, and REQUIREMENTS.md's v1.0 Definition of Done has no such branch —
  see W-01, which is the finding this verification most wants read.
gaps: []
deferred:
  - truth: "Nine Info findings from 03-REVIEW.md (IN-01…IN-09) remain open"
    addressed_in: "Phase 4 / opportunistic"
    evidence: >
      03-REVIEW-FIX.md frontmatter `deferred: 8`, `status: all_fixed` for the 6
      in-scope Critical+Warning findings. Independently confirmed IN-05 and IN-06
      are genuinely still open (four hand-maintained retailer lists still exist),
      so the deferral is honest rather than a silent claim of completion.
human_verification:
  - test: >
      Decide whether v1.0 ships at four retailers. ROADMAP Phase 3 criterion 5 was
      amended to permit "unmet and recorded"; REQUIREMENTS.md was NOT. Its
      Definition of Done still reads "Five or more retailers report stock with all
      control products green", and its Acceptance Criteria still read "`boty check`
      shows >=5 retailers". Phase 4 ships `pip install bot-y` and a v1.0.0 tag.
    expected: >
      Either REQUIREMENTS.md's Definition of Done and Acceptance Criteria are
      amended to four with the same reasoning the ROADMAP carries, or v1.0.0 is
      explicitly declared to ship against an unmet DoD. Both are fine; the two
      documents disagreeing at release is not.
    why_human: >
      A scope decision only Dan can make. No code change closes it, and no exit
      code can detect it — it is two planning documents that stopped agreeing when
      one of them was amended.
  - test: >
      Leave boty.service running 6-12 hours, then
      `ps --ppid $(systemctl show boty.service -p MainPID --value) -o pid,stat,comm=`
      and `sudo find /tmp/systemd-private-*boty.service*/tmp -maxdepth 1 -name 'uc_*' | wc -l`.
    expected: "Zero zombie (STAT Z) children, zero `uc_*` profile dirs, flat between two readings hours apart."
    why_human: >
      Carried from 02-VERIFICATION.md and NOT closed by this phase, contrary to
      QUESTIONS.md and STATE.md. I measured 0 zombies and 0 leaked profiles at
      46m40s uptime across 9 browser cycles — better than 03-03's claimed 41 min /
      7 cycles, and still inside the 71-minute window in which the original leak
      reached 13 zombies. Only elapsed time closes it. See W-03.
  - test: >
      With a real BESTBUY_API_KEY set, run `boty check` under the service
      environment and confirm the Best Buy row loses `[degraded]` and status.json
      records `"rung": "api", "degraded": false`.
    expected: "Same SKU, same IN_STOCK verdict, same price, no browser launched, no `[degraded]` tag."
    why_human: >
      Carried unchanged from 02-VERIFICATION.md. Requires a credential nobody on
      this project can obtain (manual approval, non-free email domain) — which is
      REQ-04's own documented reason the API is optional. The wiring IS pinned
      offline. If the key is permanently unobtainable, accept this as an override
      rather than carrying it into Phase 4 forever.
---

# Phase 3: The Hard Two — Verification Report

**Phase Goal:** Target and Amazon either working, or documented as unreachable with the evidence that established it. No silent gaps.
**Verified:** 2026-08-03T06:02:50Z
**Status:** human_needed — all 7 criteria verified; 3 items need Dan
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP Phase 3 success criteria) | Status | Evidence |
|---|---|---|---|
| 1 | Target reports stock, or the matrix records what was tried and why it failed | VERIFIED | `docs/retailer-evidence.md:773` `## Target (target.com)` carries one anchored `**Verdict: REFUSED**` (781), a per-request table with HTTP status and byte counts for all four requests (374,015 B / 471,173 B / 3,226 B / 41 B), the `LAST UPDATED: April 15, 2026` document header, and the quoted `Unlawful or Prohibited Uses` clause. README row 85 records rung 4 and the reason. Zero product-page requests |
| 2 | Amazon reports stock, or the same | VERIFIED | `docs/retailer-evidence.md:40` `## Amazon (amazon.com)`, one anchored `**Verdict: REFUSED**` (50), six policy-page requests recorded, `Last updated: May 30, 2025` header, quoted `LICENSE AND ACCESS` clause. README row 84. Zero product-page requests |
| 3 | Any rung-3 retailer flagged DEGRADED in the matrix and in `boty check` | VERIFIED | Both halves proved. Matrix: README row 82 reads `⚠️ Working, [degraded]`; stripping it to `✅ Working` turns `test_a_rung_three_retailer_is_flagged_degraded_in_the_matrix` RED (executed). Runtime: live `served/boty/status.json` shows the Best Buy control at `"rung": "browser", "degraded": true` and every other reading `"rung": "tls", "degraded": false`. `boty/cli.py:68` composes `[degraded]` from `r.degraded` in the same `_report` the `check` branch calls |
| 4 | All controls still green; no regression in the four from Phase 2 | VERIFIED | `make verify` under systemd-run: `control check: PASS — 4/4 controls in stock` — gamestop $549.99, walmart $2.42, bestbuy $59.99, nintendo $7.99, all `in_stock`. Live `status.json` `"healthy": true`, all four retailers `"ok": true`, no `failing_controls` |
| 5 | `boty check` reports 5+ retailers with no health warnings — **or it is unmet and recorded, never padded** | VERIFIED (recorded branch) | Count is **four**, and the recorded branch is taken in all four required places: `QUESTIONS.md § 0b`, `README.md:87`, `docs/retailer-evidence.md` Phase 3 closing record, `.planning/STATE.md` decisions. Nothing padded: `git log -- config/products.yaml` shows last change is `b5665e1 feat(02-04)` — Phase 2. See W-01 |
| 6 | A single `boty check` completes in under 2 minutes | VERIFIED | Independently read, not quoted: live `served/boty/status.json` `"duration_seconds": 35.70090914797038` at 10 watches / 4 retailers (one rung 3), written by the daemon's own cycle at 00:58:44. `boty/cli.py:318-330` times `run_once` with `monotonic` and prints the same value it publishes |
| 7 | `make verify` exits 0 | VERIFIED | Under `systemd-run` with the service `EnvironmentFile`: `VERIFY: PASS` unqualified — not OFFLINE, not INCOMPLETE — `MAKE VERIFY EXIT: 0` |

**Score:** 7/7 truths verified

### Baseline Re-measured (not read from SUMMARY.md)

| Gate | Claimed | Measured here | Match |
|---|---|---|---|
| `pytest tests/ -q` | 284 passed | `284 passed in 1.02s` | yes |
| `mypy` | clean, 15 files | `Success: no issues found in 15 source files` | yes |
| `mutation_check.py` | 6/6 | `6/6 mutations caught` | yes |
| `evidence_check.py --phase` | exit 0 | exit 0, `PASS — phase` | yes |
| `evidence_check.py --phase --strict` | exit 0 | exit 0 | yes |
| `make verify` (systemd-run) | exit 0, `VERIFY: PASS` | exit 0, `VERIFY: PASS` | yes |
| live controls | 4/4 | `PASS — 4/4 controls in stock` | yes |
| `duration_seconds` | 61.4 / 35.0 s | 35.70 s, live, current | yes |
| daemon zombies / profiles | 0 / 0 over 41 min, 7 cycles | 0 / 0 over 46m40s, 9 cycles | yes (see W-03) |

---

## The Thing Most Worth Checking: do the repaired gates bite?

The phase's own thesis is that a gate must be able to fail. Its review found that
thesis violated twice. **Both fixes verified by execution, in both directions.**
Every corruption applied to the real tree, `make verify` run, then reverted.
`make verify` aborts at its first failing stage, so all of these fail offline,
before any network request.

| # | Corruption | Result | Exit |
|---|---|---|---|
| 1 | **Ceiling** — a `microcenter` control watch appended to `config/products.yaml` | `VERIFY: FAIL (tests)`, 3 failed / 281 passed. `rule 1 (in scope)` fires by name, plus `test_no_retailer_is_configured_without_a_page_we_have_actually_read` and `test_every_configured_retailer_is_documented_in_the_matrix` | 2 |
| 2 | **Floor (CR-02)** — gamestop AND walmart watches deleted, two `**Verdict: REFUSED**` sections appended, README untouched. Config drops to `['bestbuy','nintendo']`, 3 watches. This is the exact tree that produced `253 passed` + `evidence check: PASS` before the fix | `VERIFY: FAIL (tests)`, **7 failed** / 277 passed. Both halves of the floor fire: `rule 4 (a refusal cannot outrank a capture)` names GameStop and Walmart with their real capture filenames, and `test_the_matrix_does_not_advertise_a_retailer_the_monitor_does_not_watch` fires on the stale README rows | 2 |
| 3 | **Flipped verdict (CR-01)** — only the ONE anchored Target verdict line changed to `REACHABLE (rung 1)`; confirmed the two prose mentions survive (`REFUSED occurrences left in Target section: 2`). This is the tree the shipped guard reported `[]` for | `VERIFY: FAIL (tests)`, **9 failed** / 275 passed, including `test_flipping_only_the_real_verdict_line_switches_the_guard_to_the_reachable_branch` and `test_the_prose_mentions_alone_do_not_hold_the_guard_on_the_refused_branch` — so the fix has not degenerated into "always take the other branch" | 2 |
| 4 | **My own probe** — pad the count with an IN-SCOPE retailer that carries a written REFUSED (`pokemoncenter` control watch) | Suite RED (1 failed / 283 passed) — but via `test_no_retailer_is_configured_without_a_page_we_have_actually_read`, a Phase-1-era guard. **`evidence_check.py --phase` returned `PASS — phase`, exit 0.** See W-02 | 1 (pytest) |
| 5 | **My own probe** — strip `[degraded]` from the Best Buy README row | `test_a_rung_three_retailer_is_flagged_degraded_in_the_matrix` RED. Criterion 3's matrix half is enforced against the real README, not a synthetic one | 1 (pytest) |

**Restored after every one:** `git status --porcelain` empty, `284 passed`,
`evidence check: PASS — phase`.

CR-01 and CR-02 are fixed, and the fixes hold under adversarial execution rather
than only under the tests that shipped with them.

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `scripts/evidence_check.py` | The honesty gate | VERIFIED | 594 lines, 4 rules, `ROADMAP_RETAILERS`, anchored `VERDICT_RE`, `strip_fences`, `split_sections` returning `list[tuple]`. Reads the config through `Config.load`, not a second YAML parse |
| `tests/test_evidence_check.py` | Proof the gate bites | VERIFIED | 45 tests. Wired into `make verify` via `test_the_shipped_tree_passes_the_whole_phase_gate` — proved by corruptions 1-3 reaching `VERIFY: FAIL (tests)` |
| `tests/test_support_matrix.py` | README matrix gate | VERIFIED | 14 tests, reads the real README via `_matrix()`. Both directions proved (corruptions 2 and 5) |
| `docs/retailer-evidence.md` | Ladder record + closing record | VERIFIED | 1,475 lines, 9 sections, 5 anchored verdict lines. Amazon and Target sections carry exactly one each |
| `README.md` retailer matrix | A rung for every roadmap retailer | VERIFIED | 7 rows, rungs 1/1/1/3/4/4/4, Best Buy flagged `[degraded]` |
| `boty/status.py` + `boty/cli.py` | `duration_seconds` published | VERIFIED | Live in `served/boty/status.json`; same `elapsed` printed as `check`'s last line |
| `config/products.yaml` | UNCHANGED — nothing padded | VERIFIED | `git log` last touch is `b5665e1 feat(02-04)`, Phase 2 |
| `boty/retailers.py` | Untouched by both retailer plans | VERIFIED | Absent from `git diff --name-only 81f218a~1..HEAD`. The phase's only `boty/` edits are `cli.py` and `status.py` |

---

## Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| `evidence_check --phase` | `make verify` | offline test in the `test` stage | WIRED — corruptions 1-3 all surfaced as `VERIFY: FAIL (tests)` |
| `docs/retailer-evidence.md` | `README.md` matrix | the Rung cell restates the verdict | WIRED — `test_a_rung_four_row_promoted_to_rung_one_fails_the_overstatement_rule` fires |
| `evidence_check.py` | `config/products.yaml` | `Config.load` | WIRED — the microcenter probe read through it |
| `Result.rung` | `status.json` / `boty check` | `degraded` derived from rung | WIRED — live `"rung":"browser","degraded":true`; `cli.py:68` |
| `cli.main` (check) | `status.json` | `duration_seconds=elapsed` | WIRED — `cli.py:318-330`, live value present |
| Target guard | `evidence_check` primitives | imported `split_sections`/`sections_for`/`verdict_lines`/`REFUSED` | WIRED — `test_retailers.py:1144-1148`; identity-pinned so a retype fails |

---

## Findings

### W-01 — WARNING: the milestone Definition of Done was never amended

Phase 3's criterion 5 was amended to permit "unmet and recorded". **REQUIREMENTS.md
was not.** It still says:

> v1.0 ships when **both** are true: 1. Five or more retailers report stock with
> all control products green

and, under Acceptance Criteria, `boty check` shows >=5 retailers.

Meanwhile REQUIREMENTS.md's traceability table already marks REQ-07 and REQ-08
Complete, and Phase 4 ships `pip install bot-y` and a v1.0.0 tag. So the release
phase is currently pointed at a Definition of Done its own repo says is unmet, in
a document nobody amended.

This is not a Phase 3 gap — the phase did exactly what the amended ROADMAP told it
to, and recorded the shortfall in four places rather than padding it. It is a
document disagreement that becomes load-bearing in the very next phase.
**Escalated as human verification item 1.**

### W-02 — WARNING: the honesty gate's floor has no mirror

CR-02's lesson was "a rule that points one way is half a rule". Rule 4 was added as
the floor: *a refusal cannot outrank a capture*. There is no mirror rule — *a
configuration cannot outrank a refusal*.

Proved by execution: adding a `pokemoncenter` control watch to
`config/products.yaml`, while `docs/retailer-evidence.md` continues to carry
`**Verdict: REFUSED**` for Pokémon Center, produces

```
evidence check: PASS — phase
evidence_check exit: 0
```

Rule 1 passes (in scope), rules 2 and 4 both `continue` on `retailer in configured`.
A tree that configures a retailer it has written down as refused is
self-contradicting, and the gate built to catch self-contradiction says PASS.

**Why this is a WARNING and not a BLOCKER:** `make verify` still goes red, via
`test_no_retailer_is_configured_without_a_page_we_have_actually_read` — the
fixture-provenance guard from Phase 1. The count cannot actually be padded this way
without also producing a `tests/fixtures/pokemoncenter/*.html`, which requires a
live fetch Imperva blocks. So the phase's *outcome* (criterion 5 cannot be quietly
padded) holds.

What does not hold is the *attribution*. `QUESTIONS.md § 0b` says "the gate that
would catch it if anyone tried (`scripts/evidence_check.py --phase`)". For the
out-of-scope direction that is true and I proved it. For the in-scope-but-refused
direction it is not — a different, older test does the catching. Note also that the
evidence log explicitly invites the scenario: Pokémon Center's section says the
homepage reads fine at rung 1 and the wall is worth retrying. The day a Pokémon
Center capture lands, rule 4 and the REFUSED verdict point in opposite directions
and only rule 4 has a rule.

Note the shape: the defect class CR-02 named — a one-directional rule — survives
the fix that named it, one rule over. That is the same transfer failure CR-01 was.

### W-03 — WARNING: "CR-01 durability closed" is stronger than the evidence

`QUESTIONS.md`, `STATE.md` and `03-03-SUMMARY.md` all state the Phase 2 durability
item is **closed**, on 41 minutes and 7 cycles.

Measured independently just now: MainPID 446442, uptime **46:40**, `ps --ppid`
returns no children, **0 zombies**, `find /tmp/systemd-private-*boty.service*/tmp
-name 'uc_*'` returns **0**, journal shows **9** browser cycles from 00:19:39 to
00:58:15. The readings are real and they are better than claimed.

They still do not close it. `02-VERIFICATION.md` asked for **6-12 hours**, and gave
its reason: the original leak reached 13 zombies and 204 MB inside a **71-minute**
window. 46 minutes is inside that window. 03-03's plan set its own bar at ">=40
minutes and 6 cycles" and then met it — which is a plan meeting a bar it chose,
not the open item being answered.

The right word is "strong evidence, not yet closed". Carried as human verification
item 2 rather than accepted.

### INFO — the reported `make verify` exit-code disagreement is a false alarm

Confirmed the observation: `make verify` exits **2** on failure, not 1, because
make wraps the recipe's `exit 1`. Measured on all three corruptions.

Checked the claimed disagreement and it does not exist.
`tests/test_verify_makefile.py` **never pins 1**: `assert proc.returncode != 0` in
both failure cases (lines 110, 123), `== 0` in the four pass cases. `README.md:252`
says `VERIFY: FAIL (<stage>)` -> **non-zero**. REQ-12 and every phase criterion say
"exits non-zero". The docstring phrase "the four exit codes" at
`tests/test_evidence_check.py:1124` refers to `control_check.py`'s codes (0 pass,
1/2 fail, 3 skipped, 4 incomplete), which is exactly what the tests parameterise on
via `CONTROL_RC` — not to make's own exit status. Nothing to fix.

---

## Anti-Patterns Found

| File | Pattern | Severity | Result |
|---|---|---|---|
| all 12 non-planning files touched by the phase | `TBD` / `FIXME` / `XXX` / `HACK` / `TODO` / `PLACEHOLDER` | — | **None found.** Debt-marker gate passes |

---

## Requirements Coverage

| Requirement | Description | Status | Evidence |
|---|---|---|---|
| REQ-07 | Target and Amazon each working or documented unreachable with evidence; any browser-reached retailer flagged DEGRADED in matrix and `boty check` | SATISFIED | Criteria 1, 2, 3 above. Both rung 4 by written prohibition, zero product-page requests; Best Buy `[degraded]` in both surfaces, each half proved red by corruption |
| REQ-08 | A full `boty check` completes in under two minutes at ~7 retailers, sequentially | SATISFIED, with the shortfall stated in the requirement itself | 35.70 s live at 10 watches / 4 retailers. Measured at four, not seven, and REQ-08's own body says so and says why — three of the seven are rung 4, so a seven-retailer pass cannot be run and extrapolating one would invent the number the requirement exists to pin. That is the honest form |

No orphaned requirements: `.planning/REQUIREMENTS.md` maps only REQ-07 and REQ-08
to Phase 3, and both plans declare them.

---

## Is the gate suite converging, or is this a pattern?

Asked because this is the second consecutive phase where a gate the phase built had
to be repaired by its own code review. Both readings have real support.

**Converging — on detection.** The failure *mode* changed, and that is the part
that matters. Phase 2's rot (`five or more retailers OR "rung 4" in QUESTIONS.md
AND "REFUSED" in the evidence doc`) was unfailable the day it was written and
nobody noticed for a whole phase — Pokémon Center's finding put both substrings
permanently in the tree. Phase 3's two defects were found by the phase's own review
*before the phase closed*, both were reproduced before anything was changed, and
both reproductions now run as tests against the real tree. Detection latency went
from a phase to hours. The CR-01 fix also went at the root cause rather than the
symptom — three drifted readers of the evidence log collapsed into one imported
splitter and one grammar, with an identity check pinning that `_REFUSED` **is** the
gate's constant rather than a retyped copy. And the fixes hold under corruptions
they were not written against: I flipped, deleted and padded, and got 9, 7 and 3
red tests. That is not a suite that merely passes.

**A pattern — in construction.** Three things point the other way, and the third is
new.

1. CR-01 was the *identical* defect (bare substring vs anchored) reintroduced one
   file over, in the same commit series whose whole purpose was to remove it.
   Knowing a failure mode did not stop it recurring 200 lines away.
2. CR-02's class — a rule that points one way — **survives the fix that named it**.
   W-02 above is that same shape, in the same file, in the rule added as the
   remedy. I found it by asking "what is the mirror of rule 4?" and running it. The
   review did not ask.
3. The deferred Info list is load-bearing here, not cosmetic. IN-05 and IN-06 are
   four hand-maintained lists of one fact: `ROADMAP_RETAILERS` in
   `evidence_check.py` (which *claims* to mirror `.planning/ROADMAP.md` and whose
   labels the review says already differ), a literal tuple at
   `tests/test_evidence_check.py:583`, the README table, and the ROADMAP table
   itself. WR-04 closed reader drift for the evidence *document* and left reader
   drift for the retailer *list* wide open. That is the same class again, deferred.

**Judgement:** converging on detection, not yet on construction. The gates bite —
I proved five of them do, two by routes nobody had tried. But every hole so far has
been found by a deep review or by an adversarial verifier, not by the gate suite
catching itself, and the fix for a named defect class keeps failing to generalise
one file or one rule over. That is a specific risk for Phase 4 rather than a
general worry: Phase 4 is the public release, and an outside contributor's PR gets
the gate, not the review. The cheapest thing that would change the trend is not
another rule — it is deleting one of the four retailer lists (IN-05/IN-06) so the
drift has nowhere to happen.

---

## Gaps Summary

**No gaps.** All seven ROADMAP success criteria are verified against the codebase
by execution, and the one criterion that is substantively unmet (5, at four
retailers) is unmet through the branch the amended ROADMAP explicitly provides,
recorded in four places, with `config/products.yaml` git-proven untouched since
Phase 2 and the padding routes proved red.

The phase goal — *Target and Amazon either working, or documented as unreachable
with the evidence that established it; no silent gaps* — **is achieved**. Both are
rung 4 by their own written terms, each with the clause quoted, the retrieval date,
the document header, and every request logged with an HTTP status and a byte count.
Neither was sent a single product-page request. There is no silent gap: every
retailer in the roadmap's scope is now either configured or carries an anchored
`**Verdict: REFUSED**`, and `make verify` fails if that stops being true.

Status is `human_needed`, not `passed`, for three items — one of which (W-01) is
the reason this report exists in the shape it does. Phase 4 is the public release,
and it is currently aimed at a Definition of Done that says five retailers while
the repo says four. That needs a decision, not a workaround.

---

_Verified: 2026-08-03T06:02:50Z_
_Verifier: Claude (gsd-verifier)_
