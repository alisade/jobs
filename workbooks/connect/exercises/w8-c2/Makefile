# connect/w8-c2 -- Java 11 -> 21 Lambda upgrade. Needs JDK 21 + Maven (brew install openjdk@21 maven).
SHELL := /bin/bash
CONNECT := $(abspath ../..)
JAVA := source "${CONNECT}/_env/java-env.sh" &&

.PHONY: setup test package clean

setup:       ## check the JDK, download every Maven artifact once (to ~/.m2) so grading runs offline
	@$(JAVA) java -version 2>&1 | head -1
	@$(JAVA) mvn -q -B test >/dev/null 2>&1 || true
	@$(JAVA) mvn -q -B -f tools/prefetch/pom.xml test >/dev/null
	@rm -rf tools/prefetch/target
	@echo "w8-c2 ready. Upgrade pom.xml, src/ and infra/function.yaml, then: make test"

test:
	@$(JAVA) mvn -q -B test

package:     ## build target/employee-lookup-*.jar
	@$(JAVA) mvn -q -B -DskipTests package

clean:
	@rm -rf target tools/prefetch/target
	@echo "w8-c2 clean (~/.m2 cache kept)"
