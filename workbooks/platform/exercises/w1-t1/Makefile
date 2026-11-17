# platform/w1-t1 -- prod apply denied after the WIF hardening PR. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup repro test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w1-t1 ready. Start with evidence/PAGE.txt, then: make repro"

repro:       ## replay the recorded GitHub OIDC tokens through the local WIF simulator
	@echo "== run 4409 (pull_request plan job) -> tf-plan"; ${PY} tools/wifsim.py --claims evidence/claims/plan-run-4409.json --sa tf-plan || true
	@echo; echo "== run 4412 (push to main, apply job) -> tf-apply"; ${PY} tools/wifsim.py --claims evidence/claims/apply-run-4412.json --sa tf-apply || true

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-t1 clean (shared venv kept)"
