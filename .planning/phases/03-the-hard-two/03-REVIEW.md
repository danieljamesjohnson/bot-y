---
status: findings
phase: 03-the-hard-two
reviewed: 2026-08-03T00:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - scripts/evidence_check.py
  - tests/test_evidence_check.py
  - tests/test_support_matrix.py
  - boty/status.py
  - boty/cli.py
  - scripts/mutation_check.py
  - tests/test_retailers.py
  - tests/test_status.py
  - Makefile
  - docs/retailer-evidence.md
  - README.md
critical: 2
warning: 4
info: 8
---

# Phase 3: Code Review Report — The Hard Two

**Reviewed:** 2026-08-03
**Depth:** standard (offline; no request made to any retailer)
**Files Reviewed:** 11
**Status:** issues_found

## Summary

This phase's thesis is that a gate must be *able to fail*, and it is judged by that
bar. Measured against it, the new machinery is real but two of its guards are
already unfailable, and both fail in the same way the Phase 2 clause did: a bare
substring test over a document whose own prose contains the substring.

What holds up:

- `scripts/evidence_check.py`'s core discipline is sound. `VERDICT_RE` is
  line-anchored, `split_sections` drops the preamble by construction, and rule 1
  genuinely closes the Micro Center padding door that `control_check.py`,
  `assess_health` and the fixture test all leave open. `--phase` was driven red on
  a synthetic tree in six distinct ways during this review and it bit every time.
- REQ-08's timing is correct. Both call sites use `time.monotonic()`, both measure
  `run_once` only (`boty/cli.py:165-167`, `boty/cli.py:316-318`), the delta is
  computed inside a single process so it cannot go negative, and the diff against
  `99bcfd2` confirms **no alerting behaviour changed** — the only edits to
  `watch_cycle` and the `check` branch are the timer, the extra kwarg and one print.
- `SANDBOX_CONTENTS` is complete for the current suite. Every repo-root path any
  test reads (`served`, `README.md`, `docs`, `config`, `scripts`, `Makefile`,
  `pyproject.toml`) is listed. Fail-closed still holds: a missing file surfaces as
  pytest exit 1 or 2, and `run_baseline` treats any non-zero baseline as
  `HarnessError` → exit 2 rather than a score. Verified live: 6/6 caught, baseline
  green, mypy clean, 253 tests pass.
- The Target allow-list drift guard's *predicate* is exact.
  `tests/test_retailers.py:1165` reuses `_pick`'s own comparison
  (`seller.strip().lower() in allow_list`) and fires precisely when `_pick` would
  return `None` for a marketplace retailer. It is not a tautology: the
  `..._backed_by_the_observed_seller_string_passes` case proves the clean side.

What does not hold up: the guard above is wired to a branch selector that can no
longer switch branches (CR-01), and the new count/matrix gates enforce only the
"understated" direction, so shipped coverage can halve while `make verify` stays
green and the README goes on advertising the deleted retailers (CR-02). Both were
reproduced, not inferred.

Note: this repo has no project-level `CLAUDE.md`. `Makefile` is in the review list
but is **unchanged** in `99bcfd2..HEAD` — the honesty gate reaches `make verify`
through the `test` stage, not a new target, which is a deliberate and correctly
reasoned choice (`tests/test_evidence_check.py:587-609`).

---

## Critical Issues

### CR-01: The Target drift guard's branch selector is a bare substring test, and the REACHABLE branch is already unreachable

**File:** `tests/test_retailers.py:1132` (and `tests/test_retailers.py:1100-1112`)

**Issue.** `_target_disagreements` chooses which half of itself to run with:

```python
refused = _REFUSED in _target_section(evidence_text)
```

`_REFUSED` is the plain string `"**Verdict: REFUSED**"`. The shipped Target section
of `docs/retailer-evidence.md` contains that string **three times**: once as the
machine-readable verdict line (`docs/retailer-evidence.md:766`) and twice inside
prose — `docs/retailer-evidence.md:1013` ("So the verdict is
`**Verdict: REFUSED**`, the primary reason is…") and `:1172`. Only the first is a
verdict; the other two are the document explaining its own grammar.

This is the identical defect the phase was created to remove. The module docstring
of `scripts/evidence_check.py:8-13` names it exactly: *"a clause satisfied by
documents that predate the phase — worse than no gate at all."* `evidence_check`
already exports the correct primitives (`VERDICT_RE`, `verdict_lines`,
`sections_for`); this file declined to use them and reimplemented both the splitter
and the verdict test in the weak form.

**Reproduced.** Flip only the real, line-anchored verdict at
`docs/retailer-evidence.md:766` to `**Verdict: REACHABLE (rung 1)**`, leave the
prose alone:

```
anchored verdict lines in Target section: 1
raw substring occurrences in Target section: 3
guard sees refused? -> True
problems reported on a flipped-to-REACHABLE tree: []
```

The guard stays on the REFUSED branch against a document that no longer says
REFUSED, and reports nothing about a tree that claims Target is reachable while
shipping no watch, no control, no fixture and an unobserved allow-list.

**Concrete failure scenario.** Someone registers Target (terms change, or a
sanctioned feed appears). They edit the verdict line to REACHABLE and add a watch.
What happens:

1. The REACHABLE branch — which holds the entire allow-list drift check, the only
   thing standing between the never-observed guess `FIRST_PARTY["target"] =
   {"target"}` and a live detector — **never executes**, because `refused` is still
   `True`.
2. Instead the REFUSED branch fires with the message *"docs/retailer-evidence.md
   records `**Verdict: REFUSED**` for Target while config/products.yaml configures a
   target watch"* — a statement that is now false, about a document that says the
   opposite.
3. The natural reading of a red test whose message contradicts the file it names is
   "this assertion is stale." The assertion gets edited, the allow-list guess goes
   live, `target` is in `MARKETPLACES` so `_pick`'s unattributed fallback is
   disabled, and `boty/retailers.py:177` answers a perfectly readable Target page
   with a **confident OUT_OF_STOCK**.

That is the single worst outcome this project defines for itself, reached through
the guard built to prevent it.

**Fix.** Use the anchored, section-scoped primitives that already exist rather than
`in`. Import them instead of re-deriving `_target_section`:

```python
import importlib.util
_spec = importlib.util.spec_from_file_location("ec", _REPO_ROOT / "scripts" / "evidence_check.py")
_ec = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_ec)

def _target_verdict(evidence_text: str) -> str:
    bodies = _ec.sections_for("Target", _ec.split_sections(evidence_text))
    assert len(bodies) == 1, f"expected exactly one `## Target` section, found {len(bodies)}"
    lines = _ec.verdict_lines(bodies[0])
    assert len(lines) == 1, f"expected exactly one verdict line, found {lines}"
    return lines[0]

...
refused = _target_verdict(evidence_text) == _REFUSED
```

Add a regression case that pins the hole itself: flip only the anchored verdict
line (as above) and assert the guard now reports the REACHABLE-branch problems.
Today that test fails; that is the point.

---

### CR-02: The count and matrix gates enforce only the understating direction — shipped coverage can halve with `make verify` green and the README still advertising the removed retailers

**Files:** `scripts/evidence_check.py:244-269`, `tests/test_support_matrix.py:133-152`,
`tests/test_support_matrix.py:206-224`, `README.md:79-85`, `README.md:108-114`

**Issue.** Rule 2 says a roadmap retailer must be *configured or refused in
writing*. Rule 3 exempts a short count when neither hard-two retailer is
configured — correct, and necessary for the honest four. Together they impose a
ceiling on the count and **no floor at all**: any number of configured retailers
passes, down to zero, provided each absent one carries a `**Verdict: REFUSED**`
line. Nothing cross-checks a REFUSED verdict against the durable proof already in
the tree that the retailer *was* read — `tests/fixtures/<key>/*.html`, the same
artefact `test_no_retailer_is_configured_without_a_page_we_have_actually_read`
relies on.

The README support matrix does not cover the gap either. `tests/test_support_matrix.py`
checks `configured ⊆ documented` (`:206-224`, its docstring: *"the table would
understate what the monitor actually does, which is the one direction a reader has
no way to notice"*). The opposite and more dangerous direction — the table
**overstating** what the monitor does — is unchecked. `_rungless` only requires a
digit 1-4; `_undeclared_degraded` only looks at rung-3 rows. A row reading
`| GameStop | 1 | curl_cffi + schema.org JSON-LD | ✅ Working |` passes every rule
whether or not a gamestop watch exists.

**Reproduced end to end.** Copy of the tree, gamestop and walmart watch blocks
deleted from `config/products.yaml`, two `**Verdict: REFUSED**` sections appended
to `docs/retailer-evidence.md`, README untouched:

```
configured retailers: ['bestbuy', 'nintendo']   watches: 3
README still shows: | GameStop | 1 | ... | ✅ Working |
                    | Walmart  | 1 | ... | ✅ Working |
253 passed in 1.07s
```

Half the shipped detectors gone; `make verify`'s `test` stage fully green;
`evidence_check --phase` returns `[]`; the support matrix still tells a reader that
GameStop and Walmart are watched at rung 1 and working. (`bestbuy` and `nintendo`
happen to be pinned by pre-existing per-retailer tests at
`tests/test_retailers.py:1016` and `:1038`; gamestop and walmart have no such pin,
which is why the floor is accidental where it exists at all.)

`README.md:108` states "`scripts/evidence_check.py` is what stops that number
drifting". It stops it drifting **up**. Down is free.

**Concrete failure scenario.** A future refactor drops a watch during a config
rewrite, or a contributor "cleans up" a retailer that has been failing and writes
the refusal to make the suite green. The reader consulting the support matrix —
the surface this phase built specifically to be trustworthy — believes Walmart is
being watched. No alert ever arrives, and every gate agrees the tree is honest.

**Fix.** Two cheap, offline, mechanical rules, both using evidence already on disk:

```python
# scripts/evidence_check.py — RULE 4: a refusal cannot contradict a page we read.
FIXTURE_ROOT = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

for retailer, display in ROADMAP_RETAILERS.items():
    if retailer in configured:
        continue
    if list((FIXTURE_ROOT / retailer).glob("*.html")):
        problems.append(
            f"rule 4 (a refusal cannot outrank a capture): {display} is recorded REFUSED "
            f"and unconfigured, but tests/fixtures/{retailer}/ holds a page we really "
            "fetched. A retailer we have read is not one that refused us — either the "
            "verdict is wrong or the watch was dropped without saying so."
        )
```

and in `tests/test_support_matrix.py`, the missing direction:

```python
def test_the_matrix_does_not_advertise_a_retailer_the_monitor_does_not_watch() -> None:
    rows = _matrix()
    configured = {w.retailer for w in Config.load(CONFIG).watches}
    overstated = sorted(
        name for key, name in ROADMAP_RETAILERS.items()
        if name in rows and rows[name][RUNG][:1] in {"1", "2", "3"} and key not in configured
    )
    assert not overstated, (
        f"the matrix shows a working rung for retailers with no watch: {overstated}. "
        "Rung 4 is the only honest rung for a retailer that is not configured."
    )
```

---

## Warnings

### WR-01: `split_sections` collapses identical headings, so the duplicate-section guard cannot fire on the likeliest duplicate — and the last section silently wins

**File:** `scripts/evidence_check.py:144-149` (guard at `:191-195`)

**Issue.** `sections` is a `dict` keyed by heading text. Two sections with the
*same* heading overwrite rather than accumulate, so `sections_for` returns one
body and the bespoke "*two records of one retailer means nothing here can tell
which is current*" failure never triggers. Which body survives is
insertion-order-dependent: the **last** one wins.

Both tests covering this case use deliberately *distinct* headings —
`("Amazon (amazon.com)", "Amazon, revisited")` at `tests/test_evidence_check.py:233`
and `("Amazon (x)", "Amazon (y)")` at `:246` — so the hole is invisible to the suite.
The realistic mistake, copy-pasting or appending a re-record under the same
heading, is exactly the uncovered one.

**Reproduced.** A document with `## Amazon (amazon.com)` twice, the first carrying
REFUSED and the second REACHABLE, and again in the reverse order:

```
dup  (REFUSED then REACHABLE) -> []
dup2 (REACHABLE then REFUSED) -> []
sections: ['Amazon (amazon.com)']
```

A self-contradicting evidence log passes clean, and rule 2's verdict is whichever
record happens to be last in the file.

**Fix.** Accumulate rather than overwrite, and count matches:

```python
def split_sections(text: str) -> list[tuple[str, str]]:
    matches = list(_HEADING_RE.finditer(text))
    return [
        (m.group(1).strip(), text[m.end() : (matches[i + 1].start() if i + 1 < len(matches) else len(text))])
        for i, m in enumerate(matches)
    ]

def sections_for(display_name: str, sections: list[tuple[str, str]]) -> list[str]:
    return [body for heading, body in sections if heading.startswith(display_name)]
```

Add the missing test: two *identical* headings must produce the "2 sections"
failure.

### WR-02: Fenced code blocks are parsed as real sections and real verdicts

**File:** `scripts/evidence_check.py:133` (`_HEADING_RE`), `:125-128` (`VERDICT_RE`);
same defect in `tests/test_retailers.py:1108`

**Issue.** Neither regex excludes fenced blocks. A markdown *example* of the
format is indexed as a genuine record.

**Reproduced.** A document whose only content is a fenced example, plus the line
"Nothing was actually probed.":

````markdown
```markdown
## Amazon (amazon.com)

**Verdict: REFUSED**
```
````

`check_retailer("Amazon", doc)` returns `[]`. The gate certifies Amazon as
properly recorded in a document that records nothing — which is verbatim the
failure `scripts/evidence_check.py:17-23` was written to close, reached by a route
the preamble exclusion does not cover.

**Compounded by WR-01.** If the example uses a real retailer name (the natural
choice when documenting the format), it produces an *identical* heading to the real
section. Under WR-01 the two collapse and the last wins — so a documentation
example placed below a real record **silently replaces it**. The evidence log is
already 1400+ lines and already carries a vocabulary block; a future "## How to
record a verdict" section with a template is a realistic edit.

**Fix.** Strip fenced blocks before splitting:

```python
_FENCE_RE = re.compile(r"^(?P<f>```|~~~).*?^(?P=f)\s*$", re.MULTILINE | re.DOTALL)

def _strip_fences(text: str) -> str:
    return _FENCE_RE.sub("", text)
```

Call it at the head of `split_sections`, and add the fenced-example document above
as a test that must fail for every retailer — the same role
`test_the_preamble_alone_satisfies_nothing` plays for the preamble.

### WR-03: The grammar has no "in scope, not yet probed" state, and the gate is now unconditional in `make verify` — the fastest green for the next scope expansion is a false REFUSED

**File:** `scripts/evidence_check.py:244-256`, `:118-119`;
`tests/test_evidence_check.py:502-533`

**Issue.** Rule 2 admits exactly two states for a roadmap retailer: configured, or
carrying a written REFUSED. `VERDICT_RE` deliberately has no rung-4 REACHABLE form
and no unprobed form. `tests/test_support_matrix.py` adds a third obligation — a
README row with a rung of 1-4.

This phase hit that wall itself and routed around it: `test_the_repo_as_it_stands_after_this_plan_names_target_as_the_only_gap`
(`tests/test_evidence_check.py:502`) documents that the tree was legitimately red
between 03-01 and 03-02, and the fix was to keep the gate out of `make verify` for
one plan. **That escape no longer exists** — 03-03 wired the gate into the `test`
stage permanently.

**Concrete failure scenario.** Phase 4 (or a contributor) adds a genuinely
plausible retailer to scope. Adding it to `ROADMAP_RETAILERS` correctly reddens
`test_roadmap_retailers_is_exactly_the_seven_in_scope` — that part fails in the
right direction, a deliberate reviewable edit. But from that commit until the
retailer is settled, `make verify` is red with only two ways to go green: ship the
detector, or write `**Verdict: REFUSED**` for a store nobody has probed. The second
is one line and takes a second. A gate that makes the honest state unrepresentable
pressures exactly the padding this phase exists to prevent, just in the opposite
sign.

**Fix.** Give the honest state a name, and make it expire rather than persist:

```python
UNPROBED_RE = re.compile(r"^\*\*Verdict: UNPROBED \(scoped \d{4}-\d{2}-\d{2}\)\*\*$", re.MULTILINE)
```

Rule 2 accepts UNPROBED; a `--strict` mode (run at phase close, and the one the
phase criteria cite) rejects it. The README rung cell gains a matching `—
unprobed` form accepted only alongside an UNPROBED verdict. That keeps "no silent
gaps" — an unprobed retailer is still stated in writing, with a date — while making
the honest answer expressible.

### WR-04: Three independent reimplementations of the section splitter, two of the verdict test — and they already disagree

**Files:** `scripts/evidence_check.py:136-172`, `tests/test_retailers.py:1100-1132`,
`tests/test_support_matrix.py:96-125`

**Issue.** The evidence log is parsed by `evidence_check.split_sections` (dict,
anchored verdict regex) and independently by `tests/test_retailers._target_section`
(list, bare `in` test). They already disagree in both dimensions, and each
disagreement is a live defect: the list form is the *correct* one (WR-01), the
anchored form is the *correct* one (CR-01), and neither file has both. A third
table parser lives in `tests/test_support_matrix._matrix`.

This is the coupling `scripts/evidence_check.py:82-96` warns about in its own
constant docstring — "*two different matches on one constant, and nothing in either
file makes the coupling visible*" — realised one level down, on the parsers rather
than the names.

**Fix.** `scripts/evidence_check.py` is already imported by path in two test modules
(`tests/test_evidence_check.py:47`, `tests/test_support_matrix.py:74`). Make it the
single reader: `tests/test_retailers.py` should import `split_sections`,
`sections_for` and `verdict_lines` the same way rather than carrying its own. One
splitter, one verdict grammar, one place to fix.

---

## Info

### IN-01: `duration_seconds` is published but the dashboard does not render it

**File:** `boty/status.py:45`, `served/boty/index.html` (unchanged this phase)

The new key is served and nothing consumes it. `tests/test_status.py:131-142`
explicitly frames the payload as *"a contract with the dashboard"* and cites
`tests/test_dashboard.py` as the consuming end — but no dashboard assertion was
added, and `served/boty/index.html` never reads `duration_seconds`. This is the
shape Phase 2's WR-04 named ("a contract asserted at the producing end and quietly
unimplemented at the consuming one"), reintroduced one key along. `boty check`'s
printed line is the only human surface. Either render it beside the `updated`
age, or drop the dashboard-contract framing from the test docstring.

### IN-02: Nothing gates REQ-08's two-minute budget

**File:** `boty/cli.py:316-331`, `boty/status.py:45`

REQ-08 is marked Complete on a number that is now readable and never compared to
anything. A pass taking 400 s publishes happily and `make verify` stays green. For
a project whose thesis is that a gate must be able to fail, the budget is still
"asserted rather than measured" in the sense that matters — measured, but
unenforced. A cheap version: `boty check` prints a warning line and
`assess_health` records a non-fatal note when `duration_seconds > 120`.

### IN-03: `boty check` consumes an alert edge without notifying — CONFIRMED pre-existing

**File:** `boty/cli.py:317-322`

Verified against `git diff 99bcfd2..HEAD -- boty/cli.py`: the `check` branch at
Phase 2's close already called `run_once` (which commits transitions to
`state.seen` and saves) and then only printed `"N alertable transition(s)"`. The
only edits this phase are the `time.monotonic()` timer, the `duration_seconds`
kwarg and the summary print. **Not introduced here, correctly logged, out of
scope.** It remains open: a `boty check` run between `watch` cycles still eats the
rising edge, and `watch` will never mention that restock again.

### IN-04: Hard-coded source line numbers, and one wrong consequence, in assertion messages

**File:** `tests/test_retailers.py:1172`, `tests/test_retailers.py:1234`

Both messages cite `boty/retailers.py:177` literally. It is correct today (the
`OUT_OF_STOCK` return does begin at line 177) and will rot the first time
`retailers.py` gains a line above it. Also, the stated consequence is only true
when *every* offer names a seller: if any offer has `seller is None`,
`boty/retailers.py:163-176` returns UNKNOWN, not the "CONFIDENT OUT_OF_STOCK" the
message promises. The guard still fires correctly in that case — only the
explanation is wrong. Name the branch rather than the line
(`_verdict_from_html`'s "none first-party" return) and soften the consequence to
"a confident OUT_OF_STOCK, or an UNKNOWN if any offer is unattributed".

### IN-05: `ROADMAP_RETAILERS` claims to mirror `.planning/ROADMAP.md`, nothing checks it, and the labels already differ

**File:** `scripts/evidence_check.py:71-72`, `:97-105`

The docstring says "*Every retailer in the Retailer Scope table of
`.planning/ROADMAP.md`*", and rule 1's failure message tells the reader that table
is authoritative. Nothing compares the two, and they already disagree: the roadmap
row (`.planning/ROADMAP.md:40`) reads **"Nintendo store"**, the constant reads
"Nintendo". Harmless today because nothing parses the roadmap, but rule 1 is being
enforced against a hand-maintained copy of a document it names as the source of
truth. Either parse the roadmap table (`.planning/` is not in the mutation sandbox,
so this would need a guard) or reword the docstring to say the constant *is* the
machine-readable scope and the roadmap mirrors it.

### IN-06: A fourth hand-maintained copy of the retailer set

**File:** `tests/test_evidence_check.py:583`

`for display in ("Best Buy", "Nintendo", "Pokémon Center", "Amazon", "Target")` is
a literal list that will not grow when a retailer is settled. A newly refused
retailer gets rule-2 coverage but never the per-retailer check with its
better-worded failure. Derive it: every `ROADMAP_RETAILERS` value that has a
section in the real document.

### IN-07: The mutation harness never notices a sandbox that collects fewer tests than the repo

**File:** `scripts/mutation_check.py:239-256`

`run_baseline` requires exit 0, which is what caught the missing `docs/` and
`README.md` — the fail-closed property holds and was verified. But it only detects
a missing file when some test *errors* on it. A test that degrades gracefully
(`if path.exists():`, `pytest.skip`, a `try/except FileNotFoundError`) would leave
the baseline green while the sandbox silently runs a smaller suite, and every
mutation would then be scored against it. One line closes it: capture the
collected count in the baseline and compare it to `pytest --collect-only -q` in the
repo, raising `HarnessError` on any difference.

### IN-08: Duplicated rationale block on `SANDBOX_CONTENTS`

**File:** `scripts/mutation_check.py:55-89`

Two consecutive `#:` blocks explain the same constant; the second restarts with
"Everything the suite reads." and re-covers `pyproject.toml`, `scripts` and
`Makefile` already covered by the first. It reads as an unmerged edit rather than
deliberate emphasis. Merge into one block.

### IN-09: Parser robustness — raw tracebacks and IndexError paths

**Files:** `scripts/evidence_check.py:184`, `:229-231`;
`tests/test_support_matrix.py:124`, `:137-142`

- `check_retailer` / `check_phase` let `FileNotFoundError` (and any `Config.load`
  error) escape as a traceback rather than a structured problem. The process still
  exits non-zero so the gate fails closed, but the output is not the actionable
  message every other failure path takes care to produce. Catch `OSError` and
  append a problem.
- `_matrix` stores `rows[cells[RETAILER]] = cells` — a duplicate retailer label
  silently keeps only the last row (same class as WR-01), and a row with fewer
  than two cells makes `_rungless` raise `IndexError` instead of asserting. Assert
  `len(cells) == len(HEADER_CELLS)` per row and reject duplicate labels.

### IN-10: `status.write` documents a caller obligation it does not enforce

**File:** `boty/status.py:42-44`

"Callers must time with `time.monotonic()`, never `time.time()`" is exactly right,
and both current callers obey. Nothing stops a third one from passing a wall-clock
delta and publishing a negative duration into a file served over HTTP — the failure
the comment describes. One line makes the rule enforceable:

```python
if duration_seconds is not None and duration_seconds < 0:
    log.error("refusing to publish a negative duration (%r) — caller used a wall clock", duration_seconds)
    duration_seconds = None
```

`None` is already the honest "nobody timed this", so the degradation is
well-defined.

---

_Reviewed: 2026-08-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard — offline only; no request was made to target.com or amazon.com_
