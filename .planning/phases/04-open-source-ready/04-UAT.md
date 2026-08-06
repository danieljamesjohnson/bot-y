---
status: testing
phase: 04-open-source-ready
source: [04-VERIFICATION.md]
started: 2026-08-06T15:30:00Z
updated: 2026-08-06T15:30:00Z
---

## Current Test

number: 1
name: Observe CI's `pull_request` trigger firing on a real pull request
expected: |
  A `verify` job appears under Actions with event `pull_request`, runs
  `make verify-offline`, and reports success. `gh run list --workflow ci.yml`
  then returns two runs, not one.
awaiting: user response

## Tests

### 1. Observe CI's `pull_request` trigger firing on a real pull request

expected: A `verify` job appears under Actions with event `pull_request`, runs `make verify-offline`, and reports success. `gh run list --workflow ci.yml` then returns two runs, not one.
result: [pending]

why_human: The `pull_request` trigger has never fired in production — `gh run list
--workflow ci.yml` returns exactly one run, event `push`. Criterion 2's claim that CI
runs on every PR is proven by the shipped `on:` block and by 67 machine-checked contract
tests (the verifier falsified two of them live, watching the suite go red), but GitHub
honouring the trigger is platform behaviour that cannot be observed without a real PR.
This is handoff step 5, which was offered and not taken.

how: branch it, push, `gh pr create`, then close without merging.

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
pending: 1
skipped: 0
blocked: 0
deferred: 1

## Gaps

None. Neither item is a defect.

Criteria 3 and 5 stand **UNMET and unamended** by the maintainer's recorded decision, not
by a failure of the work — the same way Phase 3.1 closed its criterion 1 after the rewrite
that would have made it meetable was proposed and declined. Phase 4 is the last phase of
v1.0, so there is nowhere to defer these to: they are human verification items, not gap-closure
plans, and `/gsd-plan-phase 4 --gaps` would have nothing to plan.
