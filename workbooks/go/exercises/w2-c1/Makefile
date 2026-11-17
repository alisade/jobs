# go/w2-c1 albstats: ALB access log parser + concurrent aggregator
SHELL := /usr/bin/env bash
FUZZTIME ?= 60s

.PHONY: setup test fuzz run clean

setup: ## download modules and build once
	go mod download
	go build ./...
	@echo "setup ok: edit alblog/parse.go and alblog/aggregate.go"

test: ## visible tests (+ fuzz seeds) with the race detector
	go test -race -count=1 ./...

fuzz: ## actually fuzz the parser (findings land in alblog/testdata/fuzz/)
	go test -run '^$$' -fuzz FuzzParse -fuzztime $(FUZZTIME) ./alblog

run: ## summarise the sample log
	go run ./cmd/albstats -workers 4 testdata/sample.log

clean:
	rm -rf bin
	go clean -testcache -fuzzcache
