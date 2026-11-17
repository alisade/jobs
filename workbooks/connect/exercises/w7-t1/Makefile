# connect/w7-t1 -- bot-to-agent handoff loses context. Shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle lint test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@$(MAKE) -s bundle
	@echo "w7-t1 ready. Start with incident/PAGE.txt."

bundle:      ## (re)generate incident/ from this checkout's flows and module
	@node scripts/gen_bundle.js

lint:
	@for f in flows/*.json modules/*.json; do node -e 'const k=require("connect-kit"); const r=k.validateFlow(require("./"+process.argv[1])); console.log((r.ok?"OK    ":"ERRORS")+" "+process.argv[1]); r.issues.forEach(i=>console.log("   ",i.severity,i.code,i.actionId,i.message))' "$${f}"; done

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf incident coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w7-t1 clean (shared toolchain kept in connect/_env)"
