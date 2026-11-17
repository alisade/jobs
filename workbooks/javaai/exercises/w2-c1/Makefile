# javaai/w2-c1 -- streaming tutor chat in TypeScript + RxJS (jest). Shared toolchain in javaai/_env.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "$(TRACK)/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w2-c1 ready. Edit src/sse.ts, src/leakGuard.ts and src/tutorChat.ts, then: make test"

test:
	@"$(TRACK)/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm -f node_modules; fi
	@echo "w2-c1 clean"
