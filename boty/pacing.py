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
#: The hedge is worth arguing rather than assuming. `monitor.State` has no
#: version and needs none: its document is a flat map of strings whose meaning
#: cannot drift. This one carries a COUNT whose units are a policy decision —
#: `BACKOFF_FACTOR` and the cap — so a future version that changed either and
#: then restored an old file under the new units would pin a retailer at a wait
#: nobody chose. One integer against that is cheap.
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
#: `record` computes `st.interval * BACKOFF_FACTOR ** st.refusals`, and float
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

    def _for(self, retailer: str) -> _RetailerState:
        if retailer not in self._state:
            self._state[retailer] = _RetailerState(
                interval=self.overrides.get(retailer, self.default_interval)
            )
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
            wait = min(
                st.interval * BACKOFF_FACTOR ** st.refusals,
                MAX_BACKOFF_SECONDS,
            )
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
        return f"paced at {st.interval / 60:.0f} min — next attempt in ~{mins:.0f} min"

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
    # loop builds the pacer and then loads INTO it. A classmethod would invite a
    # second construction site, which is the thing that invariant forbids.
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
        difference is the reason: `status.json` is atomic because it is served
        over HTTP *while* it is being written. This file has exactly one reader,
        once, at startup, in the same process that writes it.

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
