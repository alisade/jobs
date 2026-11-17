# healthai/ai-c1 -- eval gate in CI for the PA assistant. Uses the shared venv healthai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "ai-c1 ready: edit evals/gates.py, then make test"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache out-summary.md
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-c1 clean (shared venv kept)"

gate:        ## make gate RUNS=fixtures/runs/good  -> exit code and summary like CI
	@${PY} -m evals.gates $${RUNS:-fixtures/runs/good} fixtures out-summary.md
