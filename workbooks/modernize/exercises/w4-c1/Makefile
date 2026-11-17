# modernize/w4-c1 -- javax.servlet to jakarta.servlet with characterization tests. Needs JDK 21 + Maven.
SHELL := /bin/bash
TRACK := $(abspath ../..)
JAVA := source "$(TRACK)/_env/java-env.sh" &&

.PHONY: setup test run clean

setup:       ## check the JDK, download every Maven artifact once (to ~/.m2) so grading runs offline
	@$(JAVA) java -version 2>&1 | head -1
	@bash "$(TRACK)/_env/ensure-maven.sh" "$(CURDIR)"
	@echo "w4-c1 ready. make test is green now: keep it green through the migration"

test:        ## characterization tests against the golden masters (Tomcat logs to the console; look for FAILURE)
	@$(JAVA) mvn -q -B test

run:         ## run the service on :8080
	@$(JAVA) mvn -q -B -DskipTests package && java -cp "target/classes:$$(mvn -q -B dependency:build-classpath -Dmdep.outputFile=/dev/stdout)" com.corvane.claimdesk.notes.NotesServer

clean:
	@rm -rf target
	@echo "w4-c1 clean (~/.m2 cache kept)"
