"""How often to ask each retailer, and what to do when one says no.

WHY THIS EXISTS
---------------
On 2026-08-04 two of six retailers were failing continuously and had been for a
day. Neither detector was broken. The monitor polls every 300 s, Amazon carried
2 watches and GameStop 5, and there was no backoff of any kind — so a retailer
that walled us got asked again five minutes later, 288 times a day, which both
guaranteed we stayed walled and is precisely the behaviour the project's own
politeness constraint calls a hard limit.

The tell that it was rate and not reachability: a single manual `make verify`
read all six controls green *while the daemon was failing*. One request after a
gap works. 576 a day does not.

TWO KNOBS, AND THEY ANSWER DIFFERENT QUESTIONS
----------------------------------------------
`interval_seconds` per retailer is a standing decision: Amazon is worth asking
about every half hour, not every five minutes, and that is true whether or not
anything is currently wrong.

The backoff is a response to evidence: this retailer just refused us, so ask
less often until it stops. It is exponential because a linear back-off against
an exponential penalty loses, and it is capped.

THE CAP IS NO LONGER THE LAST WORD, AND THAT CLAUSE WAS WITHDRAWN ON 2026-08-28.
Until then the paragraph above ended:

    "and it is capped because a monitor that has backed off to once a day has
    quietly stopped being a monitor — at the cap it keeps trying, and the
    health report keeps saying it is refused, which is a state somebody should
    eventually see rather than one that disappears."

Three measured facts overruled it.

1. "At the cap it keeps trying" was the whole defence, and the trying is what
   costs. Against a retailer that never recovers, the fixed six-hour ceiling
   applied indefinitely makes 125 requests over a simulated 30 days — measured
   2026-08-27 against this file unmodified. 118 of those 125 are the flat tail:
   the ceiling repeating, four times a day, at a retailer that has said no
   every single time. That is not a monitor keeping watch; it is a monitor
   knocking.
2. The state somebody "should eventually see" was, by 2026-08-20, four days old
   and unseen. Recorded off the live daemon that day: gamestop at 14400 s and
   walmart at 21600 s, both on backoff, neither recovering. Nothing about
   asking them a fourth time that day was going to change either number.
3. Past `REFUSALS_BEFORE_COOLOFF` the same simulation makes 37 requests —
   measured 2026-08-28, same window, same retailer, same counting, one rule
   changed.

THE PREMISE SURVIVES AND THE CONCLUSION DOES NOT, which is why this is a
rewrite rather than a deletion. A monitor that has quietly stopped being a
monitor is still exactly the failure to avoid, and it is still the failure this
project exists one level up to prevent. What changed is the answer. A retailer
past the threshold is STILL on the schedule, STILL counted in `refusals`, STILL
published with a cadence and a reason, and STILL probed — once every three
days, and the probe is real. It is left alone, not dropped.

SO: A COOL-OFF IS NEVER A NEVER-ASK-AGAIN. A wait that did not expire would be
a silently dropped retailer wearing a row on the dashboard, which is this
project's own defect rebuilt inside the fix for it. And a cool-off is never a
way to silence a failure that is ours: if a refusal is really a dead control or
a broken detector, three days of quiet hides it for three days, which is a
different problem and not one to make worse here.

IT IS PERSISTED NOW, AND THIS FILE USED TO ARGUE THE OPPOSITE
-------------------------------------------------------------
Until 2026-08-10 the paragraph here read, in full:

    "Deliberately in-memory. A restart clears the backoff and tries once at
    full rate, which is the right trade: the alternative is a persisted
    penalty outliving the condition that caused it, and one extra request per
    restart is cheaper to reason about than a stale file."

Two measured facts overruled it.

1. `boty.service` is a systemd unit with `Restart=` semantics, so a restart is
   not a rare event — it is what a supervisor does whenever anything goes
   wrong. "One extra request per restart" is the cost of a restart you can
   count; against a flapping service it is a retailer that walled us being
   asked at FULL rate indefinitely, which is exactly the behaviour the
   politeness constraint calls a hard limit.
2. REQ-16 says a refusal that outlasts the cap is pushed ONCE. The counter that
   defines "the cap" is `refusals`, and `cli._refusal_is_entrenched` reads it
   and nothing else. If it resets, "once" silently becomes "once per process" —
   and the page-once bookkeeping hanging off it resets with it, so a restart
   re-pages a retailer somebody has already been told about. That is the
   20-pages-in-24-hours failure this module exists to prevent, rebuilt from the
   other end.

THE STALE-FILE OBJECTION IS ANSWERED, NOT DROPPED. The withdrawn paragraph's
objection was a persisted penalty outliving the condition that caused it, and
it gets two answers — the second of which is the stronger:

(a) Every record carries a wall-clock stamp and is discarded past
    `STATE_MAX_AGE_SECONDS`, so a file written before a machine was off for a
    week is ignored rather than applied; and a retailer at zero refusals is
    never written at all, so the document self-cleans.
(b) `due_at` IS STILL NOT PERSISTED, which keeps the withdrawn paragraph's own
    concession intact. A restart still tries once, immediately, at full rate,
    so the condition is re-tested at once. What is inherited is only the DEPTH
    the penalty resumes at IF that one request is refused again, plus whether
    a human has already been told. The withdrawn paragraph was right about the
    request and wrong about the memory.

SO: `refusals` and the wall-clock time it was last incremented are written,
along with the caller's paging memory. `due_at` never is. `cli.watch_loop`
drives this class with a synthetic clock (`scheduled_now`) that starts at 0.0
in every process, so a persisted `due_at` would be a number with no referent:
compared against a fresh 0.0 it either fires immediately or blocks a retailer
for the entire age of the previous process. Neither is a schedule; both are an
accident.
"""

from __future__ import annotations

import json
import logging
import math
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

#: Multiplier applied per consecutive refusal.
BACKOFF_FACTOR = 2.0

#: The longest the BACKOFF will wait between attempts. Six hours is long enough
#: to outlast a rate-limit window and short enough that a retailer coming back is
#: noticed the same day.
#:
#: THE OPENING CLAUSE WAS WITHDRAWN ON 2026-08-28. It read, in full:
#:
#:     "Never wait longer than this between attempts, however many refusals."
#:
#: The words "however many refusals" are now false: past
#: `REFUSALS_BEFORE_COOLOFF` the wait is `COOLOFF_SECONDS`, which is twelve times
#: this number.
#:
#: WHAT SURVIVES IS EVERYTHING EXCEPT THAT CLAUSE, and in particular THE VALUE IS
#: UNCHANGED AT SIX HOURS. What REQ-22 replaced is this ceiling being applied
#: INDEFINITELY, not its size — raising the value instead would have been the
#: tempting cheap fix and it would have lost the distinction the whole phase is
#: about. The cap still governs every refusal count below the threshold, which is
#: every retailer this project has ever actually observed. See
#: `REFUSALS_BEFORE_COOLOFF` for where it stops governing.
#:
#: THAT DISTINCTION IS HELD BY A TEST RATHER THAN BY THIS COMMENT.
#: `test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring`
#: still asserts `MAX_BACKOFF_SECONDS <= 6 * 60 * 60` — "a cap beyond a few hours
#: is not a monitor" — live and unmodified, so a later edit that raised the value
#: to approximate a cool-off would go red rather than read as agreeing with this
#: paragraph.
MAX_BACKOFF_SECONDS = 6 * 60 * 60

#: How many consecutive refusals end the backoff and begin a cool-off. REQ-22,
#: 2026-08-28.
#:
#: The phase goal says "30-odd times", and 30 is the value that makes the
#: superseded assertion BIND rather than survive.
#: `test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring`
#: drives exactly `range(30)` refusals and asserts the six-hour ceiling. At 31 or
#: more that test would survive untouched, which is cheaper and worse: the
#: sentence REQ-22 exists to overrule would still be standing, unremarked, at the
#: exact boundary the requirement is about. A test that survives by being routed
#: around is a test that stopped meaning anything, and nobody would be at the
#: moment of noticing.
#:
#: IT SITS UNDER `MAX_PERSISTED_REFUSALS = 64` ON PURPOSE, not incidentally. A
#: threshold at or above the clamp could never be reached from a restart, because
#: `load` clamps every restored count to 64 — so the cool-off would be a state
#: only a long-lived process could ever enter. Under the clamp, a count restored
#: from disk crosses it, which is what
#: `test_the_persisted_count_is_clamped` now measures from the other side.
#:
#: THE LOWER BOUND THIS PROJECT USED TO STATE IS WITHDRAWN, and it is recorded
#: rather than quietly satisfied. `08-PLAN-OUTLINE.md` and `08-01-PLAN.md` both
#: give it as "comfortably above `cli.REFUSALS_BEFORE_PAGING = 5`". **That
#: constant no longer exists** — it and `_refusal_is_entrenched` were deleted on
#: 2026-08-12 under the no-paging rule, and `boty/cli.py`'s own note records the
#: deletion. 30 is above 5 anyway, so the constraint is satisfied; but it is
#: satisfied against a deleted symbol, and the honest form of that is to say so
#: rather than to cite it.
#:
#: WHAT REPLACES IT IS AN ARGUMENT AND IS MARKED AS ONE. A threshold below about
#: 7 would enter the cool-off before the six-hour ceiling had bound even once (7
#: refusals at the 300 s default), which would make the cool-off a REPLACEMENT
#: for the backoff rather than its successor. 30 is four times that, so the
#: ceiling has bound for the better part of a week's worth of refusals before the
#: cool-off begins. That is a reason, not a measurement, and it is written as a
#: reason.
REFUSALS_BEFORE_COOLOFF = 30

#: How long a retailer past `REFUSALS_BEFORE_COOLOFF` is left alone before it is
#: probed once. Three days — 259 200 s. REQ-22, 2026-08-28.
#:
#: WRITTEN AS `3 * 24 * 60 * 60` on `MAX_BACKOFF_SECONDS`' own precedent, so the
#: units are legible at the definition site rather than in a comment beside a
#: six-figure number.
#:
#: DAYS, BECAUSE REQ-22 SAYS "a period measured in days". Three rather than two:
#: two is the smallest thing that can be called days and reads as a rounding-up
#: of "a couple".
#:
#: THREE RATHER THAN SEVEN, and this is the whole of the duration argument — it
#: stands alone and is not bought with a request count. `08-03` derives the
#: persisted-state staleness window from this number. A week-long window would
#: hold a refusal record as evidence for a week, which weakens at length the
#: stale-file answer the module docstring gives at the top of this file. The only
#: measurement that could reopen three days is one showing a three-day staleness
#: window is itself too long to believe a refusal record for, and that is
#: `08-03`'s to take.
#:
#: A LITERAL, NEVER A DERIVATION. No exponentiation, no `BACKOFF_FACTOR`, no
#: multiple of the cap. `current_interval` reaches this value WITHOUT evaluating
#: `st.interval * BACKOFF_FACTOR ** st.refusals` at all, because a conditional
#: expression does not evaluate the branch it does not take — so past the
#: threshold the float-exponentiation cliff `MAX_PERSISTED_REFUSALS` guards is
#: not merely clamped but unreachable, and no rounding contract is entered. That
#: is why the tests on this boundary assert exact equality rather than
#: `pytest.approx`.
COOLOFF_SECONDS = 3 * 24 * 60 * 60

#: Schema version of the persisted document. A file carrying any other value is
#: treated as absent.
#:
#: The hedge is worth arguing rather than assuming. This one carries a COUNT
#: whose units are a policy decision — `BACKOFF_FACTOR` and the cap — so a
#: future version that changed either and then restored an old file under the
#: new units would pin a retailer at a wait nobody chose. One integer against
#: that is cheap.
#:
#: THE CONTRAST THIS PARAGRAPH USED TO DRAW WAS WITHDRAWN ON 2026-08-13. Until
#: then the sentence above opened with:
#:
#:     "`monitor.State` has no version and needs none: its document is a flat
#:     map of strings whose meaning cannot drift."
#:
#: REQ-21 overruled the premise, not the conclusion. That day `monitor.State`
#: gained a reading time per entry, so its document is a map of ENTRIES each
#: carrying an availability and a stamp, and a sentence resting on *"strings"*
#: cannot be left standing over it.
#:
#: THE CONCLUSION SURVIVES AND THE REASON IS NEW, which is why this is a rewrite
#: rather than a bump over there. `monitor.State` still has no version, on three
#: measured grounds:
#:
#: 1. The distinction this comment always drew is intact and only the example on
#:    the other side of it changed: `refusals` is a count whose units are a
#:    policy decision, and epoch seconds have no policy constant to be
#:    re-pointed against.
#: 2. The price of a version THERE is paid in ALERTS rather than in one repeated
#:    notification. *Treated as absent* applied to `state.json` means forgetting
#:    13 remembered availabilities, so the next in-stock reading on each of them
#:    reads as a fresh restock.
#: 3. A version field does not answer the hazard that is actually there, which
#:    is a DOWNGRADE — an older binary comparing a mapping against `"in_stock"`
#:    and re-alerting. It would not read a version field either, because the
#:    code that would check it is the code that does not exist yet. That
#:    residual is priced, in alerts, in `monitor.State.load` — same commit.
#:
#: BUMPED TO 2 on 2026-08-10 (05-REVIEW WR-01): `warned` changed from a list of
#: names to a mapping of name to the wall clock its paging episode began, so
#: that `load` can age it the way it already ages the refusal counts. A v1 file
#: is treated as absent, which costs one repeated notification and one shallow
#: backoff — the same price the config comment already quotes for deleting the
#: file, and cheaper than reading a dateless list as if it were dated.
#:
#: NOT BUMPED TO 3 FOR REQ-22, 2026-08-28, AND THIS PARAGRAPH IS AN APPLICATION
#: OF THE RULE ABOVE RATHER THAN A WITHDRAWAL OF IT. Nothing above is reversed;
#: a reader must not take this as one. It is written here because `08-02` raised
#: the question and handed it forward, and because the next person to hit the
#: same question deserves the worked precedent and not only the rule.
#:
#: THE CASE FOR A BUMP, STATED FIRST AND IN ITS STRONGEST FORM, because a rule
#: you only ever quote against yourself is not a rule. The paragraph above says
#: this document carries a COUNT whose units are a policy decision — and REQ-22
#: changed exactly that policy. Past `REFUSALS_BEFORE_COOLOFF` the same stored
#: number now denotes a three-day wait where on 2026-08-27 it denoted six hours.
#: That is precisely the shape the rule points at, and it is why the question is
#: a real one rather than a formality.
#:
#: IT RESOLVES AGAINST A BUMP, on three measured legs.
#:
#: 1. THE DOCUMENT'S SHAPE IS UNCHANGED. No new key, no changed type, no changed
#:    nesting; `save` writes the same two sections with the same fields it wrote
#:    before the phase. A pre-phase document and a post-phase document are
#:    parse-compatible in BOTH directions, so no misparse is possible either way
#:    — and a misparse is what the v1 to v2 bump was actually bought for, when
#:    `warned` changed from a list of names to a mapping and the old shape could
#:    not be aged at all.
#:
#: 2. THE COUNT'S MEANING IS UNCHANGED, AND ONLY THE RESPONSE TO IT MOVED.
#:    `refusals` is still the number of consecutive refusals — a true fact about
#:    the retailer's history under either policy, and one neither policy
#:    rescales. What the new policy does is give UNCHANGED evidence a new answer,
#:    in the direction of asking LESS. So an old file read by new code produces a
#:    longer wait, and a new file read by old code produces the six-hour cap.
#:    Both directions are safe and neither is a wait nobody chose, which is the
#:    hazard the opening paragraph names.
#:
#: 3. THE BUMP'S OWN PRICE, QUOTED FROM ABOVE, IS DECISIVE HERE. "Treated as
#:    absent" means every retailer's refusal count is discarded on the upgrade.
#:    So on the day this phase ships, every retailer at or past the threshold
#:    would lose its cool-off, be asked at full rate, and climb the backoff from
#:    the bottom — this phase's own defect, delivered by this phase's own safety
#:    mechanism, to exactly the retailers the phase exists to protect. The price
#:    would be paid in the currency the phase is denominated in.
#:
#: THE RESIDUAL, NAMED HONESTLY. A DOWNGRADE — an older binary reading a
#: post-phase document — is unaffected by a version field, for the same reason
#: this comment already gives about `monitor.State`: the code that would check it
#: is the code that does not exist yet. What that older binary does is apply the
#: six-hour cap to a count it understands, which is leg 2's safe direction.
#:
#: AND THE RULE IS LEFT STANDING UNWEAKENED. A future change that alters the
#: document's SHAPE, or that RESCALES what a stored count denotes rather than
#: what this module does about it, still owes a bump. This one does neither.
STATE_VERSION = 2

#: The longest wait this module's own POLICY can produce, in seconds. REQ-22,
#: 2026-08-28.
#:
#: WRITTEN AS THE EXPRESSION AND NEVER AS ITS CURRENT WINNER, and that is the
#: whole of this constant's content. `COOLOFF_SECONDS` happens to be the larger
#: arm today, so spelling this `= COOLOFF_SECONDS` would produce the identical
#: number and would be wrong the day either arm moves — a later phase raising
#: `MAX_BACKOFF_SECONDS` above the cool-off, or shortening the cool-off, would
#: leave this understating a wait the module actually produces. A window shorter
#: than a wait is precisely the defect this constant exists to remove, and the
#: short form would rebuild it from the other end.
#:
#: THE ONE CASE IT DELIBERATELY EXCLUDES, said rather than left as a hole:
#: `current_interval` returns `max(st.interval, ...)`, and `config._interval`
#: enforces a floor with NO upper bound, so an operator standing interval can
#: exceed this number — a retailer configured at a week. That is outside this
#: constant's claim on purpose. Above it the outer `max` returns the standing
#: interval at EVERY refusal depth (at 0 by the `not st.refusals` branch, from 1
#: to 29 because the capped backoff cannot exceed `MAX_BACKOFF_SECONDS`, and at
#: 30 and beyond because the cool-off cannot exceed `COOLOFF_SECONDS`), so no
#: persisted count is load-bearing there at all and a depth aged out changes
#: nothing about when the retailer is asked. This is the module's POLICY range;
#: above it the wait is the operator's standing decision.
#:
#: THAT EXCLUSION IS ASSERTED RATHER THAN PROMISED, by
#: `test_a_standing_interval_above_the_window_makes_the_restored_depth_irrelevant`.
LONGEST_WAIT_SECONDS = max(MAX_BACKOFF_SECONDS, COOLOFF_SECONDS)

#: Persisted state older than this is discarded rather than applied. DERIVED
#: from `LONGEST_WAIT_SECONDS` rather than re-chosen, so the two cannot drift
#: apart — the same argument `Result.degraded` makes about deriving rather than
#: storing. That constant already IS this project's written answer to how long a
#: refusal stays evidence, because it is the longest wait this module's own
#: policy will ever schedule against one; so a record older than one full
#: longest-wait-length window has outlived the reasoning that produced it. This
#: is half the answer to the stale-file objection quoted at the top of this file;
#: the other half is that `due_at` is never persisted.
#:
#: THE DERIVATION WAS WITHDRAWN ON 2026-08-28 — the CEILING it named, not the
#: rule it states. Until then the two sentences above read, in full:
#:
#:     "DERIVED from `MAX_BACKOFF_SECONDS` rather than re-chosen, so the two
#:     cannot drift apart — the same argument `Result.degraded` makes about
#:     deriving rather than storing."
#:
#:     "The cap already IS this project's written answer to how long a refusal
#:     stays evidence ("long enough to outlast a rate-limit window and short
#:     enough that a retailer coming back is noticed the same day"), so a record
#:     older than one full cap-length window has outlived the reasoning that
#:     produced it."
#:
#: Both are quoted, because they are one argument in two halves and quoting half
#: of it would make this reversal look larger than it is.
#:
#: WHAT OVERRULED THEM, measured:
#:
#: 1. REQ-22 and `08-02` made the cap stop being the longest wait this module
#:    produces. `COOLOFF_SECONDS` is 259 200 s against a 21 600 s cap — twelve
#:    times — so the second sentence's premise ("the cap already IS the answer")
#:    became false on the day the cool-off landed.
#: 2. The consequence was a fact, not a risk. `record` re-stamps `refused_at`
#:    only when a retailer is actually refused, and a retailer in cool-off is
#:    asked once every three days, so its record is TWELVE window-lengths old at
#:    the moment its own next probe falls due. Every restart discarded it, and
#:    the retailer came back on the climbing backoff.
#: 3. `08-01` measured the old rule at 125 requests to a never-recovering
#:    retailer over 30 simulated days; `08-02` measured the new one at 37. A
#:    window that discarded the record turned that 37 back into something near
#:    the 125 on every restart — the phase's own result undone by its own
#:    persistence layer.
#:
#: WHAT SURVIVES IS THE ENTIRE ARGUMENT, and a reader who sees a reversal here
#: and expects a fallen conclusion should be told plainly that none fell.
#: Derived and never re-chosen, so the two cannot drift — untouched. "One full
#: cap-length window" survives in substance as one full longest-wait-length
#: window: the sentence's shape, its reasoning and its conclusion are all
#: intact. What changed is the PREMISE that the cap was the longest wait. The
#: constant survives as a name; only what it derives from moved.
#:
#: WHY ONE CONSTANT MUST GOVERN BOTH HALVES OF THE DOCUMENT — required, not
#: merely tidy. `load` applies this window twice: to the refusal counts and to
#: the paging memory. The persistence banner further down this file already
#: argues why they cannot be separated — restoring one without the other
#: "restores half a decision", and the half that goes missing is the worse one.
#: The mechanism is concrete here: a retailer in a three-day cool-off is not
#: CHECKED for three days, `cli.watch_cycle`'s `still_unhealthy` keeps an
#: unchecked retailer in `warned` for exactly that reason, and a six-hour window
#: against a three-day cool-off would therefore guarantee that every restart came
#: back knowing the retailer is entrenched and NOT knowing somebody had already
#: been told. One constant makes that split impossible, which is why REQ-22's
#: criterion 5 forbids a second staleness rule rather than merely discouraging
#: one, and why the two guard sites below read the same name.
#:
#: THE RESIDUAL, MEASURED RATHER THAN WAVED AT. This window now EQUALS the
#: longest wait, so a record can age out only in the sliver between a cool-off
#: expiring and the next cycle actually probing — the loop's schedule advances
#: with jitter, so the probe lands at or slightly after the wait rather than
#: exactly on it. That is roughly one cycle, about 300 s in 259 200, or 0.12% of
#: the window; and it points the same direction the withdrawn six-hour window
#: pointed 100% of the time, so this is a strict improvement rather than a trade.
#: THE OPTION NOT TAKEN, named so it reads as a decision: a window with slack
#: (`LONGEST_WAIT_SECONDS * 2`, say) would remove the sliver, and would re-choose
#: a number the paragraph above forbids re-choosing — buying 0.12% with the one
#: property that keeps these two constants from drifting apart. If the residual
#: ever bites, the change to consider is to `LONGEST_WAIT_SECONDS`' definition,
#: never a second constant beside this one.
#:
#: THE PARAGRAPH ABOVE WAS WRONG IN BOTH HALVES, AND IS KEPT UNEDITED BESIDE
#: THIS CORRECTION RATHER THAN REPAIRED IN PLACE — 2026-08-31, found by the
#: phase-8 code review, `08-REVIEW.md` CR-01. It was written on 2026-08-28 and
#: believed then; it named a mechanism that does not bite and a number ~59x too
#: small, and a record that quietly agreed with itself afterwards would teach a
#: future reader nothing. `docs/retailer-evidence.md` § 6 is the convention.
#:
#: (a) THE MECHANISM NAMED — jitter — CANCELS EXACTLY. `cli.watch_loop` computed
#: one `delay`, slept it, and advanced the pacer's clock by THE SAME FLOAT, so
#: jitter contributed no differential drift at all. Simulated over a whole window
#: with cycle duration held at zero, the residual is 3-326 s across 200 seeds: a
#: random walk about zero, not a bias, and SMALLER than the 300 s claimed.
#:
#: (b) WHAT ACTUALLY BIT was the check pass's own wall-clock cost, which was
#: never added back to that clock — systematic, unidirectional, and unbounded in
#: the window's length. Measured on this host on 2026-08-31 at the live
#: `duration_seconds: 20.43`: 865 cycles per window, 17 741 s of drift — 4.93 h,
#: or 6.84% of every window, against a claimed 0.12%. `target` sat at 46
#: refusals that day, past `REFUSALS_BEFORE_COOLOFF`, so it bound on a real
#: retailer: a restart in that gap dropped the entry, the retailer returned at 0
#: refusals, and REQ-22's own result was undone by REQ-22's own persistence
#: layer — leg 3 of the argument this very comment gives for widening the window.
#:
#: (c) FIXED AT THE CAUSE, NOT ABSORBED HERE, and `LONGEST_WAIT_SECONDS` is
#: therefore UNCHANGED — which is what the sentence four lines up told a future
#: reader to consider, and the reason it is not what was done: the drift was a
#: defect in the clock, not a property of the policy, and widening the window
#: would have hidden it at every other retailer's expense. `cli.watch_loop` now
#: advances by `delay + cycle_duration`; see the comment there for why adding the
#: term rather than replacing it is load-bearing.
#:
#: (d) THE RESIDUAL AS IT NOW STANDS, RE-MEASURED over 200 seeds after the fix:
#: the probe lands at the first cycle boundary at or after `due_at`, so the
#: sliver is bounded by ONE CYCLE and no longer grows with cycle duration —
#: mean 151 s (0.06%), worst 346 s (0.13%) at the live duration. That is the
#: claim the paragraph above was reaching for; it is true now, for the
#: quantisation reason stated here and not for the jitter reason stated there.
#:
#: CHECKED ON 2026-08-28 AND LEFT UNEDITED: concession (a) in the module
#: docstring says a file written before a machine was off for A WEEK is ignored
#: rather than applied. A week is 604 800 s and this window is 259 200 s, so the
#: sentence is still true and still says what it meant. Recorded rather than
#: silently passed over — this project has been bitten by prose that quietly went
#: false, and a sentence that survives a change is worth the one line that says
#: it was tested.
STATE_MAX_AGE_SECONDS = LONGEST_WAIT_SECONDS

#: Ceiling on a refusal count read back off disk. A measured number, not a round
#: one.
#:
#: `current_interval` computes `st.interval * BACKOFF_FACTOR ** st.refusals` —
#: the address changed on 2026-08-13 when the expression was moved out of
#: `record` into the accessor, and NOTHING ELSE IN THIS COMMENT CHANGED WITH IT.
#: The reachability is the same one call along: `record` evaluates it on every
#: refusal by calling the accessor. Float
#: exponentiation has a domain limit. Measured 2026-08-10 on CPython 3.12.3:
#: `2.0 ** 1024` raises OverflowError; `2.0 ** 1023` returns 8.99e307, and the
#: multiplication that follows overflows to `inf` — which `min()` clamps to the
#: cap harmlessly, so the failure is a cliff rather than a slope. (The exponent
#: is where it breaks; the multiply never raises.) So a file containing
#: `"refusals": 1000000000` is not a big number. It is an exception raised
#: inside every cycle, caught by `watch_loop`'s handler, counted to
#: `FAILURES_BEFORE_GIVING_UP` and returned as exit 1: a one-line denial of
#: service on the monitor, from a file the monitor wrote itself.
#:
#: 64 is far below the crash point and far above where the cap binds (7 refusals
#: at the default 300 s interval), so clamping costs nothing operationally —
#: only the number `skipped_reason` prints changes, and "64 refusal(s)" already
#: says what it needs to.
#:
#: THE OVERFLOW ARGUMENT ABOVE WAS OVERRULED BY REQ-22 AND IS KEPT AS HISTORY —
#: 2026-08-31, `08-REVIEW.md` WR-02. It was true when written on 2026-08-10 and
#: it is not true now, and the interesting part is that the phase that falsified
#: it re-argued this comment on 2026-08-28 without re-measuring it.
#:
#: `current_interval` is a CONDITIONAL EXPRESSION, so at or past
#: `REFUSALS_BEFORE_COOLOFF` the branch holding `st.interval * BACKOFF_FACTOR **
#: st.refusals` is not evaluated at all — a property REQ-22 argues for twice, at
#: `COOLOFF_SECONDS` and inside `current_interval`, without following it here.
#: MEASURED 2026-08-31 with the clamp bypassed: an UNCLAMPED `refusals = 10**9`
#: returns 259200.0 and does NOT raise. The largest exponent this module can now
#: reach is 29 (`300 * 2.0**29 = 1.61e11`), and the `2.0 ** 1024` cliff is ~35x
#: further out than anything reachable. So the denial-of-service sentence above
#: describes a door REQ-22 already closed.
#:
#: WHAT STILL MAKES THIS CONSTANT LOAD-BEARING is the relationship below — it
#: must stay ABOVE `REFUSALS_BEFORE_COOLOFF`, or a restored count could not cross
#: the threshold and persistence would silently defeat the cool-off. That one IS
#: gated, by `test_the_clamp_sits_above_the_cooloff_threshold_so_a_restored_count_can_cross_it`.
#: The constant is therefore kept on a live argument, not a withdrawn one.
#:
#: THE SECOND RELATIONSHIP THIS COMMENT NAMED WAS WITHDRAWN ON 2026-08-28,
#: because its subject had been deleted sixteen days earlier and nobody had
#: come back for the comment. It read, in full:
#:
#:     "It must also stay comfortably above `cli.REFUSALS_BEFORE_PAGING`, or
#:     persistence would silently defeat the paging clause it exists to serve."
#:
#: `REFUSALS_BEFORE_PAGING` and `_refusal_is_entrenched` were deleted on
#: 2026-08-12 under the no-paging rule — a refusal is recorded and never pushed,
#: however entrenched — so there is no paging threshold left to stay above.
#: `boty/cli.py` carries the deletion note and
#: `test_the_clamp_never_restores_a_shallower_wait_than_the_cap` was re-anchored
#: off it the same day. This comment was missed then, found by 08-01 on
#: 2026-08-28 while reading for the cool-off threshold, and fixed here.
#:
#: WHAT REPLACES IT IS A LIVE RELATIONSHIP, not a repair of the dead one. This
#: number must stay ABOVE `REFUSALS_BEFORE_COOLOFF`, and the direction is the
#: same one the withdrawn sentence was reaching for: a clamp at or below the
#: threshold would mean a count restored from disk could never cross it, so a
#: retailer deep in a cool-off would come back from a restart at the six-hour
#: ceiling and the cool-off would be a state only a long-lived process could
#: enter — persistence silently defeating the clause it exists to serve, one
#: requirement along.
#:
#: THAT RELATIONSHIP IS ASSERTED BY A TEST RATHER THAN BY THIS COMMENT, which is
#: the half of the withdrawn sentence that survives unchanged and is the reason
#: it was written this way in the first place: this module must not import
#: `boty.cli` — the dependency runs the other way — and a relationship stated
#: only in prose is one nothing checks.
MAX_PERSISTED_REFUSALS = 64


#: THE FLOOR UNDER THE LOOP'S WAKE INTERVAL, REQ-23, 2026-09-01. A tick shorter
#: than one pass takes means the loop is behind before it sleeps, and the wait
#: it publishes is then a wait it is not keeping.
#:
#: MEASURED, AND THE MEASUREMENT IS ONE READING RATHER THAN A GUARANTEE — that
#: is stated here rather than in a planning document because the next person to
#: move this number will be reading this comment. The only figure available
#: offline is the last PUBLISHED whole-pass duration, `duration_seconds: 20.43`
#: for all 13 configured watches across all six retailers, read from
#: `served/boty/status.json` on 2026-08-31 by the phase-8 code review and QUOTED
#: from that record rather than re-read (nothing in REQ-23 reads or writes that
#: file). 30 s is that reading with about 1.5x of headroom on it.
#:
#: A TICK'S DUE SET IS A SUBSET OF THAT PASS, which is why one whole-pass figure
#: bounds a tick at all: after this phase a tick asks the retailers whose grid
#: point it just crossed, never all six, so 20.43 s is an over-estimate of what
#: a tick costs rather than an estimate of it.
#:
#: WHAT HAPPENS AT THE FLOOR IS DEGRADATION AND NOT AN ERROR, and it is named
#: because it is reachable: with `interval_seconds` at 300 the clamp binds past
#: ten configured retailers, and beyond that point the slots below wrap and two
#: retailers share one. They are still asked at their own cadences — the count
#: does not move — but the separation this phase buys stops growing. Six are
#: configured today.
MIN_TICK_SECONDS = 30.0


def loop_tick_seconds(default_interval: float, roster: Iterable[str]) -> float:
    """How often `cli.watch_loop` wakes — NOT how often any retailer is asked.

    ONE EXPRESSION, READ TWICE, which is the whole reason this is a function
    rather than two literals: `cli.watch_loop` sleeps this and `Pacer` sizes
    `due`'s tolerance from it, and a wake rate that had drifted away from the
    tolerance would skip a retailer that is keeping to its cadence — the exact
    failure `due`'s docstring exists to prevent, arriving from the other side.

    THE CEILING IS WHAT PICKS THE DIVISOR. Four retailers sit on the 300 s
    default, and a tick of 300 s offers exactly ONE tick per 300 s span — so all
    four must be asked at that one tick whatever position they are given, and no
    offset can rescue it. `default_interval / len(roster)` is the largest tick
    that still gives every configured retailer its own slot inside the shortest
    standing cadence: six retailers at 300 s give 50 s slots, and 6 x 50 = 300
    exactly.

    THE FLOOR IS `MIN_TICK_SECONDS` and is argued at its definition.

    AN EMPTY ROSTER RETURNS THE STANDING DEFAULT, which is what the loop slept
    before this phase — so a `Pacer` built without a roster keeps today's
    tolerance rather than acquiring a schedule nobody configured.
    """
    names = {r for r in roster}
    if not names:
        return default_interval
    return max(MIN_TICK_SECONDS, default_interval / len(names))


def slot_offset(retailer: str, roster: Sequence[str], tick: float, standing_interval: float) -> float:
    """WHERE on its own cadence this retailer's attempts land. A position, never a duration.

    A retailer at a 300 s cadence with an offset of 150 s is still asked every
    300 s and still publishes 300. Nothing here computes a wait;
    `current_interval` is still the only expression that does.

    DERIVED FROM THE RETAILER'S NAME AND THE CONFIGURED ROSTER, AND FROM NOTHING
    ELSE. Two constraints, and both are prohibitions rather than preferences:

    1. NOT `hash()`. CPython randomises `str.__hash__` per process unless the
       interpreter is launched with a fixed `PYTHONHASHSEED`, so an offset built
       on it would be a DIFFERENT schedule in every process — which is not a
       schedule, and is the same "a number with no referent" defect this module's
       docstring refuses a persisted `due_at` for. The sorted position of a name
       in the roster is stable across processes, machines and Python builds.
    2. NOT ANYTHING HOST-DERIVED — no hostname, pid, MAC, store id or wall clock.
       An offset carrying host identity would encode a stable fingerprint in
       REQUEST TIMING, which is the one place `scripts/identity_check.py` can
       never look: it scans tracked files, and a schedule is not a file.

    DERIVED RATHER THAN STORED, which is what keeps `STATE_VERSION` out of this
    phase. Storing an offset would be a new key in the document, a bump, and —
    per `STATE_VERSION`'s own argument — every retailer's refusal count discarded
    on the day this ships. Two copies only have to disagree once; here there is
    only ever one, recomputed from config.

    THE MODULO IS WHAT MAKES IT A POSITION ON *THIS RETAILER'S* GRID. amazon at
    1800 s and walmart at 300 s do not share a cadence, so a raw slot in seconds
    would sit outside the shorter one's first interval and delay its first
    request by more than that interval.

    A RETAILER NOT IN THE ROSTER GETS 0.0 — today's behaviour, and the behaviour
    every construction site that names no roster keeps.
    """
    names = sorted(set(roster))
    if retailer not in names or tick <= 0 or standing_interval <= 0:
        return 0.0
    return (names.index(retailer) * tick) % standing_interval


def _next_on_the_grid(previous_due: float, wait: float, now: float) -> float:
    """The next attempt, stepped from the retailer's OWN previous due time.

    READING A OF THE TWO THIS PHASE NAMED, chosen deliberately on 2026-09-01 and
    recorded here because the alternative is one line shorter. Reading B stepped
    once and fell back to `now + wait` whenever that landed in the past; it
    re-anchors to the cycle's clock in EXACTLY the case a fixed-rate schedule
    exists to survive — a retailer that fell behind after a long or failed pass —
    and re-anchoring to the cycle clock is the lockstep mechanism this phase
    removes. So the case that distinguishes them is the case the phase is about.

    TWO PROPERTIES, AND THE FIRST IS THE ONE THE SEPARATION DEPENDS ON:

    1. FIRING EARLY OR LATE DOES NOT MOVE THE POSITION. `due` grants half a tick
       of grace, so a retailer routinely fires slightly before its grid point;
       stepping from `previous_due` rather than from `now` means that grace is
       not compounded into a drift. Under `now + wait` two retailers that fired
       at one tick were given the SAME next due time and stayed merged from then
       on — the merge was absorbing, and a birth offset alone was eroded back to
       six-in-a-window inside a simulated day.
    2. NO CATCH-UP STORM. `previous_due += wait` repeated blindly would queue one
       attempt per missed interval after a long outage. Stepping to the FIRST
       grid point strictly in the future spends the arrears rather than banking
       them, at the cost of skipping the requests that were never made — which is
       the safe direction for a monitor that must not knock.

    `wait` IS THE CALLER'S, COMPUTED THROUGH `current_interval` AND NOWHERE ELSE.
    This function changes WHERE the next attempt lands and never HOW LONG the
    wait is.
    """
    if wait <= 0 or previous_due > now:
        # A non-positive wait is unreachable through `current_interval`
        # (`config._interval` enforces a floor), and the second clause is the
        # early-firing case above: the grid point we just served is still ahead
        # of the clock, so the next one is exactly one wait further on.
        return previous_due + wait
    return previous_due + (math.floor((now - previous_due) / wait) + 1) * wait


@dataclass
class _RetailerState:
    interval: float
    refusals: int = 0
    #: The CALLER's clock, and it never leaves this process. `cli.watch_loop`
    #: advances a synthetic `scheduled_now` from 0.0 every process, so this
    #: number is meaningless to anybody else — which is precisely why `save`
    #: does not write it and `load` does not read it.
    due_at: float = 0.0
    #: WALL clock (`time.time()`), set when `refusals` was last incremented.
    #: This field exists only to be written down.
    #:
    #: This class now holds two clocks and confusing them is the bug that made
    #: `due_at` unpersistable, so state the distinction rather than leave it to
    #: be rediscovered: `due_at` is a position on the caller's schedule;
    #: `refused_at` is a timestamp on the EVIDENCE. `time.monotonic()` is the
    #: wrong tool here for exactly the reason it is the right one in
    #: `cli.watch_cycle`'s duration measurement — its epoch is process- and
    #: boot-local, so it means nothing in a file.
    #:
    #: The residual is accepted and bounded in both directions. An NTP
    #: correction or a manual clock change forward ages a record out early,
    #: which degrades to the old in-memory behaviour — the safe direction. A
    #: jump backwards leaves a stamp in the future, which `load` discards rather
    #: than trusting forever.
    refused_at: float = 0.0

    #: FOUR FIELDS, AND THE COOL-OFF ADDED NONE. REQ-22, 2026-08-28. Recorded
    #: here rather than in a planning document because the next person to ask
    #: "shouldn't there be an `in_cooloff` flag?" will be reading this class, not
    #: that document. Three legs, each checkable:
    #:
    #: 1. THERE IS NO FACT A FIELD WOULD CARRY. The cool-off is a THRESHOLD on
    #:    `refusals`, and `refusals` is already persisted, already stamped by
    #:    `refused_at`, already aged by `STATE_MAX_AGE_SECONDS` and already
    #:    clamped by `MAX_PERSISTED_REFUSALS` — which sits above the threshold on
    #:    purpose, so a restored count can cross it. An `in_cooloff` flag would
    #:    store a value DERIVED from a value already stored, which is the second
    #:    copy of a number this module argues against three times over. Two
    #:    copies only have to disagree once, and the disagreement would be a
    #:    retailer the file says is in cool-off and the arithmetic says is not.
    #:
    #: 2. THERE IS NO PROBE FLAG EITHER, AND THAT IS THE LEG WORTH ARGUING. The
    #:    nearest analog in this class is `_warned_since` — a per-retailer
    #:    wall-clock stamp that exists only to be written down — and copying its
    #:    shape for "we are waiting on one specific probe" was the obvious move.
    #:    It is not needed. "Exactly once" is produced by `record` re-scheduling
    #:    `due_at` UNCONDITIONALLY on every outcome, refusal or not, so the probe
    #:    cannot repeat inside a process; and across a restart `due_at` resets to
    #:    0.0 by design, which is decided and priced at one immediate request.
    #:    A stored probe flag would be a second memory of a decision `due_at`
    #:    already makes, and the two would diverge at exactly the restart the
    #:    flag was added for.
    #:
    #:    THE NUMBER IN LEG 2 MOVED ON 2026-09-01 AND THE CONCLUSION DID NOT —
    #:    noted here rather than edited over, per `docs/retailer-evidence.md` § 6.
    #:    The withdrawn clause, quoted in full: "and across a restart `due_at`
    #:    resets to 0.0 by design, which is decided and priced at one immediate
    #:    request." After REQ-23 a restart resets `due_at` to the retailer's own
    #:    OFFSET (`slot_offset`), not to 0.0, so the price is one request within
    #:    one standing interval rather than one immediate request — at most 300 s
    #:    for the default group and at most 1800 s for amazon. Nothing is
    #:    re-tested less often; each retailer is re-tested LATER within the same
    #:    interval. The compensating fact, recorded beside it: under `Restart=`
    #:    semantics a flapping service used to re-probe every retailer at full
    #:    rate on every restart, and now does not.
    #:
    #:    WHAT SURVIVES IS THE WHOLE OF LEG 2'S CONCLUSION, which is why this is a
    #:    note and not a rewrite: "exactly once" is still produced by `record`
    #:    re-scheduling `due_at` UNCONDITIONALLY on every outcome, so the probe
    #:    still cannot repeat inside a process, and no flag is owed. Only the
    #:    number beside it moved.
    #:
    #: 3. A FIELD WOULD HAVE COST A VERSION BUMP, which `STATE_VERSION`'s comment
    #:    then argues against paying. So these are one argument rather than two,
    #:    and the honest order is this one first: no field is owed, and no bump
    #:    follows from it. Reversing the order would make the bump argument look
    #:    like the reason for the field decision, when it is a consequence of it.
    #:
    #: WHAT WOULD REOPEN THIS: a cool-off that needed to remember something
    #: `refusals` cannot express — a per-retailer duration, a probe outcome kept
    #: across processes, an operator override. None exists today, and adding one
    #: means coming back to `STATE_VERSION` as well as to here.


@dataclass
class Pacer:
    """Decides which retailers are due this cycle, and how hard to back off.

    `now` is passed in rather than read, so tests can drive a day of cycles
    without sleeping through one.
    """

    default_interval: float
    overrides: dict[str, float] = field(default_factory=dict)
    _state: dict[str, _RetailerState] = field(default_factory=dict, repr=False)
    #: WHEN each paging episode began — retailer to wall clock. Not the paging
    #: decision, which `cli.watch_cycle` still owns and still passes through:
    #: this is the same thing `_RetailerState.refused_at` is for the other half
    #: of the document, a timestamp on the EVIDENCE that exists only to be
    #: written down, so that a later process can date it and throw it away.
    #:
    #: IT HAS TO BE THE FIRST TIME, not the last, and that is the whole reason
    #: this field exists rather than a `time.time()` inside `save`. `save` runs
    #: every cycle, so stamping at write time would refresh the record forever
    #: and the age-out would never fire once — a bound that cannot bind is worse
    #: than no bound, because it reads like one in the file.
    _warned_since: dict[str, float] = field(default_factory=dict, repr=False)
    #: Where the backoff survives a restart, or `None` for "do not persist".
    #:
    #: Declared LAST and with a default for the reason `Result.rung` and
    #: `Result.extraction` state one module over: every pre-existing
    #: construction site stays valid and keeps its meaning. There are nine in
    #: `tests/test_pacing.py` alone and not one names a path, and `None` is the
    #: behaviour all of them have today.
    #:
    #: THE COUNT ABOVE WAS EXACTLY TRUE WHEN IT WAS WRITTEN AND IS NOT TRUE NOW —
    #: NOTED HERE RATHER THAN EDITED OVER, 2026-09-01, on
    #: `docs/retailer-evidence.md` § 6's convention. At `46a0768`, 2026-08-10,
    #: `tests/test_pacing.py` held ELEVEN construction sites, two of which named a
    #: path, leaving the nine the sentence claims.
    #:
    #: MEASURED TODAY BY AST over every tracked `.py` file (`ast.Call` with
    #: `func.id == "Pacer"`, `.venv` excluded): 25 of 27 in `tests/test_pacing.py`
    #: name no path, and there are 32 sites tree-wide — 27 here, 3 in
    #: `tests/test_cli_watch.py`, 2 in `boty/cli.py`.
    #:
    #: THE ARGUMENT THE SENTENCE SERVES IS STRENGTHENED RATHER THAN WEAKENED, and
    #: that is why the fix is a note rather than a smaller number: the count of
    #: sites a default protects went UP, not down, and this phase adds two more
    #: defaulted fields below on the strength of it.
    state_path: Path | None = None
    #: THE CONFIGURED ROSTER AND THE LOOP'S WAKE INTERVAL, REQ-23, 2026-09-01.
    #: Declared LAST and defaulted for the reason `state_path` states directly
    #: above, and measured against the same 32 sites: an empty roster gives every
    #: retailer a 0.0 offset (`slot_offset`'s last paragraph) and a `None` tick
    #: makes `due`'s tolerance half the standing default, which is exactly what
    #: this class did before this phase.
    #:
    #: SAY PLAINLY WHAT THE DEFAULT DOES NOT COVER, because a comment that implied
    #: otherwise would be a false prediction about a suite somebody is about to
    #: run. THE DEFAULT PROTECTS THE TOLERANCE AND THE STARTING OFFSET. IT DOES
    #: NOT PROTECT `record`'s ADVANCE, which is unconditional and which no field
    #: here defaults away: a `Pacer` built with neither of these two fields still
    #: steps its next attempt from the retailer's own previous due time rather
    #: than from the cycle's clock. Ten existing tests read the old advance and
    #: `09-02` repairs all ten in the plan that broke them.
    #:
    #: GATING THE ADVANCE ON A NON-EMPTY ROSTER WAS CONSIDERED AND REFUSED. It
    #: would have kept every old test green with no edits at all, and it would
    #: have made every defaulted site — most of the suite — exercise a code path
    #: the daemon never takes, since `cli.watch_loop` always passes both fields.
    #: That buys a small diff by making the evidence describe something that does
    #: not ship.
    roster: tuple[str, ...] = ()
    tick: float | None = None

    def _tolerance_interval(self) -> float:
        """The cadence `due`'s grace is half of — the loop's tick where one is known.

        `None` rather than a numeric default because `default_interval` is not
        available as one, and because "no tick was configured" and "the tick
        happens to equal the standing interval" are the same behaviour but not
        the same fact.
        """
        return self.default_interval if self.tick is None else self.tick

    def _standing_interval(self, retailer: str) -> float:
        """This retailer's cadence with no backoff in force — override or default.

        Extracted 2026-08-17 so `_for` and `current_interval` READ THE SAME
        EXPRESSION rather than each carrying a copy of it. `current_interval` had
        to stop going through `_for` (that call inserted a record as a side
        effect — see the read-only paragraph there), and the obvious repair was
        to inline `self.overrides.get(retailer, self.default_interval)` in both
        places. That is a second copy of a number, which is the thing this module
        argues against three times over: an override added to one and not the
        other means the accessor and the constructor disagree about a retailer's
        standing cadence, and they only have to disagree once.
        """
        return self.overrides.get(retailer, self.default_interval)

    def _for(self, retailer: str) -> _RetailerState:
        if retailer not in self._state:
            standing = self._standing_interval(retailer)
            self._state[retailer] = _RetailerState(
                interval=standing,
                # BORN AT ITS OWN POSITION, not at 0.0. This is the only place an
                # offset enters the schedule; `record` preserves it from here on
                # and nothing else sets `due_at`.
                due_at=slot_offset(retailer, self.roster, self._tolerance_interval(), standing),
            )
        return self._state[retailer]

    def due(self, retailer: str, now: float) -> bool:
        """True when this retailer may be asked again.

        The half-TICK tolerance matters: the loop sleeps its tick with its own
        jitter, so a retailer whose grid point falls just past a tick would
        otherwise wait a whole further tick purely because the sleep came up 3%
        short. This class exists to stretch intervals BEYOND the loop's, never to
        drop cycles from a retailer that is keeping to it.

        THE UNIT WAS CORRECTED ON 2026-09-01 AND THE ARGUMENT WAS NOT. The
        sentence above read, in full, before REQ-23:

            The half-interval tolerance matters: the loop sleeps `interval` with
            its own jitter, so a retailer running at the DEFAULT cadence would
            otherwise be skipped roughly half the time purely because the sleep
            came up 3% short.

        WHAT OVERRULED IT: the loop no longer sleeps the standing interval. It
        sleeps `loop_tick_seconds`, which at the six configured retailers is a
        sixth of it, so a tolerance sized for that sleep was sized for a sleep
        that no longer happens. Half the standing default would now be ten times
        the gap between wake-ups and would let a retailer fire a third of a
        cadence early, every cadence — a widening of the request rate dressed as
        grace.

        WHAT SURVIVES, AND IT IS THE WHOLE SENTENCE'S POINT: this class exists to
        stretch intervals beyond the loop's, never to drop cycles from a retailer
        keeping to one. Half a tick is that same claim measured against the sleep
        that actually happens.

        THE UNDER-REPORT THIS SHRINKS, named because `boty/config.py`'s
        `_retailer_intervals` docstring quotes its old magnitude: a 900 s-override
        retailer on a 300 s global was asked roughly every 750 s while 900 was
        published, because the old `record` re-anchored to `now` and so COMPOUNDED
        the grace — every cycle's 150 s of early firing became the next cycle's
        starting point. It does not compound any more: the grid advance puts the
        next attempt one whole wait past the previous GRID POINT, not past the
        early firing, so the long-run count is exactly the published cadence and
        the residual is one early firing of at most half a tick (25 s at the six
        configured retailers). The direction is unchanged, the magnitude falls,
        and the sustained error is gone rather than reduced. That docstring's note
        is `09-04`'s — this plan does not edit `boty/config.py`.
        """
        return now + self._tolerance_interval() * 0.5 >= self._for(retailer).due_at

    def record(self, retailer: str, *, refused: bool, now: float) -> None:
        """Fold one cycle's outcome into the schedule.

        A refusal multiplies the wait. Anything else — including an ordinary
        OUT_OF_STOCK, and including a parse failure — resets it, because a
        parse failure means the retailer *served* us and the backoff has
        nothing to fix.
        """
        st = self._for(retailer)
        if refused:
            st.refusals += 1
            # Wall clock, and only here: this is the moment the evidence was
            # collected, which is the only thing a later process can date.
            st.refused_at = time.time()
            # Computed THROUGH the accessor rather than beside it, and read
            # after the increment above so it reflects the count this cycle just
            # produced — which is what the inline expression that used to sit
            # here already did, and the reason the value is identical rather
            # than merely equivalent. See `current_interval` for why the two are
            # one expression.
            wait = self.current_interval(retailer)
            log.warning(
                "%s refused us (%d in a row) — next attempt in ~%.0f min, not %.0f",
                retailer,
                st.refusals,
                wait / 60,
                st.interval / 60,
            )
        else:
            if st.refusals:
                log.info("%s is answering again after %d refusal(s)", retailer, st.refusals)
            st.refusals = 0
            st.refused_at = 0.0
            wait = st.interval
        # THE RETAILER'S OWN GRID, NOT THE CYCLE'S CLOCK — REQ-23, 2026-09-01.
        # This line read `st.due_at = now + wait`, and that was the lockstep: two
        # retailers that fired at one tick were handed the SAME next due time and
        # stayed together from then on. Under the loop's jitter the merge was
        # absorbing, so a starting offset alone was eroded back to
        # six-retailers-in-a-window inside a simulated day.
        #
        # WHAT MOVED IS *WHERE*, NOT *HOW LONG*. `wait` above is still
        # `current_interval(retailer)` on the refusal arm and `st.interval` on the
        # other, computed through the accessor and nowhere else. Nothing here
        # lengthens, shortens or clamps a wait; `_next_on_the_grid` only chooses
        # which multiple of it the next attempt lands on. A second expression
        # computing a wait would undo Phase 7's one-cadence property and Phase 8's
        # widen-only rule in a single edit, and `current_interval_seconds` would
        # stop describing the schedule that is actually running.
        #
        # UNCONDITIONAL, AND NOT DEFAULTED AWAY BY THE ROSTER OR THE TICK. See the
        # fields' own comment for why gating it was refused.
        st.due_at = _next_on_the_grid(st.due_at, wait, now)

    # THE CADENCE THIS RETAILER IS CURRENTLY ON, DERIVED AND NEVER STORED.
    # `STATE_MAX_AGE_SECONDS` above and `Result.degraded` one module over make
    # the same argument: a second copy of a number is a second thing to edit,
    # and the two only have to disagree once.
    #
    # Applied harder here, because `record` is a CALLER of this method rather
    # than a second site computing the same thing. The published cadence and the
    # fetch schedule are one expression, so an edit to the backoff cannot move
    # what is published away from what is actually happening — there is nothing
    # to keep in step, only one line to change.
    #
    # WHO READS IT: `status.write` publishes it per retailer as
    # `current_interval_seconds`, and `boty check` builds a load-only `Pacer`
    # purely so it can answer from this same method. Before that existed each
    # surface would have had to work the cadence out for itself, and `boty check`
    # would have compared a reading against `cfg.interval_seconds` while the
    # daemon compared it against the backed-off figure — two surfaces publishing
    # different staleness verdicts about one reading, which is this project's own
    # defect one level up.
    #
    # WHAT IT IS NOT: a staleness comparison. Nothing here reads a clock or takes
    # `now`. This is the threshold; the subtraction against it happens in the
    # surfaces that render it.
    def current_interval(self, retailer: str) -> float:
        """How long we are currently waiting between attempts at this retailer.

        The standing interval — the config default or a per-retailer override —
        with whatever backoff is in force applied to it. At zero refusals the
        two are the same number.
        """
        # `.get` AND NOT `_for`, WHICH IS THE WHOLE OF THIS LINE'S CONTENT. A
        # caller ASKING what the cadence is must not create the record that
        # answers. `_for` inserts a `_RetailerState` for any retailer it has not
        # seen, and `cli._current_intervals` calls this method once per
        # configured retailer — so before 2026-08-17 a `boty check` run
        # materialised an in-memory row for every retailer in the config,
        # including ones `pacer-state.json` says nothing about.
        #
        # THE CONSEQUENCE WAS NOTHING, AND THAT IS STATED RATHER THAN INFLATED:
        # `save` filters `if st.refusals`, and `boty check`'s pacer never calls
        # `save` at all. The defect was that the only thing keeping a READ
        # accessor from writing this document was a filter two methods away and
        # a caller that happens not to save. `save`'s own docstring already
        # concedes it may be promoted to temp-and-replace later; the day that
        # filter is relaxed for any reason, `boty check` — routinely run while
        # the daemon owns this file — starts writing rows for retailers it never
        # asked about.
        st = self._state.get(retailer)
        if st is None:
            # NO RECORD IS NOT AN ERROR AND NOT ZERO REFUSALS-BY-DEFAULT: it is
            # the standing interval, which is the same answer the `not
            # st.refusals` branch below gives, reached without writing anything.
            # This is the fresh-clone case `boty check` hits with no
            # `pacer-state.json`, and it must not warn.
            return self._standing_interval(retailer)
        if not st.refusals:
            # NOT COSMETIC, though at every value this project configures today
            # it is indistinguishable from the general expression below:
            # `BACKOFF_FACTOR ** 0` is 1.0, so the two agree. They stop agreeing
            # the moment a standing interval exceeds `MAX_BACKOFF_SECONDS`,
            # where the general form would clamp a cadence the operator chose
            # while `record`'s non-refusal branch went on scheduling at the
            # unclamped value — the accessor silently disagreeing with the
            # schedule, in the one direction this method exists to make
            # impossible.
            #
            # Measured 2026-08-13: the largest configured interval is Amazon's
            # 1800 s against a 21 600 s cap, so this branch cannot bind on this
            # config, and nothing asserts against it as a gate. It is here so a
            # future config edit cannot make the two answers differ.
            return st.interval
        # THE OUTER `max` IS WHY THIS METHOD IS THREE LINES AND NOT ONE, and it
        # closes the other half of the divergence the paragraph above names.
        # That paragraph closed it for `refusals == 0` and stopped there; the
        # NON-ZERO branch is the one `record` actually schedules from, and until
        # 2026-08-17 it was the bare `min` alone.
        #
        # WHAT THE BARE `min` DID, measured on this tree at `interval_seconds:
        # 86400` before the clamp existed:
        #
        #     interval at 0 refusals: 86400.0
        #     after ONE refusal -> due_at: 21600.0, current_interval: 21600
        #     log: "x refused us (1 in a row) — next attempt in ~360 min, not 1440"
        #
        # A refusal SHORTENED the wait — the monitor asking a retailer that just
        # walled us four times more often — and the log line presented that
        # increase in request rate as a backoff. `config._interval` enforces a
        # floor and no upper bound, so that is a config `Config.load` accepts in
        # silence. This is the politeness constraint inverted, and this module's
        # own opening argument calls politeness a hard limit.
        #
        # A BACKOFF MAY ONLY EVER WIDEN THE WAIT. That is the rule in one
        # sentence, and `max(st.interval, ...)` is that sentence. The CAP IS NOT
        # WEAKENED by it: below the cap the `min` still binds and the wait still
        # tops out at `MAX_BACKOFF_SECONDS`; the `max` can only fire where the
        # operator already chose a cadence longer than the cap, which is a
        # retailer being asked LESS often than the cap, never more.
        #
        # IT ALSO RESTORES `save`'s DIRECTION CLAIM, which is why that docstring
        # is not edited to hedge. `save` argues a truncated read is safe because
        # empty state means every retailer reads at its STANDING interval, and a
        # reading judged against a narrower window over-reports staleness rather
        # than under-reporting it. With the bare `min` that inverted above the
        # cap — the real document answered 21600 where empty state answered
        # 86400, so the truncated read judged against the WIDER window. With the
        # clamp, `current_interval >= st.interval` unconditionally, so the
        # claim holds for every configurable value rather than for most of them.
        #
        # THE COOL-OFF ARM, REQ-22, 2026-08-28. Past
        # `REFUSALS_BEFORE_COOLOFF` the wait stops being a backoff and becomes a
        # flat, days-scale literal. Three things about WHERE it is written:
        #
        # 1. IT IS INSIDE THE `max`, NOT A GUARD CLAUSE ABOVE THE RETURN. A guard
        #    returning `max(st.interval, COOLOFF_SECONDS)` before this line is the
        #    cheaper edit and it was deliberately not taken: it would create a
        #    SECOND `max(st.interval, ...)` site, and "a backoff may only ever
        #    widen the wait" is a rule this method keeps in exactly one place on
        #    purpose — see the paragraph above, which is the whole argument for
        #    the `max` existing at all. Two copies of a rule are two things to
        #    edit and they only have to disagree once. So the widen-only rule
        #    applies to the cool-off for free, rather than by being restated.
        #
        # 2. `COOLOFF_SECONDS` IS A LITERAL REACHED WITHOUT EXPONENTIATION. A
        #    conditional expression does not evaluate the branch it does not take,
        #    so past the threshold `st.interval * BACKOFF_FACTOR ** st.refusals`
        #    is never computed at all. The float-exponentiation cliff that
        #    `MAX_PERSISTED_REFUSALS` exists to guard is therefore not merely
        #    clamped on this arm but unreachable from it, and no rounding contract
        #    is entered — which is why the tests on this boundary assert exact
        #    equality rather than a tolerance.
        #
        # 3. `record` COMPUTES ITS WAIT THROUGH THIS ACCESSOR, so the cool-off
        #    reaches `due_at` and `status.write`'s `current_interval_seconds` with
        #    no second site. The published cadence and the fetch schedule are one
        #    expression; a days-scale wait that the dashboard did not know about
        #    would be a retailer silently off the schedule with a green-looking
        #    row, which is this project's own defect one level up.
        #
        # A COOL-OFF IS NEVER A NEVER-ASK-AGAIN. The retailer stays on the
        # schedule, stays counted, stays published with a cadence, and is probed
        # once per window. A wait that never expired would be a dropped retailer
        # wearing a row on the dashboard.
        return max(
            st.interval,
            COOLOFF_SECONDS
            if st.refusals >= REFUSALS_BEFORE_COOLOFF
            else min(
                st.interval * BACKOFF_FACTOR ** st.refusals,
                MAX_BACKOFF_SECONDS,
            ),
        )

    def skipped_reason(self, retailer: str, now: float) -> str:
        """Why this retailer was not checked — for the status page.

        A skipped retailer must never be published as if it had been checked
        and found fine. It is the same failure this project exists to prevent,
        one level up: a green dashboard over a question nobody asked.
        """
        st = self._for(retailer)
        remaining = max(0.0, st.due_at - now)
        mins = remaining / 60
        # THE COOL-OFF ARM, REQ-22, 2026-08-28. Ahead of the backing-off arm
        # rather than inside it, because the two say different things: one is a
        # widening wait, the other is a state.
        #
        # DAYS RATHER THAN MINUTES, because a true wait of "~4320 min" is a number
        # no reader of this page can act on. It is not wrong; it is right in units
        # that hide what it means, which is the quieter cousin of the failure this
        # method exists to prevent.
        #
        # ONE DECIMAL PLACE, NOT ZERO, and the difference is load-bearing. A
        # partial day formatted to zero decimals renders a live wait as "0 days" —
        # a retailer that is genuinely being left alone, described as one that is
        # not being left alone at all. That is exactly the confident lie the
        # docstring above says this method exists to prevent, reintroduced by a
        # format specifier.
        #
        # AND ONE DECIMAL PLACE DID NOT CLOSE IT — MEASURED 2026-08-31. The
        # paragraph above is kept because its argument is right; what was wrong
        # was believing `.1f` discharged it. `f"{x:.1f}"` ROUNDS, so every
        # remaining wait below 0.05 days (4320 s) still rendered as `~0.0 days`.
        # The band is reachable and reached: `due` skips a retailer while the
        # remaining wait exceeds `default_interval * 0.5` (150 s at the default),
        # so (150 s, 4320 s) is about 14 cycles per cool-off window, each writing
        # a `status.json` row saying the retailer is cooling off and that its next
        # attempt is in ~0.0 days. The tail below therefore falls back to hours —
        # a unit that survives the same rounding at that scale, and a number a
        # reader of the page can act on.
        #
        # THE FORMAT SPECIFIERS HERE ARE PRESENTATION AND NOTHING ELSE. They never
        # feed the schedule: `record` computes `due_at` from `current_interval`'s
        # float and never from this string, and nothing parses this prose back
        # into a number. That is why the boundary tests over `current_interval`
        # assert exact equality while this method is allowed to round.
        # DERIVED FROM THE SCHEDULE, NEVER RESTATED — CORRECTED 2026-08-31.
        # `st.refusals >= REFUSALS_BEFORE_COOLOFF` alone was a SECOND copy of the
        # rule `current_interval` deliberately keeps in one place, and the
        # argument for putting the cool-off inside that `max` is the same
        # argument against this: two copies of a rule are two things to edit and
        # they only have to disagree once.
        #
        # THEY ALREADY DISAGREED, on a config `Config.load` accepts in silence.
        # `config._interval` enforces a floor and no upper bound, so
        # `interval_seconds: 604800` loads; at a week's standing interval
        # `max(604800, COOLOFF_SECONDS)` returns the standing interval at EVERY
        # depth, and the retailer is asked at exactly the cadence the operator
        # chose. No cool-off is in force — and this method said "cooling off"
        # anyway, which is a surface naming a cause the code did not establish.
        if (
            self.current_interval(retailer) == COOLOFF_SECONDS
            and st.refusals >= REFUSALS_BEFORE_COOLOFF
        ):
            left = (
                f"~{remaining / 86400:.1f} days"
                if remaining >= 0.05 * 86400
                else f"~{remaining / 3600:.1f} hours"
            )
            return f"cooling off after {st.refusals} refusal(s) — next attempt in {left}"
        if st.refusals:
            return f"backing off after {st.refusals} refusal(s) — next attempt in ~{mins:.0f} min"
        # Through the accessor, not off `st.interval` directly: this was the only
        # public method that read the interval, and leaving it reading the field
        # would leave a second reader of the thing `current_interval` exists to
        # make single.
        #
        # THE OUTPUT IS UNCHANGED, which is what makes this a refactor rather
        # than a behaviour change, and it is an identity rather than a hope: this
        # branch is only reached when `st.refusals` is falsy, and at zero
        # refusals the accessor returns `st.interval`. `tests/test_pacing.py`'s
        # "paced at 30 min" assertion is byte-unchanged across this edit.
        return f"paced at {self.current_interval(retailer) / 60:.0f} min — next attempt in ~{mins:.0f} min"

    # ----------------------------------------------------------------------
    # Surviving the process
    #
    # WHY THESE TWO TAKE AND RETURN `warned`, WHICH IS NOT THIS CLASS'S STATE.
    # A reviewer will otherwise read it as a field this class forgot to store,
    # so: it is passed THROUGH and never held. `Pacer` decides cadence — `due`,
    # `record` and `skipped_reason` do not read `warned` and must not start.
    # `cli.watch_cycle` decides paging. But the two facts are written and read
    # at the same two moments, and REQ-16's "pushed once" is a joint property of
    # both: `refusals` decides whether a refusal is PAGEABLE, `warned` decides
    # whether it has ALREADY BEEN PAGED. Restoring one without the other
    # restores half a decision — and the half that is missing is the worse one,
    # because a process that comes back knowing the retailer is entrenched and
    # not knowing it already said so pages immediately. One document, one write,
    # one load. A second file would be a second gitignore line, a second
    # corrupt-file path, and a second way for a restart to come back holding a
    # contradiction. A field this class never read would be a smell; a parameter
    # it only serialises is a stated pass-through.
    #
    # Instance methods rather than a `State`-style classmethod, because `Pacer`
    # needs `default_interval` and `overrides` at construction and
    # `cli.watch_loop`'s invariant is one pacer for the life of the loop: the
    # loop builds the pacer and then loads INTO it.
    #
    # THE SENTENCE THAT USED TO CLOSE THAT PARAGRAPH WAS WITHDRAWN ON
    # 2026-08-13. It read, in full:
    #
    #     "A classmethod would invite a second construction site, which is the
    #     thing that invariant forbids."
    #
    # REQ-21 built a second construction site that day, deliberately:
    # `cli.main`'s `check` branch constructs a `Pacer` and calls `load()` on it,
    # so that `boty check` answers "what cadence is this retailer on" with the
    # daemon's own backoff depth rather than with the config value. Leaving the
    # sentence standing would have it read as forbidding the thing the file now
    # does.
    #
    # THE INVARIANT IT NAMES IS UNTOUCHED, and it was never about construction —
    # it is `cli.watch_loop`'s: ONE pacer for the life of the LOOP, because the
    # backoff is memory within a loop and a pacer rebuilt each cycle forgets
    # every refusal and hammers at full rate. `boty check` runs one pass and
    # exits. Its pacer is load-only, never reaches `run_once`, and holds no
    # memory across anything, so there is no loop for it to forget within.
    #
    # SO THE BLANKET PROHIBITION IS REPLACED BY A RULE THE NEXT CASE CAN BE
    # TESTED AGAINST, rather than by a prohibition to route around: A SECOND
    # PACER IS ALLOWED EXACTLY WHEN IT NEITHER SAVES NOR SCHEDULES. One that
    # saves is a second writer to this document; one that schedules is a second
    # memory of a backoff, and the two would diverge. `cli.main`'s satisfies
    # both clauses and `tests/test_cli_watch.py` asserts them rather than
    # trusting them.
    # ----------------------------------------------------------------------

    def load(self) -> set[str]:
        """Restore the backoff depth from disk, and hand back the paging memory.

        Built on `monitor.State.load`'s shape — one `try` around the read and
        the parse, catching `(OSError, json.JSONDecodeError)` into empty state —
        and on `parse.nextdata_offers`' discipline inside it: `isinstance` at
        every step, each failure returning nothing rather than guessing, so no
        other exception type can arise from a hostile document. A corrupt,
        truncated, absent or hand-edited file must never stop the monitor
        starting, and must never pin a retailer at the cap forever.

        `due_at` is not read, and the module docstring says why: it was measured
        against a clock that no longer exists.
        """
        if self.state_path is None:
            return set()
        try:
            doc = json.loads(self.state_path.read_text())
        except (OSError, json.JSONDecodeError):
            return set()
        if not isinstance(doc, dict) or doc.get("version") != STATE_VERSION:
            return set()

        now = time.time()
        retailers = doc.get("retailers")
        if isinstance(retailers, dict):
            for name, entry in retailers.items():
                if not isinstance(name, str) or not isinstance(entry, dict):
                    continue
                refusals = entry.get("refusals")
                # `bool` is an `int` subclass, so `"refusals": true` would
                # otherwise restore a backoff of 1. `config._price`'s own
                # precedent, one module over.
                if not isinstance(refusals, int) or isinstance(refusals, bool) or refusals <= 0:
                    continue
                refused_at = entry.get("refused_at")
                if not isinstance(refused_at, (int, float)) or isinstance(refused_at, bool):
                    continue
                # BOTH bounds. Past the staleness window the record has outlived
                # its reasoning; a stamp in the FUTURE is a clock that jumped
                # backwards, and with only an upper bound it would hold the
                # state for as long as the skew lasted.
                #
                # "Past the cap" is what this said until 2026-08-28. The bound
                # is no longer the backoff cap — it is the longest wait the
                # module's policy can produce, which past
                # `REFUSALS_BEFORE_COOLOFF` is the cool-off. A plain correction
                # rather than a dated reversal, because the words carried a
                # LABEL for the bound and not an argument about it; the argument
                # is at `STATE_MAX_AGE_SECONDS` and is where the reversal lives.
                if not 0.0 <= now - float(refused_at) <= STATE_MAX_AGE_SECONDS:
                    continue
                # `interval` comes from config, never from the file: it is a
                # standing decision, and a persisted copy would let yesterday's
                # file quietly override an edit to `retailer_intervals` — the
                # opposite of what a settings file is for.
                st = self._for(name)
                st.refusals = min(refusals, MAX_PERSISTED_REFUSALS)
                st.refused_at = float(refused_at)

        # THE PAGING MEMORY IS AGED EXACTLY LIKE THE REFUSAL COUNTS ABOVE, and
        # until 2026-08-10 it was not aged at all: `STATE_MAX_AGE_SECONDS` was
        # applied to `retailers[*].refused_at` and to nothing else, so `warned`
        # was restored unconditionally whatever the file's age. Combined with
        # `cli.watch_cycle`'s `still_unhealthy = ... | (warned - checked)`, an
        # entry only leaves the set when the retailer is CHECKED and no longer
        # pageable — which, for a genuinely broken detector, never happens. A
        # file written months ago carrying one name suppressed that retailer's
        # health warning indefinitely, from evidence this module's own docstring
        # calls outlived, and re-wrote it every cycle. The alert this project
        # exists to send, silenced permanently by a stale runtime artifact.
        #
        # Same window, same both-ended bound, same reasoning as the counts: past
        # the staleness window the record has outlived what produced it, and a
        # stamp in the FUTURE is a clock that jumped backwards. ("Past the cap"
        # until 2026-08-28, corrected for the reason given at its twin above —
        # and "same window" is now load-bearing rather than incidental: one
        # constant governs both halves so they cannot age apart.)
        warned = doc.get("warned")
        if not isinstance(warned, dict):
            return set()
        restored: set[str] = set()
        for name, stamp in warned.items():
            if not isinstance(name, str):
                continue
            if not isinstance(stamp, (int, float)) or isinstance(stamp, bool):
                continue
            if not 0.0 <= now - float(stamp) <= STATE_MAX_AGE_SECONDS:
                continue
            # Carried, not re-stamped, so the episode keeps its own age across
            # this process's whole life and the next restart can still discard it.
            self._warned_since[name] = float(stamp)
            restored.add(name)
        return restored

    def save(self, warned: set[str]) -> None:
        """Commit the backoff depth and the paging memory in one write.

        Retailers at zero refusals are omitted, so only a retailer currently in
        a backoff appears: one that started answering again drops out, and one
        deleted from the config ages out rather than accumulating forever.

        `warned` is written as a MAPPING of retailer to the wall clock at which
        its episode began, not as the sorted list it used to be, and the change
        is the whole of WR-01's fix. The old shape carried no date, so `load`
        had nothing to age it by; this one is stamped exactly as
        `retailers[*].refused_at` is, and `load` applies the identical window.
        Each entry keeps the stamp it already had — `_warned_since.get(name,
        now)` — because `save` runs every cycle and re-stamping would refresh
        the record forever. `sort_keys=True` on the dump makes the write stable,
        which is what the sorted list was buying.

        Plain `write_text`, NOT `status.write`'s temp-and-replace, and the
        difference used to be argued from a fact that is no longer true. The
        withdrawn sentence, 2026-08-13:

            "This file has exactly one reader, once, at startup, in the same
            process that writes it."

        REQ-21 overruled it that day. `cli.main`'s `check` branch now loads this
        document too, on a surface routinely run while the daemon is writing, so
        there is a second reader and it can catch a partial write.

        THE DECISION SURVIVES AND IS RE-ARGUED RATHER THAN DROPPED. The write
        stays a plain `write_text` because the new reader's worst case is
        bounded and points the safe way: a truncated read raises
        `JSONDecodeError`, `load` already turns that into empty state, every
        retailer then reads at its STANDING interval, and a reading judged
        against a narrower window than the real one over-reports staleness
        rather than under-reporting it — which is the direction REQ-21 prefers,
        and it self-heals on the next check. Promoting this to temp-and-replace
        is available and was deliberately not done when the second reader
        landed: this is the daemon's persistence path, that plan's rule was that
        pacing behaviour does not move, and the benefit accrues only to the
        reader. If the residual ever bites, that is the change to make.

        Wrapped, on `status.write`'s precedent: failing to persist a backoff
        must degrade to the old in-memory behaviour, never take down a cycle. A
        full disk is a worse monitor, not a dead one — and `watch_loop` calls
        this from a `finally` inside its own handler, so a raise here would be
        counted as a failed cycle and ten of them would exit the service.

        `Exception`, NOT `OSError`, and that widening was bought by 05-REVIEW's
        WR-05. Only the write raises `OSError`; `sorted(warned)` and
        `json.dumps` are in here too, and neither does. `sorted` over a set with
        mixed key types raises `TypeError` — reachable, before CR-01 coerced
        `Watch.retailer`, because `Health.retailer` and therefore `warned` could
        hold a non-`str`. So the handler was narrower than the promise in the
        paragraph above it, and the gap was expensive rather than untidy: the
        `finally` at the call site means anything escaping here also DISCARDS a
        pending `return 1` on the give-up path, replacing a diagnosable exit
        code with a traceback from a function whose only job is writing a
        counter to disk — the exact outcome `cli._warn_monitor_is_stuck`'s
        docstring says it exists to avoid.

        A blanket `except` is normally the wrong instinct, and it is the right
        one here for the reason `_warn_monitor_is_stuck` gives: this is a
        best-effort side effect on the failure path, so ANY failure of it must
        be reported and stepped over rather than promoted. `log.exception`
        carries the type and the traceback, so nothing is swallowed silently.
        """
        if self.state_path is None:
            return
        try:
            now = time.time()
            # Rebuilt from the caller's set every write, so a retailer that left
            # `warned` leaves the stamps too and nothing accumulates. `.get`
            # preserves the episode's ORIGINAL start; only a name that was not
            # already being tracked is stamped now.
            self._warned_since = {name: self._warned_since.get(name, now) for name in warned}
            doc = {
                "version": STATE_VERSION,
                "retailers": {
                    name: {"refusals": st.refusals, "refused_at": st.refused_at}
                    for name, st in self._state.items()
                    if st.refusals
                },
                "warned": self._warned_since,
            }
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(doc, indent=2, sort_keys=True))
        except Exception:
            log.exception(
                "could not write the pacer state to %s — the backoff still works "
                "in memory, but it will not survive a restart",
                self.state_path,
            )
