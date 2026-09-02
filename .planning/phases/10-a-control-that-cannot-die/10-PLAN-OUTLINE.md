# Phase 10: A Control That Cannot Die — Plan Outline

**Drafted:** 2026-09-02 · **Granularity:** coarse · **Requirement:** REQ-24 (the only one)
**Mode:** chunked — this file is the outline and the authority on the breakdown.

`boty/monitor.py`, `boty/models.py`, `boty/retailers.py`, `config/products.yaml` and
`docs/retailer-evidence.md` are contested files: the plans below overlap on at least one of them at
every join, so **every plan is its own wave**. Phases 8 and 9 recorded the same shape for the same
reason — *"the serialization is the schedule, not a scheduling failure"*. `files_modified` in each
plan's frontmatter is the accurate list, so the wave grouping is real rather than declared.

| Plan ID | Objective | Wave | Depends On | Requirements |
|---|---|---|---|---|
| `10-01` | **The collisions decided in writing, and the dead-control state reachable without a wire.** Write `10-DECISIONS.md` settling all nine collisions before any production code moves, then a tracer: the existing `tests/fixtures/bestbuy/unresolved-sku` capture driven end-to-end — adapter → `Result` → `assess_health` — until a Best Buy control whose SKU does not resolve is reported as a **dead control** and not as a broken detector. Definition of Done item 3's second half, closed offline. | 1 | — | REQ-24 |
| `10-02` | **The three states, distinct, and criterion 2's conjunction asserted in both halves.** Generalise the producer: an HTTP 404/410 is a dead control at every rung-1 retailer, and the 2026-08-04 false-dead precedent — Best Buy served unparseable JSON-LD and the SKU branch fired on a SKU that was perfectly alive — is gated so unreadable markup stays *detector broken*. Then arm precedence, and the mixed group where a dead control and a real refusal are both true at once. | 2 | `10-01` | REQ-24 |
| `10-03` | **Criterion 4 — the durability rule written down, numbered, and applied to every existing control with the failures named.** The rule already exists in `docs/adding-a-retailer.md` as one unnumbered sentence and has never been applied to anything. Number it, extend it where this phase's evidence forces an extension, apply it to all six controls, name every failure, and gate the naming so it cannot be dropped. Expect it to condemn more than one control; naming them is the deliverable. | 3 | `10-02` | REQ-24 |
| `10-04` | **Criterion 3 — the wire. At most three reads, Best Buy only, spaced.** Read 1 establishes what state the incumbent control is actually in, which has not been measured since the browser-capability correction. Reads 2 and 3 are the replacement's, spent under a branch table written before the first request. A refusal is the measurement. No control is shipped that has not been confirmed by a live reading. | 4 | `10-03` | REQ-24 |
| `10-05` | **Criterion 5 — M44, the gate and the verdict.** A mutation anchored on the dead-control **behaviour**, observed CAUGHT, its kill set measured against the registry before it is priced. `CLAUDE.md`'s registry counts advanced in the same commit. `make verify-offline` run and its **verdict line** read, not the exit code alone. The five-criterion verdict table. | 5 | `10-04` | REQ-24 |

---

## The five criteria, verbatim from `ROADMAP.md`, unedited

  1. Three states are **distinct** and asserted separately: *dead control* (our SKU no longer resolves), *refused* (the retailer served a challenge), and *detector broken* (the page arrived and the extractor could not read it). Today the first is reported as the third
  2. A dead control does **not** describe the retailer as refusing us, and does not silence a real refusal if both are true at once
  3. Best Buy's control is repaired — measured against a real reading, not a fixture — or replaced with one that reads, with the replacement's durability argued
  4. **The rule for what makes a control durable is written down and applied to every existing control**, with any control failing it named. Best Buy's died because it was a specific game SKU; a control that can be discontinued eventually will be
  5. `make verify-offline` exits 0, with at least one new mutation registered and observed CAUGHT

**Not one of them is reworded anywhere in this phase.** Where a criterion cannot be met as written,
the plan that owns it records **MET IN PART** with the half that is missing named. Criterion 3 is the
one this outline already expects may land there — it is the only criterion that depends on a third
party answering us — and `10-04`'s branch table says so before the first request rather than after a
refusal disappoints.

---

## The locked terms, which are binding on every plan below

From `QUESTIONS.md` § 0g, Dan's answer of 2026-09-02, and `10-CONTEXT.md`:

1. **At most THREE live requests, Best Buy only.** Not Amazon, Target or Walmart — the three already
   refusing us — and not GameStop or Nintendo. Spaced, not burst. **Only `10-04` spends any.**
2. **A refusal IS the measurement.** `README.md` records Best Buy as *"unread — refused at the
   connection layer"*. If a read returns that, it is written down as a measured result — not retried
   around, not reported as inconclusive, and not rounded into "the control could not be verified".
3. **No `boty check`.** It requests every retailer *and* writes the daemon's live
   `served/boty/status.json`. The permitted reads are made directly and narrowly.
4. **No write to `state.json`, `pacer-state.json` or `served/boty/status.json`.**
5. **No `systemctl restart boty`.** Deferred with Phases 8 and 9; that restart is Dan's and now
   carries three phases.

**What one read means, stated before any are spent.** Best Buy is rung 3, and Dan's authorisation
says *browser-rung*, so the unit is **one rendered page load through `check_bestbuy_browser`**. A
render fans out into many subresource requests to bestbuy.com — that is inherent to the rung Dan
authorised, not a loophole, and it is stated here so nobody later discovers it and treats the budget
as having been exceeded in secret. **Three navigations, no more**, and an unspent one is recorded as
unspent rather than spent because it was available.

---

## Notes the plan writers must not rediscover

### The premise "Best Buy's control is dead" has not been measured since the capability correction

REQ-24 says *"Best Buy's current dead control is repaired"*. The last recorded live reading of that
control (`docs/retailer-evidence.md`, the `make verify` transcripts around lines 3482 and 4397) is:

> `unknown  bestbuy  CONTROL — Pokémon Let's Go, Pikach   —  fetch failed: no Chrome/Chromium binary found — set BOTY_BROWSER_PATH`

**That is a local capability failure, not a dead control and not a refusal.** `10-CONTEXT.md` records
the capability claim as stale, measured 2026-09-02: Playwright chromium is present at
`~/.cache/ms-playwright`, three builds including a headless shell.

So the incumbent control may be alive, dead, refused, or unreadable-here, and **which one is not
established**. `10-04`'s read 1 exists to establish it. No plan may assert the incumbent is dead
before that read returns, and `10-01`/`10-02`/`10-03` are written so that none of them needs to: the
mechanism, the states and the rule are all provable offline against fixtures and config.

### Today's defect, located exactly

`monitor.assess_health` has three arms for a failing control, in this order:

| arm | condition | what it says |
|---|---|---|
| refused | `all(c.refused for c in broken)` | *the retailer is refusing us … the extractor was never reached* |
| store gap | `all(_is_store_gap(c) for c in broken)` | *a control reading cannot be shown to come from the store this watch is about* |
| breakage | everything else | *a control product did not read IN_STOCK and was not refused … readings from this retailer are unverified* |

A control whose target no longer resolves is `refused=False`, so it lands in the **breakage** arm and
is reported as *"readings from this retailer are unverified"* — a fact about the retailer, asserted
from a fact about our config. That is criterion 1's *"today the first is reported as the third"*,
and it is one arm and one predicate away from being right.

### The fact exists already — in prose, where nothing may read it

`retailers._verdict_from_html` already has the branch (around line 381):

> `sku {sku} did not resolve to a product page — no schema.org Product on it carries that sku`

It is carried **only in `Result.detail`**, and `assess_health` may not read it. `_is_store_gap`'s own
docstring says why, and it is the rule for this phase too:

> *Detected from FACTS, not from `detail` prose … Matching on the message text would tie this to
> prose that is edited far more often than the condition is — the anchoring lesson
> `scripts/mutation_check.py`'s M2 comment already paid for once.*

**So the phase's central artifact is a FIELD, not a string.** `Result.unresolved` *(candidate name;
`10-01` fixes it and defends it at its definition site)*, declared last after `read_at`, defaulted
`False`, on the precedent `rung`, `extraction`, `store` and `shipping` all set in `models.py`: every
one of the tree's existing construction sites stays valid and keeps its meaning.

### The false dead, which already happened here, and is why the discriminator is not optional

**2026-08-04, recorded in `docs/retailer-evidence.md` § *Best Buy served JavaScript-escaped JSON-LD,
and the control caught it*.** The control went UNKNOWN with the exact message above. The SKU was
**perfectly alive**. Best Buy had served three `ld+json` blocks of which **0 parsed** — 8 × `\'`
inside strings, 34 × a literal `\n` outside them — so `ldjson_offers` found no Product and the branch
fired.

That is criterion 1's *third* state (the page arrived and the extractor could not read it) wearing
the *first* state's message. If `unresolved` were set on `not offers and sku is not None` alone, this
phase would ship a mechanism that calls a live control dead every time a retailer deploys bad markup
— **the same misattribution it exists to fix, pointed the other way.**

The discriminator is already measured and already published: `parse.ldjson_read` returns
`LdJsonRead(blocks, unparseable, repaired)`, and `_verdict_from_html` already holds it as `ld`. The
rule `10-01` implements and `10-02` gates:

> **A control is dead only when the page was READ SUCCESSFULLY and named no product matching the
> target.** Markup that was present and could not be parsed (`ld.unparseable > 0`) is a detector or
> markup failure, never a dead control.

Both fixtures exist for this. `unresolved-sku.html` is the true dead — a search page, no Product
markup, nothing unparseable. The 08-04 episode is the false dead, and `tests/test_parse.py` already
carries the broken-escape material.

### The second producer is the HTTP status, and it generalises the state past Best Buy

Best Buy is addressed by SKU through a search redirect, so its death is a *resolution* fact. Every
other retailer here is addressed by URL, and **a dead target there is an HTTP 404** — which
`fetch.get` raises as `FetchError(status=404)`, and which `is_refusal` correctly does **not** treat
as a refusal (`REFUSAL_STATUSES` is 401/403/429). So today a 404 on a control reaches the breakage
arm and is reported as a probably-broken detector: *the identical defect, at five retailers rather
than one.*

`10-02` adds `fetch.is_unresolved(exc)` — `status in {404, 410}` — as the exact mirror of
`is_refusal`, and wires it at the **five** `is_refusal(exc)` sites in `boty/retailers.py`
(lines 545, 622, 754, 871, 969 at the time of writing; located by content, never by line number).

**And one case with no producer at all, which is named rather than left to be discovered.**
`boty/browser.py` returns `Page(status=200)` unconditionally, with a comment saying so:

> *the simple API does not surface the main frame's response status, so there is no real status to
> report and inventing one would be worse than saying so.*

So at rung 3 there is no status to read. Best Buy is covered by the resolution producer; **Target is
not covered by either** — a delisted Target control renders Target's own 404 page, reads no offers,
and is indistinguishable from a reskin at this layer. `10-03` records that as a **named gap in the
durability rule's D5 clause**, not as a passing verdict. Inventing a status in `browser.py` to close
it is **refused**: it would put a fabricated fact into a `Page`, and the comment above already argues
why. If a future phase wants it, the honest route is the response object, not a constant.

### `Health` needs a field too, and its quantifier is not `refused`'s

`assess_health`'s existing arms use `all(...)`, and the reasoning is written into the code: *"if even
one control failed for a reason that is NOT a refusal, something may really be wrong and the louder
reading is the safe one"*. A refusal **excludes knowledge** of everything else, so it is only
reportable when it is the whole story.

**Deadness excludes nothing.** A target that does not resolve is established per-watch, off our own
config, and does not become less established because a sibling control failed for another reason. So
`Health.dead_control` *(candidate)* is `any(...)` while `Health.refused` stays `all(...)`, and the
difference is argued at the field rather than left as an inconsistency for somebody to "fix".

### Criterion 2's conjunction, and where each half lands

**Half one — a dead control must not describe the retailer as refusing us.** Structural: a dead
control carries `refused=False`, so `all(c.refused)` is False and the refusal arm cannot fire. It is
still asserted directly, because "it cannot happen by construction" is exactly the claim that stops
being true after a refactor.

**Half two — a dead control must not silence a real refusal when both are true at once.** This is
the one that needs work. Today a group of one dead control and one refused control satisfies neither
`all(refused)` nor `all(_is_store_gap)`, so it falls to the breakage arm — whose sentence says
**"and was not refused"**, which is *false* about that group. That is a real refusal, silenced by a
dead control, in the shipped code today. `10-02` owns it.

**At the `Result` level the two are mutually exclusive and that is asserted as an invariant:** a
refusal means no page came back, so nothing about resolution was established — the same first line
`_is_store_gap` opens with. `refused and unresolved` is never both True on one `Result`.

### Arm precedence, and the one non-obvious ordering

`refused` → **dead** → `store_gap` → breakage.

- **`refused` stays first, unchanged.** A refusal produced no page, so nothing else could have been
  established.
- **dead goes ahead of `store_gap`, and this is a decision rather than a detail.** `_is_store_gap`
  returns `True` whenever `watch.store_id is None` — *"read off the config and therefore true
  whatever the page did"* — and `WALMART_STORE_ID` is deliberately unset today (`QUESTIONS.md`
  § 0f). So a dead Walmart control would today be reported as a store gap. A target that does not
  resolve makes the store question moot: **a page about no product cannot be a page about the wrong
  store.** Both facts are about our config; deadness is the more specific one and it is also the one
  whose remedy is different.
- **breakage stays last**, claiming least, unchanged.

### `Health.action` — the dead arm pages, on `STORE_PIN_ACTION`'s precedent

`Health.action` is *"what a person can DO about this state, in one sentence — and the whole of what
makes it worth a push"*. Today exactly one arm carries one: the store gap, whose remedy is *edit
`config/products.yaml`*. **A dead control's remedy is the same shape** — the SKU or URL in
`config/products.yaml` names a product that no longer exists, and somebody has to choose another.
Unlike a refusal and unlike breakage, its cause **is** established, which is the property `action`
exists to reward.

`10-01` carries the decision; the counter-argument (a fourth pageable state is more traffic to a
phone) is recorded beside it rather than omitted, along with the fact that this arm fires at most
once per failure episode through the existing `warned` memory in `cli.watch_cycle` and needs **no new
sender**.

### Nothing new is published to `status.json`, and that is decided rather than forgotten

`boty/status.py` builds its health rows field by field and publishes `refused` and `reason`.
`Result.shipping` and `Health.action` are both **deliberately unpublished**, each with the reasoning
written at the field. `Health.dead_control` takes the same treatment: the `reason` already carries
the diagnosis, no source artifact asks for the key, and adding one would move
`tests/test_status.py`'s key-set assertions and `served/boty/index.html`'s `esc()` obligations for no
measured benefit. **`boty/status.py` and `served/boty/index.html` are in no plan's
`files_modified`.** If a plan finds it needs them, that is the signal something published changed
shape and the decision must be reversed in writing first.

### The durability rule is half-written already, and the tree already violates it

`docs/adding-a-retailer.md` § *The rule a control has to satisfy* says:

> **first-party, evergreen, restocked routinely, never the subject of a buy-box fight, and not a
> console.**

It has **never been applied to anything in writing**, and nothing gates it. Applied mechanically to
the six shipped controls it condemns immediately: **GameStop's control is a PS5 console**, which the
rule's own last clause forbids and which `config/products.yaml`'s Walmart block already argues
against in prose. Nothing caught that.

`10-03` numbers the clauses, extends them where this phase's evidence forces it (the ROADMAP's own
words: *"a control that can be discontinued eventually will be"* — which "evergreen" gestures at and
does not state), applies them to all six, and **gates the application** so a control added later
without a verdict reddens the suite. The extension takes the dated-reversal form: the original
sentence is quoted whole and kept, because it is not wrong — it is incomplete.

**The clause set `10-03` starts from** (it may rename or re-cut them, and must defend whatever it
ships; it may not drop one to make a control pass):

- **D1 — first-party by construction.** Sold by the retailer's own entity or house brand, so no
  buy-box rotation can take the listing away. *(Absorbs "first-party" and "never a buy-box fight".)*
- **D2 — replenished, not released.** A consumable or evergreen catalogue staple, restocked
  routinely; never a unit with a launch date and an end of life.
- **D3 — not generation-bound.** Its existence does not depend on a hardware or software generation
  the manufacturer will end. *(This is the clause Best Buy's control failed. It is new.)*
- **D4 — a recorded reserve candidate that itself passes D1–D3.** The doc already asks for a
  fallback and names Nintendo's; this makes it a clause and checks the fallback against the rule.
- **D5 — its death is legible.** When the target stops resolving, the monitor reports a *dead
  control* — criteria 1 and 2. **Nothing in this repository satisfied D5 before this phase**, which
  is why it is a clause and not an assumption.

**What `10-03` is expected to name, stated in advance so a softer finding is visibly a softer
finding.** These are predictions, not verdicts; `10-03` measures each control against the shipped
rule and records what it actually finds:

| control | expected verdict |
|---|---|
| gamestop — PS5 console | **FAILS D2, D3** — a console: released, generation-bound. The rule's own words already forbade it |
| bestbuy — Pokémon Let's Go, Pikachu! (Switch) | **FAILS D2, D3** — a specific game SKU on an ended generation, and **FAILS D4**: its recorded reserve (`Let's Go, Eevee!`, `docs/retailer-evidence.md`) is the same class of product and fails the same clauses |
| nintendo — HDMI cable | **FAILS D3** — a generation-bound accessory, and **FAILS D4** for the same reason: the reserve it names (the AC adapter) is generation-bound too |
| walmart — Great Value whole milk | passes D1–D3; **D4 not recorded**. Separate finding, recorded beside and not as a durability failure: it is pinned to `${WALMART_STORE_ID}`, which is deliberately unset, so it is currently **unreadable here** — an availability fact, not a durability one |
| target — up&up microfiber dust cloths | passes D1–D3; **D4 not recorded**; **D5 NOT SATISFIED** — rung 3 surfaces no HTTP status, so a delisted Target control is indistinguishable from a reskin. The named gap above |
| amazon — Amazon Basics AA batteries | passes D1–D3; **D4 not recorded** — its rejected first candidate is recorded as a rejection, which is not the same thing as a reserve |

That is three controls condemned on the product-choice clauses, five short a recorded reserve, and
one retailer where the death signal cannot reach. **Naming them is the deliverable.** `10-03` fixes
nothing but Best Buy's, which is criterion 3's; the rest are recorded, and a control this phase does
not replace is recorded as *named and unrepaired*, never quietly repaired without a reading.

### The read budget, allocated before anything is spent

| read | plan | spent on | branch |
|---|---|---|---|
| **1** | `10-04` | the **incumbent** control, SKU `6216393`, through `check_bestbuy_browser` | establishes which of four states it is in: reads / dead / refused / unreadable-here. **Every one of those is a recorded measurement.** A refusal closes the read and is written down as the measurement |
| **2** | `10-04` | the **candidate class search** — `bestbuy_product_url` on a durable-class term rather than a SKU — to obtain a candidate SKU that passes D1–D3 without guessing one | if it refuses, no replacement can be confirmed; go to the honest-verdict branch |
| **3** | `10-04` | the **chosen candidate's SKU**, confirming it resolves and reads IN_STOCK, first-party | if it does not confirm, the config is **not** changed and the durability failure is recorded as named-and-unrepaired |

**Spacing:** at least **300 seconds** between reads — the retailer's own configured standing cadence.
Never ask Best Buy faster than the daemon would. And note the daemon is running: these reads are
*additional* to its traffic, which is one more reason not to burst them.

**Why the incumbent is read first even though the phase expects to replace it.** Criterion 3 says
*repaired … or replaced with one that reads*. If read 1 shows the incumbent reads, criterion 3 is
already met by a real reading and the replacement is criterion **4**'s business — and the record
gains something better than a repair: the correction that the control was never dead, only unread,
which is the kind of claim this repository exists to get right.

**Why no read is spent hunting a SKU from memory.** A SKU recalled rather than measured is a guess,
and a guess that resolves to the wrong product is the worst outcome this project can produce
(`_verdict_from_html`'s own words). Read 2 buys the SKU from Best Buy's own search, which is the same
URL shape the adapter already uses.

### If Best Buy refuses everything, the phase still closes

Criteria 1, 2, 4 and 5 make **no live request** and are complete before `10-04` starts. That
ordering is deliberate and is the whole reason criterion 3 is fourth.

If all three reads refuse, `10-04` records: the refusal as the measurement (Dan's term 2, verbatim),
the README row's *"unread — refused at the connection layer"* as **confirmed on 2026-09-02** rather
than inherited, the incumbent left in place because no replacement could be confirmed, and criterion
3 at **MET IN PART** — the durability half argued, the reading half refused by the retailer. That is
a shippable outcome here. What is **not** available is calling it inconclusive, retrying around it,
or spending a fourth read.

### Mutation M44

Next free ident is **M44**; M43 was consumed by Phase 9. **M21–M24 stay empty forever** —
`apply_mutation` cannot add a file, so the defect they would have covered is outside the harness by
construction. `grep -c "INTENTIONAL GAP" scripts/mutation_check.py` is **9** today and must not fall.

M44 anchors on **behaviour**: a line whose removal changes *which health arm a dead control reaches*.
Two candidate anchors — the field being set at the producer, and the arm that reads it in
`assess_health` — and `10-05` breaks both in the sandbox, records both kill sets, registers the more
informative one, and writes the loser into the prose block as evidence rather than discarding it.
Then it measures M44's kill set **against the existing registry** before pricing it: M42's kill set
turned out to be a proper subset of M33's and that was recorded as a finding rather than rounded up
into coverage; M43's was measured disjoint from all 38 before it. The same measurement is owed here,
and a subset result is written down as a subset result.

**`CLAUDE.md`'s registry counts move in the same commit that registers M44.** They are correct today
(M1–M20 and M25–M43, 39 idents, next free M44, nine gap markers) because 09-05 advanced them; nothing
in the suite gates them, and they were stale for three days once.

### Prohibitions (author descriptor-less into `must_haves.prohibitions`)

- `10-01` — *a control is never called dead because a message said so.* The dead-control state is
  read off a field set from measured facts. Matching `Result.detail` prose would tie the arm to text
  that is edited far more often than the condition, which is the anchoring lesson M2 already paid
  for.
- `10-01` — *a page that could not be READ never establishes that a product does not EXIST.*
  Unparseable markup is a detector failure. The 2026-08-04 episode is the precedent and it is in this
  repository's own evidence log.
- `10-02` — *a real refusal is never silenced by a dead control.* Both halves of criterion 2 are
  asserted, and the mixed group is the half that needs code rather than a comment.
- `10-03` — *a clause is never dropped, softened or reworded so that an existing control passes.*
  Naming a failure is the deliverable. A rule with no failures after being applied to six controls
  chosen before it existed is a rule that was fitted to them.
- `10-04` — *the budget is three reads and a refusal is a result.* No fourth request, no retry
  around a refusal, no `boty check`, no write to the three live documents. An unspent read is
  recorded as unspent.
- `10-04` — *no control is shipped that has not been confirmed by a live reading.* A replacement
  that could not be read stays a written recommendation.
- `10-05` — *a criterion is never reworded so that it passes.* MET IN PART and "not measured" are
  shippable outcomes here.

### Threat model rows (ASVS L1, block on `high`) — honest, unpadded

This phase adds **no new network surface** in code: it adds a field, an arm, a rule and a document.
It does make **three authorised requests to an existing retailer through an existing adapter**, which
is a use of the surface rather than an addition to it, and it gets its own row rather than a
footnote.

| Threat ID | Category | Component | Severity | Disposition | Mitigation |
|---|---|---|---|---|---|
| `T-10-01` | Spoofing | the dead-control verdict in `monitor.assess_health` | **high** | mitigate | a wrong "dead control" tells the operator their config is broken when the retailer's markup is. The field is set only when the page was read successfully and named no matching product; unparseable markup is excluded by `ld.unparseable`; the 2026-08-04 precedent is a gated test (`10-01`, `10-02`) |
| `T-10-02` | Repudiation | the record of the three live reads in `docs/retailer-evidence.md` | medium | mitigate | a read whose outcome is not written down is a request nobody can audit. Every read records its timestamp, its URL shape, its outcome and its spacing — including a refusal, which is the measurement — and an unspent read is recorded as unspent (`10-04`) |
| `T-10-03` | Denial of Service | Best Buy, through `check_bestbuy_browser` | medium | mitigate | three navigations, ≥300 s apart, additive to a daemon that is already polling. The cap is Dan's and is not the executor's to raise; a refusal ends the sequence rather than starting a retry (`10-04`) |
| `T-10-04` | Information Disclosure | anything written into `docs/retailer-evidence.md` from a live page | medium | mitigate | live Best Buy pages carry host paths and session-shaped tokens. `_redact_host_paths` already covers adapter details; every transcript pasted into the evidence log passes `scripts/identity_check.py --all`, and the redaction never names what it removed (`10-04`) |
| `T-10-05` | Tampering | `config/products.yaml`'s control set | medium | mitigate | a control swapped for one nobody read makes the health gate vouch for a page that may not exist. No control ships without a confirming live reading (`10-04`), and the durability verdict for every control is gated so it cannot be dropped (`10-03`) |

**There is no `T-10-SC` row, and that is stated rather than omitted.** This phase installs nothing
from npm, pip or cargo, so the package-legitimacy gate has nothing to audit.

**Residual carried, not fixed:** rung 3 surfaces no HTTP status, so a dead URL-addressed control at
Target cannot be distinguished from a reskin. Named in `10-03`'s D5 column as NOT SATISFIED, with
the fabricate-a-status remedy explicitly refused.

### Standing constraints every plan inherits

1. **Watched red before trusted.** Each new gate: run it against the unfixed code, **record the
   actual failure count**, then fix and record the pass. A test that has never failed is not a gate.
2. **Clear the caches between a perturbation and its revert.** `find . -name "__pycache__" -not -path
   "./.venv/*" -exec rm -rf {} + ; rm -rf .pytest_cache`. A same-second revert of a same-length edit
   leaves a valid `.pyc` and the interpreter keeps running the perturbed bytecode while `diff`,
   `git status` and `grep` all say the tree is clean. `CLAUDE.md` carries the measured account.
3. **Never round a claim up.** MET IN PART is shippable. Rewording a criterion so it passes is not.
4. **Superseded text is recorded beside, never edited away** — `docs/retailer-evidence.md` § 6. The
   durability sentence in `docs/adding-a-retailer.md` and any README cell this phase moves both take
   the dated form: quote the withdrawn text in full, then the measured facts that overruled it, then
   what survives.
5. **If a gate goes red on this phase's own prose, the prose changes.** At least four precedents.
   `scripts/identity_check.py` needs `--all` or `--staged`; never `--no-verify`; never add a value to
   the allow-list; never name a removed value in a commit message or a redaction note.
6. **M44 is the next free ident; M21–M24 are never filled;** the gap-marker count must not fall
   below 9.
7. **Standing invariants that must not move:** `Pacer.current_interval`'s body byte-unchanged
   (SHA-256 `6da39ac5d77ecd98cae80651c3b4d539253e88a1704fb4b1e814e6bf93449108`); `cli.watch_loop`
   keeps both clock terms (`delay + cycle_duration`); `MAX_BACKOFF_SECONDS` 6 h; `COOLOFF_SECONDS`
   259 200; `grep -c '<= STATE_MAX_AGE_SECONDS:' boty/pacing.py` = 2; `STATE_VERSION` = 2.
   **No plan in this phase touches `boty/pacing.py`.** A plan that finds it must justify it in
   writing first.
8. **Never write `state.json`, `pacer-state.json` or `served/boty/status.json`.** Copy to a scratch
   dir. **Never run `boty check`.** No live retailer request outside `10-04`'s three.
9. **No `systemctl restart boty` task.** Dan's call. That restart now carries Phases 8, 9 and 10.
10. `.venv/bin/python -m pytest`, never bare `python`. `export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh`
    before anything invoking `make`. `make verify-offline` exits 0 **and** its verdict line is read.
11. **Never invoke a `gsd-tools` state or phase WRITE subcommand.** Fourteen recorded corruptions of
    this repo's `STATE.md`, and the data-losing one survives on 1.11.0; an error return is not
    evidence that nothing was written. **No plan in this phase edits `STATE.md` or `ROADMAP.md`.**

---

## The nine collisions `10-01` settles in writing

These land in `10-DECISIONS.md` (`10-01`, Task 1) with the reasoning, before any production code
moves. Each is stated above; this is the index the decisions file must answer, one section per row.

| # | Collision | Where the outline argues it |
|---|---|---|
| 1 | The dead fact must be a FIELD, not `detail` prose | *The fact exists already* |
| 2 | Unparseable markup is not a dead control — the 2026-08-04 false dead | *The false dead* |
| 3 | The second producer is the HTTP status, and rung 3 has none | *The second producer* |
| 4 | `Health.dead_control` is `any`, `Health.refused` stays `all` | *`Health` needs a field too* |
| 5 | Arm precedence: dead ahead of `store_gap`, behind `refused` | *Arm precedence* |
| 6 | Criterion 2's mixed group — a refusal the breakage arm calls "not refused" | *Criterion 2's conjunction* |
| 7 | The dead arm carries a `Health.action` and therefore pages | *`Health.action`* |
| 8 | Nothing new is published to `status.json` | *Nothing new is published* |
| 9 | The read budget, its spacing, its counting unit and its refusal branch | *The read budget* / *If Best Buy refuses everything* |

---

## Artifacts this phase produces

Every symbol, so the executor creates these and not near-misses. Names marked *(candidate)* are the
plan writer's to fix; the shape is not.

**`boty/models.py`**
- `Result.unresolved` *(candidate)* — **declared last, after `read_at`, defaulted `False`**, on the
  `rung`/`extraction`/`store`/`shipping` precedent, with the meaning of the default written out:
  `False` is *"not established as unresolved"*, never *"resolves"*
- `Health.dead_control` *(candidate)* — declared last, defaulted `False`, `any`-quantified, with the
  difference from `refused`'s `all` argued at the field
- **deliberately absent:** no new `Availability` member — deadness is a fact about the target, not a
  stock verdict, and UNKNOWN is still the only honest availability for a page nobody could read

**`boty/fetch.py`**
- `is_unresolved(exc)` *(candidate)* — the exact mirror of `is_refusal`, `status in {404, 410}`, with
  the constant declared beside `REFUSAL_STATUSES` and the two kept visibly disjoint

**`boty/retailers.py`**
- `_verdict_from_html` — the no-offers/`sku is not None` branch sets `unresolved=True` **only when
  `ld.unparseable == 0`**; the unparseable case keeps today's verdict and today's message
- the five `is_refusal(exc)` sites gain `unresolved=is_unresolved(exc)`
- the `Blocked` arms are **untouched** — a refusal establishes nothing about resolution

**`boty/monitor.py`**
- `DEAD_CONTROL_ACTION` *(candidate)* — one constant, one spelling, on `STORE_PIN_ACTION`'s precedent
- `assess_health` — the dead arm, placed between `refused` and `store_gap`, and the mixed-group
  sentence that no longer claims "was not refused" about a group containing a refusal
- **`_is_store_gap` is NOT edited.** It is collateral of the precedence change, not a site: its
  predicate is correct and its docstring's argument is what the new arm's ordering rests on

**`config/products.yaml`**
- a numbered durability verdict beside **every** `control: true` entry, failures named per clause
- Best Buy's control target — **changed only if `10-04` confirmed a replacement by live reading**

**`docs/adding-a-retailer.md`**
- § *The rule a control has to satisfy* — the clauses numbered D1–D5, the original sentence quoted
  and kept, the extension dated
- the applied table: six controls, one verdict each, every failure named

**`docs/retailer-evidence.md`**
- § Best Buy — the three reads recorded beside the 2026-08-04 and 2026-08-03 records, never over
  them: what was asked, when, how far apart, what came back, and which reads went unspent

**`README.md`**
- the Best Buy row — **only if a cell's claim actually moved.** The matrix is gated against the code
  by `tests/test_support_matrix.py`, including `test_only_the_pinned_cells_say_unread`; if the gate
  bites, the prose changes

**`scripts/mutation_check.py`**
- `Mutation(ident="M44", ...)` on the dead-control behaviour, with the prose block carrying what it
  rebuilds, why it earned an ident, the recorded kill-set comparison, the rejected anchor, and an
  `IF IT EVER SURVIVES:` paragraph

**`CLAUDE.md`**
- the registry counts advanced in the same commit as M44

**`tests/`**
- `tests/test_models.py` — the new fields, their defaults, and the `refused`/`unresolved` mutual
  exclusion invariant
- `tests/test_retailers.py` — the true dead from `unresolved-sku`, the false dead from unparseable
  markup, and the `Blocked` arm proving a refusal sets nothing
- `tests/test_fetch.py` — `is_unresolved` against 404/410/403/429/500 and a transport error
- `tests/test_monitor.py` — criterion 1's three states asserted **separately**, criterion 2's two
  halves asserted separately, and the precedence pair against a store-pin-absent Walmart control
- `tests/test_control_durability.py` *(new)* — every `control: true` entry carries a verdict against
  every clause the doc declares; a control with no verdict, and a clause the doc drops, both redden

**New files**
- `.planning/phases/10-a-control-that-cannot-die/10-DECISIONS.md` — the nine collisions
- `.planning/phases/10-a-control-that-cannot-die/COVERAGE.md` — **already written at planning time**,
  one line, and unlike Phases 8 and 9 it declares that this phase **does** make external calls.
  `10-01` **asserts** its content rather than creating it

## OUTLINE COMPLETE
