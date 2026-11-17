# javaai/w3-c1 -- quiz generation with Gemini structured output (Java 21, Jackson, JUnit 5). Needs JDK 21 + Maven.
SHELL := /bin/bash
TRACK := $(abspath ../..)
JAVA := source "$(TRACK)/_env/java-env.sh" &&

.PHONY: setup test clean

setup:       ## check the JDK and download every Maven artifact once (to ~/.m2) so grading runs offline
	@$(JAVA) java -version 2>&1 | head -1
	@$(JAVA) mvn -q -B -Dmaven.test.failure.ignore=true test >/dev/null 2>&1 || true
	@echo "w3-c1 ready. Edit QuizSchema, QuizValidator and QuizGenerator, then: make test"

test:
	@$(JAVA) mvn -q -B test


clean:
	@rm -rf target
	@echo "w3-c1 clean (~/.m2 cache kept)"
