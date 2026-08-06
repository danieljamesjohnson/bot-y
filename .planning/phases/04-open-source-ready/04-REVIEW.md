---
phase: 04-open-source-ready
reviewed: 2026-08-06T00:00:00Z
depth: standard
diff_base: b0a272f
diff_head: b2b30d8
files_reviewed: 31
files_reviewed_list:
  - .github/workflows/ci.yml
  - .github/workflows/release.yml
  - pyproject.toml
  - Makefile
  - MANIFEST.in
  - LICENSE
  - .gitignore
  - boty/cli.py
  - boty/monitor.py
  - boty/parse.py
  - boty/retailers.py
  - scripts/identity_check.py
  - scripts/mutation_check.py
  - scripts/release_check.py
  - tests/test_ci_workflow.py
  - tests/test_cli_watch.py
  - tests/test_contributor_docs.py
  - tests/test_control_check.py
  - tests/test_evidence_check.py
  - tests/test_fetch.py
  - tests/test_identity_check.py
  - tests/test_packaging_metadata.py
  - tests/test_pacing.py
  - tests/test_parse.py
  - tests/test_retailers.py
  - tests/test_support_matrix.py
  - tests/test_verify_makefile.py
  - README.md
  - CONTRIBUTING.md
  - docs/adding-a-retailer.md
  - docs/retailer-evidence.md
  - CHANGELOG.md
findings:
  critical: 0
  warning: 7
  info: 6
  total: 13
status: issues
---

# Phase 4: Code Review Report

**Reviewed:** 2026-08-06
**Depth:** standard (diff `b0a272f..b2b30d8`)
**Files Reviewed:** 31 source/config/doc files (planning artefacts excluded)
**Status:** issues_found — 0 Critical, 7 Warning, 6 Info

## Summary

**No Critical findings, and I looked hard for them.** Specifically I could not
find any path in this diff that turns an unreadable or blocked page into a
confident verdict, and I could not find a new gate that passes vacuously:

- `_repair_ldjson` runs **only** on a block `json.loads` has already refused, so
  no page that parses today can change its reading. A block it cannot repair
  increments `unparseable` and is skipped, and the caller still lands on the
  no-offers `UNKNOWN` branch. I probed it with doubly-escaped, mixed-escaped,
  trailing-backslash and literal-backslash payloads (see IN-05) and could not
  make it produce parseable-but-wrong `availability`.
- `check_target_browser`'s retry cannot manufacture a reading: a page with no
  add-to-cart control returns `None` twice and still reads `UNKNOWN`.
- `zip(..., strict=True)` in `boty/monitor.py` is the correct direction — a
  length mismatch crashes rather than silently truncating `alerts`.
- The five pinned action SHAs were **verified against the GitHub API**. All five
  dereference to exactly the tag named in the trailing comment, including the
  annotated tag on `pypa/gh-action-pypi-publish@dc37677… → v1.14.2`.
- The `pull_request` / `pull_request_target` / `id-token` boundary is correct in
  both workflows, and `_pr_triggered_privilege` is exercised in both directions
  against synthetic *and* real corrupted copies.
- The corruption tests in `test_ci_workflow.py`, `test_packaging_metadata.py`
  and `test_contributor_docs.py` all use anchored `_corrupt*` helpers that raise
  when the anchor is absent or ambiguous, so none of them can silently corrupt
  nothing. `make verify-offline` was run: `VERIFY: PASS (OFFLINE …)`, 531 tests,
  8/8 mutations caught.

The findings below are real defects, but they are second-order: one shipped
artefact carries junk that every gate in the phase missed, one class of workflow
file escapes the pin rules, one new production code path has no test, and one
new diagnostic can misdiagnose the exact case it was written for.

---

## Warnings

### WR-01: `CHANGELOG.md` ships with leaked tool-call XML at the end of the file

> **RESOLVED 2026-08-06 in `2ac965f`**, by the orchestrator, after this review was
> written. The two lines are gone and the tree greps clean for the pattern. A
> `git grep` for the same shape across all tracked files found two more instances,
> both in historical planning summaries and neither shipped (`01-03-SUMMARY.md`,
> `03-02-SUMMARY.md`); both were trimmed in the same commit, altering no claim in
> either document. `make verify-offline` still exits 0 — 531 passed, 8/8 mutations.
>
> **The gate gap this finding names is NOT closed.** Nothing reads the changelog
> body: `release_check.py` check 10 asserts only that the file exists, and
> `_changelog_version` reads only the first `## [x.y.z]` heading. The same leak
> could land again tomorrow and publish. That fix is a code change and belongs in
> a plan, not in a post-review cleanup commit.

**File:** `CHANGELOG.md:161-162`

**Issue:** The file's last two lines are literal agent tool-call markup:

```
</content>
</invoke>
```

Verified at the byte level (`od -c`): the file ends
`…cannot be claimed.\n</content>\n</invoke>\n`. This is not markdown, it is not
a code fence, and it renders as visible garbage.

Why it matters here specifically: `MANIFEST.in:39` carries `include
CHANGELOG.md` **on purpose**, so this text is published inside the sdist to
PyPI; `[project.urls] Changelog` in `pyproject.toml:179` points every installer
at it; and the CHANGELOG is the file that argues the project's release notes are
written in a register that respects the reader. It is the first thing a
prospective contributor reads after the README.

It also demonstrates a gap in the phase's own gates. `release_check.py` check 10
asserts the Changelog URL resolves to a *file that exists*;
`_changelog_version` reads only the first `## [x.y.z]` heading. Nothing reads
the body. `scripts/identity_check.py` does not scan for markup. So this survived
`make verify`, `make verify-offline`, the mutation sandbox and the whole 04-05
verification.

**Fix:** Delete the two lines. Then close the gate that missed it — the cheapest
version is a shape rule beside the existing changelog reader:

```python
# scripts/release_check.py — beside _changelog_version
_XML_JUNK = re.compile(r"^\s*</?(?:invoke|content|parameter|function_calls)\b", re.M)

def _changelog_junk(changelog_text: str) -> list[str]:
    """Tool-call markup that leaked into a file published in the sdist."""
    return sorted(set(_XML_JUNK.findall(changelog_text)))
```

and report it as check 11. A stricter variant worth considering, since it costs
nothing: assert that every non-blank line of `CHANGELOG.md` starts with `#`,
`-`, `>`, `|`, a space, or a word character.

---

### WR-02: A third workflow file escapes the pin, exit-code, timeout and runner rules

**File:** `tests/test_ci_workflow.py:589-592`, `1070-1073`, `1082-1091`

**Issue:** Only two rules in this file iterate the whole directory —
`_pr_triggered_privilege` (via `test_no_workflow_in_this_repo_lets_a_pull_request_reach_privilege`,
line 584) and the twine/`gh release` run-block rule (line 1103). Every other
rule is bound to a named file:

```python
def test_every_action_is_first_party_and_pinned_to_a_commit_sha() -> None:
    pins = _action_pins(_raw())          # <- ci.yml only
...
def test_every_action_in_the_publish_workflow_is_pinned_to_a_trusted_owner() -> None:
    pins = _action_pins(_release_raw())  # <- release.yml only
```

So a new `.github/workflows/anything.yml` containing
`uses: some-vendor/thing@main`, a `continue-on-error: true`, a
`runs-on: ubuntu-latest` and no `timeout-minutes` passes the entire suite green.
That is the mutable-tag supply-chain risk both workflow headers spend paragraphs
arguing against, reachable by adding a file rather than by editing one.

The file's own docstring claims the privilege rule "is the only rule here that
looks beyond `ci.yml`" and will "still be doing work in a year" — which is
exactly the reason the *other* rules should also be directory-wide.

**Fix:** Convert the four file-scoped rules into directory-wide ones. The rule
functions are already pure, so this is a test change only:

```python
def test_every_action_in_every_workflow_is_pinned_to_a_trusted_owner() -> None:
    bad = {
        name: _unpinned_actions(_action_pins(text))
        for name, text in _all_workflow_texts().items()
        if _unpinned_actions(_action_pins(text))
    }
    assert bad == {}, bad


def test_no_workflow_in_this_directory_can_flatten_an_exit_code() -> None:
    bad = {
        name: _flattening(_code(text))
        for name, text in _all_workflow_texts().items()
        if _flattening(_code(text))
    }
    assert bad == {}, bad
```

and the same shape for `_floating_runners` and the `timeout-minutes` check. Keep
the two existing per-file tests as well — the count assertions
(`len(pins) == 5`) are still worth having.

---

### WR-03: `check_target_browser`'s new retry has no test of any kind

**File:** `boty/retailers.py:574-580`

**Issue:** The retry is new production code on the browser rung:

```python
page = fetch_rendered(watch.target)
if parse.add_to_cart_offers(page.text) is None:
    page = fetch_rendered(watch.target, settle_seconds=_TARGET_RETRY_SETTLE)
```

`grep -rn "TARGET_RETRY\|settle_seconds" tests/` returns only
`tests/test_browser.py` (which stubs `_render`'s signature) — nothing asserts
that a control-less first render triggers a second `fetch_rendered`, that the
second call receives `settle_seconds=_TARGET_RETRY_SETTLE`, or — the direction
that actually costs something — that a control-bearing first render does **not**
retry. The three existing `check_target_browser` tests
(`test_retailers.py:1729`, `1745`, `1758`) all raise from the *first*
`fetch_rendered`, so they exit before the new line and would pass unchanged if
the condition were inverted or deleted.

None of the eight mutations in `scripts/mutation_check.py` touches this either.
This is the failure class `CONTRIBUTING.md` and every workflow header in this
phase are written about: behaviour that has never been watched. An inverted
condition would double every Target browser render on the happy path (against
REQ-08's 120 s budget) and remove the retry from the path it was added for, and
`make verify` would stay green.

**Fix:** Two tests against a counting stub, in `tests/test_retailers.py`:

```python
def test_target_retries_once_at_the_patient_settle_when_no_control_rendered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[float | None] = []

    def _fake(url: str, *, settle_seconds: float | None = None, **kw: object) -> Page:
        calls.append(settle_seconds)
        return Page(text="<html><body>still rendering</body></html>", status=200, url=url)

    monkeypatch.setattr(retailers, "fetch_rendered", _fake)
    r = retailers.check_target_browser(_target_watch())

    assert calls == [None, retailers._TARGET_RETRY_SETTLE]
    assert r.availability is Availability.UNKNOWN   # two empty renders never guess


def test_target_does_not_re_render_when_the_first_page_carries_the_control(
    monkeypatch: pytest.MonkeyPatch, target_control: str
) -> None:
    calls: list[object] = []

    def _fake(url: str, **kw: object) -> Page:
        calls.append(kw)
        return Page(text=target_control, status=200, url=url)

    monkeypatch.setattr(retailers, "fetch_rendered", _fake)
    assert retailers.check_target_browser(_target_watch()).availability is Availability.IN_STOCK
    assert len(calls) == 1, "the happy path paid for a second browser render"
```

---

### WR-04: `LdJsonRead.summary` hides the unparseable count whenever anything was repaired

**File:** `boty/parse.py:145-152`

**Issue:**

```python
@property
def summary(self) -> str:
    if self.repaired:
        return f"{self.repaired} of {self.blocks} ld+json block(s) needed escape repair"
    if self.unparseable:
        return f"{self.blocks} ld+json block(s) present, {self.unparseable} unparseable"
    return ""
```

The two branches are mutually exclusive, but the underlying counters are not.
Demonstrated against the shipped code — three blocks, one repaired, two
unparseable:

```
blocks 3 repaired 1 unparseable 2
summary: 1 of 3 ld+json block(s) needed escape repair
```

`summary` is only ever appended in the two no-offers `UNKNOWN` branches of
`_verdict_from_html` (`boty/retailers.py:217`, `231`). So in the mixed case the
operator is told the markup "needed escape repair" — implying the repair worked
— on a page where two thirds of the blocks could not be read at all. That is the
same shape of misdirection the class was created to close: `LdJsonRead`'s own
docstring says a message that "was true and pointed at the wrong thing entirely
… cost real time before the second was found".

The combination is untested. `tests/test_parse.py` covers repaired-only
(line 445) and unparseable-only (line 468); no fixture has both.

**Fix:** Report both counts when both are non-zero:

```python
@property
def summary(self) -> str:
    """A phrase for `Result.detail`. Empty when there is nothing worth saying."""
    parts = []
    if self.repaired:
        parts.append(f"{self.repaired} of {self.blocks} ld+json block(s) needed escape repair")
    if self.unparseable:
        parts.append(
            f"{self.unparseable} of {self.blocks} ld+json block(s) unparseable"
            if self.repaired
            else f"{self.blocks} ld+json block(s) present, {self.unparseable} unparseable"
        )
    return "; ".join(parts)
```

and add the mixed-case test:

```python
def test_a_partly_repaired_read_still_reports_what_it_could_not_read() -> None:
    read = ldjson_read(_BESTBUY_ESCAPED_BREADCRUMB + _JUNK_BLOCK + _JUNK_BLOCK)
    assert (read.repaired, read.unparseable) == (1, 2)
    assert "repair" in read.summary and "unparseable" in read.summary
```

---

### WR-05: `release_check.py` extracts both artefacts with no member-path validation

**File:** `scripts/release_check.py:355-362`

**Issue:**

```python
if artifact.name.endswith(".whl"):
    with zipfile.ZipFile(artifact) as zf:
        zf.extractall(dest)
else:
    with tarfile.open(artifact) as tf:
        tf.extractall(dest)
```

`tarfile.extractall` with no `filter=` is the CVE-2007-4559 pattern: a member
named `../../…` or an absolute path or a symlink escapes `dest`. It also
emits a `DeprecationWarning` on the Python 3.12/3.13 interpreters this box runs
(verified: `.venv` is 3.12.3), and on **Python 3.14 the default becomes
`filter='data'`**, which will change this call's behaviour with nobody having
edited the line — the exact "a floating thing moved under a green tree" failure
`ci.yml:105-111` pins `ubuntu-24.04` to avoid.

Exploitability today is nil — the tarball is built by `python -m build` from
this repo's own tracked files, seconds earlier, in the same process tree — so
this is robustness and forward-compatibility, not a live vulnerability. But this
is the one script in the repo that unpacks an archive, it is run immediately
before a publish, and the fix is one keyword.

**Fix:**

```python
if artifact.name.endswith(".whl"):
    with zipfile.ZipFile(artifact) as zf:
        zf.extractall(dest)
else:
    with tarfile.open(artifact) as tf:
        # `filter="data"` refuses absolute paths, `..` escapes, symlinks and
        # device nodes. Available from 3.10.12 (backported), which is at or
        # below the floor `requires-python` declares. It becomes the default in
        # 3.14; naming it means this call does not change behaviour under us.
        tf.extractall(dest, filter="data")
```

---

### WR-06: `_tracked_top_level_dirs` does not list tracked files, and its parser breaks on spaces

**File:** `tests/test_packaging_metadata.py:350-390`

**Issue:** Two problems in one function.

1. The name, the docstring ("Top-level directories git reports"), the exception
   class (`NotATrackedTree`) and the assertion message ("these **tracked**
   top-level directories have no `prune` line", line 464) all say *tracked*. The
   command is:

   ```python
   ["git", "ls-files", "--cached", "--others", "--exclude-standard"]
   ```

   `--others` lists **untracked** files that are not gitignored. The docstring
   goes on to justify reading git "so this is a rule about what the repository
   ships rather than about what happens to be on this disk — a `.venv`, a
   `dist/` or a stray scratch directory is not a packaging decision anybody
   made", which is the opposite of what `--others` does: an untracked,
   un-ignored `notes/` turns `make verify` red on a contributor's machine.

   The `--others` behaviour is arguably *correct* (an sdist is built from the
   working tree, so untracked files really can ship), and `.gitignore`'s new
   `.ruff_cache/` entry shows the authors know it. The defect is that four
   separate pieces of prose say the wrong thing about it, and in this repo a
   comment is a decision record.

2. `entries = proc.stdout.split()` splits on **any** whitespace. `git ls-files`
   does not quote a path containing a plain space (`core.quotePath` only affects
   non-ASCII), so a tracked `my notes/file.md` yields entries `my` and
   `notes/file.md`, and the rule invents a top-level directory `notes` that has
   no `prune` line — a false red nobody can act on.

**Fix:** Rename and re-word, and split on newlines (or use `-z`):

```python
def _top_level_dirs_that_could_ship(root: Path) -> set[str]:
    """Top-level directories git reports under ``root`` — tracked AND untracked-
    but-not-ignored, because an sdist is built from the WORKING TREE and both
    kinds can end up in it. `.gitignore` is what removes something from this
    answer, which is why `.ruff_cache/` has an entry there.
    ...
    """
    proc = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root, capture_output=True, text=True,
    )
    ...
    entries = [e for e in proc.stdout.split("\0") if e]
```

and change the assertion message at line 464 from "tracked top-level
directories" to "top-level directories that could reach the sdist".

---

### WR-07: `.gitignore`'s justification for `.ruff_cache/` names a gate that cannot see it

**File:** `.gitignore:11-15`

**Issue:** The new comment reads:

> …this repo's gates enumerate files THROUGH git (identity_check.py --all, and
> the packaging test's tracked-top-level-dirs rule). A change upstream would
> surface as a confusing red packaging test rather than as an obvious cache
> directory.

`scripts/identity_check.py::_tracked_files` (line 363) runs
`git ls-files -z` with **no** `--others`, so it only ever sees files that have
been `git add`-ed. A cache directory that is never staged is outside its scope
whether or not `.gitignore` names it. The `identity_check.py --all` half of the
justification is simply not true; only the packaging-test half is (WR-06), and
the last sentence of the comment already says so correctly.

This matters because the next person to widen or narrow the ignore list will
reason from a stated rationale that half of which is wrong, and because
`identity_check.py`'s scope is the one thing in this repo nobody should be
confused about.

**Fix:** Drop the incorrect clause:

```
# Belt-and-braces. Ruff writes .ruff_cache/.gitignore containing `*`, so the
# cache already self-ignores — but that is ruff's implementation detail rather
# than a contract, and `tests/test_packaging_metadata.py`'s sdist prune rule
# enumerates through `git ls-files --others --exclude-standard`, which DOES see
# an untracked, un-ignored directory. (`scripts/identity_check.py --all` does
# not — it reads `git ls-files` with no `--others`, so an unstaged cache is
# outside its scope either way.) A change upstream would surface as a confusing
# red packaging test rather than as an obvious cache directory.
.ruff_cache/
```

---

## Info

### IN-01: `release_check.py`'s check 2 is a hardcoded `True`

**File:** `scripts/release_check.py:478-479`

```python
# 2. Both artifacts exist. (`_build` raises otherwise; this records it.)
_report(results, "both artifacts built", True, f"1 sdist, 1 wheel in {work / 'dist'}")
```

The condition is genuinely enforced — `_build` raises `ReleaseCheckError` unless
there is exactly one of each — and the comment says so. But the final line
prints `release check: PASSED — {len(results)}/{len(results)} checks, sdist and
wheel proven`, so a tautology is counted in the denominator of the number a
maintainer reads before publishing. In a repo whose stated position is that a
gate which cannot fail is worse than no gate, that is worth either removing or
demoting to a `print(f"  ..    …")` line beside the two size lines above it.

**Fix:** Replace with `print(f"  ..    1 sdist, 1 wheel in {work / 'dist'}")`, so
`results` holds nine checks that can all fail.

---

### IN-02: `build_sandbox()` leaks its temp tree, and a missing `git` escapes `HarnessError`

**File:** `scripts/mutation_check.py:298-310`, `313-349`; callers at `396-413`, `434-460`

**Issue:** `_git_or_harness_error` only inspects `proc.returncode`; if `git` is
not installed, `subprocess.run` raises `FileNotFoundError`, which is neither a
`HarnessError` nor caught anywhere, so `make verify` dies with a raw traceback
instead of the message the module's contract promises. And both callers do
`sandbox = build_sandbox()` **outside** their `try:`/`finally:`, so any raise
inside `build_sandbox` — including the two new git calls — leaves the
`mkdtemp` tree behind. Nine sandboxes per run makes that cheap to notice and
cheap to accumulate.

**Fix:**

```python
def _git_or_harness_error(argv: list[str], tmp: Path) -> None:
    try:
        proc = subprocess.run(argv, cwd=tmp, capture_output=True, text=True)
    except OSError as exc:                       # git not installed, or not executable
        raise HarnessError(
            f"cannot give the sandbox a git index: {' '.join(argv)} could not be run "
            f"in {tmp} ({type(exc).__name__}: {exc})"
        ) from exc
    if proc.returncode != 0:
        ...
```

and in `build_sandbox`, wrap everything after `mkdtemp` so the tree is removed
on the raising path:

```python
tmp = Path(tempfile.mkdtemp(prefix="boty-mutation-"))
try:
    ...  # copy loop, git init, git add
except BaseException:
    shutil.rmtree(tmp, ignore_errors=True)
    raise
return tmp
```

---

### IN-03: `RULES` is hand-maintained, so a renamed rule silently leaves the no-file-reads net

**File:** `tests/test_ci_workflow.py:668-682`, `707-728`

`test_no_rule_function_in_this_file_reads_a_file` walks `tree.body` and only
inspects functions whose name is in the 20-entry `RULES` tuple. Nothing asserts
that `RULES` covers every rule function in the module, so renaming `_flattening`
or adding `_new_rule` removes it from the check with no signal — the same
"passes by not running" shape this file's own docstring is written against.
(`_jobs`, `_steps` and `_publish_job` are already outside it today; they happen
to be pure.)

**Fix:** Assert completeness against the module's own AST, exempting `_raw` and
`_release_raw` by name since reading the file is their job:

```python
_ALLOWED_READERS = {"_raw", "_release_raw", "_workflow", "_release",
                    "_all_workflow_texts", "_load_packaging_metadata",
                    "_corrupt", "_corrupt_release"}

def test_every_rule_function_is_listed_in_RULES() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    defined = {
        n.name for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name.startswith("_")
        and n.name not in _ALLOWED_READERS
    }
    assert defined == set(RULES), sorted(defined ^ set(RULES))
```

---

### IN-04: Two decision comments carry counts this phase itself made stale

**Files:** `pyproject.toml:236`, `Makefile:115-116`

- `pyproject.toml:236` — "so a bare `ruff check` from the repo root judges the
  same **35 files** for everyone". Measured now: the `[tool.ruff] include` globs
  match **39** files. 04-04 through 04-06 added `tests/test_ci_workflow.py`,
  `tests/test_packaging_metadata.py`, `tests/test_contributor_docs.py` and
  `scripts/release_check.py` — the number went stale inside the phase that wrote
  it.
- `Makefile:115-116` — "measured on this box at 0.02s over **35 files** … before
  a **460-test** run". The suite is now 531 tests (observed in this review's
  `make verify-offline` run).

Both are present-tense claims rather than dated measurements (contrast
`ci.yml:136-138`, which says "Measured on 2026-08-04: … 145 files" and is
therefore still correct as a record even though the tree now reports 155).

**Fix:** Either date them the way `ci.yml` does — "Measured 2026-08-04: 39
files" — or drop the count and keep the ratio, which is the load-bearing part
(`lint` is the cheapest stage, and cheaper than mypy).

---

### IN-05: `_repair_ldjson` does not track string state across an escaped quote

**File:** `boty/parse.py:78-107`

The docstring claims the function "tracks string state rather than running a
blind replace, because the next retailer to break this way will not be so tidy".
It does — except for one transition. `in_string` is only toggled in the
non-escape path:

```python
if ch == "\\":
    ...
    i += 2
    continue

if ch == '"':
    in_string = not in_string
```

so a `\"` encountered while `in_string is False` emits a `"` (via the
`.get(nxt, nxt)` fallback) **without** toggling. On a fully doubly-escaped block
(`{\"@type\":\"Product\"…}`) this is self-correcting — every level of escaping
is stripped uniformly and the result parses correctly, which I verified — but on
a *partly* doubly-escaped block the state machine is desynchronised for the rest
of the input. I could not construct a payload where that produces
parseable-but-wrong data rather than a parse failure (which lands safely in
`unparseable`), which is why this is Info and not a Warning; it is recorded
because the docstring makes a stronger claim than the code supports.

**Fix:** Toggle on the structural quote in the outside-a-string branch:

```python
else:
    # A backslash outside a string is structural damage. `\n`, `\t` and `\r`
    # stood in for real whitespace; `\"` is a string delimiter that was escaped
    # a second time, so it opens or closes a string exactly as a bare `"` does.
    if nxt == '"':
        in_string = not in_string
        out.append('"')
    else:
        out.append({"n": "\n", "t": "\t", "r": "\r"}.get(nxt, nxt))
    changed = True
```

with a regression test for the mixed shape.

---

### IN-06: Target's retry discards a usable first render if the second one is refused

**File:** `boty/retailers.py:574-580`

Both `fetch_rendered` calls sit inside one `try:`, and the second overwrites
`page`. If the first render produced markup that `_verdict_from_html` could read
through `ld+json` or `__NEXT_DATA__` — but not through `add_to_cart_offers` —
and the second render raises `Blocked` or `FetchError`, the adapter returns
`UNKNOWN` even though a verdict was already in hand.

Today this is unreachable: Target ships no structured data on its PDPs
(confirmed against `tests/fixtures/target/control-dust-cloths.html` —
`ldjson_read` finds 0 blocks, `nextdata_offers` returns `None`), so
`add_to_cart_offers` really is the only reader and a first render without it
would read `UNKNOWN` anyway. It fails safe in every case. It becomes live the
day Target adds JSON-LD, and it is worth a line of comment now.

**Fix:** Either state the coupling —

```python
page = fetch_rendered(watch.target)
# `add_to_cart_offers` is the ONLY reader that answers for Target — its PDPs
# ship no ld+json and no __NEXT_DATA__ (fixture: control-dust-cloths). So
# "no control" and "no verdict" are the same condition, and re-rendering
# cannot cost a reading. If Target ever publishes structured data, this
# condition has to widen or the retry has to keep the first page.
if parse.add_to_cart_offers(page.text) is None:
```

— or keep the first page and only adopt the retry when it improves on it:

```python
first = page
try:
    page = fetch_rendered(watch.target, settle_seconds=_TARGET_RETRY_SETTLE)
except (Blocked, FetchError):
    page = first
```

---

_Reviewed: 2026-08-06_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
