# Roadmap: bot-y

## Overview

Two retailers work today, both control-verified. The journey to v1 is getting
to ~10 curated retailers without losing the property that makes the project
worth existing: every detector is provably correct, and when one isn't, you
find out. That ordering matters — we build the safety net *before* the
five-fold increase in adapters, because the failure mode we're guarding
against is invisible by construction. Then we make it a project other people
can contribute to.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Phases 1–4 and 3.1 belong to **v1.0.0** — their checklist and details are together
under *Milestone v1.0.0 — Phase Details* below. v1.0.0 remains open and untagged.

- ✅ **Milestone v0.2 — Say Only What You Measured** (scoped 2026-08-10, closed 2026-08-11) — Phases 5–6, 11 plans, complete **in the tree**; **not deployed, not tagged, not published**. Archived in full: [`milestones/v0.2-ROADMAP.md`](milestones/v0.2-ROADMAP.md) · [`milestones/v0.2-REQUIREMENTS.md`](milestones/v0.2-REQUIREMENTS.md) · [`milestones/v0.2-MILESTONE-AUDIT.md`](milestones/v0.2-MILESTONE-AUDIT.md)

- ✅ **Milestone v0.3 — Say When You Measured It** (scoped 2026-08-13, closed 2026-08-19) — Phase 7, 7 plans, one requirement (REQ-21), complete **in the tree**, **DEPLOYED 2026-08-20**, **TAGGED `v0.3.0` 2026-08-25**; **still not published** (PyPI 404, deliberately). *This line read "not deployed, not tagged, not published — the running daemon predates the milestone's first commit by ~15 hours" from the close until 2026-08-25; it was true when written, and both halves were superseded by events rather than corrected as errors — see `MILESTONES.md` § v0.3.* Archived in full: [`milestones/v0.3-ROADMAP.md`](milestones/v0.3-ROADMAP.md) · [`milestones/v0.3-REQUIREMENTS.md`](milestones/v0.3-REQUIREMENTS.md) · [`milestones/v0.3-MILESTONE-AUDIT.md`](milestones/v0.3-MILESTONE-AUDIT.md)

- 🚧 **Milestone v0.4 — Don't Get Locked Out** (scoped 2026-08-27) — Phases 8–11, REQ-22…REQ-25. **In progress.** Details under *Milestone v0.4 — Phase Details* below.

## Retailer Scope

Deliberately narrowed from a padded list of ten. Newegg, B&H and Micro Center
are PC-parts retailers that do not carry Pokémon accessories; Costco and Sam's
Club are unlikely to stock a $55 peripheral. Watching stores that will never
list the product manufactures fake breadth and real maintenance.

Target list — places a GO Plus + could genuinely appear:

| Retailer | Status |
|---|---|
| GameStop | ✅ done, control-verified |
| Walmart | ✅ done, control-verified |
| Best Buy | Phase 2 — rung 3 (browser, DEGRADED); official API optional if you have a key |
| Pokémon Center | Phase 2 |
| Nintendo store | Phase 2 |
| Target | Phase 3 — RedSky CAPTCHA-gated |
| Amazon | Phase 3 — expected hostile |

## Escalation Ladder

When a retailer resists, work down this ladder and stop at the first rung that
works. Record which rung each retailer landed on in the support matrix.

1. **TLS impersonation** (`curl_cffi`) — the default
2. **Official / structured API** — but ONLY if a fresh clone can obtain the
   credential. Best Buy's API requires manual approval and a non-free email
   domain, so it fails this test and cannot be a primary path; it stays
   available as an optional enhancement for those who have a key

3. **Browser (`nodriver`), marked DEGRADED** — allowed, but that retailer is
   flagged lower-confidence, because it depends on the fragile path we
   deliberately moved away from

4. **Drop, with evidence** — documented as unreachable in the support matrix,
   including what was tried. Never left silently broken.

## Milestone v0.4 — Phase Details

**Scoped 2026-08-27. Open.** Requirements in [`REQUIREMENTS.md`](REQUIREMENTS.md) — REQ-22…REQ-25.

**The measurement that opened it, 2026-08-27.** Three of six retailers return a challenge page;
**one of four** GO Plus + watches still reads (Nintendo). A spike drove this project's own rung-3
transport — a real headless browser — at Walmart's control and got
`rendered challenge page matched 'robot or human'` in **3.8 s**. Rung 1 refused, rung 3 refused,
and Target independently refused at rung 3 with `px-captcha`. **Escalating a rung is not a fix
that is available here**, which is why no phase below proposes one.

**What is actually being fixed:** every watch shares one egress, one client fingerprint family and
one request pattern, so one reputational event blinds all six at once. Phases 8 and 9 shrink the
footprint that earns a block and remove the lockstep signature that advertises one. Phase 10 stops
a configuration failure from being read as a retailer failure. Phase 11 establishes what is
actually true of each blocked retailer, up to and including *dropped*.

**Not scoped, deliberately:** a lost-coverage alarm (declined by Dan on 2026-08-27 — *"we don't
want to inform the user it's broken, really. we want to prevent a broken state"*), an egress
change, and rung-2 API credentials. All three are argued in `REQUIREMENTS.md` § *What is
deliberately NOT in this milestone*.

- [x] **Phase 8: Stop Knocking** *(COMPLETE 2026-08-31 in the tree; ~~NOT on the wire~~ **ON THE WIRE since 2026-09-11 07:56:33** — noted 2026-09-14, see the phase's closing record)* — a persistently refused retailer is left alone for days, not knocked on twice a day forever
- [x] **Phase 9: Out of Lockstep** *(COMPLETE 2026-09-01 in the tree; ~~NOT on the wire~~ **ON THE WIRE since 2026-09-11 07:56:33** — noted 2026-09-14, see the phase's closing record)* — six retailers stop being requested inside one short window from one origin
- [x] **Phase 10: A Control That Cannot Die** *(COMPLETE 2026-09-02 in the tree; ~~NOT on the wire~~ **ON THE WIRE since 2026-09-11 07:56:33** — noted 2026-09-14, see the phase's closing record)* — a dead control is a fact about our config, never mistaken for a fact about the retailer
- [x] **Phase 11: The Honest Ladder Position** *(COMPLETE 2026-09-14 — in the tree; it made ZERO live requests. ~~changed no production code~~ — see the correction in its closing record: the commit that carried it also carried the phase-10 re-verification's code fixes)* — what is actually true of Amazon, Target and Walmart, written down and gated

### Phase 8: Stop Knocking

**Goal**: A retailer that has refused 30-odd times in a row stops being asked twice a day, so the
footprint that earns and sustains a block shrinks.
**Depends on**: Nothing.
**Requirements**: REQ-22
**Success Criteria** (what must be TRUE):

  1. After a bounded number of consecutive refusals, the wait returned for that retailer is measured in **days**, asserted against literal expected seconds — not against "greater than the old ceiling"
  2. A retailer in cool-off is requested **exactly once** when the cool-off expires, not once per cycle. The single-probe behaviour is asserted over a simulated sequence of cycles, not inferred from the interval
  3. The total number of requests made to a retailer that **never** recovers, over a simulated 30 days, is a **stated number** and is strictly smaller than the same simulation under the current rule. Both numbers are recorded
  4. A retailer that answers during its probe returns to its normal cadence **immediately**, and the cool-off state is cleared — the failure mode where a recovered retailer stays throttled is asserted against
  5. The cool-off **survives a restart**, the same guarantee the existing backoff already carries, and is discarded when stale by the existing rule rather than a second one
  6. `make verify-offline` exits 0, with at least one new mutation registered, observed CAUGHT, and anchored on **behaviour** rather than on message text

**Plans**: 4 plans. `phases/08-stop-knocking/08-PLAN-OUTLINE.md` is the authority on the breakdown.
Every plan touches `boty/pacing.py` or `tests/test_pacing.py`, so **every plan is its own wave** —
the serialization is the schedule, not a scheduling failure.

Plans:

**Wave 1**

- [x] 08-01: The number before — 30 days of cycles against the **unmodified** rule, recorded as a stated literal, plus `08-DECISIONS.md` and `COVERAGE.md`. Changes no production code, deliberately. *(EXECUTED 2026-08-28)*

**Wave 2** *(blocked on wave 1 — criterion 3's "before" number is unobtainable once the rule moves)*

- [x] 08-02: The cool-off itself — criteria 1, 2, 3-after and 4. Leads with the end-to-end tracer. Fixes `REFUSALS_BEFORE_COOLOFF = 30` and `COOLOFF_SECONDS = 3 * 24 * 60 * 60`. *(EXECUTED 2026-08-28)*

**Wave 3** *(blocked on wave 2)*

- [x] 08-03: Criterion 5 — it survives a restart, and the rule that discards it is the one already there. Re-derives `STATE_MAX_AGE_SECONDS` to 259200. *(EXECUTED 2026-08-28)*

**Wave 4** *(blocked on wave 3)*

- [x] 08-04: Criterion 6 — M42 registered and observed CAUGHT; the consumer surfaces checked rather than assumed; the six-criterion verdict table. *(EXECUTED 2026-08-28)*

**Cross-cutting constraints** — each holds across two or more plans, and each is asserted rather than
assumed:

- `MAX_BACKOFF_SECONDS` **stays 6 hours**. What REQ-22 replaces is the ceiling being applied
  *indefinitely*, not its value — and `tests/test_pacing.py`'s surviving `<= 6 * 60 * 60` assertion is
  what keeps that distinction visible.
- **No second staleness rule.** `grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py` is 2 today and
  must stay 2; a cool-off moves that guard's right-hand side, it does not add a guard.
- **M42 is the only new ident. M21–M24 stay empty** — `grep -c "INTENTIONAL GAP"` goes 7 → 8.
- **No live retailer request, no `boty check`, no write to `state.json` / `pacer-state.json` /
  `served/boty/status.json`, and no `systemctl restart boty`** anywhere in this phase.
- **A recorded one-wave gap:** between waves 2 and 3 the tree holds a three-day cool-off that a
  restart discards after six hours. `08-02` states it before it exists; `08-03` closes it. Nothing is
  deployed mid-phase, so it is a recorded gap rather than a shipped defect.

**CLOSING RECORD — Phase 8 COMPLETE 2026-08-31, and not one criterion was reworded.**

**6 of 6 criteria met; 4 AS WRITTEN, 2 MET IN PART.** Full verdict table with every citation:
`08-04-SUMMARY.md`. Verification: `08-VERIFICATION.md` (`human_needed`, 2 items, both deployment
observations — `08-UAT.md`).

| # | Verdict | The half that is not met, where there is one |
|---|---|---|
| 1 | **MET AS WRITTEN** | — |
| 2 | **MET IN PART** | *"exactly once"* is scoped to a **running process**; `due_at` is unpersisted, so a restart costs **one** extra probe. Measured at exactly 1 over 864 simulated cycles, and priced in `08-DECISIONS.md` collision 2 before it was accepted |
| 3 | **MET AS WRITTEN**, in simulation | Both numbers stated: **125 before, 37 after**, over 30 simulated days. Floors on real requests, not predictions of them |
| 4 | **MET AS WRITTEN** | — |
| 5 | **MET IN PART — amended DOWN on 2026-08-31, beside the original** | *"discarded by the existing rule rather than a second one"* was never in doubt (`grep -c` still **2**). *"Survives a restart"* was true only **outside a 6.84% window** when this phase asserted it, because `cli.watch_loop`'s clock lagged wall clock by each check pass's cost. Fixed at the cause (`9ea42fe`); residual re-measured **0.06% mean / 0.13% worst** |
| 6 | **MET AS WRITTEN** | **M42** registered and observed CAUGHT, registry **38/38**, survivors 0 — with the measured finding recorded beside it that M42's kill set is a **proper subset of M33's**, so it buys localisation and not detection |

**Criterion 5 is the one to read.** The phase's own closing record called it MET, and a code review
five days later established by measurement that the guarantee had a systematic hole in production at
the moment that word was written — 6.84% of every cool-off window, on `target`, which sat at **46
refusals**. The verdict was amended down rather than the finding folded away. *The assertion was not
wrong about the test; it was wrong about production* — 08-03's restart test was valid and still
passes, and what nothing covered was the clock its `now` argument stands in for.

**The five cross-cutting constraints were checked by command, not by summary.** `MAX_BACKOFF_SECONDS`
still 6 h; the staleness grep still exactly **2**; M42 the only new ident with M21–M24 empty and
`INTENTIONAL GAP` at **8**; no live request (`control check: SKIPPED (--offline)`) and no write to any
of the three live documents. One honest qualification the verifier raised: the plans' stricter
*"neither read nor written"* no longer holds phase-wide — the CR-01 investigation **read**
`served/boty/status.json` to obtain `duration_seconds: 20.43`. The ROADMAP constraint above is about
**writes** and is intact.

**Gate at close:** `make verify-offline` **EXIT 0** — identity PASS over **242 files**, **920 passed /
0 skipped** (up from 916 at phase start, +4 gates from the review), mypy clean over 18 source files,
**38/38 mutations caught, survivors 0**. The verdict line is the **OFFLINE** pass: nothing in it says
the retailers still work.

**A code review ran after the four plans closed and found 1 Critical + 4 Warnings; all five are
fixed** (`08-REVIEW.md` and its Resolution section). The review's own CR-01 prescription was
**measured wrong and not applied** — it would have broken five existing tests — and the correct fix
is recorded beside it.

**NOT ON THE WIRE.** `boty` is an editable install, so Phase 8 reaches the daemon at the next
`sudo systemctl restart boty` — **Dan's action, deferred by his decision on 2026-08-31**, neither
performed nor recommended here. That restart now carries more than this phase: `9ea42fe` also returns
the loop to its configured cadence rather than ~6.8% slower, so the request rate goes **up** slightly.
That trade was named and taken, not stumbled into.

> **AND OPERATING IT FOUND A HOLE IN ITS OWN GUARANTEE — 2026-09-18, recorded beside.** A restart
> re-probes **every** backed-off retailer within seconds, discarding whatever wait remained, because
> `Pacer.load` deliberately does not restore `due_at`. Reproduced on both restarts: amazon at +3 s and
> +4 s, target and walmart within four minutes. **Target was 1 day 18 h into a three-day cool-off**, and
> the refusal restarted that clock. Phase 8's goal says a refused retailer is *"not knocked on twice a
> day forever"*; it is knocked on once per restart. The counter-persistence fix (CR-01) holds — 30 → 31,
> never reset — this is the **scheduling** half of the same area and it was not covered. `refused_at` is
> persisted and is wall-clock, so the remaining wait was derivable the whole time. Full working in
> `docs/retailer-evidence.md`; deferred to v0.5 rather than hotfixed on a deployed daemon.
>
> **ON THE WIRE SINCE 2026-09-11 07:56:33** — dated note added beside 2026-09-14, not over. Dan
> instructed the restart and phases 8, 9 and 10 went on together. **The cool-off has still never
> fired in production**, so phase 8's central mechanism is deployed and unobserved: it needs 30
> consecutive refusals and the live counts are amazon 10 / target 18. Recorded as unobserved rather
> than claimed. Full record at phase 10's closing note below.

### Phase 9: Out of Lockstep

**Goal**: The six retailers stop presenting as one coordinated crawler — independent schedules, so
a single cycle does not fire six unrelated retailers inside one short window.
**Depends on**: Phase 8 (both edit the scheduler; they serialize on `boty/pacing.py`)
**Requirements**: REQ-23
**Success Criteria** (what must be TRUE):

  1. Two retailers whose intervals coincide are **not** dispatched inside the same short window; the bound is a stated number of seconds and is asserted on the schedule, never on a wall clock
  2. Each retailer's next-attempt time is **independent**: changing one retailer's interval or backoff moves that retailer's schedule and no other's, asserted in both directions
  3. Over a simulated day, the maximum number of retailers requested within any 60-second window is a **stated number**, and it is smaller than the current six
  4. **No regression in what already works**: per-retailer cadence and backoff still hold, and `boty check` — a deliberate full pass, which is a different thing from the daemon's schedule — still completes inside REQ-08's 2-minute budget, re-measured rather than assumed
  5. `make verify-offline` exits 0, with at least one new mutation registered and observed CAUGHT

**CLOSING RECORD — Phase 9 COMPLETE 2026-09-01. ~~Four MET AS WRITTEN, one MET IN PART~~ → THREE MET AS WRITTEN, TWO MET IN PART; nothing reworded.** *(Count amended 2026-09-14, beside: criterion 1 moved to MET IN PART on 2026-09-11 and this headline was not carried with it. A verdict amended in a paragraph while the count above it still reports the old tally is a correction a reader can miss entirely — which is the failure this project's beside-not-over rule is meant to prevent, arriving through the rule rather than around it.)*

Five plans, five waves, serialized on `boty/pacing.py` / `boty/cli.py` / `tests/test_pacing.py`.
Full verdict table with citations: `09-05-SUMMARY.md`. Decisions: `09-DECISIONS.md`.

| # | Verdict | Measurement |
|---|---|---|
| 1 | ~~**MET AS WRITTEN**~~ → **MET IN PART** *(amended 2026-09-11, and the pointer added to this row 2026-09-14 — see the amendment below the table)* | **50.0 s** separation, written out at `_MIN_SEPARATION_SECONDS` and asserted on the *schedule* — never a wall clock. Hand-written rather than recomputed from the code under test, because a test that recomputes its expectation asserts only that the code agrees with itself. **AND IT HOLDS ON `due_at` ONLY.** Re-measured at `570df66` through `cli.watch_loop` over a full simulated day: two 300 s-cadence retailers are asked at the **same wake, minimum gap 0.0 s**, **17 times a day** at `_IDLE_SEED`, **11–30** across `_IDLE_SEED+0..20` and **13–29** across a disjoint set of 20. The criterion says *not dispatched inside the same short window*. The 2026-09-11 amendment named the mechanism and gave no magnitude; these are the magnitudes |
| 2 | **MET AS WRITTEN** | Independence in **both** directions, as two tests rather than one — the interval direction fails at `_standing_interval`/`slot_offset`, the backoff direction at `current_interval`, and a combined test would name the wrong one |
| 3 | **MET AS WRITTEN** *(see the 2026-09-11 correction below)* | **6 → 2** retailers in any 60 s window over a simulated day. 09-01 took the *before* against unmodified code in its own wave, because the number is unobtainable afterwards. **2 is also the arithmetic floor** — 6 × 60 s > 300 s forces some window to hold two — so a claim of 1 was never available |
| 4a | **MET AS WRITTEN** | Per-retailer daily counts and the backoff/cool-off ladder unchanged under the new tick |
| 4b | **MET IN PART** | `boty check`'s 2-minute REQ-08 budget is **BOUNDED, not re-measured** — `boty check` makes live retailer requests and writes the daemon's live `status.json`, and this phase makes none. **The verdict was committed in `09-DECISIONS.md` § Collision 8 BEFORE the attempt**, not promoted after one disappointed |
| 5 | **MET AS WRITTEN** | **M43** registered and observed **CAUGHT** (~~5~~ → **6**-test kill set, re-measured at `570df66` 2026-09-14); registry 38 → **39**, `M21`–`M24` still empty, `INTENTIONAL GAP` 8 → 9. **The sixth killer is the day test `e88a350` rewrote**: under M43 the OLD version passed and the new one fails, so repairing a seed-pinned gate also grew this mutation's kill set — and nobody noticed, so three records went on saying five. Whether the sixth overlaps any other ident's kill set is **NOT measured** |

**The mechanism.** A deterministic per-retailer offset derived from the retailer name and the
configured roster — never `hash()` (randomised per process), never a wall clock, never a pid, never
anything host-derived, because a phase derived from host identity would encode a host fingerprint
into request *timing*, which `scripts/identity_check.py` scans files for and can never see. Loop tick
**50 s** = `default_interval / len(roster)` floored at `MIN_TICK_SECONDS = 30`, chosen from a
ten-row measured sweep as the largest tick whose slots are all distinct. `record` advances on the
retailer's own grid rather than re-anchoring to `now` — without that, a merged pair stays merged and
the fleet collapses back to six-in-a-window inside a day.

**Every standing invariant survived, checked by command at the close:** `Pacer.current_interval`'s
body is **byte-unchanged** (SHA-256 gate); `cli.watch_loop` keeps **both** clock terms
(`delay + cycle_duration`); `MAX_BACKOFF_SECONDS` 6 h; `COOLOFF_SECONDS` 259200; the staleness-rule
count is still exactly **2**; `STATE_VERSION` is still **2** with no new persisted field — `roster`
and `tick` live on `Pacer`, defaulted and never written to disk.

**The finding this phase produced that nobody asked for.** Shortening the tick made **26.4% of wakes** (457 a day of 1728) ask
*nobody* — and `status.py` published `healthy` as `all(...)` over an empty list, which
is `True`. This phase would have made **a green verdict over a question nobody asked** routine: this
project's core defect, rebuilt inside the fix for a different one. A wake that asked nobody now
publishes `healthy: null`. **No new key** — the published key set is unchanged; what the existing key
can *say* changed. The same wave caught that the shorter tick would silently have turned "15 minutes
to a push, 50 to a give-up" into 2.5 and 8.3, so both thresholds were re-derived as **durations**.

**Gate at close:** `make verify-offline` **EXIT 0** — identity PASS over **259 files**, **946 passed
/ 0 skipped** (from 921 at phase start), mypy clean over 18 source files, **39/39 mutations caught,
survivors 0**. Verdict line is the **OFFLINE** pass: nothing in it says the retailers still work.

**The plan-checker found 3 blockers and one was not real.** B1 (09-02 reddening eight tests while
naming two, six of them in a file no later plan could open) and B4 (a verify gate whose polarity was
inverted — it *failed* when the prohibition held) were both real and both fixed. **B3 was a misread**:
`--all` was already present in the original planning commit. Recorded because an inflated blocker
count is the same class of error as a rounded-up verdict.

**NOT ON THE WIRE.** Phase 9 reaches the daemon only at `sudo systemctl restart boty` — Dan's action,
still deferred with Phase 8's.

> **ON THE WIRE SINCE 2026-09-11 07:56:33** — dated note added beside 2026-09-14, not over. And
> phase 9 is the one phase whose deployment was **proved rather than inferred**: `status.json` was
> rewritten twice inside 70 s after the restart, which only happens at this phase's ~50 s tick. The
> pre-phase-9 loop wrote every ~300 s. Per DoD item 2 that proves the loop is running this code and
> **nothing about the schedule being correct** — the schedule is proved offline only.

**VERIFIED INDEPENDENTLY 2026-09-11, LATE, AND IT FOUND THREE ERRORS IN THIS RECORD — ALL MINE.**
`09-VERIFICATION.md`, status **gaps_found**, score **5/7**. This phase closed WITHOUT a verifier: the
table above was the orchestrator's own assessment written from the wave summaries, and that is exactly
why it needed checking. The goal as worded IS met — six-in-a-window is gone. Three claims beside it
were not true as stated:

1. **CRITERION 1 IS AMENDED TO MET IN PART.** The 50.0 s bound holds on `due_at` — the next-attempt
   *position* — and only there. **At DISPATCH** it does not: under the loop's own ±15% jitter and
   `due()`'s half-tick (25 s) grace, two retailers on the same 300 s cadence can still be asked at one
   wake. The criterion says *"are not dispatched inside the same short window"*, so as worded it is
   not met, and no test asserts a dispatch-level separation for a coinciding pair. Recorded here
   rather than by rewording the criterion.
2. **"2 is the arithmetic floor (6 × 60 > 300), so a claim of 1 was never available" IS FALSE.** Only
   **four** of the six retailers are on the 300 s cadence, not six, so the arithmetic does not hold
   and a schedule with max 1 and unchanged counts exists. I asserted an impossibility that is not
   impossible. The measured **2** stands as a measurement; the *floor* argument beside it is withdrawn.
3. **"6 → 2" drops a figure its own plans recorded.** 2 is the max per WAKE; over any rolling 60 s
   window the measured figure is **3**, recorded by 09-02 and 09-05 and omitted here. The honest
   summary is 6 → 2 per wake, 3 per 60 s.

**One more weakness worth carrying, on criterion 4a.** The day-long count test matches 48/96/288 at
**1 of 21 seeds — its own.** It has no denominator, and its "day" spans 86,107–86,702 s across 1728
jittered wakes, so the equality depends on the seed. That is the same brittleness the 2026-09-08 CI
failure exposed, one layer up, and it is recorded rather than repaired.

> **REPAIRED 2026-09-14, and the repair changed the CUT rather than the assertion.** The paragraph
> above stands; this is the outcome beside it.
>
> **The cause, measured before anything was changed:** the test's "day" was **1728 wakes**, and a
> wake count is not a clock. At ±15% jitter 1728 wakes span **86,099.7–86,565.4 s** over seeds
> `_IDLE_SEED + 0..20`, so a 300 s-cadence retailer lands on 287, 288 or 289 purely by where the
> last wake falls.
>
> **One figure of the verifier's is not reproduced and neither is corrected away.** It reported
> **1 of 21**; this re-measurement reads **3 of 21** over `_IDLE_SEED + 0..20`. `09-VERIFICATION.md`
> does not record which seeds it swept, so the two are not comparable — both are kept, and they say
> the same thing about the gate.
>
> **What shipped:** the window is now **86,400 simulated seconds**, the test runs at **four seeds**
> instead of one, and the span it actually reached is **asserted** so an under-run is loud rather
> than presenting as low counts. **The claim got stronger, not looser** — five of the six counts are
> now exact at **21 of 21** seeds (bestbuy/nintendo/target/walmart 288, gamestop 96) where before
> **none** of them was. The sixth, amazon, is 48 **or** 49 because 86,400 / 1,800 = 48 exactly, so
> its 49th grid point *is* the day boundary: measured at **86,393.2 s** under one seed and
> **86,426.0 s** under another, from 33 s of accumulated jitter. **That is a bound, not a
> tolerance** — the test asserts the 49th fire is within one tick of the boundary, so a 49th
> arriving from anywhere else still reddens.
>
> **Watched red, three ways, each reverted from a `cp` and `diff`-confirmed byte-identical:** the
> tick returned to the standing interval (pre-REQ-23 wake rate) → red; `MIN_TICK_SECONDS` 30 → 60 →
> red; and the `_FROZEN_CLOCK` replaced by the **50 ms-per-call creep that reproduced the
> `04cd831` CI break** → red. That last one matters most: the injected clock is still load-bearing,
> so the repair did not buy seed-independence by loosening the thing the clock was added for.

**Criterion 4b's MET IN PART was confirmed correct**, including that the verdict was committed in
`09-DECISIONS.md` *before* the attempt. Criteria 2, 3, 5 and the standing invariants all VERIFIED —
the `current_interval` digest is byte-identical at the pre-phase commit, at `87871b4` and at HEAD.

**A CORRECTION TO THIS RECORD, 2026-09-02, and it was mine.** The paragraph above first read *"roughly
half of all wakes ask nobody"*. That figure was never measured — it was carried over from the
planning-time estimate in `09-PLAN-OUTLINE.md` and written into this record without being checked
against the phase's own result. **Measured, in `09-04-SUMMARY.md`: 457 wakes a day of 1728 — 26.4%**,
with a 20-seed sweep putting the configured fleet at **26.9%** and a uniform fleet at **3.5%**. So the
claim overstated the effect by nearly 2x, in the direction that made the finding sound more dramatic
than it is. The sentence is corrected in place rather than annotated, because it is not a superseded
*measurement* — it was never a measurement at all, and leaving a wrong number standing beside a right
one would imply the wrong one had once been established. What is recorded beside is this note.

**Two figures 09-03 derived were also wrong and 09-04 corrected them**, both recorded beside rather
than over: empty wakes are **457 (26.4%)**, not 432 (25.0%), and the maximum retailers per wake is
**2**, not 1 — 09-03 derived over the *unjittered* schedule. Its before-column was confirmed exactly
right against the real pre-phase code, so only the after-column moved.

### Phase 10: A Control That Cannot Die

**Goal**: A control that stops resolving is reported as a **dead control** — a fact about our
configuration — and is never reported as a refusal or a broken detector, which are facts about the
retailer.
**Depends on**: Nothing (independent of 8 and 9)
**Requirements**: REQ-24
**Success Criteria** (what must be TRUE):

  1. Three states are **distinct** and asserted separately: *dead control* (our SKU no longer resolves), *refused* (the retailer served a challenge), and *detector broken* (the page arrived and the extractor could not read it). Today the first is reported as the third
  2. A dead control does **not** describe the retailer as refusing us, and does not silence a real refusal if both are true at once
  3. Best Buy's control is repaired — measured against a real reading, not a fixture — or replaced with one that reads, with the replacement's durability argued
  4. **The rule for what makes a control durable is written down and applied to every existing control**, with any control failing it named. Best Buy's died because it was a specific game SKU; a control that can be discontinued eventually will be
  5. `make verify-offline` exits 0, with at least one new mutation registered and observed CAUGHT

**CLOSING RECORD — Phase 10 COMPLETE 2026-09-02. Three MET AS WRITTEN, two MET IN PART; nothing reworded.**

Five plans, five waves. Waves 1-3 offline; wave 4 was the only network contact in the milestone.
Verdict table with citations: `10-05-SUMMARY.md`. Ten collisions: `10-DECISIONS.md`.

**THE PREMISE WAS WRONG, AND THAT IS THE PHASE'S MAIN RESULT.** REQ-24 says *"Best Buy's current dead
control is repaired."* Proved **offline** from the evidence log (Collision 10, recorded unconditionally
so it survives even the branch where every read fails): SKU **6216393 — the control — has never been
shown dead.** It read `in_stock $59.99 · ld+json: InStock from Best Buy` in **four** `make verify`
transcripts (L1642, L1884, L2286, L2413) plus the transcribed search redirect (L860); its only
non-resolution is L960, the **documented 2026-08-04 FALSE dead** from unparseable markup on a live
SKU; and the two most recent attempts (L3482, L4397) are `no Chrome/Chromium binary found` — a **host**
failure, on a box where chromium is in fact installed. The SKU that genuinely resolves to nothing is
**6577129**, a **product** watch for the GO Plus + already removed from config and documented
"unconfirmed and probably wrong" (L822, L868, L901). **It was never the control.** The milestone
framing merged a dead product SKU, a live control and a missing browser into one story. The honest
statement, and both roundings are refused in writing: **never shown dead, last shown alive in early
August, unmeasured for ~4 weeks — absent-then-stale evidence, not contrary.**

**THE WIRE FOUND THE INVERSE DEFECT, AND IT IS WORSE THAN THE ONE REQ-24 PREDICTED.** Three
navigations, Best Buy only, spaced **313 s and 311 s** — 3 of 3 authorised, zero unspent, zero
pre-navigation failures, no fourth request under any branch, and no other retailer contacted. The
incumbent control is **ALIVE** and reads `IN_STOCK $59.99` first-party. **And the monitor, through the
path it is actually configured to use, calls that same live SKU a dead control. Twice.** So a phase
that set out to repair a dead control instead found a **false dead**: this project's core defect —
saying something false, confidently — rebuilt inside phase 10's own new code, and caught by
measurement rather than by argument. `bestbuy`/`D5` was downgraded **PARTIAL → NOT SATISFIED** on that
reading: a *live* target reading as a dead control means an `unresolved` from Best Buy carries no
information in either direction.

**CORRECTION TO THE PARAGRAPH ABOVE, 2026-09-02 — it understated the scope, and the understatement
was this orchestrator's.** "Twice" is the count of *observations*, and reads as a defect in one
product. The tree's own records are broader and are the ones to believe: `10-04-SUMMARY.md` § *THE
FINDING* and `docs/retailer-evidence.md:1250` — **"clause A now fires on every Best Buy SKU, alive or
dead."** The mechanism is why, and it is SKU-independent: Best Buy's SKU search now answers with a
**client-side** redirect (`NEXT_REDIRECT;replace;/product/…/sku/6216393;308;`), so `fetch_rendered`
snapshots the announcing shell — no ld+json, canonical still on the search endpoint — which is clause
A's exact predicate. Every Best Buy watch is configured through SKU search, so every one of them takes
that path. Read ③ went **direct to the product URL** and got `IN_STOCK $59.99` off 1,157,107 B with
blocks 3/0, which is what isolates the defect to the *transport*, not the product.

**Nothing offline could have caught this** — the fixtures are the August pages, captured before the
redirect became client-side. That is the honest reason a live read was worth spending, and it is a
better argument for criterion 3's read budget than the one the phase was planned on.

**The generality rests on the executor's two measurements plus the mechanism, not on a third read.**
The budget is exhausted, so it was not independently re-verified, and that limit is stated rather
than papered over.

**THE FIX IS NOT SHIPPED, DELIBERATELY.** The reads that would confirm it are spent, and an
unconfirmed fix is a recommendation rather than a repair. The control was **not swapped** and
`config/products.yaml`'s Best Buy target is byte-unchanged.

> **SUPERSEDED 2026-09-10, corrected here 2026-09-14 — a fix IS shipped, and it is not the one this
> paragraph declined.** The paragraph stands unedited: it was true for eight days and the reasoning
> in it was sound. What changed is that Dan authorised two more reads (`QUESTIONS.md` § 0h,
> 2026-09-10), and **they overturned the recommendation rather than confirming it.** Read ① proved
> 10-04's redirect-following transport did **not** work; read ② was reallocated to capture the shell,
> and the capture showed the real discriminator was whether the page rendered at all. **What shipped
> is `page_rendered` (2026-09-10, `9e9b78c`), plus `announced_redirect` (2026-09-11, `57ea00b`) after
> a verifier found the `<body>` gate covered only one of the two measured shapes.** The control is
> still **not swapped** and `config/products.yaml` is still byte-unchanged — that half of the
> paragraph never stopped being true. **Both fixes make the monitor honest about a retailer it still
> cannot read**; neither makes Best Buy readable, and production has made **zero** observations of
> either. Evidence: `docs/retailer-evidence.md` § *2026-09-10 — the two § 0h reads*.

| # | Verdict | The half that is not met |
|---|---|---|
| 1 | **MET IN PART** | The three states are distinct and asserted apart — but one route INTO the dead-control state was measured **over-inclusive on the wire**, which is the false dead above |
| 2 | **MET AS WRITTEN** | Both halves of the conjunction asserted separately. Note the mixed group is **unreachable in today's config** (one control per retailer, grouped by retailer) — a latent defect in the code, reachable the moment any retailer gains a second control |
| 3 | **MET IN PART** | The control was measured against a **real reading**, not a fixture — and there was nothing to repair. What is not met is a *repair*, because the premise was false; and the transport defect the read exposed is recommended, not fixed. **~~recommended, not fixed~~ — dated note, 2026-09-14 (re-verifier W3): it IS fixed, twice, and the row's verdict does not move.** `9e9b78c` (2026-09-10) gated clause A on the page having rendered; `57ea00b` (2026-09-11) added the redirect announcement after a verifier found the first covered only one of the two measured shapes; `c5b2fe4` (2026-09-14) gated both, and a re-verifier the same day found the redirect predicate was broader than its own docstring and the prose still outran the flag on a third path — both repaired. **MET IN PART stands and is not improvable by argument**: DoD item 3's first half asks for the repair to be confirmed against a real Best Buy control reading, and there has been none. Best Buy's control was last read **2026-08-25**, so production has observed NONE of it. Four offline fixes and zero live confirmations. |
| 4 | **MET AS WRITTEN** | Rule numbered D1–D5, applied to all **six** controls (the loader's count; `grep -c` says 7 and the seventh is a comment). **D4 is failed by all six**, is **not** circular — it bounds the reserve at D1–D3, the stronger reading being an infinite regress — and duplicates D3 wherever a reserve exists. Target's D5 **NOT SATISFIED**: rung 3 surfaces no HTTP status and inventing one was refused |
| 5 | **MET AS WRITTEN** | **M44** registered and observed CAUGHT (11-test kill set) on `boty/monitor.py`; registry 39 → **40**, survivors 0, `M21`–`M24` still empty, `INTENTIONAL GAP` 9 → 10 |

**Gate at close:** `make verify-offline` **EXIT 0** — **1036 passed / 0 skipped** (from 967 at wave 1),
**40/40 mutations caught**, `Pacer.current_interval` byte-unchanged, both clock terms intact,
staleness-rule count 2, `STATE_VERSION` 2. Verdict line is the **OFFLINE** pass.

**Two corrections to this orchestrator's own instructions, both recorded rather than absorbed.** A
warning was relayed requiring README's Best Buy `unread` cells to move on a successful read; the
executor **refused it with a measurement** — those two cells are the **robots.txt** and **Terms**
policy-document columns measured at rung 1, and a rung-3 *product page* read measures neither.
Moving them would have put a falsehood into a gated support matrix, and reading `robots.txt` to
justify it would have cost a **fourth navigation**. The **Status** cell moved instead, which is what
read ① can speak to. Separately, a span recorded as "7994 bytes" in phase 9's digest recipe is 7994
**characters** / 8018 bytes — corrected beside, because that number is the cross-check a future
verifier reaches for when the digest does *not* match.

**NOT ON THE WIRE.** Phase 10 reaches the daemon only at `sudo systemctl restart boty` — Dan's action,
still deferred, and now carrying Phases 8, 9 **and 10** together.

> **ON THE WIRE SINCE 2026-09-11 07:56:33. Dated note added beside 2026-09-14, not over.** Dan
> instructed the restart; `MainPID` 667833 → 746345, `ExecMainStatus=0`, `NRestarts=0`, pre-restart
> copies of all three live documents taken first. Phases 8, 9 and 10 went on together, exactly as
> the sentence above predicted they would. **Measured, not assumed:** `state.json` migrated 13 → 13
> entries with zero lost; `status.json` 13 rows, `healthy` False → True; and the new loop was proved
> live rather than inferred — `status.json` was rewritten twice inside 70 s, which only happens at
> phase 9's ~50 s tick.
>
> **Two things shipped AFTER that restart and are therefore in the tree and NOT on the wire:**
> `57ea00b` (the second false-dead shape) and `17d3e5d` (the notify redaction, a live defect). The
> next restart carries both. **And "on the wire" is still not "observed":** Best Buy has not read
> since the deploy — its control row is a remembered `in_stock`, `checked=false` — so production has
> made **zero** observations of phase 10's central fix. Three separate claims, kept apart.

### Phase 11: The Honest Ladder Position

**Goal**: What is actually true of Amazon, Target and Walmart is established by measurement and
written down — including, where that is the answer, *dropped*.
**Depends on**: Phase 8 (do not spend the probe budget before the cool-off exists)
**Requirements**: REQ-25
**Success Criteria** (what must be TRUE):

  1. Each of Amazon, Target and Walmart has a recorded verdict in `docs/retailer-evidence.md` citing a **measurement with a date**, stating rung, extraction axis, and what was tried
  2. The **egress-attached vs client-attached** question is either answered with evidence or recorded as **explicitly unanswered**, naming what was tried and what could not be. It is never left implied. *(The decisive test needs a second egress, which needs Dan; an unanswered verdict is a legitimate outcome of this phase and is not a failure)*
  3. `README.md`'s support matrix reflects every changed row and still passes its two-directional gate against the code
  4. A retailer whose honest position is **rung 4** is recorded as rung 4. **The count of working retailers is not padded** — the Phase 2 rot, in the opposite sign, is not available here
  5. **The live probe budget is capped and the cap is stated**: no more than a stated number of requests per retailer for the whole phase, with the actual count recorded. Politeness is a hard constraint and a diagnosis is not a licence
  6. `make verify-offline` exits 0

**Phase 11 — COMPLETE 2026-09-14, IN THE TREE. 2 of 2 plans. ZERO live retailer requests.**

**The constraint it was executed under, first, because it changes how every line below should be
read.** Dan authorised **no probe budget at all** (*"Work offline — no live retailer request is
authorised"*), and both prior budgets (`QUESTIONS.md` § 0g, § 0h) were spent. Every earlier record
in this project says this phase needs live requests — `STATE.md` says so four times. **That was the
right reading of the phase as planned and it was not the only way to satisfy its criteria.**

**WHAT REPLACED THE BUDGET: the daemon's own already-spent requests.** `boty` has been asking these
retailers several times a day since 2026-09-11 07:56:33 on Dan's standing authority. Reading
`journalctl -u boty`, `state.json` and `served/boty/status.json` costs nothing and asks nobody.
**Observation is not probing** — a probe adds a request to a retailer already refusing us, which is
the exact behaviour phases 8 and 9 exist to stop. **What it cannot do is vary anything**, which is
why criterion 2 is unanswered and says so.

**Window: 2026-09-11 07:56:33 → 2026-09-14 08:18:35, 3 d 0 h 22 m, one process, `NRestarts=0`.**

### The three findings, none of which the phase went looking for

**1. THE COOL-OFF FIRED IN PRODUCTION FOR THE FIRST TIME — `target`, 2026-09-14 02:00:00, at 30
consecutive refusals, to `259200` s.** Phase 8 shipped that mechanism on 2026-08-31 and it reached
the wire on 2026-09-11; it had never once been observed executing, and `STATE.md` recorded it as
unobserved rather than claiming it. **`08-UAT.md` item 1 has been open since 2026-08-31 waiting for
exactly this and is now discharged** — days-scale `skipped_reason` and all. Nobody did anything to
make it happen; three days of waiting is what the evidence cost.

**2. AMAZON IS NOT BLOCKED, and every record in this tree implied it was** — including this
milestone's own opening sentence about *"three of six retailers"*. Its refusal counter climbed to 20
and **RESET**, which happens only on a cycle where nothing was refused, and both watches carry
readings stamped 2026-09-14. It is intermittently **and partially** reachable: one page answered
while another was challenged in the same cycle. **No rate is claimed** — one reset in one window has
no denominator, and phase 9's day test was repaired three days earlier for that exact error.

**3. THE EVIDENCE LOG HAD NO SECTION FOR TWO SHIPPED RETAILERS**, and `11-01` fell into it looking
for somewhere to write Walmart's verdict. GameStop and Walmart were configured, control-verified and
advertised ✅ Working with nothing behind them. **It was a documented allowance, not an oversight** —
argued in `evidence_check.py` rule 5 and pinned by a test named `…_is_deliberately_clean`. Reversed
by **rule 7**, watched red first (2 problems, naming exactly those two), at a cost of 27 test-tree
repairs.

### Where the phase landed against the ROADMAP's six criteria

| # | Verdict | What settles it |
|---|---|---|
| 1 | **MET AS WRITTEN** | Dated verdicts for all three in `docs/retailer-evidence.md`, each stating rung, extraction axis, what was tried, and the three-day measurement. Walmart's needed a section created first |
| 2 | **MET AS WRITTEN — by recording it UNANSWERED**, which the criterion names as legitimate in its own text | New `## Phase 11 — the egress-vs-client question` section. What was tried, what could not be, and why: the instrument holds the independent variable fixed. **What the window narrows is recorded beside** — uniform blindness is dead (Amazon, GameStop, Nintendo and Best Buy were not all refused), so the blocks are per-retailer. That separates neither remaining answer |
| 3 | **MET AS WRITTEN** | Four matrix rows moved; `tests/test_support_matrix.py` **44 passed** throughout, both directions |
| 4 | **MET AS WRITTEN, in both directions** | **Padding up removed:** *"Six working retailers"* → **three of six read.** **Padding down refused:** Target and Walmart are NOT recorded as rung 4 — rung 4 here means *dropped, with evidence* (Pokémon Center's precedent, a **Terms** finding), and a retailer refusing a client is a reputational state. `config/products.yaml` is byte-unchanged; dropping either is Dan's call and REQ-25 says so |
| 5 | **MET AS WRITTEN** | Cap **0 per retailer**, stated in `COVERAGE.md` before the first plan ran. Actual **0**. No `boty check`, no write to any daemon-owned file, no restart |
| 6 | **MET AS WRITTEN — and read the second half of this cell, because the first half is the trap** | `make verify-offline` **EXIT 0**, `VERIFY: PASS (OFFLINE — live controls were NOT run…)`. **1047 passed / 0 skipped**, mypy clean, ruff clean, identity **PASS over 288 files**, **40/40 mutations caught, survivors 0**, `M21`–`M24` still the intentional gap, `M45` still free. **WHAT THIS GREEN DID NOT NOTICE, measured (verifier W7):** it stayed green throughout the sixteen days Walmart produced no resolved reading, throughout Target's climb to a cool-off, and while Best Buy went nineteen days unread. And it does not read the support matrix's Status column at all — **putting `✅ Working` and "Six working retailers" straight back keeps 119 tests green.** So this row certifies that the code does what its tests say, and certifies **nothing** about whether the monitor is still watching anything. Phase 11 exists because those two came apart |

**AND ONE THING "CLEAN" STILL DOES NOT MEAN, recorded because the verifier pushed on it rather than
accepting the word.** `served/` is inside `SANDBOX_CONTENTS`, so every sandbox also copied the
daemon's **live, gitignored `served/boty/status.json`** as it stood at that instant. That file is in
no commit and the daemon rewrites it every ~50 s. So the sandbox is **not** a pure function of the
commit, and a clean `git status` cannot show it — no test reads that copy (`mutation_check.py`'s own
comment block says so and explains why it is in the list at all), but *"the sandboxes copied
committed `2508f3c`"* is true of everything except one runtime artifact, and that is the honest
wording.

**THE GATE RUN IS A CLEAN ONE, AND THAT SENTENCE HAD TO BE EARNED.** `mutation_check.py` builds
each mutation's sandbox by copying the **live working tree at that moment**, so a run taken while
files are being edited measures something that is not any commit — the phase-10 re-verifier caught
an earlier transcript of mine doing exactly that (its W5: per-ident kill counts inflated by 27–30
because phase 11's uncommitted edits landed mid-run). **This run was taken at committed `2508f3c`
with `git status --porcelain` captured before and after it: empty both times.** Two files were
committed during it (`b5304c1`) and neither is inside `SANDBOX_CONTENTS`, so no sandbox saw them;
`identity_check` does scan every tracked file, so it was **re-run at `b5304c1` and reads 288 files,
PASS** — the same figure.

**A green here still says nothing about the retailers.** The verdict line is the OFFLINE pass, live
controls were not run, and phase 11's whole subject is that two of six retailers stopped reading
while every offline gate stayed green.

### Two claims already in this tree that the measurement contradicted

Both are corrected **beside**, and both were mine.

- **`STATE.md` / `08-UAT.md`, 2026-09-11: Walmart's rows "carry real verdicts after the restart".**
  They do not. All three carry `read_at: null` and `checked: false`, and a stamp once written is
  never removed by a refusal — so **no resolved Walmart reading has ever been recorded.** Those
  values are the migrated ledger's memory. **A remembered verdict was read off the dashboard and
  mistaken for a fresh one**, which is this project's core defect committed in its own UAT record.
- **`STATE.md` and `REQUIREMENTS.md`: "gamestop's listing is HTTP 410 … the listing is gone".**
  GameStop's GO Plus + watch carries a resolved `out_of_stock` stamped 2026-09-14 08:13:22. Both
  records stand for their own dates; the 410 is no longer available as a present-tense fact.
  `REQUIREMENTS.md`'s conclusion survives on a different premise, and that is said rather than
  letting a right answer launder a stale reason.

**`M45` IS STILL FREE and was deliberately not spent.** Rule 7 is gated by two tests and no
mutation. Pricing an ident here means measuring its kill set against all 40 existing ones, and that
was not done — phase 11's criteria require no new mutation, so registering one on a partial
measurement would buy a denominator rather than a defence. Recorded as an open, priced hole with its
anchor named.

**NOT ON THE WIRE — and the first draft of this paragraph got that wrong in two ways, both caught
by phase 11's own verifier the same day and both corrected here rather than over.**

It read: *"phase 11 changed no production code. What is in the tree and not on the daemon is
`57ea00b` … and `17d3e5d` … **a live defect: 546 health warnings have failed Telegram delivery since
the restart**."*

1. **"Changed no production code" is FALSE.** `2508f3c` — the phase-11 commit — also carries the
   phase-10 re-verification's fixes to `boty/retailers.py::_verdict_from_html`, which change how a
   dead control is decided and are covered by tests that go red when reverted. Bundling two pieces
   of work in one commit and then describing the commit by one of them is the error, not the
   bundling. **So there are THREE things in the tree and not on the daemon, not two.**
2. **"546 … since the restart" is wrong by an order of magnitude and by fifteen days.** Measured
   over the whole journal rather than since 2026-09-11: **4,305** undelivered, from **2026-08-27
   20:07:54** to 2026-09-13 05:26:07 — **16 days 9 h**, all at Telegram's byte offset 353. And that
   dates something else: the **Walmart store pin took effect at the 2026-08-27 restart**, not the
   2026-09-11 one, because the store-disagreement warning is unreachable until a store is pinned.
   Five records in this project said 2026-09-11; all are corrected beside. Full working in
   `docs/retailer-evidence.md` § Walmart.

**What still holds:** all three reach the daemon at the next `sudo systemctl restart boty`, which is
Dan's call; the notify defect is a **first execution and not a regression**; and **restock alerts
were never at risk** — the redaction is applied at two sites, both inside `send_health_warning`.

### Why no phase here proposes escalating a rung

Because it was measured and it does not work. The obvious plan on seeing three blocked retailers
is *"walk them up the ladder"*, and one spike on 2026-08-27 removed it: Walmart refuses the rung-3
browser exactly as it refuses rung 1, and Target has been refused at rung 3 all along. A milestone
that spent a phase on it would have been spending it on a hypothesis already disproved. **The
spike cost one request.**

## Milestone v1.0.0 — Phase Details

Open and untagged. Its definition of done includes *"Dan has successfully bought a
Pokémon GO Plus +"* — a market condition, not a work item — so the milestone audit
recommended against tagging it shipped. All five phases below are complete.

- [x] **Phase 1: Detector Safety Net** - Tests, fixtures and types, so new adapters can't silently break each other (completed 2026-08-02)
- [x] **Phase 2: Five Retailers Green** - Best Buy, Pokémon Center, Nintendo — the tractable ones; hits the MVP bar (completed 2026-08-03)
- [x] **Phase 3: The Hard Two** - Target and Amazon, both known to resist; escalate or document honestly (completed 2026-08-03)
- [x] **Phase 3.1: Target and Amazon, Supported** - INSERTED 2026-08-03. Reverses Phase 3's drop-on-terms decision at Dan's direction (completed 2026-08-03)
- [x] **Phase 4: Open Source Ready** - Contributor docs, CI, packaging, release (completed 2026-08-06)

### Phase 1: Detector Safety Net

**Goal**: A contributor (or I) can add a retailer adapter and be told immediately if it breaks an existing one — offline, without hitting a live site.
**Depends on**: Nothing (first phase)
**Requirements**: REQ-01, REQ-02, REQ-03, REQ-12
**Success Criteria** (what must be TRUE):

  1. Saved HTML fixtures for GameStop and Walmart drive tests that pass without network access
  2. A test proves each of the three availability states, including that an unparseable page yields UNKNOWN and never OUT_OF_STOCK
  3. A test proves a marketplace-seller offer above the price ceiling is not alertable
  4. `mypy` (or equivalent) runs clean over `boty/`
  5. Deliberately corrupting an extractor makes the suite fail, not pass quietly
  6. `make verify` exits 0 on a healthy tree and non-zero if ANY check fails — tests, types, live control products, and the mutation check

**Plans**: 4 plans

Plans:

- [x] 01-01: Fixture capture tooling — save a live page to `tests/fixtures/<retailer>/`, with a note on when and what state it captured
- [x] 01-02: Extraction tests over fixtures — the three states, seller filtering, price ceiling, and the UNKNOWN guarantee
- [x] 01-03: Type hints across `boty/` and `mypy` config
- [x] 01-04: `make verify` — one command, one exit code, covering offline tests + mypy + live control health + the mutation check

### Why `make verify` exists

GSD's verifier is an LLM forming a judgement, and a judgement can be
confidently wrong in the same direction as the code that produced it. The fix
is not a better prompt — it is success criteria that are *executable*, so the
verifier reads an exit code instead of forming an impression.

Every phase from here is verified as "`make verify` passes, plus these
specific observable facts." It also outlives the agents: Dan can run it
himself in six months and get a real answer.

### Phase 2: Five Retailers Green

**Goal**: Every retailer we can actually reach reporting trustworthy stock for the GO Plus +, each control-verified.
**Depends on**: Phase 1
**Requirements**: REQ-04, REQ-05, REQ-06
**Success Criteria** (what must be TRUE):

  1. Best Buy reports stock with NO credentials configured, flagged DEGRADED; and reports stock without the DEGRADED flag when an API key IS present
  2. The Nintendo store reports stock for a real product; Pokémon Center does the same or is documented as unreachable with the evidence
  3. Every retailer has at least one control watch, and `boty check` shows all controls in stock
  4. Each new adapter has fixture-backed tests from Phase 1
  5. The support matrix records which escalation rung each retailer landed on
  6. `make verify` exits 0

**The five-retailer count moved to Phase 3** (2026-08-02, Dan's call). It was written here
as the MVP bar on the assumption that a fifth reachable retailer existed. It does not: the
US retail set for this device is GameStop, Walmart, Nintendo, Pokémon Center, Target and
Amazon. Phase 2 settled four of them — Pokémon Center is rung 4 with four recorded
refusals — and the remaining two are Phase 3's by this roadmap's own scope.

A control-only fifth (Micro Center was probed and is viable, rung 1, config-only) would
have moved the counter without moving the goal, since it does not carry the GO Plus + and
could never alert on it. Adding it was declined for that reason. Target or Amazon landing
in Phase 3 makes five honestly. Evidence for every candidate probed is in
`docs/retailer-evidence.md`.

**Plans**: 4 plans, in 3 waves

Adapters are not as parallelizable as they look: all three touch `boty/retailers.py`,
`config/products.yaml` and `tests/test_retailers.py`, so they serialize. DEGRADED is
shared infrastructure rather than Best Buy-local, and the browser rung is unvalidated
(`nodriver` has no precedent here), so both are front-loaded into wave 1.

Plans:

- [x] 02-01-PLAN.md — Rung-3 browser transport, an offline guard that covers it, and a live spike answering whether Best Buy is reachable at all (wave 1)
- [x] 02-02-PLAN.md — The Rung/DEGRADED reading-method field on Result, surfaced in `status.json` and `boty check`, plus the IN-03 compound-`@type` fix (wave 1)
- [x] 02-03-PLAN.md — Best Buy: browser adapter flagged DEGRADED, optional API path when `BESTBUY_API_KEY` is set, control product, support-matrix row (wave 2)
- [x] 02-04-PLAN.md — Pokémon Center and Nintendo, their controls, and the five-retailers-green end-to-end proof (wave 3)

### Phase 3: The Hard Two

**Goal**: Target and Amazon either working, or documented as unreachable with the evidence that established it. No silent gaps.
**Depends on**: Phase 2
**Requirements**: REQ-07, REQ-08
**Success Criteria** (what must be TRUE):

  1. Target reports stock, or the support matrix records what was tried and why it failed
  2. Amazon reports stock, or the same
  3. Any retailer reached via rung 3 is flagged DEGRADED in the matrix and in `boty check` output
  4. All controls still green; no regression in the four from Phase 2
  5. `boty check` reports five or more retailers with no health warnings — carried over from Phase 2, which reached four because no fifth reachable retailer stocks the GO Plus +. Target or Amazon landing satisfies it. If both are rung 4, this criterion is unmet and recorded as such, never padded with a retailer that does not carry the product
  6. A single `boty check` completes in under 2 minutes
  7. `make verify` exits 0

**Plans**: 3 plans, in 3 waves

**Not parallelizable, and the ordering is deliberate.** Both retailer plans touch
`boty/retailers.py`, `config/products.yaml` and `tests/test_retailers.py` on the branch
where their retailer lands, so they serialize whatever the wave numbers say — the same
lesson Phase 2 learned. Amazon goes first because it is the cheap one: its Conditions of
Use are expected to settle it before any transport work, which is this section's own
instruction ("establish reachability cheaply *before* investing in an adapter"), and its
outcome tells the Target plan whether criterion 5 rests on Target alone.

The likely honest outcome is both refused, both documented, criterion 5 unmet. Every plan
is written so that verifies as complete rather than as a failure.

Plans:

- [x] 03-01-PLAN.md — Amazon: read the Conditions of Use before touching the transport; build the unpaddable-count gate; settle Amazon's rung (wave 1)
- [x] 03-02-PLAN.md — Target: read the Terms first, then walk the ladder politely; register it or record rung 4 with per-rung evidence (wave 2)
- [x] 03-03-PLAN.md — Close the phase: publish and measure the pass duration (REQ-08), complete and gate the support matrix, prove it live under the service's own environment (wave 3)

### Phase 3.1: Target and Amazon, Supported — INSERTED 2026-08-03

**Goal**: Target and Amazon reporting trustworthy stock for the GO Plus +, control-verified, on whatever rung reaches them.
**Depends on**: Phase 3
**Requirements**: REQ-07a (revises REQ-07), REQ-13

**Why this reverses Phase 3.** Phase 3 dropped both retailers on a reading of their
Terms of Use, and recorded criterion 5 as permanently unmet. Dan's decision, 2026-08-03:
support them. His reasoning, recorded because it is the premise the phase rests on —
*"bot-y is a bot for humans. To take the power back from other bots."* The product is
bought out by resellers running exactly this kind of software; a person's own agent
reading the same public product pages, once every five minutes, is the counterweight.

The evidence Phase 3 gathered stays — it is real observation and none of it was wrong.
What changes is the conclusion drawn from it. Phase 3's own Target section already
recorded that the two signals disagree: `www.target.com/robots.txt` does **not** disallow
`/p/`, and Target publishes `sitemap_pdp-index.xml.gz`, a product-detail sitemap that
exists to be crawled. That is the path this phase takes.

**Success Criteria** (what must be TRUE):

  1. Target reports stock for the GO Plus +, with a control watch green. **Recorded UNMET, and deliberately not amended (Dan's call, 2026-08-03).** Target has *delisted* the product — TCIN `88714054` served HTTP 200 as late as 2025-05 and now 404s — so no amount of work can satisfy this. The planner proposed rewriting it to "reports trustworthy stock", which would have been achievable; Dan declined. Editing a success criterion after the fact to make it meetable is the move this project keeps catching in itself, and a criterion that stands unmet with the reason written down is worth more than one quietly moved. Target is still registered as a control-only retailer (the Best Buy shape) at rung 3 + DOM extraction — it ships zero structured data (`isProductDetailServerSideRenderPriceEnabled: false`), so the reading comes from the rendered add-to-cart control and is degraded on both axes
  2. Amazon reports stock for the GO Plus + if it carries it, with a control watch green; or the *technical* outcome is recorded with evidence, having actually been attempted
  3. `boty check` reports **five** or more retailers with no health warnings — six if Amazon lands. Five is the honest ceiling when Amazon is technically unreachable, and criterion 2 explicitly permits that. Do not raise the target to six: a gate that fires on the honest outcome is the Phase 2 rot in the opposite sign. The real number is recorded either way
  4. Every retailer's row in the support matrix states its rung, its robots.txt position and its terms position — a reader can see the disagreement rather than only the verdict
  5. No regression: the four Phase 2 retailers still green, `make verify` exits 0
  6. A single `boty check` still completes in under 2 minutes

**Outcome, recorded 2026-08-03 by 03.1-04 — five of six MET, one UNMET and not amended:**

| # | Verdict | Measurement or reason |
|---|---|---|
| 1 | **UNMET** | Target **delisted** the GO Plus + (TCIN `88714054`, HTTP 200 as late as 2025-05, now 404). Unsatisfiable by any amount of work. The rewrite that would have made it meetable was proposed and **Dan declined it**; the criterion stands as written. Target's *control* watch is green — IN_STOCK at $12.59 |
| 2 | **MET** | Actually attempted, which Phase 3 never did: three `/dp/<ASIN>` requests, three HTTP 200s, zero block-phrase matches. Amazon carries the product, so a real product watch ships beside the control; it reads OUT_OF_STOCK correctly, the sole offer being a used unit at $219 from a reseller |
| 3 | **MET at six** | Amazon landed, so the criterion's own upper form applies. `status.json`: 6 retailers, all `ok: true`, `healthy: true`, **zero** health warnings, 13 watches, 6/6 live controls. `TARGET_RETAILER_COUNT` deliberately left at 5 |
| 4 | **MET** | Seven rows, seven columns — `Extraction` added this phase — machine-checked by `tests/test_support_matrix.py`, both directions |
| 5 | **MET** | Bare `VERIFY: PASS` under the service's `EnvironmentFile`, not `INCOMPLETE`. All four Phase 2 controls IN_STOCK with unchanged extraction sources and seller strings |
| 6 | **MET** | **45.98 s** manual, **44.81 s** service cycle, **42.84 s** next cycle — read off `duration_seconds`, not hand-timed. Budget 120 s |

Full working in `docs/retailer-evidence.md` § *REQ-08* and § *Phase 3.1 closing record*.

**Politeness is now the only constraint, and it is a hard one.** Not as ToU compliance —
as self-interest and basic decency. A blocked IP costs a working monitor, and hammering
someone's origin is how a hobby project becomes a nuisance. 5-minute cadence with jitter,
unchanged. Probing budgets during development stay capped as in Phase 3.

**Plans**: 5 plans, replanned 2026-08-03 after 03.1-02's probe. Every plan runs
in its own wave — the two retailer plans both touch `boty/retailers.py`,
`config/products.yaml` and `tests/test_retailers.py`, so they serialize whatever
the numbers say. **Plan numbers are creation order, waves are execution order**:
03.1-05 was added after 03.1-02 had already run, and runs before its rewrite.

**What the replan responds to.** 03.1-02 probed Target and found it neither
refuses us nor gives us anything: HTTP 200, ~315 KB, no challenge, `"isBot":
false`, and zero structured data of any kind. Stock renders client-side. Dan's
answer is a new extraction axis — his original pre-bot-y script decided stock
from the **Add to Cart button**, and that method is what Target needs. It is
represented as a **second axis, not a new rung**: `Rung` keeps meaning transport,
`Extraction` is `structured` or `dom`, and `Result.degraded` widens to fire on
either a browser transport or a dom extraction. Nothing is renumbered.

Plans:

- [x] 03.1-01-PLAN.md — Both gates before either retailer moves: `evidence_check` rule 5 closes W-02, and REQ-13 becomes machine-checked matrix columns
- [x] 03.1-05-PLAN.md — The Extraction axis (wave 3): `structured` vs `dom`, `degraded` widened to fire on either, M6 re-anchored and M7 proving the new disjunct, and a matrix column with two-directional rules
- [x] 03.1-02-PLAN.md — Target at rung 3 + dom (wave 4), **control-only** because Target delisted the GO Plus +: the robots.txt decision written down first, a DOM add-to-cart reader with its own mutation, a green control, and the verdict revised. *Its first execution (`c79e8ce`) probed Target at rung 1 and escalated rather than registering; that probe is what this rewrite is built on*
- [x] 03.1-03-PLAN.md — Amazon, actually attempted (wave 5): one live `/dp/<ASIN>` read classified against four defined shapes — including the rung-1-plus-dom case Target made real — then registration or a refusal that cites an observation, plus rule 6, which makes REQ-07a mechanical
- [x] 03.1-04-PLAN.md — Close (wave 6): no regression, a measured pass under two minutes with two browser-rung retailers, both axes verified against the live payload, and the real count on the record

### Phase 4: Open Source Ready

**Goal**: Someone who isn't me can install bot-y, add a retailer, and open a PR that I can trust.
**Depends on**: Phase 3
**Requirements**: REQ-09, REQ-10, REQ-11
**Success Criteria** (what must be TRUE):

  1. `docs/adding-a-retailer.md` walks through a real adapter end to end, and states why a control product is mandatory
  2. CI runs the test suite on every PR, offline, against fixtures
  3. ~~`pip install bot-y` works from PyPI~~ — **DESCOPED from v1.0 on 2026-08-07**
  4. README documents the retailer support matrix with each one's method and status
  5. ~~A tagged v1.0.0 release exists~~ — **DESCOPED from v1.0 on 2026-08-07**

**Criteria 3 and 5 were descoped, not met and not quietly reworded.** Dan's decision,
2026-08-07: *"Let's kill those 2 since I wouldn't publish it without more real testing."*
Both were downstream of the same act — publishing — which he deferred on 2026-08-06 with
*"i don't think we need to host it yet. it's probably not quite ready for that."*

They are struck through rather than deleted because **v1.0 did promise a PyPI release and
that promise was withdrawn**, and a reader who cannot see that the promise was made cannot
judge the milestone. This is a scope revision — the criterion was wrong for v1.0 — and is
a different act from the one Phase 3.1 declined, which was rewording a criterion so that
work already done would satisfy it. Nothing here is reworded to pass.

**Nothing technical blocks them.** `make release-check` → 10/10: both artefacts built in a
clean venv, `twine check` PASSED on each, the wheel installed into a venv holding nothing
else, console script run from outside the checkout. The verifier re-ran that independently
rather than trusting the summary. `04-06-HANDOFF.md` stays on disk and still matches the
tree. Publishing later needs no replanning — it needs the real testing Dan named.

REQ-11 moves with them: it is **descoped from v1.0**, not complete.

**Outcome, recorded 2026-08-06 by 04-06 — three of five MET, two UNMET; the two unmet were
subsequently descoped (above) rather than closed. The original verdicts stand unedited:**

| # | Verdict | Measurement or reason |
|---|---|---|
| 1 | **MET** | `pytest tests/test_contributor_docs.py -q` → **19 passed**. `docs/adding-a-retailer.md`, 355 lines, walks **Nintendo** end to end in four numbered steps — probe and write the evidence (8 requests, 12–20 s apart, the 404-at-217,381 B and the product page at 416,346 B), one `FIRST_PARTY` line, the `MARKETPLACES` membership decision, then two YAML watches one of which is a control. The mandate is its own section: `## Why a control product is mandatory`, with `### The rule a control has to satisfy` and `### The rule biting, on a real candidate that was rejected` |
| 2 | **MET — one half observed, one half still asserted, and the difference is written down** | Shipped `on:` block, read back from `.github/workflows/ci.yml`: `pull_request:` with no branch or path filter, plus `push: branches: [main]`. `pytest tests/test_ci_workflow.py -q` → **67 passed**. **Observed on a real runner:** run [`31066215395`](https://github.com/danieljamesjohnson/bot-y/actions/runs/31066215395) — the first live CI run this repository has ever had — event `push`, branch `main`, sha `76d4156`, one job `verify`, conclusion **success**, 02:39:05Z→02:42:22Z (3m21s incl. queue). Its log carries `identity check: PASS — 153 file(s), no host identity found`, `531 passed in 16.54s`, `mutation check: 8/8 mutations caught`, and ends `VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)`. **NOT observed:** the `pull_request` trigger. `gh run list --workflow ci.yml` returns exactly one run — that push. The optional throwaway PR (handoff step 5) was not taken, so the PR trigger remains asserted by `tests/test_ci_workflow.py` and unwitnessed in production |
| 3 | **UNMET** | Dan deferred, 2026-08-06, verbatim: *"i don't think we need to host it yet. it's probably not quite ready for that"*. Re-measured here rather than assumed from Task 1: `https://pypi.org/pypi/bot-y/json` → **HTTP 404** and `https://pypi.org/pypi/bot-y/1.0.0/json` → **HTTP 404**. No trusted publisher was configured, no install was run and no network write was attempted. The criterion is **not amended** |
| 4 | **MET — preserved, not achieved** | It was verified cell-by-cell against live `boty check` output by 03.1-04 *before this phase opened*; Phase 4's job was to not break it, and the measurement is that nothing moved. `pytest tests/test_support_matrix.py -q` → **31 passed**. Across the whole phase — base `b0a272f` re-derived, 44 commits — `git diff -U0 b0a272f..HEAD -- README.md` contains **zero** lines matching `^[-+]\| (GameStop\|Walmart\|Nintendo\|Best Buy\|Pokémon Center\|Amazon\|Target\|Retailer) `. The only README table lines the phase touches at all are the two `\| Stage \| Proves \|` rows 04-03 adds on purpose (`identity`, `lint`) — expected, required by 04-03's own acceptance criterion, and not a support-matrix row. `grep -c '^\| Retailer \| Rung \| Extraction \|' README.md` = **1**, so no second seven-column table exists to hijack the locator `tests/test_support_matrix.py` finds the table by |
| 5 | **UNMET** | No tag exists, anywhere. `git tag -l` → empty (0 tags local); `git ls-remote --tags origin` → **0 refs**, so none on the remote either. No agent created one — this plan ran no `git tag`, no `git push`, no upload. `gh run list --workflow release.yml` → no runs; the publish workflow has never fired, because only a `v*` tag push starts it. Dan's reason is criterion 3's, same date. The criterion is **not amended** |

**What was and was not done, because provenance matters here.** Step 1 of the handoff card
*was* carried out — `git push -u origin main`, `b0a272f..76d4156`, upstream configured on `main`
for the first time — but it was run by **the orchestrator agent, not by Dan**, after he answered
"Sure go for it" to the checkpoint. Steps 2, 3 and 4 (the PyPI trusted publisher, the tag, the
publish) were not done at all. A free consequence of that push, worth recording because it is
GitHub's own detector agreeing with 04-02: `api.github.com/repos/danieljamesjohnson/bot-y` now
reports `license: {"key": "mit", "spdx_id": "MIT"}`, where it read `null` before this phase.

**Neither unmet criterion was reworded, shortened or merged**, and that is deliberate. Phase 3.1
was offered a rewrite of its criterion 1 that would have made it meetable and Dan declined it;
this plan does not get to do what that one refused. Criteria 3 and 5 stand as written, unmet,
with the reason and the date. `.planning/phases/04-open-source-ready/04-06-HANDOFF.md` stays on
disk, unaltered and still accurate, so publishing later needs no replanning.

**The phase gate, run once, live, at close:** `make verify` → **`VERIFY: FAIL (live controls)`**,
exit 2. Recorded verbatim rather than trimmed or re-run until green. Two distinct classes, and
`control_check.py` separates them itself: `2/6 control(s) could not run on THIS HOST` — Best Buy
and Target, both rung 3, `no Chrome/Chromium binary found` (nodriver 0.50.3 is installed here but
no browser is), which the tool states "says nothing about the DETECTOR"; and `2/6 control(s) not
reading IN_STOCK` — Walmart and Amazon, both `blocked: challenge page` at HTTP 200, which *is* a
statement about the detector. None of this touches Phase 4's five criteria, and none of it was
caused by this phase — no plan in Phase 4 changed a retailer, an extractor or a control. It is
recorded here because a closing record that omitted it would be the omission this project keeps
catching in itself. Detail in `.planning/phases/04-open-source-ready/deferred-items.md`.

**Plans**: 6 plans, in 6 waves

Plans:

- [x] 04-01: Contributor docs — adding a retailer, the control-product requirement, the UNKNOWN contract *(wave 1)*
- [x] 04-02: The missing `LICENSE`, and packaging metadata that matches it *(wave 2, blocked on 04-01)*
- [x] 04-03: A linter, from zero — `ruff`, the findings resolved, a `lint` stage inside `make verify` *(wave 3, blocked on 04-01, 04-02)*
- [x] 04-04: GitHub Actions CI — one job per PR running `make verify-offline`, and a test that reads the workflow *(wave 4, blocked on 04-03)*
- [x] 04-05: Release engineering, all of it local — 1.0.0, CHANGELOG, Trusted Publishing workflow, artifacts proven by a clean-venv wheel install *(wave 5, blocked on 04-02, 04-03, 04-04)*
- [x] 04-06: Maintainer handoff — the PyPI Trusted Publisher, the `v1.0.0` tag push, and the five verdicts *(wave 6, blocked on 04-05, `autonomous: false`)* — **closed on a deferred publish**: the card was written and presented, Dan deferred, criteria 3 and 5 stand UNMET and unamended

### Why six plans, not the three sketched above

The original three were written before two facts were established first-hand
during planning, and neither is optional:

- **There is no `LICENSE` file.** The repo is public and `pyproject.toml`
  declares MIT, but `git ls-files` matches nothing and GitHub's API reports
  `license: None`. A public 1.0.0 asserting a licence with no licence text
  arguably grants no rights at all. → 04-02.

- **There is no linter at all** — no ruff, flake8, black or pylint anywhere —
  while REQ-10 names lint in its own wording. → 04-03.

The sixth plan exists because the phase's two maintainer-gated criteria
(3 and 5) must not share a plan with autonomous implementation work. Splitting
them is what lets waves 1–5 run to completion without waiting on Dan.

**Cross-cutting constraints:** every wave is serialised on file ownership —
`scripts/mutation_check.py` (04-01…04-04), `pyproject.toml` (04-02, 04-03,
04-05), `README.md` (04-01, 04-03, 04-05) and `MANIFEST.in` (04-02, 04-04,
04-05) are each contested across waves, never within one. Nothing in this
phase may weaken `make verify`, and every gate it adds is watched failing
before it is trusted.

## Out of Roadmap

Deliberately excluded — see PROJECT.md for reasoning:

- Generic "any URL" extraction ladder (changedetection.io owns this)
- Async/concurrent checking (no benefit at this scale)
- Formal plugin API (premature until ~10 adapters reveal the interface)
- Auto add-to-cart / checkout (different product, different ethics)
- Web UI beyond the read-only status page

## Open Questions

- **Amazon** may be unreachable without a browser or paid proxies. Phase 2 should establish that early and cheaply rather than sinking a plan into it. If it's out, say so in the support matrix with evidence.
- **The upstream `curl_cffi` fetcher contribution to changedetection.io** is tracked separately from this roadmap. Their maintainer asked for exactly the proof we now have (issue #1730); worth doing, but it is not bot-y's critical path.
