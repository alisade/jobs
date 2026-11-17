# awsfde/w2-c1 -- AgentCore Runtime entrypoint with per-tenant, per-user Memory. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w2-c1 ready. Read README.md, then edit ask_runtime/app.py and ask_runtime/memory.py."

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-c1 clean (shared venv kept)"
