---
phase: 01-detector-safety-net
fixed_at: 2026-08-02T18:35:00Z
review_path: .planning/phases/01-detector-safety-net/01-REVIEW.md
iteration: 1
findings_in_scope: 11
fixed: 11
skipped: 0
deferred: 6
status: all_fixed
---

# Phase 1: Code Review Fix Report

**Source review:** `.planning/phases/01-detector-safety-net/01-REVIEW.md`
**Scope:** all Critical (3) and Warning (8). Info (6) deferred.

**Summary:**

- Findings in scope: 11
- Fixed: 11
- Skipped: 0
- Deferred (Info, out of scope): 6

Test count went from **36 to 99**. Every fix below is pinned by at least one
test that was observed failing against the unfixed code and passing after —
the before/after output is recorded per finding rather than asserted.

## A note on how this run went

A previous run of this agent was interrupted mid-flight. It had already
committed seven fixes (CR-01 through WR-04) onto an orphan worktree branch and
left WR-05 uncommitted on disk. Those commits were **preserved, not
regenerated** — discarding them would have thrown away good work. Every one of
them was then independently re-verified here by reverting only its *source*
file (leaving its tests in place) and re-running the suite, so the before/after
evidence in this report is observed, not inherited from the earlier run's
claims. The transcript of that verification is in the per-finding sections.

## Fixed Issues

### CR-01: `run_once` never recorded OUT_OF_STOCK, so every restock after the first was missed

**Files:** `boty/monitor.py`, `tests/test_monitor.py`, `tests/test_restock_replay.py`
**Commits:** `9fbf0ae` (fix + unit tests), `6811f7f` (multi-cycle replay)

`state.transitioned_to_stock(r)` was the last term of an `and` chain inside the
`alerts` comprehension. Python short-circuits, and that call is the only writer
of `state.seen`, so a non-control watch reading OUT_OF_STOCK was never
recorded: the memory stayed pinned at `"in_stock"` and every subsequent restock
compared `previous != "in_stock"` and returned False.

The fix computes transitions in one unconditional pass and filters that for
what to notify about — `alertable` and `control` now decide what we *notify*,
never what we *remember*. It runs exactly once per result, which matters
because the method mutates `state.seen`: the old follow-up loop over controls
was a second call waiting to become a corruption the moment anything else
needed the fallback.

**Pinned by a multi-cycle transition replay** (`tests/test_restock_replay.py`),
built from the fixtures on disk as requested — `gamestop/goplusplus.html`
(OutOfStock) and `gamestop/ps5-control.html` (InStock) — driving the real stack
`run_once -> check_html -> parser -> frozen HTML` across a persistent `State`.
Four tests:

- `test_a_product_watch_alerts_on_every_rising_edge_not_just_the_first` —
  out → in → out → in for a non-control watch, asserting an alert on **both**
  rising edges.
- `test_an_unknown_reading_neither_alerts_nor_erases_what_is_known` — a
  six-cycle sequence with an UNKNOWN interleaved, asserting UNKNOWN neither
  fabricates a transition nor wipes a known state.
- `test_a_control_watch_records_state_but_never_alerts` — the double-call trap.
- `test_the_price_ceiling_suppresses_the_alert_without_freezing_the_memory`.

**Before** (with `boty/monitor.py` reverted to `9fbf0ae~1`, tests kept):

```
E       AssertionError: the second restock was swallowed: an alert fired on the first rising edge but not the second, which means the out-of-stock reading between them was never recorded
E       assert [[], ['goplusplus'], [], []] == [[], ['goplus...'goplusplus']]
E         At index 3 diff: [] != ['goplusplus']
tests/test_restock_replay.py:116: AssertionError
```

It fails on the **second** rising edge specifically — index 1 fired, index 3
did not — which is the exact shape of the bug. The UNKNOWN test failed
separately and more damningly:

```
E       AssertionError: UNKNOWN must not erase a known state
E       assert 'in_stock' == 'out_of_stock'
```

and the ceiling test showed the memory was never written at all:

```
E       assert [None, None, None, None] == ['out_of_stock', 'in_stock', 'out_of_stock', 'in_stock']
```

**After:** `4 passed in 0.03s`.

**On-disk state checked as the review asked.** `state.json` holds only the two
CONTROL entries, both `in_stock`, which is correct — they really are in stock,
and controls were the one case the old code did record. The two *product*
watches are absent entirely, which is the bug's fingerprint: they read
out_of_stock and were never written. No hand-editing is needed; the fix records
them correctly from the next cycle on.

### CR-02: the network guard was swallowed by `fetch.get` and downgraded to UNKNOWN

**Files:** `tests/conftest.py`, `tests/test_retailers.py`
**Commit:** `a37fb14`

The guard raised `AssertionError`, which `boty/fetch.py`'s blanket
`except Exception` converted into `FetchError` and `check_html` then turned
into `Availability.UNKNOWN`. A test that forgot to patch `retailers.get` passed
green while asserting on a verdict the guard itself manufactured — and
`assert ... is Availability.UNKNOWN` is the most common assertion in the suite,
so that is the most likely shape a Phase 2 adapter test will take.

Now `NetworkBlocked(BaseException)`, which `except Exception` cannot catch, and
the guard also blocks `socket.create_connection`, `socket.socket.connect` and
`connect_ex` — closing apprise and `control_check.have_connectivity`, which
bypassed `curl_cffi` entirely.

**Before** (with `tests/conftest.py` reverted to `a37fb14~1`):

```
FAILED tests/test_retailers.py::test_the_network_guard_is_not_downgraded_to_a_verdict
FAILED tests/test_retailers.py::test_the_network_guard_covers_transports_that_bypass_curl_cffi
2 failed, 97 passed
```

**After:** both pass.

**This guard paid for itself during this very session.** While developing
WR-06, `test_watch_refuses_to_start_with_nothing_to_notify` ran the real watch
loop and was caught red-handed:

```
E       conftest.NetworkBlocked: test attempted a live network request
boty/fetch.py:84: in get
    r = requests.get(url, impersonate=IMPERSONATE, ...)
```

Under the old guard that would have been swallowed into UNKNOWN and the test
would have quietly passed while hitting gamestop.com.

### CR-03: the Best Buy API key was written into `Result.url` and served in `status.json`

**Files:** `boty/retailers.py`, `tests/test_retailers.py`
**Commit:** `34f813a`

`check_bestbuy_api` interpolated the key into the request URL and returned that
full URL as `Result.url` on all three error paths. `boty/status.py` copies
`r.url` verbatim into `served/boty/status.json`, which is served over HTTP
through the Mission Control `/tools/boty` proxy — so on the *common* path
(REQ-04 records HTTP 403 as Best Buy's normal answer) this published a
credential.

Every `Result` now carries the clean public `product_url`, and anything derived
from an exception goes through a `_redact` helper first, because curl error
strings routinely echo the URL they were handed.

**Before** (with `boty/retailers.py` reverted to `34f813a~1`):

```
FAILED tests/test_retailers.py::test_bestbuy_api_key_never_reaches_the_result[transport error-<lambda>]
FAILED tests/test_retailers.py::test_bestbuy_api_key_never_reaches_the_result[blocked-<lambda>]
FAILED tests/test_retailers.py::test_bestbuy_api_key_never_reaches_the_result[bad json-<lambda>]
FAILED tests/test_retailers.py::test_bestbuy_api_key_never_reaches_the_result[sku not found-<lambda>]
```

(That revert also predates WR-02/WR-03, so three of their tests failed in the
same run; the four parametrised cases above are CR-03's own.)

**After:** all pass.

**Disk scrubbed as instructed — nothing to scrub.** No `bestbuy` watch is
configured in `config/products.yaml`, so `check_bestbuy_api` has never run on
this machine. `served/boty/status.json` and `state.json` were both inspected in
full: no `apiKey`, no credential in any `url` or `detail` field. A
`grep -rl apiKey --include=*.json` across the repo returns nothing. Both files
are gitignored, so nothing reached git history either. The exposure was real in
the code but never actualised.

### WR-01: the price ceiling failed open when the price could not be read

**Files:** `boty/models.py`, `tests/test_models.py`
**Commit:** `565d852`

`if self.watch.max_price is None or self.price is None: return True` treated an
unpriced IN_STOCK result as alertable even with a ceiling configured — the
opposite of this codebase's own rule for unknown data. A ceiling that cannot be
evaluated must not authorise an alert.

**Before** (`boty/models.py` reverted to `565d852~1`):
`FAILED tests/test_models.py::test_unpriced_in_stock_offer_does_not_pass_the_ceiling` (1 failed, 98 passed).
**After:** passes.

### WR-02: an unattributed offer was treated as first-party, even on a marketplace

**Files:** `boty/retailers.py`, `tests/test_retailers.py`
**Commit:** `37d7ef3`

The "no seller recorded means the retailer" fallback is correct for a
single-seller site like GameStop and wrong for Walmart or Target, which are in
`FIRST_PARTY` precisely *because* they are marketplaces. An explicit
`MARKETPLACES` set now switches the fallback off where the buy box can be held
by a third party.

**Before** (`boty/retailers.py` reverted to `37d7ef3~1`): 3 failed, 96 passed —
`test_unattributed_offer_is_not_first_party_on_a_marketplace`,
`test_walmart_offer_with_no_seller_recorded_is_unknown_not_a_verdict`,
`test_retailer_with_no_first_party_list_is_unknown_not_out_of_stock`.
**After:** all pass.

### WR-03: an unconfigured retailer key produced a confident OUT_OF_STOCK

**Files:** `boty/retailers.py`, `tests/test_retailers.py`
**Commit:** `265e2b5`

`FIRST_PARTY.get(retailer, set())` yields an empty allow-list for an unknown
retailer, so nothing could ever match and any page naming its seller fell
through to OUT_OF_STOCK. The truth is a config gap, not a stock fact — and
REQUIREMENTS targets three more retailers that arrive through exactly this
door. Now UNKNOWN, with a detail message that names the missing allow-list.

**Before** (`boty/retailers.py` reverted to `265e2b5~1`):
`FAILED tests/test_retailers.py::test_retailer_with_no_first_party_list_is_unknown_not_out_of_stock` (1 failed, 98 passed).
**After:** passes.

### WR-04: `control_check` passed green when a retailer had no control at all

**Files:** `scripts/control_check.py`, `scripts/mutation_check.py`, `tests/test_control_check.py`
**Commit:** `7e4b893`

The script only failed on the all-or-nothing case (zero controls anywhere). A
retailer with product watches and no control was invisible to `make verify`,
the gate everything downstream trusts — while `assess_health` already
implemented the right rule. It now fails on `configured - verified` and names
the unverified retailers.

**Before** (`scripts/control_check.py` reverted to `7e4b893~1`): 5 failed —
`test_a_retailer_with_no_control_watch_fails_the_gate`,
`test_the_unverified_retailer_is_named`,
`test_the_gate_refuses_before_making_any_request`, plus the two WR-05 tests
that share the file.
**After:** all pass.

### WR-05: an offline machine yielded an unqualified "VERIFY: PASS"

**Files:** `scripts/control_check.py`, `Makefile`, `tests/test_control_check.py`, `tests/test_verify_makefile.py`
**Commit:** `2c79495`

The skip-when-offline *policy* is right and did not change. The defect was that
the verdict carried no caveat: a skip returned 0, so `make verify` printed
`VERIFY: PASS` and exited 0, identical in every machine-readable respect to a
run where the live controls actually passed. A skip now has exit code
`SKIPPED = 3` (not 0, which is a pass; not 1 or 2, which are a failing control
and a config error), and `verify` translates it into
`VERIFY: PASS (OFFLINE — live controls were NOT run...)`.

The last three `verify` stages had to be folded into one shell, since make
gives every recipe line its own shell and `skipped` has to survive down to the
verdict. `verify` also invokes `$(CONTROL_CMD)` directly rather than through
`$(MAKE) controls`, because a sub-make exiting 3 prints its own `Error 3`
first.

**Pinned by `tests/test_verify_makefile.py`**, which runs the **real Makefile**
against a stub interpreter, so the control flow is tested without a venv,
network or suite. Exit codes 0, 1, 2 and 3 are each pinned separately, so a
`case` arm written as `0|3|*)` cannot swallow a real failure.

**Before** (source reverted, tests kept): 4 failed —

```
E       AttributeError: module 'control_check_under_test' has no attribute 'SKIPPED'
```

and, for the Makefile tests, exit 3 was read as a failure:

```
E         stub: scripts/control_check.py --offline
E         VERIFY: FAIL (live controls)
E         make[2]: *** [Makefile:56: controls] Error 3
E       assert 2 == 0
```

**After:** `14 passed`.

### WR-06: a failed notification permanently lost the alert

**Files:** `boty/cli.py`, `tests/test_cli_watch.py`
**Commits:** `c7825bd` (seam refactor), `789b025` (fix + tests)

`run_once` commits the transition and saves *before* the caller delivers, and
`send_restock`'s return value was discarded. Alerts are edge-triggered, so an
undelivered alert was a permanent drop: the next cycle found the reading
already remembered and stayed quiet. Telegram rate-limiting for one cycle at
02:00 costs the restock outright, with no error and a green status page.
`warned` had the identical defect for health warnings.

Both now roll back on a failed send. `watch` also refuses to start with no
notify URLs — `notify: [${BOTY_NOTIFY_URL}]` with the variable unset produces
exactly that, and `send_restock` returns False on its first line without
logging.

The loop body was inline in a `while True`, which is *why* this was never
pinned — the only unit available to a test was a function that does not return.
`c7825bd` extracts `watch_cycle` (one poll) and `watch_loop` (optional cycle
bound, injectable sleep) as a **separate, behaviour-free commit**, so the
red/green below is reproducible against it.

**Before** (at `c7825bd`, tests applied): 4 failed —

```
E  AssertionError: the alert was delivered once, failed, and was never attempted again — the transition had already been committed to state
E  assert [['goplusplus']] == [['goplusplus'], ['goplusplus']]

E  AssertionError: an undelivered alert must leave no trace of the transition
E  assert 'gamestop:goplusplus' not in {'gamestop:goplusplus': 'in_stock'}

E  AssertionError: the health warning was not delivered, but the retailer was marked as already warned, so the retry never happened
E  assert [['gamestop']] == [['gamestop'], ['gamestop']]
```

plus `test_watch_refuses_to_start_with_nothing_to_notify`, which ran the real
loop into conftest's network guard instead of exiting 2.

**After:** `6 passed`.

### WR-07: config values were neither validated nor coerced

**Files:** `boty/config.py`, `tests/test_config.py`
**Commit:** `d8a11fc`

Three holes, all the same shape — a plausible typo produced a config that
loaded fine and a monitor broken in a way nothing reported:

1. `max_price` was not coerced while `target` was, so `max_price: "80"` reached
   `alertable` and raised on `float <= str`. Under `watch` the loop's handler
   caught it, so the service stayed up while every cycle aborted. Now coerced,
   and refused by name if not numeric — including `max_price: true`, since
   `bool` is an `int` subclass and `float()` would happily make it `1.0`.
2. `interval_seconds` accepted 0 and negatives, making the jittered sleep zero
   — an uncapped request loop against live retailers, violating "polite
   polling, never sub-minute". Floor of 60 enforced at load.
3. An unset `${VAR}` expanded to `""` in silence. Now logged **by name only** —
   a test pins that the value is never echoed, since these hold bot tokens and
   a log line is not a mode-600 file.

**Before:** 7 failed —

```
E  AssertionError: assert '80' == 80.0
E  Failed: DID NOT RAISE ValueError      (x4: non-numeric price, interval 30 / 0 / -1)
E  AssertionError: assert 'BOTY_NOTIFY_URL' in ''
E  test_the_shipped_config_still_loads - assert False
```

**After:** `11 passed`.

This one is already visibly working in production — `make verify` now prints
`config references ${BESTBUY_API_KEY}, which is not set — substituting empty`,
which previously happened in silence.

### WR-08: the watch loop swallowed every exception, so a broken monitor looked alive

**Files:** `boty/cli.py`, `tests/test_cli_watch.py`
**Commit:** `691e263`

`except Exception: logging.exception("continuing")` is right for a transient
failure and catastrophic for a persistent one: the systemd unit stays
`active (running)`, the process never exits non-zero, the health-warning call
is itself inside the `try` so it never runs, and `status.json` keeps serving
whatever it last held.

Consecutive failures are now counted. Three in a row sends a health warning
naming the real problem ("running but not monitoring"); ten in a row exits 1,
because the exit code is the only signal a supervisor can act on. A successful
cycle resets the count, so intermittent faults are still tolerated silently.
The stuck-monitor warning is best-effort — whatever broke the cycle may have
broken notification too.

**Before:** 4 failed —

```
E  AssertionError: three cycles raised in a row and nothing was said
E  assert [] == [['(all)']]
E  assert 0 == 1        (gave up after 50 failing cycles? no — ran all 50 and returned success)
```

**After:** `13 passed`. Both thresholds are pinned from each side (nine
failures still keeps trying; the warning fires once, not every cycle) so
neither can drift into a no-op.

### Supporting fix: `config/` copied into the mutation sandbox

**File:** `scripts/mutation_check.py`
**Commit:** `458678e`

WR-07's `test_the_shipped_config_still_loads` raised `FileNotFoundError` inside
the mutation sandbox, which does not copy `config/`. The harness failed closed
and refused to proceed — "This is not a result. Nothing was proved about the
test suite either way." — which is correct behaviour and is not what changed.
The sandbox must be a faithful copy of what the suite reads, or a test failing
there for want of a file is indistinguishable from a mutation being caught.
`Makefile` was already in the list for the same reason.

Caught by gate 3 rather than by review; recorded here because it is a real
change to a verification tool.

## Deferred (Info — out of scope)

Left in place as instructed, all six:

| ID | File | Summary |
|----|------|---------|
| IN-01 | `boty/retailers.py:22` | Unused module logger — remove it or add a `log.debug` on the `_pick` outcome. |
| IN-02 | `tests/test_parse.py:5-9` | Docstring's None-vs-`[]` rationale does not match the caller; `check_html` uses `if not offers:` for both. Comment misstates the contract. |
| IN-03 | `boty/parse.py:72` | `@type` as a list (`["Product", "ProductModel"]`) not recognised. Fails safe to UNKNOWN, costs coverage not correctness. |
| IN-04 | `scripts/mutation_check.py` | No mutation covers `Result.alertable` / the price ceiling. Worth adding as M4 — note WR-01 has since added tests it would exercise. |
| IN-05 | `scripts/mutation_check.py` | `build_sandbox` leaks its temp dir if a required path is missing; `_failed_tests` depends on `-ra` being inherited. |
| IN-06 | `boty/fixtures.py:61,66` | Fixture path components not sanitised — `capture-fixture ../../x` writes outside the tree. |

IN-04 and IN-05 are both in `scripts/mutation_check.py`, which this run touched
for an unrelated reason (`458678e`); they were deliberately **not** folded in,
to keep the commit scoped to the gate failure it fixes.

## Verification gates

All three run on the final tree, verbatim.

### `.venv/bin/python -m pytest tests/ -q`

```
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 0.24s
exit=0
```

Was 36 passed; now 99, all green.

### `.venv/bin/python -m mypy`

```
Success: no issues found in 13 source files
exit=0
```

### `make verify`

```
99 passed in 0.23s
Success: no issues found in 13 source files
fixtures: 4 fixture(s) under .../tests/fixtures
  ok       gamestop/goplusplus: 0d — OutOfStock from GameStop, $54.99, via schema.org ld+json
  ok       gamestop/ps5-control: 0d — InStock control, $549.99, seller GameStop, via schema.org ld
  ok       walmart/goplusplus: 0d — IN_STOCK but seller is a marketplace reseller at ~4x MSRP; m
  ok       walmart/milk-control: 0d — IN_STOCK control, first-party seller Walmart.com
config references ${BESTBUY_API_KEY}, which is not set — substituting empty
config references ${BOTY_NOTIFY_URL}, which is not set — substituting empty
control check: 2 control(s), live
  in_stock      gamestop  CONTROL — PS5 console                $549.99  ld+json: InStock from GameStop
  in_stock      walmart   CONTROL — Great Value whole milk       $2.42  __NEXT_DATA__: IN_STOCK from Walmart.com
control check: PASS — 2/2 controls in stock
mutation check: 3 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (99 passed in 0.30s)
  CAUGHT    M1 boty/parse.py: 8 test(s) failed — test_gamestop_out_of_stock_fixture, test_gamestop_control_fixture_has_a_buyable_offer, test_ldjson_ignores_malformed_blocks (+5 more)
  CAUGHT    M2 boty/retailers.py: 2 test(s) failed — test_an_unknown_reading_neither_alerts_nor_erases_what_is_known, test_unparseable_page_is_unknown_not_out_of_stock
  CAUGHT    M3 boty/retailers.py: 5 test(s) failed — test_walmart_reseller_rejected_by_first_party_filter, test_unattributed_offer_is_not_first_party_on_a_marketplace, test_walmart_offer_with_no_seller_recorded_is_unknown_not_a_verdict (+2 more)
mutation check: 3/3 mutations caught
VERIFY: PASS
make verify exit=0
```

This is a genuine `VERIFY: PASS`, not the new offline-qualified one: the live
controls actually ran and both retailers reported their control in stock. Note
the new replay test now also catches mutation M2 — it is doing regression work
beyond the single finding it was written for.

---

_Fixed: 2026-08-02_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
