---
phase: 05-a-reading-means-something
plan: 01
subsystem: detector
tags: [walmart, store-identity, nextdata, identity-guard, status-json, dashboard]

# Dependency graph
requires:
  - phase: 04-open-source-ready
    provides: "scripts/identity_check.py running at commit time over every tracked file; make verify-offline as the phase gate"
  - phase: 03.1-hard-two-and-honest-records
    provides: "the declared-last-with-a-default field convention (rung, extraction) and the two-ends contract between status.write and the dashboard"
provides:
  - "Watch.store_id — a per-watch store pin in config/products.yaml with no default"
  - "Result.store — which store the page said answered, on every check_html return path"
  - "parse.nextdata_store — the store, off a pinned __NEXT_DATA__ path, no regex over raw HTML, no \"0\" special case"
  - "status.json keys `store` and `store_pinned`, null-not-zero when absent"
  - "a store tag in `boty check` output and on the dashboard, at two visual weights"
  - "an identity-guard rule that catches a store number typed into a YAML config key, watched going red first"
affects: [05-02, 05-03, 05-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "a carrier column in identity_check.py's `keyed` tuple, not another key spelling"
    - "the store read from the SAME __NEXT_DATA__ node the offer comes from, so price and store cannot disagree"
    - "publish the raw fact beside any derived flag (store + store_pinned, as rung + extraction sit beside degraded)"

key-files:
  created: []
  modified:
    - scripts/identity_check.py
    - boty/models.py
    - boty/config.py
    - boty/parse.py
    - boty/retailers.py
    - boty/status.py
    - boty/cli.py
    - served/boty/index.html
    - config/products.yaml
    - tests/fixtures/walmart/goplusplus.json
    - tests/fixtures/walmart/milk-control.json
    - tests/test_fetch.py
    - tests/test_identity_check.py
    - tests/test_config.py
    - tests/test_models.py
    - tests/test_parse.py
    - tests/test_retailers.py
    - tests/test_status.py
    - tests/test_dashboard.py

key-decisions:
  - "The real store number reaches the daemon as ${WALMART_STORE_ID} from the mode-600 EnvironmentFile at /home/dan/.config/boty/env — never a literal in the tracked config, never a second overlay file"
  - "parse.nextdata_store reads product.location.storeIds; contentLayout.pageMetadata.location.storeId was rejected because it is page-layout metadata rather than a fact about the offer"
  - "No \"0\" special case anywhere: \"0\" in the Walmart fixtures is this repo's redaction placeholder from 8dec2e0, not a Walmart sentinel — 05-PATTERNS.md's inference is wrong"
  - "storeIds is accepted only as a list of exactly one string; a two-entry list returns None rather than guessing at ordering"
  - "An absent store_id LOADS and is carried as data; a bool REFUSES the file — _sub's idiom for the absence, _price's for the typo"
  - "The identity rule's character classes are load-bearing and must not be simplified to a lowercase-only form, which does not catch storeId on its own"
  - "REQ-14 deliberately NOT marked complete — this plan delivers the recording half; the verdict half is 05-02"

patterns-established:
  - "A gate is watched going red against the SHIPPED script, never against a drifted test-local copy of the same rule"
  - "A comment paragraph beside a redacted-class config key carries no digits at all, because the guard does not scan commented lines"

requirements-completed: []

# Metrics
duration: 25min
completed: 2026-08-10
---

# Phase 5 Plan 01: The Store Becomes A Fact Summary

**A Walmart reading now records which store answered — `parse.nextdata_store` off `product.location.storeIds`, `Watch.store_id` pinned per watch with no default, both published in `status.json`, `boty check` and the dashboard row — behind an identity-guard rule that was measurably blind to `store_id:` and was watched going red before it was trusted.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-08-10T10:18Z (approx; first task commit 10:27)
- **Completed:** 2026-08-10T10:43Z
- **Tasks:** 4
- **Files modified:** 19

## Accomplishments

- The leak hole this phase opens was closed **first**, before the key was written into a tracked public file, and the rule was watched going red against all four YAML spellings.
- `Watch.store_id` and `Result.store` exist, both declared last with defaults, so no pre-existing construction site changed meaning.
- The store is read off the *same node* the offer comes from, so a price and a store cannot come from different subtrees and disagree — the invariant the whole phase rests on.
- **No verdict moved.** The Walmart milk control still reads `IN_STOCK` at `2.42` with `Walmart.com` in `detail`, and a structural test asserts `_verdict_from_html` never mentions `store_id`.

## Task Commits

1. **Task 1: the leak gate** — `e6b6be0` (feat)
2. **Task 2: the pin** — `6cbe368` (feat)
3. **Task 3: reading which store answered** — `20cc32f` (feat)
4. **Task 4: publishing it** — `477ed7f` (feat)

## The red-watch transcript — verbatim, all four spellings

The one gate this plan adds. Run by loading `scripts/identity_check.py` through
`importlib.util.spec_from_file_location` and calling `_identity_leaks` directly.

**BEFORE the edit** (the shipped rule as it stood at `03520af`):

```
'  store_id: 12345\n'                        -> []
'  store_id: "12345"\n'                      -> []
'    storeId: 202\n'                         -> []
'  STORE_ID: 12345\n'                        -> []
'  store_id: ${WALMART_STORE_ID}\n'          -> []
'  state_path: state.json\n'                 -> []
'  status_path: served/boty/status.json\n'   -> []
'  store_id: "0"\n'                          -> []
'  store_id: 0\n'                            -> []
'  store_id: "00000"\n'                      -> []
'  store_id: 00000\n'                        -> []
'# store_id: 12345 in a comment\n'           -> []
'  restore_id: 12345\n'                      -> []
```

**AFTER the edit:**

```
'  store_id: 12345\n'                        -> ['config/products.yaml: store number in a config key 12345']
'  store_id: "12345"\n'                      -> ['config/products.yaml: store number in a config key 12345']
'    storeId: 202\n'                         -> ['config/products.yaml: store number in a config key 202']
'  STORE_ID: 12345\n'                        -> ['config/products.yaml: store number in a config key 12345']
'  store_id: ${WALMART_STORE_ID}\n'          -> []
'  state_path: state.json\n'                 -> []
'  status_path: served/boty/status.json\n'   -> []
'  store_id: "0"\n'                          -> []
'  store_id: 0\n'                            -> []
'  store_id: "00000"\n'                      -> []
'  store_id: 00000\n'                        -> []
'# store_id: 12345 in a comment\n'           -> []
'  restore_id: 12345\n'                      -> ['config/products.yaml: store number in a config key 12345']
```

All four spellings, not only `store_id: 12345`. The `storeId` spelling is the one
an earlier draft of this plan claimed without executing, and it is why the
pattern's character classes are written the way they are. `12345` and `202` are
invented placeholders; `tests/test_fetch.py` asserts mechanically that no probe
value in it appears in any captured fixture.

The rule was also observed reddening in the test suite before it existed:
`test_a_store_number_cannot_enter_through_a_yaml_config_key` and
`test_the_config_key_rules_two_residuals_are_what_was_measured` both FAILED
against the shipped script, and passed after the one-line addition.

### The two measured residuals of the new rule

Recorded in the rule's own comment beside the measurement that established each,
and pinned in `tests/test_fetch.py` so a later widening has to move them
deliberately:

1. **A `#`-commented line is not scanned.** `'# store_id: 12345 in a comment\n'` → `[]`.
   `^\s*` followed by `[A-Za-z_]*` cannot cross the `#`. That is the property
   that keeps the rule off prose, and it is also a hole — which is *why* the
   comment paragraph beside `store_id` in `config/products.yaml` carries no
   digits at all, not even an invented example, and says so in one clause.
2. **`restore_id` is over-caught**, because `[A-Za-z_]*store` matches inside
   `restore`. Fail-closed, on the stated precedent of the ZIP+4 rule one block
   up: a false positive costs one redaction, a false negative costs a public
   address.

## The gate caught something real, in this plan, in this repo

The first draft of a comment in `tests/test_config.py` quoted a four-digit store
number as an example of a value that trips the guard. `identity_check --all` then
reported `tests/test_config.py: store number 4174` and refused the commit. The
literal was changed; **nothing was added to the allow-list**, which is the
mutation `test_the_allow_list_cannot_absorb_a_real_value` exists to catch. Noted
here because it is the only evidence in this plan that the pre-existing rules
bite on a tracked test file, and it was obtained by accident rather than designed.

## Findings recorded for later plans — flagged, not silently corrected

### 1. `_identity_leaks` exists twice, and the two copies have drifted

`scripts/identity_check.py` (the copy the pre-commit hook and `make verify`
actually run) and `tests/test_fetch.py` both define `_identity_leaks`. Measured
by diffing the two function sources, 2026-08-10 — two *behavioural* differences:

| | shipped script | `tests/test_fetch.py` copy |
|---|---|---|
| `allowed` vocabulary | contains `"ZZ"` | does **not** contain `"ZZ"` |
| reserved-IP test | calls `_is_reserved_ip(...)` (RFC 5737 + RFC 1918 + loopback) | bare `match.group(1).startswith("192.0.2.")` |

(There are also comment-text differences, which are not drift: the script's
comments use `<n>` / `NNNNN` placeholders *because the script is scanned by its
own rule*, while the test copy is the sole `_PROBE_FILES` member and may carry
digits.)

This contradicts the script's own stated design — "one rule, three callers".
**Only the shipped script was widened.** The drift was deliberately **not**
reconciled: adding `"ZZ"` to the test copy's vocabulary would redden the
`{"stateOrProvinceCode":"ZZ"}` grid cell in
`test_each_rule_fires_on_a_value_of_the_REAL_shape_not_just_the_synthetic_one`,
and that is a decision with its own argument to make, not a side effect of a
store-pin plan. Recorded for a later plan in the same form 05-04 is held to for
the ROADMAP numbering typo.

### 2. `tests/test_fetch.py` is a table omission in `05-PLAN-OUTLINE.md`

The file is in this plan's `files_modified` because `_PROBE_FILES` is exactly
`{"tests/test_fetch.py"}` — a literal `store_id: <digits>` probe would be caught
by the very rule under test anywhere else, and `_PROBE_FILES` was **not** grown
(`test_the_probe_file_exemption_cannot_quietly_grow` still passes with one
entry). The outline names it in neither 05-01's per-plan sketch nor its
file-contention table, while it *does* name `tests/test_identity_check.py`. No
other plan in this phase enters it, so there was no contention to miss — recorded
so the phase's audit reconciles the table against what was actually touched.

### 3. `tests/test_models.py` is a second, smaller table omission

Not in this plan's `files_modified` either, though the plan's own Task 2
`<verify>` block runs it. Three tests were added there — the `Watch`/`Result`
default-declaration pins and the "recording a store moves no verdict" assertion —
because that module's stated subject is exactly the declared-last-with-a-default
contract. No other plan in this phase enters it.

## The path decision, so 05-02 does not reopen it

`parse.nextdata_store` reads **`product.location.storeIds`**, expressed as
`_WALMART_STORE_PATH = (*_WALMART_PRODUCT_PATH, "location", "storeIds")` so the
store and the offer cannot drift onto different subtrees in a later edit.

The rejected candidate is
`props.pageProps.initialData.data.contentLayout.pageMetadata.location.storeId`.
Both paths exist in both shipped fixtures and both currently read the same value.
It was rejected because it lives in a **page-layout metadata** subtree — a fact
about the chrome the page rendered, not about the offer. `product.location` sits
under the very node `nextdata_offers` already reads for availability, price and
seller, so the store, the price and the availability cannot come from different
places and disagree. If they ever do, taking the metadata one would attribute an
offer to a store that did not produce it. `tests/test_parse.py::
test_the_store_is_read_from_the_same_node_as_the_offer` pins it: a payload
carrying only the `contentLayout` store reads `None`.

**`storeIds` is accepted only as a list of exactly one `str`.** Empty,
multi-entry, or holding a non-string all return `None`; picking `[0]` out of a
two-entry list would be a guess about ordering that nothing measured. Both
shipped fixtures carry exactly one element (measured 2026-08-10).

**No `"0"` special case, and this is load-bearing.** `"0"` in the fixtures is
this repo's own redaction placeholder — `8dec2e0` wrote it over a real store
number throughout both captures, and it sits in `identity_check.py`'s `allowed`
vocabulary beside `"00000"` and `"XX"`. A `if store == "0": return None` branch
would be a claim about Walmart that nothing measured. `05-PATTERNS.md` inferred
exactly that ("very likely Walmart's 'no store assigned' sentinel") and it is
wrong; the tests, both fixture `.json` notes and `parse.py`'s own comment each
say so in prose. Verified: `grep -vn '^\s*#' boty/parse.py | grep -c 'store == "0"'` → `0`.

## The `${WALMART_STORE_ID}` decision — what 05-04's checkpoint asks Dan for

Decided in `boty/config.py::_store_id`'s docstring and in
`config/products.yaml`'s comment block, not left for 05-04 to discover:

- `config/products.yaml` ships `store_id: ${WALMART_STORE_ID}` on **both** Walmart
  watches — the GO Plus + product watch at the top and the milk control below it.
- The real value goes in the mode-600 `EnvironmentFile` the systemd unit already
  loads (`/home/dan/.config/boty/env`), outside this repo. **The value appears
  nowhere in this repo, this commit series or this summary.**
- `config.py`'s existing `_expand`/`_sub` runs over the whole document before any
  `Watch` is built, so the substitution mechanism already exists and an unset
  variable already logs its own name without failing the load.
- Rejected: a literal store number in the tracked file (the leak class itself);
  a second untracked overlay config (invents a mechanism where `${VAR}`
  substitution already exists and already argues this exact case).
- The property that makes it safe rather than merely convenient: unset → empty →
  unpinned → UNKNOWN, which is the behaviour REQ-14 asks for anyway.

So 05-04's checkpoint is: **set `WALMART_STORE_ID` in the daemon's
EnvironmentFile, then restart the service.** Nothing else.

## `make verify-offline` — verdict verbatim

```
identity check: PASS — 173 file(s), no host identity found
568 passed in 9.70s
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 8 mutation(s), sandboxed (the working tree is never touched)
  baseline  unmutated sandbox passes (568 passed in 9.69s)
  CAUGHT    M1 … M8
mutation check: 8/8 mutations caught
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

Exit **0**. Test count **568**, strictly above the 531 baseline (+37). Mutations
**8/8**, unchanged — this plan deliberately adds no mutation, because the store
changes no verdict and a mutation must break something a test asserts about a
verdict. `scripts/mutation_check.py` was not touched. The count rises in 05-02.

`mypy` clean (18 source files), `ruff check` clean.

**`make verify` (live) was NOT run**, per the plan's evidence constraint: it has
read `VERIFY: FAIL (live controls)`, exit 2, since 2026-08-06 for reasons this
phase did not cause; Walmart is challenge-blocked at HTTP 200; and the probing
budget is a hard politeness constraint. No acceptance criterion here depended on
a live read. The live verdict is 05-04's to record.

## Files Created/Modified

- `scripts/identity_check.py` — one new `keyed` entry: a store number in a YAML config key, with both residuals commented
- `boty/models.py` — `Watch.store_id`, `Result.store`, each declared last with its decision paragraph
- `boty/config.py` — `_store_id` beside `_price`; wired into the `Watch(...)` construction site
- `boty/parse.py` — `_WALMART_STORE_PATH` and `nextdata_store`
- `boty/retailers.py` — the store read once in `_verdict_from_html` and threaded onto all six returns; `store=None` stated on both `check_html` refusal arms
- `boty/status.py` — `store` and `store_pinned` in the watches block
- `boty/cli.py` — `_store_tag`, four forms, appended to `_report`'s tag list
- `served/boty/index.html` — `storeTag(w)`, `.tag.store` and `.tag.store.warn`
- `config/products.yaml` — `store_id: ${WALMART_STORE_ID}` on both Walmart watches, with the no-digits decision paragraph
- `tests/fixtures/walmart/{goplusplus,milk-control}.json` — provenance notes record the store redaction, naming the placeholder and never the removed value
- `tests/test_fetch.py` — the red-watch probe against the shipped script, plus both residuals
- `tests/test_identity_check.py` — `config/products.yaml` is in the guard's scope
- `tests/test_config.py` — six `Config.load` behaviours; both Walmart watches carry the pin
- `tests/test_models.py` — the two field defaults, and recording a store moves no verdict
- `tests/test_parse.py` — the fixtures, the whole non-Walmart corpus, every defensive shape, the same-node invariant
- `tests/test_retailers.py` — all six return paths, both refusal arms, the mismatch case, and a structural "does not branch on a store" gate
- `tests/test_status.py` — both keys, null-not-zero, all four `_report` tag forms
- `tests/test_dashboard.py` — both keys in `UNTRUSTED`, both visual weights

## Decisions Made

See `key-decisions` in the frontmatter. The three that will be reached for next:

1. **REQ-14 is deliberately NOT marked complete.** This plan delivers the
   *recording* half — the pin, the reading, the publication. Criterion 2's
   "unset means UNKNOWN with a health message saying so" is the *verdict* half
   and is 05-02's, and the outline's own traceability table records REQ-14 as
   closed by 05-02. Marking it here would be the false green 04-05 recorded for
   REQ-11 under the same reasoning.
2. **No mutation added**, and that is a decision rather than an omission — see
   the verdict section above and the plan's own `<mutation_note>`.
3. **The ROADMAP numbering typo at `ROADMAP.md:387-392` (`1, 0, 2, 3, 4, 5`) was
   left alone.** It is 05-04's to fix, flagged not silently corrected.

## Deviations from Plan

### 1. The tracked-file count is 173, not 168

- **Found during:** Task 1, at the very first baseline measurement.
- **Issue:** The plan asserts `identity check: PASS — 168 file(s)` as the
  baseline and as the done criterion. The tree reports **173**.
- **Cause:** Not a regression. Five `.planning/phases/05-a-reading-means-something/*.md`
  files (CONTEXT, PATTERNS, OUTLINE and the four plans, minus what was already
  counted) were committed at `3d99d58` *after* the plan's 2026-08-10 measurement
  was taken. `git ls-files` grew; nothing left the guard's scope.
- **Resolution:** Followed the tree, per the standing rule. The criterion is met
  in substance — `--all` PASSes over the **full** tracked tree with exit 0, and
  the widening cost **zero** hits on the existing corpus, which is what the 168
  figure was standing in for.

### 2. `tests/test_models.py` touched, though not in `files_modified`

- **Found during:** Task 2.
- **Issue:** The plan's Task 2 `<verify>` runs `pytest tests/test_models.py`, but
  the file is absent from `files_modified` and from the outline's contention table.
- **Resolution:** Three tests added there rather than misfiled into
  `tests/test_config.py`, because that module's subject is exactly the
  declared-last-with-a-default contract. Recorded above as finding 3.

### 3. `Watch.store_id` declared after `control`, not after `max_price`

- **Found during:** Task 2. Anticipated by the plan, which overrides the outline
  on this point; recorded because the outline still says "after `max_price`".
- **Reason:** `control` is the last field today. Inserting ahead of it changes
  the positional signature of a frozen dataclass, which is the exact thing the
  declared-last rule exists to prevent.

### 4. The sed-style patch of `_verdict_from_html`'s returns missed two

- **Found during:** Task 3, caught by the tests written first.
- **Issue:** Two of the six `return Result(...)` sites sit at a different
  indentation level and were not rewritten by the bulk edit, so the
  "no structured stock data found" UNKNOWN and the "none first-party"
  OUT_OF_STOCK were shipping `store=None`.
- **Fix:** Both patched by hand; a source-level count now asserts six returns and
  the behavioural test walks every one of them.
- **Verification:** `test_every_verdict_path_carries_the_store_including_the_unknowns`
  went red on each, then green.
- **Committed in:** `20cc32f`.

### 5. The identity guard rejected this plan's own first commit attempt

- **Found during:** Task 2. Documented in full under "The gate caught something
  real" above. Rule 1 fix: the literal was changed, not the guard.

---

**Total deviations:** 5 (2 stale-plan corrections, 2 table omissions, 1 Rule 1
bug caught by a gate). **Impact:** none on scope. No plan item was dropped,
simplified or deferred.

## Issues Encountered

None beyond the deviations above. Every gate this plan added was watched failing
before it was trusted.

## User Setup Required

**One setup step, and it is 05-04's checkpoint, not this plan's.** `boty` will
run unchanged today: with `WALMART_STORE_ID` unset, both Walmart watches load
unpinned and `status.json` publishes `"store_pinned": null` beside whatever store
answered. Nothing crashes and no verdict changes.

To pin: set `WALMART_STORE_ID` in the daemon's `EnvironmentFile`
(`/home/dan/.config/boty/env`, mode 600) and restart `boty.service`. **Do not put
the number in `config/products.yaml`** — the guard will now refuse the commit,
which is the point.

Note the standing warning in STATE.md: `boty.service` has been running
pre-Phase-4 code since 2026-08-04, and a restart currently resets every backoff
to zero. That is what 05-03 fixes, which is why 05-04's restart comes after it.

## Next Phase Readiness

05-02 has what it needs and nothing it does not:

- `Result.store` is populated on **every** `check_html` return path including
  both refusal arms, so a guard cannot fire on a fact that is not there.
- `Watch.store_id` is carried as **data** on the `Watch`, not only as a log line,
  because `assess_health` has to read it to say why a reading is UNKNOWN.
- `_verdict_from_html` does **not** branch on either, and
  `test_the_verdict_function_does_not_branch_on_a_store_at_all` will go red the
  moment 05-02 adds its guards — deliberately, so the change is visible in a diff.
- `tests/test_retailers.py::test_a_mismatched_store_is_recorded_and_still_not_a_verdict`
  is the test 05-02 must move, and it says so in its own docstring.
- The mutation count is 8/8 and expected to rise in 05-02, anchored on
  `Availability.UNKNOWN` rather than on message text.

No blockers. The live `make verify` failure and `QUESTIONS.md` § 0e both remain
open and are both pre-existing.

---
*Phase: 05-a-reading-means-something*
*Completed: 2026-08-10*

## Self-Check: PASSED

Every file named above exists on disk; all four task commits resolve in
`git log`. Load-bearing claims re-verified mechanically after writing this
summary: one `store number in a config key` rule in `scripts/identity_check.py`;
`store_id: ${WALMART_STORE_ID}` on exactly **2** lines of `config/products.yaml`
(98 and 131 — the product watch and the control); one `def nextdata_store`;
`"store_pinned"` in `boty/status.py`; three `w.store*` reads in
`served/boty/index.html`; and **6 of 6** `return Result(...)` sites in
`_verdict_from_html` carrying `store=store`.
