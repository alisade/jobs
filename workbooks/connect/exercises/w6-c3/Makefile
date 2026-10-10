# connect/w6-c3 -- design exercise (review-only). No toolchain needed.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "w6-c3 is a design exercise: read inputs/current-state.md, fill in DESIGN.md and ANSWER.md"

test:        ## completeness report (no automated tests)
	@bash "${CONNECT}/_env/grade-design.sh" "$(CURDIR)" DESIGN.md ANSWER.md

clean:
	@echo "w6-c3: nothing to clean"
