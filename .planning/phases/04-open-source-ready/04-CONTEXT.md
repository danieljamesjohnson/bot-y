# Phase 4: Open Source Ready - Context

**Gathered:** 2026-08-04
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Someone who isn't me can install bot-y, add a retailer, and open a PR that I can
trust.

Requirements: REQ-09 (contributor guide for adding an adapter, including why a
control product is mandatory), REQ-10 (CI runs lint, type check and the offline
test suite on every PR), REQ-11 (`pip install bot-y` works from PyPI and a
v1.0.0 tag exists).

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — discuss phase was
skipped per user setting. Use ROADMAP phase goal, success criteria, and
codebase conventions to guide decisions.

### NOT at Claude's discretion — two criteria require Dan

Recorded here so planning does not quietly assume otherwise:

1. **Criterion 3 — `pip install bot-y` works from PyPI.** Publishing needs a
   PyPI API token this agent cannot obtain, and a first publish permanently
   claims the project name. Plan the packaging, the metadata and the release
   workflow so that the publish is one authenticated command (or one tag push),
   but do not publish.
2. **Criterion 5 — a tagged v1.0.0 release exists.** Outward-facing and, once
   pushed, visible to anyone watching the repo. Prepare the tag and release
   notes; Dan pushes.

Everything else in this phase is verifiable offline and should be carried to
completion without waiting on either.

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research. Known constraints
that planning must not rediscover the hard way:

- **`make verify` is the phase gate**, by design — every phase since Phase 1 is
  verified as "`make verify` exits 0, plus these specific observable facts."
  Whatever CI runs must not weaken it, and must stay offline: the test suite
  asserts its own network isolation.
- **The identity guard is a commit-time hook** (`scripts/identity_check.py` +
  tracked `hooks/pre-commit`, installed with `make hooks`). It scans every
  tracked file, not just `tests/fixtures/`. CI must run it too — a hook only
  protects the machine that installed it, and the leak this project already had
  reached `origin/main` through a `.planning/` file.
- **`nodriver` is an optional extra and is AGPL-3.0** against this project's
  MIT. Packaging must keep it optional and must not let a default install pull
  a browser stack.
- **Six retailers ship; only four can alert on the GO Plus +** (Best Buy and
  Target are control-only). The README support matrix says so in prose, and its
  `rung`/`extraction`/`degraded` cells were verified cell-by-cell against live
  status output in 03.1-04. Any doc rewrite must preserve that agreement.
- **The service and the tree can disagree silently.** `make verify` runs the
  tree; `boty.service` runs whatever it was started with. Restarting is part of
  shipping.

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the ROADMAP — discuss phase skipped. The
ROADMAP names three plans:

- 04-01: Contributor docs — adding a retailer, the control-product requirement,
  the UNKNOWN contract
- 04-02: GitHub Actions CI — lint, mypy, tests on fixtures, no network
- 04-03: Packaging and v1.0.0 release

</specifics>

<deferred>
## Deferred Ideas

None — discuss phase skipped. Items already deliberately out of scope are
recorded under "Out of Roadmap" in ROADMAP.md (generic URL extraction, async,
a formal plugin API, auto-checkout, a web UI beyond the read-only status page).

</deferred>
