# audit/w6-c1 -- eval harness per control (accuracy, exception recall, consistency, cost, latency, gate).
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup test eval eval-v4 clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@echo "w6-c1 ready: edit evalkit/metrics.py and evalkit/report.py; then make test, make eval"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

eval:        ## score prompt v3 against the labeled set and apply the gate
	@${PY} -m evalkit.cli --runs data/runs.jsonl --out out/v3

eval-v4:     ## score the prompt v4 candidate (should be blocked)
	@${PY} -m evalkit.cli --runs data/runs_prompt_v4.jsonl --out out/v4

clean:
	@rm -rf out .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-c1 clean (shared venv kept)"
