# connect/w3-c3 -- design exercise (review-only). No build; the grader reviews DESIGN.md and ANSWER.md.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "w3-c3 is a design exercise: read inputs/, then write DESIGN.md and ANSWER.md."

test:        ## completeness report (which sections are still empty)
	@bash "${CONNECT}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md | grep -v '^GRADE_TESTS'

clean:
	@echo "w3-c3: nothing to clean"
