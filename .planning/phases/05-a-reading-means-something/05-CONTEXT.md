# Phase 5: A Reading Means Something - Context

**Gathered:** 2026-08-10
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

**Goal:** A Walmart reading is a statement about a known store, and every alert names only
what was measured — or says it does not know.

**Requirements:** REQ-14, REQ-15, REQ-16

**Success Criteria** (verbatim from ROADMAP — these are the contract):

1. Every Walmart `Result` records the store it came from, and that store is published in `status.json`
2. **Store pinning is required config with no default** (decided 2026-08-10): a per-watch `store_id` in `config/products.yaml`; unset means UNKNOWN with a health message saying so, never a guessed location and never a verdict
3. A reading from an unpinned or unexpected store is UNKNOWN, never a verdict — watched going red
4. No alert text names a cause the code has not established; where the cause is unknown the alert says so
5. A refusal the backoff is handling is recorded but not pushed; one that outlasts the cap is pushed once
6. The page-once state survives a service restart — `Pacer._state` is in-memory today, so a restart currently resets every backoff to zero

**Out of scope:** everything in Phase 6 (delivered-total price ceiling, matrix binding,
workflow-file gates, CHANGELOG contents gate, version agreement). Phase 5 touches what a
*product reading* means; Phase 6 puts gates under published claims.

</domain>

<decisions>
## Implementation Decisions

### Already decided — do not re-open

**REQ-14 store pinning is required config with no default** (Dan, 2026-08-10). A `store_id`
(or equivalent) is set per Walmart watch in `config/products.yaml`. With no value set,
readings are UNKNOWN and the health message says why.

Two alternatives were explicitly **rejected** and must not be reintroduced:

- *Default to whatever Walmart assigns and only flag changes* — leaves a reading as a
  statement about an arbitrary store, which is the bug itself.
- *Geolocate from a postal code* — more moving parts, and the ZIP is precisely the value
  Phase 3.1's leak incident was about.

The standing rule: **bot-y never guesses where the user lives, and a missing pin can never
masquerade as a verdict.** This costs every user one setup step, accepted deliberately.

REQ-14 applies to the **GO Plus + product watch, not only the control**.

### Claude's Discretion

Remaining implementation choices — where store identity is carried on `Result`, the
persistence mechanism and location for `Pacer._state`, the shape of alert text — are at
Claude's discretion. Follow the ROADMAP success criteria, the requirements above, and
existing codebase conventions.

### The project's own standing constraints (they bind this phase)

- **Never amend a success criterion to make it meetable.** Phase 3.1 was offered exactly
  that and Dan declined; Phase 4 recorded two criteria UNMET rather than reword them. If a
  criterion cannot be met, record it unmet with the reason and the date.
- **Every criterion must be verified by something executable**, not by an LLM's impression.
  `make verify` exists for this reason (see ROADMAP § *Why `make verify` exists*).
- **A gate must be watched going red before it is trusted.** A test that cannot fail is not
  evidence. Criterion 3 says "watched going red" in as many words.
- **Politeness is a hard constraint.** 5-minute cadence with jitter; probing budgets during
  development stay capped. A blocked IP costs a working monitor.
- **UNKNOWN is never OUT_OF_STOCK.** The fail-safe direction is the project's core value.

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research. Known starting points:

- `boty/retailers.py` — all adapters, including Walmart; `Result` is defined for the whole
  system, so adding store identity touches every retailer's shape, not just Walmart's.
- `config/products.yaml` — per-watch config; this is where `store_id` lands.
- `tests/test_retailers.py`, `tests/fixtures/walmart/` — fixture-backed offline tests
  (`goplusplus.html`, `milk-control.html`).
- `scripts/mutation_check.py` — the mutation gate; new detectors need a mutation that
  proves the new test can fail.
- `Makefile` → `make verify` — the phase gate: offline tests + mypy + lint + live controls +
  mutation check, one exit code.
- `Pacer._state` — in-memory today; criterion 6 is explicitly about making it survive a
  restart.
- `status.json` / `served/boty/index.html` — a 132-line read-only status page that renders
  each watch with existing tag conventions (`degraded`, `dom`). Criterion 1 requires the
  store in `status.json`; surfacing it on this page should follow the existing tag/meta
  pattern rather than introduce a new visual language.

### The measurement that opened this phase (2026-08-09)

The daemon recorded the milk control `OUT_OF_STOCK` at **$3.17**; three live reads minutes
later returned `IN_STOCK` at **$2.42**. Same URL, same parser. **A parser bug does not
change a price — two different stores answered.** Full detail in
`.planning/seeds/walmart-store-assignment-is-unpinned.md`.

### The two live counterexamples behind REQ-15

Both are alert text naming a cause that was never established:

- *"the detector is probably broken"* — fired while the detector demonstrably worked.
- *"we are asking too often"* — kept firing after backing off to a 6-hour interval had
  been **observed not to help**.

</code_context>

<specifics>
## Specific Ideas

**REQ-15** — no alert names a cause that was not measured; where the cause is unknown, the
alert must say so rather than pick a plausible-sounding one.

**REQ-16** — a notification is sent only when a human decision changes the outcome:

- a refusal the backoff is actively handling → **recorded, not pushed**
- a refusal that outlasts the cap → **pushed once**
- a detector producing a *wrong verdict* → **pushed immediately**

Recording and notifying stay separate — a retailer that is not being watched right now is
real information even when there is no action to take.

</specifics>

<deferred>
## Deferred Ideas

**Pre-existing, recorded in STATE.md — not caused by this phase and not this phase's job to
close, but it will be met during execution:**

`make verify` has failed live since 2026-08-06 (`VERIFY: FAIL (live controls)`, exit 2), in
two distinct classes:

- Best Buy and Target cannot run at all on this host — no Chrome/Chromium binary, though
  `nodriver` 0.50.3 is installed. This says nothing about the detectors.
- **Walmart** and Amazon are blocked by challenge pages at HTTP 200. Both read UNKNOWN, not
  OUT_OF_STOCK, so the fail-safe works — but real restocks are being missed.

Walmart being challenge-blocked directly affects this phase's ability to observe a live
pinned-store reading. Plan for that: criterion 3's "watched going red" must be satisfiable
offline against fixtures, and any live confirmation is a bonus, not the proof. Detail in
`.planning/phases/04-open-source-ready/deferred-items.md`.

`QUESTIONS.md` § 0e (public git history carrying this host's ZIP in four fixtures) is open
and awaiting Dan — a decision, not a blocker.

</deferred>
