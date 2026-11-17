# awsfde/ai-t1 - A weekly summary email went to an outside address

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** AI Integration page (4: security; 2: the agent loop; 1: tool design)

## Symptom

Corvid Logistics' mail gateway flagged Monday's automated "Weekly carrier performance summary" from
the Tidewater relay: it went to their ops list and to `ops-archive@example.net`, an address nobody at
Corvid owns or configured. The scheduled job in the Tidewater console lists one recipient and has not
changed since September. The same week, platform rolled the shared guardrail to version 4. Corvid's
security manager wants to know what happened, what left, and how you will guarantee it does not
happen again. Read `evidence/TICKET-5633.txt` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/` | the ticket, the change log for the period, the KB ingestion audit |
| `config/tenants.json` | per-tenant verified email domains and guardrail |
| `assistant/` | this checkout: the job context, the tools, the unattended agent loop (prod code) |
| `sim/` | the environment: a KB over `sim/docs/`, the metrics store, the mail relay, and a scripted stand-in for the model that behaves like a capable but gullible model (it follows instructions it finds in tool results). Treat it as the environment, not the suspect. |
| `replay.py` | replays the three Monday runs (2026-10-27, 11-03, 11-10); `make replay GV=3` repeats them with guardrail version 3 |
| `run/` | created by `make setup`: `agent.log` (model calls, tool calls with arguments, retrieval doc ids), `mail-outbox.jsonl`, `summary.json` |

## Your task

1. Find the root cause and prove it: which content made the model add the recipient, how it got into
   the tenant's documents, and why nothing in the system stopped the send. Name the three conditions
   that had to be true together.
2. Rule the guardrail change in or out with evidence.
3. Fix it in `assistant/` so that no content the model reads can make mail leave the tenant: the
   decision about recipients must be made by the server, not by the model, and a write must be
   approved outside the model. Keep the legitimate weekly send working. Also mark retrieved content
   as untrusted data (useful, but say in `ANSWER.md` why it is not the control).
4. Verify with `make test` and `make replay` (the scripted model will still try to add the address).
5. Write `ANSWER.md`: root cause with evidence, the exposure statement, the fix, and what you would
   change in the product (partner uploads, write tools, monitoring).

## Acceptance criteria (what the grader checks)

- No replayed run sends mail outside the tenant's verified domains, with either guardrail version.
- Mail goes only to recipients that are approved outside the model (job definition or a user
  confirmation) AND on a verified domain; anything else is refused and logged, lookalike domains included.
- Search results carry the retrieved documents marked as untrusted data with their ids.
- The weekly summary still reaches Corvid's ops list; other tenants' jobs and read tools are unchanged.
- `ANSWER.md` names the mechanism (indirect prompt injection plus an unconstrained write tool plus
  auto-execution), backs it with log lines, and rules out the guardrail.

## How to run

```bash
make setup
make test
make replay          # after your fix; make replay GV=3 for the previous guardrail version
# from workbooks/: /grade awsfde/ai-t1
make clean
```
