# backend/ai-t1 -- The assistant showed another business unit's pipeline. Uses the shared venv backend/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup replay test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@if [ ! -f incident/TICKET.md ]; then ${PY} scripts/generate.py incident; fi
	@echo "ai-t1 ready. Start with incident/TICKET.md"

replay:      ## re-issue the recorded model turns of INC-7731 against your tool code
	@${PY} -m assistant_tools.replay transcripts/inc-7731.json

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-t1 clean (shared venv kept)"
