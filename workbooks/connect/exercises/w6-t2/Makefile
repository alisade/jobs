# connect/w6-t2 -- real-time supervisor alert never fires. Shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle lint test clean

setup: bundle
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w6-t2 ready. Start with incident/PAGE.txt"

bundle:      ## (re)generate the incident bundle into incident/
	@node scripts/make_bundle.js


test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf incident coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w6-t2 clean (shared toolchain kept in connect/_env)"

lint:        ## graph checks for the inbound flow and the module
	@node -e 'const k=require("connect-kit"); for (const f of ["flows/helpdesk-inbound.json","flows/modules/mod-recording-defaults.json"]) { const r=k.validateFlow(require("./"+f)); console.log(f, r.ok ? "OK" : "ERRORS"); r.issues.forEach(i=>console.log("  ", i.severity, i.code, i.actionId, i.message)); }'
