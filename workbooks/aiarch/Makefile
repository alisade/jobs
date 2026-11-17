# aiarch workbook helpers. Each exercise has its own Makefile (setup / test / clean).
SHELL := /bin/bash

.PHONY: deps workbook validate distclean

deps:        ## install the shared Python venv (aiarch/.venv) and node toolchain (aiarch/_env/node_modules)
	@bash _env/ensure-venv.sh
	@bash _env/ensure-node.sh

workbook:    ## rebuild workbook.html from exercises/*/card.json and _env/quiz/*.json
	@python3 _env/build_workbook.py

validate:    ## authoring check: setup, test, starter fails, solution passes, clean, for every exercise
	@bash _env/validate.sh all

distclean:   ## clean every exercise, remove the shared toolchains
	@for d in exercises/*/; do make -s -C "$${d}" clean >/dev/null 2>&1 || true; done
	@rm -rf _env/node_modules .venv
	@echo "removed aiarch/_env/node_modules and aiarch/.venv"
