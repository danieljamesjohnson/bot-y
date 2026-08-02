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
"""

from __future__ import annotations

from boty.models import Availability, Result, Watch


def _result(
    availability: Availability,
    *,
    price: float | None = None,
    max_price: float | None = None,
) -> Result:
    watch = Watch(
        name="goplusplus",
        retailer="walmart",
        target="https://walmart.example/1",
        max_price=max_price,
    )
    return Result(watch, availability, price=price, detail="synthetic")


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
