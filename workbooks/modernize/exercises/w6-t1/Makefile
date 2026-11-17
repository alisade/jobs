# modernize/w6-t1 -- an agent PR passed CI by rewriting the golden files. Python only.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup bundle guard test clean

setup:       ## shared venv + the incident bundle (incident/)
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@$(MAKE) -s bundle
	@echo "w6-t1 ready. Start with incident/PAGE.txt"

bundle:      ## (re)generate incident/
	@python3 scripts/make_bundle.py

guard:       ## run the CI guard on the PR that shipped
	@python3 ci/pr_guard.py incident/pr-1187.diff; echo "exit $$?"

test:
	@$(PY) -m pytest tests

clean:
	@rm -rf incident .pytest_cache __pycache__ tests/__pycache__ ci/__pycache__ scripts/__pycache__
	@echo "w6-t1 clean"
