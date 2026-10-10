# connect/w5-c3 -- tune the help desk AI agent config against a recorded eval set (lfg-sim-1).
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup eval test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w5-c3 ready. Edit tuning/agent.yaml, then: make eval (SHOW=all for every case) and make test"

eval:        ## metrics + the cases that went wrong
	@node scripts/ts-run.js scripts/eval.ts

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w5-c3 clean (shared toolchain kept in connect/_env)"
