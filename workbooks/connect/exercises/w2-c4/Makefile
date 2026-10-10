# connect/w2-c4 -- design exercise (review-only, graded by rubric).
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "w2-c4 is a design exercise: read inputs/, write DESIGN.md and ANSWER.md. 'make test' shows a completeness report."

test:        ## completeness report (no automated tests)
	@bash "${CONNECT}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md

clean:
	@echo "w2-c4 clean (nothing to remove)"
