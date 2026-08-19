# Phase 5: A Reading Means Something — Plan Outline

**Drafted:** 2026-08-10
**Granularity:** coarse
**Phase requirements:** REQ-14, REQ-15, REQ-16
**Plans:** 4, in 4 waves — every wave serial, on measured file contention (§ *Why every wave is serial*)

## Plans

| Plan ID | Objective | Wave | Depends On | Requirements |
|---|---|---|---|---|
| 05-01 | **The store becomes a fact that exists and is visible.** `Watch.store_id` lands as a per-watch pin in `config/products.yaml` with no default; `Result.store` records which store the page said answered, read off a pinned `__NEXT_DATA__` path; both reach `status.json`, `boty check` output and the dashboard row. No verdict changes in this plan — it only makes the fact recordable and readable. Also closes the leak hole this phase opens: `scripts/identity_check.py` is blind to the `store_id:` YAML spelling (measured, § *Finding 2*). | 1 | — | REQ-14 |
| 05-02 | **An unpinned or unexpected store is UNKNOWN, never a verdict — watched going red — and no alert names a cause the code did not measure.** Two distinct guards in `check_html` (config gap vs. wrong store), a third `assess_health` arm for the unpinned case, the refusal arm's *"we are asking too often"* rate diagnosis withdrawn, the else arm's *"the detector is probably broken"* narrowed to what it established, `notify`'s hardcoded "detector problem" title fixed, and a mutation per guard anchored on the verdict rather than the prose. | 2 | 05-01 | REQ-14, REQ-15 |
| 05-03 | **The backoff survives a restart, so "pushed once after the cap" means once.** Persist `refusals` plus a wall-clock stamp and *never* `due_at` (§ *Finding 3*); rewrite `pacing.py`'s "deliberately in-memory" paragraph with its reversal argued in place and the stale-file objection answered; wire load/save into `watch_loop` without rebuilding the pacer per cycle; pin REQ-16's three clauses across a simulated restart. Criteria 5 and 6 are one change. | 3 | 05-01, 05-02 | REQ-16 |
| 05-04 | **Close.** Dan supplies the real store pin (blocking checkpoint — bot-y never guesses where the user lives), the service is restarted onto the new code, `make verify` is run and its verdict recorded verbatim including a FAIL, the mutation count is observed rising, and six criterion verdicts land in the ROADMAP with measurements — unmet recorded unmet, never reworded. | 4 | 05-01, 05-02, 05-03 | REQ-14, REQ-15, REQ-16 |

**Plan numbers are creation order; waves are execution order.** Here they coincide.

---

## Findings from the tree that must shape the plans

These four were measured during outlining, not inferred. Two of them correct
`05-PATTERNS.md`.

### Finding 1 — `"0"` in the Walmart fixtures is a REDACTION ARTIFACT, not a Walmart sentinel

`05-PATTERNS.md` reasons that `storeId` = `"0"` appearing 15 times "is very
likely Walmart's 'no store assigned' sentinel, which is precisely the unpinned
condition this phase exists to catch." **That is wrong, and building on it would
invent a fact about Walmart out of this repo's own scrub.**

Measured: `git show 8dec2e0 -- tests/fixtures/walmart/milk-control.html` replaces
`"storeId":"<n>"` × 11, `"storeId":"<n>"}]` × 3, `"storeIds":["<n>"]` and
`storeId=<n>` inside ad hrefs with `"0"` throughout. The pre-redaction capture
(`95f84a6`) carries a real three-digit store number 14 times over. `"0"` is in
`identity_check.py`'s `allowed` redaction vocabulary alongside `"00000"` and
`"XX"` — it is a placeholder this repo writes on purpose.

Consequences the plans must honour:

- **`boty/parse.py` must not special-case `"0"`.** It is not a sentinel; it is
  our own placeholder. A `if store == "0": return None` branch would be a claim
  about Walmart that nothing measured.
- Both shipped fixtures therefore read store `"0"`. That is still perfectly good
  test material — pin `store_id: "0"` for the match case, anything else for the
  mismatch case, absent for the unpinned case — but the tests must say *why*
  `"0"` is the fixture's value, or the next reader will think it is Walmart's.
- The paired `.json` provenance notes (`tests/fixtures/walmart/*.json`) should
  record that the store value is redacted. Phase 3.1's own lesson was that the
  `.json` notes are inside the guard's scope and were the thing that leaked.

### Finding 2 — `identity_check.py` cannot see `store_id:` in YAML. Measured.

The guard runs at commit time over **every tracked file**, and `config/products.yaml`
is tracked and public. Its two store rules are keyed to shapes this phase does
not use:

```
# `12345` is a placeholder, not a store number. Output of
# `identity_check._identity_leaks`, run 2026-08-10:
config/products.yaml:  '    store_id: 12345\n'   -> []                       # PASSES
config/products.yaml:  '  store_id: "12345"\n'   -> []                       # PASSES
config/products.yaml:  'store_id=12345'          -> ['store number in a URL'] # caught
config/products.yaml:  '"storeId":"12345"'       -> ['store number']          # caught
```

So the exact key REQ-14 introduces walks straight through the gate that exists
to stop store numbers entering this repo. This is the *"keyed to the spelling I
had just seen rather than to the class"* defect `3bd1663` spent a re-verification
round on, one turn later, at the one key that made it likely.

**05-01 owns closing it**, and per house style the widened rule must be watched
going red against a real `store_id:` line before it is trusted.

This also forces 05-01 to *decide*, not assume, how the real pin reaches the
daemon. `boty/config.py` already has the mechanism: `_sub`/`_expand` do `${VAR}`
substitution and log an unset name without failing the load, with a docstring
that already argues this exact case (*"an unset `${BESTBUY_API_KEY}` is a
legitimate state, but it must be visible"*). `store_id: ${WALMART_STORE_ID}` in
the shipped file is still "a per-watch `store_id` in `config/products.yaml`" as
CONTEXT requires, keeps a geolocator out of a public repo, and degrades to
empty → unpinned → UNKNOWN, which is the behaviour REQ-14 asks for anyway.
05-01 must argue the choice in the file, whichever way it lands.

### Finding 3 — `due_at` is unpersistable, and `refusals` is the field criterion 6 needs

`boty/pacing.py:54` — `due_at: float = 0.0`, set at line 114 as `now + wait`,
where `now` is whatever the caller passes. `boty/cli.py:313-317`'s `watch_loop`
passes `scheduled_now`, a synthetic clock it advances by its own sleeps and
**starts at `0.0` every process**. A persisted `due_at` is therefore a number
with no referent after a restart: it would either fire immediately or block a
retailer for the age of the previous process.

`cli._refusal_is_entrenched` compares `pacer._for(retailer).refusals >=
REFUSALS_BEFORE_PAGING`, so **`refusals` is the only field REQ-16's "outlasts the
cap" clause actually reads.** 05-03 persists `refusals` plus a wall-clock stamp
(which answers the original docstring's stale-file objection by ageing state out)
and lets `due_at` rebuild. It must say so in the code, not only in the plan.

Corollary for 05-03: the state file needs a `.gitignore` line. `state.json` and
`served/boty/status.json` are both already ignored (`.gitignore:21`, `:26`); a
new `pacer` state file inherits nothing and would otherwise be committed.

### Finding 4 — REQ-16's first two clauses are already implemented; 05-03 verifies and pins, it does not build

`cli.watch_cycle:260-290` already does recorded-not-pushed (`log.info` for a
refusal the backoff is handling), pushed-once (`warned`), and outlasts-the-cap
(`_refusal_is_entrenched`). The only thing broken is that `refusals` resets on
restart. 05-03's tasks should be weighted accordingly: most of the effort is
persistence plus a restart-level test, not new push logic.

---

## Per-plan scope sketch

Task counts are the target for the per-plan write; files are the expected
`files_modified`.

### 05-01 — the store lands (wave 1, autonomous)

~3 tasks.

1. **The pin and the field.** `boty/models.py` — `Watch.store_id: str | None = None`
   after `max_price`, `Result.store: str | None = None` declared last after
   `refused`, each with the "declared last, with a default, so every pre-existing
   construction site stays valid" paragraph copied from `rung`/`extraction`
   (`models.py:136-144`), plus the paragraph `rung` and `extraction` both carry
   on what the axis is deliberately NOT folded into — and the extra one they did
   not have to write: **why an unpinned store DOES drive `Availability` to UNKNOWN
   while `degraded` deliberately does not touch `alertable`.** `boty/config.py` —
   coercion in `_price`'s shape (same `where` parameter, same bool-is-an-int-subclass
   rejection, `str()` coercion so `store_id: 12345` as a YAML int does not blow up on
   comparison), carried as data on the `Watch` rather than only as a log line,
   because `assess_health` needs it. `config/products.yaml` — `store_id` on **both**
   Walmart watches (CONTEXT: the GO Plus + product watch, not only the control) with
   the decision paragraph the file's comment convention demands: no default, missing
   means UNKNOWN not a guess, both rejected alternatives named, and how a user finds
   their store number. `scripts/identity_check.py` — the YAML spelling, watched going
   red (§ *Finding 2*).
2. **Reading which store answered.** `boty/parse.py` — a store reader beside
   `nextdata_offers`, with an exact path constant beside `_WALMART_PRODUCT_PATH`
   carrying the same kind of comment, defensive `None` at every step, no regex over
   raw HTML, and **no `"0"` special case** (§ *Finding 1*). Candidate paths present in
   both shipped fixtures: `props.pageProps.initialData.data.product.location.storeIds[0]`
   and `…contentLayout.pageMetadata.location.storeId`; the plan picks one and says
   why the other was not taken. `boty/retailers.py` — thread `store=` onto **every**
   `check_html` return path including the `except Blocked` / `except FetchError` arms,
   the way `check_target_browser:542` commits for `rung`/`extraction`. Prefer the
   generic path; a fifth arm in `cli.make_checker` needs the same written justification
   the existing four carry.
3. **Publishing it.** `boty/status.py` — a `"store"` key in the `watches` block, plus
   the pinned value, so a reader can tell "no store recorded" from "store B answered
   and you pinned A"; `None` for a non-Walmart watch, never `0` or `""` (the
   `duration_seconds` argument at `status.py:51-57` applies word for word, and
   Finding 1 makes `0` the literal wrong answer). `boty/cli.py` — `_report`'s tag list.
   `served/boty/index.html` — one more conditional `<span class="tag">`, plain weight
   for a correct pin and warning weight for unpinned/mismatched, everything through
   `esc()`. Producer and consumer both asserted (`tests/test_status.py`,
   `tests/test_dashboard.py`) and the store added to `test_dashboard.py`'s `UNTRUSTED`
   list, since it originates in Walmart's JSON and lands in `innerHTML`.

Files: `boty/models.py`, `boty/config.py`, `boty/parse.py`, `boty/retailers.py`,
`boty/status.py`, `boty/cli.py`, `served/boty/index.html`, `config/products.yaml`,
`scripts/identity_check.py`, `tests/test_config.py`, `tests/test_parse.py`,
`tests/test_retailers.py`, `tests/test_status.py`, `tests/test_dashboard.py`,
`tests/test_identity_check.py`.

### 05-02 — UNKNOWN, and only measured causes (wave 2, autonomous)

~3 tasks. Criteria 3 and 4 share `monitor.assess_health`, so they share a plan;
splitting them would put two plans inside one function.

1. **The two guards**, in `_verdict_from_html`, at or above the depth of the
   existing seller guards (`retailers.py:240-272`) and ahead of the
   `Availability.IN_STOCK if offer.available` line — a store mismatch
   short-circuits before any stock verdict forms. Two guards, two `detail`
   strings: the config gap names the key by the name a user types in
   `products.yaml` so the message is a fix instruction; the mismatch names both
   stores. Only Walmart can produce a store, so the guard must not turn every
   non-Walmart reading UNKNOWN — state the predicate explicitly.
2. **`assess_health` stops asserting what it did not measure.** A third arm for the
   unpinned/mismatched config gap, in the restrained shape of the existing
   `"no control watch configured"` line. The refusal arm's *"we are asking too
   often"* withdrawn — the code established a **refusal**, not a **rate**, and
   CONTEXT records it kept firing after a 6-hour backoff was observed not to help;
   per criterion 4 the replacement says the cause is unknown rather than picking a
   plausible one. The else arm's *"the detector is probably broken"* stops being the
   catch-all it currently is for every non-refusal failure. `boty/notify.py`'s
   hardcoded `"bot-y: detector problem"` title is the same defect in the one place a
   phone actually shows — fix it there; the module composes no diagnosis of its own
   and must not start. Any new send returns the same `bool` and is wired into
   `watch_cycle`'s rollback, or it is a drop nothing will mention again.
3. **Watched going red.** Criterion 3 says it in as many words. Mutations in
   `scripts/mutation_check.py` in `M2`'s shape — anchor on `Availability.UNKNOWN`,
   never on the message text, which will be edited — one per guard, each observed
   caught, `caught/total` recorded rising. Criterion 4 is a claim about *absence*,
   which is harder to gate: a source-level gate asserting the two known-bad strings
   are gone from `monitor.py`/`notify.py`, in the style of `test_dashboard.py`'s
   structural assertions. **Grep hygiene:** these files are dense with `#` comment
   prose, and this outline and the plan will both quote the bad strings — filter
   comments (`grep -v '^\s*#' | grep -c`) and scope to the two modules, or the gate
   is self-invalidating. Watch it red against the current text before trusting it.

Files: `boty/retailers.py`, `boty/monitor.py`, `boty/notify.py`,
`scripts/mutation_check.py`, `tests/test_retailers.py`, `tests/test_monitor.py`,
`tests/test_notify.py`.

### 05-03 — the backoff survives a restart (wave 3, autonomous)

~3 tasks.

1. **Persistence in `boty/pacing.py`**, on `monitor.State`'s pattern
   (`monitor.py:33-49`) — `load` swallowing both `OSError` and `JSONDecodeError`
   into empty state, plain `write_text` rather than `status.write`'s temp-and-replace
   (there is no concurrent reader) but wrapped in `try/except OSError:
   log.exception(...)`, because failing to persist a backoff must degrade to today's
   in-memory behaviour and never take down a cycle. Persist `refusals` + a wall-clock
   stamp; **not `due_at`** (§ *Finding 3*), with the reason in the code. **Rewrite the
   module docstring's lines 29-32** — the paragraph currently argues against criterion
   6 in prose sitting above code that will contradict it. Argue the reversal in place
   (`models.py:145-161`, `pacing.py:5-15` are the house style), name what overruled it
   (a restart resetting every backoff defeats politeness under a flapping service, and
   REQ-16's "pushed once after the cap" is meaningless if the counter resets), and
   answer the stale-file objection the original raised rather than ignoring it.
2. **Wiring.** `boty/cli.py` — load at startup in `State.load(cfg.state_path)`'s
   call-site shape, save after `record`; the invariant already stated at
   `cli.py:308-309` ("one pacer for the life of the loop") must survive. `boty/config.py`
   — a path setting beside `state_path`/`status_path`. `config/products.yaml` — the
   documented key. `.gitignore` — the new state file (§ *Finding 3* corollary).
3. **Pin REQ-16 across a restart.** `tests/test_pacing.py` — extend the module
   docstring rather than duplicate it; run to N refusals against a `tmp_path` file,
   build a **fresh** `Pacer`, assert `refusals` survived and `due_at` did not.
   `tests/test_cli_watch.py` — the loop-level shape: `cycles=`, fake sleep, state
   re-loaded from disk between assertions, proving all three REQ-16 clauses hold
   *across* the restart (handled refusal recorded not pushed; a refusal past the cap
   pushed **once**, not once per process; a wrong verdict pushed immediately). One
   mutation clearing the persisted state — pure `M6` territory, a change that alters
   no availability, no price and no alert, which a verdict-only suite passes straight
   through.

Files: `boty/pacing.py`, `boty/cli.py`, `boty/config.py`, `config/products.yaml`,
`.gitignore`, `scripts/mutation_check.py`, `tests/test_pacing.py`,
`tests/test_cli_watch.py`.

### 05-04 — close (wave 4, `autonomous: false`)

~2 tasks.

1. **`checkpoint:human-action` — the real pin.** Claude cannot supply this and must
   not derive it: the standing rule is *bot-y never guesses where the user lives*, and
   Walmart is challenge-blocked at HTTP 200 so a live read cannot supply it either.
   Dan sets the store number in the daemon's `EnvironmentFile` (or the file, per
   05-01's decision), then the service is restarted onto the new code — which is safe
   for the first time *because* 05-03 shipped, and which STATE.md has been warning
   against since 2026-08-04. Confirm from `served/boty/status.json` that the Walmart
   watches carry a store and are no longer UNKNOWN-for-want-of-a-pin. A restart is
   part of shipping: `make verify` runs the tree, not the daemon, and the two have
   disagreed silently in this project before.
2. **The verdicts.** `make verify` run once, live, at close, recorded **verbatim
   including a FAIL** — it has read `VERIFY: FAIL (live controls)` since 2026-08-06 for
   reasons this phase did not cause and is not chartered to fix, and a closing record
   that trimmed that would be the omission this project keeps catching in itself.
   `make verify-offline` is the phase gate that must be green. Mutation count observed
   rising with each new mutation caught. Six criterion verdicts in the ROADMAP outcome
   table in Phase 3.1's and Phase 4's format — measurement or reason per row, unmet
   recorded unmet with the date, **nothing reworded to pass**. `REQUIREMENTS.md`
   traceability and `STATE.md` updated.

   **A ROADMAP defect to fix here, flagged not silently corrected:** Phase 5's criteria
   list at `ROADMAP.md:387-392` is numbered `1, 0, 2, 3, 4, 5` — the second entry reads
   `0.`. `05-CONTEXT.md` renumbers the same six as 1-6, and this outline uses CONTEXT's
   numbering. Renumbering the ROADMAP list is a typo fix, not an amendment to a
   criterion's content; make it in the same commit as the outcome table and say in the
   commit message that it is a renumbering only.

Files: `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`,
`docs/retailer-evidence.md` (closing record section).

---

## Why every wave is serial

Measured file contention, not caution. The same pattern that forced Phases 2, 3,
3.1 and 4 to serialise.

| File | 05-01 | 05-02 | 05-03 | 05-04 |
|---|:--:|:--:|:--:|:--:|
| `boty/retailers.py` | ● | ● | | |
| `boty/config.py` | ● | | ● | |
| `boty/cli.py` | ● | | ● | |
| `config/products.yaml` | ● | | ● | |
| `boty/monitor.py` | | ● | | |
| `scripts/mutation_check.py` | | ● | ● | |
| `tests/test_retailers.py` | ● | ● | | |

05-02 needs `Result.store` and `Watch.store_id` to exist before it can guard on
them, and it re-enters `retailers.py` and `tests/test_retailers.py`. 05-03 re-enters
`config.py`, `cli.py` and `products.yaml` behind 05-01 and `mutation_check.py`
behind 05-02. 05-04 depends on all three by definition. **No two plans own disjoint
file sets, so no two run in the same wave.**

The one structural choice worth naming: criteria 3 and 4 could look like separate
plans, and are not, because both rewrite `monitor.assess_health` — 3 adds an arm, 4
rewrites the two arms already there. Two plans inside one function is contention
disguised as parallelism.

---

## Evidence constraint (binds every plan's `<verify>`)

`make verify` has failed live since **2026-08-06** — `VERIFY: FAIL (live controls)`,
exit 2 — for reasons recorded in STATE.md and not caused by this phase, and Walmart
specifically is **challenge-blocked at HTTP 200**. Therefore:

- **Every gate this phase adds must be watched going red offline**, against
  `tests/fixtures/walmart/` and synthetic `_nextdata(**product)` payloads
  (`tests/test_retailers.py:54-57` — a fixture cannot be edited to hold a different
  store without lying about what was captured; a synthetic payload can).
- **No plan's acceptance may depend on a live Walmart read succeeding.** A live
  confirmation is recorded as a bonus if it happens, never as the proof.
- `make verify-offline` (exit 0, 531 passed, 8/8 mutations at baseline) is the gate
  each plan asserts against. The live `make verify` verdict is *recorded* at close,
  not *required* to be green.

---

## Multi-source coverage audit

Every item below is covered by a plan. No item is deferred, simplified, or
reduced to a "v1".

### GOAL — ROADMAP phase goal

| Item | Covered by |
|---|---|
| "A Walmart reading is a statement about a known store" | 05-01 (records + publishes), 05-02 (unknown store ⇒ UNKNOWN) |
| "every alert names only what was measured — or says it does not know" | 05-02 |

### Success criteria (CONTEXT numbering 1-6)

| # | Criterion | Covered by |
|---|---|---|
| 1 | Every Walmart `Result` records its store; published in `status.json` | 05-01 |
| 2 | Store pinning is required config with no default; unset ⇒ UNKNOWN + health message | 05-01 (config + pin), 05-02 (UNKNOWN + health message) |
| 3 | Unpinned/unexpected store ⇒ UNKNOWN, never a verdict — **watched going red** | 05-02 |
| 4 | No alert text names an unestablished cause; unknown cause said so | 05-02 |
| 5 | Handled refusal recorded not pushed; one past the cap pushed once | 05-03 |
| 6 | Page-once state survives a restart | 05-03 |
| — | All six recorded with verdicts and measurements | 05-04 |

### REQ — `phase_req_ids`

| ID | Covered by | Closed by |
|---|---|---|
| REQ-14 | 05-01, 05-02 | 05-02 |
| REQ-15 | 05-02 | 05-02 |
| REQ-16 | 05-03 | 05-03 |

### RESEARCH

Not applicable — research is disabled for this project and no `05-RESEARCH.md`
exists. `05-PATTERNS.md` served that role and is fully consumed above, including
the two places this outline corrects it (Findings 1 and 3).

### CONTEXT — locked decisions

| Decision | Covered by |
|---|---|
| Store pinning is **required config, no default** (Dan, 2026-08-10) | 05-01 |
| Rejected: default to whatever Walmart assigns, flag changes only | 05-01 — named as rejected in the `products.yaml` comment |
| Rejected: geolocate from a postal code | 05-01 — named as rejected in the `products.yaml` comment |
| REQ-14 applies to the **GO Plus + product watch, not only the control** | 05-01 — `store_id` on both Walmart entries |
| Never amend a criterion to make it meetable | 05-04 |
| Every criterion verified by something executable | all four — `<verify>` blocks, `make verify-offline` |
| A gate must be watched going red before it is trusted | 05-01 (identity rule), 05-02 (both guards + prose gate), 05-03 (state mutation) |
| Politeness is a hard constraint | 05-03 (the backoff is the mechanism), 05-04 (no live probing budget spent) |
| UNKNOWN is never OUT_OF_STOCK | 05-02 |
| Do not put a real postal code or store id in a fixture or config without redaction | 05-01 (§ *Finding 2*), 05-04 (checkpoint keeps the value out of Claude's hands) |

**Claude's discretion, per CONTEXT** — where store identity is carried on `Result`,
the persistence mechanism and location for `Pacer._state`, and the shape of alert
text. Resolved above in 05-01 T1, 05-03 T1 and 05-02 T2 respectively; each carries
its argument into the code, per this codebase's dominant convention.

**Deferred, correctly absent from every plan:** the live `make verify` failure
classes (no Chrome binary; Walmart/Amazon challenge pages) are recorded at close,
not fixed. `QUESTIONS.md` § 0e stays open. All of Phase 6 — delivered-total price
ceiling, matrix/Rung binding, workflow-file gates, CHANGELOG contents gate,
`pyproject.toml` version — appears nowhere.

---

## Threat model seeds

`workflow.security_enforcement` is on, ASVS L1, block on `high`. Each PLAN.md
carries its own `<threat_model>`; these are the boundaries and threats already
established, for the per-plan writer to sharpen rather than rediscover.

**Trust boundaries:** Walmart's `__NEXT_DATA__` JSON → `boty.parse` (untrusted
input); `Result.store` → `status.json` → `served/boty/index.html` `innerHTML`
(untrusted output); the operator's store number → a public git repo (identity
egress); the persisted pacer state file → `Pacer` at daemon start (untrusted
deserialisation, local writer).

| Threat ID | Category | Component | Disposition | Mitigation |
|---|---|---|---|---|
| T-05-01 | Information disclosure | `config/products.yaml`, tracked and public | mitigate | A store number is a geolocator that resolves to one street address — `3bd1663` scrubbed exactly this class from git history. `identity_check.py` is measurably blind to the YAML spelling (§ *Finding 2*); widen the rule and watch it red. Prefer `${WALMART_STORE_ID}` indirection so no real value enters the file. **05-01.** |
| T-05-02 | Information disclosure | `served/boty/status.json`, `index.html` | accept, with the reason | Both are gitignored (`.gitignore:21`, `:26`) and served on loopback :8821 behind Tailscale with no public exposure, so publishing the store there does not commit it or expose it. Criterion 1 requires the publication. Recorded so the acceptance is deliberate. |
| T-05-03 | Tampering (XSS) | `Result.store` → dashboard `innerHTML` | mitigate | The value originates in Walmart's JSON. Route through `esc()` like `esc(w.name)`/`esc(w.url)` on the same row, and add the store to `tests/test_dashboard.py`'s `UNTRUSTED` list so the escaping is asserted, not assumed. **05-01.** |
| T-05-04 | Denial of service | persisted pacer state at daemon start | mitigate | A corrupt, absent or hostile state file must never stop the monitor starting and must never pin a retailer at the cap forever. `monitor.State.load` swallows `OSError` and `JSONDecodeError` into empty state — copy it; bound `refusals`; age state out by its wall-clock stamp. **05-03.** |
| T-05-05 | Spoofing | a reading attributed to the wrong store | mitigate | This is the phase's own subject: an unexpected store is UNKNOWN before any verdict forms, watched going red by a mutation anchored on `Availability.UNKNOWN`. **05-02.** |
| T-05-06 | Repudiation | the closing record | mitigate | Every criterion verdict cites a measurement or a reason; the live `make verify` verdict is recorded verbatim including FAIL. **05-04.** |
| T-05-SC | Tampering | npm/pip/cargo installs | mitigate | **No new dependency is expected in this phase** — every surface is an existing module. Research is disabled, so there is no `## Package Legitimacy Audit` and the fallback policy applies: if any plan finds it needs a package, every package is `[ASSUMED]` and a `<task type="checkpoint:human-verify" gate="blocking-human">` verifying it on `pypi.org/project` must precede the install. Not auto-approvable. |

---

## Metadata

**Sources consumed:** `.planning/STATE.md`, `.planning/ROADMAP.md`
(§ Phase 3.1, § Phase 4, § Milestone v0.2), `.planning/REQUIREMENTS.md`,
`05-CONTEXT.md`, `05-PATTERNS.md`.
**Tree work done during outlining:** `boty/pacing.py` (full), `boty/config.py:1-60`,
`boty/parse.py:270-330`, `scripts/identity_check.py` (rules + allow-list + scope),
both Walmart fixtures parsed and walked for store keys, `git show 8dec2e0`/`95f84a6`
for the redaction provenance, `identity_check._identity_leaks` executed against four
`store_id` spellings, `.gitignore` checked for the state and status paths.
**No project `CLAUDE.md` and no `.claude/skills/` exist in this repo** — the
governing conventions are the ones in `05-PATTERNS.md` § *Shared Patterns* and the
standing constraints in `05-CONTEXT.md`.
