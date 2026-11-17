# ANSWER: javaai/x-1 Domain and data design

## Approach

Started from the six problems in the brief and the constraints (three teams, one database, Python agent,
contract isolation), named the ambiguous terms, then drew contexts around who changes what together.

## Fix

The three decisions to defend first: drafts live in Authoring and never share a table with published items;
one modular monolith with Spring Modulith plus two Python services, with an explicit test for new services;
quiz_attempt partitioned by month with tenant-leading indexes, RLS for tenancy, and BigQuery via CDC for
analytics. Prototype: the outbox relay and RLS performance on the dashboard query.

## Trade-offs / what I would do in production

Not doing: database per service (cost and cross-context reporting) and schema per tenant (12 tenants today,
operational overhead). Revisit schema per tenant if a contract requires separate encryption keys. Biggest
risk: the partition swap of a 41M-row table; rehearse on a clone and do it month by month.
