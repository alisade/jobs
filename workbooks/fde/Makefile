# FDE workbook helpers. Each exercise has its own Makefile (setup / test / clean).
SHELL := /bin/bash

.PHONY: venv validate distclean

venv:        ## build or reuse the shared venv fde/.venv
	@bash _env/ensure-venv.sh

validate:    ## authoring check: the five SPEC validations for every exercise
	@bash _env/validate.sh all

distclean:   ## stop every exercise's processes and remove the shared venv
	@for d in exercises/*/; do make -s -C "$${d}" clean >/dev/null 2>&1 || true; done
	@rm -rf .venv
	@echo "removed fde/.venv"
