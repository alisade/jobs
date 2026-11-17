# javaai/w5-t1 -- tutor cites the wrong lessons after a re-index. Shared venv javaai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test run clean

setup:
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "w5-t1 ready. Start with incident/PAGE.txt, then: make test"

test:
	@$(PY) -m pytest -q tests

run:         ## the release-checklist retrieval eval
	@$(PY) -m ingest.eval

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-t1 clean (shared venv kept)"
