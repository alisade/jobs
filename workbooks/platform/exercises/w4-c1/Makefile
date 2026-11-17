# platform/w4-c1 -- AppDatabase composition function and readiness (Go, stdlib only)
SHELL := /bin/bash

.PHONY: setup test clean

setup:       ## build once (no modules to download)
	@go build ./...
	@echo "w4-c1 ready: edit fn/compose.go and fn/reconcile.go, then make test"

test:        ## visible tests (the hidden ones run under /grade)
	@go test -race -count=1 ./...

clean:
	@go clean -testcache
	@echo "w4-c1 clean"
