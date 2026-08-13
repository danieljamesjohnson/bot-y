# Phase 7: A Reading Has an Age - Pattern Map

**Mapped:** 2026-08-13
**Files analysed:** 9 to modify, 0 new
**Analogs found:** 7 with a worked precedent / 9 — two criteria have **no analog** and are
called out as such rather than given a weak one.

Everything below is measured off the tree at `03520af`. Line numbers are from that tree.

---

## File Classification

| File to modify | Role | Data flow | Closest analog | Match quality |
|---|---|---|---|---|
| `boty/models.py` | model | transform | `Result.store` (the field, `models.py:346-382`) | **exact** — fifth pass down a groove cut four times |
| `boty/retailers.py` | service (adapters) | request-response | the `store=`/`shipping=` bulk edit across all 20 `Result(` sites | **exact** |
| `boty/status.py` | serializer | file-I/O | `"store" / "store_pinned"` keys, `status.py:119-143` | **exact** |
| `boty/cli.py` `_report` | view (CLI) | transform | `_store_tag`, `cli.py:89-119` + the tag list `cli.py:133-147` | **exact** |
| `served/boty/index.html` | view (web) | request-response | `storeTag()` + `.tag.store` / `.tag.store.warn`, lines 60-69, 100-122 | **exact** |
| `tests/test_dashboard.py` | test | transform | the REQ-14 section, lines 195-233, and `UNTRUSTED` lines 50-59 | **exact** |
| `scripts/mutation_check.py` | gate | batch | M27/M28 and M29/M30 pairs, lines 619-693 | **exact** |
| `boty/monitor.py` `State` (persistence, criterion 4) | store | file-I/O | **`pacing.Pacer.load`/`save`** (`pacing.py:300-456`) — *not* `State`, which has no precedent for fields | **role-match, see below** |
| `boty/pacing.py` (exposing the current interval, criterion 3) | service | transform | **no analog** — the value does not exist anywhere today | **none** |

---

## Pattern Assignments

### 1. `boty/models.py` — the stamp on `Result` (criterion 1)

**Analog:** `Result.store`, `boty/models.py:346-382`, itself the fourth application of
`Result.rung`'s rule at lines 309-317.

**The declaration convention** (`models.py:309-317`, verbatim):

```python
    #: Which rung produced this reading. Declared last, with a default, so
    #: every pre-existing construction site stays valid and keeps its meaning:
    #: they are all plain TLS fetches, and none of them names a rung.
    rung: Rung = Rung.TLS
    #: What was read out of the page. Declared last, after `rung`, with a
    #: default, for the same reason `rung` is: ...
    extraction: Extraction = Extraction.STRUCTURED
```

The current last field is `shipping: float | None = None` (`models.py:406`). **The stamp is
declared after it**, with a default, and its comment names `shipping` as the field it follows —
that is the literal chain each of the four predecessors extends.

**The three paragraphs every one of these fields carries**, and which this one must therefore
carry (from `store`, `models.py:352-381`):

- *WHAT THE DEFAULT MEANS* — `store`: "`None` is 'the page did not tell us which store
  answered'. It is never 'store 0'". Here: `None` is **UNKNOWN age**, never `time.time()` at
  construction. This is criterion 2's whole content and the `duration_seconds` argument in
  `status.py:53-57` states the same rule for a number: *"A missing measurement serialised as 0
  would read off the dashboard as the fastest check ever recorded."*
- *Deliberately NOT folded into `degraded`* (`models.py:360-363`) — the stamp is not a
  confidence discount either. `degraded` means "discount this"; an age is a different fact.
- *THE ASYMMETRY A READER WILL OTHERWISE TRY TO FIX* (`models.py:365-373`) — whether the stamp
  drives `Availability` or `alertable`. `store` drives `Availability` to UNKNOWN; `rung` and
  `extraction` deliberately do not touch `alertable`. **Which side a stale reading falls on is a
  decision this phase must state explicitly in that paragraph's shape**, not leave implied.
  Note the standing rule at `models.py:517-522`: UNKNOWN is never RESOLVED into a verdict.

**Derived-not-stored precedent, if "stale" becomes a property:** `Result.degraded`
(`models.py:446-468`) — *"Derived rather than stored so there is exactly one source of truth."*
But note: staleness needs the retailer's interval, which `Result` cannot see. See §9.

---

### 2. `boty/retailers.py` — every return path (criterion 1)

**Counted by hand on this tree, as instructed.** `grep -c "Result(" boty/retailers.py` = **21**;
one of those (line 268) is inside a comment. **20 real construction sites:**

| Function | Lines of each `Result(` | Count |
|---|---|---|
| `_verdict_from_html` | 282, 311, 334, 351, 374, 391, 404, 446 | **8** |
| `check_html` (`except Blocked` / `except FetchError`) | 469, 471 | 2 |
| `check_amazon` (`except Blocked` / `except FetchError`) | 517, 526 | 2 |
| `check_bestbuy_browser` (both `except` arms) | 642, 651 | 2 |
| `check_target_browser` (both `except` arms) | 751, 761 | 2 |
| `check_bestbuy_api` (no `_verdict_from_html` delegation) | 836, 845, 855, 865 | **4** |

Phase 5 measured 8 in `_verdict_from_html` and a bulk edit missed two; the shape is identical
here, **plus `check_bestbuy_api`'s four, which do not route through `_verdict_from_html` at
all** and are the sites most likely to be missed this time.

**The stated-not-inherited rule** (`retailers.py:463-471`, verbatim):

```python
    except Blocked as exc:
        # `store=None` and `shipping=None` stated, not inherited: a refusal
        # produced no page, so nothing said which store answered or what
        # shipping would cost. Written out so this arm declares its metadata
        # the way the browser adapters declare theirs, rather than depending on
        # a dataclass default staying what it is today.
        return Result(watch, Availability.UNKNOWN, detail=f"blocked: {exc}", url=watch.target, refused=True, store=None, shipping=None)
```

**A stamp inverts this rule and that is the phase's sharpest judgement call.** For `store` and
`shipping`, an error arm states `None` because nothing was read. For a *reading time*, the
refusal arms **did** happen at a wall-clock moment — but they are `Availability.UNKNOWN`, and
`monitor.State.transitioned_to_stock` (`monitor.py:114-115`) refuses to let UNKNOWN overwrite a
known state. So a refusal that stamped "now" would refresh the age of a reading it did not take
— **exactly the 2026-08-12 Walmart failure in the seed, rebuilt**. Whichever way this lands, it
must be stated at each arm rather than inherited from a default.

**The anchoring rule that binds any new guard** (`retailers.py:267-273`): comments sit *above*
their `if`, so each condition line is immediately followed by its `return Result(` and its
verdict, "so M9 and M10 ... can anchor on the condition and the verdict and on NOTHING ELSE."

---

### 3. `boty/status.py` — publishing it (criterion 1)

**Analog:** the two store keys, `status.py:119-143`.

`status.write` builds rows **field by field, not `asdict`** — `models.py:401-405` records that
adding a field to `Result` therefore publishes nothing. Add the key in the dict comprehension at
`status.py:90-146`.

**The `null`-not-zero rule, verbatim (`status.py:136-141`):**

```python
                # Serialised as `null`, NEVER as `0` and never as `""` — the
                # `duration_seconds` argument above applies word for word ...
                # An absent store published as `0` would read off the dashboard
                # as a real store.
```

An absent stamp published as `0` is epoch 1970 — which renders as maximally stale rather than as
UNKNOWN, and is the same class of lie one direction over. `null` is the pattern.

**The top-level `updated` is confirmed cycle-level:** `status.py:42`, `"updated": int(time.time())`,
computed once per `write` call, outside the `watches` comprehension. It is unrelated to any row,
and the seed is right that it is fresh when every row is stale. **Do not reuse it, and do not
rename it** — `index.html:133-142` reads it for the "monitor may not be running" banner.

**Threading a pacer-derived value into `status.write` has a worked precedent:** the `paced`
keyword (`status.py:27, 31-39`, built at `cli.py:299-306`). That is the existing shape for
"cadence facts the results themselves cannot carry" and is the analog for criterion 3's payload.

---

### 4. `boty/cli.py::_report` — the tag list (criteria 2 and 3)

**Analog:** `_store_tag`, `cli.py:89-119`, and its append at `cli.py:142-147`.

The tag list is a `(label, bool)` comprehension (`cli.py:133-141`); anything whose **text varies**
is a separate function appended afterwards, and `_store_tag`'s docstring says exactly why:

```python
    Separate from `_report`'s comprehension because that comprehension is
    `(label, bool)` pairs and a store is not a bool — the tag's TEXT depends on
    which of the two values is present, not merely on whether one is.
```

An age tag has varying text, so it follows `_store_tag`: a module-level `_age_tag(r, ...) -> str | None`,
enumerating its forms in the docstring the way `_store_tag:96-106` enumerates four, and
appended after the comprehension. `_store_tag`'s `[store ?, pinned X]` form — *"`?` rather than a
blank, because 'the page did not tell us' is a fact worth printing"* — is the direct precedent
for rendering an absent stamp.

**`SYMBOL` is untouched.** Stated at `cli.py:126-128` and again at `_store_tag:108`; it is indexed
unconditionally by `Availability`, which has exactly three members.

**Test analog:** `tests/test_status.py:351-395` — one test per `_store_tag` form via
`capsys`, closing with `test_the_store_tag_did_not_touch_the_availability_symbols`.

---

### 5. `served/boty/index.html` — the dashboard (criteria 2 and 3)

**Analog:** `storeTag`, lines 100-122, with its CSS at lines 60-69.

**The tag convention, exactly** (do not invent a new visual language):

- `.tag` (lines 44-48) is dim and low-contrast — *an ordinary label* (`control`).
- A second class with `color: var(--warn)` and `border-color: color-mix(in srgb, var(--warn) 45%, transparent)`
  is *a warning* (`.tag.degraded` 54, `.tag.dom` 59, `.tag.store.warn` 69).
- The two-weight pattern is `.tag.store` + `.tag.store.warn` (68-69) — one class, two weights,
  a label form and a warning form. **A fresh reading is a label; stale and UNKNOWN-age are warnings.**
- Every tag carries a `title="..."` sentence explaining what it means (116-121).
- Tags are emitted inside the single template literal at line 155, in order:
  `control`, `degraded`, `dom`, `storeTag(w)`.

**Escaping, verbatim (lines 93-98):**

```javascript
// So: escape once, at the sink, and apply it to every interpolated value rather
// than to the ones currently known to be attacker-reachable. Operator-controlled
// fields go through it too. A rule of the form "these three but not those two"
// does not survive the next edit to this template.
const esc = s => String(s ?? '').replace(/[&<>"']/g, c =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
```

A numeric stamp formatted through `fmtAge` (line 80) produces no attacker-controlled string, but
if any new key is interpolated **as a string** it goes in `UNTRUSTED` and through `esc()`.

**`fmtAge` already exists** (line 80) and is used for the cycle banner. Reuse it; do not add a
second age formatter, on `Result.degraded`'s one-source-of-truth argument.

**Test analog — the producer/consumer pair:** `tests/test_dashboard.py:200-233`. Two tests per
feature: one asserting the page *reads the key* `status.write` publishes
(`re.search(r"(?<![\w.])w\.store\b", page)`), one asserting the *visual weight exists*
(`re.search(r"\.tag\.store\.warn\s*\{", page)`). Module docstring, line 8: *"A contract asserted
at one end only is a comment."* If a new string key is added, it goes in `UNTRUSTED`
(lines 50-59) — note the recorded regex subtlety there: `w.store` and `w.store_pinned` both need
listing because `\b` after `store` does not match inside `store_pinned`.

---

### 6. `scripts/mutation_check.py` — the gates (criterion 5)

**CORRECTION TO CONTEXT.md.** It says 26 mutations at M1-M20 and M25-M28, and that new idents
start at M29. **Measured on this tree: M29 and M30 already exist** (lines 680-693, Phase 6's
paging-action pair). The registry is **28 mutations: M1-M20, M25-M30**. **New idents start at M31.**
M21-M24 remain the intentional gap, stated in the code itself at line 669.

**The pair convention** (M27/M28 at 619-642, M29/M30 at 643-693): a rule that can fail in two
opposite directions gets **two mutations sharing one `search` or one subject**, with a comment
block above them saying why one would leave the other half unguarded. Verbatim, lines 656-660:

```
    # ONE MUTATION WOULD LEAVE THE OTHER HALF UNGUARDED, and the halves fail in
    # opposite directions — one restores the noise that trained him to ignore
    # this channel, the other satisfies "stop the noise" by pushing nothing at
    # all, ...
```

This phase's natural pair: one mutation making an absent stamp read as *now* (criterion 2's
failure), one making a stale reading render as fresh (criterion 3's failure).

**The house rule on anchors, verbatim (lines 662-667):**

```
    # BOTH ARE ANCHORED ON BEHAVIOUR AND NEITHER TOUCHES PROSE — M2's lesson,
    # which this repository has now paid for twice. M29 is the comprehension that
    # decides; M30 is a conditional over a NAME, which is exactly why
    # `STORE_PIN_ACTION` is a module constant rather than a literal at the call
    # site.
```

Each entry also states **WHICH TEST IS EXPECTED TO CATCH IT** (lines 671-679) and pre-counts the
anchor's occurrences (lines 594-599) because `apply_mutation` replaces the **first** occurrence.

**Anchors that are literal-coupled (the drift hazard, as requested):**

| Ident | Anchor | Coupling |
|---|---|---|
| M25 | `version = "0.3.0"` in `pyproject.toml` | **version literal** — re-pointed 2026-08-13, comment at 605-609 |
| M26 | ``Publication happens from the `v0.3.0` tag`` in `README.md` | **version literal** — re-pointed 2026-08-13, line 615 |
| M2 | `detail=(` in `retailers.py` | re-anchored 2026-08-04 when prose moved (194-199) |
| M19 | `rung=Rung.TLS,` + disambiguating newline/`#` | **non-unique** anchor, guarded by `tests/test_support_matrix.py:1617+` |

Everything else is behavioural. **Any new anchor this phase adds must be a comprehension, a
conditional, a comparison or a named constant — never a message string and never a literal that
a version roll or a prose edit moves.** If a new anchor cannot be made unique, bind it with a
test in `tests/test_support_matrix.py` using `_mutation(ident)` (lines 1591-1614); note its
assertion message: *"Idents are reserved across concurrent plans, not renumbered."*

---

### 7. Persistence across a restart (criterion 4) — **two candidate homes, measured**

#### 7a. `state.json` via `Config.state_path` (`config.py:280, 325`)

**Current shape, measured on the live file just now:**

```json
{
  "amazon:Pokémon GO Plus +": "out_of_stock",
  "gamestop:CONTROL — PS5 console": "in_stock"
}
```

A flat `dict[str, str]`, `"retailer:name"` → bare availability string. The seed's
`sorted({f for v in state.values() if isinstance(v, dict) ...}) == []` still holds.

**Reader and writer** — `monitor.State`, `monitor.py:90-119`:

```python
    path: Path
    seen: dict[str, str]

    @classmethod
    def load(cls, path: Path) -> State:
        try:
            return cls(path, json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError):
            return cls(path, {})
```

**The migration hazard, stated plainly.** `load` does **no** `isinstance` validation beyond the
JSON parse, and `transitioned_to_stock` (line 118) does `self.seen[key] = result.availability.value`
— it *writes a bare string unconditionally*. So:

- An existing `state.json` loaded by a version expecting per-entry dicts gives
  `previous = "out_of_stock"` where a dict was expected — `previous != Availability.IN_STOCK.value`
  is `True` for a dict too, so it would **fail open into a spurious alert or a swallowed one**,
  depending on shape. There is no version field and no guard.
- `pacing.py:99-104` explicitly argues why `State` needs no version: *"its document is a flat map
  of strings whose meaning cannot drift."* **Adding fields falsifies that sentence**, so the
  comment must be updated in the same commit, and the version hedge it describes becomes the
  precedent for this file too (`STATE_VERSION`, `pacing.py:98-112`, including the recorded cost
  of a bump: *"A v1 file is treated as absent, which costs …"*).

#### 7b. `pacer-state.json` via `boty/pacing.py` — **the existing precedent for a persisted wall-clock stamp**

`_RetailerState.refused_at`, `pacing.py:159-175`, verbatim:

```python
    #: WALL clock (`time.time()`), set when `refusals` was last incremented.
    #: This field exists only to be written down.
    #:
    #: This class now holds two clocks and confusing them is the bug that made
    #: `due_at` unpersistable ...: `due_at` is a position on the caller's
    #: schedule; `refused_at` is a timestamp on the EVIDENCE. `time.monotonic()`
    #: is the wrong tool here ... — its epoch is process- and boot-local, so it
    #: means nothing in a file.
```

Written at exactly one place, `pacing.py:239-241`, at the moment the evidence was collected.
Validated on load with a **both-ended bound**, `pacing.py:335-350`:

```python
                refused_at = entry.get("refused_at")
                if not isinstance(refused_at, (int, float)) or isinstance(refused_at, bool):
                    continue
                # BOTH bounds. Past the cap the record has outlived its
                # reasoning; a stamp in the FUTURE is a clock that jumped
                # backwards ...
                if not 0.0 <= now - float(refused_at) <= STATE_MAX_AGE_SECONDS:
                    continue
```

Note `isinstance(x, bool)` exclusion (bool is an int subclass), the `continue`-not-guess
discipline, and `load`'s docstring naming `monitor.State.load`'s try/except shape as its own
analog (`pacing.py:302-313`).

**Does a reading stamp share `due_at`'s hazard? No — and this is the load-bearing answer.**
`due_at` is unpersistable because `cli.watch_loop` drives the pacer with a **synthetic clock**,
`scheduled_now = 0.0` restarting every process (`cli.py:432-438, 485`), threaded as `now=` through
`watch_cycle` → `run_once` → `pacer.due/record/skipped_reason`. **A reading stamp is on the
EVIDENCE, not on the schedule**, so it takes `time.time()` like `refused_at`, and the
`_warned_since` field (`pacing.py:188-200`) is a second worked instance of the same rule —
including its trap, verbatim at 196-199: *"stamping at write time would refresh the record
forever and the age-out would never fire once — a bound that cannot bind is worse than no bound."*
**That trap is the direct analog of stamping a `Result` on a refusal arm** (see §2).

**A residual worth carrying into the plan:** `Pacer.save` omits retailers at zero refusals
(`pacing.py:443-446`) so the file self-cleans; `State.save` (`monitor.py:104-106`) never prunes,
so `state.json` accumulates keys for deleted watches forever. A stamp landing there inherits that.

---

### 8. The time source — **no analog, and this is the testability decision**

Measured across `boty/`, `tests/`, `scripts/`:

| Call | Sites |
|---|---|
| `time.time()` (wall) | `status.py:42`, `pacing.py:241, 323, 434` — **and nowhere else in `boty/`** |
| `time.monotonic()` (durations only) | `cli.py:292, 311, 592, 594` |
| `datetime.now(timezone.utc)` | `fixtures.py:108, 166` only — fixture capture age, explicitly *not* live readings (seed, "Not to be confused with") |

**There is no injected clock, no `freezegun`, no `Clock` protocol, no `monkeypatch` of `time.time`
anywhere in the suite.** The only injected time is `now: float`, which is the **synthetic
schedule clock** (`monitor.run_once:308`, `cli.watch_cycle:272`, `Pacer.due/record/skipped_reason`)
— a trap, not a seam: it starts at 0.0 every process and is documented as such at
`pacing.py:62-75` and `cli.py:432-435`. **Using it for a reading stamp would reproduce exactly the
bug that made `due_at` unpersistable.**

**How the suite actually controls wall time today — the pattern to copy**
(`tests/test_pacing.py:501-505, 585-591`):

```python
    warned = {} if warned_age is None else {"amazon": time.time() - warned_age}
    ...
            "retailers": {"amazon": {"refusals": refusals, "refused_at": time.time() - age}},
```

Relative offsets from real `time.time()`, constructed in the test, exercised through `load`. It
works because `refused_at` is *read* from a document, never *taken* inside the code under test.

**So the seam question is real and this map does not paper over it:** whatever takes the stamp
must be reachable from a test without freezing the clock. The two options with precedent in this
repo are (a) an optional `now: float | None = None` parameter on the function that stamps,
defaulting to `time.time()` — the shape `Pacer` uses for its schedule clock, applied to the wall
clock; or (b) stamp at one call site only and test everything downstream through the persisted
document, which is how `refused_at` is tested today. **(b) has the stronger precedent here; (a)
has none in this codebase for a wall clock.** Recorded as a decision the planner must make
rather than one this map can settle.

---

### 9. Staleness from the retailer's own interval (criterion 3) — **no analog; structural, not cheap**

The context asks whether the current interval is readable from where rendering happens. Measured:

**The value does not exist as a stored field anywhere.** `_RetailerState.interval`
(`pacing.py:152`) is the **standing** interval from config, unchanged by backoff — `load` refuses
to restore it from disk (`pacing.py:344-347`: *"`interval` comes from config, never from the
file"*). The **current** interval under backoff is computed inline and immediately discarded,
`pacing.py:242-245`:

```python
            wait = min(
                st.interval * BACKOFF_FACTOR ** st.refusals,
                MAX_BACKOFF_SECONDS,
            )
```

The backoff lives in `due_at`, and `due_at` is a synthetic-clock number. So criterion 3 needs
that expression **extracted into one readable place** — a `Pacer.current_interval(retailer) -> float`
— which is precisely the "derive rather than store, so the two cannot drift" argument the module
already makes twice (`STATE_MAX_AGE_SECONDS`, `pacing.py:113-123`; `Result.degraded`,
`models.py:460-462`). Note `_for()` is private and `skipped_reason` is the only public method that
reads the interval, and it returns **prose** (`pacing.py:271-272`) — not a number a comparison can use.

**It survives a restart:** `refusals` is persisted and `interval` comes from config, so the
current interval is fully reconstructible after a restart. Criterion 3 and criterion 4 agree.

**Threading, per surface:**

| Surface | Has a `Pacer`? | What is needed |
|---|---|---|
| `status.write` | no — `cli.watch_cycle` holds it (`cli.py:419-422`) | thread a per-retailer value in, **exactly as `paced` is threaded** (`cli.py:299-306` → `status.py:27`) |
| `boty check` / `_report` | **no — `main`'s check path builds no `Pacer` at all** (`cli.py:584-596`, `run_once(cfg.watches, checker, state)` with no pacer) | either construct one, or derive from `cfg.interval_seconds` / `cfg.retailer_intervals` (`config.py:274, 279`) — a *standing* interval with no backoff depth, which is a **different number** from the daemon's |
| dashboard | reads `status.json` only, by design (`status.py:4-5`) | whatever `status.write` publishes |

**The honest hazard to record in the plan:** `boty check` and the daemon would answer "what is
this retailer's current interval" differently unless `boty check` loads `pacer-state.json`.
Publishing two different staleness verdicts for the same reading is this project's own defect one
level up, and it is the reason criterion 3 is structural rather than cheap.

---

## Shared Patterns

### The "declared last, with a default" chain
**Source:** `models.py:309-317` (`rung`), `:346-351` (`store`), `:386-390` (`shipping`),
`:203-208` (`Pacer.state_path`, which cites the same rule across modules).
**Apply to:** any new field on `Result`, `Watch` or `Pacer`.
Each comment names the field it follows and states that every pre-existing construction site
stays valid. `Watch.store_id`'s variant (`models.py:273-276`) records the extra wrinkle: `control`
was last, so inserting ahead of it would have changed the positional signature.

### Three-valued honesty applied to a number
**Source:** `status.py:53-57` (`duration_seconds`), `status.py:136-141` (`store` as `null`).
**Apply to:** the stamp in `status.json`, and to `state.json`.
> *"`None` means 'nobody timed this pass', which is not 'it took no time' … A missing measurement
> serialised as 0 would read off the dashboard as the fastest check ever recorded."*

### Both-ended time-bound validation on a persisted stamp
**Source:** `pacing.py:335-350` (counts) and `:367-382` (paging memory).
**Apply to:** loading any persisted reading stamp.
Includes the `isinstance(x, bool)` exclusion, the `continue`-rather-than-guess discipline, and
the future-stamp bound: *"a stamp in the FUTURE is a clock that jumped backwards."*

### A producer/consumer contract is asserted at both ends
**Source:** `tests/test_dashboard.py:1-21` module docstring; `test_status.py` for the producer.
**Apply to:** every new `status.json` key.
> *"A contract asserted at one end only is a comment."*

### Escape once, at the sink
**Source:** `index.html:93-98`, `tests/test_dashboard.py:150-176`.
**Apply to:** any new interpolated value on the dashboard, operator-controlled included.

### Recording a withdrawal beside the text, never over it
**Source:** `pacing.py:29-53` (the in-memory paragraph quoted in full, then overruled),
`models.py:335-342` (`refused`'s withdrawn claims), `monitor.py:16-37`.
**Apply to:** `models.py:401-405` (`shipping`'s "Deliberately NOT published in `status.json`" —
still true, but its argument *"adding a field here publishes nothing new"* is about to be used in
the opposite direction) and `pacing.py:99-104` (`State` "needs no version") if 7a is chosen.

---

## No Analog Found

| File / concern | Role | Data flow | Reason |
|---|---|---|---|
| `boty/pacing.py` — a readable current interval | service | transform | The value is computed inline in `record` and discarded (`pacing.py:242-245`). No accessor, no field, and `skipped_reason` returns prose. Criterion 3 must create it. |
| A wall-clock seam for tests | test infra | — | No injected clock, no `freezegun`, no `time.time` monkeypatch anywhere. The only injected `now` is the synthetic schedule clock, which is a documented trap. `tests/test_pacing.py`'s relative-offset construction is the nearest thing and it only works for values *read from a document*. |
| `boty check`'s access to pacing state | controller | request-response | `main`'s check path constructs no `Pacer` (`cli.py:584-596`). Nothing in the repo has ever needed pacing facts on that surface. |

---

## Metadata

**Search scope:** `boty/`, `tests/`, `scripts/`, `served/boty/`, `config/`, plus the live
`state.json` and `pacer-state.json`.
**Files read:** `boty/models.py`, `boty/status.py`, `boty/pacing.py`, `boty/monitor.py`,
`boty/cli.py` (targeted ranges), `boty/retailers.py` (targeted ranges), `served/boty/index.html`,
`tests/test_dashboard.py`, `scripts/mutation_check.py` (targeted ranges),
`tests/test_support_matrix.py` (targeted range).
**Corrections to CONTEXT.md made here:** mutation registry is **28** (M1-M20, M25-M30); new
idents start at **M31**, not M29.
**Pattern extraction date:** 2026-08-13
