# Phase 1: Detector Safety Net - Context

## Phase Boundary

**In scope:** offline fixture-backed tests for the extraction layer, type
hints and a static type check, and a single `make verify` that bundles every
mechanical check behind one exit code.

**Out of scope:** any new retailer adapter. Phase 1 exists so that Phase 2 can
add three adapters without silently breaking the two that work.

## Why This Phase Is First

The failure this project exists to catch is invisible by construction. When a
retailer changes its page and a detector stops matching, a selector-based
monitor reports "out of stock" forever and looks perfectly healthy — you find
out weeks later, having missed the drop. That is how the prior generation of
tools died.

We are about to more than double the adapter count. Doing that without a
harness means more ways to fail silently and no way to notice. Hence the
ordering.

## Implementation Decisions

### Fixtures are frozen, not auto-refreshed

Saved HTML is a snapshot. It will keep passing after a retailer changes its
page — that is not a bug, it is the division of labour:

- **Fixtures** catch *code* regressions: did a change to the parser break an
  extractor that used to work?
- **Live control products** catch *reality*: did the retailer change something?

CI auto-refresh was considered and rejected: it would let a genuine breakage
land disguised as a fixture update, which is precisely the silent failure the
project exists to prevent. Instead, fixtures carry capture metadata and
`make verify` warns when one is older than 90 days.

### The mutation check is the point

A test suite that passes is not evidence it would catch anything. `make verify`
must include a step that deliberately corrupts an extractor and asserts the
suite then FAILS. Without it we have confidence without grounds — the same
error as a monitor reporting out-of-stock because it cannot parse.

### `make verify` is one command, one exit code

GSD's verifier is an LLM forming a judgement, and a judgement can be
confidently wrong in the same direction as the code that produced it. Success
criteria that are *executable* remove that: the verifier reads an exit code
instead of forming an impression. It also outlives the tooling — Dan can run
it himself in six months.

### Claude's Discretion

- Test framework: pytest (already the ecosystem default; no reason to deviate)
- Type checker: mypy, non-strict initially — the goal is catching real errors,
  not winning a strictness contest on an 854-line codebase
- Fixture storage format: raw `.html` plus a sidecar `.json` of capture metadata

## Canonical References

### Current extraction surface (what the tests must pin down)

- `boty/parse.py` — `ldjson_offers()` (schema.org), `nextdata_offers()` (Walmart's
  `props.pageProps.initialData.data.product`), both return `None` when they
  cannot find what they expect
- `boty/retailers.py` — `check_html()` maps missing structured data to
  `Availability.UNKNOWN`; `_pick()` implements first-party seller filtering
- `boty/models.py` — `Availability` (three states), `Result.alertable`
  (in-stock AND at/under `max_price`)
- `boty/monitor.py` — `assess_health()` treats a retailer with no control
  watch as unhealthy

### Known-good live values at time of writing (2026-08-02)

Useful as fixture expectations, but note these are *live* facts that will drift:

- GameStop GO Plus + → `OutOfStock`, $54.99, seller "GameStop", via ld+json
- Walmart GO Plus + → `IN_STOCK` $229.99 from seller "Clove Brothers LLC"
  (a marketplace reseller) — first-party filtering must reject this, and the
  $80 price ceiling must reject it independently
- GameStop PS5 control → `InStock`, $549.99
- Walmart Great Value milk control → `IN_STOCK`, $2.42, seller "Walmart.com"

## Specific Ideas

The Walmart GO Plus + fixture is the single most valuable test case in the
project: one page that simultaneously exercises three-state availability,
seller filtering, and the price ceiling, with a real-world reseller markup of
4x MSRP. Capture it before it changes.

## Deferred Ideas

- Cross-checking structured data against page text (changedetection.io's
  "lie detected" pattern) — worth adopting eventually, but it is a detection
  improvement, not a safety net, and belongs after the harness exists
- Property-based testing of the parsers
- Coverage thresholds
