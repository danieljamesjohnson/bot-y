---
type: seed
created: 2026-08-07
source: Phase 4 code review, finding WR-01; fixed in 2ac965f, gate gap left open
relates_to: [scripts/release_check.py, MANIFEST.in, pyproject.toml, CHANGELOG.md]
---

# Nothing reads the changelog body, and it publishes

## The observation

`CHANGELOG.md` shipped for the whole of Phase 4 ending in two literal lines of
leaked agent tool-call markup:

    </content>
    </invoke>

This was not cosmetic. `MANIFEST.in:39` deliberately includes `CHANGELOG.md` in the
sdist and `pyproject.toml:179` points `[project.urls] Changelog` at it, so the markup
was on the path to PyPI — it would have shipped inside the 1.0.0 sdist and been the
changelog every installer was directed to read. **The only reason it did not publish
is that Dan deferred the release.**

The markup is gone (`2ac965f`, which also found and trimmed two older instances in
historical planning summaries; the tree greps clean for the pattern now).

## The gap that is still open

**It survived every gate in a phase whose entire idiom is gates.** Nothing reads the
changelog body:

- `release_check.py` check 10 asserts only that the file **exists**.
- `_changelog_version` reads only the first `## [x.y.z]` heading, to compare it
  against `pyproject.toml`'s version.

So the same class of defect — leaked markup, an unreplaced placeholder, a truncated
entry, a section from the wrong version — can land again tomorrow and publish, and
`make release-check` will still print 10/10.

The changelog is what a stranger reads first. This is worth closing **before** the
publish, not after.

## Shape of a fix

A rule-function gate over the changelog text, in the idiom `test_support_matrix.py`
and `test_ci_workflow.py` already established here — rules as pure functions, the
shipped file asserted against them, and the same functions run against deliberately
corrupted copies so each rule is watched going red. Candidate rules:

- No line matching leaked-markup shapes (`^</[a-z:]+>$` and friends).
- Every `## [x.y.z]` heading parses as a version, and the top one equals
  `pyproject.toml`'s.
- No unreplaced placeholder (`TODO`, `TBD`, `x.y.z`, `<...>`).
- The file ends with a newline and no trailing blank-ish garbage.

Cheap, test-only, and it closes the class rather than the instance.

## Related

- Phase 4 code review `04-REVIEW.md` also left **WR-02** open: a third
  `.github/workflows/*.yml` added later escapes the pin, exit-code, timeout and
  runner rules while `tests/test_ci_workflow.py` stays green. The verifier
  reproduced it independently. Same shape — a gate bound to filenames rather than
  to the directory it means to cover. Also test-only.
- Pairs with
  `.planning/seeds/notify-only-when-a-decision-changes-the-outcome.md`.
