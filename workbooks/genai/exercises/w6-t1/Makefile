# genai/w6-t1 -- holiday peak stale-stock incident. Shared venv genai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup demo test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w6-t1 ready. Start with evidence/PAGE.md, then: make demo"

demo:        ## replay the store associates' day through the assistant and its cache
	@${PY} scripts/demo.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-t1 clean (shared venv kept)"
