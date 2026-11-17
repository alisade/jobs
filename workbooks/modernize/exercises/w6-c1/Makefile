# modernize/w6-c1 -- modernization pod kit (design, review-only). Nothing to install.
SHELL := /bin/bash
TRACK := $(abspath ../..)
DOCS := DESIGN.md ANSWER.md skill/dependency-upgrade/SKILL.md

.PHONY: setup test clean

setup:
	@echo "w6-c1 ready. Read inputs/, then fill in skill/dependency-upgrade/SKILL.md, DESIGN.md and ANSWER.md."

test:        ## completeness report only (the rubric grades the content)
	@bash "$(TRACK)/_env/grade-design.sh" "$(CURDIR)" $(DOCS)

clean:
	@echo "w6-c1 clean (nothing to remove)"
