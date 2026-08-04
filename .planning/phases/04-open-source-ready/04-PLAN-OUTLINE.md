# Phase 4: Open Source Ready — Plan Outline

**Drafted:** 2026-08-04
**Granularity:** coarse
**Plans:** 6, in 5 waves

| Plan ID | Objective | Wave | Depends On | Requirements |
|---|---|---|---|---|
| 04-01 | Contributor docs — `docs/adding-a-retailer.md` walking Nintendo end to end, why a control product is mandatory, the UNKNOWN contract; `CONTRIBUTING.md`; README prose entry point. Owns every README edit in wave 1 | 1 | — | REQ-09 |
| 04-02 | The missing `LICENSE`, and packaging metadata that matches it — MIT text, `license-files` wiring, URLs, classifiers, and a test that fails if the declared licence and the shipped file ever disagree | 1 | — | REQ-11 |
| 04-03 | A linter, from zero — `ruff` in the `dev` extra, a curated rule set recorded as a decision, the findings actually resolved, a `lint` stage inside `make verify`, its README stage row, and the stage watched going red | 2 | 04-01, 04-02 | REQ-10 |
| 04-04 | GitHub Actions CI — one job on every PR that runs `make verify-offline` and nothing else, plus an offline test asserting the workflow's contract (offline target, no `.[browser]`, no exit-code flattening, least-privilege permissions) | 3 | 04-03 | REQ-10 |
| 04-05 | Release engineering, all of it local — version 1.0.0, `CHANGELOG.md`, a tag-triggered publish workflow using PyPI Trusted Publishing, and artifacts *proven* by `python -m build` + `twine check` + a wheel installed into a clean venv where `boty --help` runs | 4 | 04-02, 04-03, 04-04 | REQ-11 |
| 04-06 | Maintainer handoff — the one authenticated action this agent cannot take: configure the Trusted Publisher, push `v1.0.0`, confirm `pip install bot-y` from PyPI, then record the criteria verdicts | 5 | 04-05 | REQ-11 |

---

## Per-plan notes

### 04-01 — Contributor docs · `autonomous: true`

**Closes criterion 1** (`docs/adding-a-retailer.md` walks a real adapter end to end and states why a control product is mandatory) and **preserves criterion 4** (README documents the support matrix with each retailer's method and status).

Criterion 4 is already MET in the tree — the seven-row, seven-column matrix at `README.md:98-106` is machine-read by `tests/test_support_matrix.py` and was verified cell-by-cell against live status output in 03.1-04. This phase's job is not to write it but to **not break it**. This plan therefore edits README free prose only (an "Adding a retailer" pointer, and the `## License` line pointing at the file 04-02 creates in the same wave) and re-runs `pytest tests/test_support_matrix.py` as its own verification. It must not touch the seven data rows, must not rename a header cell, and must not add another seven-column table — the locator binds by header cells, not line numbers.

Nintendo is the spine of the doc, because it teaches that **the default answer is "no adapter"**: four edits, all citable in the tree (`docs/retailer-evidence.md:958-979`, `boty/retailers.py:28`, the `MARKETPLACES` absence-is-a-claim comment at `:88-94`, `config/products.yaml:51-70`). Amazon is the second example (the case where `check_html` says UNKNOWN forever and a DOM reader is needed). Files: `docs/adding-a-retailer.md`, `CONTRIBUTING.md`, `README.md` — no overlap with 04-02, so the two run in parallel.

### 04-02 — LICENSE and packaging metadata · `autonomous: true`

**Closes the blocking half of criterion 3.** Verified: there is no `LICENSE` file in this repo, `git ls-files` matches nothing for `licen*`/`copying*`, and the GitHub API reports `license: None` — while `pyproject.toml:11` declares `license = { text = "MIT" }` and the README has a `## License` heading saying "MIT". A public 1.0.0 asserting a licence with no licence text arguably grants no rights at all, and it is precisely the asserted-but-unimplemented contract `tests/test_support_matrix.py` was written about. So the fix carries a gate: a test that reads `pyproject.toml` and `LICENSE` and fails if they ever disagree.

Version stays at `0.1.0` here — the bump belongs with the release in 04-05. The load-bearing comment blocks in `pyproject.toml` (the mypy 2.x strictness rationale at `:22-30` and `:74-87`, the audited-2026-08-02 AGPL `nodriver` note at `:32-49`, the committed-mypy-config and `addopts` notes) are recorded decisions cited from CONTEXT: they survive verbatim, and no TOML formatter runs over this file, ever. Files: `LICENSE`, `pyproject.toml`, a new metadata test.

### 04-03 — A linter, from zero · `autonomous: true`

**Closes the "lint" half of REQ-10.** There is no linter in this repo — zero references to ruff, flake8, black or pylint anywhere — so one must be chosen, introduced, and wired the way every other check here is wired: into the `Makefile`, so `make verify` and CI run the identical thing. `ruff` is the choice: one fast tool, no new heavyweight dependency, and the repo already carries `# noqa: E402` comments in `scripts/control_check.py:63-67` and `scripts/evidence_check.py:127-128`, which are ruff/flake8 codes waiting for a linter to honour them.

**This was sized rather than guessed.** Running ruff 0.16 over `boty/ scripts/ tests/`:

| Rule selection | Findings | Reading |
|---|---|---|
| A curated set (pyflakes, bugbear, simplify, import order, pyupgrade and friends) | **43**, 28 auto-fixable | tractable — this is the plan's real work |
| `E` selected wholesale | **504** — of which **497 are `E501` line-too-long** | a trap: the long lines are the prose comment blocks that carry this project's decisions |
| `ruff format --check` | **32 of 36 files would be reformatted** | rejected |

Two decisions fall out and must be written into the config as comments, in this repo's comment-as-decision-record idiom:

1. **`E501` is not selected** (or the line length is set where the existing prose lives). Selecting it demands reflowing hundreds of comment blocks whose exact text is cited from CONTEXT and PATTERNS as constraints — landmine 5, arrived at from a different direction.
2. **`ruff format` is not adopted.** A 32-file reformat immediately before a 1.0.0 tag destroys `git blame` across the whole codebase and buys nothing a reviewer wanted. Lint, not format.

Note the `RUF100` unused-noqa / `E402` coupling: whether the seven existing `# noqa: E402` comments are correct or are themselves lint errors depends on the rule set chosen. Resolve it deliberately in one direction; do not delete the comments to make a number go down.

Adding a stage to `verify` has two mandatory consequences, both already documented as landmines: the README stage table at `:375-381` gains a `lint` row in the same commit, and `tests/test_verify_makefile.py` gains a stub branch (`LINT_RC`, mirroring `CONTROL_RC`) plus a test that **watches `lint` go red inside `verify`** — "a gate asserted only against the tree it is meant to guard has never been watched failing, and this project has already shipped one of those." Nothing here may weaken `make verify`; the trap-per-stage pattern that names the stage and re-raises the failure is copied, not improvised.

### 04-04 — GitHub Actions CI · `autonomous: true`

**Closes criterion 2** (CI runs the test suite on every PR, offline, against fixtures) and the rest of REQ-10.

CI delegates to the `Makefile` rather than re-listing checks, so there stays one definition of the order and one definition of the verdict. The entry point is **`make verify-offline`** — never `make verify`, which makes live requests to six retailers and would put them on GitHub's IPs at PR frequency, against this project's own politeness budget. `verify-offline` also runs `identity` first, which is required: `scripts/identity_check.py --all` enumerates tracked files via git, a commit hook only protects machines that ran `make hooks`, and this repo has already leaked its public IP to `origin/main` through a `.planning/` file. `actions/checkout` gives a real git checkout, which is what `--all` needs.

Hard requirements: create `.venv` (or pass `PYTHON=`) because every target depends on `check-venv`; install `.[dev]` and **never** `.[browser]` (AGPL `nodriver` against this MIT project, a recorded maintainer decision — and its absence is already handled by the `PASS (INCOMPLETE)` exit-4 path); Python 3.10, the floor that `requires-python` and `[tool.mypy] python_version` both claim; no `continue-on-error`, no `|| true`, no piping make through `tee`.

Since no PR can be run offline to prove any of this, the proof is a test that reads the workflow the way `test_support_matrix.py` reads the README — asserting the offline target, the absence of `.[browser]`, the absence of exit-code flattening, and least-privilege `permissions:` — and, per the shared pattern, watched failing against a deliberately broken copy. PyYAML is already a runtime dependency, so this adds nothing.

**Threat model focus:** a workflow triggered by `pull_request` runs a fork's code, so `permissions: contents: read`, no `pull_request_target`, no secrets exposed to PR runs, and third-party actions pinned. A CI workflow with write permissions is the supply-chain foothold in a repo like this one.

### 04-05 — Release engineering · `autonomous: true`

**Prepares criteria 3 and 5; closes neither** — both need the maintainer, which is why they are split out into 04-06 rather than left as tasks that would fail.

Everything in this plan is verifiable offline and must be carried to completion: bump to `1.0.0`; write `CHANGELOG.md` / release notes; add a tag-triggered publish workflow; and then **prove the artifacts rather than assert them** — `python -m build`, `twine check dist/*`, and a wheel installed into a scratch venv with no repo checkout on the path, asserting `boty --help` runs. That last step is the real engineering: `[tool.setuptools.packages.find] include = ["boty*"]` means `scripts/`, `tests/` and `config/` are not packaged, so anything the installed CLI needs at runtime from outside `boty/` is a packaging bug this test finds and nothing else would. `[project.scripts] boty = "boty.cli:main"` already exists; an editable install proves nothing about a wheel.

`build` and `twine` do **not** go into the `dev` extra — its comment says it is "everything needed to run `make verify`", and the project's small-dependency-surface rule is explicit. A separate `release` extra, or an ephemeral venv, keeps that true.

**The publish workflow uses PyPI Trusted Publishing (OIDC), not an API token in repository secrets.** A long-lived upload token in a public repo's secrets is a standing supply-chain liability that any workflow change can be made to reach; OIDC removes the secret entirely and scopes the grant to one repository and one workflow. This is a threat-model decision, and it also makes 04-06's handoff shorter for Dan.

README's `## Install` gains the PyPI line here, written in a tense that is not a lie before publication, and carries the **name-confusion warning**: `bot-y` is the distribution name and is unclaimed, but `boty` — this project's import package *and* its console script — is taken on PyPI by an unrelated, abandoned 2012 package ("Time Flies", v0.1.1, dead googlecode homepage). Someone who types `pip install boty` installs a stranger's fourteen-year-dead code. That deserves a sentence where a user reads before typing, not a footnote.

### 04-06 — Maintainer handoff · `autonomous: false`

**Closes criteria 3 and 5, by Dan.** Split out as its own plan because a checkpoint and an implementation must never share a plan, and because these two are the phase's only work an autonomous executor cannot finish.

`checkpoint:human-action` for the PyPI Trusted Publisher configuration (a dashboard-only step) and the `v1.0.0` tag push — a first publish claims the name permanently and a pushed tag is visible to anyone watching the repo, so both are Dan's by CONTEXT's explicit reservation. Then the parts that *are* mechanical once he has acted: confirm `pip install bot-y` into a clean venv from PyPI, and record the five criteria verdicts with their measurements or their reasons — the closing shape this project has used since Phase 1, where a criterion that stands with the reason written down is worth more than one quietly moved.

---

## Source coverage audit

| Source | Item | Covered by |
|---|---|---|
| GOAL | "install bot-y" | 04-02, 04-05, 04-06 |
| GOAL | "add a retailer" | 04-01 |
| GOAL | "open a PR that I can trust" | 04-03, 04-04 |
| REQ-09 | contributor guide, control product mandatory | 04-01 |
| REQ-10 | CI runs lint + type check + offline suite on every PR | 04-03 (lint), 04-04 (CI) |
| REQ-11 | `pip install bot-y` from PyPI, v1.0.0 tag | 04-02, 04-05, 04-06 |
| Criterion 1 | adding-a-retailer doc, real adapter | 04-01 |
| Criterion 2 | CI on every PR, offline, fixtures | 04-04 |
| Criterion 3 | `pip install bot-y` works | 04-02, 04-05 (prepare) → 04-06 (Dan) |
| Criterion 4 | README support matrix | already MET; 04-01 preserves and re-verifies |
| Criterion 5 | tagged v1.0.0 release | 04-05 (prepare) → 04-06 (Dan) |
| CONTEXT-1 | publishing needs Dan; plan it, do not publish | 04-05 autonomous / 04-06 checkpoint |
| CONTEXT-2 | tag needs Dan; prepare notes | 04-05 autonomous / 04-06 checkpoint |
| Verified fact 3 | no LICENSE file exists | 04-02 |
| Verified fact 4 | no linter exists | 04-03 |
| Verified fact 2 | `boty` name confusion on PyPI | 04-05 |

**No unplanned items.** No RESEARCH.md exists for this phase (`workflow.research` is false). Nothing from CONTEXT's Deferred Ideas appears here — it lists none.

## Why six plans, not the roadmap's three

The roadmap sketched contributor docs / CI / packaging-and-release before two facts were established first-hand: **there is no `LICENSE` file**, and **there is no linter**. Neither is optional — one blocks a credible 1.0.0, the other is named in REQ-10's own wording — and neither fits inside a plan that was scoped without it. The sixth plan exists because the phase's two maintainer-gated criteria must not sit in the same plan as autonomous implementation work; splitting them is what lets waves 1-4 run to completion without waiting on Dan.

## Wave structure and file ownership

Wave 1 is the only parallel wave, and the split is drawn on file ownership rather than optimism: 04-01 owns `README.md`, `docs/`, `CONTRIBUTING.md`; 04-02 owns `LICENSE`, `pyproject.toml`. Zero overlap.

Waves 2-5 are single-plan by necessity, not by habit. `README.md` and `pyproject.toml` are contested by nearly every plan in this phase, and serialising them here is a **safety property**: `README.md` carries the machine-read support matrix, the tightest coupling in the phase, where two concurrent edits could break `tests/test_support_matrix.py` or silently rebind its seven-column locator to the wrong table. The dependency 04-03 → 04-04 is likewise real rather than bookkeeping — CI cannot lint before a linter exists and its 43 findings are resolved, and landing CI first would simply paint `main` red.
