# awsfde workbook helpers. Each exercise has its own Makefile (setup / test / clean).
SHELL := /bin/bash

.PHONY: deps workbook validate distclean

deps:        ## build or reuse the shared Python venv awsfde/.venv
	@bash _env/ensure-venv.sh

workbook:    ## rebuild workbook.html from exercises/*/card.json and _env/quiz/*.json
	@python3 _env/build_workbook.py

validate:    ## authoring check: the five SPEC validations for every exercise
	@bash _env/validate.sh all

distclean:   ## clean every exercise, remove the shared venv
	@for d in exercises/*/; do make -s -C "$${d}" clean >/dev/null 2>&1 || true; done
	@rm -rf .venv
	@echo "removed awsfde/.venv"
