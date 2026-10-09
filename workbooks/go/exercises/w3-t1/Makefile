# go/w3-t1 tenant-operator (RBAC incident)
SHELL := /usr/bin/env bash
ENVTEST_K8S_VERSION ?= 1.37.0

.PHONY: setup test manifests build clean

setup: ## download modules, envtest binaries (kube-apiserver + etcd), build
	go mod download
	go tool setup-envtest use $(ENVTEST_K8S_VERSION) -p path >/dev/null
	go build ./...
	@echo "setup ok: start with incident/PAGE.md"

manifests: ## regenerate CRDs and config/rbac/role.yaml from the kubebuilder markers
	go tool controller-gen rbac:roleName=manager-role crd paths="./..." \
	  output:crd:artifacts:config=config/crd/bases output:rbac:artifacts:config=config/rbac
	go tool controller-gen object paths="./api/..."

test: ## visible tests: unit + envtest (runs as cluster admin, like CI)
	KUBEBUILDER_ASSETS="$$(go tool setup-envtest use $(ENVTEST_K8S_VERSION) -p path)" \
	  go test -count=1 ./...

build:
	go build -o bin/manager ./cmd

clean:
	rm -rf bin
	go clean -testcache
