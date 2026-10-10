# connect/w5-c1 -- Lex V2 code hook Lambda. Uses the shared toolchain in connect/_env (node_modules symlinked in).
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w5-c1 ready. Edit src/handler.ts, then: make test"

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w5-c1 clean (shared toolchain kept in connect/_env)"
