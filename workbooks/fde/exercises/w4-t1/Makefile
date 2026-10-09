# fde/w4-t1 -- gateway identity bleed. Uses the shared venv at fde/.venv.
SHELL := /bin/bash
FDE := $(abspath ../..)
PY := ${FDE}/.venv/bin/python
PORT := 18410

.PHONY: setup test probe logs clean

setup:
	@bash "${FDE}/_env/ensure-venv.sh"
	@mkdir -p run
	@if [ -f run/gateway.pid ] && kill -0 "$$(cat run/gateway.pid)" 2>/dev/null; then \
	  echo "gateway already running (pid $$(cat run/gateway.pid)) on :${PORT}"; \
	else \
	  nohup ${PY} -m gateway.app >run/gateway.log 2>&1 & echo $$! >run/gateway.pid; \
	  for i in $$(seq 1 50); do \
	    if curl -fsS "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then break; fi; sleep 0.2; \
	  done; \
	  curl -fsS "http://127.0.0.1:${PORT}/healthz" >/dev/null || { echo "gateway did not start; see run/gateway.log"; tail -20 run/gateway.log; exit 1; }; \
	  echo "gateway up on http://127.0.0.1:${PORT} (pid $$(cat run/gateway.pid), log run/gateway.log)"; \
	fi
	@echo "Reproduce the incident: make probe"

probe:
	@${PY} scripts/probe.py || true

logs:
	@tail -40 run/gateway.log

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@if [ -f run/gateway.pid ]; then kill "$$(cat run/gateway.pid)" 2>/dev/null || true; fi
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w4-t1 clean (gateway stopped)"
