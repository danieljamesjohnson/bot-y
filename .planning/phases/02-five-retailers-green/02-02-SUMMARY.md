---
phase: 02-five-retailers-green
plan: 02
subsystem: models
tags: [provenance, escalation-ladder, degraded, schema-org, mutation-testing, status-json]

requires:
  - phase: 01-detector-safety-net
    provides: "boty.models (Availability/Result/Watch/Health), boty.status.write, boty.cli._report, scripts/mutation_check.py M1-M5, make verify"
  - phase: 02-five-retailers-green
    provides: "02-01: boty/browser.py — the rung-3 transport whose readings this plan labels"
provides:
  - "boty.models.Rung — TLS / API / BROWSER, one member per reachable escalation rung"
  - "Result.rung (defaults to Rung.TLS) and the derived Result.degraded property"
  - "status.json watches[] entries carrying `rung` (string) and `degraded` (bool)"
  - "A [degraded] tag in `boty check` output, composed alongside [control]"
  - "Mutation M6 — clearing Result.degraded turns the suite red"
  - "check_bestbuy_api labelled rung=api on all four of its return paths"
  - "ldjson_offers reads a compound schema.org @type as a Product (IN-03 closed)"
affects: [02-03-bestbuy-adapter, 02-04-pokemon-center-nintendo, 03-target-amazon, dashboard]

tech-stack:
  added: []
  patterns:
    - "Provenance as a separate axis: how a reading was obtained is a second enum beside what it says, never a fourth value inside it"
    - "Derived-not-stored flags: `degraded` is computed from `rung` so the published claim and the runtime flag cannot drift apart"
    - "Backward-compatible frozen-dataclass extension: new field declared last with a default, proven by running the whole pre-existing suite unchanged"
    - "Mutating a claim, not just a verdict: M6 changes no availability, price or alert, so only an assertion on the flag itself can catch it"

key-files:
  created:
    - tests/test_status.py
  modified:
    - boty/models.py
    - boty/retailers.py
    - boty/status.py
    - boty/cli.py
    - boty/parse.py
    - scripts/mutation_check.py
    - tests/test_models.py
    - tests/test_retailers.py
    - tests/test_parse.py

key-decisions:
  - "Rung member names are exactly TLS='tls', API='api', BROWSER='browser'; no member exists for rung 4 (dropped), which produces no readings"
  - "status.json key names are `rung` (the enum's string value) and `degraded` (bool) inside each watches[] entry — 02-03 and 02-04 consume these verbatim"
  - "degraded is derived from rung (`rung is Rung.BROWSER`), never stored, so the support matrix and the runtime flag have one source of truth"
  - "Rung.API is NOT degraded (D-01): the sanctioned API is strictly more reliable than a scraped page"
  - "boty/monitor.py is untouched — degradation must not feed Health.ok or phase criterion 4 becomes unreachable by construction"
  - "Result.alertable is untouched — a browser-read restock is still a restock"
  - "Both rung and degraded are published, not just degraded, so the matrix can distinguish rung 2 from rung 1 even though neither is degraded"

patterns-established:
  - "Provenance beside the verdict: `Rung` answers 'how did we find out', `Availability` answers 'is it buyable', and neither absorbs the other"
  - "Prove the flag bites: M6 was run and observed catching 6 tests before the mutation was accepted, rather than asserted to be caught"
  - "Membership over equality on retailer-controlled JSON: `\"Product\" not in types` skips a dict/int/nested @type instead of raising on it"

requirements-completed: [REQ-04]

duration: 34min
completed: 2026-08-02
---

# Phase 2 Plan 02: Reading Provenance Summary

**Every `Result` now records which rung of the escalation ladder produced it, a browser-read verdict is published and printed as `[degraded]` while an official-API one is not, and mutation M6 makes silently dropping that distinction a red suite.**

## What 02-03 and 02-04 must use

These names are the contract; both downstream plans consume them.

| Thing | Exact name | Value |
|---|---|---|
| Enum | `boty.models.Rung` | `Rung.TLS` = `"tls"`, `Rung.API` = `"api"`, `Rung.BROWSER` = `"browser"` |
| Field | `Result.rung` | declared last, defaults to `Rung.TLS` |
| Property | `Result.degraded` | `self.rung is Rung.BROWSER` — derived, read-only |
| status.json | `watches[].rung` | the rung's string value |
| status.json | `watches[].degraded` | bool |

A browser-backed checker sets `rung=Rung.BROWSER` on **every** `Result` it
returns, error paths included — `check_bestbuy_api` is the worked example
(`boty/retailers.py:171-206`, four returns, all tagged). A rung is a fact about
the transport, not about the verdict, so an UNKNOWN from a 403 is still a
rung-2 reading.

There is no `Rung` member for rung 4 ("dropped") on purpose: a dropped retailer
produces no readings, so the member could never appear on a `Result`.

## Performance

- **Duration:** 34 min
- **Tasks:** 3 of 3
- **Files modified:** 9 modified, 1 created
- **Tests:** 114 → 134 passing
- **Mutations:** 5/5 → 6/6 caught

## Accomplishments

### Task 1 — `Rung` and `degraded` on `Result`

`boty/models.py` gains a second enum beside `Availability`, with a docstring in
the module's existing voice explaining *why* it is separate. `Result.rung` is
declared last with a `Rung.TLS` default, which is what keeps the change
low-blast-radius on a frozen dataclass: every pre-existing construction site in
`boty/retailers.py` names no rung and every one of them is a plain TLS fetch, so
the default relabels nothing. The whole 114-test suite passed unchanged, which
is the proof rather than the claim.

`check_bestbuy_api` is tagged here rather than in 02-03, because 02-03 has a
branch that may skip its adapter work entirely while `check_bestbuy_api`
survives that branch as existing code — and a Best Buy API reading labelled
rung 1 would make the support matrix quietly wrong for exactly the person who
has a key.

- Commits: `dcd9356` (RED), `0b76d65` (GREEN)

### Task 2 — publishing it, and making it load-bearing

`boty/status.py` writes `rung` and `degraded` into each `watches[]` entry, with
a comment recording that this file is served over HTTP and the keys are
therefore public API. `boty/cli.py:_report` now *composes* tags rather than
choosing one, so a browser-read control prints `[control] [degraded]` — both
facts are true at once and either alone would mislead. `SYMBOL` is untouched
and still keyed only by `Availability`.

M6 mutates `Result.degraded` to `return False`. Nothing about any verdict
changes when it is applied — every availability, price and alert stays
byte-identical — so it is only catchable by an assertion on the flag itself.
Observed catching 6 tests.

- Commits: `eb3b388` (RED), `5a5faee` (GREEN)

### Task 3 — IN-03: a compound `@type` is still a Product

`boty/parse.py:71` was `if node.get("@type") != "Product": continue`, which
skips ordinary schema.org markup like `["Product", "ProductModel"]`. The fix is
the one `01-REVIEW.md:726-733` supplies verbatim. It matters *now* because it
fails safe — `saw_product` stays False, so the caller says UNKNOWN — meaning it
costs coverage rather than correctness and would have presented to 02-04 as a
mysterious UNKNOWN on an otherwise perfectly readable Pokémon Center or
Nintendo page.

The `None`-vs-`[]` contract survives: a node with no `@type` wraps to `[None]`,
which does not contain `"Product"`, so the extractor still returns `None`. That
is now pinned by its own test.

- Commits: `887feb3` (RED), `16d5d67` (GREEN)

## Key Decisions

**Degradation is orthogonal to availability, not a fourth value.** A fourth
`Availability` member would break `monitor.assess_health` (`is not
Availability.IN_STOCK`), `monitor.transitioned_to_stock`, and `cli.SYMBOL` —
which is a dict indexed unconditionally, so a missing key is a `KeyError` in the
middle of printing a report, after some rows have already been written.
`tests/test_status.py::test_report_does_not_raise_for_any_availability` pins
that.

**Degradation does not feed `Health.ok`.** `assess_health` answers "has this
detector been verified by a control", not "how confident is the transport". Had
it fed in, Best Buy would raise a permanent health warning and phase criterion 4
— "five or more retailers with **no** health warnings" — would be unreachable by
construction. `boty/monitor.py` is byte-identical to before this plan, and the
reason lives in the `Rung` docstring where a future reader would otherwise be
tempted.

**Degradation does not suppress alerts.** `Result.alertable` is untouched. A
browser-read restock is still a restock; withholding it would defeat the point
of supporting the retailer at all.

**Both `rung` and `degraded` are published.** Publishing only the boolean would
have collapsed rung 1 and rung 2 together, since neither is degraded — and the
support matrix has to state which rung each retailer landed on.

## Deviations from Plan

None — the plan executed as written.

Two notes for the record, both anticipated by the executor briefing rather than
discovered:

- The plan's prose says `check_bestbuy_api` has "five call sites". It has four
  (three error paths plus the success path). All four carry `rung=Rung.API`; no
  path was missed.
- The M2 and M3 mutation anchors were left untouched, as required. The only
  `boty/retailers.py` edits are inside `check_bestbuy_api`, which is textually
  disjoint from both anchors. `mutation_check.py` reported no HARNESS ERROR.

## Verification

All gates run and observed, not assumed.

| Gate | Result |
|---|---|
| `.venv/bin/python -m pytest tests/ -q` | `134 passed in 0.25s` |
| `.venv/bin/python -m mypy` | `Success: no issues found in 14 source files` |
| `.venv/bin/python scripts/mutation_check.py` | `6/6 mutations caught` (M6 caught by 6 tests) |
| `make verify` | `VERIFY: PASS`, exit 0 — with live controls actually run (2/2 in stock), not skipped |
| `len(list(Availability)) == 3` | passes — no fourth availability state |
| `grep -c '"degraded"' boty/status.py` | 1 |
| `git diff` on `boty/monitor.py` | empty |

M6 mutation output, verbatim:

```
CAUGHT    M6 boty/models.py: 6 test(s) failed — test_a_browser_reading_is_degraded,
          test_degradation_does_not_suppress_an_alert,
          test_a_browser_reading_serialises_as_degraded (+3 more)
```

Rendered `boty check` line for a browser-read control:

```
  ● bestbuy   GO Plus +      $   19.99  rendered control [control] [degraded]
```

## Known Stubs

None.

## Threat Flags

None. The plan's register anticipated everything this touched: T-02-07
(spoofing a low-confidence reading) is mitigated by deriving `degraded` from
`rung` plus M6; T-02-09 (malformed `@type`) is mitigated by testing membership
rather than accessing attributes, so a dict, int or nested list is skipped
instead of raising; T-02-10 (frozen-dataclass breakage) is mitigated by the
trailing default and evidenced by the unchanged suite. No new network surface,
no new dependency, no new credential path.

## Notes for Next Phase

- 02-03's browser adapter must set `rung=Rung.BROWSER` on **every** return,
  including the blocked/failed paths, for the same reason `check_bestbuy_api`
  tags its error paths.
- 02-04's Pokémon Center and Nintendo work now has the compound-`@type` case
  handled. If either still reads UNKNOWN, the cause is elsewhere.
- IN-02 (the `tests/test_parse.py` docstring overstating that `check_html`
  branches differently on `None` vs `[]`) remains deliberately out of scope and
  still open.
- `scripts/mutation_check.py`'s module docstring still says "three mutations"
  and "corrupts three specific things"; it has said so since M4/M5 landed in
  Phase 1 and is now six. Pre-existing drift, left alone under the scope
  boundary — worth a one-line fix in a future tidy-up.

## Self-Check: PASSED

All 7 claimed files exist on disk; all 6 claimed commits resolve in `git log`.
