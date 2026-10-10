# connect/w3-c2 -- Voice Connector as code (CDK, custom resources). Synth runs offline in the tests.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w3-c2 ready. Edit lib/voice-connector-stack.ts and config/environments.json, then: make test"

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage cdk.out
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w3-c2 clean (shared toolchain kept in connect/_env)"
