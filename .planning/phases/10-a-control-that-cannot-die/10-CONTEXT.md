# Phase 10: A Control That Cannot Die - Context

**Gathered:** 2026-09-02
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

A control that stops resolving is reported as a **dead control** — a fact about our
configuration — and is never reported as a refusal or a broken detector, which are facts about
the retailer.

**Requirement:** REQ-24 — *"A control product **cannot be discontinued out from under the
monitor** without that being distinguishable from a block. A control that stops resolving is
reported as a **dead control** … and never as a refusal or as a detector failure … Best Buy's
current dead control is repaired."*

**Depends on:** Nothing. Independent of phases 8 and 9, both of which are complete in the tree.

**Definition of Done item 3 governs the evidence:** *"REQ-24's repair is confirmed against a real
Best Buy control reading, and the dead-control state is reachable in a test without one."*
Both halves matter — the repair needs the wire, the state does not.

</domain>

<decisions>
## Implementation Decisions

### LOCKED — Dan's answer of 2026-09-02, recorded in `QUESTIONS.md` § 0g

**Up to THREE live requests, to Best Buy only.** Not Amazon, Target or Walmart — the three
already refusing us — and not GameStop or Nintendo. Spaced, not burst.

**A refusal IS the measurement.** `README.md` records Best Buy as *"unread — refused at the
connection layer"*. If that is what a read returns, it is written down as a measured result —
not retried around, not reported as an inconclusive attempt, and not rounded into "the control
could not be verified."

**No `boty check`** — it requests *every* retailer and writes the daemon's live
`served/boty/status.json`. The three permitted reads must be made directly and narrowly.

### A capability correction this phase inherits

v0.3's records say `make verify` cannot run Best Buy's control here for want of Chrome/Chromium.
**Measured 2026-09-02: that is stale.** Playwright chromium is present at `~/.cache/ms-playwright`
(three builds including a headless shell), and Best Buy is rung 3 so it needs one.
`boty/browser.py` reads `BOTY_BROWSER_PATH`. Criterion 3 was never blocked on capability.

### Claude's Discretion

Everything else — discuss was skipped per `workflow.skip_discuss=true`. Use the ROADMAP goal, the
five criteria, `CLAUDE.md`'s evidence standard, and existing conventions.

</decisions>

<code_context>
## Existing Code Insights

- `boty/models.py` — `Result`, `Availability`, `Health`, and the `rung`/`extraction` axes. The
  three states criterion 1 wants distinguished must live somewhere here or in `monitor.py`.
- `boty/monitor.py` — `assess_health`, `_is_store_gap`, and the health arm that today reports a
  dead control as a broken detector.
- `boty/retailers.py` — the Best Buy adapter and its SKU handling.
- `config/products.yaml` — the controls. Best Buy's control is `target: "6216393"` with
  `control: true` around line 210.
- `tests/fixtures/bestbuy/unresolved-sku` — captures SKU 6577129 resolving to no product: Best
  Buy returns a search page rather than a 404. That fixture is how the dead-control state is
  reachable **without** a live read, which is Definition of Done item 3's second half.
- `scripts/control_check.py` — the live control harness; `make verify` runs it, `make
  verify-offline` skips it.
- `README.md`'s support matrix is **gated against the code** and cannot drift.

</code_context>

<specifics>
## Specific Ideas

**Criterion 1 is the heart of it: three states, distinct and asserted separately.**
*dead control* (our SKU no longer resolves) — a fact about **our configuration**.
*refused* (the retailer served a challenge) — a fact about **the retailer**.
*detector broken* (the page arrived and the extractor could not read it) — a fact about **us**.
The ROADMAP states plainly that today the first is reported as the third. That is the defect.

**Criterion 2 has a conjunction that is easy to miss:** a dead control must not describe the
retailer as refusing us, **and must not silence a real refusal if both are true at once.** Both
halves need asserting.

**Criterion 4 is the durable-control rule** — written down and applied to **every existing
control**, with any control failing it **named**. The ROADMAP gives the reasoning: Best Buy's
died because it was a specific game SKU, and *"a control that can be discontinued eventually
will be."* Expect this to name more than one control; naming them is the deliverable, not a
failure.

**Criterion 3 permits a replacement, not only a repair** — *"or replaced with one that reads,
with the replacement's durability argued."* The replacement's durability must satisfy
criterion 4's own rule, which is the honest ordering: write the rule, then pick a control that
passes it.

</specifics>

<deferred>
## Deferred Ideas

- **No `systemctl restart boty`.** Phases 8 and 9 are complete in the tree and not on the wire;
  that restart is Dan's and is still open. It now carries phases 8 and 9 together.
- **No write to `state.json`, `pacer-state.json` or `served/boty/status.json`** — the running
  daemon owns them.
- **Phase 11 is not this phase.** Establishing Amazon/Target/Walmart's true ladder position is
  REQ-25's work and spends a probe budget at the refusing retailers. Dan must be asked before it
  starts.

</deferred>
