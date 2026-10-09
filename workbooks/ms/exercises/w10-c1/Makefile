.PHONY: setup test gate clean

setup:
	uv sync --quiet

test:
	uv run pytest -q tests

# Run the gate on the recorded baseline and candidate runs (writes report.json).
gate:
	uv run python -m release_gate --testset data/testset.jsonl --baseline data/runs/baseline \
	  --candidate data/runs/candidate --config gate.yaml --out report.json; echo "exit code: $$?"

clean:
	rm -rf .venv .pytest_cache report.json
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
