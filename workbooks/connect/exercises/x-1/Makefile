# connect/x-1 -- duplicate ServiceNow incidents. Uses the shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@$(MAKE) -s bundle
	@echo "x-1 ready. Start with incident/PAGE.txt"

bundle:      ## (re)generate the incident bundle into incident/
	@node scripts/make-bundle.js

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage incident
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "x-1 clean (shared toolchain kept in connect/_env)"
