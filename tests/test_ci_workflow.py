"""The CI workflow's contract, checked mechanically rather than by eye.

WHY THIS FILE EXISTS
--------------------
`.github/workflows/ci.yml` is the only artifact in this repository that runs on
somebody else's computer, holding a token for this repository, against code a
pull-request author controls. It is therefore the one file whose correctness
cannot be demonstrated by running it here: no pull request can be opened
offline, and `make verify` will never execute a line of it.

So the workflow's contract is a gate rather than a paragraph. Every rule below
is a pure function of text or of parsed content, the shipped file is asserted
against those rules, and the SAME functions are run against deliberately broken
copies of the real file — because a gate asserted only against the tree it is
meant to guard has never been watched failing, and this project has already
shipped one of those.

WHY THERE ARE TWO VIEWS OF THE FILE
-----------------------------------
The workflow carries a decision-record comment block, in this repo's idiom, and
that block has to NAME `pull_request_target`, `continue-on-error` and `make
verify` in order to explain why none of them is there. A forbidden-string rule
that read the file as written would therefore match the file's own documentation
and pass forever, whatever the YAML said.

`_code` strips YAML comments and is what every forbidden-string rule reads.
`_raw` is the file as written and is used by exactly one rule — `_action_pins`,
which needs the trailing `# v7.0.1` comment beside a SHA pin. Both directions of
that property are asserted below: the comments mention the forbidden constructs
and the rules report nothing, and the same constructs inserted as YAML are
reported.

TWO YAML SURPRISES, BOTH MEASURED, BOTH EASY TO "FIX" INTO A BUG
----------------------------------------------------------------
1. A bare `on:` key parses as the BOOLEAN ``True``, not the string ``"on"``.
   Measured against the PyYAML 6.0.3 in this repo's venv: loading a workflow
   stub returns a mapping whose only key is ``True``. YAML 1.1 treats ``on`` as
   a boolean literal, and GitHub's own schema is written in the unquoted form
   every contributor has seen. So `_triggers` looks up both spellings and
   insists exactly one of them is present, rather than quoting the key in the
   workflow to suit the reader.

2. An unquoted ``python-version: 3.10`` parses as the FLOAT ``3.1``. Measured
   with the same PyYAML. Unquoted, the workflow asks the runner for Python 3.1,
   which is not what anybody typed and not a version that exists here. So
   `test_the_python_version_is_the_string_the_package_declares_as_its_floor`
   asserts the parsed value is a `str`, not merely that it reads as 3.10.

WHY THIS DOES NOT IMPORT tomllib
---------------------------------
`tomllib` is Python 3.11+. The floor this package declares is 3.10, CI exists to
run the suite THERE, and a gate that cannot import on the interpreter it guards
is not a gate. `tests/test_packaging_metadata.py` reached the same conclusion in
04-02 and wrote a narrow `[project]`-table reader for it; this file borrows that
reader by path rather than writing a second one, so the two cannot drift into
disagreeing about what `pyproject.toml` says.

Nothing here touches the network. It reads four files off disk.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
CI = WORKFLOWS / "ci.yml"
README = REPO_ROOT / "README.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"

#: The one make target CI is allowed to run. `verify` reaches six retailers
#: live; `verify-offline` delegates to the same recipe with
#: `CONTROL_FLAGS=--offline`. The rule below extracts the target as a TOKEN
#: rather than substring-matching, because `verify` is a prefix of
#: `verify-offline` and a substring rule would pass on exactly the mistake it
#: exists to catch.
CI_TARGET = "verify-offline"

#: Scopes that are dangerous at any level, not only at `write`. `id-token` is
#: an OIDC identity — the credential 04-05's PyPI Trusted Publishing workflow
#: will legitimately need, and the one no pull-request-triggered workflow may
#: ever hold.
PRIVILEGED_SCOPES = ("id-token", "packages")

#: Trigger names through which a pull request can start a run.
PULL_REQUEST_TRIGGERS = ("pull_request", "pull_request_target")

_SHA = re.compile(r"[0-9a-f]{40}")
_MAKE = re.compile(r"\bmake\s+([A-Za-z0-9_.-]+)")
_USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(\S+)\s*(?:#\s*(.*?))?\s*$")

#: The shape 04-05 is about to write, kept here so the cross-workflow privilege
#: rule is a rule about a set larger than one. `.github/workflows/` holds a
#: single file today, so without this the boundary would be trivially satisfied
#: and would go on being satisfied by never being tested.
PUBLISH_WORKFLOW = """
name: publish
on:
  push:
    tags: ["v*"]
permissions:
  contents: read
jobs:
  pypi:
    runs-on: ubuntu-24.04
    permissions:
      id-token: write
    steps:
      - run: echo build-and-publish
"""


class NoTriggerBlock(RuntimeError):
    """A workflow with no `on:` key at all, in either of YAML's two spellings.

    Raised rather than returning an empty mapping, for the reason 04-02 wrote
    `NotATrackedTree` for: a rule that reports "no triggers" for a file it could
    not read passes by not running, and every trigger rule downstream would then
    be green about nothing.
    """


# --------------------------------------------------------------------------
# The two views of the file, and the reason they are separate
# --------------------------------------------------------------------------


def _raw() -> str:
    """The workflow exactly as written, comments and all.

    Used by ONE rule — `_action_pins` — which needs the trailing version comment
    beside each SHA pin. Every forbidden-string rule reads `_code` instead. See
    the module docstring: this file's subject names the constructs it forbids in
    order to explain their absence, so a rule reading this view would match the
    documentation and could never fail.
    """
    return CI.read_text(encoding="utf-8")


def _strip_yaml_comment(line: str) -> str:
    """Drop a `#` comment, ignoring `#` inside a quoted scalar.

    A `#` opens a YAML comment only at the start of a line or after whitespace,
    which is why the position test is here rather than a bare `split("#")`.
    """
    quote: str | None = None
    for i, ch in enumerate(line):
        if quote is not None:
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line


def _code(text: str) -> str:
    """The workflow with every comment removed — the view the string rules read."""
    return "\n".join(_strip_yaml_comment(line) for line in text.splitlines())


# --------------------------------------------------------------------------
# The rules, each a pure function so the corruption tests run the same one
# --------------------------------------------------------------------------


def _triggers(wf: dict[Any, Any]) -> dict[str, Any]:
    """The trigger mapping, under either spelling of the `on` key.

    YAML 1.1 parses a bare `on:` as the boolean `True` (measured; see the module
    docstring). Exactly one of the two spellings must be present: a file with
    both is ambiguous about which GitHub reads, and a file with neither has no
    trigger at all.
    """
    spellings = [key for key in (True, "on") if key in wf]
    if not spellings:
        raise NoTriggerBlock(
            "no `on:` key in either spelling. A workflow with no trigger runs "
            "never, and reporting an empty trigger set here would make every "
            "trigger rule below pass by not running."
        )
    if len(spellings) > 1:
        raise NoTriggerBlock("both `on` and the YAML-1.1 boolean key are present")
    value = wf[spellings[0]]
    if isinstance(value, str):
        return {value: None}
    if isinstance(value, list):
        return dict.fromkeys(value)
    return dict(value)


def _unfiltered_pull_request(triggers: dict[str, Any]) -> bool:
    """True when `pull_request` is present AND carries no filter of any kind.

    REQ-10 says every pull request. A `branches` filter silently exempts some of
    them; a `paths`/`paths-ignore` filter is worse than it looks, because the
    identity leak that mattered most in this repo's history was in a `.planning/`
    markdown file — so a docs-only pull request is precisely the one whose
    `identity` stage matters most.
    """
    if "pull_request" not in triggers:
        return False
    value = triggers["pull_request"]
    if not value:
        return True
    return not any(key in value for key in ("branches", "branches-ignore", "paths", "paths-ignore"))


def _push_branches(triggers: dict[str, Any]) -> list[str]:
    """The branches a `push` trigger is restricted to. Empty means unrestricted."""
    value = triggers.get("push") or {}
    return list(value.get("branches") or [])


def _jobs(wf: dict[Any, Any]) -> dict[str, Any]:
    return dict(wf.get("jobs") or {})


def _steps(wf: dict[Any, Any]) -> list[dict[str, Any]]:
    return [
        step
        for job in _jobs(wf).values()
        for step in (job or {}).get("steps") or []
        if isinstance(step, dict)
    ]


def _permission_grants(wf: dict[Any, Any]) -> list[tuple[str, str, str]]:
    """Every `(where, scope, level)` grant, workflow-level and job-level, flattened.

    Flattened on purpose: a job quietly widening the workflow's grant is the
    shape this repo has to notice, and it is invisible to a rule that only reads
    the workflow-level block.
    """
    grants: list[tuple[str, str, str]] = []

    def collect(where: str, perms: Any) -> None:
        if perms is None:
            return
        if isinstance(perms, str):
            # `permissions: write-all` / `read-all` — one word, every scope.
            grants.append((where, "*", perms))
            return
        for scope, level in perms.items():
            grants.append((where, str(scope), str(level)))

    collect("workflow", wf.get("permissions"))
    for name, job in _jobs(wf).items():
        collect(f"job:{name}", (job or {}).get("permissions"))
    return grants


def _write_grants(grants: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """Every grant that is writable, or that names an inherently privileged scope.

    This is the rule that keeps 04-05's publish privilege out of any workflow a
    pull request can start.
    """
    return [g for g in grants if "write" in g[2] or g[1] in PRIVILEGED_SCOPES]


def _run_blocks(wf: dict[Any, Any]) -> list[str]:
    return [str(step["run"]) for step in _steps(wf) if "run" in step]


def _make_targets(wf: dict[Any, Any]) -> list[str]:
    """The make targets invoked by run steps, as tokens.

    Tokens rather than substrings: `verify` is a prefix of `verify-offline`, so a
    substring rule would report the live target as absent from a workflow that
    ran it, and pass on the one mistake it exists to catch.
    """
    return [target for block in _run_blocks(wf) for target in _MAKE.findall(block)]


def _expression_interpolations(wf: dict[Any, Any]) -> list[str]:
    """Run blocks containing a `${{ }}` expression.

    Scoped to run blocks deliberately. An expression in `concurrency` is
    evaluated by GitHub into a value that never reaches a shell; an expression
    inside a `run:` block is a pull-request title executing as code on the
    runner, under this job's token.
    """
    return [block for block in _run_blocks(wf) if "${{" in block]


def _flattening(code: str) -> list[str]:
    """Every construct that can turn a failing check into a green run.

    Reads the COMMENT-STRIPPED view — the workflow's own decision record names
    several of these in order to explain their absence.
    """
    found: list[str] = []
    for line in code.splitlines():
        text = line.strip()
        if "continue-on-error" in text:
            found.append(f"continue-on-error: {text!r}")
        if "||" in text:
            found.append(f"an or-fallback that discards the exit code: {text!r}")
        if "set +e" in text:
            found.append(f"set +e: {text!r}")
        if re.search(r";\s*true\b", text):
            found.append(f"a `; true` no-op: {text!r}")
        if re.search(r"\bexit\s+0\b", text):
            found.append(f"an unconditional exit 0: {text!r}")
        match = _MAKE.search(text)
        if match is not None and "|" in text[match.end() :]:
            found.append(f"a pipe on the line invoking make: {text!r}")
    return found


def _action_pins(raw: str) -> list[tuple[str, str, str | None]]:
    """`(action, ref, trailing-version-comment)` for every `uses:` line.

    Reads the RAW view, because the version comment is the whole point of the
    trailing comment convention: a bare 40-character SHA tells a reviewer
    nothing about which release they are looking at.
    """
    pins: list[tuple[str, str, str | None]] = []
    for line in raw.splitlines():
        match = _USES.match(line)
        if match is None:
            continue
        action, _, ref = match.group(1).partition("@")
        pins.append((action, ref, match.group(2)))
    return pins


def _unpinned_actions(pins: list[tuple[str, str, str | None]]) -> list[str]:
    """Every pin that is third-party, tag-pinned, or missing its version comment.

    A mutable tag is another party's pointer: in March 2025 `tj-actions/changed-files`
    had its tags repointed at a malicious commit and thousands of public
    repositories printed secrets into their build logs. A full commit SHA is
    immutable and costs one deliberate edit a year here.
    """
    bad: list[str] = []
    for action, ref, comment in pins:
        if not action.startswith("actions/"):
            bad.append(f"{action}: not published by GitHub's own `actions` organisation")
        elif _SHA.fullmatch(ref) is None:
            bad.append(f"{action}: ref {ref!r} is not a 40-character commit SHA")
        elif comment is None or not re.search(r"v[0-9]", comment):
            bad.append(f"{action}: no trailing comment naming the version behind the SHA")
    return bad


def _python_versions(wf: dict[Any, Any]) -> list[Any]:
    """Every `python-version` input, AS PARSED — a float survives to the assertion."""
    return [
        (step.get("with") or {})["python-version"]
        for step in _steps(wf)
        if "python-version" in (step.get("with") or {})
    ]


def _cache_uses(wf: dict[Any, Any]) -> list[str]:
    """Every step that restores a cache, by action or by input.

    `setup-python`'s `cache:` input is `actions/cache` underneath, so naming only
    the action would leave the shorter spelling of the same risk unguarded.
    """
    found: list[str] = []
    for step in _steps(wf):
        uses = str(step.get("uses", ""))
        if "actions/cache" in uses:
            found.append(f"cache action: {uses}")
        if "cache" in (step.get("with") or {}):
            found.append(f"cache input on {uses or step.get('name')}")
    return found


def _floating_runners(wf: dict[Any, Any]) -> list[str]:
    """Every `runs-on` naming a moving alias rather than a concrete image."""
    return [
        str(job.get("runs-on"))
        for job in _jobs(wf).values()
        if str((job or {}).get("runs-on", "")).endswith("-latest")
    ]


def _pr_triggered_privilege(workflows: dict[str, str]) -> list[str]:
    """Every workflow a pull request can trigger that also holds real privilege.

    The only rule here that looks beyond `ci.yml`, and the one that will still be
    doing work in a year. It states the 04-04 / 04-05 boundary as a rule rather
    than as prose: high privilege — `id-token: write` for PyPI Trusted
    Publishing, or any `write` grant — is permitted only in a workflow that no
    pull request can start.
    """
    findings: list[str] = []
    for name, text in sorted(workflows.items()):
        wf = yaml.safe_load(text)
        triggers = _triggers(wf)
        if "pull_request_target" in triggers:
            findings.append(
                f"{name}: uses `pull_request_target`, which runs the base repo's "
                "workflow with a write token and its secrets against author-controlled code"
            )
        if not any(trigger in triggers for trigger in PULL_REQUEST_TRIGGERS):
            continue
        for where, scope, level in _write_grants(_permission_grants(wf)):
            findings.append(f"{name}: pull-request-triggerable and grants {scope}: {level} ({where})")
    return findings


# --------------------------------------------------------------------------
# The declared floor, read through 04-02's parser rather than a second one
# --------------------------------------------------------------------------


def _load_packaging_metadata() -> Any:
    """Import `tests/test_packaging_metadata.py` by path, for its TOML reader.

    The `spec_from_file_location` idiom `tests/test_support_matrix.py` uses to
    reach `scripts/evidence_check.py`. Borrowed rather than re-implemented: two
    readers of one `pyproject.toml` drift, and the floor is the number this
    file, that file and the workflow all have to agree on.
    """
    spec = importlib.util.spec_from_file_location(
        "packaging_metadata_for_ci", Path(__file__).resolve().parent / "test_packaging_metadata.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PACKAGING: Any = _load_packaging_metadata()


def _declared_floor(pyproject_text: str) -> str | None:
    """The minimum Python `requires-python` declares, e.g. `"3.10"`."""
    spec = PACKAGING._string(PACKAGING._project_table(pyproject_text).get("requires-python"))
    if spec is None:
        return None
    match = re.fullmatch(r">=\s*([0-9]+\.[0-9]+)", spec.strip())
    return match.group(1) if match is not None else None


def _mypy_python_version(pyproject_text: str) -> str | None:
    """`[tool.mypy] python_version`, the second place this repo declares the floor.

    Built from `_strip_comment` and `_string` borrowed above rather than from a
    new parser: `_project_table` reads `[project]` only, and this key lives one
    table along.
    """
    in_section = False
    for line in pyproject_text.splitlines():
        stripped = PACKAGING._strip_comment(line).strip()
        if stripped.startswith("["):
            in_section = stripped == "[tool.mypy]"
            continue
        if in_section and stripped.startswith("python_version"):
            _, _, raw = stripped.partition("=")
            return PACKAGING._string(raw.strip())
    return None


def _documented_ci_target(readme_text: str) -> str | None:
    """The make target README's fenced blocks name as the CI entry point.

    Returns `None` when README documents no CI entry point at all — which is a
    finding, not a reason to skip. README has carried
    `make verify-offline   # ... for CI` since before any CI existed; after this
    plan that line is a claim about a file, and the two are bound here.
    """
    in_fence = False
    for line in readme_text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            continue
        code, _, comment = line.partition("#")
        if "CI" not in comment:
            continue
        match = _MAKE.search(code)
        if match is not None:
            return match.group(1)
    return None


# --------------------------------------------------------------------------
# The shipped file, asserted against those rules
# --------------------------------------------------------------------------


def _workflow() -> dict[Any, Any]:
    return dict(yaml.safe_load(_raw()))


def _all_workflow_texts() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(WORKFLOWS.iterdir())
        if path.suffix in (".yml", ".yaml")
    }


def test_the_workflow_exists_and_is_one_job() -> None:
    """No skip if the file is missing. `addopts = "-ra"` exists in this repo
    because a test that quietly stops running is the failure mode it was
    configured to surface, and the mutation sandbox is where that would
    otherwise happen."""
    assert CI.is_file(), f"{CI} is missing — the PR gate has no subject"
    jobs = _jobs(_workflow())
    assert len(jobs) == 1, f"expected exactly one job, found {sorted(jobs)}"


def test_the_only_make_target_ci_runs_is_the_offline_one() -> None:
    targets = _make_targets(_workflow())
    assert targets == [CI_TARGET], (
        f"CI invokes make targets {targets}. The bare `verify` target makes live requests to six "
        "retailers; from GitHub's IP ranges at pull-request frequency that is exactly the trade "
        "docs/retailer-evidence.md argues against."
    )


def test_pull_requests_are_not_filtered_by_branch_or_path() -> None:
    triggers = _triggers(_workflow())
    assert _unfiltered_pull_request(triggers), (
        f"the pull_request trigger carries a filter: {triggers.get('pull_request')!r}. REQ-10 says "
        "every PR, and a docs-only PR is the one whose identity stage matters most."
    )


def test_push_runs_only_on_main() -> None:
    assert _push_branches(_triggers(_workflow())) == ["main"]


def test_pull_request_target_is_not_a_trigger() -> None:
    assert "pull_request_target" not in _triggers(_workflow())
    assert "pull_request_target" not in _code(_raw())


def test_the_workflow_grants_nothing_but_read_access() -> None:
    grants = _permission_grants(_workflow())
    assert ("workflow", "contents", "read") in grants, grants
    assert _write_grants(grants) == [], _write_grants(grants)


def test_no_workflow_in_this_repo_lets_a_pull_request_reach_privilege() -> None:
    findings = _pr_triggered_privilege(_all_workflow_texts())
    assert findings == [], findings


def test_every_action_is_first_party_and_pinned_to_a_commit_sha() -> None:
    pins = _action_pins(_raw())
    assert pins, "no `uses:` line at all — the job cannot be checking anything out"
    assert _unpinned_actions(pins) == [], _unpinned_actions(pins)


def test_no_run_block_interpolates_a_workflow_expression() -> None:
    assert _expression_interpolations(_workflow()) == []
    assert "${{" in _raw(), "the concurrency expression vanished — the rule above is now vacuous"


def test_nothing_in_the_workflow_can_flatten_an_exit_code() -> None:
    assert _flattening(_code(_raw())) == []


def test_the_agpl_browser_extra_is_never_installed_in_ci() -> None:
    code = _code(_raw())
    assert "[browser]" not in code
    assert "nodriver" not in code
    assert "[dev]" in code, "CI installs no dev extra at all — ruff and mypy would be absent"


def test_the_python_version_is_the_string_the_package_declares_as_its_floor() -> None:
    versions = _python_versions(_workflow())
    assert len(versions) == 1, versions
    value = versions[0]
    assert isinstance(value, str), (
        f"python-version parsed as {type(value).__name__} {value!r}. Unquoted, YAML reads 3.10 as "
        "the float 3.1 and the workflow asks the runner for Python 3.1."
    )
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    floor = _declared_floor(pyproject)
    assert value == floor, f"CI runs {value!r}; requires-python declares the floor {floor!r}"
    assert _mypy_python_version(pyproject) == floor, (
        "[tool.mypy] python_version and requires-python disagree about the floor"
    )


def test_nothing_caches_the_workspace() -> None:
    assert _cache_uses(_workflow()) == []
    assert "actions/cache" not in _code(_raw())


def test_the_job_is_time_limited_and_runs_on_a_pinned_image() -> None:
    job = next(iter(_jobs(_workflow()).values()))
    timeout = job.get("timeout-minutes")
    assert isinstance(timeout, int) and 0 < timeout <= 30, (
        f"timeout-minutes is {timeout!r}; the GitHub default is six hours"
    )
    assert _floating_runners(_workflow()) == [], _floating_runners(_workflow())


def test_the_readme_documents_the_target_the_workflow_actually_runs() -> None:
    documented = _documented_ci_target(README.read_text(encoding="utf-8"))
    assert documented is not None, (
        "README's `## Verifying it works` block no longer names a CI entry point. That line has "
        "been a claim about CI since before CI existed; it is now a claim about a file."
    )
    assert documented == _make_targets(_workflow())[0]


def test_the_shipped_comments_name_the_constructs_the_rules_forbid() -> None:
    """Direction one of the comment-stripping property.

    The workflow's own decision record names `pull_request_target`,
    `continue-on-error` and `make verify` in order to explain their absence. The
    rules must report NOTHING for it. That is the proof `_code` strips comments,
    rather than the rules having stopped looking.
    """
    raw = _raw()
    for token in ("pull_request_target", "continue-on-error", "make verify", "|| true"):
        assert token in raw, f"the workflow no longer explains why {token!r} is absent"
    code = _code(raw)
    for token in ("pull_request_target", "continue-on-error"):
        assert token not in code
    assert _flattening(code) == []
    assert _make_targets(_workflow()) == [CI_TARGET]


def test_no_rule_function_in_this_file_reads_a_file() -> None:
    """Every rule takes text or parsed content, which is what lets the
    corruption tests below call the identical function the shipped-file tests
    call. A rule that opened the file itself could only ever be asserted against
    the tree it guards."""
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    readers = {"read_text", "open", "read_bytes", "iterdir"}
    offenders = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name not in RULES:
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute) and child.attr in readers:
                offenders.append(f"{node.name} calls .{child.attr}()")
    assert offenders == [], offenders


def test_this_file_does_not_import_tomllib() -> None:
    """`tomllib` is 3.11+; the floor is 3.10 and CI exists to run the suite there.

    Asserted over the import statements rather than over the text, because this
    file's own docstring has to NAME `tomllib` in order to explain why it is not
    imported — the same collision the two views of the workflow exist for.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    assert "tomllib" not in imported, imported


# --------------------------------------------------------------------------
# The same rules, run against deliberately broken copies of the real file
# --------------------------------------------------------------------------

#: The rule functions asserted not to read anything off disk.
RULES = (
    "_code",
    "_strip_yaml_comment",
    "_triggers",
    "_unfiltered_pull_request",
    "_push_branches",
    "_permission_grants",
    "_write_grants",
    "_run_blocks",
    "_make_targets",
    "_expression_interpolations",
    "_flattening",
    "_action_pins",
    "_unpinned_actions",
    "_python_versions",
    "_cache_uses",
    "_floating_runners",
    "_pr_triggered_privilege",
    "_declared_floor",
    "_mypy_python_version",
    "_documented_ci_target",
)


def _corrupt(old: str, new: str) -> str:
    """The real workflow with one exact substitution applied.

    Fails loudly when the anchor is absent or ambiguous, following 04-02's
    `_corrupt_line`: a corruption test that silently corrupts nothing asserts
    only that the rule passes on a healthy tree, which is already covered above.
    """
    text = _raw()
    count = text.count(old)
    assert count == 1, (
        f"expected exactly one {old!r} in the real workflow, found {count} — the shipped file "
        "moved out from under this test"
    )
    return text.replace(old, new)


def test_switching_ci_to_the_live_verify_target_is_reported() -> None:
    broken = _corrupt("run: make verify-offline", "run: make verify")
    assert _make_targets(yaml.safe_load(broken)) == ["verify"]


def test_a_continue_on_error_key_is_reported() -> None:
    broken = _corrupt(
        "      - name: The verdict\n", "      - name: The verdict\n        continue-on-error: true\n"
    )
    assert any("continue-on-error" in f for f in _flattening(_code(broken)))


def test_an_or_true_after_the_check_is_reported() -> None:
    broken = _corrupt("run: make verify-offline", "run: make verify-offline || true")
    assert any("or-fallback" in f for f in _flattening(_code(broken)))


def test_piping_the_check_through_tee_is_reported() -> None:
    broken = _corrupt("run: make verify-offline", "run: make verify-offline | tee verify.log")
    assert any("a pipe on the line invoking make" in f for f in _flattening(_code(broken)))


def test_set_plus_e_and_an_unconditional_exit_zero_are_reported() -> None:
    broken = _corrupt(
        "        run: make verify-offline\n",
        "        run: |\n          set +e\n          make verify-offline\n          exit 0\n",
    )
    found = _flattening(_code(broken))
    assert any("set +e" in f for f in found), found
    assert any("exit 0" in f for f in found), found


def test_a_no_op_semicolon_true_is_reported() -> None:
    broken = _corrupt("run: make verify-offline", "run: make verify-offline ; true")
    assert any("; true" in f for f in _flattening(_code(broken)))


def test_a_workflow_level_write_grant_is_reported() -> None:
    broken = _corrupt("permissions:\n  contents: read", "permissions:\n  contents: write")
    grants = _permission_grants(yaml.safe_load(broken))
    assert _write_grants(grants) == [("workflow", "contents", "write")]


def test_a_job_that_widens_the_workflow_grant_is_reported() -> None:
    broken = _corrupt(
        "    runs-on: ubuntu-24.04\n",
        "    permissions:\n      contents: write\n    runs-on: ubuntu-24.04\n",
    )
    assert _write_grants(_permission_grants(yaml.safe_load(broken))) == [
        ("job:verify", "contents", "write")
    ]


def test_an_id_token_grant_is_reported_even_though_ci_needs_no_secret() -> None:
    broken = _corrupt(
        "    runs-on: ubuntu-24.04\n",
        "    permissions:\n      id-token: write\n    runs-on: ubuntu-24.04\n",
    )
    assert _write_grants(_permission_grants(yaml.safe_load(broken))) == [
        ("job:verify", "id-token", "write")
    ]


def test_a_pull_request_triggered_workflow_holding_privilege_is_reported() -> None:
    broken = _corrupt(
        "    runs-on: ubuntu-24.04\n",
        "    permissions:\n      id-token: write\n    runs-on: ubuntu-24.04\n",
    )
    findings = _pr_triggered_privilege({"ci.yml": broken})
    assert findings and "pull-request-triggerable" in findings[0], findings


def test_a_tag_pinned_action_is_reported() -> None:
    broken = _corrupt(
        "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "uses: actions/checkout@v7",
    )
    findings = _unpinned_actions(_action_pins(broken))
    assert findings == ["actions/checkout: ref 'v7' is not a 40-character commit SHA"], findings


def test_a_third_party_action_with_a_perfectly_good_sha_is_reported() -> None:
    broken = _corrupt(
        "uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
        f"uses: tj-actions/changed-files@{'0' * 40}",
    )
    findings = _unpinned_actions(_action_pins(broken))
    assert findings == [
        "tj-actions/changed-files: not published by GitHub's own `actions` organisation"
    ], findings


def test_a_sha_pin_with_no_version_comment_is_reported() -> None:
    broken = _corrupt(
        "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1",
        "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
    )
    findings = _unpinned_actions(_action_pins(broken))
    assert findings == [
        "actions/checkout: no trailing comment naming the version behind the SHA"
    ], findings


def test_an_expression_inside_a_run_block_is_reported() -> None:
    broken = _corrupt(
        "run: make verify-offline",
        "run: make verify-offline ${{ github.event.pull_request.title }}",
    )
    assert _expression_interpolations(yaml.safe_load(broken))


def test_installing_the_agpl_browser_extra_is_reported() -> None:
    broken = _corrupt(".venv/bin/pip install -e '.[dev]'", ".venv/bin/pip install -e '.[browser]'")
    assert "[browser]" in _code(broken)
    assert "[dev]" not in _code(broken)


def test_a_paths_ignore_filter_on_the_trigger_is_reported() -> None:
    broken = _corrupt("  pull_request:\n", "  pull_request:\n    paths-ignore: ['**.md']\n")
    assert not _unfiltered_pull_request(_triggers(yaml.safe_load(broken)))


def test_a_branch_filter_on_the_trigger_is_reported_too() -> None:
    broken = _corrupt("  pull_request:\n", "  pull_request:\n    branches: [main]\n")
    assert not _unfiltered_pull_request(_triggers(yaml.safe_load(broken)))


def test_an_unquoted_python_version_is_the_float_three_point_one() -> None:
    broken = _corrupt('python-version: "3.10"', "python-version: 3.10")
    versions = _python_versions(yaml.safe_load(broken))
    assert versions == [3.1]
    assert isinstance(versions[0], float)


def test_a_python_version_that_disagrees_with_the_declared_floor_is_reported() -> None:
    broken = _corrupt('python-version: "3.10"', 'python-version: "3.12"')
    versions = _python_versions(yaml.safe_load(broken))
    assert versions[0] != _declared_floor(PYPROJECT.read_text(encoding="utf-8"))


def test_a_cache_input_on_setup_python_is_reported() -> None:
    broken = _corrupt(
        '          python-version: "3.10"\n',
        '          python-version: "3.10"\n          cache: pip\n',
    )
    assert _cache_uses(yaml.safe_load(broken))


def test_a_floating_runner_image_is_reported() -> None:
    broken = _corrupt("runs-on: ubuntu-24.04", "runs-on: ubuntu-latest")
    assert _floating_runners(yaml.safe_load(broken)) == ["ubuntu-latest"]


def test_a_pull_request_target_trigger_is_reported_across_the_directory() -> None:
    broken = _corrupt("  pull_request:\n", "  pull_request_target:\n")
    findings = _pr_triggered_privilege({"ci.yml": broken})
    assert findings and "pull_request_target" in findings[0], findings


def test_a_workflow_with_no_trigger_block_raises_rather_than_reporting_nothing() -> None:
    broken = _corrupt("on:\n  pull_request:\n  push:\n    branches: [main]\n", "")
    try:
        _triggers(yaml.safe_load(broken))
    except NoTriggerBlock:
        return
    raise AssertionError("a workflow with no trigger reported a trigger set instead of raising")


def test_a_readme_that_stops_documenting_a_ci_entry_point_reports_nothing() -> None:
    readme = README.read_text(encoding="utf-8")
    line = next(line for line in readme.splitlines() if "for CI" in line)
    assert _documented_ci_target(readme.replace(line + "\n", "")) is None


# --------------------------------------------------------------------------
# The boundary between this workflow and the one 04-05 will write
# --------------------------------------------------------------------------


def test_the_publish_workflow_04_05_will_write_passes_while_no_pr_can_start_it() -> None:
    """`id-token: write` is legitimate for PyPI Trusted Publishing. The rule must
    permit it, or 04-05 inherits a test it can only satisfy by weakening."""
    assert _pr_triggered_privilege({"release.yml": PUBLISH_WORKFLOW}) == []


def test_the_same_publish_workflow_is_reported_the_moment_a_pr_can_start_it() -> None:
    """And the other direction, which is the whole boundary: the identical
    privilege becomes a finding as soon as a pull request can reach it."""
    reachable = PUBLISH_WORKFLOW.replace("on:\n  push:", "on:\n  pull_request:\n  push:")
    findings = _pr_triggered_privilege({"release.yml": reachable})
    assert findings == [
        "release.yml: pull-request-triggerable and grants id-token: write (job:pypi)"
    ], findings
