"""What reaches a person: the health warning's cause, and the restock's fields.

REQ-15 is the first half — no alert names a cause the code did not establish —
and it is what this file was built for. The second half arrived on 2026-08-11
with Dan's shipping reversal: `send_restock` renders `price:` and `shipping:` as
two labelled fields, and where nobody read a figure the field says `unknown`
rather than a number. Both halves belong here rather than in two files for the
same reason the module docstring already gives below: this file is scoped to
TEXT THAT REACHES A PERSON, which is a property of `monitor.py` and `notify.py`
together, and the restock body is the one push a person receives when this
project SUCCEEDS. Until 2026-08-11 not one test in this repository asserted
anything about it — every reference under `tests/` was a monkeypatch — so the
surface that carries the good news was the only unguarded one.

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
import json
import re
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


def test_exactly_one_arm_names_something_a_person_can_do() -> None:
    """The 2026-08-12 partition, over the same four arms — and it is the *reason*
    a push is allowed rather than a second description of the same split.

    Dan, twice: *"we need to never hit the user unless its something they can buy
    or actually do"*. `Health.action` is empty by default, so this asserts which
    arms deliberately fill it — and the answer has to stay ONE. Three of these
    end in a fact about a retailer or in `CAUSE_UNKNOWN`, and neither is
    something anybody can act on; the store gap ends in a value the operator
    sets.

    IT IS THE COMPLEMENT OF THE `CAUSE_UNKNOWN` PARTITION ABOVE AND MUST NOT BE
    FOLDED INTO IT. They agree today for a reason — you cannot state a remedy for
    a cause you have not established — but they answer different questions, and
    the no-control arm is the case that proves it: its cause IS established (no
    control is configured) and there is still nothing the person holding the
    phone can do about it. A single test asserting one flag would go on passing
    while the other rule quietly inverted.
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
        "no control": bool(no_control.action),
        "refusal": bool(refusal.action),
        "breakage": bool(breakage.action),
        "store gap": bool(store_gap.action),
    }

    assert carries == {
        "no control": False,
        "refusal": False,
        "breakage": False,
        "store gap": True,
    }, (
        "the partition moved. A state with no remedy must not name one, and the "
        "one state a person can close must not go quiet"
    )
    assert store_gap.action == monitor.STORE_PIN_ACTION
    assert "store_id" in store_gap.action, "the action has to name the thing to set"


def test_a_state_with_nothing_to_do_about_it_is_silent_by_default() -> None:
    """The default itself, asserted on the type rather than on any arm.

    This is what makes the rule survive an arm nobody has written yet: a `Health`
    constructed without an `action` has none, so it cannot page. A blocklist
    would have the opposite default and would need editing every time this file
    grows a branch — which is precisely how the channel filled up twice.
    """
    assert Health("anything", ok=False, reason="a state added in some later year").action == ""


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


def test_the_action_is_rendered_last_and_only_where_there_is_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """What a person is asked to DO is the point of the interruption, so it is on
    the body — and it is still composed elsewhere.

    Two bodies, differing in exactly one field, because both halves matter: an
    action that never reached the phone would make the 2026-08-12 rule pointless
    at the last step, and an empty one leaving a stray arrow would change the
    shape of every body that has nothing to ask for.
    """
    recorder = _Recorder()
    monkeypatch.setattr(notify, "_client", lambda urls: recorder)
    without = Health("walmart", ok=False, reason="a reason composed elsewhere")

    notify.send_health_warning(["ntfy://example"], [without])
    assert recorder.body == "[walmart] a reason composed elsewhere"

    notify.send_health_warning(
        ["ntfy://example"],
        [Health("walmart", ok=False, reason="a reason composed elsewhere", action="do this one thing")],
    )
    assert recorder.body == "[walmart] a reason composed elsewhere\n  → do this one thing"


# --------------------------------------------------------------------------
# The restock body — two fields, the same shape either way
# --------------------------------------------------------------------------
#
# Dan's format, verbatim, 2026-08-11: *"Instead of 'unverified', why don't you
# say price: <price> shipping: <unknown>"*. Two separate fields, the same shape
# whether or not shipping resolved, and NO DELIVERED TOTAL in either case —
# you cannot add a number to `unknown`, so where shipping is unknown nothing is
# claimed, and where it is known both addends are already on the screen. A total
# that appeared in one case and vanished in the other is exactly the
# special-casing this format avoids.


def _restock(
    *,
    price: float | None,
    shipping: float | None,
    name: str = "Pokémon GO Plus +",
    retailer: str = "nintendo",
) -> Result:
    watch = Watch(
        name=name,
        retailer=retailer,
        target=f"https://{retailer}.test/p/1",
        max_price=80,
    )
    return Result(
        watch,
        Availability.IN_STOCK,
        price=price,
        detail="synthetic",
        url=watch.target,
        shipping=shipping,
    )


def _body(monkeypatch: pytest.MonkeyPatch, result: Result) -> str:
    recorder = _Recorder()
    monkeypatch.setattr(notify, "_client", lambda urls: recorder)
    assert notify.send_restock(["ntfy://example"], [result]) is True
    return recorder.body


def test_a_resolved_shipping_cost_is_stated_as_a_figure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GameStop's captured numbers, in Dan's shape."""
    body = _body(monkeypatch, _restock(price=54.99, shipping=6.99))

    assert "price: $54.99   shipping: $6.99" in body


def test_a_shipping_cost_nobody_read_is_a_field_saying_so_and_no_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The whole of the mitigation for a hole Dan chose to reopen.

    His reasoning, verbatim, 2026-08-11: *"I think where we don't know just send
    it. If the user gets there and it's 50 dollar shipping that's disappointing
    but it's worse to feel like you 'missed out'."*

    So this alert goes out, and the ONE thing standing between him and a $45
    surprise is this word. It must not be a `$0.00` — that would state a figure
    nobody measured — and there must be no delivered total anywhere, because
    there is no total: `unknown` is not a number and nothing may be summed with
    it. Mutation M17 rebuilds exactly the collapse this forbids.
    """
    body = _body(monkeypatch, _restock(price=54.99, shipping=None))

    assert "price: $54.99   shipping: unknown" in body
    assert "$0.00" not in body, "a cost nobody read was stated as free"
    assert "61.98" not in body and "total" not in body.lower(), (
        f"a delivered total was stated over an unknown shipping cost:\n{body}"
    )


def test_a_refused_shipping_figure_never_reaches_a_phone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T-06-01, one layer further out than `delivered_total`.

    `-5.0` is a figure `established_shipping` has already refused to trust. The
    naive render reads `r.shipping` directly and prints `$-5.00`; the naive
    ARITHMETIC prints $49.99, below the item price. Neither may leave the
    machine, and `unknown` is the honest word for a figure the code threw away.
    """
    body = _body(monkeypatch, _restock(price=54.99, shipping=-5.0))

    assert "shipping: unknown" in body
    assert "-5" not in body and "$-5.00" not in body
    assert "49.99" not in body


def test_an_unreadable_price_uses_the_same_word_as_an_unreadable_shipping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ONE spelling of "nobody read this", for `CAUSE_UNKNOWN`'s reason.

    Three paraphrases drift, and a property stated three ways cannot be checked
    mechanically at all — which is how the two withdrawn sentences in
    `monitor.py` came to be wrong. Both fields go through one formatter, so they
    cannot diverge in shape either.
    """
    body = _body(monkeypatch, _restock(price=None, shipping=None))

    assert "price: unknown   shipping: unknown" in body
    assert body.count(notify.FIELD_UNKNOWN) == 2


def test_the_two_bodies_have_the_same_shape_and_differ_only_in_the_shipping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dan's "same shape whether or not shipping resolved", made mechanical.

    Asserted rather than described, because "same shape" is precisely the kind
    of claim that survives in a docstring while the code special-cases one
    branch. Both bodies match one expression carrying both labels in order, and
    the diff between them is one field's value.
    """
    resolved = _body(monkeypatch, _restock(price=54.99, shipping=6.99))
    unresolved = _body(monkeypatch, _restock(price=54.99, shipping=None))

    shape = re.compile(r"^price: (\S+)   shipping: (\S+)$", re.MULTILINE)
    assert shape.search(resolved), f"the resolved body lost the shape:\n{resolved}"
    assert shape.search(unresolved), f"the unresolved body lost the shape:\n{unresolved}"

    assert resolved.replace("$6.99", notify.FIELD_UNKNOWN) == unresolved, (
        "the two bodies differ by more than the shipping value — a branch is "
        f"special-cased:\n{resolved}\n---\n{unresolved}"
    )


def test_the_restock_alert_still_names_the_item_and_carries_the_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The unchanged half. The fields are an addition, not a replacement."""
    recorder = _Recorder()
    monkeypatch.setattr(notify, "_client", lambda urls: recorder)
    result = _restock(price=54.99, shipping=None)

    notify.send_restock(["ntfy://example"], [result])

    assert "Pokémon GO Plus +" in recorder.title
    assert "IN STOCK" in recorder.title
    assert "Pokémon GO Plus +" in recorder.body
    assert "nintendo" in recorder.body
    assert result.url in recorder.body


def test_the_restock_body_names_no_cause_either(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """REQ-15 over the surface it was never applied to.

    The `ast` scan above already walks `notify.py` whole, so the new strings are
    inside it by construction. This asserts the RENDERED body too, because a
    field label that is clean in source and a body that is clean on a phone are
    two claims and only one of them is what REQ-15 is about.
    """
    body = _body(monkeypatch, _restock(price=54.99, shipping=None))

    for fragment in WITHDRAWN:
        assert fragment not in body


# --------------------------------------------------------------------------
# The store number is a geolocator, and it must not leave the box
# --------------------------------------------------------------------------


def _walmart_page(*, answering_store: str) -> str:
    """A minimal Walmart hydration payload, shaped like the real fixture.

    Built here rather than imported from `test_retailers.py` so this file keeps
    the property its docstring claims: one requirement, one place.
    """
    doc = {
        "props": {
            "pageProps": {
                "initialData": {
                    "data": {
                        "product": {
                            "location": {"storeIds": [answering_store]},
                            "availabilityStatus": "IN_STOCK",
                            "sellerName": "Walmart.com",
                            "priceInfo": {"currentPrice": {"price": 2.42}},
                        }
                    }
                }
            }
        }
    }
    return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(doc)}</script></html>'


def test_a_store_number_never_reaches_the_notification_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A store number resolves publicly to one street address.

    `3bd1663` force-rewrote 170 commits of this repo's history to remove exactly
    that class of value, `config/products.yaml` refuses to hold one even as a
    commented example, and `_store_id`'s docstring calls it a geolocator. And
    then the mismatch guard's `detail` — which interpolates BOTH the answering
    store and the pinned one — was copied verbatim into `failing_controls` and
    joined into the push body, over a transport whose documented options include
    `ntfy://<topic>`, world-readable unless auth is configured.

    Measured 2026-08-10 against the tree BEFORE the redaction existed: the body
    read `this watch pins store '<the operator's store>'`. The mismatch arm is
    the 2026-08-09 incident this phase was built around, so it is the arm most
    likely to fire.

    THE DETAIL IS COMPOSED BY THE REAL GUARD, not typed out here, so this test
    cannot pass by agreeing with a string nobody produces. The values are this
    repo's redaction vocabulary (`0`, `00000`) and neither is a real store.

    What is redacted is the NUMBER, not the fact: the alert still says a store
    disagreed, which is the actionable half. Which store is read off the
    dashboard, which is ours.
    """
    from boty import retailers
    from boty.models import Rung

    pinned, answered = "00000", "0"
    watch = Watch(
        name="milk",
        retailer="walmart",
        target="https://walmart.example/ip/1",
        control=True,
        store_id=pinned,
    )
    result = retailers._verdict_from_html(
        watch,
        _walmart_page(answering_store=answered),
        url=watch.target,
        first_party_only=True,
        rung=Rung.TLS,
    )
    assert result.availability is Availability.UNKNOWN, "the guard did not fire; nothing is under test"
    assert pinned in result.detail, (
        "`Result.detail` no longer names the pinned store. It is supposed to — "
        "the terminal and the gitignored status.json are ours. The cut is at the "
        "notification boundary."
    )

    (health,) = monitor.assess_health([result])
    recorder = _Recorder()
    monkeypatch.setattr(notify, "_client", lambda urls: recorder)

    notify.send_health_warning(["ntfy://example"], [health])

    assert pinned not in recorder.body, (
        f"the operator's pinned store left the machine in the push body:\n{recorder.body}"
    )
    assert "store '" not in recorder.body and 'store "' not in recorder.body, (
        f"a quoted store number survived the redaction:\n{recorder.body}"
    )
    assert "<redacted>" in recorder.body, "the redaction did not run at all"
    assert "pins store" in recorder.body, "the alert stopped saying a store disagreed"


def test_the_redaction_leaves_a_reason_that_carries_no_store_alone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`h.reason` goes through the same filter as `failing_controls`.

    Asserted separately because they are two joins in `send_health_warning` and
    a fix applied to one of them looks exactly like a fix applied to both.
    """
    recorder = _Recorder()
    monkeypatch.setattr(notify, "_client", lambda urls: recorder)

    notify.send_health_warning(
        ["ntfy://example"],
        [Health("walmart", ok=False, reason="the page named store '00000'", failing_controls=[])],
    )

    assert "00000" not in recorder.body, f"only the control list was redacted:\n{recorder.body}"


def test_an_empty_send_is_still_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """The return contract, unchanged: `cli.watch_cycle` rolls back its
    once-per-episode `warned` memory on a False, so a sender that stopped
    returning the delivery result would turn a retry into a drop."""
    monkeypatch.setattr(notify, "_client", lambda urls: _Recorder())

    assert notify.send_health_warning([], [Health("walmart", ok=False)]) is False
    assert notify.send_health_warning(["ntfy://example"], []) is False
