# modernize/ai-c1 -- a guarded migration agent loop. Python only, scripted model (no API key, no network).
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test clean

setup:       ## shared venv (modernize/.venv)
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "ai-c1 ready. Harden pod_agent/loop.py, then: make test"

test:
	@$(PY) -m pytest tests

clean:
	@rm -rf .pytest_cache tests/__pycache__ pod_agent/__pycache__
	@echo "ai-c1 clean"
