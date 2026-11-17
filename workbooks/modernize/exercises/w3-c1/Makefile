# modernize/w3-c1 -- LDAP groups to JWT claims with identical authorization. Needs JDK 21 + Maven.
SHELL := /bin/bash
TRACK := $(abspath ../..)
JAVA := source "$(TRACK)/_env/java-env.sh" &&

.PHONY: setup test clean

setup:       ## check the JDK, download every Maven artifact once (to ~/.m2) so grading runs offline
	@$(JAVA) java -version 2>&1 | head -1
	@bash "$(TRACK)/_env/ensure-maven.sh" "$(CURDIR)"
	@echo "w3-c1 ready. Implement JwtRoleResolver, then: make test"

test:        ## visible tests: LDAP baseline + one JWT parity check
	@$(JAVA) mvn -q -B test

clean:
	@rm -rf target
	@echo "w3-c1 clean (~/.m2 cache kept)"
