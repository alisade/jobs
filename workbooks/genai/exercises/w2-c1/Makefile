# genai/w2-c1 -- catalog service (FastAPI) and its generated TypeScript client.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python
BIN := ${TRACK}/_env/node_modules/.bin

.PHONY: setup contract test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@bash "${TRACK}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w2-c1 ready. make contract, make test"

contract:    ## export OpenAPI from the service and regenerate the TypeScript types
	@${PY} -m catalog.export_openapi > contracts/openapi.json
	@"${BIN}/openapi-typescript" contracts/openapi.json -o web/src/catalog-api.ts
	@"${BIN}/tsc" --noEmit -p web/tsconfig.json && echo "web/ type-checks"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests; py=$$?; "${BIN}/jest" --ci; js=$$?; exit $$(( py || js ))

clean:
	@rm -rf .pytest_cache coverage
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w2-c1 clean (shared toolchains kept)"
