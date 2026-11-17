# genai/x-2 -- human handoff opens the wrong conversation (troubleshooting). Shared toolchain in genai/_env.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "x-2 ready. Start with evidence/PAGE.md, then: make test"

test:
	@"${TRACK}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "x-2 clean (shared toolchain kept in genai/_env)"
