# connect/w7-c3 -- Firehose transform for contact records + KPI SQL. Shared venv connect/.venv.
SHELL := /bin/bash
CONNECT := $(abspath ../..)
PY := ${CONNECT}/.venv/bin/python

.PHONY: setup test run clean

setup:
	@bash "${CONNECT}/_env/ensure-venv.sh"
	@echo "w7-c3 ready. Edit pipeline/transform.py and sql/kpis.sql, then: make test (make run for a local end-to-end)"

test:
	@${PY} -m pytest -q tests

run:         ## sample CTRs -> Lambda -> out/<partition>/ -> DuckDB views printed
	@${PY} scripts/run_local.py

clean:
	@rm -rf out .duck-rows.jsonl .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w7-c3 clean (shared venv kept)"
