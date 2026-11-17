# fde/ai-c1 -- eval suite for a shopping agent. Uses the shared venv at fde/.venv (built by setup).
SHELL := /bin/bash
FDE := $(abspath ../..)
PY := ${FDE}/.venv/bin/python

.PHONY: setup test eval clean

setup:
	@bash "${FDE}/_env/ensure-venv.sh"
	@echo "ai-c1 ready. Edit evals/checks.py, evals/judge.py, evals/report.py, then: make test"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

eval:
	@${PY} -m evals fixtures

clean:
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache
	@echo "ai-c1 clean (shared venv kept; make -C ../.. distclean removes it)"
