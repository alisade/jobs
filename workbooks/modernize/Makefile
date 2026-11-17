# Modernize workbook helpers. Each exercise has its own Makefile (setup / test / clean).
SHELL := /bin/bash

.PHONY: deps workbook validate distclean

deps:        ## shared toolchains: Python venv (modernize/.venv), Maven artifacts (~/.m2), dotnet check
	@bash _env/ensure-venv.sh
	@bash _env/ensure-maven.sh
	@command -v dotnet >/dev/null 2>&1 && dotnet --version || echo "dotnet SDK not found: only w5-c1 needs it (tools/doctor.sh modernize)"

workbook:    ## rebuild workbook.html from exercises/*/card.json and _env/quiz/*.json
	@python3 _env/build_workbook.py

validate:    ## authoring check: the SPEC validations for every exercise (or: make validate IDS="w1-c1 x-1")
	@bash _env/validate.sh $(or $(IDS),all)

distclean:   ## clean every exercise, remove the shared venv (the ~/.m2 and NuGet caches are kept)
	@for d in exercises/*/; do make -s -C "$${d}" clean >/dev/null 2>&1 || true; done
	@rm -rf .venv
	@echo "removed modernize/.venv"
