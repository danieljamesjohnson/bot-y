# Phase 7: A Reading Has an Age - Context

**Gathered:** 2026-08-13
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

**Goal:** Every reading says when it was taken, and a reading too old to trust is shown as
stale rather than as fact — or says it does not know.

**Requirements:** REQ-21

**Success Criteria** (verbatim from ROADMAP — the contract):

1. Every `Result` records when it was read, and that time is published per watch in `status.json`
2. A reading with no recorded time is shown as UNKNOWN age, never as current — watched going red
3. A reading older than its retailer's current interval is presented as stale in `status.json`, `boty check` and the dashboard, and the staleness is derived from the retailer's own pacing rather than a fixed clock
4. The age survives a service restart, so a restart cannot make a two-day-old reading look fresh
5. `make verify-offline` exits 0, and every gate this phase adds has been watched going red

**Out of scope:** anything about *what* a reading says (v0.2, complete). Also out of scope: the
live `make verify` failure classes and fixture re-capture — recorded in STATE.md as needing
their own plan.

</domain>

<decisions>
## Implementation Decisions

### Already decided — do not re-open

**Staleness is measured against the retailer's own current interval, not a fixed clock.**
A retailer in backoff is *legitimately* checked less often — Walmart at seven refusals sits on
a multi-hour interval and that is the politeness rule working, not a fault. What is dishonest is
not the age; it is presenting an age nobody recorded. The `Pacer` already holds the interval, so
the comparison has a real source rather than a magic number.

**Where no time was recorded, the age is UNKNOWN — never "now".** Same fail-safe direction as
every other unknown in this codebase.

### Claude's Discretion

Where the stamp is carried on `Result`, how it is persisted, the exact rendering in
`boty check` and the dashboard, and how "stale" is expressed in `status.json`.

### The project's standing constraints (they bind this phase)

- **A gate must be watched going red before it is trusted.** Criterion 2 says it in as many words.
- **Never amend a success criterion to make it meetable.** Held four times now — Phases 3.1, 4,
  5 and 6 each recorded something unmet or partial rather than reword it.
- **UNKNOWN is never a verdict.** A missing stamp must not become a plausible one.
- **Every criterion verified by something executable.** `make verify-offline` is the gate.
- **Never write a real store number or host identity.** `identity_check` runs at commit time and
  has rejected commits in this repo before.
- **Politeness is a hard constraint** — no live probing to test this.

</decisions>

<code_context>
## Existing Code Insights

Full analysis comes from the pattern map. Known starting points:

- **`boty/models.py`** — `Result` and `Watch`. The stamp is a fifth pass down a groove cut four
  times: `rung`, `extraction`, the widened `degraded`, and `store` (Phase 5). Follow it.
- **`boty/retailers.py`** — every `check_*` return path, **including the `except Blocked` /
  `except FetchError` arms**. Phase 5 measured 8 return paths in `_verdict_from_html` and a bulk
  edit there missed two; the tests caught it. Expect the same shape.
- **`boty/status.py`** — `status.write` builds rows field-by-field (not `asdict`), so a new field
  is published only if explicitly added. `status.json` has a top-level `updated` for the *cycle*
  — **not** per reading, and it is fresh even when every row is stale. That is the confusion this
  phase removes.
- **`boty/pacing.py`** — the `Pacer` holds each retailer's current interval and persists
  `refusals` + `warned` + `refused_at` to `pacer-state.json`. **`refused_at` is the existing
  precedent for a persisted wall-clock stamp** and is what made the 2026-08-13 reconstruction
  possible at all. `due_at` is deliberately NOT persisted (a synthetic clock restarting at 0.0).
- **`boty/cli.py`** — `_report` renders the `boty check` line and its tags; `watch_cycle` owns
  the cycle.
- **`served/boty/index.html`** — a small read-only status page rendering per-watch tags
  (`degraded`, `dom`, store). Everything user-supplied goes through `esc()`.
- **`state.json`** via `Config.state_path` — currently maps `"retailer:name"` to a bare
  availability string with **no fields at all**. Criterion 4 (age survives a restart) most
  likely lands here, and changing its shape needs a migration story for an existing file.
- **`scripts/mutation_check.py`** — 26 mutations at M1–M20, M25–M28. **M21–M24 are an
  intentional gap; do not fill it.** New idents start at **M29**. Anchor on behaviour, never on
  message prose.
- `make verify-offline` — the gate: exit 0, 778 passed, 26/26 at the start of this phase.

</code_context>

<specifics>
## Specific Ideas

**REQ-21** — a reading states when it was taken; one too old to trust is presented as stale
rather than fact; where nothing was recorded the age is UNKNOWN.

**The measurement that opened it (2026-08-13).** Dan asked when the Amazon and Walmart GO Plus +
watches last read `out_of_stock`. Reconstructed only from refusal history:

- **Amazon** — early 2026-08-13, before ~06:37. A refusal streak of 2 began then and the counter
  had reset, which only happens on a successful read.
- **Walmart** — **could not be established.** No later than 2026-08-12 16:49, plausibly
  2026-08-11. A service restart at 16:49:57 zeroed the refusal counter and destroyed the
  evidence. The reconstruction worked only because `pacer-state.json` persists `refused_at`, and
  it stopped working exactly where that persistence began.

Full detail in `.planning/seeds/a-reading-does-not-carry-its-age.md`.

</specifics>

<deferred>
## Deferred Ideas

- **`QUESTIONS.md` § 0f** — `WALMART_STORE_ID` is still unset, so both Walmart watches read
  UNKNOWN for want of a pin. Unrelated to this phase and not to be closed by it.
- **`QUESTIONS.md` § 0e** — pushed public history carries host geolocation and this host's IP.
- **The live `make verify` classes** (no Chrome binary; intermittent challenge pages) — recorded,
  unowned, needing their own plan.
- **No `.planning/` contents gate** for the leaked-markup class that reached a committed file
  during v0.2, plus two smaller candidates (zero-width spaces, the `store '<n>'` prose carrier in
  `identity_check`). Logged in v0.2's audit, unbuilt.

</deferred>
