# 11-01 — SUMMARY

**Landed 2026-09-14.** Criteria 1, 2 and part of 4. **Live requests made: 0.**

---

## What was established, and by what

Three dated verdicts in `docs/retailer-evidence.md`, one per retailer, plus the egress question
recorded as explicitly unanswered. **Every number came from requests the daemon had already spent**
— `journalctl -u boty`, `state.json`, `served/boty/status.json`. Window: 2026-09-11 07:56:33 →
2026-09-14 08:18:35 CDT, **3 d 0 h 22 m**, one process (`MainPID=746345`, `NRestarts=0`).

**The load-bearing fact, asserted from the code and not from memory.** `read_at` means *a resolved
reading happened*, not *we asked*: `monitor.State.transitioned_to_stock` returns early on `UNKNOWN`
(`boty/monitor.py:417-418`) and the stamp is written below that guard (`:441`), while the refusal
producer sets `read_at=None` outright (`boty/retailers.py:718`). Without that, `read_at: null` is
ambiguous and none of the verdicts below would hold.

| retailer | refusals in the window | counter series | resolved readings | published state at the end |
|---|---|---|---|---|
| **Amazon** | 14 | `10 … 20`, **RESET**, `1, 2, 3` | **2, both 2026-09-14** — GO Plus + `out_of_stock` 02:26:22, control `in_stock` 03:26:17 | backing off, 3 refusals, `14400.0` |
| **Target** | 12 | `19 → 30`, monotonic | **ZERO.** `read_at: null` | **cooling off, 30 refusals, `259200`** |
| **Walmart** | 9 | `1 → 9`, monotonic, **first refusal only at 2026-09-13 05:30:33** | **ZERO.** `read_at: null` on all three rows | backing off, 9 refusals, `21600` |
| *(GameStop, for contrast)* | **39** | bounces 1–5, **16 resets** | **all five watches**, stamped 08:13 | paced at 15 min, `900` |

## The three findings this plan did not go looking for

**1. THE COOL-OFF FIRED IN PRODUCTION, for the first time ever.** Target, 2026-09-14 02:00:00, at
exactly 30 consecutive refusals, to exactly `259200` s. Phase 8 shipped that mechanism on
2026-08-31 and it went on the wire 2026-09-11; `08-UAT.md` item 1 has been open since 2026-08-31
waiting for precisely this observation, and `STATE.md` recorded it as *unobserved* rather than
claiming it. **It is observed now.** The counter entered the window at 19, so the 30 is 12 refusals
here on top of 18 carried across a restart — which is the mechanism working on a total, as designed.

**2. AMAZON IS NOT BLOCKED, and every record in this tree implied it was.** The milestone opened on
*"three of six retailers return a challenge page"*. A counter reset means a cycle in which nothing
was refused (`boty/monitor.py:869`), and Amazon's went 20 → 0. Two stamps date it. **Amazon is
intermittently AND partially reachable** — at 03:26:17 its control resolved `in_stock` and at
03:26:19 the retailer was recorded refused, because a retailer is marked refused if *any* watch was.

**No rate is claimed.** One reset in one window has no denominator. Phase 9's day test was repaired
three days ago for exactly that error and repeating it here with a different subject would be the
same mistake.

**3. GAMESTOP REFUSES MORE THAN ANY OF THEM AND READS ANYWAY.** 39 refusals, 16 resets, never past
5, against readings minutes old. It refuses *requests*, not this client. That contrast is what makes
Target's and Walmart's monotonic climbs mean something rather than being three numbers in a row.

## Criterion 2 — recorded as EXPLICITLY UNANSWERED, with the reason

New section `## Phase 11 — the egress-vs-client question`. The decisive test is the same requests
from a second egress; there isn't one on this host, arranging one is Dan's, and it costs live
requests this phase had none of. **The instrument used holds the independent variable fixed, so no
amount of further observation through it could have answered the question** — stated rather than
discovered at the end.

**What the window does narrow, which is less than an answer:** the uniform-blindness hypothesis is
dead. Amazon answered, GameStop answers constantly, Nintendo and Best Buy were never refused. So
the blocks are **per-retailer**, not a property of the egress as such — which is compatible with
both remaining answers and separates neither. Two things that look like evidence and are not (a
shared bot-management vendor; Walmart's 45-hour prelude) are named as the stories they are.

## Two claims in the tree this plan could not leave standing

- **`STATE.md`, 2026-09-11: Walmart's rows "carry real verdicts after [the restart] (control
  in_stock, GO Plus + out_of_stock)".** Measured today: all three Walmart rows carry `read_at:
  null` and `checked: false`, and a stamp once written is never removed by a refusal. **So no
  resolved Walmart reading has ever been recorded in this document.** Those values are the migrated
  ledger's memory. Recorded here; `STATE.md` corrected beside at the phase close.
- **`STATE.md` and `REQUIREMENTS.md`: "gamestop's listing is HTTP 410 … the listing is gone".**
  GameStop's GO Plus + watch carries a resolved `out_of_stock` stamped 2026-09-14 08:13:22. Both
  records stand for their own dates; what is no longer available is treating the 410 as present
  tense. `REQUIREMENTS.md`'s conclusion — *"nothing to build"* — survives on a different premise,
  and that is said out loud rather than letting a right answer launder a stale reason.

## Gates

`scripts/evidence_check.py --phase` **PASS**. `scripts/identity_check.py --all` **PASS, 282 files**
— and it was run before the journal extracts were pasted, not after, because a syslog line carries a
hostname and this checker has fired on this project's own prose four times.

---

## VERIFIED 2026-09-14, `gaps_found` at 8/12 — and the verifier found FIVE errors in this summary

**Nothing above is edited.** Each correction is here, beside, because the *shape* of every one of
them is the shape this phase was written to catch.

**The method survived the attack, which is worth recording first.** The verifier's verdict on the
zero-budget argument: *"it is not a dodge. The phase added no requests… Nothing it claims needed a
request that wasn't made."* **Where it went wrong was not for lack of a request — it read the free
sources too narrowly.** That is a better finding than a vindication.

### 1. THE WALMART STORE PIN TOOK EFFECT 2026-08-27, NOT 2026-09-11

Five records in this project had settled on 2026-09-11 without anyone checking, and this summary
repeated it. **The pin is dated by the first store-DISAGREEMENT warning**, because that warning is
unreachable until a store is pinned — and the first one is **2026-08-27 20:07:53**, twelve hours
and forty-four minutes after that day's restart, on Walmart's six-hour backoff.

### 2. THE FIGURES WERE A WINDOWED COUNT PUBLISHED AS A TOTAL

| | this summary said | measured over the whole journal |
|---|---|---|
| undelivered Walmart health warnings | 546 | **4,305** |
| span | ~45 h | **16 days 9 h 18 m** (2026-08-27 20:07:54 → 2026-09-13 05:26:07) |
| Telegram byte offset | — | **353 on all 4,305** — one defect, not a family |

**`journalctl --since` is an assumption wearing a measurement's clothes.** The window was chosen
for a good reason — 2026-09-11 is where the current code starts — and then a count taken inside it
was reported as if it were everything. **If you bound a query, say so beside the number.**

### 3. GAMESTOP'S RESETS ARE 18, NOT 16

And the series was printed in the table directly above the wrong count, so any reader who counted it
would have found the prose disagreeing with the data on the same page.

### 4. A RESET DOES NOT PROVE AMAZON ANSWERED

It proves one cycle refused nothing. **The two dated stamps are what carry the claim** — this
summary let the reset do work the stamps were already doing, which is an inference standing in for a
measurement that was right there.

### 5. `boty/retailers.py:718` IS NOW L766

The line moved in the same commit that cited it. A line-number citation written against a file you
are editing is stale before it is committed — the same lesson Collision 10's table has now learned
three times in one day.
