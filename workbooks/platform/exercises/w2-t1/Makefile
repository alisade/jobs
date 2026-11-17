# platform/w2-t1 -- prod-blue node pool upgrade stuck. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup drain test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w2-t1 ready. Start with evidence/PAGE.txt, then: make drain"

drain:       ## simulate the surge upgrade drain against k8s/ and cluster/state.json
	@${PY} tools/drain_sim.py || true

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-t1 clean (shared venv kept)"
