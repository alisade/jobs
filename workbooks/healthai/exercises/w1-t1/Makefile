# healthai/w1-t1 -- "the CMS clock report says zero breaches". Uses the shared venv healthai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test report clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/generate.py data
	@mkdir -p incident
	@${PY} -m clockreport.report data/cases.csv out/pa_metrics.json 2> incident/report_run.log || true
	@cp -f data/audit_sample.csv incident/audit_sample.csv
	@echo "w1-t1 ready: read incident/ticket.md, then make report / make test"

report:      ## re-run the metrics report into out/pa_metrics.json
	@${PY} -m clockreport.report data/cases.csv out/pa_metrics.json

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf data out .pytest_cache incident/report_run.log incident/audit_sample.csv
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-t1 clean (shared venv kept)"
