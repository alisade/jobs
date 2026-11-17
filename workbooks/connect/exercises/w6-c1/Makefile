# connect/w6-c1 -- conversational analytics (Contact Lens) QA processor. Shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w6-c1 ready. Edit src/*.ts (not types.ts), then: make test"

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w6-c1 clean (shared toolchain kept in connect/_env)"
