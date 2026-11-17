# audit/ai-c1 -- GRC MCP server (mcp 2.x): scoped read tools and a gated write. Uses audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@echo "ai-c1 ready: edit grcmcp/server.py and grcmcp/tokens.py; then make test"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-c1 clean (shared venv kept)"
