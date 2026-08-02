---
phase: 01-detector-safety-net
plan: 03
subsystem: typing
tags: [mypy, type-hints, static-analysis, none-handling]

# Dependency graph
requires:
  - "01-01: boty/fixtures.py and the capture-fixture CLI subcommand exist to be annotated"
  - "01-02: mypy 2.3.0 installed via the dev extra; pyproject.toml left with no [tool.mypy] section"
provides:
  - "[tool.mypy] in pyproject.toml — `mypy` with no arguments checks the boty package"
  - "Full parameter and return annotations across all 9 boty modules"
  - "disallow_untyped_defs, so the next unannotated def fails the check rather than being skipped"
  - "mypy>=2.0 floor in the dev extra"
affects: [01-04 make verify, phase-2 new adapters, phase-4 outside contributors]

# Tech tracking
tech-stack:
  added:
    - "mypy configuration (no new dependency — mypy itself arrived in 01-02)"
  patterns:
    - "Any at the JSON boundary only (_as_float, _dig, Page.json, _expand) — never for our own types"
    - "Optional-returning extractors carry explicit `X | None` so the None branch cannot be dropped silently"
    - "Zero `# type: ignore` in the package; unstubbed third-party libs handled by per-module overrides instead"

key-files:
  created: []
  modified:
    - pyproject.toml
    - boty/parse.py
    - boty/retailers.py
    - boty/monitor.py
    - boty/notify.py
    - boty/status.py
    - boty/config.py
    - boty/cli.py
    - boty/fixtures.py
    - boty/fetch.py

key-decisions:
  - "Non-strict mypy skips unannotated function bodies entirely, so the planned config passed with zero annotations — disallow_untyped_defs added to stop the check being decorative"
  - "The check was proved to bite by deleting the `offer is None` branch and confirming mypy flags it, rather than trusting a Success line"
  - "dev extra floor raised mypy>=1.8 -> >=2.0 so contributors cannot resolve a weaker checker than the one this config was verified against"
  - "Any confined to the JSON boundary; boty's own types are named everywhere"
  - "models.py needed no changes — it was already fully annotated"

patterns-established:
  - "A new config flag is justified in a comment stating what silently passes without it, not what it enables"

requirements-completed: [REQ-03]

# Metrics
duration: 5min
completed: 2026-08-02
---

# Phase 1 Plan 03: Type Hints and mypy Summary

**Full annotations across all 9 `boty` modules plus a committed `[tool.mypy]`
config that was caught being a false green — non-strict mypy skips unannotated
function bodies entirely, so the planned settings passed the whole package with
zero annotations until `disallow_untyped_defs` was added.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-08-02T17:00:30Z
- **Completed:** 2026-08-02T17:05:00Z
- **Tasks:** 3 (producing 4 commits)
- **Files modified:** 10 (0 created, 10 modified)

## Accomplishments

- **`[tool.mypy]` in pyproject.toml** — `python_version = "3.10"`,
  `files = ["boty"]`, `warn_unused_ignores`, `warn_redundant_casts`,
  `no_implicit_optional`, plus `disallow_untyped_defs` /
  `disallow_incomplete_defs` (see Deviations). `ignore_missing_imports`
  overrides for `curl_cffi.*`, `apprise.*` and `yaml.*`. Not `strict = true`.
- **`boty/parse.py`** — `_as_float(v: Any) -> float | None`,
  `_iter_nodes(doc: Any) -> Iterator[dict[str, Any]]`,
  `_dig(doc: Any, path: Iterable[str]) -> Any | None`. The two public
  extractors already declared `list[Offer] | None`.
- **`boty/retailers.py`** — `_pick(...) -> parse.Offer | None`. This is the
  load-bearing one: the `None` return is what turns a reseller-only page into
  OUT_OF_STOCK instead of a wrong IN_STOCK.
- **`boty/monitor.py`** — `run_once`'s `checker` parameter typed
  `Callable[[Watch], Result]`. (`run_once`'s tuple return was already present,
  as the plan warned; it was verified, not assumed.)
- **`boty/notify.py`, `status.py`, `config.py`, `cli.py`** — `list[Result]` /
  `list[Health]` parameters, `_client -> Any | None`, `main(argv: list[str] |
  None) -> int`, `_make_checker(cfg: Config) -> Callable[[Watch], Result]`.
- **`boty/fetch.py` and `boty/fixtures.py`** — `Page.json -> Any`,
  `metadata -> dict[str, Any] | None`. Both inside `files = ["boty"]` but
  omitted from the plan's original task list.
- **`boty/models.py` needed no changes** — already fully annotated. Checked
  rather than edited for the sake of appearing in the file list.

## Task Commits

| Task | Name | Commit | Type |
|---|---|---|---|
| 1 | mypy configuration | `fb06496` | chore |
| 2 | Annotate extraction and retailer modules | `b856707` | feat |
| 3 | Annotate the remaining modules | `fa63201` | feat |
| 3b | Make the check enforce rather than permit | `8a6aed2` | fix |

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m mypy` (no args) | **Success: no issues found in 11 source files** |
| `.venv/bin/python -m pytest tests/ -q` | **36 passed in 0.06s** — unchanged from 01-02 |
| Bare `# type: ignore` anywhere in `boty/` | **none** (`grep` returns nothing) |
| `mypy --disallow-untyped-defs --disallow-incomplete-defs` audit | clean — every def in the package is fully annotated |
| `boty check` behaviour | identical (see below) |

**The check was proved to bite, not just to pass.** A `Success` line over an
unannotated codebase means nothing, so the `offer is None` branch in
`check_html` was temporarily deleted and mypy re-run:

```
boty/retailers.py:84: error: Item "None" of "Offer | None" has no attribute "available"  [union-attr]
boty/retailers.py:85: error: Item "None" of "Offer | None" has no attribute "seller"  [union-attr]
boty/retailers.py:89: error: Item "None" of "Offer | None" has no attribute "price"  [union-attr]
boty/retailers.py:90: error: Item "None" of "Offer | None" has no attribute "raw_availability"  [union-attr]
```

That is exactly the failure this plan exists to catch — dropping that branch
does not crash, it reports a marketplace flipper's listing as a restock. The
file was restored (`git diff` clean) before committing.

**`boty check` behaviour, verified offline** (no live retailer requests):

- `boty --help` and `boty capture-fixture --help` render identically; 01-01's
  subcommand is still wired
- `boty check -c <empty>` prints `no watches configured`, exits `2`
- `Config.load('config/products.yaml')` yields the same 4 watches with the same
  `max_price=80` ceilings and the same two controls

## Decisions Made

- **The planned config was a false green, and that was the main finding.**
  With only the flags the plan specified, `mypy` reported success across the
  entire package *before a single annotation was written*. Non-strict mypy does
  not check the body of an unannotated function — it skips it. So the config
  alone delivered a green check that asserted nothing, which is structurally
  the same failure as a detector reporting out-of-stock forever: green, and
  meaningless. `disallow_untyped_defs` + `disallow_incomplete_defs` fix it.
- **Those two flags are free right now and were verified so.** An audit run
  with them passed before they were committed, so they impose no debt — they
  only bind future code.
- **This is not `strict = true`.** The plan's objection to strict is that
  contributors start `# type: ignore`-ing it. `disallow_untyped_defs` emits one
  clear, actionable message ("add annotations") rather than the variance and
  `Any`-propagation errors that make strict feel arbitrary. The other strict
  components remain off.
- **`Any` is confined to the JSON boundary.** `_as_float`, `_dig`,
  `Page.json`, `_expand` and `metadata` all sit where a retailer's payload
  shape is genuinely not ours to promise. Every one of boty's own types is
  named. Widening `Any` inward would have made the check pass while removing
  the point of it.
- **Zero suppressions.** No `# type: ignore` was needed anywhere. The two
  unstubbed dependencies (`apprise`, `curl_cffi`) are handled by per-module
  overrides in one declared place, so a future reader can see the whole set of
  concessions in the config rather than hunting comments through the source.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] The specified config passes with no annotations at all**

- **Found during:** Task 1 verification
- **Issue:** `python_version`/`files`/`warn_unused_ignores`/
  `warn_redundant_casts`/`no_implicit_optional` do not cause mypy to check
  unannotated function bodies — mypy skips them silently. Running the committed
  config against the then-unannotated package returned
  `Success: no issues found in 11 source files`. The plan's must-have "mypy runs
  over boty/ and exits 0" would therefore have been satisfiable without doing
  any of the work, and worse, the very next contributor to add a bare `def`
  would get a silent free pass with the check still green. REQ-03 would have
  read as met while decaying immediately.
- **Fix:** Added `disallow_untyped_defs = true` and
  `disallow_incomplete_defs = true`, with a config comment stating what
  silently passes without them. Verified free at HEAD before committing.
- **Files modified:** `pyproject.toml`
- **Commit:** `8a6aed2`

**2. [Rule 2 - Missing Critical] dev extra could resolve a weaker mypy than the one verified**

- **Found during:** Task 3
- **Issue:** The dev extra floor was `mypy>=1.8`, but everything here was
  developed and verified against mypy **2.3.0**, which is meaningfully stricter
  by default. A contributor or CI run resolving 1.x would execute a weaker
  check and get a green that means less than ours — and nothing would say so.
  01-04's `make verify` will depend on this floor.
- **Fix:** Raised to `mypy>=2.0` (2.0.0 confirmed available on PyPI), with the
  reason in a comment.
- **Files modified:** `pyproject.toml`
- **Commit:** `8a6aed2`

### Scope Notes (not deviations)

- `boty/fetch.py` and `boty/models.py` were listed in the plan frontmatter and
  picked up in Task 3 as the plan's own task body instructed. `models.py`
  required no edit — it was already complete — so it does not appear in the
  commits despite being in `files_modified`.
- The plan's warnings about already-annotated code were accurate and were
  checked rather than trusted: `check_html`, `check_bestbuy_api`,
  `run_once`'s return type, `ldjson_offers` and `nextdata_offers` all already
  carried annotations and were left alone.

---

**Total deviations:** 2 auto-fixed (both missing-critical, both in `pyproject.toml`)
**Impact on plan:** Both convert a check that would have been decorative into
one that enforces the requirement. No behavioural change to `boty` itself — the
annotations are additive and the 36-test suite is byte-for-byte unchanged in
outcome. No new dependencies.

## Issues Encountered

- **None blocking.** The prior wave's warning that mypy is 2.3.0 rather than
  1.x turned out to cut the other way than expected: 2.x surfaced **zero**
  errors on the existing code once annotated. The codebase was already
  None-disciplined — `parse` and `retailers` genuinely do check every optional
  before use. The value delivered here is prospective (catching the next
  mistake) rather than corrective, which is why proving the check bites
  mattered more than usual.

## Known Stubs

None.

## User Setup Required

None. `mypy` is already installed in `.venv`; the floor bump only affects fresh
`pip install -e '.[dev]'` runs.

## Next Phase Readiness

Ready for 01-04 (`make verify`):

- `.venv/bin/python -m mypy` — no arguments needed, config is committed, exits 0
- `.venv/bin/python -m pytest tests/ -q` — 36 passed
- Both are single commands with no flags, so a `verify` target can call them
  directly without encoding knowledge that would drift out of sync
- The netns offline proof from 01-02 remains available if `make verify` wants a
  hard offline assertion

No blockers.

## Self-Check: PASSED

All 10 claimed modified files exist on disk; all 4 task commits
(`fb06496`, `b856707`, `fa63201`, `8a6aed2`) present in git history.

---
*Phase: 01-detector-safety-net*
*Completed: 2026-08-02*
</content>
</invoke>
