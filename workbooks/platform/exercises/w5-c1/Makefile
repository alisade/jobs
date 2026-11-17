# platform/w5-c1 -- admission gate for Helm-rendered manifests. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python
MODE ?= dry-run

.PHONY: setup test run clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w5-c1 ready. Try: make run   (or make run MODE=enforce)"

run:         ## gate the shipped render: make run [MODE=dry-run|enforce]
	@${PY} gate.py --mode ${MODE} --policy config/policy.yaml --attestations config/attestations.json rendered; echo "exit $$?"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-c1 clean (shared venv kept)"
