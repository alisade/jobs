# aiarch/w6-t1 -- prod CDK deploy blocked by an explicit deny in an SCP. Shared venv aiarch/.venv.
SHELL := /bin/bash
AIARCH := $(abspath ../..)
PY := ${AIARCH}/.venv/bin/python

.PHONY: setup bundle test sim clean

setup: bundle
	@bash "${AIARCH}/_env/ensure-venv.sh"
	@echo "w6-t1 ready. Start with incident/PAGE.txt."

bundle:      ## (re)generate the incident evidence in incident/
	@python3 scripts/make_bundle.py incident

sim:         ## decisions for the visible requests through the current policies
	@${PY} -m scpsim tests/requests_visible.json || true

test:
	@${PY} -m pytest -q tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-t1 clean (shared venv kept)"
