# modernize/w5-t1 -- the remediation report says fixed, the scanner says vulnerable. Python only.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup report test clean

setup:       ## build the shared venv (modernize/.venv)
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "w5-t1 ready. Start with evidence/PAGE.txt"

report:      ## re-run the release gate exactly as CI does, into report/
	@python3 remediate.py --before sbom/before.cdx.json --after sbom/after.cdx.json --advisories advisories --out report --fail-on CRITICAL; echo "gate exit $$?"

test:
	@$(PY) -m pytest tests

clean:
	@rm -rf report .pytest_cache tests/__pycache__ __pycache__
	@echo "w5-t1 clean"
