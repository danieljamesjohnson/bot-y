# Phase 6: Claims With Gates Under Them — Plan Outline

**Drafted:** 2026-08-10
**Granularity:** coarse
**Phase requirements:** REQ-17, REQ-18, REQ-19, REQ-20
**Plans:** 6, in 6 waves — every wave serial, and for a *different* measured reason than Phase 5's
(§ *Why every wave is serial*: it is the shared gate, not the files. Three plans here own provably
disjoint file sets, which is a first for this project)

**This phase is nothing but gates, so its own rule binds it with double force: every gate below
must be watched going red before it is trusted.** Criterion 2 is literally a report that an
existing gate *cannot* go red. Two of the six plans get their red-watch against the **real tree**
rather than a corrupted copy, because the tree is red today — that is the strongest form
available and it is called out where it applies.

## Plans

| Plan ID | Objective | Wave | Depends On | Requirements |
|---|---|---|---|---|
| 06-01 | **The ceiling measures what you would pay, and refuses to guess.** `Offer` gains a shipping field read from each retailer's own payload (GameStop's `OfferShippingDetails` object; Walmart's *free* signals only, resolved to zero on two agreeing fields); `Result` carries a delivered total; `alertable` refuses an alert when a ceiling is configured and the delivered total cannot be established, on the exact `price is None → False` template one line above it. **No shipping number is parsed out of prose** (§ *Finding 4* — Nintendo's `shippingDetails` is a sentence, and the naive read of it is wrong). M4's anchor is re-pointed in the same commit, because this edit necessarily breaks it (§ *Finding 6*). | 1 | — | REQ-17 |
| 06-02 | **A rung in the README is bound to the rung the code takes — watched going red by the mutation the criterion names.** Two joins the tree does not currently make: retailer → adapter (`cli._make_checker`'s `if`-chain) and adapter → `Rung` (a keyword argument at ~15 `Result(...)` sites). Two-directional, in `_extraction_mismatch`'s shape: a working-rung row must have an adapter that takes that rung, and a rung-4 row must have none. Best Buy's `3 (2 with a key)` handled by the established `rung[:1]` convention plus a second assertion for the parenthetical. Plus the `Rung`→numeral mapping, which **does not exist anywhere in this tree** (§ *Finding 5*), landed as a pin with its justification inline. | 2 | 06-01 | REQ-18 |
| 06-03 | **A workflow file added under `.github/workflows/` cannot escape the pin, exit-code, timeout and runner rules.** Four rule families currently keyed to `CI = WORKFLOWS / "ci.yml"` and duplicated for `RELEASE` become functions of `dict[str, str]` returning filename-prefixed findings — the exact shape `_pr_triggered_privilege` already demonstrates and documents in its own docstring. Per-file tests kept as the specific cases. Red-watch: a third, deliberately non-compliant synthetic workflow in `PUBLISH_WORKFLOW`'s established idiom, one violation per rule family. | 3 | 06-02 | REQ-19 |
| 06-04 | **`CHANGELOG.md` is gated on its contents, and the gate is scoped so it cannot invalidate itself.** New `tests/test_changelog.py` in `test_contributor_docs.py`'s whole-file idiom: rules as pure functions of text, run against the shipped file and against a corrupted copy derived from it. Scoped to `CHANGELOG.md` **deliberately and with the measurement written down** — the leaked-markup sweep now returns 9 lines in 4 files, all in `.planning/`, all deliberate quotations, and `06-PATTERNS.md` became three of them in the act of measuring the sweep (§ *Finding 3*). Sandbox absence handled by a file-presence skip, not by widening `SANDBOX_CONTENTS` (§ *Finding 7*). | 4 | 06-03 | REQ-19 |
| 06-05 | **`pyproject.toml` reads `0.2.0`, and the three places this project states its version cannot silently diverge.** The gate is written **first and observed red against the real tree** — `pyproject.toml` says `1.0.0` and `.planning/STATE.md` says `v0.2` today, so this is a red-watch against the shipped tree rather than a synthetic corruption. Then the roll: `1.0.0` → `0.2.0`, a `## [0.2.0]` CHANGELOG heading written from this phase's measurements, and the `Development Status :: 5 - Production/Stable` classifier re-decided rather than inherited (§ *Finding 8* — the comment arguing for it argues *against* it at 0.2.0). | 5 | 06-04 | REQ-20 |
| 06-06 | **Close. No code.** Per 05-04's recorded decision: *"a closing plan that implemented its way to a green table would be a phase measuring work it did in the act of measuring."* `make verify-offline` run and its verdict recorded verbatim; the mutation count observed rising from 16 and each new mutation observed CAUGHT; REQ-18's stale *"leaves 131 green"* figure re-measured rather than repeated; **a blocking checkpoint carrying the measured alertability consequence of criterion 1** (§ *Finding 2* — which GO Plus + watches can still alert, and which cannot); five criterion verdicts in the ROADMAP outcome table in Phase 3.1's / 4's / 5's format, unmet recorded unmet with the date, nothing reworded. | 6 | 06-01, 06-02, 06-03, 06-04, 06-05 | REQ-17, REQ-18, REQ-19, REQ-20 |

**Plan numbers are creation order; waves are execution order.** Here they coincide, and plan
numbers also coincide with ROADMAP criterion numbers 1–5 for readability. 06-06 is the close.

`autonomous: true` for 06-01 … 06-05. **`autonomous: false` for 06-06** (one blocking checkpoint).

---

## Where `06-CONTEXT.md` is wrong

Two corrections come from `06-PATTERNS.md`, which did real measurement. Both are load-bearing.
CONTEXT was auto-generated (`workflow.skip_discuss`), so this is a drafting error rather than a
withdrawn decision — nothing Dan decided is being re-opened.

### CONTEXT-1 — "already binds Routing and Extraction **to the code** in both directions"

`06-CONTEXT.md` § *Existing Code Insights*, criterion 2. **Measured false.**
`_extraction_mismatch` (`tests/test_support_matrix.py:379-406`) binds the README's Extraction
cell to the README's **Rung cell**. Both directions are *inside the table*. PATTERNS grepped and
found **no test anywhere in `tests/` that compares a matrix cell to a `Rung` member or to
`boty/retailers.py`**. Re-confirmed here: `grep -n "Rung\." tests/test_support_matrix.py` returns
nothing, and the file does not import `boty.models` at all.

So 06-02 is not copying an existing binding across one column. **The code-side half of the
support matrix does not exist and is new construction**, and the outline sizes 06-02 accordingly.

### CONTEXT-2 — "unresolvable ⇒ UNKNOWN" is framed as the exception

`06-CONTEXT.md` § *Specific Ideas*, REQ-17, reads as though resolving shipping is the normal case
and failure is the edge. **Measured backwards.** In both shipped Walmart fixtures *every* numeric
shipping field is `null` — `shippingPrice`, `shippingCostType`, `shippingOption.shipPrice`,
`priceInfo.shipPrice`, `topBoostedOffer.shippingCost`, `fulfillmentSummary[0].fulfillmentPrice`,
`fulfillmentOptions[0].speedDetails.fulfillmentPrice`. Only *free*-shipping signal is present.
**No payload this repo has ever captured shows what Walmart emits for paid marketplace
shipping** — which is precisely the case REQ-17 exists for.

Consequence 06-01 must honour: unresolvable is the **common** Walmart path, not the rare one, and
a field name for the paid case cannot be invented. See § *Finding 1* for what 06-01 does instead.

---

## Findings from the tree that must shape the plans

All eight measured during outlining, on 2026-08-10, against the working tree at
`03520af`. Findings 3–8 go beyond what `06-PATTERNS.md` measured.

### Finding 1 — Shipping is resolvable on exactly one of the four alertable retailers

Four watches carry a `max_price` ceiling, and all four are the GO Plus + product watch
(`config/products.yaml:72-75, 113-117, 123-126, 266-269`). **Every control watch carries no
`max_price` at all**, so `alertable` short-circuits at `if self.watch.max_price is None: return
True` and **no control's verdict can change under any ceiling edit.** That is the blast radius,
measured: criterion 1 cannot break `make verify`'s control stage.

What each of the four publishes about shipping, parsed out of the shipped fixtures today:

| Retailer | Extraction | Shipping signal in `goplusplus.html` | Resolvable as a number? |
|---|---|---|---|
| GameStop | JSON-LD | `shippingDetails.shippingRate.value = "6.99"` inside an `OfferShippingDetails` **object** | **Yes — 6.99.** The only real number in the corpus |
| Nintendo | JSON-LD | `shippingDetails` is a **prose string**: `"Standard UPS Ground Shipping: $6.99, 3-9 business days. Free UPS Ground Shipping on orders over $50."` | **No** — see § *Finding 4* |
| Walmart | `__NEXT_DATA__` | every numeric field `null`; `freeFulfillment: true`, `shippingText: "Free shipping"`, `additionalFees.shippingAndImportFee.price = 0` | **Free only**, and only if 06-01 decides free resolves to zero |
| Amazon | `dom` (add-to-cart control) | nothing the reader touches — `add_to_cart_offers` reads a button, an availability line and a seller name | **No** |

**The decision 06-01 must make in writing**, with all three options measured and none of them free:

1. **Strict.** A configured ceiling plus an unestablished delivered total ⇒ not alertable.
   Consequence, stated rather than discovered: **Nintendo's and Amazon's GO Plus + watches stop
   being alertable.** Nintendo is the one entry in this config listing the product at its $54.99
   MSRP with no marketplace attached (README:102) — so the honest rule silences the watch most
   likely to be a real restock.
2. **Fall back to the item price when a retailer publishes no shipping information at all.**
   Rejected in advance here, and the reason must be written into the code if 06-01 reconsiders:
   it reopens the exact hole REQ-17 closes. Walmart's paid-marketplace payload is *unobserved*
   (§ CONTEXT-2), so "publishes nothing" and "publishes something we did not read" are
   indistinguishable on the retailer this criterion exists for.
3. **A per-watch operator declaration**, in Phase 5's `store_id` shape — required config, no
   default, unset means unresolved. This is inside CONTEXT's *"Claude's Discretion: where the
   delivered total is computed and carried"*, and it has a direct precedent decided by Dan on
   2026-08-10 (REQ-14: when the page cannot tell us, the operator pins it and bot-y never
   guesses). It costs a config key and a docs paragraph.

**The tiebreaker is already recorded and 06-01 must apply it rather than re-derive it:**
`REQUIREMENTS.md` § Non-Functional — *"**Trustworthiness over coverage.** Where they conflict,
correctness wins. … This is the tiebreaker for every scoping decision."* Option 1 is therefore
the floor; option 3 may be added on top of it but never in place of it, and option 2 is out.
**Whichever lands, the consequence goes to Dan at 06-06's checkpoint as a measured table, not as
a sentence** — a monitor that can no longer alert on two of its four product watches is a change
he should see, and this milestone exists so consequences are stated rather than absorbed.

### Finding 2 — Where the UNKNOWN goes: `alertable`, not `Availability`

Criterion 1 says *"an unresolvable shipping cost is UNKNOWN, not a pass"*, and PATTERNS correctly
flags that `alertable` returns `bool` while `Availability` is set in a different function with a
different vocabulary. **Decided here, because the reasoning is already written down in this
repo and only needs following.**

`tests/test_models.py:80-92`, verbatim, is the existing precedent for exactly this shape:

> `test_unpriced_in_stock_offer_does_not_pass_the_ceiling` — *"A ceiling that cannot be evaluated
> must not authorise an alert."*

An unestablished delivered total is a ceiling that cannot be evaluated. So:

- **`Result.alertable` returns `False`** — one branch below `if self.price is None: return False`,
  same paragraph of reasoning, same file.
- **`Availability` is NOT touched.** Driving availability to UNKNOWN would make the page's own
  stock statement disappear because of a *pricing* question, and it would put a permanent UNKNOWN
  on Nintendo and Amazon with no path back. The standing rule *"UNKNOWN is never a verdict, and
  never OUT_OF_STOCK"* is a rule against **resolving** an unknown into a verdict; `alertable ==
  False` resolves nothing.
- **The unknown is carried on the delivered total itself** — `None`, with the docstring stating
  what the default MEANS (*"nobody read one"*, never `0.0`), per the house convention `rung`,
  `extraction` and `store` all follow (`models.py:262-270, 297-304`).
- **It is said out loud in `detail`**, which `status.py` already publishes, so a reader sees *in
  stock, delivered total not established, not alertable* rather than silence.

**Explicitly not in scope, and this is scope creep rather than scope reduction:** a dedicated
`status.json` key for the shipping figure. Phase 5 published `store` because *its* criterion 1
said *"and that store is published in `status.json`"*. Criterion 1 here says no such thing, and
no source artifact asks for it. Recorded so nobody reads its absence as an omission.

### Finding 3 — The leaked-markup sweep grew while this phase was being planned. Measured.

`06-PATTERNS.md` measured the sweep and reported hits in three files, all in `.planning/`, all
deliberate quotations of the defect. **Re-run today it returns 9 matching lines in FOUR files, and
three of them are `06-PATTERNS.md` itself** — the document became a hit in the act of measuring
the sweep:

| File | Matching lines | What it is |
|---|---|---|
| `.planning/phases/04-open-source-ready/04-REVIEW.md` | 3 | quoting the original defect |
| `.planning/seeds/nothing-reads-the-changelog-body.md` | 2 | quoting the defect |
| `.planning/phases/06-claims-with-gates-under-them/06-CONTEXT.md` | 1 | quoting the defect |
| `.planning/phases/06-claims-with-gates-under-them/06-PATTERNS.md` | 3 | **new — the measurement's own file** |

`CHANGELOG.md`, `README.md`, `boty/`, `scripts/`, `tests/`, `docs/` and `.github/` are all clean;
the 2026-08-07 fix (`2ac965f`) held. `CHANGELOG.md` also ends with a newline today, so that rule
is green on arrival.

**This is the argument for scoping, and it is now empirical rather than predicted: a rule scoped
to `.planning/` goes red on every document that describes the defect, including the ones written
to plan the gate against it.** That is the self-invalidating gate `test_contributor_docs.py`
warns about in its own docstring (*"A gate that invalidates itself to make a point is worse than
no gate"*). **06-04 scopes to `CHANGELOG.md`** — the file the criterion names, the file
`MANIFEST.in:39` puts in the sdist, and the file `pyproject.toml:179` points every installer at.
Widening later is a decision with a `_PROBE_DIR_PREFIXES`-style exemption attached, not a default.

*(This outline deliberately names the tag shapes without reproducing them, so it does not become
the fifth file in that table. That is the cheapest possible demonstration of the problem.)*

### Finding 4 — Two retailers publish `shippingDetails` under the same key with different TYPES

Measured today by parsing both fixtures' JSON-LD through `parse.ldjson_read`:

- GameStop: `"shippingDetails":{"@type":"OfferShippingDetails","shippingRate":{"@type":"MonetaryAmount","value":"6.99","currency":"USD"},…}` — an object.
- Nintendo: `"shippingDetails": "Standard UPS Ground Shipping: $6.99, 3-9 business days. Free UPS Ground Shipping on orders over $50."` — a string.

**Both are read by the same extractor** (`parse.ldjson_offers`). Two consequences 06-01 must
carry:

1. A reader written for GameStop's shape must **type-check before it digs**, and return `None`
   for the string case *on purpose*, with the reason in the code — not by the accident of `_dig`
   returning `None` when handed a `str`.
2. **A lenient reader that pulled `$6.99` out of Nintendo's sentence would produce a WRONG
   number.** The prose says free over $50; the item is $54.99; the true shipping cost is **zero**.
   A regex over that sentence yields $61.98 for an item that ships free — the delivered total
   would be inflated, the ceiling could suppress a genuine MSRP restock, and the number would be
   invented from prose. **No shipping figure is parsed out of prose anywhere in this phase.**
   This is the same class as 05-01's rejected `"0"` sentinel: reading our own or someone else's
   presentation text as a fact.

`06-PATTERNS.md` measured GameStop and Walmart. It did not measure Nintendo or Amazon, and both
change the answer.

### Finding 5 — There is no `Rung` → numeral mapping anywhere in this tree

`boty.models.Rung` has three members and their values are `"tls"`, `"api"`, `"browser"`
(`models.py:55-60`). The README says `1`, `2`, `3`, `4`. `tests/test_support_matrix.py:123` has
`RUNGS = {"1","2","3","4"}` as *strings from the table*. **Nothing joins them.** `grep -rn
"Rung\." boty/ scripts/ tests/` finds the enum used only as a keyword argument and a comparison;
the ladder's numbering lives in prose only.

So 06-02 creates the mapping. It is a **pin, not a rule**, in the sense
`UNREAD_POSITIONS` and `TRUSTED_ACTION_OWNERS` already establish (§ *Shared Patterns* item 5) —
enumerated with the justification inline, so widening it means editing a red test. It belongs in
`tests/test_support_matrix.py`, **not** in `boty/models.py`: a numeral is a documentation fact
about the ladder, `models.py` deliberately keeps `Rung` out of `monitor`/`Health`, and putting it
in `boty/` would put 06-02 into 06-01's files for no gain.

**Also measured, and it decides the static-vs-dynamic question PATTERNS left open:**

- `boty.models.KNOWN_RETAILERS` is exactly six — `walmart, gamestop, nintendo, bestbuy, target,
  amazon`. **Pokémon Center is absent**, has no adapter and no routing arm, and its README row is
  rung 4 with `—` extraction. That is the clean other half of the two-directional rule: a rung-4
  row must have **no** adapter binding, and a working-rung row must have one.
- `cli._make_checker` (`cli.py:41-84`) is a closure containing an `if`-chain with arms for
  `bestbuy` (two, keyed on `cfg.bestbuy_api_key`), `amazon` and `target`, falling through to
  `check_html` for gamestop / walmart / nintendo. There is **deliberately no registry**
  (`cli.py:42-48`).
- A **dynamic** binding would need to drive five adapter functions across three transports —
  including `check_bestbuy_api`, for which **no fixture exists** (`tests/fixtures/bestbuy/` holds
  two HTML files and no API payload) — and would still not read the routing `if`-chain.
- A **static AST** binding reads both joins uniformly, needs no network, no fixture and no
  browser stub, and `ast`-over-repo is already an idiom here (`test_ci_workflow.py:66`,
  `:668`).

**Recommendation, to be argued in the file: static AST, with its own cost written down** — it
asserts what the source says, not what runs. That cost is smaller than it looks, because *the
failure mode this criterion names is a source edit*: a developer changing an adapter's rung and
forgetting the README. The mutation is what proves the assertion is load-bearing. And because a
static gate could otherwise bind to a function nothing calls, **both joins must be in the rule**
— retailer→function from `cli.py` and function→rung from `retailers.py`. A binding to
`check_amazon` alone would stay green if `_make_checker` stopped routing amazon to it.

### Finding 6 — The criterion-2 mutation anchor PATTERNS proposes mutates the WRONG adapter

`06-PATTERNS.md` proposes `search="rung=Rung.TLS"` → `replace="rung=Rung.BROWSER"` "inside
`check_amazon`". Measured: `apply_mutation` (`mutation_check.py:543-556`) does
`before.replace(mutation.search, mutation.replace, 1)` — **the first occurrence in the file** —
and `rung=Rung.TLS,` occurs at:

- `boty/retailers.py:419` — inside `check_html`, which serves **GameStop, Walmart and Nintendo**
- `boty/retailers.py:481` — inside `check_amazon`

So the naive anchor mutates `check_html`, not `check_amazon`, and the mutation's `breaks=`
sentence would describe something that did not happen. **The anchor must be uniquely
disambiguated** — the `check_amazon` site is followed immediately by an Amazon-specific
`allow_dom=True,` keyword that `check_html`'s call does not carry, which is a behavioural
disambiguator rather than message prose.

Worth noting for 06-02: mutating `check_html`'s rung contradicts **three** README rows at once
and is a perfectly good second mutation. But REQ-18's own text names `check_amazon`, so the
`check_amazon` mutation is the one the criterion requires and it must be the one that lands.

**And the M4 collision, which is a required same-commit edit rather than a surprise.** M4's
anchor is verbatim:

```
"        if self.price is None:\n            return False\n        return self.price <= self.watch.max_price"
```

Any delivered-total edit to `alertable` moves that final `return`. `apply_mutation` raises
`HarnessError` — *"The source drifted away from this mutation. Skipping it silently would quietly
reduce the check to two mutations while still printing a total."* — so `make verify` dies rather
than degrading. **Precedent for the fix is Phase 4's:** *"M2's anchor was re-pointed because this
change moved the line it named, and the harness refused to run rather than quietly drop to seven
mutations."* 06-01 re-points M4 in the same commit and its `breaks=` sentence is re-checked
against what the mutation now does.

### Finding 7 — The sandbox problem, and why the sandbox is not widened

`mutation_check.SANDBOX_CONTENTS` (`:125-128`) is `boty, tests, scripts, config, served, docs,
hooks, pyproject.toml, Makefile, README.md, CONTRIBUTING.md, LICENSE, MANIFEST.in, .github`.
**`CHANGELOG.md` and `.planning/` are both absent**, and `build_sandbox()` raises `HarnessError`
for a `SANDBOX_CONTENTS` entry with no file behind it. So a gate that *unconditionally* reads
either file dies under `make mutation`.

Measured costs of the two escapes:

- **Widen `SANDBOX_CONTENTS`.** `.planning/` is **2.9 MB across 101 tracked files**, and
  `build_sandbox()` runs once per mutation plus a baseline — **17 full copies** at M17, ~50 MB of
  copying added to every `make verify`, on top of the `git add -A` the index costs. It also
  widens the set of paths the contributor-docs citation rule may resolve, which
  `mutation_check.py`'s own `_IGNORE` comment already names as *"that gate's decision to take,
  not this one's"*.
- **Skip on the file's absence**, with the reason written out. **This is Phase 5's answer to the
  identical problem**, and it is already in the tree at `tests/test_config.py:363-374`, keyed on
  `.gitignore` being absent, with the reason stated in the skip message: *"it skips on
  `tests/test_identity_check.py`'s `needs_repo` precedent rather than being bought green by
  widening `SANDBOX_CONTENTS`."*

**Both 06-04 and 06-05 take the skip**, keyed on the file's own presence — and note the skip is
sound here for the reason `test_packaging_metadata.py:59-68` says it is *not* sound for
`MANIFEST.in`: no mutation targets `CHANGELOG.md` or `.planning/STATE.md`, so running these rules
inside the sandbox could not change any mutation's verdict. Both plans state that in the skip
reason rather than leaving a bare `skipif`.

**Consequence for 06-05, and it is the load-bearing part of criterion 5:** the STATE.md half of
the version binding does not run under mutation. So 06-05 pairs it with a
`pyproject.toml` ↔ `CHANGELOG.md` binding that is **entirely inside the shipped tree and runs
everywhere**. The criterion's text — *"agrees with the project's milestone version"* — is met by
the STATE.md rule; the always-on rule is what keeps the gate from being a skip line nobody reads.
Neither substitutes for the other and 06-05 says so.

### Finding 8 — Rolling to `0.2.0` inverts the argument `pyproject.toml` already carries

`pyproject.toml:68-90` argues at length for `Development Status :: 5 - Production/Stable`, and
Phase 4 recorded the decision: *"tagging 1.0.0 while classifying the package Beta is exactly the
asserted-versus-real disagreement this phase exists to close, and leaves a reader to decide which
of the two numbers to believe."*

**At `0.2.0` that argument runs the other way.** A package classified Production/Stable at version
0.2.0 is the same asserted-versus-real disagreement, pointed the opposite direction. 06-05 must
re-decide it and argue the decision in place — the house style for a reversal is
`models.py:145-161` / `pacing.py:5-15`: argue it where the old argument lives, name what
overruled it, do not delete the original. It must **not** be left as stale prose beside a version
it no longer describes.

Related and cheap: `pyproject.toml:179` `[project.urls] Changelog` and `MANIFEST.in:39` are what
make `CHANGELOG.md`'s contents reach a stranger, and both are already correct. No edit.

---

## Per-plan scope sketch

Task counts are the target for the per-plan write; files are the expected `files_modified`.

### 06-01 — the ceiling measures the delivered total (wave 1, autonomous)

~3 tasks.

1. **The carrier and the readers.** `boty/parse.py` — a shipping field on `Offer`, declared
   **last with a default**, whose docstring states what the default MEANS (*"nobody read one"*,
   never `0.0`) per the `rung`/`extraction`/`store` convention. `_as_float` is **reused, not
   re-written** (`parse.py:50-54`). `ldjson_offers` reads `shippingDetails.shippingRate.value`
   **only when `shippingDetails` is a mapping** (§ *Finding 4*), and returns unresolved for the
   string form with the reason in the code. `nextdata_offers` resolves Walmart to **zero only
   when two independent fields agree** — `speedDetails.freeFulfillment is True` and
   `priceInfo.additionalFees.shippingAndImportFee.price == 0`, both present and both agreeing on
   both shipped fixtures — and leaves everything else unresolved, with a comment recording that
   **no captured payload shows Walmart's paid-shipping shape** so no field name is being guessed
   (§ CONTEXT-2). `add_to_cart_offers` reads nothing and says why: a button carries no shipping.
   Path constants beside `_WALMART_PRODUCT_PATH` carrying the same kind of comment; no regex over
   raw HTML.
2. **The verdict.** `boty/models.py` — a delivered-total property or field on `Result`, and the
   `alertable` branch, on the `price is None → False` template one line above it and quoting its
   *"a ceiling that cannot be evaluated must not authorise an alert"* reasoning (§ *Finding 2*).
   Reject a negative shipping value explicitly (T-06-01). `boty/retailers.py` — thread shipping
   onto **every** `Result(...)` return in `_verdict_from_html` including both UNKNOWNs and both
   refusal arms, exactly as `store` is threaded — 05-01's bulk edit missed two of six and the
   tests written first caught it, so write the tests first here too. `boty/models.py`'s
   `Watch.max_price` comment (`:213-215`) now describes a different quantity and is rewritten
   rather than left stale. **The decision from § *Finding 1* is settled and argued in the code
   here**, not in the plan file alone.
3. **Watched going red.** `scripts/mutation_check.py` — **M4 re-anchored in this same commit**
   (§ *Finding 6*), plus new mutations from **M17**: one that lets an unresolved delivered total
   clear the ceiling (the exact defect REQ-17 names), one that drops shipping from the sum.
   Anchor on the control-flow line or the expression, never on any `detail` string. `tests/` —
   the arithmetic pinned in `test_models.py` in `_result(...)`'s existing shape, and the
   **extraction** pinned against the real GameStop fixture in `test_parse.py`, so the rule is
   watched biting on captured data rather than only on synthetic input. GameStop is the only
   retailer where that is possible ($54.99 + $6.99 = $61.98; it clears an $80 ceiling and fails a
   $60 one). A **hypothetical** paid-shipping Walmart payload goes through `_nextdata(**product)`
   (`test_retailers.py:55-63`) and is labelled a synthetic stand-in in `PUBLISH_WORKFLOW`'s
   idiom — a fixture cannot be edited to carry shipping Walmart never sent without lying about
   what was captured.

Also in this plan because they are claims this edit falsifies: `README.md:49` (*"independent price
ceiling as a second line of defence"*), `README.md:164`, `config/products.yaml:75`
(`# MSRP is $54.99; anything near $140 is a flip`), and the ceiling paragraphs in
`docs/adding-a-retailer.md`. The README **matrix table rows (`:98-106`) are not touched** — 06-02
reads them.

Files: `boty/parse.py`, `boty/models.py`, `boty/retailers.py`, `scripts/mutation_check.py`,
`config/products.yaml`, `README.md`, `docs/adding-a-retailer.md`, `tests/test_parse.py`,
`tests/test_models.py`, `tests/test_retailers.py`.

### 06-02 — the Rung cell is bound to the code (wave 2, autonomous)

~3 tasks.

1. **The mapping and the two joins.** `tests/test_support_matrix.py` — the `Rung`→numeral pin
   with its justification inline (§ *Finding 5*); an AST walk of `boty/cli.py` for the
   `_make_checker` `if`-chain (retailer → adapter, including the `check_html` fallthrough and the
   `bestbuy_api_key` arm) and of `boty/retailers.py` for `rung=Rung.X` per function. Rules are
   pure functions of text with the `readme_text: str | None = None` signature convention, so the
   same function runs against the shipped README and a `_corrupt`-derived copy.
2. **Two-directional, or it is worthless.** `_extraction_mismatch`'s docstring says so in as many
   words. A working-rung row (`rung[:1] in WORKING_RUNGS`) must have an adapter taking that rung;
   a rung-4 row must have **none** — Pokémon Center is the live case and it is clean today
   (absent from `KNOWN_RETAILERS`, no routing arm, no adapter). Best Buy's `3 (2 with a key)`
   uses the established `rung[:1]` for the primary arm plus a second assertion that the
   parenthetical corresponds to `check_bestbuy_api`'s `Rung.API`. Red-watch tests in the
   `:709`-on block, one per direction, against `_corrupt`ed copies of the real README.
3. **The mutation the criterion names.** `scripts/mutation_check.py` — `check_amazon`'s rung
   flipped to `Rung.BROWSER`, **uniquely anchored** (§ *Finding 6*: the bare `rung=Rung.TLS`
   anchor hits `check_html` first and mutates the wrong three retailers). Observed CAUGHT, count
   recorded rising. REQ-18's *"leaves 131 green"* figure is **re-measured against the current
   tree, not repeated** — the suite is 667 tests today — and the re-measurement is recorded as a
   measurement note, never as an amendment to the criterion.

Files: `tests/test_support_matrix.py`, `scripts/mutation_check.py`.

### 06-03 — the workflow rules are keyed to the directory (wave 3, autonomous)

~2 tasks.

1. **Four rule families become functions of the directory.** `tests/test_ci_workflow.py` — `pin`
   (`_action_pins` / `_unpinned_actions`, `:344`/`:361`, currently `_raw()` and duplicated for
   `RELEASE` at `:1070`), `exit-code` (`_flattened_exit_codes`, tests at `:600` / `:1082`),
   `timeout` (inline at `:632-637` and `:1086-1091`) and `runner` (`_floating_runners`,
   `:414-420`) take `dict[str, str]` of name→text and return `list[str]` of findings **prefixed
   with the filename**. That is exactly `_pr_triggered_privilege`'s shape (`:423-431`), which
   documents itself as *"the only rule here that looks beyond `ci.yml`, and the one that will
   still be doing work in a year."* `_all_workflow_texts()` (`:534-539`) already exists and is
   used by only three tests. **Per-file tests stay** as the specific cases; the directory rules
   are added beside them, not in place of them. Two traps already encoded in the module docstring
   (`:34-46`) must survive: a bare `on:` key parses as boolean `True`, and unquoted
   `python-version: 3.10` parses as float `3.1`.
2. **Watched going red on a file that does not exist yet.** A third, deliberately non-compliant
   synthetic workflow string in `PUBLISH_WORKFLOW`'s established idiom (`:127`), fed as
   `{"third.yml": …}` the way `:930` already does — one violation per rule family (a floating
   `@v4` action, a swallowed exit code, no `timeout-minutes`, `runs-on: ubuntu-latest`), each
   asserted to be reported **with its filename**. This is the criterion stated as a test: a
   workflow file added under `.github/workflows/` **is** covered.

If a directory-wide rule finds a real violation in the shipped `release.yml`, it is fixed here
and named in the summary — not exempted.

Files: `tests/test_ci_workflow.py`, and `.github/workflows/release.yml` only if a rule bites.

### 06-04 — `CHANGELOG.md` is gated on its contents (wave 4, autonomous)

~2 tasks.

1. **`tests/test_changelog.py`**, new, in `tests/test_contributor_docs.py`'s whole-file idiom —
   rules as pure functions of the document's text returning lists of problems, so the corruption
   tests at the bottom run the *same* rule against a deliberately broken copy derived from the
   real file. Rules from the seed, each with its own justification: no leaked tool-call markup
   (the shapes named, scoped to this file per § *Finding 3*); every `## [x.y.z]` heading parses;
   the top non-`Unreleased` heading equals `pyproject.toml`'s version; no unreplaced placeholder;
   the file ends with a newline. **`## [Unreleased]` currently reads "Nothing yet." and no rule
   may require it to be non-empty** — that would redden the shipped tree the fastest way, by
   inventing an entry.
2. **The scoping decision and the sandbox skip, both argued in the module docstring.** Why
   `CHANGELOG.md` and not the tracked tree, with the 9-lines-in-4-files measurement quoted and
   `identity_check._PROBE_FILES` / `_PROBE_DIR_PREFIXES` (`scripts/identity_check.py:427-434`)
   named as the exemption mechanism a future widening would need. Why the file-presence skip
   rather than `SANDBOX_CONTENTS` (§ *Finding 7*), keyed on `CHANGELOG.md` itself and stating
   that no mutation targets it. Every rule watched going red against a `_corrupt`-style copy of
   the real file — including the markup rule, which is watched red against a copy with a tag
   spliced in rather than against a hand-typed string.

**Not touched:** `scripts/release_check.py`. PATTERNS establishes this as a finding rather than a
preference — `release_check.py` needs the network and is deliberately outside `make verify`
(`Makefile:97-98`), so a contents gate placed there would never run in `verify-offline`, which is
this phase's gate.

Files: `tests/test_changelog.py` (new).

### 06-05 — one version, and it cannot silently diverge (wave 5, autonomous)

~2 tasks.

1. **The gate, written first and observed red against the REAL tree.** `pyproject.toml:7` says
   `1.0.0`; `CHANGELOG.md`'s top non-`Unreleased` heading says `1.0.0`; `.planning/STATE.md`
   frontmatter says `milestone: v0.2`. **They disagree today**, so this red-watch is against the
   shipped tree rather than a synthetic corruption — the strongest form this repo has, and the
   same method 05-02 used for its `ast` prose gate (*written and run before the edit, that red
   output quoted verbatim in the summary*). The rule lives in `tests/test_packaging_metadata.py`
   and **borrows** `_project_table` / `_string` / `_strip_comment` rather than writing a second
   reader, on `test_ci_workflow.py:453-498`'s precedent and for its stated reason — *"two readers
   of one `pyproject.toml` drift"*. **It must not import `tomllib`** (3.11+, above the declared
   3.10 floor; `test_this_file_does_not_import_tomllib` at `:685` enforces this one file over and
   the reasoning transfers verbatim). Two rules, not one: `pyproject` ↔ `CHANGELOG` (always
   runs), and `pyproject` ↔ STATE.md's milestone (skips on file absence, § *Finding 7*).
   Normalisation between `v0.2` and `0.2.0` is stated as a rule, not left implicit.
2. **The roll, and the classifier it invalidates.** `pyproject.toml` `1.0.0` → `0.2.0`;
   `CHANGELOG.md` gains a `## [0.2.0]` heading whose entry is written **from this phase's
   measurements**, which exist by wave 5 — the CHANGELOG's own preamble demands *"the measurement
   behind it"*, and writing that entry in wave 1 would have been this milestone's own defect
   committed inside the plan that closes it. `Development Status` re-decided and argued in place
   (§ *Finding 8*). Gate observed **green** after the roll, and the red-then-green pair recorded.
   `pyproject.toml:73-90`'s existing reasoning is read before editing so it is amended rather
   than orphaned.

Files: `pyproject.toml`, `CHANGELOG.md`, `tests/test_packaging_metadata.py`.

### 06-06 — close (wave 6, `autonomous: false`)

~3 tasks. **No code.** 05-04's recorded decision governs: *"a closing plan that implemented its
way to a green table would be a phase measuring work it did in the act of measuring."*

1. **`checkpoint:human-verify` — the alertability consequence.** Criterion 1 changes which
   watches can page Dan, and § *Finding 1* measures it: a table of the four GO Plus + watches
   with, for each, whether a delivered total can be established and whether it can still alert.
   Not a request for permission to have shipped it — the tiebreaker in `REQUIREMENTS.md` settles
   the design — but a statement of a user-visible consequence, which is the entire subject of
   this milestone. Offer the same shape of answers 05-04's card did, and record whatever comes
   back verbatim, including a deferral.
2. **The gates, measured.** `make verify-offline` run once and its verdict recorded verbatim
   (baseline at Phase 5's close: **exit 0, 667 passed, 16/16**). Mutation count observed rising
   from 16 with each new mutation observed **CAUGHT** by ident. REQ-18's *"131 green"* figure
   re-measured against the current tree and recorded as a measurement note. **`make verify` is
   NOT the gate** and its live FAIL is recorded verbatim if it is run at all — three classes as
   of 2026-08-10, none of them this phase's, none of them this phase's to fix.
3. **The verdicts.** Five criterion verdicts in the ROADMAP outcome table in Phase 3.1's / 4's /
   5's format — measurement or reason per row, unmet recorded unmet with its date and reason,
   **nothing reworded to pass**. `REQUIREMENTS.md` traceability for REQ-17 … REQ-20 and
   `STATE.md` updated. STATE.md's own `milestone: v0.2` is now machine-read by 06-05's gate, so
   any edit to that line is a gate-visible act — say so where it will be seen.

Files: `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`,
`docs/retailer-evidence.md` (closing record section).

---

## Why every wave is serial — and it is NOT the files this time

**File ownership, measured. Three of the six plans own provably disjoint sets, which has not
happened before in this project:**

| File | 06-01 | 06-02 | 06-03 | 06-04 | 06-05 | 06-06 |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| `boty/parse.py` | ● | | | | | |
| `boty/models.py` | ● | | | | | |
| `boty/retailers.py` | ● | | | | | |
| `config/products.yaml` | ● | | | | | |
| `docs/adding-a-retailer.md` | ● | | | | | |
| `README.md` (prose only, not the matrix rows) | ● | | | | | |
| `scripts/mutation_check.py` | ● | ● | | | | |
| `tests/test_parse.py` / `test_models.py` / `test_retailers.py` | ● | | | | | |
| `tests/test_support_matrix.py` | | ● | | | | |
| `tests/test_ci_workflow.py` | | | ● | | | |
| `tests/test_changelog.py` *(new)* | | | | ● | | |
| `tests/test_packaging_metadata.py` | | | | | ● | |
| `pyproject.toml` | | | | | ● | |
| `CHANGELOG.md` | | | | | ● | |
| `.planning/*`, `docs/retailer-evidence.md` | | | | | | ● |

Only **one** genuine file collision exists: `scripts/mutation_check.py`, shared by 06-01 and
06-02, which puts 06-02 behind 06-01. **06-03, 06-04 and 06-05 collide with nothing** — they own
one test file each, plus (06-05) two files no other plan touches.

**They are still serialised, for a mechanism rather than for caution.** Every plan's acceptance is
`make verify-offline`, which is a **whole-tree** gate, and its mutation stage is not a read:
`build_sandbox()` (`scripts/mutation_check.py`) does `shutil.copytree` of every
`SANDBOX_CONTENTS` entry **out of the live working tree** into a temp dir, once per mutation plus
a baseline — **17 snapshots at M17**, sequentially, over tens of seconds, plus `git init` and
`git add -A` in each. `tests/` is in `SANDBOX_CONTENTS`. So a second agent writing *any* test
file during that window lands in some snapshots and not others; a file that is complete but
references a helper the next Write has not added yet fails collection at the **baseline**, which
`run_baseline` turns into a `HarnessError` and `make verify` reports as a mutation-stage failure.
That is the *"least attributable failure this harness could produce"* the `_IGNORE` comment
already worries about, arriving from a file in neither the plan's diff nor its file list. The
`identity`, `lint` and `types` stages are whole-tree in the same way.

**So: file ownership is not what serialises this phase; a single shared whole-tree gate is.**
Recorded explicitly because it is forward-useful — **06-03, 06-04 and 06-05 are the first plans in
this project that could run concurrently if the gate were per-plan**, and that is where a future
phase should look if wave parallelism is ever worth buying.

Two dependencies are real regardless of the gate: 06-02 behind 06-01 (`mutation_check.py`, and
06-01 moves lines in `boty/retailers.py` that 06-02 anchors near), and 06-06 behind everything by
definition.

---

## Evidence constraint (binds every plan's `<verify>`)

`make verify` has failed live since **2026-08-06**, re-measured at Phase 5's close on 2026-08-10
in **three** classes — two pre-existing (no Chrome/Chromium binary for Best Buy and Target; an
intermittent Walmart/Amazon challenge class that did **not** manifest on that pass) and one caused
by Phase 5 and correct (Walmart UNKNOWN through the config-gap guard in a pinless shell).
Therefore:

- **`make verify-offline` is the gate.** Baseline at Phase 5's close and re-confirmed by
  collection today: **exit 0, 667 tests, 16/16 mutations**. Every plan asserts against it.
- **No plan's acceptance may depend on a live retailer read, and no plan plans live probing.**
  Every gate in this phase is watched going red offline — against the shipped fixtures, against
  `_corrupt`-derived copies of the real README/CHANGELOG, against synthetic
  `_nextdata(**product)` payloads and synthetic workflow strings, and in two cases against the
  **real tree while it is still red** (06-05's version disagreement; 06-02's rung mutation, which
  is the criterion's own report that the gate cannot currently go red).
- The live `make verify` verdict is **recorded** at close if it is run, never **required** to be
  green, and never trimmed.
- `conftest.py`'s `NetworkBlocked` derives from `BaseException` on purpose — an `Exception` guard
  is swallowed by `boty.fetch` and downgraded into `Availability.UNKNOWN`, the most common
  assertion in this suite. Any new adapter-driving test in 06-01 inherits the autouse fixture and
  must monkeypatch `retailers.get` (`test_retailers.py:38-45`).

---

## Multi-source coverage audit

Every item below is covered by a plan. No item is deferred, simplified, or reduced to a "v1".

### GOAL — ROADMAP phase goal

*"Every claim this project publishes — a price filter, a matrix row, a shipped file, a version
number — has a gate under it that has been watched going red."*

| Item | Covered by |
|---|---|
| a price filter | 06-01 (delivered total + M17/M18, and M4 re-anchored) |
| a matrix row | 06-02 (Rung ↔ code, two-directional, + the mutation REQ-18 names) |
| a shipped file | 06-03 (`.github/workflows/*`), 06-04 (`CHANGELOG.md`) |
| a version number | 06-05 (three-way binding, red-watched on the real tree) |
| *"has been watched going red"* — for every gate, not only the new claims | all five, and 06-06 records the count rising and each new mutation CAUGHT by ident |

### Success criteria (ROADMAP numbering 1–5)

| # | Criterion | Covered by |
|---|---|---|
| 1 | Ceiling applies to the delivered total; unresolvable shipping is UNKNOWN, not a pass | 06-01 |
| 2 | Mutating an adapter's `Rung` against a contradicting README row turns a test red | 06-02 |
| 3 | A workflow file added under `.github/workflows/` is covered by all four rules | 06-03 |
| 4 | `CHANGELOG.md` gated on contents; the leaked-markup class cannot ship again | 06-04 |
| 5 | `pyproject.toml` reads `0.2.0`, agrees with the milestone version, cannot silently diverge | 06-05 |
| — | All five recorded with verdicts and measurements; unmet recorded unmet | 06-06 |

### REQ — `phase_req_ids`

| ID | Covered by | Closed by |
|---|---|---|
| REQ-17 | 06-01, 06-06 | 06-06 |
| REQ-18 | 06-02, 06-06 | 06-06 |
| REQ-19 | 06-03, 06-04, 06-06 | 06-06 |
| REQ-20 | 06-05, 06-06 | 06-06 |

**Every requirement ID appears in at least one plan's `requirements` frontmatter.** REQ-19 spans
two plans deliberately — its text names both halves (*"`CHANGELOG.md` shipped with leaked tool-call
markup … A workflow file added under `.github/workflows/` likewise escapes …"*) and they share no
file, so splitting them is separation rather than fragmentation. Following 04-05's and 05-01's
precedent, **a requirement is not marked complete by the plan that ships its code**; 06-06 closes
all four by measuring what landed.

### RESEARCH

Not applicable — research is disabled for this project and no `06-RESEARCH.md` exists.
`06-PATTERNS.md` served that role and is fully consumed above, including the two places it
corrects CONTEXT (§ *CONTEXT-1*, § *CONTEXT-2*) and the two places this outline corrects or
extends it (§ *Finding 4*: Nintendo and Amazon were not measured; § *Finding 6*: the proposed
mutation anchor mutates the wrong adapter).

### CONTEXT — locked decisions

| Decision | Covered by |
|---|---|
| `pyproject.toml` goes `1.0.0` → `0.2.0`; the roll is **the correction, not a normal bump**, and is safe only because publishing was deferred | 06-05 — argued in place at `pyproject.toml:73-90`, not asserted in a commit message |
| Criterion 1 is **not** scoped to eBay (closed 2026-08-10); Walmart carries marketplace sellers and is the live exposure | 06-01 — the Walmart free-signal resolution and the unobserved-paid-shipping note are both about Walmart; eBay appears nowhere |
| Never amend a success criterion to make it meetable | 06-06 — and applied in advance to REQ-18's stale "131", which is re-measured rather than edited |
| A gate must be watched going red before it is trusted — **with double force, this phase being nothing but gates** | 06-01 … 06-05 each carry their own red-watch; 06-06 records them |
| UNKNOWN is never a verdict, and never OUT_OF_STOCK | 06-01 § *Finding 2* — `alertable` returns False and `Availability` is deliberately untouched, with the reasoning quoted from the existing test that already made this call |
| Every criterion verified by something executable | all six — `<verify>` blocks against `make verify-offline` |
| Never write a real store number or host identity into a tracked file; `identity_check` runs at commit time | all six — no plan handles a store number, and the shipping work touches prices only. The pre-commit hook (`hooks/pre-commit`, staged-files only) stays in force |
| Out of scope: anything about what a *product reading* means (Phase 5, complete) | honoured — no plan re-enters `monitor.py`, `notify.py`, `pacing.py`, `config.py` or `status.py`. 06-01 enters `retailers.py` for the shipping thread-through only and does not touch the store guards |
| Out of scope: the live `make verify` failure classes and the fixture re-capture they need | honoured — recorded at close, not fixed. No plan probes a retailer |

**Claude's Discretion, per CONTEXT** — *where the delivered total is computed and carried* (06-01
§ *Finding 2*, with the three-way option set in § *Finding 1* to be settled in code), *how the
Rung binding is expressed* (06-02, static AST recommended in § *Finding 5* with its cost written
down), *the shape of the workflow-file and CHANGELOG content gates* (06-03, 06-04), and *the
mechanism keeping `pyproject.toml` and the milestone version from diverging* (06-05, two rules
because one of them cannot run under mutation, § *Finding 7*). Each carries its argument into the
code, per this codebase's dominant convention.

**Deferred, correctly absent from every plan:** the deployment (Dan answered `defer` 2026-08-10;
the daemon still runs 2026-08-04 code and that is *recorded*, not pending here — `QUESTIONS.md`
§ 0f); the live `make verify` failure classes and fixture re-capture; `identity_check`'s missing
`store '<n>'` prose rule; `QUESTIONS.md` § 0e; `deploy/boty-secret`'s missing `store`
subcommand (flagged by 05-04, *"NOT grown here"*); reconciling the two drifted copies of
`_identity_leaks` (flagged by 05-01). None appears in any plan above.

---

## Threat model seeds

`workflow.security_enforcement` is on, ASVS L1, block on `high`. Each PLAN.md carries its own
`<threat_model>`; these are the boundaries and threats established during outlining, for the
per-plan writer to sharpen rather than rediscover.

**Trust boundaries:** a retailer's JSON shipping value → `boty.parse` → `Result.alertable` → a
push to Dan's phone (untrusted input reaching an alert decision); a file under
`.github/workflows/` → GitHub Actions holding this repository's token (untrusted config reaching
privilege); `CHANGELOG.md` → `MANIFEST.in` → the sdist → a stranger's machine (published
contents); `pyproject.toml`'s version → the identity of a published artifact; the README support
matrix → a reader's judgement about what this tool can be trusted to read.

| Threat ID | Category | Component | Disposition | Mitigation |
|---|---|---|---|---|
| T-06-01 | Tampering | a retailer-supplied shipping value reaching `alertable` | mitigate | A hostile or malformed value must not clear the ceiling. `_as_float` returns `None` for non-numeric input (reused, not re-written); a **negative** value is rejected explicitly rather than subtracted, because a negative shipping cost would lower a delivered total below the item price and turn the new defence into a new hole. Unresolved ⇒ not alertable, watched by M17. **06-01.** |
| T-06-02 | Spoofing | a reseller offer defeating the price ceiling with shipping | mitigate | The phase's own subject. `$54.99 + $45` must not read as `$54.99`. Watched biting on captured data at GameStop ($54.99 + $6.99 against a $60 ceiling) and on a labelled synthetic payload for the Walmart paid case that no capture shows. **06-01.** |
| T-06-03 | Elevation of privilege | a new file under `.github/workflows/` | mitigate | **The highest-severity item in this phase.** Today a second workflow can carry a floating action tag, a swallowed exit code, no timeout and a floating runner while the suite stays green — `_pr_triggered_privilege` is the *only* rule that looks past `ci.yml`. Four rule families re-keyed to the directory, each watched red against a deliberately non-compliant synthetic third file. **06-03.** |
| T-06-04 | Tampering | `CHANGELOG.md` contents reaching every installer | mitigate | Leaked tool-call markup shipped for a whole phase. Content gate scoped to `CHANGELOG.md`, watched red against a corrupted copy of the real file. **Deliberately not widened to the tracked tree** — measured today, four `.planning/` files quote the defect on purpose and a wider rule reddens them (§ *Finding 3*). **06-04.** |
| T-06-05 | Repudiation | a published artifact whose version disagrees with the project's own record | mitigate | A stranger handed `1.0.0` by a project whose state file says `v0.2` cannot tell which claim to believe. Three-way binding, red-watched **against the real tree**, plus the roll. **06-05.** |
| T-06-06 | Tampering | the README support matrix claiming a rung the code does not take | mitigate | A reader trusts a transport claim; today mutating `check_amazon`'s rung contradicts the shipped row and nothing goes red. Two-directional binding across both joins (routing and rung), plus the mutation REQ-18 names, uniquely anchored. **06-02.** |
| T-06-07 | Denial of service | the mutation harness | accept, with the reason | Every new gate is a pytest test arriving through `make test`, so no Makefile stage is added (`Makefile:156-182`; a new stage would also break `test_the_documented_stages_are_the_stages_verify_runs`). New mutations add ~17 s each to `make verify`'s mutation stage at the measured per-sandbox cost. Accepted, as the ~29 s git-index cost was accepted in 04-04 and recorded rather than silently paid. |
| T-06-08 | Tampering | a gate that cannot run where it is needed | mitigate | `CHANGELOG.md` and `.planning/` are absent from `SANDBOX_CONTENTS`, so an unconditional read raises `HarnessError` under `make mutation`. Handled by a file-presence skip with the reason written out, **not** by widening the sandbox (§ *Finding 7*), and paired in 06-05 with an always-on rule so the criterion is not met by a skip line nobody reads. **06-04, 06-05.** |
| T-06-SC | Tampering | npm/pip/cargo installs | mitigate | **No new dependency is expected in this phase** — every surface is an existing module, and `ast`, `importlib` and `yaml` are already imported by the test files being extended. Research is disabled, so there is no `## Package Legitimacy Audit` and the fallback policy applies: if any plan finds it needs a package, every package is `[ASSUMED]` and a `<task type="checkpoint:human-verify" gate="blocking-human">` verifying it on `pypi.org/project` must precede the install. Not auto-approvable, and `workflow.auto_advance` does not apply. |

---

## Metadata

**Sources consumed:** `.planning/STATE.md`, `.planning/ROADMAP.md` (§ Phase 3.1, § Phase 4,
§ Phase 5 outcome table, § Phase 6), `.planning/REQUIREMENTS.md`, `06-CONTEXT.md`,
`06-PATTERNS.md`, `05-PLAN-OUTLINE.md` (house style), `05-04-SUMMARY.md` context via STATE.md and
the ROADMAP outcome table.

**Tree work done during outlining (2026-08-10, at `03520af`, working tree clean):** both Walmart,
GameStop, Nintendo and Amazon `goplusplus.html` fixtures parsed through `boty.parse` and their
offers printed; GameStop's and Nintendo's JSON-LD `shippingDetails` extracted verbatim and their
**types** compared; `scripts/mutation_check.py` read for `apply_mutation`'s `replace(..., 1)`
semantics, `build_sandbox()`'s copy loop, `SANDBOX_CONTENTS`, `_IGNORE` and M4's exact anchor;
`grep -n "rung=Rung\." boty/retailers.py` for anchor uniqueness; `boty/models.py` read for `Rung`,
`Extraction`, `KNOWN_RETAILERS`, `Watch.max_price` and `alertable`; `boty/cli.py:41-84` for the
routing chain; `config/products.yaml` for which watches carry a ceiling; `tests/test_support_matrix.py`
for `HEADER_CELLS`, `RUNGS`, `WORKING_RUNGS`, `rung[:1]` and `_corrupt`; `tests/test_ci_workflow.py`
for `CI`/`RELEASE`/`_all_workflow_texts` and the per-file keying; `tests/test_packaging_metadata.py`
for the borrowed-parser precedent and the three rejected sandbox answers;
`tests/test_config.py:363-374` and `tests/test_identity_check.py:36-49` for the skip precedent;
`hooks/pre-commit`; `Makefile:150-182`; `pyproject.toml` version, comment block and classifiers;
`CHANGELOG.md` preamble and trailing byte; the leaked-markup sweep re-run over the tracked tree;
`du -sh .planning` and `git ls-files .planning | wc -l`; `pytest --collect-only` (667) and
`pytest tests/test_support_matrix.py --collect-only` (31).

**No project `CLAUDE.md` and no `.claude/skills/` exist in this repo** — the governing conventions
are `06-PATTERNS.md` § *Shared Patterns* and the standing constraints in `06-CONTEXT.md`
§ *The project's standing constraints*.
