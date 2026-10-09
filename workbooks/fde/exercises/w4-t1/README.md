# fde/w4-t1 - Managed Agents gateway: one customer sees another customer's cart

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 4 (Mon-Tue: Managed Agents gateway variant, Option B signed-claim identity); Week 5 add-on (Wed: advanced asyncio)

## Scenario

Larkspur Home runs the commerce-agents shopping agent on Managed Agents. The hosted agent
reaches the storefront tools through `storefront-gateway`, which you built in week 4: the
Managed Agents vault holds a short-lived signed customer claim, the gateway verifies it on
every request, binds the customer, rate-limits them, and runs the tool through the same
`ShoppingToolExecutor` the blueprint's storefront MCP server uses (one executor per
customer session).

Last night's "Fall Refresh" push produced three tickets where customers saw items in their
cart they never chose (`incident/ticket.txt`). Tier-2 cannot reproduce with one test
account. Platform blames the session-cache TTL change in release 2026.10.07
(`incident/CHANGELOG.txt`). The push repeats tomorrow at 19:00; rolling back the whole
release also reverts the rate limiter.

## What you have

| Path | What |
|---|---|
| `gateway/` | The gateway as deployed (auth, identity, sessions, app) |
| `gateway.env` | Local copy of the prod config |
| `incident/` | The escalation, release notes, a prod log excerpt |
| `scripts/probe.py` | A burst of concurrent customer sessions against the running gateway |
| `tests/` | Visible tests (they fail until the fault is fixed) |

## Task

1. `make setup` (starts the gateway on 127.0.0.1:18410), then `make probe` to reproduce.
2. Find the root cause. Prove it, and rule the TTL change in or out with evidence.
3. Fix it with the smallest change that makes identity correct under any interleaving.
   Keep the `gateway.identity` API (`bind`, `release`, `current_principal`): tool code
   deep in the stack depends on it.
4. Verify: `make test`, then restart and re-probe (`make clean && make setup && make probe`).
5. Write up `ANSWER.md`.

## Acceptance criteria

- Under any number of concurrent customers, every tool call acts for the customer whose
  claim was on that request, and each cart holds only its own customer's items.
- No provenance holds caused by one customer's lookup landing in another's session.
- The bound identity does not outlive its request (outside a request,
  `current_principal()` raises `Unauthenticated`); nested bind/release restores correctly.
- Authentication still rejects missing, forged, and expired claims.
- `ANSWER.md` names the root cause with evidence and explains why one test account never
  reproduces it.

## How to run

```bash
make setup     # shared venv + gateway in the background (pid and log under run/)
make probe     # 100 concurrent tool calls from 5 customers; reports leaks
make logs      # tail the gateway log (audit lines: customer=<digest> session=gw-<digest>)
make test      # visible tests
# from workbooks/: /grade fde/w4-t1
make clean     # stops the gateway, removes run/
```

Ports: 18410 only. Read first: `docs/safety.md` (Identity row), `docs/backends.md` step 1,
`shopping-agent/managed-agents/storefront-mcp-server/README.md` (Identity).

## What to submit

The fixed files and a filled-in `ANSWER.md` (root cause with evidence carries most of the
points).
