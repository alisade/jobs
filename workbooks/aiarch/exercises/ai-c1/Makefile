# aiarch/ai-c1 -- change-management MCP server (MCP Python SDK 2.x, tested in-process). Shared venv aiarch/.venv.
SHELL := /bin/bash
AIARCH := $(abspath ../..)
PY := ${AIARCH}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${AIARCH}/_env/ensure-venv.sh"
	@echo "ai-c1 ready. Edit changemgmt/server.py, then: make test"

test:
	@${PY} -m pytest -q tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-c1 clean (shared venv kept)"
