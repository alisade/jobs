# genai/w3-t1 -- model bill up 9x overnight. Uses the shared venv genai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup demo report test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w3-t1 ready. Start with evidence/PAGE.md, then: make report and make demo"

demo:        ## replay 40 production-shaped questions through gateway.py on a fake clock; prints cost
	@${PY} scripts/simulate.py

report:      ## group the provider usage export by request fingerprint (extend scripts/cost_report.py)
	@${PY} scripts/cost_report.py evidence/usage-export.csv

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@/bin/rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec /bin/rm -rf {} + 2>/dev/null || true
	@echo "w3-t1 clean (shared venv kept)"
