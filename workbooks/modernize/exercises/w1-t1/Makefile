# modernize/w1-t1 -- the intake batch dies after the JDK 21 release. Needs JDK 21 + Maven.
SHELL := /bin/bash
TRACK := $(abspath ../..)
JAVA := source "$(TRACK)/_env/java-env.sh" &&

.PHONY: setup test run tree clean

setup:       ## check the JDK, download every Maven artifact once (to ~/.m2) so grading runs offline
	@$(JAVA) java -version 2>&1 | head -1
	@bash "$(TRACK)/_env/ensure-maven.sh" "$(CURDIR)"
	@echo "w1-t1 ready. Start with evidence/PAGE.txt, then: make run"

test:        ## visible unit tests (CI ran exactly these)
	@$(JAVA) mvn -q -B test

run:         ## run the nightly intake over inbox/ into target/outbox/
	@$(JAVA) mvn -q -B -DskipTests package && java -cp "target/classes:$$(mvn -q -B dependency:build-classpath -Dmdep.outputFile=/dev/stdout)" com.corvane.claimdesk.intake.IntakeBatch

tree:        ## the resolved dependency tree, with the reasons Maven picked each version
	@$(JAVA) mvn -q -B dependency:tree -Dverbose -DoutputFile=/dev/stdout

clean:
	@rm -rf target
	@echo "w1-t1 clean (~/.m2 cache kept)"
