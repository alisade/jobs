# backend/w2-t1 -- The account timeline got slow after release 2026.44. Uses the shared node toolchain
# in backend/_env (jest + PGlite, an in-process PostgreSQL 18).
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup bundle explain test clean

setup:
	@bash "${TRACK}/_env/ensure-node.sh" link "$(CURDIR)"
	@$(MAKE) -s bundle
	@echo "w2-t1 ready: start with incident/PAGER.txt; make explain shows the live plan of queries/timeline.sql"

bundle:      ## (re)generate the evidence in incident/
	@NODE_OPTIONS=--no-warnings node scripts/make_incident.js

explain:     ## EXPLAIN (ANALYZE, BUFFERS) of queries/timeline.sql as pipeline-svc runs it
	@NODE_OPTIONS=--no-warnings node scripts/explain.js

test:
	@bash "${TRACK}/_env/jest.sh"

clean:
	@rm -rf incident coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w2-t1 clean (shared toolchain kept in backend/_env)"
