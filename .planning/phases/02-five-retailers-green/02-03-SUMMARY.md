---
phase: 02-five-retailers-green
plan: 03
subsystem: retailers
tags: [bestbuy, rung-3, browser, degraded, escalation-ladder, controls, evidence, fixtures]

requires:
  - phase: 02-five-retailers-green
    provides: "02-01: boty/browser.py fetch_rendered + fixtures.capture(browser=True) + the Best Buy REACHABLE verdict. 02-02: Rung/degraded, and Rung.API already on check_bestbuy_api"
  - phase: 01-detector-safety-net
    provides: "check_html's three-state contract, _pick, the control gate, mutation M2/M3, make verify"
provides:
  - "boty.retailers.check_bestbuy_browser — Best Buy with no credentials at all, every Result tagged Rung.BROWSER"
  - "boty.retailers._verdict_from_html — the fetch/verdict split, so every transport shares one UNKNOWN path"
  - "boty.retailers.bestbuy_product_url — SKU -> a URL that actually resolves, shared by both Best Buy rungs"
  - "boty capture-fixture --browser — rung-3 fixture capture from the CLI (02-04 depends on this)"
  - "A Best Buy control watch reading IN_STOCK live, so three retailers are now control-verified"
  - "README's retailer matrix with a Rung column"
affects: [02-04-pokemon-center-nintendo, 03-target-amazon, dashboard]

tech-stack:
  added: []
  patterns:
    - "Transport/verdict split: I/O at the edge, one shared pure function decides what a page means"
    - "Provenance passed in, not derived: url and rung are facts only the caller knows"
    - "Prefer the URL form whose MISS path was verified over the one whose hit path looks tidier"
    - "Redact host filesystem paths from anything a browser transport puts in a served Result"

key-files:
  created:
    - tests/fixtures/bestbuy/pikachu-control.html
    - tests/fixtures/bestbuy/pikachu-control.json
    - tests/fixtures/bestbuy/unresolved-sku.html
    - tests/fixtures/bestbuy/unresolved-sku.json
  modified:
    - boty/retailers.py
    - boty/cli.py
    - config/products.yaml
    - tests/conftest.py
    - tests/test_retailers.py
    - tests/test_browser.py
    - README.md
    - docs/retailer-evidence.md

key-decisions:
  - "Branch A taken: Best Buy is a supported retailer on rung 3, credential-free, flagged DEGRADED"
  - "bestbuy_product_url returns Best Buy's SKU search URL, which redirects to the product page — the only SKU-derivable form that works, and the only one whose miss path was verified to fail safe"
  - "Result.url on the API path moved to the same helper: the legacy /site/-/<sku>.p link it published is refused by Best Buy and 404s for anyone who clicks it"
  - "No Best Buy GO Plus + watch ships — Best Buy does not carry the product, and SKU 6577129 was disproved rather than merely unverified"
  - "The fabricated SKU was removed from tests too; a value nobody has seen resolve must not sit in a test looking like a fact"
  - "_redact_host_paths added to the browser rung: it is the one transport that reports failures in terms of this machine, and detail is served over HTTP"
  - "MARKETPLACES and _pick untouched — Best Buy attributes seller.name as 'Best Buy', already in FIRST_PARTY"
  - "No named Best Buy extractor in parse.py: the rendered page carries ordinary schema.org Product markup that ldjson_offers already reads"

patterns-established:
  - "Fixture the miss, not just the hit: unresolved-sku.html freezes what a retailer returns when a target stops resolving, which is the shape a silent failure actually arrives in"
  - "A retailer can be supported without watching the flagship product — support is defined by a live control, not by carrying the item"

requirements-completed: [REQ-04, REQ-06]

duration: 71min
completed: 2026-08-02
---

# Phase 2 Plan 03: Best Buy on Rung 3 Summary

**Best Buy now reports a real stock verdict with no credentials configured —
a headless browser reading schema.org markup, flagged `[degraded]`, upgrading
to the official API and dropping the flag when `BESTBUY_API_KEY` is set — and
the same investigation established that Best Buy does not sell the Pokémon GO
Plus +, so it ships a control and no product watch.**

**Branch A** was taken, per 02-01's `**Verdict: REACHABLE (rung 3)**`.

## The problem the plan could not have known about

The design specified `bestbuy_product_url(sku: str) -> str` and said its
template was "whichever form the spike proved works". **The spike proved no
SKU-to-URL template works.** The legacy `/site/-/<sku>.p` form is uniformly
refused, and the live `/product/<slug>/<ID>` form's `<ID>` is an opaque token
that cannot be derived from a SKU. Both facts were already in
`docs/retailer-evidence.md`; what was missing was any way to satisfy the
plan's own constraint that one YAML entry serve both rungs.

Two live probes settled it:

| Probe | Result |
|---|---|
| `/site/searchpage.jsp?st=6216393` (a bare SKU) | **Redirects to the product page.** 1,109,548 B, canonical `/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ/sku/6216393`, `ldjson_offers` → exactly one offer, `price=59.99`, `seller='Best Buy'`, `InStock` |
| `/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ` | Renders, identical single offer — the control still worked four hours after 02-01 saw it |

So Best Buy's own search is the SKU resolver, and that is what the helper
returns. `watch.target` stays a SKU exactly as the plan required, and no model
or config schema change was needed.

**The reason to prefer it is the miss path, and the miss path was checked.**
A search matching nothing — SKU `6577129`, and both GO Plus + searches — returns
a search page carrying **no schema.org Product markup at all**, despite listing
a dozen products with prices on screen. So a SKU that stops resolving reads
UNKNOWN, loudly. A guessed product-URL template had no such guarantee: Best
Buy's 404 is a fully rendered 597 KB Best Buy page and what it carries in
`ld+json` was never established. Choosing the uglier URL whose failure mode is
known over the tidier one whose failure mode is not is the whole of this
project's thesis applied to its own implementation.

Both pages are now frozen as fixtures, so the hit and the miss are both
regression-tested offline.

## Best Buy does not sell the GO Plus +

02-01 recorded this as an absence of evidence. It is now a disproof: searched on
the exact path that redirects a real SKU straight to its product page, `6577129`
matches nothing. Every product link in the two saved search pages is a gift
card, a membership card, or a Let's Go title.

So **`config/products.yaml` ships a Best Buy control and no Best Buy GO Plus +
watch.** A watch on a product the retailer does not carry would sit at UNKNOWN
forever and raise a permanent health warning — the monitor reporting itself
broken for correctly observing that something is not there. The unverified SKU
was removed from `tests/test_retailers.py` at the same time.

This does not cost the phase its retailer count. Best Buy is supported and
verified by a live control, which is how "supported" is defined here. It does
mean Best Buy will never alert on the product this project was built for, and
that is worth saying plainly rather than burying.

## Performance

- **Duration:** ~71 min
- **Tasks:** 3 of 3
- **Files:** 4 created, 8 modified
- **Tests:** 134 → **150** passing
- **Live requests:** 4 (2 probes, 2 fixture captures), spaced 25–30 s apart,
  plus one `make verify` and one `boty check` cycle. No retry storms, no refusals.

## Accomplishments

### Task 1 — the adapter and the one dispatch seam

**Step 1 (unconditional, what 02-04 consumes).** `nodriver` 0.50.3 imports in
this worktree. `boty capture-fixture --browser` now exists and routes to the
`browser` keyword 02-01 added, covered by a parameterised test that also pins
the default to False — a capture that silently started launching Chrome for
GameStop would change what every existing fixture is a snapshot *of*.
`check_bestbuy_api` still carries `Rung.API` on all four returns, asserted by
the pre-existing parameterised credential test.

**Step 2.** `check_html` split into `_verdict_from_html` (no I/O, takes `url`
and `rung`) plus a thin fetch wrapper, so the WR-02/WR-03 escape hatches live in
exactly one place. `check_bestbuy_browser` fetches through a module-scope
`fetch_rendered` — the same shape `_serve` uses for `get`, so a test patches one
name — and tags `Rung.BROWSER` on all three of its returns. `_make_checker`
grew a two-armed bestbuy branch and stayed one function, because
`scripts/control_check.py` builds its checker with it.

`_redact_host_paths` was added to the browser rung. It handles no credential,
but it is the only transport that reports failures in terms of *this machine* —
a missing binary, a Chrome that would not start, a profile directory — and
`Result.detail` is copied verbatim into a status file served over HTTP.

**The mutation gate was run before any new test existed to mask a regression**,
as the plan required: 6/6, M2's anchor intact at unchanged indentation.

- Commits: `1e67464` (step 1), `5596e72` (step 2)

### Task 2 — fixtures, tests, control

Two rung-3 captures with sidecars and notes. `bestbuy/unresolved-sku` is the
one worth pointing at: it is not a synthetic `<html>nope</html>` but Best Buy's
genuine answer to a target that stopped resolving, which is the shape a silent
failure actually arrives in.

All eight behaviour bullets are covered, plus the price ceiling on the browser
rung, the host-path redaction, and two config assertions that pin REQ-06 offline
rather than only in the live gate. The UNKNOWN-not-OUT_OF_STOCK assertion is
restated for this adapter deliberately.

`test_the_browser_rung_is_never_reached_without_being_asked` deliberately does
*not* patch the transport: it asserts conftest's guard fires and is not
downgraded to an Exception, since `check_bestbuy_browser` would otherwise turn a
live-network attempt into a quiet UNKNOWN.

- Commits: `e5e4b90` (RED — 1 failed, 6 errors), `a91e3e0` (GREEN — 150 passed)

### Task 3 — the matrix, the evidence, the gate

README's table gained a **Rung** column filled in for every retailer, an
install subsection for the browser extra and `BOTY_BROWSER_PATH`, and the
cross-cutting warning that rung 3 is not a strict upgrade. Two stale claims went
with it: "The 36 offline tests" (it was 150) and "corrupts three specific
things" (it is six).

`docs/retailer-evidence.md` carries the URL-form finding, the miss-path proof,
the GO Plus + disproof, and the confirmed control with a reserve candidate. It
still ends its Best Buy section in exactly one bold Verdict line.

- Commit: `90f2c45`

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 - Blocking] `bestbuy_product_url` had no template the spike proved works**

- **Found during:** Task 1, before any code was written
- **Issue:** The plan's design assumed the spike had found a working SKU-to-URL
  form. It had found the opposite — both known forms are unusable from a SKU.
  Without a resolution, `check_bestbuy_browser` could not be written at all
  without changing `Watch`, `Config` and the YAML schema.
- **Fix:** Two live probes established that Best Buy's SKU search redirects to
  the product page, and that a non-matching search carries no Product markup.
  `bestbuy_product_url` returns the search URL. No schema change was needed and
  `watch.target` stays a SKU, as the plan intended.
- **Files:** `boty/retailers.py`, `docs/retailer-evidence.md`
- **Commit:** `5596e72`

**2. [Rule 1 - Bug] `check_bestbuy_api` published a dead link on every Result**

- **Found during:** Task 1
- **Issue:** `Result.url` was `https://www.bestbuy.com/site/-/<sku>.p` — the
  exact form 02-01 proved Best Buy refuses. `boty.status.write` copies it into a
  served status file, so every Best Buy row on the dashboard offered a link that
  does not load. Pre-existing, and REQ-04 records HTTP 403 as Best Buy's normal
  API answer, so it was the common case rather than the edge one.
- **Fix:** Both rungs now build the URL from `bestbuy_product_url`. The
  assertion at `tests/test_retailers.py:350` moved with it, as the plan
  explicitly authorised.
- **Commit:** `5596e72`

**3. [Rule 2 - Missing critical functionality] The browser rung could publish host paths**

- **Found during:** Task 1
- **Issue:** The plan asked for a `_redact` on this path but the browser handles
  no credential, so the obvious reading was "nothing to redact". The real
  exposure is different in kind: this is the only transport whose failures name
  local filesystem paths — the Chrome executable, `$HOME`, a profile directory —
  and those land in `Result.detail`, which is served over HTTP.
- **Fix:** `_redact_host_paths` replaces `BOTY_BROWSER_PATH` and `$HOME` before
  either failure path builds its Result. Pinned by
  `test_browser_failures_do_not_publish_this_machines_paths`.
- **Commit:** `5596e72`

**4. [Rule 1 - Bug] The unverified SKU `6577129` was in shipped tests**

- **Found during:** Task 1
- **Fix:** Replaced with `6216393`, a SKU observed resolving live, with a
  comment recording why. `6577129` survives only as the *subject* of the
  unresolved-sku fixture, which is the honest place for it.
- **Commit:** `5596e72`

### Deliberate scope choices

- **No Best Buy GO Plus + watch, and no `goplusplus` Best Buy fixture.** The
  plan's task 2 named one; Best Buy does not carry the product. Inventing a
  watch on a non-existent page was explicitly ruled out by the briefing, and the
  control fixture already covers both bullets a product fixture would have
  (expected availability, non-None price).
- **No named Best Buy extractor in `boty/parse.py`.** The plan made this
  conditional on the rendered page carrying no usable schema.org offer. It
  carries an ordinary one. `nextdata_offers` was not generalised.
- **`MARKETPLACES` and `_pick` untouched**, as 02-01 established and M3 requires.
- **`scripts/mutation_check.py`'s stale docstring left alone** — logged to
  `deferred-items.md`. The equivalent README drift was fixed because that file
  was being rewritten anyway; the mutation harness was kept textually stable
  across the plan that moves one of its anchors.

### No authentication gates

`BESTBUY_API_KEY` remains unset, deliberately — the credential-free path is what
this plan exists to prove, and it is the path `make verify` exercised.

## Verification

All gates run and observed on danserver, with `boty.service` stopped for the
live stages and restarted afterwards.

| Gate | Before | After |
|---|---|---|
| `pytest tests/ -q` | 134 passed | **150 passed** |
| `BOTY_BROWSER_PATH= pytest tests/ -q` | — | **150 passed** (no browser started) |
| `mypy` | clean, 14 files | **clean, 14 files** |
| `scripts/mutation_check.py` | 6/6 caught | **6/6 caught** |
| `make verify` | exit 0 | **`VERIFY: PASS`, exit 0 — not the OFFLINE variant** |

Live control stage, verbatim:

```
control check: 3 control(s), live
  in_stock      gamestop  CONTROL — PS5 console                $549.99  ld+json: InStock from GameStop
  in_stock      walmart   CONTROL — Great Value whole milk       $2.42  __NEXT_DATA__: IN_STOCK from Walmart.com
  in_stock      bestbuy   CONTROL — Pokémon Let's Go, Pikach    $59.99  ld+json: InStock from Best Buy
control check: PASS — 3/3 controls in stock
```

`boty check` with no API key set:

```
  ● bestbuy   CONTROL — Pokémon Let's Go, Pi$   59.99  ld+json: InStock from Best Buy [control] [degraded]
```

`served/boty/status.json`:

```
[('gamestop','tls',False), ('walmart','tls',False), ('gamestop','tls',False),
 ('walmart','tls',False), ('bestbuy','browser',True), ('gamestop','tls',False), ...]
healthy: True — bestbuy ok, gamestop ok, walmart ok
```

Plan-specific checks:

- `import nodriver` succeeds here (0.50.3).
- `--browser` present in `boty.cli`; `browser` in `inspect.signature(fixtures.capture)`.
- `grep -q "Rung.API" boty/retailers.py` — present, 4 constructions plus docstring.
- `docs/retailer-evidence.md` has exactly **one** bold Verdict line.
- `grep -n "Rung" README.md` — the matrix column is there.
- No health warning for any configured retailer.
- Chrome left no orphaned processes after the live stages.

## Known Stubs

None. No placeholder values, no unwired data paths, no hardcoded empty
collections. The one thing that is *absent* rather than stubbed — a Best Buy
GO Plus + watch — is documented as a finding in three places
(`config/products.yaml`, `docs/retailer-evidence.md`, `README.md`) rather than
left as a gap for a future plan to trip over.

## Threat Flags

None beyond the plan's register. Notes on two register entries:

| Entry | Outcome |
|---|---|
| T-02-11 (credential leak) | Strengthened, not just preserved: the parameterised four-path test still passes, and `Result.url` now points somewhere real on both rungs. |
| T-02-14 (mutation gate silently disabled) | Held. `make mutation` was run inside task 1 as required, before any new test existed to mask a regression. M2 now fails 3 tests instead of 2, the new one being this adapter's own. |

One residual worth recording rather than flagging: on danserver the live stages
run with `BOTY_BROWSER_NO_SANDBOX=1`, so retailer JavaScript executes
unsandboxed. That is 02-01's opt-in host escape hatch, it logs a warning on every
render, and it is a host fact rather than a repo one — a machine with a packaged
Chrome needs none of it.

## Notes for Next Plans

- **02-04 (Pokémon Center / Nintendo):** everything you depend on is on `main`,
  outside any branch. `boty capture-fixture <retailer> <name> <url> --browser`
  works. `_verdict_from_html(watch, html, *, url, first_party_only, rung)` is
  the seam to delegate to — do not reimplement the UNKNOWN logic, and pass
  `rung=Rung.BROWSER` on error paths too. Note that neither retailer is in
  `FIRST_PARTY`, so an unconfigured allow-list currently lands them in the WR-03
  UNKNOWN escape hatch by design; add the key rather than removing the guard.
- **Phase criterion 4 (five retailers):** three are now green and
  control-verified. 02-04's two are what close it.
- **Anyone touching Best Buy:** if the control starts reading UNKNOWN with a
  *transport* failure rather than a parse failure, suspect the unexplained
  per-product refusal before suspecting the extractor. Reserve control candidate
  is `Pokémon: Let's Go, Eevee!` (`J7GSL4G7L4`).
- **`Event loop is closed` tracebacks** after every render are cosmetic and
  logged in `deferred-items.md`. They make a successful run look like a crash,
  and would camouflage a real traceback.

## Self-Check: PASSED

- `boty/retailers.py`, `boty/cli.py`, `config/products.yaml`, `tests/conftest.py`,
  `tests/test_retailers.py`, `tests/test_browser.py`, `README.md`,
  `docs/retailer-evidence.md` — FOUND
- `tests/fixtures/bestbuy/{pikachu-control,unresolved-sku}.{html,json}` — FOUND
- Commits `1e67464`, `5596e72`, `e5e4b90`, `a91e3e0`, `90f2c45` — FOUND in `git log`
