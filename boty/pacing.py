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
an exponential penalty loses, and it is capped because a monitor that has
backed off to once a day has quietly stopped being a monitor — at the cap it
keeps trying, and the health report keeps saying it is refused, which is a
state somebody should eventually see rather than one that disappears.

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
import time
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

#: Multiplier applied per consecutive refusal.
BACKOFF_FACTOR = 2.0

#: Never wait longer than this between attempts, however many refusals. Six
#: hours is long enough to outlast a rate-limit window and short enough that a
#: retailer coming back is noticed the same day.
MAX_BACKOFF_SECONDS = 6 * 60 * 60

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
STATE_VERSION = 2

#: Persisted state older than this is discarded rather than applied. DERIVED
#: from `MAX_BACKOFF_SECONDS` rather than re-chosen, so the two cannot drift
#: apart — the same argument `Result.degraded` makes about deriving rather than
#: storing. The cap already IS this project's written answer to how long a
#: refusal stays evidence ("long enough to outlast a rate-limit window and short
#: enough that a retailer coming back is noticed the same day"), so a record
#: older than one full cap-length window has outlived the reasoning that
#: produced it. This is half the answer to the stale-file objection quoted at
#: the top of this file; the other half is that `due_at` is never persisted.
STATE_MAX_AGE_SECONDS = MAX_BACKOFF_SECONDS

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
#: says what it needs to. It must also stay comfortably above
#: `cli.REFUSALS_BEFORE_PAGING`, or persistence would silently defeat the paging
#: clause it exists to serve. That relationship is asserted by a test rather
#: than by this comment, because this module must not import `boty.cli` — the
#: dependency runs the other way.
MAX_PERSISTED_REFUSALS = 64


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
    state_path: Path | None = None

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
            self._state[retailer] = _RetailerState(interval=self._standing_interval(retailer))
        return self._state[retailer]

    def due(self, retailer: str, now: float) -> bool:
        """True when this retailer may be asked again.

        The half-interval tolerance matters: the loop sleeps `interval` with
        its own jitter, so a retailer running at the DEFAULT cadence would
        otherwise be skipped roughly half the time purely because the sleep
        came up 3% short. This class exists to stretch intervals BEYOND the
        loop's, never to drop cycles from a retailer that is keeping to it.
        """
        return now + self.default_interval * 0.5 >= self._for(retailer).due_at

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
        st.due_at = now + wait

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
        return max(
            st.interval,
            min(
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
        mins = max(0.0, st.due_at - now) / 60
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
                # BOTH bounds. Past the cap the record has outlived its
                # reasoning; a stamp in the FUTURE is a clock that jumped
                # backwards, and with only an upper bound it would hold the
                # state for as long as the skew lasted.
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
        # the cap the record has outlived what produced it, and a stamp in the
        # FUTURE is a clock that jumped backwards.
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
