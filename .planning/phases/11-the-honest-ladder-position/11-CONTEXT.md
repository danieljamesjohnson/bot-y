# Phase 11 — The Honest Ladder Position: context

**Written 2026-09-14, before any plan.** Milestone v0.4, REQ-25, the last phase.

---

## The constraint this phase was planned under, stated first because it changes everything

**ZERO live retailer requests are authorised.** Dan's instruction opening this session:
*"Work offline — no live retailer request is authorised."* `QUESTIONS.md` § 0g (three Best Buy
reads) and § 0h (two more) are both fully spent, and no new budget exists.

Every earlier record says this phase needs a probe budget. `STATE.md` says so four times:
*"PHASE 11 MUST NOT START WITHOUT ASKING DAN — it spends a live probe budget at Amazon, Target and
Walmart."* That was the right reading of the phase as planned. **It is not the only way to satisfy
its criteria, and the reason is the thing this phase turns on.**

## The instrument this phase uses instead, and why it is not a loophole

**The daemon is already asking these three retailers, on Dan's standing authority, several times a
day. It has been since 2026-09-11 07:56:33.** Every one of those requests is already spent. Reading
what came back costs nothing and asks nobody.

Three documents record it, all readable without making a request:

| source | what it establishes | cost |
|---|---|---|
| `journalctl -u boty` | every refusal, timestamped, with the consecutive count the ladder is standing on | 0 requests |
| `state.json` | `read_at` per watch — and by `monitor.State.record`'s own early return, a stamp is written **only** for a RESOLVED reading, never for a refusal | 0 requests |
| `served/boty/status.json` | the published per-retailer `reason` and `current_interval_seconds` | 0 requests |

**This is observation, not probing, and the difference is real rather than a word chosen to get
past a rule.** A probe adds a request to a retailer that is already refusing us — the precise thing
phases 8 and 9 exist to stop doing. Reading the daemon's own ledger adds nothing to any retailer's
view of us. The politeness budget is untouched because nothing was spent.

**What it cannot establish, stated before anything is built on it.** It cannot answer any question
that needs a request we have not already made: a different egress, a different fingerprint, a
different rung, or a `robots.txt` nobody has fetched. **Criterion 2 is exactly such a question**,
and this phase's answer to it is *explicitly unanswered* — which criterion 2 itself names as a
legitimate outcome, in writing, at planning time.

**And it is a window, not a distribution.** Three days and nine hours of one host's readings. A
retailer that refused every time in that window has refused every time *in that window*.

## What the window already shows, before any plan is written

Measured 2026-09-14 ~08:18 CDT against the daemon running since 2026-09-11 07:56:33 (PID 746345,
`NRestarts=0`), so the window is **3 d 0 h 22 m**:

- **THE COOL-OFF HAS FIRED IN PRODUCTION FOR THE FIRST TIME.** `target`, 2026-09-14 02:00:00,
  30 consecutive refusals, `current_interval_seconds: 259200`, published reason *"cooling off after
  30 refusal(s) — next attempt in ~2.7 days"*. **This discharges `08-UAT.md` item 1**, which has
  been open since 2026-08-31 waiting for exactly this. It is phase 8's central mechanism, observed
  on the wire rather than in simulation, and it was not observable on 2026-09-11 (target was at 18).
- **Target has produced no resolved reading at all**: `read_at` is `None` on its control. Its
  published `in_stock` is a remembered value from the ledger, `checked: false`.
- **Walmart likewise**: all three rows `read_at: None`, 9 consecutive refusals, first one only at
  2026-09-13 05:30 — before that it was answering and failing for a *different* reason.
- **Amazon is the surprise, and it is the one that stops this phase being a formality.** Its
  refusal counter climbed 10 → 20 and then **RESET to 1**, which happens only on a cycle where no
  amazon watch was refused. Both amazon watches carry real stamps: the GO Plus + resolved
  `out_of_stock` at 2026-09-14 02:26:22 and the control `in_stock` at 03:26:17. **Amazon is not
  blocked. It is intermittently and partially reachable**, and no record in this tree said so.

**So the phase's premise was half wrong in the direction that matters.** The milestone opened on
*"three of six retailers return a challenge page"*. Three days of live observation says the three
are not alike: two of them have not answered once, and the third answered this morning.

## Why "what was tried" is already on the record for all three

Criterion 1 wants rung, extraction axis, and what was tried. None of that needs a new request:

- **Walmart** — rung 1 refused (challenge page), and **rung 3 refused too**: the 2026-08-27 spike
  drove this project's own headless browser at Walmart's control and got
  `rendered challenge page matched 'robot or human'` in 3.8 s. The ladder is exhausted.
- **Target** — already AT rung 3, and refused there: `px-captcha`, recorded 2026-08-27. There is no
  rung above 3 short of rung 4.
- **Amazon** — rung 1, `dom` extraction, and it reads. The open question is not the rung.

## Open questions carried into the plans

1. **Does "not padded" (criterion 4) require moving `README.md` rows to rung 4?** Two of the three
   have not read in three days. The count of *working* retailers is what criterion 4 protects.
2. **Is Amazon's intermittency a duty cycle we can state?** One window, one reset — a rate computed
   off a single reset would be a number with no denominator, which is the error phase 9's day test
   was just repaired for.
3. **`pacer.record(refused=any(...))` vs `assess_health`'s `all(...)`.** A retailer is marked
   refused if ANY watch was refused, so Amazon counted a refusal at 03:26:19 in the same cycle its
   control resolved `in_stock` at 03:26:17. Both are defensible; the asymmetry is noted here as an
   observation and **no change to either is in this phase's scope**.
