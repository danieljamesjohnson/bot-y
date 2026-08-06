---
phase: 04-open-source-ready
verified: 2026-08-06T15:24:08Z
status: human_needed
score: 3/5 roadmap criteria verified; 2 UNMET by recorded maintainer deferral
overrides_applied: 0
re_verification: null
human_verification:
  - test: "Open a throwaway pull request against `main` (branch it, push, `gh pr create`, close without merging)."
    expected: "A `verify` job appears under Actions with event `pull_request`, runs `make verify-offline`, and reports success. `gh run list --workflow ci.yml` then returns two runs, not one."
    why_human: "The `pull_request` trigger has never fired in production. `gh run list --workflow ci.yml` returns exactly one run, event `push`. Criterion 2's claim that CI runs on every PR is proven by the shipped `on:` block and by 67 machine-checked contract tests (I falsified two of them live), but GitHub honouring the trigger is platform behaviour that cannot be observed without a real PR. It is handoff step 5, which was offered and not taken."
  - test: "Decide whether to publish 1.0.0 to PyPI — the four steps on `04-06-HANDOFF.md` (trusted publisher, tag, push, watch)."
    expected: "Criteria 3 and 5 close. `https://pypi.org/pypi/bot-y/1.0.0/json` returns 200, `git ls-remote --tags origin` returns a `v1.0.0` ref, and REQ-11 flips to Complete."
    why_human: "Deferred by Dan on 2026-08-06, verbatim: *\"i don't think we need to host it yet. it's probably not quite ready for that\"*. Publishing permanently claims a PyPI distribution name; it is reserved to the maintainer by `04-CONTEXT.md`. There is no code gap to close — I rebuilt and re-proved the artifacts myself (10/10 checks) and they are publishable today."
---

# Phase 4: Open Source Ready — Verification Report

**Phase Goal:** Someone who isn't me can install bot-y, add a retailer, and open a PR that I can trust.
**Verified:** 2026-08-06T15:24:08Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

The goal decomposes into three clauses. Two are achieved and verified first-hand. The
third — *install* — is achieved locally and blocked only on a maintainer action that was
offered, declined and recorded.

| Clause | Verdict | Basis |
|---|---|---|
| …can **add a retailer** | ✓ ACHIEVED | 355-line walkthrough, 19-test gate, gate falsified live |
| …can **open a PR I can trust** | ✓ ACHIEVED (one half unobserved) | Unfiltered `pull_request` trigger running `make verify-offline`; 67-test contract gate, falsified live; one real green run on `push` |
| …can **install bot-y** | ⚠ LOCALLY PROVEN, NOT PUBLISHED | I rebuilt the artifacts: 10/10 release checks, `twine check` PASSED both, clean-venv install works. Not on PyPI because Dan deferred |

### Observable Truths — the five ROADMAP success criteria

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | `docs/adding-a-retailer.md` walks a real adapter end to end, and states why a control product is mandatory | ✓ VERIFIED | 355 lines. Four numbered steps walking Nintendo (`### 1. Probe…` → `### 4. Two YAML watches, one of them a control`). `## Why a control product is mandatory` present with `### The rule a control has to satisfy` and `### The rule biting, on a real candidate that was rejected`. `## The UNKNOWN contract` at L171 with "An absence is never OUT_OF_STOCK" at L181. `pytest tests/test_contributor_docs.py -q` → **19 passed**. **Falsified live (F1):** renamed the control-mandate heading in an isolated worktree → 3 failed incl. `test_a_deleted_heading_is_caught` |
| 2 | CI runs the test suite on every PR, offline, against fixtures | ✓ VERIFIED (config + gate); production PR trigger unobserved | `.github/workflows/ci.yml` L79-82: `on: pull_request:` with **no** branch or path filter, plus `push: branches: [main]`. Single run step L186 `run: make verify-offline`, which per `Makefile` L157-170 runs identity → lint → tests → types → **fixtures** → controls (skipped offline) → mutation. `pytest tests/test_ci_workflow.py -q` → **67 passed**. **Real run observed:** `gh run view 31066215395` → event `push`, branch `main`, sha `76d4156`, conclusion **success**. **Falsified live (F3, F5):** added `branches: [main]` to the `pull_request` trigger → `test_pull_requests_are_not_filtered_by_branch_or_path` failed; swapped `verify-offline` for the live `verify` → 9 failed. **NOT observed:** `gh run list --workflow ci.yml` returns exactly **one** run — the push. The PR trigger has never fired. → human verification item 1 |
| 3 | `pip install bot-y` works from PyPI | ✗ UNMET — deferred by the maintainer, not a build defect | Re-measured by me: `https://pypi.org/pypi/bot-y/json` → **HTTP 404**, `https://pypi.org/pypi/bot-y/1.0.0/json` → **HTTP 404**. Dan deferred on 2026-08-06, verbatim: *"i don't think we need to host it yet. it's probably not quite ready for that"*. Everything the criterion needs exists and was re-proven by me — see the release-check row below |
| 4 | README documents the retailer support matrix with each one's method and status | ✓ VERIFIED (preserved, not achieved this phase) | `grep -c '^| Retailer | Rung | Extraction'` → **1** (one table, so no second table can hijack the locator). Seven rows present — GameStop, Walmart, Nintendo, Best Buy, Pokémon Center, Amazon, Target — each carrying a `Method` and a `Status` cell. `pytest tests/test_support_matrix.py -q` → **31 passed**. **Falsified live (F4):** changed GameStop's Rung cell from 1 to 9 → 10 failed |
| 5 | A tagged v1.0.0 release exists | ✗ UNMET — same deferral | `git tag -l` → **0 tags**. `git ls-remote --tags origin` → **0 refs**. No tag anywhere, local or remote. `gh run list --workflow release.yml` → no runs, consistent with a workflow only a `v*` tag push can start |

**Score:** 3/5 roadmap criteria verified. The two unmet ones are a single deferred human
action, not two implementation gaps.

### Why criteria 3 and 5 are NOT reported as gaps

This is the finding I most wanted to falsify, and could not. Three independent checks say
the deferral is honest rather than a cover for unfinished work:

1. **The artifacts exist and are publishable today.** I ran `make release-check` myself
   rather than trusting `04-05-SUMMARY.md`: `release check: PASSED — 10/10 checks, sdist
   and wheel proven`, exit 0. `twine check` printed `PASSED` for both
   `bot_y-1.0.0-py3-none-any.whl` and `bot_y-1.0.0.tar.gz`. The clean-venv install outside
   the repo ran `boty --help` → 0 and `boty check -c no-such-config.yaml` → 2. The install
   pulled 16 packages and `nodriver` was not among them. `License-Expression: MIT` and
   `bot_y-1.0.0.dist-info/licenses/LICENSE` both reached the wheel.
2. **Nothing was published, tagged or pushed by an agent.** `grep` for `twine upload`,
   `gh release create`, `git tag `, `git push` across the phase's non-planning,
   non-workflow diff returns nothing. `scripts/release_check.py` contains no upload verb.
3. **The handoff card is on disk and still accurate.** `04-06-HANDOFF.md`, 192 lines. I
   spot-checked its two load-bearing strings against the shipped tree: it names the
   environment as `pypi`, and `.github/workflows/release.yml:143` reads `environment: pypi`
   — they match. It states at L169 "There is no `PYPI_API_TOKEN` in this design and no
   repository secret to add", which is consistent with the OIDC-only workflow.

Phase 4 is the last phase in the roadmap, so Step 9b deferred-filtering found no later
phase to route these to. They belong to the maintainer, and they are surfaced as human
verification item 2 rather than as a gap-closure plan.

### Required Artifacts

Every artifact declared across all six plans exists and is substantive. `gsd-tools query
verify.artifacts` reported `all_passed: true` for all six plans (28 artifact declarations,
0 issues — including every `min_lines` and `contains` constraint).

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `docs/adding-a-retailer.md` | REQ-09 walkthrough + control mandate | ✓ VERIFIED | 355 lines, 16 headings, Nintendo end to end |
| `CONTRIBUTING.md` | Setup, hook, checks, PR contract | ✓ VERIFIED | names `make hooks` |
| `tests/test_contributor_docs.py` | Docs gate | ✓ VERIFIED | 492 lines, 19 tests, falsified live |
| `LICENSE` | MIT text | ✓ VERIFIED | present; GitHub API now reports `license: mit` |
| `MANIFEST.in` | Explicit sdist surface | ✓ VERIFIED | `prune tests/config/docs/scripts/deploy/hooks/served/.github/.planning`, `include CHANGELOG.md` |
| `pyproject.toml` | PEP 639 licence, 1.0.0, ruff config | ✓ VERIFIED | `version = "1.0.0"` L7; `[tool.ruff.lint] select` L283 |
| `tests/test_packaging_metadata.py` | Licence + sdist prune gate | ✓ VERIFIED | 651 lines, 19 tests, falsified live |
| `Makefile` | `lint` stage inside `verify` | ✓ VERIFIED | L159 `$(MAKE_Q) lint || { echo "VERIFY: FAIL (lint)"; exit 1; }`; `release-check` L97 |
| `tests/test_verify_makefile.py` | Stage gates incl. `LINT_RC` | ✓ VERIFIED | 252 lines, 8 tests; runs the real Makefile against a failing stub |
| `.github/workflows/ci.yml` | The PR gate | ✓ VERIFIED | unfiltered `pull_request`, `permissions` read-only, `python-version: "3.10"` quoted, `runs-on: ubuntu-24.04` |
| `tests/test_ci_workflow.py` | Workflow contract gate | ✓ VERIFIED | 1232 lines, 67 tests, falsified live twice |
| `.github/workflows/release.yml` | Tag-triggered OIDC publish | ✓ VERIFIED | `environment: pypi`, `id-token: write` on the publish job only |
| `scripts/release_check.py` | Artifact proof | ✓ VERIFIED | 604 lines; **I ran it: 10/10 PASSED** |
| `scripts/mutation_check.py` | Sandbox carries the new gates' inputs | ✓ VERIFIED | `SANDBOX_CONTENTS` includes `CONTRIBUTING.md`, `LICENSE`, `MANIFEST.in`, `.github` |
| `CHANGELOG.md` | Release notes | ✓ VERIFIED | `## [1.0.0] - 2026-08-05` L21; WR-01 markup leak confirmed gone (0 matches) |
| `boty/cli.py` | Actionable missing-config error | ✓ VERIFIED | behavioural check below |
| `04-06-HANDOFF.md` | Ordered publish card | ✓ VERIFIED | 192 lines, 10 sections, strings match the shipped tree |
| `.planning/ROADMAP.md` | Five-criterion outcome table | ✓ VERIFIED | present, criteria wording unaltered |

### Key Link Verification

`gsd-tools query verify.key-links` produced several false negatives — double-escaped regex
literals (`scan\\(`), and prose-named sources like ``Makefile `verify` `` reported as
"Source file not found". Every link was re-checked by hand against the real files.

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `README.md` | `docs/adding-a-retailer.md` | markdown link | ✓ WIRED | L383 `[docs/adding-a-retailer.md](docs/adding-a-retailer.md)` |
| `README.md` | `LICENSE` | markdown link | ✓ WIRED | L463 `[LICENSE](LICENSE)` |
| `docs/adding-a-retailer.md` | `boty/retailers.py` | `FIRST_PARTY` / `MARKETPLACES` | ✓ WIRED | both symbols pinned two-directionally by the gate |
| `pyproject.toml` | `LICENSE` | `license-files` | ✓ WIRED | proven downstream: `License-Expression: MIT` in the built wheel |
| `MANIFEST.in` | sdist file set | `prune` directives | ✓ WIRED | L41 `prune tests`; release-check confirms "no pruned directory in either artifact" |
| `Makefile verify` | `Makefile lint` | trap line | ✓ WIRED | L159 exact trap; watched re-raising by `test_a_failing_lint_fails_verify` |
| `Makefile lint` | `[tool.ruff.lint]` | bare `ruff check` | ✓ WIRED | invoked as `$(PYTHON) -m ruff`, no rule flags |
| `ci.yml` | `Makefile verify-offline` | single run step | ✓ WIRED | L186 |
| `ci.yml` | `requires-python` | quoted `python-version` | ✓ WIRED | `"3.10"`, gate rejects the unquoted float |
| `tests/test_ci_workflow.py` | `ci.yml` | `yaml.safe_load` | ✓ WIRED | L434, L531 |
| `tests/test_ci_workflow.py` | `release.yml` | 04-04 rules reapplied | ✓ WIRED | L930, L937 and the whole 990-1229 block |
| `scripts/release_check.py` | `scripts/identity_check.py` | `scan(paths, root)` | ✓ WIRED | L532 `leaks += scan(files, extracted)`; ran green |
| `release.yml` | PyPI Trusted Publishing | OIDC | ✓ WIRED | `id-token: write` scoped to the publish job |
| `Makefile` | `scripts/release_check.py` | `release-check` target | ✓ WIRED | L97-98; **executed, exit 0** |
| `mutation_check.py` | new gates' inputs | `SANDBOX_CONTENTS` | ✓ WIRED | 8/8 mutations caught with the gates inside the sandbox |
| `04-06-HANDOFF.md` | `release.yml` | environment name | ✓ WIRED | card says `pypi`; workflow L143 says `environment: pypi` |
| clean-venv install | `pypi.org/pypi/bot-y/1.0.0/json` | published artifact | ✗ NOT WIRED | 404 — the deferred publish. Criterion 3's only remaining link |

### Data-Flow Trace (Level 4)

| Artifact | Data source | Produces real data | Status |
|---|---|---|---|
| `tests/test_contributor_docs.py` | reads `docs/adding-a-retailer.md`, `CONTRIBUTING.md`, `README.md` off disk | Yes — corrupting the real doc reddens it | ✓ FLOWING |
| `tests/test_packaging_metadata.py` | reads `pyproject.toml` + `LICENSE` off disk, `git ls-files` for prune coverage | Yes — swapping the licence text reddens it | ✓ FLOWING |
| `tests/test_ci_workflow.py` | `yaml.safe_load` over the real workflow directory | Yes — editing the real `ci.yml` reddens it | ✓ FLOWING |
| `tests/test_verify_makefile.py` | copies the **real** Makefile to `tmp_path`, runs `make` against a stub `$(PYTHON)` | Yes — a stage failure propagates to the exit code | ✓ FLOWING |
| `tests/test_support_matrix.py` | parses the real README table | Yes — a changed cell reddens it | ✓ FLOWING |
| `scripts/release_check.py` | builds from 157 tracked files into a clean tree, installs into a venv outside the repo | Yes — 10 checks over real built bytes | ✓ FLOWING |
| Vacuous-green guard | `_tracked_top_level_dirs` | Raises `NotATrackedTree` rather than returning an empty set; asserted by `pytest.raises` at L605 and L625, plus a positive control at L634 | ✓ FLOWING |

No hollow artifacts. No gate reads a fixture where it claims to read the tree.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| The phase gate is green offline | `make verify-offline` | exit **0** — identity PASS (156 files), **531 passed**, mypy "no issues found in 18 source files", **8/8 mutations caught**, `VERIFY: PASS (OFFLINE …)` | ✓ PASS |
| The artifacts build and are publishable | `make release-check` | exit **0** — `release check: PASSED — 10/10 checks`; `twine check` PASSED both | ✓ PASS |
| Console script runs | `python -m boty.cli --help` | exit 0 | ✓ PASS |
| Missing config is actionable, not a traceback | `python -m boty.cli check -c /nonexistent/nope.yaml` | exit **2**, three lines of guidance, **0** `Traceback` lines | ✓ PASS |
| Not on PyPI | `curl https://pypi.org/pypi/bot-y/json` | **404** | ✓ PASS (confirms criterion 3 UNMET) |
| No tag exists | `git tag -l` / `git ls-remote --tags origin` | 0 / 0 refs | ✓ PASS (confirms criterion 5 UNMET) |
| CI ran for real, once | `gh run view 31066215395` | event `push`, `main`, `76d4156`, conclusion **success** | ✓ PASS |
| CI has never run on a PR | `gh run list --workflow ci.yml` | exactly **1** run | ✓ PASS (confirms the honest caveat) |

### Probe Execution — gates watched going red

The phase's own idiom is that no gate is trusted until it has been watched failing. I did
not take the SUMMARYs' word for this. I created a detached `git worktree` at HEAD,
corrupted **real** inputs one at a time, and ran the gate. Baseline in the clean worktree:
**136 passed** across the four suites.

| # | Corruption applied to the real file | Gate | Result | Status |
|---|---|---|---|---|
| F1 | Renamed `## Why a control product is mandatory` in `docs/adding-a-retailer.md` | `test_contributor_docs.py` | **3 failed**, 16 passed — incl. `test_a_deleted_heading_is_caught` | ✓ RED |
| F2 | Replaced the MIT `LICENSE` body with Apache-2.0 text | `test_packaging_metadata.py` | **5 failed**, 14 passed — incl. `test_a_licence_file_with_another_licences_title_is_caught` | ✓ RED |
| F3 | Added `branches: [main]` to `ci.yml`'s `pull_request` trigger | `test_ci_workflow.py` | **2 failed**, 65 passed — incl. `test_pull_requests_are_not_filtered_by_branch_or_path` | ✓ RED |
| F4 | Changed GameStop's Rung cell from `1` to `9` in the README matrix | `test_support_matrix.py` | **10 failed**, 21 passed | ✓ RED |
| F5 | Switched CI's run step from `make verify-offline` to `make verify` | `test_ci_workflow.py` | **9 failed**, 58 passed | ✓ RED |
| F7 | Added a third PR-triggered workflow holding `id-token: write` | `test_ci_workflow.py` | **1 failed** — `test_no_workflow_in_this_repo_lets_a_pull_request_reach_privilege` | ✓ RED |
| F6 | Added a third workflow with `some-vendor/thing@main`, `continue-on-error: true`, `ubuntu-latest`, no `timeout-minutes` | `test_ci_workflow.py` | **67 passed — GREEN** | ✗ DID NOT CATCH (see WR-02) |

**Every "watched going red" claim in the SUMMARYs that I tested is real.** The gates read
the tree, not a fixture, and they fail on a single corrupted token. F6 is the one probe
that came back green, and it is exactly the scope gap `04-REVIEW.md` WR-02 already names —
independently reproduced here rather than taken on trust.

The worktree was removed and `git status --short` is empty. Nothing in the repository was
modified by this verification.

### Requirements Coverage

| Requirement | Source plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| REQ-09 | 04-01 | `docs/adding-a-retailer.md` walks a contributor through a real adapter end to end and states why a control product is mandatory | ✓ SATISFIED | Criterion 1 above. Marked `[x]` / Complete in REQUIREMENTS.md — **correct** |
| REQ-10 | 04-03, 04-04 | CI runs lint, type check and the offline test suite on every PR | ✓ SATISFIED | `ci.yml` runs `make verify-offline`, which runs `lint` (Makefile L159) and `types` (L161) and the suite (L160). Marked `[x]` / **Complete (04-04)** — **correct**, and correctly attributed: 04-03 landed the lint half only and carries no `requirements` field; 04-04 owns the requirement. The two premature Complete flips were reverted (`61dccab`, `6b9a212`) and have not crept back |
| REQ-11 | 04-02, 04-05, 04-06 | `pip install bot-y` works from PyPI, and a v1.0.0 tag exists | ✗ BLOCKED — correctly **Pending** | Both halves re-measured by me: PyPI 404, 0 tags local and remote. Marked `[ ]` / Pending in REQUIREMENTS.md — **correct**. Blocked on a maintainer action, not on code |

**Requirement-status hygiene: clean.** All three IDs REQUIREMENTS.md maps to Phase 4 are
claimed by at least one plan — no orphans. No requirement is marked Complete on evidence
that does not support it, and no criterion was reworded, shortened or merged to make it
meetable.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `tests/test_support_matrix.py` | 70, 303, 868, 874 | literal `TBD` | ℹ️ Info — **not a debt marker** | `TBD` is the string the gate *rejects*: `test_..._tbd_...` corrupts a matrix cell to `TBD` and asserts the rule reddens. A gate testing its own rejection vocabulary is the opposite of debt |

Scanned all 32 non-planning files in `git diff b0a272f..HEAD`. **Zero** `FIXME`, `XXX`,
`TODO`, `HACK`, `PLACEHOLDER`, "coming soon", "not yet implemented" or "will be here" in
any of them. The debt-marker gate does not fire.

The one genuine content defect the review found — WR-01, leaked agent tool-call markup at
the end of a `CHANGELOG.md` that ships to PyPI via `MANIFEST.in` — is **fixed and
verified**: `grep -c 'antml\|invoke name\|parameter name='` over `CHANGELOG.md` returns
**0**. The gate gap it names is real and remains open: `scripts/release_check.py` touches
`CHANGELOG.md` only to read a version string (L436, L465) and to assert its presence in
the sdist (L169). Nothing reads the body, so a future prose leak would ship again.

### Review Warnings — do any undermine a must-have?

| Finding | Undermines a must-have? | Reasoning |
|---|---|---|
| **WR-02** third workflow escapes the pin / exit-code / timeout / runner rules | **No** — WARNING | Reproduced live (F6). But 04-04's actual truth is *"A pull request cannot obtain a write token, a repository secret or an OIDC identity through any workflow in this repo, and a later workflow cannot quietly acquire one"* — and that rule **is** directory-wide, proven by F7 catching a third PR-triggered workflow with `id-token: write`. The pinning truth is scoped to the workflows that exist, and both `ci.yml` and `release.yml` are covered by per-file rules. This is future-proofing, not a broken claim |
| **WR-06** `_tracked_top_level_dirs` says "tracked" but passes `--others`; `.split()` breaks on spaces | **No** — WARNING | 04-02's truth is that the gate *"raises a named error rather than returning an empty set when git cannot answer"*. Verified: `NotATrackedTree` raised at L374 and L385, asserted by `pytest.raises` at L605 and L625, with a positive control at L634 guarding against unconditional raising. WR-06 is a naming/prose accuracy defect plus a latent false-red on paths containing spaces |
| **WR-01** changelog markup leak | **No** — fixed | 0 matches remain |
| WR-03, WR-04, WR-05, WR-07, IN-01…IN-06 | No | None touch a Phase 4 must-have or a success-criterion claim. WR-03/WR-04/IN-05/IN-06 concern `boty/retailers.py` and `boty/parse.py` detector behaviour, which is Phase 2/3 territory |

### Not caused by this phase — recorded, not scored against it

`make verify` (live) fails on this host: `VERIFY: FAIL (live controls)`, exit 2. Two
distinct classes, which `control_check.py` separates itself: Best Buy and Target
(rung 3) **could not run** — `no Chrome/Chromium binary found`, which says nothing about
the detector; Walmart and Amazon are **blocked at the edge** by challenge pages at HTTP
200, which does. All four read UNKNOWN, never a false verdict — the fail-safe working as
designed.

I did not re-run the live gate (two retailers are in backoff), and I confirmed the
attribution instead: `git diff --name-only b0a272f..HEAD` outside `.planning/` touches
`boty/cli.py`, `boty/monitor.py`, `boty/parse.py` and `boty/retailers.py` only, and the
review attributes those edits to lint fixes plus a Target retry. No Phase 4 plan added,
removed or repointed a retailer, extractor or control. Detail is on disk in
`.planning/phases/04-open-source-ready/deferred-items.md`, which is accurate.

### Gaps Summary

**No implementation gaps.** I set out to falsify the SUMMARY narrative and could not. The
strongest attempt — corrupting seven real inputs and watching the gates — put six of seven
gates red on a single changed token, and the seventh miss was a scope limitation the
project's own code review had already found and written down.

What remains is not code. It is one maintainer decision (publish, or don't) and one
five-minute confirmation (open a throwaway PR). Both are surfaced as human verification
items. Criteria 3 and 5 stand UNMET and unamended, which is the honest record of a
deferral, not a failure — and the handoff card means closing them later needs no
replanning.

The two things worth a maintainer's attention when convenient, neither blocking:

1. **WR-02** — a third workflow file added later would escape the pin, exit-code, timeout
   and runner rules while the suite stays green. Reproduced here (F6). The rule functions
   are already pure, so making the four file-scoped rules directory-wide is a test-only
   change.
2. **WR-01's residue** — nothing reads the changelog *body*, so the class of defect that
   shipped agent markup into a PyPI-bound file has no gate. Worth closing before the
   publish, since the changelog is what a stranger reads first.

---

_Verified: 2026-08-06T15:24:08Z_
_Verifier: Claude (gsd-verifier)_
