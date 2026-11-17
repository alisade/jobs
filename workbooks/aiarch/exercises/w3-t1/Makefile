# aiarch/w3-t1 -- agent image never becomes healthy on AgentCore Runtime. Shared venv aiarch/.venv.
SHELL := /bin/bash
AIARCH := $(abspath ../..)
PY := ${AIARCH}/.venv/bin/python

.PHONY: setup bundle test gate clean

setup: bundle
	@bash "${AIARCH}/_env/ensure-venv.sh"
	@echo "w3-t1 ready. Start with incident/PAGE.txt."

bundle:      ## (re)generate the incident evidence in incident/
	@python3 scripts/make_bundle.py incident

gate:        ## run your arch gate against the fixtures
	@for f in index-arm64 index-multi index-amd64-with-attestation; do printf '%-32s ' "$${f}"; python3 scripts/check_image_arch.py tests/fixtures/$${f}.json; done
	@printf '%-32s ' "single + amd64 config"; python3 scripts/check_image_arch.py tests/fixtures/manifest-single.json tests/fixtures/config-amd64.json || true

test:
	@${PY} -m pytest -q tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-t1 clean (shared venv kept)"
