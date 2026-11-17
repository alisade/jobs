# platform/ai-c1 -- on-call page triage assistant. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup evals test live clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "ai-c1 ready. Try: make evals"

evals:       ## replay the 10 recorded scenarios and apply the CI gate
	@${PY} -m triage.evals || true

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

live:        ## optional, not graded: a real model call is not implemented in this exercise
	@echo "make live is a stub: wire triage/llm.py to the Messages API yourself if you want a live run (needs your own API key)."

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-c1 clean (shared venv kept)"
