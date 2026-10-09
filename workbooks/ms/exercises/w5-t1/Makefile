.PHONY: setup test preflight clean

setup:
	uv sync --quiet
	uv run python scripts/make_incident.py

test:
	uv run pytest -q tests

# What the release workflow should run before any pac solution import
preflight:
	uv run python deploy/preflight.py --manifest deploy/manifest.yaml --inventory deploy/environments/uat.json --artifacts deploy/artifacts.json

clean:
	rm -rf .venv incident .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
