# awsfde/w3-t1 -- new tenant sees another tenant's documents. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test replay clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} replay.py run >/dev/null
	@echo "w3-t1 ready. Start with evidence/TICKET-5521.txt, then run/summary.txt and run/*.log."

replay:      ## re-run the customers' questions through this checkout (after a fix)
	@${PY} replay.py run

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-t1 clean (shared venv kept)"
