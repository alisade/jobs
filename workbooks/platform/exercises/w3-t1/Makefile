# platform/w3-t1 -- import batch 07 plans to replace the VPC. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup plan test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w3-t1 ready. Start with evidence/PAGE.txt, then: make plan"

plan:        ## plan migration/ against the live inventory (local simulator)
	@${PY} tools/tfplan_sim.py || true

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-t1 clean (shared venv kept)"
