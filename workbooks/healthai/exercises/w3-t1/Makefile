# healthai/w3-t1 -- PAs pended for "missing diagnosis" after release 2026.11.1. Uses the shared venv healthai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup replay test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/generate.py data
	@${PY} -m pipeline.run data/requests.json out 2> incident/engine-run.log || true
	@echo "w3-t1 ready: read incident/ticket.md; make replay re-runs the pipeline"

replay:      ## re-run the pipeline into out/routes.json and print the summary
	@${PY} -m pipeline.run data/requests.json out 2>&1 | grep 'route=' || true

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf data out .pytest_cache incident/engine-run.log
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-t1 clean (shared venv kept)"
