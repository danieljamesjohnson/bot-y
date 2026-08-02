# Phase 2: Five Retailers Green - Context

**Gathered:** 2026-08-02
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Five retailers reporting trustworthy stock for the GO Plus +, each
control-verified. This is the MVP bar.

In scope: Best Buy, Pokémon Center, Nintendo store adapters, each with a control
product, fixture-backed tests, and a support-matrix entry recording which
escalation rung it landed on.

Out of scope: Target and Amazon (Phase 3 — they are the hard two), PyPI
packaging and CI (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### Locked by prior evidence — do not relitigate

**Best Buy's primary path is rung 3 (browser), flagged DEGRADED.** Impersonated
HTTP is refused at the connection layer — verified across `chrome` and `safari`
fingerprints: HTTP/2 stream reset, HTTP/1.1 timeout. That is a wall, not a
tuning problem. The official API was the plan, but signup requires manual
approval AND rejects free email domains, so anyone cloning this repo hits the
same wall. Therefore: browser path works with no credentials and carries the
DEGRADED flag; when `BESTBUY_API_KEY` is set, prefer the API and drop the flag.
Nothing waits on the key. (REQ-04, and `QUESTIONS.md`.)

**Every retailer needs a control watch.** Phase 1's code review (WR-04) made
this mechanical: `scripts/control_check.py` now fails the gate when a configured
retailer has zero controls. Adding an adapter without a control will break
`make verify` by design. Pick controls the way `config/products.yaml` already
documents — first-party, restocked routinely, never a marketplace buy-box
fight. A console is a bad control on a marketplace.

**A retailer that cannot be reached is documented, not faked.** The project's
core value is that a reading is trustworthy. "Unreachable, here is the evidence"
is an acceptable outcome; a detector that reports OUT_OF_STOCK because it was
blocked is not. Anything reached via a browser is flagged DEGRADED in both the
support matrix and `boty check` output.

### Claude's discretion

Adapter internals, control-product selection, fixture naming, and how the
support matrix is rendered. Follow existing codebase conventions.

</decisions>

<code_context>
## Existing Code Insights

Phase 1 delivered infrastructure this phase should use rather than reinvent:

- **`boty capture-fixture <retailer> <url>`** saves a live page plus a JSON
  sidecar recording capture time and observed stock state. Every new adapter
  gets fixtures this way. `boty.fixtures.load` reads them with no network.
- **`tests/conftest.py` has an autouse network guard** that raises a
  `BaseException` subclass, deliberately un-swallowable by `boty.fetch.get`'s
  blanket `except Exception`. A new adapter's tests cannot silently hit the
  network. If a test needs a transport the guard does not yet patch, extend the
  guard rather than working around it.
- **`make verify`** runs tests, mypy, fixture staleness, live controls, and a
  5-mutation check, and exits non-zero if any fails. Phase 2's criterion 7 is
  literally "it exits 0". Note M4/M5 now mutate `models.py` and `monitor.py`.
- **mypy is configured with `disallow_untyped_defs`** over `boty` and `scripts`.
  New adapter code must be fully annotated or the gate fails.
- **Retailer dispatch lives in `boty/retailers.py`**; extraction in
  `boty/parse.py` (schema.org ld+json and Next.js `__NEXT_DATA__` today).

### Carried-forward hazard from Phase 1's review

An unconfigured retailer key previously produced a confident `OUT_OF_STOCK`
from an empty allow-list (WR-03, now fixed to UNKNOWN). When adding retailers,
keep that discipline: absence of knowledge is UNKNOWN, never a verdict.

Deferred Info finding **IN-03** is directly relevant here: a compound
`@type: ["Product", "ProductModel"]` currently reads as an unexplained UNKNOWN,
and Pokémon Center / Nintendo are exactly the kind of sites likely to emit
compound `@type`. Consider fixing it as part of whichever adapter hits it.

</code_context>

<specifics>
## Specific Ideas

- Best Buy's browser rung needs a browser driver (the roadmap names `nodriver`).
  That is a new heavyweight dependency — it should not become a hard install
  requirement for contributors who only need the HTTP retailers.
- Pokémon Center is first-party for Pokémon goods and is plausibly the single
  most likely genuine restock source for the GO Plus +.
- Nintendo's store is first-party for the hardware itself.
- The three adapters are independent and can be planned as parallel work.

</specifics>

<deferred>
## Deferred Ideas

- Target and Amazon — Phase 3.
- Async fetching and a plugin API — deferred project-wide.
- The 6 open Info findings from `01-REVIEW.md`, except IN-03 where an adapter
  hits it.

</deferred>
