# awsfde/x-2 -- design exercise (graded by rubric only; no automated tests).
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "x-2 ready. Read inputs/, then write DESIGN.md and ANSWER.md."

test:        ## completeness report only (which sections are still empty)
	@bash "${TRACK}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md | sed '$$d'

clean:
	@echo "x-2 clean (nothing to remove)"
