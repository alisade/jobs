# healthai/w4-c1 -- LangGraph PA intake graph with human review. Uses the shared venv healthai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w4-c1 ready: edit pa_graph/graph.py, then make test"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache checkpoints.db
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-c1 clean (shared venv kept)"
