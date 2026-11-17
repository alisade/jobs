# connect/w4-c2 -- migration program plan (design, review-only). Nothing to install.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "w4-c2 ready. Read inputs/, then fill in DESIGN.md and ANSWER.md."

test:        ## completeness report only (the rubric grades the content)
	@bash "${CONNECT}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md

clean:
	@echo "w4-c2 clean (nothing to remove)"
