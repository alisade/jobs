# connect/w7-c4 -- design exercise (review-only). No build; the grader reviews DESIGN.md and ANSWER.md.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "w7-c4 is a design exercise: read inputs/, then write DESIGN.md and ANSWER.md."

test:        ## completeness report (which sections are still empty)
	@bash "${CONNECT}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md | sed '$$d'

clean:
	@echo "w7-c4 clean (nothing to remove)"
