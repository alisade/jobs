# connect/w7-c1 -- ServiceNow incident Lambda for the help desk flow. Shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w7-c1 ready. Edit src/servicenow.ts and src/handler.ts, then: make test"

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w7-c1 clean (shared toolchain kept in connect/_env)"
