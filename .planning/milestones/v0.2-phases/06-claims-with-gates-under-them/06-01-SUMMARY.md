---
phase: 06-claims-with-gates-under-them
plan: 01
subsystem: parsing
tags: [shipping, price-ceiling, delivered-total, schema-org, next-data, mutation-testing, req-17]

requires:
  - phase: 05-a-reading-is-about-one-store
    provides: "`Result.store` and the ten-site thread-through pattern this plan copied for `Result.shipping`; the M9/M10 anchoring discipline; the `_verdict_from_html` guard placement"
  - phase: 03.1-degraded-readings
    provides: "`Result.degraded` as the worked example of a DERIVED property with one source of truth, which `delivered_total` follows"
provides:
  - "`parse.Offer.shipping` — a shipping cost where a retailer publishes one in a form that can be read, `None` where it does not"
  - "`parse._ldjson_shipping` — type-checks before it digs, so Nintendo's prose under GameStop's key yields no number"
  - "`parse._nextdata_shipping` — resolves Walmart to `0.0` only where two independent fields agree, selected by `type` and never by index"
  - "`models.Result.shipping` and the derived `models.Result.delivered_total`"
  - "`alertable`'s ceiling half rewritten as ONE guard against the delivered total"
  - "M4 re-anchored, plus M17 (the rejected lenient fallback, rebuilt) and M18 (the addend dropped)"
  - "A measured four-watch alertability table — 06-06's blocking-checkpoint material"
affects: [06-06, 06-05, future-shipping-work, config.py-operator-declarations]

tech-stack:
  added: []
  patterns:
    - "Type-check the container before digging into it, where the same key carries two types across retailers"
    - "Resolve a fact to a value only when two INDEPENDENT fields agree; one field agreeing with itself is one field"
    - "Guard a retailer-supplied number ONCE, at the point it becomes a decision, not in each reader"

key-files:
  created: []
  modified:
    - boty/parse.py
    - boty/models.py
    - boty/retailers.py
    - scripts/mutation_check.py
    - tests/test_parse.py
    - tests/test_models.py
    - tests/test_retailers.py
    - tests/test_monitor.py
    - README.md
    - config/products.yaml
    - docs/adding-a-retailer.md

key-decisions:
  - "The price ceiling measures the delivered total (item price + shipping), and where the delivered total cannot be established it refuses to authorise an alert rather than guessing — option 1 (strict), alone; option 2 (fall back to item price) rejected because it reopens the hole REQ-17 closes"
  - "The refusal goes to `alertable`, never to `Availability` — no reading became OUT_OF_STOCK and no UNKNOWN was resolved into a verdict because a shipping cost could not be read"
  - "No shipping figure is parsed out of prose anywhere: Nintendo's `shippingDetails` sentence would yield $61.98 for an item that ships free"
  - "`fulfillmentOptions[*].speedDetails.fulfillmentPrice` is not read at all — the only non-null instance in the corpus is a $7.95 from-store DELIVERY fee"
  - "A negative shipping cost is refused in `delivered_total` and in exactly one place, rather than in each reader"
  - "The redundant `price is None` guard in `alertable` was DELETED so M4 stays load-bearing"
  - "No `max_price` was raised and no watch edited to absorb the cost — it goes to Dan at 06-06's checkpoint"

patterns-established:
  - "Two-signal resolution: a value is claimed only when two independent fields agree, and unresolved is the fail-safe default"
  - "A derived property (`delivered_total`) as the single point where an untrusted number becomes a decision"

requirements-completed: []

duration: 44min
completed: 2026-08-10
---

# Phase 6 Plan 01: The Ceiling Measures What You Would Pay — Summary

**The `max_price` ceiling now measures the delivered total (item price + shipping) read out of each retailer's own payload, and refuses to authorise an alert where that total cannot be established — closing the $54.99-listing-with-$45-shipping hole at the measured cost of two, possibly three, of the four ceiling-carrying watches losing the ability to page.**

## Performance

- **Duration:** ~44 min
- **Started:** 2026-08-10T20:10Z (approx — first commit 20:30:25Z)
- **Completed:** 2026-08-10T20:54Z
- **Tasks:** 3 (2 of them TDD, so 5 code commits)
- **Files modified:** 11

## Accomplishments

- `Offer.shipping` and `Result.shipping` carried the way `store` is carried; `Result.delivered_total` derived the way `degraded` is derived.
- One `alertable` guard replaced one `alertable` guard. The redundant `price is None` check is gone, which is what keeps M4 able to fail.
- Three per-retailer readers that fill the field **or refuse to**, each refusal argued inline against the specific wrong verdict it prevents.
- 18/18 mutations caught, up from 16/16, with M4 re-anchored in the same commit that moved its target.
- Test count 667 → **688**.
- Every ceiling claim in `README.md`, `config/products.yaml` and `docs/adding-a-retailer.md` rewritten in the same commit as the code that made the old wording false.

## Task Commits

1. **Task 1: the carrier and the three readers** — `0c9cf0a` (test, RED) → `467551d` (feat, GREEN)
2. **Task 2: the verdict, and the claims it falsifies** — `1ca5987` (test, RED) → `1dedd8d` (feat, GREEN)
3. **Task 3: watched going red** — `b548b6a` (test)

No REFACTOR commit on either TDD task: the GREEN implementations were the shape the plan specified, and a cleanup commit with no changes in it would be a commit asserting work that did not happen.

## The gate, recorded verbatim

`make verify-offline`, run at `b548b6a`, **exit code 0**:

```
identity check: PASS — 190 file(s), no host identity found
All checks passed!
688 passed in 10.35s
  baseline  unmutated sandbox passes (687 passed, 1 skipped in 10.61s)
mutation check: 18/18 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

- **Verdict line:** `VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)`
- **Test count:** 688 (baseline at Phase 5's close: 667)
- **Mutation ratio:** 18/18 (baseline: 16/16)

`make verify` (live) was **not run**. It is not this plan's gate, it has failed live since 2026-08-06 in three known classes, and none of them is this plan's.

## M4: old anchor, new anchor, and why the re-point was required

**Old** (`scripts/mutation_check.py`, before this plan):

```
        if self.price is None:
            return False
        return self.price <= self.watch.max_price
```

**New:**

```
        total = self.delivered_total
        if total is None:
            return False
        return total <= self.watch.max_price
```

**Why it was required, in one sentence:** Task 2 replaced the three lines M4 named, so `apply_mutation` would have raised `HarnessError` — *"The source drifted away from this mutation. Skipping it silently would quietly reduce the check to two mutations while still printing a total."* — and `make verify` would have died rather than degraded.

**The trap the re-point had to avoid, and did.** If `alertable` had kept a `price is None` guard *ahead of* the delivered-total guard, flipping the first one's `return False` to `return True` would change nothing (the total is also `None`, the next guard returns `False`), M4 would have SURVIVED, and the harness would have reported a hole that was not there. The redundant guard was deleted in the same commit for exactly this reason.

**M4's rewritten `breaks=`:**

> a delivered total that could not be established clears the ceiling — an unreadable price, or an offer whose shipping cost was never read, becomes alertable at any price

## M17 and M18

**M17 `breaks=`:**

> rebuilds the REJECTED lenient fallback exactly: an offer whose shipping cost could not be read is treated as shipping free, so its delivered total is the item price and the $54.99-listing-with-$45-shipping case walks through an $80 ceiling again — REQ-17's own defect, and a tree that summed a resolved shipping correctly while quietly falling back otherwise would pass M4 with the whole hole intact

**M18 `breaks=`:**

> drops the shipping addend from the sum, so the ceiling measures the item price again while every guard around it still looks correct — killed on CAPTURED GameStop numbers rather than synthetic ones: $54.99 + $6.99 fails a $60 ceiling and $54.99 alone clears it

**Ident-by-ident CAUGHT output** (from `make mutation`, the three this plan owns):

```
  CAUGHT    M4 boty/models.py: 9 test(s) failed — test_unpriced_in_stock_offer_does_not_pass_the_ceiling, test_an_unresolved_shipping_cost_under_a_ceiling_is_not_alertable, test_an_unreadable_price_under_a_ceiling_is_still_not_alertable (+6 more)
  CAUGHT    M17 boty/models.py: 4 test(s) failed — test_an_unresolved_shipping_cost_under_a_ceiling_is_not_alertable, test_the_delivered_total_is_none_whenever_either_half_is_missing, test_a_number_in_a_field_never_observed_carrying_one_is_not_a_shipping_cost (+1 more)
  CAUGHT    M18 boty/models.py: 3 test(s) failed — test_the_delivered_total_is_the_price_plus_the_shipping, test_the_ceiling_bites_on_the_delivered_total_and_on_nothing_else, test_the_gamestop_capture_carries_its_shipping_cost_all_the_way_to_a_result
```

M4 is killed by **both** the unreadable-price test and the unresolved-shipping test, as required. M18 is killed only by the arithmetic tests, on captured GameStop numbers. The full run is 18/18, every mutation CAUGHT; nothing SURVIVED.

## THE FOUR-WATCH ALERTABILITY TABLE — 06-06 CHECKPOINT MATERIAL

Re-measured against the **built tree** at `b548b6a`, offline, by driving each
shipped capture through the real adapter with `retailers.get` monkeypatched. **No
retailer was probed.** Exactly four watches carry `max_price` and all four are
the GO Plus + product watch; every control carries none, so no control's verdict
can change.

The second column is the counterfactual the question actually asks: *if this
retailer's page came back with a genuine first-party offer at the $54.99 MSRP,
in the shape the shipped capture shows, could the watch page Dan?*

| GO Plus + watch | Delivered total establishable? | Can still alert on a restock? |
|---|---|---|
| **GameStop** | **Yes** — `shipping=6.99` read off `OfferShippingDetails`; `54.99 + 6.99 = 61.980000000000004`, under 80 | **YES** (measured `alertable=True`) |
| **Walmart** | **Shape-dependent, and NOT demonstrated for a restock** — see the correction below | **NOT DEMONSTRATED** |
| **Nintendo** | **No** — `shippingDetails` is prose | **NO — this watch stops being alertable** |
| **Amazon** | **No** — the reader is an add-to-cart button | **NO — this watch stops being alertable** |

Raw measurement, each watch read through its real adapter against its shipped
capture (Walmart pinned to store `"0"`, this repo's redaction placeholder, so
the 05-02 store guard does not mask the shipping question):

```
gamestop  max_price=80.0
          availability=out_of_stock price=54.99 shipping=6.99 delivered_total=61.980000000000004 alertable=False
          restock-at-MSRP counterfactual: delivered_total=61.980000000000004 alertable=True

walmart   max_price=80.0   (first_party_only=True, the shipped default)
          availability=out_of_stock price=None shipping=None delivered_total=None alertable=False
          restock-at-MSRP counterfactual: delivered_total=None alertable=False

nintendo  max_price=80.0
          availability=out_of_stock price=54.99 shipping=None delivered_total=None alertable=False
          restock-at-MSRP counterfactual: delivered_total=None alertable=False

amazon    max_price=80.0
          availability=out_of_stock price=None shipping=None delivered_total=None alertable=False
          restock-at-MSRP counterfactual: delivered_total=None alertable=False
```

**At minimum two of four product watches — Nintendo and Amazon — stop being able
to page Dan, and one of them is the watch most likely to be a genuine MSRP
restock.** This plan did not absorb that: no ceiling was raised, no watch was
edited, and nothing was softened. It is Dan's to accept or reject, at **06-06's
blocking checkpoint**.

### CORRECTION TO THIS PLAN'S OWN `<decision>` TABLE — the measurement wins

The plan's `<decision>` block predicted **Walmart: "Yes, when a first-party offer
under the ceiling appears."** Measured against the built tree, that is **not
established**, and the correction is load-bearing for the checkpoint.

Walmart's shipping resolves on one capture and not the other, and the split does
not fall where the prediction assumed:

```
walmart goplusplus (marketplace reseller), first_party_only=False
  as read: in_stock price=229.99 shipping=0.0 delivered_total=229.99 alertable=False
  restock-at-MSRP counterfactual: delivered_total=54.99 alertable=True

walmart milk-control (FIRST-PARTY Walmart.com, IN_STOCK), first_party_only=True
  as read: in_stock price=2.42 shipping=None delivered_total=None alertable=False
  restock-at-MSRP counterfactual: delivered_total=None alertable=False
```

The **only first-party Walmart capture in this repository resolves NO shipping
cost**, because its SHIPPING fulfilment option carries `speedDetails: null` — so
there is no `freeFulfillment` to agree with the zero fee, and one signal is not
two. The capture that *does* resolve is the marketplace-reseller one, which is
precisely the offer the seller filter suppresses before any ceiling is consulted.

Two things follow, and neither is a reason to soften the rule:

1. **The honest answer for Walmart is "not demonstrated", not "yes".** A
   first-party Walmart restock might publish `freeFulfillment: True` — the milk
   control is a pickup-only grocery item and is a poor proxy for a shipped
   accessory — but nothing in this repository shows it doing so. Claiming "yes"
   would be the same unmeasured assertion this milestone exists to close.
2. **So the exposure at the checkpoint is two watches confirmed lost and a third
   unproven**, not two lost and two safe. Dan should be told that.

### What contradicts the plan's `<measured_facts>`, and what does not

- **F1, F2, F3, F4, F5 and F6 all held**, re-verified against the fixtures during
  execution. `54.99 + 6.99 == 61.980000000000004` confirmed; GameStop's
  `shippingDetails` is a dict and Nintendo's is a str; the milk control carries
  the `7.95` DELIVERY `fulfillmentPrice` and no non-null shipping field; exactly
  four watches carry `max_price` and every control carries none.
- **One refinement to F2's table, in the same direction.** F2 says
  `fulfillmentOptions[type=SHIPPING].speedDetails.freeFulfillment` is *"absent"*
  on `milk-control`. Measured: the whole of `speedDetails` is `null` there, so
  the key is absent because its container is. Same outcome, and the reader
  type-checks `speedDetails` before reading into it for exactly this reason.
- **The `<decision>` block's Walmart row is corrected above.** The
  `<measured_facts>` block never claimed it; it is the decision table's
  extrapolation from F1 that the measurement does not support.

## Files Created/Modified

- `boty/parse.py` — `Offer.shipping`; `_ldjson_shipping` (type-checked, prose refused); `_nextdata_shipping` (two-signal, `type`-selected, `fulfillmentPrice` untouched); three new Walmart path constants; a one-line reason on `add_to_cart_offers`.
- `boty/models.py` — `Result.shipping`; the derived `Result.delivered_total`; `alertable`'s single ceiling guard; `Watch.max_price`'s comment rewritten to describe the delivered total.
- `boty/retailers.py` — shipping threaded onto all ten `Result(...)` sites the html path can return; the `detail` suffix for an unevaluable ceiling; the group comment recording that a missed site here would be behaviourally invisible.
- `scripts/mutation_check.py` — M4 re-anchored with a dated comment; M17 and M18 added. 18 mutations.
- `tests/test_parse.py` — seven tests: the four captures, the corpus sweep, and the type-discipline shapes.
- `tests/test_models.py` — `_result` gains `shipping`; eight new delivered-total tests; four pre-existing ceiling tests now state `shipping=0.0`.
- `tests/test_retailers.py` — four new thread-through tests including the labelled synthetic paid-shipping Walmart stand-in; the Amazon-cost test; two control watches corrected.
- `tests/test_monitor.py` — the restock-edge test states `shipping=0.0` so it keeps testing the edge.
- `README.md` — the three ceiling claims (§2, the Amazon paragraph, the mutation list).
- `config/products.yaml` — what `max_price` measures, and what it now costs Nintendo. No value changed.
- `docs/adding-a-retailer.md` — what `max_price` measures, and the instruction not to parse prose.

## Decisions Made

Beyond the plan's own settled decisions, three were taken during execution:

1. **The two control watches carrying a synthetic `max_price: 80` had it removed rather than their assertions inverted.** `test_target_control_fixture_is_in_stock_priced_and_alertable` and `test_amazon_control_fixture_is_in_stock_first_party_priced_and_alertable` both built a control watch with a ceiling the shipped config does not give it — every control in `config/products.yaml` carries `max_price: None`. Under REQ-17 those synthetic ceilings turned both assertions into statements about the new refusal rather than about the detector. Removing the ceiling made the synthetic watches *more* faithful to the shipped ones, and the refusal is pinned directly instead (next item).
2. **A new test pins REQ-17's cost rather than only describing it.** `test_a_first_party_amazon_offer_under_a_ceiling_cannot_be_alerted` drives the first-party Amazon control capture — IN_STOCK, $9.99, every other defence satisfied — through a product-shaped watch with `max_price=80` and asserts `alertable is False` plus the `detail` suffix. That is the shipped Amazon product watch's future, held by a test rather than by a paragraph.
3. **A fourth thread-through test was added for the resolved-Walmart case.** `test_the_walmart_capture_that_says_free_shipping_says_so_on_the_result` asserts `shipping == 0.0` reaches the `Result` and that the $229.99 reseller listing still fails the $80 ceiling — the new rule tightened this defence without loosening it anywhere.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Pre-existing tests asserted alertability under a ceiling with no shipping**

- **Found during:** Task 2 (GREEN)
- **Issue:** Seven existing tests built a `Result` with a `max_price` and no shipping cost and asserted `alertable is True`. Under the new rule that is `False`, so the suite could not go green — and none of those tests is *about* shipping (their subjects are ceiling inclusivity, degradation not suppressing alerts, the store not changing a verdict, and the CR-01 restock edge).
- **Fix:** Each states `shipping=0.0` — the positive claim "this offer ships free" — so it keeps exercising its own subject instead of passing on REQ-17's refusal. Each edit carries a comment saying why.
- **Files modified:** `tests/test_models.py`, `tests/test_monitor.py`
- **Verification:** `make verify-offline` exit 0; M5 (the restock edge) and M6/M7 (the degraded flag) still CAUGHT, which is what proves those tests still bite.
- **Committed in:** `1dedd8d`

**2. [Rule 1 - Bug] Two control tests carried a ceiling the shipped config does not give them**

- **Found during:** Task 2 (GREEN)
- **Issue:** The Target and Amazon control tests attached `max_price=80` to a *control* watch. Measured against `config/products.yaml`: every control carries `max_price: None`, and only the four GO Plus + product watches carry a ceiling. The synthetic ceiling was wrong before this plan and merely invisible.
- **Fix:** Ceiling removed from both synthetic control watches, with docstrings recording why; the refusal it was accidentally exercising is pinned in a purpose-built test instead.
- **Files modified:** `tests/test_retailers.py`
- **Verification:** M8 (the DOM availability decision, Target's guard) still CAUGHT; the new Amazon-cost test fails under M4 and M17.
- **Committed in:** `1dedd8d`

**3. [Rule 2 - Missing critical] The plan's `<decision>` table overstated Walmart's coverage**

- **Found during:** Task 3 (the re-measurement)
- **Issue:** The plan predicted Walmart keeps its alertability. Measured, the only first-party Walmart capture resolves no shipping at all, so the prediction is not supported and the checkpoint would have been given a rosier number than the tree produces.
- **Fix:** Not a code change — the table above states "not demonstrated" and shows the measurement. The measurement wins, per the plan's own instruction.
- **Files modified:** this SUMMARY.
- **Verification:** Both Walmart captures driven through `check_html` offline; output reproduced verbatim above.
- **Committed in:** the metadata commit.

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 bug, 1 missing critical).
**Impact on plan:** No scope creep. Two are test-fidelity corrections forced by the new rule; the third is a correction to the plan's own prediction, which the plan explicitly asked for.

## Issues Encountered

None that required problem-solving beyond the above. The M4 re-anchor trap the plan warned about did not materialise, because the redundant guard was deleted as instructed — M4 was CAUGHT by nine tests on the first run.

## Known Stubs

None. No placeholder, no "resolve it properly later", nothing deferred out of this plan's scope. One **pre-existing** out-of-scope item was logged rather than fixed — `scripts/mutation_check.py`'s module docstring still says "three mutations" — see `deferred-items.md` (`D-06-01-a`).

## Threat Flags

None. No new network endpoint, auth path, file access pattern or schema change at a trust boundary. Every surface touched is an existing module, no dependency was added, no fixture was edited or re-captured, and no store number, postal code or host identity is handled anywhere in this plan. `scripts/identity_check.py` passed over all 190 tracked files inside `make verify-offline`.

## REQ-17 status

**Deliberately left Pending.** 06-06 closes it by measuring what landed, on 04-05's and 05-01's precedent. Nothing here marks it complete.

## Next Phase Readiness

- Criterion 1 of five is built and gated. 06-02 through 06-05 are unblocked (this plan is wave 1 with no dependents in flight).
- **06-06 needs the four-watch table above, including the Walmart correction**, at its blocking checkpoint. The question for Dan is not "is this a bug" — it is whether losing Nintendo's and Amazon's ability to page, and possibly Walmart's, is an acceptable price for a ceiling that cannot be fooled by shipping.
- If Dan says no, the plan already names the path that does not reopen the hole: option 3, a per-watch operator declaration in Phase 5's `store_id` shape. It needs `boty/config.py`, which this phase scoped out of every plan.

## Self-Check: PASSED

- `boty/parse.py`, `boty/models.py`, `boty/retailers.py`, `scripts/mutation_check.py`, `tests/test_parse.py`, `tests/test_models.py`, `tests/test_retailers.py`, `tests/test_monitor.py`, `README.md`, `config/products.yaml`, `docs/adding-a-retailer.md` — all present.
- Commits `0c9cf0a`, `467551d`, `1ca5987`, `1dedd8d`, `b548b6a` — all found in `git log`.

---
*Phase: 06-claims-with-gates-under-them*
*Completed: 2026-08-10*
