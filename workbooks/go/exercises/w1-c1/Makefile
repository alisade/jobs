# go/w1-c1 snapshot-janitor
SHELL := /usr/bin/env bash

.PHONY: setup test build clean

setup: ## download modules and build once
	go mod download
	go build ./...
	@echo "setup ok: edit janitor/janitor.go and cmd/snapshot-janitor/main.go"

test: ## visible tests (the hidden ones run under /grade)
	go test -race -count=1 ./...

build:
	go build -o bin/snapshot-janitor ./cmd/snapshot-janitor

clean:
	rm -rf bin
	go clean -testcache
