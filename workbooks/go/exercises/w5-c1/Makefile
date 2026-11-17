# go/w5-c1 taskbus tracing
SHELL := /usr/bin/env bash

.PHONY: setup test clean

setup: ## download modules and build once (Kafka runs in-process via kfake; no Docker)
	go mod download
	go build ./...
	go vet ./...
	@echo "setup ok: edit tracing/carrier.go and tracing/tracing.go"

test: ## visible tests (the hidden ones run under /grade)
	go test -race -count=1 ./...

clean:
	go clean -testcache
