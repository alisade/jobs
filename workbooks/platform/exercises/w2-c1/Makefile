# platform/w2-c1 -- fleet upgrade planner. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python
FLEET ?= fleet.json

.PHONY: setup run test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w2-c1 ready. Try: make run"

run:         ## print the plan: make run [FLEET=fleet.json]
	@${PY} planner.py ${FLEET} || true

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-c1 clean (shared venv kept)"
