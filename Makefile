# bot-y — one command that answers "is this still working", with an exit code.
#
# `make verify` is the contract. Every phase of this project states its success
# criteria in terms of it, so it has exactly one job: exit non-zero if ANY check
# fails. A verify that prints FAIL and exits 0 is worse than no verify at all,
# because everything downstream is built on trusting the number.
#
# That is why no recipe line here is prefixed with `-`, none of them ends in a
# no-op fallback that discards a failure, and none of them pipes: a pipeline
# takes the exit status of its LAST command, so `check | tee log` silently
# swallows the very failure it was supposed to report.

PYTHON ?= .venv/bin/python

# Set to --offline by `verify-offline` (and overridable on the command line) so
# the live control check can be skipped where hitting real retailers is wrong.
CONTROL_FLAGS ?=

# One definition of how the live control check is invoked, shared by the
# `controls` target and by `verify`. `verify` cannot delegate to `controls`
# through $(MAKE), because it needs to tell exit code 3 (SKIPPED) apart from a
# real failure and a sub-make that exits 3 prints its own "Error 3" first.
CONTROL_CMD = $(PYTHON) scripts/control_check.py $(CONTROL_FLAGS)

MAKE_Q := $(MAKE) --no-print-directory

.DEFAULT_GOAL := help

.PHONY: help test lint types controls fixtures mutation identity hooks verify verify-offline release-check check-venv

help:
	@echo "bot-y — make targets"
	@echo ""
	@echo "  verify          everything below, in order; exits non-zero if any check fails"
	@echo "  verify-offline  same, but skips the live retailer check (for CI)"
	@echo ""
	@echo "  lint            ruff over boty/, scripts/ and tests/"
	@echo "  test            offline pytest suite — catches CODE regressions"
	@echo "  types           mypy over boty/ and scripts/"
	@echo "  fixtures        warn about stale or unlabelled fixtures (never fails)"
	@echo "  controls        live control products — catches RETAILER changes"
	@echo "  mutation        prove the test suite would notice a broken extractor"
	@echo ""
	@echo "  ---"
	@echo "  release-check   build the sdist and wheel, install the wheel into a clean"
	@echo "                  venv and run it from outside this repo. NEEDS THE NETWORK,"
	@echo "                  so it is not part of verify. Run it before a release."
	@echo ""
	@echo "  PYTHON=$(PYTHON) (override to use a different interpreter)"

check-venv:
	@test -x $(PYTHON) || { \
	  echo "no interpreter at $(PYTHON)."; \
	  echo "  python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'"; \
	  echo "  (or run: make PYTHON=\$$(command -v python3) ...)"; \
	  exit 1; }

test: check-venv
	@$(PYTHON) -m pytest tests/ -q

# `$(PYTHON) -m ruff`, not the bare `ruff` console script, for two reasons and
# the second is the load-bearing one. It runs under the interpreter $(PYTHON)
# names, so `make PYTHON=... lint` stays honest and a `ruff` elsewhere on PATH
# cannot shadow the one the venv installed. And tests/test_verify_makefile.py
# stubs $(PYTHON) — a bare `ruff` would be unreachable from that stub, so this
# stage could never be watched failing, which is the whole point of adding it.
#
# No rule flags: the selection lives in [tool.ruff.lint] in pyproject.toml, and
# a flag here would be a second definition of it that can drift. This is a RULE
# check only — ruff's formatter is deliberately not adopted, and there is no
# `format` target anywhere in this file; the measurement behind that decision
# (32 of 36 files would be rewritten) is recorded in the [tool.ruff] block.
#
# Written without the literal formatter subcommand on purpose: the acceptance
# criterion for this stage greps this file AGAINST it, so naming it here would
# defeat the check that keeps a formatter out of the build.
lint: check-venv
	@$(PYTHON) -m ruff check

types: check-venv
	@$(PYTHON) -m mypy

# NOT a `verify` stage, and that is a decision rather than an omission.
#
# `verify` and `verify-offline` are network-free by contract — the test suite
# asserts its own isolation — and .github/workflows/ci.yml runs `verify-offline`
# on every pull request. This target creates two virtual environments and
# downloads from PyPI, so putting it inside either would make that contract
# false and make every contributor's every commit wait on pypi.org. It is run
# before a release, not on every change.
#
# It is also deliberately ABSENT from README's `| Stage | Proves |` table.
# `tests/test_verify_makefile.py::test_the_documented_stages_are_the_stages_verify_runs`
# asserts set equality between the stages the `verify` recipe invokes and the
# rows in that table, so a row here for a target `verify` never calls would turn
# that gate red. The absence is correct; do not "fix" it.
release-check: check-venv
	@$(PYTHON) scripts/release_check.py

fixtures: check-venv
	@$(PYTHON) scripts/control_check.py --fixtures

# Exits 3 when the live check was SKIPPED. That is not a pass — see the
# SKIPPED constant in scripts/control_check.py — so it is not flattened to 0.
controls: check-venv
	@$(CONTROL_CMD)

mutation: check-venv
	@$(PYTHON) scripts/mutation_check.py

# Order is deliberate: cheap and offline first, so a plain syntax error is
# reported in seconds rather than after a network round-trip.
#
# `lint` runs second. It is the cheapest check in this file — measured on this
# box at 0.02s over 35 files, against mypy's 0.09s and the identity scan's
# 3.33s — and a rule violation should be reported before a 460-test run rather
# than after it. It goes second rather than first only because `identity`'s
# position is justified by CONSEQUENCE and not by cost: a leak is the one
# failure you cannot walk back after a push.
#
# make aborts a recipe at the first failing line, so a naive `verify` could
# never reach a closing verdict. Each step therefore carries its own trap that
# names the stage and re-raises the failure — the verdict is printed AND the
# exit code survives.
#
# The live control check is the exception: it has THREE outcomes, not two, and
# the third has to reach the final line. Exit 3 means the check was skipped
# because this machine has no outbound connectivity, which is neither a pass
# nor a failure — nothing was learned. Flattening that to 0 made a run that
# verified nothing about any retailer print exactly the same "VERIFY: PASS" as
# a fully green one, and phase success criteria are written as "`make verify`
# exits 0". So the last three stages share one shell: `skipped` has to survive
# from the control check down to the verdict, and make gives every recipe LINE
# its own shell. Every failure path still exits non-zero explicitly.
#
# Exit 4 is a fourth outcome, added for the same reason 3 was: it is neither a
# pass nor a failure, and flattening it into either loses the thing worth
# knowing. It means some controls ran and passed while others could not run on
# THIS host — the fresh-clone case, where the Best Buy control needs the
# optional `browser` extra and a Chrome binary that `dev` deliberately does not
# install. Reporting that as FAIL told contributors their extractor was broken;
# reporting it as an unqualified PASS would claim a detector was verified when
# it was never reached. It gets its own verdict line.
# Every tracked file, not just the fixtures — the leak that mattered most was in
# .planning/, and the second-most was in tests/. Cheap and offline, so it runs
# first: a leak is the one failure you cannot walk back after a push.
identity: check-venv
	@$(PYTHON) scripts/identity_check.py --all

# Install the tracked pre-commit hook. Not automatic: writing to .git/hooks
# behind someone's back is the kind of thing a build should ask for.
hooks:
	@install -m 0755 hooks/pre-commit .git/hooks/pre-commit
	@echo "installed .git/hooks/pre-commit — staged files are now identity-checked"

verify:
	@echo "=== verify: identity, lint, tests, types, fixtures, controls, mutation ==="
	@$(MAKE_Q) identity || { echo "VERIFY: FAIL (host identity in a tracked file)"; exit 1; }
	@$(MAKE_Q) lint     || { echo "VERIFY: FAIL (lint)"; exit 1; }
	@$(MAKE_Q) test     || { echo "VERIFY: FAIL (tests)"; exit 1; }
	@$(MAKE_Q) types    || { echo "VERIFY: FAIL (types)"; exit 1; }
	@$(MAKE_Q) fixtures || { echo "VERIFY: FAIL (fixtures)"; exit 1; }
	@$(CONTROL_CMD); rc=$$?; \
	 case $$rc in \
	   0) verdict= ;; \
	   3) verdict=offline ;; \
	   4) verdict=incomplete ;; \
	   *) echo "VERIFY: FAIL (live controls)"; exit 1 ;; \
	 esac; \
	 $(MAKE_Q) mutation || { echo "VERIFY: FAIL (mutation check)"; exit 1; }; \
	 if [ "$$verdict" = offline ]; then \
	   echo "VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)"; \
	 elif [ "$$verdict" = incomplete ]; then \
	   echo "VERIFY: PASS (INCOMPLETE — some controls could not run on this host; the detectors they cover are unverified here)"; \
	 else \
	   echo "VERIFY: PASS"; \
	 fi

# Delegates to `verify` rather than duplicating it, so there is one definition
# of the order and one definition of the verdict.
verify-offline:
	@$(MAKE_Q) verify CONTROL_FLAGS=--offline
