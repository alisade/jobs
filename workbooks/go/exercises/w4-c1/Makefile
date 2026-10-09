# go/w4-c1 agent-fleet-operator: MCPServer reconciler
SHELL := /usr/bin/env bash
ENVTEST_K8S_VERSION ?= 1.37.0

.PHONY: setup test generate manifests run clean

setup: ## download modules, envtest binaries (cached per user), build once
	go mod download
	go tool setup-envtest use $(ENVTEST_K8S_VERSION) -p path >/dev/null
	go build ./...
	@echo "setup ok: edit internal/controller/mcpserver_controller.go"

test: ## visible tests against a real kube-apiserver + etcd (envtest)
	KUBEBUILDER_ASSETS="$$(go tool setup-envtest use $(ENVTEST_K8S_VERSION) -i -p path)" \
	  go test -count=1 ./...

generate: ## deepcopy
	go tool controller-gen object:headerFile=hack/boilerplate.go.txt paths=./api/...

manifests: ## CRD + RBAC from markers
	go tool controller-gen crd rbac:roleName=manager-role paths=./... \
	  output:crd:artifacts:config=config/crd/bases output:rbac:artifacts:config=config/rbac

clean:
	rm -rf bin
	go clean -testcache
