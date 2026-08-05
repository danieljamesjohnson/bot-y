#!/usr/bin/env python3
"""Prove the published artifacts, not the checkout they were built from.

WHY THIS FILE EXISTS
--------------------
An editable install *is* the checkout. `pip install -e .` puts this repository
on `sys.path` and nothing else changes, so every green `make verify` in this
project's history says exactly nothing about what a stranger gets from
`pip install bot-y`. The two are different artifacts with different file sets,
and only one of them has ever been tested.

`[tool.setuptools.packages.find] include = ["boty*"]` is why the gap has teeth:
`scripts/`, `tests/` and `config/` are NOT packaged. Anything the installed CLI
reaches for outside `boty/` resolves fine in a checkout and is a hard failure in
a wheel, and there is exactly one way to find out which — put a wheel somewhere
that is not this repository and run it.

That found one. Measured 2026-08-04: on a wheel installed into a clean venv and
run from `/tmp`, `boty --help` exited 0 and `boty check` — the first command
README teaches — died with an uncaught `FileNotFoundError` naming
`config/products.yaml`, a path inside a directory this package deliberately does
not ship. Nothing else in this project would have noticed, because `make verify`
runs from the repo root, where that path resolves. The fix is in `boty/cli.py`;
`SMOKE_ARGS` below is what stops it coming back through a change nobody
connected to packaging.

WHY THIS IS NOT A `verify` STAGE
--------------------------------
It creates two virtual environments and downloads from PyPI. `make verify` and
`make verify-offline` are network-free by contract — the test suite asserts its
own isolation — and `.github/workflows/ci.yml` runs `verify-offline` on every
pull request. Putting a network gate inside either would make that contract
false and make every contributor's every commit wait on pypi.org. So this is its
own target, `make release-check`, and it is run before a release rather than on
every change.

WHY THE BUILD HAPPENS IN AN EMPTY VENV
--------------------------------------
The reason is stronger than dependency hygiene, and it is the whole design of
this file. Building inside `.venv` — which already has `curl_cffi`, `PyYAML` and
`apprise` installed — CANNOT detect a missing or wrong `Requires-Dist`, because
every import resolves anyway from packages that happen to be lying around.
Building in a venv holding only `build` and `twine`, and then installing the
resulting wheel into a SECOND venv holding nothing at all, is what turns the
dependency declaration from a statement into a measurement.

A `release` extra in `pyproject.toml` was the alternative. It was rejected: it
publishes a `Provides-Extra: release` claim to every installer, it takes the
`dev` extra's promise ("everything needed to run `make verify`") from three
packages to roughly fifteen, and it still leaves the build happening wherever
the caller happens to be standing.

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
It does not publish, tag, or create a release. No upload verb appears anywhere
in this file and none ever should: the first publish permanently claims a name
on PyPI and a pushed tag is visible to everyone watching the repository. Both
are the maintainer's, by explicit reservation. `twine` is invoked here by
`_twine_check` and nowhere else — an acceptance criterion greps this file for
the upload verbs, so naming one in this prose would defeat the check that keeps
it out.

Exit 0 when every check passed, 1 when a check failed, 2 on a usage error.
There is deliberately NO partial-success code. `scripts/control_check.py` has
one (3 SKIPPED, 4 INCOMPLETE) because it has a real "could not run here" case
worth telling apart — a live retailer is not reachable from every machine. Every
check in this file is either performed or the whole run is meaningless, so a
third verdict would only give a future caller something green to accept.

    scripts/release_check.py            # build, prove, clean up
    scripts/release_check.py --keep     # leave the temp trees for inspection
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

# Run from a checkout without installing: make `scripts/` importable, so the
# identity rule below is the SAME function `make verify` runs rather than a
# second copy of it. Same idiom as scripts/control_check.py and
# scripts/evidence_check.py one directory over, including the E402 suppression
# on the import below — ruff does not raise E402 after a `sys.path` mutation but
# pycodestyle does, and `[tool.ruff.lint] external = ["E402"]` is what stops
# RUF100 reporting the directive as unused and autofixing it away. (The literal
# directive is deliberately not written out in this prose: ruff parses every
# occurrence of it, including one inside a comment, and warns that the trailing
# text is not a rule code. 04-04 met the same collision one file over.)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from identity_check import scan  # noqa: E402

#: What the ephemeral build environment gets, and nothing else. The project is
#: never installed into it.
#:
#: The twine floor is a measurement, and both halves of it are recorded because
#: the pin is conservative ON PURPOSE rather than by accident. This project emits
#: `Metadata-Version: 2.4` today. Against that metadata, twine **5.1.1 rejects
#: the wheel outright** — `InvalidDistribution: Metadata is missing required
#: fields: Name, Version. ... is using a supported Metadata-Version: 1.0, 1.1,
#: 1.2, 2.0, 2.1, 2.2, 2.3` — while twine **6.0.1 passes** and **7.0.0 passes**.
#: So the measured floor is 6.0.1. The pin sits at 6.1 because that is the number
#: 04-02's handoff named: the stricter of the two, kept deliberately.
#:
#: Supply-chain note (audited 2026-08-04, in the form the `nodriver` and `ruff`
#: notes in pyproject.toml use). Both are published by the PyPA — the same
#: organisation that publishes `setuptools`, which `[build-system] requires`
#: already executes on every build of this project, so the publisher is inside
#: this project's trust boundary already rather than new to it. `build` 1.5.0,
#: MIT, 36 releases, source github.com/pypa/build. `twine` 7.0.0, Apache-2.0, 60
#: releases, source github.com/pypa/twine. Typosquat neighbours checked by name:
#: `buld`, `biuld`, `twinee` and `pypa-build` are all 404. Three adjacent names
#: DO exist and were resolved rather than left as an unrecorded 200 — `twin`
#: 0.0.1 (Brandon Hoffman, no summary, no uploaded files at all, so it cannot
#: even be installed), `python-build` 0.2.13 (Colm O'Connor, "Tool to download
#: and build python based upon pyenv", last released 2015) and `py-build` 0.2.0
#: (Cory Laughlin, github.com/Aesonus/py-build, last released 2021). None is
#: PyPA, none is a build frontend, and none is installed here: the two strings
#: below are exact.
BUILD_REQUIREMENTS = ("build", "twine>=6.1")

#: The console script name `[project.scripts]` declares. Note that it is `boty`
#: while the DISTRIBUTION is `bot-y`; the two differing is the whole reason
#: README's install section carries a name-confusion warning.
CONSOLE_SCRIPT = "boty"

#: Argument vectors run against the INSTALLED console script, with the exit code
#: each must produce.
#:
#: The second one is not a CLI test — `tests/test_cli_watch.py` owns that. It is
#: a PACKAGING test, and it is the exact invocation that found the bug described
#: at the top of this file: a default config path that only resolves inside a git
#: checkout. Running it here, from a wheel, from outside the repository, is what
#: stops that regression returning through an edit nobody connected to packaging.
SMOKE_ARGS: tuple[tuple[tuple[str, ...], int], ...] = (
    (("--help",), 0),
    (("check", "-c", "no-such-config.yaml"), 2),
)

#: Must not appear in a default install's `pip list`. `nodriver` is AGPL-3.0
#: against this project's MIT and is an optional extra for that reason — the
#: maintainer decision of 2026-08-02, recorded under the `browser` extra in
#: pyproject.toml. This asserts it against the BUILT ARTIFACT rather than against
#: the config that produced it.
FORBIDDEN_IN_INSTALL = ("nodriver",)

#: Directory prefixes that must appear in neither artifact.
#:
#: This duplicates nothing. `MANIFEST.in` states the INTENT — eight `prune`
#: lines — and this states what was actually OBSERVED in a built file list. A
#: manifest and a wheel are produced by different machinery, and this is the only
#: place the stated and the actual can be seen to agree.
PRUNED_PREFIXES = (
    "tests/", "config/", "docs/", "scripts/", "deploy/", "hooks/", "served/",
    ".planning/", ".github/",
)

#: Files an sdist must carry beyond the package itself. `README.md`, `LICENSE`
#: and `pyproject.toml` arrive through setuptools' own defaults; `CHANGELOG.md`
#: arrives only because `MANIFEST.in` names it, which is what makes it worth
#: asserting.
SDIST_REQUIRED = ("CHANGELOG.md", "README.md", "MANIFEST.in", "pyproject.toml")


class ReleaseCheckError(RuntimeError):
    """The harness could not run, so nothing it would report can be believed.

    Same distinction `scripts/mutation_check.py` draws with `HarnessError`: a
    build that could not happen is not the same finding as artifacts that are
    wrong, and collapsing the two lets a broken environment read as a verdict.
    """


# ---------------------------------------------------------------------------
# Reading what was declared
# ---------------------------------------------------------------------------

def _table_value(text: str, table: str, key: str) -> str | None:
    """The single-line string value of ``key`` inside ``[table]``.

    Deliberately narrow, and there is deliberately no `tomllib` import.
    `tomllib` is stdlib only from Python 3.11, while `requires-python` claims
    `>=3.10` and `.github/workflows/ci.yml` pins 3.10 — so importing it here
    would mean this gate could not run on the floor this package declares.
    04-02 made the same trade one file over.

    `tests/test_packaging_metadata.py` already has a richer reader
    (`_project_table`, `_string`). It is NOT reused, and the reason is the
    direction of the dependency rather than the amount of code: `scripts/` is
    what `make verify` trusts to tell the truth about everything else, and
    making it import from `tests/` would mean a gate script stops working the
    moment the test tree it reaches into moves. `tests/` importing `scripts/` is
    fine and already happens; the reverse is not.
    """
    section = re.escape(f"[{table}]")
    body = re.split(rf"^{section}\s*$", text, maxsplit=1, flags=re.M)
    if len(body) < 2:
        return None
    rest = re.split(r"^\[", body[1], maxsplit=1, flags=re.M)[0]
    match = re.search(rf'^{re.escape(key)}\s*=\s*"([^"]*)"\s*(?:#.*)?$', rest, flags=re.M)
    return match.group(1) if match else None


def _declared_version(pyproject_text: str) -> str | None:
    """The one place this project states its version."""
    return _table_value(pyproject_text, "project", "version")


def _changelog_url(pyproject_text: str) -> str | None:
    """`[project.urls] Changelog`, which must resolve to a file in this repo."""
    return _table_value(pyproject_text, "project.urls", "Changelog")


def _changelog_version(changelog_text: str) -> str | None:
    """The version in the first ``## [x.y.z]`` heading that is not Unreleased."""
    for line in changelog_text.splitlines():
        match = re.match(r"^##\s*\[([^\]]+)\]", line)
        if match and match.group(1).lower() != "unreleased":
            return match.group(1)
    return None


def _wheel_filename_version(wheel: Path) -> str:
    """`bot_y-1.0.0-py3-none-any.whl` -> `1.0.0`."""
    parts = wheel.name.split("-")
    if len(parts) < 2:
        raise ReleaseCheckError(f"cannot read a version out of the wheel name {wheel.name!r}")
    return parts[1]


def _wheel_metadata(wheel: Path) -> str:
    with zipfile.ZipFile(wheel) as zf:
        names = [n for n in zf.namelist() if n.endswith(".dist-info/METADATA")]
        if len(names) != 1:
            raise ReleaseCheckError(f"expected exactly one dist-info/METADATA in {wheel.name}, found {names}")
        return zf.read(names[0]).decode("utf-8", errors="replace")


def _metadata_field(metadata: str, field: str) -> str | None:
    for line in metadata.splitlines():
        if not line.strip():
            break  # the headers end at the first blank line; the body follows
        if line.lower().startswith(f"{field.lower()}:"):
            return line.split(":", 1)[1].strip()
    return None


# ---------------------------------------------------------------------------
# Building, in an environment that holds nothing else
# ---------------------------------------------------------------------------

def _run(argv: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True)


def _tracked_tree(root: Path, dest: Path) -> int:
    """Copy every tracked path into a clean tree, working-tree contents and all.

    Building from the repository root would work, but it would also build from
    whatever untracked files happen to be sitting there — and a published
    artifact is supposed to be a function of what is committed. Copying by
    `git ls-files` makes the input to the build the same set a fresh clone
    would have, which is the set a release is actually built from.
    """
    proc = _run(["git", "-C", str(root), "ls-files", "-z"])
    if proc.returncode != 0:
        raise ReleaseCheckError(f"git ls-files failed in {root}: {proc.stderr.strip()}")
    copied = 0
    for rel in proc.stdout.split("\0"):
        if not rel:
            continue
        src = root / rel
        if not src.is_file():
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        copied += 1
    return copied


def _ephemeral_venv(path: Path, requirements: tuple[str, ...]) -> Path:
    """A venv holding exactly ``requirements`` — no project, no extras."""
    proc = _run([sys.executable, "-m", "venv", str(path)])
    if proc.returncode != 0:
        raise ReleaseCheckError(f"could not create a venv at {path}: {proc.stderr.strip()}")
    python = path / "bin" / "python"
    if requirements:
        proc = _run([str(python), "-m", "pip", "install", "--quiet", *requirements])
        if proc.returncode != 0:
            raise ReleaseCheckError(
                f"could not install {list(requirements)} into {path}:\n{proc.stdout}\n{proc.stderr}"
            )
    return python


def _build(source_root: Path, builder_python: Path, out_dir: Path) -> tuple[Path, Path]:
    """`python -m build`, and BOTH artifacts or it is not a release.

    A wheel with no sdist is a release nobody can rebuild from source, which is
    the thing a distribution packager needs and the thing an archive keeps.
    """
    proc = _run([str(builder_python), "-m", "build", "--outdir", str(out_dir), str(source_root)])
    if proc.returncode != 0:
        raise ReleaseCheckError(f"python -m build failed:\n{proc.stdout}\n{proc.stderr}")
    sdists = sorted(out_dir.glob("*.tar.gz"))
    wheels = sorted(out_dir.glob("*.whl"))
    if len(sdists) != 1 or len(wheels) != 1:
        raise ReleaseCheckError(
            f"expected exactly one sdist and one wheel, got {[p.name for p in sdists]} "
            f"and {[p.name for p in wheels]}"
        )
    return sdists[0], wheels[0]


def _twine_check(builder_python: Path, artifacts: list[Path]) -> tuple[bool, str]:
    """`twine check`, where a non-zero exit and a missing PASSED are one failure."""
    proc = _run([str(builder_python), "-m", "twine", "check", *[str(a) for a in artifacts]])
    output = f"{proc.stdout}{proc.stderr}".strip()
    passed = output.count("PASSED")
    return proc.returncode == 0 and passed == len(artifacts), output


# ---------------------------------------------------------------------------
# Reading what was actually built
# ---------------------------------------------------------------------------

def _artifact_files(artifact: Path) -> list[str]:
    """Member names, with the sdist's `<name>-<version>/` component stripped.

    Stripping it is what lets the sdist and the wheel be compared against one
    set of prefixes instead of two.
    """
    if artifact.name.endswith(".whl"):
        with zipfile.ZipFile(artifact) as zf:
            return sorted(n for n in zf.namelist() if not n.endswith("/"))
    with tarfile.open(artifact) as tf:
        names = [m.name for m in tf.getmembers() if m.isfile()]
    return sorted(n.split("/", 1)[1] for n in names if "/" in n)


def _extract(artifact: Path, dest: Path) -> Path:
    """Extract to a temp tree, so the rules below read what a DOWNLOADER gets.

    Reading the repository instead would answer a different question — and the
    question this file exists to ask is what is in the file strangers receive.
    """
    dest.mkdir(parents=True, exist_ok=True)
    if artifact.name.endswith(".whl"):
        with zipfile.ZipFile(artifact) as zf:
            zf.extractall(dest)
    else:
        with tarfile.open(artifact) as tf:
            tf.extractall(dest)
    return dest


def _forbidden_members(names: list[str]) -> list[str]:
    return [n for n in names if any(n.startswith(p) for p in PRUNED_PREFIXES)]


# ---------------------------------------------------------------------------
# Installing the wheel somewhere that is not this repository
# ---------------------------------------------------------------------------

def _install_and_smoke(wheel: Path, venv_path: Path, run_dir: Path) -> list[str]:
    """Install THE WHEEL into an empty venv and run the console script.

    Never the source tree, never `-e`: an editable install is the checkout, and
    proving the checkout works is what `make verify` already does.

    `run_dir` is load-bearing and it is outside the repository on purpose. Run
    from the repo root, `boty check` would find `config/products.yaml` sitting
    right there and the packaging bug at the top of this file would hide again —
    which is exactly how it survived three phases.
    """
    python = _ephemeral_venv(venv_path, ())
    proc = _run([str(python), "-m", "pip", "install", "--quiet", str(wheel)])
    if proc.returncode != 0:
        raise ReleaseCheckError(f"could not install {wheel.name} into a clean venv:\n{proc.stderr}")

    script = venv_path / "bin" / CONSOLE_SCRIPT
    if not script.is_file():
        return [f"the wheel installed no `{CONSOLE_SCRIPT}` console script at {script}"]

    failures: list[str] = []
    for args, expected in SMOKE_ARGS:
        # No PYTHONPATH: an inherited one could put this repository back on
        # sys.path and undo the whole point of installing a wheel.
        result = _run([str(script), *args], cwd=run_dir, env={"PATH": "/usr/bin:/bin", "HOME": str(run_dir)})
        output = f"{result.stdout}{result.stderr}"
        if result.returncode != expected:
            failures.append(
                f"`{CONSOLE_SCRIPT} {' '.join(args)}` exited {result.returncode}, expected "
                f"{expected}\n      {output.strip().splitlines()[-1] if output.strip() else '(no output)'}"
            )
        if "Traceback" in output:
            failures.append(f"`{CONSOLE_SCRIPT} {' '.join(args)}` printed a traceback")
    return failures


def _installed_version(venv_python: Path) -> str | None:
    proc = _run([str(venv_python), "-m", "pip", "show", "bot-y"])
    for line in proc.stdout.splitlines():
        if line.lower().startswith("version:"):
            return line.split(":", 1)[1].strip()
    return None


def _installed_packages(venv_python: Path) -> list[str]:
    proc = _run([str(venv_python), "-m", "pip", "list", "--format=freeze"])
    return [line.split("==")[0].strip().lower() for line in proc.stdout.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def _report(results: list[tuple[str, bool, str]], name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {detail}")


def check_release(root: Path, work: Path) -> list[tuple[str, bool, str]]:
    """Every check, in order, each printing one line as it is decided."""
    results: list[tuple[str, bool, str]] = []

    pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
    changelog_path = root / "CHANGELOG.md"
    declared = _declared_version(pyproject_text)
    if declared is None:
        raise ReleaseCheckError("no `version = \"...\"` in the [project] table of pyproject.toml")
    changelog_version = _changelog_version(changelog_path.read_text(encoding="utf-8"))

    source = work / "src"
    source.mkdir()
    tracked = _tracked_tree(root, source)
    print(f"  ..    built from {tracked} tracked file(s), copied to a clean tree")

    builder = _ephemeral_venv(work / "build-venv", BUILD_REQUIREMENTS)
    sdist, wheel = _build(source, builder, work / "dist")
    print(f"  ..    {sdist.name}  {sdist.stat().st_size:,} bytes")
    print(f"  ..    {wheel.name}  {wheel.stat().st_size:,} bytes")

    install_venv = work / "install-venv"
    run_dir = work / "run"
    run_dir.mkdir()
    smoke_failures = _install_and_smoke(wheel, install_venv, run_dir)
    install_python = install_venv / "bin" / "python"
    shown = _installed_version(install_python)
    metadata = _wheel_metadata(wheel)
    metadata_version = _metadata_field(metadata, "Version")
    wheel_name_version = _wheel_filename_version(wheel)

    # 1. Five statements of one number.
    statements = {
        "pyproject.toml": declared,
        "CHANGELOG.md": changelog_version,
        "wheel filename": wheel_name_version,
        "wheel METADATA": metadata_version,
        "pip show": shown,
    }
    disagree = {k: v for k, v in statements.items() if v != declared}
    _report(
        results, "one version, stated five times",
        not disagree,
        ", ".join(f"{k}={v}" for k, v in statements.items())
        + ("" if not disagree else f"  <- DISAGREE: {disagree}"),
    )

    # 2. Both artifacts exist. (`_build` raises otherwise; this records it.)
    _report(results, "both artifacts built", True, f"1 sdist, 1 wheel in {work / 'dist'}")

    # 3. twine check.
    twine_ok, twine_output = _twine_check(builder, [sdist, wheel])
    _report(results, "twine check", twine_ok, twine_output.replace("\n", " | ") or "(no output)")

    # 4. Nothing pruned leaked into either artifact.
    sdist_files = _artifact_files(sdist)
    wheel_files = _artifact_files(wheel)
    leaked = _forbidden_members(sdist_files) + _forbidden_members(wheel_files)
    _report(
        results, "no pruned directory in either artifact",
        not leaked,
        f"{len(sdist_files)} sdist member(s), {len(wheel_files)} wheel member(s)"
        + ("" if not leaked else f"  <- LEAKED: {leaked[:10]}"),
    )

    # 5. What each artifact must carry.
    missing: list[str] = []
    if not any(n.endswith("LICENSE") for n in sdist_files):
        missing.append("sdist:LICENSE")
    if not any(n.endswith("LICENSE") for n in wheel_files):
        missing.append("wheel:LICENSE")
    missing += [f"sdist:{n}" for n in SDIST_REQUIRED if n not in sdist_files]
    _report(
        results, "the files a source release has to carry",
        not missing,
        "LICENSE in both; " + ", ".join(SDIST_REQUIRED) + " in the sdist"
        + ("" if not missing else f"  <- MISSING: {missing}"),
    )

    # 6. The licence actually shipped, which the BUILD does not check.
    licence_member = [n for n in wheel_files if n.endswith(".dist-info/licenses/LICENSE")]
    expression = _metadata_field(metadata, "License-Expression")
    licence_ok = bool(licence_member) and expression is not None
    _report(
        results, "the licence reached the wheel",
        licence_ok,
        f"License-Expression: {expression}; {licence_member[0] if licence_member else 'NO dist-info/licenses/LICENSE'}",
    )

    # 7. The identity rule, over what a downloader receives.
    #
    # The fourth caller of `scan` — after the pre-commit hook, `make verify` and
    # the test suite. It is NOT redundant with `make verify`'s `identity` stage:
    # that stage scans TRACKED files, and an artifact additionally contains
    # generated metadata — `PKG-INFO`, `METADATA`, `RECORD` — that no
    # tracked-file scan has ever read. This repository has already leaked a real
    # value to `origin/main` once, through a file nobody was scanning.
    leaks: list[str] = []
    for artifact in (sdist, wheel):
        extracted = _extract(artifact, work / f"extracted-{artifact.suffix.lstrip('.')}")
        files = [p for p in extracted.rglob("*") if p.is_file()]
        leaks += scan(files, extracted)
    _report(
        results, "no host identity in the built artifacts",
        not leaks,
        "sdist + wheel extracted and scanned by the same rule `make verify` runs"
        + ("" if not leaks else f"  <- {leaks[:5]}"),
    )

    # 8. The wheel runs somewhere that is not this repository.
    _report(
        results, "the installed console script runs from outside the repo",
        not smoke_failures,
        "; ".join(f"`{CONSOLE_SCRIPT} {' '.join(a)}` -> {e}" for a, e in SMOKE_ARGS)
        + ("" if not smoke_failures else "\n        " + "\n        ".join(smoke_failures)),
    )

    # 9. A default install pulls no browser stack.
    installed = _installed_packages(install_python)
    present = [p for p in FORBIDDEN_IN_INSTALL if p in installed]
    _report(
        results, "no forbidden package in a default install",
        not present,
        f"{len(installed)} package(s): {', '.join(sorted(installed))}"
        + ("" if not present else f"  <- PRESENT: {present}"),
    )

    # 10. The metadata URL that 04-02 refused to write until it was true.
    url = _changelog_url(pyproject_text)
    rel = url.rsplit("/blob/main/", 1)[-1] if url else ""
    url_ok = bool(url) and (root / rel).is_file()
    _report(
        results, "the Changelog URL resolves to a file in this repo",
        url_ok,
        f"{url} -> {rel} {'exists' if url_ok else 'DOES NOT EXIST'}",
    )

    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the distribution and prove it works.")
    ap.add_argument(
        "--keep", action="store_true",
        help="leave the temporary build/install trees in place for inspection",
    )
    args = ap.parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    work = Path(tempfile.mkdtemp(prefix="boty-release-"))
    print(f"release check: building {root.name} in {work}")

    try:
        results = check_release(root, work)
    except ReleaseCheckError as exc:
        print("release check: HARNESS ERROR", file=sys.stderr)
        print(f"{exc}", file=sys.stderr)
        return 1
    finally:
        if args.keep:
            print(f"  ..    kept {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)

    failed = [name for name, ok, _ in results if not ok]
    if failed:
        print(f"release check: FAILED — {len(failed)} of {len(results)} checks failed: {', '.join(failed)}")
        return 1
    print(f"release check: PASSED — {len(results)}/{len(results)} checks, sdist and wheel proven")
    return 0


if __name__ == "__main__":
    sys.exit(main())
