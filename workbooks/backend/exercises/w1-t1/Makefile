# backend/w1-t1 -- Contacts attached to the wrong accounts after the pilot import. Uses the shared venv backend/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup import test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@if [ ! -f incident/export/Account.csv ]; then ${PY} scripts/generate.py incident >/dev/null; fi
	@if [ ! -f incident/pilot/recon.txt ]; then ${PY} scripts/run_import.py incident/export incident/pilot >/dev/null; fi
	@echo "w1-t1 ready. Start with incident/TICKET.md, then incident/pilot/recon.txt and incident/pilot/import.log"

import:      ## re-run the importer + reconciliation with your code into incident/run/
	@${PY} scripts/run_import.py incident/export incident/run

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-t1 clean (shared venv kept)"
