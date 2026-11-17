# aiarch/w2-c1 -- Strands orchestrator + two specialists as tools, offline with a scripted model.
SHELL := /bin/bash
AIARCH := $(abspath ../..)
PY := ${AIARCH}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${AIARCH}/_env/ensure-venv.sh"
	@echo "w2-c1 ready. Edit helpdesk/tools.py, hooks.py, agents.py, then: make test"

test:
	@${PY} -m pytest -q tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-c1 clean (shared venv kept)"
