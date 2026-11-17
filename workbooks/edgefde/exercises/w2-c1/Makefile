# edgefde/w2-c1 -- spectral features and bearing-fault detection. Uses the shared venv edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test report clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w2-c1 ready. Implement vib/features.py, then: make test, make report"

report:      ## healthy vs outer vs inner race on 10 synthetic captures each
	@${PY} scripts/report.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-c1 clean (shared venv kept)"
