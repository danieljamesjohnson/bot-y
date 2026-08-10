"""REQ-15: no alert names a cause the code did not establish.

ONE REQUIREMENT OVER TWO MODULES, WHICH IS WHY IT HAS ITS OWN FILE.
-------------------------------------------------------------------
`boty/monitor.py` composes the sentence and `boty/notify.py` puts a title on it,
and REQ-15 is a claim about what *reaches a person* — so it is a property of the
pair, not of either one. Filing the scan under `test_monitor.py` would leave the
title untested by the thing that tests the body; filing it under a
`test_notify.py` would put a scan of `monitor.py` in a module named after the
other file. Both halves of one requirement belong in one place, the way
`test_dashboard.py` holds one surface.

WHY THIS IS AN `ast` SCAN AND NOT A `grep`, WHICH MATTERS MORE THAN IT SOUNDS.
-----------------------------------------------------------------------------
The claim under test is an ABSENCE, and the naive gate for it is
self-invalidating in this repository specifically:

- `boty/monitor.py` carries a comment quoting *"the detector is probably
  broken"* verbatim, as history. That comment is the argument for the
  withdrawal, so it must stay.
- The same file's module docstring and the arms' comments quote all three
  withdrawn sentences, because house style here is that a reversed position gets
  its reversal argued in place.
- `boty/monitor.py` already records a previous acceptance criterion that greps
  this same file, and had to be written around it.

A comment-filtered `grep -c` would pass today and rot on the next comment.
`ast.parse` does not see comments at all — they are not in the tree — and
docstrings are excluded here by NODE IDENTITY rather than by matching their text,
so the scan checks precisely the thing it claims to check: strings that can reach
a user. `ast` is stdlib; nothing is installed for this.

f-strings are `JoinedStr` nodes whose literal parts are ordinary `Constant`
children, so `notify.py`'s interpolated title is caught by the same walk. That is
asserted directly below, because it is the one withdrawn string that is not a
plain literal and a walk that missed it would pass vacuously.

THE POSITIVE HALF IS HERE TOO, and it is not decoration: a gate that only checks
for absence can be satisfied by deleting every explanation. `CAUSE_UNKNOWN` is
asserted to be carried by exactly the two arms whose cause is genuinely unknown,
and by neither of the two whose cause was measured.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from boty import monitor, notify
from boty.models import Availability, Health, Result, Watch

#: Sentences that were sent to a person and named a cause nobody had measured.
#: Each entry is short and CONTIGUOUS AS IT APPEARS IN SOURCE, deliberately: the
#: live detector sentence is split across two adjacent string literals
#: (`"...the detector is "` and `"probably broken, so real restocks..."`), so a
#: gate looking for the full rendered phrase would match nothing and pass
#: vacuously — a gate that cannot go red. `probably broken` is the fragment that
#: actually bites.
WITHDRAWN = (
    # 2026-08-04, the refusal arm. Amazon and GameStop had been refusing us for
    # a day; the alert said we were asking too often. Falsified twice: after
    # backing off to a 6-hour interval the very next single request was still
    # refused. The code established a REFUSAL, never a RATE.
    "we are asking too often",
    # 2026-08-04, the same arm's other half. A refusal means the extractor was
    # never reached, so the reading establishes nothing about the detector in
    # EITHER direction — "probably fine" is as unmeasured as "probably broken".
    "probably fine",
    # 2026-08-04, the breakage arm, and the sentence that cost 20 pages in 24
    # hours for two retailers whose detectors were fine.
    "probably broken",
    # The hardcoded notification title, which asserted a problem with the
    # detector over a body that might be saying the detector was never reached —
    # on the one surface a phone actually shows.
    "detector problem",
)

#: Exactly two modules. The scan is scoped, not global, because REQ-15 is about
#: text that reaches a PERSON: `monitor.py` composes `Health.reason` and
#: `notify.py` composes the title and the body. `retailers.py` also produces
#: prose a person reads — `Result.detail` — but it is out of scope here on
#: purpose: those strings are gated by the behavioural tests that assert their
#: content in `tests/test_retailers.py`, and widening this scan to every module
#: would make it a spell-checker rather than a gate on one requirement.
SCANNED = (monitor, notify)


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """The id() of every node that IS a docstring, so it can be skipped exactly.

    By identity rather than by value: a module that legitimately used the same
    sentence twice, once as a docstring and once as an alert, would otherwise be
    let through by a value-based filter.
    """
    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    found: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, holders):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            found.add(id(first.value))
    return found


def _user_facing_strings(module: object) -> list[str]:
    """Every string constant in the module that is not a docstring."""
    source = Path(module.__file__).read_text()  # type: ignore[attr-defined]
    tree = ast.parse(source)
    skip = _docstring_nodes(tree)
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in skip
    ]


# --------------------------------------------------------------------------
# The absence — no alert names a cause the code did not establish
# --------------------------------------------------------------------------


@pytest.mark.parametrize("module", SCANNED, ids=lambda m: m.__name__)
def test_no_withdrawn_claim_survives_in_any_reachable_string(module: object) -> None:
    """The gate REQ-15 exists for."""
    offenders = [
        (fragment, text)
        for text in _user_facing_strings(module)
        for fragment in WITHDRAWN
        if fragment in text
    ]

    assert not offenders, (
        f"{module.__name__} still carries {len(offenders)} withdrawn claim(s):\n"  # type: ignore[attr-defined]
        + "\n".join(f"  {frag!r} in {text!r}" for frag, text in offenders)
    )


def test_the_scan_sees_inside_f_strings() -> None:
    """The one withdrawn string that was never a plain literal.

    `notify.py`'s title was an f-string. An `ast` walk that only collected
    top-level `Constant` nodes and not the `Constant` children of a `JoinedStr`
    would have passed over it and reported a clean file — the vacuous pass this
    whole module is written to avoid.
    """
    strings = _user_facing_strings(notify)

    assert any("retailer(s)" in s for s in strings), (
        "the scan did not reach the literal parts of the title's f-string, so a "
        "withdrawn claim could sit in it and this gate would never see it"
    )


def test_the_gate_can_go_red() -> None:
    """A gate on an absence must be shown to be capable of failing.

    The suite watched the real thing go red against the pre-edit text — the
    transcript is in `05-02-SUMMARY.md`. This keeps that property alive after the
    text was fixed: the matcher, applied to a string that DOES contain a
    withdrawn fragment, finds it.
    """
    assert any(fragment in "the detector is probably broken" for fragment in WITHDRAWN)
    assert any(fragment in "bot-y: detector problem (2 retailer(s))" for fragment in WITHDRAWN)
    assert not any(fragment in "the cause is not established" for fragment in WITHDRAWN)


# --------------------------------------------------------------------------
# The positive half — where the cause IS unknown, the alert says so
# --------------------------------------------------------------------------


def _control(
    availability: Availability,
    *,
    retailer: str = "gamestop",
    refused: bool = False,
    store_id: str | None = None,
    store: str | None = None,
) -> Result:
    watch = Watch(
        name="ctl",
        retailer=retailer,
        target=f"https://{retailer}.test/p",
        control=True,
        store_id=store_id,
    )
    return Result(watch, availability, detail="synthetic", refused=refused, store=store)


def test_exactly_the_two_unknown_causes_say_so() -> None:
    """The partition, across all four arms of `assess_health`.

    Two of these failures have a cause the code measured and two do not, and the
    difference has to survive an edit. Without this half, deleting every
    explanation would satisfy the absence gate above perfectly.
    """
    (no_control,) = monitor.assess_health(
        [Result(Watch(name="p", retailer="target", target="https://t/1"), Availability.OUT_OF_STOCK)]
    )
    (refusal,) = monitor.assess_health([_control(Availability.UNKNOWN, refused=True)])
    (breakage,) = monitor.assess_health([_control(Availability.OUT_OF_STOCK)])
    (store_gap,) = monitor.assess_health(
        [_control(Availability.UNKNOWN, retailer="walmart", store_id=None)]
    )

    carries = {
        "no control": monitor.CAUSE_UNKNOWN in no_control.reason,
        "refusal": monitor.CAUSE_UNKNOWN in refusal.reason,
        "breakage": monitor.CAUSE_UNKNOWN in breakage.reason,
        "store gap": monitor.CAUSE_UNKNOWN in store_gap.reason,
    }

    assert carries == {
        "no control": False,
        "refusal": True,
        "breakage": True,
        "store gap": False,
    }, (
        "the partition moved. A cause we measured must not be reported as "
        "unknown, and a cause we did not must not be reported as anything else"
    )


def test_cause_unknown_is_one_constant_with_one_spelling() -> None:
    """Three paraphrases would drift, which is how the withdrawn sentences got
    to be wrong in the first place — and a property stated three ways cannot be
    checked mechanically at all."""
    reasons = [
        monitor.assess_health([_control(Availability.UNKNOWN, refused=True)])[0].reason,
        monitor.assess_health([_control(Availability.OUT_OF_STOCK)])[0].reason,
    ]

    assert all(r.count(monitor.CAUSE_UNKNOWN) == 1 for r in reasons)
    assert monitor.CAUSE_UNKNOWN.strip() == monitor.CAUSE_UNKNOWN


# --------------------------------------------------------------------------
# notify.py composes no diagnosis of its own
# --------------------------------------------------------------------------


class _Recorder:
    def __init__(self) -> None:
        self.title = ""
        self.body = ""

    def notify(self, title: str, body: str) -> bool:
        self.title = title
        self.body = body
        return True


def test_the_title_states_the_measured_state_and_names_no_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The one surface a phone actually shows.

    `apprise` is never imported: `_client` is replaced wholesale, so this runs
    with no notification dependency installed at all.
    """
    recorder = _Recorder()
    monkeypatch.setattr(notify, "_client", lambda urls: recorder)

    sent = notify.send_health_warning(
        ["ntfy://example"],
        [Health("walmart", ok=False, reason="something measured", failing_controls=["milk: unknown"])],
    )

    assert sent is True
    for fragment in WITHDRAWN:
        assert fragment not in recorder.title
    assert "1" in recorder.title, "the count is measured, so it stays"


def test_the_body_is_exactly_the_reason_and_the_failing_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`notify.py` emits `h.reason` verbatim and composes nothing itself.

    That is the property that keeps REQ-15 checkable in ONE place: if this module
    started writing its own sentences, the gate on `assess_health`'s four arms
    would stop being a gate on what a person reads.
    """
    recorder = _Recorder()
    monkeypatch.setattr(notify, "_client", lambda urls: recorder)
    health = Health(
        "walmart",
        ok=False,
        reason="a reason composed elsewhere",
        failing_controls=["milk: unknown (detail)", "eggs: unknown (detail)"],
    )

    notify.send_health_warning(["ntfy://example"], health and [health])

    assert recorder.body == (
        "[walmart] a reason composed elsewhere\n"
        "  • milk: unknown (detail)\n"
        "  • eggs: unknown (detail)"
    )


def test_an_empty_send_is_still_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """The return contract, unchanged: `cli.watch_cycle` rolls back its
    once-per-episode `warned` memory on a False, so a sender that stopped
    returning the delivery result would turn a retry into a drop."""
    monkeypatch.setattr(notify, "_client", lambda urls: _Recorder())

    assert notify.send_health_warning([], [Health("walmart", ok=False)]) is False
    assert notify.send_health_warning(["ntfy://example"], []) is False
