# javaai/w5-c1 -- retrieval eval: chunking, recall@k, MRR and a CI gate. Shared venv javaai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test run clean

setup:
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "w5-c1 ready. Edit rag/chunking.py, retrieve.py, metrics.py and evaluate.py, then: make test"

test:
	@$(PY) -m pytest -q tests

run:         ## the eval report and the gate
	@$(PY) -m rag.evaluate

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-c1 clean (shared venv kept)"
