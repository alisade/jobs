# aiarch/w4-c1 -- on-behalf-of token exchange (RFC 8693) for Lighthouse tools. Shared venv aiarch/.venv.
SHELL := /bin/bash
AIARCH := $(abspath ../..)
PY := ${AIARCH}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${AIARCH}/_env/ensure-venv.sh"
	@echo "w4-c1 ready. Edit obo/exchange.py, then: make test"

test:
	@${PY} -m pytest -q tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-c1 clean (shared venv kept)"
