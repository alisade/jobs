# go/ai-t1 agent-runtime cannot call the k8s-tools MCP server (403 RBAC: access denied)
SHELL := /usr/bin/env bash

.PHONY: setup test check clean

setup: ## download modules, build the mesh model, show the page
	go mod download
	go build ./...
	@echo
	@cat artifacts/PAGER.md
	@echo
	@echo "setup ok: evidence in artifacts/, desired state in manifests/ (what ArgoCD applies)"

test: ## visible tests + the call matrix from the offline mesh model
	@rc=0; go test -count=1 -v ./... || rc=$$?; echo; $(MAKE) --no-print-directory check; exit $${rc}

check: ## print what the k8s-tools sidecar would do for each caller
	go run ./cmd/meshcheck

clean:
	go clean -testcache
