.PHONY: setup test clean

setup:
	uv sync --quiet

test:
	uv run pytest -q tests

clean:
	rm -rf .venv .pytest_cache tests/__pycache__ .grading/tests/__pycache__
