# javaai/w6-c1 -- tuned vs prompted Gemini: dataset and eval. Shared venv javaai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test run clean

setup:
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "w6-c1 ready. Edit tuneval/tuning.py and tuneval/evaluate.py, then: make test"

test:
	@$(PY) -m pytest -q tests

run:         ## the comparison report
	@$(PY) -m tuneval.evaluate

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-c1 clean (shared venv kept)"
