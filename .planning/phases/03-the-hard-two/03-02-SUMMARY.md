---
phase: 03-the-hard-two
plan: 02
subsystem: testing
tags: [target, terms-of-use, robots-txt, redsky, evidence, rung-4, retailer-scope, tdd]

requires:
  - phase: 03-the-hard-two
    provides: 03-01's terms-first pattern, scripts/evidence_check.py, and the Amazon rung-4 precedent that put the whole of criterion 5 on this plan
  - phase: 02-five-retailers-green
    provides: the evidence-log format, the verdict grammar, control_check.py's configured-minus-verified rule, and the Pokémon Center rung-4 precedent
provides:
  - Target settled at rung 4 by its Terms & Conditions, clause quoted and dated, with zero product-page requests ever made
  - The five-retailer criterion recorded UNMET at four, with the shortfall fully described rather than padded
  - A test set that binds the Target verdict to the shipped tree in both directions, including the FIRST_PARTY allow-list drift guard specified for the REACHABLE branch
  - evidence_check.py --phase passing on the real tree for the first time — the precondition 03-03 needs to wire it into make verify
  - The REQ-08 baseline for 03-03 — a full boty check at four retailers
affects: [03-03 phase close, 04-01 contributor docs]

tech-stack:
  added: []
  patterns:
    - "Terms-first, applied twice: two retailers settled in one phase with zero product-page requests between them"
    - "A guard written for a branch the repo is not on gets driven synthetically in BOTH directions, so it is exercised today rather than on the day it first matters"
    - "Membership guards mirror the production predicate (_pick's .strip().lower() set test) rather than a substring grep — the substring version silently accepted the exact mismatch it existed to catch"

key-files:
  created:
    - .planning/phases/03-the-hard-two/03-02-SUMMARY.md
  modified:
    - docs/retailer-evidence.md
    - tests/test_retailers.py
    - README.md
    - QUESTIONS.md

key-decisions:
  - "Target is rung 4, settled by its Terms & Conditions — the `Unlawful or Prohibited Uses` bullet forbidding data-gathering tools and storing prices carries NO commercial-use qualifier, unlike the bullet above it, which does"
  - "The `except pursuant to the limited license` carve-out closes rather than opens: the licence is granted 'only to the extent such use does not violate ... the prohibitions listed in the UNLAWFUL OR PROHIBITED USES section'"
  - "Zero requests were made to any Target product page, at any rung — 4 curl requests total, all policy documents and robots.txt"
  - "Target's robots.txt is BROADER than its ToU — the opposite direction to Amazon's. /p/ carries no Disallow and sitemap_pdp-index.xml.gz is published; the terms still govern"
  - "Rung 2 is closed four ways: redsky.target.com/robots.txt is `Disallow: /` for every agent; the `key` is Target's internal front-end constant, not an issuable credential; the terms cover all hosts; and it is CAPTCHA-gated"
  - "No TCIN discovery was attempted even though robots.txt hands over the PDP sitemap — whether Target stocks the GO Plus + is a deliberate NON-finding, unlike Best Buy's, which is a disproof"
  - "FIRST_PARTY['target'] = {'target'} was NOT widened and NOT deleted: it is a guess, it is unreachable while no target watch exists, and an offline test now fails the moment a watch makes it live"
  - "The plan's starting URL /c/terms-conditions/-/N-4sr7p serves Target's PRIVACY POLICY; the Terms are at N-4sr7l. Both recorded so no future reader quotes the wrong document"
  - "Criterion 5 is recorded UNMET at four and it is now final: both Phase 3 candidates refused in writing, and Phase 2 already established there is no third US retailer stocking the product"

requirements-completed: []  # REQ-07 is now fully evidenced but flips in 03-03 with the phase — see below

duration: 19min
completed: 2026-08-03
---

# Phase 3 Plan 02: Target Summary

**Target settled at rung 4 by its own Terms & Conditions — quoted, dated, and reached with four `curl` requests to policy documents and not one to a product page — which makes the five-retailer criterion honestly unmet at four, recorded rather than padded.**

## Performance

- **Duration:** ~19 min
- **Started:** 2026-08-03T04:06:00Z
- **Completed:** 2026-08-03T04:25:00Z
- **Tasks:** 3, in 4 commits
- **Files modified:** 4 (0 created, 4 modified) — **none of them under `boty/`**

## The requested record

**Terms & Conditions.** Requested
`https://www.target.com/c/terms-conditions/-/N-4sr7l`. HTTP 200, 471,173 B,
`text/html; charset=utf-8`, no redirect. Retrieved **2026-08-03**. Document
header: `LAST UPDATED: April 15, 2026`.

**The operative clause,** from `Unlawful or Prohibited Uses`:

> Whether on behalf of yourself or on behalf of any third party, YOU MAY NOT:
> […] **Make any use of data extraction, scraping, mining or other data
> gathering tools, or create a database by systematically downloading or storing
> Site content, or otherwise scrape, collect, store or use any Content, account
> information, product listings, descriptions, prices or images, except pursuant
> to the limited license granted by these Terms & Conditions;**

And the Introduction, which is what makes a bot a party to the terms at all:

> BY ACCESSING OR OTHERWISE USING THE SITE YOU AGREE TO THESE TERMS &
> CONDITIONS. **Any person or entity who interacts with the Site through the use
> of crawlers, robots, browsers, data mining or extraction tools […] is
> considered to be using the Site.**

**Requests actually made to `*.target.com`: 4 in total**, ≥15 s apart, all by
`curl`, none by `boty.fetch.get`, all HTTP 200:

| Requested | Result |
|---|---|
| `www.target.com/c/terms-conditions/-/N-4sr7p` | 200, 374,015 B — **the wrong document**, node `4sr7p` is the Privacy Policy |
| `www.target.com/c/terms-conditions/-/N-4sr7l` | 200, 471,173 B — the Terms |
| `www.target.com/robots.txt` | 200, 3,226 B, 122 lines, **one** `User-agent` group |
| `redsky.target.com/robots.txt` | 200, 41 B — `User-agent: * / Crawl-delay: 1 / Disallow: /` |

**Requests to a Target product page: 0.** Budget was 12; 4 were spent. No retry,
no backoff and no refusal-counter was ever reached, because nothing refused —
there was nothing to be refused from. `boty.browser.fetch_rendered` was never
called and `boty capture-fixture` was never run.

**Live `offers.seller.name` string observed: NONE.** Observing it would have
required fetching a product page. `FIRST_PARTY["target"]` therefore still holds
the un-evidenced guess `{"target"}`, dormant and now guarded — see below.

**Control check, before and after.** Byte-identical, twice standalone under the
service's own `EnvironmentFile` and a third time inside `make verify`:

```
control check: PASS — 4/4 controls in stock
  in_stock      gamestop  CONTROL — PS5 console                $549.99  ld+json: InStock from GameStop
  in_stock      walmart   CONTROL — Great Value whole milk       $2.42  __NEXT_DATA__: IN_STOCK from Walmart.com
  in_stock      bestbuy   CONTROL — Pokémon Let's Go, Pikach    $59.99  ld+json: InStock from Best Buy
  in_stock      nintendo  CONTROL — Nintendo HDMI cable          $7.99  ld+json: InStock from Nintendo of America Inc.
```

The GameStop control needed one automatic retry on the *first* run
(`fetch failed: HTTP 403`, retried and read `InStock`) and none on the second —
ordinary backoff behaviour, not a Target finding. No pre-existing control
regressed, because no defended endpoint was touched.

**`make verify` verdict line, verbatim:**

```
VERIFY: PASS
```

Exit 0, under
`sudo systemd-run --pipe --quiet --uid=dan --property=EnvironmentFile=/home/dan/.config/boty/env --property=WorkingDirectory=/home/dan/CodeProjects/pokemongoplusplus /usr/bin/make verify`
— not the OFFLINE and not the INCOMPLETE variant, so the live control stage
actually ran.

**REQ-08 baseline for 03-03.** A full `boty check` at the retailer count this
plan leaves behind — **10 watches, 4 retailers, one of them on rung 3**:

```
real	0m36.823s
user	0m1.767s
sys	0m0.681s
```

**36.8 s against a 120 s budget**, measured under the service's own environment.
Slightly *faster* than the 40 s Phase 2 recorded for the same shape. Run against
a scratch `state_path`/`status_path` so the live `boty.service`'s files were not
clobbered or raced; nothing was notified.

## Accomplishments

- **Target is rung 4, and the reason is written rather than technical.** Its
  Terms prohibit this three ways, and the record is careful about which of the
  three actually bites. The commercial-use bullet does **not** reach a personal
  restock monitor. The navigation bullet carves out "generally publicly
  available browsers", which a determined reading could stretch over headless
  Chrome. The data-extraction bullet has neither escape and forbids four things
  bot-y does by definition — including the bare verb *use* applied to a price.
- **The `except pursuant to the limited license` carve-out was read, not
  assumed.** It points at a licence granted "only to the extent such use does
  not violate … the prohibitions listed in the UNLAWFUL OR PROHIBITED USES
  section". The circle closes against us; bot-y's use being personal and
  non-commercial gets it past the licence's first condition and straight into
  its second.
- **Zero product-page requests, at any rung, for the second retailer running.**
  Phase 3 has now settled both of its retailers without a single product fetch
  between them. Pokémon Center cost ten probes across two transports before a
  desk review produced the reason; Amazon cost six policy reads; Target cost
  four.
- **The robots.txt disagreement runs the opposite way to Amazon's, and that is
  the finding most likely to tempt somebody later.** `www.target.com/robots.txt`
  has no named-bot blocks at all, does not disallow `/p/`, and *publishes*
  `sitemap_pdp-index.xml.gz` — a product-detail index that would have solved the
  TCIN-discovery problem `.planning/STATE.md` records Phase 2 giving up on. It
  was not used. The narrower technical file does not license what the broader
  written one refuses.
- **Rung 2 closed four separate ways**, the first of them mechanical:
  `redsky.target.com/robots.txt` is 41 bytes of `Disallow: /` for every agent —
  broader than Pokémon Center's, which closed five paths rather than the host.
- **The sharp edge in the shipped code is now guarded rather than only
  described.** `FIRST_PARTY["target"] = {"target"}` has been in
  `boty/retailers.py` since before anyone probed Target. It is a guess, and with
  `target` in `MARKETPLACES` a wrong guess produces a **confident OUT_OF_STOCK**
  at `boty/retailers.py:177` on a page read perfectly. It was neither widened
  (that needs a live page) nor deleted (it records a true fact) — instead an
  offline test now fails the moment a Target watch makes it live, and a second
  test pins the REACHABLE-branch rule that any future allow-list value must be a
  member-match against a seller string read off a shipped fixture.
- **`evidence_check.py --phase` passes on the real tree for the first time.**
  Every retailer in `ROADMAP_RETAILERS` is now either configured or carries
  `**Verdict: REFUSED**`. That is the precondition 03-01 deliberately left
  unmet; 03-03 can wire the gate into `make verify`.

## Task Commits

1. **Task 1: read Target's terms before walking its ladder** — `bea56c9` (docs)
2. **Task 2: Target settled at rung 4 — no rung walked, no request made** — `6e25ae9` (docs)
3. **Task 3 (RED/tests): pin the REFUSED branch and the allow-list drift guard** — `675a7ce` (test)
4. **Task 3 (docs): rung 4 in the matrix, and the shortfall recorded** — `6a7e6e2` (docs)

## TDD Gate Compliance

Task 3 is `tdd="true"` and branches on task 2's verdict. **The REFUSED branch
ships no production code**, by the plan's own instruction ("Change no code"), so
there is a `test(...)` commit and deliberately **no `feat(...)` or
`refactor(...)` commit**. A GREEN commit here would have meant inventing
production code the evidence says must not exist.

RED was performed rather than skipped, in three ways:

1. **The drift guard was watched failing for the wrong reason, and that caught a
   real bug in it.** The first version asked
   `any(seller in fixture_text.lower() for seller in allow_list)`. It passed
   against an allow-list of `{"target"}` and a page whose seller is
   `"Target Corporation"` — because `"Target Corporation"` *contains*
   `"target"`. The guard was waving through precisely the mismatch it exists to
   catch. Replaced with `_pick`'s own predicate,
   `seller.strip().lower() in allow_list` (`boty/retailers.py:62`), so the test
   fails exactly when `_pick` would.
2. **Both real-tree guards were watched failing against a contradicting tree.**
   Appending a `retailer: target` watch to `config/products.yaml` turns
   `test_the_target_verdict_and_the_shipped_tree_agree` and
   `test_the_dormant_target_allow_list_entry_is_documented_as_a_guess` red;
   writing `tests/fixtures/target/injected.html` turns the first red on its own.
   Both injections were reverted.
3. **The REACHABLE branch is driven synthetically in both directions**, so it is
   exercised today rather than only on the day Target ships. Without the passing
   counterpart the guard could be satisfied by never letting Target be
   REACHABLE, which would make it a rule against a branch instead of a rule
   about it.

## Files Created/Modified

- `docs/retailer-evidence.md` — the `## Target (target.com)` section: four
  requests with byte counts, three clauses quoted in full, an explicit reading of
  which two clauses do *not* bite, the robots.txt disagreement in both
  directions, the four-way rung-2 closure, what was not done, the dormant
  allow-list hazard, and a do-not-re-probe note.
- `tests/test_retailers.py` — `_target_disagreements` and six tests (+6, 232 →
  238).
- `README.md` — Target row at rung 4; the retailer-count paragraph corrected from
  "the two that fell out" to three.
- `QUESTIONS.md` — `## 0b. Target is rung 4 too`, and a dated update on the
  Pokémon Center entry.

## Verification gates

| Gate | Result |
|---|---|
| `.venv/bin/python -m pytest tests/ -q` | **238 passed** (was 232; +6 new) |
| `.venv/bin/python -m mypy` | `Success: no issues found in 15 source files` |
| `.venv/bin/python scripts/mutation_check.py` | `6/6 mutations caught` |
| `make verify` (`systemd-run`, service `EnvironmentFile`) | exit 0, `VERIFY: PASS`, live control stage ran |
| `evidence_check.py --retailer Target` | exit 0 (was exit 1, *"no section for 'Target'"*) |
| `evidence_check.py --phase` | **exit 0 — first time on the real tree** |
| `grep -E '^\| *Target *\| *[1-4]' README.md` | matches (rung 4) |
| verdict ↔ shipped config agreement | `target: REFUSED`, no watch, no `FIRST_PARTY` change, no fixture |
| every configured retailer has a control | 4/4 |
| `rung 4` in `QUESTIONS.md` | present (6 occurrences) |
| `notify-dan` | `sent: bot-y: Target is rung 4` |

`M2`'s anchor — the `no structured stock data found (page shape changed?)` return
text and its twelve spaces of indentation — is untouched, because
`boty/retailers.py` is untouched. `git diff` over this plan's four commits shows
**no change under `boty/`** at all.

## Decisions Made

Recorded in the frontmatter. The three that will matter to later plans:

- **The five-retailer criterion is unmet at four, and that is now final rather
  than pending.** Both of Phase 3's candidates refused in writing; Phase 2's
  fifth-retailer search already established no other US retailer stocks the
  GO Plus +, and a control-only Micro Center was probed and explicitly declined
  on those grounds. There is no honest path to five, so nobody should go looking
  for one.
- **`FIRST_PARTY["target"]` stays as a guarded guess.** Deleting it would have
  meant editing `boty/retailers.py` in a plan whose whole finding is that no code
  change is warranted; widening it would have meant fetching a page the terms
  forbid. The tests make it safe to leave: it cannot become live without a red.
- **Whether Target stocks the GO Plus + is deliberately not established.** This
  is a NON-finding, and it is different in kind from Best Buy's, which is a
  disproof backed by two searches. Stated explicitly so a future reader does not
  cite it as evidence in either direction.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's Terms URL serves the Privacy Policy**

- **Found during:** Task 1.
- **Issue:** `03-02-PLAN.md` names
  `https://www.target.com/c/terms-conditions/-/N-4sr7p` as the starting URL. It
  returns HTTP 200 with a `terms-conditions` slug in the path but its own
  metadata reads `"canonical_url":"/c/target-privacy-policy/-/N-4sr7p"` and
  `"seo_h1":"Target Privacy Policy"`. Quoting from it would have produced a
  confident "no automated-access prohibition found" from a document that has no
  reason to contain one — the worst available failure for this plan.
- **Fix:** the correct node id (`N-4sr7l`) was read out of the wrong page's own
  `children` list rather than guessed a second time — the same discipline
  03-01 applied after its HTTP 404 on a guessed Amazon slug. Both requests are
  recorded in the evidence table so a future reader following the plan's URL is
  warned.
- **Files modified:** `docs/retailer-evidence.md`
- **Committed in:** `bea56c9`

**2. [Rule 1 - Bug] The allow-list drift guard accepted the mismatch it exists to catch**

- **Found during:** Task 3, on the first run of the new test set.
- **Issue:** the guard asked whether any allow-list value appeared as a
  *substring* of the fixture text. `"Target Corporation"` contains `"target"`,
  so an allow-list holding only the un-evidenced guess passed against a page
  naming a different seller — the exact scenario that produces a confident
  OUT_OF_STOCK at `boty/retailers.py:177`.
- **Fix:** replaced with `_pick`'s own predicate — the seller strings are read
  out of the fixture with the production extractors (`parse.ldjson_offers` /
  `parse.nextdata_offers`) and tested with `.strip().lower() in allow_list`, so
  the test fails exactly when `_pick` would.
- **Files modified:** `tests/test_retailers.py`
- **Verification:** the guard now goes red on the mismatch case and green on the
  evidence-backed case; both are pinned as tests.
- **Committed in:** `675a7ce`

**3. [Rule 2 - Missing Critical] README and QUESTIONS corrected where this outcome falsified them**

- **Found during:** Task 3.
- **Issue:** the plan specifies adding a README *row*. But the paragraph below
  the table said "Pokémon Center and Amazon are **the two** that fell out",
  which stops being true the moment Target is dropped; and `QUESTIONS.md`'s
  Pokémon Center entry ended "Phase 3 targets Target and Amazon. If either
  lands, the count reaches five there", which this plan makes false. This is the
  same class of defect 03-01 fixed in the same README paragraph — a support
  matrix accurate in its table and wrong in its summary is what this project
  exists not to ship.
- **Fix:** the paragraph now says three, distinguishes the ladder-walked refusal
  from the two settled by terms, and adds that with Target recorded, every
  in-scope retailer is now either shipped or refused in writing. The Pokémon
  Center entry carries a dated update instead of a stale prediction.
- **Files modified:** `README.md`, `QUESTIONS.md`
- **Committed in:** `6a7e6e2`

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 missing critical).
**Impact on plan:** none on scope. One was a defect in the plan's own input, one
was self-inflicted by the new test and caught by running it, and the third keeps
three documents from contradicting each other about the same number.

## Issues Encountered

- **The document at the plan's URL was the wrong one.** See deviation 1. Worth
  restating as an issue rather than only as a fix: Target serves *both* policies
  under a `/c/terms-conditions/` path shape, differing only in the node id, and
  the wrong one returns a perfectly ordinary HTTP 200.
- **Target's terms have moved recently and in a direction worth noting.** The
  `Agentic Commerce and Delegated Access` section is new and is the only place
  Target contemplates an automated agent acting for a person. It is scoped to
  authenticated account actions and closes with "Other automated or unauthorized
  agentic tools are expressly prohibited", so today it narrows rather than widens
  the door — but it is the clause a future reader should check first.
- **No pressure was applied to the honest answer, and it is worth saying where
  the pressure was.** `03-01` had already put the whole of criterion 5 on this
  plan, `robots.txt` published the product sitemap that would have made TCIN
  discovery easy, and the two policy pages both fetched clean at HTTP 200 from
  plain `curl` — three separate invitations to go and look. None was taken.

## User Setup Required

None. Dan was notified (`notify-dan`, delivered) because criterion 5 is now
recorded unmet; nothing is blocked on him.

## Known Stubs

None. Nothing was stubbed, mocked or left half-wired: the REFUSED branch's
deliverable is documentation plus guards, and both are complete.

## Next Phase Readiness

- **03-03 is unblocked, and one of its preconditions is now met.**
  `evidence_check.py --phase` exits 0 on the real tree for the first time, so
  the gate can be wired into `make verify` as 03-01 planned. Note that 03-03's
  plan may assume a *registered* Target — it must not; there is none, and the
  `03-04` split contemplated by this plan's rung-3 branch was **not** created
  because Target never reached rung 3.
- **REQ-07 is now fully evidenced** — "Target and Amazon are each either working
  or documented as unreachable with evidence" is satisfied in both halves — but
  it is deliberately left Pending here, for the same reason 03-01 left it
  Pending: `REQUIREMENTS.md`'s own rule is that a requirement flips when its
  **phase** completes. 03-03 marks it.
- **REQ-08 has its baseline:** 36.8 s for 10 watches across 4 retailers, one on
  rung 3, against a 120 s budget. The retailer count is final, so that number
  will not move for a reason this phase controls.
- **Nothing here touched `boty/`.** No adapter code, no `_pick`, no change to
  the M2 mutation anchor, no new dependency. 03-03 starts from the tree 03-01
  left, plus documentation and tests.

## Self-Check: PASSED

All 4 claimed files exist on disk; all 4 claimed commit hashes resolve in
`git log`; `tests/fixtures/target/` does not exist; `config/products.yaml`
contains no `target` retailer; and `git diff --stat bea56c9~1..HEAD` shows
changes to exactly `docs/retailer-evidence.md`, `tests/test_retailers.py`,
`README.md` and `QUESTIONS.md` — **no change under `boty/`**.

---
*Phase: 03-the-hard-two*
*Completed: 2026-08-03*
