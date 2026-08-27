# Requirements — Milestone v0.4: Don't Get Locked Out

**Scoped 2026-08-27.** Fresh file: v0.3's was removed at its close on 2026-08-19 and archived to
[`milestones/v0.3-REQUIREMENTS.md`](milestones/v0.3-REQUIREMENTS.md), which is the same act v0.2's
close performed. **REQ-01…REQ-13 belong to v1.0.0**, which is open, untagged and not archived;
**REQ-14…REQ-20** are v0.2's and **REQ-21** is v0.3's. This milestone opens at **REQ-22**.

---

## Why this milestone exists

**Measured 2026-08-27, and this is the whole argument.** Of six retailers, three — Amazon, Target,
Walmart — return a challenge page instead of a product page. Of four watches on the actual
Pokémon GO Plus +, **one** still reads: Nintendo. GameStop's listing returns `HTTP 410` (delisted,
like Target's before it). Best Buy's control fails for an unrelated reason: its SKU stopped
resolving.

**The escalation ladder is exhausted for Walmart, and that was measured rather than assumed.** A
single spike on 2026-08-27 drove the project's own rung-3 transport — a real headless browser,
the same one Target and Best Buy use — at Walmart's control product. It came back
`rendered challenge page matched 'robot or human'` in **3.8 s**. Rung 1 is refused and rung 3 is
refused, and Target is independently refused at rung 3 with `px-captcha`. So *escalating a rung*
is not a fix that is available here.

**The defect this milestone attacks is not "three retailers block us".** It is that all six
watches share one point of failure — one egress, one client fingerprint family, one request
pattern — so a single reputational event blinds everything at once. The staggered onset (Target
~2026-08-11, Amazon ~2026-08-22, Walmart 2026-08-24) is consistent with that and also with three
independent detection upgrades; **the two have not been told apart, and REQ-25 exists to tell
them apart rather than to assume.**

**Dan's framing, 2026-08-27, verbatim, and it set this milestone's shape:** *"we don't want to
inform the user it's broken, really. we want to prevent a broken state."* An alarm for lost
coverage was proposed and **deliberately not scoped here**. The requirements below are all
preventive. That choice has a cost worth stating once: prevention lowers the probability and the
blast radius of a lockout and **cannot reduce either to zero**, so a residual undetected-blindness
window remains open at the end of this milestone by design, not by oversight.

---

## Requirements, as written

| ID | Requirement |
|---|---|
| **REQ-22** | A retailer that has refused persistently is **left alone**, not knocked on forever. After a bounded number of consecutive refusals the monitor stops requesting that retailer for a period measured in **days**, then probes **once**. The current behaviour — a fixed 6-hour ceiling applied indefinitely — is replaced, and the replacement is proved to reduce the request count against a retailer that never recovers. |
| **REQ-23** | The retailers are **not checked in lockstep**. Each retailer's schedule is independent, so a single cycle does not present six unrelated retailers requested inside one short window from one origin. The fleet's aggregate request pattern is asserted by test, not by inspection. |
| **REQ-24** | A control product **cannot be discontinued out from under the monitor** without that being distinguishable from a block. A control that stops resolving is reported as a **dead control** — a fact about our configuration — and never as a refusal or as a detector failure, which are facts about the retailer. Best Buy's current dead control is repaired. |
| **REQ-25** | Each blocked retailer's **true ladder position is established and written down**, including whether the block is attached to this egress or to this client. Where the honest answer is **rung 4 — dropped, with evidence** — it is recorded as that rather than left as an open failure. No retailer is described as working, degraded or recoverable on anything but a measurement. |

---

## Definition of Done

1. `make verify-offline` exits **0**, with the mutation registry grown and every new gate observed
   failing before it is trusted.
2. REQ-22 and REQ-23 are proved by **offline tests over the scheduler**, not by observing the live
   daemon — the daemon is evidence, never the gate.
3. REQ-24's repair is confirmed against a real Best Buy control reading, and the dead-control state
   is reachable in a test without one.
4. REQ-25's verdict for **each** of Amazon, Target and Walmart is written into
   `docs/retailer-evidence.md` and cited by `README.md`'s support matrix, which is gated against
   the code and cannot drift.
5. **A retailer that cannot be recovered is recorded as unrecovered.** Meeting this milestone does
   not require Walmart or Amazon to read again — it requires the reason to be established. Padding
   the count with a retailer that does not carry the product is the move Phase 2 already caught
   this project making, and it is not available here.

---

## What is deliberately NOT in this milestone

- **A lost-coverage alarm.** Proposed 2026-08-27 and declined by Dan the same day, on the framing
  quoted above. Recorded because the residual it leaves is real: if prevention fails, nothing here
  will tell you promptly.
- **An egress change** — proxy, VPN or second host. It may turn out to be the only thing that
  recovers Walmart and Amazon, but it costs money, adds a dependency and raises terms-of-use
  questions this project has taken seriously before. **REQ-25 produces the evidence that decision
  needs; the decision itself is Dan's and is out of scope.**
- **Rung 2 / official APIs.** Best Buy's key is free but manually approved, and Walmart's and
  Amazon's have real barriers. All three need a credential only Dan can obtain, so none can be a
  requirement of an autonomous milestone.
- **GameStop's `HTTP 410`.** The listing is gone. The watch already reports *cannot read* correctly
  and recovers by itself if GameStop relists. There is nothing to build.
