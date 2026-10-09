# fde/w3-t1 -- checkout allowed during a risk-API brownout. Uses the shared venv fde/.venv.
SHELL := /bin/bash
FDE := $(abspath ../..)
PY := ${FDE}/.venv/bin/python

.PHONY: setup test replay clean

setup:
	@bash "${FDE}/_env/ensure-venv.sh"
	@${PY} scripts/make_bundle.py run/incident
	@echo "w3-t1 ready. Start with run/incident/PAGE.txt; deployed config is in deploy/."
	@echo "Reproduce locally: make replay"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

replay:
	@${PY} scripts/replay_brownout.py deploy/trust.env

clean:
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-t1 clean (incident bundle removed; make setup regenerates it)"
