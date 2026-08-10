# Phase 6: Claims With Gates Under Them - Context

**Gathered:** 2026-08-10
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

**Goal:** Every claim this project publishes — a price filter, a matrix row, a shipped file, a
version number — has a gate under it that has been watched going red.

**Requirements:** REQ-17, REQ-18, REQ-19, REQ-20

**Success Criteria** (verbatim from ROADMAP — these are the contract):

1. The price ceiling applies to the delivered total; an unresolvable shipping cost is UNKNOWN, not a pass
2. Mutating an adapter's `Rung` against a contradicting README row turns a test red — today it leaves 131 green
3. A workflow file added under `.github/workflows/` is covered by the pin, exit-code, timeout and runner rules
4. `CHANGELOG.md` is gated on its **contents**, not its existence — the leaked-markup class cannot ship again
5. `pyproject.toml` reads `0.2.0`, agrees with the project's milestone version, and cannot silently diverge

**Why second** (from the ROADMAP): none of this changes what a *reading* means, so it could not
block Phase 5 — but all of it is the same shape as the bugs Phase 5 fixed, one level up: **a
claim asserted at the producing end with nothing checking it at the consuming one.**

**Out of scope:** anything about what a product reading means (Phase 5, complete). Also out of
scope: the live `make verify` failure classes and the fixture re-capture they need — that is
recorded in STATE.md and `deferred-items.md` as needing its own plan, and is not this phase's.

</domain>

<decisions>
## Implementation Decisions

### Already decided — do not re-open

**REQ-20's version roll is safe *only because publishing was deferred*.** `pyproject.toml` goes
`1.0.0` → `0.2.0`. Nothing was ever tagged or uploaded (`git tag -l` empty, `git ls-remote
--tags origin` 0 refs, PyPI 404 for both `bot-y` and `bot-y/1.0.0` as of Phase 4's close), so
nobody can be pinned to a 1.0.0 that exists. **The v1.0 numbering was itself the same overclaim
this milestone corrects everywhere else** — declared before the project had shipped, published
or bought anything. Do not treat the roll as a normal version bump; it is the correction.

**Note on criterion 1's origin.** The delivered-total hole was found while researching eBay,
which is now **closed** (developer registration rejected, 2026-08-10). The finding outlived the
retailer: **Walmart carries marketplace sellers**, so a $54.99 listing with $45 shipping defeats
one of only two reseller defences *today*. Do not scope this to a retailer that no longer
matters.

### Claude's Discretion

Where the delivered total is computed and carried, how the Rung binding is expressed, the shape
of the workflow-file and CHANGELOG content gates, and the mechanism that keeps `pyproject.toml`
and the milestone version from diverging. Follow the ROADMAP criteria, the requirements, and the
conventions already in this codebase.

### The project's standing constraints (they bind this phase)

- **Never amend a success criterion to make it meetable.** Phase 3.1 declined exactly that
  rewrite; Phase 4 recorded two criteria UNMET rather than reword them; Phase 5 held the line
  again. If a criterion cannot be met, record it unmet with the reason and the date.
- **A gate must be watched going red before it is trusted.** This is the whole subject of this
  phase, so it applies to this phase's own gates with double force. Criterion 2 is literally a
  report that an existing gate *cannot* go red.
- **UNKNOWN is never a verdict, and never OUT_OF_STOCK.** Criterion 1 says an unresolvable
  shipping cost is UNKNOWN, not a pass.
- **Every criterion verified by something executable** — `make verify` exists because an LLM's
  judgement can be confidently wrong in the same direction as the code that produced it.
- **Never write a real store number or any host identity** into a tracked file. `identity_check`
  runs at commit time over every tracked file and is load-bearing.

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research. Known starting points:

- **Criterion 1** — the price ceiling lives with the existing `max_price` / seller filtering
  logic (`boty/models.py`, `boty/retailers.py`, and the offer parsing in `boty/parse.py`).
  Phase 1 already has a test proving "a marketplace-seller offer above the price ceiling is not
  alertable"; this criterion widens *what the ceiling is measured against*.
- **Criterion 2** — `tests/test_support_matrix.py` already binds the README's **Routing** and
  **Extraction** cells to the code in both directions (`_extraction_mismatch`, built in Phase
  3.1 and watched failing each way against a corrupted copy of the real README). **`Rung` is the
  one cell with no binding** — that file is the direct analog to copy.
- **Criteria 3 and 4** — `scripts/release_check.py` (asserts `CHANGELOG.md` *exists*;
  `_changelog_version` reads only its first heading), `tests/test_ci_workflow.py` (67 tests
  reading `.github/workflows/ci.yml`, but keyed to that one file rather than to the directory),
  `MANIFEST.in` and `pyproject.toml` (which together put `CHANGELOG.md` in the sdist and point
  installers at it — that is why its contents matter to a stranger).
- **Criterion 5** — `pyproject.toml`'s version, and whatever reads the milestone version
  (`.planning/STATE.md` frontmatter carries `milestone: v0.2`).
- `scripts/mutation_check.py` — 16 mutations at Phase 5's close, all observed caught. Criterion
  2's gate needs a mutation of exactly the shape the criterion describes.
- `make verify` / `make verify-offline` — one command, one exit code. `verify-offline` is the
  gate that must be green (Phase 5 close: exit 0, 667 passed, 16/16 mutations).

### What Phase 5 just changed underneath this phase

Phase 5 shipped and its post-review fixes landed. Relevant to planning:

- `boty/models.py` gained `Watch.store_id`, `Result.store`, `STORE_SCOPED` and `KNOWN_RETAILERS`;
  `boty/config.py` gained `_retailer` (unknown retailer spellings are now **refused**, not
  silently accepted) and `_store_id`.
- `boty/monitor.py` has `CAUSE_UNKNOWN` and a rewritten `assess_health`; `boty/notify.py` has
  `_redact_store_numbers` over `h.reason` and each `failing_controls` entry.
- `boty/pacing.py` persists to `pacer-state.json` (`refusals` + `warned` + a wall-clock stamp;
  `due_at` deliberately not persisted); `watch_cycle` carries `warned` forward across cycles.
- `scripts/identity_check.py` catches store numbers in YAML config keys, in every spelling.

</code_context>

<specifics>
## Specific Ideas

**REQ-17** — the ceiling applies to the delivered total, not the item price; a shipping cost
that cannot be resolved produces UNKNOWN rather than a pass.

**REQ-18** — every claim in the README support matrix is bound to the code it describes. The
measured gap: mutating `check_amazon` to return `Rung.BROWSER`, directly contradicting the
shipped `| Amazon | 1 | dom |` row, **left 131 tests green**.

**REQ-19** — files that ship to a stranger are gated on their contents, not their existence.
`CHANGELOG.md` shipped with **leaked tool-call markup for an entire phase**, because
`release_check.py` asserts only that the file exists. A workflow file added under
`.github/workflows/` likewise escapes the pin, exit-code, timeout and runner rules while the
suite stays green.

*(This class is not hypothetical and recurred during Phase 5: `05-02-PLAN.md` was written with a
stray `</content>`/`</invoke>` pair at its end, caught by a planning agent before commit. The
defect REQ-19 describes is live and ongoing, not historical.)*

**REQ-20** — the package version and the project's own milestone version agree and cannot
silently diverge.

</specifics>

<deferred>
## Deferred Ideas

**Carried from Phase 5, explicitly not this phase's work:**

- The live `make verify` failure, re-measured 2026-08-10 in **three** classes: Best Buy and
  Target cannot run (no Chrome/Chromium binary, though STATE.md records that Playwright's
  Chromium works when `BOTY_BROWSER_PATH` points at it); the Walmart/Amazon challenge class did
  **not** manifest on that pass, so it is intermittent rather than permanent; and 1/6 not
  reading IN_STOCK is Walmart through Phase 5's own config-gap guard, because `make verify` runs
  with no `WALMART_STORE_ID`. Needs its own plan — polite probing plus fixture re-capture.
- **The deployment itself.** Dan answered `defer` on 2026-08-10: the daemon still runs
  2026-08-04 code (`MainPID=3059142`). Everything Phase 5 built is in the tree and not on the
  wire, including the fix for the unpinned-Walmart alert that is live right now. `QUESTIONS.md`
  § 0f holds the open question.
- `scripts/identity_check.py` has no rule for the `store '<n>'` **prose** carrier — the shape
  CR-03 actually leaked through. Recorded rather than switched on blind; it needs a sweep of the
  tracked tree first.
- `QUESTIONS.md` § 0e (public git history) remains open — a decision, not a blocker.

</deferred>
