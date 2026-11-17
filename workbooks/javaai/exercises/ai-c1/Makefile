# javaai/ai-c1 -- read-only learner-progress MCP server (Python MCP SDK). Shared venv javaai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test run clean

setup:
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "ai-c1 ready. Edit progress_mcp/server.py, then: make test"

test:
	@$(PY) -m pytest -q tests

run:         ## the server over stdio (add it to Claude Code or MCP Inspector)
	@$(PY) -m progress_mcp.server

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-c1 clean (shared venv kept)"
