# Phase 6: Claims With Gates Under Them - Pattern Map

**Mapped:** 2026-08-10
**Files analysed:** 12 (5 criteria; every file measured, none guessed)
**Analogs found:** 10 / 12 — two criteria have **no analog** and are called out as such

Everything below was read out of the tree today. Where a thing does not exist, this file says
"does not exist" rather than nominating a near-miss.

---

## File Classification

| New/Modified file | Role | Data flow | Closest analog | Match |
|---|---|---|---|---|
| `boty/parse.py` (`Offer` gains a shipping field; `nextdata_offers` / `ldjson_offers` read it) | parser | transform | itself — `Offer.price` / `_as_float`, `parse.py:40-54,250-323` | exact (same function) |
| `boty/models.py` (`Result.alertable` measures the delivered total) | model | transform | itself — `alertable`'s `price is None` branch, `models.py:361-378` | exact (same property) |
| `boty/retailers.py` (`_verdict_from_html` carries shipping onto `Result`) | service | request-response | itself — the `store` thread-through, `retailers.py:200,289-397` | exact |
| `tests/test_models.py` (delivered-total cases) | test | — | `test_unpriced_in_stock_offer_does_not_pass_the_ceiling`, `test_models.py:80-92` | exact |
| `tests/test_parse.py` / `tests/test_retailers.py` (shipping extraction) | test | — | `_nextdata(**product)` / `_ldjson(**offer)` builders, `test_retailers.py:55-63` | exact |
| `tests/test_support_matrix.py` (Rung bound to code) | test/gate | transform | `_extraction_mismatch` + its two red-watch tests, `test_support_matrix.py:379-406`, `:709-736` | role-match — see the gap below |
| `tests/test_ci_workflow.py` (directory-wide workflow rules) | test/gate | file-I/O | `_pr_triggered_privilege` + `_all_workflow_texts`, `test_ci_workflow.py:423-445,534-539` | exact |
| `tests/test_changelog.py` **(new)** | test/gate | file-I/O | `tests/test_contributor_docs.py` whole-file idiom | exact |
| `tests/test_packaging_metadata.py` (version agreement) | test/gate | file-I/O | `_declared_floor` / `_mypy_python_version` cross-file rule, `test_ci_workflow.py:473-498` | role-match |
| `scripts/mutation_check.py` (new mutations) | gate registry | batch | `MUTATIONS` tuple, `mutation_check.py:174-189` | exact |
| `pyproject.toml` (`version = "0.2.0"`) | config | — | line 7 | exact |
| `CHANGELOG.md` (0.2.0 heading) | doc | — | existing `## [1.0.0] - 2026-08-05` heading | exact |

---

## Criterion 1 — delivered-total ceiling (REQ-17)

### The measurement that decides this criterion

I parsed both shipped Walmart fixtures' `__NEXT_DATA__` product node and GameStop's JSON-LD.
**Result: a numeric shipping cost is present for GameStop and absent for Walmart.**

`tests/fixtures/walmart/goplusplus.html` — the marketplace case this criterion exists for
(`sellerName: "Clove Brothers LLC"`, `priceInfo.currentPrice.price: 229.99`):

| Field (under `props.pageProps.initialData.data.product`) | Value |
|---|---|
| `shippingPrice` | `null` |
| `shippingCostType` | `null` |
| `shippingOption.shipPrice` | `null` |
| `priceInfo.shipPrice` | `null` |
| `topBoostedOffer.shippingCost` | `null` |
| `fulfillmentSummary[0].fulfillmentPrice` | `null` |
| `fulfillmentOptions[0].speedDetails.fulfillmentPrice` | `null` |
| `fulfillmentOptions[0].speedDetails.freeFulfillment` | `true` |
| `fulfillmentLabel[0].shippingText` | `"Free shipping"` (prose) |
| `priceInfo.additionalFees.shippingAndImportFee` | `{"price": 0, "priceString": "$0.00"}` |
| `priceInfo.additionalFees.estimatedTotalPrice` | present (`$2.42` on the milk fixture) |

`milk-control.html` (first-party, `sellerName: "Walmart.com"`, `sellerType: "INTERNAL"`) is
identical in shape: every numeric shipping field `null`, `additionalFees.shippingAndImportFee`
`$0.00`, and an `estimatedTotalPrice` equal to the item price.

`tests/fixtures/gamestop/goplusplus.html` JSON-LD, by contrast, carries a real number:

```json
"shippingDetails":{"@type":"OfferShippingDetails",
  "shippingRate":{"@type":"MonetaryAmount","value":"6.99","currency":"USD"}, ...}
```

**What this means for the planner, stated plainly:**

1. For **Walmart — the live exposure named in CONTEXT — a shipping cost is NOT present as a
   number in the captured corpus.** Free shipping is expressible (`freeFulfillment: true`,
   `shippingText: "Free shipping"`, `shippingAndImportFee.price == 0`); a *non-zero* shipping
   cost is **unrepresented in anything this repo has captured**. No fixture in the tree shows
   what Walmart emits for a paid-shipping marketplace offer. Any rule written for that case is
   written against an unobserved payload — which is exactly the thing this project forbids
   asserting. Say so in the plan; do not invent a field name.
2. Therefore **"unresolvable ⇒ UNKNOWN" is the common path on Walmart, not the rare one**,
   unless the plan chooses to treat an explicit zero/free signal as resolved-at-zero. That is a
   real decision with a measurable basis (`freeFulfillment` and `shippingAndImportFee.price` are
   both present and both agree on both fixtures), and it is the difference between a working
   Walmart watch and a permanently-UNKNOWN one.
3. `estimatedTotalPrice` exists under `priceInfo.additionalFees` on both Walmart fixtures and is
   the closest thing Walmart publishes to a delivered total — but on the marketplace fixture it
   was captured with free shipping, so it has never been observed *differing* from the item
   price. It is a candidate, not evidence.
4. **GameStop is where a delivered-total rule can be watched biting on real captured data**
   ($54.99 + $6.99 = $61.98 against an $80 ceiling; against a $60 ceiling it flips). That is the
   only retailer in the corpus with a non-zero shipping number.

### Where the code attaches

**`boty/parse.py:40-48` — the carrier to widen:**

```python
@dataclass(frozen=True)
class Offer:
    """One seller's offer for a product."""

    available: bool
    price: float | None
    seller: str | None
    raw_availability: str = ""
```

Note the house convention already used three times on `Result` (`rung`, `extraction`, `store`):
**a new field is declared last, with a default, so every existing construction site stays valid
and keeps its meaning** (`models.py:262-270,297-304`). A shipping field must follow it, and its
default has to mean "nobody read one", not "zero".

**`boty/parse.py:50-54` — the coercion to reuse, not re-write:**

```python
def _as_float(v: Any) -> float | None:
    try:
        return float(str(v).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None
```

**`boty/models.py:361-378` — the ceiling, and the exact reasoning to extend:**

```python
    @property
    def alertable(self) -> bool:
        """In stock, and cheap enough to be a real restock rather than a flip."""
        if self.availability is not Availability.IN_STOCK:
            return False
        if self.watch.max_price is None:
            return True
        # A ceiling was configured and the price could not be read. "I could
        # not tell" must not resolve to "cheap enough" ...
        if self.price is None:
            return False
        return self.price <= self.watch.max_price
```

The `price is None → False` branch is the precise template for "shipping unresolved → not
alertable". **Note the constraint interaction:** criterion 1's wording is "an unresolvable
shipping cost is UNKNOWN, not a pass". `alertable` returns a bool and cannot say UNKNOWN;
`Availability` is set in `retailers._verdict_from_html` (`retailers.py:387-397`). Whether UNKNOWN
means *availability* UNKNOWN or *not alertable* is a decision the plan must make explicitly —
`models.alertable` and `retailers._verdict_from_html` are two different places with two different
vocabularies, and the standing rule "UNKNOWN is never a verdict and never OUT_OF_STOCK" bears on
the choice.

**`boty/retailers.py:387-397` — the single place an `Offer` becomes a `Result`:**

```python
    state = Availability.IN_STOCK if offer.available else Availability.OUT_OF_STOCK
    seller = offer.seller or "first-party"
    return Result(
        watch,
        state,
        price=offer.price,
        detail=f"{source}: {offer.raw_availability} from {seller}",
        url=url,
        rung=rung,
        extraction=extraction,
        store=store,
    )
```

The `store` field's thread-through is the pattern for a new field: read once
(`retailers.py:200`), carried onto **every** return including the UNKNOWNs, because "error paths
carry the same metadata as success paths" is committed to in four adapter docstrings.

**Phase 1's existing ceiling test (the one CONTEXT points at), `tests/test_models.py:80-92`:**

```python
def test_unpriced_in_stock_offer_does_not_pass_the_ceiling() -> None:
    """A ceiling that cannot be evaluated must not authorise an alert. ..."""
    assert _result(Availability.IN_STOCK, price=None, max_price=80).alertable is False
```

and `tests/test_retailers.py:70-93` for the fixture-driven side, with `_serve` monkeypatching
`retailers.get` and the synthetic builders at `test_retailers.py:55-63`:

```python
def _nextdata(**product: object) -> str:
    """A minimal Walmart hydration payload, shaped like the real fixture."""
    doc = {"props": {"pageProps": {"initialData": {"data": {"product": product}}}}}
    return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(doc)}</script></html>'
```

`_nextdata` is how a *hypothetical* paid-shipping Walmart payload can be exercised without
claiming it is what Walmart emits — a synthetic stand-in, labelled as one, in the idiom
`PUBLISH_WORKFLOW` used in `test_ci_workflow.py:127`.

**Existing mutation to mirror — M4, `mutation_check.py:218-223`:**

```python
    Mutation(
        ident="M4",
        target="boty/models.py",
        search="        if self.price is None:\n            return False\n        return self.price <= self.watch.max_price",
        replace="        if self.price is None:\n            return True\n        return self.price <= self.watch.max_price",
        ...
```

Any edit to `alertable` **will break M4's `search` anchor**. That is a required, deliberate edit
in the same commit, not a surprise.

---

## Criterion 2 — Rung bound to the README (REQ-18)

### The analog to copy: `_extraction_mismatch`

`tests/test_support_matrix.py:379-406`, verbatim:

```python
def _extraction_mismatch(rows: dict[str, list[str]]) -> dict[str, tuple[str, str]]:
    """Rows whose Extraction cell and Rung cell disagree about whether anything is read.

    DELIBERATELY TWO-DIRECTIONAL ... One-directional would be worthless.
    """
    bad: dict[str, tuple[str, str]] = {}
    for name in ROADMAP_RETAILERS.values():
        if name not in rows:
            continue
        rung, extraction = rows[name][RUNG], rows[name][EXTRACTION]
        working = rung[:1] in WORKING_RUNGS
        if (working and extraction not in EXTRACTIONS) or (
            not working and extraction != NO_EXTRACTION
        ):
            bad[name] = (rung, extraction)
    return bad
```

How it locates the table — `test_support_matrix.py:200-219`:

```python
def _cells(line: str) -> list[str]:
    """The pipe-delimited cells of one markdown table row."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]

def _matrix(readme_text: str | None = None) -> dict[str, list[str]]:
    text = README.read_text(encoding="utf-8") if readme_text is None else readme_text
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines)
                  if line.startswith("|") and tuple(_cells(line)) == HEADER_CELLS), None)
    assert start is not None, ...
```

`HEADER_CELLS = ("Retailer", "Rung", "Extraction", "robots.txt", "Terms", "Method", "Status")`
(line 63) is asserted literally by `test_the_matrix_header_is_exactly_the_seven_cells` so a
column cannot move silently. `readme_text: str | None = None` is the key signature convention:
**every rule is a pure function of text**, so the same function runs against the shipped README
and against a corrupted copy built by `_corrupt` (`:632-645`), which derives the broken case from
the real file rather than typing one out. Red-watch tests live in the block from `:709` on
(`test_a_rung_four_row_claiming_an_extraction_fails`,
`test_a_working_rung_row_disclaiming_an_extraction_fails` — one per direction).

### The gap this criterion actually names — and it is real

**`_extraction_mismatch` binds the README's Extraction cell to the README's Rung cell. Neither is
bound to code.** I grepped: no test in `tests/` compares a README cell to a `Rung` member or to
`boty/retailers.py`. CONTEXT's phrasing "binds Routing and Extraction to the code in both
directions" is not what the file does — both directions are *within the table*. The planner is
building the code-side half from scratch. That is the honest finding.

### How each adapter's Rung is discoverable from code — measured

There is **no registry**. It is deliberate (`cli.py:42-48`: "there is no registry to fall out of
sync with it"). Two facts have to be joined:

1. **Routing** — retailer string → adapter function, a chain of `if`s inside a closure,
   `boty/cli.py:65-84`:

```python
    def check(watch: Watch) -> Result:
        if watch.retailer == "bestbuy":
            if cfg.bestbuy_api_key:
                return check_bestbuy_api(watch, cfg.bestbuy_api_key)
            return check_bestbuy_browser(watch, first_party_only=cfg.first_party_only)
        if watch.retailer == "amazon":
            return check_amazon(watch, first_party_only=cfg.first_party_only)
        if watch.retailer == "target":
            return check_target_browser(watch, first_party_only=cfg.first_party_only)
        return check_html(watch, first_party_only=cfg.first_party_only)
```

2. **Rung** — a keyword argument at every `Result(...)` / `_verdict_from_html(...)` call site
   inside each adapter, never a return value and never a module constant. Measured occurrences
   in `boty/retailers.py`: `check_html` → `rung=Rung.TLS` (:419); `check_amazon` → `Rung.TLS`
   (:463,:472,:481 — plus `extraction=Extraction.DOM` on every path); `check_bestbuy_browser` →
   `Rung.BROWSER` (:588,:597,:606); `check_target_browser` → `Rung.BROWSER`
   (:697,:707,:717); `check_bestbuy_api` → `Rung.API` (:782,:791,:801,:812). `Result.rung`
   defaults to `Rung.TLS` (`models.py:265`).

**Consequences the planner must choose between (both viable, neither free):**

- **Dynamic binding** — drive each adapter against its fixture with `retailers.get`
  monkeypatched (`test_retailers.py:38-45`) and read `result.rung`. Real, end-to-end, and
  mutation-visible. Costs: Best Buy/Target/Amazon go through browser adapters, and the config
  choice (`bestbuy_api_key`) changes the rung — which is precisely why the README cell reads
  `3 (2 with a key)`. Any rule must handle that cell, whose first character is `3`;
  `WORKING_RUNGS` membership already uses `rung[:1]`, so the same `[:1]` convention applies.
- **Static binding** — AST-walk `boty/retailers.py` for `rung=Rung.X` per function plus
  `boty/cli.py` for the routing `if`s. `test_ci_workflow.py` already imports `ast`
  (`:66`, used by `test_no_rule_function_in_this_file_reads_a_file` at `:668`), so AST-over-repo
  is an established idiom here. Costs: it asserts what the source says, not what runs.

Whichever is chosen, the mutation named by the criterion is a Phase-5-style behaviour anchor:
`search="rung=Rung.TLS"` inside `check_amazon` → `replace="rung=Rung.BROWSER"`. Registration
pattern, `mutation_check.py:174-189`:

```python
@dataclass(frozen=True)
class Mutation:
    ident: str
    target: str
    search: str
    replace: str
    breaks: str

MUTATIONS = (
    Mutation(
        ident="M1",
        target="boty/parse.py",
        search='raw.rsplit("/", 1)[-1] in BUYABLE',
        replace='raw.rsplit("/", 1)[-1] not in BUYABLE',
        breaks="inverts every offer's availability — in-stock reads as out-of-stock and back",
```

**Count measured today: 16 mutations** (`M1`..`M16`), matching CONTEXT. New ones continue at
`M17`. Anchors in the existing set are all behavioural expressions or control-flow lines — none
anchors on message prose. Note `mutation_check.SANDBOX_CONTENTS` (`:125-128`) already includes
`.github`, `docs`, `config` and `Makefile`, so a gate reading any of those runs inside the
sandbox; `.planning/` and `CHANGELOG.md` are **not** in `SANDBOX_CONTENTS`. A new gate that reads
`CHANGELOG.md` will raise `HarnessError` under mutation unless `CHANGELOG.md` is added there —
the comment at `:120-124` documents exactly that failure and the fix.

---

## Criterion 3 — workflow-file rules keyed to the directory (REQ-19a)

`.github/workflows/` currently holds **two** files: `ci.yml` and `release.yml`.

**The directory reader already exists** — `test_ci_workflow.py:534-539`:

```python
def _all_workflow_texts() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(WORKFLOWS.iterdir())
        if path.suffix in (".yml", ".yaml")
    }
```

**But only three tests use it** — measured: `test_no_workflow_in_this_repo_lets_a_pull_request_reach_privilege`
(`:584`), `test_no_workflow_in_this_directory_uploads_from_a_run_block` (`:1103`), and the
red-watch pair at `:901`/`:930`. Its rule function says so itself, `:423-431`:

```python
def _pr_triggered_privilege(workflows: dict[str, str]) -> list[str]:
    """Every workflow a pull request can trigger that also holds real privilege.

    The only rule here that looks beyond `ci.yml`, and the one that will still be
    doing work in a year. ...
    """
```

Everything the criterion names is keyed to a hardcoded path — `CI = WORKFLOWS / "ci.yml"` (`:73`)
and `RELEASE = WORKFLOWS / "release.yml"` (`:962`):

| Rule | Function | Currently reads |
|---|---|---|
| pin | `_action_pins` (:344) / `_unpinned_actions` (:361) | `_raw()` = `ci.yml`; duplicated for `RELEASE` at :1070 |
| exit-code | `_flattened_exit_codes`, tests at :600 / :1082 | `ci.yml`, then `release.yml` separately |
| timeout | inline in `test_the_job_is_time_limited_and_runs_on_a_pinned_image` (:632-637) and `:1086-1091` | one file each |
| runner | `_floating_runners` (:414-420) | `_jobs(wf)` of one parsed file |

So the shape of the fix is already demonstrated by `_pr_triggered_privilege`: **take
`dict[str, str]` of name→text (or iterate `_all_workflow_texts()` at the test), return
`list[str]` of findings prefixed with the filename**, and keep the per-file tests as the
specific cases. The timeout rule at `:1086-1091` is the closest existing loop-over-jobs form:

```python
        timeout = (job or {}).get("timeout-minutes")
        assert isinstance(timeout, int) and 0 < timeout <= 30, f"{name}: timeout-minutes={timeout!r}"
```

Two documented traps the rules already encode and a directory-wide version must keep: a bare
`on:` key parses as boolean `True` (hence `_triggers` looking up both spellings), and unquoted
`python-version: 3.10` parses as float `3.1`. Both are in the module docstring at `:34-46`.

Red-watch material for "a newly added workflow file is covered": `PUBLISH_WORKFLOW`
(`:127`) is the established synthetic-workflow-as-string stand-in, fed to a rule as
`{"release.yml": PUBLISH_WORKFLOW}` (`:930`). A third, deliberately non-compliant, synthetic
file is the natural red-watch.

---

## Criterion 4 — CHANGELOG gated on contents (REQ-19b)

### What exists today

`scripts/release_check.py:169`:

```python
SDIST_REQUIRED = ("CHANGELOG.md", "README.md", "MANIFEST.in", "pyproject.toml")
```
used only as `missing += [f"sdist:{n}" for n in SDIST_REQUIRED if n not in sdist_files]` (`:502`)
— membership in a built artifact's file list. And `:221-228`:

```python
def _changelog_version(changelog_text: str) -> str | None:
    """The version in the first ``## [x.y.z]`` heading that is not Unreleased."""
```

That is the whole of it. Nothing reads the body. `release_check.py` also **needs the network**
(`Makefile:45-47`, `:97-98`: it is deliberately not part of `verify`), so a contents gate placed
there would never run in `verify-offline`. **A new `tests/test_changelog.py` is the right home;
`release_check.py` is not.** That is a real finding, not a preference.

Why contents matter to a stranger, measured: `MANIFEST.in:39` `include CHANGELOG.md` puts it in
the sdist, and `pyproject.toml:179` `[project.urls] Changelog` points every installer at it. The
CHANGELOG's own preamble makes the claim this criterion has to back:

> `pyproject.toml` states the version; `scripts/release_check.py` binds this file's top heading
> to it, so the two cannot drift.

### The leaked-markup sweep — measured, in full

`git grep` over the tracked tree for `</invoke>`, `</content>`, `<function_calls>`,
`<parameter>` and `antml:` outside code fences returns **five hits in three files, all in
`.planning/`, and every one of them is a deliberate quotation**:

| File | Line | What it is |
|---|---|---|
| `.planning/phases/04-open-source-ready/04-REVIEW.md` | 113, 114 | inside a fenced block quoting the original defect |
| `.planning/phases/04-open-source-ready/04-REVIEW.md` | 118 | inline-code quotation of the byte sequence |
| `.planning/phases/06-claims-with-gates-under-them/06-CONTEXT.md` | 132 | inline-code quotation (`` `</content>`/`</invoke>` ``) |
| `.planning/seeds/nothing-reads-the-changelog-body.md` | 15, 16 | indented code block quoting the defect |

**`CHANGELOG.md`, `README.md`, `boty/`, `scripts/`, `tests/`, `docs/` and `.github/` are all
clean.** The 2026-08-07 fix (`2ac965f`) held.

The implication for rule design is concrete and load-bearing: **a naive `^</[a-z:]+>$` rule run
over `.planning/` goes red on three files that are describing the defect.** This is the exact
self-invalidating-gate problem `test_contributor_docs.py` already names in its docstring
(":29-31" — "A gate that invalidates itself to make a point is worse than no gate"). Two escapes
already exist in this repo for it and either can be copied:

- **fence/quote awareness** — `_documented_ci_target` (`test_ci_workflow.py:509-522`) tracks
  ```` ``` ```` fences line by line; `test_ci_workflow.py`'s `_code` vs `_raw` split
  (docstring `:19-32`) is the same idea for YAML comments, and its
  `test_the_shipped_comments_name_the_constructs_the_rules_forbid` (`:650`) asserts *both*
  directions — the documentation names the forbidden thing and the rule stays quiet.
- **enumerated exemption** — `identity_check._PROBE_FILES` / `_PROBE_DIR_PREFIXES`
  (`scripts/identity_check.py:427-434`):

```python
_PROBE_FILES = frozenset({
    "tests/test_fetch.py",
})
_PROBE_DIR_PREFIXES = (".planning/phases/",)

def _is_probe_file(rel: str) -> bool:
    return rel in _PROBE_FILES or rel.startswith(_PROBE_DIR_PREFIXES)
```

Scope note: if the gate is scoped to `CHANGELOG.md` (the file the criterion is about), none of
this bites. If it is widened to the tracked tree, it does.

### The rule-file idiom to copy

`tests/test_contributor_docs.py` is the closest whole-file analog — same subject (a shipped
markdown document), same structure. Its docstring states the contract the new file should
restate (`:32-42`):

> Each rule is a pure function of the document's text, returning a list of problems rather than
> asserting anything, so the corruption tests at the bottom run the *same* rule against a
> deliberately broken copy of the real file. From `tests/test_support_matrix.py`: a gate asserted
> only against the tree it is meant to guard has never been watched failing, and this project has
> already shipped one of those.

The seed `.planning/seeds/nothing-reads-the-changelog-body.md` already lists four candidate
rules (leaked-markup shapes, every `## [x.y.z]` parses and the top one equals pyproject's, no
unreplaced placeholder, ends with a newline). It is a seed, not a decision.

---

## Criterion 5 — version agreement (REQ-20)

### Every place the project states its own version — measured

| Place | Value today | Read by anything offline? |
|---|---|---|
| `pyproject.toml:7` `version = "1.0.0"` | `1.0.0` | **No.** `tests/test_packaging_metadata.py` never reads `version` (grepped) |
| `CHANGELOG.md` first non-Unreleased heading `## [1.0.0] - 2026-08-05` | `1.0.0` | only by `release_check._changelog_version`, network-bound |
| `.planning/STATE.md` frontmatter `milestone: v0.2` | `v0.2` | nothing |
| `boty/__init__.py` | **empty file, 0 lines — there is no `__version__`** | — |
| wheel filename / wheel METADATA / `pip show` | derived at build | `release_check.py`, network-bound |

**No offline gate reads the package version at all.** There is no analog for "version agreement
in `make verify-offline`" — the planner is building it. The nearest existing patterns:

**1. The five-way comparison, `release_check.py:464-477` (network-bound, so a template not a home):**

```python
    statements = {
        "pyproject.toml": declared,
        "CHANGELOG.md": changelog_version,
        "wheel filename": wheel_name_version,
        "wheel METADATA": metadata_version,
        "pip show": shown,
    }
    disagree = {k: v for k, v in statements.items() if v != declared}
    _report(results, "one version, stated five times", not disagree, ...)
```

**2. The offline cross-file agreement rule to copy — `test_ci_workflow.py:473-498`**, which binds
three statements of the Python floor (`requires-python`, `[tool.mypy] python_version`, the
workflow's `python-version`) using a borrowed parser rather than a second one:

```python
def _declared_floor(pyproject_text: str) -> str | None:
    """The minimum Python `requires-python` declares, e.g. `"3.10"`."""
    spec = PACKAGING._string(PACKAGING._project_table(pyproject_text).get("requires-python"))
    ...
```

The borrowing itself is the pattern (`:453-467`), and the reason is stated there: **"two readers
of one `pyproject.toml` drift"**. `tests/test_packaging_metadata.py` owns `_project_table`,
`_string` and `_strip_comment`; a version rule must use them, and must not import `tomllib`
(Python 3.11+, above the declared 3.10 floor — `test_this_file_does_not_import_tomllib`, `:685`,
enforces this for `test_ci_workflow.py` and the reasoning transfers verbatim).

**3. Reading `.planning/STATE.md` frontmatter has no precedent in `tests/`.** Nothing under
`tests/` or `scripts/` reads `.planning/` today, and `.planning/` is **not** in
`mutation_check.SANDBOX_CONTENTS` (`:125-128`) — a gate that reads it will fail under
`make mutation` with a `HarnessError`. Either add it to `SANDBOX_CONTENTS` (the comment at
`:120-124` documents that exact sequencing, "this line and .github/workflows/ci.yml landed in the
same commit") or bind `pyproject.toml` to `CHANGELOG.md`'s top heading, which is entirely inside
the shipped tree. The second is cheaper and covers "cannot silently diverge" for the two
statements a stranger actually sees; it does **not** cover STATE.md's `milestone: v0.2`. That is
a real trade-off for the plan to make explicitly rather than discover.

Also note `pyproject.toml:73-74` already carries a comment reasoning about the version being
`0.1.0` at the time — worth reading before the roll so the comment does not become stale prose.

---

## Shared Patterns

### The house gate idiom (applies to every gate in this phase)

**Source:** `tests/test_support_matrix.py`, `tests/test_ci_workflow.py`,
`tests/test_contributor_docs.py` — all three state it in their docstrings.

1. Rules are **pure functions of text**, signature `def _rule(text: str | None = None) -> list |
   dict`, returning findings rather than asserting.
2. The shipped file is asserted against the rule.
3. **The same function is run against a deliberately corrupted copy of the real file**, derived
   by a `_corrupt`-style helper, so the rule is watched going red.
4. Two-directional wherever a rule could be satisfied by blanking everything
   (`_extraction_mismatch`'s docstring: "One-directional would be worthless").
5. Constants that are **pins, not rules** (`UNREAD_POSITIONS`, `TRUSTED_ACTION_OWNERS`) are
   enumerated with the justification inline, so widening them means editing a red test.

`_corrupt` — `test_support_matrix.py:632-645`:

```python
def _corrupt(retailer: str, column: int, value: str) -> str:
    """The real README with one cell of one retailer's row replaced."""
    return _corrupt_text(README.read_text(encoding="utf-8"), retailer, column, value)
```

### Importing a `scripts/` module from a test

**Source:** `test_support_matrix.py:151-162`, reused at `test_ci_workflow.py:453-467`,
originally `test_control_check.py`.

```python
    spec = importlib.util.spec_from_file_location(
        "evidence_check_for_matrix", REPO_ROOT / "scripts" / "evidence_check.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

### Adding a field to a frozen dataclass

**Source:** `boty/models.py:262-270, 297-304` (`rung`, `extraction`, `store`). Declared **last**,
with a default, and the docstring must state **what the default MEANS** — for `store`, "the page
did not tell us", explicitly never "store 0". A shipping field needs the same paragraph.

### Mutation registration

**Source:** `scripts/mutation_check.py:174-189`. 16 mutations today. Anchor on behaviour
(a control-flow line, an expression), never on message prose — Phase 5's lesson, visible in every
existing `search`. `SANDBOX_CONTENTS` (`:125-128`) must contain every file a new gate reads, and
`_IGNORE` (`:158-160`) plus the note at `:130-150` explains the one file the copy loop brings in
that the repo does not track.

### Test-suite network guard

**Source:** `tests/conftest.py:26-40`. `NetworkBlocked` derives from `BaseException` on purpose —
an `Exception` guard is swallowed by `boty.fetch` and downgraded into `Availability.UNKNOWN`,
which is the most common assertion in the suite. Any new adapter-driving test inherits this via
the autouse fixture and must monkeypatch `retailers.get` (`test_retailers.py:38-45`).

### `make verify` composition

**Source:** `Makefile:156-182`. Ordered stages, each `|| { echo "VERIFY: FAIL (<stage>)"; exit 1; }`:

```make
verify:
	@$(MAKE_Q) identity || { echo "VERIFY: FAIL (host identity in a tracked file)"; exit 1; }
	@$(MAKE_Q) lint     || { echo "VERIFY: FAIL (lint)"; exit 1; }
	@$(MAKE_Q) test     || { echo "VERIFY: FAIL (tests)"; exit 1; }
	@$(MAKE_Q) types    || { echo "VERIFY: FAIL (types)"; exit 1; }
	@$(MAKE_Q) fixtures || { echo "VERIFY: FAIL (fixtures)"; exit 1; }
...
verify-offline:
	@$(MAKE_Q) verify CONTROL_FLAGS=--offline
```

New gates that are pytest tests need **no Makefile change** — they arrive through `test`. A gate
that is a new script does, and `release-check` (`:97-98`) is deliberately outside `verify`
because it needs the network.

---

## No Analog Found

| File / thing | Role | Data flow | Reason |
|---|---|---|---|
| A README-cell → **code** binding of any kind | test/gate | transform | Measured: no test in `tests/` compares a matrix cell to a `Rung` member or to `boty/retailers.py`. `_extraction_mismatch` binds cell-to-cell. Criterion 2's code-side half is new construction. |
| An **offline** gate over the package version | test/gate | file-I/O | `tests/test_packaging_metadata.py` never reads `[project] version`; the only version cross-check is `release_check.py`'s, which needs the network and is excluded from `verify`. |
| Anything reading `.planning/` from `tests/` or `scripts/` | test/gate | file-I/O | No precedent, and `.planning/` is absent from `mutation_check.SANDBOX_CONTENTS`. |
| A Walmart payload carrying a **non-zero** shipping cost | fixture | — | Not in the corpus. Both Walmart fixtures have every numeric shipping field `null` and free shipping. Any rule for paid Walmart shipping is written against an unobserved payload. |
| `boty/__init__.py` `__version__` | model/config | — | The file is empty. There is no runtime version constant to bind to. |

---

## Metadata

**Analog search scope:** `boty/`, `scripts/`, `tests/`, `tests/fixtures/`, `.github/workflows/`,
`Makefile`, `pyproject.toml`, `MANIFEST.in`, `CHANGELOG.md`, `README.md`, `.planning/`
**Files scanned:** 24 source/test files read or grepped; 4 HTML fixtures parsed as JSON
**Measurements run:** `__NEXT_DATA__` product-node walk over both Walmart fixtures; JSON-LD
shipping read over GameStop; `git grep` leaked-markup sweep over the tracked tree; mutation count
(`ident="M` → 16); workflow-directory listing (2 files)
**Pattern extraction date:** 2026-08-10
