# javaai/x-2 -- Kanban flow metrics and a Monte Carlo forecast. Shared venv javaai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test run clean

setup:
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "x-2 ready. Edit kanban/forecast.py, then: make test"

test:
	@$(PY) -m pytest -q tests

run:         ## the forecast for the remaining backlog
	@$(PY) -m kanban.forecast

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "x-2 clean (shared venv kept)"
