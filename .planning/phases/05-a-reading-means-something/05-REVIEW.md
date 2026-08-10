---
phase: 05-a-reading-means-something
reviewed: 2026-08-10T13:05:00Z
depth: deep
files_reviewed: 14
files_reviewed_list:
  - boty/models.py
  - boty/config.py
  - boty/parse.py
  - boty/retailers.py
  - boty/status.py
  - boty/monitor.py
  - boty/notify.py
  - boty/pacing.py
  - boty/cli.py
  - scripts/identity_check.py
  - scripts/mutation_check.py
  - config/products.yaml
  - served/boty/index.html
  - .gitignore
findings:
  critical: 3
  warning: 8
  info: 4
  total: 15
status: findings
---

# Phase 5: Code Review Report

**Reviewed:** 2026-08-10T13:05:00Z
**Depth:** deep (static review + offline suite; no live retailer reads)
**Files Reviewed:** 14 source files (plus the phase's test files, read for coverage gaps only)
**Status:** findings

## Summary

The phase's central mechanism is sound where it is wired: `_verdict_from_html`'s two
guards sit ahead of every stock verdict, they are keyed on the single `STORE_SCOPED`
definition that `assess_health` also reads, `Result.store` is threaded onto every return
including the error paths, and the dashboard's new `storeTag` puts both interpolated
values through `esc()` exactly like its neighbours. The persisted pacer state is
defensively parsed — `isinstance` at every step, both age bounds, the `bool`-is-`int`
trap handled, the refusal count clamped, write failures degraded to in-memory. The
offline suite is green (642 passed, 9.8s).

Three things are wrong, and all three defeat the phase's own stated purpose rather than
merely degrading it.

The guard is enforced on a **config string that is never validated, never coerced and
compared case-sensitively**. `retailer: Walmart` instead of `walmart` — one capital —
routes to the same generic checker, reads the same Walmart page, and produces
`in_stock $2.42` with a green health row from a store nobody pinned. Reproduced below.

The health arm **names a cause it did not measure** for any non-refusal transport
failure. A DNS error or a connection timeout on a pinned Walmart control produces
`store=None`, which `_is_store_gap` reads as a store gap, and the alert tells the
operator to go check `store_id` in `config/products.yaml`. That is REQ-15's defect,
rebuilt inside the arm that was added to fix it.

And the store number — the geolocator this repo force-rewrote 170 commits of history to
remove — **goes out in the push notification body**, unredacted, via
`failing_controls` → `Result.detail`. Both the pinned store and the answering store.
The documented notification transports include `ntfy://<topic>`, where a topic is
world-readable unless auth is configured.

Everything below is reproduced against the tree, not inferred.

## Critical Issues

### CR-01: A one-letter `retailer:` typo silently disables the store guard and publishes an arbitrary store's verdict

**File:** `boty/config.py:226`, `boty/retailers.py:253`, `boty/models.py:138`
**Issue:** `Config.load` takes `retailer=entry["retailer"]` verbatim — no `str()`
coercion (unlike `target`), no case normalisation, and no validation against the set of
retailers the code actually knows. Every consumer compares it case-sensitively:
`_make_checker`'s `== "bestbuy" / "amazon" / "target"`, `retailers.MARKETPLACES`, and
now `watch.retailer in STORE_SCOPED`. An unrecognised value falls through
`_make_checker` to `check_html`, which is the *correct* transport for Walmart — so a
capitalised `Walmart` reaches Walmart's real page, parses it perfectly, and skips both
the guard and `_is_store_gap`.

Reproduced against `tests/fixtures/walmart/milk-control.html`:

```
walmart  -> unknown       price=None store='0' health_ok=False
           detail: the page named store '0'; this watch pins store '4521' — ...
Walmart  -> in_stock      price=2.42 store='0' health_ok=True
           detail: __NEXT_DATA__: IN_STOCK from Walmart.com
```

This is the exact 2026-08-09 failure the phase exists to prevent — a price and an
availability from a store the operator did not ask about, published as a verdict, with
the dashboard green — and it is reachable by a plausible YAML typo that nothing warns
about. `tests/test_monitor.py:274` asserts the opposite as an invariant ("the guards in
`retailers.py` already made it impossible for an unpinned reading to be IN_STOCK at
all"); that claim holds only for the exact lowercase spelling.

**Fix:** validate the key at load, fail-closed, in `Config.load`:

```python
#: Every retailer this build knows how to check. A watch naming anything else
#: cannot be checked correctly — `_make_checker` would fall through to
#: `check_html`, and `models.STORE_SCOPED` would not recognise it, so a
#: store-scoped retailer would lose its guard silently.
KNOWN_RETAILERS = frozenset({"walmart", "gamestop", "bestbuy", "amazon", "target"})

retailer = str(entry["retailer"]).strip().lower()
if retailer not in KNOWN_RETAILERS:
    raise ValueError(
        f"watch {entry.get('name')!r}: unknown retailer {entry['retailer']!r} — "
        f"expected one of {', '.join(sorted(KNOWN_RETAILERS))}"
    )
```

Refusing the file is the right idiom here rather than `_store_id`'s log-and-continue:
an unknown retailer is not a legitimate state (unlike an absent pin), and the
alternative is a verdict about the wrong store. Add a test that a store-scoped retailer
spelled with any casing still reaches the guard.

### CR-02: A plain fetch failure on a pinned Walmart control is reported as a store-pin config gap

**File:** `boty/monitor.py:88-107` (`_is_store_gap`), `boty/monitor.py:174-197` (the arm)
**Issue:** `_is_store_gap` excludes refusals and then treats `c.store != c.watch.store_id`
as a store gap. But `check_html`'s `FetchError` arm returns `refused=is_refusal(exc)`,
and `is_refusal` is True only for `Blocked` and statuses `{401, 403, 429}`
(`boty/fetch.py:135-142`). A connection timeout, a DNS failure, a TLS error, an HTTP 500
or 502 — all of which produce **no page at all** — return `refused=False, store=None`,
which satisfies `c.store != c.watch.store_id`.

Reproduced:

```
>>> r = Result(walmart_control_pinned_4521, Availability.UNKNOWN,
...            detail='fetch failed: connection timed out', refused=False, store=None)
>>> assess_health([r])[0].reason
'a control reading cannot be shown to come from the store this watch is about —
 store_id is unset in config/products.yaml, or the page answered for a different
 store. Each control below names what the page said and what is pinned'
```

Neither disjunct in that sentence is true: `store_id` *is* set, and no page answered for
any store. The arm deliberately omits `CAUSE_UNKNOWN` because "the code MEASURED" the
cause — but here it measured nothing, and it points the operator at the wrong file. That
is REQ-15's defect ("no alert names a cause the code has not established") reintroduced
by the arm added to serve REQ-15. The same applies to a Walmart page that parses but
stops emitting `product.location.storeIds`: the honest reading is "the page shape
changed", not "check your store_id".

`_is_store_gap`'s own docstring already contains the right argument for refusals — "A
refusal means no page came back, so the store could not have been established either" —
it just does not extend it to the other no-page outcomes.

**Fix:** require a positive store fact before claiming a store gap. Only two states are
genuinely measured: the pin is absent, or a store *answered* and it was the wrong one.

```python
def _is_store_gap(c: Result) -> bool:
    if c.refused:
        return False
    if c.watch.retailer not in STORE_SCOPED:
        return False
    if c.watch.store_id is None:
        # Measured: nobody pinned a store. True regardless of what came back.
        return True
    # A page that named NO store establishes nothing about the pin — a timeout,
    # a 500 and a reshaped payload all land here, and none of them is a config
    # gap. Only a store that answered and disagreed is a measured mismatch.
    return c.store is not None and c.store != c.watch.store_id
```

Everything else falls to the breakage arm, which carries `CAUSE_UNKNOWN` and is the
reading that claims least. Add the missing test: a pinned store-scoped control with
`refused=False, store=None` must **not** produce a reason containing `store_id`.

### CR-03: The operator's store number is sent verbatim in the push-notification body

**File:** `boty/retailers.py:288-302` → `boty/monitor.py:221` → `boty/notify.py:84-94`
**Issue:** The mismatch guard's `detail` interpolates both store numbers:

```python
f"the page named {answered}; this watch pins store {watch.store_id!r} — ..."
```

`assess_health` copies each broken control's `detail` into `failing_controls`
(`monitor.py:221`), and `send_health_warning` joins `h.reason` and `h.failing_controls`
into the notification body with no redaction of any kind (`notify.py:84-87`). Reproduced
body:

```
[walmart] a control reading cannot be shown to come from the store this watch is about — ...
  * CONTROL milk: unknown (the page named store '0'; this watch pins store '4521' —
    a reading that cannot be shown to come from the pinned store is not a verdict about it)
```

`'4521'` there is the operator's pinned store — the value `config/products.yaml`
refuses to hold even as a commented example, that `_store_id`'s docstring calls "a
geolocator — it resolves publicly to one street address", and that `3bd1663` rewrote 170
commits to remove. It now leaves the machine on every store-mismatch page, over a
third-party transport whose documented options include `ntfy://<topic>` (public unless
authenticated) and `discord://` / `tgram://` webhooks. This is not a hypothetical arm:
the mismatch case is the 2026-08-09 incident the phase was built around, so it is the
arm most likely to fire.

Note the surrounding code takes this seriously everywhere else — `_redact_host_paths`
exists so a home directory does not reach `Result.detail`, and `check_bestbuy_api`
redacts its key out of exception text — so the omission is inconsistent with the
module's own standard, not with an absent one.

**Fix:** keep the numbers on the local surfaces (terminal, gitignored `status.json`) and
strip them from anything that leaves the box. The cleanest cut is at the notification
boundary, so `Result.detail` stays diagnostic:

```python
# notify.py
_STORE_NUM_RE = re.compile(r"store '([^']*)'")

def _redact_store_numbers(text: str) -> str:
    """A store number resolves to one street address. It is useful on the
    dashboard, which is ours; it has no business on a third-party push
    transport, which may be a public ntfy topic."""
    return _STORE_NUM_RE.sub("store <redacted>", text)
```

applied to both `h.reason` and each `failing_controls` entry in `send_health_warning`.
The alert still says *that* the store disagreed, which is the actionable fact; the
operator reads *which* off their own dashboard. Add a test asserting the pinned
`store_id` string never appears in the composed body.

## Warnings

### WR-01: The persisted paging memory never ages out and never self-cleans

**File:** `boty/pacing.py:333-336` (load), `boty/pacing.py:360-368` (save), `boty/cli.py:335`
**Issue:** `STATE_MAX_AGE_SECONDS` is applied to `retailers[*].refused_at` and to nothing
else. `warned` is restored unconditionally, whatever the file's age. Combined with
`still_unhealthy = ... | (warned - checked)` (cli.py:335), an entry only leaves `warned`
when the retailer is *checked and no longer pageable* — which, for a genuinely broken
detector, never happens.

Concrete consequence: a `pacer-state.json` written months ago carrying
`"warned": ["walmart"]` is restored on startup; walmart's control is broken; `pageable`
contains it, `fresh` excludes it (already in `warned`), `still_unhealthy` re-adds it, and
it is re-saved every cycle. No health warning is ever sent, indefinitely, from evidence
the module's own docstring says "has outlived the reasoning that produced it". The
document's self-cleaning claim in `save`'s docstring holds only for the `retailers` half:
a retailer deleted from the config stays in `warned` forever, and there is no bound on
the list's length.

**Fix:** stamp and age the paging memory the same way the refusal counts are, e.g. write
`{"warned": {"<retailer>": <wall clock>}}` under a bumped `STATE_VERSION` and apply the
identical `0.0 <= now - stamp <= STATE_MAX_AGE_SECONDS` window in `load`. Add the
mutation-check counterpart to M12 for the `warned` half, and a test that a `warned`
entry older than the cap is discarded.

### WR-02: The new identity-gate rule misses the single-quoted YAML spelling it claims to cover

**File:** `scripts/identity_check.py:269-270`
**Issue:** The pattern ends `\s*:\s*"?(\d+)` — it accepts an optional *double* quote
only. Measured against the shipped rule:

```
'store_id: 4521'                  -> ['store number in a config key 4521']
'store_id: "4521"'                -> ['store number in a config key 4521']
'storeId: 4521'                   -> ['store number in a config key 4521']
"store_id: '4521'"                -> []        <-- walks through
'  - {name: x, store_id: 4521}'   -> []        <-- walks through
'store_id: !!str 4521'            -> []        <-- walks through
```

Single-quoted scalars are an ordinary YAML spelling, and the natural one for a value the
author wants kept as a string. The 30-line comment above the rule asserts that
"*every* YAML spelling of the exact key REQ-14 adds to `config/products.yaml`" was
measured, and records two residuals — commented lines and the `restore_id` over-catch —
but not this one. `tests/test_identity_check.py:1229-1231` probes bare, double-quoted and
camelCase forms and no single-quoted form, so the gap is untested as well as
undocumented. A gate whose stated coverage exceeds its real coverage is worse than one
with a known hole.

**Fix:**

```python
(r'(?m)^\s*[A-Za-z_]*[Ss]tore(?:_?[Ii][Dd]|_?[Nn]umber|_?[Nn]o|_?[Cc]ode)?\s*:\s*["\']?(\d+)',
 "store number in a config key"),
```

and drop the `^\s*` anchor requirement for the flow-mapping form (or add a second rule
allowing a preceding `{` / `,`). Extend the probe table in `tests/test_fetch.py` with
`store_id: '12345'` and `{store_id: 12345}` and update the residuals paragraph to
whatever is genuinely left uncovered.

### WR-03: `store_id: 04521` is silently reinterpreted as octal 2385

**File:** `boty/config.py:82-141`
**Issue:** `_store_id` correctly guards the `bool` typo and correctly `str()`-coerces the
int YAML hands it — but PyYAML resolves a leading-zero all-digits scalar as **octal**
before `_store_id` ever sees it:

```
store_id: 04521  ->  2385  ->  '2385'
store_id: 1_234  ->  1234  ->  '1234'
store_id: 12:30  ->   750  ->   '750'
```

The failure is in the safe direction (the pin never matches, so the reading is UNKNOWN)
but it is silent and the diagnosis is actively misleading: the alert says "this watch
pins store '2385'" for a file that says `04521`, and the operator has no way to see the
transformation. The function's own docstring makes exactly this argument for the `str()`
coercion ("an `int` compared against the string Walmart puts in its own JSON is a silent
never-match") and then stops one step short of the value YAML mangled on the way in.

**Fix:** refuse a non-string pin outright, which forces the quoted form and makes the
YAML resolver irrelevant:

```python
if not isinstance(value, str):
    raise ValueError(
        f"{where}: store_id must be quoted — YAML reads an unquoted store number "
        f"as an integer, and a leading zero as OCTAL ({value!r}). Write "
        f"store_id: \"...\" or store_id: ${{WALMART_STORE_ID}}"
    )
```

`${WALMART_STORE_ID}` substitution already produces a `str`, so the shipped config is
unaffected. Alternatively keep the coercion and warn loudly when
`str(value) != str(raw_scalar)`.

### WR-04: `Pacer.record` does not clamp `refusals`, so the overflow `MAX_PERSISTED_REFUSALS` exists to prevent is still reachable

**File:** `boty/pacing.py:217-240`
**Issue:** `MAX_PERSISTED_REFUSALS = 64` is applied only on the load path
(`pacing.py:330`). `record` increments `st.refusals` without bound and then evaluates
`st.interval * BACKOFF_FACTOR ** st.refusals`. The constant's own comment measures the
cliff: `2.0 ** 1024` raises `OverflowError`, which propagates out of `record` → `run_once`
→ `watch_cycle`, is counted by `watch_loop`'s handler, and after
`FAILURES_BEFORE_GIVING_UP` exits the service. A long-lived process against a retailer
refusing at the 6-hour cap reaches that in roughly 256 days — improbable, but the guard
was written precisely because "a one-line denial of service on the monitor" is not
acceptable, and the in-memory path has no guard at all.

**Fix:** clamp at the source, so load and record cannot disagree:

```python
st.refusals = min(st.refusals + 1, MAX_PERSISTED_REFUSALS)
```

The constant is already documented as "far below the crash point and far above where the
cap binds", so this costs nothing operationally and makes the load-path `min()`
redundant-by-agreement rather than the only defence.

### WR-05: `pacer.save()` in a `finally` can raise a type it does not catch, replacing the give-up exit

**File:** `boty/cli.py:411-429`, `boty/pacing.py:369-377`
**Issue:** `save` wraps only `OSError`. `json.dumps` and `sorted(warned)` are inside the
`try`, but `sorted` over a set with mixed key types raises `TypeError` — reachable
because `Watch.retailer` is not coerced (see CR-01), so `Health.retailer` and therefore
`warned` can hold a non-`str`. Because the call sits in a `finally`, a raise there also
*discards* the pending `return 1` on the give-up path, converting a diagnosable exit code
into a traceback from the wrong place — the exact outcome `_warn_monitor_is_stuck`'s
docstring says it exists to avoid. `save`'s own docstring commits to "failing to persist
a backoff must degrade to the old in-memory behaviour, never take down a cycle"; the
handler is narrower than that promise.

**Fix:** widen the handler to `except Exception:` with the same `log.exception` message,
or (better, and complementary) fix the root cause in CR-01 and keep `OSError` for the
I/O half while adding `except (TypeError, ValueError)` around the serialisation.

### WR-06: `warned` is keyed only by retailer, so a failure that changes cause is never re-paged

**File:** `boty/cli.py:316-345`
**Issue:** `warned` records *that* a retailer was paged, not *what about*. A retailer that
was paged for an entrenched refusal and then starts answering with a broken control — or
with a store gap — stays in `warned` (it is still `pageable`, so `still_unhealthy`
carries it, and `fresh` excludes it). The operator is never told the failure changed into
one that needs a different action. Pre-existing in shape, but 05-03 made it materially
worse: before, a paced-out cycle cleared the memory, and a restart cleared it entirely;
now the union at line 335 plus persistence means the episode can outlive the cause
indefinitely.

**Fix:** key the episode on the pair, not the retailer:

```python
# The episode is (retailer, what kind of failure) — a refusal that becomes a
# broken detector is a NEW thing to say, not the same thing said twice.
def _episode(h: Health) -> str:
    return f"{h.retailer}:{'refused' if h.refused else 'unverified'}"
```

and carry `set[str]` of episode keys through `warned` / `Pacer.load` / `Pacer.save`
(bump `STATE_VERSION`). `checked` then compares on the retailer prefix.

### WR-07: `status.json` publishes the operator's pinned store to everything that can reach the dashboard

**File:** `boty/status.py:142-143`, `boty/monitor.py:260-267`
**Issue:** `"store_pinned": r.watch.store_id` writes the geolocator into
`served/boty/status.json`. The file is correctly gitignored (`.gitignore:31`), but it is
served over HTTP by design and the dashboard is bound to all interfaces in this
deployment. `Result.detail` carrying both numbers lands in the same file. Separately,
`run_once` logs `r.detail[:70]` at INFO (`monitor.py:260-267`), which for the mismatch
message includes both store numbers in journald.

Lower severity than CR-03 because the surface is the operator's own tailnet rather than a
third-party transport, and because `store_pinned` is genuinely needed to render the tag —
but it is the same value class, and the decision to publish it is not argued anywhere in
`status.py`'s otherwise exhaustive comment (which argues only about `null` versus `0`).

**Fix:** state the decision explicitly in `status.py`'s comment (who may reach this file,
and why that is acceptable) so a future reader does not have to re-derive it, and consider
serving the *derived* tag state (`match` / `mismatch` / `unpinned` / `not-stated`) plus
only the answering store, keeping the pinned value out of the file entirely — the
dashboard's four render branches need nothing more than that.

### WR-08: `check_bestbuy_api` bypasses `_verdict_from_html`, so `STORE_SCOPED` is unenforced on that path

**File:** `boty/retailers.py:725-813`, `boty/models.py:134-137`
**Issue:** `models.STORE_SCOPED`'s comment states the cost of adding a retailer as: "every
watch for it starts reading UNKNOWN until somebody pins a store, including the control".
That is only true for the four adapters that route through `_verdict_from_html`.
`check_bestbuy_api` builds its `Result` directly and never consults `STORE_SCOPED`, so
adding `bestbuy` (or any future API-backed retailer) to the set would yield a guarded
browser path and an unguarded API path — a verdict from an unpinned store, on the rung
`_make_checker` *prefers*. Latent today, and exactly the "one definition, two readers"
drift the constant's own comment is written to prevent.

**Fix:** either add the guard to `check_bestbuy_api` (an API reading also cannot be shown
to come from a pinned store), or state in `STORE_SCOPED`'s comment that the API path is
unguarded and that adding an API-backed retailer to the set requires wiring it there
first. The former is preferable — a one-line `if watch.retailer in STORE_SCOPED and
watch.store_id != <nothing measurable>` is awkward, so the honest version is to return
UNKNOWN for any store-scoped retailer reached over a transport that cannot report a
store.

## Info

### IN-01: `_refusal_is_entrenched` reaches into `Pacer._for` and mutates as a side effect of a query

**File:** `boty/cli.py:230-234`
**Issue:** A private member of another module, and `_for` *creates* a `_RetailerState`
entry when one is absent — so asking "is this refusal entrenched?" silently grows
`Pacer._state`, which `save` then writes (harmlessly, since `refusals` is 0 and the
comprehension filters it out). Works, but couples `cli` to `pacing`'s internals and makes
a read-shaped call a write.
**Fix:** add `Pacer.refusals(retailer) -> int` as a non-mutating public query
(`self._state.get(retailer)` with a `0` default) and call that.

### IN-02: The two store-tag renderers do not consult `STORE_SCOPED`

**File:** `boty/cli.py:89-119`, `served/boty/index.html:104-119`
**Issue:** Both branch purely on `store` / `store_pinned` being present. `nextdata_store`
is called unconditionally for every retailer, so if any non-Walmart page ever emits
`props.pageProps.initialData.data.product.location.storeIds`, that retailer's rows render
a loud `store X · unpinned` warning tag for a retailer where no pin is expected or
meaningful. No verdict is affected (the guard and `_is_store_gap` both key on
`STORE_SCOPED`), so this is cosmetic — but it is the one place the phase's single
definition is not consulted.
**Fix:** publish a `store_scoped` boolean alongside `store` / `store_pinned` in
`status.write` and gate the `unpinned` branch on it in both renderers.

### IN-03: `__NEXT_DATA__` is extracted and JSON-parsed twice per Walmart page

**File:** `boty/parse.py:326-390`, `boty/retailers.py:200-201`
**Issue:** `nextdata_store` runs `_NEXTDATA_RE.search` and `json.loads` over the same
~470KB blob `nextdata_offers` parses moments later. Correctness is unaffected and the
duplication buys real independence between the two readers, but a shared
`_nextdata_doc(html)` helper would give both the same parsed document — which is also the
stronger guarantee, since it makes "the store and the offer came from the same parse"
true by construction rather than by both re-reading the same bytes.

### IN-04: Two behaviours added by this phase have no test

**File:** `tests/test_monitor.py:200-284`, `tests/test_pacing.py`
**Issue:** (a) No test covers a pinned store-scoped control failing for a **non-refusal
transport reason** (`refused=False, store=None`) — the CR-02 path; the suite's four store
cases are unpinned, mismatched, mixed-with-breakage and mixed-with-refusal. (b) No test
covers `warned` restored from a file older than `STATE_MAX_AGE_SECONDS` — because there is
no such behaviour (WR-01). Both gaps are why a green 642-test run does not contradict the
findings above.
**Fix:** add both cases when fixing CR-02 and WR-01; the second belongs beside
`test_state_older_than_the_backoff_cap_is_discarded`.

## Verified Clean

Stated so the fixer does not re-litigate ground that holds:

- **Guard placement.** Both `STORE_SCOPED` returns sit after `extraction` is settled and
  before `if not offers:`, so no stock verdict can form ahead of them, and both guarded
  Results carry the same `rung`, `extraction`, `url` and `store` as every other return.
- **Guards do not over-fire on non-Walmart.** `watch.retailer in STORE_SCOPED` gates both
  returns; `_is_store_gap` gates on the same frozenset; there is no second copy of the
  predicate. (Subject to CR-01's casing hole, which is a config-validation defect rather
  than a drift between the two readers.)
- **Dashboard XSS.** `storeTag` puts both `w.store` and `w.store_pinned` through `esc()`,
  and both land in text content rather than in an attribute. `esc` covers `& < > " '`.
  No new sink.
- **Persisted state as untrusted input.** `load` catches `(OSError, JSONDecodeError)`,
  version-checks, `isinstance`-checks name, entry, `refusals` (with the `bool`-subclass
  trap) and `refused_at`, bounds the stamp in both directions (so `inf` and `NaN` are
  discarded), clamps the count, and never reads `interval` or `due_at` from the file. A
  corrupt, absent, truncated, directory-shaped or hostile file yields a usable pacer.
- **`due_at` is genuinely never persisted**, so a restart always re-tests the condition
  once at full rate — the withdrawn docstring's concession is intact.
- **`still_unhealthy` cannot page a recovered retailer.** `fresh` is drawn only from
  `pageable`; `warned - checked` contributes to the carried memory, never to the send
  list. The failed-delivery rollback (`still_unhealthy - fresh`) is correct and reaches
  disk through the `finally`.
- **`config/products.yaml` holds only `${WALMART_STORE_ID}`** on both Walmart watches, no
  literal anywhere, and the comment block carries no digits at all — consistent with the
  documented blind spot that `#`-commented lines are not scanned by the identity gate.
- **Both Walmart fixtures are redacted to the `0` placeholder** and both `.json` sidecars
  now say so explicitly; `nextdata_store` correctly has no special case for it.
- **`.gitignore`** covers `pacer-state.json` as a bare basename (matches at any depth),
  and `served/boty/status.json` was already covered.

---

_Reviewed: 2026-08-10T13:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
