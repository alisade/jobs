# healthai/w4-t1 -- reviewer decisions land on the wrong case. Uses the shared venv healthai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup repro test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/repro.py incident/audit-export.jsonl > /dev/null
	@echo "w4-t1 ready: read incident/ticket.md; make repro replays the burst"

repro:
	@${PY} scripts/repro.py

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache incident/audit-export.jsonl
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-t1 clean (shared venv kept)"
