# aiarch/w1-t1 -- GitLab release tags cannot assume the prod deploy role (OIDC). Shared venv aiarch/.venv.
SHELL := /bin/bash
AIARCH := $(abspath ../..)
PY := ${AIARCH}/.venv/bin/python

.PHONY: setup bundle test check clean

setup: bundle
	@bash "${AIARCH}/_env/ensure-venv.sh"
	@echo "w1-t1 ready. Start with incident/PAGE.txt."

bundle:      ## (re)generate the incident evidence in incident/
	@python3 scripts/make_bundle.py incident

check:       ## evaluate both recorded tokens against the current trust policies
	@python3 -m oidccheck trust/gitlab-deploy-dev.json incident/claims-main-deploy-dev.json 111100000003
	@python3 -m oidccheck trust/gitlab-deploy-prod.json incident/claims-tag-v2.4.0-deploy-prod.json 111100000004

test:
	@${PY} -m pytest -q tests

clean:
	@rm -rf incident .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w1-t1 clean (shared venv kept)"
