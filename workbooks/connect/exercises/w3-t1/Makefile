# connect/w3-t1 -- one-way audio on the Voice Connector trunk. Shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)
RUN := node scripts/run-ts.js

.PHONY: setup bundle test audit replay clean

setup: bundle
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w3-t1 ready. Start with incident/PAGE.txt, then incident/homer-ladders.txt."

bundle:      ## (re)generate the incident evidence in incident/
	@node scripts/make-bundle.js incident >/dev/null

audit:       ## run src/sdp-audit.ts over every SDP in the bundle
	@NODE_PATH="${CONNECT}/_env/node_modules" $(RUN) src/audit-cli.ts

replay:      ## replay 200 calls through the CURRENT config/sbc/*.conf
	@NODE_PATH="${CONNECT}/_env/node_modules" $(RUN) src/replay.ts

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf incident coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w3-t1 clean (shared toolchain kept in connect/_env)"
