# platform/w3-c1 -- import blocks from a Cloud Asset Inventory export. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup run test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w3-c1 ready. Try: make run   (writes imports/)"

run:         ## generate imports/<owner>/imports.tf and imports/report.json
	@${PY} importgen.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache imports
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-c1 clean (shared venv kept)"
