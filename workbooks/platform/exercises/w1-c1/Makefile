# platform/w1-c1 -- foundation guardrails over a Terraform plan. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python
PLAN ?= plans/foundation.plan.json

.PHONY: setup run test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w1-c1 ready. Try: make run   (or make run PLAN=<your plan.json>)"

run:         ## evaluate a plan: make run PLAN=plans/foundation.plan.json
	@${PY} guardrails.py ${PLAN} --policy policy.yaml || true

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-c1 clean (shared venv kept)"
