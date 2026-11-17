# javaai/w6-t1 -- learner dashboard query slow (SQLite stands in for Cloud SQL). Shared venv javaai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test explain clean

setup:       ## venv + data/kestrel.db with 200k attempts (V1-V6 applied, as in production)
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@mkdir -p data
	@if [ ! -f data/kestrel.db ]; then $(PY) scripts/seed.py data/kestrel.db; fi
	@echo "w6-t1 ready. Start with incident/PAGE.txt; make explain shows the plan and timing."

test:
	@$(PY) -m pytest -q tests

explain:     ## applies new migrations to data/kestrel.db, prints the plan and ms per query
	@$(PY) scripts/timeit.py

clean:
	@rm -rf data .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-t1 clean (shared venv kept)"
