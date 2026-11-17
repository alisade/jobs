# connect/w7-c1 - ServiceNow incident Lambda for the help desk flow

**Type:** coding | **Estimate:** 3 hours | **Study plan:** Week 7 (ServiceNow integration patterns, Customer Profiles, Lambda in flows); Week 1 (Lambda limits)

## Scenario

Larkspur Financial Group's inbound help desk flow calls `lfg-servicenow-incident` (Invoke AWS
Lambda function, synchronous, `STRING_MAP` response) right after the caller picks "hardware or
software problem". The Lambda identifies the caller, tells the flow how many incidents the
employee already has open (agents see it in the screen pop and the flow uses it to offer
"press 1 to hear the status of INC0012345"), and opens a new incident for this call.

The contractor's version passed the demo against the ServiceNow PDI. In the first pilot week
on the shared Larkspur instance it: logged a new OAuth token on every invocation (the
ServiceNow admin flagged 9,000 tokens/day), reported "0 open incidents" for people with 60, threw
on the first `429 Too Many Requests` during the Monday 08:00 peak (Connect took the error branch,
callers heard "technical difficulties"), and opened two or three incidents for one call when
Connect retried the invoke.

## What you have

| Path | What it is |
|---|---|
| `src/handler.ts` | the Lambda: `makeHandler(deps)` (testable) and `handler` (production wiring) |
| `src/servicenow.ts` | the ServiceNow Table API client |
| `events/connect-invoke.json` | a real-shaped Connect `ContactFlowEvent` payload |
| `tests/` | visible tests and the harness: a local fake ServiceNow (`connect-kit` `startFakeServiceNow`: OAuth token endpoint, Table API with `sysparm_query`/`sysparm_fields`/`sysparm_limit`/`sysparm_offset`, `Link` + `X-Total-Count`, fault injection), a mocked Customer Profiles client (aws-sdk-client-mock) and a virtual clock |

## Requirements

Contract with the flow (Parameters in, flat string map out):

- In: `Details.ContactData.ContactId`, `CustomerEndpoint.Address` (E.164), `Details.Parameters.action`
  (`lookup` or `lookupOrCreate`), `shortDescription`, `category`.
- Out (every value a string): `status` (`OK` | `NOT_FOUND` | `AMBIGUOUS` | `DEGRADED` | `BAD_REQUEST`),
  `employeeFound`, `employeeId`, `vip`, `openIncidentCount`, `latestOpenIncident`, `incidentCreated`,
  `incidentNumber`, `incidentSysId`.

Behavior:

1. Validate the caller number (E.164) before calling anything; `BAD_REQUEST` otherwise.
2. Customer Profiles `SearchProfiles` on key `_phone`. LFG stores the employee number in
   `AccountNumber`. No match: `NOT_FOUND`. More than one (shared desk phones): `AMBIGUOUS`, create nothing.
3. ServiceNow `sys_user` by `employee_number` AND `active=true` (`sysparm_query`), asking only for the
   fields you need (`sysparm_fields`). Values placed into an encoded query must not be able to add clauses.
4. Open incidents for that `caller_id` (`active=true`, newest first), following pagination until the
   last page. `openIncidentCount` counts all of them.
5. `lookupOrCreate`: if an open incident already has `correlation_id == ContactId`, return it
   (`incidentCreated=false`); otherwise create one with `caller_id`, `short_description` (max 160
   chars), `category`, `contact_type=phone`, `correlation_id=ContactId`, `correlation_display=AmazonConnect`.
6. OAuth 2.0 client credentials (form body, never the query string). Cache the token across warm
   invocations and refresh it 60 s before expiry. On `401`, refresh once and retry the request.
7. `429`: honor `Retry-After`, at most 3 retries, and never wait past the invocation budget (default
   6.5 s, under Connect's 8 s synchronous limit). Budget exhausted, 5xx, or any ServiceNow error:
   return `status=DEGRADED` as a flat map; never throw into the flow.

## Acceptance criteria (what the grader checks)

- Flat `STRING_MAP` output in every outcome, including errors.
- Customer Profiles search shape; NOT_FOUND / AMBIGUOUS / BAD_REQUEST paths create nothing.
- `sysparm_query` filters and `sysparm_fields` on every read; injection neutralized.
- Pagination via `Link rel="next"`; the idempotency guard works when the match is on the last page.
- Exactly one incident per contact across repeated invocations.
- Token cached and reused; refreshed before expiry and after a 401; credentials in the body.
- 429 handling: waits as told when it fits, degrades when it does not, bounded retries, total waits under budget.
- `ANSWER.md`: how this behaves at the Monday peak, and what you would change for production.

## How to run

```bash
make setup     # links the shared toolchain (first run installs it once)
make test      # visible tests (fake ServiceNow on 127.0.0.1, random port)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w7-c1
make clean
```

Notes: ServiceNow added the OAuth `client_credentials` grant for inbound REST in the Washington DC
release; it is off by default and must be enabled by an admin. Older instances use password grant or Basic auth.
`correlation_id` is a standard task field intended for integration ids.
