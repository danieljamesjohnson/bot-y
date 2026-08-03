---
phase: 03-the-hard-two
fixed_at: 2026-08-03T00:00:00Z
review_path: .planning/phases/03-the-hard-two/03-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
deferred: 8
status: all_fixed
---

# Phase 3: Code Review Fix Report — The Hard Two

**Fixed at:** 2026-08-03
**Source review:** `.planning/phases/03-the-hard-two/03-REVIEW.md`
**Iteration:** 1

**Summary:**

- Findings in scope: 6 (CR-01, CR-02, WR-01 – WR-04)
- Fixed: 6
- Skipped: 0
- Deferred (Info, out of scope): 8

Every fix is pinned by at least one test that was watched failing against the
unfixed code first, with the failure output recorded in its commit message. The
review's two critical findings were reproduced before anything was changed, and
both reproductions now run as tests against the real tree.

## What the review got right about the root cause

The prompt's reading was correct and it changed the shape of the work: **WR-04
is the root cause of CR-01 and WR-01, and fixing it properly fixed both.** Three
independent readers of `docs/retailer-evidence.md` existed and two had already
drifted apart in both available dimensions at once — `evidence_check`'s splitter
was a dict (wrong, WR-01) with an anchored verdict regex (right), while
`tests/test_retailers._target_section` was a list (right) with a bare substring
test (wrong, CR-01). Neither file had both halves. So the fix was one splitter
and one verdict grammar, imported everywhere, rather than three local patches —
and WR-02's fence stripping then landed for the Target guard for free, which
`test_the_target_guard_inherits_the_gates_fence_handling` pins.

## Fixed Issues

### WR-01: `split_sections` collapsed identical headings

**Files modified:** `scripts/evidence_check.py`, `tests/test_evidence_check.py`
**Commit:** `d84bc05`

Reproduced first, in both orders:

```
dup  (REFUSED then REACHABLE) -> []
dup2 (REACHABLE then REFUSED) -> []
sections: ['Amazon (amazon.com)']
```

`split_sections` now returns `list[tuple[str, str]]`; `sections_for` filters it.
Two new tests, both watched failing against the dict implementation.

### WR-02: Fenced code blocks parsed as real sections and real verdicts

**Files modified:** `scripts/evidence_check.py`, `tests/test_evidence_check.py`
**Commit:** `3212137`

Reproduced: a document whose only content was "Nothing was actually probed." and
a fenced `## Amazon` template returned `check_retailer("Amazon", doc) == []`.
`strip_fences` runs at the head of `split_sections`. A third test reads the real
1400-line log and asserts the strip leaves its 9 headings and 5 verdicts intact,
so a mispairing fence regex cannot quietly swallow a section — that one passes
before and after by design; it guards the fix rather than pinning it.

### CR-01: The Target drift guard's branch selector was a bare substring test

**Files modified:** `tests/test_retailers.py`
**Commit:** `5af59a2`

Reproduced exactly as the review reported, before any change:

```
anchored verdict lines in Target section: 1
raw substring occurrences in Target section: 3
guard sees refused? -> True
problems reported on a flipped-to-REACHABLE tree: []
```

`_target_section` is gone; the guard imports `split_sections`, `sections_for`
and `verdict_lines` and compares the one anchored verdict line for equality. The
regression test flips **only** the anchored line, asserts the two prose mentions
survive, and asserts all three REACHABLE-branch problems fire. A complement test
asserts the surviving prose still reads as REFUSED, so the fix cannot degenerate
into "always take the other branch".

### WR-04: Three reimplementations of the splitter, two of the verdict test

**Files modified:** `tests/test_retailers.py`
**Commit:** `0b43a57`

Two pins that keep the readers from re-diverging: an identity check that
`_REFUSED` **is** the gate's constant rather than a retyped copy (verified: two
equal literals in separate modules are distinct objects in CPython, so a retype
fails it), and a behavioural check that the Target guard inherits `strip_fences`.
Both watched failing against a restored private reader.

The third parser the review names, `test_support_matrix._matrix`, reads the
README table — a different document with a different grammar — so it was left
alone. IN-09 covers its own robustness and is deferred.

### CR-02: The count had a ceiling and no floor

**Files modified:** `scripts/evidence_check.py`, `tests/test_evidence_check.py`,
`tests/test_support_matrix.py`, `README.md`
**Commit:** `109bd92`

Reproduced end to end on a copy of the tree — gamestop and walmart watches
deleted, two REFUSED sections appended, README untouched:

```
configured retailers: ['bestbuy', 'nintendo']   watches: 3
README still shows: | GameStop | 1 | ... | ✅ Working |
                    | Walmart  | 1 | ... | ✅ Working |
253 passed in 1.07s
evidence check: PASS — phase
```

Two rules, both offline, both reading evidence already on disk:

- **`evidence_check` rule 4 — a refusal cannot outrank a capture.** An
  unconfigured roadmap retailer whose `tests/fixtures/<key>/` holds a `*.html`
  is a dropped watch, not a refusal. Keyed on `*.html` rather than on the
  directory, so an empty leftover folder cannot redden the gate.
- **`test_support_matrix._overstated`** — no row may claim a working rung (1–3)
  for a retailer nothing watches.

`check_phase` now takes `fixture_root` as a **required** argument. A default
would be inherited silently by every synthetic case in
`tests/test_evidence_check.py`, whose stated invariant is that nothing in it
reads the shipped tree — rule 4 would then have been enforced against the repo's
four real capture directories while the test believed it described its `tmp_path`.

Nine new tests. The rule-4 ones were driven red against a **neutered rule body**
rather than merely a changed signature, so the recorded failure is the reviewer's
`[]` and not a `TypeError`. Two of them run the reproduction against the real
evidence log and the real captures and assert rule 4 is the **only** rule that
fires — a floor that works only while rule 2 also happens to be broken is not a
floor.

`README.md`'s "what stops that number drifting" paragraph now says which
direction each rule points, because it previously claimed a property the tree
had in one direction only.

### WR-03: No "in scope, not yet probed" state, with the gate now unconditional

**Files modified:** `scripts/evidence_check.py`, `tests/test_evidence_check.py`,
`tests/test_support_matrix.py`, `docs/retailer-evidence.md`, `README.md`
**Commit:** `661de20`

Took the review's first option — give the honest state a name — rather than only
rewording the failure message, because a better message does not make the state
representable: the tree stays red with the same two greens available. Both halves
shipped: the grammar gained a form **and** rule 2's message now names it.

    **Verdict: UNPROBED (scoped YYYY-MM-DD)**

Deliberately not a quiet exemption. It costs more to write than the lie it
replaces: it is written in the evidence log, it carries the date the retailer
entered scope, `--phase --strict` rejects it outright (the phase-close bar), and
it **expires after 60 days** — the clock runs from the date in the line, so
touching the file does not reset it. The Phase 2 clause rotted by *persisting*;
an escape hatch that never expires is that same shape with a date on it for
reassurance. An impossible date (`2026-13-45` matches `\d{4}-\d{2}-\d{2}`) is
rejected by `date.fromisoformat` and is therefore not an UNPROBED verdict at all,
so it cannot buy silence forever.

The README rung cell may read `—` **only** while the evidence log carries the
matching verdict, so the exemption cannot leak into the `Planned` evasion the
rung rule already caught.

`test_the_shipped_tree_carries_no_unprobed_verdict` keeps the state visible:
nothing is unprobed today, and a scope expansion pays one deliberate red test to
name which retailer is waiting. 11 new tests, all watched failing against the
two-state grammar.

## Gates

All run after the last commit, on the restored tree.

| Gate | Result |
|---|---|
| `.venv/bin/python -m pytest tests/ -q` | **284 passed** (was 253; +31) |
| `.venv/bin/python -m mypy` | `Success: no issues found in 15 source files` |
| `.venv/bin/python scripts/mutation_check.py` | `6/6 mutations caught` |
| `.venv/bin/python scripts/evidence_check.py --phase` | exit **0** |
| `.venv/bin/python scripts/evidence_check.py --phase --strict` | exit **0** |
| `make verify` | exit **0** — `VERIFY: PASS (INCOMPLETE — some controls could not run on this host)` |
| `make verify` via `systemd-run` with the service `EnvironmentFile` | exit **0** — `VERIFY: PASS`, unqualified, `control check: PASS — 4/4 controls in stock` |

The INCOMPLETE in the plain shell is the documented fresh-clone case: no
`BOTY_BROWSER_PATH`, so the Best Buy rung-3 control cannot run. The service's own
environment resolves it, which is why the `systemd-run` form is the one that
matters.

No rule was weakened to make a gate pass. Every gate above was green before this
work as well; the point of the six fixes is that the gates can now **fail**.

## The repaired gate driven red, the way 03-03 did it

Each corruption applied to the real tree, `make verify` run, then reverted.
`make verify` aborts at its first stage, so all three fail before any network
request is made.

**1. A retailer added out of scope** — a `microcenter` control watch appended to
`config/products.yaml`:

```
VERIFY: FAIL (tests)
rule 1 (in scope): config/products.yaml configures 'microcenter', which is not in
the Retailer Scope table of .planning/ROADMAP.md ...
```

**2. A working retailer silently removed** — the gamestop watches deleted **and a
`**Verdict: REFUSED**` section appended** so rule 2 is fully satisfied, README
untouched. This is the exact tree that produced `253 passed` and
`evidence check: PASS — phase` before CR-02:

```
VERIFY: FAIL (tests)
FAILED tests/test_evidence_check.py::test_the_shipped_tree_passes_the_whole_phase_gate
FAILED tests/test_support_matrix.py::test_the_matrix_does_not_advertise_a_retailer_the_monitor_does_not_watch
```

Both halves of the floor fire — the gate on the capture, and the matrix on the
overstatement.

**3. A verdict flipped** — the one anchored Target verdict line changed to
`**Verdict: REACHABLE (rung 1)**`, the two prose mentions left alone. This is the
tree the shipped guard reported `[]` for:

```
VERIFY: FAIL (tests)
FAILED tests/test_retailers.py::test_the_target_verdict_and_the_shipped_tree_agree
FAILED tests/test_retailers.py::test_flipping_only_the_real_verdict_line_switches_the_guard_to_the_reachable_branch
FAILED tests/test_evidence_check.py::test_the_shipped_tree_passes_the_whole_phase_gate
```

**Restored:** `git status` clean, `make verify` exit **0**.

## Deferred — the 8 Info findings, out of scope for this pass

None was fixed and none is closed. Carried forward as-is:

| ID | Summary |
|---|---|
| IN-01 | `duration_seconds` is published but `served/boty/index.html` never renders it |
| IN-02 | Nothing gates REQ-08's two-minute budget — measured, unenforced |
| IN-03 | `boty check` consumes an alert edge without notifying (confirmed pre-existing) |
| IN-04 | Hard-coded `boty/retailers.py:177` in assertion messages, and one wrong consequence |
| IN-05 | `ROADMAP_RETAILERS` claims to mirror `.planning/ROADMAP.md`; the labels already differ |
| IN-06 | A fourth hand-maintained retailer list at `tests/test_evidence_check.py:583` |
| IN-07 | `mutation_check` does not notice a sandbox collecting fewer tests than the repo |
| IN-08 | Duplicated rationale block on `SANDBOX_CONTENTS` |
| IN-09 | Parser robustness: raw tracebacks in `check_retailer`/`check_phase`, `IndexError` in `_matrix` |

Two are worth flagging as now slightly *more* relevant, without being in scope:

- **IN-06** is unchanged in shape but now guards more: the literal retailer tuple
  at `tests/test_evidence_check.py` still will not grow when a retailer is
  settled, and WR-03 adds a state it also will not see.
- **IN-09**'s second half (`_matrix` keeping only the last row for a duplicate
  label) is the same defect class as WR-01, now fixed in `evidence_check` and
  still present in the README table parser.

## Notes

- This repo has no project-level `CLAUDE.md`; the global operating guide applied.
- `Makefile` is untouched by all six fixes (`git diff` over the range: 0 lines),
  as it was by the phase itself. The honesty gate still reaches `make verify`
  through the `test` stage.
- `--strict` is a CLI mode pinned by tests on synthetic trees only. `make verify`
  deliberately runs the gate **non**-strict, so the grace period is real; the
  expiry is what enforces it unattended.
- No request was made to target.com or amazon.com at any point. Both are settled
  at rung 4 by their own Terms, and probing them would contradict the finding the
  phase recorded. The two live control runs above touched only the four
  configured retailers.

---

_Fixed: 2026-08-03_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
