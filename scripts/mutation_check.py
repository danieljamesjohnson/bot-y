#!/usr/bin/env python3
"""Prove the test suite would actually catch a broken extractor.

A passing test suite is not evidence that it detects anything. Delete the
assertions and it still passes; assert the wrong thing and it still passes. The
only way to know a suite bites is to break the code on purpose and watch it go
red — so this corrupts three specific things in `boty` and requires the suite to
notice each one.

The three mutations are not arbitrary. Each is a real failure this project
exists to prevent, and each would be invisible in production:

  M1  Invert the buyable check in the parser. Every offer's availability flips.
      Survival means the suite never really asserts *which* availability came
      back — the single most load-bearing fact it reports.
  M2  Turn "I could not read this page" from UNKNOWN into OUT_OF_STOCK.
      Survival means the three-state contract is untested, and the monitor's
      defining behaviour — never saying out-of-stock when it means "I got
      lost" — could be dropped without a single red test.
  M3  Disable the first-party seller filter. Survival means reseller listings
      at 4x MSRP could start alerting and nothing would say so.

FOUR THINGS THAT WOULD MAKE THIS PROVE NOTHING
----------------------------------------------
1. Mutating the working tree. This copies `boty/`, `tests/` and
   `pyproject.toml` into a temp dir and mutates the COPY. A script that edited
   in place and crashed mid-run would leave a corrupted checkout.
2. No baseline. If the sandbox is broken, every mutation "fails" and the check
   reports 3/3 caught while proving nothing at all. So the UNMUTATED copy is
   run first and must PASS.
3. Treating any non-zero exit as "caught". pytest exits 2 on collection error,
   4 on usage error, 5 when it collected no tests. A temp copy missing
   `tests/fixtures/` would score a perfect 3/3. Only exit code 1 — real test
   failures — counts; anything else aborts as a harness error.
4. Importing the real package. `bot-y` is installed editable through a
   meta-path finder holding an absolute path to the real `boty/`, so
   `.venv/bin/pytest` would import the UNMUTATED source, every mutation would
   survive, and this would fail forever for the wrong reason. pytest is
   invoked as `python -m pytest` with `PYTHONPATH` pointed at the sandbox, and
   the baseline asserts `boty.__file__` really does resolve under the temp dir.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Copied into every sandbox. pyproject.toml is required: it carries the pytest
#: ini options, and `boty.fixtures` anchors FIXTURE_ROOT to the directory
#: containing it — without it the sandbox would read the real fixture tree.
#:
#: `scripts` and `Makefile` are here because the suite tests them too:
#: tests/test_control_check.py loads scripts/control_check.py by path and
#: tests/test_verify_makefile.py runs the Makefile's verify recipe against a
#: stub interpreter. A sandbox missing either would fail at collection, pytest
#: would exit 2, and `check_mutation` would abort as a harness error rather
#: than quietly scoring it — but the run would still be dead. The sandbox has
#: to be a faithful copy of everything the suite reaches for.
#: Everything the suite reads. The sandbox has to be a faithful copy or the
#: run proves nothing: a test that fails inside it for want of a file is
#: indistinguishable from a mutation being caught, and the baseline check
#: turns that into "nothing was proved either way". `config` is here because
#: tests/test_config.py asserts the shipped products.yaml still loads — a
#: guard against validation that rejects the repo's own config. `served` is here
#: because tests/test_dashboard.py reads served/boty/index.html: the status page
#: is the consuming half of `status.write`'s published contract, and asserting
#: that contract at only one end is what let the page quietly stop rendering
#: `degraded` at all. `docs` is here because tests/test_evidence_check.py checks
#: the real docs/retailer-evidence.md through scripts/evidence_check.py — the
#: retailer count and the written verdicts are a claim the suite is supposed to
#: police, and a sandbox without the document turns that test into a
#: FileNotFoundError that reads exactly like a caught mutation. `README.md` is
#: here for the same reason one layer along: tests/test_support_matrix.py parses
#: the README's retailer table, because phase criterion 3 requires a rung-3
#: retailer to be flagged DEGRADED in the support matrix as well as at runtime,
#: and the matrix is prose in that file. M6 is precisely the mutation that
#: clears the runtime flag, so a sandbox without the README would break the
#: matrix half of that pair inside the run meant to score the runtime half.
#: `CONTRIBUTING.md` is here because tests/test_contributor_docs.py reads it off
#: disk and applies four of its six rules to it. Inside the sandbox the tree
#: root is the temp directory, not the repository, so without this entry that
#: read raises FileNotFoundError, pytest exits 1, and `run_baseline` turns a
#: missing file into a HarnessError — killing `make verify` for a reason that
#: has nothing to do with any mutation, and proving nothing about the suite in
#: either direction.
#: `hooks` is here because rule 1 of that same file resolves every backticked
#: path the contributor docs cite against that same root, and
#: docs/adding-a-retailer.md cites hooks/pre-commit — installing the commit hook
#: is the security-critical instruction in the document. A sandbox without the
#: directory makes this repository's own tracked hook look like a fabricated
#: citation, which turns the strongest line in the doc into the thing that
#: reddens the harness.
#: `LICENSE` is here because tests/test_packaging_metadata.py reads it off disk
#: relative to its own parent — which inside the sandbox is the temp directory,
#: not the repository. That file's whole subject is a licence declared in
#: metadata with no licence text behind it, so a sandbox that reproduces exactly
#: that state would fail five of its tests at the BASELINE, `run_baseline` would
#: raise a HarnessError, and `make verify` would die for a reason that has
#: nothing to do with any mutation. The block above already states the rule: a
#: test that fails inside it for want of a file is indistinguishable from a
#: mutation being caught.
#: `MANIFEST.in` is here for the same reason one file along. The sdist prune rule
#: reads it to decide whether every tracked top-level directory has a `prune`
#: line, and the published file surface of this project is the one thing that
#: rule guards. A sandbox without it turns a FileNotFoundError into what looks
#: like a caught mutation.
#: `.github` is here because tests/test_ci_workflow.py reads
#: .github/workflows/ci.yml off disk relative to its own parent — the temp
#: directory inside the sandbox, not the repository — and because that file is
#: the one artifact in this repo that runs on somebody else's computer holding
#: this repository's token, so its gate is not allowed to stop running. Every
#: shipped-file test there would raise FileNotFoundError at the BASELINE,
#: `run_baseline` would turn that into a HarnessError, and `make verify` would
#: die for a reason with nothing to do with any mutation. The directory also
#: cannot be added ahead of the workflow: `build_sandbox()` raises HarnessError
#: for an entry with no file behind it, which is why this line and
#: .github/workflows/ci.yml landed in the same commit.
SANDBOX_CONTENTS = (
    "boty", "tests", "scripts", "config", "served", "docs", "hooks", "pyproject.toml",
    "Makefile", "README.md", "CONTRIBUTING.md", "LICENSE", "MANIFEST.in", ".github",
)

#: `status.json` is ignored because the sandbox now has a git index, and
#: `git add -A` in a directory with no `.gitignore` stages everything it finds.
#: Measured by set difference against the real repo's `git ls-files`,
#: `served/boty/status.json` is the ONLY file the copy loop brings in that this
#: repository does not track — it is `.gitignore`d here, but `.gitignore` is not
#: in SANDBOX_CONTENTS, so git inside the sandbox has never heard of it. Once the
#: index un-skips `test_the_repo_is_clean_right_now`, the identity scan runs over
#: it *inside the sandbox*. It is clean today, but it is a runtime artifact that
#: every live `make verify` rewrites, and its `reason` fields carry
#: retailer-failure exception text — the exact string class that can pick up a
#: local path or a host. That would redden `make verify` from a file in neither
#: the repository nor the diff, which is the least attributable failure this
#: harness could produce. Nothing reads the sandbox's copy: every test that
#: touches status.json writes to `tmp_path`.
#:
#: THE IGNORE SET AND `.gitignore` ARE ALLOWED TO DIFFER, because they answer
#: different questions. `.gitignore` says "do not track this in the repository".
#: `_IGNORE` says "the suite does not read this, so a faithful copy does not need
#: it". They overlap without either containing the other. The one place they must
#: agree is a file the copy loop reaches that the repo does not track, and that
#: set has exactly one member today.
#:
#: The alternative — putting `.gitignore` into SANDBOX_CONTENTS so git honours it
#: inside the sandbox — was considered and rejected. It works, but it leaves a
#: nondeterministic runtime artifact sitting in a harness whose entire claim is
#: reproducibility and merely hides it from the index; and it widens the set of
#: paths the contributor-docs citation rule is allowed to resolve, which is that
#: gate's decision to take, not this one's.
_IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", ".pytest_cache", "*.egg-info", "status.json",
)

#: pytest's exit codes. Only 1 means "tests failed", which is the only thing
#: that can count as a mutation being caught.
_PYTEST_CODES = {
    0: "all tests passed",
    1: "tests failed",
    2: "collection error / interrupted",
    3: "internal error",
    4: "usage error",
    5: "no tests were collected",
}


@dataclass(frozen=True)
class Mutation:
    ident: str
    target: str
    search: str
    replace: str
    breaks: str


MUTATIONS = (
    Mutation(
        ident="M1",
        target="boty/parse.py",
        search='raw.rsplit("/", 1)[-1] in BUYABLE',
        replace='raw.rsplit("/", 1)[-1] not in BUYABLE',
        breaks="inverts every offer's availability — in-stock reads as out-of-stock and back",
    ),
    Mutation(
        ident="M2",
        target="boty/retailers.py",
        # Re-anchored 2026-08-04: the `detail=` on this branch became a
        # parenthesised expression when it gained the ld+json block counts, so
        # the old one-line anchor drifted and this check refused to run rather
        # than quietly dropping to seven mutations. The anchor deliberately
        # stops at `detail=(` — matching the message text would tie a mutation
        # to prose that is edited far more often than the verdict is.
        search='Availability.UNKNOWN,\n            detail=(\n                "no structured stock data found',
        replace='Availability.OUT_OF_STOCK,\n            detail=(\n                "no structured stock data found',
        breaks="an unreadable page becomes OUT_OF_STOCK instead of UNKNOWN — the silent-failure bug itself",
    ),
    Mutation(
        ident="M3",
        target="boty/retailers.py",
        search="if first_party_only:",
        replace="if False:",
        breaks="disables the first-party seller filter — reseller listings become alertable",
    ),
    # M4 and M5 cover the two decisions that live OUTSIDE the extractors.
    # M1-M3 all mutate parse.py/retailers.py, which meant the gate said nothing
    # about the price ceiling or the state machine. That was not hypothetical:
    # CR-01 lived in `run_once`, passed all 36 tests of the day, and deleting
    # every test that now pins it still produced `VERIFY: PASS` at exit 0.
    # A mutation gate that cannot see the layer where the worst bug lived is
    # not guarding the thing it claims to guard.
    # Re-anchored 2026-08-10 (06-01, REQ-17): the ceiling stopped measuring
    # `self.price` and started measuring `self.delivered_total`, so the three
    # lines M4 named no longer exist. `apply_mutation` would have raised
    # HarnessError and `make verify` would have died rather than quietly
    # dropping to fifteen mutations — the same required re-point M2 and M13
    # already record, made deliberately rather than discovered.
    #
    # The re-point is onto the ONE guard that now remains. `alertable` used to
    # carry a `price is None` check ahead of this one; it was deleted in the
    # same commit, and that deletion is what keeps this mutation load-bearing:
    # with both guards in place, flipping the first `return False` to
    # `return True` would change nothing (the delivered total is also None, the
    # second guard returns False), M4 would SURVIVE, and the harness would
    # report a hole that was not there.
    #
    # RE-ANCHORED AGAIN 2026-08-11 (06-07), AND M4'S SUBJECT NARROWED. Dan
    # reversed 06-01's rule — where no shipping cost can be established the
    # ceiling now measures the item price and the alert goes out — so `alertable`
    # split into two branches and the three lines M4 named stopped existing for
    # the second time in two days. Before 2026-08-11 this ident guarded the
    # claim that an unestablished DELIVERED TOTAL cannot clear the ceiling; it
    # now guards the narrower claim that an unreadable PRICE cannot, because the
    # wider one is no longer true and a `breaks=` sentence describing it would
    # be a harness reporting a rule the tree does not hold. The price refusal
    # moved INTO the unresolvable branch, where it is reachable and mutatable —
    # which is what keeps this mutation able to fail at all, the same property
    # the deletion above bought in 06-01.
    Mutation(
        ident="M4",
        target="boty/models.py",
        search="        if self.price is None:\n            return False\n        return self.price <= self.watch.max_price",
        replace="        if self.price is None:\n            return True\n        return self.price <= self.watch.max_price",
        breaks="an offer whose PRICE could not be read clears the ceiling — with no shipping cost either, an unpriced IN_STOCK reading becomes alertable at any price, which is Walmart's reshaped `priceInfo.currentPrice` turned into a push",
    ),
    Mutation(
        ident="M5",
        target="boty/monitor.py",
        search="    transitions = [state.transitioned_to_stock(r) for r in results]",
        replace="    transitions = [r.alertable and state.transitioned_to_stock(r) for r in results]",
        breaks="restores the CR-01 short-circuit — state is only recorded when alertable, so every restock after the first is silently missed",
    ),
    # M6 guards a claim rather than a verdict. `Result.degraded` is the whole
    # of what makes "documented, not faked" mean anything: it is what the
    # status page and the support matrix use to distinguish a reading we trust
    # from one we got by driving a browser at a site that does not want us
    # there. Nothing about the stock verdict changes when it is dropped — every
    # availability, price and alert stays byte-identical — so a suite that only
    # asserts on verdicts would go on passing while every degraded reading was
    # published as a first-class one. A flag nothing asserts on is a flag that
    # can be silently cleared.
    Mutation(
        ident="M6",
        target="boty/models.py",
        search="        return self.rung is Rung.BROWSER or self.extraction is Extraction.DOM",
        replace="        return False",
        breaks="clears the degraded flag — a browser-read verdict is published as if it were a first-class TLS reading, in the status page and in the support matrix",
    ),
    # M7 is M6's second half, and it gets a mutation of its own rather than
    # riding on M6 because they prove different things. M6 dying proves the
    # flag EXISTS. Only M7 proves the flag's NEW disjunct is load-bearing:
    # `degraded` used to be derived from the rung alone, so a DOM adapter on a
    # cheap transport — the most fragile thing anyone could add to this
    # codebase, and the easiest — would ship looking fully trustworthy.
    # Reverting the expression to its pre-widening form is a one-token edit
    # that changes no verdict, no price and no alert, which is precisely the
    # kind of change a verdict-only suite cannot see.
    #
    # M6 and M7 share a `search` string deliberately. Each mutation is applied
    # in its own sandbox, so there is no interaction between them.
    Mutation(
        ident="M7",
        target="boty/models.py",
        search="        return self.rung is Rung.BROWSER or self.extraction is Extraction.DOM",
        replace="        return self.rung is Rung.BROWSER",
        breaks="drops the dom disjunct — a DOM reading on a non-browser transport is published as a first-class structured one, in `boty check`, in the status page and in the support matrix",
    ),
    # M8 is M1 pointed at the other extractor, and it is here because the DOM
    # reader is the most fragile thing in this codebase by some distance.
    #
    # M1 guards `BUYABLE`, which decides availability for four retailers off
    # schema.org strings that are commercially load-bearing and change rarely.
    # `add_to_cart_offers` decides it for Target off whether a rendered button
    # carries `disabled` — presentation markup, a CSS-framework decision, and one
    # a reskin can invert without anybody at Target noticing they broke us. The
    # mutation is a one-token edit that produces a page-perfect reading of the
    # exact opposite of the truth: every out-of-stock item reads buyable, which
    # on a monitor whose ceiling is $80 means a push notification for something
    # nobody can buy, and every restock reads sold out, which means silence
    # during the only event this project exists to catch.
    #
    # Target is registered control-only, so the live half of this guard is a
    # single always-in-stock watch. M8 is the offline half: it proves the suite
    # would go red before anyone had to notice the control had.
    Mutation(
        ident="M8",
        target="boty/parse.py",
        search="    available = not disabled",
        replace="    available = disabled",
        breaks="inverts the add-to-cart availability decision — a disabled (out-of-stock) Target button reads as buyable and an enabled one reads as sold out",
    ),
    # M9 and M10 guard the phase-5 store contract: a Walmart reading that cannot
    # be shown to come from the store the watch is about is UNKNOWN, never a
    # verdict. The measurement behind it, 2026-08-09: the daemon recorded the
    # milk control OUT_OF_STOCK at $3.17 while three live reads minutes later
    # returned IN_STOCK at $2.42 — same URL, same parser. A parser bug does not
    # change a price; two different stores answered.
    #
    # Both are anchored on the guard's own condition line plus the verdict, and
    # on NOTHING ELSE — no part of either `detail` message appears in a `search`
    # string. M2's comment records why: it had to be re-anchored in 2026-08-04
    # when the prose on its branch moved, and "matching the message text would
    # tie a mutation to prose that is edited far more often than the verdict is."
    # `_verdict_from_html` keeps each condition adjacent to its `return` so these
    # anchors can stay prose-free.
    #
    # TWO MUTATIONS AND NOT ONE, on M6/M7's precedent: they prove different
    # things. M9 dying proves the config-gap guard EXISTS. Only M10 proves the
    # COMPARISON is load-bearing — a tree that checked the pin was present and
    # then never compared it against what actually answered would pass M9 while
    # shipping the 2026-08-09 defect completely intact. Both also die if
    # `models.STORE_SCOPED` is ever emptied, which is what makes that constant
    # load-bearing rather than decorative.
    Mutation(
        ident="M9",
        target="boty/retailers.py",
        search="        if watch.store_id is None:\n            return Result(\n                watch,\n                Availability.UNKNOWN,",
        replace="        if watch.store_id is None:\n            return Result(\n                watch,\n                Availability.OUT_OF_STOCK,",
        breaks="an unpinned Walmart watch produces a stock verdict about whichever store the page chose to answer for — a statement about an arbitrary location, published as a fact about yours",
    ),
    Mutation(
        ident="M10",
        target="boty/retailers.py",
        search="        if store != watch.store_id:\n            return Result(\n                watch,\n                Availability.UNKNOWN,",
        replace="        if store != watch.store_id:\n            return Result(\n                watch,\n                Availability.OUT_OF_STOCK,",
        breaks="the 2026-08-09 measurement itself ships: one store's OUT_OF_STOCK at $3.17 published as a verdict about a watch pinned to a store that had it IN_STOCK at $2.42",
    ),
    # M11-M14 guard the phase-5 persistence contract: the backoff, and the
    # memory of having paged about it, outlive the process.
    #
    # THIS IS M6/M7 TERRITORY IN THE PUREST FORM THIS HARNESS HAS SEEN. Not one
    # of these four changes an availability, a price or an alert VERDICT. A
    # verdict-only suite passes every one of them straight through while the
    # monitor comes back from each restart hammering a retailer that walled it
    # and re-notifying a human about a refusal they were already told about.
    # M6's comment already states the rule these four are here to serve: a flag
    # nothing asserts on is a flag that can be silently cleared.
    #
    # FOUR AND NOT ONE, on the same precedent, because they are independent
    # halves that fail in different directions and each ships a different
    # regression. Every `search` is anchored on the STATEMENT THAT DOES THE
    # WORK — the assignment applying the restored count, the comparison bounding
    # the age, the expression producing the restored memory, the union that
    # carries it forward — and on nothing else. `boty/pacing.py` is now dense
    # with the prose of a reversed decision and 05-04 may still edit it, so M2's
    # re-anchoring lesson applies here with extra force: no `search` below
    # contains a fragment of a docstring, a comment or a log message.
    Mutation(
        ident="M11",
        target="boty/pacing.py",
        search="                st.refusals = min(refusals, MAX_PERSISTED_REFUSALS)",
        replace="                st.refusals = 0",
        breaks="the restored refusal count never reaches the schedule — every restart climbs the backoff again from 2x against a retailer that has already walled us, and asks once at full rate on the way",
    ),
    Mutation(
        ident="M12",
        target="boty/pacing.py",
        search="                if not 0.0 <= now - float(refused_at) <= STATE_MAX_AGE_SECONDS:",
        replace="                if False:",
        breaks="stale state is applied regardless of its stamp — a file written before a machine was off for a week pins a retailer at the cap on startup, which is the exact objection the withdrawn docstring paragraph raised",
    ),
    # Re-anchored 2026-08-10 (05-REVIEW WR-01): the expression producing the
    # restored memory used to be a one-line set comprehension over a list. It is
    # now a loop with an age filter, so the statement that DOES THE WORK is the
    # return of what the loop accumulated. Same claim, same regression, new line
    # — M2's lesson, applied deliberately rather than discovered.
    Mutation(
        ident="M13",
        target="boty/pacing.py",
        search="        return restored",
        replace="        return set()",
        breaks="the paging memory does not cross the restart while the backoff itself keeps working perfectly — REQ-16's 'pushed once' silently reverts to 'pushed once per process', and the only symptom is a duplicate notification that reads exactly like a legitimate one",
    ),
    # M14 is M13's other half and gets its own mutation for the reason M7 does.
    # M13 dying proves the memory crosses a PROCESS boundary. Only M14 proves it
    # survives a paced-out CYCLE — and it was measured not to on 2026-08-10: a
    # retailer skipped by its own backoff has no result, so no health entry, so
    # it read as recovered, and the memory was erased by the cycle after the one
    # that paged. A tree that persisted `warned` faithfully and dropped this
    # union would write an EMPTY set to disk and pass M13 while shipping the
    # duplicate page intact, both across a restart and within one process.
    Mutation(
        ident="M14",
        target="boty/cli.py",
        search="    still_unhealthy = {h.retailer for h in pageable} | (warned - checked)",
        replace="    still_unhealthy = {h.retailer for h in pageable}",
        breaks="a cycle the backoff skipped counts as the retailer recovering, so a refusal past the cap is re-paged at every subsequent check — one notification every six hours, forever, about a refusal somebody was already told about",
    ),
    # M15 restores the exact clause 05-REVIEW's CR-02 found, and it is here
    # rather than left to the two tests for M6's stated reason: this one moves
    # no availability, no price and no `ok` flag — only WHICH SENTENCE a person
    # reads — so a verdict-only suite passes it straight through while the alert
    # sends somebody to edit a config file that is not the problem. The `search`
    # is the return statement and nothing else; the paragraph above it is
    # freshly written prose and M2's re-anchoring lesson applies.
    Mutation(
        ident="M15",
        target="boty/monitor.py",
        search="    return c.store is not None and c.store != c.watch.store_id",
        replace="    return c.store != c.watch.store_id",
        breaks="a fetch that produced NO PAGE — a timeout, a DNS failure, an HTTP 500, or a payload that stopped naming a store — is reported as a store-pin config gap, so the alert names a cause nobody measured and points the operator at a `store_id` that is set correctly. REQ-15's own defect, rebuilt inside the arm added to serve REQ-15",
    ),
    # M16 is M12's counterpart for the OTHER half of the same document, and the
    # asymmetry it pins is the whole of WR-01: before 05-REVIEW,
    # STATE_MAX_AGE_SECONDS was applied to `retailers[*].refused_at` and to
    # nothing else, so a 90-day-old file correctly discarded a refusal count of
    # 9 and restored `warned` regardless. Measured against the tree at 1328c0e.
    # It gets its own mutation for M7's reason: M12 dying proves the counts are
    # aged, and only this proves the memory is — a tree that aged one and not
    # the other passes M12 and M13 together while silencing a broken detector
    # forever.
    Mutation(
        ident="M16",
        target="boty/pacing.py",
        search="            if not 0.0 <= now - float(stamp) <= STATE_MAX_AGE_SECONDS:",
        replace="            if False:",
        breaks="a paging memory of any age is restored, so a `pacer-state.json` left on disk from months ago permanently suppresses the health warning for the retailer it names — the alert this project exists to send, silenced by a stale runtime artifact, with a green dashboard over it",
    ),
    # M17 and M18 are the two halves of REQ-17, and they get their own
    # mutations rather than riding on the re-anchored M4 for M6/M7's stated
    # reason: they prove different things.
    #
    # M4 dying proves that an unreadable PRICE is refused under a ceiling. It
    # says nothing about whether shipping is part of the total the ceiling
    # measures, nor about what an unread shipping cost is allowed to be called.
    # (Before 2026-08-11 that sentence read "an unestablished delivered total";
    # M4's own comment block above records why it narrowed.)
    #
    # Both are anchored on an EXPRESSION and a condition, never on a `detail`
    # string, a docstring, a comment or any message prose. 06-01 added a
    # sentence to `_verdict_from_html`'s success `detail` that a careless
    # anchor would grab, and M2's re-anchoring lesson is explicit about what
    # that costs: "matching the message text would tie a mutation to prose that
    # is edited far more often than the verdict is."
    # M17 WAS RE-POINTED ON 2026-08-11 BECAUSE ITS SUBJECT REVERSED, and this
    # gets the longest comment in the file because that is the one thing a
    # mutation harness must never do quietly.
    #
    # Until 2026-08-11 this ident pinned the item-price fallback as REJECTED —
    # its `breaks=` sentence read "rebuilds the REJECTED lenient fallback
    # exactly", and 06-01's SUMMARY records it as such. Dan then chose a version
    # of that fallback, verbatim: "I think where we don't know just send it. If
    # the user gets there and it's 50 dollar shipping that's disappointing but
    # it's worse to feel like you 'missed out'." A `breaks=` sentence describing
    # a rejection that did not survive is a gate asserting a rule the tree does
    # not hold, so it could not be left standing.
    #
    # IT WAS RE-POINTED RATHER THAN DELETED. Deleting a mutation to make a suite
    # green is forbidden in this repository, and it would have been the easy
    # move here: the behaviour M17 guarded is now the behaviour, so the ident
    # "no longer applies" is exactly the argument that would have lost a gate.
    #
    # WHAT IT GUARDS NOW: the CLAIM, where it used to guard the VERDICT. It
    # points at `established_shipping`'s refusal returning `0.0` instead of
    # `None` — a shipping cost NOBODY MEASURED, stated as free, in the alert
    # body AND in the sum. That is the one thing Dan did not choose, and T-06-72
    # names it: `None` never collapses to `0.0`, while `0.0` remains a positive
    # claim of free shipping and survives untouched. Killed by the
    # `delivered_total is None` tests and by the `shipping: unknown` render
    # tests in tests/test_alert_text.py.
    Mutation(
        ident="M17",
        target="boty/models.py",
        search="    if shipping is None or shipping < 0:\n        return None\n    return shipping",
        replace="    if shipping is None or shipping < 0:\n        return 0.0\n    return shipping",
        breaks="a shipping cost NOBODY READ is stated as free: `established_shipping` collapses the absence of a claim into $0.00, so the delivered total becomes the item price, the ceiling measures a figure nobody measured, and the push body says `shipping: $0.00` over a $45 charge waiting at the checkout page — the one reading of Dan's 2026-08-11 decision he did not choose",
    ),
    # M18's anchor moved on 2026-08-11 for a MECHANICAL reason and not a
    # semantic one: `delivered_total` now binds `established_shipping(self.
    # shipping)` to a local, so the addend is spelled `shipping` rather than
    # `self.shipping`. Same expression, same subject, same kill list.
    Mutation(
        ident="M18",
        target="boty/models.py",
        search="        return self.price + shipping",
        replace="        return self.price",
        breaks="drops the shipping addend from the sum, so the ceiling measures the item price again while every guard around it still looks correct — killed on CAPTURED GameStop numbers rather than synthetic ones: $54.99 + $6.99 fails a $60 ceiling and $54.99 alone clears it, which is the half of REQ-17 that survives Dan's reversal intact",
    ),
    # M19 and M20 are REQ-18: the README support matrix's Rung cell, and the
    # two joins that hold it up. Before 06-02 that column was bound to nothing —
    # measured 2026-08-10 by applying M19's exact edit to a sandbox built from
    # the tree of the day: pytest exit 0, `687 passed, 1 skipped`. REQ-18
    # recorded the same measurement at an older suite size ("left 131 tests
    # green"); the number moved and the fact did not.
    #
    # M19'S ANCHOR IS DISAMBIGUATED ON PURPOSE, and the naive version is a trap
    # this harness would have walked straight into. `apply_mutation` does
    # `before.replace(search, replace, 1)` — FIRST OCCURRENCE WINS — and the
    # bare `rung=Rung.TLS,` occurs TWICE in boty/retailers.py, in `check_html`
    # BEFORE `check_amazon`. Counted on the tree at 800b2a6: 2 for the bare
    # form, 1 for the form below. So the obvious anchor would mutate the adapter
    # serving GameStop, Walmart and Nintendo while the `breaks=` sentence
    # described Amazon — a harness reporting a result about work it did not do,
    # which is worse than no result.
    #
    # The disambiguator is the SHORTEST unique extension: the newline and the
    # indented `#` that opens `check_amazon`'s `sku=` comment. It is one
    # punctuation character of comment rather than comment prose, so rewording
    # that comment cannot silently re-point this mutation, and deleting it
    # outright raises HarnessError — the harness refusing to run rather than
    # quietly checking something else. M2's re-anchoring lesson, applied ahead
    # of the drift instead of after it.
    #
    # BOUND BY A TEST rather than by this comment:
    # tests/test_support_matrix.py loads this registry, asserts M19's `search`
    # occurs exactly once in the real source, and asserts that applying it moves
    # `check_amazon` to rung 3 while `check_html` stays at rung 1. The day
    # somebody adds a second `rung=Rung.TLS,` followed by a comment, that test
    # goes red BEFORE this mutation starts measuring a different adapter.
    Mutation(
        ident="M19",
        target="boty/retailers.py",
        search="        rung=Rung.TLS,\n        #",
        replace="        rung=Rung.BROWSER,\n        #",
        breaks="`check_amazon` takes a browser rung while the README support matrix's Amazon row still reads `| Amazon | 1 | dom |`, so the table a reader consults BEFORE deciding what a reading is worth states a transport the code does not take — REQ-18's own measurement, and the one column of that table that used to be bound to nothing",
    ),
    # M20 is M19's other join and gets its own mutation for M6/M7's stated
    # reason: they prove different things. M19 dying proves the ADAPTER→RUNG
    # join exists. Only M20 proves the RETAILER→ADAPTER join is load-bearing —
    # a tree that read `check_amazon`'s rung perfectly and stopped routing
    # amazon to it would pass M19 while the matrix described an adapter nothing
    # calls, and the retailer would be read at whatever rung the adapter that
    # replaced it takes. That is the same false claim, moved one join along.
    #
    # `check_amazon` and `check_target_browser` take the identical
    # `(watch, *, first_party_only)` signature, so the mutated tree imports,
    # collects and runs rather than dying at collection — which would be a
    # HarnessError and not a result. The anchor occurs once in boty/cli.py,
    # counted on the tree at 800b2a6, and it is a call expression: no docstring,
    # no comment, no `detail` prose. `_make_checker`'s arms are dense with
    # recorded reasoning that a careless anchor would grab.
    Mutation(
        ident="M20",
        target="boty/cli.py",
        search="return check_target_browser(watch, first_party_only=cfg.first_party_only)",
        replace="return check_amazon(watch, first_party_only=cfg.first_party_only)",
        breaks="a target watch is routed to Amazon's adapter, so Target is read at rung 1 against a README row that says 3 — and `check_target_browser` is UNTOUCHED and still says `Rung.BROWSER`, so a gate that read only boty/retailers.py stays green while the transport claim is false",
    ),
    # ------------------------------------------------------------------
    # M25 and M26 are THE FIRST MUTATIONS IN THIS REPOSITORY THAT TARGET
    # SOMETHING OTHER THAN A FILE UNDER boty/, and that deserves saying out
    # loud rather than being noticed later in a diff.
    #
    # This module's docstring says the harness breaks THE CODE on purpose, and
    # M1-M20 all honour that: every one of them mutates a `.py` file under
    # boty/. REQ-20's subject is not code. It is a NUMBER this project states
    # about itself in four places — pyproject.toml, README.md's publication
    # instruction, CHANGELOG.md's top released heading and the project's own
    # milestone — where nothing offline read any of the four and two of them had
    # already diverged. A mutation that broke a function could not express that;
    # the thing to break is a statement.
    #
    # BOTH TARGETS ARE IN SANDBOX_CONTENTS ALREADY, for reasons argued in that
    # constant's own comment block, so neither is here to make a mutation
    # possible — which is the trap Phase 4's rule for that tuple exists to close
    # ("an entry lands in the same commit as the file it names, and is proven
    # load-bearing by removal"). CHANGELOG.md and .planning/ are NOT in it and
    # are NOT added: the two version rules that read them skip here, and the
    # pyproject <-> README rule is precisely the one that does not.
    #
    # WHICH TEST IS EXPECTED TO CATCH EACH: the always-on binding
    # tests/test_packaging_metadata.test_the_readme_publication_instruction_names_
    # the_declared_version, which is the ONLY version rule whose two files both
    # reach this sandbox. If either of these ever SURVIVES, the first thing to
    # check is whether that test acquired a skip decorator — a surviving
    # mutation here means criterion 5 is being met by a skip line.
    #
    # BOTH ANCHORS WERE COUNTED BEFORE THEY WERE WRITTEN, because
    # `apply_mutation` replaces the FIRST occurrence and a non-unique anchor
    # mutates a line the `breaks=` sentence is not describing — M19's recorded
    # trap. Measured on the tree these were registered against:
    # `grep -o 'version = "0.2.0"' pyproject.toml | wc -l` -> 1, and
    # `grep -o 'Publication happens from the \`v0.2.0\` tag' README.md | wc -l` -> 1.
    Mutation(
        ident="M25",
        target="pyproject.toml",
        search='version = "0.3.0"',
        replace='version = "0.4.0"',
        # Re-pointed 2026-08-13 with the v0.3 scoping roll, and the subject is unchanged:
        # the anchor is the declared version literal, so it necessarily moves every time
        # that literal does. The harness refused to run rather than silently dropping to
        # 25 mutations while printing 26 — which is the behaviour that made this a
        # two-minute fix instead of a quiet hole.
        breaks="silently changes the version this package would publish under — the wheel filename, its METADATA and what `pip install bot-y==<v>` resolves — while README.md's publication instruction, CHANGELOG.md's top released heading and the project's own milestone all keep stating the old one. Before REQ-20 nothing offline read `[project] version` at all, so this edit was invisible to the entire suite",
    ),
    Mutation(
        ident="M26",
        target="README.md",
        search="Publication happens from the `v0.3.0` tag",  # re-pointed with the v0.3 roll, same reason as M25
        replace="Publication happens from the `v0.9.0` tag",
        breaks="the README tells a stranger to install from a tag this package was never built as. It is the other direction of the same binding — M25 moves the declaration away from the records, this moves a record away from the declaration — and one direction alone would be satisfied by a gate that only ever watched pyproject.toml move",
    ),
    # M27 AND M28 SHARE A `search` STRING DELIBERATELY, on M6/M7's precedent —
    # "each mutation is applied in its own sandbox, so there is no interaction
    # between them" — and for M6/M7's reason: they prove different things about
    # one expression. The item-price comparison is the whole of what is left of
    # the price defence once shipping cannot be read, and it has to be shown to
    # bite in BOTH directions. M27 proves the branch ALERTS at all; M28 proves
    # the ceiling STILL BINDS inside it. A single mutation would leave whichever
    # half it did not rebuild unguarded, and the two halves fail in opposite
    # directions: one silently un-reverses a user's decision, the other silently
    # over-reads it.
    Mutation(
        ident="M27",
        target="boty/models.py",
        search="        return self.price <= self.watch.max_price",
        replace="        return False",
        breaks="rebuilds 06-01's strict refusal exactly, undoing Dan's 2026-08-11 reversal: an offer whose shipping cost could not be read never alerts again, so Nintendo — the only first-party GO Plus + listing in this project's config — and Amazon go quiet, with every test around them still looking sensible",
    ),
    Mutation(
        ident="M28",
        target="boty/models.py",
        search="        return self.price <= self.watch.max_price",
        replace="        return True",
        breaks="rebuilds the MISREADING of Dan's decision — \"where we don't know just send it\" taken to mean send it at any price — so a $229.99 reseller listing whose shipping nobody read pages him, which is the most likely future regression here because it reads exactly like the decision",
    ),
    # ------------------------------------------------------------------
    # M29 AND M30 ARE THE TWO DIRECTIONS OF ONE RULE, on M27/M28's precedent:
    # Dan, 2026-08-12, the second time he raised it — *"im still getting annoying
    # messages. we need to never hit the user unless its something they can buy
    # or actually do"*. A push now costs a `Health.action`, a stated thing a
    # person can DO, and the field is empty unless an arm fills it.
    #
    # M29 rebuilds LOUDNESS: the filter stops reading the field, so every health
    # state pages again — including the one that fired at 16:49:58 that day about
    # an Amazon control nobody can repair from a phone.
    # M30 rebuilds SILENCE where the one remedy exists: the store-pin arm stops
    # naming it, so the single health state Dan can close goes quiet.
    #
    # ONE MUTATION WOULD LEAVE THE OTHER HALF UNGUARDED, and the halves fail in
    # opposite directions — one restores the noise that trained him to ignore
    # this channel, the other satisfies "stop the noise" by pushing nothing at
    # all, which is the cheapest way to pass a suppression rule and the way that
    # loses him a monitor.
    #
    # BOTH ARE ANCHORED ON BEHAVIOUR AND NEITHER TOUCHES PROSE — M2's lesson,
    # which this repository has now paid for twice. M29 is the comprehension that
    # decides; M30 is a conditional over a NAME, which is exactly why
    # `STORE_PIN_ACTION` is a module constant rather than a literal at the call
    # site. The sentence a person reads can be rewritten freely without either
    # mutation drifting.
    #
    # M21-M24 ARE AN INTENTIONAL GAP and are not filled here.
    #
    # WHICH TESTS ARE EXPECTED TO CATCH EACH. M29:
    # tests/test_cli_watch.py's REQ-16 paging section (re-pointed 2026-08-13:
    # that section was labelled REQ-21, an ident that was invented in a test
    # file and never existed as a requirement — its subject is REQ-16's. v0.3
    # minted a real REQ-21 meaning something else entirely, so this citation
    # would otherwise have become ambiguous. Nothing about what M29 tests
    # changed), in particular
    # test_a_control_that_stopped_reading_in_stock_is_recorded_and_not_pushed and
    # test_a_health_state_nobody_has_written_yet_is_silent. M30: that section's
    # test_the_store_pin_gap_is_pushed_because_a_person_can_close_it, plus
    # tests/test_alert_text.py's
    # test_exactly_one_arm_names_something_a_person_can_do. If either SURVIVES,
    # the first thing to check is whether the paging decision acquired a second
    # gate somewhere — two gates on one rule means neither can be shown to bite.
    Mutation(
        ident="M29",
        target="boty/cli.py",
        search="    pageable = [h for h in unhealthy if h.action]",
        replace="    pageable = list(unhealthy)",
        breaks="every health state wakes somebody again, which is the blocklist-shaped default Dan has now asked to have removed twice: a refusal nobody can answer, a control nobody can repair and every arm added after today all page, and the alert channel this project exists to be trusted on fills up with states that ask for no decision",
    ),
    Mutation(
        ident="M30",
        target="boty/monitor.py",
        search='                    action=STORE_PIN_ACTION if store_gap else "",',
        replace='                    action="",',
        breaks="the one health state a person can close stops saying so, so nothing reaches a phone at all — an unpinned or mismatched store leaves every Walmart reading UNKNOWN forever, silently, which is the suppression rule satisfied by deleting the monitor rather than the noise",
    ),
    # ------------------------------------------------------------------
    # M31 — A NON-READ ARM STAMPS THE MOMENT OF ITS REFUSAL. REQ-21, 2026-08-13.
    #
    # This is the phase's own defect rebuilt inside the fix meant to prevent it,
    # which is why it is the one mutation 07-01 ships. A refusal DOES happen at a
    # wall-clock moment. It took no READING. `boty/models.py`'s `read_at` dates a
    # reading, so stamping a refusal refreshes the age of a reading nobody took —
    # and `pacing.py:196-199` already wrote the lesson down for `_warned_since`:
    # *"stamping at write time would refresh the record forever and the age-out
    # would never fire once — a bound that cannot bind is worse than no bound,
    # because it reads like one in the file."*
    #
    # WHICH ARM, SPECIFICALLY — never "an error arm". `apply_mutation` replaces
    # the FIRST occurrence, so the `breaks=` sentence has to describe the line the
    # anchor actually lands on or it describes something that did not happen (M19
    # is the recorded trap; this repository has paid for it once). The anchor was
    # PRE-COUNTED against the tree it is registered on:
    #
    #     grep -c 'refused=True, store=None, shipping=None, read_at=None' \
    #         boty/retailers.py   ->   1
    #
    # Exactly one, at `boty/retailers.py:544` — `check_html`'s `except Blocked`
    # arm. The bare substring `read_at=None` occurs 17 times in that file (9
    # construction sites plus the comments that argue them), which is why the
    # anchor is the arm's whole stated metadata rather than the field alone.
    #
    # BEHAVIOURAL, NOT PROSE. It carries no message text, no tag, no `detail`
    # string and no version literal — it is the keyword metadata four arms state
    # explicitly. That is the hard rule after M25 and M26 both drifted on
    # 2026-08-13 when the milestone version rolled, and after M2 was re-anchored
    # in 2026-08-04 when the prose on its branch moved.
    #
    # THE REPLACEMENT DEPENDS ON `time` BEING IMPORTED IN `boty/retailers.py`, and
    # it is (added by 07-01 for `_verdict_from_html`'s stamp). That dependency is
    # deliberate: the mutant must produce a PLAUSIBLE WRONG AGE rather than a
    # `NameError`. A mutation caught by a crash proves nothing about the rule — it
    # proves the suite notices a broken module, which it would notice anyway.
    #
    # WHICH TESTS ARE EXPECTED TO CATCH IT: `tests/test_retailers.py`'s
    # `test_a_transport_that_refused_took_no_reading` (the `check_html` x `Blocked`
    # parametrisation asserts `read_at is None`) and
    # `test_the_read_and_non_read_arms_are_partitioned_exactly` (the AST partition
    # sees the literal `None` become a call). If it ever SURVIVES, the first thing
    # to check is whether either acquired a skip decorator or stopped asserting
    # `is None` in favour of falsiness — `0.0` is falsy, and a falsiness assertion
    # would let a different wrong answer through the same gate.
    #
    # M32 IS NOT A SECOND GAP. `07-PLAN-OUTLINE.md` assigns it to **07-02**
    # (`State.load` defaulting a missing stamp to `time.time()` — criterion 4's
    # failure in one line). The orchestrator reserved M31-M32 for this phase's
    # first wave; 07-01 consumes M31 only and leaves M32 to the plan the outline
    # assigns it to, rather than renumbering five downstream plans and 07-06's
    # arithmetic. `tests/test_support_matrix.py`'s own message governs: *"Idents
    # are reserved across concurrent plans, not renumbered."*
    #
    # M21-M24 REMAIN THE INTENTIONAL GAP and are still not filled.
    Mutation(
        ident="M31",
        target="boty/retailers.py",
        search="refused=True, store=None, shipping=None, read_at=None",
        replace="refused=True, store=None, shipping=None, read_at=time.time()",
        breaks="`check_html`'s `except Blocked` arm — a refusal that never received a page now stamps the moment of the refusal, so every refusal refreshes the age of a reading nobody took. Amazon and Walmart have both been refusing this host for hours at a stretch, so both would publish a perpetually fresh age while nothing was read at all: the 2026-08-12 failure REQ-21 exists to fix, rebuilt inside the fix",
    ),
    # ------------------------------------------------------------------
    # M32 — LOAD DEFAULTS A MISSING STAMP TO NOW. REQ-21, 2026-08-13.
    #
    # M31 is this defect at the READING; M32 is the same defect at the RESTART,
    # which is criterion 4's failure in one line: "the age survives a service
    # restart, so a restart cannot make a two-day-old reading look fresh".
    #
    # WHICH LINE, SPECIFICALLY, AND PRE-COUNTED BEFORE REGISTRATION. The anchor is
    # `monitor._remembered_stamp`'s type guard AND the `return None` beneath it,
    # joined with an explicit `\n` exactly as M2 does, because `apply_mutation`
    # replaces the FIRST occurrence and a non-unique anchor mutates a line this
    # `breaks=` sentence is not describing — M19's recorded trap, which this
    # repository has paid for once. Measured against the tree this is registered
    # on:
    #
    #     grep -c 'if not isinstance(stamp, (int, float)) or isinstance(stamp, bool):' \
    #         boty/monitor.py   ->   1
    #
    # and the two-line string itself counted once over the file's text. The bare
    # `return None` occurs 3 times in that file, which is why the guard is carried
    # into the anchor rather than the fall-through alone.
    #
    # BEHAVIOURAL, NOT PROSE — a type guard and its fall-through, carrying no
    # message text, no rendered tag, no `detail` string and no version literal.
    # That is § *Finding 1*'s hard rule after M25 and M26 both drifted on
    # 2026-08-13 when the milestone version rolled, and after M2 was re-anchored
    # in 2026-08-04 when the prose on its branch moved.
    #
    # `now` IS A PARAMETER OF THE ENCLOSING FUNCTION, so the replacement yields a
    # PLAUSIBLE WRONG AGE rather than a `NameError`. A mutation caught by a crash
    # proves nothing about the rule — it proves the suite notices a broken module,
    # which it would notice anyway.
    #
    # WHY THIS GUARD AND NOT THE PRE-07 BRANCH ABOVE IT. This one covers BOTH
    # directions the phase has to hold: the one-time migration of Dan's bare-string
    # document, AND the `"read_at": null` this program writes for itself on every
    # cycle thereafter for any entry whose moment was never established. So the
    # gate sits on the path that runs at every restart forever, rather than on the
    # one that runs once.
    #
    # THE SAVE-SIDE MIRROR — `save` inventing a stamp — IS GUARDED BY A TEST AND
    # NOT BY A MUTATION, and the asymmetry is stated rather than left to be
    # noticed: this plan holds one ident, and the LOAD direction is the one
    # criterion 4 names. `tests/test_monitor.py`'s
    # `test_saving_the_migrated_document_twice_never_invents_an_age` is the
    # save-side gate.
    #
    # WHICH TESTS ARE EXPECTED TO CATCH IT — SEVEN, MEASURED BY APPLYING IT
    # RATHER THAN PREDICTED. In `tests/test_monitor.py`:
    # `test_a_pre_07_document_loads_as_availability_with_an_unknown_age`,
    # `test_the_real_pre_07_document_loads_with_its_alert_behaviour_unchanged`
    # (13 undated entries all come back dated NOW),
    # `test_saving_the_migrated_document_twice_never_invents_an_age`, and
    # `test_a_stamp_that_cannot_be_believed_loses_the_age_and_keeps_the_memory`
    # at its `null`, `a-string` and `a-bool` parametrisations. In
    # `tests/test_cli_watch.py`:
    # `test_a_reading_the_first_process_could_not_date_comes_back_undated`.
    #
    # THE OTHER THREE PARAMETRISATIONS ARE NOT KILLERS AND THAT IS CORRECT, not
    # a gap: `in-the-future`, `zero` and `a-seconds-value-that-lost-a-thousand`
    # are all real numbers, so they pass THIS guard and are rejected by the
    # `EARLIEST_CREDIBLE_READING <= stamp <= now` bound one line below, which
    # this mutation does not touch. Naming them as expected killers would be
    # describing a catch that did not happen — the same defect as a `breaks=`
    # sentence that describes the wrong line.
    #
    # NOR IS `test_the_age_of_a_reading_survives_the_restart`, and the reason is
    # worth the line because 07-02's plan predicted it: its stamp is a real
    # two-day-old float, so `_remembered_stamp` returns before ever reaching this
    # fall-through. The restart-side test that DOES bind is the undated one named
    # above, and it was added when this was measured — a gate is named after
    # watching it fail, never after expecting it to.
    #
    # If it ever SURVIVES, the first thing to check is whether one of the seven
    # acquired a skip decorator.
    #
    # M33 IS NOT A NEW GAP. `07-PLAN-OUTLINE.md` assigns it to **07-03**
    # (`current_interval` ignoring the backoff). 07-01 reserved M32 for this plan
    # and this plan consumes M32 only. `tests/test_support_matrix.py`'s own
    # message governs: *"Idents are reserved across concurrent plans, not
    # renumbered."*
    #
    # M21-M24 REMAIN THE INTENTIONAL GAP and are still not filled.
    Mutation(
        ident="M32",
        target="boty/monitor.py",
        search="    if not isinstance(stamp, (int, float)) or isinstance(stamp, bool):\n        return None",
        replace="    if not isinstance(stamp, (int, float)) or isinstance(stamp, bool):\n        return now",
        breaks="`monitor._remembered_stamp`'s type guard stops meaning \"the age is not established\" and starts meaning \"the age is now\", so every entry with no believable stamp comes back off disk dated at the instant the daemon started. Applied to the document on this host that is all 13 entries — including `walmart:Pokémon GO Plus +`, which has not been updatable since 2026-08-12 and cannot be until a store is pinned — so a restart makes a two-day-old reading look four seconds old. That is criterion 4's failure in one line, and it is the same manufacture of an age nobody recorded that REQ-21 exists to end, moved from the reading to the restart",
    ),
    # ------------------------------------------------------------------
    # M33 — THE ACCESSOR IGNORES THE BACKOFF. REQ-21, 2026-08-13.
    #
    # Criterion 3 says a reading is stale when it is older than its retailer's
    # current interval, "derived from the retailer's own pacing rather than a
    # fixed clock". This mutation is that clause deleted: `current_interval`
    # returns the STANDING config value and the backoff stops reaching any
    # surface.
    #
    # THE ANCHOR IS MULTI-LINE, AND THAT SHAPE WAS MEASURED BEFORE IT WAS
    # CHOSEN rather than after it misfired. `st.interval * BACKOFF_FACTOR **
    # st.refusals` occurs TWICE in `boty/pacing.py`:
    #
    #     python -c "...src.count('st.interval * BACKOFF_FACTOR ** st.refusals')"
    #         ->  2   (line 156, inside MAX_PERSISTED_REFUSALS' comment, which
    #                  QUOTES the expression to argue the float-overflow cliff;
    #                  and line 344, the accessor's own return)
    #     python -c "...src.count(the four-line `return min(...)` form)"
    #         ->  1
    #
    # `apply_mutation` replaces the FIRST occurrence, so a single-line anchor
    # would mutate PROSE — changing no behaviour, surviving, and being reported
    # as a hole in the suite with no attribution. That is M19's recorded trap,
    # and this is the second time this repository has priced it; M2 carries the
    # same multi-line `\n`-joined shape for the same reason.
    #
    # BEHAVIOURAL, NOT PROSE — an arithmetic expression and a `min`, carrying no
    # message text, no rendered tag, no `detail` string and no version literal.
    # § *Finding 1*'s hard rule after M25 and M26 both drifted on 2026-08-13 when
    # the milestone version rolled.
    #
    # IT BREAKS TWO THINGS AT ONCE, AND THAT IS THE DESIGN BEING ASSERTED rather
    # than sloppiness in the anchor. `record` computes its wait by CALLING this
    # accessor, so the published cadence and the fetch schedule are one
    # expression. A mutation that broke only the published number would mean the
    # two had drifted apart — which is the thing 07-03 exists to make impossible.
    # One mutation proving both is the join under test.
    #
    # WHICH TESTS CATCH IT — ELEVEN, MEASURED BY APPLYING IT BY HAND RATHER THAN
    # PREDICTED. A gate is named after watching it fail, never after expecting it
    # to; 07-02 paid for that rule when M32's predicted killer turned out not to
    # bind. Nine in `tests/test_pacing.py`:
    #
    #   the REQ-21 accessor section —
    #     test_the_current_interval_widens_with_the_backoff  (both intervals)
    #     test_a_retailer_that_answers_is_back_on_its_standing_interval_at_once
    #     test_the_backoff_schedule_is_exactly_the_schedule_it_was  (both)
    #   and the 2026-08-04 backoff section, which predates REQ-21 entirely —
    #     test_a_refusal_pushes_the_next_attempt_out_exponentially
    #     test_the_backoff_is_capped_so_a_monitor_does_not_quietly_stop_monitoring
    #     test_the_restored_count_is_load_bearing_on_the_next_wait
    #     test_the_persisted_count_is_clamped
    #
    # THOSE LAST FOUR ARE THE JOIN SHOWING UP IN THE MEASUREMENT. They were
    # written before this accessor existed and they fail anyway, because `record`
    # now computes its wait through it — which is the design claim above,
    # observed rather than asserted. A version of this change that published a
    # number beside the schedule instead of through it would leave all four
    # green.
    #
    # Two in `tests/test_cli_watch.py`:
    #     test_both_surfaces_publish_one_cadence_from_one_document, which asserts
    #       the shared value is 2400.0 precisely so that "both surfaces agree on
    #       300" cannot pass it
    #     test_a_refusal_the_backoff_is_handling_is_recorded_not_pushed_across_a_restart,
    #       from the REQ-16-across-a-restart section, whose MEASURED cycle counts
    #       (10 cycles yields exactly 3 refusals) move the moment the schedule
    #       does
    #
    # Measured: `pytest tests/test_pacing.py tests/test_cli_watch.py -q` exits 1
    # at 11 failed / 100 passed. If it ever SURVIVES, the first thing to check is
    # whether one of them acquired a skip decorator.
    #
    # WHY THERE IS NO PAIRED MUTATION FOR THE MIRROR DIRECTION. The opposite
    # failure — a retailer on the standard cadence publishing a WIDER window than
    # it is on, so a genuinely stale reading reads as fresh — is guarded by
    # assertions rather than by a second ident: `current_interval` is asserted
    # EQUAL to the standing interval at zero refusals, to the float, and
    # `tests/test_status.py` pins the retailers array as a whole dict. Stated
    # plainly rather than left to be noticed as an asymmetry.
    #
    # M34 IS NOT A NEW GAP. `07-PLAN-OUTLINE.md` assigns it to **07-04** (a
    # remembered row published as `checked: true`, or with its stamp dropped).
    # This plan consumes M33 only. `tests/test_support_matrix.py`'s own message
    # governs: *"Idents are reserved across concurrent plans, not renumbered."*
    #
    # M21-M24 REMAIN THE INTENTIONAL GAP and are still not filled.
    Mutation(
        ident="M33",
        target="boty/pacing.py",
        search="        return min(\n            st.interval * BACKOFF_FACTOR ** st.refusals,\n            MAX_BACKOFF_SECONDS,\n        )",
        replace="        return st.interval",
        breaks="`Pacer.current_interval` returns the standing config interval however many refusals are in force, so the backoff stops reaching any surface. On this host that is target and walmart at seven refusals judged against 300 s instead of the six-hour cap they are actually on, and amazon against 1800 s instead of 7200 — every reading from a backed-off retailer reads as wildly stale on all three surfaces, which is criterion 3's \"derived from the retailer's own pacing rather than a fixed clock\" stated as a mutation. And because `record` computes its wait THROUGH this accessor, the fetch schedule collapses with it: a retailer that just walled us is asked again at full rate, which is the 2026-08-04 behaviour boty/pacing.py exists to prevent and the politeness constraint calls a hard limit",
    ),
)


class HarnessError(RuntimeError):
    """The sandbox is wrong, so nothing the run reports can be believed."""


def _git_or_harness_error(argv: list[str], tmp: Path) -> None:
    """Run a git command in the sandbox; a failure is a broken sandbox, not a result.

    The module's contract is that anything wrong with the copy raises
    HarnessError carrying the cause, rather than surfacing as a bare
    CalledProcessError or — worse — as a mutation score.
    """
    proc = subprocess.run(argv, cwd=tmp, capture_output=True, text=True)
    if proc.returncode != 0:
        raise HarnessError(
            f"cannot give the sandbox a git index: {' '.join(argv)} exited "
            f"{proc.returncode} in {tmp}.\n{proc.stderr.strip()}"
        )


def build_sandbox() -> Path:
    """Copy the package, the suite and pyproject.toml into a fresh temp dir."""
    tmp = Path(tempfile.mkdtemp(prefix="boty-mutation-"))
    if not str(tmp).startswith(tempfile.gettempdir()):  # pragma: no cover - paranoia
        raise HarnessError(f"refusing to use sandbox outside the temp dir: {tmp}")
    for item in SANDBOX_CONTENTS:
        src = REPO_ROOT / item
        if not src.exists():
            raise HarnessError(f"cannot build sandbox: {src} does not exist")
        if src.is_dir():
            shutil.copytree(src, tmp / item, ignore=_IGNORE)
        else:
            shutil.copy2(src, tmp / item)

    # The suite reaches for the git INDEX, not only for files, so a copy without
    # one is not the faithful copy this module's docstring demands. Without it,
    # `git ls-files` exits 128 in here and
    # tests/test_packaging_metadata.py::_tracked_top_level_dirs raises
    # NotATrackedTree — deliberately, because the alternative is that the only
    # gate on this project's published file surface reports success in the one
    # place it could not run. Three tests in tests/test_identity_check.py also
    # stop skipping once this exists, which is a strengthening: the identity
    # guard's scope test should run wherever the suite runs. It costs ~3.3 s per
    # sandbox, times the nine sandboxes main() builds. That is the price and it
    # is accepted; do not buy it back by deleting these two lines.
    #
    # `-c` goes BEFORE `init`. Measured on git 2.43.0: `git init -q -c
    # init.defaultBranch=main` is not valid git — it exits 129 with ``unknown
    # switch `c` `` — so the wrong order makes every build_sandbox() call raise,
    # and the HarnessError it produces points the reader at SANDBOX_CONTENTS,
    # which is not the cause.
    #
    # No commit is made. `git ls-files` reads the index, and committing would
    # need a user.name and user.email that no box has to have configured for a
    # throwaway directory.
    _git_or_harness_error(["git", "-c", "init.defaultBranch=main", "init", "-q"], tmp)
    _git_or_harness_error(["git", "add", "-A"], tmp)
    return tmp


def _env(sandbox: Path) -> dict[str, str]:
    env = {**os.environ, "PYTHONPATH": str(sandbox)}
    # The sandbox must be self-contained; an inherited override would point the
    # fixture loader back at the real tree.
    env.pop("BOTY_FIXTURE_ROOT", None)
    return env


def run_suite(sandbox: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
        cwd=sandbox,
        env=_env(sandbox),
        capture_output=True,
        text=True,
    )


def assert_imports_from_sandbox(sandbox: Path) -> None:
    """Fail loudly if `import boty` resolves to the real, unmutated package."""
    proc = subprocess.run(
        [sys.executable, "-c", "import boty; print(boty.__file__)"],
        cwd=sandbox,
        env=_env(sandbox),
        capture_output=True,
        text=True,
    )
    resolved = proc.stdout.strip()
    if proc.returncode != 0 or not resolved:
        raise HarnessError(f"could not import boty inside the sandbox: {proc.stderr.strip()}")
    if not resolved.startswith(str(sandbox)):
        raise HarnessError(
            f"sandbox is not on the import path: `import boty` resolved to {resolved}, "
            f"not {sandbox}. Every mutation would be applied to a copy nobody imports, "
            "so all three would 'survive' and this check would fail for the wrong reason."
        )


def _failed_tests(proc: subprocess.CompletedProcess[str]) -> list[str]:
    # `FAILED tests/test_parse.py::test_name - AssertionError: ...`
    return [line.split(" ")[1] for line in proc.stdout.splitlines() if line.startswith("FAILED ")]


def run_baseline() -> None:
    """Run the UNMUTATED copy and require it to pass. Aborts otherwise."""
    sandbox = build_sandbox()
    try:
        assert_imports_from_sandbox(sandbox)
        proc = run_suite(sandbox)
        if proc.returncode != 0:
            meaning = _PYTEST_CODES.get(proc.returncode, "unrecognised pytest exit code")
            raise HarnessError(
                f"baseline FAILED in the unmutated sandbox (pytest exit {proc.returncode}: {meaning}).\n"
                "Without a passing baseline every 'mutation caught' below would really be\n"
                "'sandbox broken', and this check would report success while proving nothing.\n"
                f"--- pytest stdout ---\n{proc.stdout}\n--- pytest stderr ---\n{proc.stderr}"
            )
        tail = proc.stdout.strip().splitlines()
        print(f"  baseline  unmutated sandbox passes ({tail[-1] if tail else 'no pytest output'})")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def apply_mutation(sandbox: Path, mutation: Mutation) -> None:
    path = sandbox / mutation.target
    before = path.read_text(encoding="utf-8")
    if mutation.search not in before:
        raise HarnessError(
            f"{mutation.ident}: anchor not found in {mutation.target}.\n"
            f"  looked for: {mutation.search!r}\n"
            "The source drifted away from this mutation. Skipping it silently would\n"
            "quietly reduce the check to two mutations while still printing a total."
        )
    after = before.replace(mutation.search, mutation.replace, 1)
    if after == before:
        raise HarnessError(f"{mutation.ident}: substitution left {mutation.target} unchanged")
    path.write_text(after, encoding="utf-8")


def check_mutation(mutation: Mutation) -> bool:
    """True if the suite caught this mutation. Raises HarnessError if unclear."""
    sandbox = build_sandbox()
    try:
        apply_mutation(sandbox, mutation)
        proc = run_suite(sandbox)
        code = proc.returncode

        if code == 1:
            names = _failed_tests(proc)
            caught_by = ", ".join(n.split("::")[-1] for n in names[:3]) or "the suite"
            extra = f" (+{len(names) - 3} more)" if len(names) > 3 else ""
            print(f"  CAUGHT    {mutation.ident} {mutation.target}: {len(names)} test(s) failed — {caught_by}{extra}")
            return True

        if code == 0:
            print(f"  SURVIVED  {mutation.ident} {mutation.target}: the suite passed anyway")
            return False

        meaning = _PYTEST_CODES.get(code, "unrecognised pytest exit code")
        raise HarnessError(
            f"{mutation.ident}: pytest exited {code} ({meaning}), not 1.\n"
            "Only exit code 1 — real test failures — can count as a mutation being caught.\n"
            "Anything else means the sandbox itself is broken, and counting it would let\n"
            "a suite with no tests in it score a perfect result.\n"
            f"--- pytest stdout ---\n{proc.stdout}\n--- pytest stderr ---\n{proc.stderr}"
        )
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def main() -> int:
    print(f"mutation check: {len(MUTATIONS)} mutation(s), sandboxed (the working tree is never touched)")

    try:
        run_baseline()
        survivors = [m for m in MUTATIONS if not check_mutation(m)]
    except HarnessError as exc:
        print(f"\nmutation check: HARNESS ERROR\n{exc}", file=sys.stderr)
        print(
            "\nThis is not a result. Nothing was proved about the test suite either way.",
            file=sys.stderr,
        )
        return 2

    caught = len(MUTATIONS) - len(survivors)
    print(f"mutation check: {caught}/{len(MUTATIONS)} mutations caught")

    if survivors:
        sys.stdout.flush()
        print("", file=sys.stderr)
        for m in survivors:
            print(f"  SURVIVED {m.ident} in {m.target}: {m.breaks}", file=sys.stderr)
            print(f"           search: {m.search!r}", file=sys.stderr)
        print(
            "\n  A survivor names a specific hole in the suite: that breakage can be shipped\n"
            "  with every test green. Add an assertion that fails when it is applied.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
