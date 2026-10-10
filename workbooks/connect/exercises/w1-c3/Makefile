# connect/w1-c3 -- design exercise (review-only). Edit DESIGN.md and ANSWER.md.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "w1-c3 is a design exercise: read inputs/, fill in DESIGN.md and ANSWER.md, then /grade connect/w1-c3"

test:        ## completeness report (which sections are still empty); graded by rubric, not tests
	@bash "${CONNECT}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md

clean:
	@echo "w1-c3 clean (nothing to remove)"
