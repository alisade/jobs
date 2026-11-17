# go/x-2 registry lookup cache
SHELL := /usr/bin/env bash

.PHONY: setup test bench clean

setup: ## download modules and build once
	go mod download
	go build ./...
	@echo "setup ok: edit ttlcache/cache.go"

test: ## visible tests (the hidden ones run under /grade)
	go test -race -count=1 ./...

bench: ## benchmarks with allocation counts
	go test -run XXX -bench . -benchmem ./ttlcache

clean:
	rm -rf bin
	go clean -testcache
