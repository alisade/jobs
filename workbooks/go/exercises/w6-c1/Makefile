# go/w6-c1 triage-agent
SHELL := /usr/bin/env bash

.PHONY: setup test live clean

setup: ## download modules and build once
	go mod download
	go build ./...
	@echo "setup ok: edit agent/agent.go"

test: ## visible tests against the fake Messages API (the hidden ones run under /grade)
	go test -race -count=1 ./...

live: ## OPTIONAL: one run against the real Claude API. Needs ANTHROPIC_API_KEY and costs money. Never run by /grade.
	go run ./cmd/triage

clean:
	rm -rf bin
	go clean -testcache
