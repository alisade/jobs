# connect/w5-c4 -- design exercise (graded by rubric only). No toolchain needed.
SHELL := /bin/bash

.PHONY: setup test clean

setup:
	@echo "w5-c4 is a design exercise: read inputs/, then write DESIGN.md and ANSWER.md"

test:        ## completeness report (which sections are still empty); there are no automated tests
	@bash ../../_env/grade-design.sh "$(CURDIR)" DESIGN.md ANSWER.md

clean:
	@echo "w5-c4 clean (nothing to remove)"
