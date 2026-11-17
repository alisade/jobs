# audit/w2-t1 -- the CM-03 population does not reconcile. Uses the shared venv audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup export test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@mkdir -p incident
	@cp -f notes/*.txt incident/ 2>/dev/null || true
	@${PY} export.py >/dev/null 2>&1 || true
	@echo "w2-t1 ready: incident/ has the export log, the reconciliation, the auditor's note and the chat thread; make export re-runs it"

export:
	@${PY} export.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache incident
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-t1 clean (shared venv kept)"
