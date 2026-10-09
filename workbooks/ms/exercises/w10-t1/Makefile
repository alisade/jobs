.PHONY: setup test clean

setup:
	uv sync --quiet
	uv run python scripts/make_incident.py

test:
	uv run pytest -q tests

clean:
	rm -rf .venv incident .pytest_cache tests/__pycache__ scripts/__pycache__ .grading/tests/__pycache__
