# platform/ai-t1 -- the agent PR said no-op, the plan had a replace. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup repro test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "ai-t1 ready. Start with evidence/PAGE.txt, then: make repro"

repro:       ## rerun the agent pipeline on the incident plan
	@${PY} -m agent.pipeline evidence/plan-run-212.json

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-t1 clean (shared venv kept)"
