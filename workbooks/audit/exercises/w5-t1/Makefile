# audit/w5-t1 -- an exception closed overnight "per system note". Shared venv audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup run test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@${PY} run.py >/dev/null
	@${PY} scripts/make_incident.py
	@echo "w5-t1 ready: read incident/, replay the overnight run with make run"

run:         ## replay the overnight run from a fresh GRC state (recorded model responses)
	@${PY} run.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident state .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-t1 clean (shared venv kept)"
