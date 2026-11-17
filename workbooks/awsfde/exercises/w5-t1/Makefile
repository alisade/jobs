# awsfde/w5-t1 -- Acme's product shows a supplier it never used. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test replay clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} replay.py run >/dev/null
	@echo "w5-t1 ready. Start with evidence/TICKET-5611.txt, then run/summary.txt, run/load-jobs.log, run/load/."

replay:      ## rebuild the graph from the load history with this checkout and re-run the questions
	@${PY} replay.py run

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-t1 clean (shared venv kept)"
