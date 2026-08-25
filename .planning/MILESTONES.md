# Milestones: bot-y

Historical record. One entry per closed milestone, newest first.

**v0.3 IS TAGGED as of 2026-08-25 — the first tag in this project's history — and no
milestone has ever been published.** Tagging and publishing were one rule here until that
date; they are now two, and this file distinguishes them per entry.

> **The paragraph this replaces stood from the file's creation until 2026-08-25 and is kept
> verbatim, because it recorded a decision and the decision is what changed:** *"**No
> milestone in this project has ever been tagged or published.** `git tag -l` → 0; `git
> ls-remote --tags origin` → 0 refs; PyPI 404. That is deliberate, and as of 2026-08-12 it
> is an explicit decision rather than a deferral: **Dan chose no tag** at the v0.2 deploy
> (`4609d95`), matching v1.0.0."*
>
> **What reversed it**, Dan, 2026-08-25, verbatim: *"shipping is fine. correct it so that it
> can ship. just not a 1.0 release."* And, on the second half: *"forget the pypi part, just
> get it to github."* So the tag half is reversed and the publish half is not — PyPI stays
> 404 by the same 2026-08-06 reason (*"I wouldn't publish it without more real testing"*),
> and `Development Status :: 4 - Beta` stays with it.

---

## v0.3 — Say When You Measured It

**Closed:** 2026-08-19 · **Scoped:** 2026-08-13 (`d837676`) · **DEPLOYED 2026-08-20 07:43:22 CDT**
· **TAGGED `v0.3.0` 2026-08-25**
**Status:** ✅ Complete in the tree, **RUNNING** since 2026-08-20, **TAGGED** since
2026-08-25 — and still **NOT published**

> **`NOT tagged` was true in this line from the close until 2026-08-25**, and is superseded
> rather than wrong; the reversal that moved it is recorded at the top of this file. Note
> that all three states are now separate and the milestone is in a different one of each:
> complete-in-the-tree (2026-08-19), running-on-the-daemon (2026-08-20), tagged-on-GitHub
> (2026-08-25), unpublished (still). "Shipped" on its own has stopped being a useful word
> for this milestone — say which one you mean.

> **The line above used to read "Complete in the tree — NOT deployed", and that was true from
> 2026-08-13 until 2026-08-20.** It is recorded rather than edited away because "archived is not
> shipped" was the standing fact of this project across three milestones, and v0.2's material
> still says it of itself accurately. **Dan authorised the restart on 2026-08-20** and it was
> performed: `sudo systemctl restart boty`, PID 547119 → **548295**, `NRestarts=0`, no unit
> changes. **What the deploy actually did, measured on this host rather than predicted:**
> `state.json` migrated 13 → 13 entries with **zero lost and every availability byte-identical**,
> each bare pre-07 string becoming `{availability, read_at}`; `served/boty/status.json` went from
> **3 watch rows to 13**, all 13 carrying `read_at` and `checked`, and the 6 retailer rows gaining
> a real `current_interval_seconds` (gamestop 14400, walmart 21600 — both on backoff — amazon 1800,
> target 600, bestbuy 300, nintendo 300). The page was **looked at**, not inferred: five rows carry
> real ages (`1M AGO`, `80S AGO`, `78S AGO`, `71S AGO`, `68S AGO`), eight carry amber **`AGE ?`**,
> zero console errors. `walmart:Pokémon GO Plus +` — the frozen entry Dan was shown at 07-06's
> checkpoint — renders `out_of_stock · AGE ?` exactly as the closing record said it would, and
> will until a store is pinned. **The pin remains deferred** (`QUESTIONS.md` § 0f, unchanged).
> Pre-restart copies of all three state files were taken first.
**Phases:** 7 (one phase) · **Plans:** 7 (six planned; 07-07 appended after the close) ·
**Requirements:** 1 (REQ-21) · **Commits:** 72 from `b10df8c` · **Diff:** 41 files,
+18,146 / −104
**Gate:** `make verify-offline` EXIT=0 — **884 passed / 0 skipped, 34/34 mutations, survivors
0**, mypy clean over 18 source files, identity PASS over 225 files. At milestone start: 778
passed, 26/26.
**Audit:** `tech_debt` — no blockers, no unsatisfied requirements, no broken flows, no orphans;
six residuals carried forward.

**Delivered.** v0.2 was *say only what you measured*; this is its unfinished half. **A reading
with no age is a claim about the past presented as the present** — the same shape as *"the
detector is probably broken"*, except the unestablished thing is *when*. Scoped from a question
the system could not answer: Dan asked when the Amazon and Walmart GO Plus + watches had last
been read, and there was no recorded answer — Amazon's was reconstructible only from refusal
history, and **Walmart's could not be established at all**, because a restart had zeroed the
counter that held the evidence.

**Key accomplishments:**

1. `Result.read_at` stated at **every** construction site — not inherited from a default — with
   completeness proved by a **static AST gate over the source**, so an arm added later cannot
   silently omit it. An arm that read nothing carries `null`, **never `0`** (M31).
2. The age **survives the process**: `monitor.State` became a dated per-watch ledger that loads
   the real pre-07 document on this disk — 13 bare strings, no version field — preserving every
   availability, inventing no age, leaving alert behaviour byte-for-byte unchanged (M32).
3. The retailer's current cadence is **one number both surfaces read**, with `record` computing
   its own wait *through* it so the number published and the schedule kept cannot drift (M33).
4. **One row per CONFIGURED watch.** The sharpest finding of the milestone: a paced-out watch did
   not have a *stale* row — **it had no row at all**, measured at 3 published for 13 configured.
   A staleness rule over only the rows that exist would have been a bound that cannot bind
   (M34/M35).
5. Four rendered age forms on both consumers, each judged against that published per-retailer
   cadence and never against the page's 30-minute banner constant (M36/M37 — the first mutation
   in this registry under `served/`).
6. **No `stale` key was added to `status.json`**, deliberately: a boolean written at write time
   says `false` for exactly the interval during which it becomes true.

**The five facts this milestone must not be read without:**

1. **NONE OF IT IS RUNNING, and the running code is older than the milestone.** `boty watch`
   `MainPID=547119`, started **2026-08-12 17:28:29** — ~15 hours *before* this milestone's first
   commit — so the deployed daemon has never at any moment held a line of this code. Its
   `status.json` carries none of the four new keys and publishes 10 rows for 13 configured
   watches; `state.json` still holds 13 bare pre-07 strings.
2. **The restart is verified SAFE BY EXECUTION**, not argued: run against copies of all three
   live pre-phase documents — 13/13 availabilities survive, 0 ages invented, the pacer document
   round-trips, the real `config/products.yaml` does not trip the new config guard. Rollback cost
   bounded at 2 duplicate restock pushes. Deferred by Dan twice (`QUESTIONS.md` § 0f, 2026-08-10
   and 2026-08-17).
3. **Criterion 3 is MET IN PART by Dan's explicit decision (2026-08-17)** — `status.json`
   publishes the *ingredients* of a staleness verdict and no verdict. Not an oversight, not a
   TODO, not queued work. **No key was added to make the row read MET.**
4. **Criterion 5's qualification is NOT discharged.** The join test was watched red 5/5 on
   2026-08-19, establishing non-vacuity — **but after the fact, against an implementation that
   already existed. The original RED was never observed and TDD ordering was not followed.**
   *The gate bites* and *the gate came first* are two claims; only the first is established.
5. **A post-close code review found 1 Critical + 8 Warnings; all nine fixed.** The Critical was a
   **reproduced** XSS sink — `served/boty/index.html` interpolated `w.availability` into a
   `class="dot ${...}"` attribute unescaped, reachable because 07-04 publishes any string from
   `state.json`, **and the gate that should have caught it named a sibling field and omitted this
   one**. Three Info findings were recorded and **not** fixed.

**No criterion text was amended at any point in the phase**, asserted by command: 34 criterion
bodies at baseline, 34 at close, none added or removed, with REQ-21's own body byte-identical.

**Known deferred items at close: 9** (see `.planning/STATE.md` § *Deferred at the v0.3 milestone
close*) — the restart, the store number, the three Info findings, the audit's six residuals, the
`gsd-tools` state-writer workaround, `QUESTIONS.md` § 0e's three residues, five open phase
verifications (four of them v1.0.0's), and the unowned live-`make verify` classes.

**Archive:** [`milestones/v0.3-ROADMAP.md`](milestones/v0.3-ROADMAP.md) ·
[`milestones/v0.3-REQUIREMENTS.md`](milestones/v0.3-REQUIREMENTS.md) ·
[`milestones/v0.3-MILESTONE-AUDIT.md`](milestones/v0.3-MILESTONE-AUDIT.md)

---

## v0.2 — Say Only What You Measured

**Closed:** 2026-08-11 · **Scoped:** 2026-08-10 (`79e0c84`)
**Status:** ✅ Complete **in the tree** — **NOT deployed, NOT tagged, NOT published**
**Phases:** 5–6 · **Plans:** 11 (Phase 5: 4; Phase 6: 7, one inserted mid-phase at Dan's
direction) · **Commits:** 84 · **Diff:** 75 files, +30,483 / −568
**Gate:** `make verify-offline` exit 0 — **769 passed, 24/24 mutations**, identity PASS over
201 files. At milestone start: 531 passed, 8/8.
**Audit:** `passed` — opened `gaps_found` on one item, closed at `0d6d1b8`.

**Delivered.** One shape, found six times in four days of live operation after Phase 4: the
system stating something it had not established. Phase 5 fixed what a *product reading* means
— store pinning with no default, alert text that names only measured causes, backoff that
survives a restart. Phase 6 put gates under *published claims* — the delivered-total ceiling,
the README matrix bound to the code, workflow-file and `CHANGELOG.md` content gates, version
agreement. Every new gate was watched going red before it was trusted.

**Key accomplishments:**

1. A Walmart reading names its store, and an unpinned or unexpected one is UNKNOWN, never a
   verdict (M9/M10).
2. Four alert strings that named unmeasured causes withdrawn behind an `ast` gate paired with
   a `CAUSE_UNKNOWN` partition, so it cannot be satisfied by deleting every explanation.
3. Backoff and paging memory persist across a restart — and the measurement found "pushed
   once" was already false *within* one process (2 pushes in 120 cycles).
4. The price ceiling measures the delivered total wherever shipping can be read, and refuses
   to guess one where it cannot. **Reversed in part by Dan on 2026-08-11.**
5. The README `Rung` cell bound to the code across both joins, statically by AST,
   two-directionally — a claim that could not previously go red.
6. `CHANGELOG.md` and `.github/workflows/` gated on their **contents**, each watched red
   against the byte-exact document that actually shipped.
7. `pyproject.toml` rolled `1.0.0` → **`0.2.0`** as *the correction, not a bump*, bound to
   four records with `pyproject` authoritative and compared component-wise.

**The four facts this milestone must not be read without:**

1. **None of it is running.** Dan answered `defer` on 2026-08-10; `boty.service` still runs
   2026-08-04 code (`MainPID=3059142`) and still makes every claim v0.2 fixed. `boty` is an
   **editable install**, so `sudo systemctl restart boty` deploys REQ-15, REQ-16 and REQ-17
   today with no store pin. Only REQ-14 additionally needs `WALMART_STORE_ID`.
2. **REQ-17 was revised by Dan mid-milestone**, knowingly reopening the hole it was written
   to close: *"where we don't know just send it … it's worse to feel like you 'missed out'."*
   The original text stands unedited beside the revision; Phase 6 criterion 1 is recorded
   **MET IN PART**, not rounded up.
3. **v1.0.0 remains open and untagged**, and v0.2 is the correction of that numbering — safe
   only because publishing was deferred and nothing was ever tagged or uploaded. v1.0.0 was
   **not archived** and did not ship.
4. **The recurring defect kept catching itself:** leaked agent tool-call markup reached a
   *committed* file inside this milestone's own planning (`06-07-SUMMARY.md` at `a71e79b`),
   one day after the gate for that byte-shape landed. No gate this repo ships covers
   `.planning/`. Three candidate rules are logged and unbuilt.

**Known deferred items at close: 9** (see `.planning/STATE.md` § *Deferred Items*) — the
deploy, the store number, five open phase verifications (four of them v1.0.0's),
`QUESTIONS.md` § 0e, and the audit's seven tech-debt items.

**Archive:** [`milestones/v0.2-ROADMAP.md`](milestones/v0.2-ROADMAP.md) ·
[`milestones/v0.2-REQUIREMENTS.md`](milestones/v0.2-REQUIREMENTS.md) ·
[`milestones/v0.2-MILESTONE-AUDIT.md`](milestones/v0.2-MILESTONE-AUDIT.md)

**Note added 2026-08-19 at the v0.3 close, beside the entry above and not over it: v0.2 WENT ON
THE WIRE on 2026-08-12** (`4609d95`), at Dan's direction, one day after this entry was written —
so its `Status` line and its fact 1 are true as of the close and false as of now. Measured back
off `status.json` after a fresh cycle rather than assumed: `store` and `store_pinned` present on
every watch row, both Walmart rows `unknown` / `alertable=False` (the 2026-08-09 defect was live
until that restart), `probably broken` no longer published by any retailer, and
`pacer-state.json` on disk with the backoff outliving the process for the first time.
**REQ-14 remains the exception** — Walmart cannot alert on the GO Plus + until
`WALMART_STORE_ID` is set, which it still is not (measured as a count, `0`). The entry is left
unedited because a closing record is corrected beside itself, not over itself.

---

## v1.0.0 — open, untagged, NOT archived

Listed here only so its absence is not read as an oversight. Phases 1–4 and 3.1 are all
complete, but the milestone's own definition of done includes *"Dan has successfully bought a
Pokémon GO Plus +"* — a market condition, not a work item — and its audit
(`.planning/v1.0.0-MILESTONE-AUDIT.md`) recommended against tagging it shipped. Two of its
Phase 4 criteria (`pip install bot-y` from PyPI; a tagged `v1.0.0` release) were **descoped**
on 2026-08-07, not met and not reworded. Its phases and details remain in
`.planning/ROADMAP.md`.
