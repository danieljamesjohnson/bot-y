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
) -> Result:
    watch = Watch(
        name="goplusplus",
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


def _payload(tmp_path: Path, results: list[Result], duration_seconds: object = _OMITTED) -> dict:
    path = tmp_path / "status.json"
    health = [Health("bestbuy", ok=True)]
    if duration_seconds is _OMITTED:
        write(path, results, health)
    else:
        write(path, results, health, duration_seconds=duration_seconds)  # type: ignore[arg-type]
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
