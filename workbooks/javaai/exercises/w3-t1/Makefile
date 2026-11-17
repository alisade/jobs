# javaai/w3-t1 -- quiz generation returns 500 for some lessons. Shared venv javaai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test run clean

setup:
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "w3-t1 ready. Start with incident/PAGE.txt, then: make test"

test:
	@$(PY) -m pytest -q tests

run:         ## the service on :8081 against the replay model
	@$(PY) -m uvicorn quizsvc.app:app --port 8081

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-t1 clean (shared venv kept)"
