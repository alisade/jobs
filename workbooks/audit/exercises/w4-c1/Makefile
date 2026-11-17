# audit/w4-c1 -- durable test run with a review gate and a hash-chained log. Uses the shared venv audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@echo "w4-c1 ready: edit durable/run.py and durable/log.py; then make test"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache *.db *.jsonl
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-c1 clean (shared venv kept)"
