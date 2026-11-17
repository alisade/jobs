# aiarch/w4-t1 - A contractor approved another team's access request

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 4 (Thu: Cedar and Policy in AgentCore)

## Symptom

Security reports that `vk-ext-0042`, a contractor manager for the claims vendor team, approved
a payments access request (AR-1187) through the Lighthouse agent's `approve_access_request`
tool. The gateway's Cedar policy set has a `forbid` for cross-team approvals. The policy engine
moved from LOG_ONLY to ENFORCE an hour before the approval, so on-call believes ENFORCE is not
enforcing and wants to roll back. Read `incident/PAGE.txt` first (created by `make setup`).

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the ticket and on-call notes |
| `incident/policy-decision-log.jsonl` | decisions with mode, input, determining policies and evaluation errors |
| `incident/claims-*.json` | the decoded tokens of the contractor and of a workforce manager |
| `policies/gateway.cedar` | the policy set (edit this) |
| `policies/schema.json` | the Cedar schema generated from the tool definitions (do not change) |
| `authz/engine.py` | local stand-in for Policy in AgentCore with cedarpy: claims to principal, tool call to request (works as shipped) |

## Your task

1. Find the root cause: why did the forbid not stop the approval, and why did LOG_ONLY not
   reveal it? Use the decision log.
2. Fix the policy set with the smallest change. A manager whose token carries no team must not
   be able to approve anything; reads stay as they are; keep every guard rail policy.
3. Make the policy set pass schema validation (`make replay` prints the result) and explain
   why validation would have caught this before ENFORCE.
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix and verification, Trade-offs.
   Say what you think of the rollback-to-LOG_ONLY proposal and the "permits first" theory.

## Acceptance criteria (what the grader checks)

- Decisions for workforce and contractor managers with and without team claims, self-approval,
  employees, auditors and unknown tools.
- Schema validation passes and contractor requests evaluate with no errors.
- Both forbids and all three permits still exist.
- `ANSWER.md` explains that a policy whose evaluation errors is skipped, with the log evidence.

## How to run

```bash
make setup     # evidence bundle + aiarch/.venv (cedarpy)
make replay    # decisions for the visible requests + schema validation
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w4-t1
make clean
```

## What to submit

`policies/gateway.cedar` and `ANSWER.md`.
