# awsfde/w2-t1 -- "order tool unavailable" behind AgentCore Gateway. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test replay clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} -m replay.simulate --out run >/dev/null
	@echo "w2-t1 ready. Start with evidence/TICKET.txt, then run/gateway-2026-11-12.log and run/lambda-tw-order-tools-prod.log."

replay:      ## re-run the recorded traffic through this checkout (after a fix)
	@${PY} -m replay.simulate --out run

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-t1 clean (shared venv kept)"
