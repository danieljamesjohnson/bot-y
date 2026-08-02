---
phase: 01-detector-safety-net
plan: 01
subsystem: testing
tags: [fixtures, curl_cffi, argparse, json-ld, next-data, offline-tests]

# Dependency graph
requires: []
provides:
  - "boty.fixtures: capture(), load(), age_days(), list_fixtures(), FIXTURE_ROOT"
  - "boty capture-fixture CLI subcommand with --note, standalone (no config file)"
  - "Four frozen retailer fixtures with capture metadata sidecars"
  - "tests/fixtures/README.md — the fixtures-vs-live-controls contract"
affects: [01-02 extraction tests, 01-03 type hints, 01-04 make verify, phase-2 new adapters]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy network import: boty.fetch imported inside capture() so importing boty.fixtures cannot reach the network"
    - "Fixture = .html + .json sidecar (url, retailer, name, captured_at, status, bytes, note)"
    - "argparse subparsers per command, shared -c/--config and -v flags via a helper"

key-files:
  created:
    - boty/fixtures.py
    - tests/fixtures/README.md
    - tests/fixtures/gamestop/goplusplus.html
    - tests/fixtures/gamestop/ps5-control.html
    - tests/fixtures/walmart/goplusplus.html
    - tests/fixtures/walmart/milk-control.html
  modified:
    - boty/cli.py

key-decisions:
  - "FIXTURE_ROOT anchors to the repo root, not the working directory, so load() behaves the same from any cwd"
  - "A blocked or failed fetch writes nothing at all — a CAPTCHA page saved under a product name would poison every test while looking green"
  - "argparse converted to subparsers rather than bolting positional args onto one parser, so capture-fixture gets real required-argument enforcement and its own --help"
  - "The synthetic reseller fixture contingency was not needed: the live Walmart buy box is still held by Clove Brothers LLC at $229.99"

patterns-established:
  - "Fixtures are frozen deliberately and never auto-refreshed in CI — an auto-refresh would let a real breakage land disguised as a fixture update"
  - "Every fixture carries a free-text note describing the stock state it represented, so a later reader can judge whether it still means anything"

requirements-completed: [REQ-01]

# Metrics
duration: 8min
completed: 2026-08-02
---

# Phase 1 Plan 01: Fixture Capture Tooling Summary

**`boty capture-fixture` freezes live retailer pages as HTML + JSON-sidecar fixtures, with an offline `load()` that cannot reach the network — plus four captured fixtures including the Walmart reseller page that exercises seller filtering and the price ceiling at once.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-08-02T16:47:05Z
- **Completed:** 2026-08-02T16:55:00Z
- **Tasks:** 4
- **Files modified:** 11 (2 code, 9 fixtures/docs)

## Accomplishments

- `boty/fixtures.py` — capture, load, staleness and enumeration, with `boty.fetch` imported lazily so the test suite has no path to an outbound request
- `boty capture-fixture <retailer> <name> <url> --note "..."` — standalone, no config file, exits 1 and writes nothing when a bot wall answers
- Four fixtures captured and verified against their extractors; every one reproduces the known-good live values recorded in `01-CONTEXT.md`:

  | Fixture | Extractor reads |
  |---|---|
  | `gamestop/goplusplus` | OutOfStock, $54.99, seller GameStop |
  | `gamestop/ps5-control` | InStock $549.99 (three offers on the page) |
  | `walmart/goplusplus` | IN_STOCK $229.99, seller **Clove Brothers LLC** |
  | `walmart/milk-control` | IN_STOCK $2.42, seller Walmart.com |

- `tests/fixtures/README.md` states in prose and in a table that green fixtures prove nothing about whether a retailer still works — that is the live control products' job

## Task Commits

1. **Task 1: Fixture capture and load module** — `b5385da` (feat)
2. **Task 2: capture-fixture CLI subcommand** — `bdce4f7` (feat)
3. **Task 3: Capture the GameStop and Walmart fixtures** — `7bfc21c` (feat)
4. **Task 4: Document the fixture contract** — `e49b3ea` (docs)

## Files Created/Modified

- `boty/fixtures.py` — `FIXTURE_ROOT`, `capture()`, `load()`, `metadata()`, `age_days()`, `list_fixtures()`, plus `html_path()`/`meta_path()` helpers
- `boty/cli.py` — subparsers for `check` / `watch` / `capture-fixture`; `_capture_fixture()` handles Blocked and FetchError
- `tests/fixtures/{gamestop,walmart}/*.html` + `*.json` — four frozen pages with capture metadata
- `tests/fixtures/README.md` — what fixtures catch, what they do not, how to capture, staleness procedure

## Decisions Made

- **Repo-anchored `FIXTURE_ROOT`.** The plan specified `Path("tests/fixtures")`, which is cwd-relative; pytest and `make` can both be invoked from a subdirectory, and a load that succeeds or fails depending on where you are standing is a trap. Anchored to the repo root when a `pyproject.toml` is present, overridable via `BOTY_FIXTURE_ROOT`, falling back to the plain relative path when installed outside a checkout.
- **Subparsers over a widened positional.** Gives `capture-fixture` required-argument enforcement and its own `--help`; `boty watch -c config/products.yaml` (the systemd unit's exact invocation) still parses identically.
- **Capture fetches before it writes.** Blocked/FetchError propagate out of `capture()` and the CLI turns them into exit 1, so a challenge page can never land on disk as a fixture.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] `FIXTURE_ROOT` made working-directory independent**

- **Found during:** Task 1
- **Issue:** A literal `Path("tests/fixtures")` resolves against the caller's cwd. Tests run from a subdirectory — or an editor's test runner — would raise FileNotFoundError for reasons unrelated to the code under test, which is exactly the flakiness fixtures exist to remove.
- **Fix:** `_default_root()` anchors to the package's repo root when `pyproject.toml` is present, honours a `BOTY_FIXTURE_ROOT` override, and falls back to the relative path otherwise.
- **Files modified:** `boty/fixtures.py`
- **Verification:** `load()` succeeds from `/tmp` and from the repo root; the override was used to keep the CLI failure tests out of the real fixture tree.
- **Committed in:** `b5385da`

**2. [Rule 2 - Missing Critical] `capture()` takes a `note` argument**

- **Found during:** Task 1
- **Issue:** The plan's signature was `capture(retailer, name, url)` but the sidecar must contain a `note` and Task 2 requires the CLI to store `--note` there. Without the parameter the two tasks are unimplementable together.
- **Fix:** Added `note: str = ""`; the CLI warns on stderr when no note is supplied.
- **Files modified:** `boty/fixtures.py`, `boty/cli.py`
- **Verification:** All four captured sidecars carry a non-empty note.
- **Committed in:** `b5385da`, `bdce4f7`

**3. [Rule 2 - Missing Critical] Enriched two fixture notes with what the extractor actually sees**

- **Found during:** Task 3
- **Issue:** `gamestop/ps5-control` carries **three** Product offers — an OutOfStock $749.99 bundle plus two InStock $549.99 offers. A test writer reading the plan's note ("InStock control, $549.99") would reasonably assert on the first offer and get a false failure. The Walmart reseller note named neither the seller nor the price it was captured at.
- **Fix:** Amended both sidecar notes with the verified-at-capture values and, for the PS5 page, an explicit warning to assert that *some* first-party offer is buyable rather than the first one.
- **Files modified:** `tests/fixtures/gamestop/ps5-control.json`, `tests/fixtures/walmart/goplusplus.json`
- **Verification:** `boty.parse` output cross-checked against each note.
- **Committed in:** `7bfc21c`

---

**Total deviations:** 3 auto-fixed (3 missing-critical)
**Impact on plan:** All three protect the harness against false failures or misreadings. No scope creep; no new dependencies.

## Issues Encountered

- **Walmart reseller contingency evaluated and not triggered.** The plan required a hand-authored synthetic `walmart/goplusplus-reseller.html` if the buy box had changed hands by capture time. It had not: the live page still reads `IN_STOCK`, `$229.99`, `sellerName "Clove Brothers LLC"` — a genuine 4x-MSRP reseller listing. The real fixture exercises three-state availability, first-party filtering and the price ceiling simultaneously, so no synthetic fixture was created. If that page is ever re-captured and the reseller is gone, the contingency in this plan is the procedure to follow.
- All four live captures succeeded on the first attempt with no bot-wall interference.

## Known Stubs

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Ready for plan 01-02 (extraction tests):

- `from boty.fixtures import load` works with sockets disabled — verified by monkeypatching `socket.socket` to raise
- Expected values for assertions are recorded above and in each sidecar's `note`
- `age_days()` is in place for the 90-day staleness warning that plan 01-04's `make verify` needs
- Fixture tree is ~1.9 MB across four pages; no `.gitignore` rule excludes it

No blockers.

## Self-Check: PASSED

All 10 claimed files exist on disk; all 4 task commits present in git history.

---
*Phase: 01-detector-safety-net*
*Completed: 2026-08-02*
