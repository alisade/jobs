# audit/ai-t1 -- Gemini cost up after the prompt refactor (implicit cache misses). Uses audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup replay test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@${PY} -m promptkit.scenario incident
	@echo "ai-t1 ready: read incident/, then promptkit/"

replay:      ## re-run the 2026-10-07 batch (two instances) against your current code
	@${PY} -m promptkit.scenario incident

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-t1 clean (shared venv kept)"
