# connect/w8-c3 -- design exercise (graded by rubric only; no automated tests).
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "w8-c3 ready. Read inputs/, then write DESIGN.md and ANSWER.md."

test:        ## completeness report only (which sections are still empty)
	@bash "${CONNECT}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md | sed '$$d'

clean:
	@echo "w8-c3 clean (nothing to remove)"
