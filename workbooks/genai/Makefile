# genai workbook helpers. Each exercise has its own Makefile (setup / test / clean).
SHELL := /bin/bash

.PHONY: deps workbook validate distclean

deps:        ## install the shared node toolchain (genai/_env/node_modules) and the Python venv (genai/.venv)
	@bash _env/ensure-node.sh
	@bash _env/ensure-venv.sh

workbook:    ## rebuild workbook.html from exercises/*/card.json and _env/quiz/*.json
	@python3 _env/build_workbook.py

validate:    ## authoring check: the SPEC validations for every exercise (make validate ID=w1-c1 for one)
	@bash _env/validate.sh $(or $(ID),all)

distclean:   ## clean every exercise, remove the shared toolchains
	@for d in exercises/*/; do make -s -C "$${d}" clean >/dev/null 2>&1 || true; done
	@rm -rf _env/node_modules .venv
	@echo "removed genai/_env/node_modules and genai/.venv"
