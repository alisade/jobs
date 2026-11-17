# edgefde/w3-t1 -- model v7 promoted on a stale metric. Uses the shared venv edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python
export OMP_NUM_THREADS := 1
export PYTHONWARNINGS := ignore

.PHONY: setup run test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/build_incident.py data incident >/dev/null
	@echo "w3-t1 ready: incident/ holds ci-build-412.log, registry-snapshot/, gateway-alerts.csv, changelog.md"

run:         ## rebuild the pre-#412 registry in run/ and replay build #412 through your current ci/ code
	@${PY} scripts/build_incident.py run/data run/incident

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf data incident run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-t1 clean (shared venv kept)"
