# backend/x-1 -- design exercise (review-only, timed). Edit DESIGN.md and ANSWER.md.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "x-1 is a timed design exercise: set a 45-minute timer, read inputs/prompt.md only, write DESIGN.md."
	@echo "Open inputs/curveballs.md at minute 30. Then fill in ANSWER.md and /grade backend/x-1"

test:        ## completeness report (which sections are still empty); graded by rubric, not tests
	@bash "${TRACK}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md

clean:
	@echo "x-1 clean (nothing to remove)"
