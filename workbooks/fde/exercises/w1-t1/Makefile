# fde/w1-t1 -- cache_read collapsed after a harmless change. Uses the shared venv fde/.venv.
SHELL := /bin/bash
FDE := $(abspath ../..)
PY := ${FDE}/.venv/bin/python

.PHONY: setup test replay clean

setup:
	@bash "${FDE}/_env/ensure-venv.sh"
	@${PY} -m replay.simulate --out run >/dev/null
	@echo "w1-t1 ready. Start with incident/PAGE.txt, then run/dashboard.txt and run/logs/."

replay:      ## re-run this checkout's code through the 16 workers (after a fix)
	@${PY} -m replay.simulate --out run --only current

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-t1 clean (shared venv kept)"
