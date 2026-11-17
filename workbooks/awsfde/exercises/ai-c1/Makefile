# awsfde/ai-c1 -- agent eval harness as a CI gate. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test eval clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "ai-c1 ready. Read README.md, then edit evalkit/checks.py and evalkit/harness.py, then make eval."

eval:        ## gate the candidate release against the baseline (exit 1 = no-go)
	@"${TRACK}/.venv/bin/python" -m evalkit.cli fixtures/candidate.jsonl --baseline fixtures/baseline.jsonl

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf .pytest_cache run
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "ai-c1 clean (shared venv kept)"
