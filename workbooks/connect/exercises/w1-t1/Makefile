# connect/w1-t1 -- callers loop on "all specialists are busy". Shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle lint simulate test clean

setup:
	@$(MAKE) -s bundle
	@echo "w1-t1 ready. Start with incident/PAGE.txt."

bundle:      ## (re)generate the incident bundle from the flow deployed on 2026-10-07
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@node scripts/make-bundle.js

lint:        ## graph checks on YOUR working copy flows/helpdesk-inbound.json
	@node -e 'const k=require("connect-kit"); const r=k.validateFlow(require("./flows/helpdesk-inbound.json")); r.issues.forEach(i=>console.log(i.severity.padEnd(8), i.code.padEnd(22), (i.actionId||"-").padEnd(24), i.message)); console.log(r.ok ? "flow OK" : "flow has errors"); process.exit(r.ok?0:1)'

simulate:    ## replay one caller through YOUR working copy: make simulate INPUTS=2 PR_STAFFED=0 VIP=false
	@node scripts/simulate.js

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf incident coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w1-t1 clean"
