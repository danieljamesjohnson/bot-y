# Phase 3: The Hard Two - Context

**Gathered:** 2026-08-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Target and Amazon either working, or documented as unreachable with the evidence
that established it. No silent gaps.

In scope: walking the escalation ladder at Target and Amazon, controls for
whichever land, support-matrix rows, and the `boty check` runtime budget.

Out of scope: PyPI packaging, CI, and the v1.0.0 tag (Phase 4 — and Dan's to
trigger, not this run's).

</domain>

<decisions>
## Locked by prior evidence — do not relitigate

**Both of these are expected to be hostile, and "REFUSED with evidence" is a
successful outcome.** The roadmap says so in its own criteria: "Target reports
stock, **or** the support matrix records what was tried and why it failed."
Phase 2 established the pattern with Pokémon Center — six probes, two
transports, two WAF vendors, byte counts, and a quoted Terms-of-Use clause. Match
that standard. Do not escalate indefinitely to manufacture a REACHABLE.

**Check the Terms of Use before the wall.** Pokémon Center's decisive finding was
not technical: its ToU prohibits automated interaction outright, which is a
better and more durable reason than "we could not get in." Amazon's ToU is
notoriously explicit on this point. Read it first — if a retailer forbids this
in writing, that settles it and no amount of transport work is relevant. A
README claiming we respect robots.txt while the code works around a ToU would be
worse than not supporting the retailer.

**Target history (from `.planning/STATE.md`, do not re-derive):** RedSky is
CAPTCHA-gated even with a warmed cookie session; product pages fetch clean but no
valid `www` TCIN was ever found. Work stopped at three strikes. That is a
starting point, not a conclusion.

**The five-retailer criterion arrived here from Phase 2.** It is now criterion 5
of this phase. Target or Amazon landing satisfies it. If both are rung 4, it is
unmet and recorded as such — never padded with a retailer that does not carry the
GO Plus +. A control-only Micro Center was probed in Phase 2 and explicitly
declined for exactly that reason; that decision stands.

### Claude's discretion

Adapter internals, control selection, fixture naming, matrix rendering. Follow
existing conventions.

</decisions>

<code_context>
## What Phase 2 built that this phase should use

- **Rung 3 exists**: `boty/browser.py` drives Chrome via nodriver behind an
  optional `[browser]` extra. `Rung`/`Result.degraded` flag anything rendered.
  **A browser is not a strict upgrade** — the same headless Chrome that reads
  Best Buy is Cloudflare-walled on gamestop.com, which rung 1 reads on every
  verify run. Reach for it only when a retailer refuses HTTP at the connection
  layer.
- **`BLOCK_PHRASES` now catches Akamai** (`sec-if-cpt-container`,
  `scf-akamai-protected-by`), added *because* Akamai fronts Target. Without it a
  Target refusal would surface as "page shape changed?" and send someone
  debugging an extractor that works. Imperva (`pardon our interruption`,
  `_incapsula_resource`) and DataDome-at-403 are also covered.
- **Do NOT add `datadome` as a block phrase.** Real product pages reference
  DataDome assets while serving genuine content; another project had to revert
  exactly that false positive. `captcha-delivery.com` plus the `var dd={` marker
  is the safer pair if one is ever wanted.
- **`boty capture-fixture --browser`** captures a rendered page. Every adapter
  gets fixtures this way.
- **Controls are mechanically enforced**: `scripts/control_check.py` fails the
  gate when a configured retailer has zero controls. Add a retailer and its
  control in the same task or `make verify` goes red between plans.
- **`make verify` has three verdicts now**: `PASS`, `PASS (INCOMPLETE — some
  controls could not run on this host)`, and `FAIL (<stage>)`. INCOMPLETE exists
  because a green obtained in a shell with browser env exported, while the
  service could not find Chrome, is how a false green shipped in Phase 2 and
  paged Dan at 2am.

### Hazards carried forward

**A rung-3 capture leaks the capturing host's identity.** Phase 2 froze this
repo's own public IP and Akamai EdgeScape geolocation into a committed fixture in
a public repo. `tests/test_fetch.py::test_no_fixture_leaks_the_capturing_hosts_identity`
now guards it — but the guard only knows the markers it was taught. Any new
rung-3 fixture is suspect until checked.

**Daemon-lifetime bugs are not covered by any gate.** The browser transport
leaked zombie Chrome processes and `/tmp` profiles on the live deployment — 13
zombies at 69 minutes — and nothing in `make verify` could see it, because the
teardown tests drive a *fake* nodriver and `make verify` is a one-shot process
measuring a daemon property. If this phase adds browser usage, that class of bug
is still unguarded. Watch for it explicitly rather than trusting green.

**The M2 mutation anchor is an exact source substring** including twelve spaces
of indentation. Refactoring `boty/retailers.py` can drift it and take
`make verify` down as a HARNESS ERROR that looks nothing like its cause.

</code_context>

<specifics>
## Specific Ideas

- **REQ-08 baseline:** a full `boty check` — 10 watches, 4 retailers, one on rung
  3 — took **40 s**, a third of the two-minute budget. Adding two more retailers,
  especially on rung 3, is what could blow it. Measure rather than assume.
- Establish Amazon's reachability *cheaply and early*, before investing in an
  adapter. The roadmap says so explicitly.
- Both plans are independent in principle but both touch `boty/retailers.py`,
  `config/products.yaml` and `tests/test_retailers.py`, so they serialize — the
  same lesson Phase 2 learned the hard way.

</specifics>

<deferred>
## Deferred Ideas

- Phase 4 entirely: PyPI, CI, the v1.0.0 tag.
- The 6 open Info findings from `01-REVIEW.md` and 6 from `02-REVIEW.md`,
  including IN-01 (`scripts/mutation_check.py`'s docstring still says "three
  mutations" against six).
- Async fetching and a plugin API — deferred project-wide.

</deferred>
