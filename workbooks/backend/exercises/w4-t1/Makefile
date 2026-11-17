# backend/w4-t1 -- Sales managers see someone else's account names in the pipeline view. Uses the shared
# node toolchain in backend/_env (jest, graphql-js, DataLoader).
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup repro test clean

setup:
	@bash "${TRACK}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w4-t1 ready: start with evidence/ticket-SUP-8812.md; make repro replays two tenants' requests"

repro:       ## replay an EMEA request, then an AMER request, and print what each saw
	@NODE_OPTIONS="--experimental-vm-modules --no-warnings" "${TRACK}/_env/node_modules/.bin/jest" --ci --forceExit --rootDir . -t "repro" tests/repro.test.ts 2>&1 | grep -E 'REPRO|Tests:'

test:
	@bash "${TRACK}/_env/jest.sh"

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w4-t1 clean (shared toolchain kept in backend/_env)"
