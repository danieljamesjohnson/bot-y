# Requirements: bot-y

**Current milestone: v0.3 — Say When You Measured It** (scoped 2026-08-13).

Earlier milestones' requirements are archived, not repeated here:
[`milestones/v0.2-REQUIREMENTS.md`](milestones/v0.2-REQUIREMENTS.md) covers REQ-14…REQ-20.
REQ-01…REQ-13 belong to **v1.0.0**, which is open and untagged.

## v0.3 Requirements

- [x] **REQ-21**: A reading states when it was taken, and one too old to trust is presented as
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
| REQ-21 | Phase 7 | **Complete 2026-08-17 — in the tree, NOT yet on the wire.** What was measured, not what was intended: `read_at` stated at **all 20** `Result(` construction sites and proved complete by a **static AST gate over the source**, published per watch row as `null`-never-`0`, with the read/non-read partition at **11 / 9** and two Best Buy arms the naive rule mis-stamps corrected by hand (07-01, `CAUGHT M31`). The age **survives a real two-process restart**, and the **real pre-07 document on this disk** — 13 bare strings — loads as *availability with an unknown age*, alert behaviour byte-for-byte unchanged (07-02, `CAUGHT M32`). The retailer's current cadence is **one number both surfaces read**, with the fetch schedule asserted unmoved against literal expected seconds (07-03, `CAUGHT M33`). **13 rows published where the live file had 3–10**, a remembered row carrying `checked: false` and a stated `alertable: false` (07-04, `CAUGHT M34`/`M35`). **Four rendered forms on both consumers**, judged against that published per-retailer cadence and never against the page's 30-minute banner constant (07-05, `CAUGHT M36`/`M37`). Gate: **26/26 → 33/33**, all seven watched red by hand and CAUGHT, survivors 0, `make verify-offline` exit 0 re-measured at close. **Two criteria closed MET IN PART rather than rounded up** — see `.planning/ROADMAP.md` § *Phase 7* and `docs/retailer-evidence.md` § *Phase 7 closing record*. **Not confirmed on the deployed daemon:** `MainPID=547119`, started 2026-08-12 17:28:29, re-measured 2026-08-17 and unchanged |

### Measurement notes recorded beside REQ-21, whose text is NOT edited (2026-08-17)

Phase 3.1's format: the original is quoted and left exactly as written, because a requirement is the
record of why the work was done and correcting it in place destroys the evidence that the
measurement mattered.

**1. REQ-21's sentence *"the page presents both as current"* is one direction off, and the truth is
worse rather than better.** Measured: a paced-out watch had **no row at all** — not a stale one.
Row counts against **13** configured watches, from a configuration that did not change once:
3 at 2026-08-13 08:25:10, 8 at 09:24:54 the same morning, 5 at 2026-08-14 07:36:57, then **5 at
08:43:44, 5 at 08:48:32 and 10 at 08:54:14** — the count moving 5 → 10 between two consecutive
cycles eleven minutes apart. So the row count is a function of **pacing**, which is the sharper
statement, and *"presents both as current"* understates it: the stale one was not presented at all.
Dan's opening question — *"so they are out of stock as of when?"* — cannot be answered by a row that
is missing either. **This is why the fix that landed is a row per configured watch** (07-04) before
any staleness rule could bind: a rule applied only to rows that are fresh by construction is a bound
that cannot bind. First written in `07-PLAN-OUTLINE.md` § *Finding 4*, re-measured by 07-04, 07-05
and 07-06.

**2. The registry arithmetic, so a reader of this file meets it once.** **26** mutations at phase
start (`M1`–`M20`, `M25`–`M30`), **seven** added by this phase (M31 07-01, M32 07-02, M33 07-03,
**M34 and M35** 07-04, **M36 and M37** 07-05), **33** at close. `M21`–`M24` are a **deliberate gap**
left by Phase 6 — 06-03 and 06-04 each register no mutation by design, with their reasons recorded at
the time and restated three times in `scripts/mutation_check.py` itself — and are **not four lost
mutations**. Read from the registry with comment lines filtered; a bare `grep -c` counts comment
prose, which is the class that produced both the wrong registry figure and the wrong watch count this
phase had to correct.

**A third note, on the denominator, because it is the same class as note 2.** Every planning document
in this phase says **14 configured watches**, sourced from `grep -c "retailer:" config/products.yaml`.
`Config.load` returns **13**; the fourteenth match is a comment at `config/products.yaml:309` about a
watch that deliberately does not exist. A count taken off a grep, twice in one phase, in a milestone
about claims that exceed what was measured.

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
