# genai/w4-t1 -- promo code that does not exist. Uses the shared venv genai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup demo prompt test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w4-t1 ready. Start with evidence/PAGE.md, then: make demo"

demo:        ## replay the recorded production questions through the pipeline: what customers see
	@${PY} scripts/replay.py

prompt:      ## same, then print the full prompt the model saw for the first question
	@${PY} scripts/replay.py --prompt

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@/bin/rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec /bin/rm -rf {} + 2>/dev/null || true
	@echo "w4-t1 clean (shared venv kept)"
