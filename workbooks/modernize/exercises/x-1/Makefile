# modernize/x-1 -- ClaimDesk will not deploy on JBoss EAP 8: the legacy security domain. Python only (static dry run).
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup check test clean

setup:       ## shared venv (modernize/.venv)
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@echo "x-1 ready. Start with evidence/PAGE.txt"

check:       ## static dry run of config/migrate-security.cli against the EAP 8 target model
	@python3 tools/cli_lint.py

test:
	@$(PY) -m pytest tests

clean:
	@rm -rf .pytest_cache tests/__pycache__ tools/__pycache__
	@echo "x-1 clean"
