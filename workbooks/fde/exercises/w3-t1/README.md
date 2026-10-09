# fde/w3-t1 - Checkout silently allowed during a risk-API brownout

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 3 (Thu: fail policy, logging, outcomes), Week 2 (Thu: latency budgets and fail-open vs fail-closed)

## Scenario

Northwind Outfitters runs the commerce-agents retail vertical with `northwind-trust`, its
agent-trust layer: an `AgentTrustMixin` in front of the storefront backend that calls
Halyard Risk on every cart write and at checkout, behind a 150/400 ms budget and a circuit
breaker. The trust team's matrix says cart writes fail open and **checkout fails closed**.

On Monday 2026-10-06 Halyard had a 43-minute brownout. On Tuesday fraud-ops paged: 37
chargebacks on shopping-agent orders from that window, all with no risk decision attached.
The previous brownout (2026-09-28) cost nothing. Release 1.4.0 shipped in between.

You are the forward-deployed engineer on the call. Find out why checkouts went through,
whether it can happen again right now, and fix it.

## What you have

After `make setup`:

| Path | What it is |
|---|---|
| `run/incident/PAGE.txt` | the page, as fraud-ops and on-call wrote it |
| `run/incident/decisions-2026-10-06.jsonl` | decision log during the incident (1.4.0) |
| `run/incident/decisions-2026-09-28.jsonl` | decision log during the previous brownout (1.3.2) |
| `run/incident/halyard-risk-latency-2026-10-06.csv` | risk API latency, errors, client breaker state per minute |
| `run/incident/fraud-ops-chargebacks-2026-10.csv` | the chargeback export |
| `deploy/trust.env` | the config deployed as the pod's environment |
| `deploy/release-1.4.0.diff` | the 1.4.0 release |
| `northwind_trust/` | the deployed package (policy, breaker, mixin, wiring) |
| `make replay` | replays a brownout locally against `deploy/trust.env` |

Useful: `jq` over the JSONL (e.g. group checkout outcomes by `error` and `policy`), and a
diff of what the two brownouts logged for the same hook.

## Task

1. Find the root cause and prove it with evidence from the bundle and the code.
2. Fix it so the deployed config means what it says, and so a bad value can never again
   silently pick a fail mode.
3. Fill in `ANSWER.md` (Approach, Root cause with evidence, Fix with verification,
   Trade-offs).

## Acceptance criteria

- With `deploy/trust.env` as deployed, a checkout whose risk call times out, errors, or
  hits an open breaker returns an error result and renders no checkout card.
- Cart writes still proceed (fail open) when the risk API is slow.
- Boolean settings accept `true/false`, `1/0`, `yes/no`, case-insensitive and trimmed.
- An unrecognised value (`ture`, `2`, `disabled`) stops the backend from building at
  startup with a clear error; unset settings keep the documented defaults.
- A deployment that deliberately sets checkout to fail open still gets fail-open.
- `ANSWER.md` names the root cause precisely, shows the evidence, and explains why the
  brownout, the breaker change and the dependency bumps are not the cause.

## How to run

```bash
make setup     # shared venv + incident bundle in run/incident/
make replay    # reproduce: what the model reads at checkout during a brownout
make test      # visible tests
# from workbooks/: /grade fde/w3-t1
make clean
```

## What to submit

Your fix in `northwind_trust/` (and `deploy/` if you change it) plus `ANSWER.md`.
