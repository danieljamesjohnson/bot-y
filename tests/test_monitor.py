"""Detector health, and edge-triggered alerting with a memory that survives UNKNOWN.

Both behaviours here exist because of the same failure: a monitor that looks
healthy while being broken.

`assess_health` refuses to call a retailer healthy on the strength of its
product watches alone. Only a control — an item known to be in stock — can say
the detector still works, and a retailer with no control is reported unhealthy
rather than assumed fine.

`State.transitioned_to_stock` is edge-triggered, and UNKNOWN never overwrites
what it remembers. One blocked fetch resetting the memory would produce a
duplicate alert on the next successful check, and an alert stream you learn to
distrust is worse than no alert stream.

No fixtures needed — these are hand-built Results.
"""

from __future__ import annotations

from pathlib import Path

from boty.models import Availability, Result, Watch
from boty.monitor import CAUSE_UNKNOWN, State, assess_health, run_once


def _result(
    availability: Availability,
    *,
    retailer: str = "gamestop",
    name: str = "thing",
    control: bool = False,
    price: float | None = None,
    max_price: float | None = None,
) -> Result:
    watch = Watch(
        name=name,
        retailer=retailer,
        target=f"https://{retailer}.example/{name}",
        max_price=max_price,
        control=control,
    )
    return Result(watch, availability, price=price, detail="synthetic")


def _health_for(results: list[Result], retailer: str):
    (found,) = [h for h in assess_health(results) if h.retailer == retailer]
    return found


# --------------------------------------------------------------------------
# assess_health
# --------------------------------------------------------------------------


def test_control_in_stock_is_healthy() -> None:
    results = [
        _result(Availability.OUT_OF_STOCK, name="goplusplus"),
        _result(Availability.IN_STOCK, name="ps5", control=True),
    ]
    assert _health_for(results, "gamestop").ok is True


def test_control_out_of_stock_means_the_detector_is_broken() -> None:
    """The detector-broken alarm.

    A control is an item that is always in stock. If it reads OUT_OF_STOCK the
    honest conclusion is not "the retailer sold out of milk" — it is "we can no
    longer read this site", and every product verdict alongside it is suspect.
    """
    results = [
        _result(Availability.OUT_OF_STOCK, name="goplusplus"),
        _result(Availability.OUT_OF_STOCK, name="ps5", control=True),
    ]
    health = _health_for(results, "gamestop")

    assert health.ok is False
    assert health.failing_controls
    assert "ps5" in health.failing_controls[0]


def test_control_unknown_is_also_unhealthy() -> None:
    """UNKNOWN on a control is just as disqualifying as a wrong answer."""
    results = [_result(Availability.UNKNOWN, name="ps5", control=True)]
    health = _health_for(results, "gamestop")

    assert health.ok is False
    assert health.failing_controls


def test_retailer_with_no_control_watch_is_unhealthy() -> None:
    """An unverified detector is treated as broken, deliberately.

    Nothing is known to be wrong — but nothing is known at all, and "we have
    never checked" must not read the same as "we checked and it was fine".
    """
    results = [
        _result(Availability.OUT_OF_STOCK, retailer="target", name="goplusplus"),
        _result(Availability.IN_STOCK, retailer="target", name="something-else"),
    ]
    health = _health_for(results, "target")

    assert health.ok is False
    assert "control" in health.reason
    assert health.failing_controls == []


def test_health_is_reported_per_retailer() -> None:
    results = [
        _result(Availability.IN_STOCK, retailer="gamestop", name="ps5", control=True),
        _result(Availability.OUT_OF_STOCK, retailer="walmart", name="milk", control=True),
    ]
    health = {h.retailer: h.ok for h in assess_health(results)}

    assert health == {"gamestop": True, "walmart": False}


# --------------------------------------------------------------------------
# The four arms — which one fires for which input, and what each may claim
# --------------------------------------------------------------------------
#
# REQ-15. Two of these failures have a cause the code measured and two do not,
# and every arm is only allowed to say what its own inputs establish.
#
# Store values in this file come from the redaction vocabulary — `"0"` and
# `"00000"` — because `scripts/identity_check.py` scans every tracked file and a
# real store number resolves publicly to one street address.


def _control(
    availability: Availability,
    *,
    retailer: str = "gamestop",
    name: str = "ctl",
    refused: bool = False,
    store_id: str | None = None,
    store: str | None = None,
) -> Result:
    watch = Watch(
        name=name,
        retailer=retailer,
        target=f"https://{retailer}.example/{name}",
        control=True,
        store_id=store_id,
    )
    return Result(watch, availability, detail="synthetic", refused=refused, store=store)


def test_a_refusal_names_the_refusal_and_claims_nothing_else() -> None:
    """What the code established is that a page did not come back.

    It did NOT establish a rate — that sentence kept firing after backing off to
    a 6-hour interval had been observed not to help — and it establishes nothing
    about the detector in either direction, because a refusal means the extractor
    was never reached.
    """
    (health,) = assess_health([_control(Availability.UNKNOWN, refused=True)])

    assert health.ok is False
    assert health.refused is True
    assert "refus" in health.reason, "the measured fact has to be named"
    assert CAUSE_UNKNOWN in health.reason
    for withdrawn in ("we are asking too often", "probably fine", "probably broken"):
        assert withdrawn not in health.reason
    assert "no action is needed" not in health.reason, (
        "`assess_health` takes a list of Results and cannot see a Pacer, so it "
        "cannot know what action is needed — and `cli.watch_cycle` only pages a "
        "refusal once it is entrenched, which is exactly when that advice is false"
    )


def test_a_broken_control_names_the_measurement_and_says_the_cause_is_unknown() -> None:
    """A control did not read IN_STOCK, and it was not a refusal. Whether the
    cause is the extractor, the retailer's markup, or the control itself having
    genuinely sold out is NOT established — so the arm states the measurement and
    then says so."""
    (health,) = assess_health([_control(Availability.OUT_OF_STOCK)])

    assert health.ok is False
    assert health.refused is False
    assert "IN_STOCK" in health.reason
    assert CAUSE_UNKNOWN in health.reason
    assert "probably broken" not in health.reason


def test_an_unpinned_store_is_the_one_failure_whose_cause_was_measured() -> None:
    """The store arm, and the reason it must NOT carry CAUSE_UNKNOWN.

    Saying "the cause is not established" about a gap we can name is the same
    class of dishonesty as the withdrawn sentences, pointed the other way.
    """
    (health,) = assess_health(
        [_control(Availability.UNKNOWN, retailer="walmart", store_id=None)]
    )

    assert health.ok is False
    assert health.refused is False
    assert "store_id" in health.reason
    assert CAUSE_UNKNOWN not in health.reason


def test_a_mismatched_store_reaches_the_same_arm() -> None:
    """Pinned, but the page answered for somebody else's store."""
    (health,) = assess_health(
        [_control(Availability.UNKNOWN, retailer="walmart", store_id="0", store="00000")]
    )

    assert health.ok is False
    assert "store_id" in health.reason
    assert CAUSE_UNKNOWN not in health.reason


def test_the_no_control_arm_is_unchanged_and_claims_no_unknown_cause() -> None:
    """Its cause was measured too: there is no control configured, and the file
    that would configure one is the whole of the diagnosis."""
    (health,) = assess_health([_result(Availability.OUT_OF_STOCK, retailer="target")])

    assert health.reason == "no control watch configured"
    assert CAUSE_UNKNOWN not in health.reason


def test_a_refusal_is_never_attributed_to_the_store_pin() -> None:
    """Precedence, and the reason for it.

    This control is refused AND unpinned — both predicates match. A refusal means
    no page came back, so the store could not have been established either;
    reporting it as a store gap would be naming a cause we did not measure, which
    is the defect this whole plan closes.
    """
    (health,) = assess_health(
        [_control(Availability.UNKNOWN, retailer="walmart", refused=True, store_id=None)]
    )

    assert health.refused is True
    assert CAUSE_UNKNOWN in health.reason
    assert "store_id" not in health.reason


def test_a_store_gap_beside_a_plain_breakage_is_reported_as_breakage() -> None:
    """`all`, not `any` — the existing rule, applied to the new arm.

    If even one control failed for a reason that is neither a refusal nor a store
    gap, something may really be wrong, and the louder reading is the safe one.
    """
    results = [
        _control(Availability.UNKNOWN, retailer="walmart", name="a", store_id=None),
        _control(Availability.OUT_OF_STOCK, retailer="walmart", name="b", store_id="0", store="0"),
    ]
    (health,) = assess_health(results)

    assert health.refused is False
    assert CAUSE_UNKNOWN in health.reason, "the group's cause is not established"
    assert len(health.failing_controls) == 2


def test_a_refusal_beside_a_store_gap_falls_to_the_louder_arm() -> None:
    """The other mixed group, and it is not a refusal report.

    `refused` stays True only when EVERY broken control is a refusal, so this
    group is not the refusal arm's. It is not the store arm's either — a refusal
    is not a store gap, on the precedence above — so it lands on the breakage arm,
    which is the reading that claims least about a mixed group.
    """
    results = [
        _control(Availability.UNKNOWN, retailer="walmart", name="a", refused=True, store_id="0"),
        _control(Availability.UNKNOWN, retailer="walmart", name="b", store_id=None),
    ]
    (health,) = assess_health(results)

    assert health.refused is False
    assert CAUSE_UNKNOWN in health.reason


def test_a_page_that_never_arrived_is_not_reported_as_a_store_pin_gap() -> None:
    """The other no-page outcome, and it is not a refusal.

    `is_refusal` is True only for `Blocked` and statuses {401, 403, 429}. A
    connection timeout, a DNS failure, a TLS error, an HTTP 500 or 502 all
    produce NO PAGE AT ALL and return `refused=False, store=None` — which
    satisfied `c.store != c.watch.store_id` and sent the operator to check a
    `store_id` that is set correctly, in a file that is not the problem.

    That is REQ-15's own defect ("no alert names a cause the code has not
    established") rebuilt inside the arm that was added to serve REQ-15.
    `_is_store_gap`'s docstring already carried the right argument for refusals —
    "a refusal means no page came back, so the store could not have been
    established either" — it just did not extend it to the rest of the no-page
    outcomes.

    Where the cause is genuinely unknown the alert must SAY so, so this asserts
    `CAUSE_UNKNOWN` as well as the absence: an arm that met this test by going
    silent would fail REQ-15's second clause instead of its first.
    """
    (health,) = assess_health(
        [
            _control(
                Availability.UNKNOWN,
                retailer="walmart",
                store_id="0",
                store=None,
            )
        ]
    )

    assert health.ok is False
    assert health.refused is False
    assert "store_id" not in health.reason, (
        "a fetch that produced no page was reported as a store-pin config gap. "
        "Nothing here measured a store, and the pin is set."
    )
    assert CAUSE_UNKNOWN in health.reason


def test_a_reshaped_page_that_names_no_store_is_not_a_store_pin_gap_either() -> None:
    """The same predicate reached from the other side, and it is not the same bug.

    A Walmart page that parses fine but stops emitting
    `product.location.storeIds` also lands on `store=None` with the pin set. The
    honest reading is "the page shape changed", which is exactly the thing the
    code cannot distinguish from three others — so it is the breakage arm's, and
    the breakage arm says the cause is not established.

    Listed separately from the timeout above because the two arrive through
    different code (`FetchError` versus a successful parse) and a fix that only
    covered one of them would look identical from outside.
    """
    reshaped = _control(
        Availability.OUT_OF_STOCK,
        retailer="walmart",
        store_id="00000",
        store=None,
    )
    (health,) = assess_health([reshaped])

    assert "store_id" not in health.reason
    assert CAUSE_UNKNOWN in health.reason


def test_the_store_arm_still_fires_on_the_two_states_that_were_measured() -> None:
    """The positive half, so the fix above cannot pass by disabling the arm.

    Only two states are genuinely measured: nobody pinned a store, or a store
    ANSWERED and it was the wrong one. Both must still reach the arm that names
    `store_id`, and neither may claim the cause is unknown.
    """
    for description, control in (
        ("unpinned", _control(Availability.UNKNOWN, retailer="walmart", store_id=None)),
        (
            "answered for another store",
            _control(Availability.UNKNOWN, retailer="walmart", store_id="0", store="00000"),
        ),
    ):
        (health,) = assess_health([control])
        assert "store_id" in health.reason, f"{description}: the measured arm stopped firing"
        assert CAUSE_UNKNOWN not in health.reason, f"{description}: a measured cause claimed to be unknown"


def test_an_unpinned_watch_is_a_store_gap_whatever_came_back() -> None:
    """`store_id is None` is measured from CONFIG, not from the page.

    So it stays true regardless of what the fetch produced — including the
    no-page outcomes above. The narrowing applies only to the mismatch half.
    """
    (health,) = assess_health(
        [_control(Availability.UNKNOWN, retailer="walmart", store_id=None, store=None)]
    )

    assert "store_id" in health.reason


def test_a_healthy_store_scoped_control_is_untouched_by_the_new_arm() -> None:
    """The store arm reads only BROKEN controls. A Walmart control reading
    IN_STOCK is healthy whatever its pin says — the guards in `retailers.py`
    already made it impossible for an unpinned reading to be IN_STOCK at all."""
    (health,) = assess_health(
        [_control(Availability.IN_STOCK, retailer="walmart", store_id=None)]
    )

    assert health.ok is True
    assert health.reason == ""


# --------------------------------------------------------------------------
# State — edge-triggered alerting
# --------------------------------------------------------------------------


def test_first_in_stock_sighting_transitions(tmp_path: Path) -> None:
    state = State.load(tmp_path / "state.json")
    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is True


def test_second_consecutive_in_stock_does_not_transition(tmp_path: Path) -> None:
    """Alerts are edge-triggered, not level-triggered.

    You want to be told when something *becomes* available, not once a minute
    for as long as it stays available.
    """
    state = State.load(tmp_path / "state.json")
    first = _result(Availability.IN_STOCK)

    assert state.transitioned_to_stock(first) is True
    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is False


def test_out_of_stock_then_in_stock_transitions_again(tmp_path: Path) -> None:
    state = State.load(tmp_path / "state.json")

    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is True
    assert state.transitioned_to_stock(_result(Availability.OUT_OF_STOCK)) is False
    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is True


def test_unknown_does_not_overwrite_remembered_state(tmp_path: Path) -> None:
    """A blocked fetch must not cause a spurious re-alert on recovery.

    IN_STOCK, then UNKNOWN, then IN_STOCK again is one continuous in-stock
    period interrupted by a failed check. If UNKNOWN cleared the memory, the
    third reading would look like a fresh restock and fire a duplicate alert —
    and duplicate alerts are how you learn to ignore the notifications.
    """
    state = State.load(tmp_path / "state.json")

    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is True
    assert state.transitioned_to_stock(_result(Availability.UNKNOWN)) is False
    assert state.seen["gamestop:thing"] == Availability.IN_STOCK.value
    assert state.transitioned_to_stock(_result(Availability.IN_STOCK)) is False


def test_state_survives_a_save_and_reload(tmp_path: Path) -> None:
    """The memory has to outlive the process — the monitor runs as a service."""
    path = tmp_path / "nested" / "state.json"
    state = State.load(path)
    state.transitioned_to_stock(_result(Availability.IN_STOCK))
    state.save()

    assert State.load(path).transitioned_to_stock(_result(Availability.IN_STOCK)) is False


def test_unreadable_state_file_starts_empty(tmp_path: Path) -> None:
    """A corrupt state file must not crash the service on boot."""
    path = tmp_path / "state.json"
    path.write_text("{ not json")

    assert State.load(path).seen == {}


# --------------------------------------------------------------------------
# run_once — the pieces wired together
# --------------------------------------------------------------------------


def test_run_once_alerts_on_products_only_and_records_controls(tmp_path: Path) -> None:
    """Controls are canaries, not shopping list items — they never alert.

    Their state is still recorded, so that flipping a watch from control to
    product later does not fire a phantom "restock".
    """
    product = Watch(name="goplusplus", retailer="gamestop", target="https://x/1")
    control = Watch(name="ps5", retailer="gamestop", target="https://x/2", control=True)

    def checker(watch: Watch) -> Result:
        return Result(watch, Availability.IN_STOCK, price=54.99, detail="synthetic")

    state = State.load(tmp_path / "state.json")
    results, health, alerts = run_once([product, control], checker, state)

    assert len(results) == 2
    assert [h.ok for h in health] == [True]
    assert [a.watch.name for a in alerts] == ["goplusplus"]
    assert state.seen["gamestop:ps5"] == Availability.IN_STOCK.value

    # Second pass: nothing changed, so nothing alerts.
    _, _, alerts_again = run_once([product, control], checker, state)
    assert alerts_again == []


def test_run_once_does_not_alert_above_the_price_ceiling(tmp_path: Path) -> None:
    watch = Watch(name="goplusplus", retailer="walmart", target="https://x/1", max_price=80)

    def checker(w: Watch) -> Result:
        return Result(w, Availability.IN_STOCK, price=229.99, detail="reseller")

    state = State.load(tmp_path / "state.json")
    _, _, alerts = run_once([watch], checker, state)

    assert alerts == []


def test_run_once_records_state_for_every_result_not_just_alertable_ones(
    tmp_path: Path,
) -> None:
    """`alertable` decides what we NOTIFY, never what we REMEMBER.

    The memory used to be written from inside the `alerts` comprehension, as
    the last term of an `and` chain. Python short-circuits, so a product watch
    reading OUT_OF_STOCK never reached the call and its state was never
    recorded — the remembered value stayed pinned at whatever it last alerted
    on.
    """
    watch = Watch(name="goplusplus", retailer="gamestop", target="https://x/1")

    def checker(w: Watch) -> Result:
        return Result(w, Availability.OUT_OF_STOCK, price=54.99, detail="synthetic")

    state = State.load(tmp_path / "state.json")
    run_once([watch], checker, state)

    assert state.seen == {"gamestop:goplusplus": Availability.OUT_OF_STOCK.value}


def test_run_once_alerts_again_on_the_restock_after_a_sellout(tmp_path: Path) -> None:
    """in_stock -> out_of_stock -> in_stock must alert TWICE, not once.

    This is the failure the whole project exists to prevent, and it is worse
    than a missed alert: after the first alert the watch was silently pinned at
    "in_stock" forever, so EVERY subsequent restock was swallowed while the
    dashboard stayed green. It survived 36 passing tests because no existing
    test ever fed a non-control watch anything but IN_STOCK.
    """
    watch = Watch(name="goplusplus", retailer="gamestop", target="https://x/1", max_price=80)
    state = State.load(tmp_path / "state.json")

    fired: list[int] = []
    for availability in (
        Availability.IN_STOCK,
        Availability.OUT_OF_STOCK,
        Availability.IN_STOCK,
    ):

        # `shipping=0.0` — a positive claim that this offer ships free, so the
        # delivered total is $54.99 and the $80 ceiling passes. The subject
        # here is the restock EDGE, and under REQ-17 a reading with no shipping
        # cost read is not alertable under a ceiling: without this the loop
        # would fire zero alerts and stop saying anything about the edge at all.
        def checker(w: Watch, av: Availability = availability) -> Result:
            return Result(w, av, price=54.99, detail="synthetic", shipping=0.0)

        _, _, alerts = run_once([watch], checker, state)
        fired.append(len(alerts))

    assert fired == [1, 0, 1], (
        "the second restock was swallowed: the out-of-stock reading between "
        "them was never recorded, so the monitor still believed it was in stock"
    )


def test_run_once_records_a_control_exactly_once(tmp_path: Path) -> None:
    """A control's state must be written once per cycle, not twice.

    `transitioned_to_stock` mutates `state.seen` as a side effect, so calling
    it twice for the same result would compare the second call against the
    value the first call just wrote — turning a genuine transition into a
    non-transition. Controls never alert, so that corruption would be invisible
    on a control; it becomes a missed alert the moment a control is promoted to
    a product watch.
    """
    control = Watch(name="ps5", retailer="gamestop", target="https://x/2", control=True)
    state = State.load(tmp_path / "state.json")

    calls: list[str] = []
    real = State.transitioned_to_stock

    def counting(self: State, result: Result) -> bool:
        calls.append(result.watch.key)
        return real(self, result)

    State.transitioned_to_stock = counting  # type: ignore[method-assign]
    try:
        run_once([control], lambda w: Result(w, Availability.IN_STOCK, detail="synthetic"), state)
    finally:
        State.transitioned_to_stock = real  # type: ignore[method-assign]

    assert calls == ["gamestop:ps5"]
