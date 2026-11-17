# audit/w4-t1 -- duplicate GRC issues after a retry. Uses the shared venv audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup replay test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@${PY} -m orchestrator.scenario incident
	@echo "w4-t1 ready: read incident/, then the code in orchestrator/"

replay:      ## re-run the 02:00 publish run against your current code (rewrites incident/)
	@${PY} -m orchestrator.scenario incident

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-t1 clean (shared venv kept)"
