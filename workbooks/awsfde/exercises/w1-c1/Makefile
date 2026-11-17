# awsfde/w1-c1 -- Converse tool-use loop with a guardrail and cost logging. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w1-c1 ready. Read README.md, then edit ask_agent/loop.py and ask_agent/costs.py."

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-c1 clean (shared venv kept)"
