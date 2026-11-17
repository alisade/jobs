# edgefde/w4-c1 -- export to ONNX, quantize to INT8, prove the budget. Uses the shared venv edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python
export OMP_NUM_THREADS := 1
export PYTHONWARNINGS := ignore

.PHONY: setup build test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/train.py artifacts data

build:       ## export, quantize, benchmark; prints report.md and the exit code
	@${PY} -m edge.export --artifacts artifacts --data data --out build; echo "exit code $$?"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf artifacts data build .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-c1 clean (shared venv kept)"
