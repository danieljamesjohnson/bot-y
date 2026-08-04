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

Deliberately in-memory. A restart clears the backoff and tries once at full
rate, which is the right trade: the alternative is a persisted penalty
outliving the condition that caused it, and one extra request per restart is
cheaper to reason about than a stale file.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

#: Multiplier applied per consecutive refusal.
BACKOFF_FACTOR = 2.0

#: Never wait longer than this between attempts, however many refusals. Six
#: hours is long enough to outlast a rate-limit window and short enough that a
#: retailer coming back is noticed the same day.
MAX_BACKOFF_SECONDS = 6 * 60 * 60

@dataclass
class _RetailerState:
    interval: float
    refusals: int = 0
    due_at: float = 0.0


@dataclass
class Pacer:
    """Decides which retailers are due this cycle, and how hard to back off.

    `now` is passed in rather than read, so tests can drive a day of cycles
    without sleeping through one.
    """

    default_interval: float
    overrides: dict[str, float] = field(default_factory=dict)
    _state: dict[str, _RetailerState] = field(default_factory=dict, repr=False)

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
