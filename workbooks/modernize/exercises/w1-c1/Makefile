# modernize/w1-c1 -- ClaimDesk rating export: JDK 8 to JDK 21. Needs JDK 21 + Maven.
SHELL := /bin/bash
TRACK := $(abspath ../..)
JAVA := source "$(TRACK)/_env/java-env.sh" &&

.PHONY: setup test run jdeps clean

setup:       ## check the JDK, download every Maven artifact once (to ~/.m2) so grading runs offline
	@$(JAVA) java -version 2>&1 | head -1
	@bash "$(TRACK)/_env/ensure-maven.sh" "$(CURDIR)"
	@echo "w1-c1 ready. Start with: make test (it will not compile on JDK 21 yet)"

test:        ## visible characterization tests
	@$(JAVA) mvn -q -B test

run:         ## the nightly batch: data/claims-2026-11-12.csv -> target/outbox/*.env
	@$(JAVA) mvn -q -B -DskipTests package && java -cp "target/classes:$$(mvn -q -B dependency:build-classpath -Dmdep.outputFile=/dev/stdout)" com.corvane.claimdesk.rating.Main

jdeps:       ## jdeps over the compiled classes (after it compiles): internal API use and module deps
	@$(JAVA) jdeps --jdk-internals --multi-release 21 -cp "$$(mvn -q -B dependency:build-classpath -Dmdep.outputFile=/dev/stdout)" target/classes || true

clean:
	@rm -rf target
	@echo "w1-c1 clean (~/.m2 cache kept)"
