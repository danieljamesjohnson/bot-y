# Deferred items — Phase 6

Out-of-scope discoveries, logged rather than fixed. Each names the plan that
found it and why it was not that plan's to touch.

## D-06-01-a — `scripts/mutation_check.py`'s module docstring says "three mutations"

**Found during:** 06-01, Task 3. **Not fixed.**

The docstring opens *"this corrupts three specific things in `boty` and requires
the suite to notice each one"* and then *"The three mutations are not
arbitrary"*, enumerating M1-M3. The harness registered 16 before this plan and
18 after it. The claim was already false at 16 and 06-01 did not make it more
false — it is pre-existing drift, and the scope boundary says a plan fixes what
its own changes broke.

It is nonetheless exactly this milestone's subject: a document asserting a
number that the code beside it contradicts. Whoever picks it up should note that
the count has drifted six times without anybody noticing, which argues for a
test that reads `len(MUTATIONS)` rather than a fresh hand-written number.
