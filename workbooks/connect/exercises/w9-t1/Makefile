# connect/w9-t1 -- agent SAML login loop after an Okta migration. Uses the shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle decode attrs test clean

setup:
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@$(MAKE) -s bundle
	@echo "w9-t1 ready. Start with incident/PAGE.txt."

bundle:      ## (re)generate incident/
	@node scripts/make-bundle.js

decode:      ## decode the SAMLResponse captured in the HAR
	@node tools/saml.js decode incident/har-mrios-login.txt

attrs:       ## evaluate the app's attribute statements for config/users-sample.csv
	@node tools/saml.js attrs

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf incident coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w9-t1 clean (shared toolchain kept in connect/_env)"
