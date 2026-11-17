# audit/x-1 -- Azure Function to Gemini via Workload Identity Federation: impersonation denied. Uses audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup sim test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@${PY} -m wifsim.scenario incident
	@echo "x-1 ready: read incident/ and config/; replay with make sim"

sim:         ## run the call path against config/ with the Function's token
	@${PY} -m wifsim.sim --claims wifsim/sample_claims.json --config config || true

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "x-1 clean (shared venv kept)"
