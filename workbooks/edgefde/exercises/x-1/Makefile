# edgefde/x-1 -- CMMS work-order client: retries, Retry-After, idempotency keys. Uses edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup demo test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "x-1 ready. Implement cmms/client.py, then: make demo, make test"

demo:        ## one work order through 503, a lost response and a 429
	@${PY} scripts/demo.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "x-1 clean (shared venv kept)"
