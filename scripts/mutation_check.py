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
SANDBOX_CONTENTS = (
    "boty", "tests", "scripts", "config", "served", "docs", "hooks", "pyproject.toml",
    "Makefile", "README.md", "CONTRIBUTING.md", "LICENSE", "MANIFEST.in",
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
    Mutation(
        ident="M4",
        target="boty/models.py",
        search="        if self.price is None:\n            return False\n        return self.price <= self.watch.max_price",
        replace="        if self.price is None:\n            return True\n        return self.price <= self.watch.max_price",
        breaks="an unreadable price clears the ceiling — a flip at any price becomes alertable",
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
