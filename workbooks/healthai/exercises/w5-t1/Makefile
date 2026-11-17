# healthai/w5-t1 -- the chunker splits a criteria table mid-row. Uses the shared venv healthai/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python
P ?= KHP-MP-0101

.PHONY: setup eval chunks test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w5-t1 ready: read incident/ticket.md, then make eval / make chunks"

eval:        ## retrieval eval (recall@5 overall and per kind, misses)
	@${PY} -m chunking.evaluate 5

chunks:      ## print the chunks of one policy: make chunks P=KHP-MP-0101
	@${PY} -c "import sys; from pathlib import Path; from chunking.chunker import chunk_policy; [print('-----', c.id, '|', c.section_path, '|', c.kind, chr(10) + c.text) for c in chunk_policy(Path('policies/${P}.md').read_text(), '${P}')]"

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-t1 clean (shared venv kept)"
