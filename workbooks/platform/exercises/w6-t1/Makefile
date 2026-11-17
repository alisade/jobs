# platform/w6-t1 -- the import agent ran terraform apply. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup replay test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w6-t1 ready. Start with evidence/PAGE.txt, then: make replay"

replay:      ## replay the night's agent commands through this checkout's guard
	@${PY} tools/replay.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-t1 clean (shared venv kept)"
