# audit/x-2 -- design exercise (review-only). Edit DESIGN.md and ANSWER.md.
SHELL := /bin/bash
AUDIT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "x-2 is a design exercise: read inputs/, fill in DESIGN.md and ANSWER.md, then /grade audit/x-2"

test:        ## completeness report (which sections are still empty); graded by rubric, not tests
	@bash "${AUDIT}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md

clean:
	@echo "x-2 clean (nothing to remove)"
