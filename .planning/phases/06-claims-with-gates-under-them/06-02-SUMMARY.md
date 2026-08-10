---
phase: 06-claims-with-gates-under-them
plan: 02
subsystem: documentation-gates
tags: [req-18, support-matrix, rung, ast-binding, mutation-testing, two-directional]

requires:
  - phase: 06-claims-with-gates-under-them
    plan: 01
    provides: "the 18-mutation registry this plan extends to 20, and the 688-test baseline it raises to 701"
  - phase: 03.1-degraded-readings
    provides: "`_extraction_mismatch` — the two-directional rule shape, and the `_corrupt`/`x_text: str | None = None` convention every corruption test here is built on"
provides:
  - "`RUNG_NUMERALS` — the `Rung` → README-numeral pin, which existed nowhere in this tree"
  - "`_routing` — retailer → adapter, read out of `cli._make_checker`'s if-chain by AST; raises rather than reporting seven clean rows"
  - "`_adapter_rungs` — adapter → rung, from literal `rung=Rung.X` keywords only"
  - "`_declared_rungs` — `3 (2 with a key)` as a two-numeral claim rather than a special case"
  - "`_rung_mismatch` — two-directional, spanning both joins, distinguishing 'no adapter' from 'an adapter that states no rung'"
  - "M19 (check_amazon's rung, uniquely anchored and bound by a test) and M20 (the routing arm)"
  - "The README paragraph stating that the Rung cell now has a gate under it"
affects: [06-06, 06-05]

tech-stack:
  added: []
  patterns:
    - "Bind a published claim to the code across EVERY join it depends on, not only the last one"
    - "A static gate that cannot parse its input raises; it never returns an empty mapping"
    - "A mutation anchor's uniqueness is a gated fact (a test), not a one-time observation at execution"
    - "Report 'the gate cannot read this' separately from 'there is nothing to read' — they are different findings"

key-files:
  created: []
  modified:
    - tests/test_support_matrix.py
    - scripts/mutation_check.py
    - README.md

key-decisions:
  - "Static AST over both joins, argued in the module docstring, with the cost — it asserts what the source says, not what runs — stated rather than buried"
  - "`RUNG_NUMERALS` lives in the test file, not in `boty/models.py`: a numeral is a documentation fact about the ladder README publishes, and the package has no consumer for it"
  - "Set EQUALITY, not containment, so Best Buy's conditional cell needs no exemption and an unnamed second rung is caught"
  - "`_routing` raises with a message naming what was not found — a rule handed `{}` reports seven clean rows"
  - "M19's anchor is the shortest UNIQUE extension of the naive one; the bare `rung=Rung.TLS,` would have mutated GameStop, Walmart and Nintendo under Amazon's name"
  - "REQ-18's text and its inaccurate 'Routing and Extraction are already pinned' parenthetical were NOT edited — the correction is a measurement note"

requirements-completed: []

duration: 41min
completed: 2026-08-10
---

# Phase 6 Plan 02: A Claim That Could Not Go Red — Summary

**The README support matrix's Rung cell is now bound to the code that takes it across BOTH joins — retailer→adapter out of `cli._make_checker`'s if-chain and adapter→rung out of `boty/retailers.py`, statically by AST, two-directionally, and watched going red nine ways — so REQ-18's own mutation, which left the entire suite green when measured hours earlier, now fails nine tests.**

## Performance

- **Duration:** ~41 min
- **Tasks:** 3
- **Files modified:** 3
- **Tests:** 688 → **701**
- **Mutations:** 18/18 → **20/20**

## Task Commits

| Task | Name | Commit |
|---|---|---|
| 1 | The re-measurement, the pin, the two joins and the rule | `36e2527` |
| 2 | Watched going red — both joins, both directions | `800b2a6` |
| 3 | M19 and M20, their anchors bound by tests, and the README paragraph | `c5efe66` |

No `boty/` file was edited. No matrix row was edited. No existing test was weakened, renamed or deleted. No dependency was added — `ast` and `re` are stdlib.

## THE PRE-GATE RE-MEASUREMENT — a measurement note, not an amendment

REQ-18's criterion reads: *"mutating `check_amazon` to return `Rung.BROWSER`, directly contradicting the shipped `| Amazon | 1 | dom |` row, **left 131 tests green**."* That figure predates Phase 5. Re-measured **before a line of the gate was written**, by applying the criterion's own edit inside `scripts/mutation_check.py`'s own sandbox so the working tree was never touched:

```
anchor occurrences: 1
pytest exit: 0
687 passed, 1 skipped in 10.50s
--- FAILED lines ---
```

There were none. **Pytest exit code 0. `687 passed, 1 skipped`.**

- **REQ-18's figure:** 131 green.
- **Re-measured on the post-06-01 tree, 2026-08-10:** 687 passed, 1 skipped, **exit 0**.

The number moved and the fact did not. **The criterion is not edited.** Contingency (b) in the plan — pytest exiting 1 because some unrelated test incidentally caught it — did not arise: nothing in the tree opposed the edit at all.

**One correction to the plan's own Task 1 snippet.** As written it raises `AttributeError: 'NoneType' object has no attribute '__dict__'` from inside `dataclasses`: `@dataclass` resolves annotations through `sys.modules[cls.__module__]`, and `spec_from_file_location` + `exec_module` does not register the module there. `sys.modules[spec.name] = module` before `exec_module` fixes it. The same fix is written into `_mutation()` in the test file, with the reason inline, because `_load_evidence_check` does not need it and the next reader will wonder why they differ.

## `make mutation` — M19 and M20 by ident, with every killing test

Full run: **20/20 mutations caught, nothing SURVIVED.** The two this plan owns, verbatim from the harness:

```
  CAUGHT    M19 boty/retailers.py: 9 test(s) failed — test_every_matrix_rung_cell_matches_the_rung_its_adapter_takes, test_an_adapter_taking_a_rung_the_readme_does_not_claim_fails, test_a_readme_rung_cell_contradicting_the_code_fails (+6 more)
  CAUGHT    M20 boty/cli.py: 8 test(s) failed — test_a_target_watch_is_dispatched_to_the_browser_and_dom_path, test_every_matrix_rung_cell_matches_the_rung_its_adapter_takes, test_a_readme_rung_cell_contradicting_the_code_fails (+5 more)
```

The harness prints only three names, so both were re-run with the full list captured. **M19 — 9 failures, every one of them the new gate:**

```
tests/test_support_matrix.py::test_every_matrix_rung_cell_matches_the_rung_its_adapter_takes
tests/test_support_matrix.py::test_an_adapter_taking_a_rung_the_readme_does_not_claim_fails
tests/test_support_matrix.py::test_a_readme_rung_cell_contradicting_the_code_fails
tests/test_support_matrix.py::test_routing_a_retailer_to_another_retailers_adapter_fails
tests/test_support_matrix.py::test_a_rung_four_row_whose_retailer_gains_an_adapter_fails
tests/test_support_matrix.py::test_best_buys_conditional_cell_must_name_both_of_its_rungs
tests/test_support_matrix.py::test_an_adapter_that_states_no_rung_is_not_mistaken_for_no_adapter
tests/test_support_matrix.py::test_the_amazon_rung_mutation_moves_check_amazon_and_only_check_amazon
tests/test_support_matrix.py::test_the_target_routing_mutation_moves_target_and_only_target
```

**M20 — 8 failures, and one of them is a PRE-EXISTING test:**

```
tests/test_retailers.py::test_a_target_watch_is_dispatched_to_the_browser_and_dom_path   <-- pre-existing
tests/test_support_matrix.py::test_every_matrix_rung_cell_matches_the_rung_its_adapter_takes
tests/test_support_matrix.py::test_a_readme_rung_cell_contradicting_the_code_fails
tests/test_support_matrix.py::test_routing_a_retailer_to_another_retailers_adapter_fails
tests/test_support_matrix.py::test_a_rung_four_row_whose_retailer_gains_an_adapter_fails
tests/test_support_matrix.py::test_best_buys_conditional_cell_must_name_both_of_its_rungs
tests/test_support_matrix.py::test_an_adapter_that_states_no_rung_is_not_mistaken_for_no_adapter
tests/test_support_matrix.py::test_the_target_routing_mutation_moves_target_and_only_target
```

That pre-existing killer **contradicts this plan's F6** and is recorded rather than hidden — see the corrections section below. It does not change what was built and it does not make M20 redundant: it pins Target's dispatch, not the README row, so it would still have been green for every other retailer's arm.

## `make verify-offline` — the gate

Run at `c5efe66`, **exit code 0**:

```
identity check: PASS — 192 file(s), no host identity found
All checks passed!
701 passed in 10.44s
  baseline  unmutated sandbox passes (700 passed, 1 skipped in 10.72s)
mutation check: 20/20 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

- **Verdict line:** `VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)`
- **Test count:** **701** (06-01's close: 688; Phase 5's close: 667)
- **Mutation ratio:** **20/20** (06-01's close: 18/18)

`make types` clean over 18 source files; `ruff` clean over `boty/`, `scripts/` and `tests/`.

`make verify` (live) was **not run**. It is not this plan's gate, it has failed live since 2026-08-06 in three known classes, and none of them is this plan's.

## M19 and M20 — the `search` strings and why each is unique

Occurrence counts measured against the **post-06-01 tree** (at `800b2a6`, immediately before registration):

| Ident | Target | `search` | Occurrences | Why unique |
|---|---|---|---|---|
| M19 | `boty/retailers.py` | `"        rung=Rung.TLS,\n        #"` | **1** | The bare `rung=Rung.TLS,` occurs **2** times — `check_html` first, then `check_amazon`. The trailing newline and indented `#` (the first character of `check_amazon`'s `sku=` comment) is the shortest extension that isolates the second |
| M20 | `boty/cli.py` | `"return check_target_browser(watch, first_party_only=cfg.first_party_only)"` | **1** | `check_target_browser` is called from exactly one place in the router, and every other reference to it in the tree is an import or a direct test call |

**Why the disambiguation mattered.** `apply_mutation` does `before.replace(search, replace, 1)` — first occurrence wins. `06-PATTERNS.md` proposed the bare anchor. That anchor mutates `check_html`, which serves **GameStop, Walmart and Nintendo**, while M19's `breaks=` sentence describes Amazon: a harness reporting a result about work it did not do. The disambiguator is one punctuation character of comment rather than comment prose, so rewording that comment cannot silently re-point the mutation, and deleting it raises `HarnessError` — the harness refusing to run rather than checking something else.

**And the uniqueness is now a gated fact rather than an observation.** `test_the_amazon_rung_mutation_moves_check_amazon_and_only_check_amazon` loads the registry by path, asserts M19's `search` occurs exactly once in the real `boty/retailers.py`, and asserts by **AST** that applying it leaves `check_html` at `("1",)` while moving `check_amazon` to `("3",)`. A string count says one place matched; it does not say which. `test_the_target_routing_mutation_moves_target_and_only_target` does the same for M20 against `boty/cli.py`.

## F1's CORRECTION — for 06-06 to carry

`06-CONTEXT.md` § *Existing Code Insights* states that `tests/test_support_matrix.py` *"already binds the README's **Routing** and **Extraction** cells to the code in both directions"*. REQ-18's own text states *"Routing and Extraction are already pinned; Rung is the gap."*

**Both are measured false, and this plan re-confirmed it against the tree before building anything.**

- `_extraction_mismatch` binds the README's Extraction cell to the README's **Rung cell**. Both of its directions are *inside the table*.
- Before this plan, `grep -n "Rung\." tests/test_support_matrix.py` returned **nothing**, and the file did not import `boty.models` at all — its only package import was `boty.config.Config`.
- There was **no README-cell → code binding of any kind** anywhere in `tests/`.

Two consequences, both carried:

1. **The code side was new construction, not a column copy**, and this plan built **both** joins — routing and rung — because neither existed. A rung-only gate would have stayed green the day `_make_checker` stopped routing amazon to `check_amazon`, and M20 exists to prove that half is load-bearing rather than to assert it.
2. **REQ-18's text is NOT edited, and neither is `REQUIREMENTS.md`.** The standing rule is that a criterion is never amended to make it meetable; the same rule points the other way — it is not amended to make it *accurate* either. This is the record for 06-06 to carry into the ROADMAP outcome table.

## Measurements that contradict this plan's `<measured_facts>`

The measurement wins in every case below, and each says which fact it corrects.

**1. F6 is WRONG about there being no existing test for the target arm.** F6 states: *"No existing test routes a **target** watch through `_make_checker` — `grep -rn 'check_target_browser' tests/` finds only direct calls to the adapter, and `test_retailers.py`'s `_make_checker` tests cover bestbuy and gamestop. So M20 is expected to be killed by the new gate and by nothing else."*

Measured: `tests/test_retailers.py::test_a_target_watch_is_dispatched_to_the_browser_and_dom_path` loads the shipped config, takes the target watch and calls `_make_checker(cfg)(target_watches[0])` with `fetch_rendered` stubbed. It is in M20's kill list. F6's grep was for `check_target_browser`; that test never names the adapter — it observes the URL the browser path asks for — so the grep could not have found it.

What follows, and what does not: M20 is **not** killed only by the new gate. It is **not** redundant either — the pre-existing test pins Target's dispatch, and would go on passing for every other retailer's arm, so it says nothing about the README row M20 exists to falsify. Nothing was rebuilt in response; the plan's own instruction was that a pre-existing killer *"is recorded, not hidden, and it does not change what was built."*

**2. F2's adapter tuple ORDER differs for Best Buy, and the set does not.** F2 quotes `'bestbuy': ('check_bestbuy_api', 'check_bestbuy_browser')`; the shipped `_routing` returns `('check_bestbuy_browser', 'check_bestbuy_api')`, because `_called_names` walks with `ast.walk` (breadth-first) and the outer arm's `return` is reached before the nested key arm's. Every rule here compares **sets**, and every assertion in the suite is either a set comparison or an explicit tuple that matches what the tree produces, so this is a note rather than a defect. Both adapters are found, which is the fact F2 was quoted for.

**3. Everything else in F2 held exactly.** All seven rows clean on arrival, `pokemoncenter` at `declared=('4',) code=()`, Best Buy at `('2', '3')` both sides. F4 held: `_verdict_from_html` does not appear in the rung map. F5's counts held on the post-06-01 tree (2 for the bare anchor, 1 for the disambiguated one). F7 held: Best Buy needed no special case. F8 held: no `SANDBOX_CONTENTS` edit was needed and both mutations were caught through it.

## What was built

**`tests/test_support_matrix.py`** — the file's module docstring gained a `WHY THE RUNG CELL IS BOUND TO THE CODE, AND WHAT THAT BINDING COSTS` section carrying the re-measurement, the both-joins argument, and the static-versus-dynamic cost **stated rather than buried**: a static gate asserts what the source *says*, not what *runs*, and the runtime half is covered by `tests/test_retailers.py`'s `_make_checker` / `result.rung` assertions. Its closing sentence now reads *"It reads four files off disk"* rather than two.

- **`RUNG_NUMERALS`** — `{Rung.TLS: "1", Rung.API: "2", Rung.BROWSER: "3"}`, a **pin** in `UNREAD_POSITIONS`' sense with the README ladder sentence and the three member docstrings quoted inline, and `models.Rung`'s own *"a dropped retailer produces no readings, so a `Rung` for it would be a value that can never appear on a `Result`"* recorded as why rung 4 has no member.
- **`_routing(cli_text=None, known=None)`** — walks to `_make_checker`, then to the nested `check` closure; every string constant in an arm's test is a retailer key and every plainly-named function called in a `return` **anywhere inside** that arm is an adapter (the recursion is what finds `check_bestbuy_api` behind the nested key check). The final top-level `return` is the fallthrough and is assigned to every `known` key no arm named. **Raises `AssertionError`** — never returns `{}` — for a missing `_make_checker`, a missing closure or a missing fallthrough, each naming what was not found.
- **`_adapter_rungs(retailers_text=None)`** — literal `rung=Rung.X` keywords only, scoped so a nested function's claim is not credited to its parent. `rung=rung` inside `_verdict_from_html` is an `ast.Name` and deliberately does not count: a pass-through is not a claim about which rung anything takes.
- **`_declared_rungs(cell)`** — `cell[:1]` plus every parenthesised digit, so `3 (2 with a key)` declares `('2', '3')` and needs no exemption.
- **`_rung_mismatch(rows, routing=None, rungs=None)`** — set **equality** for a working-rung row, **no adapter at all** for a non-working one, and `"<adapter> states no rung"` reported distinctly from `"no adapter"`.
- **Four shipped-tree tests**, green on arrival, plus **seven corruption tests** and **two anchor-binding tests**.

**`scripts/mutation_check.py`** — M19 and M20 registered with their full reasoning: the two-occurrence trap and its resolution, and M6/M7's precedent for why the routing join needs a mutation of its own rather than riding on M19. `search` strings copied verbatim out of the files they target. Idents were reserved by the phase plan and the highest present was M18, so no gap was created.

**`README.md`** — one new paragraph immediately after the Extraction paragraph, stating that the Rung cell is now bound to the code in both directions and across both joins, that a conditional cell binds both of its numerals, that a rung-4 row must have no adapter, and that the binding is static with the cost named. Verified against the three live gates it had to respect:

- `grep -cE '(\.(py|md|toml|in|yml)|Makefile):[0-9]+' README.md` → **0**. No line-numbered citation.
- No line in the paragraph starts with `|`, so `_matrix` cannot consume it as a table row.
- `grep -oE 'v[0-9]+\.[0-9]+(\.[0-9]+)?' README.md` → exactly **one** occurrence, `v1.0.0` in the publication sentence, unchanged. 06-05's M26 anchor stays unambiguous.
- `git diff --stat README.md` → **17 insertions, 0 deletions**. No matrix row touched.

## The nine red-watches, and what each one watches

| Test | Direction watched | What would be true without it |
|---|---|---|
| `..._an_adapter_taking_a_rung_the_readme_does_not_claim_fails` | code edited | Criterion 2 unmet. This IS REQ-18, as a test |
| — its second assertion | the anchor moved the right adapter | A red test proving something about GameStop, Walmart and Nintendo under Amazon's name |
| `..._a_readme_rung_cell_contradicting_the_code_fails` | **table** edited, no code change | The binding would be satisfied by a README that was right once and then drifted |
| `..._routing_a_retailer_to_another_retailers_adapter_fails` | the routing join alone | A rung-only gate stays green while Target is read at rung 1 |
| `..._a_rung_four_row_whose_retailer_gains_an_adapter_fails` | the rung-4 direction | Rung 4 becomes a free cell; `_overstated` cannot see this, because it reads the config |
| `..._best_buys_conditional_cell_must_name_both_of_its_rungs` | both, incl. the **clean side** | Either the parenthetical is unbacked, or no cell may carry one and the honest state is unrepresentable |
| `..._an_adapter_that_states_no_rung_is_not_mistaken_for_no_adapter` | the gate's own blind spot | An adapter this gate cannot read masquerades as a retailer nothing reads — the rung-4 hole |
| `..._a_router_this_gate_cannot_parse_raises...` | the vacuous pass, three ways | `{}` reports seven clean rows and every gate above it passes |
| `..._the_amazon/target_..._mutation_moves_..._and_only_...` | the harness's own anchors | Anchor uniqueness is an execution-day observation somebody can silently break |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The plan's Task 1 measurement snippet does not run**

- **Found during:** Task 1, step 1 — the very first command.
- **Issue:** `spec_from_file_location` + `module_from_spec` + `exec_module` without registering the module in `sys.modules` makes `@dataclass` fail with `AttributeError: 'NoneType' object has no attribute '__dict__'` from inside `dataclasses`, because it resolves annotations through `sys.modules[cls.__module__]`. `scripts/mutation_check.py` has a frozen dataclass at module level; `scripts/evidence_check.py`, which the file's existing `_load_evidence_check` loads the same way, does not.
- **Fix:** `sys.modules[spec.name] = module` before `exec_module`, in the throwaway measurement script and permanently in `_mutation()` in the test file, with the reason written inline so the asymmetry with `_load_evidence_check` is not read as an inconsistency.
- **Files modified:** `tests/test_support_matrix.py`.
- **Verification:** the measurement ran; `test_the_amazon_rung_mutation_...` and `test_the_target_routing_mutation_...` pass and both kill their mutations.
- **Committed in:** `36e2527` (measurement), `c5efe66` (the permanent loader).

**2. [Rule 2 - Missing critical] `test_every_retailer_the_router_names_is_a_known_retailer` needs the arm keys, not the routing map**

- **Found during:** Task 1, step 6.
- **Issue:** `_routing()` assigns the fallthrough to every member of `known`, so `set(_routing()) <= KNOWN_RETAILERS` is true by construction and the named test would have asserted nothing. A typo in an arm (`"targat"`) does not fail loudly — the watch falls through to `check_html`, a real transport — so this is exactly the case worth catching.
- **Fix:** No new helper. `_routing(known=frozenset())` yields exactly the keys the router names in an `if`, because the fallthrough is then assigned to nobody; the parameter that exists for the rung-4 red-watch answers this question too. Documented in `_routing`'s docstring and in the test.
- **Files modified:** `tests/test_support_matrix.py`.
- **Verification:** the test fails if an arm names a retailer outside `KNOWN_RETAILERS`; `models.KNOWN_RETAILERS`' own comment names those three `==` comparisons as its consumers and nothing checked them before.
- **Committed in:** `36e2527`.

**3. [Rule 2 - Missing critical] The unparseable-router watch covers three failures, not one**

- **Found during:** Task 2, test 7.
- **Issue:** The plan specified one arm — `_make_checker` renamed. `_routing` raises in three independent places, and two of them (a renamed `check` closure, a replaced fallthrough `return`) are equally plausible edits that would each have produced a vacuous pass had the assertion been missing.
- **Fix:** All three watched in the one test, each derived from the real `boty/cli.py` through `_corrupt_source`, each matched on the part of the message that names what was not found.
- **Files modified:** `tests/test_support_matrix.py`.
- **Verification:** `pytest.raises(AssertionError, match=...)` on all three; the closure arm's matcher was tightened from `"check"` (which the `_make_checker` message also contains) to `"nested \`check\` closure"`.
- **Committed in:** `800b2a6`.

**4. [Rule 3 - Blocking] `ruff` SIM300 on a Yoda-free comparison**

- **Found during:** Task 2 verification.
- **Issue:** `assert RUNGS - WORKING_RUNGS == {"4"}` trips SIM300; `ruff` is a `make verify-offline` stage.
- **Fix:** Written as `{"4"} == RUNGS - WORKING_RUNGS`, ruff's own suggested form.
- **Files modified:** `tests/test_support_matrix.py`.
- **Verification:** `ruff check boty scripts tests` → `All checks passed!`.
- **Committed in:** `800b2a6`.

---

**Total deviations:** 4 auto-fixed (2 blocking, 2 missing critical). No Rule 4 architectural decision arose. **No scope creep:** three of the four are corrections forced by the tree, and the fourth widens a red-watch the plan already named.

## Issues Encountered

None beyond the four above. The plan's four named failure shapes — a survivor, a `HarnessError`, an ambiguous anchor, a shipped-tree test red on arrival — none of them materialised. The four shipped-tree tests were green on their first run, which is what F2 predicted and what the plan required: *"the gate goes in green and is made red by corruption, never the other way round."*

## Known Stubs

None. Nothing is deferred, placeholdered or left for a later plan. Both joins were built; the prohibition in the plan's `<decision>` block — no "v1", no "the routing half in a later phase" — was not tested.

## Threat Flags

None. No new network endpoint, auth path, file access pattern or schema change at a trust boundary. No file under `boty/` was edited; the gate reads that package as **text** and does not import it. No fixture was captured or edited, no store number, postal code or host identity is handled anywhere in this plan, and `scripts/identity_check.py` passed over all **192** tracked files inside `make verify-offline`.

Every `mitigate` disposition in the plan's threat register was applied: T-06-06 (both joins, two-directional, four red-watch directions), T-06-12 (`_routing` raises, watched three ways; `_adapter_rungs` raises on an unrecognised member; the pin asserted against the enum), T-06-13 (anchor disambiguated **and bound by a test**), T-06-14 ("states no rung" reported distinctly, watched), T-06-15 (README paragraph verified against all three of its live gates by command). T-06-07 was accepted with its reason: two more sandbox builds, no new Makefile stage, `test_the_documented_stages_are_the_stages_verify_runs` unaffected. T-06-SC did not arise — no package was installed.

## REQ-18 status

**Deliberately left Pending.** 06-06 closes it by measuring what landed, on 04-05's and 05-01's precedent — and it has two things to carry beyond the build: the re-measured `687 passed, 1 skipped / exit 0` figure beside the criterion's `131`, and F1's correction that neither `06-CONTEXT.md` nor REQ-18's own parenthetical is accurate about Routing and Extraction already being pinned. `REQUIREMENTS.md` was not edited by this plan.

## Next Phase Readiness

- Criterion 2 of five is built and gated. **The sentence REQ-18 was written to make true is now true**, observed CAUGHT by ident.
- 06-03, 06-04 and 06-05 are unblocked. Idents **M21 onward** remain free; this plan took M19 and M20 and created no gap.
- 06-05's M26 anchor is safe: `README.md` still carries exactly one `vX.Y.Z`-shaped token.
- The support matrix now has **three** of its columns bound — Rung to the code, Extraction to Rung, and the overstatement rule to `config/products.yaml`. The `robots.txt` and Terms columns remain bound only to a vocabulary and to `docs/retailer-evidence.md`, which is the honest state: they are claims about documents, not about this tree.

## Self-Check: PASSED

- `tests/test_support_matrix.py`, `scripts/mutation_check.py`, `README.md` — all present and modified.
- Commits `36e2527`, `800b2a6`, `c5efe66` — all found in `git log`.
- `grep -c 'ident="M19"\|ident="M20"'` over non-comment lines of `scripts/mutation_check.py` → **2**.
- `make verify-offline` → exit **0**, `701 passed`, **20/20**.

---
*Phase: 06-claims-with-gates-under-them*
*Completed: 2026-08-10*
