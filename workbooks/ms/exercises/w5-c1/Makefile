.PHONY: setup test clean explain

setup:
	uv sync --quiet

test:
	uv run pytest -q tests

# Example: make explain U=maria.dispatch P=Read R=wo-1005
explain:
	PYTHONPATH=src uv run python -m dvaccess data/tailspin.json $(or $(U),maria.dispatch) $(or $(P),Read) $(or $(R),wo-1005)

clean:
	rm -rf .venv .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
