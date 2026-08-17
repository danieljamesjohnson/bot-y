---
phase: 07-a-reading-has-an-age
reviewed: 2026-08-17T13:02:46Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - boty/cli.py
  - boty/config.py
  - boty/models.py
  - boty/monitor.py
  - boty/pacing.py
  - boty/retailers.py
  - boty/status.py
  - scripts/mutation_check.py
  - served/boty/index.html
  - tests/test_cli_watch.py
  - tests/test_config.py
  - tests/test_dashboard.py
  - tests/test_models.py
  - tests/test_monitor.py
  - tests/test_pacing.py
  - tests/test_retailers.py
  - tests/test_status.py
findings:
  critical: 1
  warning: 8
  info: 3
  total: 12
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-08-17T13:02:46Z
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

The phase's central claim — *no unknown age is ever presented as a known one* — holds
on every path I could trace. I attacked it specifically and could not break it:

- All 20 `Result(` sites in `boty/retailers.py` name `read_at` explicitly; the 11/9
  read/non-read partition matches the AST gate and the four refusal arms carry a
  literal `None`, not the variable.
- `monitor._remembered_stamp` bounds the disk stamp at **both** ends, rejects `bool`
  (an `int` subclass), and drops only the age while keeping the availability — so a
  hand-edited number costs an age, never a re-alert.
- `status._remembered_rows`' `(UNKNOWN, None)` default and `status.write`'s literal
  `"alertable": False` mean a remembered row cannot borrow either a verdict or an
  authority. I traced the alert path end to end: `alerts` is built only from `Result`
  objects in `run_once`, and no remembered row ever becomes one. **No alertability
  leak found.**
- The scheduler/display invariant holds where `interval <= MAX_BACKOFF_SECONDS`:
  `record` computes its wait *through* `current_interval`, so there is one expression,
  not two.

What I did find splits into three groups.

**One security defect with a working proof of concept (CR-01).** `served/boty/index.html`
interpolates `w.availability` into an HTML `class` attribute **without `esc()`**, and
07-04 opened a data path from `state.json` — a mutable file the process trusts after a
restart — straight to that sink, because `monitor._remembered_availability` deliberately
does not validate the string against the enum. `tests/test_dashboard.py`'s escaping gate
cannot see it: `w.availability` is not in `UNTRUSTED`. This is the one finding where the
page's own stated rule ("escape once, at the sink, and apply it to **every** interpolated
value rather than to the ones currently known to be attacker-reachable") is broken.

**Two measured invariant breaks that the config loader permits (WR-01, WR-02).** Both are
about numbers the phase promises are one number. Neither is reachable on the shipped
`config/products.yaml`; both are reachable on a config `Config.load` accepts without
complaint, and I ran each rather than reasoning about it.

**The `pacer-state.json` direction question, answered.** The recorded failure direction
(*a truncated read over-reports staleness*) is **correct for every configured interval at
or below the 21 600-second cap**, and **inverts** above it — see WR-01. That is the one
place I can show it failing the dangerous way.

Everything else is quality: a negative duration on one surface where the other clamps, a
read accessor with a write side effect, a shared temp filename between two writers, and
a stale justifying comment that is load-bearing in a codebase where comments are the
argument.

## Critical Issues

### CR-01: A ledger string reaches `innerHTML` unescaped, through the row path 07-04 built

**File:** `served/boty/index.html:271` (`<span class="dot ${w.availability}"></span>`),
`boty/monitor.py:131-159` (`_remembered_availability`), `boty/status.py:362`
(`"availability": availability`), `tests/test_dashboard.py:75-85` (`UNTRUSTED`)

**Issue:**

Every other interpolated value on this page goes through `esc()`. `w.availability` does
not. Before 07-04 that was defensible: the only producer was `r.availability.value`, an
`Availability` enum member, so the value was one of three literals. 07-04 added a second
producer, and it is not enum-bounded.

The chain, each link quoted from the code:

1. `monitor._remembered_availability` returns *any* `str` a `dict` entry carries, and its
   docstring states the exemption as a decision: *"THE REMEMBERED AVAILABILITY IS NOT
   VALIDATED AGAINST THE `Availability` ENUM … The only comparison ever made against this
   string is `!= Availability.IN_STOCK.value`."*
2. `cli._remembered` pairs it up; `status._remembered_rows` passes it through;
   `status.write` publishes it verbatim as `"availability"`.
3. `index.html` interpolates it into an attribute value with no escaping.

Measured, not argued — run against this tree:

```
$ .venv/bin/python  # state.json entry: {"walmart:milk": {"availability": "\" onmouseover=alert(1) x=\"", "read_at": null}}
loaded seen: {'walmart:milk': '" onmouseover=alert(1) x="'}
published availability: '" onmouseover=alert(1) x="'
rendered: <span class="dot " onmouseover=alert(1) x=""></span>
```

The attribute is broken out of and an event handler is attached. Because the page is
proxied under Mission Control's `/tools/boty`, that runs on Mission Control's origin —
the exact consequence `tests/test_dashboard.py`'s own module docstring is written to
prevent.

**Reachability, stated rather than assumed:** the only writer of `state.json` today is
`State.save`, which serialises `result.availability.value`, so there is **no remote path
to this sink in the shipped tree**. What is demonstrated is the sink and the flow, not a
remote attacker. Two things nevertheless make this Critical rather than latent:

- the guard that is supposed to catch exactly this is blind to it. `UNTRUSTED` in
  `tests/test_dashboard.py` lists `w.read_at` with the explicit reasoning *"A value whose
  upstream is a file on disk is the last one to make an exception for"* — and then omits
  `w.availability`, which travels the same path out of the same file;
- the page's rule is not "escape what is currently reachable". It is *"escape once, at
  the sink, and apply it to every interpolated value … A rule of the form 'these three
  but not those two' does not survive the next edit to this template."* This is that
  rule already not surviving.

**Fix:** escape at the sink and close the gate that missed it.

```js
      <span class="dot ${esc(w.availability)}"></span>
```

and in `tests/test_dashboard.py`:

```python
UNTRUSTED = (
    "w.name",
    "w.detail",
    "w.retailer",
    "w.url",
    "w.store",
    "w.store_pinned",
    "w.read_at",
    "w.availability",   # ledger-provenance, like w.read_at: status.json's
                        # `availability` is whatever state.json said, because
                        # monitor._remembered_availability does not validate it
    "r.retailer",
    "r.reason",
)
```

Do **not** fix this by adding enum validation in `_remembered_availability` alone: that
would leave the sink unescaped and re-argue an exemption the page has already rejected in
writing. If the validation is added as well, `_remembered_availability`'s docstring must
stop claiming the string has one consumer (see WR-08).

## Warnings

### WR-01: A standing interval above the backoff cap makes a refusal ask *more* often — and inverts the recorded staleness direction

**File:** `boty/pacing.py:319-346` (`current_interval`), `boty/pacing.py:260-294`
(`record`), `boty/config.py:228-238` (`_interval`)

**Issue:** `current_interval` returns `min(st.interval * BACKOFF_FACTOR ** st.refusals,
MAX_BACKOFF_SECONDS)` once `refusals` is non-zero. When the standing interval already
exceeds the 21 600-second cap, that `min` returns a number **smaller** than the standing
interval, and `record` schedules `due_at = now + wait` from the same call — so a refusal
*shortens* the wait.

Measured on this tree with `interval_seconds: 86400`:

```
interval at 0 refusals: 86400.0
after ONE refusal -> refusals: 1  due_at: 21600.0  current_interval: 21600
log: "x refused us (1 in a row) — next attempt in ~360 min, not 1440"
```

The log line presents a 4x **increase** in request rate as a backoff. `config._interval`
enforces only a floor (`MIN_INTERVAL_SECONDS = 60`); there is no upper bound, so this is
a config the loader accepts silently. This is a direct inversion of the module's own
politeness constraint (*"a retailer that walled us got asked again five minutes later …
precisely the behaviour the project's own politeness constraint calls a hard limit"*).

`current_interval`'s zero-refusal early return has a comment naming exactly this
divergence — *"They stop agreeing the moment a standing interval exceeds
`MAX_BACKOFF_SECONDS`"* — and closes it only for `refusals == 0`. The non-zero branch is
where `record` actually schedules, and it is not closed.

**This also answers the `pacer-state.json` direction question.** `Pacer.save`'s docstring
claims a truncated read is safe because *"a reading judged against a narrower window than
the real one over-reports staleness rather than under-reporting it."* That holds for every
interval at or below the cap (empty state ⇒ `st.interval` ≤ the backed-off figure). Above
the cap it inverts: empty state yields 86400, the real document yields 21600, so the
truncated read judges against the **wider** window and **under-reports** staleness — the
direction REQ-21 does not prefer.

**Fix:** clamp the standing interval into the backoff domain, or refuse the config. The
smaller change keeps one expression:

```python
    def current_interval(self, retailer: str) -> float:
        st = self._for(retailer)
        if not st.refusals:
            return st.interval
        # `max(st.interval, ...)`: a backoff may only ever WIDEN the wait. A
        # standing interval above the cap would otherwise make a refusal ask
        # more often, which is the politeness constraint inverted.
        return max(st.interval, min(st.interval * BACKOFF_FACTOR ** st.refusals, MAX_BACKOFF_SECONDS))
```

Add a mutation for it: with the `max()` removed, nothing in the suite goes red today.

### WR-02: A per-retailer override below `interval_seconds` publishes a cadence the loop cannot keep

**File:** `boty/config.py:241-265` (`_retailer_intervals`), `boty/cli.py:684-687`
(`watch_loop`'s sleep), `boty/pacing.py:319-346`

**Issue:** `_retailer_intervals` holds overrides to `MIN_INTERVAL_SECONDS` only. Its own
docstring states the intent — *"A per-retailer override is for asking LESS often"* — and
nothing enforces it. `watch_loop` sleeps `cfg.interval_seconds * uniform(0.85, 1.15)` per
cycle, so no retailer can be polled more often than roughly the global interval, whatever
its override says.

Measured on this tree:

```
config accepted: interval_seconds=3600, retailer_intervals={'gamestop': 900}
published cadence for gamestop: 900
real gap between polls: >= ~3060 s
```

The phase's stated invariant is that the displayed `current_interval_seconds` and the
interval actually used to schedule cannot drift. Here they differ by 3.4x on a config the
loader accepts, and the drift is in the dangerous direction for the rendering: every
GameStop row on the dashboard and in `boty check` paints `warn`/stale permanently while
the monitor is reading that watch as often as it possibly can.

(A milder version of the same effect exists on the shipped config: `Pacer.due`'s
tolerance is `self.default_interval * 0.5` regardless of the override, so a
900-second-override retailer is actually asked roughly every 750 s while 900 is published.
That direction under-reports staleness by up to half the default interval. Worth a
comment, not a fix.)

**Fix:** hold the override to the global interval as well as the floor, in
`_retailer_intervals`:

```python
        if seconds < MIN_INTERVAL_SECONDS:
            raise ValueError(...)
        # And never BELOW the global cadence: `watch_loop` sleeps
        # `interval_seconds` per cycle, so a shorter override cannot be kept —
        # it would only publish a threshold the schedule can never satisfy, and
        # paint every row of that retailer stale while the monitor behaves.
```

`_interval` runs before this in `Config.load`, so the global value is available to
compare against.

### WR-03: `boty check` renders a negative age; the dashboard clamps it and `status.py`'s own rule forbids it

**File:** `boty/cli.py:201` (`_age_tag`), `boty/cli.py:141-145` (`_age`)

**Issue:** `age = None if r.read_at is None else now - r.read_at` with no lower clamp,
and `_age` formats a negative float without objecting.

Measured:

```
_age_tag(Result(read_at=1000.0), now=990.0, interval=300.0)  ->  '[age -10s]'
_age(-10.0)  ->  '-10s'
```

Three places in this tree say this must not happen. `served/boty/index.html:219` clamps
for exactly this reason and states the limit: *"A viewer's clock behind the host's yields
a negative age, and a negative duration in a served surface is the defect `status.py`
already records for `duration_seconds`."* `status.py:164-167` records that defect.
`models.py:428` names the producing case by name: *"a jump backwards leaves a stamp in the
future for a reader to discard."* `_age_tag` does not discard it; it prints it, and the
two surfaces the phase went to trouble to keep identical now disagree on this input.

No test covers it: `tests/test_monitor.py:541`'s `in-the-future` parametrisation guards
`State.load`, not the renderer.

**Fix:**

```python
    # Clamped at 0 for `index.html:219`'s stated reason, and stated here for the
    # same one: a negative duration on a surface a human reads is `status.py`'s
    # `duration_seconds` defect, and a stamp in the future is the case
    # `models.py:428` already names. The clamp cannot make a stale reading look
    # fresh — it only moves values already below zero.
    age = None if r.read_at is None else max(0.0, now - r.read_at)
```

### WR-04: `current_interval` mutates pacer state, contradicting the phase's own load-only rule

**File:** `boty/pacing.py:242-247` (`_for`), `boty/pacing.py:319-346`,
`boty/cli.py:231-236` (`_current_intervals`), `boty/cli.py:823-829`

**Issue:** the phase's scope note is that `boty check` reads pacer state **load-only —
reading the cadence must not mutate it**. `current_interval` calls `_for`, which
*inserts* a `_RetailerState` into `self._state` for any retailer not already present.
`_current_intervals` calls it once per configured retailer, so a `boty check` run
materialises an in-memory entry for every retailer in the config, including ones the
document says nothing about.

**Consequence today: none, and I say so rather than inflating it.** `Pacer.save` filters
`if st.refusals`, the check-path pacer never calls `save`, and `test_both_surfaces_
publish_one_cadence_from_one_document` proves the bytes are unchanged. The defect is that
the *only* thing keeping a read accessor from writing this document is a filter two
methods away and a caller that happens not to save. `Pacer.save`'s own docstring already
concedes it may be promoted to temp-and-replace later; the day the `if st.refusals` filter
is relaxed for any reason, `boty check` starts writing rows for retailers it never asked
about.

**Fix:** make the accessor genuinely read-only.

```python
    def current_interval(self, retailer: str) -> float:
        # Read-only: `.get` rather than `_for`, because a caller ASKING what the
        # cadence is must not create the record that answers. `boty check`'s
        # pacer is load-only and this is the method it calls thirteen times.
        st = self._state.get(retailer)
        if st is None:
            return self.overrides.get(retailer, self.default_interval)
        ...
```

### WR-05: two writers share one temp filename, so the "atomic" comment no longer holds

**File:** `boty/status.py:385-391`, `boty/cli.py:506-515`, `boty/cli.py:852-860`

**Issue:** `write` does `tmp = path.with_suffix(".tmp"); tmp.write_text(...);
tmp.replace(path)` and comments the rename `# atomic, so the page never reads a
half-written file`. The rename is atomic. The *temp file* is a fixed sibling name shared
by every caller of this function, and this phase made two concurrent callers a documented
workflow: `pacing.py:530-534` states plainly that *"`cli.main`'s `check` branch now loads
this document too, on a surface routinely run while the daemon is writing."* The same
`boty check` invocation also writes `cfg.status_path`.

Interleaving: the daemon truncates and begins writing `status.tmp`; a concurrent
`boty check` truncates the same file and writes its own payload; the daemon renames.
Whichever process renames last publishes whatever bytes happen to be in that one file.
`JSON.parse` in `tick()` then throws and the dashboard shows `status unavailable` until
the next write. Transient, self-healing, and not what the comment promises.

`boty check` writing `status.json` predates this phase; the *documented concurrency* does
not, and `pacing.py` explicitly re-argued the second-reader case for its own document
without extending the reasoning here.

**Fix:** give each write a unique temp name in the same directory (same filesystem, so
`replace` stays atomic):

```python
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(path)  # atomic, and the temp name is per-process so a
                           # concurrent `boty check` cannot truncate it mid-write
```

Wrap in `try/finally` with `tmp.unlink(missing_ok=True)` so a failed write leaves no
orphan.

### WR-06: `boty check` consumes a restock transition and sends nothing

**File:** `boty/cli.py:795` (`run_once(cfg.watches, checker, state)`),
`boty/monitor.py:608-628`, `boty/cli.py:861-862`

**Issue:** `run_once` calls `state.transitioned_to_stock(r)` for every result and then
`state.save()` — committing the transition to `state.json` — before returning. `boty
check` calls it, prints `N alertable transition(s)`, and sends nothing. So a `boty check`
run that happens to catch a restock writes "already seen, in stock" to disk and no alert
is delivered by anybody.

The running daemon holds its own in-memory `State`, so it still fires on its own next
cycle and its next `save()` overwrites the file — the loss is not immediate. It becomes
real if the daemon restarts (or is not running) between the check and the daemon's own
detection, which under `Restart=` semantics is not a rare state. `cli.py:517-522` already
records the principle: *"a send that does not arrive is not a retry — it is a drop
nothing will ever mention again."*

This predates the phase. It is in scope because the phase re-argued precisely this class
of concurrent-`boty check` hazard for `pacer-state.json` (`pacing.py:526-547`) and did not
carry the reasoning to `state.json`, whose second writer is the more expensive one.

**Fix:** the cheapest honest option is to give `run_once` a `commit: bool = True` and have
`boty check` pass `commit=False`, so the check reads and reports without mutating the
daemon's ledger. Record the residual either way: a check that does not commit cannot
report `alertable transition(s)` relative to the daemon's own memory, only relative to
the file as it stood.

### WR-07: `check_bestbuy_api` narrows a JSON body it never proved is an object, and does not coerce the price

**File:** `boty/retailers.py:944-1010`

**Issue:** `except ValueError` catches `json.JSONDecodeError` from `page.json`
(`fetch.py:151-157` is a bare `json.loads`). A body that is valid JSON but not an object —
`[]`, `"error"`, `null` — parses fine and then reaches `data.get("products")`, which
raises `AttributeError`. That escapes `check_bestbuy_api` entirely: in `boty check` it is
an uncaught traceback; in `boty watch` it is counted toward `FAILURES_BEFORE_GIVING_UP`
with no diagnosis naming Best Buy.

Separately, `price=p.get("salePrice")` is passed through with no coercion. A string there
would raise `TypeError` in `Result.alertable`'s `self.price <= self.watch.max_price` and
`ValueError` in `_report`'s `f"${r.price:>8.2f}"` — which is precisely the failure
`config._price`'s docstring documents and fixes for `max_price` (*"In `boty check` that
kills the command; in `boty watch` the loop's handler catches it, so the service stays up
while every cycle aborts"*).

**Not measured.** I have no observation of Best Buy returning a non-object body or a
string `salePrice`; the shape claim is inferred from the code, not from the API. Reported
as a suspected defect at the boundary, not a confirmed one.

**Fix:**

```python
    if not isinstance(data, dict):
        return Result(
            watch, Availability.UNKNOWN,
            detail="api returned a body that is not an object",
            url=product_url, rung=Rung.API, read_at=read_at,
        )
    products = data.get("products") or []
    ...
    raw_price = p.get("salePrice")
    price = float(raw_price) if isinstance(raw_price, (int, float)) and not isinstance(raw_price, bool) else None
```

`float(...)` guarded by `isinstance` rather than `try/float(str)`, on `config._price`'s
own bool-is-an-int precedent.

### WR-08: `_remembered_availability`'s justifying comment is now false, and it is the comment a future reader will trust

**File:** `boty/monitor.py:146-151`

**Issue:** the docstring justifies skipping enum validation with a claim about consumers:

> *"The only comparison ever made against this string is `!= Availability.IN_STOCK.value`,
> so a value outside the enum already behaves as 'not in stock' — the safe direction.
> Rejecting it would add a branch that changes no outcome, which is a gate that cannot
> bite."*

07-04 added a second consumer in the same phase: `status.write` publishes this string as
`"availability"`, and `served/boty/index.html` renders it into an attribute (CR-01). The
premise — one consumer, one comparison — stopped being true four plans later in the same
phase, and the conclusion rests entirely on it.

In a codebase whose house style is that the comment *is* the argument (this file rewrites
withdrawn paragraphs rather than deleting them), a stale premise left standing is how the
next reviewer re-derives the same exemption.

**Fix:** rewrite the paragraph in this file's own reversal style, naming the second
consumer and saying which guard now carries the weight:

```
    THE REMEMBERED AVAILABILITY IS NOT VALIDATED AGAINST THE `Availability` ENUM.
    THE ARGUMENT THAT USED TO CARRY THAT — "the only comparison ever made against
    this string is `!= Availability.IN_STOCK.value`" — WAS OVERTAKEN BY 07-04,
    which publishes this string as `status.json`'s `availability` and renders it
    on the dashboard. It is still not validated here, because the fail-safe
    direction for a memory is KEEP IT; what carries the safety at the sink is
    `esc()` in served/boty/index.html, asserted by tests/test_dashboard.py's
    UNTRUSTED list, which names this field.
```

## Info

### IN-01: `state.json` accumulates entries for watches that no longer exist

**File:** `boty/monitor.py:254-286` (`load`), `boty/monitor.py:326-334` (`save`)

**Issue:** `load` restores every key in the document and `save` rebuilds the document from
`seen`, so a key whose watch was renamed or deleted from `config/products.yaml` is loaded
and rewritten every cycle, forever, carrying a stamp that never ages out. Nothing renders
it (`_remembered_rows` iterates the *configured* watches), so it is inert — but the file
grows monotonically with config churn and holds increasingly old stamps for keys nobody
can explain.

**Fix:** prune on save against the configured key set, or record the growth as accepted in
`save`'s docstring the way the orphan-`read_at` residual already is.

### IN-02: the strict age boundary renders as `[age 5m > 5m]`

**File:** `boty/cli.py:141-145`, `tests/test_status.py:1026-1041`

**Issue:** `_age` floors to whole units, so a reading one second past a 300-second cadence
prints two identical numbers either side of a `>`. The suite asserts this exact string, so
it is deliberate — but `_age_tag`'s docstring sells the two-number form as *"show the two
operands and let the reader see the comparison"*, and two equal operands show nothing.

**Fix:** none required; if it is ever revisited, one decimal in the stale branch
(`5.0m > 5m`) would restore the intent without touching the fresh-row format.

### IN-03: the dashboard trusts the shape of `status.json`

**File:** `served/boty/index.html:239-277`

**Issue:** `d.updated`, `d.retailers`, `d.watches` and `w.price.toFixed(2)` are used with
no shape guard, inside `tick()` but outside its `try`. A payload missing any of them (a
pre-07 file during a deploy, a truncated write per WR-05, a non-numeric price per WR-07)
throws mid-render, the `list` keeps whatever it last held, and nothing on the page says
so — a silently frozen dashboard, which is the failure class this project exists to
prevent one level up.

**Fix:** widen the `try` around the render and fall back to the `'status unavailable'`
message the fetch path already uses, so a malformed payload is *visible* rather than
frozen.

---

_Reviewed: 2026-08-17T13:02:46Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
