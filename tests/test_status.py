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
from pathlib import Path

import pytest

from boty.cli import _report
from boty.models import Availability, Health, Result, Rung, Watch
from boty.status import write


def _result(
    *,
    rung: Rung | None = None,
    control: bool = False,
    availability: Availability = Availability.IN_STOCK,
) -> Result:
    watch = Watch(
        name="goplusplus",
        retailer="bestbuy",
        target="6577129",
        control=control,
    )
    if rung is None:
        return Result(watch, availability, price=54.99, detail="synthetic")
    return Result(watch, availability, price=54.99, detail="synthetic", rung=rung)


def _payload(tmp_path: Path, results: list[Result]) -> dict:
    path = tmp_path / "status.json"
    write(path, results, [Health("bestbuy", ok=True)])
    return json.loads(path.read_text())


# --------------------------------------------------------------------------
# The served payload
# --------------------------------------------------------------------------


def test_every_watch_entry_carries_a_rung_and_a_degraded_flag(tmp_path: Path) -> None:
    payload = _payload(tmp_path, [_result(), _result(rung=Rung.BROWSER)])

    assert len(payload["watches"]) == 2
    for entry in payload["watches"]:
        assert isinstance(entry["rung"], str)
        assert isinstance(entry["degraded"], bool)


def test_a_browser_reading_serialises_as_degraded(tmp_path: Path) -> None:
    (entry,) = _payload(tmp_path, [_result(rung=Rung.BROWSER)])["watches"]

    assert entry["rung"] == "browser"
    assert entry["degraded"] is True


def test_a_default_reading_serialises_as_tls_and_not_degraded(tmp_path: Path) -> None:
    (entry,) = _payload(tmp_path, [_result()])["watches"]

    assert entry["rung"] == "tls"
    assert entry["degraded"] is False


def test_an_api_reading_serialises_as_api_and_not_degraded(tmp_path: Path) -> None:
    """The rung is published even when it does not imply degradation.

    D-01 drops the flag on the API path, but the support matrix still has to
    be able to say Best Buy was reached at rung 2 rather than rung 1.
    """
    (entry,) = _payload(tmp_path, [_result(rung=Rung.API)])["watches"]

    assert entry["rung"] == "api"
    assert entry["degraded"] is False


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


def test_report_does_not_tag_a_plain_reading(capsys: pytest.CaptureFixture[str]) -> None:
    out = _tags(capsys, _result())

    assert "[degraded]" not in out
    assert "[control]" not in out


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
