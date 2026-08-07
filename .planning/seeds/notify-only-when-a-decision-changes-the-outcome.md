---
type: seed
created: 2026-08-07
source: live operation during Phase 4 execution; Dan's call, 2026-08-07
relates_to: [boty/pacing.py, boty/monitor.py, boty/notify.py, REQ-06]
---

# Page only when a human decision changes the outcome

## The observation

Between 2026-08-05 15:37 and 2026-08-06 16:21, Walmart refused us **9 times in a
row** — roughly 24 hours — and the service sent **5 push notifications** about it.
The correct response to every one of them was "wait". Walmart then recovered on its
own; the 09:42 read on 2026-08-07 was clean (`__NEXT_DATA__: IN_STOCK from
Walmart.com`, control at $2.42). Amazon is running the same pattern now.

Dan's framing, 2026-08-07: *"if something breaks and there's nothing the user can do
you don't have to inform them."*

Five pages you can do nothing about is worse than silence, because it trains you to
ignore the one channel whose whole job is to be worth interrupting you for.

## The line that has to stay drawn

**"Don't tell me" and "don't record it" are different things.** While Walmart was
walled, the GO Plus + was not being watched at Walmart. If the drop had landed in
that window it would have been missed, and nothing would have said why. So the status
page and the log must keep carrying refusals plainly and in full. It is the *push*
that goes quiet, not the record.

This is the same distinction the pre-phase pacing work was reaching for when it split
"the retailer is refusing us" from "the detector is broken" — this is the stronger
version of it.

## The proposed rule

Page when a human decision changes the outcome:

| Condition | Channel |
|---|---|
| Refusal the backoff is actively handling | status page + log only — no push |
| Refusal that **outlasts the cap** and keeps going | push **once** — Dan may want to check that retailer by hand during a drop, and only he can decide that |
| Detector reading **wrong** — parse succeeded, verdict is garbage | push immediately; this is the failure the project exists to catch |
| Control product not reading IN_STOCK | push — an unverified detector is a broken one (REQ-06) |

Note the middle row is what today's code already *tries* to do and gets wrong: the
current message fires repeatedly and its text still says "we are asking too often…
no action is needed unless this persists" **after** the backoff has saturated, which
is precisely when that sentence has stopped being true.

## Why this is a plan and not an edit

It changes what the alerting channel means, and this project's convention is that a
gate or a message with a decision in it gets watched going red in both directions.
The de-duplication state ("have I already paged about this streak?") is new state,
and `Pacer._state` is currently in-memory only — a restart resets it, so a naive
implementation would re-page on every service restart.

## Related

- `Pacer._state` (`boty/pacing.py:67`) does not survive a restart. Any page-once
  bookkeeping hung off it inherits that. Worth deciding deliberately rather than
  discovering.
- Pairs with `.planning/seeds/nothing-reads-the-changelog-body.md` — both are
  "something that should have been noticed, wasn't, and no gate covers it."
