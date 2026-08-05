---
phase: 04-open-source-ready
plan: 05
subsystem: packaging
tags: [req-11, packaging, release, oidc, trusted-publishing, supply-chain, wheel, changelog]

requires:
  - phase: 04-open-source-ready
    plan: 02
    provides: "PEP 639 licence metadata, MANIFEST.in's prune list and the 0.1.0 version this plan bumps; the deferred Development Status classifier and the placeholder Changelog-URL comment"
  - phase: 04-open-source-ready
    plan: 03
    provides: "[tool.ruff] and the `lint` stage, so the new script and the cli.py edit are lint-clean under a committed rule set"
  - phase: 04-open-source-ready
    plan: 04
    provides: "tests/test_ci_workflow.py's 20 rule functions and its cross-workflow privilege rule, applied here rather than re-implemented; `prune .github` and `.github` in SANDBOX_CONTENTS already covering the directory"
provides:
  - "scripts/release_check.py + `make release-check` — ten checks over the BUILT artifacts, the only thing here that can tell `the package builds` from `the package works`"
  - "boty/cli.py's missing-config guard — a fresh install's first command answers instead of raising FileNotFoundError at an unpackaged path"
  - "CHANGELOG.md — the release notes 04-06 hands to a reader, bound to pyproject.toml's version by check 1"
  - ".github/workflows/release.yml — tag-triggered publish over OIDC, two jobs, id-token: write on one, five SHA-pinned actions"
  - "tests/test_ci_workflow.py extended 44 -> 67 tests; TRUSTED_ACTION_OWNERS as an enumerated pin"
  - "README `### From PyPI` — the bot-y / boty name-confusion warning, above the install command"
  - "pyproject.toml at 1.0.0, with the Development Status classifier and the Changelog URL"
affects:
  - "04-06 / Dan: the PyPI trusted-publisher form needs environment `pypi`, workflow filename `release.yml`; the v1.0.0 tag is his to create and push — this plan created none"

tech-stack:
  added:
    - "build (PyPA, MIT, 1.5.0) — ephemeral venv only, in no dependency list or extra"
    - "twine>=6.1 (PyPA, Apache-2.0, 7.0.0) — ephemeral venv only, `twine check` and nothing else"
    - "actions/upload-artifact v7.0.1 @ 043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
    - "actions/download-artifact v8.0.1 @ 3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"
    - "pypa/gh-action-pypi-publish v1.14.2 @ dc37677b2e1c63e2034f94d8a5b11f265b73ba33 (first non-actions/ action in this repo)"
  patterns:
    - "Build isolation as a MEASUREMENT: a venv holding only the build frontend, then a second holding nothing at all, because a venv that already has the runtime deps cannot detect a missing Requires-Dist"
    - "Five statements of one version bound so that bumping any one alone goes red"
    - "One rule, now four callers: identity_check.scan over extracted artifacts reads generated metadata no tracked-file scan has ever seen"
    - "An enumerated owner allow-list widened in the same commit as the workflow that justifies it, never deleted"

key-files:
  created:
    - scripts/release_check.py
    - CHANGELOG.md
    - .github/workflows/release.yml
  modified:
    - boty/cli.py
    - tests/test_cli_watch.py
    - pyproject.toml
    - MANIFEST.in
    - Makefile
    - tests/test_ci_workflow.py
    - README.md

key-decisions:
  - "The wheel test found a real packaging bug and this plan FIXED it rather than filing it — boty check on a clean-venv install raised FileNotFoundError at config/products.yaml, a path only a checkout has"
  - "Packaging a default config was considered and REJECTED in writing: the watches, price ceilings and control products are the operator's decisions, and shipping them publishes this maintainer's list to every installer"
  - "build and twine go into an ephemeral venv, NOT the dev extra — the reason is build isolation as a measurement, not tidiness; a `release` extra was rejected because it publishes a Provides-Extra claim and still builds wherever the caller stands"
  - "release-check is a Makefile target and deliberately NOT a verify stage and NOT a README stage-table row — it needs the network, and a row would break 04-03's stage-agreement test"
  - "Trusted Publishing over OIDC, never an API token in repository secrets: a long-lived token in a public repo is reachable by any future workflow edit and outlives everyone who remembers it"
  - "Two jobs, with the claim stated SMALL: splitting stops build-time code obtaining a mintable token, it does NOT stop a malicious tag publishing a malicious package"
  - "No GitHub Release step: it needs contents: write on the job that already holds an identity, for something the tag and PyPI already record"
  - "Development Status :: 5 - Production/Stable, with `4 - Beta` rejected in writing — tagging 1.0.0 while classifying Beta is the asserted-versus-real disagreement this phase exists to close"
  - "The action-owner rule was WIDENED to TRUSTED_ACTION_OWNERS = (actions, pypa), not deleted; two corruption tests still watch it bite on an owner in neither"
  - "The boty/bot-y name confusion is ACCEPTED with documentation as the only available mitigation — PyPI does not release a name that has files, so the neighbour cannot be defensively claimed"

metrics:
  duration: 22m
  completed: 2026-08-05
  tasks: 3
  commits: 3
  tests_before: 506
  tests_after: 531
---

# Phase 04 Plan 05: The release — Summary

**A wheel built from this tree installs into a venv holding nothing else, runs `boty --help`
with exit 0 from outside the repository and answers `boty check` with a message instead of a
stack trace — all of it measured by a command anyone can re-run, with the two ways it could
quietly stop being true watched making it fail. Nothing was published and no tag exists.**

## Task commits

| Task | Commit | What |
|---|---|---|
| 1 — 1.0.0, the changelog, the fresh install | `542e6a1` (feat) | `boty/cli.py`, `tests/test_cli_watch.py`, `pyproject.toml`, `CHANGELOG.md`, `MANIFEST.in` |
| 2 — the proof | `ca4025b` (feat) | `scripts/release_check.py`, `Makefile` |
| 3 — the publish workflow and its gate | `aa57283` (feat) | `.github/workflows/release.yml`, `tests/test_ci_workflow.py`, `README.md` |

---

## Task 1 — the packaging bug, fixed rather than filed

### The RED, observed before the guard existed

The new test was written first and run against the unfixed tree. It failed with the real
exception, not with an assertion about wording:

```
>       assert cli.main(["check", "-c", str(missing)]) == 2
tests/test_cli_watch.py:422:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
boty/cli.py:404: in main
    cfg = Config.load(args.config)
boty/config.py:140: in load
    raw = _expand(yaml.safe_load(Path(path).read_text()) or {})
...
E       FileNotFoundError: [Errno 2] No such file or directory:
        '/tmp/pytest-of-dan/pytest-1689/test_a_missing_config_file_is_0/nowhere/products.yaml'

1 failed, 1 passed, 16 deselected in 0.08s
```

The "1 passed" is `test_capture_fixture_still_needs_no_config_file`, which pins the early
return above the guard — a decision that had a comment in `main` and nothing under it. It was
green on arrival by design: its job is to stay green after the guard lands.

### The GREEN

```
18 passed in 0.07s
```

### The message the guard prints, verbatim from the installed console script

```
$ .venv/bin/boty check -c /nonexistent/products.yaml   ; echo $?
no config file at '/nonexistent/products.yaml' — there is nothing to watch.
This package ships no default config on purpose: the products, the price ceilings and the control products are yours to choose, not this maintainer's to publish.
Copy the example from https://github.com/danieljamesjohnson/bot-y (config/products.yaml) and point `-c`/`--config` at your copy.
2
```

`boty watch -c <missing>` behaves identically (exit 2), and `boty capture-fixture --help`
still needs no config file. `Traceback` appears in none of it.

Exit **2**, not 1, matching the two neighbours: `no watches configured` returns 2 and
`no notify URLs configured` returns 2. All three mean "you have not configured this yet".

The guard is in `boty/cli.py` § `main`, **not** in `Config.load` — `load` receiving a
nonexistent path is a legitimate programming error for every other caller, and swallowing it
in the loader would hide it from the tests that use it.

### Metadata

| Change | Value |
|---|---|
| `[project] version` | `0.1.0` -> **`1.0.0`** |
| `classifiers[0]` | `Development Status :: 5 - Production/Stable` (alphabetically first, keeping 04-02's sort) |
| `[project.urls] Changelog` | `https://github.com/danieljamesjohnson/bot-y/blob/main/CHANGELOG.md`, replacing 04-02's placeholder comment |
| `MANIFEST.in` | one `include CHANGELOG.md` line, the file's only `include` |

All six of 04-02's load-bearing comment fragments still `grep -F` clean, `[tool.ruff.lint]`
is intact, `[project.optional-dependencies]` still has exactly `dev` and `browser`,
`browser == ["nodriver>=0.38"]`, and neither `build` nor `twine` is in either.

`CHANGELOG.md` is 162 lines, one `## [1.0.0]` heading, one `## [Unreleased]`, and it claims
nowhere that the package is on PyPI — the "Not in this release" section states that 1.0.0 is
the first published release in a tense that is true both before and after 04-06 acts.

---

## Task 2 — `scripts/release_check.py`, and the proof watched failing

### The full run on the healthy tree

```
release check: building pokemongoplusplus in /tmp/boty-release-l7m144l8
  ..    built from 152 tracked file(s), copied to a clean tree
  ..    bot_y-1.0.0.tar.gz  92,839 bytes
  ..    bot_y-1.0.0-py3-none-any.whl  77,831 bytes
  ok    one version, stated five times: pyproject.toml=1.0.0, CHANGELOG.md=1.0.0, wheel filename=1.0.0, wheel METADATA=1.0.0, pip show=1.0.0
  ok    both artifacts built: 1 sdist, 1 wheel in /tmp/boty-release-l7m144l8/dist
  ok    twine check: Checking .../bot_y-1.0.0-py3-none-any.whl: PASSED | Checking .../bot_y-1.0.0.tar.gz: PASSED
  ok    no pruned directory in either artifact: 26 sdist member(s), 19 wheel member(s)
  ok    the files a source release has to carry: LICENSE in both; CHANGELOG.md, README.md, MANIFEST.in, pyproject.toml in the sdist
  ok    the licence reached the wheel: License-Expression: MIT; bot_y-1.0.0.dist-info/licenses/LICENSE
  ok    no host identity in the built artifacts: sdist + wheel extracted and scanned by the same rule `make verify` runs
  ok    the installed console script runs from outside the repo: `boty --help` -> 0; `boty check -c no-such-config.yaml` -> 2
  ok    no forbidden package in a default install: 16 package(s): apprise, bot-y, certifi, cffi, charset-normalizer, click, curl_cffi, idna, markdown, oauthlib, pip, pycparser, pyyaml, requests, requests-oauthlib, urllib3
  ok    the Changelog URL resolves to a file in this repo: https://github.com/danieljamesjohnson/bot-y/blob/main/CHANGELOG.md -> CHANGELOG.md exists
release check: PASSED — 10/10 checks, sdist and wheel proven
```

`twine check` printed **PASSED** for both artifacts. `nodriver` is absent from the install
venv's 16 packages, so a default install pulls no browser stack.

### The observed member lists

**`bot_y-1.0.0-py3-none-any.whl` — 19 members:**

```
bot_y-1.0.0.dist-info/METADATA        boty/config.py     boty/notify.py
bot_y-1.0.0.dist-info/RECORD          boty/fetch.py      boty/pacing.py
bot_y-1.0.0.dist-info/WHEEL           boty/fixtures.py   boty/parse.py
bot_y-1.0.0.dist-info/entry_points.txt boty/models.py    boty/retailers.py
bot_y-1.0.0.dist-info/licenses/LICENSE boty/monitor.py   boty/status.py
bot_y-1.0.0.dist-info/top_level.txt   boty/__init__.py
boty/browser.py                       boty/cli.py
```

**`bot_y-1.0.0.tar.gz` — 26 members (leading `bot_y-1.0.0/` stripped):**

```
CHANGELOG.md   LICENSE   MANIFEST.in   PKG-INFO   README.md   pyproject.toml   setup.cfg
bot_y.egg-info/{PKG-INFO,SOURCES.txt,dependency_links.txt,entry_points.txt,requires.txt,top_level.txt}
boty/{__init__,browser,cli,config,fetch,fixtures,models,monitor,notify,pacing,parse,retailers,status}.py
```

Nothing under `tests/`, `config/`, `docs/`, `scripts/`, `deploy/`, `hooks/`, `served/`,
`.planning/` or `.github/` is in either — including after `release.yml` became tracked, which
is `prune .github` doing its job on a second file.

### RED 1 — a broken `[project.scripts]` entry point

`boty = "boty.cli:main"` -> `boty = "boty.cli:not_main"`, `make release-check`, exit **non-zero**:

```
  ok    the licence reached the wheel: License-Expression: MIT; bot_y-1.0.0.dist-info/licenses/LICENSE
  ok    no host identity in the built artifacts: ...
  FAIL  the installed console script runs from outside the repo: `boty --help` -> 0; `boty check -c no-such-config.yaml` -> 2
        `boty --help` exited 1, expected 0
      ImportError: cannot import name 'not_main' from 'boty.cli' (/tmp/boty-release-el21rz4x/install-venv/lib/python3.12/site-packages/boty/cli.py)
        `boty --help` printed a traceback
        `boty check -c no-such-config.yaml` exited 1, expected 2
      ImportError: cannot import name 'not_main' from 'boty.cli' (...)
        `boty check -c no-such-config.yaml` printed a traceback
release check: FAILED — 1 of 10 checks failed: the installed console script runs from outside the repo
make: *** [Makefile:98: release-check] Error 1
```

Note the path in the ImportError: `install-venv/lib/python3.12/site-packages/boty/cli.py`. The
failure is being observed against the *installed* package, not the checkout.

### RED 2 — a version that disagrees with `CHANGELOG.md`

`version = "1.0.0"` -> `"1.0.1"`, exit **non-zero**, and check 1 is what bit:

```
  ..    bot_y-1.0.1.tar.gz  91,615 bytes
  ..    bot_y-1.0.1-py3-none-any.whl  77,333 bytes
  FAIL  one version, stated five times: pyproject.toml=1.0.1, CHANGELOG.md=1.0.0, wheel filename=1.0.1, wheel METADATA=1.0.1, pip show=1.0.1  <- DISAGREE: {'CHANGELOG.md': '1.0.0'}
release check: FAILED — 1 of 10 checks failed: one version, stated five times
```

Both numbers named, and the four that moved together shown moving together — which is what
tells a reader the binding is real rather than incidental.

### GREEN after each, and the file restored

`git diff --quiet -- pyproject.toml` clean after both. No `dist/` or `build/` directory
was left inside the repository (the script builds into a temp tree and removes it unless
`--keep`), and `.venv` still contains neither `build` nor `twine`.

### The design decision the constraint asked to be recorded

**The build happens in a venv holding only `build` and `twine`, and the wheel installs into a
second venv holding nothing at all.** Building inside `.venv` — which already has `curl_cffi`,
`PyYAML` and `apprise` — **cannot detect a missing or wrong `Requires-Dist`**, because every
import resolves anyway from packages that happen to be lying around. That is the property, and
it is stronger than dependency hygiene. A `release` extra was the alternative and was rejected:
it publishes a `Provides-Extra: release` claim to every installer, it takes the `dev` extra's
own promise ("everything needed to run `make verify`") from three packages to roughly fifteen
(measured: twine's `requires_dist` alone is nine entries), and it still leaves the build
happening wherever the caller happens to be standing.

### `make release-check` is a target, not a stage

`release-check` is in `.PHONY` and in `make help` (below the verify block, visually
separated). The `verify` recipe does not invoke it — asserted programmatically — and there is
**no README stage-table row** for it, because 04-03's
`test_the_documented_stages_are_the_stages_verify_runs` asserts set equality between the
documented rows and the stages `verify` actually invokes. Both reasons are in a comment above
the target.

---

## Task 3 — the publish workflow

`.github/workflows/release.yml`, 166 lines, the majority of it the decision-record comment
block this repo's files carry.

| Decision | Value | Recorded reason |
|---|---|---|
| Trigger | `push: tags: ["v*"]` and nothing else | Four absences, four separate reasons — see below |
| Jobs | **two**: `build`, `publish` | `python -m build` executes the build backend from the tag; it must not sit in the job that can mint a credential |
| Workflow `permissions` | `contents: read` | Least privilege, inherited by `build` |
| `publish` `permissions` | `id-token: write` **and** `contents: read` | A job-level block **replaces** the workflow-level one; dropping the restated read scope is the obvious "simplification" that breaks it |
| `build` `permissions` | none declared, inherits read | The whole security property of the split |
| `environment` | **`pypi`** | A place to attach reviewers later, and PyPI's form scopes the grant by it |
| GitHub Release | **not created** | Needs `contents: write` on the job that already holds an identity, for what the tag and PyPI already record |
| `runs-on` / `timeout-minutes` | `ubuntu-24.04` / 15, both jobs | Same reasoning as `ci.yml` |
| Python | `"3.10"`, quoted | Unquoted it is the float `3.1` (04-04's measurement); building on the declared floor |

**The four refusals, each with its own reason:** `pull_request` and `pull_request_target`
because this file holds `id-token: write` and a fork's code must never run in a job that can
mint a PyPI credential; `workflow_dispatch` for a *record-keeping* reason rather than a
security one — a dispatch run publishes from whatever ref the operator picked in a web form
and leaves no permanent name for what was published, while a tag outlives the run log (a
mis-tagged release is fixed by yanking on PyPI and tagging again, never by re-running with
different inputs); and the `release` event because it puts a mouse click between the tag and
the artifact.

**The two-job claim is stated small, deliberately.** Splitting stops build-time code from
obtaining a token usable elsewhere. It does **not** stop a malicious tag from publishing a
malicious package — nothing in a workflow can, since whoever can push a `v*` tag here can
publish. Writing the smaller claim down is what keeps the control understood.

### The action SHAs, resolved rather than copied

`git ls-remote` at execution time, 2026-08-05:

```
=== actions/checkout ===
3d3c42e5aac5ba805825da76410c181273ba90b1	refs/tags/v7
9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0	refs/tags/v7.0.0
3d3c42e5aac5ba805825da76410c181273ba90b1	refs/tags/v7.0.1
=== actions/setup-python ===
5fda3b95a4ea91299a34e894583c3862153e4b97	refs/tags/v7
5fda3b95a4ea91299a34e894583c3862153e4b97	refs/tags/v7.0.0
=== actions/upload-artifact ===
b7c566a772e6b6bfb58ed0dc250532a479d7789f	refs/tags/v6.0.0
043fb46d1a93c77aae656e7c1c64a875d1fc6a0a	refs/tags/v7
bbbca2ddaa5d8feaa63e36b76fdaad77386f024f	refs/tags/v7.0.0
043fb46d1a93c77aae656e7c1c64a875d1fc6a0a	refs/tags/v7.0.1
=== actions/download-artifact ===
37930b1c2abaa49bbe596cd826c3c89aef350131	refs/tags/v7.0.0
3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c	refs/tags/v8
70fc10c6e5e1ce46ad2ea6f2b72d43f7d47b13c3	refs/tags/v8.0.0
3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c	refs/tags/v8.0.1
=== pypa/gh-action-pypi-publish ===
a892a5a61159132606e93a2fa6f4358831b04d26	refs/tags/v1.14.2
dc37677b2e1c63e2034f94d8a5b11f265b73ba33	refs/tags/v1.14.2^{}
```

| Action | Tag | Commit SHA | Commit date (GitHub API) |
|---|---|---|---|
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` | 2026-07-17T18:45:11Z |
| `actions/setup-python` | v7.0.0 | `5fda3b95a4ea91299a34e894583c3862153e4b97` | 2026-07-20T03:02:03Z |
| `actions/upload-artifact` | v7.0.1 | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | 2026-04-10T16:08:32Z |
| `actions/download-artifact` | v8.0.1 | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` | 2026-03-11T15:35:54Z |
| `pypa/gh-action-pypi-publish` | v1.14.2 | `dc37677b2e1c63e2034f94d8a5b11f265b73ba33` | 2026-07-28T18:38:00Z |

**`pypa/gh-action-pypi-publish`'s tags are ANNOTATED** — every one carries a `^{}`
dereference line, and the pinned SHA is the dereferenced commit, not the tag object. The
`actions/*` v7/v8 tags are lightweight, so the listed object *is* the commit. That distinction
is exactly what measured fact 11 warned about, and it was checked rather than assumed.

### The reused helpers — no second parser was written

Every rule applied to `release.yml` is 04-04's, called unchanged:

`_code` / `_strip_yaml_comment` (the two views), `_triggers`, `_jobs`, `_steps`,
`_permission_grants`, `_write_grants`, `_run_blocks`, `_expression_interpolations`,
`_flattening`, `_action_pins`, `_unpinned_actions`, `_python_versions`, `_cache_uses`,
`_floating_runners`, `_pr_triggered_privilege`, `_declared_floor`.

**No second YAML reader and no second permission flattener.** The new section lives in
`tests/test_ci_workflow.py` rather than a sibling file, with a header comment saying why:
there is one definition in this repository of what a workflow may be, and a second file would
be a second definition free to drift from it — about the file that holds the only privilege
here. Two new helpers were added and neither is a rule: `_release_raw()` / `_release()` (the
subject) and `_publish_job()` (which job holds `id-token`).

`PUBLISH_WORKFLOW`, 04-04's synthetic stand-in, was **left in place**: it keeps doing a job the
real file cannot, asserting the boundary against text nobody is tempted to fix.

### The widened allow-list, in the form it actually took

```python
TRUSTED_ACTION_OWNERS = ("actions", "pypa")
```

carrying a `#:` comment block in the `UNREAD_POSITIONS` idiom that names it a **pin, not a
rule**, states that widening it is a deliberate edit to a red test made in the same commit as
the workflow that justifies it, and names what backs each entry — for `pypa`: it already
publishes `setuptools`, which `[build-system] requires` **executes** on every build of this
project, plus `build` and `twine`, which `scripts/release_check.py` runs; and the alternative
is hand-rolling the OIDC exchange in a shell step, i.e. unreviewed credential-handling code in
the one job that holds an identity.

`_unpinned_actions` now reads that constant instead of a hard-coded `actions/` prefix. It was
**widened, not deleted**, and two corruption tests still watch it bite:
`test_a_third_party_action_with_a_perfectly_good_sha_is_reported` (`tj-actions/changed-files`,
against `ci.yml`) and the new `test_a_third_party_owner_in_the_publish_workflow_is_reported`
(`some-vendor/publish-to-pypi` with a perfectly valid 40-hex SHA, against `release.yml`). Both
now expect the new message naming the allow-list.

### The gate watched failing against the real `release.yml`

A `pull_request:` trigger spliced into the shipped file. **7 failed, 60 passed**, exit 1. The
headline assertion, verbatim:

```
E       AssertionError: ['release.yml: pull-request-triggerable and grants id-token: write (job:publish)']
E       assert ['release.yml...job:publish)'] == []
E         Left contains one more item: 'release.yml: pull-request-triggerable and grants id-token: write (job:publish)'
```

and, from the trigger-set rule:

```
E       AssertionError: the publish workflow's triggers are ['pull_request', 'push']. It holds
        id-token: write, so the only thing that may start it is a tag push.
E       assert {'pull_request', 'push'} == {'push'}
```

Three of the seven failures are the corruption harness refusing to corrupt nothing — the same
bonus 04-04 recorded:

```
E       AssertionError: expected exactly one 'on:\n  push:\n' in the real publish workflow,
        found 0 — the shipped file moved out from under this test
```

**Restored: 67 passed, and `git diff --quiet -- .github/workflows/release.yml` clean against
the staged file** — byte-identical.

### Corruption coverage for `release.yml` — nine tests

| Test | Rule it exercises |
|---|---|
| `test_a_pull_request_trigger_on_the_publish_workflow_is_reported` | `_pr_triggered_privilege` — the most important assertion here |
| `test_a_pull_request_target_trigger_on_the_publish_workflow_is_reported` | `_pr_triggered_privilege`, unconditional branch |
| `test_a_workflow_dispatch_trigger_on_the_publish_workflow_is_visible` | `_triggers` (proves the trigger-set assertion is not vacuous) |
| `test_moving_the_id_token_grant_to_the_workflow_level_is_reported` | `_permission_grants` + `_write_grants` |
| `test_a_contents_write_grant_on_the_publish_workflow_is_reported` | `_write_grants` |
| `test_a_tag_pinned_publisher_is_reported` | `_unpinned_actions` (SHA branch) |
| `test_a_third_party_owner_in_the_publish_workflow_is_reported` | `_unpinned_actions` (owner branch, post-widening) |
| `test_an_expression_in_a_publish_workflow_run_block_is_reported` | `_expression_interpolations` |
| `test_removing_the_environment_from_the_publish_job_is_reported` | the environment assertion |

Plus 14 shipped-file tests over `release.yml`, including one asserting that **no `run:` block
in any workflow in the directory invokes twine or `gh release`** — publishing goes through the
pinned action, never a hand-written shell line.

### README

`### From PyPI` inserted above `### From a clone`, inside `## Install`, +28 lines, free prose,
no tables. It names the distribution `bot-y`, states that `boty` is a different PyPI package,
gives the measurement (0.1.1, "Time Flies", Bart Thate, googlecode homepage, last released
**2012-03-10**), says plainly that the neighbouring name cannot be defensively claimed because
PyPI does not release a name that has files, then the fenced `pip install bot-y`, then the
tense sentence that needs no maintenance:

> Publication happens from the `v1.0.0` tag. If that command reports no matching
> distribution, the tag has not been pushed yet and the clone below is the way in.

`git diff -U0 -- README.md` contains **zero** changed lines beginning with `| ` — no table row
moved. `grep -c '^| Retailer | Rung | Extraction |'` is exactly `1`. The three clone lines are
byte-identical. No fenced block added here carries a comment mentioning CI, so 04-04's
`_documented_ci_target` locator stays unambiguous.

---

## The open audit obligation, closed

Planning left three PyPI neighbours of `build`/`twine` returning HTTP 200 and unidentified.
Resolved against the JSON API on 2026-08-05:

| Name | What it actually is |
|---|---|
| `twin` | **0.0.1, Brandon Hoffman, no summary, no licence — and zero uploaded files**, so it cannot be installed at all. A reserved name, not a package. |
| `python-build` | **0.2.13, Colm O'Connor, MIT, "Tool to download and build python based upon pyenv"**, 21 releases, first 2015-07-06, last in the 2015 series. A pyenv wrapper, unrelated to the PEP 517 frontend. |
| `py-build` | **0.2.0, Cory Laughlin, github.com/Aesonus/py-build, "A package that can be used to create a build process"**, 2 releases, 2021-02-23 and 2021-02-28. |

None is PyPA-published, none is a build frontend, and none is installed here — the install
lines name `build` and `twine` exactly. Recorded because leaving an unresolved 200 unrecorded
is how a neighbour stops being watched.

The twine floor's measurement is recorded beside the constant: twine **5.1.1 rejects** this
project's `Metadata-Version: 2.4` wheel with `InvalidDistribution: Metadata is missing
required fields: Name, Version`; **6.0.1 passes**; **7.0.0 passes**. The pin is `twine>=6.1` —
04-02's number, the stricter of the two, kept deliberately rather than relaxed to the measured
6.0.1.

---

## `boty/fixtures.py` was measured and deliberately not touched

`_default_root()` returns `_REPO_ROOT / "tests" / "fixtures"` only when
`<parent>/pyproject.toml` is a file, and falls back to the plain relative
`Path("tests/fixtures")` otherwise — with a docstring saying so. On a wheel install the
fallback is taken, nothing raises at import, and `capture-fixture` writes cwd-relative. The
release check runs `boty --help` and `boty check` on exactly that install and neither trips it.
**This is not a bug and must not be "fixed".** Recorded so nobody fixes a non-bug while
looking at the real one next door.

---

## Verification

| Check | Result |
|---|---|
| `pytest tests/ -q` | **531 passed** (pre-plan **506**; +2 Task 1, +23 Task 3, none lost) |
| `pytest tests/test_ci_workflow.py -q` | **67 passed** (04-04 left it at 44) |
| Observed red: PR trigger on the real `release.yml` | **7 failed, 60 passed**; restored byte-identical |
| Observed red: broken `[project.scripts]` | `release check: FAILED`, smoke check named; `pyproject.toml` restored |
| Observed red: version drift vs `CHANGELOG.md` | `release check: FAILED`, check 1 named with both numbers; restored |
| Observed red: `test_a_missing_config_file_...` | `FileNotFoundError` in the captured output, then 18 passed |
| `make lint` | exits 0, `All checks passed!` — **no new `# noqa`** |
| `mypy` | `Success: no issues found in 18 source files` (was 17; `release_check.py` is inside `files`) |
| `scripts/mutation_check.py` | **8/8 mutations caught**, no `HarnessError` |
| `identity_check.py --all` | `PASS — 151 file(s), no host identity found` |
| Wave 1-4 gates (`test_ci_workflow`, `test_packaging_metadata`, `test_support_matrix`, `test_contributor_docs`, `test_verify_makefile`) | **144 passed** |
| `make verify-offline` | exits 0 |
| `make release-check` | exits 0, **`release check: PASSED — 10/10 checks`** |
| `git tag -l 'v*'` | **empty** |
| `git status --porcelain` | **empty**; no `dist/`, no `build/`, no stray backup |
| `git diff` for upload/tag verbs | **none** — no `twine upload`, no `gh release create`, no `git push --tags` |
| `.venv` contains `build` or `twine` | **no** |

Verdict line, verbatim:

```
VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)
```

`make verify` was **deliberately not run**. This plan changes no retailer code, and `verify`
makes live requests to six retailers; spending the politeness budget to prove a wheel installs
is the trade `docs/retailer-evidence.md` argues against. `make verify` remains the phase gate,
run once at phase close.

### Diffstat

```
 .github/workflows/release.yml | 166 ++++++++++
 CHANGELOG.md                  | 162 ++++++++++
 MANIFEST.in                   |   8 +
 Makefile                      |  24 +-
 README.md                     |  28 ++
 boty/cli.py                   |  38 +++
 pyproject.toml                |  37 ++-
 scripts/release_check.py      | 604 ++++++++++++++++++++++++++++++++++++++
 tests/test_ci_workflow.py     | 335 ++++++++++++++++++++-
 tests/test_cli_watch.py       |  47 ++++
 10 files changed, 1436 insertions(+), 13 deletions(-)
```

`pyproject.toml`: +37/-8 — the version line, the `Development Status` classifier plus its
comment paragraph, the `Changelog` key replacing 04-02's placeholder comment, and the
"THREE ABSENCES" block becoming "TWO ABSENCES" now that one of them landed. `MANIFEST.in`:
one `include` line and a six-line comment, no `exclude` lines, no `prune` line touched.
`README.md`: +28, all inside `## Install`, no table row and no matrix cell moved.
`Makefile`: the `release-check` target with its two-decision comment, one `.PHONY` word and
three `help` lines.

---

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 3 — blocking] Ruff warned on a `noqa` directive written inside a prose comment**

- **Found during:** Task 2, first `make lint` over `scripts/release_check.py`
- **Issue:** the comment explaining the `sys.path` idiom quoted the E402 suppression
  directive literally, and ruff parses **every** occurrence of it — including one inside a
  comment — producing
  `warning: Invalid `# noqa` directive on scripts/release_check.py:87: expected code to consist
  of uppercase letters followed by digits only`. Exactly the collision 04-04 met when its test
  grepped its own docstring for `tomllib`, one file over.
- **Fix:** the prose now names E402 without writing the directive out, and says why in
  parentheses. The directive on the import line itself is untouched.
- **Commit:** `ca4025b`

**2. [Rule 2 — missing critical] The module docstring named an upload verb in order to refuse it**

- **Found during:** Task 2, running the acceptance criterion that greps
  `scripts/release_check.py` for `twine upload`
- **Issue:** the "WHAT THIS DELIBERATELY DOES NOT DO" section said "There is no `twine upload`
  in this file", which made the criterion's grep match the sentence promising the opposite.
  A gate that its own subject can defeat by explaining itself is not a gate.
- **Fix:** reworded to "No upload verb appears anywhere in this file", with a sentence saying
  the literal is deliberately not written out *because* an acceptance criterion greps for it.
  Same resolution shape the Makefile already uses for `ruff format`.
- **Commit:** `ca4025b`

**3. [Rule 2 — missing critical] The widened owner rule's message was asserted by an existing test**

- **Found during:** Task 3, widening `_unpinned_actions`
- **Issue:** `test_a_third_party_action_with_a_perfectly_good_sha_is_reported` asserts the
  finding string exactly, and the old string named "GitHub's own `actions` organisation" — a
  claim that stops being true the moment `pypa` is allowed.
- **Fix:** the message now names the allow-list and the offending owner, and 04-04's test was
  updated in the same commit as the widening. Not a weakening: that test still watches the
  rule report `tj-actions/changed-files`.
- **Commit:** `aa57283`

**Total deviations:** 3 auto-fixed (1 blocking, 2 missing-critical). **Impact:** none on
behaviour. Two are the same class of defect — a decision record colliding with a rule that
reads text — which this repository has now met three times and resolves the same way each
time: name the thing without writing the token.

### Not deviations, but worth stating

- **No package entered any dependency list or extra.** `build` and `twine` are installed only
  into a venv `scripts/release_check.py` creates and destroys, and the project is never
  installed into it. `.venv` still holds exactly what `make verify` needs.
- **`boty/fixtures.py`, `.gitignore`, `SANDBOX_CONTENTS` and `MANIFEST.in`'s prune list were
  not touched.** 04-04's handoff said `prune .github` and the sandbox tuple already cover the
  directory, and the second workflow file confirmed it: sdist member count is unchanged at 26.
- **No `# noqa` was added anywhere.**
- **No CI badge, no PyPI badge.** Both would assert a status nobody has observed.

---

## Known Stubs

None. Every check in `scripts/release_check.py` runs against a real built artifact, and every
rule applied to `release.yml` runs against both the shipped file and a corrupted copy of it.

## Threat Flags

None beyond the plan's own register. `<threat_model>` T-04-05-01 … T-04-05-12 enumerate this
plan's surface and every `mitigate` disposition is implemented and asserted by a named test or
a named check above. Two dispositions are worth restating because they are **not** mitigations:

- **T-04-05-10 remains `accept`.** `pip install boty` fetches a stranger's abandoned package
  and this cannot be engineered away — PyPI does not release a name that has files, so the
  neighbour cannot be defensively claimed. The residual risk includes the case where that
  dormant 2012 account is compromised and a malicious `boty` 0.2.0 appears. Documentation at
  the point of typing is the only available mitigation and it is now live in README.
- **T-04-05-12 remains `transfer`.** The first publish and the tag push are Dan's.

---

## Handoff to 04-06 and Dan — in the order to act

**Nothing has been published. No tag exists.** `git tag -l 'v*'` is empty, no upload verb
appears anywhere in this plan's diff, and `.github/workflows/release.yml` has **never run** —
its first live execution will be 04-06's tag push. Everything above was measured locally.

### 1. Configure the PyPI trusted publisher for `bot-y`

At <https://pypi.org/manage/account/publishing/> (a *pending* publisher, since the project
does not exist on PyPI yet). Four fields, and the last one is the one that goes wrong:

| Field | Value |
|---|---|
| PyPI project name | `bot-y` |
| Owner | `danieljamesjohnson` |
| Repository name | `bot-y` |
| Workflow name | `release.yml` |
| **Environment name** | **`pypi`** |

**The environment string must be exactly `pypi`.** It is what the publish job declares. If the
two differ, the OIDC mint fails with an error that reads like a configuration problem on the
GitHub side rather than on the PyPI side, and you will look in the wrong place.

Also confirm before this: `bot-y` on PyPI returned **HTTP 404** on 2026-08-04, i.e. unclaimed.
Re-check, because a name is claimed by whoever gets there first.

### 2. Push the tag — this plan created none

```bash
git tag -a v1.0.0 -m "bot-y 1.0.0"
git push origin main          # main has no upstream yet: git push -u origin main
git push origin v1.0.0
```

Note the order: the tag has to point at a commit that exists on the remote, and **`main` has
no upstream configured** (a side effect of the § 0e `filter-repo` + force-push). Push the
branch first.

### 3. What the first workflow run should show

Two jobs, `build` then `publish`. The build job produces `bot_y-1.0.0.tar.gz` and
`bot_y-1.0.0-py3-none-any.whl` and uploads them as the `dist` artifact; the publish job
downloads them and uploads to PyPI.

**Two things no offline gate here could establish, and they are what to actually read:**

1. **That the OIDC mint succeeded.** The publish step should show a token exchange with PyPI
   and no fallback of any kind — no prompt for a username, no `HTTPError: 403 Invalid or
   non-existent authentication information`. A 403 there almost always means the environment
   name, the workflow filename or the repository in the PyPI form does not match this
   workflow. It is a configuration mismatch, not a code problem.
2. **That the version PyPI shows is `1.0.0` and matches `CHANGELOG.md`'s top heading.** The
   local check binds five statements of that number; PyPI's project page is the sixth and it
   is the only one this repository cannot assert.

### 4. Confirm `pip install bot-y` from PyPI — this is what closes criterion 3

```bash
python3 -m venv /tmp/boty-from-pypi
/tmp/boty-from-pypi/bin/pip install bot-y
cd /tmp && /tmp/boty-from-pypi/bin/boty --help ; echo $?
/tmp/boty-from-pypi/bin/pip show bot-y
```

Expect exit **0**, the usage for `{check,watch,capture-fixture}`, and `Version: 1.0.0`.

**`make release-check` already proves every part of that except the download itself** — the
build, the metadata, the file sets, the licence in the wheel, the console script running from
outside a checkout, and `nodriver` staying out of a default install. What is left to establish
is that PyPI serves the same bytes, which is the one thing only a publish can answer.

### 5. The name-confusion warning is already live

README's `### From PyPI` ships from this plan and nothing about it waits on publication. It is
deliberately written to stay true both before and after the tag is pushed, so there is no
second edit to remember.

---

## Self-Check

- `scripts/release_check.py` — FOUND (`release check:` verdict line present, 604 lines)
- `CHANGELOG.md` — FOUND (one `## [1.0.0]`, one `## [Unreleased]`, 162 lines)
- `.github/workflows/release.yml` — FOUND (`id-token: write` present, 166 lines)
- `pyproject.toml` — FOUND (`version = "1.0.0"`, `Development Status :: 5 - Production/Stable`, `Changelog` URL)
- `boty/cli.py` — FOUND (missing-config guard; `boty check -c <missing>` exits 2, observed)
- `Makefile` — FOUND (`release-check` in `.PHONY`, in `help`, not in `verify`)
- `tests/test_ci_workflow.py` — FOUND (`TRUSTED_ACTION_OWNERS`, 67 tests)
- `README.md` — FOUND (`### From PyPI` above `### From a clone`)
- Commit `542e6a1` — FOUND
- Commit `ca4025b` — FOUND
- Commit `aa57283` — FOUND

## Self-Check: PASSED

---

## A note on REQ-11, deliberately left open

**REQ-11 is NOT marked complete by this plan, and `.planning/REQUIREMENTS.md` was not
touched.** REQ-11 reads "`pip install bot-y` works **from PyPI**, and a **v1.0.0 tag
exists**". This plan bumped the version to 1.0.0 and proved a wheel locally; neither is a PyPI
publish and neither is a pushed tag. **04-06** closes REQ-11, by measuring what Dan actually
publishes. Two earlier plans in this phase flipped a requirement green on landing work that
merely fed it and were reverted (`61dccab`, `6b9a212`); this is the third opportunity and it
was declined.

---
*Phase: 04-open-source-ready*
*Completed: 2026-08-05*
