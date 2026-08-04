# Phase 4: Open Source Ready - Pattern Map

**Mapped:** 2026-08-04
**Files analyzed:** 8 (5 new, 3 modified)
**Analogs found:** 6 / 8 (2 have no in-repo analog — CI workflow, LICENSE)

## File Classification

| New/Modified File | New? | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|---|
| `docs/adding-a-retailer.md` | new | contributor doc | narrative / worked example | `docs/retailer-evidence.md` | exact (same dir, same voice, same author-of-record conventions) |
| `.github/workflows/ci.yml` | new | CI config | batch / gate | `Makefile` (`verify-offline`) + `hooks/pre-commit` | role-mismatch — no workflow exists; the *contract* analog is the Makefile |
| `pyproject.toml` | modified | packaging config | config | itself (in-place edit; comment conventions are the analog) | exact |
| `README.md` | modified | doc | narrative + machine-read table | itself §"Retailer status" + §"Verifying it works" | exact |
| `LICENSE` | new | legal | — | none in repo | **no analog — and it is currently missing entirely** |
| `CONTRIBUTING.md` | new (optional) | contributor doc | narrative | `README.md` §"Verifying it works" (lines 346–381) | role-match |
| `Makefile` | modified (only if a `lint` stage is added) | build config | batch | itself (`types` target + `verify` trap chain) | exact |
| `tests/test_verify_makefile.py` | modified (only if `verify` gains a stage) | test | subprocess | itself | exact |

---

## Pattern Assignments

### `docs/adding-a-retailer.md` (contributor doc, worked example)

**Analog:** `docs/retailer-evidence.md` — the only file in `docs/`. Copy its conventions exactly; a second doc in the same directory written in a different register reads as a different project.

**Conventions to copy** (`docs/retailer-evidence.md:1-13`):

```markdown
# Retailer evidence log

What was actually tried against each retailer, and what actually came back.

`.planning/ROADMAP.md` defines an escalation ladder — rung 1 impersonated HTTP,
rung 2 a documented API, rung 3 a real browser, rung 4 "drop, with evidence".
This file is where that evidence lives. It exists because "we tried and it did
not work" is a claim, not a finding: ...
```

1. **Title, then a one-line statement of what the file is, then a "It exists because…" paragraph.** Every doc here justifies its own existence before it instructs.
2. **Dated headings for anything that changed** — `### 2026-08-03, 03.1-03 — the request Phase 3 never made` (line 121).
3. **Retraction, never overwrite.** `retailer-evidence.md:87-96` and `:645-651` are the canonical shape: the superseded text is quoted, dated, and labelled *historical*, and the new finding sits beside it. If this new doc later contradicts itself, it must do the same.
4. **Bold verdict/claim lines carry the measurement**, not the conclusion (`:216-219`, `:372`).
5. **Tables for observations**, prose for reasoning (`:210-214`).
6. **Cross-reference by file:line**, e.g. `:798` cites `boty/models.py:73-75`.

**Which shipped retailer is the worked example — use Nintendo as the spine, GameStop as the fallback contrast.**

Nintendo is the best worked example, and the evidence log already says why (`docs/retailer-evidence.md:964-971`):

> Nintendo's store is the cheapest retailer in this repo to support. It needs **no
> new adapter code at all** — no extractor, no `_make_checker` branch, no
> `MARKETPLACES` entry. `check_html` reads it as shipped; the only change is one
> `FIRST_PARTY` line and two YAML watches. `02-PATTERNS.md` §1 predicted exactly
> this, and it is worth stating plainly because the instinct on adding a retailer
> is to write a class.

That is the whole lesson the doc should teach first: **the default answer is "no adapter"**. The Nintendo path is exactly four edits, all of which exist in the tree and can be cited:

| Step | Where | Citation |
|---|---|---|
| 1. Probe and write the evidence | `docs/retailer-evidence.md` § Nintendo | `:958-979` |
| 2. One `FIRST_PARTY` entry | `boty/retailers.py:28` | `FIRST_PARTY` dict |
| 3. Decide `MARKETPLACES` membership — and the *absence* is a claim | `boty/retailers.py:88-94` | quoted below |
| 4. Two YAML watches, one of them a control | `config/products.yaml:51-70` | control rule at `:45-51` |

`boty/retailers.py:88-94` is the single best excerpt in the codebase for the doc's "a blank is a claim" point:

```python
#: `nintendo` is deliberately absent, and that absence is a claim backed by
#: evidence rather than an oversight: Nintendo's store has no third-party seller
#: surface at all — no buy box, no "other sellers", nobody but Nintendo of
#: America who can list on it. Adding it here "to be safe" would be the opposite
#: of safe, because it would strip `_pick`'s unattributed-offer fallback and turn
#: any future page that drops the seller node into a permanent UNKNOWN.
MARKETPLACES = {"walmart", "target", "amazon", "bestbuy"}
```

**When a new adapter IS needed**, the dispatch point is one function with one `if` and the doc must say so — there is no plugin registry, deliberately (`boty/cli.py:40-85`):

```python
def _make_checker(cfg: Config) -> Callable[[Watch], Result]:
    """The one place a watch is matched to a transport.

    `scripts/control_check.py` deliberately builds its checker with this same
    function rather than its own: a gate that routed requests differently from
    the running monitor would prove something about a code path nobody runs.
    So this stays one function with one `if`, and there is no registry to fall
    out of sync with it.
    """
```

Amazon (`boty/retailers.py:286`, `check_amazon`) is the best *second* example — the case where `check_html` reads the page fine and says UNKNOWN forever, so a DOM reader is needed (`boty/cli.py:69-76`). Best Buy (`:416`, `:561`) is the two-rung/credential-optional example. Target (`:482`) is the single-rung example.

**Why a control product is mandatory (REQ-09's explicit ask)** — the argument is already written in two places; the doc should quote rather than re-derive:

- `README.md:30-40` — "I don't know" is not "out of stock", and the control is what makes silence detectable.
- `config/products.yaml:45-51` — the control *rule*: first-party, evergreen, restocked routinely, never a buy-box fight, not a console.
- `docs/retailer-evidence.md:183-200` — a control candidate being **rejected** and the rejection recorded (`B014I8SIJY`, "Only 2 left in stock"). Best concrete illustration of the rule biting.
- `scripts/control_check.py` exit codes: 0 pass, 3 SKIPPED (offline), 4 INCOMPLETE (this host cannot run some controls). The doc must not describe controls as pass/fail — the exit-code table is at `README.md:360-365`.

**The UNKNOWN contract** — cite `boty/parse.py` / `docs/retailer-evidence.md:669-673`:

> `parse.add_to_cart_offers` therefore returns `None` (UNKNOWN) when the control is absent and will never say OUT_OF_STOCK on Amazon's word from an absence. That is a gap, recorded as one.

Also cite the seller-default trap, which is the most dangerous thing a new adapter author can get wrong (`docs/retailer-evidence.md:427-432`): Target treats *absence* of a seller block as first-party; Amazon must not, and `test_an_amazon_offer_with_no_seller_recorded_is_unknown_not_a_verdict` pins it.

**What the doc must also require of a contributor, because gates already enforce it:**
- an evidence-log section with a verdict line in one of the three exact forms (`docs/retailer-evidence.md:15-21`) — `scripts/evidence_check.py` fails `make verify` otherwise;
- a README matrix row that passes `tests/test_support_matrix.py` (see coupling below);
- fixtures redacted **by class, not by value** (`docs/retailer-evidence.md:434-455`), and `make hooks` installed.

---

### `.github/workflows/ci.yml` (CI config, gate)

**No analog exists** — there is no `.github/` directory. The behavioural analog is the `Makefile`, and CI must delegate to it rather than re-listing checks; the Makefile header states why (`Makefile:1-12`):

```make
# `make verify` is the contract. Every phase of this project states its success
# criteria in terms of it, so it has exactly one job: exit non-zero if ANY check
# fails. A verify that prints FAIL and exits 0 is worse than no verify at all,
# because everything downstream is built on trusting the number.
```

**Which targets are network-free vs live — definitive:**

| Target | Network? | CI-safe |
|---|---|---|
| `identity` (`scripts/identity_check.py --all`) | none — reads tracked files via git | **yes, and required** |
| `test` (`pytest tests/ -q`) | none — the suite asserts its own isolation | yes |
| `types` (`mypy`, files = `boty`, `scripts`) | none | yes |
| `fixtures` (`control_check.py --fixtures`) | none — staleness/label warnings only, **never fails** | yes |
| `controls` (`control_check.py`) | **LIVE retailer requests** | **no** |
| `mutation` (`scripts/mutation_check.py`) | none — corrupts a copy and re-runs the suite | yes |
| `hooks` | none, but writes `.git/hooks` | not for CI |
| `verify` | includes live `controls` | **no** |
| `verify-offline` | passes `CONTROL_FLAGS=--offline` | **yes — this is the CI entry point** |

**`make verify-offline` confirmed** (`Makefile`, last two rules):

```make
verify-offline:
	@$(MAKE_Q) verify CONTROL_FLAGS=--offline
```

It delegates to `verify` with `CONTROL_FLAGS=--offline`, so `control_check.py` prints `control check: SKIPPED (--offline) — no live retailer request made.` (`scripts/control_check.py:375-376`) and exits 3. `verify` maps rc 3 to `verdict=offline` and prints `VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)` with exit 0. `tests/test_verify_makefile.py:128 test_verify_offline_propagates_the_offline_flag` already pins the flag reaching the script.

**Two hard requirements for the workflow:**

1. **`PYTHON`.** Every target depends on `check-venv`, which hard-fails unless `.venv/bin/python` is executable (`Makefile`, `check-venv`). CI must either create `.venv` (`python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'` — the exact line the error message prints) or invoke `make PYTHON=$(command -v python) verify-offline`. Prefer the venv: it is the documented path in `README.md:253-258` and keeps CI and a fresh clone identical.
2. **Do NOT install `.[browser]`.** `nodriver` is AGPL-3.0 against this MIT project and must stay opt-in (`pyproject.toml:32-49`). Its absence is also *already handled*: exit 4 / `PASS (INCOMPLETE)` exists precisely for the fresh-clone-without-Chrome case (`Makefile`, the exit-4 comment block).

**Identity guard in CI — required, per CONTEXT.** `hooks/pre-commit:1-12` states the hook only protects the machine that installed it (installation is opt-in via `make hooks`, deliberately). `scripts/identity_check.py:22-31` names the three callers:

```
So: one rule, three callers — the pre-commit hook (staged files), `make verify`
(the whole tree), and the test suite (which watches the rule fail, per class,
per carrier). A guard that only runs where the last leak was is a guard aimed
at the past.

Exit 0 clean, 1 on a leak, 2 on a usage error.
```

`verify-offline` already runs `identity` first, so a single `make verify-offline` step covers it — **provided the checkout is a real git checkout** (`--all` enumerates tracked files via git). `actions/checkout` default `fetch-depth: 1` is sufficient for `git ls-files`; a sparse or non-git artifact download is not.

**Lint — flag: there is no linter in this repo.** `grep -rin "ruff|flake8|black|lint"` across source, `pyproject.toml` and `Makefile` returns **zero** hits. REQ-10 says "lint, type check and the offline test suite". So the planner must choose, explicitly:
- (a) treat `mypy` as the type check and add a real linter (`ruff` is the low-friction choice) to the `dev` extra plus a `lint` Makefile target, or
- (b) argue in writing that `mypy` satisfies both, which contradicts REQ-10's wording.

If (a), see the two coupling hazards under "Would break an existing gate" below.

**Workflow shape to write** (no in-repo analog; keep it minimal so the Makefile stays the single definition):
- trigger: `pull_request` + `push` to `main`
- one job, `ubuntu-latest`, `actions/checkout@v4`, `actions/setup-python@v5` with `python-version: "3.10"` — the floor from `requires-python = ">=3.10"` and `[tool.mypy] python_version = "3.10"`; testing the floor is what the config claims
- steps: create `.venv`, `pip install -e '.[dev]'`, `make verify-offline`
- **no** `continue-on-error`, no `|| true`, no piping the make output through `tee` — the Makefile header (`:1-12`) explains that a pipeline takes the status of its last command, and the same failure mode is available in YAML.

---

### `pyproject.toml` (packaging config)

**Analog:** itself. It is a heavily commented file where the comments carry decisions that are load-bearing elsewhere in the tree. **Nothing may be reformatted, reordered or rewritten by a tool.**

**Comment blocks that must survive verbatim:**

| Lines | What it records | Why it cannot be dropped |
|---|---|---|
| 22-30 | `dev` extra kept out of runtime deps; `mypy>=2.0` not `>=1.8` | "a contributor resolving 1.x would run a WEAKER check … and get a green that means less than ours" |
| 32-49 | `browser` extra + the **audited 2026-08-02** `nodriver` supply-chain note and the AGPL-vs-MIT reasoning | CONTEXT names this a constraint; it is the record of a maintainer approval |
| 60-63 | mypy committed so a bare `mypy` checks the same thing for everyone | |
| 65-69 | `files = ["boty", "scripts"]` — the verifier is itself type-checked | |
| 74-87 | `disallow_untyped_defs` rationale, and the explicit "Deliberately NOT strict" | |
| 89-93 | missing-stub overrides | |
| 97-99 | `addopts = "-ra"` — a silently-skipped test is the failure mode this project exists to prevent | |

**Changes Phase 4 actually needs:**

```toml
name = "bot-y"        # keep — `pip install bot-y`, REQ-11; PyPI name is unclaimed and the first publish claims it permanently
version = "0.1.0"     # -> "1.0.0"
license = { text = "MIT" }
```

- `[project.scripts] boty = "boty.cli:main"` (`:54-55`) already exists — the console entry point is done; a release check should verify `boty --help` works from a wheel install, not just an editable one.
- `[tool.setuptools.packages.find] include = ["boty*"]` (`:57-58`) — `scripts/`, `tests/`, `config/` are **not** packaged. Anything the installed CLI needs at runtime that lives outside `boty/` is a packaging bug; `config/products.yaml` is user-supplied by design, so verify `boty` starts from a wheel with no repo checkout.
- `[project.urls] Homepage = "https://github.com/danieljamesjohnson/bot-y"` (`:51-52`) — confirm this is the real remote before publishing.
- Consider adding `Documentation`/`Source`/`Issues` URLs and PyPI classifiers, in the same commented style.

---

### `LICENSE` (new — currently missing)

**Flag, blocking REQ-11.** `pyproject.toml:11` declares `license = { text = "MIT" }`, `README.md:411` has a `## License` heading, and **there is no `LICENSE` file in the repo** (`ls LICENSE*` → no such file). A 1.0.0 release of an "open source ready" project whose licence exists only as a metadata string is exactly the kind of asserted-but-unimplemented contract `tests/test_support_matrix.py:12-19` was written about. Add `LICENSE` (MIT, "Dan Johnson", 2026) and, if setuptools does not pick it up automatically, wire it in `[project]`.

---

### `README.md` (doc + machine-read table)

**Analog:** itself. Two regions with different rules.

**1. The support matrix (README.md:98-106) is parsed by `tests/test_support_matrix.py`. This is the tightest coupling in the phase.**

- The table is located **by its header cells, not by line number** (`test_support_matrix.py:59-63`):

```python
HEADER_CELLS = ("Retailer", "Rung", "Extraction", "robots.txt", "Terms", "Method", "Status")
RETAILER, RUNG, EXTRACTION, ROBOTS, TERMS, METHOD, STATUS = 0, 1, 2, 3, 4, 5, 6
```
  So prose around the table can move freely, but **renaming a header cell or adding/removing a column breaks the locator** — and note the surrounding tables are safe only by luck: "the `make verify` verdict table further down is three columns and the stage table is two, but that is luck, not a rule" (`:61-63`). Any new 7-column table added to README could hijack the locator.
- Row labels must match `ROADMAP_RETAILERS` values **character for character, accent included** (`test_support_matrix.py:29-35`; `scripts/evidence_check.py:156-164`): `GameStop, Walmart, Best Buy, Pokémon Center, Nintendo, Target, Amazon`. "If a row does not match, fix the README label; do not loosen the comparison."
- Cell vocabularies are fixed: `ROBOTS_POSITIONS = ("permits","disallows","silent on","unread")`, `TERMS_POSITIONS = ("forbids","permits","silent","unread")`, `RUNGS = {"1","2","3","4"}`, `EXTRACTIONS = ("structured","dom")`, `NO_EXTRACTION = "—"`, `DISAGREE = "⚠ disagree"`.
- `UNREAD_POSITIONS` (`:110-118`) is an **enumerated pin of five (retailer, column) pairs** — widening it means editing a red test in the same commit as the evidence-log entry that justifies it.
- Rung ↔ Extraction is tied **in both directions** by `_extraction_mismatch`; `WORKING_RUNGS = {"1","2","3"}` cells must be backed by a configured watch in `config/products.yaml`.
- 03.1-04 verified the `rung`/`extraction`/`degraded` cells cell-by-cell against live status output. **Any Phase 4 rewrite of the matrix re-opens that verification.** The safe move is: do not touch the seven data rows; add the "Method"/"Status" narrative only if a live re-check backs it.
- Corruption tests at the bottom of the file run the same rules against a deliberately broken copy of the real README (`:37-42`), so a rule cannot be quietly weakened.

**2. The doc regions Phase 4 should extend** (free prose, no parser):
- `## Install` (`:253-268`) — add the PyPI line `pip install bot-y` once published; keep the editable/`.[browser]` instructions.
- `## Verifying it works` (`:346-381`) — carries the verdict table (`:360-365`) and the **stage table** (`:375-381`, one row per `verify` stage: `test`, `types`, `fixtures`, `controls`, `mutation`). **Adding a `lint` stage to `verify` requires adding a row here**, and `:349-350` already documents `make verify-offline   # same minus the live check — for CI`.
- Add a link to `docs/adding-a-retailer.md` — there is currently **no** "Adding a retailer" section in the README (headings are: Why another one, Retailer status, Install, Use, Verifying it works, Being a good citizen, License).

---

## Shared Patterns

### Comment-as-decision-record
**Source:** `pyproject.toml:22-30`, `boty/retailers.py:88-94`, `Makefile:1-12`, `tests/test_support_matrix.py:1-45`
**Apply to:** every file this phase touches.
Every non-obvious choice carries a `WHY THIS EXISTS` block naming the failure it prevents, often with the incident that motivated it. New files (workflow YAML, CONTRIBUTING) must do the same; a bare config file is off-pattern here.

### Gates over judgement
**Source:** `.planning/ROADMAP.md` § "Why `make verify` exists"; `tests/test_verify_makefile.py:1-13`
**Apply to:** CI, and any new doc claim.
If a doc asserts something, ask whether a test can read it — the support matrix is the precedent (prose that nothing checked, until it was checked).

### A gate must be watched failing
**Source:** `tests/test_support_matrix.py:37-42`
**Apply to:** any new check added in this phase (lint, CI).
"A gate asserted only against the tree it is meant to guard has never been watched failing, and this project has already shipped one of those." If a `lint` target lands, demonstrate it going red.

### Never overwrite a superseded claim
**Source:** `docs/retailer-evidence.md:87-96`, `:645-651`; `.planning/REQUIREMENTS.md:110`
**Apply to:** `docs/adding-a-retailer.md`, README edits, and the release notes.

---

## Where a naive implementation breaks something

1. **CI runs `make verify` instead of `make verify-offline`** → live requests to six retailers on every PR, from GitHub's IPs, at PR frequency. Directly contradicts the politeness budget (`docs/retailer-evidence.md:341-352`) and the pacing decision in `config/products.yaml:15-31`.
2. **CI flattens exit 3/4 to a pass, or pipes make through `tee`** → a run that verified nothing prints the same green. The Makefile header and the exit-3/exit-4 comment blocks exist because this already happened.
3. **CI skips `identity`** → the guard reverts to protecting only machines that ran `make hooks`. `verify-offline` includes it; a hand-rolled "pytest + mypy" workflow would not.
4. **CI installs `.[browser]`** → pulls AGPL `nodriver` into a build of an MIT project, against a recorded maintainer decision (`pyproject.toml:40-49`), and converts the intended `PASS (INCOMPLETE)` path into a live-Chrome path.
5. **Reformatting `pyproject.toml`** (a TOML formatter, or a "tidy up the comments" pass) → deletes the mypy-strictness rationale and the nodriver audit. Both are cited from CONTEXT as constraints.
6. **Editing the support-matrix header, adding a 7-column table to README, or renaming a retailer label** → `tests/test_support_matrix.py` fails, or silently binds to the wrong table.
7. **Adding a `lint` stage to `verify` without updating `README.md:375-381` and re-reading `tests/test_verify_makefile.py`** → the documented stage list and the real one disagree; the Makefile tests stub `$(PYTHON)` and assert the recipe's control flow, so a new stage needs a stub branch.
8. **Bumping to 1.0.0 with no `LICENSE` file** → ships an MIT claim with no MIT text.
9. **Publishing to PyPI or pushing the v1.0.0 tag** → explicitly reserved for Dan (`04-CONTEXT.md:32-39`). Plan the release so it is one authenticated command / one tag push; do not execute it.
10. **A contributor doc with a fictional retailer** → REQ-09 says "a real adapter end to end". Nintendo (`docs/retailer-evidence.md:958-979`, `boty/retailers.py:28`, `config/products.yaml:63-70`) is the one to walk, because it teaches "no code" as the default answer.

## Metadata

**Analog search scope:** repo root, `boty/`, `scripts/`, `tests/`, `docs/`, `config/`, `hooks/`, `.planning/`
**Files scanned:** 20
**Pattern extraction date:** 2026-08-04
