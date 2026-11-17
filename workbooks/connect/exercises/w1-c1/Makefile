# connect/w1-c1 -- help desk inbound flow. Uses the shared toolchain in connect/_env (node_modules symlinked in).
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test lint simulate clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w1-c1 ready. Edit flows/helpdesk-inbound.json, then: make lint && make test"

lint:        ## structural + graph checks only
	@node -e 'const k=require("connect-kit"); const r=k.validateFlow(require("./flows/helpdesk-inbound.json")); r.issues.forEach(i=>console.log(i.severity.padEnd(8), i.code.padEnd(22), (i.actionId||"-").padEnd(22), i.message)); console.log(r.ok ? "flow OK" : "flow has errors"); process.exit(r.ok?0:1)'

simulate:    ## one call path: make simulate INPUTS='1' OPEN=true
	@node scripts/simulate.js

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w1-c1 clean (shared toolchain kept in connect/_env)"
