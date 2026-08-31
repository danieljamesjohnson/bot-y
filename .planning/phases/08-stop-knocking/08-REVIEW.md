---
phase: 08-stop-knocking
reviewed: 2026-08-31T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - boty/monitor.py
  - boty/pacing.py
  - scripts/mutation_check.py
  - tests/test_cli_watch.py
  - tests/test_monitor.py
  - tests/test_pacing.py
findings:
  critical: 1
  warning: 4
  info: 0
  total: 5
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-08-31
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

The cool-off itself is correct. I traced the threshold at 29/30/31, the persisted
`refusals` counter across a restart, the clamp/threshold ordering, and the two-sided
`refused_at` bound, and found no off-by-one and no path that lets the monitor publish a
confident availability it did not measure. `run_once`, `assess_health` and `State` are
comment-only in this phase and are unchanged in behaviour. `.venv/bin/python -m pytest
tests/test_pacing.py tests/test_monitor.py tests/test_cli_watch.py -q` → **189 passed**;
`ruff check boty/ tests/ scripts/` → clean.

What the phase got wrong is not the schedule — it is **two measured claims that the code
contradicts, and one reachable surface that names a cause the code did not establish.**
In a repository whose stated rule is "a claim must be tied to a measurement" and "never
round a claim up", those are the findings that matter here.

The headline: the ~0.12% staleness-window residual is recorded as deliberate, and I am
not re-litigating the decision to accept a residual. What I am reporting is that **the
recorded number and the recorded mechanism are both wrong.** The mechanism named
(jitter) provably cancels; the mechanism that actually bites (the check pass's own
wall-clock duration, never added to the pacer's synthetic clock) is systematic and
unidirectional, and measured against this host's own `status.json` it is ~70× the
recorded figure.

All five findings were reproduced by running code, not by reading it. Reproductions are
inline.

---

## Critical Issues

### CR-01: The recorded staleness residual names a mechanism that cancels and a number that is ~70× too small — a restart in an 8.4% window silently undoes the phase

**File:** `boty/pacing.py:414-426` (the residual paragraph), with the mechanism at
`boty/cli.py:700-701` and `boty/cli.py:479,524`

**Issue:**

`STATE_MAX_AGE_SECONDS`' comment states, as a measurement:

> "…a record can age out only in the sliver between a cool-off expiring and the next
> cycle actually probing — **the loop's schedule advances with jitter**, so the probe
> lands at or slightly after the wait rather than exactly on it. **That is roughly one
> cycle, about 300 s in 259 200, or 0.12% of the window**"

Both halves are false, for one reason each.

**1. Jitter cancels exactly.** `cli.watch_loop` computes one `delay`, sleeps it, and
advances the pacer's clock by *the same float*:

```python
delay = cfg.interval_seconds * random.uniform(0.85, 1.15)   # cli.py:699
sleep(delay)                                                 # cli.py:700
scheduled_now += delay                                       # cli.py:701
```

There is no jitter-induced drift between `scheduled_now` and wall clock. Simulated over
one whole window with duration held at zero, the residual is **107 s (0.04%)** — i.e.
jitter alone is *smaller* than the recorded 300 s claim, and it is a random walk about
zero rather than a bias.

**2. What does not cancel is the check pass.** `watch_cycle` runs before the sleep and
takes real wall-clock time (`started = time.monotonic()` at `cli.py:479`,
`duration_seconds=time.monotonic() - started` at `cli.py:524`). That duration is **never
added to `scheduled_now`.** So the pacer's synthetic clock lags wall clock by the
cumulative cycle duration, monotonically and always in the same direction.

`refused_at` is wall clock (`pacing.py:634`); `due_at` is synthetic (`pacing.py:655`);
`load`'s bound compares wall against wall (`pacing.py:962`). So the cool-off probe fires
at wall time `refused_at + COOLOFF_SECONDS + Σ(cycle durations)`, while the record ages
out at wall time `refused_at + STATE_MAX_AGE_SECONDS` — and those two constants are now
deliberately **equal**. Everything in between is a window in which the on-disk record is
stale and the retailer has not yet been re-stamped.

**Measured, not argued.** `served/boty/status.json` on this host records
`duration_seconds: 27.613526625093073` for a live cycle. One cool-off window is ~864
cycles at the 300 s standing cadence:

```
cycle duration   0.00s -> 868 cycles, probe at wall  259307s, record stale for    107s (0.03 h) =  0.04% of the window
cycle duration   5.00s -> 865 cycles, probe at wall  263583s, record stale for   4383s (1.22 h) =  1.66% of the window
cycle duration  27.61s -> 867 cycles, probe at wall  283019s, record stale for  23819s (6.62 h) =  8.42% of the window
```

So the real residual on this host is **6.62 hours, or 8.42% of every cool-off window** —
not 300 s and not 0.12%. `pacer.save()` runs every cycle throughout that window and
rewrites the same stale `refused_at`, so the document on disk is stale-but-present the
whole time.

**Why this is a BLOCKER and not a rounding quibble.** A restart landing in that window
makes `load` `continue` past the entry (`pacing.py:962-963`). The retailer comes back at
**0 refusals**, is asked at full rate, and has to climb 300 → 600 → … → 21600 and then
accumulate 30 consecutive refusals before it re-enters cool-off — roughly six days of
six-hourly knocking. That is precisely leg 3 of the argument this same comment gives for
widening the window in the first place ("the phase's own result undone by its own
persistence layer"), reintroduced at 8.42% per window instead of 100%. The module's own
docstring argues that under `Restart=` semantics a restart "is what a supervisor does
whenever anything goes wrong", so this is not a rare draw. Live state today has `target`
at **46 refusals** — past the threshold — so the mechanism binds on a real retailer at
the next daemon restart, not on a hypothetical one.

**Fix:** The recorded number and mechanism must be corrected whatever else is decided —
under this repo's rules a wrong measurement presented as measured is the defect. The
cheapest correct fix also removes the drift: advance the pacer's clock by the time the
cycle actually consumed, so `scheduled_now` tracks wall clock.

```python
# boty/cli.py, watch_loop
cycle_started = time.monotonic()
try:
    warned = watch_cycle(cfg, checker, state, warned, pacer=pacer, now=scheduled_now)
    ...
finally:
    pacer.save(warned)

completed += 1
delay = cfg.interval_seconds * random.uniform(0.85, 1.15)
sleep(delay)
# The check pass consumed real time that `due_at` is measured against. Advancing
# only by `delay` makes the pacer's clock lag wall clock by the cumulative cycle
# duration — measured at 27.6 s/cycle on this host, 6.6 h over one cool-off window —
# which is long enough for `refused_at` to age past STATE_MAX_AGE_SECONDS before the
# probe that would re-stamp it.
scheduled_now += time.monotonic() - cycle_started
```

If the drift is instead accepted, the paragraph at `pacing.py:414-426` must be rewritten
to name the real mechanism (un-accounted check-pass duration, not jitter) and the real
size (a function of cycle duration; 6.62 h / 8.42% at the 27.6 s measured today), and
the `08-03` SUMMARY/PLAN lines carrying `0.12%` should be superseded *beside* rather
than edited away, per `docs/retailer-evidence.md` § 6.

---

## Warnings

### WR-01: `skipped_reason` publishes "cooling off" for a wait that is entirely the operator's standing cadence

**File:** `boty/pacing.py:840-844` (the arm) against `boty/pacing.py:799-807` (the schedule)

**Issue:** The cool-off state is decided by **two independent copies** of
`st.refusals >= REFUSALS_BEFORE_COOLOFF` — one inside `current_interval`'s `max`
(`pacing.py:802`) and one in `skipped_reason` (`pacing.py:840`). The module argues three
separate times against exactly this ("Two copies of a rule are two things to edit and
they only have to disagree once" — `pacing.py:775-777`, which is the whole justification
for putting the cool-off *inside* the `max` rather than in a guard clause).

They already disagree, in a configuration the module explicitly documents as legitimate.
`config._interval` (`boty/config.py:228-238`) enforces a floor and **no upper bound**, so
`interval_seconds: 604800` loads. `LONGEST_WAIT_SECONDS`' own comment
(`pacing.py:333-343`) names this case and says "no persisted count is load-bearing there
at all", and `test_a_standing_interval_above_the_window_makes_the_restored_depth_irrelevant`
(`tests/test_pacing.py:1496`) drives it — but asserts only `current_interval`, never
`skipped_reason`. Reproduced:

```
$ .venv/bin/python -c "..."   # default_interval = 604800, 30 refusals
current_interval: 604800   (== standing 604800)
due_at:           604800.0
skipped_reason:   cooling off after 30 refusal(s) — next attempt in ~7.0 days
```

No cool-off is in force: `max(604800, 259200)` returns the standing interval, and the
retailer would be asked at exactly that cadence at zero refusals too. The status page
nonetheless attributes the wait to a penalty this module applied. That is a surface
naming a cause the code did not establish, which is REQ-15's rule, and it is the same
class of defect `_is_store_gap`'s docstring in `boty/monitor.py:416-452` was rewritten to
remove.

`scripts/mutation_check.py`'s M42 block (`mutation_check.py:1640-1651`) already records
that this divergence exists and is un-gated under mutation; what it does not record is
that it is reachable **without any mutation**, on a config `Config.load` accepts in
silence — which is the same standard `test_a_refusal_never_shortens_the_wait_however_long_the_standing_interval`
was written to, "not reachable on `config/products.yaml` today … which is exactly why it
needs a test rather than a comment".

**Fix:** derive the state from the one expression instead of restating the comparison,
and add the missing assertion to the existing test.

```python
# boty/pacing.py, skipped_reason
# Derived, never restated: the cool-off is a fact about the SCHEDULE, and the
# schedule is `current_interval`. Restating the threshold here lets the page call a
# standing interval above COOLOFF_SECONDS a penalty that is not in force.
if self.current_interval(retailer) == COOLOFF_SECONDS and st.refusals >= REFUSALS_BEFORE_COOLOFF:
    return (
        f"cooling off after {st.refusals} refusal(s) — "
        f"next attempt in ~{remaining / 86400:.1f} days"
    )
```

```python
# tests/test_pacing.py, in test_a_standing_interval_above_the_window_...
assert "cooling off" not in p.skipped_reason("amazon", 0.0), (
    "the page called the operator's own standing cadence a cool-off penalty"
)
```

---

### WR-02: The clamp's stated purpose is now unreachable, and `# must not raise` is a gate that cannot bite

**File:** `boty/pacing.py:440-453` and `boty/pacing.py:969`; the test at
`tests/test_pacing.py:1532-1574` (assertion at `:1573`)

**Issue:** `MAX_PERSISTED_REFUSALS`' comment states the hazard as live:

> "So a file containing `"refusals": 1000000000` is not a big number. It is an exception
> raised inside every cycle, caught by `watch_loop`'s handler, counted to
> `FAILURES_BEFORE_GIVING_UP` and returned as exit 1: a one-line denial of service on the
> monitor, from a file the monitor wrote itself."

REQ-22 made that false. `current_interval` is a conditional expression, so at
`refusals >= 30` the branch containing `st.interval * BACKOFF_FACTOR ** st.refusals` is
never evaluated — a property the phase itself argues for at `pacing.py:779-786` and at
`COOLOFF_SECONDS` (`pacing.py:214-221`), without following it through to this comment.
The exponent is now only ever evaluated at refusals 1–29, where the largest value is
`300 * 2**29 = 1.6e11`. Reproduced with the clamp bypassed:

```
$ # st.refusals = 10**9, as if `load` did NOT clamp
record() with an UNCLAMPED 1e9 count did NOT raise; due_at = 259200.0
max exponent actually reachable: 29 -> 161061273600.0
```

The consequence is a dead gate. `test_the_persisted_count_is_clamped` carries
`p.record("amazon", refused=True, now=0.0)  # must not raise` — that line now passes with
or without the clamp, so it no longer defends anything. Its docstring nonetheless asserts
the opposite, in a paragraph *written by this phase on 2026-08-28*:

> "WHAT SURVIVES IS THIS TEST'S ENTIRE SUBJECT, untouched. The subject is the measured
> `2.0 ** 1024` `OverflowError` above and the clamp that prevents it … and a cool-off has
> nothing to do with it."

A cool-off has everything to do with it: the cool-off is now what prevents it. This is
the repo's own rule — "a test that has never failed is not a gate" — landing on a gate the
phase re-argued and did not re-measure.

**Fix:** the clamp is still load-bearing for the *new* relationship (staying above
`REFUSALS_BEFORE_COOLOFF`, which `test_the_clamp_sits_above_the_cooloff_threshold_so_a_restored_count_can_cross_it`
does gate), so keep it — but record the withdrawal beside the old argument rather than
leaving it standing:

```python
#: THE OVERFLOW ARGUMENT ABOVE WAS OVERRULED ON <date> AND IS KEPT AS HISTORY.
#: REQ-22 made `current_interval` a conditional expression, so at or past
#: `REFUSALS_BEFORE_COOLOFF` the exponentiation is not evaluated at all. Measured:
#: an UNCLAMPED `refusals = 10**9` returns 259200.0 and does not raise. The largest
#: exponent this module can now reach is 29 (`300 * 2**29 = 1.6e11`), far below the
#: 1024 cliff. What still makes this constant load-bearing is the relationship
#: below — it must stay ABOVE `REFUSALS_BEFORE_COOLOFF` — and that one is gated.
```

and mark the dead assertion in the test rather than letting it read as a live gate:

```python
# `# must not raise` no longer bites: with the cool-off arm this call returns
# 259200.0 whether or not the clamp ran. Kept as a smoke check, NOT as the gate
# for this constant — that gate is
# test_the_clamp_sits_above_the_cooloff_threshold_so_a_restored_count_can_cross_it.
p.record("amazon", refused=True, now=0.0)
```

---

### WR-03: The cool-off arm renders a live wait as "~0.0 days" — the exact failure its own comment says one decimal place exists to prevent

**File:** `boty/pacing.py:843` (the format), against the comment at `boty/pacing.py:828-833`

**Issue:** The comment states:

> "ONE DECIMAL PLACE, NOT ZERO, and the difference is load-bearing. A partial day
> formatted to zero decimals renders a live wait as '0 days' — a retailer that is
> genuinely being left alone, described as one that is not being left alone at all."

One decimal place does not close that. `f"{x:.1f}"` rounds, so any remaining wait below
`0.05 days = 4320 s` renders as `0.0`:

```
150  -> ~0.0 days      4319 -> ~0.0 days
300  -> ~0.0 days      4320 -> ~0.1 days
```

The arm is reachable across that whole band. `due()` skips a retailer while
`remaining > default_interval * 0.5` (150 s at the default), so the reachable window is
`(150 s, 4320 s)` — about **14 cycles per cool-off window**, each of which writes a
`status.json` row reading `cooling off after N refusal(s) — next attempt in ~0.0 days`.

The practical harm is smaller than the comment's framing (at 70 minutes remaining the
retailer genuinely is about to be probed), which is why this is a WARNING and not a
BLOCKER. But the comment claims a property the code does not have, on a surface this
module says exists to stop exactly that.

**Fix:** either state the residual honestly, or render the tail in units that survive it:

```python
# boty/pacing.py, skipped_reason
if st.refusals >= REFUSALS_BEFORE_COOLOFF:
    # Below ~72 min a `.1f` day count still rounds to "0.0 days" — the failure this
    # method exists to prevent, one band down. So the tail falls back to hours,
    # which is a number a reader of the page can act on at that scale.
    left = (
        f"~{remaining / 86400:.1f} days"
        if remaining >= 0.05 * 86400
        else f"~{remaining / 3600:.1f} hours"
    )
    return f"cooling off after {st.refusals} refusal(s) — next attempt in {left}"
```

and pin it, since the existing test only exercises `remaining` at a full window:

```python
# tests/test_pacing.py
def test_a_cooloff_near_its_probe_does_not_render_as_zero_days() -> None:
    p = Pacer(default_interval=300)
    for _ in range(REFUSALS_BEFORE_COOLOFF):
        p.record("cooling", refused=True, now=0.0)
    reason = p.skipped_reason("cooling", 259200.0 - 3600.0)  # one hour left
    assert "0.0 days" not in reason, reason
```

---

### WR-04: `CLAUDE.md`'s mutation-registry invariants went stale with M42 and were not updated

**File:** `scripts/mutation_check.py:1709` (M42) against `CLAUDE.md:162,166,171`

**Issue:** M42 was registered and its comment block added an eighth `INTENTIONAL GAP`
restatement (base commit: 7, HEAD: 8 — `grep -c "INTENTIONAL GAP"`). Three statements in
`CLAUDE.md` are now false:

- `CLAUDE.md:162` — "Currently **M1–M20 and M25–M41**" (should read M25–M42)
- `CLAUDE.md:166` — "The script says so in **seven** places (`grep -c "INTENTIONAL GAP"`)
  — six until M41 added the seventh on 2026-08-25" (now eight; M42 added the eighth)
- `CLAUDE.md:171` — "Next free ident is **M42**" (M42 is consumed; next free is M43)

Nothing in the suite gates these counts, which is exactly why they drift. `CLAUDE.md`'s
own closing section makes this the reviewed work's responsibility: "When this file is
wrong — fix it as part of your work. A stale `CLAUDE.md` misleads every future agent."
The registry-arithmetic paragraph is precisely the kind a future agent trusts without
re-counting, and "next free ident is M42" would cause an ident collision.

**Fix:**

```diff
-suite notices. Currently **M1–M20 and M25–M41**.
+suite notices. Currently **M1–M20 and M25–M42**.
@@
-> harness by construction. The script says so in seven places (`grep -c "INTENTIONAL GAP"`)
-> — six until M41 added the seventh on 2026-08-25, which restates the rule rather than
+> harness by construction. The script says so in eight places (`grep -c "INTENTIONAL GAP"`)
+> — seven until M42 added the eighth on 2026-08-28, which restates the rule rather than
@@
-Next free ident is **M42**. Register one only when it defends something new — if every
+Next free ident is **M43**. Register one only when it defends something new — if every
```

---

## Already recorded as deliberate — checked, not re-litigated

Verified against `08-DECISIONS.md` and the phase SUMMARY files; each was traced in the
code and confirmed to be the argued behaviour rather than an accident. **Not counted as
findings.**

- **`record()`'s `~4320 min` log line** (`pacing.py:642-648`). Confirmed live: a
  cool-off refusal logs `refused us (N in a row) — next attempt in ~4320 min, not 5`,
  in the same module whose `skipped_reason` docstring argues 4320 minutes is "right in
  units that hide what it means". Recorded as left unfixed.
- **No `_RetailerState` field for the cool-off** (`pacing.py:519-555`). The three-leg
  argument holds: `refusals` is persisted, stamped, aged and clamped, and
  `MAX_PERSISTED_REFUSALS (64) > REFUSALS_BEFORE_COOLOFF (30)` is gated by a test, so a
  restored count crosses the threshold. Verified end to end.
- **No `STATE_VERSION` bump** (`pacing.py:269-318`). Confirmed: `save` writes the same
  two sections with the same fields, so pre- and post-phase documents are
  parse-compatible in both directions.
- **The three `fmtDur` bands in `served/boty/index.html:118`** — out of scope for this
  file list; confirmed 259200 s renders as `72h`.
- **No mutation ident for the `skipped_reason` / `current_interval` divergence**
  (`mutation_check.py:1640-1651`). The reasoning is sound as far as it goes; WR-01 above
  is a *different* claim — that the divergence is reachable in unmutated code on a
  config the loader accepts — and is not covered by it.
- **The `warned` age-out widening from 6 h to 3 days**, which can suppress a health
  warning about our own dead control for up to three days. Argued at
  `STATE_MAX_AGE_SECONDS` and named in `tests/test_pacing.py:1155-1162`; bounded, never
  unbounded. Confirmed the bound is two-sided and that one constant governs both halves
  of the document (`pacing.py:962`, `pacing.py:999`).

---

## Checked and clean

Traced and found no defect, recorded so the next reviewer does not re-derive them:

- **Threshold boundary.** `>=` in both sites; 29 → 21600, 30 → 259200, 31 → 259200 at
  both configured standing intervals. No off-by-one. `MAX_PERSISTED_REFUSALS >
  REFUSALS_BEFORE_COOLOFF` holds and is gated.
- **Cool-off across a restart.** `load` restores `min(refusals, 64)`, never `due_at`;
  a restart costs exactly one probe (`test_a_restart_mid_cooloff_is_probed_exactly_once_over_a_whole_window`,
  re-run green). The failure mode is CR-01's stale-window case, not the restore itself.
- **Stale `refused_at` cannot resurrect a cool-off.** The bound is two-sided
  (`0.0 <= now - refused_at <= STATE_MAX_AGE_SECONDS`), so a future stamp is discarded
  rather than trusted forever; `test_a_stamp_in_the_future_is_discarded` covers it at
  cool-off depth via `_RESTORE_ACROSS_THE_STALENESS_WINDOW` row 5.
- **No confident-availability path.** `run_once` still produces no `Result` for a paced
  retailer, `assess_health` never sees it, and `status.write` publishes `checked: false`
  / `ok: false` — asserted by the new `test_a_retailer_in_cooloff_publishes_the_days_scale_cadence_it_is_actually_on`.
  A cool-off cannot become a green row.
- **M42's anchor is unique.** `grep -c '            if st.refusals >= REFUSALS_BEFORE_COOLOFF$'
  boty/pacing.py` → 1. `skipped_reason`'s guard is eight-space indented and ends in a
  colon, so it is a different string and is not reachable by the replacement, exactly as
  the comment claims.
- **`boty check` does not call `skipped_reason`**, so the load-only pacer's `due_at = 0.0`
  cannot produce a bogus "next attempt in ~0.0 days" on that surface.
- **`monitor.py` is comment-only in this phase.** No behavioural change; the corrected
  `EARLIEST_CREDIBLE_READING` paragraph now matches the re-derived
  `pacing.STATE_MAX_AGE_SECONDS`.
- `ruff check boty/ tests/ scripts/` → clean. No unused imports in the new test code.

---

_Reviewed: 2026-08-31_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---

## Resolution — 2026-08-31

All five findings were addressed the same day the review was written. The report
above is left **unedited**: it is the record of what was found, and the outcomes
belong beside it rather than over it (`docs/retailer-evidence.md` § 6).

| ID | Outcome | Commit |
|---|---|---|
| CR-01 | **Fixed at the cause**, not absorbed in the window | `9ea42fe` |
| WR-01 | **Fixed** — the label is derived from `current_interval` | `232565a` |
| WR-02 | **Recorded beside itself**; the dead assertion marked a smoke check | `a58e7ac` |
| WR-03 | **Fixed** — the tail falls back to hours | `232565a` |
| WR-04 | **Fixed** — CLAUDE.md counts, and the M42 collision closed | `f2474f6` |

**Two corrections to this report, both in its favour and both measured.**

1. **CR-01's suggested fix would have broken five existing tests.** The report
   proposes `scheduled_now += time.monotonic() - cycle_started`. That replaces the
   delay term instead of adding to it, and `watch_loop`'s clock comment says the
   delay term is what keeps the loop deterministic under the tests' fake `sleep`.
   Measured: that variant fails **7 tests** — the two new clock gates plus five
   pre-existing tests it would have silently disarmed. Shipped instead:
   `scheduled_now += delay + cycle_duration`, with `cycle_duration` read *before*
   the sleep. The diagnosis was right; the prescription was not.

2. **CR-01's percentage used a different denominator.** The report gives 8.42% at
   27.61 s/cycle, dividing the drift by the *wall* window. Against the cool-off
   constant the same drift is 9.24%. Both are defensible framings and the
   magnitude is identical; the tree records the figure at the live 20.43 s/cycle
   (**6.84%**) so the number and the host that produced it travel together.

**Gate after the fixes:** `make verify-offline` **EXIT 0** — identity PASS over
242 files, **920 passed / 0 skipped** (up from 916, +4 gates), mypy clean over 18
source files, **38/38 mutations caught, survivors 0**. Watched red first at
**3 failed / 141 passed**; the fourth new test was green from birth and is
recorded as a regression guard rather than claimed as a gate.
