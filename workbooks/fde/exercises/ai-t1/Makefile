# fde/ai-t1 -- intermittent 400 from the Messages API. Uses the shared venv fde/.venv.
SHELL := /bin/bash
FDE := $(abspath ../..)
PY := ${FDE}/.venv/bin/python

.PHONY: setup replay test clean

setup:
	@bash "${FDE}/_env/ensure-venv.sh"
	@${PY} -m agentloop.replay --fixtures fixtures/recorded_turns.jsonl --out run
	@echo "ai-t1 ready. Start with incident/pager.txt, then run/ (logs, sentry, metrics, failing_request.json)."

replay:
	@${PY} -m agentloop.replay --fixtures fixtures/recorded_turns.jsonl --out run

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-t1 clean (shared venv kept)"
