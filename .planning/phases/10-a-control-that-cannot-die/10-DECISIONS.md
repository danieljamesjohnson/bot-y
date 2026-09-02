# Phase 10: A Control That Cannot Die — Decisions

**Phase:** 10-a-control-that-cannot-die · **Written:** 2026-09-02 · **Wave:** 1 (`10-01`) · **Requirement:** REQ-24

These are the decisions wave 1 takes so that waves 2, 3, 4 and 5 do not take them mid-flight.
Everything below is settled in writing **before any production code moves** — Task 1 of `10-01`
changes no source file.

A later wave that disagrees must reverse a decision here in the dated form this repository uses
(`docs/retailer-evidence.md` § 6: quote the withdrawn text in full, then the measured facts that
overruled it, then what survives), rather than quietly deciding otherwise.

**Ten sections, one per collision.** Collision 10 is not a choice between two courses of action — it
is a **finding**, provable offline today, and it is in this list because nothing else in the phase
can be described honestly until it is written down.

---

## Collision 1 — the dead fact is a FIELD, not `detail` prose

**Decided: a boolean field on `Result`, declared last with a default of `False`.**

`retailers._verdict_from_html` already knows the fact. Its no-offers branch, guarded on a SKU having
been bound, writes:

> `sku {sku} did not resolve to a product page — no schema.org Product on it carries that sku`

and that sentence lands in `Result.detail`, which is the one place `monitor.assess_health` may not
read.

**The refused alternative, stated so it is not re-proposed as the cheap fix:** `assess_health` could
substring-match that message. It would work today, need no new field, and touch one file. It is
refused because `_is_store_gap`'s own docstring already argues the case, in this module, about this
exact class of decision:

> *Detected from FACTS, not from `detail` prose … Matching on the message text would tie this to
> prose that is edited far more often than the condition is — the anchoring lesson
> `scripts/mutation_check.py`'s M2 comment already paid for once.*

M2 was re-anchored on 2026-08-04 when the prose on its branch moved. That is a measured precedent
in this repository, not a hypothetical: the message drifted, the anchor did not, and nothing went
red. A health arm keyed to a sentence would fail the same way and be **silent** about it, which is
strictly worse than a mutation raising.

**The shape, on the standing precedent.** `rung`, `extraction`, `store`, `shipping` and `read_at`
were each appended to `Result` with a default, for one stated reason: every pre-existing
construction site stays valid and keeps its meaning. This field is appended the same way, after
`read_at`, and its default carries a written meaning — `False` is *"not established as
unresolved"*, never *"resolves"*. Those are different claims and only one of them is measured.

**The name is `Result.unresolved`.** The outline marked it *(candidate)*; it is fixed here. It reads
correctly at the site that sets it (`unresolved=True` on the branch whose message already says
*"did not resolve"*) and at the site that reads it, and it does not overclaim: a page can be
unresolved without anybody knowing why.

---

## Collision 2 — the predicate, stated EXACTLY, with the residual named

**This section states the predicate in a form somebody could implement from without inventing
anything.** It is the most consequential decision in the phase, both easy readings of it are wrong,
and the reasons are measured rather than argued.

### The precedent that makes a discriminator non-optional: the 2026-08-04 false dead

`docs/retailer-evidence.md` § *2026-08-04 — Best Buy served JavaScript-escaped JSON-LD, and the
control caught it*. The control watch went UNKNOWN at ~16:35 with:

> `sku 6216393 did not resolve to a product page — no schema.org Product on it carries that sku`

**The SKU was perfectly alive.** Best Buy had served three `ld+json` blocks of which **zero**
parsed — 8 × `\'` inside strings, 34 × a literal `\n` outside them — so `ldjson_offers` found no
Product and the branch fired. That is criterion 1's *third* state (the page arrived and the
extractor could not read it) wearing the *first* state's message.

If the field were set on `not offers and sku is not None` alone, this phase would ship a mechanism
that calls a live control dead every time a retailer deploys bad markup — **the same misattribution
it exists to fix, pointed the other way.** That is `T-10-01`, rated high, happening on the day it
ships.

### What was measured, and why both easy readings fail

Re-measured 2026-09-02 by `10-01`'s executor with `.venv/bin/python` over `boty.parse.ldjson_read`
and a `rel="canonical"` scan of the raw fixture text. These are this executor's own numbers, not
the planner's carried forward:

| page, read for | bytes | `blocks` | `unparseable` | our sku in offers | `rel="canonical"` points at |
|---|---|---|---|---|---|
| `unresolved-sku.html`, sku 6577129 | 921,732 | **0** | 0 | no | `/site/searchpage.jsp?id=pcat17071&st=6577129` |
| `pikachu-control.html`, sku 6216393 | 1,138,265 | 3 | 0 | **yes** (`InStock`, 59.99, `Best Buy`) | `/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ/sku/6216393` |
| `pikachu-control.html`, sku 6577129 | 1,138,265 | 3 | 0 | **no** | `/product/…/sku/6216393` |
| the 2026-08-04 live page (from the record, L963-972) | — | 3 | **3** | no | a product page |

- **`unparseable == 0` alone is wrong.** It is satisfied by a page carrying *no* JSON-LD at all — a
  reskin, a partial render, a soft block that matched no known challenge phrase — and would mark
  every one of them a dead control.
- **`blocks > 0 and unparseable == 0` is also wrong.** The true-dead capture has `blocks == 0`, so
  that predicate makes the dead state **unreachable from the fixture this phase is built on**. It
  would pass review and gate nothing.

**Both are stated before the one that works, because each is what a reader arrives at first.**

### The third discriminator, and why it is trustworthy

Best Buy publishes a `rel="canonical"` link on both page shapes and they differ in exactly the way
the question asks: a SKU that resolves gets a canonical pointing at a **product** path; a SKU that
resolves to nothing gets one pointing at the **search endpoint**. That is Best Buy's own statement
about what page you are on — the same class of commercially load-bearing markup `README.md` already
argues the schema.org feed is, and the opposite of the presentation matching this repository
distrusts.

### THE PREDICATE

> A SKU-addressed reading is **unresolved** when
> **(A)** the page's own canonical link points at the **search endpoint** rather than a product
> path — the retailer saying no product was resolved; **or**
> **(B)** structured markup was present and parsed (`blocks > 0` **and** `unparseable == 0`) and no
> Product on it carries the requested sku — a page about somebody else's product.
>
> It is **never** unresolved when markup was present and could not be parsed. That is the
> 2026-08-04 case and it keeps today's verdict and today's message.

**Compared on PATH, never on the whole URL.** The request is `…/site/searchpage.jsp?st=<sku>` and
the canonical measured above is `…/site/searchpage.jsp?id=pcat17071&st=<sku>` — the canonical
carries a category parameter the request does not. A whole-string comparison would have been false
on the day it was written. The comparison is `urlsplit(canonical).path == urlsplit(search_url).path`
against the URL `retailers.bestbuy_product_url` itself builds, so the two cannot drift apart.

**HTML entities are unescaped before parsing.** The measured canonical href reads
`…?id=pcat17071&amp;st=6577129` in the raw markup. The path comparison is unaffected either way,
and unescaping is done anyway so a future reader of the query string is not handed a lie.

### THE RESIDUAL, named here and not only in the code

**A page with no canonical link AND no parseable structure is not a dead control.** It is not
distinguishable at this layer from a reskin or a broken render, so it keeps today's verdict, it is
pinned by a test in `10-01` Task 3, and `10-03` carries it into Best Buy's D5 column as **PARTIAL**
— not as a pass.

**What that costs, stated rather than hidden:** a page whose markup is broken **and** whose product
is genuinely gone reads as a detector failure rather than as a dead control. That is the wrong
answer. It is the right direction, because it **claims less** — the breakage arm says the cause is
not established, which is true, where a dead-control verdict would tell the operator their config is
broken on no evidence.

This is the honest version of the thing both rejected readings were each trying to get for free.

---

## Collision 3 — the second producer is the HTTP status, and rung 3 has none

**Decided: `fetch.is_unresolved(exc)` — `status in {404, 410}` — as the exact mirror of
`is_refusal`, wired at the `is_refusal(exc)` sites in `boty/retailers.py`. That is `10-02`'s work,
not `10-01`'s.**

Best Buy is addressed by SKU through a search redirect, so its death is a *resolution* fact. Every
other retailer here is addressed by URL, and a dead target there is an **HTTP 404** — which
`fetch.get` raises as a `FetchError` carrying a status, and which `is_refusal` correctly does **not**
treat as a refusal (`REFUSAL_STATUSES` is 401/403/429). So today a 404 on a control reaches the
breakage arm and is reported as a probably-broken detector: **the identical defect, at five
retailers rather than one.**

The two constants stay visibly disjoint, declared beside each other, so a reader can see at a glance
that a refusal and a deletion are different facts.

**THE GAP, RECORDED PLAINLY RATHER THAN DISCOVERED LATER.** `boty/browser.py` returns
`Page(status=200)` unconditionally, and its own comment says why:

> *the simple API does not surface the main frame's response status, so there is no real status to
> report and inventing one would be worse than saying so.*

So at rung 3 there is no status to read. Best Buy is covered by the resolution producer above;
**Target is not covered by either** — a delisted Target control renders Target's own 404 page, reads
no offers, and is indistinguishable from a reskin at this layer.

**Refused remedy:** inventing a status in `boty/browser.py`. It would put a fabricated fact into a
`Page`, and that comment already argues why. The honest route for a future phase is the response
object, not a constant. `10-03` records this as a **named gap in the durability rule's D5 clause**,
never as a passing verdict.

---

## Collision 4 — `Health.dead_control` is `any`, `Health.refused` stays `all`

**Decided: the new `Health` field is `any`-quantified over the broken controls; `refused` keeps its
`all`.** The difference is argued at the field itself, so nobody later "fixes" the inconsistency.

`assess_health`'s existing arms use `all(...)` and the reasoning is already in the code: *"if even
one control failed for a reason that is NOT a refusal, something may really be wrong and the louder
reading is the safe one."*

**That reasoning is about a refusal specifically, and it does not transfer.** A refusal **excludes
knowledge** of everything else — no page came back, so nothing about the store, the markup or the
product was established. It is therefore only reportable when it is the whole story.

**Deadness excludes nothing.** A target that does not resolve is established per-watch, off our own
config, from a page we successfully read. It does not become less established because a sibling
control failed for another reason. One dead control in a group of three is still one dead control,
and the operator still has one line to change in `config/products.yaml`.

---

## Collision 5 — arm precedence: refusal, then dead, then store gap, then breakage

**Decided: `refused` → `dead` → `store_gap` → breakage.**

- **`refused` stays first, unchanged.** A refusal produced no page, so nothing else could have been
  established. Moving anything ahead of it would name a cause nobody measured.
- **breakage stays last, unchanged.** It claims least.
- **dead goes AHEAD of `store_gap`, and this is the non-obvious half.**

`_is_store_gap` returns `True` whenever `watch.store_id is None` — *"read off the config and
therefore true whatever the page did"*. The pin is absent in **any process that does not load the
daemon's `EnvironmentFile`**, which is every test and every dev shell. So without this ordering, a
dead Walmart control would be reported as a store gap: the wrong remedy, in the right file.

**A page about no product cannot be a page about the wrong store.** Both facts are about our config;
deadness is the more specific one, and it is also the one whose remedy differs.

**A correction this section must not repeat.** Earlier records in this project describe
`WALMART_STORE_ID` as *"deliberately unset"*. That was true from 2026-08-10 to 2026-08-25 and is
**stale**: `QUESTIONS.md` § 0f records that Dan supplied it on 2026-08-25 and it was written to the
daemon's mode-600 `EnvironmentFile` outside the repository. It is **set on disk and not yet in
effect**, because `EnvironmentFile=` is read once at process start and the restart is still Dan's
and still deferred. The value is measured only ever as a **count**, never read, derived, inferred or
printed. The precedence argument above does not depend on which of those two states it is in — a
test process loads no `EnvironmentFile` either way.

---

## Collision 6 — the mixed group, and the refusal it silences

**Decided: the group's reason names every cause that was established and claims no single one.
`Health.refused` keeps its `all` meaning. `10-02` implements it; `10-01` does not touch it.**

Today a group of one dead control and one refused control satisfies neither `all(c.refused)` nor
`all(_is_store_gap(c))`, so it falls to the breakage arm — whose sentence is:

> *a control product did not read IN_STOCK **and was not refused**, so readings from this retailer
> are unverified…*

That sentence is **false** about that group. One of them was refused. A real refusal, silenced by a
dead control, in the shipped code.

**Its reachability, stated precisely, because the loose version is falsifiable.** `assess_health`
groups by retailer and every retailer in `config/products.yaml` has **exactly one** control, so a
mixed group is **not reachable in the shipped configuration**. It becomes reachable the moment any
retailer gains a second control — which `10-03`'s D4 clause makes *more* likely, since it asks every
control for a recorded reserve. So this is a defect **in the code**, latent rather than live, and no
plan may claim a wrong alert is being produced today.

**Refused alternative:** making `Health.refused` an `any`. It is refused because that field is read
by `boty/status.py`, by `cli.watch_cycle`'s paging filter and by `notify`, and it would come to mean
something different at each — *"the retailer refused us"* versus *"something here was refused"* —
with no consumer updated to notice.

---

## Collision 7 — the dead arm carries an action, and therefore pages

**Decided: the dead-control arm carries a `Health.action` naming `config/products.yaml`.** One
constant, one spelling, on `STORE_PIN_ACTION`'s precedent: `DEAD_CONTROL_ACTION`.

`Health.action` is *"what a person can DO about this state, in one sentence — and the whole of what
makes it worth a push"*. Today exactly one arm carries one. A dead control's remedy is the same
shape: the SKU or URL in `config/products.yaml` names a product that no longer exists, and somebody
has to choose another. Unlike a refusal and unlike breakage, **its cause is established**, which is
the property `action` exists to reward.

**The counter-argument, recorded beside the decision rather than omitted.** A second pageable state
is more traffic to a phone, and Dan's bar is *"never hit the user unless its something they can buy
or actually do"* (2026-08-12, the second time he raised it). Weighed against: this state names a
one-line edit in a tracked file, which is squarely inside his bar; and it fires **at most once per
failure episode** through the existing `warned` memory in `cli.watch_cycle`. **No new sender is
needed** — the existing `pageable = [h for h in unhealthy if h.action]` filter picks it up, and the
existing failed-delivery branch already rolls the memory back. An unwired send would be *"not a
retry — it is a drop nothing will ever mention again"*.

**The arm does NOT carry `CAUSE_UNKNOWN`**, for the same reason the store-gap arm does not: saying
the cause is not established about a cause we can name is the same dishonesty pointed the other way.

### The three things this decision BREAKS, all of them `10-01`'s own collateral

They are repaired in this wave. None is optional.

**1. M30's mutation anchor.** `scripts/mutation_check.py` M30 searches for the literal

```
                    action=STORE_PIN_ACTION if store_gap else "",
```

and this decision rewrites that line. `apply_mutation` **raises** on a missing anchor and the harness
runs inside `make verify-offline`, so an un-repaired anchor breaks criterion 5's own gate from wave 1
to wave 5 — and it would read as this phase's regression rather than as an anchor that moved. The
precedent for re-pointing is in that file already (M2 in 2026-08-04, M4 in 2026-08-11, M25/M26,
M33 twice, M36): the re-point is **recorded**, never silently applied, and `breaks=` keeps describing
the **behaviour** destroyed rather than the literal.

**Expected, and not a regression:** `make verify-offline` fails with a missing anchor between
`10-01`'s Task 2 and Task 3. Task 3 closes it.

**2. `test_exactly_one_arm_names_something_a_person_can_do`** — its docstring says the answer *"has
to stay ONE"*, and the answer becomes two.

**3. `test_exactly_the_two_unknown_causes_say_so`** — *"the partition, across all four arms"*, and
there are now five.

**Both tests enumerate their arms BY NAME and neither constructs the new one, so both keep passing
while both have become false.** This decision says that plainly because the natural way to check
them is to run them, **and running them proves nothing** — green is the symptom, not the evidence.
The mechanical check is: the number of arms each partition constructs must equal the number of arms
`assess_health` can produce. `10-01` Task 3 extends both to five and corrects both docstrings in the
dated form. For the action partition, what survives the correction is the **rule** — a push costs
somebody writing down what a person can DO, and an arm added next year is silent by default — not
the **number**.

---

## Collision 8 — nothing new is published to `status.json`

**Decided: the new `Health` field is deliberately unpublished, on two standing precedents in this
tree.**

`Result.shipping`: *"Deliberately NOT published in `status.json`. `boty.status` builds its watch rows
field by field rather than `asdict`-ing a `Result`, so adding a field here publishes nothing new,
and no source artifact asks for a shipping key."* `Health.action`: the same paragraph, at the other
end.

The `reason` string already carries the diagnosis and is already published. Adding a key would move
`tests/test_status.py`'s key-set assertions and `served/boty/index.html`'s `esc()` obligations for no
measured benefit.

**The consequence, stated so it is checkable:** `boty/status.py` and `served/boty/index.html` are in
**no plan's `files_modified` in this phase**. A plan that finds it needs them has discovered that
something published changed shape, and **must reverse this decision in writing first**.

---

## Collision 9 — the read budget

### Dan's terms, transcribed rather than paraphrased

From `QUESTIONS.md` § 0g, answered 2026-09-02, verbatim from the option he selected:

> *"Authorize up to 3 Best Buy reads"* — "A hard cap of 3 live requests to Best Buy only, spaced,
> browser-rung. Enough to confirm a repaired or replacement control actually reads, so criterion 3
> can close MET AS WRITTEN. Nothing touches Amazon, Target or Walmart — the three already refusing
> us — and nothing touches the daemon's live state files. If Best Buy refuses at the connection
> layer (as README records), that refusal is itself the measurement and gets written down as one."

And the binding terms recorded beneath it: at most three, Best Buy only, spaced not burst; **a
refusal IS the measurement**; **no `boty check`**; no write to `state.json`, `pacer-state.json` or
`served/boty/status.json`; no `systemctl restart boty`.

**`10-01` spends none of them. This plan makes no live request of any kind.**

### The three things his answer does not state, settled here

**The counting unit: one rendered page load through the Best Buy adapter.** A rung-3 navigation
fans out into dozens of subresource requests, and that fan-out is **inherent to the rung he
authorised** — it is what a browser does, and counting subresources would make the cap unspendable
rather than strict. One `fetch_rendered` call is one read.

**What counts as SPENT, and the single exemption:**

1. **Any navigation attempt that leaves this host counts as SPENT, whatever it returns.** A timeout,
   a TLS reset, a partial render, a challenge page, a 4xx, a 5xx, an empty body — all spent. Best Buy
   received a request; what came back does not refund it.
2. **Only a PRE-NAVIGATION failure is exempt**, and only because no packet reached Best Buy: chromium
   could not start, or no browser binary was found. That is a host fact and it is recorded as one.
3. **The exemption may be taken AT MOST ONCE.** A second pre-navigation failure **ends the sequence**
   and criterion 3 closes on what was measured to that point. There is no fix-and-retry loop, because
   *"fix the host and try again"* is how a cap of three becomes a cap of whatever the executor's
   patience allows.

**Worst case, checkable by counting: one exempt pre-navigation failure, then reads 1, 2 and 3 —
three navigations, never more, under every branch.**

**The spacing: at least 300 seconds between reads** — Best Buy's own configured standing cadence in
`config/products.yaml`. Never ask a retailer faster than the daemon would. And the daemon is
running, so these reads are **additive** to its traffic, which is a second reason not to burst them.

**The allocation:**

| read | plan | spent on |
|---|---|---|
| 1 | `10-04` | the **incumbent** control, SKU `6216393`, through `check_bestbuy_browser` — establishing which of four states it is in: reads / dead / refused / unreadable-here. Every one of those is a recorded measurement |
| 2 | `10-04` | the **candidate class search** — a durable-class term rather than a SKU — to obtain a candidate SKU that passes D1–D3 without guessing one |
| 3 | `10-04` | the **chosen candidate's SKU**, confirming it resolves and reads IN_STOCK, first-party |

**The refusal branch is written before the first request**, which is the point of settling this in
wave 1: if all three refuse, `10-04` records the refusal as the measurement, confirms README's
*"unread — refused at the connection layer"* row as measured on the day rather than inherited, leaves
the incumbent in place because no replacement could be confirmed, and closes criterion 3 at **MET IN
PART**. What is not available is calling it inconclusive, retrying around it, or spending a fourth
read. An unspent read is recorded as unspent.

**Why the incumbent is read first even though the phase expects to replace it.** Criterion 3 says
*repaired … or replaced with one that reads*. If read 1 shows the incumbent reads, criterion 3 is met
by a real reading and the replacement becomes criterion **4**'s business — and the record gains
something better than a repair. See Collision 10.

---

## Collision 10 — what "Best Buy's dead control" actually refers to

**This is a FINDING, not a choice.** It is provable **offline today**, it needs no live read, and it
must not be conditioned on one. REQ-24's last sentence is *"Best Buy's current dead control is
repaired"* and criterion 3 is built on it — so a phase that repairs something never shown broken is
the exact failure this repository's standard exists to catch.

### The record, with line citations — each one re-opened and checked by this executor on 2026-09-02

All citations are into `docs/retailer-evidence.md` (5,015 lines at the time of checking). Every line
number below was read individually rather than copied from the outline.

| what the record says | where | checked |
|---|---|---|
| SKU `6216393` — the control — read `in_stock … $59.99 … ld+json: InStock from Best Buy` in **four** separate `make verify` transcripts | L1642, L1884, L2286, L2413 | ✅ all four lines carry `in_stock bestbuy CONTROL — Pokémon Let's Go, Pikach $59.99 ld+json: InStock from Best Buy` |
| the same SKU's search redirect, transcribed in full | L860 | ✅ *"Redirected to the product page."* 1,109,548 B, title `Pokémon: Let's Go, Pikachu! Nintendo Switch HACPADW2A - Best Buy`, canonical `/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ/sku/6216393`, exactly **one** offer: `available=True, price=59.99, seller='Best Buy'` |
| the **only** "did not resolve" for that SKU — the documented **2026-08-04 FALSE dead**, from unparseable markup on a SKU that was alive | L960 | ✅ and the claim of uniqueness was re-measured, not assumed: `grep -n "did not resolve" docs/retailer-evidence.md` returns **exactly one line, L960** |
| the two most recent attempts are `no Chrome/Chromium binary found` — a **host** failure | L3482 (Phase 5 close, 2026-08-10), L4397 (Phase 7 close, 2026-08-17) | ✅ both read `fetch failed: no Chrome/Chromium` |
| SKU `6577129` — the one that genuinely resolves to nothing — was a **product watch**, recorded as *unconfirmed and probably wrong*, and **never the control** | L822, L868, L901 | ✅ L822 *"SKU `6577129` is unconfirmed and probably wrong … a fixture value nobody has ever seen resolve, not an established fact"*; L868 the search-miss branch; L901 *"now has a direct disproof rather than an absence of evidence"* |

**Two further checks this executor ran that the outline did not claim, because "the only" and "never
the control" are the two assertions above that a single missed line would falsify:**

- `grep -n "6216393" docs/retailer-evidence.md` → **7 lines** (L790, L842, L860, L919, L920, L960,
  L972). Six describe successful resolution or the page's own markup; L960 is the false dead. There
  is no second unresolved reading anywhere in the log.
- `grep -n "6577129" config/products.yaml` → **one line, L201, inside a comment** explaining that
  the SKU *"this repo used to carry for it (6577129) resolves to nothing"*. It is **not** a watch,
  and Best Buy's only `control: true` entry is `target: "6216393"` at L208-211. So "already removed
  from config" is measured, not recalled.

### THE CONCLUSION, and both roundings refused

> **Best Buy's control has never been shown dead. It was last shown ALIVE in early August, and it
> has been unmeasured for roughly four weeks. The evidence is ABSENT-THEN-STALE, not contrary.**

**Not *"the control is dead"*.** Nothing in the record establishes that. The single unresolved
reading of `6216393` is the one this repository itself documented as **false**, caused by unparseable
markup on a SKU that was alive — and it is the reason Collision 2's predicate has a discriminator at
all. The SKU that does resolve to nothing is `6577129`, which was a product watch, was already
removed from config, was recorded as *unconfirmed and probably wrong* when it was introduced, and was
never the control. **Reading the phase requirement as "the control died" is a conflation of two
different SKUs.**

**Not *"the control is fine"* either.** A four-week-old reading is a reading about early August. The
two most recent attempts established nothing about Best Buy at all — they are `no Chrome/Chromium
binary found`, a fact about **this host**, and `10-CONTEXT.md` records even that claim as stale
(measured 2026-09-02: Playwright chromium is present, three builds including a headless shell). So
the honest statement is that nobody has asked Best Buy about this SKU in about a month.

**No plan in this phase may assert the control is dead** — not in prose, not in a test name, not in a
commit message.

### This finding survives read 1, whatever read 1 returns

It was established **without** a live read, so a live result cannot unestablish it:

- **a refusal** leaves it standing — a refusal establishes nothing about resolution;
- **a successful read** confirms it — the control was alive in early August and is alive now;
- **an unresolved result** does not contradict it — it dates the death to somewhere inside the
  four-week window this record bounds, which is *more* than the record held before.

`10-05`'s criterion 3 row carries this finding **unconditionally**.

### What criterion 3's honest verdict looks like in the alive branch

**There was nothing to repair.** The defect was in a *record*, not in a config: REQ-24's last
sentence describes a death the evidence log does not support. The phase's deliverable there is the
correction plus a replacement chosen on durability grounds under criterion 4's own rule — which is a
better outcome than a repair, and is the kind of claim this repository exists to get right.

---

## COVERAGE.md — asserted, not created

`.planning/phases/10-a-control-that-cannot-die/COVERAGE.md` was written at planning time. `10-01`
**asserts** it rather than creating it. It is one line, and quoted in full:

> External API integration: this phase makes up to THREE live requests, to Best Buy only,
> browser-rung and spaced, under the hard cap Dan authorised in QUESTIONS.md § 0g — every other
> criterion is closed offline, and an unspent read is recorded as unspent.

**Confirmed: it declares that this phase DOES make external calls**, which is the departure from
Phases 8 and 9, whose COVERAGE files declared the opposite.

---

## What is NOT decided here

- **The mixed-group sentence's exact wording** — Collision 6 decides the rule; `10-02` writes the
  sentence and gates it.
- **`fetch.is_unresolved` and its five wiring sites** — Collision 3 decides the shape; `10-02` ships
  it.
- **The durability rule D1–D5 and its applied table** — `10-03`'s, entirely.
- **Anything about what a live read returns** — `10-04`'s, and nothing in this file assumes it.
- **Mutation M44** — `10-05` registers it, after measuring its kill set against the existing
  registry. `10-01` only re-points M30.

## What `10-01` does not claim

- Not that the control is dead. See Collision 10.
- Not that a wrong alert is being produced today by the mixed group. See Collision 6 — it is latent.
- Not that the predicate covers every dead control. It covers SKU-addressed Best Buy readings via
  clause A and clause B; the residual and the rung-3 status gap are both named and neither is closed.
