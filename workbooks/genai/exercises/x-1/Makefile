# genai/x-1 -- assistant behind a flag in the existing storefront (coding). Shared toolchain in genai/_env.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "x-1 ready. Edit src/rollout.ts and src/AssistantEntry.tsx, then: make test"

test:
	@"${TRACK}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "x-1 clean (shared toolchain kept in genai/_env)"
