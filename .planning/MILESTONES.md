# Milestones: bot-y

Historical record. One entry per closed milestone, newest first.

**No milestone in this project has ever been tagged or published.** `git tag -l` → 0;
`git ls-remote --tags origin` → 0 refs; PyPI 404. That is deliberate.

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

---

## v1.0.0 — open, untagged, NOT archived

Listed here only so its absence is not read as an oversight. Phases 1–4 and 3.1 are all
complete, but the milestone's own definition of done includes *"Dan has successfully bought a
Pokémon GO Plus +"* — a market condition, not a work item — and its audit
(`.planning/v1.0.0-MILESTONE-AUDIT.md`) recommended against tagging it shipped. Two of its
Phase 4 criteria (`pip install bot-y` from PyPI; a tagged `v1.0.0` release) were **descoped**
on 2026-08-07, not met and not reworded. Its phases and details remain in
`.planning/ROADMAP.md`.
