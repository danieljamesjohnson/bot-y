---
phase: 06-claims-with-gates-under-them
verified: 2026-08-11T15:13:10Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 1
overrides:
  - must_have: "The price ceiling applies to the delivered total; an unresolvable shipping cost is UNKNOWN, not a pass"
    reason: >-
      Second half only. Reversed by Dan on 2026-08-11, verbatim: "I think where we don't know
      just send it. If the user gets there and it's 50 dollar shipping that's disappointing but
      it's worse to feel like you 'missed out'." Recorded in ROADMAP.md in Phase 3.1's format
      (original quoted intact, reversal beside it) and in REQUIREMENTS.md's REQ-17 cell. REQ-17's
      text is unedited — verified byte-identical against the pre-phase baseline 4994c7d. The
      FIRST half is met as written and was verified independently by this verifier (below).
    accepted_by: "dan"
    accepted_at: "2026-08-11T00:00:00Z"
deferred:
  - truth: "No gate covers the leaked-markup class in `.planning/` (06-07-SUMMARY.md at a71e79b)"
    addressed_in: "Not scheduled — recorded, unbuilt extension"
    evidence: >-
      Recorded in REQUIREMENTS.md REQ-19's cell ("None of the three is caught by any gate this
      repo ships: `leaked_markup` is deliberately scoped to `CHANGELOG.md`, `.planning/` is
      covered by no contents rule at all"), and the widening mechanism is named in
      tests/test_changelog.py ("scripts/identity_check.py's `_PROBE_FILES` /
      `_PROBE_DIR_PREFIXES` is the shape such a widening would need"). See the assessment
      section below — verifier's judgement is that this is a correctly-scoped gate with a
      recorded extension, NOT a gap in criterion 4.
  - truth: "The live `make verify` pass (exit 2) has three pre-existing failure classes"
    addressed_in: "Carried in 06-CONTEXT.md § Deferred and .planning/STATE.md"
    evidence: >-
      "the live `make verify` failure ... Needs its own plan — polite probing plus fixture
      re-capture." Verified independently that none of the three classes can be Phase 6's:
      exactly four `max_price: 80` entries exist in config/products.yaml, all on GO Plus +
      product watches, and ZERO controls carry a ceiling — so no control's verdict can move
      under criterion 1 in either its strict or its reversed form.
---

# Phase 6: Claims With Gates Under Them — Verification Report

**Phase Goal:** Every claim this project publishes — a price filter, a matrix row, a shipped
file, a version number — has a gate under it that has been watched going red.
**Verified:** 2026-08-11T15:13:10Z
**Status:** passed
**Re-verification:** No — initial verification

**Method.** This phase's subject is gates that can go red, so it was held to its own subject.
Four of the five criteria were verified by **breaking the thing myself and watching the suite
notice**, then restoring — not by reading SUMMARY.md. Every mutation was reverted in a `trap`
and `git status --porcelain` was confirmed empty after each one. No live retailer read was made.

---

## The phase gate, reproduced

```
$ make verify-offline
=== verify: identity, lint, tests, types, fixtures, controls, mutation ===
identity check: PASS — 200 file(s), no host identity found
All checks passed!
768 passed in 10.63s
Success: no issues found in 18 source files
fixtures: 11 fixture(s) under /home/dan/CodeProjects/pokemongoplusplus/tests/fixtures
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 24 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (740 passed, 28 skipped in 10.91s)
  CAUGHT    M1 …  M2 …  M3 …  M4 …  M5 …  M6 …  M7 …  M8 …  M9 …  M10 …
  CAUGHT    M11 … M12 … M13 … M14 … M15 … M16 … M17 … M18 … M19 … M20 …
  CAUGHT    M25 pyproject.toml: 1 test(s) failed — test_the_readme_publication_instruction_names_the_declared_version
  CAUGHT    M26 README.md: 1 test(s) failed — test_the_readme_publication_instruction_names_the_declared_version
  CAUGHT    M27 boty/models.py: 4 test(s) failed — test_an_unresolved_shipping_cost_under_a_ceiling_is_alertable, …
  CAUGHT    M28 boty/models.py: 4 test(s) failed — test_an_item_price_over_the_ceiling_is_not_alertable_when_shipping_is_unknown, …
mutation check: 24/24 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
EXIT_CODE=0
```

**Exit 0, 768 passed, 24/24 mutations — exactly as recorded.** Allowed to finish; not re-run to
get a better answer.

**The M21–M24 gap is intentional, and the registry was read rather than assumed:**

```
$ grep -n 'ident="M' scripts/mutation_check.py
M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M13 M14 M15 M16 M17 M18 M19 M20 M25 M26 M27 M28
```

Twenty-four idents, gap at M21–M24. Both SUMMARYs give the reasons at the point the decision was
made, not retrospectively:

- **06-03-SUMMARY.md § "Why this plan registers NO mutation"** — *"`apply_mutation` cannot add a
  file. It performs `before.replace(search, replace, 1)` on an existing file inside the sandbox.
  The criterion is about *a workflow file that does not exist yet*, so the defect it names is
  outside the harness's reach **by construction**, not by oversight."* Plus two further reasons.
- **06-04-SUMMARY.md § "Why this plan registers NO mutation"** — *"The harness mutates `boty/`
  … `CHANGELOG.md` is not copied — confirmed this run: `(sandbox / "CHANGELOG.md").exists()` is
  `False`."* Plus three further reasons, including that widening `SANDBOX_CONTENTS` would break
  Phase 4's recorded rule for that constant.

Both close with the same sentence: *"A mutation that survives is never explained away; a mutation
that cannot exist is recorded as not existing."* **Verified: an intentional gap, not four lost
mutations.**

---

## Goal Achievement

### Observable Truths (the five ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | The price ceiling applies to the delivered total; an unresolvable shipping cost is UNKNOWN, not a pass | **MET IN PART / PASSED (override)** | First half VERIFIED by my own mutation and by direct execution. Second half REVISED by Dan 2026-08-11 and met as revised — see override. 06-06's "MET IN PART" judgement is correct and was not rounded up |
| 2 | Mutating an adapter's `Rung` against a contradicting README row turns a test red — today it leaves 131 green | ✓ VERIFIED | I mutated `check_amazon` to `Rung.BROWSER` against the unchanged `\| Amazon \| 1 \| dom \|` row: **exit 1, 9 failed, 759 passed** |
| 3 | A workflow file added under `.github/workflows/` is covered by the pin, exit-code, timeout and runner rules | ✓ VERIFIED | I wrote a violating third workflow into the real directory: **exit 1, 3 failed, 765 passed**, all four families named in one assertion. Removed in a `trap`; tree clean |
| 4 | `CHANGELOG.md` is gated on its contents, not its existence — the leaked-markup class cannot ship again | ✓ VERIFIED | I appended the byte-exact tail recovered from `2ac965f^` (never retyped): **exit 1, 2 failed, 766 passed**, naming both lines and both shapes |
| 5 | `pyproject.toml` reads `0.2.0`, agrees with the project's milestone version, and cannot silently diverge | ✓ VERIFIED | Reads `0.2.0`. I disagreed it **both directions** — `0.21.0` vs `v0.2` → 4 failed; `v0.3` vs `0.2.0` → 2 failed. The `startswith` trap is closed component-wise |

**Score:** 5/5 (one via override)

---

### Criterion 1 — the delivered-total ceiling, executed

**Note:** REVISED by Dan on 2026-08-11. 06-06 recorded this **MET IN PART**, deliberately not
rounded up. I checked that judgement and it is right.

**The half that is MET as written**, run against the real code:

```
$ .venv/bin/python  # Watch(max_price=80.0), Availability.IN_STOCK
resolvable, under ceiling (54.99 + 6.99)     delivered_total=61.980000000000004  alertable=True   availability=IN_STOCK
resolvable, OVER ceiling (54.99 + 45.00)     delivered_total=99.99000000000001   alertable=False  availability=IN_STOCK
resolvable free shipping (0.0 survives)      delivered_total=54.99               alertable=True   availability=IN_STOCK
unresolvable shipping (None) under cap       delivered_total=None                alertable=True   availability=IN_STOCK
unresolvable shipping, price OVER cap        delivered_total=None                alertable=False  availability=IN_STOCK
NEGATIVE shipping refused                    delivered_total=None                alertable=True   availability=IN_STOCK
price unreadable + ceiling                   delivered_total=None                alertable=False  availability=IN_STOCK

established_shipping(-20.0) = None   established_shipping(0.0) = 0.0
```

- **Ceiling measures the delivered total where shipping resolves** — `54.99 + 6.99 =
  61.980000000000004`, never rounded. ✓
- **A resolvable total ABOVE the ceiling is still suppressed** — `54.99 + 45.00` → `alertable
  False`. This is the exact case REQ-17's second sentence names, and it is still closed wherever
  the number is readable. ✓
- **Nothing is guessed** — `0.0` survives as a positive claim; a negative figure is refused; the
  absence of a claim never collapses to `$0.00`. ✓
- **`Availability` is untouched** — IN_STOCK in every row above. No reading became OUT_OF_STOCK
  and no UNKNOWN was resolved into a verdict. ✓

**The readers fill the field or refuse to**, read out of the real captures:

```
gamestop/goplusplus.html         -> [(54.99, 6.99, 'GameStop')]                  # OfferShippingDetails object
nintendo/goplusplus.html         -> [(54.99, None,  'Nintendo of America Inc.')] # prose under the identical key -> nothing
walmart/goplusplus.html          -> [(229.99, 0.0,  'Clove Brothers LLC')]       # reseller; 229.99 > 80 -> suppressed
walmart/milk-control.html        -> [(2.42,  None,  'Walmart.com')]              # the real 7.95 fulfilmentPrice read nowhere
```

**My own mutation — rebuilding the pre-REQ-17 bug** (ceiling back on the item price):

```
$ # boty/models.py: `return total <= max_price` -> `return self.price <= max_price`
FAILED tests/test_models.py::test_the_ceiling_bites_on_the_delivered_total_and_on_nothing_else
E   assert r.alertable is False   ->   AssertionError: assert True is False
1 failed, 767 passed
```

**My own mutation — making the code guess free shipping**:

```
$ # boty/models.py established_shipping: `return None` -> `return 0.0`
FAILED tests/test_alert_text.py::test_a_refused_shipping_figure_never_reaches_a_phone
FAILED tests/test_models.py::test_established_shipping_trusts_a_claim_and_refuses_the_absence_of_one
FAILED tests/test_models.py::test_a_negative_shipping_cost_never_lowers_a_delivered_total
FAILED tests/test_retailers.py::test_a_number_in_a_field_never_observed_carrying_one_is_not_a_shipping_cost
… 9 failed, 759 passed
```

**The half that is REVISED**, and the mitigation rendered rather than described:

```
TITLE: IN STOCK: GO Plus +          TITLE: IN STOCK: GO Plus +
GO Plus + at walmart                GO Plus + at walmart
price: $54.99   shipping: unknown   price: $54.99   shipping: $6.99
https://x/1                         https://x/1
```

Same shape either way; no delivered total stated in either. An unresolvable cost falls back to
the item price and the alert goes out. **The hole REQ-17's second sentence names is reopened,
knowingly, by the user** — with a visible empty field as the whole of the mitigation. "Just send
it" did not mean "at any price": the item-price ceiling still binds (`$229.99` with unread
shipping → `alertable False`).

**REQ-17's text was not edited** — verified byte-identical against baseline `4994c7d`.

---

### Criterion 2 — mutating an adapter's Rung, by my own hand

```
$ # boty/retailers.py check_amazon: rung=Rung.TLS -> rung=Rung.BROWSER
MUTATED check_amazon: Rung.TLS -> Rung.BROWSER (README still says '| Amazon | 1 | dom |')
$ grep -oE '^\| Amazon \| [^|]* \| [^|]* \|' README.md
| Amazon | 1 | dom |

$ .venv/bin/python -m pytest tests/ -q
E  AssertionError: assert {'Amazon': ('1', '3')} == {'Target': ('3', '1')}
FAILED tests/test_support_matrix.py::test_every_matrix_rung_cell_matches_the_rung_its_adapter_takes
FAILED tests/test_support_matrix.py::test_an_adapter_taking_a_rung_the_readme_does_not_claim_fails
FAILED tests/test_support_matrix.py::test_a_readme_rung_cell_contradicting_the_code_fails
FAILED tests/test_support_matrix.py::test_routing_a_retailer_to_another_retailers_adapter_fails
FAILED tests/test_support_matrix.py::test_a_rung_four_row_whose_retailer_gains_an_adapter_fails
FAILED tests/test_support_matrix.py::test_best_buys_conditional_cell_must_name_both_of_its_rungs
FAILED tests/test_support_matrix.py::test_an_adapter_that_states_no_rung_is_not_mistaken_for_no_adapter
FAILED tests/test_support_matrix.py::test_the_amazon_rung_mutation_moves_check_amazon_and_only_check_amazon
FAILED tests/test_support_matrix.py::test_the_target_routing_mutation_moves_target_and_only_target
9 failed, 759 passed in 10.69s   (PYTEST_EXIT=1)
```

This is the criterion's own sentence, executed. The `131` it names is a pre-Phase-5 figure that
was **not edited**; the gate that used to leave it green now turns nine tests red. Tree restored,
`git status --porcelain` empty.

---

### Criterion 3 — a new workflow file, written into the real directory

Probe: `.github/workflows/zz-verifier-probe.yml`, one violation per family — `runs-on:
ubuntu-latest`, `uses: actions/checkout@v4`, no `timeout-minutes`, `run: make verify-offline ||
true`. Removed in a `trap ... EXIT`; **no mutation sandbox was built while it existed.**

```
$ .venv/bin/python -m pytest tests/test_ci_workflow.py::test_every_workflow_in_this_directory_passes_every_directory_rule -q
>   assert reported == {}, reported
E   AssertionError: {'pin': ["zz-verifier-probe.yml: actions/checkout: ref 'v4' is not a 40-character commit SHA"],
E                    'exit-code': ['zz-verifier-probe.yml: an or-fallback that discards the exit …'],
E                    'timeout': ['zz-verifier-probe.yml: probe: timeout-minutes=None'],
E                    'runner': ['zz-verifier-probe.yml: ubuntu-latest']}
1 failed   (PYTEST_EXIT=1)

$ .venv/bin/python -m pytest tests/ -q
FAILED tests/test_ci_workflow.py::test_every_workflow_in_this_directory_passes_every_directory_rule
FAILED tests/test_ci_workflow.py::test_a_non_compliant_workflow_added_to_this_directory_is_reported_by_every_rule
FAILED tests/test_ci_workflow.py::test_an_untrusted_action_owner_in_a_new_workflow_is_reported_across_the_directory
3 failed, 765 passed in 10.64s   (PYTEST_EXIT=1)
```

**All four families — pin, exit-code, timeout, runner — reported in one assertion, naming the
file.** After the `trap`:

```
$ git status --porcelain      # (empty)
PORCELAIN_EMPTY=yes
$ ls -1 .github/workflows/
ci.yml
release.yml
```

---

### Criterion 4 — the CHANGELOG contents gate, fed the historical incident

```
$ git show '2ac965f^:CHANGELOG.md' | tail -2 | cat -A
</content>$
</invoke>$

$ git show '2ac965f^:CHANGELOG.md' | tail -2 >> CHANGELOG.md
$ .venv/bin/python -m pytest tests/ -q
>   assert not leaked_markup(text)
E   assert not ["line 262: the whole line is a tag: '</content>'",
E               "line 262: tool-call markup in the prose: '</content>'",
E               "line 263: the whole line is a tag: '</invoke>'",
E               "line 263: tool-call markup in the prose: '</invoke>'"]
FAILED tests/test_changelog.py::test_the_shipped_changelog_carries_no_leaked_markup
FAILED tests/test_changelog.py::test_the_shipped_file_is_clean_or_the_corruption_tests_prove_nothing
2 failed, 766 passed in 10.56s   (PYTEST_EXIT=1)
```

Restored with `git checkout -- CHANGELOG.md`; tree clean. **The gate bites on the exact bytes
that shipped, recovered from git and never retyped.** Both shapes are reported, on both lines.

---

### Criterion 5 — the version binding, disagreed in both directions

```
$ grep -n '^version' pyproject.toml
35:version = "0.2.0"                    # reads 0.2.0 ✓
$ grep -n "^milestone:" .planning/STATE.md
3:milestone: v0.2

# direction 1: move pyproject, keep the milestone — and pick the startswith trap on purpose
$ # version = "0.2.0" -> "0.21.0"
E  AssertionError: ["README.md states 'v0.2.0' … but pyproject.toml declares '0.21.0' …
E   Compared as component lists rather than as a string prefix, because "0.21.0".startswith("0.2") is True']
FAILED tests/test_packaging_metadata.py::test_the_readme_publication_instruction_names_the_declared_version
FAILED tests/test_packaging_metadata.py::test_the_changelog_top_release_heading_names_the_declared_version
FAILED tests/test_packaging_metadata.py::test_the_projects_own_milestone_names_the_declared_version
FAILED tests/test_packaging_metadata.py::test_all_four_statements_of_the_version_agree_right_now
4 failed, 764 passed   (PYTEST_EXIT=1)

# direction 2: move the milestone, keep pyproject
$ # .planning/STATE.md: milestone: v0.2 -> v0.3
FAILED tests/test_packaging_metadata.py::test_the_projects_own_milestone_names_the_declared_version
FAILED tests/test_packaging_metadata.py::test_all_four_statements_of_the_version_agree_right_now
2 failed, 39 passed   (PYTEST_EXIT=1)
```

**"Cannot silently diverge" is a two-way binding, and both ways bite.** The `startswith` trap is
closed component-wise and the failure message says so. Tree restored both times.

---

## The two claims most able to flatter the phase

### 1. "No criterion's text was reworded anywhere" — CHECKED WITH GIT, INDEPENDENTLY

06-06's own control used a **set** of criterion bodies against `HEAD~1`. I ran a stronger check:
an ordered, line-numbered diff against `4994c7d`, the commit immediately **before** Phase 6
started.

```
$ diff <(git show 4994c7d:.planning/ROADMAP.md | grep -nE '^  [0-9]+\. ') \
       <(grep -nE '^  [0-9]+\. ' .planning/ROADMAP.md)
IDENTICAL (text and line numbers)

$ git show 4994c7d:.planning/ROADMAP.md | grep -cE '^  [0-9]+\. '   ->  41
$ grep -cE '^  [0-9]+\. ' .planning/ROADMAP.md                       ->  41
```

**Every criterion line in the whole document is byte-identical AND at the same line number.**
Nothing was reworded, shortened, merged, amended, moved or renumbered.

The `40` in 06-06's SUMMARY versus my `41` is not a discrepancy — their control de-duplicates
into a `set`, and exactly one criterion body occurs twice:

```
$ grep -oE '^  [0-9]+\. .*' .planning/ROADMAP.md | sed -E 's/^  [0-9]+\. //' | sort | uniq -d
`make verify` exits 0
```

**Phase 5's closing table, checked against the pre-phase baseline** (06-06 only checked against
`HEAD~1`):

```
phase5 table rows: baseline 8 now 8
byte-identical: True | bytes: 4241
```

**REQ-17 … REQ-20 in REQUIREMENTS.md**, same baseline:

```
REQ-17..REQ-20 TEXT IDENTICAL (only the [ ]->[x] checkbox differs)
```

**Verdict: the claim holds, and holds against a wider baseline than the one it was asserted
against.**

### 2. "M21–M24 is an intentional gap, not four lost mutations" — CONFIRMED

Registry read directly (above): M1–M20, M25–M28 = 24. Reasons recorded at the time in
06-03-SUMMARY.md § "Why this plan registers NO mutation, and why the M21-M22 gap is deliberate"
and 06-04-SUMMARY.md § "Why this plan registers NO mutation, and why the M21-M24 gap is
deliberate". Both are substantive, measured (06-04 stat-ed the sandbox: `(sandbox /
"CHANGELOG.md").exists()` is `False`), and both instruct the closing plan not to read the gap as
a loss. **Verdict: intentional.**

---

## The outstanding item, assessed rather than assumed

**Question:** `06-07-SUMMARY.md` was committed at `a71e79b` carrying leaked tool-call markup —
the exact defect REQ-19 exists to close, one day after the gate landed — and no gate this repo
ships covers it. Is that a gap in criterion 4?

**Confirmed as fact first:**

```
$ git show a71e79b:.planning/phases/.../06-07-SUMMARY.md | tail -5 | cat -A
---$
*Phase: 06-claims-with-gates-under-them*$
*Completed: 2026-08-11*$
</content>$
</invoke>$

$ tail -4 .planning/phases/.../06-07-SUMMARY.md      # HEAD — clean
$ git show 7355034 --stat
    fix(06-06): the third instance — 06-07-SUMMARY shipped the defect REQ-19 names
```

**Verdict: a correctly-scoped gate with a recorded, unbuilt extension — NOT a gap in criterion
4.** Four reasons, in order of weight:

1. **Criterion 4 names its subject.** It reads "`CHANGELOG.md` is gated on its **contents**".
   The gate is on `CHANGELOG.md` and I watched it go red on the exact bytes that shipped. The
   criterion is met on its own terms, and this project's standing rule is that a criterion is
   never amended — in either direction, to make it meetable or to make it broader.
2. **REQ-19's own subject is "files that ship to a stranger", and `.planning/` does not ship.**
   Measured, not assumed: `MANIFEST.in` carries `prune .planning`, and
   `test_every_unpackaged_top_level_directory_is_pruned_from_the_sdist` **passes**, so a new
   top-level directory cannot silently enter the sdist. `CHANGELOG.md` is `include`d in the
   sdist and is the `[project.urls] Changelog` target; `.planning/` is neither. The publication
   path REQ-19 is written about does not carry the defect.
3. **The narrow scope is argued structurally, not by convenience, and the argument is itself
   gated.** `tests/test_changelog.py` records that a tree-scoped rule would redden *its own
   definition* by construction, because the module must contain the shapes it forbids — and that
   is asserted rather than claimed by
   `test_this_gate_would_redden_its_own_definition_if_it_were_scoped_to_the_tree`, which
   **passes**. The widening mechanism is named in place (`scripts/identity_check.py`'s
   `_PROBE_FILES` / `_PROBE_DIR_PREFIXES`) so a future widening starts from the right place.
4. **The instance was found by measurement and recorded, not smoothed over.** 06-06 found it at
   close, removed it at `7355034`, and wrote it into REQ-19's cell with the commit hash and the
   sentence *"None of the three is caught by any gate this repo ships."* That is the house
   standard being met, not evaded.

**But it is a live question, and it should go to Dan rather than be closed here.** `QUESTIONS.md`
§ 0e establishes that this repository's history *is* pushed and public. So while `.planning/`
markup does not reach a `pip install` stranger, it *does* reach a GitHub reader. That reopens the
question at the **REQ-19 / milestone level**, where § 0e already lives as an open decision — not
at criterion 4's, whose named subject is gated and watched red. Listed under `deferred:` above.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `tests/test_changelog.py` | ~193-195 | Stale claim with no gate under it | ⚠️ **WARNING** | See below — a claim this phase's own deliverable makes, invalidated by a sibling plan in the same phase |
| `boty/parse.py`, `tests/test_changelog.py`, `tests/test_support_matrix.py`, `tests/test_parse.py`, `docs/retailer-evidence.md` | various | `TBD` / `FIXME` / `XXX` tokens | ℹ️ Info | **Not debt markers.** Every hit is the token being *quoted as the thing forbidden* (`PLACEHOLDERS = ("TODO", "TBD", "FIXME", …)`, corruption fixtures) or `\uXXXX` escape notation. No unresolved debt marker exists in any file this phase touched |

### WARNING — a stale claim inside the phase's own gate

`tests/test_changelog.py` states, beside `HISTORICAL_TAIL`:

> `git diff --stat 2ac965f -- CHANGELOG.md` is empty — the shipped file has not moved since the
> fix — so today's `CHANGELOG.md` plus this tail *is*, byte for byte, the document that shipped.

Run today, the command it names is **not** empty:

```
$ git diff --stat 2ac965f -- CHANGELOG.md
 CHANGELOG.md | 105 ++++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 103 insertions(+), 2 deletions(-)

$ git log --oneline 2ac965f..HEAD -- CHANGELOG.md
ac8155b fix(06-05): roll 1.0.0 -> 0.2.0 — the correction, not a bump
```

**06-05 invalidated 06-04's claim, inside the same phase, and nothing noticed.** The `HISTORICAL_TAIL`
bytes are still byte-exact — I proved the gate bites on them — so **criterion 4 is unaffected**
and this is not a blocker. But the *sentence* is now false, and it is a claim asserted at the
producing end with nothing checking it at the consuming one: the phase's own defect class, in the
phase's own deliverable. Recommend correcting the comment (or binding it) rather than leaving it.

---

## Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|---|---|---|---|
| REQ-17 | 06-01, 06-07 | ✓ SATISFIED (as revised) | Delivered-total ceiling verified by execution and by two independent mutations; reversal recorded, REQ-17 text byte-identical to baseline |
| REQ-18 | 06-02 | ✓ SATISFIED | Rung mutation → 9 tests red, my own hand |
| REQ-19 | 06-03, 06-04 | ✓ SATISFIED | Both halves watched red by me: workflow probe (4 families, one assertion) and CHANGELOG historical tail |
| REQ-20 | 06-05 | ✓ SATISFIED | `0.2.0`; divergence bites both directions; `startswith` trap closed component-wise |

No orphaned requirements: `grep "Phase 6" .planning/REQUIREMENTS.md` returns exactly REQ-17…REQ-20,
and all four appear in the plans' `requirements:` fields.

---

## Behavioural Spot-Checks

| Behaviour | Command | Result | Status |
|---|---|---|---|
| Phase gate green | `make verify-offline` | exit 0, 768 passed, 24/24 | ✓ PASS |
| Ceiling on delivered total | direct `Result.alertable` exercise, 7 cases | as tabled above | ✓ PASS |
| Real readers fill or refuse | `ldjson_offers` / `nextdata_offers` over 6 fixtures | 6.99 / None / 0.0 / None | ✓ PASS |
| Push body renders both states | `notify.send_restock` with a stubbed client | `shipping: unknown` / `shipping: $6.99` | ✓ PASS |
| No control carries a ceiling | parse `config/products.yaml` | 4 `max_price: 80`, all GO Plus + product watches; controls: `[]` | ✓ PASS |
| Live retailer reads | *(not run — deliberate)* | 06-06 ran the live pass once and recorded it verbatim; probing budgets capped | ? SKIP — see `deferred:` |
| Working tree unchanged | `git status --porcelain` after every mutation | empty, every time | ✓ PASS |

**On the skipped live pass.** 06-06 recorded `make verify` at exit 2 with three failure classes,
none of them Phase 6's. I did not re-run it, but I did independently verify the load-bearing
reason it cannot be Phase 6's: exactly four `max_price` entries exist, all on GO Plus + product
watches, and **zero controls carry one** — so `alertable` short-circuits before any ceiling rule
and no control's verdict can move under criterion 1 in either its strict or its reversed form.

---

## Gaps Summary

**None.** Every one of the five criteria was verified against the codebase, and four of the five
were verified by breaking the thing myself and watching the suite go red — the standard this
phase set for itself and the bar Phase 5's verifier set.

Criterion 1 is **MET IN PART as written**, which is exactly what 06-06 recorded and deliberately
did not round up. I checked that judgement against the code and it is correct: the first half —
ceiling on the delivered total where shipping resolves, resolvable totals above the ceiling still
suppressed, nothing guessed, `Availability` untouched — is true in the code and I watched two
different mutations of it go red. The second half is reversed by Dan on the record, with the
verbatim quote, the date, the measured cost he was shown, and REQ-17's own text left unedited.
That is a user reversing a decision, not an agent rewording a criterion to make finished work look
successful — and the difference is visible in the diff: **41 criterion lines, byte-identical and
at identical line numbers, against the commit before this phase began.**

Two items are outstanding and both are recorded-and-deferred rather than unmet criteria: the
`.planning/` contents-rule extension (correctly scoped today, live as a REQ-19-level question
because the history is public — belongs beside `QUESTIONS.md` § 0e), and the live `make verify`
failure classes, all three of which predate this phase and none of which can move under criterion
1.

One new WARNING was found that nobody had recorded: `tests/test_changelog.py`'s byte-identity
claim about `CHANGELOG.md`, falsified by 06-05's own commit `ac8155b` within this same phase. The
gate is unharmed; the sentence is not.

---

_Verified: 2026-08-11T15:13:10Z_
_Verifier: Claude (gsd-verifier) — every criterion mutated by hand, every mutation reverted in a `trap`, `git status --porcelain` confirmed empty after each_
