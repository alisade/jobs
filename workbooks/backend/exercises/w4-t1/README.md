# backend/w4-t1 - Sales managers see someone else's account names in the pipeline view

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 4 (Thu: GraphQL read layer and DataLoader)

## Scenario

Keystone's pipeline view (and the agent assistant, which uses the same GraphQL read layer) shows each
open opportunity with its account. Since the sprint 44 deploy, sales managers in Americas report seeing
an EMEA customer's name on their own deals; a refresh usually fixes it. An EMEA rep says a renamed
account kept its old name until a pod restarted. Support thinks a CDN is caching responses between
users. Security wants a root cause today, because a cross-tenant read through the agent assistant is a
reportable incident.

## What you have

| Path | What it is |
|---|---|
| `evidence/ticket-SUP-8812.md` | the support ticket, L2 notes and the edge team's reply |
| `evidence/request-log.jsonl`, `evidence/query-log.txt` | request log and outbound calls from one pod |
| `evidence/git-log.txt` | what changed in sprint 44 |
| `src/` | the read layer: `schema.ts` (graphql-js), `context.ts` (per-request context), `server.ts` (POST /graphql handler), `store.ts` (in-memory stand-ins for accounts-svc and pipeline-svc, with a query log) |
| `tests/` | visible tests; `make repro` replays the ticket |

Account ids come from the CRM migration and are unique per tenant only: account `1042` exists in
`bu-emea` and in `bu-amer`.

## Your task

1. Find the root cause and prove it with the evidence and a reproduction. Explain why the CDN theory and
   "a refresh fixes it" do or do not fit.
2. Fix it without bringing back the N+1 that sprint 44 removed.
3. Write `ANSWER.md`: approach, root cause with evidence, fix and verification, and what you would put
   in place (tests, review rules, security follow-up) so it does not happen again.

## Acceptance criteria (what the grader checks)

- Requests from two tenants, sequential or interleaved, each see only their own accounts; every
  accounts-svc call carries the auth of the request whose ids it contains.
- A rename is visible on the next request.
- Still one accounts-svc call per request for the account level.
- `ANSWER.md` names the root cause with evidence; most of the points are for the explanation.

## How to run

```bash
make setup      # links the shared toolchain
make repro      # replays the ticket: an EMEA request, then an AMER request
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/w4-t1
make clean
```
