# Requirements: bot-y v1.0

## Definition of Done

v1.0 ships when **both** are true:

1. Five or more retailers report stock with all control products green
2. Dan has successfully bought a Pokémon GO Plus +

The second is not a joke requirement. The tool exists to solve one concrete
problem, and a monitor that runs beautifully while the thing stays unbought
has not worked.

## User Stories

- **As Dan**, I want a push notification the moment a GO Plus + is buyable *from a retailer, at near MSRP*, so I can buy it before it sells out — and not be woken up by a reseller listing at $229.
- **As Dan**, I want to be told when a detector stops working, so a silent parser failure doesn't cost me the drop while the dashboard looks healthy.
- **As a contributor**, I want to add a retailer by writing one adapter plus a control product, and have tests tell me if I broke anything.

## Functional Requirements

### Phase 1 — Detector Safety Net

- **REQ-01**: Extraction logic is testable offline against saved HTML fixtures, with no network access.
- **REQ-02**: Tests assert the three-state contract explicitly — in particular that an unparseable page produces UNKNOWN and never OUT_OF_STOCK — and that seller filtering plus the price ceiling each independently suppress a marketplace listing.
- **REQ-03**: `boty/` carries type hints and passes a static type check.

### Phase 2 — Five Retailers Green

- **REQ-04**: Best Buy stock is read via the official Products API, since impersonated HTTP is refused at the connection layer. Absent a key, Best Buy watches are skipped, not reported as failures.
- **REQ-05**: Target, Amazon and Pokémon Center each report stock for a real product, or are documented as unreachable with the evidence that established it.
- **REQ-06**: Every configured retailer has at least one control watch. A retailer without one is reported unhealthy — an unverified detector is treated as a broken one.

### Phase 3 — Ten Retailers Green

- **REQ-07**: Roughly ten curated retailers are supported, each control-verified.
- **REQ-08**: A full `boty check` completes in under two minutes at that watch count, sequentially.

### Phase 4 — Open Source Ready

- **REQ-09**: `docs/adding-a-retailer.md` walks a contributor through a real adapter end to end and states why a control product is mandatory.
- **REQ-10**: CI runs lint, type check and the offline test suite on every PR.
- **REQ-11**: `pip install bot-y` works from PyPI, and a v1.0.0 tag exists.

## Non-Functional Requirements

- **Trustworthiness over coverage.** Where they conflict, correctness wins. Ten provably-correct retailers beat a hundred maybes. This is the tiebreaker for every scoping decision.
- **No-browser-first.** A browser is a last resort. It is slower, heavier, and empirically less effective against these targets than TLS impersonation.
- **Polite polling.** 5-minute default with jitter. Never sub-minute.
- **Secrets never in the repo.** Credentials live in a mode-600 env file loaded by systemd, set through a tool that prompts hidden and verifies before writing.
- **Small dependency surface.** Every dependency is another thing that can silently break a monitor.

## Acceptance Criteria

- `boty check` shows ≥5 retailers, every control in stock, no health warnings
- Deliberately breaking an extractor makes the test suite fail
- A retailer with no control watch is surfaced as unhealthy
- A marketplace listing above the price ceiling does not produce an alert
- A blocked or unparseable fetch produces UNKNOWN, never OUT_OF_STOCK
- Telegram delivery verified end to end via `boty-ping`

## Table Stakes (already shipped)

Delivered before this roadmap; listed so they are not re-planned:

- Three-state availability with the UNKNOWN guarantee
- Control products and per-retailer health assessment
- Seller-aware detection and price ceiling
- `curl_cffi` TLS-impersonation fetching
- schema.org JSON-LD and Next.js hydration extraction
- GameStop and Walmart adapters
- YAML config, Apprise notifications, state and edge-triggered alerts
- systemd deployment, status page, Mission Control tool button
