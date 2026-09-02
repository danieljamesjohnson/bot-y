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
| `10-01` | **The collisions decided in writing, and the dead-control state reachable without a wire.** Write `10-DECISIONS.md` settling all nine collisions before any production code moves, then a tracer: a captured Best Buy product page driven end-to-end — adapter → `Result` → `assess_health` — until a control whose SKU the page does not carry is reported as a **dead control** and not as a broken detector, on a predicate measured against both fixtures rather than assumed. Definition of Done item 3's second half, closed offline. Also **re-anchors M30** and **extends two four-arm partitions to five**, both in this wave, because both go wrong the moment the fifth arm exists. | 1 | — | REQ-24 |
| `10-02` | **The three states, distinct, and criterion 2's conjunction asserted in both halves.** Generalise the producer: an HTTP 404/410 is a dead control at every rung-1 retailer, and the 2026-08-04 false-dead precedent — Best Buy served unparseable JSON-LD and the SKU branch fired on a SKU that was perfectly alive — is gated so unreadable markup stays *detector broken*. Then arm precedence, and the mixed group where a dead control and a real refusal are both true at once — which is where the `assess_health` tests that live in `tests/test_pacing.py` collide. | 2 | `10-01` | REQ-24 |
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

### THE PREMISE — and it may be false. No plan asserts it; `10-04` measures it

REQ-24's last sentence is *"Best Buy's current dead control is repaired"*, and criterion 3 is built
on it. **Every piece of evidence in this tree points the other way**, and the plan writers have to
meet that before they meet the criterion, because a phase that repairs something never shown broken
is the exact failure this repository's standard exists to catch.

**Three facts, checked against the tree on 2026-09-02:**

1. **`6577129` was never the control.** It is the SKU this repo once carried for the **GO Plus +
   itself**, it resolves to nothing, it was removed from `config/products.yaml` with the finding
   recorded in prose, and `docs/retailer-evidence.md` describes the identification as unconfirmed
   and probably wrong. It is the subject of the `unresolved-sku` fixture. **A dead product SKU is
   not a dead control.**
2. **`6216393` is the control, and there is a SUCCESSFUL read of it on the record.**
   `docs/retailer-evidence.md` § Best Buy: the bare SKU *"Redirected to the product page,"*
   1,109,548 B, title `Pokémon: Let's Go, Pikachu! Nintendo Switch HACPADW2A - Best Buy`, canonical
   `.../product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ/sku/6216393`, exactly one offer:
   `available=True, price=59.99, seller='Best Buy'`.
3. **The only failing reading of it is a HOST failure, and it is stale.** The `make verify`
   transcripts read `fetch failed: no Chrome/Chromium binary found — set BOTY_BROWSER_PATH`. That is
   not a dead control, not a refusal and not a reading — and `10-CONTEXT.md` records the capability
   claim as stale, measured 2026-09-02: Playwright chromium is present at `~/.cache/ms-playwright`,
   three builds including a headless shell.

**So the incumbent may be alive, dead, refused, or unreadable on this host, and which one is NOT
ESTABLISHED.** `10-04`'s read 1 exists to establish it, under a branch table written before the
request. **No plan may assert the control is dead** — not in prose, not in a test name, not in a
commit message.

**If read 1 shows the control alive**, criterion 3's honest verdict is that **there was nothing to
repair**: the defect was in a record, not in a config, and the phase's deliverable there is the
correction plus a replacement chosen on durability grounds. Criteria 1, 2, 4 and 5 carry the phase
in that branch exactly as they do in every other, because none of them depends on the premise —
which is why they are all closed offline before the first request.

### The premise correction is PROVABLE TODAY, offline, and it is this phase's best artifact

**It does not need read 1 and must not be conditioned on it.** The evidence log already settles what
"Best Buy's dead control" refers to, and `10-01` records it in writing in wave 1 — four weeks before
any request, and independent of what any request returns.

| what the record says | where |
|---|---|
| SKU `6216393`, the control, read `in_stock $59.99 · ld+json: InStock from Best Buy` in **four** separate `make verify` transcripts | `docs/retailer-evidence.md` L1642, L1884, L2286, L2413 |
| the same SKU's search redirect transcribed in full — 1,109,548 B, correct title, one first-party offer | L860 |
| the **only** "did not resolve" for that SKU is the documented **2026-08-04 FALSE dead**, from unparseable markup on a SKU that was alive | L960 |
| the two most recent attempts are `no Chrome/Chromium binary found` — a **host** failure, at the Phase 5 close (2026-08-10) and the Phase 7 close (2026-08-17) | L3482, L4397 |
| SKU `6577129` — the one that genuinely resolves to nothing — was a **product watch, already removed from config**, recorded as *unconfirmed and probably wrong* | L822, L868, L901 |

**The honest statement, and it is neither of the two comfortable ones:**

> **Best Buy's control has never been shown dead. It was last shown ALIVE in early August, and it
> has been unmeasured for roughly four weeks.** The evidence is **absent-then-stale**, not contrary.

Do not round that to *the control is dead* — nothing establishes it. Do not round it to *the control
is fine* either — a four-week-old reading is a reading about early August. **`10-05`'s criterion 3
row carries this finding whatever read 1 returns**, because it was established offline and a live
result cannot unestablish it: a refusal would leave it standing, a successful read would confirm it,
and an unresolved result would date the death to somewhere in a four-week window this record bounds.

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

### The predicate, stated exactly — and MEASURED against both captures rather than reasoned about

**Two obvious readings were tried at planning time and BOTH FAIL.** Measured 2026-09-02 with
`.venv/bin/python` over `boty.parse.ldjson_read` and the raw fixture text:

| page, read for | `blocks` | `unparseable` | our sku in offers | `rel="canonical"` points at |
|---|---|---|---|---|
| `unresolved-sku.html`, sku 6577129 | **0** | 0 | no | `/site/searchpage.jsp?id=…&st=6577129` |
| `pikachu-control.html`, sku 6216393 | 3 | 0 | **yes** | `/product/…/sku/6216393` |
| `pikachu-control.html`, sku 6577129 | 3 | 0 | **no** | `/product/…/sku/6216393` |
| the 2026-08-04 live page (from the record) | 3 | **3** | no | a product page |

- **`unparseable == 0` alone is wrong**: it marks a page carrying *no* JSON-LD at all — a reskin,
  a partial render — as a dead control. That is `T-10-01` (rated high) happening on the day it
  ships.
- **`blocks > 0 and unparseable == 0` is also wrong**: the true-dead capture has `blocks == 0`, so
  that predicate makes the dead state **unreachable from the fixture the phase is built on**.

**There is a third discriminator, and it is measured, positive, and retailer-maintained.** Best Buy
publishes a `rel="canonical"` link on both page shapes and they differ in exactly the way the
question asks: a SKU that resolves gets a canonical pointing at a **product** path; a SKU that
resolves to nothing gets one pointing at the **search endpoint**. That is Best Buy's own statement
about what page you are on — the same class of commercially load-bearing markup `README.md` already
argues the schema.org feed is, and the opposite of the presentation matching this repository
distrusts.

**So the predicate `10-01` ships, and `10-02` gates, is a disjunction of two measured facts:**

> A SKU-addressed reading is **unresolved** when
> **(A)** the page's canonical link points at the search endpoint rather than a product path — the
> retailer saying no product was resolved; **or**
> **(B)** structured markup was present and parsed (`blocks > 0` and `unparseable == 0`) and no
> Product on it carries the requested sku — a page about somebody else's product.
> It is **never** unresolved when markup was present and could not be parsed, which is the
> 2026-08-04 case.

Compare canonical URLs on **path**, never on the whole string: the request is
`…/site/searchpage.jsp?st=<sku>` and the canonical adds a category parameter, so a whole-string
comparison would be false on the day it was written.

**THE RESIDUAL, NAMED RATHER THAN CLOSED.** A page with **no canonical and no parseable structure**
— `blocks == 0`, no canonical link — is not distinguishable at this layer from a reskin or a broken
render, and it does not become a dead control. `10-01` pins that with a test, states it beside the
predicate in the code, and `10-03` carries it into Best Buy's D5 column as **PARTIAL**, not as a
pass. This is the honest version of the thing the two rejected readings were each trying to get for
free.

**Which fixture proves which half.** `pikachu-control.html` read for a sku it does not carry is
**(B)**, and it is what `10-01`'s tracer drives — a real capture of a real Best Buy product page,
reaching the dead state with no live read, which is Definition of Done item 3's second half.
`unresolved-sku.html` is **(A)** by its canonical, and it also pins the residual: with the canonical
check removed it must fall back to the ambiguous case rather than to a dead control. The 08-04
episode is the false dead, and `tests/test_parse.py` already carries the broken-escape material.

Reading the canonical needs a small reader in `boty/parse.py`, tested there, beside the other
readers. It is not written inline in `_verdict_from_html`.

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
the one that needs work. A group of one dead control and one refused control satisfies neither
`all(refused)` nor `all(_is_store_gap)`, so it falls to the breakage arm — whose sentence asserts
that nothing was refused, which is *false* about that group.

**State its reachability precisely, because today's config falsifies the loose version.**
`assess_health` groups by retailer and every retailer here has **exactly one** control, so a mixed
group is **not reachable in the shipped configuration**. It is reachable the moment any retailer
gains a second control — which `10-03`'s D4 clause makes more likely, not less, since it asks every
control for a recorded reserve. So this is a defect **in the code**, latent rather than live, and the
plans say that rather than claiming a wrong alert is being produced today. `10-02` owns it.

**At the `Result` level the two are mutually exclusive and that is asserted as an invariant:** a
refusal means no page came back, so nothing about resolution was established — the same first line
`_is_store_gap` opens with. `refused and unresolved` is never both True on one `Result`.

### Arm precedence, and the one non-obvious ordering

`refused` → **dead** → `store_gap` → breakage.

- **`refused` stays first, unchanged.** A refusal produced no page, so nothing else could have been
  established.
- **dead goes ahead of `store_gap`, and this is a decision rather than a detail.** `_is_store_gap`
  returns `True` whenever `watch.store_id is None` — *"read off the config and therefore true
  whatever the page did"* — and the pin is absent in **any process that does not load
  `~/.config/boty/env`**, which is every test and every dev shell. (`QUESTIONS.md` § 0f: the value
  was supplied on 2026-08-25 and written to that file, mode 600; it reaches the daemon at the next
  restart, which is still deferred. It is **set on disk and not yet in effect** — never "unset",
  and never printed, derived or named.) So a dead Walmart control would today be reported as a
  store gap. A target that does not resolve makes the store question moot: **a page about no
  product cannot be a page about the wrong store.** Both facts are about our config; deadness is
  the more specific one and it is also the one whose remedy is different.
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

**How many controls there are, and why the obvious command answers wrong.**
`grep -c 'control: true' config/products.yaml` returns **7**. There are **6** controls: the seventh
match is a **comment** on the transition watches, which reads that they are deliberately *not*
`control: true`. Every gate and every count in `10-03` therefore goes through the config **loader**,
never through a grep — the loader is what `control_check.py` and `assess_health` both filter on, and
a gate that counts a comment is a gate measuring the file rather than the configuration.

**What `10-03` is expected to name, stated in advance so a softer finding is visibly a softer
finding.** These are predictions, not verdicts; `10-03` measures each control against the shipped
rule and records what it actually finds:

| control | expected verdict |
|---|---|
| gamestop — PS5 console | **FAILS D2, D3** — a console: released, generation-bound. The rule's own words already forbade it |
| bestbuy — Pokémon Let's Go, Pikachu! (Switch) | **FAILS D2, D3** — a specific game SKU on an ended generation, and **FAILS D4**: its recorded reserve (`Let's Go, Eevee!`, `docs/retailer-evidence.md`) is the same class of product and fails the same clauses |
| nintendo — HDMI cable | **FAILS D3** — a generation-bound accessory, and **FAILS D4** for the same reason: the reserve it names (the AC adapter) is generation-bound too |
| walmart — Great Value whole milk | passes D1–D3; **D4 not recorded**. Separate finding, recorded beside and not as a durability failure: it is store-pinned, and the pin is **set on disk since 2026-08-25 and not yet in effect** — it reaches the daemon at the next restart, and any process that does not load that env file sees no pin at all. An availability fact about a deferred restart, not a durability one, and the value is only ever measured as a count |
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

### What counts as a spent read — the cap is Dan's, and it has exactly one exemption

A budget with an open-ended exemption is not a budget. So the counting rule is stated here, restated
in `10-DECISIONS.md` § *Collision 9*, and restated again in `10-04`'s branch table, and it is the
same three sentences in all three places:

1. **Any navigation attempt that leaves this host counts as SPENT, whatever it returns.** A timeout,
   a TLS reset, a partial render, a challenge page, a 4xx, a 5xx, an empty body — all spent. Best Buy
   received a request; what came back does not refund it.
2. **Only a PRE-NAVIGATION failure is exempt**, and only because no packet reached Best Buy: chromium
   could not start, or no browser binary was found. That is a host fact and it is recorded as one.
3. **The exemption may be taken AT MOST ONCE.** A second pre-navigation failure **ends the
   sequence**, and criterion 3 closes on what was measured up to that point. There is no
   fix-and-retry loop, because "fix the host and try again" is how a cap of three becomes a cap of
   whatever the executor's patience allows.

**Worst case, stated so it can be checked by counting:** one exempt pre-navigation failure, then
reads 1, 2 and 3 — **three navigations, and never more, under every branch.** If the exemption is
taken twice, the total is **one navigation or zero** and the phase closes on that.

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

### Two tests and one mutation that already exist, and collide — all three in WAVE 1 or 2

**A — `scripts/mutation_check.py`'s M30 anchors on a line Collision 7 changes, and it breaks
criterion 5's own gate from wave 1.** M30's `search=` is the exact literal
`action=STORE_PIN_ACTION if store_gap else ""`. Adding a second arm that carries an action rewrites
that line. `apply_mutation` **raises** on a missing anchor and the harness runs inside
`make verify-offline`, so between wave 1 and wave 5 the gate criterion 5 is judged by would be
broken — and it would look like this phase's own regression rather than like an anchor that moved.

**`scripts/mutation_check.py` is therefore in `10-01`'s `files_modified`, and `10-01` re-anchors M30
in its own wave.** The precedent is in that file already: M2 and M4 were re-pointed when the lines
they anchored on moved, and the re-point was recorded rather than silently applied. Two obligations
come with it: **M30's `breaks=` sentence must still describe the behaviour it destroys** (the one
health state a person can close stops saying so), and its comment block cites
`test_exactly_one_arm_names_something_a_person_can_do` — a test whose own claim this phase changes,
which is collision C.

**B — `tests/test_pacing.py` holds `assess_health` tests, and one of them is exactly `10-02` Task 3's
subject.** `test_one_non_refusal_among_refusals_is_treated_as_breakage` asserts on the reason of a
group **containing a refusal** — that it is treated as breakage and carries the unestablished-cause
marker. `10-02` rewrites what such a group says. Six `assess_health` tests live in that file, which
is not where a reader would look for them; **`tests/test_pacing.py` is in `10-02`'s
`files_modified`**, and the rewrite keeps that test's *point* (a non-refusal among refusals is never
swallowed) while its expected sentence moves.

**C — `tests/test_alert_text.py` holds two partitions over FOUR arms, and a fifth arm makes them
FALSE WITHOUT MAKING THEM RED.** This is the worst outcome available under this repository's
standard and it is the reason this section exists.

- `test_exactly_the_two_unknown_causes_say_so` — *"the partition, across all four arms of
  `assess_health`"* — builds a dict of four named arms and asserts which carry the
  unestablished-cause marker.
- `test_exactly_one_arm_names_something_a_person_can_do` — the 2026-08-12 partition over the same
  four arms, whose docstring says *"the answer has to stay ONE"*, and whose own body explains that
  a single test asserting one flag would go on passing while the other rule quietly inverted.

Both enumerate their arms **by name**. `10-01` adds a fifth arm that carries an action and does not
carry the unestablished-cause marker. Neither test constructs it, so **both keep passing while both
docstrings have become false** — "all four arms" is now four of five, and "the answer has to stay
ONE" is now two.

**`tests/test_alert_text.py` is in `10-01`'s `files_modified`, and `10-01` extends both partitions to
five arms in its own wave.** The plan says explicitly: **do not confirm these by running them and
seeing green.** Green is the symptom. The check is whether the arm count in each partition equals the
arm count in `assess_health`, and the docstrings must be corrected in the dated form — the withdrawn
sentence quoted, what overruled it, and what survives, which for the action partition is the *rule*
(a push costs somebody writing down what to DO) rather than the *number*.

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

**Residuals carried, not fixed — two, both named in `10-03`'s D5 column rather than papered over:**
rung 3 surfaces no HTTP status, so a dead URL-addressed control at **Target** cannot be
distinguished from a reskin (**NOT SATISFIED**, with the fabricate-a-status remedy explicitly
refused); and at **Best Buy** a page carrying neither a canonical link nor parseable structure is
not distinguishable from a reskin either (**PARTIAL**, pinned by a test in `10-01`). Neither is
closed by this phase and neither is described as closed.

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

## The ten collisions `10-01` settles in writing

These land in `10-DECISIONS.md` (`10-01`, Task 1) with the reasoning, before any production code
moves. Each is stated above; this is the index the decisions file must answer, one section per row.
Collision 10 is not a conflict between two courses of action — it is a **finding**, and it is in this
list because it has to be settled in writing before anything else in the phase can be described
honestly.

| # | Collision | Where the outline argues it |
|---|---|---|
| 1 | The dead fact must be a FIELD, not `detail` prose | *The fact exists already* |
| 2 | The predicate, stated EXACTLY: canonical-path OR parsed-markup-without-our-sku, never unparseable markup — plus the no-canonical residual, named | *The false dead* / *The predicate, stated exactly* |
| 3 | The second producer is the HTTP status, and rung 3 has none | *The second producer* |
| 4 | `Health.dead_control` is `any`, `Health.refused` stays `all` | *`Health` needs a field too* |
| 5 | Arm precedence: dead ahead of `store_gap`, behind `refused` | *Arm precedence* |
| 6 | Criterion 2's mixed group — a refusal the breakage arm calls "not refused" | *Criterion 2's conjunction* |
| 7 | The dead arm carries a `Health.action` and therefore pages | *`Health.action`* |
| 8 | Nothing new is published to `status.json` | *Nothing new is published* |
| 9 | The read budget: allocation, spacing, counting unit, **what counts as spent and the single one-shot exemption**, and the refusal branch | *The read budget* / *What counts as a spent read* / *If Best Buy refuses everything* |
| 10 | **What "Best Buy's dead control" actually refers to** — settled offline from the record, with line citations, and carried by `10-05` whatever read 1 returns | *The premise correction is provable today* |

---

## Artifacts this phase produces

Every symbol, so the executor creates these and not near-misses. Names marked *(candidate)* are the
plan writer's to fix; the shape is not.

**`boty/parse.py`**
- `canonical_url(html)` *(candidate)* — the retailer's own `rel="canonical"` link, read beside the
  other readers and tested there. Returns nothing when the page carries none, which is the residual
  case and not an error

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
- **M30 re-anchored in `10-01`**, on the M2/M4 precedent, with the re-point recorded and its
  `breaks=` sentence still describing the behaviour it destroys — otherwise `apply_mutation` raises
  on a missing anchor and `make verify-offline` is broken from wave 1 to wave 5
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
  halves asserted separately, and the precedence pair against a Walmart control whose pin is not in
  effect in a test process
- `tests/test_parse.py` — the canonical reader, including a page that carries none
- `tests/test_alert_text.py` *(`10-01`)* — both four-arm partitions extended to five, in the dated
  form, and NOT confirmed by seeing green
- `tests/test_pacing.py` *(`10-02`)* — the `assess_health` tests that live there, including the
  mixed-group one whose expected sentence moves while its point survives
- `tests/test_control_durability.py` *(new)* — every control **loaded through the config loader**
  (never grepped: a grep counts the comment that says the transition watches are deliberately not
  controls) carries a verdict against every clause the doc declares; a control with no verdict, and a
  clause the doc drops, both redden

**New files**
- `.planning/phases/10-a-control-that-cannot-die/10-DECISIONS.md` — the nine collisions
- `.planning/phases/10-a-control-that-cannot-die/COVERAGE.md` — **already written at planning time**,
  one line, and unlike Phases 8 and 9 it declares that this phase **does** make external calls.
  `10-01` **asserts** its content rather than creating it

## OUTLINE COMPLETE
