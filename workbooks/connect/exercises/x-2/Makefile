# connect/x-2 -- guardrail blocks legitimate password resets. Uses the shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle evals test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@$(MAKE) -s bundle
	@echo "x-2 ready. Start with incident/PAGE.txt"

bundle:      ## (re)generate the incident bundle into incident/
	@node scripts/make-bundle.js

evals:       ## replay evals/cases.jsonl through the local guardrail stand-in (CONFIG=..., CASES=...)
	@node scripts/run-ts.js src/run-evals.ts

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage incident
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "x-2 clean (shared toolchain kept in connect/_env)"
