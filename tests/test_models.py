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

import dataclasses
import time

import pytest

from boty.models import (
    Availability,
    Extraction,
    Result,
    Rung,
    Watch,
    established_shipping,
)
from boty.monitor import assess_health


def _result(
    availability: Availability,
    *,
    price: float | None = None,
    max_price: float | None = None,
    rung: Rung | None = None,
    extraction: Extraction | None = None,
    control: bool = False,
    shipping: float | None = None,
    read_at: float | None = None,
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
    #
    # `shipping` follows the same convention for the same reason, and here it
    # is load-bearing rather than tidy: omitting it is what a reading from a
    # retailer that published no shipping cost actually looks like, and that is
    # the case REQ-17 turns into "not alertable".
    kwargs: dict[str, Rung | Extraction | float] = {}
    if rung is not None:
        kwargs["rung"] = rung
    if extraction is not None:
        kwargs["extraction"] = extraction
    if shipping is not None:
        kwargs["shipping"] = shipping
    # `read_at` follows the same convention again, and here omission is the case
    # under test rather than a tidiness: a `Result` nobody stamped is what an
    # arm that read nothing actually constructs, and its age must come out
    # UNKNOWN rather than *now*.
    if read_at is not None:
        kwargs["read_at"] = read_at
    return Result(watch, availability, price=price, detail="synthetic", **kwargs)


def test_in_stock_under_the_ceiling_is_alertable() -> None:
    assert _result(Availability.IN_STOCK, price=54.99, shipping=0.0, max_price=80).alertable is True


def test_in_stock_exactly_at_the_ceiling_is_alertable() -> None:
    """The ceiling is inclusive — an $80 cap means "$80 is fine".

    `shipping=0.0` and not omitted: `0.0` is the positive claim "this offer
    ships free", which is what makes $80.00 the whole of what you would pay.
    Omitting it would be the *absence* of a claim, and REQ-17 refuses that
    under a ceiling — this test would then pass for a reason that has nothing
    to do with inclusivity.
    """
    assert _result(Availability.IN_STOCK, price=80.0, shipping=0.0, max_price=80).alertable is True


def test_in_stock_above_the_ceiling_is_not_alertable() -> None:
    assert (
        _result(Availability.IN_STOCK, price=229.99, shipping=0.0, max_price=80).alertable is False
    )


def test_in_stock_with_no_ceiling_configured_is_alertable() -> None:
    """No `max_price` means the operator asked for any restock at any price."""
    assert _result(Availability.IN_STOCK, price=229.99).alertable is True
    assert _result(Availability.IN_STOCK, price=None).alertable is True


def test_unpriced_in_stock_offer_does_not_pass_the_ceiling() -> None:
    """A price nobody read is not "cheap enough", in either branch.

    Walmart has already reshaped `priceInfo.currentPrice` once — that is why
    `parse._dig` exists — and `nextdata_offers` returns
    `Offer(available=True, price=None, ...)` when the dig misses. If an
    unreadable price counted as "cheap enough", the $229.99 flip listing would
    clear the ceiling silently and be pushed with a `price: unknown` field: an
    alert for a reseller's markup, with nothing in it to show why. That is
    exactly the noise that trains you to ignore the notifications.

    THE HEADLINE OF THIS DOCSTRING USED TO READ *"A ceiling that cannot be
    evaluated must not authorise an alert"*, and that sentence is withdrawn
    rather than quietly reused: since 2026-08-11 a ceiling with no shipping
    figure under it CAN be evaluated, against the item price, and does authorise
    an alert. What survives is the narrower and older rule — an unreadable
    PRICE leaves nothing to evaluate at all.
    """
    assert _result(Availability.IN_STOCK, price=None, shipping=0.0, max_price=80).alertable is False


def test_not_in_stock_is_never_alertable() -> None:
    for availability in (Availability.OUT_OF_STOCK, Availability.UNKNOWN):
        assert _result(availability, price=1.0, max_price=80).alertable is False
        assert _result(availability, price=1.0, shipping=0.0, max_price=80).alertable is False
        assert _result(availability).alertable is False


# --------------------------------------------------------------------------
# The delivered total — what the ceiling actually measures (REQ-17)
# --------------------------------------------------------------------------
#
# The ceiling used to measure `offer.price`. A $54.99 listing with $45 shipping
# walked straight through an $80 cap — one of only two defences against a
# reseller alert, defeated by a number the page publishes. It now measures
# price + shipping, and where that cannot be established it refuses to
# authorise an alert rather than guessing.
#
# ARITHMETIC NOTE, and it is why `pytest.approx` appears below: `54.99 + 6.99`
# is `61.980000000000004`, so `54.99 + 6.99 <= 61.98` is False. The delivered
# total is deliberately NEVER rounded — rounding would invent precision no
# retailer stated, and it would move a boundary case in the permissive
# direction. The ceilings used here are 80 and 60, which are unambiguous either
# way.


def test_established_shipping_trusts_a_claim_and_refuses_the_absence_of_one() -> None:
    """The one predicate three consumers ask, and the `0.0` case is the point.

    `0.0` is a positive claim that this offer ships free — two independent
    Walmart fields agreeing, or a retailer's own `MonetaryAmount` saying so —
    and it survives, sums, and renders as `$0.00`. `None` is the absence of any
    claim, and a negative figure is a claim the code refuses to trust (T-06-01,
    because it would pull a delivered total below the item price). Both of
    those collapse to the same answer, because both mean "nobody established a
    shipping cost", and that is the state the alert body spells `unknown`.
    """
    assert established_shipping(None) is None
    assert established_shipping(-5.0) is None
    assert established_shipping(0.0) == 0.0
    assert established_shipping(6.99) == 6.99


def test_the_delivered_total_is_the_price_plus_the_shipping() -> None:
    """GameStop's captured numbers: $54.99 + $6.99, under an $80 ceiling."""
    r = _result(Availability.IN_STOCK, price=54.99, shipping=6.99, max_price=80)

    assert r.delivered_total == pytest.approx(61.98)
    assert r.alertable is True


def test_the_ceiling_bites_on_the_delivered_total_and_on_nothing_else() -> None:
    """The whole of REQ-17 in one assertion.

    $54.99 clears a $60 ceiling comfortably. $54.99 + $6.99 does not. If this
    ever passes, the ceiling has gone back to measuring the item price and the
    shipping half is decorative.
    """
    r = _result(Availability.IN_STOCK, price=54.99, shipping=6.99, max_price=60)

    assert r.delivered_total == pytest.approx(61.98)
    assert r.alertable is False


def test_an_unresolved_shipping_cost_under_a_ceiling_is_alertable() -> None:
    """REVERSED BY DAN, 2026-08-11. Where shipping is unknown, the alert goes out.

    REQ-17's own sentence stands unedited in
    `.planning/milestones/v0.2-REQUIREMENTS.md` (it lived in
    `.planning/REQUIREMENTS.md` until the v0.2 milestone was archived on
    2026-08-11, which moved the file and changed not one character of the
    requirement) and is quoted here intact, because a criterion is never
    reworded to fit the code:

        "The price ceiling applies to the delivered total, not the item price,
        and a shipping cost that cannot be resolved produces UNKNOWN rather
        than a pass. A $54.99 listing with $45 shipping currently defeats one
        of only two defences against a reseller alert."

    06-01 built exactly that, measured what it cost — Nintendo and Amazon both
    stopped being able to page anybody — and put the bill to Dan. He reversed
    it, verbatim, on 2026-08-11:

        "I think where we don't know just send it. If the user gets there and
        it's 50 dollar shipping that's disappointing but it's worse to feel
        like you 'missed out'."

    So this test asserts the opposite of what it asserted yesterday, and it is
    RENAMED to say so: a name stating the old verdict over an assertion of the
    new one is the self-invalidating document this whole milestone exists to
    close.

    STATE THE COST PLAINLY. This reopens the specific hole REQ-17 names. A
    $54.99 listing with $45 of shipping the page does not publish readably now
    pages Dan, and he will not be told the total. What it gives back is the two
    watches 06-01 took: Nintendo — the only first-party GO Plus + listing
    anywhere in this project's config, at MSRP — and Amazon. The whole of the
    mitigation is that the push body carries `shipping: unknown` as a field, so
    the hole is visible at the moment of decision rather than explained
    afterwards.

    What did NOT reverse is asserted two tests up: where shipping IS readable
    the ceiling still measures the delivered total, and $54.99 + $6.99 still
    fails a $60 ceiling.
    """
    assert _result(Availability.IN_STOCK, price=54.99, max_price=80).alertable is True


def test_an_item_price_over_the_ceiling_is_not_alertable_when_shipping_is_unknown() -> None:
    """"Just send it" never meant "send it at any price".

    The item-price ceiling is the whole of what is left of this defence once
    shipping cannot be read, so it has to bite: the $229.99 reseller listing
    that motivated the ceiling in the first place is still refused when nobody
    read its shipping cost. Mutation M28 rebuilds the misreading — the
    unresolvable branch passing unconditionally — and this is what kills it.
    """
    assert _result(Availability.IN_STOCK, price=229.99, max_price=80).alertable is False


def test_an_unreadable_price_under_a_ceiling_is_still_not_alertable() -> None:
    """The pre-existing rule, and the one refusal the reversal does NOT touch.

    An unreadable price is not "cheap enough" in either branch, and both are
    asserted because they now run through different code: with `shipping=0.0`
    the delivered total is unestablished only because the price is, and with
    shipping omitted the unresolvable branch has to refuse the price itself.
    A tree that reversed too much — treating an unreadable price the way it now
    treats an unread shipping cost — would pass the first and fail the second.
    This is what kills M4.
    """
    assert _result(Availability.IN_STOCK, price=None, shipping=0.0, max_price=80).alertable is False
    assert _result(Availability.IN_STOCK, price=None, max_price=80).alertable is False


def test_no_ceiling_configured_still_short_circuits_before_any_of_this() -> None:
    """An operator who configured no ceiling asked for any restock at any price.

    Nothing about the delivered total is consulted, and it must not be: every
    control watch in `config/products.yaml` carries no `max_price`, so this
    short-circuit is what makes REQ-17's blast radius exclude the control
    stage of `make verify` entirely.
    """
    assert _result(Availability.IN_STOCK, price=54.99).alertable is True


def test_a_negative_shipping_cost_never_lowers_a_delivered_total() -> None:
    """T-06-01: a retailer-supplied number that would turn the defence into a hole.

    `54.99 + -5.0` is `49.99`, which clears a ceiling the honest total might
    not. A negative shipping cost pulls the delivered total BELOW the item
    price, so it is refused outright rather than subtracted — the total stays
    unestablished, which is what this test's name says and what it still
    asserts.

    Guarded in `established_shipping` and in exactly one place, not in each
    reader: this is the single point at which a shipping number becomes a
    decision, and N readers would be N chances to get it wrong. It moved out of
    `delivered_total` on 2026-08-11 because two more consumers now ask the same
    question — the alert body and the `detail` suffix — and the behaviour is
    unchanged for every input.

    THE SECOND ASSERTION REVERSED ON 2026-08-11, and the name did not, because
    the name is still accurate. A refused figure is an unknown figure, and
    under Dan's decision an unknown shipping cost alerts on the item price
    alone: $54.99 against an $80 ceiling. What the reversal must NOT do is let
    `-5.0` reach the sum or the push body — `delivered_total` is still `None`
    here, and `tests/test_alert_text.py` asserts no `-5` reaches a phone.
    """
    r = _result(Availability.IN_STOCK, price=54.99, shipping=-5.0, max_price=80)

    assert r.delivered_total is None
    assert r.alertable is True


def test_the_delivered_total_is_none_whenever_either_half_is_missing() -> None:
    """Published as `None`, not as a partial sum, so nothing downstream can guess."""
    assert _result(Availability.IN_STOCK, price=54.99).delivered_total is None
    assert _result(Availability.IN_STOCK, shipping=6.99).delivered_total is None
    assert _result(Availability.IN_STOCK).delivered_total is None


def test_shipping_moves_no_availability() -> None:
    """UNKNOWN is never resolved into a verdict, and nothing becomes OUT_OF_STOCK.

    Where the UNKNOWN goes is `alertable`, not `Availability`, and that is a
    decision rather than an accident. Driving availability to UNKNOWN over a
    PRICING question would make the page's own stock statement disappear, and
    it would strand Nintendo and Amazon at a permanent UNKNOWN with no path
    back. `alertable is False` resolves nothing and moves in the fail-safe
    direction.
    """
    for availability in Availability:
        for shipping in (None, 0.0, 6.99, -5.0):
            r = _result(availability, price=54.99, shipping=shipping, max_price=80)
            assert r.availability is availability


def test_a_result_built_without_a_shipping_cost_did_not_read_one() -> None:
    """`None` is "no shipping cost was read". It is never `0.0`.

    `0.0` is a positive claim that this offer ships free. For Amazon and for
    both browser adapters `None` is the honest and permanent value, because
    none of their readers touches shipping at all.
    """
    r = _result(Availability.IN_STOCK)
    assert r.shipping is None
    assert r.delivered_total is None


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
    r = _result(
        Availability.IN_STOCK, price=54.99, shipping=0.0, max_price=80, rung=Rung.BROWSER
    )
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
        Availability.IN_STOCK, price=54.99, shipping=0.0, max_price=80, extraction=Extraction.DOM
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
    # `shipping=0.0` on both: the subject here is the store, and under REQ-17 a
    # ceiling with no shipping cost read is not alertable — so without a
    # resolved shipping these two assertions would pass for the wrong reason
    # and stop saying anything about the store at all.
    pinned = Result(
        watch, Availability.IN_STOCK, price=54.99, detail="synthetic", store="0", shipping=0.0
    )
    mismatched = Result(
        watch,
        Availability.IN_STOCK,
        price=54.99,
        detail="synthetic",
        store="00000",
        shipping=0.0,
    )

    assert pinned.store == "0"
    assert mismatched.store == "00000"
    # Both still alertable, and both still IN_STOCK. 05-02 changes this; this
    # plan deliberately does not.
    assert pinned.alertable is True
    assert mismatched.alertable is True
    assert mismatched.availability is Availability.IN_STOCK


# --------------------------------------------------------------------------
# REQ-21: a reading carries the moment it was taken
# --------------------------------------------------------------------------
#
# Asked when the Amazon and Walmart GO Plus + watches last read `out_of_stock`,
# this system had no answer: a row read four seconds ago and one last read two
# days ago were byte-identical in shape. `Result.read_at` is the datum that ends
# that, and the two things asserted here are the two that can go wrong at the
# source — the default meaning UNKNOWN age rather than *now*, and the stamp
# leaking into a verdict it must not touch.
#
# NO CLOCK IS FROZEN, INJECTED OR MONKEYPATCHED, here or anywhere in this phase.
# The two-day-old case is CONSTRUCTED as `time.time() - 172800` — a value read
# rather than taken — which is `tests/test_pacing.py:501-505`'s existing method
# and the reason no time seam is built at all.


def test_a_result_built_without_a_stamp_has_no_age() -> None:
    """`None`, and specifically not `0.0` and not `time.time()`.

    Both wrong answers are available and they fail in opposite directions.
    `time.time()` at construction dates a reading to the moment somebody built
    the object, which makes a refusal look like a fresh reading — the failure
    REQ-21 exists to remove. `0.0` renders as 1 January 1970, i.e. maximally
    stale, which is the same lie pointed the other way.

    Asserted with `is None` rather than for falsiness on purpose: `0.0` is falsy,
    so `assert not r.read_at` would pass against the value this must never take.
    """
    r = _result(Availability.IN_STOCK, price=54.99)

    assert r.read_at is None


def test_read_at_is_declared_last_with_a_default_of_none() -> None:
    """"Declared last, after `shipping`" is asserted statically, not described.

    Every field added to `Result` since `rung` has been appended for one reason:
    every pre-existing construction site stays valid and keeps its meaning. That
    property is a fact about field ORDER, so a comment claiming it is a claim
    nothing measures — this is the measurement.
    """
    fields = dataclasses.fields(Result)

    assert fields[-1].name == "read_at"
    assert fields[-1].default is None
    # The field it follows, named: `shipping`'s own comment is the precedent
    # this one extends, and an insertion between them would silently break the
    # positional signature this rule exists to protect.
    assert fields[-2].name == "shipping"


def test_the_stamp_changes_no_verdict() -> None:
    """A fresh, a two-day-old and an unstamped reading agree on all four verdicts.

    This is the asymmetry paragraph as a test rather than as a claim. Staleness
    touches neither `Availability` nor `alertable`, and the reason is mechanical:
    a `Result` is always fresh at the instant it is constructed, so a staleness
    term inside either property is a term that is always false — a branch that
    can never be taken, which is the unbindable-gate defect this phase exists to
    avoid, one level in.

    The ceiling is configured and the shipping cost is established so `alertable`
    is `True` in all three cases. An assertion that every arm is `False` would
    hold just as well against a property that had been broken to refuse
    everything, and would therefore have nothing to lose.
    """
    fresh = _result(
        Availability.IN_STOCK, price=54.99, shipping=0.0, max_price=80, read_at=time.time()
    )
    two_days_old = _result(
        Availability.IN_STOCK,
        price=54.99,
        shipping=0.0,
        max_price=80,
        read_at=time.time() - 172800,
    )
    unstamped = _result(Availability.IN_STOCK, price=54.99, shipping=0.0, max_price=80)

    assert fresh.read_at is not None
    assert two_days_old.read_at is not None
    assert unstamped.read_at is None

    for r in (fresh, two_days_old, unstamped):
        assert r.availability is Availability.IN_STOCK
        assert r.alertable is True
        assert r.degraded is False
        assert r.delivered_total == pytest.approx(54.99)
