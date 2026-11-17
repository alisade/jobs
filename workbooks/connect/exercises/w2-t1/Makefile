# connect/w2-t1 -- service level dropped after a routing change. Uses the shared toolchain in connect/_env.
SHELL := /bin/bash
CONNECT := $(abspath ../..)

.PHONY: setup bundle replay test clean

setup: bundle
	@bash "${CONNECT}/_env/ensure-node.sh" link "$(CURDIR)"
	@echo "w2-t1 ready. Start with incident/PAGE.txt"

bundle:      ## (re)generate the incident bundle into incident/
	@node scripts/make-bundle.js

replay:      ## replay the week of 2026-10-05 with the routing profiles in config/ (after your fix)
	@node -e 'const s=require("./tools/scenario"); const p=require("./config/routing-profiles.json"), u=require("./config/users.json"); const w=s.replayWeek(p,u,"after"); for (const [q,v] of Object.entries(w)) console.log(q.padEnd(18), "SL", (100*v.serviceLevel).toFixed(1)+"%", " abandon", (100*v.abandonRate).toFixed(1)+"%", " ASA", v.asaSeconds.toFixed(1)+"s"); for (const d of s.DAYS.filter(x=>x.phase==="after")) { const r=s.replayDay(p,u,d); console.log(d.date, Object.entries(r.queues).map(([q,v])=>q.replace("q-","")+" "+(100*v.serviceLevel).toFixed(0)+"%").join("  ")); }'

test:
	@"${CONNECT}/_env/node_modules/.bin/jest" --ci

clean:
	@rm -rf incident coverage
	@if [ -L node_modules ]; then rm node_modules; fi
	@echo "w2-t1 clean (shared toolchain kept in connect/_env)"
