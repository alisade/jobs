# fde/x-2 -- PII in decision logs. Uses the shared venv at fde/.venv.
SHELL := /bin/bash
FDE := $(abspath ../..)
PY := ${FDE}/.venv/bin/python

.PHONY: setup scan test clean

setup:
	@bash "${FDE}/_env/ensure-venv.sh"
	@${PY} scripts/generate_bundle.py
	@echo "Bundle: run/decisions.log, run/dlp-report.txt, plus incident/. Re-scan after a fix: make scan"

scan:
	@${PY} scripts/generate_bundle.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "x-2 clean"
