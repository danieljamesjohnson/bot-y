---
phase: 04-open-source-ready
plan: 04
subsystem: ci
tags: [req-10, github-actions, supply-chain, least-privilege, workflow-gate, python-floor]

requires:
  - phase: 04-open-source-ready
    plan: 03
    provides: "the `lint` stage inside `make verify`, so CI's single step already covers REQ-10's lint half and no separate lint step exists to drift"
  - phase: 04-open-source-ready
    plan: 02
    provides: "`MANIFEST.in`'s prune-coverage gate and the mutation sandbox's git index — the first fired on `.github` on purpose, the second is what makes the new gate run inside the sandbox"
provides:
  - ".github/workflows/ci.yml — the repo's first workflow: one job, one step, `make verify-offline`, least privilege, SHA-pinned first-party actions"
  - "tests/test_ci_workflow.py — 20 rule functions, 44 tests, 26 of them corruption tests; the workflow's contract as a gate rather than a paragraph"
  - "`prune .github` in MANIFEST.in — CI configuration stays out of the published sdist"
  - "`.github` in SANDBOX_CONTENTS — the new gate runs inside the mutation sandbox instead of raising FileNotFoundError at the baseline"
  - "The first end-to-end execution of this package on the Python version it has declared as its floor since Phase 1"
affects:
  - "04-05: `_pr_triggered_privilege` already enforces the publish workflow's privilege boundary across every file in `.github/workflows/`; `prune .github` and SANDBOX_CONTENTS already cover the directory"
  - "04-06 / Dan: the first live run of this workflow is the first pull request"

tech-stack:
  added:
    - "actions/checkout v7.0.1 @ 3d3c42e5aac5ba805825da76410c181273ba90b1 (MIT, GitHub first-party)"
    - "actions/setup-python v7.0.0 @ 5fda3b95a4ea91299a34e894583c3862153e4b97 (MIT, GitHub first-party)"
  patterns:
    - "CI delegates to the Makefile: one make invocation, one target, so there stays one definition of the check order and one of the verdict"
    - "Two named views of a config file — comment-stripped for forbidden-string rules, raw for the one rule that needs a trailing comment — because the file's own decision record names what it forbids"
    - "A privilege boundary stated as a rule over every file in a directory, exercised against a synthetic instance of the file the NEXT plan will write"

key-files:
  created:
    - .github/workflows/ci.yml
    - tests/test_ci_workflow.py
  modified:
    - MANIFEST.in
    - scripts/mutation_check.py

key-decisions:
  - "One step, not five. A workflow re-listing pytest, mypy and ruff would be a second definition of the order and of the verdict, free to drift from the one a maintainer runs"
  - "`runs-on: ubuntu-24.04`, not `ubuntu-latest` — same reasoning as 04-03's `ruff<0.17` ceiling, one layer out"
  - "No caching at all, including `setup-python`'s `cache:` input: the saving is seconds against a measured 1 m 05 s check, and a cache restore is unreviewed content the following steps execute"
  - "The identity guard printing a leaked value into a public run log is ACCEPTED with limits, not suppressed — a guard whose output is hidden is not a guard, and CI only ever sees already-pushed commits"
  - "`_documented_ci_target` fails rather than skips when README stops naming a CI entry point"

requirements-completed: [REQ-10]

metrics:
  duration: ~80m
  completed: 2026-08-05
  tasks: 3
  commits: 2
  tests_before: 462
  tests_after: 506
---

# Phase 04 Plan 04: CI — Summary

**This repository now has a pull-request gate whose verdict is `make verify-offline`'s exit
code and whose every value is a recorded decision; the Python floor it has declared since
Phase 1 has actually run its checks for the first time; and the workflow's contract is
machine-checked by 44 tests, 26 of which have been watched failing.**

## Task commits

| Task | Commit | What |
|---|---|---|
| 1 — rehearse the floor | *(no file written — the tree ran clean on 3.10 first time)* | |
| 2 — the workflow and its two consequences | `e3aeca5` (feat) | `.github/workflows/ci.yml`, `prune .github`, `.github` in `SANDBOX_CONTENTS` |
| 3 — the gate | `a776a3d` (test) | `tests/test_ci_workflow.py` |

---

## Task 1 — the declared floor, executed

`requires-python = ">=3.10"` and `[tool.mypy] python_version = "3.10"` have been claims since
Phase 1, verified against nothing: this box's `.venv` is Python 3.12.3 and no 3.10 exists
here. It does now, in a container, and the whole CI job was rehearsed inside it before a line
of YAML was written.

| Measurement | Value |
|---|---|
| Image | `python:3.10`, digest `sha256:c4015e4e509b1aae50f742d32798ab65b8d08863305f61da5a0b0072d0070348` |
| Interpreter | **Python 3.10.20** |
| `make --version` | **GNU Make 4.4.1** (present in the image; nothing installed) |
| `git --version` | **git version 2.47.3** (present in the image; nothing installed) |
| Clone depth | `git rev-list --count HEAD` = **1** — genuinely shallow, via the `file://` form |
| Tracked files in the shallow clone | **146**, identical to the host |
| `identity_check.py --all` in the shallow clone | `identity check: PASS — 145 file(s), no host identity found` |
| `identity_check.py --all` on the host | `identity check: PASS — 145 file(s), no host identity found` |
| **Equality asserted** | **host = 145, shallow clone = 145** |
| Wall clock, whole container run | **128 s** (2 m 08 s), including image-less clone, venv, install, and the full check |

Verdict line, verbatim, from inside the container on Python 3.10:

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

and the stages it ran, also from inside the container:

```
=== verify: identity, lint, tests, types, fixtures, controls, mutation ===
identity check: PASS — 145 file(s), no host identity found
All checks passed!
462 passed in 10.52s
Success: no issues found in 17 source files
control check: SKIPPED (--offline) — no live retailer request made.
mutation check: 8/8 mutations caught
```

### No Python 3.10 incompatibility was found. The tree ran clean on the floor, first time.

No source or test file was changed by this task, so it produced no commit. `python-version`
was **not** raised; `QUESTIONS.md` was not touched, because there was no finding to record.

### The install on 3.10, resolved

`.venv/bin/pip install -e '.[dev]'` completed with **zero warnings, zero deprecations and
zero metadata errors** — `grep -niE 'warn|deprecat|error'` over the whole container log
returned nothing. That is the specific thing the plan asked to watch for, since 04-02 raised
`[build-system] requires` to `setuptools>=77` and the pip bundled with 3.10 is older than
this box's.

The full resolved set (`pip freeze`, 29 entries):

```
apprise==1.12.0          ast_serialize==0.6.0     certifi==2026.7.22
cffi==2.1.1              charset-normalizer==3.4.9 click==8.4.2
curl_cffi==0.16.0        exceptiongroup==1.3.1    idna==3.18
iniconfig==2.3.0         librt==0.13.0            Markdown==3.10.3
mypy==2.3.0              mypy_extensions==1.1.0   oauthlib==3.3.1
packaging==26.3          pathspec==1.1.1          pluggy==1.6.0
pycparser==3.0           Pygments==2.20.0         pytest==9.1.1
PyYAML==6.0.3            requests==2.34.2         requests-oauthlib==2.0.0
ruff==0.16.1             tomli==2.4.1             typing_extensions==4.16.0
urllib3==2.7.0           -e git+file:///repo@6b9a2121ffb771f803ff0569b45f444525b56b63#egg=bot_y
```

Two things worth noting from that list. `tomli==2.4.1` is present on 3.10 as a transitive of
mypy — it is **not** `tomllib`, and nothing in this repo imports either; 04-02's and this
plan's hand-written `[project]`-table reader is still what reads `pyproject.toml`. And
`ruff==0.16.1` resolved identically to the host, inside 04-03's `>=0.16,<0.17` ceiling, so the
lint CI runs is the lint a maintainer runs.

### One deviation in the rehearsal command

The plan's verify command runs `git config --global --add safe.directory /repo`. That is not
sufficient for a `file://` clone from a read-only host mount: git rejects the repository at
`/repo/.git`, not at `/repo`, and the clone dies with

```
fatal: detected dubious ownership in repository at '/repo/.git'
```

Adding `--add safe.directory /repo/.git` as a second line fixed it. This is an artifact of
rehearsing through a bind mount owned by a different uid; `actions/checkout` clones as the
runner user into its own workspace and never meets it. Recorded because the plan's literal
command does not work as written.

---

## Task 2 — the workflow

`.github/workflows/ci.yml`, 186 lines, of which the majority is the decision-record comment
block this repo's files carry. Every value below is asserted by a test in Task 3.

| Decision | Value | Recorded reason |
|---|---|---|
| Target | `make verify-offline`, once | `verify` reaches six retailers live; GitHub IP ranges × PR frequency is the trade `docs/retailer-evidence.md` argues against |
| Steps | **four**, one of which is the check | The Makefile header, quoted in the file: one definition of the order, one of the verdict |
| Triggers | `pull_request` (no filter at all) + `push: branches: [main]` | REQ-10 says *every* PR; the leak that mattered most here was in a `.planning/` markdown file, so a docs-only PR is the one whose `identity` stage matters most |
| `pull_request_target` | absent, named only in the comment explaining its absence | Runs the base repo's workflow with a write token and its secrets against author-controlled code |
| `permissions` | `contents: read`, workflow level, no job block | Stated accurately: for a fork PR GitHub already forces read-only, so this is what protects `push: main` and in-repo branches |
| `concurrency` | group by workflow+ref, `cancel-in-progress` only for PRs | A cancelled `main` run leaves the commit everything downstream trusts with no verdict |
| `runs-on` | `ubuntu-24.04` | Same reasoning as 04-03's `ruff<0.17` ceiling, one layer out |
| `timeout-minutes` | **15** | Measured: 1 m 05 s on this box (04-03), 2 m 08 s cold in the container (Task 1). Default is six hours |
| `actions/checkout` | `@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`, default `fetch-depth` | Task 1's 145 = 145 measurement is in the comment beside it, with the instruction not to "fix" it to `fetch-depth: 0` |
| `actions/setup-python` | `@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0`, `python-version: "3.10"` quoted | Unquoted it is the float `3.1` |
| Install | `python -m venv .venv` then `.venv/bin/pip install -e '.[dev]'` | The exact two lines `check-venv` prints; `.[browser]` never, AGPL-3.0 vs MIT, recorded 2026-08-02 |
| Caching | none, including `setup-python`'s `cache:` input | Seconds of saving against unreviewed content the following steps execute |

### The action SHAs, resolved rather than guessed

`git ls-remote https://github.com/actions/checkout 'refs/tags/v*'`, tail:

```
1af3b93b6815bc44a9784bd300feb67ff0d1eeb3	refs/tags/v6.0.0
8e8c483db84b4bee98b60c0593521ed34d9990e8	refs/tags/v6.0.1
de0fac2e4500dabe0009e67214ff5f5447ce83dd	refs/tags/v6.0.2
9f698171ed81b15d1823a05fc7211befd50c8ae0	refs/tags/v6.0.3
df4cb1c069e1874edd31b4311f1884172cec0e10	refs/tags/v6.0.3^{}
d23441a48e516b6c34aea4fa41551a30e30af803	refs/tags/v6.1.0
3d3c42e5aac5ba805825da76410c181273ba90b1	refs/tags/v7
9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0	refs/tags/v7.0.0
3d3c42e5aac5ba805825da76410c181273ba90b1	refs/tags/v7.0.1
```

`git ls-remote https://github.com/actions/setup-python 'refs/tags/v*'`, tail:

```
a309ff8b426b58ec0e2a45f0f869d46889d02405	refs/tags/v6.2.0
ece7cb06caefa5fff74198d8649806c4678c61a1	refs/tags/v6.3.0
5fda3b95a4ea91299a34e894583c3862153e4b97	refs/tags/v7
5fda3b95a4ea91299a34e894583c3862153e4b97	refs/tags/v7.0.0
```

| Action | Tag | Commit SHA | Commit date (GitHub API) |
|---|---|---|---|
| `actions/checkout` | `v7.0.1` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | **2026-07-17T18:45:11Z** |
| `actions/setup-python` | `v7.0.0` | `5fda3b95a4ea91299a34e894583c3862153e4b97` | **2026-07-20T03:02:03Z** |

Both v7 tags are **lightweight** — no `^{}` dereference line appears for either, and
`GET /repos/{owner}/{repo}/commits/{sha}` resolves both directly — so the listed object *is*
the commit SHA. `v6.0.3` is shown above precisely because it *is* annotated and carries a
`^{}` line; that is the case the plan warned about, and it is not the case we took.

These SHAs are a snapshot of what those tags pointed at on **2026-08-04**. That snapshot is
the security property. The test asserts the *shape* — first-party owner, 40-hex lowercase ref,
trailing version comment — and deliberately not the literal SHA, which would be a second
definition free to drift from the workflow.

### 04-02's prune-coverage gate, observed RED then GREEN on `.github`

This is the first new top-level directory in this repo since that rule landed. With the
workflow staged and no `prune` line yet:

```
E       AssertionError: these tracked top-level directories have no `prune` line in
        MANIFEST.in: ['.github']. `[tool.setuptools.packages.find]` governs the WHEEL
        only, so without a line here they are candidates for the published sdist. Add
        `prune <dir>` if it should not ship.
E       assert not ['.github']

tests/test_packaging_metadata.py:463: AssertionError
1 failed, 18 passed in 0.06s
```

After adding `prune .github` in the file's existing order and style, with a comment paragraph
in the register of its neighbours (and the block's "the other **seven** are guards" count
corrected to **eight**):

```
19 passed in 0.05s
```

### `SANDBOX_CONTENTS`, and the entry watched being load-bearing

`.github` was added to the tuple in the same commit as the workflow it names, because
`build_sandbox()` raises `HarnessError` for an entry with no file behind it. The comment block
gained a paragraph naming `tests/test_ci_workflow.py` and the failure it prevents.

That claim was not left as a claim. With `".github"` temporarily removed from the tuple,
`scripts/mutation_check.py` exited **2**:

```
mutation check: HARNESS ERROR
baseline FAILED in the unmutated sandbox (pytest exit 1: tests failed).
E  FileNotFoundError: [Errno 2] No such file or directory:
   '/tmp/boty-mutation-s4ght9jt/.github/workflows/ci.yml'
```

restored byte-identical afterwards (`git diff --quiet` clean). Exactly the failure measured
fact 7 predicted: a missing file reading as a caught mutation, killing `make verify` for a
reason with nothing to do with CI.

### Diffstat for the two one-line consequences

```
 .github/workflows/ci.yml  | 186 ++++++++++
 MANIFEST.in               |   9 +-
 scripts/mutation_check.py |  13 +-
 tests/test_ci_workflow.py | 905 ++++++++++++++++++++++++++++++++++++++++++++++
 4 files changed, 1111 insertions(+), 2 deletions(-)
```

`MANIFEST.in`: **one** added `prune .github` line plus a six-line comment, and one word
changed (`seven` → `eight`). `scripts/mutation_check.py`: **one** tuple entry plus an
eleven-line comment paragraph; the two "deletions" are the tuple's last line and the count
word being rewrapped. Neither tuple nor comment block was restructured.

`git diff --name-only -- README.md pyproject.toml Makefile` is **empty**. Nothing outside this
plan's four files moved.

---

## Task 3 — the gate

`tests/test_ci_workflow.py`, **905 lines, 44 tests collected, 26 of them corruption tests**,
built in the shape of `tests/test_support_matrix.py`: rules as pure functions, the shipped
file asserted against them, the identical functions run against deliberately broken copies.

### The two views, and the comment quoted verbatim

```python
def _raw() -> str:
    """The workflow exactly as written, comments and all.

    Used by ONE rule — `_action_pins` — which needs the trailing version comment
    beside each SHA pin. Every forbidden-string rule reads `_code` instead. See
    the module docstring: this file's subject names the constructs it forbids in
    order to explain their absence, so a rule reading this view would match the
    documentation and could never fail.
    """
```

`_code(text)` strips YAML comments quote-awarely — a `#` opens a comment only at the start of
a line or after whitespace, which is why the position test is in `_strip_yaml_comment` rather
than a bare `split("#")`.

### The rule inventory

| Rule | Reads | Watched failing by |
|---|---|---|
| `_triggers` | parsed workflow | `test_a_workflow_with_no_trigger_block_raises_rather_than_reporting_nothing` (raises `NoTriggerBlock`) |
| `_unfiltered_pull_request` | trigger mapping | `test_a_paths_ignore_filter_on_the_trigger_is_reported`, `test_a_branch_filter_on_the_trigger_is_reported_too` |
| `_push_branches` | trigger mapping | shipped-file only (`== ["main"]`) |
| `_permission_grants` | parsed workflow | the three grant tests below |
| `_write_grants` | flattened grants | `test_a_workflow_level_write_grant_is_reported`, `test_a_job_that_widens_the_workflow_grant_is_reported`, `test_an_id_token_grant_is_reported_even_though_ci_needs_no_secret` |
| `_run_blocks` | parsed workflow | via `_make_targets` / `_expression_interpolations` |
| `_make_targets` | parsed workflow | `test_switching_ci_to_the_live_verify_target_is_reported` |
| `_expression_interpolations` | parsed workflow | `test_an_expression_inside_a_run_block_is_reported` |
| `_flattening` | comment-stripped text | `test_a_continue_on_error_key_is_reported`, `..._an_or_true_...`, `..._piping_the_check_through_tee_...`, `..._set_plus_e_and_an_unconditional_exit_zero_...`, `..._a_no_op_semicolon_true_...` |
| `_action_pins` | **raw** text | via `_unpinned_actions` |
| `_unpinned_actions` | pin tuples | `test_a_tag_pinned_action_is_reported`, `test_a_third_party_action_with_a_perfectly_good_sha_is_reported`, `test_a_sha_pin_with_no_version_comment_is_reported` |
| `_python_versions` | parsed workflow | `test_an_unquoted_python_version_is_the_float_three_point_one` |
| `_cache_uses` | parsed workflow | `test_a_cache_input_on_setup_python_is_reported` |
| `_floating_runners` | parsed workflow | `test_a_floating_runner_image_is_reported` |
| `_pr_triggered_privilege` | `{filename: text}` | `test_a_pull_request_target_trigger_is_reported_across_the_directory`, `test_a_pull_request_triggered_workflow_holding_privilege_is_reported`, and both publish-workflow boundary tests |
| `_declared_floor` | `pyproject.toml` text | `test_a_python_version_that_disagrees_with_the_declared_floor_is_reported` |
| `_mypy_python_version` | `pyproject.toml` text | shipped-file only (asserted equal to `_declared_floor`) |
| `_documented_ci_target` | README text | `test_a_readme_that_stops_documenting_a_ci_entry_point_reports_nothing` |
| `_code` / `_strip_yaml_comment` | text | `test_the_shipped_comments_name_the_constructs_the_rules_forbid` (direction 1) + every `_flattening` corruption (direction 2) |

**No rule function reads a file**, and that is asserted rather than promised:
`test_no_rule_function_in_this_file_reads_a_file` parses this file with `ast` and fails if any
name in the `RULES` tuple calls `.read_text()`, `.open()`, `.read_bytes()` or `.iterdir()`.

### The `pyproject.toml` reader actually reused

**`_project_table` and `_string`, from `tests/test_packaging_metadata.py`**, loaded by
`importlib.util.spec_from_file_location` under the module name `packaging_metadata_for_ci` —
the same idiom `tests/test_support_matrix.py` uses for `scripts/evidence_check.py`. **No
second TOML parser was written.** `_mypy_python_version` needed one addition, because
`_project_table` reads the `[project]` table only and `python_version` lives in `[tool.mypy]`
one table along; it is a nine-line section scan built out of that module's own
`_strip_comment` and `_string`, with the reason in its docstring. `tomllib` is not imported,
asserted over this file's import statements with `ast` rather than over its text — because the
docstring has to *name* `tomllib` to explain why it is absent, which is the same collision the
two views of the workflow exist for.

### Both directions of the comment-stripping property

Direction one, `test_the_shipped_comments_name_the_constructs_the_rules_forbid`: the raw file
must contain `pull_request_target`, `continue-on-error`, `make verify` **and** `|| true`; the
comment-stripped view must contain none of the first two; `_flattening` must return `[]`; and
`_make_targets` must return exactly `["verify-offline"]` even though the string `make verify`
is present twice over — once in a comment, once as a prefix of the real target.

Direction two: every `_flattening` corruption test inserts the identical construct as YAML and
asserts it is reported.

### The 04-05 privilege boundary, exercised in both directions

`PUBLISH_WORKFLOW` is a synthetic tag-triggered publish workflow holding `id-token: write` for
PyPI Trusted Publishing — the shape 04-05 is about to write.

- `test_the_publish_workflow_04_05_will_write_passes_while_no_pr_can_start_it` → `[]`.
- `test_the_same_publish_workflow_is_reported_the_moment_a_pr_can_start_it` → exactly
  `["release.yml: pull-request-triggerable and grants id-token: write (job:pypi)"]`.

The rule enumerates **every** `*.yml`/`*.yaml` in `.github/workflows/`, so 04-05 inherits a red
test rather than a paragraph.

### The gate watched failing against the real file

**Breakage 1 — `make verify-offline` → `make verify` (sed over the whole file):**
`9 failed, 35 passed`, exit 1. Headline assertion, verbatim:

```
E  AssertionError: CI invokes make targets ['verify']. The bare `verify` target makes live
   requests to six retailers; from GitHub's IP ranges at pull-request frequency that is
   exactly the trade docs/retailer-evidence.md argues against.
E  assert ['verify'] == ['verify-offline']
E    At index 0 diff: 'verify' != 'verify-offline'
```

**Breakage 2 — `.[dev]` → `.[browser]`:** `2 failed, 42 passed`, exit 1:

```
E  AssertionError: assert '[browser]' not in '\n\n\n\n\n\...rify-offline'
E    '[browser]' is contained here:
E      tall -e '.[browser]'
```

**Restored, both times:** `44 passed`, and `git diff --quiet -- .github/workflows/ci.yml`
clean — the workflow came back **byte-identical** to the committed one.

**A bonus worth recording, and it is 04-02's again.** Both breakages also reddened corruption
tests through `_corrupt`'s own anchor assertion:

```
E  AssertionError: expected exactly one 'run: make verify-offline' in the real workflow,
   found 0 — the shipped file moved out from under this test
```

That is the corruption harness refusing to corrupt nothing. A corruption test that silently
edits nothing asserts only that the rule passes on a healthy tree, which the shipped-file
tests already cover.

---

## Verification

| Check | Result |
|---|---|
| `pytest tests/test_ci_workflow.py -q` | **44 passed** (26 corruption tests) |
| Observed red: `make verify` | **9 failed, 35 passed**, restored byte-identical |
| Observed red: `.[browser]` | **2 failed, 42 passed**, restored byte-identical |
| `make lint` | exits 0, `All checks passed!` — **no new `# noqa`** |
| `pytest tests/ -q` | **506 passed** (pre-plan **462**; +44, none lost) |
| `mypy` | `Success: no issues found in 17 source files` |
| `scripts/mutation_check.py` | **8/8 mutations caught**, no `HarnessError` |
| Mutation sandbox baseline | **506 passed** — the new gate genuinely runs inside the sandbox |
| `pytest tests/test_packaging_metadata.py -q` | **19 passed** |
| `identity_check.py --all` | `PASS — 146 file(s), no host identity found` |
| `make verify-offline` | exits 0, **1 m 38 s** wall clock |
| `git status --porcelain` | **empty** — no stray backup of the workflow |
| `git diff --name-only -- README.md pyproject.toml Makefile` | **empty** |

Verdict line, verbatim:

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

`make verify` was **deliberately not run**: this plan changes no retailer code, and spending
the politeness budget on six live requests to prove a YAML file is correct is precisely the
trade this plan exists to avoid making at PR frequency. `make verify` remains the phase gate,
run once at phase close.

---

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 — blocking] The plan's rehearsal command could not clone from the read-only mount**

- **Found during:** Task 1, first container run
- **Issue:** `git config --global --add safe.directory /repo` is not enough for a `file://`
  clone of a bind-mounted repository owned by a different uid. Git rejects `/repo/.git`:
  `fatal: detected dubious ownership in repository at '/repo/.git'`, and the clone exits 128
  with an empty log.
- **Fix:** a second `--add safe.directory /repo/.git`. Nothing about the workflow changed —
  `actions/checkout` clones as the runner user into its own workspace and never meets this.
- **Commit:** none (Task 1 wrote no file)

**2. [Rule 1 — bug in this plan's own new test] `test_this_file_does_not_import_tomllib` asserted over text**

- **Found during:** Task 3, first run of the new file
- **Issue:** the test grepped its own source for `tomllib`, and this file's docstring has to
  *name* `tomllib` in the section explaining why it is not imported. The test failed on its own
  documentation — the exact defect the two views of the workflow exist to prevent, reproduced
  one level up.
- **Fix:** rewritten to walk `ast.Import` / `ast.ImportFrom` nodes, so it asserts the import
  statements rather than the prose. Docstring extended to say why.
- **Commit:** `a776a3d`

**3. [Rule 2 — missing critical documentation] `MANIFEST.in`'s guard count was stale on arrival**

- **Found during:** Task 2, adding `prune .github`
- **Issue:** the comment block reads "Only `prune tests` removes anything today. The other
  **seven** are guards" — adding an eighth guard without touching that sentence would leave a
  count that a reader checks against the file and finds wrong.
- **Fix:** `seven` → `eight`, in the same edit as the line it counts.
- **Commit:** `e3aeca5`

### Not deviations, but worth stating

- **No new pip/npm/cargo package was introduced.** The only install CI performs is
  `pip install -e '.[dev]'`, audited in 04-02 and 04-03. The two GitHub Actions are the
  third-party surface, and both were resolved with `git ls-remote` and recorded above.
- **`python-version` was never raised** to make anything pass; there was nothing to make pass.
- **No CI badge was added to README.md**, deliberately: a badge asserts a status nobody has
  observed, which is the asserted-but-unimplemented shape this phase exists to close.
- **README.md, pyproject.toml and the Makefile were not opened.**

---

## Known Stubs

None. Every rule in `tests/test_ci_workflow.py` runs against the shipped workflow and against
a corrupted copy of it, and the one rule whose input could go missing (`_triggers`) raises a
named error rather than reporting an empty trigger set.

## Threat Flags

None beyond the plan's own register. This plan adds no network endpoint, no auth path and no
schema change. It does add the repository's first CI surface, which is exactly what
`<threat_model>` T-04-04-01 … T-04-04-12 enumerate; every `mitigate` disposition there is
implemented and asserted by a named test above. **T-04-04-05 remains `accept`**: a red
`identity` stage in CI will print a real value into a public log. Bounded by CI only ever
seeing already-pushed commits, by no `set -x`, no env dump and no context interpolation, and
by `identity` running first so a leak stops the run before anything else prints. The response
to it is rotation and redaction — never deleting the log.

---

## Handoff to 04-05 (the release)

**The privilege boundary, in the form you have to satisfy:**

1. Your publish workflow may hold `id-token: write` (or any `write` grant) **only while no
   pull request can trigger it.** Tag-triggered is fine; adding a `pull_request` trigger to the
   same file makes `tests/test_ci_workflow.py::test_no_workflow_in_this_repo_lets_a_pull_request_reach_privilege`
   go red, naming your file. `pull_request_target` is reported unconditionally, privilege or
   not.
2. That rule enumerates **every** `*.yml`/`*.yaml` in `.github/workflows/` — it is not about
   `ci.yml`. It has already been exercised in both directions against a synthetic
   tag-triggered publish workflow carrying `id-token: write` (`PUBLISH_WORKFLOW` in that file),
   so you are inheriting a test that already knows the shape you are about to write.
3. **`prune .github` and `SANDBOX_CONTENTS` already cover the directory.** A second workflow
   file needs neither. Do not add a second `prune` line and do not touch the tuple.
4. `_action_pins` / `_unpinned_actions` apply only to `ci.yml` today. If your workflow uses
   `pypa/gh-action-pypi-publish`, that is a **third-party** action and the current shipped-file
   test would report it if it were in `ci.yml` — decide deliberately whether to widen the rule
   to your file or to record the exception, in a commit that says which.

---

## Handoff to 04-06 and Dan — the honest part

**No pull request has run this workflow. Not one.** Everything above was measured offline, in
a container, or against text. The first live observation of this workflow is the first pull
request, and nothing here says CI has been seen green on GitHub.

What the first run should print, at the end of the `The verdict` step:

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

**Two things worth checking on that first run that no offline gate could establish:**

1. **That `actions/setup-python` actually provisioned 3.10.** Open the *Provision the
   interpreter this package declares as its floor* step and read the version it resolved. The
   gate asserts the workflow *asks* for the string `"3.10"`; only a real run says what it got.
2. **That the whole job finished inside `timeout-minutes: 15`.** The budget came from 1 m 05 s
   on this box and 2 m 08 s in a cold container. A GitHub runner is a different machine, and
   the `mutation` stage alone builds nine sandboxes — it is the slow part, and 04-02's git
   index made it ~29 s slower on purpose. If the job lands anywhere near the timeout, raise the
   timeout in a commit that records the observed duration; do not remove the sandbox index.

A third, if it ever fires: **a red `identity` stage in CI writes a real value into a public
log.** That is accepted and bounded (see Threat Flags), but the response is rotation and
redaction at the source, not deleting the run.

---

## Self-Check

- `.github/workflows/ci.yml` — FOUND (`make verify-offline` present)
- `tests/test_ci_workflow.py` — FOUND (`yaml.safe_load` present, 905 lines)
- `MANIFEST.in` — FOUND (`prune .github` present)
- `scripts/mutation_check.py` — FOUND (`.github` in `SANDBOX_CONTENTS`, asserted by import)
- Commit `e3aeca5` — FOUND
- Commit `a776a3d` — FOUND

## Self-Check: PASSED

---
*Phase: 04-open-source-ready*
*Completed: 2026-08-05*
