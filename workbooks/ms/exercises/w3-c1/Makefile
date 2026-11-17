.PHONY: setup test clean demo

setup:
	uv sync --quiet

test:
	uv run pytest -q tests

# Build a fragmented demo lakehouse under ./demo and run the job against it in dry-run mode.
demo:
	uv run python tests/make_demo.py demo
	uv run python src/maintenance.py --config demo/maintenance.json --report demo/report.json --dry-run

clean:
	rm -rf .venv .pytest_cache demo
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
