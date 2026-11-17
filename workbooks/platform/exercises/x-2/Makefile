# platform/x-2 -- chart 3.0 reached every cluster at once. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup sim test clean

setup:       ## shared venv; the evidence bundle is static in evidence/
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "x-2 ready. Start with evidence/PAGE.txt, then: make sim"

sim:         ## render the ApplicationSets: make sim [INDEX=charts/index.yaml] [ARGS=--json]
	@${PY} tools/appset_sim.py $(if $(INDEX),--index $(INDEX),) $(ARGS)

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "x-2 clean (shared venv kept)"
