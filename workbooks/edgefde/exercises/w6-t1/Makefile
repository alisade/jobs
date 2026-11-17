# edgefde/w6-t1 -- pip and uv fail on the plant build box behind a TLS-inspecting proxy. Uses edgefde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)
PY := ${TRACK}/.venv/bin/python

.PHONY: setup bundle test clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@${PY} scripts/make_incident.py incident
	@echo "w6-t1 ready: read incident/README.txt first. Configs to fix are in site/"

bundle:      ## build the CA bundle from certs/ into run/ca-bundle.pem with your script
	@mkdir -p run
	@CERT_DIR=certs OUT=run/ca-bundle.pem bash site/build-ca-bundle.sh && grep '^# Subject' run/ca-bundle.pem

test:
	@${PY} -m pytest -q -p no:cacheprovider tests

clean:
	@rm -rf incident run .pytest_cache
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w6-t1 clean (shared venv kept)"
