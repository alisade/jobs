# go/ai-c1 platform-mcp
SHELL := /usr/bin/env bash

.PHONY: setup test run clean

setup: ## download modules and build once
	go mod download
	go build ./...
	@echo "setup ok: edit platformmcp/server.go"

test: ## visible tests (the hidden ones run under /grade)
	go test -race -count=1 ./...

run: ## local server on :8080 for MCP Inspector (tokens demo-read / demo-write)
	go run ./cmd/platform-mcp

clean:
	rm -rf bin
	go clean -testcache
