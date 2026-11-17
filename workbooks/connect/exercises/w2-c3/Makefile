# connect/w2-c3 -- help desk KPI analytics in DuckDB SQL. Uses the shared venv connect/.venv.
SHELL := /bin/bash
CONNECT := $(abspath ../..)
PY := ${CONNECT}/.venv/bin/python
Q ?= queries/q1_weekly_volume_by_driver.sql

.PHONY: setup test run clean

setup:
	@bash "${CONNECT}/_env/ensure-venv.sh"
	@${PY} scripts/generate.py data
	@echo "w2-c3 ready. Explore with: make run Q=queries/q1_weekly_volume_by_driver.sql"

run:         ## make run Q=queries/<file>.sql [N=40]
	@${PY} scripts/run.py ${Q} ${N}

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf data .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-c3 clean (shared venv kept)"
