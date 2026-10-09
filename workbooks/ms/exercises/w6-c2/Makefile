.PHONY: setup test clean

setup:
	uv sync --quiet
	@echo "Ready. Edit woodgrove_sync/client.py, then: make test"

test:
	uv run pytest -q tests

clean:
	rm -rf .venv .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
