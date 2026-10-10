# connect/w2-c2 -- routing simulator. Uses the shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)
CONFIG ?= inputs/tuned-config.json
SEED ?=

.PHONY: setup test run baseline clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w2-c2 ready. Edit src/sim.ts, then: make test; tune inputs/tuned-config.json with make run"

baseline:    ## today's LFG routing design on the published stream
	@node scripts/run.js inputs/lfg-config.json ${SEED}

run:         ## your tuned design: make run [CONFIG=...] [SEED=n]
	@node scripts/run.js ${CONFIG} ${SEED}

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w2-c2 clean (shared toolchain kept in connect/_env)"
