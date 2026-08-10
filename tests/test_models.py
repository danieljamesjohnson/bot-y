"""`Result.alertable` — the last gate before a notification goes out.

Two independent defences stop a flipper's listing becoming an alert: the
first-party seller filter (in `boty.retailers`) and the price ceiling (here).
They are tested separately because they fail separately, and because REQ-02
requires the ceiling to suppress a marketplace listing *on its own*.

The rule this module exists to enforce is the same one `Availability.UNKNOWN`
enforces one layer down: a check that could not be evaluated must not resolve
to the permissive answer. An unreadable availability is UNKNOWN, never
"out of stock"; an unreadable price under a configured ceiling is "I cannot
tell", never "cheap enough".

`Rung` is pinned here too. It answers a different question from `Availability`
— not "is it buyable" but "how did we find out" — and the tests below exist to
keep those two questions from collapsing into one another.

`Extraction` is the second axis, and it is pinned for a third question again:
not "how did we find out" but "what did we read". A rung and an extraction are
independent — Best Buy is browser + structured, Target would be browser + dom,
and a rung-1 DOM adapter is both possible and the most fragile thing anyone
could add here. That last case is why `degraded` is asserted on each axis
separately below rather than only where the two coincide.
"""

from __future__ import annotations

from boty.models import Availability, Extraction, Result, Rung, Watch
from boty.monitor import assess_health


def _result(
    availability: Availability,
    *,
    price: float | None = None,
    max_price: float | None = None,
    rung: Rung | None = None,
    extraction: Extraction | None = None,
    control: bool = False,
) -> Result:
    watch = Watch(
        name="goplusplus",
        retailer="walmart",
        target="https://walmart.example/1",
        max_price=max_price,
        control=control,
    )
    # `rung` and `extraction` are omitted rather than passed-with-a-default
    # when the caller does not ask for one, because half the point of both
    # fields is that every pre-existing construction site — which names
    # neither — keeps its meaning. A helper that always passed them would test
    # a call shape nothing in `boty` actually uses.
    kwargs: dict[str, Rung | Extraction] = {}
    if rung is not None:
        kwargs["rung"] = rung
    if extraction is not None:
        kwargs["extraction"] = extraction
    return Result(watch, availability, price=price, detail="synthetic", **kwargs)


def test_in_stock_under_the_ceiling_is_alertable() -> None:
    assert _result(Availability.IN_STOCK, price=54.99, max_price=80).alertable is True


def test_in_stock_exactly_at_the_ceiling_is_alertable() -> None:
    """The ceiling is inclusive — an $80 cap means "$80 is fine"."""
    assert _result(Availability.IN_STOCK, price=80.0, max_price=80).alertable is True


def test_in_stock_above_the_ceiling_is_not_alertable() -> None:
    assert _result(Availability.IN_STOCK, price=229.99, max_price=80).alertable is False


def test_in_stock_with_no_ceiling_configured_is_alertable() -> None:
    """No `max_price` means the operator asked for any restock at any price."""
    assert _result(Availability.IN_STOCK, price=229.99).alertable is True
    assert _result(Availability.IN_STOCK, price=None).alertable is True


def test_unpriced_in_stock_offer_does_not_pass_the_ceiling() -> None:
    """A ceiling that cannot be evaluated must not authorise an alert.

    Walmart has already reshaped `priceInfo.currentPrice` once — that is why
    `parse._dig` exists — and `nextdata_offers` returns
    `Offer(available=True, price=None, ...)` when the dig misses. If an
    unreadable price counted as "cheap enough", the $229.99 flip listing would
    clear the ceiling silently, and `notify.send_restock` would push it with a
    "price unknown" body: an alert for a reseller's markup, with nothing in it
    to show why. That is exactly the noise that trains you to ignore the
    notifications.
    """
    assert _result(Availability.IN_STOCK, price=None, max_price=80).alertable is False


def test_not_in_stock_is_never_alertable() -> None:
    for availability in (Availability.OUT_OF_STOCK, Availability.UNKNOWN):
        assert _result(availability, price=1.0, max_price=80).alertable is False
        assert _result(availability).alertable is False


# --------------------------------------------------------------------------
# Rung — how the reading was obtained, which is not what the reading says
# --------------------------------------------------------------------------


def test_availability_still_has_exactly_three_members() -> None:
    """Degradation must never become a fourth stock state.

    `monitor.assess_health` and `monitor.transitioned_to_stock` branch on
    `Availability`, and `cli.SYMBOL` is a dict indexed unconditionally — a
    fourth member would be a KeyError in the middle of printing a report. The
    three-state contract is the design; provenance lives beside it, not in it.
    """
    assert [a.value for a in Availability] == ["in_stock", "out_of_stock", "unknown"]


def test_rung_has_one_member_per_reachable_escalation_rung() -> None:
    """Three rungs, because rung 4 ("dropped") produces no readings at all."""
    assert [r.value for r in Rung] == ["tls", "api", "browser"]


def test_a_result_built_without_a_rung_is_tls_and_not_degraded() -> None:
    """The default is what makes this a low-blast-radius change.

    Every existing construction site in `boty.retailers` names no rung, and
    each of them is a plain TLS fetch. If the default were anything else, this
    field would silently relabel the whole codebase.
    """
    r = _result(Availability.IN_STOCK)
    assert r.rung is Rung.TLS
    assert r.degraded is False


def test_a_browser_reading_is_degraded() -> None:
    assert _result(Availability.IN_STOCK, rung=Rung.BROWSER).degraded is True


def test_an_official_api_reading_is_not_degraded() -> None:
    """D-01: the API path is strictly more reliable, so it drops the flag."""
    assert _result(Availability.IN_STOCK, rung=Rung.API).degraded is False


def test_degradation_does_not_suppress_an_alert() -> None:
    """A browser-read restock is still a restock.

    Suppressing alerts on a degraded reading would defeat the point of
    supporting the retailer through a browser at all — the flag exists to
    label confidence, not to withhold the thing you asked to be told about.
    """
    r = _result(Availability.IN_STOCK, price=54.99, max_price=80, rung=Rung.BROWSER)
    assert r.degraded is True
    assert r.alertable is True


def test_a_degraded_control_reading_in_stock_is_still_healthy() -> None:
    """Degradation is not ill health.

    `assess_health` answers "has this detector been verified by a control",
    not "how confident is the transport". If a degraded reading flipped
    `Health.ok`, Best Buy would raise a permanent health warning and the phase
    criterion "five or more retailers with no health warnings" could never be
    met by construction.
    """
    control = _result(Availability.IN_STOCK, rung=Rung.BROWSER, control=True)
    health = assess_health([control])
    assert [(h.retailer, h.ok) for h in health] == [("walmart", True)]


# --------------------------------------------------------------------------
# Extraction — what was read out of the page, which is not how it was fetched
# --------------------------------------------------------------------------


def test_extraction_has_exactly_two_members() -> None:
    """Two, and pinned literally, for the reason `Availability` is pinned.

    A third member would be a new claim about how much a reading is worth, and
    `_undeclared_degraded` in `tests/test_support_matrix.py` plus the
    `EXTRACTIONS` vocabulary in the README both enumerate this set. Adding one
    silently would leave the matrix able to say something the runtime cannot,
    which is the WR-04 shape the whole degraded contract was rebuilt against.
    """
    assert [e.value for e in Extraction] == ["structured", "dom"]


def test_a_result_built_without_either_axis_is_tls_structured_and_not_degraded() -> None:
    """The default is what makes this a low-blast-radius change, twice over.

    Every existing construction site in `boty.retailers` names neither a rung
    nor an extraction, and every one of them is a plain TLS fetch of a
    structured payload. If either default were anything else, these two fields
    would silently relabel the whole codebase.
    """
    r = _result(Availability.IN_STOCK)
    assert r.rung is Rung.TLS
    assert r.extraction is Extraction.STRUCTURED
    assert r.degraded is False


def test_a_dom_reading_on_the_default_transport_is_degraded() -> None:
    """The hole this axis was added to close, asserted directly.

    `degraded` used to be derived from the rung alone. A rung-1 DOM adapter —
    cheap to write, and the most fragile thing anyone could add to this
    codebase — would have shipped looking fully trustworthy on the dashboard,
    in `boty check` and in the support matrix. Nothing about the transport is
    wrong here: the bytes came over impersonated TLS exactly as GameStop's do.
    It is what was read out of them that a reader has to discount.
    """
    r = _result(Availability.IN_STOCK, extraction=Extraction.DOM)
    assert r.rung is Rung.TLS
    assert r.degraded is True


def test_each_axis_degrades_a_reading_on_its_own() -> None:
    """Both disjuncts, proved apart rather than only where they coincide.

    Best Buy's shape is browser + structured: a page we rendered, carrying the
    retailer's own schema.org feed. Target's would be browser + dom: a page we
    rendered, read for its buttons. Both are degraded, for different reasons,
    and a test that only ever exercised the overlap would go on passing if
    either half of the expression were deleted.
    """
    bestbuy_shape = _result(
        Availability.IN_STOCK, rung=Rung.BROWSER, extraction=Extraction.STRUCTURED
    )
    target_shape = _result(Availability.IN_STOCK, rung=Rung.BROWSER, extraction=Extraction.DOM)

    assert bestbuy_shape.degraded is True
    assert target_shape.degraded is True


def test_a_dom_reading_is_still_alertable() -> None:
    """The `rung` invariant, restated for the second axis.

    Withholding the alert would defeat the point of supporting the retailer
    through a DOM read at all — the flag labels confidence, it does not
    suppress the thing you asked to be told about.
    """
    r = _result(
        Availability.IN_STOCK, price=54.99, max_price=80, extraction=Extraction.DOM
    )
    assert r.degraded is True
    assert r.alertable is True


def test_a_dom_control_reading_in_stock_is_still_healthy() -> None:
    """The other `rung` invariant, restated. Degradation is not ill health.

    `assess_health` answers "has this detector been verified by a control",
    not "how confident is the reading". A dom reading that flipped `Health.ok`
    would raise a permanent health warning that is never going to change, and
    the phase criterion "five or more retailers with no health warnings" could
    never be met by construction.
    """
    control = _result(Availability.IN_STOCK, extraction=Extraction.DOM, control=True)
    health = assess_health([control])
    assert [(h.retailer, h.ok) for h in health] == [("walmart", True)]


# --------------------------------------------------------------------------
# The store: `Watch.store_id` (what was pinned) and `Result.store` (what answered)
# --------------------------------------------------------------------------
#
# The values below are `0` and `00000` — this repo's redaction vocabulary — for
# the reason recorded in `tests/test_config.py`: this file is tracked and public,
# and a real store number resolves to one street address.


def test_a_watch_built_without_a_store_pin_is_unpinned() -> None:
    """`store_id` is declared LAST, after `control`, with a default.

    Every pre-existing construction site in this repo names neither, and
    inserting the field ahead of `control` would change the positional
    signature of a frozen dataclass that is constructed positionally in tests.

    `None` here means "nobody pinned a store" — a third state beside "your
    store" and "someone else's store". The default is a DECISION, not an
    omission: CONTEXT rejected defaulting to whatever Walmart assigns, because
    that leaves a reading as a statement about an arbitrary store, which is the
    bug.
    """
    w = Watch(name="thing", retailer="walmart", target="https://walmart.example/1")
    assert w.store_id is None


def test_a_result_built_without_a_store_did_not_learn_one() -> None:
    """`None` is "the page did not tell us which store answered".

    It is never "store 0". `0` is this repo's own redaction placeholder — it is
    in the identity guard's `allowed` vocabulary and it is what `8dec2e0` wrote
    over the store number in both Walmart fixtures — so a default of `0` would
    read off the dashboard as a real store the fixtures use.

    For a non-Walmart retailer `None` is the honest value and always will be:
    no other retailer here publishes a store on its product page.
    """
    r = _result(Availability.IN_STOCK)
    assert r.store is None


def test_the_store_is_carried_on_the_result_and_changes_no_verdict() -> None:
    """Recording a store must not move an `Availability`, and here it does not.

    This is the split the phase was planned around: 05-01 makes the store a fact
    that exists and is published; 05-02 is where an unpinned or mismatched store
    reaches a verdict. A guard here would put two plans inside one branch.
    """
    watch = Watch(
        name="goplusplus",
        retailer="walmart",
        target="https://walmart.example/1",
        max_price=80,
        store_id="0",
    )
    pinned = Result(watch, Availability.IN_STOCK, price=54.99, detail="synthetic", store="0")
    mismatched = Result(
        watch, Availability.IN_STOCK, price=54.99, detail="synthetic", store="00000"
    )

    assert pinned.store == "0"
    assert mismatched.store == "00000"
    # Both still alertable, and both still IN_STOCK. 05-02 changes this; this
    # plan deliberately does not.
    assert pinned.alertable is True
    assert mismatched.alertable is True
    assert mismatched.availability is Availability.IN_STOCK
