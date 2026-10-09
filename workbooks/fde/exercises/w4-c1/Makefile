# fde/w4-c1 -- trust-advisor Customer MCP server. Uses the shared venv fde/.venv.
SHELL := /bin/bash
FDE := $(abspath ../..)
PY := ${FDE}/.venv/bin/python

.PHONY: setup test serve clean

setup:
	@bash "${FDE}/_env/ensure-venv.sh"
	@echo "w4-c1 ready. Edit trust_advisor/{server,redact,policy_lint,hooks}.py, then: make test"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

serve:       ## optional: streamable HTTP on 127.0.0.1:8300/mcp (Ctrl-C to stop; try MCP Inspector)
	@${PY} -m trust_advisor.server

clean:
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache
	@echo "w4-c1 clean (shared venv kept)"
