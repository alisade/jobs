# connect/w4-c1 -- legacy IVR to Connect translator. Uses the shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w4-c1 ready. Implement src/translate/{avaya,cisco,five9}.ts, then: make test"

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w4-c1 clean (shared toolchain kept in connect/_env)"
