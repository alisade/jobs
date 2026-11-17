# aiarch/w6-c1 -- SSM Automation runbook: roll back an AgentCore endpoint (local interpreter). Shared venv aiarch/.venv.
SHELL := /bin/bash
AIARCH := $(abspath ../..)
PY := ${AIARCH}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${AIARCH}/_env/ensure-venv.sh"
	@echo "w6-c1 ready. Edit runbooks/rollback-agent-endpoint.yaml, then: make test"

test:
	@${PY} -m pytest -q tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-c1 clean (shared venv kept)"
