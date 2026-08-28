# Phase 8: Stop Knocking — Decisions

**Phase:** 08-stop-knocking · **Written:** 2026-08-28 · **Wave:** 1 (`08-01`) · **Requirement:** REQ-22

These are the decisions wave 1 took so that waves 2, 3 and 4 do not take them mid-flight. Everything
below is settled in writing before any production code moves; a later wave that disagrees should
reverse a decision here in the dated form this repo uses, rather than quietly deciding otherwise.

---

## The baseline number

**Under the current rule, a retailer that never recovers is asked 125 times in 30 simulated days.**

That is criterion 3's `before` half and nothing else. There is no comparison here, no claim of a
reduction, and no threshold value — the `after` number and the word *strictly* are `08-02`'s.

**The restart assumption sits on the number, not under it.** The simulation models **zero restarts**
across the 30 days, and **each restart would cost exactly one extra request** on top of the 125.
`boty/pacing.py`'s module docstring, concession (b), is why: `due_at` is never persisted, so a
restart re-tests the condition at once at full rate. What a restart inherits is the DEPTH the
penalty resumes at, never the position on the schedule. Under a systemd unit with `Restart=`
semantics that is not a rare event, so a reader is told rather than left to infer it. The number is
therefore a floor on real-world requests, not a prediction of them.

**How it was measured.**

| | |
|---|---|
| Command | `.venv/bin/python -m pytest tests/test_pacing.py -q` |
| Test | `test_the_current_rule_asks_a_never_recovering_retailer_this_many_times_in_thirty_days` |
| Retailer | `walmart` — the retailer measured on 2026-08-20 sitting at 21 600 s on backoff, so the simulation has a real subject rather than a placeholder |
| Standing interval | 300 s, the config default, no override |
| Denominator | 8640 cycles x 300 s = 2 592 000 s = 30 days, asserted after the loop rather than assumed |
| `git rev-parse --short HEAD` at measurement | `85a8d9f` |
| `git log -1 --format=%h -- boty/pacing.py` | `e986d01` |
| Rule measured | `MAX_BACKOFF_SECONDS = 6 * 60 * 60`, applied indefinitely; no cool-off branch in `current_interval` |

The two revisions differ and that is not a discrepancy: `git diff 85a8d9f e986d01 -- boty/pacing.py`
is **empty**, so `boty/pacing.py` at the measured HEAD is byte-identical to its last-modified
revision. The measurement was taken against unmodified production code, and `git status --porcelain
boty/` printed nothing before the run.

**The transcript the literal was transcribed from.** The test was written with a deliberate
placeholder (`== -1`), run, and the count read out of the failure message — so the number is
evidence, not an expectation the test was shaped to meet:

```
$ .venv/bin/python -m pytest tests/test_pacing.py -q
>       assert len(offsets) == -1, (
E       AssertionError: the current rule asked a never-recovering retailer 125 times over a
E       simulated thirty days at the 300-second standing cadence; the recorded before-number
E       for criterion 3 is the literal in this assertion
E       assert 125 == -1
E        +  where 125 = len([0.0, 600.0, 1800.0, 4200.0, 9000.0, 18600.0, ...])
```

With `125` transcribed in: `76 passed in 0.11s`.

**The shape of the 125 — a decomposition of the one count, not a second count.** Read off the
offsets the run printed, `125 = 6 + 1 + 118`: six requests while the backoff climbs (t = 0, 600,
1800, 4200, 9000, 18 600), one at t = 37 800 where the cap first binds, and 118 more at one every
21 600 s for the remaining 29-and-a-bit days. **The flat tail is the overwhelming majority of the
number** — the six-hour ceiling repeating, four times a day, against a retailer that has said no
every single time. That tail is the sentence REQ-22 exists to overrule, stated as arithmetic.

**What is NOT claimed here.** Not criterion 6 — no mutation was registered and none was observed
CAUGHT; **M42 is still free**. Not a comparison. Not a threshold.

---

## Collision 1 — the staleness window's derivation (`boty/pacing.py:151`)

**The question.** `STATE_MAX_AGE_SECONDS = MAX_BACKOFF_SECONDS`, and `MAX_BACKOFF_SECONDS` is the
ceiling this phase stops applying indefinitely. If the cool-off makes the effective longest wait
days-scale, a six-hour staleness window discards it on every restart.

**Resolved as option (a): the derivation carries the new number.** The argument is the constant's
OWN comment, which is why this is the derivation's argument rather than a new one imposed on it. It
says a record older than *"one full cap-length window"* has outlived the reasoning that produced it
— so the window must be **the longest wait this module can produce**, not the longest *backoff*.
Those were the same number until this phase; they stop being the same number in wave 2.

**The shape.** A named derived constant — `LONGEST_WAIT_SECONDS` (candidate name, `08-03`'s to fix)
— with `STATE_MAX_AGE_SECONDS` deriving from it. Deriving rather than re-choosing is the whole
point: two independently chosen numbers only have to disagree once, which is the argument
`STATE_MAX_AGE_SECONDS`' own comment and `Result.degraded` both already make.

**Option (b) is criterion 5 failing, and is recorded as that rather than as a tradeoff.** A
days-long cool-off discarded after six hours on every restart does not survive a restart. Criterion
5 says it must. There is no version of (b) that is a different balance of costs.

**Two constants do NOT move:** `MAX_BACKOFF_SECONDS` stays at 6 hours, and `STATE_MAX_AGE_SECONDS`
survives as a name. Only the derivation moves.

**Where it lands, and why that is not the obvious wave.** It lands in **`08-03`, not `08-02`** — so
that `08-03`'s tests are genuinely red against unfixed code, rather than red against a synthetic
revert. A test written after the fix, against code that was never wrong, is the watched-red
formality this repo refuses.

**The consequence, stated out loud, because it is a real gap.** Between wave 2 and wave 3 the tree
holds a days-long cool-off that a restart would discard after six hours. That is a **recorded
one-wave gap, not a shipped defect**, and all three clauses are needed to say so:

1. nothing is deployed mid-phase;
2. `boty` is an editable install, so the daemon picks up a change only on a restart; and
3. a restart is Dan's call, never a task.

The third clause alone is not the argument — it is only the last of three.

---

## Collision 2 — `due_at` stays unpersisted, and a restart costs exactly one probe

**Concession (b), quoted rather than paraphrased** (`boty/pacing.py:62-67`):

> (b) `due_at` IS STILL NOT PERSISTED, which keeps the withdrawn paragraph's own
>     concession intact. A restart still tries once, immediately, at full rate,
>     so the condition is re-tested at once. What is inherited is only the DEPTH
>     the penalty resumes at IF that one request is refused again, plus whether
>     a human has already been told. The withdrawn paragraph was right about the
>     request and wrong about the memory.

**Decision: KEEP it.** No `due_at` is persisted by this phase.

**Why criterion 5 is met anyway.** Criterion 5 asks for *"the same guarantee the existing backoff
already carries"*. That guarantee **is** depth-only — it always was — so a cool-off that survives as
`refusals` (already persisted, already stamped, already aged) carries exactly the guarantee named,
without a new persisted field.

**The scoping this forces on criterion 2, said now rather than discovered later.** Criterion 2's
*"exactly once"* is scoped to **a running process**. A restart mid-cool-off re-probes immediately.
That qualification is normal to state now and would be unforgivable to discover at verification
time, which is the only reason it is written here in advance of the code that will need it.

**The price, in one sentence a reader can act on:** one immediate request per restart, at full rate.

Criterion 3's baseline number states this assumption in its own docstring rather than leaving it to
be inferred, so the 125 above is explicitly a zero-restart figure.

---

## Collision A — an existing test breaks deliberately, and that is the outcome to choose

**The test**, `tests/test_pacing.py:176`,
`test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring`. It drives `for _ in
range(30)` refusals and then asserts, in full and verbatim:

```python
    assert p._for("amazon").due_at - now == MAX_BACKOFF_SECONDS
    assert MAX_BACKOFF_SECONDS <= 6 * 60 * 60, "a cap beyond a few hours is not a monitor"
```

**Withdrawn:** the first — that after 30 refusals the wait equals `MAX_BACKOFF_SECONDS`. REQ-22
overrules it for a *persistently* refused retailer: 30 consecutive refusals is precisely the case
the phase exists to stop treating as "keep asking every six hours forever."

**Survives:** the second. `MAX_BACKOFF_SECONDS <= 6 * 60 * 60` — *"a cap beyond a few hours is not a
monitor"* — stays live and stays true.

**`MAX_BACKOFF_SECONDS` stays 6 hours.** What this phase replaces is the ceiling being applied
*indefinitely*, not its value. Raising the value instead would trip the surviving assertion and lose
the distinction the phase is entirely about — the backoff is still right, it just must not be the
last word.

`08-02` rewrites this test in the dated-reversal form: the withdrawn assertion quoted in full with
its date, the measured facts that overruled it, then what survives.

### The threshold band — recorded; the value is `08-02`'s to pick

| Bound | Value | Status |
|---|---|---|
| Upper | **at most 30** | **Hard.** At 31 or more this test survives untouched, which is the worse outcome — see below. |
| Lower | above where the cap first binds (7 refusals at the 300 s default) | **Provisional.** See the withdrawal immediately below. |
| Far ceiling | far below `MAX_PERSISTED_REFUSALS = 64` | Holds; 64 is itself far below the measured `2.0 ** 1024` overflow cliff. |

**Why 31-or-more is the worse cheap option**, even though it leaves the test untouched: the sentence
REQ-22 exists to overrule would then still be standing, unremarked, at exactly the boundary
criterion 1 is about. A test that survives by being routed around is a test that stopped meaning
anything, and nobody would be at the moment of noticing. Breaking it is how the change gets seen.

**A stated lower bound is WITHDRAWN here, on a measurement taken 2026-08-28.** `08-PLAN-OUTLINE.md`
and `08-01-PLAN.md` both give the lower bound as *"comfortably above `cli.REFUSALS_BEFORE_PAGING =
5` (or persistence defeats the paging clause)"*. **That constant does not exist.**
`REFUSALS_BEFORE_PAGING` and `_refusal_is_entrenched` were deleted on 2026-08-12; `boty/cli.py:432`
carries the deletion note, and `test_the_clamp_never_restores_a_shallower_wait_than_the_cap`
(`tests/test_pacing.py:977`) was re-anchored off it the same day, because *"Dan's rule removed that
clause and its constant with it: a refusal is recorded and never pushed, however entrenched, so
there is no longer a paging threshold to stay above."* Recorded beside the original rather than
edited away — the outline's constraint was written against a repo state that had already moved, and
a later wave reading only the outline would have preserved a bound whose reason is gone.

What replaces it is weaker and is marked as such: a threshold below ~7 would enter the cool-off
before the six-hour ceiling had bound even once, which makes the cool-off a *replacement* for the
backoff rather than its successor. That is an argument, not yet a measurement, and it is
**`08-02`'s to settle** — this document does not pick the number.

**A stale comment found and deliberately not fixed.** `boty/pacing.py:175` still reads *"It must
also stay comfortably above `cli.REFUSALS_BEFORE_PAGING`"*, naming the same deleted constant. It is
a genuine defect. `08-01` changes no production code by design, and its acceptance criteria assert
the changed-file list by equality, so fixing it here would poison the scope fence the baseline
number depends on. **Handed to `08-02` or `08-03`**, both of which edit `boty/pacing.py` and both of
which will be reading this comment block anyway.

---

## Collision B — the dashboard's `fmtDur` tops out in hours

**The measured fact.** `served/boty/index.html:118`:

```javascript
const fmtDur = s => s < 90 ? `${s|0}s` : s < 5400 ? `${(s/60)|0}m` : `${(s/3600)|0}h`;
```

Three bands, the last unbounded in hours, so a three-day cool-off renders as `72h`.

**Decision: `72h` is legible, and the decision is deliberately `08-04`'s to make rather than wave
1's to pre-empt.** It is a presentation choice that depends on what the number actually turns out to
be, and `08-04` is the wave that has the number. **Keeping `72h` is itself a deliverable** — what is
forbidden is discovering the format by accident, not choosing to leave it.

**The constraint that binds `08-04` either way.** If a day band is added, both dashboard gates
re-enter:

- **no HTML comments inside the `<script>` block** — a backtick inside one closed a template literal
  and stopped the whole page parsing while every regex gate stayed green;
- `esc()` on every `UNTRUSTED` field;
- `node --check` on the extracted script, which needs `export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh`
  first, because `make` does not inherit nvm.

Note also that `fmtDur` is shared: `fmtAge` is defined through it, so a new band changes the
banner's age string too. That coupling is deliberate (one home for the bands) and is a reason to
change it carefully, not a reason not to.

---

## Collision C — the baseline test does not survive 08-02, and that is its second job

**Provenance differs from the four above: found while writing `08-01`.** It is in neither
`08-PLAN-OUTLINE.md` nor `08-PATTERNS.md`.

**The mechanics.** Task 1's simulation drives 125 consecutive refusals through `current_interval` —
far past any threshold at or below 30. The moment `08-02`'s cool-off branch lands, the stated
literal `125` is wrong and the test goes red.

**Resolution: that red is the point, and it is `08-02`'s watched-red evidence for criterion 3.** The
sequence is: the baseline test passes at 125 today; `08-02`'s change turns it red at the after-number;
`08-02` records both counts and the transition; then `08-02` **rewrites** the test in the dated-reversal
form — the withdrawn literal quoted with its date and the command that produced it, the new literal
asserted live. That is one test carrying both of criterion 3's numbers, which is what criterion 3
asks for. No second test file, no duplicated simulation.

**The option NOT taken, because it is the tempting one.** Freezing a hand-written reproduction of
the old arithmetic into the test file, so the before-number stays re-runnable forever. **Rejected**:
it is a second copy of a number, which this module argues against three times over — and the copy
would be of a *rule that no longer exists*, so nothing could ever check it again. A re-runnable
assertion over dead arithmetic looks like evidence and is not.

**The residual, stated honestly: after `08-02` the before-number is a dated record rather than a
re-runnable assertion.** That is the same footing every superseded measurement in this repo stands
on. `CLAUDE.md`'s rule for it is *recorded beside, never edited away*, and what does the recording is
this section, the rewritten test's docstring, and the phase record together.

---

## The assumption-delta detector — fired, and dismissed

The detector flagged the token *"second"* in criterion 5's *"discarded when stale by the existing
rule rather than a second one"*.

**False positive.** The criterion is not introducing a second case; it is **forbidding** one. No
identity-model question is open, and nothing is owed to a later wave.

Recorded here rather than raised as a question in `QUESTIONS.md`, because it names nothing Dan could
decide or do. A detector that ran and found nothing is worth one line — a reader who cannot tell
*"ran and cleared"* from *"never ran"* has learned nothing from the silence.
