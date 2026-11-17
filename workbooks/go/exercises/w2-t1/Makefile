# go/w2-t1 driftwood log shipper OOMKills
SHELL := /usr/bin/env bash

.PHONY: setup test repro build clean

setup: ## build, then reproduce the incident locally into artifacts/goroutines-live.txt
	go mod download
	go build ./...
	go run ./cmd/repro -out artifacts/goroutines-live.txt -for 3s
	@echo "setup ok: start with artifacts/PAGER.txt"

repro: ## re-run the brownout reproduction after your fix and compare
	go run ./cmd/repro -out artifacts/goroutines-live.txt -for 3s

test: ## visible tests (the hidden ones run under /grade)
	go test -race -count=1 ./...

build:
	go build -o bin/driftwood ./cmd/driftwood

clean:
	rm -rf bin artifacts/goroutines-live.txt
	go clean -testcache
