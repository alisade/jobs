# modernize/w2-t1 -- the reverse-engineer skill missed the batch module's tables. Python only.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := $(TRACK)/.venv/bin/python

.PHONY: setup bundle scan test clean

setup:       ## shared venv + the incident bundle (repo/ and incident/)
	@bash "$(TRACK)/_env/ensure-venv.sh"
	@$(MAKE) -s bundle
	@echo "w2-t1 ready. Start with incident/PAGE.txt"

bundle:      ## (re)generate repo/ and incident/
	@python3 scripts/make_bundle.py

scan:        ## run the skill's scanner the way the agent does
	@python3 skill/reverse-engineer/scripts/scan_db.py repo

test:
	@$(PY) -m pytest tests

clean:
	@rm -rf repo incident .pytest_cache tests/__pycache__ __pycache__ skill/reverse-engineer/scripts/__pycache__ scripts/__pycache__
	@echo "w2-t1 clean"
