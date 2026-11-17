# connect/w5-t1 -- RAG bot answers with stale / wrong-department articles. Shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle replay test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@$(MAKE) -s bundle
	@echo "w5-t1 ready. Start with incident/PAGE.txt"

bundle:      ## regenerate incident/ from this checkout (deterministic)
	@node scripts/ts-run.js scripts/make-bundle.ts

replay:      ## replay the recorded traffic through this checkout's exporter + retriever
	@node scripts/ts-run.js scripts/replay.ts

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage incident
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w5-t1 clean (shared toolchain kept in connect/_env)"
