"""Config loading.

Adding a product is editing a YAML file. That is the whole bar, and it is
the main thing that makes bot-y different from the tools it replaces —
streetmerchant, for instance, requires editing two TypeScript union types,
a per-series price map, and a store file to add a single SKU.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .models import Watch

log = logging.getLogger(__name__)

_ENV_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")

#: Floor for the polling interval, in seconds. "Polite polling, never
#: sub-minute" is a stated non-functional requirement, and it is also
#: self-protective: hammering a retailer is what gets an IP blocked, and a
#: blocked IP takes every detector down at once.
MIN_INTERVAL_SECONDS = 60


def _sub(match: re.Match[str]) -> str:
    """Substitute one ${VAR}, saying so when it is not set.

    Silently expanding a missing variable to "" is how a monitor ends up with
    no notifier at all — `notify: [${BOTY_NOTIFY_URL}]` becomes `[""]`, which
    the filter below drops to `[]`, and then `watch` polls forever and tells
    nobody. Not an error, because an unset ${BESTBUY_API_KEY} is a legitimate
    state, but it must be visible.

    The name is logged and the value never is: these hold bot tokens and API
    keys, and a log line is not a mode-600 file.
    """
    name = match.group(1)
    if name not in os.environ:
        log.warning("config references ${%s}, which is not set — substituting empty", name)
    return os.environ.get(name, "")


def _expand(value: Any) -> Any:
    """Expand ${VAR} from the environment so secrets stay out of the file."""
    if isinstance(value, str):
        return _ENV_RE.sub(_sub, value)
    if isinstance(value, list):
        return [_expand(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    return value


def _price(value: Any, where: str) -> float | None:
    """Coerce a configured ceiling to a float, or refuse the file.

    `target` was coerced with `str()` and this was not, so YAML's perfectly
    reasonable reading of `max_price: "80"` as a string survived all the way to
    `Result.alertable`, where `float <= str` raises TypeError. In `boty check`
    that kills the command; in `boty watch` the loop's handler catches it, so
    the service stays up while every cycle aborts, the status page freezes at
    whatever it last held, and no notification is ever sent.
    """
    if value is None:
        return None
    if isinstance(value, bool):  # bool is an int subclass; `max_price: true` is a typo
        raise ValueError(f"{where}: max_price must be a number, got {value!r}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{where}: max_price must be a number, got {value!r}") from exc


def _store_id(value: Any, where: str) -> str | None:
    """Coerce a configured store pin to a string, or refuse the file.

    Built in `_price`'s shape — same `where` parameter, same call-site form —
    because it is the same class of value read out of the same document, and a
    second idiom here would be a second place to get the bool case wrong.

    Branch by branch:

    - `None` in, `None` out. An ABSENT pin is a legitimate state and must not
      raise. See the load-vs-refuse paragraph below; this is the whole reason
      this function is not just `str(value)`.
    - A `bool` raises, naming the watch. `bool` is an `int` subclass, so
      `store_id: true` — an entirely plausible typo, exactly as `max_price: true`
      is — would otherwise coerce to the perfectly plausible pin `"True"` and
      never match anything, silently, forever. `_price`'s precedent, followed
      rather than re-argued.
    - Anything else becomes `str(value).strip()`, and an empty result becomes
      `None`. The `str()` coercion is `_price`'s own documented bug one field
      over: YAML reads an unquoted store number as an `int`, and an `int`
      compared against the string Walmart puts in its own JSON is a silent
      never-match — no exception, no log line, just a pin that can never agree.

    WHY AN ABSENCE LOADS AND A TYPO REFUSES. This module has both idioms and
    picking the wrong one takes the daemon down: `_price` and `_interval` refuse
    the whole file, while `_sub` logs and continues because "an unset
    ${BESTBUY_API_KEY} is a legitimate state, but it must be visible". A store
    pin needs the second. Refusing would crash `boty watch` — five healthy
    retailers taken down over one Walmart watch — and the phase criterion for an
    unpinned store is UNKNOWN *plus a health message*, which requires a daemon
    still running to deliver it. So the absence is carried as DATA on the
    `Watch`, not only as a log line, because `assess_health` has to be able to
    read it and say so.

    HOW THE REAL STORE NUMBER REACHES THE DAEMON — decided here, not left open.
    `config/products.yaml` ships `store_id: ${WALMART_STORE_ID}` on both Walmart
    watches, and the real value lives in the mode-600 `EnvironmentFile` the
    systemd unit already loads, outside this repo. `_expand`/`_sub` run over the
    whole document before any `Watch` is built, so the mechanism already exists
    and an unset variable already logs its own name without failing the load.

    Why not the obvious alternatives:

    - *A literal store number in the tracked file.* That is the leak class
      itself. A store number is a geolocator — it resolves publicly to one
      street address — and `3bd1663` force-rewrote 170 commits of this repo's
      history to remove exactly this class. `config/products.yaml` is tracked
      and public.
    - *A second, untracked overlay config.* Invents a mechanism where `${VAR}`
      substitution already exists and already argues this exact case.

    The property that makes the choice safe rather than merely convenient: an
    unset variable degrades to empty, which is unpinned, which is UNKNOWN — the
    behaviour REQ-14 asks for anyway.
    """
    if value is None:
        return None
    if isinstance(value, bool):  # bool is an int subclass; `store_id: true` is a typo
        raise ValueError(f"{where}: store_id must be a store number, got {value!r}")
    return str(value).strip() or None


def _interval(settings: dict[str, Any]) -> int:
    value = settings.get("interval_seconds", 300)
    try:
        interval = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"interval_seconds must be a whole number of seconds, got {value!r}") from exc
    if interval < MIN_INTERVAL_SECONDS:
        raise ValueError(
            f"interval_seconds must be >= {MIN_INTERVAL_SECONDS} (polite polling), got {interval}"
        )
    return interval


def _retailer_intervals(settings: dict[str, object]) -> dict[str, int]:
    """Parse `retailer_intervals:` — a mapping of retailer to seconds.

    Held to the same floor as the global interval. A per-retailer override is
    for asking LESS often; letting it undercut the floor would turn a politeness
    setting into its opposite, one typo at a time.
    """
    raw = settings.get("retailer_intervals") or {}
    if not isinstance(raw, dict):
        raise ValueError(f"retailer_intervals must be a mapping, got {type(raw).__name__}")
    out: dict[str, int] = {}
    for retailer, value in raw.items():
        try:
            seconds = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"retailer_intervals[{retailer!r}] must be a whole number of seconds, got {value!r}"
            ) from exc
        if seconds < MIN_INTERVAL_SECONDS:
            raise ValueError(
                f"retailer_intervals[{retailer!r}] must be >= {MIN_INTERVAL_SECONDS} "
                f"(polite polling), got {seconds}"
            )
        out[str(retailer)] = seconds
    return out


@dataclass
class Config:
    watches: list[Watch]
    notify_urls: list[str] = field(default_factory=list)
    bestbuy_api_key: str = ""
    first_party_only: bool = True
    interval_seconds: int = 300
    #: Per-retailer overrides, e.g. {"amazon": 1800}. A retailer with real bot
    #: protection and several watches costs far more requests per day than the
    #: global cadence suggests, and 2026-08-04 established that Amazon and
    #: GameStop both refuse us at 300 s while answering fine at a lower rate.
    retailer_intervals: dict[str, int] = field(default_factory=dict)
    state_path: Path = Path("state.json")
    #: Snapshot for the dashboard. Written every cycle; served as a static file.
    status_path: Path = Path("served/boty/status.json")
    #: Where `boty.pacing.Pacer` remembers its backoff across a restart: how many
    #: times each retailer has refused in a row, and which retailers have already
    #: been paged about their current failure.
    #:
    #: NAMED FOR THE OBJECT THAT OWNS IT even though the document holds two
    #: things, because ROADMAP criterion 6 names `Pacer._state` in as many words
    #: and one slightly-narrow name beats two names for two keys in one file.
    #:
    #: NOT folded into `state.json`, and that was considered. That file's
    #: document is `State.seen` in its entirety — `monitor.State.load` parses the
    #: whole thing as the map — so a second top-level key there is a schema
    #: change with a migration behind it. Worse, `run_once` saves it BEFORE
    #: delivery is attempted, on purpose, which is exactly the wrong moment to
    #: commit a paging memory whose entire job is to be rolled back when a
    #: delivery fails.
    pacer_state_path: Path = Path("pacer-state.json")

    @classmethod
    def load(cls, path: str | Path) -> Config:
        raw = _expand(yaml.safe_load(Path(path).read_text()) or {})
        settings = raw.get("settings") or {}

        watches: list[Watch] = []
        for entry in raw.get("watches") or []:
            watches.append(
                Watch(
                    name=entry["name"],
                    retailer=entry["retailer"],
                    target=str(entry["target"]),
                    max_price=_price(entry.get("max_price"), f"watch {entry.get('name')!r}"),
                    control=bool(entry.get("control", False)),
                    store_id=_store_id(entry.get("store_id"), f"watch {entry.get('name')!r}"),
                )
            )

        return cls(
            watches=watches,
            notify_urls=[u for u in (raw.get("notify") or []) if u],
            bestbuy_api_key=settings.get("bestbuy_api_key", ""),
            first_party_only=bool(settings.get("first_party_only", True)),
            interval_seconds=_interval(settings),
            retailer_intervals=_retailer_intervals(settings),
            state_path=Path(settings.get("state_path", "state.json")),
            status_path=Path(settings.get("status_path", "served/boty/status.json")),
            pacer_state_path=Path(settings.get("pacer_state_path", "pacer-state.json")),
        )
