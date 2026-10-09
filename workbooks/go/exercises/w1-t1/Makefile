# go/w1-t1 flagd: every PUT returns 500
SHELL := /usr/bin/env bash
ADDR ?= 127.0.0.1:8088

.PHONY: setup test run repro clean

setup: ## download modules, build the broken v1.14.0 binary, list the evidence
	go mod download
	go build -o bin/flagd ./cmd/flagd
	@echo "setup ok: bin/flagd built (v1.14.0). Evidence is in artifacts/:"
	@ls -1 artifacts
	@echo "Reproduce locally: 'make run' in one terminal, 'make repro' in another."

test: ## visible tests (shows the symptom until fixed)
	go test -race -count=1 ./...

run: ## run flagd in the foreground with debug logging
	go run ./cmd/flagd -addr $(ADDR)

repro: ## send the on-call engineer's requests to a running flagd
	@echo '--- valid PUT'; curl -s -i -X PUT http://$(ADDR)/v1/flags/checkout-v2 \
	  -d '{"owner":"payments@corvidpay.example","env":"prod","enabled":true,"rollout":10}'; echo
	@echo '--- invalid PUT'; curl -s -i -X PUT http://$(ADDR)/v1/flags/Promo_2026 \
	  -d '{"owner":"growth","env":"qa","rollout":120}'; echo

clean:
	rm -rf bin
	go clean -testcache
