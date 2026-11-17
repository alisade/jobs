# genai/w1-c1 -- streamed assistant panel (React + TypeScript). Shared toolchain in genai/_env.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w1-c1 ready. Edit src/*.ts(x), then: make test"

test:
	@"${TRACK}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w1-c1 clean (shared toolchain kept in genai/_env)"
