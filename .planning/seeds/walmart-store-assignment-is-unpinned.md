---
type: seed
created: 2026-08-09
severity: the control noise is cosmetic; the product-watch implication is not
relates_to: [boty/fetch.py, boty/parse.py, boty/retailers.py, config/products.yaml, REQ-06]
---

# Walmart reads are not pinned to a store, so they are not reproducible

## What was measured

On 2026-08-09 the service paged: *"[walmart] control product is not reading IN_STOCK —
the detector is probably broken, so real restocks would be missed silently"*, with
`CONTROL — Great Value whole milk: out_of_stock (__NEXT_DATA__: OUT_OF_STOCK from
Walmart.com)`, price **$3.17**, recorded at 11:11:43.

Three live reads of the same URL through `boty.fetch.get`, spaced ~25 s, immediately
after:

| read | `available` | price | `raw_availability` |
|---|---|---|---|
| 1 | `True` | **$2.42** | `IN_STOCK` |
| 2 | `True` | **$2.42** | `IN_STOCK` |
| 3 | `True` | **$2.42** | `IN_STOCK` |

`parse.nextdata_offers` returned `Offer(available=True, price=2.42, seller='Walmart.com',
raw_availability='IN_STOCK')` on all three. The primary product node —
`props.pageProps.initialData.data.product`, which `_WALMART_PRODUCT_PATH` addresses
explicitly rather than by a generic walk — read `IN_STOCK`.

**The detector is not broken.** It read the page it was given, correctly, both times.

## The mechanism, and the price is what proves it

Same URL, same parser, **different price** — $3.17 vs $2.42. A price difference is not
something a parser bug produces; it means the two requests were answered for **different
stores**. Walmart assigns a store per session, and grocery price and availability are
per-store properties. bot-y sends no store or postal pin, so which store answers is
effectively arbitrary per request.

So a Walmart reading is currently **not reproducible**: the same URL fetched twice can
legitimately return different availability, and nothing in the reading records which store
it came from. The page carries a `storeId` and a postal code in `__NEXT_DATA__`; neither is
captured, asserted, or published.

## Two consequences, and the second is the one that matters

**1. The control flaps, and the alert asserts a false cause.** Milk was chosen (see the
comment above the entry in `config/products.yaml`) to avoid marketplace buy-box fights, and
that reasoning was sound — it just did not anticipate that a grocery item's availability is
a property of a *store*. Every flap pages with *"the detector is probably broken"*, which is
not established and in this instance is false. This is the second alert this week that names
a cause it has not measured — see
[[notify-only-when-a-decision-changes-the-outcome]], which is about the refusal message
making the opposite error.

**2. The same unpinned assignment applies to the GO Plus + product watch on Walmart.**
Walmart is one of only four retailers that can alert on the real product. If store
assignment varies per request, then a restock reading is a statement about *some* store, not
about Walmart — and this project's entire premise is that a reading means something specific.
An alert that fires for a store the user cannot buy from, or a restock missed because an
arbitrary store answered, are both failures of the core value. Neither has been observed;
neither is currently prevented.

## Shape of a fix

Pin the location and make it part of the reading, rather than picking a different control
and calling it solved:

- Send a store/postal pin on Walmart requests so successive reads are comparable, with the
  pinned value coming from config rather than from wherever the host happens to be.
- Capture `storeId` from `__NEXT_DATA__` into the `Result`, publish it, and treat a reading
  whose store differs from the pinned one as **UNKNOWN** rather than as a verdict — the
  existing three-state contract already has the right answer for "I could not tell".
- Only then reconsider the control product. A location-independent control (a shipped,
  non-grocery, first-party item) may still be the better canary, but choosing one before
  pinning the store just hides the product-watch problem.

**Do not put a real postal code in a fixture or a committed config without redacting it.**
Phase 3.1 spent seven re-verification rounds on exactly this leak class, and the identity
guard exists because of it.

## Related

- [[notify-only-when-a-decision-changes-the-outcome]] — the alert-policy seed. This finding
  sharpens it: the fix is not only "page less", it is "do not name a cause you have not
  measured".
- Target's control was failing in the same cycle with `no structured stock data found (page
  shape changed?)` — a different mechanism (DOM read, likely the render race the pre-phase
  work addressed with a 10 s re-render) and not investigated here.
