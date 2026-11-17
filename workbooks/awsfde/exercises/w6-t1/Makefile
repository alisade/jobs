# awsfde/w6-t1 -- embedded dashboard blank on refresh, and a cross-tenant view. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test replay clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} replay.py run >/dev/null
	@echo "w6-t1 ready. Start with evidence/TICKETS.txt, then run/summary.json and the logs in run/."

replay:      ## re-run the morning's page loads through this checkout (after a fix)
	@${PY} replay.py run

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-t1 clean (shared venv kept)"
