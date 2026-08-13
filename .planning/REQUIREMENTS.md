# Requirements: bot-y

**Current milestone: v0.3 — Say When You Measured It** (scoped 2026-08-13).

Earlier milestones' requirements are archived, not repeated here:
[`milestones/v0.2-REQUIREMENTS.md`](milestones/v0.2-REQUIREMENTS.md) covers REQ-14…REQ-20.
REQ-01…REQ-13 belong to **v1.0.0**, which is open and untagged.

## v0.3 Requirements

- [ ] **REQ-21**: A reading states when it was taken, and one too old to trust is presented as
  stale rather than as fact. Today nothing records it: `state.json` stores the bare string
  `"out_of_stock"` with no fields at all, and `status.json`'s per-watch rows carry no timestamp
  — so a row read four seconds ago and one last read two days ago are **byte-identical in
  shape**, and the page presents both as current. Where no time was recorded the age is
  UNKNOWN, never "now". **Staleness is measured against the retailer's own current interval,
  not a fixed clock**: a retailer in backoff is legitimately checked less often, and what is
  dishonest is not the age but presenting an age nobody recorded. The measurement that opened
  it, 2026-08-13: asked when Amazon and Walmart were last read, the system had no answer —
  Amazon's was reconstructible to "before ~06:37 that morning" only from refusal history, and
  **Walmart's could not be established at all**, because a service restart had zeroed the
  counter that held the evidence. Detail in
  `.planning/seeds/a-reading-does-not-carry-its-age.md`.

### Traceability

| Requirement | Phase | Status |
|---|---|---|
| REQ-21 | Phase 7 | Pending |

---

## Project-level requirements — re-seeded 2026-08-13 from v0.2's archive

These belong to **v1.0.0**, which is open and untagged. They were parked in v0.2's archive when this file was deleted at that milestone's close, and are re-seeded here as instructed — `docs/retailer-evidence.md` and `tests/test_evidence_check.py` both cite the non-functional fresh-clone rule by name, and a citation that dangles is the defect v0.2 existed to close.
material that is not v0.2's and is not complete: the v1.0 definition of done, the user
stories, the non-functional requirements, the acceptance criteria, and the table stakes.
**They belong to v1.0.0, which is open and untagged.** They are reproduced verbatim below —
not archived, *parked* — because `docs/retailer-evidence.md` and `tests/test_evidence_check.py`
both cite the non-functional fresh-clone rule by name, and a citation that dangles is the
defect this milestone exists to close. **Re-seed them into the next `.planning/REQUIREMENTS.md`
when a new milestone is scoped.** The pre-deletion file is in git history at `e469625`.

One of them was tested hard by this milestone and held: *"Secrets never in the repo"* — the
identity guard was widened and watched going red on all four YAML spellings **before**
`store_id` was written into the tracked config, and it then rejected this milestone's own
first commit attempt over a four-digit literal in a test comment. Nothing was added to the
allow-list.



### Definition of Done

v1.0 ships when **both** are true:

1. Five or more retailers report stock with all control products green (of ~7 targeted: GameStop, Walmart, Best Buy, Pokémon Center, Nintendo, Target, Amazon). *Standing at four after Phase 3; Phase 3.1 adds Target and Amazon, which clears this.*
2. Dan has successfully bought a Pokémon GO Plus +

The second is not a joke requirement. The tool exists to solve one concrete
problem, and a monitor that runs beautifully while the thing stays unbought
has not worked.

### User Stories

- **As Dan**, I want a push notification the moment a GO Plus + is buyable *from a retailer, at near MSRP*, so I can buy it before it sells out — and not be woken up by a reseller listing at $229.
- **As Dan**, I want to be told when a detector stops working, so a silent parser failure doesn't cost me the drop while the dashboard looks healthy.
- **As a contributor**, I want to add a retailer by writing one adapter plus a control product, and have tests tell me if I broke anything.

### Non-Functional Requirements

- **Trustworthiness over coverage.** Where they conflict, correctness wins. Ten provably-correct retailers beat a hundred maybes. This is the tiebreaker for every scoping decision.
- **No-browser-first.** A browser is a last resort. It is slower, heavier, and empirically less effective against these targets than TLS impersonation.
- **Polite polling.** 5-minute default with jitter. Never sub-minute.
- **Secrets never in the repo.** Credentials live in a mode-600 env file loaded by systemd, set through a tool that prompts hidden and verifies before writing.
- **Small dependency surface.** Every dependency is another thing that can silently break a monitor.
- **Works from a fresh clone.** A retailer's PRIMARY path must work for someone who clones the repo and adds no credentials. Paths requiring a credential most people cannot obtain — manual approval, a paid domain, a commercial agreement — may be supported as an OPTIONAL enhancement, but never as the documented way that retailer works. A capability the average user cannot enable is a footnote, not support.

### Acceptance Criteria

- `boty check` shows ≥5 retailers, every control in stock, no health warnings
- `make verify` exits 0 on a healthy tree
- Deliberately breaking an extractor makes `make verify` exit non-zero
- A retailer with no control watch is surfaced as unhealthy
- A marketplace listing above the price ceiling does not produce an alert
- A blocked or unparseable fetch produces UNKNOWN, never OUT_OF_STOCK
- Telegram delivery verified end to end via `boty-ping`

### Table Stakes (already shipped)

Delivered before this roadmap; listed so they are not re-planned:

- Three-state availability with the UNKNOWN guarantee
- Control products and per-retailer health assessment
- Seller-aware detection and price ceiling
- `curl_cffi` TLS-impersonation fetching
- schema.org JSON-LD and Next.js hydration extraction
- GameStop and Walmart adapters
- YAML config, Apprise notifications, state and edge-triggered alerts
- systemd deployment, status page, Mission Control tool button

---

_Archived at milestone close. Milestone record: `.planning/milestones/v0.2-ROADMAP.md`.
Audit: `.planning/milestones/v0.2-MILESTONE-AUDIT.md`._
