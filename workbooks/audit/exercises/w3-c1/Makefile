# audit/w3-c1 -- ADK CM-03 tester with scoped tools and callbacks. Uses the shared venv audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@echo "w3-c1 ready: edit tester/guard.py and tester/agent.py; then make test"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-c1 clean (shared venv kept)"
