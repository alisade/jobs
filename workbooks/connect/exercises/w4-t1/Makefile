# connect/w4-t1 -- wave 2 parallel run fails migration validation. Uses the shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle validate test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@$(MAKE) -s bundle
	@echo "w4-t1 ready. Start with incident/PAGE.txt, then incident/validation-report.txt."

bundle:      ## (re)generate incident/ from the current config
	@node scripts/make-bundle.js

validate:    ## run the migration validation suite: make validate DATES=2026-10-09,2026-11-02
	@node tools/validate.js --dates "$${DATES:-2026-10-09,2026-10-12,2026-10-13}"

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf incident coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w4-t1 clean (shared toolchain kept in connect/_env)"
