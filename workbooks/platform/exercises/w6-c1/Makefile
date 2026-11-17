# platform/w6-c1 -- plan-gate: a Terraform plan JSON gate for CI (Go, stdlib only)
SHELL := /bin/bash

.PHONY: setup test clean

setup:       ## build once (no modules to download)
	@go build ./...
	@echo "w6-c1 ready: edit gate/*.go, then make test"

test:        ## visible tests (the hidden ones run under /grade)
	@go test -race -count=1 ./...

clean:
	@go clean -testcache
	@echo "w6-c1 clean"

.PHONY: run
run:         ## make run PLAN=testdata/import-batch-07-replace.plan.json POLICY=testdata/policy-migration.json [ARGS=-json]
	@go run ./cmd/plan-gate -plan $(PLAN) $(if $(POLICY),-policy $(POLICY),) $(ARGS); echo "exit $$?"
