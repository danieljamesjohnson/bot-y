---
phase: 02-five-retailers-green
plan: 01
subsystem: fetching
tags: [nodriver, browser, headless-chrome, cdp, escalation-ladder, test-isolation, supply-chain]

requires:
  - phase: 01-detector-safety-net
    provides: "boty.fetch (Page/Blocked/FetchError/BLOCK_PHRASES), the autouse no_network guard, boty.fixtures capture/load, make verify"
provides:
  - "boty/browser.py — rung-3 transport: fetch_rendered() -> Page, over nodriver + headless Chrome"
  - "A `browser` optional-dependency extra, so contributors on the HTTP retailers never pull a browser stack"
  - "An offline network guard that actually covers the browser transport, with a self-test proving it fires"
  - "boty.fixtures.capture(..., browser=True) — rung-3 fixture capture for retailers that refuse rung 1"
  - "docs/retailer-evidence.md — the escalation-ladder evidence log, opened with a real Best Buy verdict"
  - "BOTY_BROWSER_NO_SANDBOX — opt-in, per-host escape hatch for Ubuntu 24.04's userns restriction"
affects: [02-03-bestbuy-adapter, 02-04-pokemon-center-nintendo, 03-target-amazon]

tech-stack:
  added: ["nodriver>=0.38 (optional extra `browser`)"]
  patterns:
    - "Single-seam transport: one module-level function does all browser I/O, so the test guard has exactly one name to patch"
    - "Lazy heavyweight import inside the function body, extending the boty/fixtures.py:82 precedent to an optional extra"
    - "Security downgrades are opt-in env vars that log a warning, never silent defaults"

key-files:
  created:
    - boty/browser.py
    - tests/test_browser.py
    - docs/retailer-evidence.md
  modified:
    - pyproject.toml
    - boty/fixtures.py
    - tests/conftest.py

key-decisions:
  - "Best Buy is REACHABLE on rung 3 — a headless browser reads its product pages, with price and seller both present"
  - "Best Buy's legacy /site/<slug>/<sku>.p URL scheme is uniformly refused; the live scheme is /product/<slug>/<ID> where <ID> is not the SKU"
  - "MARKETPLACES needs no change — Best Buy attributes offers[].seller.name as 'Best Buy', which is already in FIRST_PARTY"
  - "No evidence Best Buy carries the GO Plus + at all; SKU 6577129 in test_retailers.py:316 is unverified"
  - "Chrome's sandbox stays ON by default; BOTY_BROWSER_NO_SANDBOX is opt-in per host because this transport executes retailer JavaScript"
  - "nodriver approved as an optional extra only, after a supply-chain audit — never a hard install requirement"

patterns-established:
  - "Evidence-over-conclusion: docs/retailer-evidence.md records error codes, byte counts and URL forms, not verdicts alone"
  - "Falsify the hypothesis before recording it: the 'physical vs digital' explanation for Best Buy's per-product refusal was tested and disproved"
  - "Prove a guard fires by removing it and watching the test go red, rather than asserting the patch line exists"

requirements-completed: [REQ-04]

duration: 62min
completed: 2026-08-02
---

# Phase 2 Plan 01: Rung-3 Browser Transport Summary

**Best Buy is REACHABLE on rung 3 — a headless browser reads its product pages with price, availability and a first-party seller all present — but only on its current `/product/<slug>/<ID>` URL scheme, and some product pages are reproducibly refused for reasons still unexplained.**

## The Best Buy verdict (02-03 branches on this)

`**Verdict: REACHABLE (rung 3)**` — recorded in `docs/retailer-evidence.md`.

Both questions the plan called load-bearing are answered **YES**:

- **Price is readable.** `offers[].price` is present (`59.99` on the probed
  product), so the WR-01 ceiling hardening in `boty/models.py:73-75` — which
  makes `alertable` False when a ceiling is set and `price is None` — will not
  veto GO Plus + alerts.
- **Seller is readable, and resolves first-party.** `offers[].seller.name` is
  `"Best Buy"`, already in `FIRST_PARTY["bestbuy"]`. The concern that `bestbuy`
  being in `MARKETPLACES` would turn every offer into UNKNOWN **does not bite**,
  because these offers are attributed. **No change to `MARKETPLACES` is needed.**

Three findings change what 02-03 should build:

1. **The legacy `/site/<slug>/<sku>.p` scheme is uniformly refused** —
   `ERR_HTTP2_PROTOCOL_ERROR`, three attempts across two unrelated SKUs. Best Buy
   now serves `/product/<slug>/<ID>`, where `<ID>` (e.g. `J7GSL4G7GQ`) is **not**
   the SKU. An adapter that builds a URL from a SKU will not work.
2. **A refusal is distinguishable from a 404.** A refusal is Chromium's own error
   page at a consistent ~185 KB; a bad product ID returns a genuine rendered Best
   Buy "Page Not Found" at 597 KB. Only the first is UNKNOWN territory.
3. **Refusal is per-product, not rate limiting.** The Best Buy essentials HDMI
   cable failed twice 90 s apart while the gift card succeeded twice across the
   same window. A "physical vs digital" hypothesis was tested and **falsified** —
   a physical Nintendo Switch game rendered fine.

Two further findings worth carrying forward:

- **No evidence Best Buy sells the GO Plus + at all.** Two searches returned only
  gift cards and unrelated Switch titles. **SKU `6577129`** (used at
  `tests/test_retailers.py:316`) appears nowhere in Best Buy's results and its
  legacy URL is refused — it is an unverified fixture value, not an established
  fact. Best Buy can still contribute a *control*, but a GO Plus + watch there
  may be watching nothing.
- **The obvious control is refused.** A Best Buy essentials house-brand cable is
  exactly the shape `config/products.yaml:49-51` prescribes, and is one of the
  reproducibly-refused pages. `Pokémon: Let's Go, Pikachu!` (SKU `6216393`,
  `$59.99`, InStock, sold by Best Buy) is proposed instead, with the caveat that
  02-03 should re-confirm it renders and keep a reserve candidate.

## Performance

- **Duration:** ~62 min
- **Tasks:** 3 of 3
- **Files modified:** 6 (3 created, 3 modified)
- **Commits:** 4

## Accomplishments

**Task 1 — supply-chain gate (approved).** Audited PyPI `nodriver` before
installing anything: version 0.50.3, 43 releases since 2024-02-20, all three
project URLs pointing at `github.com/UltrafunkAmsterdam/nodriver` (4,604 stars,
last push the same day as the last release, not archived), described upstream as
the successor to undetected-chromedriver. No typosquat neighbours exist —
`no-driver`, `nodriver-py`, `nodrivers`, `nodriver2`, `py-nodriver` are all HTTP
404. The plan's `>=0.38` pin resolves to a real release (2024-11-21). Dan
approved it **as an optional extra**, which is how it was installed.

One thing the audit surfaced that is worth remembering: **nodriver is AGPL-3.0
and this project is MIT.** Keeping it an optional dependency the user installs
themselves — never vendored, never redistributed — is what keeps that clean. The
rationale is recorded as a comment on the extra in `pyproject.toml`.

**Task 2 — the transport, and a guard that actually covers it.**
`boty/browser.py` exposes `BROWSER_PATH_ENV`, `find_browser`, `_render` and
`fetch_rendered`, fully annotated, with `nodriver` imported inside `_render` so
importing the module costs nothing and cannot reach the network. `_render` is
the single seam every rendered byte passes through, bounded by
`asyncio.wait_for` and stopping the browser in a `finally` on every path.

The guard extension was the sensitive part. Rung 3 does its networking in a
Chrome **subprocess**, so every socket patch `no_network` already had would have
sat idle while a test hit a live retailer. `tests/conftest.py` now also patches
`boty.browser._render` and `BaseEventLoop.create_connection`.

**Task 3 — the live spike.** ~16 requests, spaced 12–22 s apart with a 90 s
backoff partway through. Full evidence in `docs/retailer-evidence.md`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Chrome could not start at all on this host**

- **Found during:** Task 3, before any Best Buy request was made
- **Issue:** Chrome dumped core on launch. Ubuntu 24.04 ships
  `kernel.apparmor_restrict_unprivileged_userns=1`, denying unprivileged user
  namespaces to binaries with no AppArmor profile, so an unpackaged
  Chrome-for-Testing cannot build its sandbox. This is a **host** fact and had to
  be told apart from "Best Buy blocked us" before any verdict could be recorded —
  exactly the false-alarm the environment notes warned about.
- **Fix:** Added `BOTY_BROWSER_NO_SANDBOX`, an **opt-in** per-host escape hatch
  that logs a warning, and passed `sandbox=` through to `nodriver.start`
  explicitly. Not a silent default: this transport executes attacker-controlled
  retailer JavaScript, and Chrome's sandbox is the boundary between a renderer
  exploit and the host, so a downgrade nobody reviewed would have been the wrong
  trade. The better fixes (distro Chrome package, AppArmor profile, setuid
  `chrome_sandbox`) are recorded in the module docstring and the evidence doc.
- **Files modified:** `boty/browser.py`, `tests/test_browser.py`
- **Commit:** `dfe2998`

**2. [Rule 2 - Missing critical functionality] Fixture sidecars did not record which rung produced them**

- **Found during:** Task 2
- **Issue:** `boty/fixtures.py` exists to make a frozen page interpretable six
  months later, but a rung-3 capture and a rung-1 capture are different artefacts
  — a rendered one always reports `status: 200` because a browser has no response
  code — and nothing on disk distinguished them.
- **Fix:** The sidecar now carries `"transport": "browser" | "http"`, asserted in
  both capture tests.
- **Files modified:** `boty/fixtures.py`, `tests/test_browser.py`
- **Commit:** `3738f72`

### Deliberate scope choices

- **No CLI `--browser` flag.** `boty/cli.py` belongs to 02-02 in this wave; 02-03
  adds the flag, per the plan.
- **No `QUESTIONS.md` entry.** The plan directs one only on a REFUSED verdict.
  The verdict is REACHABLE, and the GO Plus +/SKU finding is not blocking — it is
  recorded in `docs/retailer-evidence.md`, which 02-03 reads.
- **No Best Buy adapter.** 02-03 owns it.

## Verification

| Gate | Before | After |
|---|---|---|
| `pytest tests/ -q` | 99 passed | **114 passed** |
| `mypy` | clean, 13 files | **clean, 14 files** |
| `mutation_check.py` | 5/5 caught | **5/5 caught** |
| `make verify` | exit 0 | **exit 0 (VERIFY: PASS)** |

Plan-specific checks:

- `import boty.browser` does not import `nodriver` — asserted in the suite and
  re-checked standalone.
- `inspect.signature(boty.fixtures.capture)` carries `browser`.
- `docs/retailer-evidence.md` carries exactly **one** bold Verdict line.
- Suite passes with `BOTY_BROWSER_PATH` unset — nothing depends on a browser
  being installed.
- No orphaned Chrome processes after ~16 live renders, confirming the
  `finally: browser.stop()` mitigation (T-02-02) empirically.

**The guard was proved, not assumed.** Removing only the
`monkeypatch.setattr(boty.browser, "_render", _blocked)` line turned the
self-test red, and the failure shows control reaching *real* nodriver's browser
discovery — so the patch is what stops a live launch, not luck. Restored
immediately; the suite is green with it in place.

## Known Stubs

None. No placeholder values or unwired data paths were introduced.

## Threat Flags

None beyond the plan's register. Two register entries are worth flagging as
*changed in disposition*:

| Flag | File | Description |
|---|---|---|
| threat_flag: mitigation-weakened | `boty/browser.py` | T-02-01 assumed a sandboxed browser. On hosts setting `BOTY_BROWSER_NO_SANDBOX` (including danserver), retailer JavaScript runs unsandboxed. Opt-in and warned, but the residual risk is real and now documented. |
| threat_flag: detection-gap | `boty/browser.py` | T-02-03 assumed challenge pages are caught by `BLOCK_PHRASES`. Best Buy's refusal happens *below* HTTP (`ERR_HTTP2_PROTOCOL_ERROR`), so it surfaces as `FetchError`, not `Blocked`. Safe — both are UNKNOWN, never a stock verdict — but phrase-matching is not what catches this retailer. |

## Notes for Next Plans

- **02-03 (Best Buy adapter):** proceed — the retailer is reachable. Build around
  `/product/<slug>/<ID>`; do not construct URLs from SKUs. Treat a ~185 KB
  Chromium error page as UNKNOWN, distinct from a real 404. Expect some product
  pages to be refused reproducibly, so control selection needs a fallback
  candidate. `MARKETPLACES` and `FIRST_PARTY` need no changes.
- **02-04 (Pokémon Center / Nintendo):** rung-3 capture
  (`capture(..., browser=True)`) is available now, as planned.
- **Everyone:** a browser is **not** a strict upgrade. The same headless Chrome
  that reads Best Buy is blocked by Cloudflare on `gamestop.com`, which rung 1
  reads fine on every `make verify`. Escalate because a page needs JS or refuses
  HTTP at the connection layer — not because a fetch failed once.

## Self-Check: PASSED

- `boty/browser.py` — FOUND
- `tests/test_browser.py` — FOUND
- `docs/retailer-evidence.md` — FOUND
- Commits `3738f72`, `dfe2998`, `91c9569` — FOUND in `git log`
