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
SANDBOX_CONTENTS = (
    "boty", "tests", "scripts", "config", "served", "docs", "pyproject.toml", "Makefile",
    "README.md",
)

_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "*.egg-info")

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
        search='Availability.UNKNOWN,\n            detail="no structured stock data found',
        replace='Availability.OUT_OF_STOCK,\n            detail="no structured stock data found',
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
)


class HarnessError(RuntimeError):
    """The sandbox is wrong, so nothing the run reports can be believed."""


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
