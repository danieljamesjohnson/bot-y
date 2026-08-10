# Requirements: bot-y

**Current milestone: v0.2 — Say Only What You Measured** (scoped 2026-08-10).
v1.0.0 remains open and untagged: its definition of done includes *"Dan has
successfully bought a Pokémon GO Plus +"*, which is a market condition, and the
milestone audit recommended against tagging it as shipped. **The v1.0 numbering was
itself an overclaim** — declared before the project had shipped, published or bought
anything — and v0.2 is the correction.

## Definition of Done

v1.0 ships when **both** are true:

1. Five or more retailers report stock with all control products green (of ~7 targeted: GameStop, Walmart, Best Buy, Pokémon Center, Nintendo, Target, Amazon). *Standing at four after Phase 3; Phase 3.1 adds Target and Amazon, which clears this.*
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

- [x] **REQ-01**: Extraction logic is testable offline against saved HTML fixtures, with no network access.
- [x] **REQ-02**: Tests assert the three-state contract explicitly — in particular that an unparseable page produces UNKNOWN and never OUT_OF_STOCK — and that seller filtering plus the price ceiling each independently suppress a marketplace listing.
- [x] **REQ-03**: `boty/` carries type hints and passes a static type check.
- [x] **REQ-12**: A single `make verify` runs every mechanical check — offline fixture tests, static types, live control-product health, and a mutation check that corrupts an extractor — and exits non-zero if any fails. Phase success criteria are stated in terms of it, so verification is an exit code rather than a judgement.

### Phase 2 — Five Retailers Green

- [x] **REQ-04**: Best Buy's primary path must work without credentials. Impersonated HTTP is refused at the connection layer (verified: HTTP/2 stream reset, HTTP/1.1 timeout, across chrome and safari fingerprints), so rung 2 was the plan — but the official API requires manual approval AND a non-free email domain, which most people cloning this repo cannot satisfy. Best Buy therefore escalates to rung 3 (browser, flagged DEGRADED). The official API remains supported as an OPTIONAL enhancement for anyone who has a key: when `BESTBUY_API_KEY` is set, prefer it and drop the DEGRADED flag, since it is strictly more reliable.
- [x] **REQ-05**: Pokémon Center and the Nintendo store each report stock for a real product, or are documented as unreachable with the evidence that established it.
- [x] **REQ-06**: Every configured retailer has at least one control watch. A retailer without one is reported unhealthy — an unverified detector is treated as a broken one.

### Phase 3 — The Hard Two

- [x] **REQ-07**: Target and Amazon are each either working or documented as unreachable with evidence. Any retailer reached via a browser is flagged DEGRADED in the support matrix and in `boty check` output.
- [x] **REQ-07a** *(revises REQ-07, Phase 3.1)*: Target and Amazon are **supported**, not dropped. Phase 3 satisfied REQ-07 by documenting both as refused on a reading of their Terms of Use; that decision was reversed 2026-08-03. The evidence Phase 3 gathered stands — only the conclusion changes. A retailer is dropped only when it is technically unreachable, and the reason recorded is the observation, not a policy reading.
- [x] **REQ-13**: Every row of the support matrix states four things a reader can check independently: the escalation rung reached, **what was extracted off the page** (`structured` / `dom` / `—`, added 2026-08-03 by 03.1-05), the retailer's `robots.txt` position on the path used, and its terms position. Where those disagree — as they do at Target, whose robots.txt permits `/p/` and publishes a product sitemap while its terms forbid extraction — the matrix shows the disagreement rather than only the verdict it resolved to. A reader should be able to reach their own conclusion from the same facts.
- [x] **REQ-08**: A full `boty check` completes in under two minutes at ~7 retailers, sequentially.
  **Measured at four retailers, not seven, and that is not a shortfall in the
  measurement — it is the shipped configuration.** Three of the roadmap's seven
  are rung 4 (Pokémon Center, Amazon, Target), each refused in writing or after
  a ladder walked to exhaustion, so a seven-retailer pass cannot be run and
  extrapolating one would invent the number this requirement exists to pin.
  What was measured, under the service's own `EnvironmentFile`: **61.4 s** for a
  manual pass at 10 watches across 4 retailers (one on rung 3), and **35.0 s**
  published by `boty.service`'s own next cycle for the same config — the
  difference being one transient `curl: (28)` timeout, which read UNKNOWN rather
  than OUT_OF_STOCK. Both are readable off `served/boty/status.json`'s
  `duration_seconds` rather than re-timed by hand. Evidence:
  `docs/retailer-evidence.md` § *REQ-08: how long a full pass actually takes*.

### Phase 4 — Open Source Ready

- [x] **REQ-09**: `docs/adding-a-retailer.md` walks a contributor through a real adapter end to end and states why a control product is mandatory.
- [x] **REQ-10**: CI runs lint, type check and the offline test suite on every PR.
- [~] **REQ-11**: ~~`pip install bot-y` works from PyPI, and a v1.0.0 tag exists.~~ **DESCOPED from v1.0 on 2026-08-07** — not met, not reworded, and struck through rather than deleted so the withdrawn promise stays visible. Dan: *"Let's kill those 2 since I wouldn't publish it without more real testing."* Nothing technical blocks it (`make release-check` → 10/10, artefacts proven in a clean venv); the handoff card is on disk. Carry it into a later milestone if the project is published.

### Milestone v0.2 — Say Only What You Measured

<!-- Every one of these closes a claim the system was making without having measured it.
     Scoped 2026-08-10 from four days of live operation after Phase 4. v1.0.0 stays open
     and untagged; none of these depend on it and none of them close it. -->

- [ ] **REQ-14**: A Walmart reading states which store it came from, and a reading from an unpinned or unexpected store is UNKNOWN rather than a verdict. Measured 2026-08-09: the same URL returned `OUT_OF_STOCK`/$3.17 to the daemon and `IN_STOCK`/$2.42 to three consecutive live reads minutes later. The differing **price** is what proves the mechanism — a parser bug does not change a price; two different stores answered. Applies to the GO Plus + product watch, not only the control.
- [ ] **REQ-15**: No alert names a cause that was not measured. The two live counterexamples are the whole requirement: *"the detector is probably broken"* fired while the detector demonstrably worked, and *"we are asking too often"* kept firing after backing off to a 6-hour interval had been observed not to help. Where the cause is unknown, the alert says so.
- [ ] **REQ-16**: A notification is sent only when a human decision changes the outcome. A refusal the backoff is actively handling is recorded, not pushed; a refusal that outlasts the cap is pushed once; a detector producing a *wrong* verdict is pushed immediately. Recording and notifying stay separate — a retailer that is not being watched right now is real information even when there is no action to take.
- [ ] **REQ-17**: The price ceiling applies to the **delivered total**, not the item price, and a shipping cost that cannot be resolved produces UNKNOWN rather than a pass. A $54.99 listing with $45 shipping currently defeats one of only two defences against a reseller alert.
- [ ] **REQ-18**: Every claim in the README support matrix is bound to the code it describes. Today the **Rung** cell is not: mutating `check_amazon` to return `Rung.BROWSER`, directly contradicting the shipped `| Amazon | 1 | dom |` row, left 131 tests green. Routing and Extraction are already pinned; Rung is the gap.
- [ ] **REQ-19**: Files that ship to a stranger are gated on their contents, not their existence. `CHANGELOG.md` shipped with leaked tool-call markup for an entire phase — `MANIFEST.in` puts it in the sdist and `pyproject.toml` points installers at it — because `release_check.py` asserts only that the file exists and `_changelog_version` reads only its first heading. A workflow file added under `.github/workflows/` likewise escapes the pin, exit-code, timeout and runner rules while the suite stays green.
- [ ] **REQ-20**: The package version and the project's own milestone version agree, and cannot silently diverge. Rolling `pyproject.toml` from the aspirational `1.0.0` to `0.2.0` is safe only because publishing was deferred — nothing was tagged or uploaded, so nobody can be pinned to a 1.0.0 that exists.

## Non-Functional Requirements

- **Trustworthiness over coverage.** Where they conflict, correctness wins. Ten provably-correct retailers beat a hundred maybes. This is the tiebreaker for every scoping decision.
- **No-browser-first.** A browser is a last resort. It is slower, heavier, and empirically less effective against these targets than TLS impersonation.
- **Polite polling.** 5-minute default with jitter. Never sub-minute.
- **Secrets never in the repo.** Credentials live in a mode-600 env file loaded by systemd, set through a tool that prompts hidden and verifies before writing.
- **Small dependency surface.** Every dependency is another thing that can silently break a monitor.
- **Works from a fresh clone.** A retailer's PRIMARY path must work for someone who clones the repo and adds no credentials. Paths requiring a credential most people cannot obtain — manual approval, a paid domain, a commercial agreement — may be supported as an OPTIONAL enhancement, but never as the documented way that retailer works. A capability the average user cannot enable is a footnote, not support.

## Acceptance Criteria

- `boty check` shows ≥5 retailers, every control in stock, no health warnings
- `make verify` exits 0 on a healthy tree
- Deliberately breaking an extractor makes `make verify` exit non-zero
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

## Traceability

Maintained by `gsd-tools`; a requirement flips to Complete when its phase completes.

| Requirement | Phase | Status |
|---|---|---|
| REQ-01 | Phase 1 | Complete |
| REQ-02 | Phase 1 | Complete |
| REQ-03 | Phase 1 | Complete |
| REQ-04 | Phase 2 | Complete |
| REQ-05 | Phase 2 | Complete |
| REQ-06 | Phase 2 | Complete |
| REQ-07 | Phase 3 | Complete |
| REQ-08 | Phase 3 | Complete |
| REQ-09 | Phase 4 | Complete |
| REQ-10 | Phase 4 | **Complete (04-04)** — `.github/workflows/ci.yml` exists and runs on every pull request with no branch or path filter. One job, one step, `make verify-offline`, which since 04-03 runs identity → lint → tests → types → fixtures → controls (skipped offline) → mutation. `permissions: contents: read`, both actions first-party and SHA-pinned, `timeout-minutes: 15`, Python 3.10 — the floor `requires-python` declares, rehearsed end to end in a `python:3.10` container from a shallow clone before the YAML was written. The contract is machine-checked by `tests/test_ci_workflow.py` (44 tests, 26 of them corruption tests), and the gate was watched failing against the real file for two single-token breakages. **What is NOT observed:** no pull request has run this workflow yet — the first live run is the first PR, and that is stated in the summary rather than implied away. What 04-03 left, for the record: it landed the **lint half**: ruff configured, every finding resolved, a `lint` stage inside `make verify` watched going red. That is the precondition, not the requirement. REQ-10's own text is "CI runs lint, type check and the offline test suite **on every PR**", and at the end of wave 3 `ls .github/` returns *No such file or directory* — there is no workflow, so nothing runs on any PR. **04-04** is the plan that closes this, and it is the one carrying `requirements: [REQ-10]` in its frontmatter; 04-03 carries none |
| REQ-11 | Phase 4 | **DESCOPED from v1.0 (2026-08-07)** — Dan: *"Let's kill those 2 since I wouldn't publish it without more real testing."* Not met and not reworded; the criterion was wrong scope for v1.0, which is a different act from rewording one to pass. History, unedited: Pending — 04-02 shipped the licence and the packaging metadata REQ-11 rests on, and its frontmatter claimed the requirement on landing. It does not close it. REQ-11's own text is `pip install bot-y` works **from PyPI**, and a **v1.0.0** tag exists: at the end of wave 2 the version is `0.1.0`, `git tag -l` is empty, and nothing has been published. **04-06** is the plan that closes this, by measuring what Dan actually publishes rather than by asserting it here. **04-06 ran on 2026-08-06 and did NOT close it — the honest outcome is that it stays Pending.** Dan deferred publishing, verbatim: *"i don't think we need to host it yet. it's probably not quite ready for that"*. Re-measured at close rather than assumed: `https://pypi.org/pypi/bot-y/json` → **HTTP 404**, `git tag -l` → empty, `git ls-remote --tags origin` → **0 refs**. Both halves of REQ-11's text are therefore unproven, and no criterion was reworded to make it closeable. What 04-06 *did* deliver is the handoff card at `.planning/phases/04-open-source-ready/04-06-HANDOFF.md`, which carries every exact string the publish needs, read off the shipped tree — so closing REQ-11 later needs no replanning, only the four steps on that card |
| REQ-12 | Phase 1 | Complete |
| REQ-07a | Phase 3.1 | Complete — **both retailers registered, and both on an observation rather than a policy reading, which is the whole point of this requirement.** *(This cell described the mid-phase state until 2026-08-03: "Target stays dropped … Amazon still unprobed". Both halves were overtaken by the plans that followed and the narrative is replaced rather than appended to, because a status cell is not a log.)* **Target** — reachable at rung 1 but *empty* (no price, availability or seller anywhere in the HTML; stock renders from `redsky.target.com`, `Disallow: /`). Dan answered the `robots.txt` question in `QUESTIONS.md` 0d, so 03.1-02 registered it at **rung 3 + `dom`**, reading the add-to-cart control off the rendered page — **control-only**, because Target has delisted the GO Plus + (TCIN `88714054`, HTTP 200 as late as 2025-05, now 404). **Amazon** — 03.1-03 made this repo's first live `/dp/` requests: three, all HTTP 200, no challenge, no `BLOCK_PHRASES` match. No structured data at all, but `<input id="add-to-cart-button">` is in the rung-1 bytes, so it registered at **rung 1 + `dom`** (shape C). Phase 3 had dropped it on its Conditions of Use having never sent a request; the technical answer is that it serves us. Six retailers ship, 6/6 control-verified. The gate that makes this mechanical is `evidence_check` rule 6 — a `REFUSED` verdict must cite an observation carrying a status code, a byte count or a matched block phrase, watched failing on a prose-only body |
| REQ-14 | Phase 5 | Pending |
| REQ-15 | Phase 5 | Pending |
| REQ-16 | Phase 5 | Pending |
| REQ-17 | Phase 6 | Pending |
| REQ-18 | Phase 6 | Pending |
| REQ-19 | Phase 6 | Pending |
| REQ-20 | Phase 6 | Pending |
| REQ-13 | Phase 3.1 | Complete — 03.1-01 built six matrix columns with a two-directional `⚠ disagree` rule; 03.1-05 grew the row contract to a fourth field, **Extraction** (`structured` / `dom` / `—`), tied to the Rung cell in both directions by `_extraction_mismatch` and watched failing each way on a corrupted copy of the real README |
