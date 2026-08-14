"""What gets published, and what gets printed.

`boty.status.write` is the only thing that produces `served/boty/status.json`,
and that file is served over HTTP through the Mission Control proxy. Its keys
are therefore public API: the dashboard reads them, and Phase 2's support
matrix reads them to say which escalation rung each retailer landed on. A key
that silently stops being written is a dashboard that silently stops saying
anything — which is the same shape of failure as a detector that reports
out-of-stock forever.

`cli._report` is the other consumer of the same two fields. It is tested here
alongside the payload because they answer one question — "how much is this
reading worth" — in two places, and the answer must not diverge.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from boty.cli import _report
from boty.models import Availability, Extraction, Health, Result, Rung, Watch
from boty.status import write

#: "this argument was not passed at all", which is a different thing from
#: passing None. The unmeasured path has to be reachable through the helper
#: exactly as every pre-existing caller reaches it — by omission.
#:
#: DECLARED ABOVE `_result` SINCE REQ-21, and only because Python needs a
#: default's name to exist when the `def` runs. `_result` now takes `read_at`
#: through the same sentinel for the same reason `_payload` takes
#: `duration_seconds` through it: "nobody stamped this reading" is the case
#: under test, and passing `None` explicitly is a different call shape from the
#: one every arm in `boty/retailers.py` that read nothing actually makes.
_OMITTED = object()


def _result(
    *,
    rung: Rung | None = None,
    extraction: Extraction | None = None,
    control: bool = False,
    availability: Availability = Availability.IN_STOCK,
    store: str | None = None,
    store_pinned: str | None = None,
    read_at: object = _OMITTED,
    name: str = "goplusplus",
) -> Result:
    watch = Watch(
        name=name,
        retailer="bestbuy",
        target="6577129",
        control=control,
        store_id=store_pinned,
    )
    kwargs: dict[str, Rung | Extraction | float] = {}
    if rung is not None:
        kwargs["rung"] = rung
    if extraction is not None:
        kwargs["extraction"] = extraction
    if read_at is not _OMITTED:
        kwargs["read_at"] = read_at  # type: ignore[assignment]
    return Result(watch, availability, price=54.99, detail="synthetic", store=store, **kwargs)


def _payload(
    tmp_path: Path,
    results: list[Result],
    duration_seconds: object = _OMITTED,
    intervals: object = _OMITTED,
    watches: object = _OMITTED,
    remembered: object = _OMITTED,
) -> dict:
    path = tmp_path / "status.json"
    health = [Health("bestbuy", ok=True)]
    # Built by omission for the reason `_OMITTED` exists at all: "this argument
    # was not passed" is a different call shape from "this argument was passed
    # None", and both are cases under test.
    #
    # `watches` and `remembered` join it under REQ-21 for a sharper version of
    # the same reason: the no-`watches` call is not a degraded mode to be
    # simulated with `None` — it is the shape every caller in this file and in
    # `tests/test_pacing.py` used before 07-04, and the assertion that it still
    # produces the pre-07-04 payload is only about the real path if it reaches
    # the real path.
    kwargs: dict[str, object] = {}
    if duration_seconds is not _OMITTED:
        kwargs["duration_seconds"] = duration_seconds
    if intervals is not _OMITTED:
        kwargs["intervals"] = intervals
    if watches is not _OMITTED:
        kwargs["watches"] = watches
    if remembered is not _OMITTED:
        kwargs["remembered"] = remembered
    write(path, results, health, **kwargs)  # type: ignore[arg-type]
    return json.loads(path.read_text())


# --------------------------------------------------------------------------
# The served payload
# --------------------------------------------------------------------------


def test_every_watch_entry_carries_a_rung_an_extraction_and_a_degraded_flag(
    tmp_path: Path,
) -> None:
    payload = _payload(tmp_path, [_result(), _result(rung=Rung.BROWSER)])

    assert len(payload["watches"]) == 2
    for entry in payload["watches"]:
        assert isinstance(entry["rung"], str)
        assert isinstance(entry["extraction"], str)
        assert isinstance(entry["degraded"], bool)


def test_a_browser_reading_serialises_as_degraded(tmp_path: Path) -> None:
    (entry,) = _payload(tmp_path, [_result(rung=Rung.BROWSER)])["watches"]

    assert entry["rung"] == "browser"
    assert entry["degraded"] is True


def test_a_default_reading_serialises_as_tls_structured_and_not_degraded(
    tmp_path: Path,
) -> None:
    (entry,) = _payload(tmp_path, [_result()])["watches"]

    assert entry["rung"] == "tls"
    assert entry["extraction"] == "structured"
    assert entry["degraded"] is False


def test_a_dom_reading_serialises_as_dom_and_degraded(tmp_path: Path) -> None:
    """The second axis, published — and published as degraded on its own.

    The transport here is the default one. Nothing about `rung` says to
    discount this reading, so if the dashboard read only `rung` it would
    render a DOM read of a retailer's buttons identically to GameStop's
    schema.org feed. `extraction` is what lets a reader tell them apart, and
    `degraded` is what makes them look different without having to.
    """
    (entry,) = _payload(tmp_path, [_result(extraction=Extraction.DOM)])["watches"]

    assert entry["rung"] == "tls"
    assert entry["extraction"] == "dom"
    assert entry["degraded"] is True


def test_an_api_reading_serialises_as_api_and_not_degraded(tmp_path: Path) -> None:
    """The rung is published even when it does not imply degradation.

    D-01 drops the flag on the API path, but the support matrix still has to
    be able to say Best Buy was reached at rung 2 rather than rung 1.
    """
    (entry,) = _payload(tmp_path, [_result(rung=Rung.API)])["watches"]

    assert entry["rung"] == "api"
    assert entry["degraded"] is False


# --------------------------------------------------------------------------
# REQ-08: how long the pass took
# --------------------------------------------------------------------------


def test_a_measured_pass_publishes_its_duration(tmp_path: Path) -> None:
    """REQ-08 gives a two-minute budget, so the number has to be readable.

    Before this key existed the only figure anybody had was a hand-timed 40 s
    in a plan summary. A budget nobody can read after the fact is a budget
    asserted rather than measured.
    """
    payload = _payload(tmp_path, [_result()], duration_seconds=41.7)

    assert payload["duration_seconds"] == 41.7


def test_an_unmeasured_pass_publishes_null_rather_than_zero(tmp_path: Path) -> None:
    """`None` means "nobody timed this pass", which is not "it took no time".

    The same three-valued honesty `Availability` is built on, applied to a
    number: a missing measurement that serialised as `0` would read off the
    dashboard as the fastest check ever recorded.
    """
    payload = _payload(tmp_path, [_result()])

    assert "duration_seconds" in payload, "the key must always be present, even unmeasured"
    assert payload["duration_seconds"] is None


def test_publishing_a_duration_does_not_disturb_any_existing_key(tmp_path: Path) -> None:
    """This file is a contract with the dashboard. Adding to it is additive.

    `served/boty/index.html` reads these keys verbatim and `tests/test_dashboard.py`
    pins the consuming end, so a reordered or renamed key here is a page that
    silently stops saying anything.
    """
    measured = _payload(tmp_path, [_result(rung=Rung.BROWSER)], duration_seconds=1.5)
    unmeasured = _payload(tmp_path, [_result(rung=Rung.BROWSER)])

    for payload in (measured, unmeasured):
        assert set(payload) == {"updated", "healthy", "retailers", "watches", "duration_seconds"}
        (entry,) = payload["watches"]
        assert set(entry) == {
            "name",
            "retailer",
            "availability",
            "price",
            "detail",
            "url",
            "control",
            "alertable",
            "rung",
            "extraction",
            "degraded",
            "store",
            "store_pinned",
            # REQ-21, added 2026-08-13. This assertion going red when the key
            # landed is Finding 10 working exactly as intended, not a
            # regression — and it is ENUMERATED rather than relaxed to a subset
            # check, because a `<=` here would stop noticing the next key
            # entirely. Appended last so no existing key moves.
            "read_at",
            # REQ-21, added 2026-08-14, and enumerated for the same reason one
            # line up — the third time this assertion has gone red on purpose in
            # this phase. WHICH provenance this row has is the whole of what
            # this key says: `true` here because this row came from a `Result`,
            # i.e. somebody read a page this cycle. The remembered rows that
            # carry `false` are asserted in the section below.
            "checked",
        }
        assert entry["rung"] == "browser"
        assert entry["degraded"] is True
        assert payload["healthy"] is True
        # Additive, deliberately. `refused` and `checked` were added 2026-08-04
        # because "ok: false" had been carrying three different meanings —
        # the detector is broken, the retailer is refusing us, and we did not
        # ask this cycle. The dashboard cannot distinguish them from `ok`
        # alone, and the first two produced 20 false pages in 24 hours.
        assert payload["retailers"] == [
            {
                "retailer": "bestbuy",
                "ok": True,
                "refused": False,
                "checked": True,
                "reason": "",
                "failing_controls": [],
                # REQ-21, added 2026-08-13, and ENUMERATED rather than the
                # assertion being relaxed to a subset — this row is pinned as a
                # whole dict on purpose, harder than the watch row above, and a
                # `<=` here would stop noticing the next key entirely. `None`
                # because this caller passes no `intervals`: the cadence is not
                # established on this surface, which is a different fact from a
                # cadence of zero. Appended last so no existing key moves.
                "current_interval_seconds": None,
            }
        ]


# --------------------------------------------------------------------------
# REQ-21: when the reading was taken, published per watch
# --------------------------------------------------------------------------
#
# Criterion 1's second half. `Result.read_at` exists at the source; this is where
# it becomes readable by the dashboard, by `boty check` and by anything else
# reading the file.
#
# THE ASSERTIONS BELOW READ THE BYTES BACK, not the dict that produced them.
# `null` versus `0` is a question about what `json.dumps` wrote, and asserting
# on the payload dict before it was serialised would answer a different one.


def test_an_unstamped_reading_publishes_null_rather_than_zero(tmp_path: Path) -> None:
    """A reading nobody dated is `null` — not `0`, not `""`, and never absent.

    Both wrong values are available and they lie in opposite directions. `0`
    renders as 1 January 1970, i.e. MAXIMALLY STALE, which is the
    `store`-published-as-`0` mistake one direction over — that one invents a
    real store, this one invents a real (and terrible) age. Omitting the key
    instead would leave the dashboard's own consumer to invent a default, which
    is the same failure delegated.
    """
    payload = _payload(tmp_path, [_result()])
    (entry,) = payload["watches"]

    assert "read_at" in entry, "the key must always be present, even unstamped"
    assert entry["read_at"] is None
    # Not falsiness: `0` is falsy and `0` is precisely the value this must never
    # take. Asserted against the serialised text as well, because `null` and `0`
    # are the same truthiness and different bytes.
    raw = (tmp_path / "status.json").read_text()
    assert '"read_at": null' in raw
    assert '"read_at": 0' not in raw


def test_a_stamped_reading_round_trips_its_moment(tmp_path: Path) -> None:
    """The float survives the file. A stamp that does not survive is not a stamp.

    Constructed as `time.time() - 172800` rather than taken, so nothing here
    depends on a clock this test controls — the phase's standing rule.
    """
    stamp = time.time() - 172800

    payload = _payload(tmp_path, [_result(read_at=stamp)])
    (entry,) = payload["watches"]

    assert entry["read_at"] == stamp
    assert isinstance(entry["read_at"], float)


def test_the_row_stamp_is_not_the_file_stamp(tmp_path: Path) -> None:
    """`updated` and `read_at` answer different questions, and this is the split.

    The top-level `updated` is when the CYCLE ran. It is computed once per
    `write` call, outside the row comprehension, and it is FRESH even when every
    row beneath it is two days old — which is exactly the reading this project
    gave when asked how old the Amazon and Walmart GO Plus + readings were. So a
    two-day-old row under a `updated` written this second is the state REQ-21
    exists to make visible, and it must be REPRESENTABLE rather than collapsed.
    """
    stamp = time.time() - 172800

    payload = _payload(tmp_path, [_result(read_at=stamp)])
    (entry,) = payload["watches"]

    assert payload["updated"] >= stamp + 172000, "`updated` is this cycle, not the reading"
    assert entry["read_at"] == stamp
    assert entry["read_at"] != payload["updated"]


# --------------------------------------------------------------------------
# REQ-21: the cadence each retailer is CURRENTLY on, published per retailer
# --------------------------------------------------------------------------
#
# Criterion 3's threshold. A reading is stale when it is older than its
# retailer's own current interval, so the page needs that interval to compare
# against — and it is the BACKED-OFF one, not the operator's standing
# `interval_seconds`. Measured on this host 2026-08-13: four of six retailers
# were on a cadence different from their configured one, by factors of up to 72.
#
# PER RETAILER, NOT PER WATCH, and the retailers array is where the per-retailer
# facts already live. A copy on each of fourteen watch rows is thirteen more
# copies that can drift out of step.
#
# The assertions read the BYTES back for the same reason the `read_at` section
# above does: `null` versus `0` is a question about what `json.dumps` wrote.


def test_the_current_cadence_is_published_for_a_checked_retailer(tmp_path: Path) -> None:
    """The number the dashboard, `boty check` and the daemon all judge against.

    21 600 rather than a standing 300 because that is the state this key exists
    to make visible: target and walmart sat at seven refusals on this host, i.e.
    on the six-hour cap, while `config/products.yaml` still said 300.
    """
    payload = _payload(tmp_path, [_result()], intervals={"bestbuy": 21600.0})
    (row,) = payload["retailers"]

    assert row["current_interval_seconds"] == 21600.0
    assert isinstance(row["current_interval_seconds"], float)


def test_the_current_cadence_is_published_for_a_paced_out_retailer_too(tmp_path: Path) -> None:
    """The PACED branch of the array, which is the row that actually matters.

    A retailer deep in a backoff is skipped, so it is published from the second
    comprehension rather than from `health` — and it is precisely the retailer
    whose readings are oldest and whose staleness question is live. A key
    published on only the checked branch would be absent from every row a reader
    most needs it on.
    """
    path = tmp_path / "status.json"
    write(
        path,
        [],
        [],
        paced={"walmart": "backing off after 7 refusal(s) — next attempt in ~53 min"},
        intervals={"walmart": 21600.0},
    )
    (row,) = json.loads(path.read_text())["retailers"]

    assert row["checked"] is False, "this is the paced branch, not the checked one"
    assert row["current_interval_seconds"] == 21600.0


def test_a_cadence_nobody_established_publishes_null_rather_than_zero(tmp_path: Path) -> None:
    """`null`, NEVER `0`, and here the argument is sharper than for `store`.

    A cadence published as `0` says *this retailer is checked continuously*, so
    every reading against it is stale the instant it is taken — the most
    confident possible lie about a number nobody established. `null` says the
    cadence is not established on this surface, which is the same three-valued
    honesty the `checked: false` row beside it already carries.
    """
    absent_from_the_map = _payload(tmp_path, [_result()], intervals={"walmart": 300.0})
    (row,) = absent_from_the_map["retailers"]
    assert row["retailer"] == "bestbuy", "the map deliberately does not mention this retailer"
    assert row["current_interval_seconds"] is None

    raw = (tmp_path / "status.json").read_text()
    assert '"current_interval_seconds": null' in raw
    assert '"current_interval_seconds": 0' not in raw


def test_a_write_with_no_intervals_at_all_still_publishes_the_key(tmp_path: Path) -> None:
    """Every pre-existing caller omits the argument and must keep working.

    The key is present and `null`, never absent: omitting it would leave each
    consumer to invent its own default, which is the same failure delegated one
    level out.
    """
    payload = _payload(tmp_path, [_result()])
    (row,) = payload["retailers"]

    assert "current_interval_seconds" in row
    assert row["current_interval_seconds"] is None


# --------------------------------------------------------------------------
# REQ-21: every configured watch has a row, and a remembered row says so
# --------------------------------------------------------------------------
#
# WHAT WAS MEASURED, THREE TIMES, AND IT MOVED EVERY TIME. The live
# `served/boty/status.json` this daemon writes carried 3 watch rows at 08:25:10
# on 2026-08-13, 8 rows at 09:24:54 the same morning, and 5 rows at 07:36:57 on
# 2026-08-14 — from a config that declares 13 watches and did not change between
# any of those readings. The row count is a function of PACING, not of
# configuration, which is a sharper statement of the defect than any one of
# those numbers: a reader who opens the page twice in one morning watches the
# watch list change size with no way to tell a watch that was removed from a
# watch that was not asked.
#
# `status.write` rebuilds `watches` from `results`, and `run_once` filters the
# watches down to those the pacer says are due. So a paced-out watch does not
# leave a STALE row behind — it has no row at all, and a row that is absent
# cannot answer "so they are out of stock as of when?" any better than an
# undated one can.
#
# THE ASSERTIONS READ THE BYTES BACK, for the reason the two sections above
# give: `null` versus a default is a question about what `json.dumps` wrote.


def _watch(name: str, retailer: str, **kw: object) -> Watch:
    """A configured watch, distinct from every other by `retailer:name`.

    Separate from `_result`'s inline `Watch` because this section is about
    watches that produced NO result — the case that helper cannot express.
    """
    return Watch(name=name, retailer=retailer, target=f"https://x/{retailer}/{name}", **kw)  # type: ignore[arg-type]


_FRESH = _watch("fresh", "bestbuy")
_REMEMBERED = _watch("memory", "walmart")
_NEVER = _watch("never", "target")
_THREE = [_FRESH, _REMEMBERED, _NEVER]


def _rows(payload: dict) -> dict[str, dict]:
    return {w["retailer"] + ":" + w["name"]: w for w in payload["watches"]}


def _read_this_cycle() -> Result:
    """A `Result` for `_FRESH` — the one watch of the three that was asked."""
    return Result(_FRESH, Availability.IN_STOCK, price=54.99, detail="synthetic")


def test_every_configured_watch_has_a_row_whether_or_not_it_was_read(
    tmp_path: Path,
) -> None:
    """Three configured, one read, three rows — and provenance on each.

    This is the plan in one assertion. Before today the answer was ONE row, and
    the two watches nobody asked about were indistinguishable from two watches
    that had been deleted from the config.
    """
    payload = _payload(
        tmp_path,
        [_read_this_cycle()],
        watches=_THREE,
        remembered={"walmart:memory": ("out_of_stock", time.time() - 172800)},
    )
    rows = _rows(payload)

    assert set(rows) == {"bestbuy:fresh", "walmart:memory", "target:never"}, (
        "a watch that was not asked has a row that says nobody asked, rather "
        "than no row at all"
    )
    assert rows["bestbuy:fresh"]["checked"] is True
    assert rows["walmart:memory"]["checked"] is False
    assert rows["target:never"]["checked"] is False


def test_a_remembered_row_publishes_the_availability_and_stamp_the_ledger_holds(
    tmp_path: Path,
) -> None:
    """The memory, and its age, off the bytes.

    The stamp is `time.time() - 172800` — REQ-21's own two-day example,
    constructed by subtraction rather than by freezing a clock, which is this
    phase's standing rule and `tests/test_pacing.py:585-591`'s method.
    """
    stamp = time.time() - 172800

    payload = _payload(
        tmp_path,
        [_read_this_cycle()],
        watches=_THREE,
        remembered={"walmart:memory": ("out_of_stock", stamp)},
    )
    row = _rows(payload)["walmart:memory"]

    assert row["availability"] == "out_of_stock"
    assert row["read_at"] == stamp
    assert isinstance(row["read_at"], float)
    assert row["read_at"] != payload["updated"], (
        "the remembered row published THIS cycle's clock instead of the "
        "ledger's stamp, which is the age being manufactured rather than "
        "remembered"
    )


def test_a_watch_the_ledger_never_resolved_publishes_unknown_with_no_age(
    tmp_path: Path,
) -> None:
    """Criterion 2 at this layer: never `now`, never `0`, never omitted.

    Two ways a configured watch reaches this branch and both are live: a fresh
    clone, and a watch every reading of which has been UNKNOWN — which on this
    host is what `WALMART_STORE_ID` being unset does to both Walmart watches.
    """
    payload = _payload(tmp_path, [_read_this_cycle()], watches=_THREE, remembered={})
    row = _rows(payload)["target:never"]

    assert row["availability"] == "unknown"
    assert "read_at" in row, "the key must always be present, even unknown"
    assert row["read_at"] is None
    assert row["read_at"] != payload["updated"]
    # `0` is falsy and `null` is falsy; they are different bytes and only one of
    # them means "nobody established this". `0` reads as 1 January 1970 —
    # maximally stale rather than unknown.
    raw = (tmp_path / "status.json").read_text()
    assert '"read_at": 0' not in raw


def test_a_remembered_row_publishes_null_for_every_fact_about_the_act_of_reading(
    tmp_path: Path,
) -> None:
    """Nobody performed a reading, so nothing about one is published.

    Asserted as a SET over the row rather than key by key, so a later key added
    to the fresh branch cannot quietly acquire a default over here. `detail: ""`
    is a value the fresh path produces and means *the page said nothing worth
    repeating*; `null` never appears on a fresh row, which is the entire reason
    to prefer it — it is distinguishable. And `degraded: false` on a memory
    would be a confidence claim about a reading nobody took, so `rung`,
    `extraction` and their derived flag go out as `null` together.
    """
    payload = _payload(
        tmp_path,
        [_read_this_cycle()],
        watches=_THREE,
        remembered={"walmart:memory": ("out_of_stock", time.time() - 172800)},
    )
    row = _rows(payload)["walmart:memory"]

    about_the_act_of_reading = {"price", "detail", "rung", "extraction", "degraded", "store"}
    assert {k: row[k] for k in about_the_act_of_reading} == dict.fromkeys(
        about_the_act_of_reading
    ), f"a fact nobody measured was published as a default: {row}"


def test_a_remembered_row_refuses_the_authority_a_derived_value_would_grant(
    tmp_path: Path,
) -> None:
    """`alertable` is a stated `False`, on the one fixture where that differs.

    A remembered `in_stock` on a watch with NO `max_price` is exactly the
    configuration under which a derived value is `True` — and the second half of
    this test measures that rather than asserting it, by publishing the same
    watch as a fresh reading and watching `alertable` come back `true`. Any
    other fixture would let M35 survive.

    Measured against this host's ledger on 2026-08-14: 8 of 13 remembered
    entries are `in_stock`, 6 are controls, and the other two are the GameStop
    `TRANSITION —` watches, neither of which carries a `max_price`. So a derived
    value publishes two false buy-signals on every cycle GameStop is paced out,
    and GameStop runs on a 900-second override.
    """
    no_ceiling = _watch("transition", "gamestop")

    remembered_row = _rows(
        _payload(
            tmp_path,
            [_read_this_cycle()],
            watches=[_FRESH, no_ceiling],
            remembered={"gamestop:transition": ("in_stock", time.time() - 172800)},
        )
    )["gamestop:transition"]
    fresh_row = _rows(
        _payload(
            tmp_path,
            [_read_this_cycle(), Result(no_ceiling, Availability.IN_STOCK)],
            watches=[_FRESH, no_ceiling],
            remembered={},
        )
    )["gamestop:transition"]

    assert no_ceiling.max_price is None, "the fixture drifted to a watch with a ceiling"
    assert fresh_row["alertable"] is True, (
        "this fixture no longer distinguishes a stated `alertable` from a "
        "derived one, so it can no longer catch a memory inheriting one"
    )
    assert remembered_row["alertable"] is False, (
        "a reading nobody took was published as worth waking somebody for"
    )


def test_a_remembered_row_publishes_the_config_facts_it_can_know(
    tmp_path: Path,
) -> None:
    """True whether or not anybody looked, so they are published either way.

    Without them the row is a key and two values, and the dashboard cannot
    render it at all: it interpolates `w.url` and `w.name` unconditionally.
    """
    pinned = _watch("pinned", "walmart", control=True, store_id="1234")

    payload = _payload(
        tmp_path,
        [_read_this_cycle()],
        watches=[_FRESH, pinned],
        remembered={"walmart:pinned": ("in_stock", None)},
    )
    row = _rows(payload)["walmart:pinned"]

    assert row["name"] == "pinned"
    assert row["retailer"] == "walmart"
    assert row["url"] == pinned.target
    assert row["control"] is True
    assert row["store_pinned"] == "1234"
    # An availability the ledger holds with no stamp beside it: a remembered
    # reading whose moment was never established. Not `0`, not this cycle.
    assert row["availability"] == "in_stock"
    assert row["read_at"] is None


def test_a_fresh_row_and_a_remembered_row_carry_the_same_keys_in_the_same_order(
    tmp_path: Path,
) -> None:
    """REQ-21's own sentence, converted from a defect into a design property.

    The requirement opens by complaining that a row read four seconds ago and
    one last read two days ago are *byte-identical in shape*. That is now TRUE
    ON PURPOSE and it is the fix rather than the bug — because `checked` and
    `read_at` are the only two fields carrying the difference, and both of them
    say which kind of row this is out loud.
    """
    payload = _payload(
        tmp_path,
        [_read_this_cycle()],
        watches=_THREE,
        remembered={"walmart:memory": ("out_of_stock", time.time() - 172800)},
    )
    rows = _rows(payload)

    fresh = list(rows["bestbuy:fresh"])
    remembered = list(rows["walmart:memory"])
    assert fresh == remembered, (
        f"provenance must live in `checked` and `read_at` and nowhere else; "
        f"fresh={fresh} remembered={remembered}"
    )
    assert list(rows["target:never"]) == fresh


def test_a_write_with_no_watches_at_all_publishes_one_row_per_result(
    tmp_path: Path,
) -> None:
    """The pre-07-04 payload, plus `checked`, reached by OMISSION.

    Every caller in `tests/` and `tests/test_pacing.py:320` still calls `write`
    this way, and they must all keep working. The permissive default is NOT what
    stops that from becoming a production regression — the static AST gate in
    `tests/test_cli_watch.py` asserting both `boty/cli.py` call sites pass both
    keywords is, because a behavioural test cannot see a dropped keyword while
    every other assertion stays green.
    """
    payload = _payload(tmp_path, [_read_this_cycle()])

    (row,) = payload["watches"]
    assert row["name"] == "fresh"
    assert row["checked"] is True


def test_remembered_rows_come_after_every_fresh_row_and_are_ordered_by_key(
    tmp_path: Path,
) -> None:
    """Checked rows first, then the not-checked ones sorted by key.

    The same order `sorted((paced or {}).items())` already gives the retailers
    array one level up in this file, and taken for that reason: the file's own
    established shape is worth more than the cosmetic win of emitting rows in
    config order, which would have meant rewriting the commented fresh-row
    comprehension to get it. The consequence — row order still shifts as pacing
    shifts — is stated rather than hidden.
    """
    payload = _payload(
        tmp_path,
        [_read_this_cycle()],
        # Deliberately NOT in sorted order, so a test that passed by accident of
        # input order would fail here.
        watches=[_NEVER, _REMEMBERED, _FRESH],
        remembered={"walmart:memory": ("out_of_stock", None)},
    )

    keys = [w["retailer"] + ":" + w["name"] for w in payload["watches"]]
    assert keys == ["bestbuy:fresh", "target:never", "walmart:memory"]
    assert [w["checked"] for w in payload["watches"]] == [True, False, False]


# --------------------------------------------------------------------------
# The printed report
# --------------------------------------------------------------------------


def _tags(capsys: pytest.CaptureFixture[str], result: Result) -> str:
    _report([result], [])
    return capsys.readouterr().out


def test_report_tags_a_degraded_reading(capsys: pytest.CaptureFixture[str]) -> None:
    out = _tags(capsys, _result(rung=Rung.BROWSER))

    assert "[degraded]" in out
    assert "[control]" not in out
    assert "[dom]" not in out, "a browser read of a structured feed is not a DOM read"


def test_report_marks_a_dom_reading_visibly(capsys: pytest.CaptureFixture[str]) -> None:
    """`[degraded]` says discount this; `[dom]` says why.

    Two tags rather than one because `degraded` now has two disjuncts, and a
    reader looking at a single line of `boty check` has no other way to tell
    which one fired — "a browser rendered this" and "a reskin will break this
    silently" are different things to plan around.
    """
    out = _tags(capsys, _result(extraction=Extraction.DOM))

    assert "[dom]" in out
    assert "[degraded]" in out


def test_report_does_not_tag_a_plain_reading(capsys: pytest.CaptureFixture[str]) -> None:
    out = _tags(capsys, _result())

    assert "[degraded]" not in out
    assert "[control]" not in out
    assert "[dom]" not in out


def test_report_still_tags_a_control(capsys: pytest.CaptureFixture[str]) -> None:
    out = _tags(capsys, _result(control=True))

    assert "[control]" in out
    assert "[degraded]" not in out


def test_report_shows_both_tags_for_a_degraded_control(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Both facts are true at once and neither may hide the other.

    A browser-read control is exactly what Best Buy's canary will be, and
    "this is the canary" and "this reading is lower confidence" are separate
    things a reader needs.
    """
    out = _tags(capsys, _result(rung=Rung.BROWSER, control=True))

    assert "[control]" in out
    assert "[degraded]" in out


def test_report_does_not_raise_for_any_availability(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`SYMBOL` is indexed unconditionally, so every key must exist.

    This is the concrete reason `Rung` is a separate enum rather than a fourth
    `Availability` member: a missing key here is a KeyError in the middle of
    printing a report, after some of the rows have already been written.
    """
    for availability in Availability:
        _report([_result(availability=availability, rung=Rung.BROWSER)], [])
    assert capsys.readouterr().out.count("[degraded]") == len(list(Availability))


# --------------------------------------------------------------------------
# WHICH STORE — both the one that answered and the one that was pinned
# --------------------------------------------------------------------------
#
# Synthetic store values here are `"0"` and `"00000"`, this repo's redaction
# vocabulary, and the assertions go through a subscript rather than a whole-dict
# literal. Measured 2026-08-10: a four-digit store number written as a JSON
# `store` value inside a tracked test file trips the identity guard, which is
# correct — this file is public and a store number resolves to one street
# address.


def test_both_stores_are_published_because_one_cannot_tell_the_states_apart(
    tmp_path: Path,
) -> None:
    """Two keys, not one, and that is the whole reason this block exists.

    `store` is what answered; `store_pinned` is what was configured. With only
    one of them a reader cannot tell "no store recorded" from "store B answered
    and you pinned A" — and those are exactly the two states this phase exists
    to distinguish. It is the same precedent the `rung`/`extraction`/`degraded`
    block sets one field over: publish the raw fact beside any derived flag,
    because the flag alone cannot say WHY.
    """
    payload = _payload(tmp_path, [_result(store="00000", store_pinned="0")])

    (entry,) = payload["watches"]
    assert entry["store"] == "00000"
    assert entry["store_pinned"] == "0"


def test_a_watch_with_no_store_publishes_null_rather_than_zero(tmp_path: Path) -> None:
    """`null`, never `0` and never `""`.

    `duration_seconds`' argument applies word for word: "a missing measurement
    serialised as 0 would read off the dashboard as the fastest check ever
    recorded". Here it is worse than an analogy — `0` is this repo's redaction
    placeholder and the literal value both Walmart fixtures carry, so an absent
    store published as `0` would read off the dashboard as a real store.
    """
    payload = _payload(tmp_path, [_result()])

    (entry,) = payload["watches"]
    assert entry["store"] is None
    assert entry["store_pinned"] is None
    assert entry["store"] != 0 and entry["store"] != ""


def test_each_store_key_is_published_independently_of_the_other(tmp_path: Path) -> None:
    """The two asymmetric states, which are the interesting ones.

    A page that answered with a store nobody pinned, and a pin whose page said
    nothing. Neither collapses to "no store", and a single key would render both
    as the same row.
    """
    answered_only = _payload(tmp_path, [_result(store="0")])["watches"][0]
    pinned_only = _payload(tmp_path, [_result(store_pinned="0")])["watches"][0]

    assert answered_only["store"] == "0" and answered_only["store_pinned"] is None
    assert pinned_only["store"] is None and pinned_only["store_pinned"] == "0"


# --------------------------------------------------------------------------
# The printed report — the store tag
# --------------------------------------------------------------------------


def test_report_shows_a_matching_store_plainly(capsys: pytest.CaptureFixture[str]) -> None:
    out = _tags(capsys, _result(store="0", store_pinned="0"))

    assert "[store 0]" in out


def test_report_says_when_the_page_answered_and_nothing_was_pinned(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = _tags(capsys, _result(store="0"))

    assert "[store 0, unpinned]" in out


def test_report_says_when_a_pin_exists_and_the_page_did_not_say(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = _tags(capsys, _result(store_pinned="0"))

    assert "[store ?, pinned 0]" in out


def test_report_says_when_the_two_disagree(capsys: pytest.CaptureFixture[str]) -> None:
    """The 2026-08-09 case, on one line of `boty check`.

    The daemon recorded the milk control out of stock at one price while live
    reads minutes later read in stock at another. Same URL, same parser, two
    stores. This tag is what makes that visible without a second reading to
    compare against.
    """
    out = _tags(capsys, _result(store="00000", store_pinned="0"))

    assert "[store 00000 != pinned 0]" in out


def test_report_prints_no_store_tag_for_a_watch_with_neither(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Five retailers here can never produce a store. Their rows must stay clean."""
    out = _tags(capsys, _result())

    assert "store" not in out


def test_the_store_tag_did_not_touch_the_availability_symbols() -> None:
    """`SYMBOL` is indexed unconditionally and must stay three-membered.

    Stated here because the store is the third thing in two phases to arrive
    looking like it might want to be an `Availability` member. It is not: a
    fourth key is a KeyError in the middle of printing a report, and this plan
    changes no availability at all.
    """
    from boty.cli import SYMBOL

    assert set(SYMBOL) == set(Availability)
    assert len(SYMBOL) == 3
