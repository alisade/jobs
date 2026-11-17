# javaai/w2-t1 -- quiz screen shows the wrong lesson (TypeScript + RxJS, jest). Shared toolchain in javaai/_env.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "$(TRACK)/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w2-t1 ready. Start with incident/PAGE.txt, then: make test"

test:
	@"$(TRACK)/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm -f node_modules; fi
	@echo "w2-t1 clean"
