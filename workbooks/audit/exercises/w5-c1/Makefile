# audit/w5-c1 -- evidence chunks, hybrid retrieval and citation-checked conclusions. Shared venv audit/.venv.
SHELL := /bin/bash
AUDIT := $(abspath ../..)
PY := ${AUDIT}/.venv/bin/python

.PHONY: setup test chunks clean

setup:
	@bash "${AUDIT}/_env/ensure-venv.sh"
	@echo "w5-c1 ready: edit evidencekit/chunks.py, search.py, verify.py, answer.py; then make test"

chunks:      ## print the chunks your chunker builds from the evidence container
	@${PY} -c "from evidencekit.blobfake import FakeContainerClient; from evidencekit.chunks import build_chunks; [print(c.id, '|', c.text.replace(chr(10), ' / ')[:90]) for c in build_chunks(FakeContainerClient('evidence'))]"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-c1 clean (shared venv kept)"
