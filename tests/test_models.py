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
"""

from __future__ import annotations

from boty.models import Availability, Result, Rung, Watch
from boty.monitor import assess_health


def _result(
    availability: Availability,
    *,
    price: float | None = None,
    max_price: float | None = None,
    rung: Rung | None = None,
    control: bool = False,
) -> Result:
    watch = Watch(
        name="goplusplus",
        retailer="walmart",
        target="https://walmart.example/1",
        max_price=max_price,
        control=control,
    )
    # `rung` is omitted rather than passed-with-a-default when the caller does
    # not ask for one, because half the point of the field is that every
    # pre-existing construction site — which names no rung at all — keeps its
    # meaning. A helper that always passed it would test a call shape nothing
    # in `boty` actually uses.
    if rung is None:
        return Result(watch, availability, price=price, detail="synthetic")
    return Result(watch, availability, price=price, detail="synthetic", rung=rung)


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
