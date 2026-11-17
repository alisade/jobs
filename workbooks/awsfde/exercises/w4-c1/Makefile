# awsfde/w4-c1 -- tenant-scoped tool Lambda, single-table DynamoDB, LeadingKeys. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w4-c1 ready. Read README.md, then edit tickets/*.py."

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-c1 clean (shared venv kept)"
