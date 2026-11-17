# awsfde/ai-t1 -- a summary email went to an outside address. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test replay clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} replay.py run >/dev/null
	@echo "ai-t1 ready. Start with evidence/TICKET-5633.txt, then run/summary.json and run/agent.log."

replay:      ## re-run the three Monday jobs through this checkout (after a fix); add GV=3 to try another guardrail version
	@${PY} replay.py run $(if ${GV},--guardrail-version ${GV},)

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-t1 clean (shared venv kept)"
