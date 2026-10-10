# connect/w6-t1 -- card numbers in the contact drivers report. Shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle report test clean

setup: bundle
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w6-t1 ready. Start with incident/PAGE.txt"

bundle:      ## (re)generate the incident bundle into incident/
	@node scripts/make_bundle.js

report:      ## run this checkout's report over the incident S3 mirror: make report FROM=2026-09-20 TO=2026-10-07
	@node scripts/run_report.js

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf incident coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w6-t1 clean (shared toolchain kept in connect/_env)"
