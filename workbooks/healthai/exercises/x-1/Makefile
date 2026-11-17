# healthai/x-1 -- design: LoRA vs prompting for ICD-10-CM extraction (rubric-graded, no tests).
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test clean

setup:
	@echo "x-1 is a design exercise: read inputs/, write DESIGN.md and ANSWER.md"

test:
	@bash "${TRACK}/_env/grade-design.sh" "$(CURDIR)"

clean:
	@echo "x-1 clean (nothing to remove)"
