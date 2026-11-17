# aiarch/w4-t1 -- a contractor approved another team's access request through the gateway. Shared venv aiarch/.venv.
SHELL := /bin/bash
AIARCH := $(abspath ../..)
PY := ${AIARCH}/.venv/bin/python

.PHONY: setup bundle test replay clean

setup: bundle
	@bash "${AIARCH}/_env/ensure-venv.sh"
	@echo "w4-t1 ready. Start with incident/PAGE.txt."

bundle:      ## (re)generate the incident evidence in incident/
	@python3 scripts/make_bundle.py incident

replay:      ## replay the visible requests through the current policy set, then validate against the schema
	@${PY} -m authz.engine tests/requests_visible.jsonl

test:
	@${PY} -m pytest -q tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-t1 clean (shared venv kept)"
