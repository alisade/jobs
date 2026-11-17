# edgefde/w2-t1 -- phantom fault peak on the new pumps. Uses the shared venv edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup run test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/run.py incident >/dev/null
	@echo "w2-t1 ready: incident/ holds alerts.log, firmware-changelog.txt, gateway.yaml. Re-run the board: make run"

run:         ## the alert board over today's captures, through your current pre-processing
	@${PY} scripts/run.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-t1 clean (shared venv kept)"
