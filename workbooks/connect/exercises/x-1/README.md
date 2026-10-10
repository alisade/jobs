# connect/x-1 - Duplicate ServiceNow incidents from the phone channel

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 10 add-on (integration resilience drills); Week 7 (ServiceNow integration patterns)

## Symptom

Since Monday the Larkspur Service Desk sees pairs of identical incidents created by the
`connect.integration` user for the same call: same caller, same short description, created a
few seconds apart. Agents work one, the other breaches its SLA. It does not happen on every call
and "seems worse in the morning". Integration on-call wants a ServiceNow business rule that
deletes the second incident. Read `incident/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `incident/` (created by `make setup`) | problem record, Lambda logs, flow log lines, ServiceNow incident export and transaction times, per-contact timings |
| `src/handler.ts` | `lfg-create-incident`, invoked by the inbound flow after the bot collects the issue |
| `src/servicenow.ts` | the shared ServiceNow Table API client (OAuth client credentials, retries) |
| `src/idempotency.ts` | an idempotency-record store another team wrote (in-memory and DynamoDB) |
| `config/lambda.env` | prod configuration |

The tests run against `connect-kit`'s local fake ServiceNow (OAuth token endpoint, Table API,
`sysparm_query`, injectable 429s, latency and "commit then 504" failures).

## Your task

1. Find the root cause and prove it with evidence: why duplicates happen, why only some calls,
   why mornings. Rule the "Connect invokes the Lambda twice" theory in or out with evidence.
2. Fix it in the Lambda so that one contact produces at most one incident, whatever happens on
   the wire, including Connect re-invoking the function and two invocations racing. Keep the
   flat string map contract (`incidentNumber`, `incidentSysId`, `created`, `error`).
3. Do not "fix" it by deleting duplicates in ServiceNow or by turning retries off and losing
   incidents.
4. Write `ANSWER.md`: Approach, Root cause (with commands and excerpts), Fix (and how you
   verified it), Trade-offs / production follow-ups.

## Acceptance criteria (what the grader checks)

- A create that commits in ServiceNow but answers 504 (or times out) yields exactly one
  incident, and the handler returns that incident's number (with and without the idempotency store).
- A 504 that did not commit, and a 429, still end with exactly one incident.
- A sequential re-invoke for the same contact returns the same incident and creates nothing;
  two concurrent invocations for one contact create one incident.
- `DynamoIdempotencyStore.claim` is a conditional put with a TTL and reports a lost race.
- Non-retryable errors create nothing; the result stays a flat string map.
- `ANSWER.md` names the mechanism with evidence; a passing test suite with a hand-waved
  explanation does not pass.

## How to run

```bash
make setup      # links the shared toolchain, generates incident/
make test       # visible tests (they pass on the starter: the bug needs the right failure to show)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/x-1
make clean
```
