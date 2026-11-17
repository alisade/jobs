# healthai/w6-t1 -- member names in exported spans despite redaction. Uses the shared venv healthai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup pipeline scan test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} -m app.pipeline out
	@${PY} scripts/scan.py out > incident/scan_report.txt
	@echo "w6-t1 ready: read incident/ticket.md and incident/scan_report.txt"

pipeline:    ## re-run 300 synthetic cases into out/
	@${PY} -m app.pipeline out

scan:        ## Security's leak scanner over out/
	@${PY} scripts/scan.py out

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf out .pytest_cache incident/scan_report.txt
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-t1 clean (shared venv kept)"
