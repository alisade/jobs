.PHONY: setup test clean

setup:
	uv sync --quiet

test:
	uv run pytest -q tests

clean:
	rm -rf .venv .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
