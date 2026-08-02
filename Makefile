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

controls: check-venv
	@$(PYTHON) scripts/control_check.py $(CONTROL_FLAGS)

mutation: check-venv
	@$(PYTHON) scripts/mutation_check.py

# Order is deliberate: cheap and offline first, so a plain syntax error is
# reported in seconds rather than after a network round-trip.
#
# make aborts a recipe at the first failing line, so a naive `verify` could
# never reach a closing verdict. Each step therefore carries its own trap that
# names the stage and re-raises the failure — the verdict is printed AND the
# exit code survives.
verify:
	@echo "=== verify: tests, types, fixtures, controls, mutation ==="
	@$(MAKE_Q) test     || { echo "VERIFY: FAIL (tests)"; exit 1; }
	@$(MAKE_Q) types    || { echo "VERIFY: FAIL (types)"; exit 1; }
	@$(MAKE_Q) fixtures || { echo "VERIFY: FAIL (fixtures)"; exit 1; }
	@$(MAKE_Q) controls || { echo "VERIFY: FAIL (live controls)"; exit 1; }
	@$(MAKE_Q) mutation || { echo "VERIFY: FAIL (mutation check)"; exit 1; }
	@echo "VERIFY: PASS"

# Delegates to `verify` rather than duplicating it, so there is one definition
# of the order and one definition of the verdict.
verify-offline:
	@$(MAKE_Q) verify CONTROL_FLAGS=--offline
