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
fixed_at: 2026-08-10
fixed_by: gsd-code-fixer
dispositions:
  fixed: [CR-01, CR-02, CR-03, WR-01, WR-02, WR-03, WR-05]
  deferred: [WR-04, WR-06, WR-07, WR-08, IN-01, IN-02, IN-03]
  fixed_in_passing: [IN-04]
gate_after_fixes: "make verify-offline exit 0 — 667 passed, 16/16 mutations, identity PASS (181 files)"
---

# Phase 5: Code Review Report

**Reviewed:** 2026-08-10T13:05:00Z
**Depth:** deep (static review + offline suite; no live retailer reads)
**Files Reviewed:** 14 source files (plus the phase's test files, read for coverage gaps only)
**Status:** findings

---

## Dispositions, recorded 2026-08-10 after the fix pass

Each finding below carries a **Disposition** line. Seven were fixed, each in its own
commit, each watched going red first. Baseline before the pass: 642 passed, 14/14
mutations. After: **667 passed, 16/16 mutations, `make verify-offline` exit 0.** No
live retailer read was made.

**Two things about this file itself, recorded rather than quietly repaired:**

1. **A store number was redacted out of this document.** CR-03's own text below
   identifies the value it quotes as "the operator's pinned store", and this file is
   tracked and public — so the finding that a store number must not leave the box was
   written up in a way that put one into the repository. Every occurrence, and the
   octal value WR-03 derived from it, is now the `REDACTED` / `<octal>` placeholder.
   The shape of every measurement is unchanged. It remains in this repo's git history,
   in the review commit and in `3ddf504` (which copied it into a docstring in
   `boty/notify.py` before the identity gate caught it) — history is not rewritten
   here, because `QUESTIONS.md` § 0e already has that decision open with Dan.
2. **`scripts/identity_check.py` has no rule for this carrier.** The config-key rule
   catches `store_id: <n>`; it does not catch `store '<n>'` in prose, which is the
   shape `_verdict_from_html` writes and the shape this document leaked in. Not fixed
   here — a new rule needs a sweep of the whole tracked tree before it can be turned
   on without reddening `make verify` — and recorded as the follow-up it is.

**Not touched, deliberately:** no success criterion was amended, and the Phase 5
closing outcome table in `.planning/ROADMAP.md` was left exactly as it stood. Two
findings do bear on recorded verdicts and are flagged for the orchestrator rather
than absorbed — see CR-02 (criterion 4) and WR-01 (criteria 5 and 6).

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
           detail: the page named store '0'; this watch pins store 'REDACTED' — ...
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

**Disposition: FIXED, with the suggested fix corrected in two places** — `337d743`.

`models.KNOWN_RETAILERS` (beside `STORE_SCOPED`, on that constant's own
one-definition argument) plus `config._retailer`. A name differing from a known
retailer only by case or whitespace is REFUSED, naming the spelling to write; a name
that is no known retailer at all is logged at ERROR and loaded.

*Correction 1 — the suggested set would have refused the shipped config.*
`KNOWN_RETAILERS = {"walmart", "gamestop", "bestbuy", "amazon", "target"}` omits
`nintendo`, which `config/products.yaml` names on two watches. Taken verbatim,
`boty watch` would not have started. The set is now bound to `retailers.FIRST_PARTY`'s
keys by a test rather than by anybody's reading.

*Correction 2 — the reproduction understates its precondition.* The transcript's
`Walmart -> in_stock $2.42` needs `first_party_only: false`; the shipped config sets it
true. Re-measured against the same fixture:

```
first_party_only=True   walmart  -> unknown    price=None
first_party_only=True   Walmart  -> unknown    price=None
first_party_only=True   walmrt   -> unknown    price=None
first_party_only=False  walmart  -> unknown    price=None
first_party_only=False  Walmart  -> in_stock   price=2.42
first_party_only=False  walmrt   -> in_stock   price=2.42
```

The finding stands — under `first_party_only: true` the typo reads UNKNOWN only
because `Walmart` is also missing from `FIRST_PARTY`, which is luck, not a guard, and
the message it produces sends the reader to debug a seller list.

*Why unknown names are logged rather than refused, which is a departure from the
suggested fix.* Row 6 shows `walmrt` is dangerous in the same way, so refusing every
unknown name is the complete fix — and it makes two other gates unrepresentable.
`scripts/evidence_check.py` rule 1's test case is a **config-only `microcenter` watch
with no adapter at all**, and rule 5's is a **`pokemoncenter` watch shipped ahead of
its evidence**, whose own docstring says a blanket ban would make "the outcome this
whole phase is walking towards — a refused retailer re-probed, reached, and shipped —
unrepresentable". Refusing would kill rule 1 outright (`KNOWN_RETAILERS` is a subset of
`ROADMAP_RETAILERS`, so its condition could never fire again) and force 7 tests in
another phase's gate to be rewritten or deleted. **That is the orchestrator's call, not
the fixer's.** The residual is written down beside `KNOWN_RETAILERS`, tested, and
carries the two options for closing it.

Watched going red: with the loader hook removed, all 8 new assertions fail; the
shipped-config positive control passes on both sides.

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
>>> r = Result(walmart_control_pinned_REDACTED, Availability.UNKNOWN,
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

**Disposition: FIXED as suggested** — `32a0279`. `_is_store_gap` now requires a
positive store fact, and no new cause was invented for the gap it leaves: the reading
falls to the breakage arm, which carries `CAUSE_UNKNOWN`.

Two negative tests (the timeout path and the reshaped-payload path, which arrive
through different code) plus two positive ones, so the narrowing cannot have been met
by disabling the arm. Both negatives were watched failing against the unfixed tree;
both positives passed on either side. **M15** pins it — a mutation that restores the
exact clause and moves no availability, no price and no `ok` flag, only which sentence
a person reads, so a verdict-only suite would pass it straight through. This also
closes IN-04(a).

**Bears on a recorded verdict, flagged not absorbed.** The ROADMAP's criterion-4 row
records the `ast` alert-text gate as MET in the tree. That gate checks which arms carry
`CAUSE_UNKNOWN`; it cannot see which arm a given *reading* lands on, which is what was
wrong here. Criterion 4 was therefore MET by a gate that could not have caught this.
Whether the row needs a note is the orchestrator's call — the table is untouched.

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
  * CONTROL milk: unknown (the page named store '0'; this watch pins store 'REDACTED' —
    a reading that cannot be shown to come from the pinned store is not a verdict about it)
```

`'REDACTED'` there is the operator's pinned store — the value `config/products.yaml`
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

**Disposition: FIXED as suggested, and fixed first** — `3ddf504`.
`notify._redact_store_numbers`, applied to both joins. The regex matches either quote
delimiter, because `repr` switches when the value contains one; it stays keyed on the
carrier rather than on any run of digits, since the same body carries the SKUs, HTTP
statuses and prices somebody is being paged to read.

Prioritised above CR-01 and CR-02 because it is armed to fire on the very next action
the phase recommends: the number reaches a push body only when a pin is *set*, and
setting the pin is what the closing checkpoint asks Dan to do.

The test composes the detail through the real guard rather than typing it out, so it
cannot pass by agreeing with a string nobody produces. Watched going red: the body read
`this watch pins store '<the pin>'`. Both joins are asserted separately, because a fix
applied to one looks exactly like a fix applied to both.

**One thing this fix does not cover, and it is the same class:** `_redact_host_paths`
and this function are both prose filters. WR-07 records the other surfaces the number
still reaches (`status.json`, journald at INFO); those are deferred below.

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

**Disposition: FIXED as suggested** — `47c2afe`. Exactly the shape proposed,
`STATE_VERSION` 1 → 2, plus one thing the suggestion did not name and that the fix
turns on: **the stamp has to be the FIRST time, not the last.** `save` runs every
cycle, so stamping at write time would refresh the record forever — a bound that cannot
bind, which is worse than no bound because the file then reads as though it were dated.
`Pacer._warned_since` carries the episode's original start across writes, and a test
asserts the stamp survives two saves unchanged.

Reproduced first, against a 90-day-old document:

```
restored refusals: 0            <- correctly aged out
restored warned  : {'walmart'}  <- not aged out
```

**M16** is the M12 counterpart asked for; it gets its own mutation on M7's reason,
because a tree that ages one half of the document and not the other passes M12 and M13
together while silencing a broken detector forever. **M13 was re-anchored** — the
statement doing the work moved from a set comprehension to the return of an accumulated
set. This also closes IN-04(b).

**Bears on recorded verdicts, flagged not absorbed.** Criterion 5 ("pushed once") and
criterion 6 ("survives a restart") are both recorded MET. They still are — but the
persistence they were verified against silenced the retailer permanently once a stale
file existed, which is the opposite of what criterion 5 is for. Neither row is edited.

**Residual, stated because the fix is load-only:** within one long-running process the
memory still never ages, because the window is applied at `load`. That is WR-06's
territory (the episode is keyed by retailer, not by cause) and is deferred below.

### WR-02: The new identity-gate rule misses the single-quoted YAML spelling it claims to cover

**File:** `scripts/identity_check.py:269-270`
**Issue:** The pattern ends `\s*:\s*"?(\d+)` — it accepts an optional *double* quote
only. Measured against the shipped rule:

```
'store_id: REDACTED'                  -> ['store number in a config key REDACTED']
'store_id: "REDACTED"'                -> ['store number in a config key REDACTED']
'storeId: REDACTED'                   -> ['store number in a config key REDACTED']
"store_id: 'REDACTED'"                -> []        <-- walks through
'  - {name: x, store_id: REDACTED}'   -> []        <-- walks through
'store_id: !!str REDACTED'            -> []        <-- walks through
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

**Disposition: FIXED, going further than suggested** — `d35e4e5`. Reproduced exactly
as measured. The rule is now
`(?:^|[{,])\s*…\s*:\s*(?:!!\S+\s+)?["\']?(\d+)` — either quote, the `!!str` tag form
(which the finding listed but the suggested pattern did not cover), and the
flow-mapping position via the `[{,]` alternative rather than a second rule.

The residuals paragraph went from two entries to three, and residual 1 was **narrowed
rather than restated**: a commented *flow mapping* is now scanned, because `[{,]` does
not have to reach back past the `#`. More coverage, so the no-digits rule for the
`products.yaml` comment paragraph stands unchanged. Residual 3 is the prose over-catch
the alternative buys, accepted on residual 2's stated fail-closed trade.

Watched going red: the three new probes failed against the shipped rule. Then the
widened rule reddened `identity_check.py` **itself**, twice, while its own comment was
being written — once on a literal flow-mapping example, once on the sentence describing
residual 3. That is a better demonstration than the probe table, and both are now
described rather than quoted; the executable table lives in the one file `_PROBE_FILES`
exempts. The same run is what caught a store number in `boty/notify.py` — see the
dispositions header.

### WR-03: `store_id: 0<n>` is silently reinterpreted as octal

**File:** `boty/config.py:82-141`
**Issue:** `_store_id` correctly guards the `bool` typo and correctly `str()`-coerces the
int YAML hands it — but PyYAML resolves a leading-zero all-digits scalar as **octal**
before `_store_id` ever sees it:

```
store_id: 0REDACTED  ->  <octal>  ->  '<octal>'
store_id: 1_234  ->  1234  ->  '1234'
store_id: 12:30  ->   750  ->   '750'
```

The failure is in the safe direction (the pin never matches, so the reading is UNKNOWN)
but it is silent and the diagnosis is actively misleading: the alert says "this watch
pins store '<octal>'" for a file that says `0REDACTED`, and the operator has no way to see the
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

**Disposition: FIXED, taking the first option** — `5f8188d`. The alternative is not
available: `yaml.safe_load` has already discarded the raw scalar by the time
`_store_id` is called, so there is nothing to compare against without parsing the
document twice.

This **reverses `test_a_yaml_integer_store_id_is_coerced_to_a_string`**, which asserted
the opposite and had a good argument for it (an `int` against the `str` in Walmart's
own JSON is a silent never-match). That argument is kept and its method replaced —
refusing forces the quoted form, which cannot be outrun by the parser the way `str()`
was. The reversal is argued in place in both the test and the docstring, on this repo's
house style. A positive test pins both documented forms so the check cannot be met by
refusing everything.

Watched going red, then the identity gate reddened on the illustrative table in the
docstring and in the test — its own config-key rule catching its own examples — so both
are described rather than quoted, the same move WR-02 made.

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

**Disposition: DEFERRED — real, and not fixed here.** The reasoning is sound and the
fix is one line. It was left out because it is the only warning in this pass with no
route to a fail-safe violation: the finding's own arithmetic puts the crash at roughly
256 days of continuous refusal at the 6-hour cap, and `MAX_PERSISTED_REFUSALS` already
bounds every value that crosses a restart. Adding a one-line change with no test that
can be watched going red inside the cap's lifetime is worth less than saying plainly
that it was not done. Recommended as a follow-up, with the clamp and an
`OverflowError`-shaped test together.

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

**Disposition: FIXED, taking the first option** — `1328c0e`. `except Exception`, with
the document construction moved inside the `try` so `sorted(warned)` is actually
covered. The narrower option was rejected: this is a best-effort side effect called
from a `finally` on the failure path, so the class of exception is not the interesting
question — `_warn_monitor_is_stuck` makes exactly this argument one module over, and it
is the function whose docstring names the outcome being prevented. `log.exception`
keeps the type and traceback, so nothing is swallowed.

CR-01's coercion did close the specific `TypeError` route, as the finding predicted.
The handler is widened anyway, because the promise in `save`'s own docstring is about
persistence failing, not about one exception type.

Watched going red, both halves: `save({"amazon", 1})` raised straight out, and
`watch_loop`'s give-up path returned a `TypeError` instead of `1`. The second test
drives `json.dumps` rather than replacing `save`, because replacing `save` would test
the test.

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

**Disposition: DEFERRED — agreed, and it is a behaviour change, not a repair.** Changing
what an episode *is* changes when a person's phone rings, which is REQ-16's subject
matter rather than a defect in its implementation. WR-01 was fixed because a stale file
silencing a detector forever is unambiguously wrong; this one has a real trade on the
other side (a retailer whose failure oscillates between two causes would page on every
flip), and picking a side of it is a decision, not a fix.

WR-01 has already bumped `STATE_VERSION` to 2, so whoever takes this gets the version
bump for free and should fold the episode key into the same `warned` mapping the
timestamps now live in. Note also that WR-01's fix is load-only, so **this finding is
what still bounds the memory inside one long-running process.**

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

**Disposition: DEFERRED — and it is the one deferral worth looking at next.** CR-03 cut
the third-party transport, which is the surface that leaves the tailnet. This one is
about `served/boty/status.json` and about `run_once`'s INFO line, which puts both store
numbers into journald. Both are ours, which is why it is a warning and not a critical —
but "ours" is doing real work in that sentence and it is not argued anywhere in
`status.py`.

Not fixed here because the good version (serve the derived tag state and drop
`store_pinned` entirely) touches `status.write`, `boty/cli.py`'s renderer,
`served/boty/index.html` and their tests together — four surfaces and a schema change,
which is a plan item rather than a review fix. The comment-only half was left out too:
a comment recording a decision nobody has actually taken would be worse than the
silence.

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

**Disposition: DEFERRED — latent, and confirmed latent.** `STORE_SCOPED` is
`{"walmart"}` and `check_bestbuy_api` is reachable only for `bestbuy`, so no watch can
take the unguarded path today. The drift is real and the finding is right about it.

Not fixed here for a specific reason: the finding's own preferred fix — return UNKNOWN
for any store-scoped retailer on a transport that cannot report a store — is
unreachable dead code until somebody adds a retailer to the set, which means it cannot
be watched going red against anything. A guard nobody can see fail is precisely what
this project's standing rule refuses to trust. The cheap half (state in `STORE_SCOPED`'s
comment that the API path is unguarded and must be wired first) is also not done,
because that comment already says adding a retailer "is a decision with a commit message
behind it" and the honest place for this constraint is that commit, beside the change
that makes it live.

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

**Disposition: DEFERRED — correct, and it is a refactor.** The side effect is real and
harmless exactly as the finding says (`refusals` is 0, so `save`'s comprehension filters
it out), and WR-01's rewrite of `save` did not change that. Left alone because every
change in this pass was one somebody could be shown going red, and a non-mutating query
that behaves identically cannot be. Good first item for whoever touches `cli.py` next.

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

**Disposition: DEFERRED — and it should be folded into WR-07, not done on its own.**
Both findings add or remove a field in `status.json` and then change two renderers to
match; doing them separately means touching the same four surfaces twice and writing the
schema test twice. The finding is right that this is the one place the phase's single
definition is not consulted, and right that no verdict is affected.

### IN-03: `__NEXT_DATA__` is extracted and JSON-parsed twice per Walmart page

**File:** `boty/parse.py:326-390`, `boty/retailers.py:200-201`
**Issue:** `nextdata_store` runs `_NEXTDATA_RE.search` and `json.loads` over the same
~470KB blob `nextdata_offers` parses moments later. Correctness is unaffected and the
duplication buys real independence between the two readers, but a shared
`_nextdata_doc(html)` helper would give both the same parsed document — which is also the
stronger guarantee, since it makes "the store and the offer came from the same parse"
true by construction rather than by both re-reading the same bytes.

**Disposition: DEFERRED — and the finding argues its own other side.** A shared
`_nextdata_doc` would make "the store and the offer came from the same parse" true by
construction, which is stronger; the duplication buys real independence between the two
readers, which is what caught nothing yet but is why it was written that way. Neither is
wrong, so it is a design choice rather than a defect, and it belongs with somebody
holding a profile of a real ~470KB page rather than with a review fixer.

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

**Disposition: FIXED, both halves, exactly where the finding said to put them.**
(a) closed by `32a0279` — `test_a_page_that_never_arrived_is_not_reported_as_a_store_pin_gap`,
plus a second case for the reshaped-payload route, plus M15.
(b) closed by `47c2afe` —
`test_a_paging_memory_older_than_the_backoff_cap_is_discarded`, written as the sibling of
`test_state_older_than_the_backoff_cap_is_discarded`, plus its younger-than-cap and
future-stamp counterparts, plus M16.

The finding's closing observation held up under the pass: the 642-test run was green
because these two behaviours did not exist to be tested, not because they worked.

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

---

## Post-fix note: the "operator's pinned store" escalation was a FALSE ALARM

**Recorded 2026-08-10 by the orchestrator, because an unfounded leak claim left
standing is the same defect this milestone exists to close — one level up.**

The code-fixer escalated that this file had carried *"the operator's pinned
store"* into a tracked public file, and asked whether a history rewrite was
needed (the §0e class). It measured three things and none of them holds:

1. **There is no operator pinned store.** `WALMART_STORE_ID` is not set in
   `/home/dan/.config/boty/env` — Dan answered `defer` to Phase 5's checkpoint
   on 2026-08-10 and never set it. No such value exists to leak.
2. **`4521` was synthetic**, invented by the code-reviewer to reproduce CR-03.
   It is not this host's store and never was.
3. **Its hits in older commits are coincidental substrings.** `95f84a6`,
   `74ec742` and `2ee51d6` match inside SVG path coordinates — `3.34521` — not
   store numbers.

**No history rewrite is needed and none was done.** `QUESTIONS.md` § 0e is
unaffected and stays open on its own merits.

**The redaction that was applied is still correct**, and is kept: the identity
gate cannot distinguish a synthetic store number from a real one, and refusing
both is the fail-closed behaviour this project wants. The gate doing its job on
a made-up value is evidence it works, not evidence of a leak.

**Still open, and genuinely worth doing** — the fixer's second point stands:
`scripts/identity_check.py` has no rule for the `store '<n>'` *prose* carrier,
which is the shape CR-03 actually leaked through. Adding one needs a sweep of
the tracked tree first, so it was recorded rather than switched on blind.
