# audit/w1-t1 -- every change passes after the prompt v2 rollout. Uses the shared venv audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup run test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@echo "w1-t1 ready: make run replays the Q3 CM-03 run; the evidence/ folder has the release notes, diff and logs"

run:
	@${PY} run.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-t1 clean (shared venv kept)"
