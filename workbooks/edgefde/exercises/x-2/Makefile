# edgefde/x-2 -- spikes at every chunk boundary in the streaming band-pass. Uses edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup run test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/run.py incident >/dev/null
	@echo "x-2 ready: incident/ holds gateway.log and first_chunk_samples.csv. Re-run: make run"

run:         ## 30 s of a healthy stream through your current filter
	@${PY} scripts/run.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "x-2 clean (shared venv kept)"
