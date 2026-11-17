# javaai/ai-t1 -- the tutor marked lessons mastered that learners never attempted. Shared venv javaai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "ai-t1 ready. Start with incident/PAGE.txt, then: make test"

test:
	@$(PY) -m pytest -q tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-t1 clean (shared venv kept)"
