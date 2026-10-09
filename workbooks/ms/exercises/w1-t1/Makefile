.PHONY: setup test clean simulate

setup:
	uv sync --quiet
	uv run python scripts/make_incident.py

test:
	uv run pytest -q tests

simulate:
	uv run python tools/simulate_run.py pipelines/PL_Nightly_ERP_Load.DataPipeline/pipeline-content.json

clean:
	rm -rf .venv .pytest_cache incident
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
