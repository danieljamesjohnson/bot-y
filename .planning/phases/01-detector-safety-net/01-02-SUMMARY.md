---
phase: 01-detector-safety-net
plan: 02
subsystem: testing
tags: [pytest, offline-tests, network-guard, three-state, seller-filter, price-ceiling]

# Dependency graph
requires:
  - "01-01: boty.fixtures.load and the four frozen retailer fixtures"
provides:
  - "36-test offline pytest suite covering parse, retailers and monitor"
  - "tests/conftest.py: autouse network guard + four fixture-loading fixtures"
  - "[project.optional-dependencies] dev (pytest, mypy), installed into .venv"
  - "[tool.pytest.ini_options] testpaths + -ra"
affects: [01-03 type hints, 01-04 make verify, phase-2 new adapters]

# Tech tracking
tech-stack:
  added:
    - "pytest 9.1.1 (dev extra)"
    - "mypy 2.3.0 (dev extra — installed here, configured in 01-03)"
  patterns:
    - "Autouse function-scoped network guard patching curl_cffi.requests entry points"
    - "check_html tested by monkeypatching boty.retailers.get to return a Page built from a fixture"
    - "assess_health / State tested with hand-built Results — no fixtures, no I/O beyond tmp_path"

key-files:
  created:
    - tests/conftest.py
    - tests/test_parse.py
    - tests/test_retailers.py
    - tests/test_monitor.py
  modified:
    - pyproject.toml

key-decisions:
  - "The network guard gets its own self-test — a guard nobody verifies can rot silently and the suite would start making live requests unnoticed"
  - "The GameStop control fixture is asserted as 'some offer is buyable', never offers[0], because that page leads with an OutOfStock $749.99 bundle"
  - "Offline-ness proved empirically by running the suite inside a network namespace with no interfaces, not just by trusting the monkeypatch"
  - "REQ-03 left unchecked despite appearing in this plan's frontmatter — it is 01-03's deliverable and nothing here type-checks boty/"

patterns-established:
  - "Negative assertions carry an explanatory message stating why the wrong answer is dangerous, so a future reader cannot 'fix' the test by relaxing it"

requirements-completed: [REQ-01, REQ-02]

# Metrics
duration: 4min
completed: 2026-08-02
---

# Phase 1 Plan 02: Extraction and Alerting Tests Summary

**A 36-test suite that runs with no network at all — verified inside an interface-less network namespace — pinning the three-state verdict contract, both independent defences against reseller listings, and the guarantee that an UNKNOWN reading never erases what the monitor remembers.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-08-02T16:55:07Z
- **Completed:** 2026-08-02T16:59:00Z
- **Tasks:** 6 (5 producing commits, 1 verification-only)
- **Files modified:** 5 (4 created, 1 modified)

## Accomplishments

- **`tests/conftest.py`** — an autouse, function-scoped fixture replacing
  `curl_cffi.requests.{get,post,request,Session}` with a callable that raises
  `AssertionError("test attempted a live network request")`. Plus the four
  fixture-loading fixtures, each documented with the exact values it carries so
  a test author does not have to open a 470 KB HTML file to find out.
- **`tests/test_parse.py` (14 tests)** — the `None` vs `[]` distinction asserted
  from both sides, the single-primary-product regression, malformed-JSON
  tolerance, and the fact that `ldjson_offers` finds nothing on a Walmart page
  (which is *why* `check_html` has a fallback chain).
- **`tests/test_retailers.py` (9 tests)** — the three-state contract and both
  flipper defences:

  | Case | Verdict |
  |---|---|
  | GameStop GO Plus + | OUT_OF_STOCK, $54.99, not alertable |
  | GameStop PS5 control | IN_STOCK, alertable (no ceiling set) |
  | Walmart reseller, `first_party_only=True` | not IN_STOCK, detail says "none first-party" |
  | Walmart reseller, filter **off**, `max_price=80` | IN_STOCK at $229.99 but **not alertable** |
  | Walmart milk control | IN_STOCK from Walmart.com, $2.42 |
  | Unreadable page | UNKNOWN, explicitly `is not OUT_OF_STOCK` |
  | `Blocked` raised | UNKNOWN, detail says blocked |
  | `FetchError` raised | UNKNOWN, detail says fetch failed |

- **`tests/test_monitor.py` (13 tests)** — health from controls (including the
  no-control-watch case reading unhealthy), edge-triggered alerting, the
  IN_STOCK → UNKNOWN → IN_STOCK sequence that must not re-alert, save/reload
  persistence, corrupt-state-file recovery, and `run_once` wiring.
- **`pyproject.toml`** — `dev` extra (pytest, mypy) and `[tool.pytest.ini_options]`
  with `testpaths = ["tests"]` and `addopts = "-ra"`.

## Task Commits

| Task | Name | Commit | Type |
|---|---|---|---|
| 0 | Install dev dependencies | `f266e82` | chore |
| 1 | pytest scaffolding and network guard | `2d55ca8` | test |
| 2 | Parser tests | `7d091ad` | test |
| 3 | Retailer and alerting contract tests | `dc02e09` | test |
| 4 | Monitor health and state tests | `f71fdbe` | test |
| 5 | Full suite green, offline | — | verification only, no file changes |

## Files Created/Modified

- `tests/conftest.py` — `no_network` autouse guard; `gamestop_goplusplus`,
  `gamestop_ps5`, `walmart_goplusplus`, `walmart_milk`
- `tests/test_parse.py` — `ldjson_offers` / `nextdata_offers` contract
- `tests/test_retailers.py` — `check_html` three-state, seller filter, price ceiling
- `tests/test_monitor.py` — `assess_health`, `State`, `run_once`
- `pyproject.toml` — `dev` extra, pytest ini options

## Decisions Made

- **The guard has a self-test.** `test_the_network_guard_actually_fires` calls
  `boty.fetch.get` and asserts the guard's message surfaces. A guard nobody
  verifies is exactly the kind of thing that stops working after an upstream
  rename, and the suite would quietly begin hitting live retailers with no
  visible symptom. (It surfaces as `FetchError` rather than `AssertionError`
  because `fetch.get` wraps every exception from the transport — still loud,
  still unmistakable, and the test asserts on the message.)
- **Offline-ness proved, not assumed.** In addition to the monkeypatch, the
  whole suite was run inside a network namespace with no interfaces:
  `sudo unshare -n sudo -u dan .venv/bin/python -m pytest tests/ -q -p no:cacheprovider`
  → 36 passed. Connectivity inside that namespace was separately confirmed
  absent (`Errno 101 Network is unreachable`). This is a candidate for 01-04's
  `make verify`.
- **`first_party_only=False` is set explicitly in the price-ceiling test.** The
  point of that case is that the ceiling holds the line *on its own*. Leaving
  the seller filter on would have made it pass for the other defence's reason
  and proved nothing about independence.
- **Never assert on `offers[0]` for the PS5 control.** That page leads with an
  OutOfStock $749.99 bundle, as 01-01's summary warned. The test filters for
  buyable offers instead, with a comment saying why.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added a self-test for the network guard**

- **Found during:** Task 3
- **Issue:** The plan specified the guard but nothing that proves it is still
  wired to the right attributes. If `curl_cffi` renames or restructures its
  request entry points, `monkeypatch.setattr` on a stale name raises — but
  `raising=False` on the optional ones, or a future refactor, could leave a
  hole. A silently-dead guard means live requests during CI with no symptom.
- **Fix:** `test_the_network_guard_actually_fires` invokes `boty.fetch.get` and
  asserts the guard's sentinel message reaches the caller.
- **Files modified:** `tests/test_retailers.py`
- **Committed in:** `dc02e09`

**2. [Rule 2 - Missing Critical] Guard also patches `post` and `request`**

- **Found during:** Task 1
- **Issue:** The plan named `get` and `Session`. `boty.fetch` only uses `get`
  today, but a Phase 2 adapter posting to a retailer's search API would slip
  straight past a guard that only covers `get` — and the first sign would be a
  live request in CI.
- **Fix:** Also patched `post` and `request` with `raising=False`, so the guard
  covers the surface a new adapter is likely to reach for without breaking if
  those attributes are absent.
- **Files modified:** `tests/conftest.py`
- **Committed in:** `2d55ca8`

### Scope Notes (not deviations)

- Beyond the cases the plan enumerated, the suite adds: malformed-ld+json
  tolerance, `Product` with no offers returning `[]`, `__NEXT_DATA__` present
  but missing the product path, corrupt state file recovery, and two `run_once`
  tests (controls never alert but are recorded; the price ceiling suppresses).
  All are within the plan's stated files and subject matter.
- **REQ-03 deliberately left unchecked.** This plan's frontmatter lists it, but
  REQ-03 is "`boty/` carries type hints and passes a static type check" — 01-03's
  deliverable. Nothing here type-checks `boty/`; marking it complete would be a
  false green in the traceability table. Only REQ-01 and REQ-02 were marked.

---

**Total deviations:** 2 auto-fixed (both missing-critical)
**Impact on plan:** Both harden the network guard, which is the assumption the
entire suite rests on. No new dependencies beyond the planned `dev` extra.

## Issues Encountered

- **pytest and mypy were genuinely absent from `.venv`**, exactly as Task 0
  anticipated. `pip install -e '.[dev]'` pulled pytest 9.1.1 and mypy 2.3.0.
  01-03 will find mypy already installed and can go straight to configuring it —
  note that mypy **2.x** is a good deal stricter by default than the 1.x the
  plan's `mypy>=1.8` floor implies.
- **`unshare -rn` (rootless) is not permitted on this box** — `/proc/self/uid_map`
  write denied. The offline proof used `sudo unshare -n` re-dropping to `dan`,
  with `-p no:cacheprovider` so no root-owned `.pytest_cache` was left behind.

## Known Stubs

None.

## User Setup Required

None.

## Next Phase Readiness

Ready for 01-03 (type hints + mypy) and 01-04 (`make verify`):

- `.venv/bin/python -m pytest tests/ -q` → **36 passed in 0.06s**
- mypy 2.3.0 already installed; `pyproject.toml` has no `[tool.mypy]` section
  yet, left clear for 01-03 as coordinated
- The netns command above is available for 01-04 if `make verify` wants a hard
  offline assertion rather than trusting the monkeypatch
- Any Phase 2 adapter now inherits the guard automatically — a new test that
  forgets to stub its fetch fails immediately with a message naming the problem

No blockers.

## Self-Check: PASSED

All 5 claimed files exist on disk; all 5 task commits present in git history.

---
*Phase: 01-detector-safety-net*
*Completed: 2026-08-02*
