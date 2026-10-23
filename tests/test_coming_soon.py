"""A page whose buy button says "Coming Soon" is not in stock, whatever its ld+json says.

Dan, 2026-10-23, after the daemon pushed a restock for the Zelda 40th Anniversary
Pro Controller at GameStop: *"It's not - it's 'coming soon'"*.

MEASURED THAT MORNING, one rung-1 request at 07:22:33: the page's single
schema.org offer read `InStock`, $99.99, seller GameStop — and its only purchase
control was `<button data-test-id="btn-coming-soon-disabled" ... disabled> Coming
Soon </button>`. The structured data and the button contradicted each other and
the monitor believed the one nobody can click. That is the second half of this
project's core value broken outright: an "in stock" for something you cannot buy.

`data-available="false"` on the availability block is NOT the signal, and that is
measured too: the in-stock PS5 control fixture carries the identical attribute,
because GameStop fills it in client-side. The disabled Coming Soon button appeared
on the controller page and on neither fixture nor a live in-stock page (the Pitch
Black Booster Bundle, read 07:23:12).
"""

from __future__ import annotations

from boty.fixtures import load
from boty.models import Availability, Watch
from boty.retailers import Rung, _verdict_from_html

CONTROLLER = Watch(
    name="Pro Controller",
    retailer="gamestop",
    target="https://www.gamestop.com/x/451609.html",
    max_price=125,
)


def _read(html: str, watch: Watch = CONTROLLER):
    return _verdict_from_html(watch, html, url=watch.target, first_party_only=True, rung=Rung.TLS)


def test_a_coming_soon_page_is_not_in_stock_even_when_its_ld_json_says_so() -> None:
    r = _read(load("gamestop", "zelda-pro-controller-coming-soon"))

    assert r.availability is Availability.OUT_OF_STOCK, (
        f"read {r.availability.value} ({r.detail}) — the page's only buy button is a "
        f"disabled 'Coming Soon', and this is the reading that paged Dan for nothing"
    )
    assert not r.alertable
    assert "coming soon" in r.detail.lower(), "the detail must say why the ld+json was overruled"
    assert r.price == 99.99, "the price is still a real reading and is kept"


def test_an_in_stock_gamestop_page_without_the_button_still_reads_in_stock(gamestop_ps5: str) -> None:
    ps5 = Watch(name="ps5", retailer="gamestop", target="https://www.gamestop.com/x/11108140.html", control=True)
    r = _read(gamestop_ps5, ps5)

    assert r.availability is Availability.IN_STOCK, (
        "the Coming Soon rule fired on a page with no Coming Soon button — it would "
        "turn every GameStop restock into an out-of-stock"
    )
