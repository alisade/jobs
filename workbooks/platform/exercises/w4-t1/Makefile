# platform/w4-t1 -- AppDatabase XRs never become Ready. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup reconcile test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w4-t1 ready. Start with evidence/PAGE.txt, then: make reconcile"

reconcile:   ## render every XR in teams/ through platform/ and show MR conditions
	@${PY} tools/xpsim.py || true

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-t1 clean (shared venv kept)"
