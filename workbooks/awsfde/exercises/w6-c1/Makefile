# awsfde/w6-c1 -- embed-URL Lambda, registered and anonymous embedding. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w6-c1 ready. Read README.md, then edit embed/handler.py."

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-c1 clean (shared venv kept)"
