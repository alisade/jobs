# genai/w1-t1 -- duplicated words after the proxy change (troubleshooting). Shared toolchain in genai/_env.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w1-t1 ready. Start with evidence/PAGE.md, then: make test"

test:
	@"${TRACK}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w1-t1 clean (shared toolchain kept in genai/_env)"
