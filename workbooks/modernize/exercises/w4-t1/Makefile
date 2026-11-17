# modernize/w4-t1 -- the mainframe rejects September's claims extract. Needs JDK 21 + Maven.
SHELL := /bin/bash
TRACK := $(abspath ../..)
JAVA := source "$(TRACK)/_env/java-env.sh" &&

.PHONY: setup test run clean

setup:       ## check the JDK, download every Maven artifact once (to ~/.m2) so grading runs offline
	@$(JAVA) java -version 2>&1 | head -1
	@bash "$(TRACK)/_env/ensure-maven.sh" "$(CURDIR)"
	@echo "w4-t1 ready. Start with evidence/PAGE.txt"

test:
	@$(JAVA) mvn -q -B test

run:         ## make run MONTH=2025-09 -> target/CLMRECON.2025-09.dat (compare with evidence/)
	@$(JAVA) mvn -q -B -DskipTests package && java -cp target/classes com.corvane.claimdesk.recon.ExtractJob data/paid-losses-$(or $(MONTH),2025-09).csv target/CLMRECON.$(or $(MONTH),2025-09).dat

clean:
	@rm -rf target
	@echo "w4-t1 clean (~/.m2 cache kept)"
