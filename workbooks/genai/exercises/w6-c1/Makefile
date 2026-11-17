# genai/w6-c1 -- catalog enrichment with validated structured output. Uses the shared venv genai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup run test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w6-c1 ready. Try: make run   (sample feed + recorded model answers), then: make test"

run:         ## run the sample supplier feed through the pipeline with recorded model answers
	@${PY} scripts/run_batch.py data/feed.jsonl data/recorded-answers.json out

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf out .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-c1 clean (shared venv kept)"
