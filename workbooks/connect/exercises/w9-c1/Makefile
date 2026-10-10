# connect/w9-c1 -- identity and security architecture (design, review-only). Nothing to install.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "w9-c1 ready. Read inputs/, then fill in DESIGN.md and ANSWER.md."

test:        ## completeness report only (the rubric grades the content)
	@bash "${CONNECT}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md

clean:
	@echo "w9-c1 clean (nothing to remove)"
