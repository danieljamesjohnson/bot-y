# Phase 8: Stop Knocking - Pattern Map

**Mapped:** 2026-08-28
**Files analyzed:** 4 (2 certain, 2 conditional)
**Analogs found:** 4 / 4 — every file this phase touches already exists, so every pattern is an
in-file precedent rather than a cousin. This is a *modify* phase, not a *create* phase.

## File Classification

| File | New/Modified | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|---|
| `boty/pacing.py` | modified | service (scheduler + persistence) | event-driven state machine + file-I/O | itself — the existing backoff (`record`/`current_interval`) and the existing `load`/`save` | exact (self) |
| `tests/test_pacing.py` | modified | test | simulation over an injected clock | itself — `_CADENCE_AFTER_N_REFUSALS` + the `_pacer(path)` restart idiom | exact (self) |
| `scripts/mutation_check.py` | modified | config/registry | batch | `Mutation(ident="M41", ...)` and the four existing `target="boty/pacing.py"` entries (M11, M12, M16, M33, M38) | exact |
| `boty/monitor.py` / `boty/status.py` / `boty/cli.py` | probably UNCHANGED | consumer | request-response | `monitor.run_once`'s pacer block; `cli._current_intervals` | see finding F4 |

---

## Findings (measured, not assumed)

**F1 — the test module is `tests/test_pacing.py`, 1055 lines, 50 test functions, 75 collected**
(`.venv/bin/python -m pytest tests/test_pacing.py --collect-only -q` → `75 tests collected`; the
gap is two `@pytest.mark.parametrize` pairs and the 20-case `_HOSTILE` table). It is the only module
importing `boty.pacing` directly. `tests/test_cli_watch.py` touches the pacer through `watch_loop`.

**F2 — a consecutive-refusal counter ALREADY EXISTS and the phase must reuse it, not add one.**
`_RetailerState.refusals` (`boty/pacing.py:185`) is incremented on every refusal and *reset to 0* on
any non-refusal in `record`. It is already persisted, already aged, and already clamped at
`MAX_PERSISTED_REFUSALS = 64`. So criterion 1's "bounded number of consecutive refusals" is a
threshold *on an existing counter*. What does **not** exist is any notion of a cool-off, a probe, or
a "we are currently in a long wait" flag.

**Consequence for the plan:** the cheapest correct shape is likely a threshold constant
(e.g. `REFUSALS_BEFORE_COOLOFF`) plus a new branch inside `current_interval`, because `record`
already schedules `due_at = now + self.current_interval(retailer)` — the days-scale wait then reaches
the schedule *and* `status.json` through the one expression, with no second site. Anything that
sets `due_at` directly would split the published cadence from the fetch schedule, which
`current_interval`'s comment (lines 309-331) exists to forbid.

**F3 — `MAX_PERSISTED_REFUSALS = 64` is a live constraint on the threshold.** A cool-off threshold
of ~30 sits under the clamp, fine. But `test_the_clamp_never_restores_a_shallower_wait_than_the_cap`
(line 884) asserts `300.0 * 2**64 >= MAX_BACKOFF_SECONDS` — if the cap becomes days-scale that
assertion still holds comfortably, but re-check it rather than assume.

**F4 — W1 (`Pacer.due`'s tolerance) is ADJACENT, in the literal sense: it is the method criterion 2's
single-probe behaviour is asserted through.** `due` returns
`now + self.default_interval * 0.5 >= self._for(retailer).due_at` (line 271). A cool-off measured in
days is far outside the 150 s tolerance, so W1 cannot make a cool-off leak. But `due` *is* in the
code path — a simulated-cycles test asserting "requested exactly once" calls `due` every cycle. **Do
not fix W1 here.** Just do not write the cool-off in a way that depends on the tolerance being
correct.

**F5 — `due_at` is deliberately NOT persisted, and this collides with criterion 5.** Module docstring
lines 62-75: a restart resets the synthetic clock to 0.0, so `due_at` has no referent and a restart
*always tries once immediately at full rate*. That is the current, argued behaviour. A cool-off that
must "survive a restart" therefore cannot survive as a `due_at`; it has to survive as `refusals`
(already persisted, already aged by `refused_at`) — which is exactly what criterion 5's "the existing
rule rather than a second one" is pointing at. **The plan should state explicitly whether a restart
during a cool-off costs one immediate probe**, because on today's code it does, and that is an
argued property rather than a bug. If the phase changes it, that is a docstring reversal in the
house style (state the withdrawn paragraph, then the two measured facts that overruled it).

---

## Pattern Assignments

### `boty/pacing.py` (service; event-driven + file-I/O)

**Analog: itself.** Five excerpts, one per thing the phase must do.

#### 1. The existing backoff — where the count lives, the fixed ceiling, and how `current_interval` composes them

The ceiling constant (`boty/pacing.py:91-94`):

```python
#: Never wait longer than this between attempts, however many refusals. Six
#: hours is long enough to outlast a rate-limit window and short enough that a
#: retailer coming back is noticed the same day.
MAX_BACKOFF_SECONDS = 6 * 60 * 60
```

The counter (`boty/pacing.py:182-207`, trimmed of its comment blocks):

```python
@dataclass
class _RetailerState:
    interval: float
    refusals: int = 0
    due_at: float = 0.0        # CALLER's clock. Never persisted.
    refused_at: float = 0.0    # WALL clock, set when `refusals` was last incremented.
```

`record` — increment, stamp, compute the wait **through the accessor**, schedule
(`boty/pacing.py:273-307`):

```python
    def record(self, retailer: str, *, refused: bool, now: float) -> None:
        st = self._for(retailer)
        if refused:
            st.refusals += 1
            st.refused_at = time.time()
            wait = self.current_interval(retailer)
            log.warning(
                "%s refused us (%d in a row) — next attempt in ~%.0f min, not %.0f",
                retailer, st.refusals, wait / 60, st.interval / 60,
            )
        else:
            if st.refusals:
                log.info("%s is answering again after %d refusal(s)", retailer, st.refusals)
            st.refusals = 0
            st.refused_at = 0.0
            wait = st.interval
        st.due_at = now + wait
```

`current_interval` — the single expression behind both the published number and the fetch schedule.
Note its three branches; a cool-off branch goes **here** (`boty/pacing.py:332-422`, comments elided):

```python
    def current_interval(self, retailer: str) -> float:
        st = self._state.get(retailer)          # `.get` AND NOT `_for` — a read must not create
        if st is None:
            return self._standing_interval(retailer)
        if not st.refusals:
            return st.interval
        return max(
            st.interval,
            min(
                st.interval * BACKOFF_FACTOR ** st.refusals,
                MAX_BACKOFF_SECONDS,
            ),
        )
```

Two invariants the phase must not break, both already gated:
- **`current_interval` must never write.** `test_asking_what_the_cadence_is_does_not_create_the_record_that_answers` (line 409) asserts `p._state == {}` after three reads.
- **A backoff may only ever widen the wait** — the outer `max`. `test_a_refusal_never_shortens_the_wait_however_long_the_standing_interval` (line 185) and M38 gate it.

The prose surface (`boty/pacing.py:424-445`) will need a cool-off arm — note it too reads through the accessor:

```python
    def skipped_reason(self, retailer: str, now: float) -> str:
        st = self._for(retailer)
        mins = max(0.0, st.due_at - now) / 60
        if st.refusals:
            return f"backing off after {st.refusals} refusal(s) — next attempt in ~{mins:.0f} min"
        return f"paced at {self.current_interval(retailer) / 60:.0f} min — next attempt in ~{mins:.0f} min"
```

#### 2. Persistence, and THE EXISTING STALENESS RULE (criterion 5)

**The rule is the two-sided window on `refused_at`, inside `Pacer.load` (`boty/pacing.py:542-543`),
bounded by `STATE_MAX_AGE_SECONDS`, which is itself DERIVED from `MAX_BACKOFF_SECONDS`
(`boty/pacing.py:151`):**

```python
STATE_MAX_AGE_SECONDS = MAX_BACKOFF_SECONDS
```

```python
                # BOTH bounds. Past the cap the record has outlived its
                # reasoning; a stamp in the FUTURE is a clock that jumped
                # backwards, and with only an upper bound it would hold the
                # state for as long as the skew lasted.
                if not 0.0 <= now - float(refused_at) <= STATE_MAX_AGE_SECONDS:
                    continue
```

**Function name: `Pacer.load`.** The identical window is applied a second time in the same function
to the paging memory (`boty/pacing.py:576`), so "the existing rule" is already applied twice and a
cool-off is its third application — not a new rule.

> **Load-bearing consequence for criterion 5, and it is a real design question the plan must answer.**
> `STATE_MAX_AGE_SECONDS` is currently 6 hours *because it is derived from the ceiling this phase is
> replacing*. If the cool-off makes the effective ceiling days-scale, then either (a) the derivation
> carries the new number along — a record survives as long as the longest wait, which is the
> derivation's own stated argument — or (b) a days-long cool-off is discarded after 6 hours on every
> restart, i.e. it does not survive, i.e. criterion 5 fails. **(a) is almost certainly right and it
> is still a change to a persisted window, so it wants the dated-note treatment, not a silent edit.**
> `test_the_age_out_is_derived_from_the_backoff_cap` (line 907) asserts the identity and will hold
> either way; `test_state_older_than_the_backoff_cap_is_discarded` (line 719) is written against
> `STATE_MAX_AGE_SECONDS` symbolically and will also hold.

The full restore loop, for the shape any new field must match (`boty/pacing.py:524-550`):

```python
        retailers = doc.get("retailers")
        if isinstance(retailers, dict):
            for name, entry in retailers.items():
                if not isinstance(name, str) or not isinstance(entry, dict):
                    continue
                refusals = entry.get("refusals")
                # `bool` is an `int` subclass, so `"refusals": true` would
                # otherwise restore a backoff of 1.
                if not isinstance(refusals, int) or isinstance(refusals, bool) or refusals <= 0:
                    continue
                refused_at = entry.get("refused_at")
                if not isinstance(refused_at, (int, float)) or isinstance(refused_at, bool):
                    continue
                if not 0.0 <= now - float(refused_at) <= STATE_MAX_AGE_SECONDS:
                    continue
                st = self._for(name)
                st.refusals = min(refusals, MAX_PERSISTED_REFUSALS)
                st.refused_at = float(refused_at)
```

The write, and its self-cleaning filter (`boty/pacing.py:650-675`):

```python
        if self.state_path is None:
            return
        try:
            now = time.time()
            self._warned_since = {name: self._warned_since.get(name, now) for name in warned}
            doc = {
                "version": STATE_VERSION,
                "retailers": {
                    name: {"refusals": st.refusals, "refused_at": st.refused_at}
                    for name, st in self._state.items()
                    if st.refusals
                },
                "warned": self._warned_since,
            }
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(doc, indent=2, sort_keys=True))
        except Exception:
            log.exception(...)
```

**`STATE_VERSION = 2`.** Its comment (lines 96-140) states the bump rule explicitly: a version bump
is owed when the document carries *a count whose units are a policy decision* and the policy moves.
If the cool-off adds a field or re-points `refusals`' meaning, **read that comment before deciding**;
the precedent bump (v1→v2) was paid for by exactly this kind of change and its price is stated in
the comment as "one repeated notification and one shallow backoff". If the phase adds a field that
old readers ignore harmlessly and new readers treat as absent, no bump is needed — say which, and why.

#### 3. Retailer identity through the pacing layer (criterion: none, but it constrains every signature)

**A retailer is a plain `str`, everywhere, with no wrapper type.**

| Site | Type |
|---|---|
| `Pacer._state` | `dict[str, _RetailerState]` (`pacing.py:220`) |
| `Pacer.overrides` | `dict[str, float]` (`pacing.py:219`) |
| `Pacer._warned_since` | `dict[str, float]` (`pacing.py:232`) |
| `due` / `record` / `current_interval` / `skipped_reason` | first positional param `retailer: str` |
| `pacer-state.json` | `{"retailers": {"<retailer>": {...}}, "warned": {"<retailer>": <float>}}` — retailer name is the JSON object key |
| source of the value | `Watch.retailer`, coerced to `str` by 05-REVIEW's CR-01 |

`load` re-validates it anyway (`if not isinstance(name, str): continue`) because the file is hostile
input. Any new persisted structure must do the same.

---

### `tests/test_pacing.py` (test; simulation over an injected clock)

**Analog: itself.** There is no fixture, no `freezegun`, and no monkeypatched clock for the
schedule. **Time is a plain float parameter passed in by the test.** `Pacer`'s own docstring says so
(`pacing.py:213-215`): *"`now` is passed in rather than read, so tests can drive a day of cycles
without sleeping through one."*

**The simulated-cycles idiom** (criteria 2 and 3 must reuse this) —
`test_an_overridden_retailer_is_asked_less_often`, line 275:

```python
def test_an_overridden_retailer_is_asked_less_often() -> None:
    p = Pacer(default_interval=300, overrides={"amazon": 1800})
    now = 0.0
    checked = 0
    for _ in range(24):  # two hours of 5-minute cycles
        if p.due("amazon", now):
            checked += 1
            p.record("amazon", refused=False, now=now)
        now += 300
    assert 4 <= checked <= 5, (
        f"amazon checked {checked} times in 2h at a 30-minute cadence; expected ~4"
    )
```

That `if p.due(...): count += 1; p.record(...)` loop **is** the 30-day request-count simulation
(criterion 3) at a different bound — 30 days of 300 s cycles is `range(8640)`. And it is the
single-probe assertion (criterion 2) with the count checked over the window around expiry.

**Criterion 1's literal-seconds discipline already has a precedent, and the plan should extend that
table rather than invent a style** (`tests/test_pacing.py:379-382`, with its argument at 364-378):

```python
_CADENCE_AFTER_N_REFUSALS = [
    (300.0, [300.0, 600.0, 1200.0, 2400.0, 4800.0, 9600.0, 19200.0, 21600.0, 21600.0]),
    (1800.0, [1800.0, 3600.0, 7200.0, 14400.0, 21600.0, 21600.0, 21600.0, 21600.0, 21600.0]),
]
```

> "LITERALS, AND THAT IS THE POINT OF THE LIST. Computing these through `current_interval` — or
> through `BACKOFF_FACTOR` and `MAX_BACKOFF_SECONDS` — would make every assertion below a
> re-derivation of the code it is checking, which is a test that cannot fail."

That paragraph *is* criterion 1's rule, already written in this repo's own words. **Note both rows
currently run to 8 refusals and flatten at 21600. A cool-off at ~30 refusals is off the end of both
rows, so the table must be extended (or a sibling table added) rather than reused as-is — and the
extension must be hand-written literals.**

**The restart idiom** (criterion 5) — a *second, brand-new* `Pacer` over the same path, never
`load()` on the instance that wrote it. The section banner at line 556 says why:

```python
def _pacer(path: Path | None = None, interval: float = 300) -> Pacer:
    return Pacer(default_interval=interval, state_path=path)
```

```python
def test_a_refusal_count_survives_into_a_brand_new_pacer(tmp_path: Path) -> None:
    path = tmp_path / "pacer-state.json"
    first = _pacer(path)
    for _ in range(5):
        first.record("amazon", refused=True, now=0.0)
    first.save(set())

    second = _pacer(path)
    second.load()

    assert second._for("amazon").refusals == 5, (...)
```

**And the sibling that makes it load-bearing** — `test_the_restored_count_is_load_bearing_on_the_next_wait`
(line 634) proves the restored value reaches the *arithmetic*, not just a field. The cool-off needs
both halves, for the same stated reason: *"A `load` that wrote the count somewhere `record` never
reads would pass the assertion above and change nothing about how often we ask."*

**Staleness-test idiom** (criterion 5's discard half) — `_document(refusals, age, warned_age)` at
line 702 builds a well-formed doc stamped `age` seconds ago, and the tests write it straight to
`tmp_path` and assert the count came back 0 (line 719) or 5 (line 838).

**Criterion 4 (recovery clears the cool-off) has an exact precedent to copy** —
`test_a_retailer_that_answers_is_back_on_its_standing_interval_at_once`, line 463, which is
deliberately asserted *at the cap* rather than one refusal in:

```python
    p = Pacer(default_interval=300, overrides={"amazon": 1800})
    for _ in range(7):
        p.record("amazon", refused=True, now=0.0)
    assert p.current_interval("amazon") == MAX_BACKOFF_SECONDS

    p.record("amazon", refused=False, now=0.0)

    assert p.current_interval("amazon") == 1800.0
```

**The hostile-document table must gain rows for any new persisted field** — `_HOSTILE` (line 925) is
a 20-row parametrize, and its test asserts *both* that `load` survives and that `record` afterwards
survives, because "a table that only drove `load` would pass while the crash sat one method along."

---

### `scripts/mutation_check.py` (config/registry; batch)

**Next free ident, read from the file: `M42`.** Confirmed by `grep -n 'ident='` — the registry runs
M1–M20, M25–M41, and `MUTATIONS` closes at line 1448. That matches CLAUDE.md.

**The gap markers: there are seven `INTENTIONAL GAP` occurrences** (`grep -c "INTENTIONAL GAP"` → 7),
at lines 672, 757, 847, 941, 1051, 1325 and 1405. Their form is a comment immediately above the next
`Mutation(...)`, e.g. line 757:

```python
    # M21-M24 REMAIN THE INTENTIONAL GAP and are still not filled.
```

and the original at line 672 states the reason: `apply_mutation` cannot add a file, so the defect
M21–M24 would have covered is outside the harness by construction. **M42's comment block should
restate the gap the same way — an eighth marker that reaffirms the rule, exactly as M41 did.**

**The dataclass (line 174):**

```python
@dataclass(frozen=True)
class Mutation:
    ident: str
    target: str
    search: str
    replace: str
    breaks: str
```

**Two representative recent entries, verbatim.** M40 (line 1392):

```python
    Mutation(
        ident="M40",
        target="served/boty/index.html",
        search="    renderStatus(d);",
        replace="    try { renderStatus(d); } catch { return; }",
        breaks="a status document the page cannot render goes back to being invisible. ...",
    ),
```

M41 (line 1441) — a deletion mutation, which is the shape a cool-off gate will most likely take:

```python
    Mutation(
        ident="M41",
        target=".github/workflows/release.yml",
        search="    if: vars.PUBLISH_TO_PYPI == 'true'\n",
        replace="",
        breaks="a git tag becomes a PyPI upload again, with no person in between. ...",
    ),
```

**The closest in-file analogs for an M42 on `boty/pacing.py` are M11, M12, M16, M33 and M38.** Two
worth copying wholesale:

```python
    Mutation(
        ident="M12",
        target="boty/pacing.py",
        search="                if not 0.0 <= now - float(refused_at) <= STATE_MAX_AGE_SECONDS:",
        replace="                if False:",
        breaks="stale state is applied regardless of its stamp — a file written before a machine was off for a week pins a retailer at the cap on startup, which is the exact objection the withdrawn docstring paragraph raised",
    ),
```

```python
    Mutation(
        ident="M11",
        target="boty/pacing.py",
        search="                st.refusals = min(refusals, MAX_PERSISTED_REFUSALS)",
        replace="                st.refusals = 0",
        breaks="the restored refusal count never reaches the schedule — every restart climbs the backoff again from 2x against a retailer that has already walled us, and asks once at full rate on the way",
    ),
```

**Conventions extracted from the recent entries, all of which M42 must satisfy:**
1. `search` is a **whole indented source line** (leading whitespace included, sometimes a trailing `\n`) — an exact substring of the target file. Not a fragment of a docstring, comment or log message; the comment above M11 says so and M2 is the recorded lesson.
2. `replace` is either the inverted/neutered expression (`if False:`, `not in`, `= 0`) or the empty string.
3. `breaks` is a long prose paragraph naming the **observable behaviour** that regresses and who pays for it — never "the test fails", never a message string.
4. A prose comment block **above** the `Mutation(...)` carries: what it rebuilds, why it earned an ident (M41: "since not every one-line gate does"), and an **`IF IT EVER SURVIVES:`** paragraph naming the two most likely ways the gate could be weakened. M39, M40 and M41 all carry that last section; M42 should.
5. Anchor on behaviour: for this phase that means the search line must be one whose removal changes *when a request is made*, not one that changes a log string. The days-scale branch inside `current_interval`, or the threshold comparison, are the candidates. **A mutation on `MAX_BACKOFF_SECONDS`'s value would be caught by the literal-seconds table and is therefore a weaker choice than one on the branch.**

---

### `boty/monitor.py`, `boty/status.py`, `boty/cli.py` (consumers; request-response)

**Prediction: no edit needed.** Quoted so the plan can confirm rather than assume.

`monitor.run_once` (`boty/monitor.py:642-656`) drives the whole pacer contract through four calls and
knows nothing about backoff depth:

```python
    if pacer is not None:
        due = [w for w in watches if pacer.due(w.retailer, now)]
        skipped = {w.retailer for w in watches} - {w.retailer for w in due}
        for retailer in sorted(skipped):
            log.info("%-9s skipped — %s", retailer, pacer.skipped_reason(retailer, now))
        watches = due

    results = [checker(w) for w in watches]

    if pacer is not None:
        by_retailer: dict[str, list[Result]] = {}
        for r in results:
            by_retailer.setdefault(r.watch.retailer, []).append(r)
        for retailer, group in by_retailer.items():
            pacer.record(retailer, refused=any(x.refused for x in group), now=now)
```

`cli._current_intervals` (`boty/cli.py:225-247`) is a `dict` comprehension over
`pacer.current_interval(retailer)`, and `status.write` publishes it as `current_interval_seconds`
(`boty/status.py:183,200`). **So a days-scale number flows to the dashboard automatically** — which
is the payoff of putting the cool-off inside `current_interval`, and the thing that breaks if it is
put anywhere else.

**One thing to check rather than assume:** `served/boty/index.html` renders
`current_interval_seconds`. A number that jumps from 21600 to ~10^5–10^6 may format badly (a "paced
at 43200 min" style string). `skipped_reason` returns `~{mins:.0f} min` unconditionally. That is a
presentation question the plan should decide deliberately — and any edit to `index.html` re-enters
the two dashboard gates named in `CLAUDE.md` (no HTML comments in the `<script>` block; `esc()` on
every UNTRUSTED field; `node --check`).

---

## Shared Patterns

### The reversal convention (applies to every docstring and comment this phase edits)
**Source:** `boty/pacing.py:29-75` and the `STATE_VERSION` comment at 105-139.
A superseded paragraph is **quoted in full, dated, and then overruled by numbered measured facts** —
never deleted. This phase replaces a rule the module argues for at length ("it is capped because a
monitor that has backed off to once a day has quietly stopped being a monitor"), so **the
`MAX_BACKOFF_SECONDS` comment at lines 91-94 and the module docstring's second section are both
going to need this treatment.** The house form:

```
THE SENTENCE THAT USED TO CLOSE THAT PARAGRAPH WAS WITHDRAWN ON <date>. It read, in full:

    "<the withdrawn text>"

<what overruled it, as measured facts>

<what survives, and why this is a rewrite rather than a deletion>
```

`CLAUDE.md`'s evidence standard states the same rule for docs: *"Superseded measurements are
recorded beside, never edited away"* (`docs/retailer-evidence.md` § 6).

### Derive, never re-choose a number
**Source:** `boty/pacing.py:142-151` (`STATE_MAX_AGE_SECONDS = MAX_BACKOFF_SECONDS`), asserted by
`test_the_age_out_is_derived_from_the_backoff_cap`.
**Apply to:** the cool-off duration and the staleness window. If the cool-off length is a new
constant, the staleness window should be derived *from the longest wait the module can produce*, not
re-chosen — otherwise the two drift, which is F5's hazard.

### A read accessor must not write
**Source:** `boty/pacing.py:339-356` (`.get` not `_for`), gated by `test_asking_what_the_cadence_is_does_not_create_the_record_that_answers`.
**Apply to:** any new accessor (`in_cooloff`, `cooloff_remaining`, whatever) — `boty check` builds a
load-only `Pacer` and calls these once per configured retailer while the daemon owns the file.

### Best-effort persistence degrades, never raises
**Source:** `boty/pacing.py:670-675` — blanket `except Exception` + `log.exception`, because
`watch_loop` calls `save` from a `finally` and a raise there discards a pending `return 1`.
**Apply to:** any new write path.

### Watch every gate go red first
**Source:** `CLAUDE.md` § the evidence standard; every phase record in `.planning/`.
**Apply to:** all six criteria. Criterion 3 additionally requires the *current* rule's 30-day number
be recorded — which means running the simulation against the **unmodified** `pacing.py` and writing
the number down before the fix, not reconstructing it after.

---

## No Analog Found

None. Every file has an in-repo, in-file precedent. The only genuinely new *concept* is the
single-probe-on-expiry state (criterion 2) — there is no existing "we are waiting for one specific
probe" state anywhere in `boty/`. Its nearest structural cousin is `_warned_since` in this same
class: a per-retailer wall-clock stamp that exists **only to be written down** and is read by a later
process to decide whether an episode is still live (`boty/pacing.py:222-232`). If the cool-off needs
a stamp distinct from `refused_at`, copy that field's shape and — importantly — its rule that the
stamp is **the first time, not the last**, because `save` runs every cycle and re-stamping makes the
age-out unable to ever fire.

## Metadata

**Analog search scope:** `boty/`, `tests/`, `scripts/` (full read of `boty/pacing.py` 675 lines and
`tests/test_pacing.py` 1055 lines; targeted reads of `scripts/mutation_check.py` at 120-190 and
1370-1500; grep-only over `boty/monitor.py`, `boty/status.py`, `boty/cli.py`).
**Files scanned:** 6 read/grepped, 24 test modules listed.
**Pattern extraction date:** 2026-08-28
**Read-only:** no source file was modified; no `boty` command was run; `state.json`,
`pacer-state.json` and `served/boty/status.json` were not read or written. The only command executed
against Python was `pytest --collect-only`.
