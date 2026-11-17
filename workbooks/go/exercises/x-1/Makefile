# go/x-1 labelgate CPU and p99 regression
SHELL := /usr/bin/env bash

.PHONY: setup profile test bench build clean

setup: ## build and capture real CPU + heap profiles of the current code into artifacts/
	go mod download
	go build ./...
	go run ./cmd/loadprofile -for 6s -cpu artifacts/cpu.pprof -heap artifacts/heap.pprof
	@echo "setup ok: start with artifacts/PAGER.txt, then: go tool pprof -top -cum artifacts/cpu.pprof"

profile: ## re-capture profiles after a change (writes artifacts/cpu-after.pprof, heap-after.pprof)
	go run ./cmd/loadprofile -for 6s -cpu artifacts/cpu-after.pprof -heap artifacts/heap-after.pprof

test: ## visible tests (the hidden ones run under /grade)
	go test -race -count=1 ./...

bench:
	go test -run XXX -bench . -benchmem ./router

build:
	go build -o bin/labelgate ./cmd/labelgate

clean:
	rm -rf bin artifacts/*.pprof
	go clean -testcache
