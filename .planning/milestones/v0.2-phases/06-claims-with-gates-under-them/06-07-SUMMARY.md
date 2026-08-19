---
phase: 06-claims-with-gates-under-them
plan: 07
subsystem: alerting
tags: [shipping, price-ceiling, alert-body, reversal, mutation-testing, req-17]

requires:
  - phase: 06-claims-with-gates-under-them
    provides: "06-01's `Offer.shipping` / `Result.shipping` carrier, `delivered_total`, and the four-watch alertability table that put the bill to Dan"
  - phase: 06-claims-with-gates-under-them
    provides: "06-05's `v0.2.0` README/pyproject binding (M26), which constrains what may enter README.md"
provides:
  - "`models.established_shipping` — the ONE predicate deciding whether a shipping figure is trusted, read by the sum, the alert body and the `detail` suffix"
  - "`alertable`'s two branches: the delivered total where it resolves, the item price where it does not"
  - "`notify.send_restock`'s two-field body — `price:` and `shipping:`, same shape either way, no delivered total stated"
  - "`notify.FIELD_UNKNOWN` — one spelling of a field nobody read"
  - "M4 and M17 re-pointed with their subjects' changes recorded, M18 re-anchored, M27 and M28 added — 24/24"
  - "A re-measured four-watch alertability table and the rendered push body for each — 06-06's material"
affects: [06-06, config.py-operator-declarations]

tech-stack:
  added: []
  patterns:
    - "A reversed decision is argued IN PLACE beside the reasoning it reverses, never over it"
    - "A mutation whose subject reverses is re-pointed with the reversal recorded, never deleted"
    - "Render a field and its actual state rather than a sentence explaining it — subtracting a claim, not adding one"

key-files:
  created: []
  modified:
    - boty/models.py
    - boty/parse.py
    - boty/notify.py
    - boty/retailers.py
    - scripts/mutation_check.py
    - tests/test_models.py
    - tests/test_retailers.py
    - tests/test_alert_text.py
    - README.md
    - config/products.yaml
    - docs/adding-a-retailer.md

key-decisions:
  - "Where a shipping cost cannot be established the ceiling measures the ITEM PRICE and the alert goes out — Dan's reversal of 06-01, 2026-08-11, quoted verbatim in code, tests, config and the shipped README"
  - "Where shipping IS resolvable the ceiling still measures the delivered total and a resolvable total above it is still suppressed — 06-01's main win kept"
  - "The mitigation is a visible field, not a suppressed alert: `shipping: unknown`, with NO delivered total stated in either case"
  - "One predicate (`established_shipping`) for three consumers, and the negative-shipping rule in exactly one place in `boty/`, proven by count"
  - "REQUIREMENTS.md and ROADMAP.md left unedited; REQ-17 stays Pending; the revision record is carried here in Phase 3.1's format for 06-06 to apply"
  - "M17 re-pointed rather than deleted, with the sentence that its subject reversed written into the harness itself"

patterns-established:
  - "A user's reversal is recorded with the accepter named, the words verbatim and the date — the shape an `accept` disposition is supposed to have"
  - "'Same shape either way' asserted mechanically (one regex over both bodies, differing by one value) rather than described"

requirements-completed: []

duration: 32min
completed: 2026-08-11
---

# Phase 6 Plan 07: Alert When Shipping Is Unknown, And Show It As A Field — Summary

**Where a shipping cost cannot be read the price ceiling now measures the item price alone and the alert goes out carrying `price: $54.99   shipping: unknown` — deliberately reopening the hole REQ-17 was written to close, on Dan's explicit decision, with a visible empty field as the whole of the mitigation.**

## Performance

- **Duration:** ~32 min (first commit 13:39:52Z, last code commit 14:03:13Z)
- **Started:** 2026-08-11T13:32:23Z
- **Completed:** 2026-08-11T14:04Z
- **Tasks:** 3 (2 of them TDD, so 5 code commits)
- **Files modified:** 11

## Task Commits

1. **Task 1: one predicate, and the branch that reverses** — `717015b` (test, RED) → `05867ca` (feat, GREEN)
2. **Task 2: two fields, the same shape either way** — `63a69aa` (test, RED) → `f38a715` (feat, GREEN)
3. **Task 3: watched going red** — `b9e39bc` (test)

No REFACTOR commit on either TDD task: both GREEN implementations were the shape the plan specified, and a cleanup commit with nothing in it would assert work that did not happen. Same reasoning 06-01 recorded.

## SAY IT PLAINLY: THIS REOPENS THE HOLE REQ-17 NAMES

A $54.99 listing with $45 of shipping the page does not publish readably **now pages Dan**, and the push will not warn him about the $45 — it will show him an empty shipping field. That is not a defect discovered here; it is the trade Dan chose, having been shown 06-01's measurement of what the strict rule cost. It is stated in `alertable`'s comment, in `Watch.max_price`'s comment, in the test that pins the $54.99-plus-$45 case, in `config/products.yaml`, in `docs/adding-a-retailer.md`, in the shipped `README.md`, and in T-06-70 of the plan's threat register. It is not softened in any of them.

What still stands: a **resolvable** delivered total above the ceiling is still suppressed ($54.99 + $6.99 still fails a $60 ceiling), an item price above the ceiling is still refused even when shipping is unknown ($229.99 under $80), an unreadable price is still refused in both branches, the seller filter is untouched, and **no `Availability` verdict moved**.

## The gate, recorded verbatim

`make verify-offline`, run at `b9e39bc`, **exit code 0**:

```
identity check: PASS — 198 file(s), no host identity found
All checks passed!
768 passed in 10.82s
mutation check: 24 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (740 passed, 28 skipped in 11.00s)
mutation check: 24/24 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

- **Verdict line:** `VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)`
- **Test count:** **768** (baseline, re-measured before this plan rather than inherited: 759)
- **Mutation ratio:** **24/24** (baseline: 22/22)

`make verify` (live) was **not run.** It is not this plan's gate, it has failed live since 2026-08-06 in three known classes, and none of them is this plan's.

## M4, M17 and M18 — old anchor, new anchor, and why each re-point was required

### M4 — subject NARROWED

**Old** (`scripts/mutation_check.py`, before this plan):

```
        total = self.delivered_total
        if total is None:
            return False
        return total <= self.watch.max_price
```

**New:**

```
        if self.price is None:
            return False
        return self.price <= self.watch.max_price
```

**Why it was required, in one sentence:** Task 1 split `alertable` into two branches, so the three lines M4 named stopped existing for the second time in two days and `apply_mutation` would have raised `HarnessError` — the harness refusing to run rather than quietly checking less.

**And the honest part.** Before 2026-08-11 M4 guarded the claim that an unestablished **delivered total** cannot clear the ceiling. That claim is no longer true, so the ident now guards the narrower one — an unreadable **price** cannot — and its comment block says so with the date. Its rewritten `breaks=`:

> an offer whose PRICE could not be read clears the ceiling — with no shipping cost either, an unpriced IN_STOCK reading becomes alertable at any price, which is Walmart's reshaped `priceInfo.currentPrice` turned into a push

The property 06-01 bought by deleting a redundant guard is preserved: the price refusal moved **into** the unresolvable branch, where it is reachable and mutatable, which is what keeps M4 able to fail at all.

### M17 — subject REVERSED, and it was re-pointed rather than deleted

**Old:**

```
        if self.price is None or self.shipping is None or self.shipping < 0:
            return None
        return self.price + self.shipping
```

**New** (in `established_shipping`):

```
    if shipping is None or shipping < 0:
        return None
    return shipping
```

**Why it was required, in one sentence:** Task 1 moved the negative-shipping rule out of `delivered_total` into the shared predicate, so M17's anchor no longer existed.

**THE SENTENCE THAT MATTERS, recorded in the harness itself and not only here.** Until 2026-08-11 this ident pinned the item-price fallback as **REJECTED** — its `breaks=` read *"rebuilds the REJECTED lenient fallback exactly"*, and `06-01-SUMMARY.md` records it that way. **Dan then chose a version of that fallback.** A `breaks=` sentence describing a rejection that did not survive is a gate asserting a rule the tree does not hold, so it could not be left standing. **It was re-pointed rather than deleted**, because deleting a mutation to make a suite green is forbidden in this repository — and deletion was the easy move here, since "the behaviour it guarded is now the behaviour" is exactly the argument that would have lost a gate. **It now guards the CLAIM where it used to guard the VERDICT.** Its rewritten `breaks=`:

> a shipping cost NOBODY READ is stated as free: `established_shipping` collapses the absence of a claim into $0.00, so the delivered total becomes the item price, the ceiling measures a figure nobody measured, and the push body says `shipping: $0.00` over a $45 charge waiting at the checkout page — the one reading of Dan's 2026-08-11 decision he did not choose

### M18 — mechanical re-anchor, subject unchanged

**Old:** `        return self.price + self.shipping`
**New:** `        return self.price + shipping`

**Why it was required, in one sentence:** `delivered_total` now binds `established_shipping(self.shipping)` to a local, so the addend is spelled `shipping`; same expression, same subject, same kill list. Its `breaks=` gained one clause naming this as the half of REQ-17 that survives Dan's reversal intact.

## M27 and M28 — the two new idents

**M27 `breaks=`:**

> rebuilds 06-01's strict refusal exactly, undoing Dan's 2026-08-11 reversal: an offer whose shipping cost could not be read never alerts again, so Nintendo — the only first-party GO Plus + listing in this project's config — and Amazon go quiet, with every test around them still looking sensible

**M28 `breaks=`:**

> rebuilds the MISREADING of Dan's decision — "where we don't know just send it" taken to mean send it at any price — so a $229.99 reseller listing whose shipping nobody read pages him, which is the most likely future regression here because it reads exactly like the decision

They share a `search` string deliberately, on M6/M7's precedent (*"each mutation is applied in its own sandbox, so there is no interaction between them"*) and for M6/M7's reason: M27 proves the branch **alerts**, M28 proves the ceiling **still binds** inside it. **M21–M24 remain unallocated** — 06-03's and 06-04's deliberate gap, not four lost mutations.

## Ident-by-ident CAUGHT output

From `make mutation` at `b9e39bc`, the five this plan owns:

```
  CAUGHT    M4 boty/models.py: 2 test(s) failed — test_unpriced_in_stock_offer_does_not_pass_the_ceiling, test_an_unreadable_price_under_a_ceiling_is_still_not_alertable
  CAUGHT    M17 boty/models.py: 9 test(s) failed — test_a_shipping_cost_nobody_read_is_a_field_saying_so_and_no_total, test_a_refused_shipping_figure_never_reaches_a_phone, test_an_unreadable_price_uses_the_same_word_as_an_unreadable_shipping (+6 more)
  CAUGHT    M18 boty/models.py: 3 test(s) failed — test_the_delivered_total_is_the_price_plus_the_shipping, test_the_ceiling_bites_on_the_delivered_total_and_on_nothing_else, test_the_gamestop_capture_carries_its_shipping_cost_all_the_way_to_a_result
  CAUGHT    M27 boty/models.py: 4 test(s) failed — test_an_unresolved_shipping_cost_under_a_ceiling_is_alertable, test_a_negative_shipping_cost_never_lowers_a_delivered_total, test_a_number_in_a_field_never_observed_carrying_one_is_not_a_shipping_cost (+1 more)
  CAUGHT    M28 boty/models.py: 4 test(s) failed — test_an_item_price_over_the_ceiling_is_not_alertable_when_shipping_is_unknown, test_run_once_does_not_alert_above_the_price_ceiling, test_bestbuy_price_ceiling_still_bites_on_the_browser_rung (+1 more)
```

The full run is **24/24, every mutation CAUGHT; nothing SURVIVED.** M17 is killed by both the arithmetic tests and the new render tests — the claim and the verdict — which is the property its re-point was supposed to buy. M27 and M28 are killed by disjoint tests, which is what proves they are not one mutation written twice.

## THE FOUR-WATCH ALERTABILITY TABLE — RE-MEASURED, 06-06 CHECKPOINT MATERIAL

Measured against the **built tree at `b9e39bc`**, offline, by driving each shipped capture through its real adapter with `retailers.get` monkeypatched and Walmart pinned to store `"0"` (this repo's redaction placeholder). **No retailer was probed.** The counterfactual column is the question that actually matters: *if this retailer's page came back with a genuine first-party offer at the $54.99 MSRP, in the shape the shipped capture shows, could the watch page Dan?*

| GO Plus + watch | 06-01 — "Delivered total establishable?" | 06-01 — could alert? | **NOW — what the ceiling measures** | **NOW — can alert?** |
|---|---|---|---|---|
| **GameStop** | **Yes** — `shipping=6.99`; `54.99 + 6.99 = 61.98`, under 80 | **YES** | the **delivered total**, unchanged | **YES** |
| **Walmart** | **Shape-dependent, and NOT demonstrated for a restock** | **NOT DEMONSTRATED** | the **item price** — the first-party capture resolves no shipping | **YES** |
| **Nintendo** | **No** — `shippingDetails` is prose | **NO — this watch stops being alertable** | the **item price** | **YES** |
| **Amazon** | **No** — the reader is an add-to-cart button | **NO — this watch stops being alertable** | the **item price** | **YES** |

**All four move, and Walmart moves off "not demonstrated".** 06-01's honest answer for Walmart was that the only first-party capture in this repository resolves no shipping at all (`speedDetails: null`, so nothing agrees with the zero fee) and therefore could not be shown to alert. Under the reversal, resolving no shipping is no longer a reason it cannot alert — it is the branch that alerts on the item price — so the same unchanged measurement now yields **YES**. Nothing about Walmart's payload was re-read or re-captured; only the conclusion drawn from it changed.

Raw measurement, verbatim:

```
gamestop  goplusplus             max_price=80 first_party_only=True
          availability=out_of_stock price=54.99 shipping=6.99 delivered_total=61.980000000000004 alertable=False
          restock-at-MSRP counterfactual: delivered_total=61.980000000000004 alertable=True

walmart   goplusplus             max_price=80.0   (first_party_only=True, the shipped default)
          availability=out_of_stock price=None shipping=None delivered_total=None alertable=False
          restock-at-MSRP counterfactual: delivered_total=None alertable=True

walmart   milk-control (the only FIRST-PARTY Walmart capture)   max_price=80 first_party_only=True
          availability=in_stock price=2.42 shipping=None delivered_total=None alertable=True
          restock-at-MSRP counterfactual: delivered_total=None alertable=True

nintendo  goplusplus             max_price=80 first_party_only=True
          availability=out_of_stock price=54.99 shipping=None delivered_total=None alertable=False
          restock-at-MSRP counterfactual: delivered_total=None alertable=True

amazon    control-aa-batteries   max_price=80 first_party_only=True
          availability=in_stock price=9.99 shipping=None delivered_total=None alertable=True
          restock-at-MSRP counterfactual: delivered_total=None alertable=True
```

One row worth reading twice: the **Walmart marketplace** capture, driven with `first_party_only=False` to reach the ceiling at all, reads `in_stock price=229.99 shipping=0.0 delivered_total=229.99 alertable=False`. The $229.99 reseller listing is **still refused**, by a resolvable total over the ceiling, before the seller filter is even considered. The reversal loosened nothing there.

## WHAT THE PUSH WOULD ACTUALLY SAY — the table 06-01 could not produce

Dan is being asked to accept a reopened hole on the strength of one word in a notification body. Here is the body, captured from the **real** `send_restock` with `_client` monkeypatched, for each of the four watches at the restock-at-MSRP counterfactual:

```
--- GameStop (shipping resolved) ---
title: IN STOCK: Pokémon GO Plus +
Pokémon GO Plus + at gamestop
price: $54.99   shipping: $6.99
https://www.gamestop.com/x

--- Walmart, first-party capture (shipping unresolved) ---
title: IN STOCK: Pokémon GO Plus +
Pokémon GO Plus + at walmart
price: $54.99   shipping: unknown
https://www.walmart.com/ip/2

--- Nintendo (shipping is prose, never parsed) ---
title: IN STOCK: Pokémon GO Plus +
Pokémon GO Plus + at nintendo
price: $54.99   shipping: unknown
https://www.nintendo.com/x

--- Amazon (the reader is a button) ---
title: IN STOCK: Pokémon GO Plus +
Pokémon GO Plus + at amazon
price: $54.99   shipping: unknown
https://www.amazon.com/dp/X
```

And the Walmart marketplace capture, which is the one case in the corpus where a **claim** of free shipping exists — `shipping: $0.00` is a measured statement there, not a default:

```
--- Walmart, marketplace capture (shipping resolved as free) ---
price: $54.99   shipping: $0.00
```

**No delivered total appears in any body**, in either case, and no total was needed to make either legible. That is the format Dan asked for, verbatim: *"Instead of 'unverified', why don't you say price: &lt;price&gt; shipping: &lt;unknown&gt;"*.

## REQ-17 REVISED BY DAN'S DECISION 2026-08-11

*In Phase 3.1's format: the original quoted intact, the reversal beside it, never over it. **`REQUIREMENTS.md` was NOT edited** — applying this is 06-06's edit, and the difference between a user reversing a decision and an agent rewording a criterion is exactly that line.*

**The original requirement, quoted intact and unedited in the tree:**

> **REQ-17**: The price ceiling applies to the **delivered total**, not the item price, and a shipping cost that cannot be resolved produces UNKNOWN rather than a pass. A $54.99 listing with $45 shipping currently defeats one of only two defences against a reseller alert.

**Dan's decision, verbatim, 2026-08-11:**

> "I think where we don't know just send it. If the user gets there and it's 50 dollar shipping that's disappointing but it's worse to feel like you 'missed out'."

**And on the alert format, also his:**

> "Instead of 'unverified', why don't you say price: &lt;price&gt; shipping: &lt;unknown&gt;"

**What is reversed.** The second half of REQ-17's first sentence. A shipping cost that cannot be resolved no longer suppresses the alert; the ceiling falls back to the item price and the alert goes out. The hole named in REQ-17's second sentence — a $54.99 listing with $45 of unread shipping — is **reopened**, knowingly, by the user, with the reasoning above on the record.

**What still stands.** The first half, entire: the ceiling applies to the **delivered total** wherever a shipping cost can be read, and a resolvable total above the ceiling is still suppressed. So is the rule that nothing is guessed — no shipping figure is parsed out of prose, `fulfillmentOptions[*].speedDetails.fulfillmentPrice` is still not read, a negative figure is still refused, and `None` never collapses to `$0.00`. So is the rule that this touches `alertable` and never `Availability`.

**And the sentence that keeps the two kinds of reversal apart: 06-01's measurements were right, and only the conclusion drawn from them changed.** Nintendo really does publish its shipping as prose; Amazon's reader really is a button; the only first-party Walmart capture really does resolve no shipping. Not one of those measurements was re-taken, softened or re-interpreted. What changed is what the system does about them, and that change was made by the person the tool pages.

## The classification of every changed assertion, into F3's two classes

The plan predicted exactly four assertion sites reverse and named them. Measured: **exactly those four, and no others.** The full suite went green with no further edits, so **class (B) is empty this plan** — 06-01 had already stated `shipping=0.0` on every test whose subject is something else, and that work held.

| Site | Class | Handling |
|---|---|---|
| `tests/test_models.py` `test_an_unresolved_shipping_cost_under_a_ceiling_is_not_alertable` | **(A)** its subject IS the refusal | Reversed, **renamed** to `..._is_alertable`, docstring carries Dan's quote dated and REQ-17's sentence intact beside it |
| `tests/test_models.py` `test_a_negative_shipping_cost_never_lowers_a_delivered_total` (`alertable` half only) | **(A)** | Reversed to `True`; `delivered_total is None` unchanged; **not renamed** — the name is still accurate; docstring says exactly why |
| `tests/test_retailers.py` `test_a_number_in_a_field_never_observed_carrying_one_is_not_a_shipping_cost` | **(A)** | Reversed to `True`; **name kept** (the fee still does not become a shipping cost); last docstring paragraph rewritten to say without hedging that this is the case REQ-17 names and that it now pages |
| `tests/test_retailers.py` `test_a_first_party_amazon_offer_under_a_ceiling_cannot_be_alerted` | **(A)** | Reversed and **renamed** to `..._alerts_with_its_shipping_unknown`; its `detail` assertion moved with the suffix in Task 2 |

Two further docstring corrections were made rather than left standing, both because the code made them false in the same commit — recorded as deviations 2 and 3 below.

## Files Created/Modified

- `boty/models.py` — `established_shipping` (module-level, above `Watch`, three consumers named); `delivered_total` binds it, behaviour identical for every input; `alertable`'s two branches with the reversal argued in place and 06-01's reasoning extended rather than deleted; `Watch.max_price`'s comment rewritten.
- `boty/parse.py` — **comments only, no behaviour**: `Offer.shipping`'s field comment now says the `None`/`0.0` distinction decides what the alert STATES; `_ldjson_shipping`'s docstring drops *"`None` refuses the alert"* and names `models.established_shipping` as where a negative value is refused.
- `boty/notify.py` — `FIELD_UNKNOWN`; one `_field` formatter for both fields; `send_restock`'s two-field body, reading shipping through `established_shipping`, stating no total, with the reason in its docstring.
- `boty/retailers.py` — the `detail` suffix now states which figure the ceiling measured, on the `established_shipping(offer.shipping) is None` condition (which also catches a negative, where the old `offer.shipping is None` did not); the no-anchor warning extended to M27/M28. Ten `shipping=` thread-through sites, unchanged.
- `scripts/mutation_check.py` — M4 and M17 re-pointed with dated comments, M18 re-anchored, M27 and M28 added. **24 mutations.**
- `tests/test_models.py` — the reversal argued in place, the two new boundaries, the four predicate cases, and the withdrawn *"a ceiling that cannot be evaluated"* headline.
- `tests/test_retailers.py` — the reopened hole and the Amazon watch that can page again, both against real adapters; the healthy GameStop `detail` pinned byte-identical under a configured ceiling.
- `tests/test_alert_text.py` — a new section: **the first assertions ever made about `send_restock`'s body**, plus a module docstring extended to say why both halves of what reaches a person live in one file.
- `README.md` — one honest paragraph in § 2 saying the ceiling measures the delivered total where shipping can be read, the item price where it cannot, and that **a listing with large unread shipping can reach you**.
- `config/products.yaml` — the `max_price` header block and the Nintendo block: every measured sentence kept, only the consequence reversed, with the date.
- `docs/adding-a-retailer.md` — the new rule, the reopened hole, and the instruction not to parse prose kept **exactly as it was**.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Two of the three README paragraphs the plan names no longer exist**

- **Found during:** Task 2
- **Issue:** The plan targets `README.md:52-59` (the § 2 ceiling paragraph ending *"refuses to authorise the alert"*), `README.md:178-188` (*"Amazon and Nintendo will not page anybody"*) and `README.md:479-485` (the mutation list naming *"the fallback that would let an unread shipping cost pass as free"*). The README was cut from 503 lines to 183 in `d6d16fe` and `8b205fe`, **after this plan was written**. Measured on the tree: the Amazon/Nintendo paragraph is gone entirely, the mutation paragraph is now two generic sentences naming no mutation, and § 2 had been compressed to *"keeps a price ceiling as a second, independent defence"* — which claims nothing about shipping and is therefore not false.
- **Fix:** Followed the tree. Nothing was restored to make the plan's line numbers true. The one edit made is additive and minimal, respecting the compression's intent: § 2 gains a short paragraph stating what the ceiling measures in each branch and, plainly, that **a listing with large unread shipping can reach you** — the sentence the plan says a reader deciding whether to trust this tool is entitled to. The other two targets needed no edit because no false claim survives at either.
- **Files modified:** `README.md`
- **Verification:** `grep -c` for the plan's quoted phrases returns 0 across the file; the version-token count is still exactly 1, so M26's anchor is intact and it is still CAUGHT.
- **Committed in:** `f38a715`

**2. [Rule 1 - Bug] A test docstring asserted a rule the same commit falsified**

- **Found during:** Task 2
- **Issue:** `tests/test_models.py::test_unpriced_in_stock_offer_does_not_pass_the_ceiling` opened with *"A ceiling that cannot be evaluated must not authorise an alert"* — the sentence 06-01 built REQ-17 on, quoted by the plan and by `06-PATTERNS.md`. After the reversal a ceiling with no shipping figure under it **can** be evaluated, against the item price, and does authorise an alert. Left alone it would have been a self-invalidating document of exactly the class this milestone exists to close, sitting over a still-correct assertion. The same docstring also described the withdrawn `"price unknown"` push body.
- **Fix:** The headline is **withdrawn rather than quietly reused** — the docstring says so, keeps the narrower rule that survives (an unreadable price leaves nothing to evaluate at all), and updates the body reference to `price: unknown`.
- **Files modified:** `tests/test_models.py`
- **Verification:** M4 still CAUGHT, by this test and the new one; full suite green.
- **Committed in:** `f38a715`

**3. [Rule 1 - Bug] A cross-reference to a renamed test, and its reasoning, both stale**

- **Found during:** Task 1
- **Issue:** `test_target_control_fixture_is_in_stock_priced_and_alertable`'s docstring cites `test_a_first_party_amazon_offer_under_a_ceiling_cannot_be_alerted` by name — a name this plan removes — and explains the removal of a synthetic `max_price: 80` by reference to REQ-17's refusal, which no longer exists in that form.
- **Fix:** Citation re-pointed to the new name, with one sentence recording that it now pins an alert rather than a refusal, and that removing the synthetic ceiling was right either way and for a reason the reversal does not touch: the shipped control carries none.
- **Files modified:** `tests/test_retailers.py`
- **Verification:** Full suite green; `grep -r` finds no reference to the old name outside `.planning/`.
- **Committed in:** `717015b`

**4. [Rule 3 - Blocking] `ruff` rejected a single-line import**

- **Found during:** Task 1
- **Issue:** `from boty.models import Availability, Extraction, Result, Rung, Watch, established_shipping` exceeded the line-length rule; `make lint` exit 1.
- **Fix:** Split into a parenthesised import, in the repository's existing style. The same shape was used for `boty/retailers.py`'s `from .models import (...)` in Task 2.
- **Files modified:** `tests/test_models.py`, `boty/retailers.py`
- **Verification:** `make lint` → `All checks passed!`
- **Committed in:** `05867ca`, `f38a715`

**5. [Rule 3 - Blocking] `ROADMAP.md` deliberately not updated by `roadmap update-plan-progress`**

- **Found during:** state updates
- **Issue:** The executor workflow calls for `roadmap update-plan-progress`, and this plan's `<decision>` and `<success_criteria>` both require `ROADMAP.md` to be **unedited** — the phase's plan count does not include an unplanned seventh plan, and the outcome table is 06-06's job.
- **Fix:** The plan wins. `ROADMAP.md` is untouched and the reason is recorded here rather than the file being edited and un-edited.
- **Files modified:** none.
- **Verification:** `git status` shows no `ROADMAP.md` change in any commit of this plan.
- **Committed in:** n/a

---

**Total deviations:** 5 auto-fixed (3 blocking, 2 bugs). No scope creep: three are documents the code falsified in the same commit, one is a lint form, and one is a deliberate non-edit required by the plan itself.

## What contradicts this plan's `<measured_facts>`

- **F1 held with one exception, and the exception is deviation 1.** The mutation count moved 22 → 24 as predicted, the `shipping=` count in `boty/retailers.py` stayed at 10, both `Availability.` counts are unchanged (1 in `models.py`, 20 in `retailers.py`), and the README version-token count is still 1. What F1 could not know is that the README paragraphs its sibling instructions target had already been deleted; the counts it asserts were unaffected.
- **F2 held.** Nothing under `tests/` asserted anything about `send_restock`'s body before this plan. It does now.
- **F3 held exactly.** Four sites reversed, and the "everything else does not flip" list was correct — the suite went green with no class-(B) edits at all.
- **F4 and F5 held.** All three anchors had drifted, `apply_mutation` would have refused to run, and both naive renderers do state something false (`$-5.00` and a mislabelled `unknown`), which is why the predicate exists and why the render reads through it.
- **F6's "before" is reproduced above and its expectation was right in the strong form:** all four watches move, and Walmart moves off *not demonstrated* to **YES**.
- **F7 held.** No forbidden reading was added: `fulfillmentPrice` is still untouched and Nintendo's prose is still unparsed. The `detail` suffix's condition changed from `offer.shipping is None` to the predicate, which is strictly more conservative — it now also catches a negative figure the old form let through silently.

## Sequencing: 06-06 has NOT run

Confirmed on this tree at execution time: `06-06-PLAN.md` exists and `06-06-SUMMARY.md` does not; `STATE.md` read *"5 of 6 plans complete"*. This plan executed **before** 06-06, as its `<sequencing>` block requires, so 06-06 will measure what landed rather than what 06-01 built.

**06-06's blocking checkpoint card is now stale**, and it was **not edited here**. It was written to ask Dan the question he has since answered, and it explicitly names the lenient rule as *"a rejection with its reason rather than an option"* — he has now chosen a variant of it. That card needs 06-06's own replan.

## REQ-17 status

**Deliberately left Pending.** The hole REQ-17 names is **reopened, by the user's decision**, and nothing here marks the requirement complete or edits its text. 06-06 closes it by measuring what landed, carrying the revision record above.

## Known Stubs

None. No placeholder, no deferred behaviour, nothing narrower than the rule as written. `deferred-items.md`'s pre-existing `D-06-01-a` (the mutation harness's module docstring still says "three mutations") is untouched and still out of scope.

## Threat Flags

None. No new network endpoint, auth path, file access pattern or schema change at a trust boundary. Every surface touched is an existing module, no dependency was added, no fixture was edited or re-captured, and no store number, postal code or host identity is handled anywhere in this plan — `send_restock` carries only the watch name, the retailer, a configured URL and two numbers, and `_redact_store_numbers` stays scoped to `send_health_warning` where the mismatch guard's `detail` actually carries one. `scripts/identity_check.py` passed over all 198 tracked files inside `make verify-offline`.

T-06-70 is an **accept** disposition with the accepter named, the decision quoted and the date recorded, and its four residual controls are each watched going red: M28 (the item-price ceiling still binds), M18 (a resolvable total over the ceiling is still suppressed), M17 (the body shows `shipping: unknown` rather than `$0.00`), and the untouched seller filter.

## Next Phase Readiness

- **06-06 is next, and it needs a replan before it runs.** Its checkpoint card asks a question that has been answered; its record should carry the re-measured four-watch table, the rendered bodies, and the REQ-17 revision block above.
- REQ-17, REQ-18, REQ-19 and REQ-20 are all still Pending on purpose. `REQUIREMENTS.md` and `ROADMAP.md` are unedited by this plan.
- **The daemon still runs pre-Phase-4 code.** Nothing in this plan reaches a phone until `boty.service` is restarted onto this tree, and no restart was made.

## Self-Check: PASSED

- `boty/models.py`, `boty/parse.py`, `boty/notify.py`, `boty/retailers.py`, `scripts/mutation_check.py`, `tests/test_models.py`, `tests/test_retailers.py`, `tests/test_alert_text.py`, `README.md`, `config/products.yaml`, `docs/adding-a-retailer.md` — all present.
- Commits `717015b`, `05867ca`, `63a69aa`, `f38a715`, `b9e39bc` — all found in `git log`.

---
*Phase: 06-claims-with-gates-under-them*
*Completed: 2026-08-11*
