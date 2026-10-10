# connect/ai-t1 -- GenAI summary Lambda times out under Connect's 8 s limit. Shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle test clean

setup:
	@$(MAKE) -s bundle
	@echo "ai-t1 ready. Start with incident/PAGE.txt."

bundle:      ## (re)generate the incident bundle (deterministic)
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@node scripts/make-bundle.js

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf incident coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "ai-t1 clean"
