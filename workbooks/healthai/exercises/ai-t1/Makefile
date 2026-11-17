# healthai/ai-t1 -- denial finalized with no reviewer. Uses the shared venv healthai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup replay test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/replay.py fixtures/transcript_incident.json PA-2026-0412 > incident/agent-transcript.txt
	@echo "ai-t1 ready: read incident/ticket.md and incident/agent-transcript.txt"

replay:      ## make replay T=fixtures/transcript_incident.json C=PA-2026-0412
	@${PY} scripts/replay.py $${T:-fixtures/transcript_incident.json} $${C:-PA-2026-0412}

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache incident/agent-transcript.txt
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-t1 clean (shared venv kept)"
