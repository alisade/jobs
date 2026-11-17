# genai/w5-c1 -- design exercise (review-only). Edit DESIGN.md and ANSWER.md.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "w5-c1 is a design exercise: read inputs/, fill in DESIGN.md and ANSWER.md, then /grade genai/w5-c1"

test:        ## completeness report (which sections are still empty); graded by rubric, not tests
	@bash "${TRACK}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md

clean:
	@echo "w5-c1 clean (nothing to remove)"
