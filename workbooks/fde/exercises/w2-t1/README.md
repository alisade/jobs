# fde/w2-t1 - MCP gateway intermittently 401s after a JWKS rotation

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 2 (Wed: JWT / JWKS verification, Thu: latency budgets and fail policy), Week 4 (Mon-Tue: Managed Agents gateway variant)

## The page

> **PagerDuty - SEV2 - edge-mcp-gateway: 401 rate 48% (threshold 2%)**
> Triggered 09:12 UTC. Service: edge-mcp-gateway (prod, 1 task).
>
> **#shopping-agent-oncall, 09:15** - Support: "About half of customers on the hosted
> shopping agent get 'I can't reach the store right now' on their first message. If they
> start a new chat it sometimes works. Customers who were already mid-conversation are
> fine."
>
> **09:18** - IdP team: "Heads up, monthly signing-key rollover for login.northwind.example
> started at 09:10 per the runbook. Staged: half of new tokens on the new key for the first
> day. JWKS has published both keys since 09:10. No errors on our side."
>
> **09:20** - Platform: "Gateway config hasn't changed in weeks (last change PLAT-2291).
> Seeing a lot of 'issuer clock ahead' warnings too, maybe NTP?"

You are the FDE on call. Find the root cause, fix it so the gateway follows key rotations
**without a restart**, and leave evidence a reviewer can check.

## The system (local)

`make setup` starts three processes and replays the morning:

| Process | Port | What it is |
|---|---|---|
| fake IdP | 18210 | JWKS at `/.well-known/jwks.json`, tokens at `POST /oauth/token`, `GET /admin/state` |
| edge-mcp-gateway | 18211 | `POST /mcp` verifies the bearer token, then proxies; `GET /debug/jwks`, `GET /healthz` |
| upstream MCP stub | 18212 | stands in for the storefront MCP server |

The gateway was started, then the IdP began its rollover (`POST /admin/rotate`), then one
probe ran (`run/probe-at-setup.txt`). Logs: `run/gateway.log`, `run/idp.log`.
Gateway code: `gateway/`, config: `gateway.env`.

Useful commands:

```bash
make probe                                   # 40 synthetic sessions, 401 rate by kid
curl -s localhost:18210/.well-known/jwks.json | jq '.keys[].kid'
curl -s localhost:18211/debug/jwks
make restart                                 # restart only the gateway (after a fix)
make status
```

Restarting the gateway makes the symptom go away for a while. That is a workaround, not a
fix: the next rollover is in 30 days and nobody will remember.

## Acceptance criteria

- `ANSWER.md` names the root cause precisely (file, setting, code path) with evidence:
  commands you ran and output excerpts that rule causes in and out, including the
  "issuer clock ahead" warnings.
- After your fix, a gateway that was started **before** a rotation accepts new-kid tokens
  within a bounded time and without a restart, while the old kid keeps working.
- Callers sending random `kid` values still cannot make the gateway hammer the IdP
  (security requirement SEC-114, quoted in `gateway.env`).
- Token verification is not loosened anywhere (signature, `aud`, `iss`, `exp`, leeway).
- The gateway refuses to start with the misconfiguration that caused this (guard against
  recurrence), with an error message an operator can act on.
- `make test` passes (it checks the fixed state in-process, independent of the running
  processes).

## How to run

```bash
make setup     # venv, start the three processes, replay the rollover, one probe
make probe     # reproduce the page
make test      # in-process checks of the fixed state (fail until you fix it)
# from workbooks/: /grade fde/w2-t1
make clean     # stops all three processes and removes run/
```

## What to submit

Your changes under `gateway/` and `gateway.env`, and `ANSWER.md` with Approach, Root cause
(with evidence), Fix (and how you verified it, ideally by showing the live gateway
recovering without `make restart`), and Trade-offs.
