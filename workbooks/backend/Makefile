# Backend workbook helpers. Each exercise has its own Makefile (setup / test / clean).
SHELL := /bin/bash

.PHONY: deps workbook validate distclean

deps:        ## install the shared node toolchain (backend/_env/node_modules), the Python venv (backend/.venv) and the Temporal test server (backend/.temporal)
	@bash _env/ensure-node.sh
	@bash _env/ensure-venv.sh
	@bash _env/ensure-temporal.sh >/dev/null

workbook:    ## rebuild workbook.html from exercises/*/card.json and _env/quiz/*.json
	@python3 _env/build_workbook.py

validate:    ## authoring check: the five SPEC validations for every exercise (or: make validate IDS="w1-t1 w3-c1")
	@bash _env/validate.sh $(if $(IDS),$(IDS),all)

distclean:   ## clean every exercise, remove the shared toolchains
	@for d in exercises/*/; do make -s -C "$${d}" clean >/dev/null 2>&1 || true; done
	@rm -rf _env/node_modules .venv .temporal
	@echo "removed backend/_env/node_modules, backend/.venv and backend/.temporal"
