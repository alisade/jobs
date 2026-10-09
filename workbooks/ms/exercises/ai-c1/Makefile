.PHONY: setup test demo clean

setup:
	uv sync --quiet

test:
	uv run pytest -q tests

# Replay the recorded injection conversation and print the transcript.
demo:
	uv run python -m parts_agent.demo fixtures/injection.json

clean:
	rm -rf .venv .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
