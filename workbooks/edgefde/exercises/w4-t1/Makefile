# edgefde/w4-t1 -- INT8 model misses faults on the gateway. Uses the shared venv edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python
export OMP_NUM_THREADS := 1
export PYTHONWARNINGS := ignore

.PHONY: setup run inspect test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/make_incident.py >/dev/null
	@echo "w4-t1 ready: incident/ holds release-quantize.log, gateway-eval.txt, gateway-dun-p007.log"

run:         ## rebuild the models with your edge/quantize.py and score a gateway day
	@${PY} -m edge.quantize --out build && ${PY} scripts/gateway_eval.py build

inspect:     ## scale and zero point of every QuantizeLinear in the INT8 model
	@${PY} scripts/inspect_qdq.py build/pump-anomaly-int8.onnx

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf artifacts data build incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-t1 clean (shared venv kept)"
