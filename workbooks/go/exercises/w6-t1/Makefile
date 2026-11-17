# go/w6-t1 kb-retriever: search_kb timeouts after the KB backfill
SHELL := /usr/bin/env bash

.PHONY: setup test clean

setup: ## build the service code and show the page
	go mod download
	go build ./...
	@echo
	@cat artifacts/PAGER.md
	@echo
	@echo "setup ok: evidence is in artifacts/, code in retrieval/, schema in migrations/"

test: ## visible tests: replays the production query against a model of the planner
	go test -count=1 -v ./...

clean:
	go clean -testcache
