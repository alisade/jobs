# healthai/w2-t1 -- CriteriaService goes dark after a FHIR latency spike. Uses the shared venv healthai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup stubs test clean repro

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${MAKE} -s stubs
	@echo "w2-t1 ready: read incident/ticket.md; make repro reproduces it"

stubs:       ## (re)generate gen/criteria_pb2*.py from protos/criteria.proto
	@rm -rf gen && mkdir -p gen
	@${PY} -m grpc_tools.protoc -Iprotos --python_out=gen --grpc_python_out=gen protos/criteria.proto

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf gen .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-t1 clean (shared venv kept)"

repro:       ## live reproduction: normal traffic, a FHIR latency spike, then normal traffic again
	@${PY} scripts/repro.py
