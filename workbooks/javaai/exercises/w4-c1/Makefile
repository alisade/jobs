# javaai/w4-c1 -- FastAPI tutor agent service: auth, scoped tools, guardrails. Shared venv javaai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test run clean

setup:
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "w4-c1 ready. Edit tutor/auth.py, agent.py and app.py, then: make test"

test:
	@$(PY) -m pytest -q tests

run:         ## (needs a model; tests are the main loop)
	@$(PY) -m uvicorn tutor.app:create_app --factory --port 8082

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-c1 clean (shared venv kept)"
