# backend/w4-c1 -- Opportunity stage transitions with an outbox (Fastify + Kysely). Uses the shared node
# toolchain in backend/_env (jest, Fastify, Kysely, Zod, PGlite).
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w4-c1 ready. Edit src/transitions.ts, src/app.ts and src/shutdown.ts, then: make test"

test:
	@bash "${TRACK}/_env/jest.sh"

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w4-c1 clean (shared toolchain kept in backend/_env)"
