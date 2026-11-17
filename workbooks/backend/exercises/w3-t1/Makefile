# backend/w3-t1 -- The partner sync is missing contacts. Uses the shared venv backend/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup repro test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@if [ ! -f incident/TICKET.md ]; then ${PY} scripts/generate.py incident; fi
	@echo "w3-t1 ready. Start with incident/TICKET.md"

repro:       ## walk the API with your code over the same data the partner has: make repro [LIMIT=100]
	@${PY} scripts/walk.py $(if $(LIMIT),$(LIMIT),100)

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-t1 clean (shared venv kept)"
