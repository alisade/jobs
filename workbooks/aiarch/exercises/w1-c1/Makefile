# aiarch/w1-c1 -- Lighthouse org guardrails (SCPs + RCP) checked by a local evaluator. Shared venv aiarch/.venv.
SHELL := /bin/bash
AIARCH := $(abspath ../..)
PY := ${AIARCH}/.venv/bin/python

.PHONY: setup test sim clean

setup:
	@bash "${AIARCH}/_env/ensure-venv.sh"
	@echo "w1-c1 ready. Edit policies/*.json, then: make test (make sim for a per-request table)"

test:
	@${PY} -m pytest -q tests

sim:         ## per-request decision table for the visible requests
	@${PY} -m scpsim tests/requests_visible.json || true

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-c1 clean (shared venv kept)"
