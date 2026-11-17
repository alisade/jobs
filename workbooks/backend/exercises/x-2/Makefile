# backend/x-2 -- The migration that took the API down. Shared node toolchain (PGlite) in backend/_env.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup lint migrate test clean

setup:
	@bash "${TRACK}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "x-2 ready. Start with evidence/TIMELINE.md"

lint:        ## kmigrate-lint over migrations/ (0057 and later)
	@node scripts/lint.js migrations

migrate:     ## apply every migration to a fresh seeded PGlite database and show the result
	@NODE_OPTIONS="--experimental-vm-modules --no-warnings" node scripts/migrate.js

test:
	@bash "${TRACK}/_env/jest.sh"

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "x-2 clean (shared toolchain kept in backend/_env)"
