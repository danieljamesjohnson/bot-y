# Phase 9: Out of Lockstep — Decisions

**Phase:** 09-out-of-lockstep · **Written:** 2026-09-01 · **Wave:** 1 (`09-01`) · **Requirement:** REQ-23

These are the decisions wave 1 took so that waves 2, 3, 4 and 5 do not take them mid-flight.
Everything below is settled in writing **before any production code moves** — `09-01` changes none.
A later wave that disagrees should reverse a decision here in the dated form this repository uses
(`docs/retailer-evidence.md`'s convention: quote the withdrawn text in full, then the measured facts
that overruled it, then what survives), rather than quietly deciding otherwise.

---

## The before-number

**Under the current rule, all SIX configured retailers are requested inside a single 60-second
window at least once over a simulated day.**

That is criterion 3's `before` half and nothing else. There is no comparison here and no claim of a
reduction — the `after` number and the word *smaller* are `09-02`'s.

**Why it is its own wave.** The current rule dispatches every due retailer inside one 300-second
pass. `09-02` replaces both the pass cadence and the schedule under it, and once that lands there is
no way to re-measure this number except by reverting the change — a synthetic revert, measured
against code that is no longer the code, which is not a measurement.

### How it was measured

| | |
|---|---|
| Command | `.venv/bin/python -m pytest tests/test_pacing.py -q` |
| Test | `test_the_max_retailers_in_any_sixty_seconds_over_a_day_is_a_stated_number` |
| Fleet | `amazon` 1800 s, `gamestop` 900 s, `bestbuy` / `nintendo` / `target` / `walmart` on the 300 s global default — the six `config/products.yaml` configures, asserted against it rather than hand-copied |
| Denominator | 288 cycles x 300 s = 86 400 s = one day, **asserted after the loop** rather than assumed |
| Total requests counted | 1296 = 48 (amazon) + 96 (gamestop) + 4 x 288 (the default group) |
| Window | a **sliding** 60 s window over the recorded event times, never fixed bins |
| `git rev-parse --short HEAD` at measurement | `87871b4` |
| `git log -1 --format=%h -- boty/pacing.py` | `a58e7ac` |
| `git log -1 --format=%h -- boty/cli.py` | `9ea42fe` |
| `git status --porcelain boty/` before the run | **empty** |

The HEAD and the last-modified revisions differ and that is not a discrepancy:
`git diff a58e7ac 87871b4 -- boty/pacing.py` is **empty**, so the file at the measured HEAD is
byte-identical to its last-modified revision. The measurement was taken against unmodified
production code.

The rule measured, in two lines: `Pacer.record` ends `st.due_at = now + wait` — re-anchoring every
retailer that fires at one tick to the *same* next due time — and `Pacer.due`'s tolerance is
`self.default_interval * 0.5`. Those two together are the lockstep.

### The transcript the literal was transcribed from

The assertion was written with a deliberate placeholder (`== -1`), run, and the number read out of
the failure message. **It was not computed by reasoning and then written down.**

```
$ .venv/bin/python -m pytest tests/test_pacing.py -q
>       assert max_in_any_60s == -1, (
E       AssertionError: the current rule put 6 of the six configured retailers (amazon, bestbuy, gamestop, nintendo, target, walmart) inside a single 60-second window at least once over a simulated day; the recorded before-number for criterion 3 is the literal in this assertion
E       assert 6 == -1

1 failed, 97 passed in 0.20s
```

With `6` transcribed in: `98 passed in 0.19s`.

### The window model, and the direction of its residual

**A pass asks its due retailers back to back.** `monitor.run_once` filters to the due set and then
evaluates `results = [checker(w) for w in watches]` with no sleep between them, so every request one
pass makes is modelled as falling inside one 60-second window whatever their order inside it.

That is a modelling claim and it carries its measurement: **the last published whole-pass figure is
`duration_seconds: 20.43` for 13 watches across all six retailers**, read from
`served/boty/status.json` on **2026-08-31** by the phase-8 code review and **quoted here rather than
re-read** — nothing in this phase reads or writes that file.

**The residual points the safe way.** One reading is a bound, not a guarantee. If a pass ever
exceeded 60 s the model would **over**-count, because some of that pass's requests would in truth
fall into the next window. So **6 is an upper bound on the before-number**, which is the safe
direction for a number this phase must come in under: it cannot flatter the change.

### Two things the number is not

- **It is a count of RETAILERS, not of requests.** `run_once` dispatches one `Result` per *watch*
  and `record`s once per *retailer*; criterion 3 asks for "the maximum number of retailers
  requested". The fleet carries 13 watches, so a window holding six retailers holds more than six
  HTTP requests. A later reader comparing this against a request count would be comparing two
  different things.
- **It assumes zero restarts, and restarts cannot make it smaller.** `due_at` is never persisted, so
  every process starts with all six retailers due at once — which is the t=0 burst this simulation
  counts. A restart mid-day adds another such burst; it removes none.

### Rule 1's stated exception, and the three reds that replace it

This repository's standing rule is that every gate is watched red before it is trusted. **The
literal above is the exception, and the exception is a finding rather than a skipped formality.**

A watched-red gate works by pointing a new assertion at code that is currently wrong; the failure
count is evidence that the assertion has a subject. **This literal's subject is the code as it
stands.** The lockstep is not a defect being fixed here — it is the thing being measured. Writing a
deliberately wrong literal and watching `assert ==` reject it would prove that `assert ==` works and
nothing else.

Three assertions that **do** have subjects were watched red on 2026-09-01. Each was perturbed, the
red observed, the perturbation reverted, and `diff` confirmed the file back to the intended edit.

**RED 1 — the denominator.** Loop bound reduced to `_ONE_DAY_OF_CYCLES - 1`:

```
>       assert now == float(_ONE_DAY_OF_SECONDS), (
E       AssertionError: the simulated clock finished at 86100.0 s, not the 86400 s that are one day — so the maximum above is a maximum over some other window. A run that exited early presents a smaller maximum as a shorter day, which is a reduction achieved by not asking rather than by spreading
E       assert 86100.0 == 86400.0
1 failed, 97 passed in 0.20s
```

**Failure count: 1 failed, 97 passed. The assertion that fired was the denominator, not the
literal.** That distinction is the finding, and it is the whole reason the denominator assertion
exists: **the literal still read 6 over the shortened day and passed.** A window that quietly shrank
would have been invisible to the literal alone — exactly the reduction-by-not-counting this plan's
prohibition names. This is the same result `08-01` recorded for its own denominator, on a different
number, which makes it a repeated measurement rather than a one-off.

**RED 2 — the fleet.** `_FLEET_INTERVALS["gamestop"]` perturbed from 900 to 600:

```
>       assert cfg.retailer_intervals == {
E       AssertionError: config/products.yaml overrides {'amazon': 1800, 'gamestop': 900}, but this table's non-default cadences are {'amazon': 1800, 'gamestop': 600} against a global interval_seconds of 300
E       assert {'amazon': 18...amestop': 900} == {'amazon': 18...amestop': 600}
E         Differing items:
E         {'gamestop': 900} != {'gamestop': 600}
1 failed, 97 passed in 0.20s
```

**Failure count: 1 failed, 97 passed. The fleet assertion fired — and again the literal did not.**
At a 600 s gamestop cadence the maximum is still 6, because 1800 is a multiple of 600 and the
coincidence survives. So the literal is blind to a fleet change too, which is the second
independent reason the fleet assertion is not decoration.

**RED 3 — the tallies.** One recorded event deleted, leaving the per-retailer counts intact:

```
>       assert len(events) == sum(per_retailer.values()), (
E       AssertionError: 1295 recorded events against 1296 counted requests — a request was made and not counted, or counted and not made
E       assert 1295 == 1296
E        +  and   1296 = sum(dict_values([48, 288, 96, 288, 288, 288]))
1 failed, 97 passed in 0.20s
```

**Failure count: 1 failed, 97 passed.**

**A fourth guard, not red-watchable but worth naming:** each retailer's observed count is also
checked against the cadence arithmetic its configured interval implies
(`86400 // interval` → amazon 48, gamestop 96, the default group 288 each). That expectation is
derived from `config/products.yaml` rather than from the loop, so a cycle the loop skipped shows up
as a shortfall against a number the loop had no hand in producing.

---

## Collision 1 — the tick must shrink, and it was forced rather than chosen

**Resolved: the phase changes `cli.watch_loop`'s tick as well as `Pacer`'s schedule.** Recorded as a
proof so a later reader meeting a ~6x wake rate understands what forced it.

`config/products.yaml` puts **four** retailers on the 300 s default. `cli.watch_loop` sleeps
`cfg.interval_seconds` per cycle and `run_once` asks every due retailer inside that one pass. So:

1. Four retailers need a request inside every 300 s span.
2. The loop makes requests only at a tick, and a 300 s tick gives **exactly one tick per 300 s span**.
3. Therefore all four must be requested at that one tick, **whatever phase they are given**.

**Criterion 1 is unsatisfiable while the tick equals the cadence, and no offset can rescue it.** The
before-number above is the same fact measured: 6, at t=0 and at every t=1800k.

Two alternatives were considered and are rejected in writing:

- **Lengthening the standing intervals** so fewer retailers coincide meets criteria 1 and 3 by
  **halving coverage**, and criterion 4 forbids exactly that (*"per-retailer cadence still holds"*).
  It is the reduction-by-not-asking move this repository has caught itself making before.
- **Spacing the requests inside a pass** (a sleep between retailers) is a **wall-clock** mechanism,
  which criterion 1 rules out in its own words (*"asserted on the schedule, never on a wall clock"*),
  and it would spend the `boty check` budget criterion 4 protects.

**`09-02` lands the tick.** Its value is not decided here — see § *What is NOT decided here*.

---

## Collision 2 — the module docstring's concession (b) is withdrawn, with its price named

`boty/pacing.py`'s module docstring, § *THE STALE-FILE OBJECTION IS ANSWERED, NOT DROPPED*, leg (b).
**Quoted in full before it is withdrawn:**

> (b) `due_at` IS STILL NOT PERSISTED, which keeps the withdrawn paragraph's own
>     concession intact. **A restart still tries once, immediately, at full rate,
>     so the condition is re-tested at once.** What is inherited is only the DEPTH
>     the penalty resumes at IF that one request is refused again, plus whether
>     a human has already been told. The withdrawn paragraph was right about the
>     request and wrong about the memory.

**The word withdrawn is *immediately*.** A birth phase means a retailer whose phase is 250 s is
first asked 250 s after a restart, not at once.

**What overrules it:** the elimination argument in collision 1. The alternative — phase only from
the **second** attempt, keeping the immediate probe — was considered and is **not available**. It
puts a six-retailer burst at t=0 of every process, criterion 3's simulation counts a day from a cold
start, and excluding that burst from the count would be a reduction achieved by not counting. It
would also leave criterion 1 unmet at exactly the moment the fleet is most visible as one crawler.

**The price, stated rather than left to be inferred:** *each retailer is re-tested once within one
standing interval, rather than immediately.* For the default group that is at most 300 s; for amazon
at most 1800 s. Nothing is re-tested less often — only later within the same interval.

**The compensating fact, recorded beside it:** under `Restart=` semantics a flapping service
previously re-probed **every** retailer at full rate on **every** restart, and now does not. A
restart loop was the one condition under which the old concession's "immediately" was most expensive
and least useful.

**What survives untouched, and it is the half the argument was really for:**

- **`due_at` is still never persisted.** Nothing in this phase stores it. The phase offset is
  *derived*, not read back from disk — see collision 7.
- **DEPTH is still what a restart inherits.** `refusals`, its wall-clock stamp and the paging memory
  are unchanged in shape and in meaning.
- The module docstring's closing paragraph — that a persisted `due_at` compared against a fresh 0.0
  *"either fires immediately or blocks a retailer for the entire age of the previous process"* — is
  strengthened by this phase, not weakened: it is now the argument for *deriving* the starting
  position rather than merely for leaving it at zero.

**`09-02` lands it**, as a dated note beside the concession, never over it. `_RetailerState`'s leg 2
carries the same number one level down (*"across a restart `due_at` resets to 0.0 by design, which is
decided and priced at one immediate request"*) and takes the same treatment; **leg 2's conclusion
survives whole** — the probe cannot repeat inside a process because `record` re-schedules
unconditionally on every outcome — so only the number beside it moved.

---

## Collision 3 — `record` must stop re-anchoring to `now`

**Resolved: the next attempt is derived from the previous `due_at`, stepped forward by whole waits
until it is in the future, never re-anchored to the cycle's clock.**

Today `record` ends `st.due_at = now + wait`. Two retailers that fire at the same tick are therefore
given the **same** next `due_at` and are in lockstep from then on — that is the mechanism, not a side
effect. Worse, `due`'s tolerance lets a retailer fire a tick early under the loop's jitter, and a
retailer that drifts into another's slot **stays there**: the merge is absorbing. A birth phase alone
would be eroded back to six-in-a-window.

A fixed-rate advance has the property the birth phase needs — firing early or late does not move the
phase, so the separation survives jitter indefinitely — and the property a naive `due_at += wait`
does not: **no catch-up storm** when a pass runs long.

**`09-02` must state at the site that this changes *where* the next attempt lands and NOT *how long*
the wait is.** `wait` still comes from `current_interval` and from nowhere else. A phase is a
**position**, never a duration; nothing outside `current_interval` may compute a wait, or Phase 7's
one-cadence property and Phase 8's widen-only rule are undone in the same edit.

**The advance is UNCONDITIONAL.** Gating it behind a non-empty roster is **refused**: it would keep
every old test green with no edits, and it would make every defaulted construction site — most of the
suite — exercise a code path the daemon never takes, since `cli.watch_loop` always passes a roster.
That buys a small diff by making the evidence describe something that does not ship.

**Collateral, named here so nobody "fixes" it:** `Pacer.skipped_reason` renders `due_at - now`, so its
output moves with the advance while its logic must not. **A repair that needs `skipped_reason`'s
logic to change is the signal that the mechanism moved a cadence rather than a position.**

**`09-02` lands it**, and repairs the ten tests it reddens itself — no plan after it owns
`tests/test_pacing.py`, so a deferred repair is not a bad habit here, it is impossible.

---

## Collision 4 — an empty tick must not publish a vacuously green verdict

**The defect, stated as arithmetic.** `boty/status.py:154` is:

```python
        "healthy": all(h.ok for h in health),
```

and **`all([]) is True`**. Today every 300 s cycle asks somebody, so an empty pass is only reachable
when every retailer is backed off simultaneously. **After this phase roughly half of all ticks ask
nobody**, so a pass that checked nothing publishing `healthy: true` becomes routine — *a green
dashboard over a question nobody asked*, which is this project's own defect one level up, rebuilt
inside the fix for a different one.

**Two measured facts that bound it** (measured 2026-09-01 unless noted):

- **The dashboard does not read `healthy` at all.** `grep -n healthy served/boty/index.html` returns
  nothing, exit 1.
- **`boty/status.py:154` is its only producer.** The blast radius is `tests/test_status.py:217` (the
  key-set assertion, which is unaffected — the key stays) and `tests/test_status.py:249`
  (`assert payload["healthy"] is True`).

So this is **not** a live-surface defect today. It is a latent one that this phase would make routine,
and it is recorded now so it is paid rather than discovered.

**The shape to prefer, and it is already argued twelve lines above the defect** — `status.write`'s own
docstring on the per-retailer rows:

> the retailer is not healthy (nothing was verified) and not unhealthy (nothing failed) — it simply
> was not asked

The aggregate gets **that same third state**, not a new invention. The comment immediately above the
defect already says the flag is *"Only over retailers actually CHECKED"* — which is exactly why an
empty checked-set has no verdict to give.

**`09-04` lands it.** Not `09-03`: the outline assigns the empty-tick cost to the wave that prices
what a shorter tick costs.

---

## Collision 5 — the two failure counters are counts of cycles, and the cycle is about to shrink

`boty/cli.py:378` `FAILURES_BEFORE_WARNING = 3` and `boty/cli.py:383`
`FAILURES_BEFORE_GIVING_UP = 10` were chosen against a 300 s cycle: roughly **15 minutes to a
warning** and **50 minutes to giving up**. They are counts of *cycles*, and this phase shortens the
cycle. At a shorter tick both fire proportionally sooner in wall time.

**The warning one sends a notification.** An accidental multiple-fold increase in how fast this
monitor pages a human is the `notify-dan` bar failing in the direction this repository cares about
most — *"never hit the user unless it's something they can buy or actually do"*.

**`09-04` must either re-derive them as durations or accept the change IN WRITING.** Silently
inheriting the count is the one outcome not available. This document does not pick between the two:
the choice depends on the tick, and the tick is `09-02`'s to measure.

---

## Collision 6 — `boty/config.py`'s cycle sentence goes false; the validator does not move

`boty/config.py`, `_retailer_intervals`' docstring. **Quoted in full before it is reversed:**

> `cli.watch_loop` sleeps `interval_seconds * uniform(0.85, 1.15)` per CYCLE,
> not per retailer, so no watch can be polled more often than roughly the
> global interval whatever its override says.

**What overrules it:** collision 1. After this phase `cli.watch_loop` sleeps a **tick**, and
`interval_seconds` is no longer the loop's sleep.

**The rule survives and its reason changes.** `retailer_intervals[x] >= interval_seconds` stays,
because `interval_seconds` stops being the loop's sleep and becomes **the shortest standing
cadence** — which is still the floor a per-retailer override must not go under. An override below it
would still publish a cadence faster than any retailer is scheduled at, which is still REQ-21's
defect (a reading presented as something it is not).

**The validator itself is untouched**, and so is the `EQUAL IS ACCEPTED` boundary.

**One sentence in the same docstring gets a note too, because this phase moves its number.** It
reads: *"`Pacer.due`'s tolerance is `self.default_interval * 0.5` regardless of any override, so a
900-second-override retailer on a 300-second global is actually asked roughly every 750 s while 900
is published."* This phase re-anchors that tolerance from `default_interval` to the tick, which
**shrinks** the under-report rather than removing it. The direction is unchanged and the magnitude
falls; `09-02` states the new magnitude beside the old.

**`09-02` lands both notes**, in the dated-reversal form, beside and never over.

---

## Collision 7 — no persisted state, therefore no `STATE_VERSION` question — confronted, not stepped around

Phase 8 refused a `STATE_VERSION` bump with a three-legged argument written into `boty/pacing.py`,
whose decisive leg is quoted here rather than referenced:

> 3. THE BUMP'S OWN PRICE, QUOTED FROM ABOVE, IS DECISIVE HERE. "Treated as
>    absent" means every retailer's refusal count is discarded on the upgrade.
>    So on the day this phase ships, every retailer at or past the threshold
>    would lose its cool-off, be asked at full rate, and climb the backoff from
>    the bottom — this phase's own defect, delivered by this phase's own safety
>    mechanism, to exactly the retailers the phase exists to protect.

**This phase must not reopen that, and does not need to.** The rule Phase 8 left standing is explicit
about what still owes a bump: *"A future change that alters the document's SHAPE, or that RESCALES
what a stored count denotes rather than what this module does about it, still owes a bump."*

**This phase does neither, and the reason is structural rather than lucky: the phase offset is
DERIVED from the retailer's name and the configured roster, so it is stable across processes without
being stored.** That is the same argument `STATE_MAX_AGE_SECONDS` and `Result.degraded` make one
level up — derive rather than store, because two copies only have to disagree once. Storing the phase
would be a new key, which *would* owe a bump, which would discard every refusal count on the day this
ships. **Deriving it is what makes the question not arise.**

**A consequence worth naming in the same breath: `hash()` is not available for this.** CPython
randomises `str.__hash__` per process under `PYTHONHASHSEED`, so a phase derived from it would be a
different schedule in every process — which is not a schedule at all, and would silently reintroduce
the very "a number with no referent" failure the module docstring rejects persisted `due_at` for.

**`09-02` must state this at the definition site.** **`09-04` must CONFIRM by inspection of
`save`/`load` that the document's shape is unchanged, rather than predict it.** A prediction here
would be a claim about code a later wave writes.

---

## Collision 8 — criterion 4's budget can be bounded, and probably not measured

**Stated before any measurement is attempted, so a disappointing result cannot be mistaken for a
finding that arrived late: criterion 4's budget half is expected to land at MET IN PART.**

`boty check` makes **live retailer requests** and writes the live `served/boty/status.json`, which
the running daemon owns. **This phase makes no live request anywhere**, and `boty check` will **not**
be run to close the gap. Definition of Done item 2 is why this is not a compromise: REQ-23 is proved
by offline tests over the scheduler — *"the daemon is evidence, never the gate."*

**The two instruments that ARE available offline:**

- **(a) A structural fact, already gated.** `boty check`'s pacer is **load-only** and **is never
  passed to `run_once`** — `boty/cli.py` argues all four clauses of that at the site, clause 3 being
  *"IT IS NEVER PASSED TO `run_once`. `boty check` re-reads every watch by design"*. Therefore **no
  scheduling change this phase makes can reach that path.** `tests/test_cli_watch.py` already gates
  the `boty check` surface (see its `boty check` section around lines 653 and 1363).
- **(b) The last PUBLISHED `duration_seconds` from a real pass** — `20.43` s for 13 watches, read
  2026-08-31, **read and never written**, quoted here rather than re-read.

**`09-04` states the verdict as MET IN PART if that is what it is, and names which half is
unmeasured.** Rewording the criterion so it passes is the one unforgivable move.

*(Note on ownership: the outline's plan table assigns criterion 4's budget half and the final verdict
to `09-05`, while `09-01`'s own objective assigns criterion 5 to `09-04`. The two documents number
the waves differently in their tails. This document names `09-04` because that is what `09-01`'s
plan — the authority this wave executes under — says; whichever wave actually owns it inherits the
obligation, not the number.)*

---

## Test collision A — `test_a_retailer_at_the_default_cadence_is_due_every_cycle`

`tests/test_pacing.py`. **The assertion, quoted before it is withdrawn:**

```python
    for cycle in range(20):
        assert p.due("walmart", now), f"walmart not due at cycle {cycle} (t={now})"
        p.record("walmart", refused=False, now=now)
        now += 300 * 0.86  # a short-jitter cycle, the adversarial case
```

and its docstring calls the failure it guards *"the regression that would make this change quietly
halve coverage"*.

**After this phase the UNIT is wrong and the FEAR is still right.** A retailer at the default cadence
is due once per **cadence**, not once per **tick** — and being due every tick would now be the defect,
since a tick shorter than the cadence would mean asking several times per cadence.

**Rewrite, do not delete, and do not rename away from `git log -S`'s reach.** Quote the withdrawn
assertion, record what overruled it, and **keep the coverage half alive**: the retailer must still be
asked the **same number of times per day**. That is the assertion that carries the original fear
forward into the new unit, and it is `09-02`'s gate.

**`09-02` rewrites it.**

---

## Test collision B — `test_the_restored_pacer_starts_its_schedule_from_zero`

`tests/test_pacing.py`. **The assertions, quoted before they are withdrawn:** `second._for("amazon").due_at == 0.0`
and `second.due("amazon", 0.0)`, carrying the message *"a restart must still try once,
immediately"*.

**Both halves move**, and this is collision 2 wearing an assertion.

**What must survive verbatim is the sentence the test exists for:** *"a `due_at` came back from disk.
It was measured against a clock that no longer exists"*. Nothing in this phase persists `due_at`, so
that sentence is untouched and is in fact the reason the repair is available at all.

**Re-point the assertion at *the phase, and only the phase*:** a restored pacer's `due_at` is its
retailer's phase and nothing else — **a number this process computed, not one a previous process left
behind.** That is a strictly stronger claim than `== 0.0`, because `0.0` is also what a
maliciously-crafted or truncated document would produce.

**A THIRD superseded sentence, found while writing this document and recorded rather than left for
`09-02` to discover mid-flight.** The same test's *docstring* also carries the concession, in its own
words:

> Leaving it at 0.0 also KEEPS the withdrawn docstring's concession — a restart still tries once at
> full rate.

That sentence goes false with collision 2 and takes the same treatment. **The rest of that docstring
survives verbatim and gets stronger**, because "a persisted `due_at` is a number with no referent" is
precisely the argument for *deriving* the starting position rather than reading one back.

**`09-02` rewrites the test and both sentences.**

---

## Test collision C — `09-01`'s baseline test is consumed by `09-02`, and that is its second job

Exactly as `08-01`'s was. **`09-02`'s change turns this test red**, and that red is not a casualty —
it is **`09-02`'s watched-red evidence for criterion 3**. There is no other way to get one: the
literal has no subject today (see § *Rule 1's stated exception*), and it acquires one the moment the
scheduling rule moves.

**The form of the rewrite, fixed here so `09-02` does not have to choose it mid-flight:** the
before-number becomes a **dated record in the docstring** and the *same simulation*, unchanged in
every other respect, carries the after-number. The denominator, the fleet assertion, both tallies and
the sliding window all stay exactly put. **That is what makes the two numbers comparable rather than
two answers to two questions.**

**After that rewrite the before-number is a dated record rather than a re-runnable assertion, and
that is stated plainly rather than papered over.** Criterion 3 asks for both numbers *recorded*, not
both re-runnable. Freezing a hand-written reproduction of the old arithmetic to keep 6 re-runnable
was considered and is rejected on `08-02`'s precedent: it would be a second copy of a number, and the
copy would be of a **rule that no longer exists**, so nothing could ever check it again. A
re-runnable assertion over dead arithmetic looks like evidence and is not.

**`09-02` rewrites it**, and adds the `< 6` comparison that is the word *smaller* in criterion 3.

---

## The construction sites, and what defaulting them does NOT buy

A `Pacer` built with no roster and no tick keeps today's behaviour **in its tolerance and in its
birth phase** — the same defaulting argument `Result.rung`, `Result.extraction` and `Pacer.state_path`
already make in this tree. **It does NOT keep today's advance**, because `record`'s grid-anchored
advance is unconditional (collision 3).

**Measured 2026-09-01 by AST over every tracked `.py` file** (`ast.Call` with `func.id == "Pacer"`,
`.venv` excluded), **after this plan's own commits**:

| | |
|---|---|
| Construction sites, tree-wide | **32** |
| `tests/test_pacing.py` | 27 |
| `tests/test_cli_watch.py` | 3 |
| `boty/cli.py` | 2 |
| Naming no `state_path`, tree-wide | 25 |
| Naming no `state_path`, in `tests/test_pacing.py` | 25 of 27 |
| Distinct **keyword signatures** | 4 |
| Distinct **normalised call texts** (`ast.unparse`) | 10 |

**The count moved, and this plan is what moved it — recorded rather than quietly restated.** The
outline measured **31** tree-wide (26 in `tests/test_pacing.py`, 24 of them naming no path) and **9**
distinct call shapes, on 2026-09-01 **before** `09-01` ran. `09-01` adds exactly one site — the
day-long simulation's own `Pacer` — so 31 → **32**, 26 → **27**, 24-of-26 → **25-of-27**, and
9 → **10** distinct call texts. Nothing else changed. A wave that quotes 31 after this plan is
quoting a pre-image of the tree it is standing in.

**A measurement-method correction, stated because the two numbers look like a contradiction.** The
outline's *"9 distinct call shapes"* is a count of distinct **call text**, not of distinct **keyword
signatures**. By signature there are only **4** (`default_interval`; `+overrides`;
`+overrides+state_path`; `+state_path`). Both numbers are true of different questions; a reader who
takes 9/10 as a count of API shapes will over-estimate how many ways this class is constructed.
Neither figure is edited away.

### The consequence, stated in the direction it actually points

It is tempting to write that the defaults keep the phase-8 tests untouched and that their passing
therefore proves the schedule is safe. **That is backwards**, twice over:

1. **The advance is unconditional, so those tests do NOT come through untouched.** Ten of them redden
   and `09-02` repairs them. Predicting otherwise would have been a false claim.
2. **Even for the tests that do come through, a green defaulted site proves nothing about the
   schedule the daemon runs**, because `cli.watch_loop` **always** passes a roster and a tick. A
   regression sweep run only on defaulted sites **cannot fail for the reason it exists**.

**So `09-04`'s sweep must additionally assert under the SHIPPING construction** — roster and tick
present — or it is a sweep over a shape nobody runs.

### And a stale count in production code, recorded and deliberately not fixed here

`boty/pacing.py`'s `state_path` paragraph reads:

> There are nine in `tests/test_pacing.py` alone and not one names a path

That was **exactly true when written** — `46a0768`, 2026-08-10: eleven sites, two naming a path,
nine not. It is **not true now**: 25 of 27 in `tests/test_pacing.py` name no path.

**The argument the sentence serves is strengthened, not weakened** — the number of sites the default
protects went *up*. Only the count moved.

**Not fixed by `09-01`:** this plan's acceptance criteria assert its changed-file list by equality,
and a production edit would poison the scope fence the before-number depends on. **`09-02` puts a
dated note beside it**, since it is already editing that region.

---

## What is NOT decided here

Stated so the boundary is explicit and a later wave does not read this document as settling more than
it does.

- **The tick's value**, and `MIN_TICK_SECONDS`. Two bounds are recorded, not a number: a **floor**,
  since a tick cannot be outrun by one pass and the only offline instrument is the published
  `duration_seconds: 20.43` bound (one reading of a live pass, not a guarantee, and to be written that
  way); and a **ceiling**, since the tick must divide the shortest standing cadence often enough to
  give the four coinciding retailers distinct slots.
- **The phase derivation's exact form** — only that it is derived from the retailer name and the
  configured roster, never from a hostname, a store id, a MAC, a wall clock, a pid or `hash()`.
- **Criterion 1's stated separation in seconds.**
- **Whether the two failure counters are re-derived as durations or accepted as counts** (collision 5).
- **The choice between the two readings of the advance rule** (step in whole waits, versus step once
  and floor at the cycle clock). `09-02` names both, chooses one deliberately, and records the choice
  with its collateral.

**This document fixes the shape, not the numbers.** They are `09-02`'s to choose **by measurement
against the day-long simulation** and to defend at their definition sites, the way
`REFUSALS_BEFORE_COOLOFF` is defended at its.

---

## COVERAGE.md — written at planning time, and that is a departure

`.planning/phases/09-out-of-lockstep/COVERAGE.md` **already existed before `09-01` ran**. It was
written at planning time, and it carries one line:

> No external API integration: this phase edits boty/pacing.py's and boty/cli.py's scheduling
> arithmetic and makes no live retailer request.

**This departs from Phase 8**, where `08-01` created that file itself. **`09-01` asserts its content
instead of creating it**, and the departure is stated here rather than left as a discrepancy for a
reader comparing the two phases to trip over.

---

## A trap that bit this wave: a stale `.pyc` can keep a reverted perturbation live

**Found 2026-09-01 while running this plan's own red-watches. Recorded here because every remaining
wave in this phase red-watches `tests/test_pacing.py`, and the trap defeats the protocol silently.**

The red-watch protocol in this repository is: perturb the source, run, observe the red, revert,
confirm `diff` is back to the intended edit. **That protocol has a hole, and it is `diff`.**

RED 2's perturbation changed `_FLEET_INTERVALS["gamestop"]` from `900` to `600`. **Those two source
files are byte-identical in LENGTH**, and the revert (`cp`) landed within the same wall-clock second
as the perturbed run. CPython and pytest's assertion-rewriting cache both validate a cached `.pyc`
against the source's **mtime (one-second resolution) and size**. Both matched, so the cache was
considered valid and **the reverted source was never recompiled**. The interpreter kept executing the
perturbed bytecode.

**The observable symptoms, in the order they appeared and each one misleading:**

1. `diff` said the source was IDENTICAL. It was.
2. `git status --porcelain` was empty. It was.
3. `grep` showed `"gamestop": 900` in the working tree *and* in `HEAD`. It did.
4. `make verify-offline` nonetheless failed with `this table's non-default cadences are
   {'amazon': 1800, 'gamestop': 600}` — a value present in no file on disk.
5. Bisecting by test file reported **every** file as the trigger, which is the shape of a
   session-level cause being mistaken for a test interaction.

Measured directly: `tests/__pycache__/test_pacing.cpython-312-pytest-9.1.1.pyc` at
`08:13:36.389` against a source at `08:13:36.575` — 186 ms apart, the same second.

**The fix is one line and it belongs in the protocol, not in a test:**

```bash
find . -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + ; rm -rf .pytest_cache
```

**All three of this plan's red-watches were re-run from a cleared cache after this was found**, and
all three reproduced with the same assertion firing and the same count — `1 failed, 97 passed` each,
with `98 passed` restored. **The recorded counts in § *Rule 1's stated exception* are the re-run
ones**, not the originals; the originals agreed, but they were taken under a cache that had just been
shown to be untrustworthy and are therefore not what is cited.

**Waves 2-5 must clear the cache between a perturbation and its revert.** A same-length edit — one
digit for another, `True` for `Fals`, `<=` for `>=` — reverted quickly is exactly the shape this hole
swallows, and it is also exactly the shape of most red-watch perturbations. **The failure mode is the
worst available: the gate goes red for a reason that is not in any file, and the natural response is
to distrust the new test.**

*(This belongs in `CLAUDE.md` § *Traps that have actually bitten*. `09-01` cannot put it there:
this plan's acceptance criteria assert its changed-file list by equality, and editing `CLAUDE.md`
would poison the scope fence the before-number depends on. **Handed to a later wave in this phase**,
and recorded here so it is not lost if none of them takes it.)*

---

## What `09-01` does not claim

- **Criterion 5 is NOT discharged here.** No mutation was registered and none was observed CAUGHT;
  **M43 is still free**, and `grep -c "INTENTIONAL GAP" scripts/mutation_check.py` is still **8**.
  `make verify-offline` was run to prove the tree is still green with a new test in it — a regression
  check.
- **No comparison and no reduction.** One number is stated. The thing it will be compared against
  does not exist yet.
- **Criteria 1 and 2 (`09-02`/`09-03`), criterion 4 (`09-03`/`09-04`) and criterion 3's `after` half
  (`09-02`)** are untouched.
- **No production code moved.** No live retailer request was made, `boty check` was not run, and
  `state.json`, `pacer-state.json` and `served/boty/status.json` were neither read nor written.


---

## The `current_interval` digest IS reproducible — the recipe, recorded 2026-09-02

`09-03-SUMMARY.md` records that `Pacer.current_interval`'s SHA-256 is *"not reproducible — 09-02
recorded no extraction recipe; four plausible ones miss"*, and falls back on the stronger fact that
`git diff 653bc80..HEAD -- boty/` is empty. **That summary is left unedited: its complaint was fair
and its fallback was the right move.** But the conclusion is one step too strong, and the missing
piece was never the digest — it was the recipe, which no plan wrote down.

**The recipe, stated so the gate is checkable by anyone rather than only by whoever wrote it:**

```python
import hashlib, re
s = open('boty/pacing.py', encoding='utf-8').read()
m = re.search(r'\n    def current_interval\(.*?(?=\n    def )', s, re.S)
hashlib.sha256(m.group(0).encode()).hexdigest()
```

Span is **7994 bytes** — from the newline before `    def current_interval(` up to but excluding the
newline before the next `    def `, i.e. the decorator-free method block including its trailing blank
line, hashed as UTF-8 with no normalisation.

> **Correction recorded beside, 2026-09-02 (`10-01`), not edited away.** The span is **7994
> CHARACTERS and 8018 BYTES**. `len(m.group(0))` is 7994; `len(m.group(0).encode())` is 8018 — the
> block contains non-ASCII (em dashes, `é`), so the two differ by 24. The sentence above says
> *bytes* about the character count.
>
> **The digest is unaffected and the recipe is exactly right.** `.encode()` is applied before
> hashing in the code block above, so the hash was always taken over the 8018 bytes;
> `6da39ac5d77ecd98cae80651c3b4d539253e88a1704fb4b1e814e6bf93449108` re-verified again on
> 2026-09-02 from `10-01`'s working tree, unchanged.
>
> Recorded because the number is a *cross-check* — the one a future verifier reaches for when the
> digest does NOT match, to find out whether they extracted the wrong span. A reader who measured
> `len(...encode())` and got 8018 would have concluded the span had drifted and gone looking for a
> change to `boty/pacing.py` that never happened.

**Re-verified 2026-09-02 against the tree at the phase-9 close:
`6da39ac5d77ecd98cae80651c3b4d539253e88a1704fb4b1e814e6bf93449108`** — identical to the literal
09-02 recorded, and identical on every check made during waves 2, 3, 4 and 5. The gate was also
watched red independently before wave 2 ran: a one-character body edit moves the digest and the
check exits 1.

**Why this is worth a note rather than a shrug.** A digest with no stated extraction is a gate only
its author can run, and this repository's whole standard is that a claim is tied to a measurement
someone else can repeat. `09-03` was right to distrust it. The fix is to publish the recipe, not to
drop the gate — and not to leave the record saying "not reproducible" about something that is.
