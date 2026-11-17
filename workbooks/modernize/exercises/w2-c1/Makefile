# modernize/w2-c1 -- reverse-engineer claimdesk-web into an evidence-backed inventory. Python only.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup test check clean

setup:       ## build the shared venv (modernize/.venv)
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "w2-c1 ready. Read app/, fill spec/inventory.json and spec/SPEC.md"

test:        ## visible checks: schema, every evidence ref resolves, a few obvious facts
	@$(PY) -m pytest tests

check:       ## list evidence references that do not resolve
	@$(PY) -c "import sys; sys.path.insert(0,'tests'); import inventory_check as ic; p=ic.evidence_problems(ic.load()); print('\n'.join(p) or 'all evidence resolves')"

clean:
	@rm -rf .pytest_cache tests/__pycache__
	@echo "w2-c1 clean"
