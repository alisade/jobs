# genai/ai-t1 -- prompt cache hit rate fell to zero. Shared venv genai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup demo test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "ai-t1 ready. Start with evidence/PAGE.md, then: make demo"

demo:        ## 10 worker processes with their own hash seeds against a simulated provider cache
	@${PY} scripts/demo.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-t1 clean (shared venv kept)"
