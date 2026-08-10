# Phase 5 — deferred items

Out-of-scope discoveries, flagged rather than silently fixed. Each was found
while executing a plan that did not own the file.

## From 05-02

### 1. `README.md:327` quotes a sentence the code no longer says

The systemd/`EnvironmentFile` section tells the reader the service paged with
*"control product is not reading IN_STOCK — the detector is probably broken"*.
That string was withdrawn on 2026-08-10 under REQ-15. The passage is still
*true as history* — it describes what happened on a real day — but it reads as
a quotation of live output, and a reader who greps for it will not find it.

Not fixed here: `README.md` is not in 05-02's `files_modified`, and the same
paragraph is load-bearing for the support-matrix tests, so an edit belongs in a
plan that owns the document. **Found during:** Task 2. **Suggested owner:**
05-04 (closing record) or a Phase 6 docs plan.

### 2. `boty/cli.py:~302` repeats the withdrawn rate claim in a comment

> "It is not a page, because nothing is broken and the monitor is already
> fixing it by asking less often."

Same class as the withdrawn refusal-arm sentence: *nothing is broken* is not
established by a refusal, and *fixing it by asking less often* is the rate
story that a 6-hour backoff falsified twice. It is a comment, so it is outside
`tests/test_alert_text.py`'s subject (strings that reach a person) and outside
REQ-15's text. Not fixed here because **05-02 must not touch `boty/cli.py`** —
the plan's own success criteria assert `git diff --stat` is empty for it, and
05-03 owns that file. **Found during:** Task 2. **Suggested owner:** 05-03.

### 3. `scripts/mutation_check.py`'s module docstring still says "three"

> "this corrupts three specific things in `boty`" … "The three mutations are
> not arbitrary."

Stale since M4 landed; the count is now ten. Pre-existing — not caused by
05-02, which only appended M9 and M10 — so it was left alone rather than
folded into a store-guard commit. **Found during:** Task 3.

---

Not deferred, recorded only so it is not re-reported: `CHANGELOG.md:68` and
`:149` also quote the withdrawn sentences. Those are changelog entries about
2026-08-04 and are correct as history by construction.
