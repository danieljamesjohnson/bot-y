---
phase: 02-five-retailers-green
plan: 04
subsystem: retailers
tags: [nintendo, pokemoncenter, rung-1, rung-4, refused, escalation-ladder, controls, evidence, fixtures, imperva, block-detection, IN-03]

requires:
  - phase: 02-five-retailers-green
    provides: "02-02: Rung/degraded and the IN-03 compound-@type fix, which is what makes Nintendo readable at all. 02-03: `boty capture-fixture --browser` and `_verdict_from_html`"
  - phase: 01-detector-safety-net
    provides: "check_html's three-state contract, _pick, the control gate, mutation M2/M3, make verify"
provides:
  - "Nintendo as a supported retailer on rung 1 — one FIRST_PARTY line and two watches, no adapter code"
  - "A first-party GO Plus + watch at $54.99 MSRP with no marketplace attached — the most credible restock signal in the config"
  - "A Nintendo control watch reading IN_STOCK live, so four retailers are now control-verified"
  - "boty.fetch.BLOCK_PHRASES recognises Imperva walls served at HTTP 200"
  - "tests/test_fetch.py — block detection pinned in both directions, including against false positives on shipped fixtures"
  - "test_no_retailer_is_configured_without_a_page_we_have_actually_read — an offline anti-padding gate on the retailer count"
  - "A recorded rung-4 verdict for Pokémon Center with the two probes worth retrying"
affects: [03-target-amazon, dashboard]

tech-stack:
  added: []
  patterns:
    - "Probe before you build: task 1 wrote no code and established that task 2 needed almost none"
    - "A retailer is a string key plus an allow-list entry — the instinct to write an adapter class produces dead code"
    - "Membership in MARKETPLACES is a claim about a site, decided by evidence; 'to be safe' is the unsafe default"
    - "Anti-padding gates must be offline and mechanical — a live gate cannot fail in CI, and 'we would notice' is not a control"
    - "A block phrase is a bet that no real page contains it; test both directions or a working retailer reads blocked forever"

key-files:
  created:
    - tests/fixtures/nintendo/goplusplus.html
    - tests/fixtures/nintendo/goplusplus.json
    - tests/fixtures/nintendo/hdmi-control.html
    - tests/fixtures/nintendo/hdmi-control.json
    - tests/test_fetch.py
  modified:
    - boty/retailers.py
    - boty/fetch.py
    - config/products.yaml
    - tests/conftest.py
    - tests/test_retailers.py
    - tests/test_parse.py
    - README.md
    - docs/retailer-evidence.md
    - QUESTIONS.md

key-decisions:
  - "Nintendo ships on rung 1 with no adapter: no extractor, no _make_checker branch, no parse.py change at all"
  - "Nintendo is in FIRST_PARTY and deliberately out of MARKETPLACES — its store has no third-party seller surface, and adding it would strip _pick's unattributed-offer fallback"
  - "Pokémon Center is rung 4, REFUSED. No watch, no fixture, no allow-list entry — the phase reports four retailers"
  - "Nintendo's target is a plain URL, not a SKU: its product URLs are derivable from a published sitemap, so Best Buy's indirection would be cargo-culting a workaround for a problem this retailer does not have"
  - "The WR-03 test was repointed from pokemoncenter to costco — 'out of scope on purpose' is a more durable promise than 'unreachable today'"
  - "pardon our interruption and _incapsula_resource added to BLOCK_PHRASES: a Rule 2 fix the ladder walk found in our code, not in Pokémon Center's"
  - "A new offline test asserts every configured retailer has a captured page, because capture() cannot be made to write one for a site that refuses us"

patterns-established:
  - "Pin a deferred finding against live bytes once a retailer confirms it: IN-03 had four synthetic tests that all agreed with each other by construction, and none was evidence any retailer emits that shape"
  - "When a count is the success criterion, ship the gate that makes padding it fail — mechanically, offline, before anyone is tempted"

requirements-completed: [REQ-05, REQ-06]

duration: 35min
completed: 2026-08-02
---

# Phase 2 Plan 04: Nintendo Green, Pokémon Center Refused Summary

**Nintendo is a supported retailer for the cost of one `FIRST_PARTY` line and
two YAML watches — no adapter, no extractor, no parse.py change — and it is the
only place in this config that lists the Pokémon GO Plus + as a first-party
product at its $54.99 MSRP; Pokémon Center refused every rung of the ladder and
is documented as rung 4, so the phase closes at four control-verified retailers
rather than five.**

## The headline number is wrong on purpose

Phase 2's criterion 4 says five retailers. **It lands on four:** gamestop,
walmart, bestbuy, nintendo.

Pokémon Center is the one that fell out, and the thing worth saying about it is
that it would have been *easy* to make the number read five. Pokémon Center
genuinely stocks the GO Plus + — `/product/715e10557/pokemon-go-plus`, found via
its own published sitemap. A `retailer: pokemoncenter` watch pointing at that URL
would have looked completely plausible to a reviewer, and would have read nothing
for the rest of the project's life.

The roadmap's standard for this is "working, or documented as unreachable with
the evidence that established it". That is what shipped: `**Verdict: REFUSED**`
in `docs/retailer-evidence.md` with the byte counts and the WAF vendors, a
`rung 4` entry in `QUESTIONS.md`, a push to Dan, a README matrix row, and an
explanatory block in `config/products.yaml` where the missing entry would be.

Every other criterion holds. `make verify` exits 0 with the live stage run,
`healthy` is true, all four controls read IN_STOCK, the matrix records a rung for
every row, and both new fixtures are backed by offline tests.

## Task 1 — the probe that made task 2 small

The plan was emphatic that these two "probably need no new checker at all" and
that task 1 should be a cheap probe rather than an adapter build. It was right,
and the evidence is the size of task 2's diff.

**Nintendo: `**Verdict: REACHABLE (rung 1)**`.** 8 requests, 12–20 s apart, no
refusal and no retry. `robots.txt` is `Allow: /` for everyone except named AI
crawlers. Its store publishes a **36,530-entry sitemap**, which is how both
product URLs were found — the on-site search is client-side Algolia and useless
at rung 1, but the sitemap is deliberately published and answers the same
question. A guessed slug returns a clean HTTP 404 rather than a refusal, which
is itself worth knowing: this retailer tells you when you are wrong.

**Pokémon Center: `**Verdict: REFUSED**`.** Four refusals across two products,
two URL forms, two transports and two different WAF vendors:

| Transport | Result |
|---|---|
| rung 1, cold | HTTP **403**, 858 B, CloudFront + DataDome JS challenge |
| rung 1, session warmed from the homepage, with `Referer` | HTTP **200**, 6,183 B, Imperva `Pardon Our Interruption` |
| rung 1, a second product, cold | HTTP **200**, 6,183 B, identical |
| rung 3, headless Chrome | `Blocked` — `capture-fixture` refused to save it |
| rung 3, after a 120 s backoff | refused again, 1,085 B, `_Incapsula_Resource` iframe |

The homepage read fine at rung 1 both **before and between** those refusals, so
this host is not IP-banned — the wall is specifically on `/product/*`. That
detail is the reason the section ends with two named probes worth retrying later
rather than a shrug.

Rung 2 is not merely unavailable here, it is **closed**: Pokémon Center publishes
no documented API, and its own `robots.txt` explicitly `Disallow`s `/cortex`,
`/availabilities`, `/prices`, `/offers` and `/items` — precisely the endpoints
that would answer the stock question. Taking data a retailer has asked in writing
that we not take, to power a monitor whose entire pitch is trustworthy readings,
is not a trade this project makes.

- Commit: `213f928`

## Task 2 — one line of allow-list, and a bug we found in ourselves

**The whole of Nintendo's support:**

```python
"nintendo": {"nintendo of america inc.", "nintendo", "nintendo.com"},
```

Plus two watches. No `_make_checker` branch, no named extractor, no
`MARKETPLACES` entry, and `boty/parse.py` was not touched at all —
`nextdata_offers` was not generalised and `_WALMART_PRODUCT_PATH` was left alone,
as the design required.

`MARKETPLACES` membership was decided by evidence and the absence is commented as
a claim rather than left to look like an oversight. Nintendo's store has no
third-party seller surface — no buy box, nobody but Nintendo of America who can
list on it — so adding it "to be safe" would strip `_pick`'s unattributed-offer
fallback and turn any future page that drops the seller node into a permanent
UNKNOWN. The safe-looking default was the unsafe one.

**IN-03's first live confirmation.** Nintendo's product node declares
`"@type": ["Product"]` — a one-element list, the least suspicious shape
imaginable, and exactly what an `== "Product"` comparison drops on the floor.
Under the pre-02-02 extractor this page would have read as "no product markup
here" and Nintendo would have been an unexplained permanent UNKNOWN: a
first-party retailer, publishing complete and correct availability and price,
invisible for a one-character reason. `test_the_compound_type_fix_is_confirmed_by_a_real_retailer`
pins it against the shipped bytes, because the four existing IN-03 tests all
build their own JSON and therefore agree with each other by construction.

**The WR-03 escape hatch moved to `costco`,** with every assertion intact plus a
new one asserting `costco` is not in `FIRST_PARTY`. `pokemoncenter` was tempting
now that it is rung 4, but "unreachable today" is a weaker promise than "out of
scope on purpose", and walls come down again.

- Commits: `60b9ac1` (RED — 8 failed, 159 passed), `a9ccda0` (GREEN — 167 passed)

## Task 3 — the matrix, and the green checked the way the service sees it

README's table gained rows for Nintendo and Pokémon Center, so every row carries
a rung. The opening sample is real output from this run rather than the
two-retailer one it showed before, and it reads top-to-bottom as the project's
own argument: the product is out of stock everywhere, and the four green control
lines below it are why you can believe that.

**`make verify` was run twice, and the second run is the one that counts.**
02-03 shipped a green obtained in a shell with `BOTY_BROWSER_PATH` exported;
systemd starts with almost no environment, so the deployed service could not find
Chrome and paged Dan half an hour later. So this plan re-ran the whole gate under
`systemd-run --property=EnvironmentFile=/home/dan/.config/boty/env`, and it
passed identically. **Nintendo needs no new environment variable at all** — rung
1, no credential, no browser — so nothing was added to `deploy/boty.service` or
the env file, and that is a checked fact rather than an assumption.

- Commit: `3a98a4e`

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 2 - Missing critical functionality] An Imperva wall at HTTP 200 read as a page, not a block**

- **Found during:** Task 1, probing Pokémon Center
- **Issue:** Imperva serves `Pardon Our Interruption` with **HTTP 200**, and none
  of `boty.fetch.BLOCK_PHRASES` matched it. So `get()` returned the wall as an
  ordinary `Page`, and `_verdict_from_html` reported
  `no structured stock data found (page shape changed?)`. The *verdict* was never
  wrong — UNKNOWN either way, failing safe — but the **reason** was, and the two
  send a reader to opposite ends of the problem: one says re-capture the fixture
  and see which assertions moved, the other says this retailer is turning us
  away. A monitor whose whole pitch is that it tells you when it breaks owes the
  right reason. Nothing about it is Pokémon Center-specific; Imperva sits in
  front of a great many retailers and Phase 3's two are prime candidates.
- **Fix:** `pardon our interruption` and `_incapsula_resource` added to
  `BLOCK_PHRASES`. `_incapsula_resource` is the durable one — it appeared in both
  the rung-1 and rung-3 refusals where the human-readable wording appeared in
  only one. New `tests/test_fetch.py` pins both, on both rungs, **and pins the
  opposite direction**: a parameterised test runs the shipped 380–420 KB product
  fixtures back through `get()`, because a phrase broad enough to match a real
  page would report a working retailer as blocked forever, which is a worse
  failure than the one the list prevents. Plus an assertion that every phrase is
  lower-case, since `get` lowercases the body once and a capital anywhere in that
  tuple is a phrase that can never fire.
- **Files:** `boty/fetch.py`, `tests/test_fetch.py`
- **Commits:** `60b9ac1` (RED), `a9ccda0` (GREEN)

**2. [Rule 2 - Missing critical functionality] Nothing offline could stop the retailer count being padded**

- **Found during:** Task 2, deciding how to make the rung-4 outcome durable
- **Issue:** The plan's own gate argues that padding `config/products.yaml`
  "cannot work" because `control_check.py` fails a retailer with no control and
  `assess_health` fails one whose control cannot be read. Both are true and both
  need a **network** to say so. `make verify-offline` runs in CI and would have
  been perfectly green with a fabricated Pokémon Center watch in the file, and
  the phase whose success criterion is a retailer *count* is exactly the one
  where that matters.
- **Fix:** `test_no_retailer_is_configured_without_a_page_we_have_actually_read`
  asserts every configured retailer has a captured page under `tests/fixtures/`.
  This is unfakeable in the relevant direction: `boty.fixtures.capture` only
  writes a fixture after a live fetch that was not blocked, and it refused to
  write one for Pokémon Center. The assertion message points at
  `docs/retailer-evidence.md`, so the next person to hit it meets the reasoning
  rather than an obstacle.
- **Files:** `tests/test_retailers.py`
- **Commit:** `60b9ac1`

**3. [Rule 1 - Bug] The evidence doc claimed a fix that had not been made yet**

- **Found during:** Task 1, before committing
- **Issue:** The Pokémon Center section was drafted in the past tense —
  "`pardon our interruption` and `incapsula incident` **were added** to
  `BLOCK_PHRASES`" — in a commit where they had not been. A document whose entire
  purpose is recording observations rather than conclusions cannot afford a
  tense that outruns the code. The phrase was also wrong: `_incapsula_resource`
  is what actually appears in both captured refusals.
- **Fix:** Reworded to name what task 2 would do, then confirmed by task 3's
  append. Phrase corrected against the captured bytes.
- **Files:** `docs/retailer-evidence.md`
- **Commit:** `213f928`

### Deliberate scope choices

- **No Pokémon Center anything.** No watch, no fixture, no `FIRST_PARTY` entry,
  no speculative adapter waiting for the wall to come down. The plan's or-clause
  exists for exactly this and it was taken at face value.
- **No further escalation past rung 4.** Beyond it are residential proxies and
  CAPTCHA-solving services, which are out of scope by design and would fail the
  project's "a fresh clone can do this" test anyway.
- **Nintendo's `target` is a URL, not a SKU.** Best Buy's SKU indirection exists
  because Best Buy's product URLs are not derivable; Nintendo's are, from a
  published sitemap. Copying the shape would be cargo-culting a workaround for a
  problem this retailer does not have. Pinned by
  `test_the_shipped_nintendo_watches_are_urls_with_no_ceiling_on_the_control`.
- **`max_price: 80` on the Nintendo GO Plus + watch** even though Nintendo has no
  marketplace and lists at MSRP. It costs nothing and it is the independent
  second line if the seller filter ever regresses — the two defences are tested
  separately in this suite precisely because they fail separately.
- **`_pick`, `MARKETPLACES` and the "no structured stock data found" text
  untouched**, as M2 and M3 require.
- **The `Event loop is closed` tracebacks** after every Best Buy render are still
  cosmetic and still in `deferred-items.md`. Not fixed here; this plan added no
  browser code.

### No authentication gates

Nothing in this plan needed a credential, and that is the point of rung 1. No new
environment variable was introduced, so `deploy/boty.service` and the env file
are unchanged — confirmed by re-running the whole gate under `systemd-run`
rather than asserted.

## Verification

All gates run and observed on danserver, with `boty.service` stopped for the live
stages and restarted afterwards (`active (running)`, confirmed).

| Gate | Before | After |
|---|---|---|
| `pytest tests/ -q` | 150 passed | **167 passed** |
| `mypy` | clean, 14 files | **clean, 14 files** |
| `scripts/mutation_check.py` | 6/6 caught | **6/6 caught** |
| `make verify` (shell) | exit 0 | **`VERIFY: PASS`, exit 0 — not the OFFLINE variant** |
| `make verify` (systemd-run + EnvironmentFile) | — | **`VERIFY: PASS`, exit 0** |

Live control stage, verbatim, from the systemd-run form:

```
control check: 4 control(s), live
  in_stock      gamestop  CONTROL — PS5 console                $549.99  ld+json: InStock from GameStop
  in_stock      walmart   CONTROL — Great Value whole milk       $2.42  __NEXT_DATA__: IN_STOCK from Walmart.com
  in_stock      bestbuy   CONTROL — Pokémon Let's Go, Pikach    $59.99  ld+json: InStock from Best Buy
  in_stock      nintendo  CONTROL — Nintendo HDMI cable          $7.99  ld+json: InStock from Nintendo of America Inc.
control check: PASS — 4/4 controls in stock
```

`boty check`, verbatim, ANSI stripped:

```
  ○ gamestop  Pokémon GO Plus +             $   54.99  ld+json: OutOfStock from GameStop
  ○ walmart   Pokémon GO Plus +                        1 offer(s) via __NEXT_DATA__, none first-party
  ○ nintendo  Pokémon GO Plus +             $   54.99  ld+json: OutOfStock from Nintendo of America Inc.
  ● gamestop  CONTROL — PS5 console         $  549.99  ld+json: InStock from GameStop [control]
  ● walmart   CONTROL — Great Value whole mi$    2.42  __NEXT_DATA__: IN_STOCK from Walmart.com [control]
  ● bestbuy   CONTROL — Pokémon Let's Go, Pi$   59.99  ld+json: InStock from Best Buy [control] [degraded]
  ● nintendo  CONTROL — Nintendo HDMI cable $    7.99  ld+json: InStock from Nintendo of America Inc. [control]
  ● gamestop  TRANSITION — Pitch Black Boost$   59.99  ld+json: InStock from GameStop
  ● gamestop  TRANSITION — Ascended Heroes M$   24.99  ld+json: InStock from GameStop
  ○ gamestop  TRANSITION — Mega Evolution Bo$   44.99  ld+json: OutOfStock from GameStop
```

No `!` health warning lines. `served/boty/status.json`:

```
4 retailers, healthy = True
  bestbuy ok=True   gamestop ok=True   nintendo ok=True   walmart ok=True
  nintendo GO Plus +      out_of_stock  54.99  rung=tls  degraded=false
  nintendo HDMI control   in_stock       7.99  rung=tls  degraded=false
```

### REQ-08 baseline for Phase 3

**A full `boty check` — 10 watches across 4 retailers, one of them on rung 3 —
took 40 s wall clock.** That is a third of REQ-08's two-minute budget, with the
browser rung included. `fetch.get`'s 0.4–1.6 s jitter dominates; the Best Buy
render is the single most expensive watch. Phase 3 adding two more retailers at
rung 1 costs roughly 2–4 s each. Adding one at rung 3 costs closer to 10 s.

### Plan-specific checks

- `grep -cE '^\*\*Verdict: …\*\*' docs/retailer-evidence.md` → **3** (Best Buy,
  Nintendo, Pokémon Center). The task-1 gate required ≥3.
- Every fixture has a sidecar with a non-empty note — 8/8, all 0 days old.
- `Config.load` → configured `{bestbuy, gamestop, nintendo, walmart}`, minus
  verified → **empty**. REQ-06 holds against the shipped config.
- `'rung 4' in QUESTIONS.md` → True; `'**Verdict: REFUSED**' in
  docs/retailer-evidence.md` → True. The shortfall clause is genuinely satisfied,
  not merely asserted.
- `notify-dan` sent, naming Pokémon Center and the consequence for the count.
- README matrix carries a Rung for all six rows including the two planned ones.
- No orphaned Chrome processes after the live stages.

## Known Stubs

None. No placeholder values, no unwired data paths, no hardcoded empty
collections. The one thing *absent* rather than stubbed — Pokémon Center — is
documented as a finding in five places (`config/products.yaml`,
`docs/retailer-evidence.md`, `README.md`, `QUESTIONS.md`, and a test whose
failure message points at the first of them) rather than left as a gap for a
future plan to trip over.

## Threat Flags

None beyond the plan's register. Notes on three entries:

| Entry | Outcome |
|---|---|
| T-02-17 (a reshaped page read as a confident OUT_OF_STOCK) | Held, and strengthened in an unplanned direction: the register assumed the risk was a parser losing its footing. The live finding was a *bot wall* arriving as a 200-status page with no product markup — same UNKNOWN, wrong reason. `BLOCK_PHRASES` now separates them. |
| T-02-19 (a third-party listing alerting as first-party) | `MARKETPLACES` membership decided by evidence, `_pick` untouched, ceiling retained on the product watch. Nintendo has no marketplace, which is a finding rather than an assumption — `test_nintendo_is_first_party_but_not_a_marketplace` asserts both halves. |
| T-02-20 (a retailer added with no control) | Held, and given an offline sibling. The register's mitigation needs a network; `test_no_retailer_is_configured_without_a_page_we_have_actually_read` does not. |
| T-02-21 (polite-polling budget, accepted) | Baseline recorded above: 40 s for 10 watches across 4 retailers. Comfortably inside REQ-08. |

One residual, unchanged from 02-03: the live stages run with
`BOTY_BROWSER_NO_SANDBOX=1` for Best Buy's rung, so retailer JavaScript executes
unsandboxed. A host fact, not a repo one. Nintendo needs none of it.

## Notes for Next Plans

- **Phase 3 (Target / Amazon):** `check_html` is now proven to carry a retailer
  with no adapter code whatsoever. Probe first and write the allow-list entry;
  reach for `parse.py` only when a probe says you must. `BLOCK_PHRASES` now
  covers Imperva, which both of your targets may well sit behind — if a probe
  returns a 200 with no product markup, check whether it is a wall before
  suspecting the extractor.
- **The five-retailer bar** is unmet at four. If Target or Amazon lands, it is
  met in Phase 3. Do not retro-fit Pokémon Center to close it without re-running
  the two probes named in `docs/retailer-evidence.md`.
- **Anyone touching Nintendo:** its store sitemap
  (`/us/store/sitemap.xml`, 36,530 entries) is the discovery mechanism — the
  on-site search is client-side and useless at rung 1. Reserve control candidate
  if the HDMI cable is discontinued: the AC adapter, `ac-adapter-104900`.
- **Anyone adding a block phrase:** `tests/test_fetch.py` runs every shipped
  product fixture back through `get()`. If your phrase eats one, that test is
  telling you it would have reported a working retailer as blocked forever.

## Self-Check: PASSED

- `boty/retailers.py`, `boty/fetch.py`, `config/products.yaml`,
  `tests/conftest.py`, `tests/test_retailers.py`, `tests/test_parse.py`,
  `tests/test_fetch.py`, `README.md`, `docs/retailer-evidence.md`,
  `QUESTIONS.md` — FOUND
- `tests/fixtures/nintendo/{goplusplus,hdmi-control}.{html,json}` — FOUND
- `tests/fixtures/pokemoncenter/` — CORRECTLY ABSENT (rung 4; `capture-fixture`
  refused to write a challenge page)
- Commits `213f928`, `60b9ac1`, `a9ccda0`, `3a98a4e` — FOUND in `git log`
