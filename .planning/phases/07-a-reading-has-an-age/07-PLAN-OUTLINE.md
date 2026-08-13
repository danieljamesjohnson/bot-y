# Phase 7: A Reading Has an Age — Plan Outline

**Drafted:** 2026-08-13
**Granularity:** coarse
**Phase requirements:** REQ-21
**Plans:** 6, in 6 waves — every wave serial, and this time for the **plainest** reason this
project has had: **no two plans own disjoint file sets.** Phase 6 recorded three plans that could
have run concurrently if the gate were per-plan; this phase has none, and § *Why every wave is
serial* shows the table rather than asserting it.

**The bar, doubled, and it is the same doubling Phase 6 took.** Criterion 2 says *"watched going
red"* in as many words and criterion 5 says every gate this phase adds has been. A gate shipped
without being observed failing is this phase committing its own defect — publishing a claim
(*"this is gated"*) that nobody measured. Every plan below carries its own red-watch, and 07-06
records them.

**One measurement reshapes the phase and it is stated before the table, because the table does not
make sense without it:** a paced-out watch does not have a *stale* row in `status.json` — **it has
no row at all**. See § *Finding 4*. Criterion 3 names `boty check` as a surface where staleness
must be presented, and `boty check` re-reads every watch, so under a stamp-only design that half
of the criterion is unreachable code. Carrying the remembered reading onto the surfaces is
therefore **required by criteria 3 and 4**, not scope added to them.

## Plans

| Plan ID | Objective | Wave | Depends On | Requirements |
|---|---|---|---|---|
| 07-01 | **A reading carries the moment it was taken, and a non-reading carries none.** `Result.read_at` declared last after `shipping` with the three paragraphs the four fields before it carry, and the asymmetry paragraph settled in writing: staleness touches **neither** `Availability` nor `alertable`, because every `Result` is fresh at the instant it is constructed, so a staleness flag folded into either could never fire (§ *Finding 7*). Threaded onto **all 20** `Result(` sites — and the naive rule *"an `except` arm read nothing"* is **measured false at two of them** (§ *Finding 2*): `check_bestbuy_api`'s `bad api json` and `sku not found` arms are responses that WERE read. Published in `status.json` as `null`, never `0` — epoch 1970 renders as maximally stale, the same class of lie one direction over. M31. | 1 | — | REQ-21 |
| 07-02 | **The age survives the restart, and the file that survives it changes shape without breaking on Dan's disk.** `monitor.State`'s document becomes a dated per-watch ledger; the **real** pre-07 shape — 13 bare strings, measured on this host today — loads as *availability with an UNKNOWN age*, which is criterion 2's direction and is also simply true of that file. Both-ended bound validation on the stamp, on `pacing.py:335-350`'s worked shape. `pacing.py:99-104`'s *"`monitor.State` … needs no version: its document is a flat map of strings whose meaning cannot drift"* is **falsified by this edit and rewritten in the same commit**, argued in place, original kept. The trap closes on a guard that already exists (§ *Finding 3*). M32. | 2 | 07-01 | REQ-21 |
| 07-03 | **The retailer's current interval becomes one readable number, and both surfaces read the same one.** `Pacer.current_interval(retailer)` extracted from the expression `record` computes inline and discards (`pacing.py:242-245`) and **used by `record`**, so the accessor and the schedule cannot drift — the derive-don't-store argument the module already makes twice. Threaded into `status.write` exactly as `paced` is threaded, published per retailer in the `retailers` array (a cadence is a per-retailer fact; a copy on every watch row is a second copy that can drift). `boty check` builds a **load-only** `Pacer` — never `save()`, never passed to `run_once` — so the surface that answers *"is this stale?"* cannot answer differently from the daemon (§ *Finding 8*). M33. | 3 | 07-02 | REQ-21 |
| 07-04 | **Every configured watch has a row, and a remembered reading says it is remembered.** Measured today: **3 rows for 14 configured watches**, and the two Dan asked about are among the eleven missing (§ *Finding 4*). `status.write` emits a row per configured watch — read-this-cycle rows unchanged, the rest carrying the remembered availability, its stamp (possibly `null`) and `checked: false`, which is the same three-valued honesty the `retailers` array already applies one level up in this very file. `alertable` on a remembered row is **false, stated not inherited**: an alert decision belongs to a reading somebody took. M34. | 4 | 07-03 | REQ-21 |
| 07-05 | **The three surfaces say the age out loud, and an absent one says UNKNOWN.** `cli._age_tag`, module-level and appended after the `(label, bool)` comprehension exactly as `_store_tag` is, with its forms enumerated in the docstring — including `[age ?]`, on `_store_tag`'s own recorded reasoning that *"the page did not tell us" is a fact worth printing*. Dashboard: `.tag.age` + `.tag.age.warn` at the established two weights, `fmtAge` **reused** not duplicated, the threshold **joined from the published interval and never from `index.html`'s existing hard-coded 30-minute file-level banner** (§ *Finding 9*). Producer/consumer pair per new key. M35/M36 — the natural pair: one makes an absent stamp render as *now*, one makes a stale reading render as fresh. | 5 | 07-04 | REQ-21 |
| 07-06 | **Close. No code.** 05-04's recorded decision governs: *"a closing plan that implemented its way to a green table would be a phase measuring work it did in the act of measuring."* `make verify-offline` run and recorded verbatim; the mutation count observed rising **from 26** (§ *Finding 1*) with each new ident observed CAUGHT; a **blocking checkpoint** carrying three measured user-visible consequences — the dashboard going from 3 rows to 14, `state.json` changing shape on his box at the next restart with the downgrade cost priced, and Walmart's GO Plus + row publishing an **UNKNOWN age forever** until a store is pinned (§ *Finding 5*); five criterion verdicts in Phase 3.1's / 4's / 5's / 6's outcome-table format, unmet recorded unmet with the date, nothing reworded. | 6 | 07-01 … 07-05 | REQ-21 |

**Plan numbers are creation order; waves are execution order.** Here they coincide. Plans 01–05
do **not** map one-to-one onto ROADMAP criteria 1–5 the way Phase 6's did, and that is stated
rather than left to be noticed: criterion 2 is split across 07-01 (the datum: an absent stamp is
`None`, never `now`) and 07-05 (the rendering: it shows as UNKNOWN), and criterion 3 is split
across 07-03 (the interval), 07-04 (a row that can be old) and 07-05 (the three renderings). The
§ *Multi-source coverage audit* carries the mapping explicitly for that reason.

`autonomous: true` for 07-01 … 07-05. **`autonomous: false` for 07-06** (one blocking checkpoint).

---

## Where the planning documents are wrong

Three corrections, all measured on this tree at `dbc9d49`, working tree clean. `07-CONTEXT.md` was
auto-generated (`workflow.skip_discuss`), so its errors are drafting errors and nothing Dan decided
is being re-opened. `07-PATTERNS.md` did real measurement and is right about almost everything —
including the one thing CONTEXT got wrong — but its own arithmetic slips once, in the same
sentence, and the slip has been repeated downstream.

### CORRECTION 1 — the mutation registry is **26**, and both documents state it wrong

`07-CONTEXT.md` § *Existing Code Insights*: *"26 mutations at M1–M20, M25–M28 … New idents start
at **M29**."* The **set is wrong** (M29 and M30 exist, at `mutation_check.py:680-693`, Phase 6's
paging-action pair) and its own stated set counts to 24, not 26.

`07-PATTERNS.md` § 6 corrects the set and miscounts it: *"The registry is **28** mutations: M1-M20,
M25-M30."* M1–M20 is twenty and M25–M30 is six. **That is 26.** The planning brief for this
outline inherited the 28 and asked for it to be checked against what is present; checked:

```
grep -c 'ident="M' scripts/mutation_check.py   →  26
idents, in file order: M1 … M20, M25, M26, M27, M28, M29, M30
```

**So all three of these are true and they do not conflict:** the registry is **26**;
`make verify-offline` prints **26/26** because that ratio is *caught over the whole registry*, not
26 of a larger 28; and **new idents start at M31**, which is what PATTERNS got right and what
matters most. M21–M24 remain the intentional gap, stated in the code itself at
`mutation_check.py:669`. **07-06 must record the count rising from 26.** A closing plan that
recorded it rising from 28 would be this milestone's own defect in the plan that closes it.

### CORRECTION 2 — CONTEXT's *"`status.json` … presents both as current"* is measured false in one direction

`07-CONTEXT.md` § *Existing Code Insights* and REQ-21 itself both say a four-second-old row and a
two-day-old row are byte-identical in shape and the page presents both as current. **Measured on
the live file: the two-day-old row is not there.** See § *Finding 4*. This is not an amendment to
REQ-21 — the requirement's text stands unedited and the phase is still exactly the phase it was —
but the shape of the fix changes, because a row that is absent cannot be labelled stale.

### CORRECTION 3 — `07-PATTERNS.md` § 8 asks the planner to settle the time seam; it is settled here as **no new seam**

Not a factual error — PATTERNS explicitly declines to settle it and hands it over. Settled in
§ *Finding 6*: every assertion this phase needs is reachable without an injected clock, provided
one rule holds — **every staleness comparison takes `now` as a parameter**, which is
`Pacer.due(retailer, now)`'s existing convention applied one module over. Written down here so no
plan spends its context rediscovering it, and so no plan adds `freezegun` to a project whose
non-functional requirements name a small dependency surface.

---

## Findings from the tree that must shape the plans

All measured 2026-08-13 against the working tree at `dbc9d49`. Findings 4, 5, 8, 9, 10 and 11 go
beyond what `07-PATTERNS.md` measured.

### Finding 1 — the registry, and which anchors are literal-coupled

Covered as § *CORRECTION 1* above: **26**, M1–M20 ∪ M25–M30, new idents at **M31**.

The drift hazard, re-measured, because the brief asked which anchors are literal-coupled and this
phase must not add more of them:

| Ident | Anchor | Coupling |
|---|---|---|
| M25 | the version literal in `pyproject.toml` | **version literal** — drifted and was re-pointed **2026-08-13** when the milestone rolled |
| M26 | the tag name in `README.md`'s publication sentence | **version literal** — re-pointed the same day |
| M2 | `detail=(` in `retailers.py` | re-anchored 2026-08-04 when prose moved |
| M19 | `rung=Rung.TLS,` plus a disambiguating line | **non-unique** anchor, bound by a test |

Everything else is behavioural. **Every anchor this phase adds must be a comprehension, a
conditional, a comparison or a named constant** — never a `detail` string, never a tag's rendered
text, never a version literal. Two of this phase's six new mutations live on surfaces made of
prose (a CLI tag, a dashboard `title=` sentence), so this is the constraint most likely to be
violated by accident: anchor on the *condition that chooses* the tag, never on the tag.

And the pre-count rule still binds — `apply_mutation` replaces the **first** occurrence in the
file. `read_at=None` will occur at eight arms in `retailers.py` after 07-01; a mutation anchored on
it hits `check_html`'s `except Blocked` arm, and the `breaks=` sentence must describe **that** arm
or it describes something that did not happen (Phase 6 paid for exactly this once).

### Finding 2 — 20 `Result(` sites, and *"an `except` arm read nothing"* is FALSE at two of them

Counted by hand. `grep -c "Result(" boty/retailers.py` = 21; line 268 is inside a comment. The 20
real sites, and — the part no prior document has — **what each one knows about whether a page was
actually read**:

| Function | Lines | Count | Did a page come back? |
|---|---|---|---|
| `_verdict_from_html` | 282, 311, 334, 351, 374, 391, 404, 446 | **8** | **Yes, all eight.** Every one follows a successful fetch and parse; they differ in what the page *said*, not in whether it answered |
| `check_html` `except Blocked` / `except FetchError` | 469, 471 | 2 | No |
| `check_amazon` `except Blocked` / `except FetchError` | 517, 526 | 2 | No |
| `check_bestbuy_browser` both `except` arms | 642, 651 | 2 | No |
| `check_target_browser` both `except` arms | 751, 761 | 2 | No |
| `check_bestbuy_api` — **no `_verdict_from_html` delegation at all** | 836, 845, 855, 865 | **4** | **Mixed: 1 no, 3 yes** |

`check_bestbuy_api`'s four, in order: `api error` (`except (Blocked, FetchError)`) — **nothing came
back**; `bad api json` (`except ValueError`) — **Best Buy answered and the bytes were unparseable**;
`sku not found` (an empty `products` list) — **Best Buy answered**; and the success arm.

**So the rule *"an `except` arm read nothing"* mis-stamps two of the twenty**, and it mis-stamps
them in the dangerous direction: it would mark a reading that *did happen* as having no age, and
Best Buy is then permanently UNKNOWN-aged on the one retailer this project reaches through an
official API. Phase 5's bulk edit missed two of eight and only the tests caught it; the sites at
highest risk this time are these four, exactly as PATTERNS predicted, but for a sharper reason
than "they do not delegate".

**The completeness gate that matches this repo's idiom:** a static AST assertion that every
`Result(` construction in `boty/retailers.py` names `read_at` explicitly — the same
`ast`-over-source shape `tests/test_support_matrix.py` and `tests/test_ci_workflow.py` already
use. It is the only form that cannot be satisfied by testing nineteen arms.

### Finding 3 — THE TRAP, and the guard that already closes half of it

A refusal happened at a wall-clock moment but **took no reading**, so stamping it refreshes the age
of a reading that never happened — the 2026-08-12 Walmart failure from the seed, rebuilt inside the
fix meant to prevent it. `pacing.py:196-199` already wrote the lesson down for `_warned_since`:

> *"stamping at write time would refresh the record forever and the age-out would never fire once —
> a bound that cannot bind is worse than no bound, because it reads like one in the file."*

**Half of the trap is already closed by a guard nobody wrote for this purpose**, and the plan
should inherit it rather than re-invent it. `monitor.State.transitioned_to_stock` returns on
UNKNOWN **before** it writes:

```python
        if result.availability is Availability.UNKNOWN:
            return False
        key = result.watch.key
        previous = self.seen.get(key)
        self.seen[key] = result.availability.value
```

So the persisted document is already written only when a verdict was resolved. A stamp written on
the line beside `self.seen[key] = …` inherits exactly the right rule, and 07-02 should say so
rather than add a second guard — **two gates on one rule means neither can be shown to bite**,
which is `mutation_check.py:678`'s own warning.

**The other half does not close itself, and 07-01 must state it per arm.**
`availability is UNKNOWN` is **not** the same predicate as *"no reading was taken"*: a store-gap
UNKNOWN and a parse-failure UNKNOWN both read a page, and a refusal did not. `refused=True` is
closer but still not identical — `check_bestbuy_api`'s `bad api json` arm sets no `refused` and
still received a response. So there is **no existing field that answers "was a page read"**, and
`read_at` becoming that field is the honest framing: it is not a derived view of `refused` or of
`availability`, and 07-01's declaration comment should say so in the shape
`models.py:365-373` uses for the asymmetry a reader will otherwise try to fix.

### Finding 4 — a paced-out watch has NO ROW in `status.json`. It does not go stale; it vanishes

**This is the finding that changes the phase's shape**, and it is measured off the live file this
daemon wrote at 08:25:10 today:

- `watches`: **3 rows** — one Nintendo product watch and two controls. `config/products.yaml`
  declares **14** watches.
- `retailers`: 6 rows, of which **four carry `checked: false`** — amazon *(backing off after 2
  refusals)*, gamestop *(paced, next attempt in ~11 min)*, target and walmart *(backing off after 7
  refusals each, next attempt in ~97 min)*.
- **The Amazon and Walmart GO Plus + watches — the exact two Dan asked about — are absent from the
  file.**

The mechanism, confirmed in source: `monitor.run_once` filters `watches` down to those the pacer
says are due (`monitor.py:319-324`) and `status.write` builds `watches` from `results`
(`status.py:90-146`). The file is rewritten from scratch every cycle. So a retailer that is not due
does not leave a stale row behind — its rows are simply not written.

**Three consequences, and together they are why 07-04 exists:**

1. **REQ-21's own sentence is one direction off.** *"the page presents both as current"* — measured,
   the page presents the stale one **not at all**. That is not better. Dan's question was *"so they
   are out of stock as of when?"*, and a row that is missing cannot answer it either. The
   requirement's text is **not edited**; this is recorded beside it, on Phase 3.1's precedent.
2. **Criterion 3's `status.json` half could otherwise only bind on a stopped daemon.** Every row in
   a running daemon's file is at most one cycle old by construction. Rows do age once the daemon
   stops — and they cross their per-retailer thresholds at *different* times, which is genuinely
   non-vacuous — but that case is already covered by the file-level banner, and it is not the case
   the seed is about.
3. **Criterion 3's `boty check` half could NOT bind at all.** `boty check` re-reads every watch
   with no pacer (`cli.py:584-596`), so under a stamp-only design its rows are fresh by
   construction and its staleness branch is unreachable code — *a bound that cannot bind*, on a
   surface criterion 3 names by name.

**So the remembered reading has to reach the surfaces.** That is 07-04 and it is required by the
criteria rather than added to them. It is also squarely inside CONTEXT's *Claude's Discretion* —
*"the exact rendering in `boty check` and the dashboard, and how 'stale' is expressed in
`status.json`"* — so it is a discretion exercised with the measurement written down, not a
decision taken away from anyone.

**The cheaper alternative, measured and rejected in advance:** stamp only, publish only, render
only what was checked this cycle. It costs four fewer files and it satisfies criterion 1 and
criterion 2 completely. It fails criterion 3 on two of the three named surfaces, and it leaves the
two watches that opened the phase invisible. **Rejected on `REQUIREMENTS.md` § Non-Functional's
recorded tiebreaker — *"Trustworthiness over coverage. Where they conflict, correctness wins"* —
and on this repository's standing rule that a gate which cannot go red is worse than none.**

### Finding 5 — `state.json` holds a FOSSIL, and it is on Dan's disk right now

The live file, 13 entries, every value a bare string, `sorted({f for v in state.values() if
isinstance(v, dict) for f in v})` still `[]` exactly as the seed says. Among them:

```
"walmart:Pokémon GO Plus +"   ->   "out_of_stock"
```

**That string can no longer be updated by anything.** The 2026-08-12 restart deployed Phase 5's
store-gap guard; `WALMART_STORE_ID` is still unset (`QUESTIONS.md` § 0f, open); so every Walmart
reading is now `Availability.UNKNOWN`; and `transitioned_to_stock` returns on UNKNOWN before it
writes. The value is not merely undated — **it is frozen, and it will say `out_of_stock` forever
until a store is pinned.**

This is the strongest available statement of the phase's defect and it needs no simulation. It also
sets one expectation 07-06 must carry to Dan rather than let him discover: **after this phase,
Walmart's GO Plus + row will publish `out_of_stock` with an UNKNOWN age**, indefinitely. That is
the honest output — the age genuinely is not established, and inventing one would be the defect —
but it is the second time this milestone has handed him the same open question, and a checkpoint
that shows it is better than a dashboard that surprises him with it.

### Finding 6 — the time seam: there is none, none is needed, and here is why

Re-measured across `boty/`, `tests/`, `scripts/`: `time.time()` at four sites
(`status.py:42`, `pacing.py:241, 323, 434`) and nowhere else in `boty/`; `time.monotonic()` for
durations only; no `freezegun`, no `Clock` protocol, no `monkeypatch` of `time.time`. The only
injected `now` is the **synthetic schedule clock** starting at 0.0 every process, documented as a
trap at `pacing.py:62-75` and `cli.py:432-435`. PATTERNS is right that using it for a reading
stamp would reproduce the bug that made `due_at` unpersistable.

**Settled: no new seam is built.** Every assertion this phase needs is already reachable:

| What must be asserted | How, with no seam |
|---|---|
| a non-read arm has no stamp | `assert r.read_at is None` — no clock involved at all |
| a read arm stamps the moment it read | bracket it: `before = time.time()`, call, `after = time.time()`, `assert before <= r.read_at <= after` |
| a stale reading renders as stale | construct `read_at=time.time() - age` — a value **read** rather than **taken**, which is exactly `tests/test_pacing.py:501-505`'s existing method |
| the age survives a restart | construct the persisted document with `time.time() - age` and load it — `test_pacing.py:585-591`'s method verbatim |
| the current interval is the backed-off one | `Pacer` already takes `now` as a parameter |

**The one design rule that makes all of it hold, and it must be in every plan that computes
staleness: the comparison takes `now` as a parameter and never reads the clock itself.**
`_age_tag(r, *, now, interval)`, not `_age_tag(r)`. That is `Pacer.due(retailer, now)`'s convention
applied one module over, and it means the only wall-clock reads this phase adds are at the sites
that *take* the stamp, where bracketing is sufficient.

### Finding 7 — a `stale` flag must NOT be computed at write time, and this repo already argued it

Tempting shape: `status.write` computes `stale: true/false` per row and publishes the answer.
**It cannot work, and the reason is written down in this repository already** — `pacing.py:196-199`,
quoted in full in § *Finding 3*: a value stamped at write time refreshes forever and the bound
never fires. Here it fails the mirror way: a row written fresh carries `stale: false`, and it keeps
carrying `stale: false` for as long as that file sits there, which is precisely the interval during
which it becomes stale.

**So: publish the raw facts and derive staleness at render time, in each of the three consumers.**
`read_at` per watch; the retailer's current interval per retailer; every consumer subtracts against
its own `now`. This is also `status.py:119-133`'s own recorded rule, applied a third time:

> *"the raw facts go out alongside any derived flag, because a single value cannot tell a reader
> WHY."*

It has a cost worth stating rather than discovering: **three consumers means three implementations
of one comparison** (`cli._age_tag`, the dashboard's JS, and whatever `status.json`'s own readers
do). The mitigation is the mutation pair in 07-05 plus the producer/consumer contract tests — not a
shared helper, because the dashboard cannot import Python.

**And it settles criterion 1's asymmetry paragraph.** Neither `Availability` nor `alertable` may
depend on staleness, and the reason is mechanical rather than aesthetic: **a `Result` is always
fresh at the instant it is constructed**, so a staleness term inside either property is a term that
is always false — a branch that can never be taken, which is the same unbindable gate one level in.
`models.py:517-522`'s standing rule (UNKNOWN is never RESOLVED into a verdict) points the same way
independently.

### Finding 8 — `boty check` has the ledger already and is missing only the interval

`main`'s check path builds no `Pacer` (`cli.py:584-596`: `run_once(cfg.watches, checker, state)`),
which PATTERNS flagged. **But it already does `State.load(cfg.state_path)` one line above**, so the
persisted ledger 07-02 creates is in its hands for free. Only the cadence is missing.

`refusals` is persisted and `interval` comes from config, so a `Pacer` constructed from
`cfg.interval_seconds`, `cfg.retailer_intervals` and `cfg.pacer_state_path` and then `load()`-ed
reconstructs **the daemon's own current interval exactly**. Criteria 3 and 4 agree rather than
fight, as PATTERNS says.

**Three constraints on that construction, each of which is a defect if missed:**

1. **Load-only. It must never `save()`.** `pacer-state.json` belongs to the daemon, and a second
   writer to one document is precisely the contradiction `pacing.py`'s own argument against a
   second file exists to prevent — pointed the other way. `boty check` is routinely run while the
   service is running.
2. **It must NOT be passed to `run_once`.** That would make `boty check` skip watches, which is a
   behaviour change nobody asked for, and it would reintroduce § *Finding 4*'s vanishing rows on
   the one surface that shows all of them.
3. **A missing `pacer-state.json` is the standing interval, not an error.** On a fresh clone
   `refusals` is 0 everywhere and the answer is the config value — correct, and it must not warn.

### Finding 9 — the dashboard already hard-codes a fixed clock, for a different question

`served/boty/index.html:133`: `const stale = age > 1800;` — a hard-coded 30-minute threshold on
`d.updated`, driving the *"the monitor may not be running"* banner. Criterion 3 forbids a fixed
clock **for a reading**; this one is about the **file**, and it is correct where it is.

**They must not be unified, and 07-05 must say so where a future reader will look**, because the
next person to see two staleness rules on one page will try to merge them. The banner asks *"is
this snapshot being written?"*; the row tag asks *"is this reading younger than the cadence its
own retailer is currently on?"*. The second cannot borrow the first's constant — a retailer at
seven refusals is legitimately on a ~97-minute cadence, and 1800 seconds would paint it stale
while it is behaving exactly as the politeness rule requires.

Two more measured facts for 07-05: **`fmtAge` already exists** at line 80 and is reused, not
duplicated (`Result.degraded`'s one-source-of-truth argument); and the tag convention is
`.tag` dim = an ordinary label, a second class with `var(--warn)` = a warning, with
`.tag.store` / `.tag.store.warn` as the worked two-weight pair. **A fresh reading is a label; stale
and UNKNOWN-age are warnings.**

### Finding 10 — `tests/test_status.py` asserts the EXACT key set, so every new key is a gate-visible act

`tests/test_status.py:171-187` asserts `set(payload) == {"updated", "healthy", "retailers",
"watches", "duration_seconds"}` and the exact 13-key set of a watch row. **Adding `read_at`,
`checked`, or a per-retailer interval turns that test red.**

Recorded so it is not read as a regression and not "fixed" by loosening the assertion to a subset
check. It is a producer-side contract of exactly the kind this milestone exists to add, it is the
first thing that will go red in 07-01, and it should be updated in the same commit that adds the
key — with the new keys enumerated, not with `<=`.

### Finding 11 — REQ-21 is already used in this tree, for something else

`tests/test_cli_watch.py:774` carries the section header:

```
# REQ-21: a push has to carry a human action, and the default is silence
```

written 2026-08-12 by Phase 6's paging work. **REQ-21 is minted nowhere in v0.2's archive and
nowhere in Phase 6's planning** — `grep -rn "REQ-21" .planning/milestones/
.planning/phases/06-*/` returns nothing. So that ident was invented in a test file and never
existed as a requirement. v0.3 then minted a real REQ-21, meaning something entirely different, on
2026-08-13.

It is not inert. **`scripts/mutation_check.py:672` cites *"tests/test_cli_watch.py's REQ-21
section"* as M29's expected killer**, so that citation becomes ambiguous the moment this phase
writes its own `# REQ-21:` section — and this phase creates the second half of the collision.

The section's own wording is REQ-16's wording (*"A notification is sent only when a human decision
changes the outcome"*), and `tests/test_cli_watch.py:510` already carries a `# REQ-16 across a
RESTART` section, so the label is a slip — somebody reached for the next free number instead of the
governing requirement. **Recommended:** the plan that first adds a REQ-21 test section relabels
line 774 to REQ-16 and re-points `mutation_check.py:672`'s citation in the same commit, with the
correction argued in place rather than silently retyped. **This is not a criterion being amended
to be meetable** — no criterion, requirement or measurement changes; a mistyped cross-reference in
a test file is being made to point at what it always meant. If a plan disagrees, the fallback is to
leave both and disambiguate every citation by line, which is worse but honest.

---

## Per-plan scope sketch

Task counts are the target for the per-plan write; files are the expected `files_modified`.

### 07-01 — a reading carries the moment it was taken (wave 1, autonomous)

~3 tasks.

1. **The field.** `boty/models.py` — `read_at: float | None = None` declared **last, after
   `shipping`**, its comment naming `shipping` as the field it follows, carrying the three
   paragraphs every one of `rung` / `extraction` / `store` / `shipping` carries: *what the default
   MEANS* (`None` is UNKNOWN age, **never** `time.time()` at construction — criterion 2's entire
   content, and `status.py:53-57`'s *"a missing measurement serialised as 0 would read off the
   dashboard as the fastest check ever recorded"* is the same rule for a number); *deliberately NOT
   folded into `degraded`* (an age is not a confidence discount, and it is not `degraded`'s third
   disjunct); and *the asymmetry a reader will otherwise try to fix* — **staleness touches neither
   `Availability` nor `alertable`, settled in § *Finding 7* on a mechanical argument**, with
   `models.py:517-522`'s standing rule cited as the independent second reason. State also that
   `read_at` is not derivable from `refused` or from `availability` (§ *Finding 3*), because that
   is the first simplification a reader will propose. `models.py:401-405`'s *"adding a field here
   publishes nothing new"* stays true of `shipping` and needs no edit — but it must not be read as
   forbidding publication of `read_at`, which criterion 1 requires by name.
2. **All twenty sites, stated not inherited.** `boty/retailers.py` — the three-way partition in
   § *Finding 2*, with the reason written at each non-read arm in `retailers.py:463-471`'s verbatim
   shape (*"stated, not inherited: a refusal produced no page…"*), and **`check_bestbuy_api`'s
   `bad api json` and `sku not found` arms stamped as reads with the reason stated**, because they
   are the two the obvious rule gets wrong. Tests written **first** — 05-01's bulk edit missed two
   of six and only the tests caught it — plus the AST completeness assertion from § *Finding 2*,
   which is the only form that cannot be satisfied by covering nineteen arms. The anchoring rule at
   `retailers.py:267-273` binds: comments above their `if`, so each condition line is immediately
   followed by its `return Result(` and its verdict.
3. **Published, and watched going red.** `boty/status.py` — `read_at` in the row comprehension,
   serialised as `null`, **never `0`**: epoch 1970 renders as maximally stale, which is the
   `store`-as-`0` lie one direction over, and the `status.py:136-141` paragraph is the precedent to
   extend. `tests/test_status.py:171-187`'s exact-keyset assertion goes red and is updated here
   (§ *Finding 10*), enumerated not loosened. **M31**: an absent stamp reads as *now* — anchored on
   the first `read_at=None,` arm with the `breaks=` sentence naming **that** arm (§ *Finding 1*),
   or on the serialiser's expression if that proves the cleaner behavioural anchor.

Files: `boty/models.py`, `boty/retailers.py`, `boty/status.py`, `scripts/mutation_check.py`,
`tests/test_models.py`, `tests/test_retailers.py`, `tests/test_status.py`.

### 07-02 — the age survives the restart (wave 2, autonomous)

~3 tasks.

1. **The ledger, and the migration.** `boty/monitor.py` — `State`'s document gains a per-watch
   stamp beside the availability. **A bare string is the pre-07 shape and loads as *availability
   with no age*** — which is criterion 2's fail-safe direction and is also simply true of that
   file, so the migration and the criterion agree rather than trade off. Both-ended bound
   validation on any stamp read back (`pacing.py:335-350`'s worked shape: the
   `isinstance(x, bool)` exclusion because bool is an int subclass, `continue`-rather-than-guess,
   and the future-stamp bound — *"a stamp in the FUTURE is a clock that jumped backwards"*).
   **The version question decided in writing, not defaulted:** `pacing.py`'s `STATE_VERSION`
   precedent exists and its cost is recorded; the argument for *not* taking it here is that the new
   field's units cannot drift the way a refusal count's can — which is the exact distinction
   `pacing.py:99-104` already draws — and that a version field does not protect against the real
   hazard, which is a **downgrade**: an older binary reading a newer file compares a mapping to
   `"in_stock"`, finds them unequal, and **re-alerts once per watch**. Whichever way it lands,
   that cost is priced in the code, and a second document is rejected on `pacing.py`'s own recorded
   argument (*"a second gitignore line, a second corrupt-file path, and a second way for a restart
   to come back holding a contradiction"*).
2. **Only a reading is stamped, and the guard already exists.** The stamp is written beside
   `self.seen[key] = result.availability.value`, inheriting the early UNKNOWN return rather than
   adding a second gate (§ *Finding 3*). **`boty/pacing.py:99-104` is rewritten in the same
   commit** — its premise (*"a flat map of strings whose meaning cannot drift"*) is falsified by
   this edit — argued in place with the original kept, on `models.py:145-161` / `pacing.py:5-15`'s
   house style for a reversal. Two residuals recorded rather than fixed: `State.save` never prunes,
   so keys for deleted watches accumulate and a stamp inherits that; and Walmart's frozen entry
   (§ *Finding 5*) will carry an UNKNOWN age indefinitely, which is correct and is 07-06's
   checkpoint material.
3. **Watched going red, across a real restart.** `tests/test_cli_watch.py:510`'s *"REQ-16 across a
   RESTART"* section is the idiom: one process writes, a second loads, the ages survive. Plus the
   **real** pre-07 document — the bare-string shape measured on this host today — loaded by the new
   code and asserted to yield unknown ages, no exception, and **unchanged alert behaviour**, which
   is the assertion that actually protects Dan's box. **M32**: `load` defaults a missing stamp to
   `time.time()` — criterion 4's failure in one line, *a restart makes a two-day-old reading look
   fresh*.

Files: `boty/monitor.py`, `boty/pacing.py` (the version comment only), `scripts/mutation_check.py`,
`tests/test_monitor.py`, `tests/test_cli_watch.py`.

### 07-03 — one interval, read the same way by both surfaces (wave 3, autonomous)

~3 tasks.

1. **The number exists.** `boty/pacing.py` — `current_interval(retailer) -> float`, the expression
   `record` computes inline at `pacing.py:242-245` and discards into `due_at`, extracted **and then
   used by `record`**, so the accessor and the schedule cannot drift apart. That is the
   derive-don't-store argument this module already makes twice (`STATE_MAX_AGE_SECONDS`,
   `pacing.py:113-123`) and `models.py:460-462` makes a third time. `skipped_reason` may be
   re-expressed through it — it is the only public method that reads the interval today and it
   returns prose, which is why criterion 3 had no source to compare against.
2. **Both surfaces read it.** `boty/cli.py` — `watch_cycle` threads a per-retailer interval into
   `status.write` **exactly as `paced` is threaded** (`cli.py:299-306` → `status.py:27`), and
   `main`'s check path builds the load-only `Pacer` under § *Finding 8*'s three constraints: never
   `save()`, never passed to `run_once`, absent file means the standing interval and no warning.
   `boty/status.py` publishes it **in the existing `retailers` array**, which already carries
   per-retailer facts — a copy on every watch row would be a second copy that can drift, and this
   file's own `store`/`store_pinned` paragraph is the precedent for publishing the raw fact rather
   than a derived one.
3. **Watched going red, and the two surfaces pinned to each other.** **M33**: `current_interval`
   ignores the backoff and returns the standing interval, so a retailer at seven refusals is judged
   against its config cadence instead of its real one — that is criterion 3's *"derived from the
   retailer's own pacing rather than a fixed clock"* stated as a mutation. Plus a test that
   `boty check` and `watch_cycle` produce the **same** number from the same `pacer-state.json`
   document — PATTERNS § 9's honest hazard asserted rather than hoped, and the reason criterion 3
   is structural rather than cheap.

Files: `boty/pacing.py`, `boty/cli.py`, `boty/status.py`, `scripts/mutation_check.py`,
`tests/test_pacing.py`, `tests/test_status.py`, `tests/test_cli_watch.py`.

### 07-04 — every configured watch has a row (wave 4, autonomous)

~3 tasks. **This is the plan § *Finding 4* exists to justify; its objective paragraph must carry
that argument, not cite it.**

1. **The rows.** `boty/status.py` — `write` takes the configured watches and the remembered ledger
   as keywords threaded the way `paced` is (so `boty.status` keeps importing nothing but
   `boty.models`), and emits one row per configured watch. Rows for watches read this cycle are
   unchanged plus `checked: true`; the rest carry the remembered availability, its stamp (possibly
   `null`) and `checked: false`. **The precedent is in this same file, one level up**:
   `status.py:80-88` already publishes `checked: false` retailers with a reason, for the reason
   stated there — *"the retailer is not healthy (nothing was verified) and not unhealthy (nothing
   failed) — it simply was not asked"*. That paragraph applies word for word to a watch.
2. **A remembered row cannot be mistaken for a fresh one.** `alertable` is **`False` on a
   remembered row, stated not inherited** — an alert decision belongs to a reading somebody took,
   and 07-04 must not let a two-day-old memory authorise a push. `price`, `store`, `detail`,
   `rung`, `extraction` are **absent facts, published as `null`, not defaults** — the
   `null`-never-`0` rule for the third time. `tests/test_status.py`'s exact-keyset assertions
   updated again (§ *Finding 10*), and the row-count assertion is the one that states the change
   plainly: 3 rows for 14 watches today, 14 after.
3. **Watched going red.** **M34**: remembered rows published with `checked: true`, or with the
   remembered stamp dropped — either makes a two-day-old reading indistinguishable from one taken
   this cycle, which is REQ-21's own sentence as a mutation. Anchor on the comprehension or the
   conditional that partitions the rows, never on a key's name in a message.

Files: `boty/status.py`, `boty/cli.py`, `scripts/mutation_check.py`, `tests/test_status.py`,
`tests/test_cli_watch.py`.

### 07-05 — the three surfaces say it (wave 5, autonomous)

~3 tasks.

1. **`boty check`.** `boty/cli.py` — `_age_tag(r, *, now, interval) -> str | None`, module-level,
   appended after `_report`'s `(label, bool)` comprehension exactly as `_store_tag` is and for the
   reason `_store_tag`'s docstring gives (*"the tag's TEXT depends on which of the two values is
   present"*). Forms enumerated in the docstring the way `_store_tag:96-106` enumerates four —
   including **`[age ?]` for an absent stamp**, on `_store_tag`'s own recorded reasoning that
   *"the page did not tell us" is a fact worth printing*. `now` is a **required parameter, never
   read inside** (§ *Finding 6*). `SYMBOL` is untouched and still three-membered, restated at the
   two places `cli.py:126-128` and `_store_tag:108` already restate it. Tests in
   `tests/test_status.py:351-395`'s idiom: one `capsys` test per form, closing with the *did not
   touch the availability symbols* assertion.
2. **The dashboard.** `served/boty/index.html` — an age tag at the established two weights
   (`.tag.age` label / `.tag.age.warn` warning, matching `.tag.store` / `.tag.store.warn`), a
   `title=` sentence on each form, **`fmtAge` reused** (line 80), and the threshold joined from the
   published per-retailer interval — **never `index.html:133`'s file-level 30-minute constant,
   which stays exactly where it is and answers a different question** (§ *Finding 9*, and the
   distinction goes in a comment where the next reader will look). Any new **string** key goes in
   `UNTRUSTED` and through `esc()` on the escape-once-at-the-sink rule (lines 93-98), including
   operator-controlled ones; a numeric stamp through `fmtAge` is not attacker-reachable and the
   plan says which it is rather than leaving it implied. Producer/consumer pair per new key in
   `tests/test_dashboard.py:200-233`'s shape — one test that the page reads the key `status.write`
   publishes, one that the visual weight exists — and the recorded `\b` subtlety at `UNTRUSTED`
   applies to any key that is a prefix of another.
3. **Watched going red, as a pair.** **M35/M36**, the pair `07-PATTERNS.md` § 6 predicts and the
   convention M27/M28 and M29/M30 establish — *one mutation would leave the other half unguarded,
   and the halves fail in opposite directions*: one makes an **absent** stamp render as *now*
   (criterion 2's failure — the reading nobody dated presented as current), one makes a **stale**
   reading render as fresh (criterion 3's failure). Both anchored on the conditional or comparison
   that chooses the form, **never on the tag's text or its `title=` sentence** (§ *Finding 1*),
   with each entry naming which test is expected to catch it and the anchor's occurrences
   pre-counted.

Files: `boty/cli.py`, `served/boty/index.html`, `scripts/mutation_check.py`,
`tests/test_status.py`, `tests/test_dashboard.py`.

### 07-06 — close (wave 6, `autonomous: false`)

~3 tasks. **No code.**

1. **`checkpoint:human-verify` — three measured consequences.** (a) The dashboard goes from **3
   rows to 14**; every watch he has configured appears, and eleven of them will be carrying a
   remembered reading rather than a fresh one on any given cycle. (b) **`state.json` changes shape
   on his box at the next restart**, with the downgrade cost priced from 07-02 rather than
   described. (c) **Walmart's GO Plus + will publish `out_of_stock` with an UNKNOWN age
   indefinitely** (§ *Finding 5*) — honest, and the second time this milestone has put the same
   open question in front of him (`QUESTIONS.md` § 0f). Offer 05-04's and 06-06's shape of answers
   and record whatever comes back **verbatim, including a deferral**.
2. **The gates, measured.** `make verify-offline` run once and its verdict recorded verbatim —
   baseline re-measured for this outline today, run to completion: **exit 0, 778 passed, 26/26
   mutations caught** (§ *Evidence constraint*).
   Mutation count observed rising **from 26** (§ *CORRECTION 1* — not 28, and 07-06 is the plan
   where getting that wrong would be the milestone's own defect) with **each new ident observed
   CAUGHT by ident**. `make verify` is **NOT the gate**; its live verdict is recorded verbatim if
   it is run at all and never required to be green.
3. **The verdicts.** Five criterion verdicts in Phase 3.1's / 4's / 5's / 6's outcome-table format,
   measurement or reason per row, **unmet recorded unmet with its date and reason, nothing
   reworded**. `REQUIREMENTS.md` traceability for REQ-21; `STATE.md` updated — and note where it
   will be seen that `STATE.md`'s `milestone:` key is **machine-read** by
   `tests/test_packaging_metadata.py` against `pyproject.toml`, so editing that line is a
   gate-visible act. Record § *Finding 11*'s disposition and § *CORRECTION 2* as measurement notes
   beside REQ-21's unedited text, on Phase 3.1's format.

Files: `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`,
`docs/retailer-evidence.md` (closing record section).

---

## Why every wave is serial — and this time the files alone settle it

**File ownership, measured. Unlike Phase 6, NO plan here owns a disjoint set:**

| File | 07-01 | 07-02 | 07-03 | 07-04 | 07-05 | 07-06 |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| `boty/models.py` | ● | | | | | |
| `boty/retailers.py` | ● | | | | | |
| `boty/monitor.py` | | ● | | | | |
| `boty/pacing.py` | | ● *(comment)* | ● | | | |
| `boty/status.py` | ● | | ● | ● | | |
| `boty/cli.py` | | | ● | ● | ● | |
| `served/boty/index.html` | | | | | ● | |
| `scripts/mutation_check.py` | ● | ● | ● | ● | ● | |
| `tests/test_models.py` | ● | | | | | |
| `tests/test_retailers.py` | ● | | | | | |
| `tests/test_monitor.py` | | ● | | | | |
| `tests/test_pacing.py` | | | ● | | | |
| `tests/test_status.py` | ● | | ● | ● | ● | |
| `tests/test_cli_watch.py` | | ● | ● | ● | | |
| `tests/test_dashboard.py` | | | | | ● | |
| `.planning/*`, `docs/retailer-evidence.md` | | | | | | ● |

**Five genuine collisions, and each one is a real dependency rather than caution:**

- `scripts/mutation_check.py` — all five code plans. Unavoidable: this phase's own rule is that
  each plan ships its gate in its own commit.
- `boty/status.py` — 07-01 (the key), 07-03 (the interval), 07-04 (the rows). Three plans editing
  one payload; the order is *what a row carries* → *what a retailer carries* → *which rows exist*.
- `boty/cli.py` — 07-03 (the check-path pacer and the threading), 07-04 (the ledger threading),
  07-05 (`_age_tag`).
- `tests/test_status.py` — four plans, and § *Finding 10*'s exact-keyset assertion is edited by
  three of them.
- `boty/pacing.py` — 07-02 (the version comment its own change falsifies) and 07-03 (the accessor).

**Beyond the files, Phase 6's mechanism still holds and is inherited rather than re-derived.**
Every plan's acceptance is `make verify-offline`, a **whole-tree** gate whose mutation stage is not
a read: `build_sandbox()` copies every `SANDBOX_CONTENTS` entry out of the **live working tree**
once per mutation plus a baseline — **27 snapshots at M26 today, 33 at M32 by 07-06** — and
`tests/` is in `SANDBOX_CONTENTS`. A second agent writing any test file during that window lands in
some snapshots and not others; a file that references a helper the next Write has not added yet
fails collection at the **baseline**, which `run_baseline` turns into a `HarnessError` reported as
a mutation-stage failure with no attribution to the plan that caused it.

**So Phase 6's forward-looking note does not apply here.** It recorded that 06-03, 06-04 and 06-05
were the first plans in this project that *could* have run concurrently if the gate were per-plan.
Nothing in this phase could: the file table alone forbids it, before the gate argument is reached.

---

## Evidence constraint (binds every plan's `<verify>`)

- **`make verify-offline` is the gate.** Baseline re-measured for this outline on 2026-08-13 at
  `dbc9d49`, working tree clean, run to completion rather than collected:

  ```
  identity check: PASS — 208 file(s), no host identity found
  778 passed in 10.81s
  mutation check: 26/26 mutations caught
  VERIFY: PASS (OFFLINE — live controls were NOT run, ...)
  EXIT=0
  ```

  mypy clean over 18 source files, 11 fixtures all `ok`, control check SKIPPED (`--offline`).
  **`26/26` is caught over the WHOLE registry** — it is not 26 of 28 (§ *CORRECTION 1*). Every plan
  asserts against this target, and every plan records the ratio's numerator and denominator rather
  than the word "green".
- **No plan's acceptance may depend on a live retailer read, and no plan plans live probing.**
  Politeness is a hard constraint and three of six retailers are refusing us as of this morning.
  Every red-watch in this phase is offline: constructed `Result`s, constructed persisted documents
  built from `time.time() - age` (`tests/test_pacing.py:501-505`'s method), the **real** pre-07
  `state.json` shape, and mutations inside the harness's own sandbox.
- The live `make verify` verdict is **recorded** at close if it is run, never **required** to be
  green, and never trimmed. Its three failure classes are v0.2's carried debt and none of them is
  this phase's to fix.
- `conftest.py`'s `NetworkBlocked` derives from `BaseException` on purpose — an `Exception` guard is
  swallowed by `boty.fetch` and downgraded into `Availability.UNKNOWN`, the most common assertion
  in this suite. **07-01 drives four adapters through their error arms and is the plan most exposed
  to this**; it monkeypatches `retailers.get` on `tests/test_retailers.py:38-45`'s precedent.
- **No new anchor may be literal-coupled** (§ *Finding 1*). Two anchors drifted on 2026-08-13 when
  the version literal moved, and this phase's two prose-adjacent surfaces (a CLI tag, a dashboard
  `title=` sentence) are exactly where the same mistake would be made again.
- **Never write a real store number or host identity into a tracked file.** `identity_check` runs
  at commit time and has rejected a commit in this repo over a four-digit literal in a test
  comment. This phase publishes epoch seconds and intervals — but **07-04 republishes `store` and
  `store_pinned` on carried-forward rows**, which is the one place it widens what a file contains,
  and `served/boty/status.json` is gitignored (`.gitignore:31`) rather than tracked.

---

## Multi-source coverage audit

Every item below is covered by a plan. **No item is deferred, simplified, or reduced to a "v1".**

### GOAL — ROADMAP phase goal

> *"Every reading says when it was taken, and a reading too old to trust is shown as stale rather
> than as fact — or says it does not know."*

| Item | Covered by |
|---|---|
| *"Every reading says when it was taken"* | 07-01 (all 20 construction sites, AST-complete) + 07-02 (it survives the process) |
| *"a reading too old to trust"* — *too old* needs a threshold | 07-03 (the retailer's own current interval, one number, both surfaces) |
| *"is shown as stale rather than as fact"* — *shown* needs a row to show | 07-04 (a row exists for every watch) + 07-05 (all three surfaces render it) |
| *"or says it does not know"* | 07-01 (the datum is `None`, never `now`), 07-02 (a stamp-less document loads as unknown, never `now`), 07-05 (`[age ?]` and the dashboard's warn weight) |

### Success criteria (ROADMAP numbering 1–5)

| # | Criterion | Covered by |
|---|---|---|
| 1 | Every `Result` records when it was read, and that time is published per watch in `status.json` | **07-01** |
| 2 | A reading with no recorded time is shown as UNKNOWN age, never as current — watched going red | **07-01** (the datum + M31) and **07-05** (the rendering + M35) |
| 3 | A reading older than its retailer's current interval is presented as stale in `status.json`, `boty check` and the dashboard, derived from the retailer's own pacing rather than a fixed clock | **07-03** (the interval, M33), **07-04** (a `status.json` row that can be old, M34), **07-05** (the two renderings, M36) |
| 4 | The age survives a service restart | **07-02** (M32) |
| 5 | `make verify-offline` exits 0, and every gate this phase adds has been watched going red | **all five carry their own red-watch**; **07-06** records the ratio and each new ident CAUGHT |

**Criterion 3 is the one that spans three plans, and § *Finding 4* is why.** Recorded here so its
spread is read as structure rather than as dilution.

### REQ — `phase_req_ids`

| ID | Covered by | Closed by |
|---|---|---|
| REQ-21 | 07-01, 07-02, 07-03, 07-04, 07-05, 07-06 | **07-06** |

**REQ-21 appears in every plan's `requirements` frontmatter.** Following 04-05's, 05-01's and
06-06's precedent, **a requirement is not marked complete by the plan that ships its code**; 07-06
closes it by measuring what landed.

### RESEARCH

Not applicable — research is disabled for this project and no `07-RESEARCH.md` exists.
`07-PATTERNS.md` served that role and is fully consumed above, including the place it corrects
CONTEXT (the mutation registry's *set*), the place this outline corrects **it** (§ *CORRECTION 1*,
the registry's *count*), the decision it explicitly handed to the planner (§ *CORRECTION 3*, the
time seam), and the six places this outline measures past it (§ *Findings 4, 5, 8, 9, 10, 11*).

### CONTEXT — locked decisions

| Decision | Covered by |
|---|---|
| **Staleness is measured against the retailer's own current interval, not a fixed clock** | 07-03 builds the number from `Pacer`; 07-05 renders against it and is explicitly forbidden from borrowing `index.html`'s existing fixed constant (§ *Finding 9*) |
| **Where no time was recorded, the age is UNKNOWN — never "now"** | 07-01 (`None` at every non-read arm, M31), 07-02 (a stamp-less document loads unknown, M32), 07-05 (`[age ?]`, M35) |
| A gate must be watched going red before it is trusted | six new mutations across five plans, each named with its expected killer; 07-06 records each CAUGHT |
| Never amend a success criterion to make it meetable | 07-06 — and applied in advance to § *CORRECTION 2*: REQ-21's *"the page presents both as current"* is measured one direction off and is **recorded beside the unedited text**, never rewritten |
| UNKNOWN is never a verdict | 07-01's asymmetry paragraph — staleness touches neither `Availability` nor `alertable`, on `models.py:517-522` and on § *Finding 7*'s mechanical argument |
| Every criterion verified by something executable | all six — `<verify>` against `make verify-offline` |
| Never write a real store number or host identity | all six; 07-04 is the one that widens a published file and it publishes to a **gitignored** path |
| Politeness is a hard constraint — no live probing to test this | honoured; § *Evidence constraint* |
| Out of scope: anything about *what* a reading says (v0.2, complete) | honoured — no plan touches `parse.py`, `notify.py`, the ceiling, the shipping readers or the store guards. 07-01 enters `retailers.py` for the stamp thread-through only |
| Out of scope: the live `make verify` classes and fixture re-capture | honoured — recorded at close, not fixed |

**Claude's Discretion, per CONTEXT** — *where the stamp is carried on `Result`* (07-01: a field
declared last, on the four-times-worn groove), *how it is persisted* (07-02: extending
`state.json`, shape-tolerant, with a second document rejected on `pacing.py`'s own argument),
*the exact rendering in `boty check` and the dashboard* (07-05), and *how "stale" is expressed in
`status.json`* (07-03 + 07-04: **raw facts published, staleness derived at render time**, settled
in § *Finding 7* on this repository's own recorded lesson about bounds that cannot bind).

**Deferred, correctly absent from every plan:** `QUESTIONS.md` § 0f (`WALMART_STORE_ID` — this
phase *surfaces* its consequence at 07-06's checkpoint and does not close it); `QUESTIONS.md` § 0e;
the live `make verify` failure classes and fixture re-capture; the `.planning/` contents gate and
its two smaller candidates. None appears in any plan above.

---

## Threat model seeds

`workflow.security_enforcement` is on, ASVS L1, block on `high`. Each PLAN.md carries its own
`<threat_model>`; these are the boundaries and threats established during outlining, for the
per-plan writer to sharpen rather than rediscover.

**Trust boundaries:** a retailer's response → `boty.retailers` → a stamped `Result` → a claim about
when something was true; a persisted document on the host (`state.json`, `pacer-state.json`) → a
process that trusts it after a restart; `status.json` → HTTP → the dashboard behind Mission
Control's proxy → `innerHTML` on that origin; `boty check` → `pacer-state.json`, a file the daemon
is concurrently writing.

| Threat ID | Category | Component | Disposition | Mitigation |
|---|---|---|---|---|
| T-07-01 | Repudiation | a reading claiming an age nobody recorded | mitigate | **The phase's own subject.** Three independent ways to manufacture a false age, each closed and each mutated: stamping a non-reading (07-01, M31), defaulting a missing stamp on load (07-02, M32), and publishing a memory as if it were taken this cycle (07-04, M34). The governing rule is `pacing.py:196-199`'s, quoted in § *Finding 3*. |
| T-07-02 | Tampering | a stamp read back off disk | mitigate | `state.json` is a plain file on the host and a stamp is a number a process will trust. Validate with a **both-ended** bound on `pacing.py:335-350`'s worked shape — including the `isinstance(x, bool)` exclusion (bool is an int subclass) and `continue`-rather-than-guess — so a value in the future, a value past the cap, a string or a `True` is discarded rather than believed. **07-02.** |
| T-07-03 | Tampering | `boty check` and the daemon writing one `pacer-state.json` | mitigate | `boty check` is routinely run while the service is running. The `Pacer` it constructs is **load-only and never `save()`s**, and it is never passed to `run_once`. Two writers to one document is the contradiction `pacing.py`'s own argument against a second file exists to prevent, pointed the other way. **07-03**, § *Finding 8*. |
| T-07-04 | Tampering / XSS | a new interpolated value on the dashboard | mitigate | Escape once, at the sink, applied to **every** interpolated value including operator-controlled ones (`index.html:93-98`) — *"a rule of the form 'these three but not those two' does not survive the next edit to this template."* A numeric stamp through `fmtAge` is not attacker-reachable and the plan states which class each new key is in; any string key goes in `UNTRUSTED` and through `esc()`. **07-05.** |
| T-07-05 | Information disclosure | `status.json` served over HTTP | mitigate | 07-04 republishes `store` and `store_pinned` on carried-forward rows — the one place this phase widens what the file contains. Nothing new is host-identifying (epoch seconds, intervals), the file is **gitignored** (`.gitignore:31`) rather than tracked, and `identity_check` still runs at commit time over what is. **07-04.** |
| T-07-06 | Denial of service | the mutation harness | accept, with the reason | Six new mutations mean six more full `build_sandbox()` copies per `make verify` — 27 snapshots today, 33 by 07-06. Accepted and recorded rather than silently paid, as 04-04's git-index cost and 06-07's were. No Makefile stage is added; every new gate arrives as a pytest test through `make test`. |
| T-07-07 | Tampering | a gate that cannot bind | mitigate | **This phase's own highest-severity failure mode, because it is the defect it exists to fix wearing the fix's clothes.** Three concrete forms, each structurally prevented: a `stale` flag computed at write time (§ *Finding 7*); a staleness rule applied only to rows that are fresh by construction (§ *Finding 4* → 07-04); and a `boty check` age tag whose stale branch is unreachable (§ *Finding 4* → 07-03 + 07-04). Every one of the six mutations is required to be observed **CAUGHT by ident**, and 07-06 records them. |
| T-07-08 | Tampering | an existing `state.json` broken by the shape change | mitigate | Dan's file is 13 bare strings and his daemon runs this tree (editable install), so the shape change reaches disk at the next restart. The pre-07 shape must load without exception and with **unchanged alert behaviour** — asserted against the real shape, not a hand-typed approximation (07-02, task 3). The **downgrade** direction is the residual: an older binary reading a newer file re-alerts once per watch. Priced in the code rather than discovered. |
| T-07-SC | Tampering | npm/pip/cargo installs | mitigate | **No new dependency is expected.** § *Finding 6* settles the one place a package would have been reached for — a clock-freezing library — and settles it as *not needed*, which also honours `REQUIREMENTS.md` § Non-Functional's small-dependency-surface rule. Research is disabled, so there is no `## Package Legitimacy Audit` and the fallback policy applies: if any plan finds it needs a package, every package is `[ASSUMED]` and a `<task type="checkpoint:human-verify" gate="blocking-human">` verifying it on `pypi.org/project` must precede the install. Not auto-approvable; `workflow.auto_advance` does not apply. |

---

## Metadata

**Sources consumed:** `.planning/STATE.md`, `.planning/ROADMAP.md` (§ *Milestone v0.3 … Phase
Details*, § Phase 7), `.planning/REQUIREMENTS.md` (REQ-21), `07-CONTEXT.md`, `07-PATTERNS.md`,
`.planning/seeds/a-reading-does-not-carry-its-age.md`, `06-PLAN-OUTLINE.md` (house style),
`.planning/milestones/v0.2-REQUIREMENTS.md` (REQ-14 … REQ-20 bodies, for § *Finding 11*).

**Tree work done during outlining (2026-08-13, at `dbc9d49`, working tree clean):**
`grep -c 'ident="M' scripts/mutation_check.py` and every ident listed in file order (26, M1–M20 ∪
M25–M30); `mutation_check.py:660-700` read for the pair convention, the M21–M24 gap statement and
M29/M30's anchors; every `Result(` in `boty/retailers.py` located and each one's arm classified by
reading `check_bestbuy_api:826-870` and both browser adapters' `except` arms; `boty/models.py`
read at the `shipping` declaration, `delivered_total`, `degraded` and the `Availability` rule;
`boty/status.py` read whole at the payload and the row comprehension; `boty/monitor.py` `State` and
`run_once`'s pacer filter; `boty/pacing.py` at `STATE_VERSION`, `_RetailerState`, `record`'s inline
backoff expression and `skipped_reason`; `boty/cli.py` at `_store_tag`, `_report`, `watch_cycle`'s
`paced` threading, `watch_loop`'s pacer construction and `main`'s check path;
`served/boty/index.html` at the tag CSS, `esc`, `storeTag`, `fmtAge` and the banner threshold;
`tests/test_status.py:170-200` (the exact-keyset assertion), `tests/test_dashboard.py`'s
`UNTRUSTED` and REQ-14 producer/consumer pair, `tests/test_cli_watch.py:768-790`;
**the live `served/boty/status.json` parsed** (3 watch rows against 14 configured watches; 4 of 6
retailers `checked: false`); **the live `state.json` parsed** (13 entries, all bare strings, zero
per-entry fields — the seed's probe re-run and still `[]`); **the live `pacer-state.json` parsed**
(version 2, three retailers carrying refusals); `git check-ignore -v served/boty/status.json`;
`grep -c "retailer:" config/products.yaml` (14); `pytest tests/ --collect-only` (**778**);
`grep -rn "REQ-21"` across the tree and across `.planning/milestones/` and `.planning/phases/06-*/`;
and **`make verify-offline` run to completion** for the baseline in § *Evidence constraint*.

**No project `CLAUDE.md` and no `.claude/skills/` exist in this repo** — the governing conventions
are `07-PATTERNS.md` § *Shared Patterns* and the standing constraints in `07-CONTEXT.md`
§ *The project's standing constraints*.
