# backend/w5-c1 -- Idempotent timeline consumer in Go. Go standard library only (no module downloads).
SHELL := /bin/bash
TRACK := $(abspath ../..)
export GOFLAGS := -mod=mod
export GOPROXY := off

.PHONY: setup test replay clean

setup:
	@go build ./...
	@echo "w5-c1 ready. Edit consumer/consumer.go, then: make test && make replay"

replay:      ## run the consumer over a messy stream and print the timeline
	@go run ./cmd/replay

test:
	@go test -race -count=1 ./...

clean:
	@rm -rf bin
	@go clean -testcache
	@echo "w5-c1 clean"
