# connect/w1-c2 -- help desk instance as CDK (TypeScript). Synth is offline; nothing is deployed.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test synth clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w1-c2 ready. Edit lib/helpdesk-stack.ts, then: make test"

synth:       ## print the synthesized template: make synth ENV=prod
	@"${CONNECT}/_env/node_modules/.bin/tsc" --outDir .build --module commonjs --target ES2022 --esModuleInterop --skipLibCheck scripts/synth.ts
	@node .build/scripts/synth.js

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage cdk.out .build
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w1-c2 clean (shared toolchain kept in connect/_env)"
