# edgefde/w5-t1 -- alert counts tripled after the WAN outage. Uses the shared venv edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup run test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/outage.py incident >/dev/null
	@echo "w5-t1 ready: incident/ holds gateway.log, ntp.log, dashboard.csv, summary.txt, buffer.db. Re-run the day: make run"

run:         ## replay 2026-11-04 (outage + flaky link) through your current buffer
	@${PY} scripts/outage.py run

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-t1 clean (shared venv kept)"
