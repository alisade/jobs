SHELL := /bin/bash
.PHONY: setup test lint clean

setup:
	uv sync --quiet
	@echo "Ready. Edit pl_nightly_orchestrator.DataPipeline/pipeline-content.json, then: make lint && make test"

lint:
	uv run python lint/pipeline_lint.py pl_nightly_orchestrator.DataPipeline/pipeline-content.json

test:
	uv run pytest -q tests

clean:
	rm -rf .venv .pytest_cache tests/__pycache__ lint/__pycache__
