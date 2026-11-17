# connect/w8-t1 -- prod release failing after promotion. Uses the shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle release test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@$(MAKE) -s bundle
	@echo "w8-t1 ready. Start with incident/PAGE.txt"

bundle:      ## (re)generate the incident bundle into incident/
	@node scripts/make-bundle.js

release:     ## re-run the pipeline promote step + check-refs gate: export/dev -> release/prod
	@node scripts/run-ts.js pipeline/release.ts

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage incident
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w8-t1 clean (shared toolchain kept in connect/_env)"
