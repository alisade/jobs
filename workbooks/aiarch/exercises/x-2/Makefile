# aiarch/x-2 -- design exercise: pipeline ADR and endpoint policies. Graded by rubric (no tests).
SHELL := /bin/bash
AIARCH := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "x-2 ready. Nothing to install; read inputs/requirements.md, then write DESIGN.md and ANSWER.md."

test:        ## completeness report (rubric-graded, no tests)
	@bash "${AIARCH}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md

clean:
	@echo "x-2 clean (nothing to remove)"
