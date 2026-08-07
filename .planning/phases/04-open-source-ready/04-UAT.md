---
status: resolved
phase: 04-open-source-ready
source: [04-VERIFICATION.md]
started: 2026-08-06T15:30:00Z
updated: 2026-08-07T00:00:00Z
---

## Current Test

number: 2
name: Decide whether to publish 1.0.0 to PyPI
expected: |
  Criteria 3 and 5 close.
awaiting: deferred by Dan, 2026-08-06 — no test is pending

## Tests

### 1. Observe CI's `pull_request` trigger firing on a real pull request

result: [withdrawn — not worth manufacturing]

**Withdrawn 2026-08-07 on Dan's call.** This test does not test bot-y. It tests
whether GitHub honours a `pull_request:` key, which is documented platform behaviour
and is not a property of this repository. The marginal information over what is
already observed is close to zero:

- The `push` run (`31066215395`, green) already proves the workflow file parses, the
  runner provisions, `setup-python` resolves the declared 3.10 floor, and
  `make verify-offline` passes in CI. The only untested difference is which event key
  GitHub matches on.
- The specific way this could plausibly break — a branch or path filter narrowing the
  trigger — is asserted by `tests/test_ci_workflow.py`, and the verifier proved that
  assertion bites by adding `branches: [main]` to the real file and watching 2 tests
  go red.

So the trigger will be observed the first time anyone opens a real pull request, at
zero cost, and staging a throwaway one to tick a box was ceremony. Recorded here
rather than deleted, because the reasoning is the point: *a manual test whose only
possible finding is "GitHub is broken" is not a test of this project.*

The original wording also carried a defect worth noting: its success criterion was
"`gh run list` returns two runs, not one", a row count that was silently invalidated
the moment six pending commits were pushed to `main` and produced a second `push` run.
A counting assertion over a shared, externally-appended log was never going to hold.

### 2. Decide whether to publish 1.0.0 to PyPI

expected: Criteria 3 and 5 close. `https://pypi.org/pypi/bot-y/1.0.0/json` returns 200, `git ls-remote --tags origin` returns a `v1.0.0` ref, and REQ-11 flips to Complete.
result: [deferred]

why_human: Deferred by Dan on 2026-08-06, verbatim: *"i don't think we need to host it
yet. it's probably not quite ready for that"*. Publishing permanently claims a PyPI
distribution name; it is reserved to the maintainer by `04-CONTEXT.md` § *NOT at Claude's
discretion*. **There is no code gap to close** — the verifier rebuilt and re-proved the
artifacts independently (`make release-check` → 10/10, `twine check` PASSED both, clean-venv
install runs the console script) and they are publishable today.

how: the four ordered steps on `04-06-HANDOFF.md`, which stays on disk and still matches
the tree (card says environment `pypi`; `release.yml:143` says `environment: pypi`).

## Summary

total: 2
passed: 0
issues: 0
pending: 0
skipped: 0
blocked: 0
withdrawn: 1
deferred: 1

**No test is pending.** One was withdrawn as ceremony, one is deferred by the
maintainer's decision. There is nothing here for a human to execute.

## Gaps

None. Neither item is a defect.

Criteria 3 and 5 stand **UNMET and unamended** by the maintainer's recorded decision, not
by a failure of the work — the same way Phase 3.1 closed its criterion 1 after the rewrite
that would have made it meetable was proposed and declined. Phase 4 is the last phase of
v1.0, so there is nowhere to defer these to: they are human verification items, not gap-closure
plans, and `/gsd-plan-phase 4 --gaps` would have nothing to plan.
