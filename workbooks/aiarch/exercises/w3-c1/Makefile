# aiarch/w3-c1 -- Lighthouse runtime + gateway stack in CDK (TypeScript). Synth is offline; nothing is deployed.
SHELL := /bin/bash
AIARCH := $(abspath ../..)

.PHONY: setup test synth clean

setup:
	@bash "${AIARCH}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w3-c1 ready. Edit lib/app.ts, then: make test (make synth ENV=prod TAG=v2.4.0 to print a template)"

synth:       ## print the runtime template: make synth ENV=prod TAG=v2.4.0
	@"${AIARCH}/_env/node_modules/.bin/tsc" --outDir .build --module commonjs --target ES2022 --esModuleInterop --resolveJsonModule --skipLibCheck bin/app.ts
	@cd .build && node -e 'const {App}=require("aws-cdk-lib");const {buildApp}=require("./lib/app");const a=new App({context:{env:process.argv[1],imageTag:process.argv[2]}});const s=buildApp(a);console.log(JSON.stringify(a.synth().getStackByName(s.runtime.stackName).template,null,1))' "${ENV}" "${TAG}"

test:
	@"${AIARCH}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf coverage cdk.out .build
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w3-c1 clean (shared toolchain kept in aiarch/_env)"
