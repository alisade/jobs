# edgefde/w1-t1 -- gaps in window counts after every consumer restart. Uses the shared venv edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup run test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/simulate.py incident >/dev/null
	@echo "w1-t1 ready: incident/ holds sink.log, broker.log, window_counts.csv, summary.txt. Re-run the day with: make run"

run:         ## replay 2026-10-20 with the supervisor restarts through the current sink code
	@${PY} scripts/simulate.py run

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-t1 clean (shared venv kept)"
