# backend/w3-c1 -- Idempotency keys that survive concurrent retries. Uses the shared venv backend/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test run clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w3-c1 ready. Edit app/idempotency.py (and app/main.py if you need to), then: make test"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-c1 clean (shared venv kept)"
