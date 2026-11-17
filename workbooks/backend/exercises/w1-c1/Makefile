# backend/w1-c1 -- design exercise (review-only). Edit DESIGN.md, adr/ and ANSWER.md.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "w1-c1 is a design exercise: read inputs/, fill in DESIGN.md, the two ADRs in adr/ and ANSWER.md, then /grade backend/w1-c1"

test:        ## completeness report (which sections are still empty); graded by rubric, not tests
	@bash "${TRACK}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md adr/0001-tenancy-model.md adr/0002-service-integration.md ANSWER.md

clean:
	@echo "w1-c1 clean (nothing to remove)"
