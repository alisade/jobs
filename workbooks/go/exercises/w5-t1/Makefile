# go/w5-t1 audit-sink rebalance loop
SHELL := /usr/bin/env bash

.PHONY: setup test repro clean

setup: ## download modules, build, and show where the evidence is
	go mod download
	go build ./...
	@echo "setup ok. Start with artifacts/PAGE.md; replay the incident with: make repro"

test: ## visible tests (the hidden ones run under /grade)
	go test -race -count=1 ./...

repro: ## replay the incident: 3 replicas from deploy/audit-sink.yaml against in-process Kafka (~15s)
	go run ./cmd/repro -manifest deploy/audit-sink.yaml

clean:
	go clean -testcache
