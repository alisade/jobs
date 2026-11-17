# awsfde/w5-c1 -- openCypher queries and a tenant-safe Neptune Analytics graph tool. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w5-c1 ready. Read README.md, then write queries/*.cypher and graphlib/graph_tool.py."

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-c1 clean (shared venv kept)"
