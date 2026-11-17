# javaai/w1-t1 -- learner progress endpoint is slow (Java 21, Spring Data JPA, H2). Needs JDK 21 + Maven.
SHELL := /bin/bash
TRACK := $(abspath ../..)
JAVA := source "$(TRACK)/_env/java-env.sh" &&

.PHONY: setup test run clean

setup:       ## check the JDK and download every Maven artifact once (to ~/.m2) so grading runs offline
	@$(JAVA) java -version 2>&1 | head -1
	@$(JAVA) mvn -q -B -Dmaven.test.failure.ignore=true test >/dev/null 2>&1 || true
	@echo "w1-t1 ready. Start with incident/PAGE.txt, then: make test"

test:
	@$(JAVA) mvn -q -B test

run:         ## start the API on :8080 (H2 in memory)
	@$(JAVA) mvn -q -B spring-boot:run

clean:
	@rm -rf target
	@echo "w1-t1 clean (~/.m2 cache kept)"
