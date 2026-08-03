---
phase: 03-the-hard-two
plan: 01
subsystem: testing
tags: [amazon, terms-of-use, robots-txt, evidence, gate, retailer-scope, creators-api, tdd]

requires:
  - phase: 02-five-retailers-green
    provides: the evidence-log format, the verdict grammar, control_check.py's configured-minus-verified rule, and the Pokémon Center rung-4 precedent
provides:
  - Amazon settled at rung 4 by its Conditions of Use, with the clause quoted, dated, and zero product-page requests ever made
  - scripts/evidence_check.py — a per-retailer honesty gate that replaces Phase 2's count clause, which had decayed into one that could not fail
  - ROADMAP_RETAILERS, the machine-readable retailer scope that makes a padded count a visible edit rather than a quiet YAML line
  - README support-matrix row for Amazon at rung 4
affects: [03-02 Target, 03-03 phase close, 04-01 contributor docs]

tech-stack:
  added: []
  patterns:
    - "Read the terms before the wall: a written prohibition outranks a technical finding and is cheaper to obtain"
    - "A gate's escape hatch must not be a bare substring test — the document's own vocabulary preamble satisfies one"
    - "Constants whose values are matched literally in two different ways get both obligations stated in the comment and asserted in a test"

key-files:
  created:
    - scripts/evidence_check.py
    - tests/test_evidence_check.py
  modified:
    - docs/retailer-evidence.md
    - README.md
    - QUESTIONS.md
    - scripts/mutation_check.py

key-decisions:
  - "Amazon is rung 4, settled by its Conditions of Use rather than by a wall — the licence excludes 'any collection and use of any product listings, descriptions, or prices', which is exactly and only what bot-y reads"
  - "Zero requests were made to any Amazon product page, at any rung, so the evidence log can state that bot-y makes no requests to amazon.com as a fact rather than a policy"
  - "Amazon's robots.txt is narrower than its ToU and the two disagree: /dp/<ASIN> carries no Disallow while /dp/product-availability/ and /gp/offer-listing/ do — the broader written document governs"
  - "Rung 2 is closed twice over: PA-API 5 is deprecated and answers HTTP 403, and its successor the Creators API requires an Associates commercial agreement, a tax interview and per-region approval, which a fresh clone cannot obtain"
  - "The count gate is per-retailer, not per-document: docs/retailer-evidence.md states both verdict strings in its own preamble, so any whole-file substring test passes against a document recording nothing"
  - "ROADMAP_RETAILERS is asserted literally in a test because its values are matched two different ways — as an evidence-heading PREFIX and as an EXACT README row label — and they agree only by luck of capitalisation"
  - "evidence_check.py --phase is deliberately NOT wired into make verify until 03-03: Target is genuinely unrecorded until 03-02, and weakening rule 2 so today's tree passes would reintroduce the Phase 2 defect one layer out"

patterns-established:
  - "Terms-first ladder walking: retrieve and quote the retailer's own terms before spending any transport work, so a prohibition settles the question at zero cost to the host's IP"
  - "Scope-as-code: the roadmap's retailer list lives in an executable constant so adding an out-of-scope retailer fails a gate instead of moving a counter"

requirements-completed: []  # REQ-07 is HALF done and deliberately left Pending — see below

duration: 34min
completed: 2026-08-03
---

# Phase 3 Plan 01: Amazon and the Unpaddable Count Summary

**Amazon settled at rung 4 by its own Conditions of Use — quoted, dated, and reached without ever fetching a product page — plus `scripts/evidence_check.py`, a per-retailer gate that replaces Phase 2's count clause after that clause decayed into one that could not fail.**

## Performance

- **Duration:** ~34 min
- **Started:** 2026-08-03T04:02:00Z
- **Completed:** 2026-08-03T04:36:00Z
- **Tasks:** 3 (one of them TDD, so 4 commits)
- **Files modified:** 6 (2 created, 4 modified)

## Accomplishments

- **Amazon is rung 4, and the reason is written rather than technical.** Its
  Conditions of Use grant a licence that explicitly excludes "any collection and
  use of any product listings, descriptions, or prices" — availability and price
  are the only two fields bot-y reads. That is a stronger prohibition than
  Pokémon Center's, which forbids the *method* and leaves room to argue about
  what counts as one; Amazon forbids the method *and independently* names the
  data.
- **Zero product-page requests, at any rung.** The terms were read first, on
  purpose, so `docs/retailer-evidence.md` can state as a fact — not a policy —
  that bot-y makes no requests to amazon.com. Pokémon Center cost ten probes
  across two transports before a desk review produced the reason that actually
  settled it; this cost six policy reads and no transport work at all.
- **`scripts/evidence_check.py` exists and has been watched failing** on a
  padded config, a missing verdict, four shapes of malformed verdict string, an
  inconsistent count, and a duplicated section. 23 new tests.
- **The four Phase 2 retailers are still control-green**, and `make verify`
  exits 0 with `VERIFY: PASS` under the service's own `EnvironmentFile`.

## Task Commits

1. **Task 1: Read Amazon's terms before touching its transport** — `9a3e9e0` (docs)
2. **Task 2 (RED): failing tests for the unpaddable retailer-count gate** — `deb1244` (test)
3. **Task 2 (GREEN): `evidence_check.py`** — `d14280e` (feat)
4. **Task 3: Amazon settled at rung 4 — no watch, no fixture, no request** — `67e00ad` (docs)

No REFACTOR commit: the implementation went green without needing one.

## Files Created/Modified

- `scripts/evidence_check.py` — the honesty gate. `--retailer <display name>`
  checks one section; `--phase` applies three rules over the whole tree.
- `tests/test_evidence_check.py` — 23 tests, most of which are the gate being
  watched fail.
- `docs/retailer-evidence.md` — the `## Amazon (amazon.com)` section: six
  requests with byte counts, the clause quoted in full, the robots.txt
  disagreement, the rung-2 evaluation, what was not done, and a do-not-re-probe
  note.
- `README.md` — Amazon row at rung 4; the "four working retailers, not five"
  paragraph now distinguishes the two dropped retailers and names the gate.
- `QUESTIONS.md` — `## 0a. Amazon is rung 4`, in the shape of the existing
  Pokémon Center heads-up.
- `scripts/mutation_check.py` — `docs` added to `SANDBOX_CONTENTS`.

## The requested record

**Conditions of Use.** Requested
`https://www.amazon.com/gp/help/customer/display.html?nodeId=508088`, which
redirects to the current canonical
`https://www.amazon.com/gp/help/customer/display.html?nodeId=GLSBYFE9MGKKQXXM`.
HTTP 200, 344,140 B. Retrieved **2026-08-03**. Document header:
`Last updated: May 30, 2025`.

**The operative clause,** from `LICENSE AND ACCESS`:

> Subject to your compliance with these Conditions of Use and any Service Terms,
> and your payment of any applicable fees, Amazon or its content providers grant
> you a limited, non-exclusive, non-transferable, non-sublicensable license to
> access and make personal and non-commercial use of the Amazon Services. This
> license does not include any resale or commercial use of any Amazon Service,
> or its contents; **any collection and use of any product listings,
> descriptions, or prices**; any derivative use of any Amazon Service or its
> contents; any downloading, copying, or other use of account information for
> the benefit of any third party; or **any use of data mining, robots, or
> similar data gathering and extraction tools**.

**Requests actually made to amazon.com: 6 in total, spaced 22–24 s apart, all by
`curl`, none by `boty.fetch.get`, and none to a product page.** Two to
`www.amazon.com` (the policy page above and `robots.txt`, 7,887 B, 436 lines,
100 `User-agent` blocks); four to the developer-documentation hosts
`webservices.amazon.com` and `affiliate-program.amazon.com` for the rung-2
evaluation, one of which was an HTTP 404 on a guessed slug and is recorded as
such. **Requests to an Amazon product page: 0.**

**`make verify` verdict line, verbatim:**

```
VERIFY: PASS
```

Exit 0, produced under
`sudo systemd-run --pipe --quiet --uid=dan --property=EnvironmentFile=/home/dan/.config/boty/env --property=WorkingDirectory=/home/dan/CodeProjects/pokemongoplusplus /usr/bin/make verify`
— not the OFFLINE and not the INCOMPLETE variant, so the live control stage
actually ran.

**Control check, before and after.** There was no probing to bracket, because
the REFUSED branch makes no requests — but both runs are recorded anyway:

```
control check: PASS — 4/4 controls in stock
  in_stock      gamestop  CONTROL — PS5 console                $549.99  ld+json: InStock from GameStop
  in_stock      walmart   CONTROL — Great Value whole milk       $2.42  __NEXT_DATA__: IN_STOCK from Walmart.com
  in_stock      bestbuy   CONTROL — Pokémon Let's Go, Pikach    $59.99  ld+json: InStock from Best Buy
  in_stock      nintendo  CONTROL — Nintendo HDMI cable          $7.99  ld+json: InStock from Nintendo of America Inc.
```

Identical before (standalone, under the service environment) and after (inside
`make verify`). Dan's monitor was never at risk: no defended endpoint was
touched.

## Verification gates

| Gate | Result |
|---|---|
| `.venv/bin/python -m pytest tests/ -q` | **232 passed** (was 209; +23 new) |
| `.venv/bin/python -m mypy` | `Success: no issues found in 15 source files` |
| `.venv/bin/python scripts/mutation_check.py` | `6/6 mutations caught` |
| `make verify` (plain shell and `systemd-run`) | exit 0, `VERIFY: PASS` |
| `evidence_check.py --retailer Amazon` | exit 0 |
| `grep -E '^\| *Amazon *\| *[1-4]' README.md` | matches (rung 4) |
| verdict ↔ shipped config agreement | `amazon: REFUSED`, no watch, no `FIRST_PARTY` entry, no fixture |

The gate proved on the real tree: `Best Buy`, `Nintendo`, `Pokémon Center` and
`Amazon` each exit 0; `Target` exits 1 with *"no section for 'Target'"*. That
last one is the correct answer today and is why `--phase` is not yet in
`make verify`.

No rung-3 fixture was captured, so the CR-02 identity-leak guard had nothing new
to inspect.

## Decisions Made

Recorded in the frontmatter. The two that will matter to later plans:

- **The gate stays strict and stays out of `make verify` for one plan.** Rule 2
  says a roadmap retailer must be either configured or recorded REFUSED, and
  Target is currently neither. The alternative — softening rule 2 so today's
  tree passes — would rebuild the exact defect this plan exists to fix, an
  escape hatch that stops being able to fail. 03-02 writes Target's verdict;
  03-03 wires the gate in. `test_the_repo_as_it_stands_after_this_plan_names_target_as_the_only_gap`
  is where that reasoning lives in the tree rather than only in this document.
- **`amazon` stays in `boty.retailers.MARKETPLACES`.** It is the archetypal
  buy-box marketplace and that entry is a statement about the retailer, not a
  claim to support it. `_pick` was not touched, and neither was the
  `no structured stock data found` return text that `mutation_check.py`'s M2
  anchors on.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `docs/` added to the mutation-check sandbox**

- **Found during:** Task 2 (GREEN), when `mutation_check.py` reported
  `HARNESS ERROR` on the baseline.
- **Issue:** `tests/test_evidence_check.py` checks the real
  `docs/retailer-evidence.md` through the gate, but `SANDBOX_CONTENTS` did not
  copy `docs/`, so the test raised `FileNotFoundError` inside the sandbox.
  Because the baseline failed, the whole mutation run aborted — correctly
  refusing to score anything, but `make verify` would have gone red.
- **Fix:** added `"docs"` to `SANDBOX_CONTENTS` with a comment giving the
  reason. This is what that constant's own comment already prescribes: *"The
  sandbox has to be a faithful copy of everything the suite reaches for"*, and
  the failure mode it warns about is exactly the one hit here — a test failing
  in the sandbox for want of a file is indistinguishable from a mutation being
  caught.
- **Files modified:** `scripts/mutation_check.py`
- **Verification:** `6/6 mutations caught`, baseline `232 passed`.
- **Committed in:** `d14280e` (Task 2 GREEN commit)

**2. [Rule 1 - Bug] Test helper did not create nested `tmp_path` subdirectories**

- **Found during:** Task 2 (GREEN). Three tests build a *second* synthetic
  evidence tree to compare two failure messages, and `_write_evidence` wrote
  into a subdirectory it had not created.
- **Fix:** `tmp_path.mkdir(parents=True, exist_ok=True)` in the helper.
- **Files modified:** `tests/test_evidence_check.py`
- **Verification:** 23 passed.
- **Committed in:** `d14280e`

**3. [Rule 2 - Missing Critical] README's retailer-count paragraph corrected**

- **Found during:** Task 3.
- **Issue:** the plan specifies adding an Amazon *row*. But the prose below the
  table said Pokémon Center "is the one that fell out", which stops being true
  the moment Amazon is dropped — a support matrix that is accurate in its table
  and wrong in its summary is the kind of thing this project exists not to ship.
- **Fix:** the paragraph now names both dropped retailers, distinguishes their
  reasons (a ladder walked to exhaustion vs. terms that answer before a request
  would), and points at `evidence_check.py` as what holds the number.
- **Files modified:** `README.md`
- **Verification:** `evidence_check.py --retailer Amazon` exits 0; the README
  row grep matches.
- **Committed in:** `67e00ad`

**4. [Rule 1 - Bug] REQ-07 left Pending rather than marked complete**

- **Found during:** state updates, after `requirements mark-complete REQ-07`
  flipped it to `[x]`.
- **Issue:** this plan's frontmatter claims REQ-07, but so do 03-02 and 03-03,
  and the requirement reads "**Target and Amazon** are each either working or
  documented as unreachable with evidence." Target is not documented — the gate
  this same plan shipped says so out loud, exiting 1 with *"no section for
  'Target'"*. `REQUIREMENTS.md`'s own rule is that a requirement "flips to
  Complete when its **phase** completes". A green traceability row that
  contradicts the executable gate in the same commit is precisely the false
  green this project exists to prevent.
- **Fix:** reverted `.planning/REQUIREMENTS.md`. 03-03 marks REQ-07 when both
  retailers are settled.
- **Files modified:** `.planning/REQUIREMENTS.md` (reverted to unmodified)
- **Verification:** `REQ-07 | Phase 3 | Pending`;
  `evidence_check.py --phase` still names Target as the one gap, consistently.

---

**Total deviations:** 4 auto-fixed (1 blocking, 2 bugs, 1 missing critical).
**Impact on plan:** none on scope. Two were self-inflicted by the new test file
and fixed where they arose; the third keeps two halves of the same README
section from contradicting each other.

## Issues Encountered

- **The rung-2 answer had moved since anyone last looked.** The plan expects to
  evaluate the Product Advertising API against the fresh-clone rule. PA-API 5 is
  now **deprecated** and returns `HTTP 403 AccessDeniedException`; its successor,
  the Creators API, requires an Associates account, a tax interview, a Partner
  Tag and per-region approval. Both facts are recorded, because "the API this
  repo would have reached for no longer exists" is worth more to a future reader
  than a restatement of the rule.
- **One HTTP 404 on a guessed documentation slug.** Recorded in the evidence
  table rather than quietly dropped; the correct URL was then read out of the
  previous page's own links instead of guessed a second time.

## User Setup Required

None.

## Next Phase Readiness

- **03-02 (Target) is unblocked** and now carries the whole weight of phase
  criterion 5. If Target also refuses, the count stays at four and criterion 5
  is recorded unmet — `evidence_check.py` verifies that outcome as *clean*,
  which is deliberate: a gate that goes red on the honest answer pressures the
  next person into padding.
- **03-02 must write Target's verdict section.** Until it does,
  `evidence_check.py --phase` exits 1 naming Target as the one gap. That is
  correct, and it is why the gate is not in `make verify` yet. 03-03 wires it in
  and adds the shipped-tree test.
- **Nothing here touched `boty/`.** No adapter code, no `_pick`, no change to
  the M2 mutation anchor. `boty/retailers.py` is untouched, so 03-02 starts from
  the tree Phase 2 left.

## Self-Check: PASSED

All 7 claimed files exist on disk; all 4 claimed commit hashes resolve in
`git log`; `tests/fixtures/amazon/` does not exist; `git diff --stat` over this
plan's commit range shows **no change to `boty/`** at all.

---
*Phase: 03-the-hard-two*
*Completed: 2026-08-03*
