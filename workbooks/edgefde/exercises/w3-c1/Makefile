# edgefde/w3-c1 -- champion/challenger promotion gate. Uses the shared venv edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python
export OMP_NUM_THREADS := 1
export PYTHONWARNINGS := ignore::RuntimeWarning

.PHONY: setup gate test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/data.py data

gate:        ## make gate V=2  (promote v2 against the current champion; prints the CI comment)
	@mkdir -p run
	@${PY} -m gate.gate promote --registry data/registry --model pump-anomaly --challenger $${V:-1} \
		--holdout data/holdout.npz --expected-holdout-sha "$$(shasum -a 256 data/holdout.npz | cut -d' ' -f1)" \
		--comment run/comment.md; rc=$$?; cat run/comment.md 2>/dev/null; echo "exit code $${rc}"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf data run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-c1 clean (shared venv kept)"
