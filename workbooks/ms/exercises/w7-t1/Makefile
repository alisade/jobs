.PHONY: setup test replay clean

setup:
	uv sync --quiet
	uv run python -m flowsim.make_incident
	@echo "Evidence is in incident/. The flow you fix is in solution/Workflows/."

test:
	uv run pytest -q tests

replay:
	uv run python -m flowsim.replay

clean:
	rm -rf .venv .pytest_cache incident
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
