# aiarch/w5-c1 -- DynamoDB single table for agent platform state (moto, offline). Shared venv aiarch/.venv.
SHELL := /bin/bash
AIARCH := $(abspath ../..)
PY := ${AIARCH}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${AIARCH}/_env/ensure-venv.sh"
	@echo "w5-c1 ready. Edit lighthouse_state/store.py, then: make test"

test:
	@${PY} -m pytest -q tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-c1 clean (shared venv kept)"
