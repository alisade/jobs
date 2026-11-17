.PHONY: setup test render guard clean

ENV ?= PROD

setup:
	uv sync --quiet
	uv run python scripts/make_incident.py

test:
	uv run pytest -q tests

# Dry-run the release for one environment: make render ENV=PPE
render:
	uv run python deploy/render.py --env $(ENV) --out incident/render/$(ENV)

# Run the post-render guard on the dry-run output: make guard ENV=PROD
guard: render
	uv run python deploy/check_bindings.py --env $(ENV) --rendered incident/render/$(ENV)

clean:
	rm -rf .venv incident .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
