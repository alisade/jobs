# backend/w6-c1 -- Lead assignment workflow with manager approval. Uses the shared venv backend/.venv
# and the Temporal time-skipping test server in backend/.temporal (downloaded once by setup).
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@bash "${TRACK}/_env/ensure-temporal.sh" >/dev/null
	@echo "w6-c1 ready. Edit keystone_workflows/workflow.py, then: make test"

test:
	@BACKEND_TEMPORAL_TEST_SERVER="$$(bash "${TRACK}/_env/ensure-temporal.sh")" ${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-c1 clean (shared venv and test server kept)"
