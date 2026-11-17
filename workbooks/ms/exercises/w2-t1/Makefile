SHELL := /bin/bash
.PHONY: setup test replay clean

setup:
	uv sync --quiet
	uv run python scripts/make_incident.py

# Replay the Eventstream preview through YOUR mapping file (eventhouse/mappings/...).
replay:
	@test -f incident/eventstream_data_preview.jsonl || { echo "run make setup first"; exit 1; }
	uv run python scripts/sim.py replay incident/eventstream_data_preview.jsonl

test:
	uv run pytest -q tests

clean:
	rm -rf .venv .pytest_cache incident tests/__pycache__ scripts/__pycache__
