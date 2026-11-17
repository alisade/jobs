# javaai/w4-t1 -- tutor-agent slow and 504s on Cloud Run. Shared venv javaai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test run load clean

setup:
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "w4-t1 ready. Start with incident/PAGE.txt, then: make test"

test:
	@$(PY) -m pytest -q tests

run:         ## the service on :8083 (2 s fake model)
	@$(PY) -m uvicorn tutorsvc.app:app --port 8083

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-t1 clean (shared venv kept)"

load:        ## 10 concurrent turns in-process: compare wall time with one model call
	@$(PY) tests/load.py
