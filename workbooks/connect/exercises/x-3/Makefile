# connect/x-3 -- Lex fallbacks after a slot type change. Uses the shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle evals test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@$(MAKE) -s bundle
	@echo "x-3 ready. Start with incident/PAGE.txt"

bundle:      ## (re)generate the incident bundle into incident/
	@node scripts/make-bundle.js

evals:       ## replay evals/utterances.csv through the offline NLU (BOT=... CASES=...)
	@node scripts/run-ts.js tools/run-evals.ts

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage incident
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "x-3 clean (shared toolchain kept in connect/_env)"
