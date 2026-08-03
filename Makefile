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

.PHONY: help test types controls fixtures mutation verify verify-offline check-venv

help:
	@echo "bot-y — make targets"
	@echo ""
	@echo "  verify          everything below, in order; exits non-zero if any check fails"
	@echo "  verify-offline  same, but skips the live retailer check (for CI)"
	@echo ""
	@echo "  test            offline pytest suite — catches CODE regressions"
	@echo "  types           mypy over boty/ and scripts/"
	@echo "  fixtures        warn about stale or unlabelled fixtures (never fails)"
	@echo "  controls        live control products — catches RETAILER changes"
	@echo "  mutation        prove the test suite would notice a broken extractor"
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

types: check-venv
	@$(PYTHON) -m mypy

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
verify:
	@echo "=== verify: tests, types, fixtures, controls, mutation ==="
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
