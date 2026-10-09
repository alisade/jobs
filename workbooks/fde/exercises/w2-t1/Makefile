# fde/w2-t1 -- MCP gateway 401s after a JWKS rotation. Uses the shared venv at fde/.venv.
# setup starts three local processes (ports 18210-18212), replays the rotation, and runs
# one probe so the logs in run/ show the incident.
SHELL := /bin/bash
FDE := $(abspath ../..)
PY := ${FDE}/.venv/bin/python

.PHONY: setup test probe status restart clean

setup:
	@bash "${FDE}/_env/ensure-venv.sh"
	@mkdir -p run && rm -f run/*.log run/idp-state.json
	@bash scripts/ctl.sh start
	@curl -fsS --max-time 3 -X POST http://127.0.0.1:18210/admin/rotate >/dev/null
	@${PY} scripts/probe.py --n 40 >run/probe-at-setup.txt 2>&1 || true
	@echo "w2-t1 environment is up: IdP :18210, gateway :18211, upstream :18212 (logs in run/)."
	@echo "The page is in README.md. Start with: make probe"

probe:
	@${PY} scripts/probe.py --n 40

status:
	@bash scripts/ctl.sh status

restart:
	@bash scripts/ctl.sh restart-gateway

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@bash scripts/ctl.sh stop
	@rm -rf run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w2-t1 stopped and cleaned (shared venv kept)"
