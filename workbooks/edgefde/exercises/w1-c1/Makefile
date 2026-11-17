# edgefde/w1-c1 -- idempotent vibration-feature ingest with backfill. Uses the shared venv edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test demo backfill clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/gen.py archive
	@echo "w1-c1 ready. Try: make demo, make backfill DAY=2026-10-14"

demo:        ## produce an hour of traffic to the fake broker and run your consumer
	@${PY} scripts/demo.py run/demo.db

backfill:    ## make backfill DAY=2026-10-14
	@mkdir -p run
	@${PY} -m ingest.backfill --db run/features.db --archive archive --day $${DAY:-2026-10-14} --devices pump-01,pump-02,pump-03,pump-04

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf archive run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-c1 clean (shared venv kept)"
