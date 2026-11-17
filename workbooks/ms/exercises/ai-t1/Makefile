.PHONY: setup test eval clean

# Build the production index from config/index.yaml, then generate the incident bundle.
setup:
	uv sync --quiet
	uv run python -m policy_rag.build --config config/index.yaml --corpus corpus --out index --built-at 2026-12-07T02:14:09Z
	uv run python -m scripts.make_incident

test:
	uv run pytest -q tests

# Run the retrieval eval with the app config against the built index.
eval:
	uv run python -m policy_rag.evaluate --config config/app.yaml --questions eval/questions.jsonl --out report.json

clean:
	rm -rf .venv .pytest_cache index incident report.json
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
