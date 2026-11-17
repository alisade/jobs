# edgefde/ai-t1 -- the assistant raised machine 4's alarm threshold. Stub LLM, no network. Uses edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup run test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/replay.py incident >/dev/null
	@echo "ai-t1 ready: incident/ holds transcript.json, audit.log, thresholds.json, changes.txt. Replay: make run"

run:         ## replay the recorded conversation through the current assistant code
	@${PY} scripts/replay.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-t1 clean (shared venv kept)"
