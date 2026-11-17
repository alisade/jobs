# audit/w1-c1 -- structured CM-03 evidence extraction with google-genai. Uses the shared venv audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@echo "w1-c1 ready: edit controlpilot/contract.py, extract.py, attributes.py; then make test"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-c1 clean (shared venv kept)"
