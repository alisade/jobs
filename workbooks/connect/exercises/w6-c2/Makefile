# connect/w6-c2 -- after-contact summarization pipeline. Shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w6-c2 ready. Edit src/redact.ts summarize.ts knowledge.ts handler.ts eval.ts, then: make test"

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w6-c2 clean (shared toolchain kept in connect/_env)"
