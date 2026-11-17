# go/w3-c1 config-reloader
SHELL := /usr/bin/env bash

.PHONY: setup test build clean

setup: ## download modules and build once
	go mod download
	go build ./...
	@echo "setup ok: edit reloader/controller.go"

test: ## visible tests (the hidden ones run under /grade)
	go test -race -count=1 ./...

build:
	go build -o bin/config-reloader ./cmd/config-reloader

clean:
	rm -rf bin
	go clean -testcache
