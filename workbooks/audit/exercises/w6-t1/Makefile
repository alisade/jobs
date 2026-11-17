# audit/w6-t1 -- "97% accuracy, 4 missed exceptions": investigate the eval dashboard. Shared venv audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup test dashboard refresh-golden clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@${PY} scripts/make_incident.py
	@echo "w6-t1 ready: read incident/, run make dashboard"

dashboard:       ## score the Q3 production run against the golden set
	@${PY} -m harness.cli --golden labels/golden.jsonl --runs runs/2026Q3/production.jsonl

refresh-golden:  ## migrate the golden set to the current schema
	@${PY} scripts/refresh_golden.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-t1 clean (shared venv kept)"
