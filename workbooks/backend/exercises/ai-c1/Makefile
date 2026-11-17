# backend/ai-c1 -- Tenant-scoped MCP tool server with an audit log. Uses the shared venv backend/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "ai-c1 ready. Read README.md, then edit keystone_mcp/server.py and keystone_mcp/identity.py"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-c1 clean (shared venv kept)"
