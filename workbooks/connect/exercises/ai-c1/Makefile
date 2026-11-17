# connect/ai-c1 -- guarded LLM triage + eval harness. Recorded fixtures only; no model is called.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test eval clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "ai-c1 ready. Edit src/triage.ts and src/eval.ts, then: make test && make eval"

eval:        ## run eval/cases.jsonl through your triage with the replay client; prints the gate
	@"${CONNECT}/_env/node_modules/.bin/tsc" --outDir .build --module commonjs --target ES2022 --esModuleInterop --skipLibCheck scripts/run-eval.ts
	@node .build/scripts/run-eval.js

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage .build
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "ai-c1 clean"
