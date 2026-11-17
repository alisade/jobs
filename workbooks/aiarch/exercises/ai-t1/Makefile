# aiarch/ai-t1 -- prompt cache stopped hitting after release 3.1.0. Shared venv aiarch/.venv.
SHELL := /bin/bash
AIARCH := $(abspath ../..)
PY := ${AIARCH}/.venv/bin/python

.PHONY: setup bundle test clean

setup: bundle
	@bash "${AIARCH}/_env/ensure-venv.sh"
	@echo "ai-t1 ready. Start with incident/PAGE.txt."

bundle:      ## (re)generate the incident evidence in incident/
	@python3 scripts/make_bundle.py incident

test:
	@${PY} -m pytest -q tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-t1 clean (shared venv kept)"
