# modernize/w3-t1 -- 401s for some adjusters after the IdP rotated its signing key. Needs JDK 21 + Maven.
SHELL := /bin/bash
TRACK := $(abspath ../..)
JAVA := source "$(TRACK)/_env/java-env.sh" &&

.PHONY: setup test clean

setup:       ## check the JDK, download every Maven artifact once (to ~/.m2) so grading runs offline
	@$(JAVA) java -version 2>&1 | head -1
	@bash "$(TRACK)/_env/ensure-maven.sh" "$(CURDIR)"
	@echo "w3-t1 ready. Start with evidence/PAGE.txt"

test:        ## visible tests
	@$(JAVA) mvn -q -B test

clean:
	@rm -rf target
	@echo "w3-t1 clean (~/.m2 cache kept)"
