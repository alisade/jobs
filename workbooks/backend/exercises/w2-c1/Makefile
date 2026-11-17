# backend/w2-c1 -- Keystone core schema with tenancy enforced in the database. Uses the shared node
# toolchain in backend/_env (jest + PGlite, an in-process PostgreSQL 18).
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test plans clean

setup:
	@bash "${TRACK}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w2-c1 ready. Edit migrations/*.sql, then: make test (and make plans)"

test:
	@bash "${TRACK}/_env/jest.sh"

plans:       ## print the EXPLAIN plan of each query in queries/ as keystone_app for bu-emea
	@NODE_OPTIONS=--no-warnings node scripts/plans.js

clean:
	@rm -rf coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w2-c1 clean (shared toolchain kept in backend/_env)"
