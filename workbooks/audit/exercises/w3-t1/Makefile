# audit/w3-t1 -- the nightly tester re-tests finished samples after a restart. Uses audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup run night1 night2 report test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@rm -rf run incident && mkdir -p incident
	@${PY} -m nightly.batch > incident/night1.out 2> incident/night1.log
	@${PY} -m nightly.batch > incident/night2.out 2> incident/night2.log
	@${PY} report.py > incident/queue-report.json
	@echo "w3-t1 ready: two nightly runs done (separate processes); see incident/ and run/"

run: night1 night2 report

night1 night2:
	@${PY} -m nightly.batch 2>>run/batch.log

report:
	@${PY} report.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf run incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-t1 clean (shared venv kept)"
