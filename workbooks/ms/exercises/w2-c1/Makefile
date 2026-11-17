SHELL := /bin/bash
.PHONY: setup test clean

setup:
	uv sync --quiet
	@echo "Ready. Edit queries/*.kql, then run: make test"

test:
	uv run pytest -q tests

clean:
	rm -rf .venv .pytest_cache tests/__pycache__
