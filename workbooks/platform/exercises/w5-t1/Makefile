# platform/w5-t1 -- the RIQ burn-rate alert never fired. Uses the shared venv platform/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python
RULES ?= rules/riq-slo.rules.yaml
TSDB ?= incident/tsdb-2026-11-04.json
AT ?= 2026-11-04T13:30:00Z

.PHONY: setup alerts query test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} tools/gen_tsdb.py incident ${TSDB}
	@echo "w5-t1 ready. Start with artifacts/PAGE.txt, then: make alerts / make query Q='...'"

alerts:      ## replay the rule file over the incident TSDB: make alerts [RULES=...] [TSDB=...]
	@${PY} tools/eval_rules.py --rules ${RULES} --tsdb ${TSDB}

query:       ## instant query: make query Q='sum by (job) (rate(http_requests_total[5m]))' [AT=2026-11-04T13:30:00Z]
	@${PY} tools/eval_rules.py --tsdb ${TSDB} --query '${Q}' --at ${AT}

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w5-t1 clean (shared venv kept)"
