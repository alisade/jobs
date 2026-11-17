# audit/w2-c1 -- CM-03 population, completeness/accuracy and sample selection. Uses audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python
SEED ?= 20261005

.PHONY: setup select test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@echo "w2-c1 ready: edit sampling/population.py; make select SEED=<n> writes selection_log.json"

select:
	@${PY} select.py ${SEED}

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache selection_log.json
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-c1 clean (shared venv kept)"
