# modernize/ai-t1 -- the headless migration agent costs 4x: prompt caching never hits. Python only, offline.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup replay test clean

setup:       ## shared venv (modernize/.venv)
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "ai-t1 ready. Start with evidence/PAGE.txt, then: make replay"

replay:      ## replay a recorded 8-turn session through build_request and the offline cache model
	@$(PY) -m migrate_agent.session

test:
	@$(PY) -m pytest tests

clean:
	@rm -rf .pytest_cache tests/__pycache__ migrate_agent/__pycache__
	@echo "ai-t1 clean"
