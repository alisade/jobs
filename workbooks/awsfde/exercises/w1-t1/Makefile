# awsfde/w1-t1 -- throttling storm after the resilience release. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup test replay clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@AWS_ACCESS_KEY_ID=testing AWS_SECRET_ACCESS_KEY=testing AWS_DEFAULT_REGION=us-east-1 AWS_EC2_METADATA_DISABLED=true ${PY} -m replay.simulate --out run >/dev/null
	@echo "w1-t1 ready. Start with evidence/PAGE.txt, then run/dashboard.txt and run/logs/."

replay:      ## after a fix: replay this checkout's code on 2026-11-09, print its summary
	@AWS_ACCESS_KEY_ID=testing AWS_SECRET_ACCESS_KEY=testing AWS_DEFAULT_REGION=us-east-1 AWS_EC2_METADATA_DISABLED=true ${PY} -m replay.simulate --out run --only current
	@echo "full panel: run/replay-current/dashboard.txt"

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-t1 clean (shared venv kept)"
