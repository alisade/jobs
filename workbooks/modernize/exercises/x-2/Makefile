# modernize/x-2 -- blast radius and rollback for corvane-commons 3.0 (design, review-only). Nothing to install.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "x-2 ready. Read inputs/, then fill in DESIGN.md and ANSWER.md."

test:        ## completeness report only (the rubric grades the content)
	@bash "$(TRACK)/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md

clean:
	@echo "x-2 clean (nothing to remove)"
