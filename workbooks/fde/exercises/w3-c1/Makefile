# fde/w3-c1 -- AgentTrustMixin. Uses the shared venv at fde/.venv (built by setup).
SHELL := /bin/bash
FDE := $(abspath ../..)
PY := ${FDE}/.venv/bin/python

.PHONY: setup test clean

setup:
	@bash "${FDE}/_env/ensure-venv.sh"
	@echo "w3-c1 ready. Edit trust_mixin/mixin.py, then: make test"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache
	@echo "w3-c1 clean (shared venv kept; make -C ../.. distclean removes it)"
