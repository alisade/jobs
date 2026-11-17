# backend/w5-t1 -- Duplicate stage-change events after the relay restart. Uses the shared venv backend/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup repro test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@if [ ! -f incident/PAGER.md ]; then ${PY} scripts/generate.py incident; fi
	@echo "w5-t1 ready. Start with incident/PAGER.md"

repro:       ## replay the incident against your code
	@${PY} scripts/repro.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-t1 clean (shared venv kept)"
