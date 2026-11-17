# connect/w8-c1 -- flow promotion tool. Uses the shared toolchain in connect/_env (node_modules symlinked in).
SHELL := /bin/bash
CONNECT := $(abspath ../..)
ENV ?= prod

.PHONY: setup test promote clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w8-c1 ready. Edit src/promote.ts, then: make test && make promote ENV=prod"

promote:     ## dist/$(ENV)/ artifacts + report.json; exit 1 on problems
	@node scripts/promote.js "$(ENV)"

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage dist
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w8-c1 clean (shared toolchain kept in connect/_env)"
