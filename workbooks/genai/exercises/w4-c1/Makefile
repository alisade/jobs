# genai/w4-c1 -- paired bias probes. Uses the shared venv genai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup report test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w4-c1 ready. Edit evals/bias_probe.py, then: make test and make report"

report:      ## run the probes: writes report.json and report.md; exit code is the CI gate
	@${PY} -m evals.bias_probe --out report.json --md report.md

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@/bin/rm -rf .pytest_cache report.json report.md
	@find . -name __pycache__ -type d -prune -exec /bin/rm -rf {} + 2>/dev/null || true
	@echo "w4-c1 clean (shared venv kept)"
