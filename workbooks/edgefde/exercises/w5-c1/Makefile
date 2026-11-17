# edgefde/w5-c1 -- OTA model rollout with canary and automatic rollback. Uses the shared venv edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python
V ?= v7

.PHONY: setup rollout test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w5-c1 ready. Implement fleet/rollout.py, then: make rollout V=v7 (or v7-crash, v7-storm, v7-slow, v7-rev2bad)"

rollout:     ## make rollout V=<version>
	@${PY} scripts/rollout.py ${V}

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-c1 clean (shared venv kept)"
