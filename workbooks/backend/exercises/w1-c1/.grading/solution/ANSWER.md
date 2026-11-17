# ANSWER: backend/w1-c1 Whiteboard write-up: the Keystone platform layer

## Approach

Started from the numbers: only activities are large (about 58 GB now, about 150 GB with indexes in three
years), writes are small, reads are dominated by the support console. Then read the CRM inventory as the
real requirements list, because the flows, triggers and roll-ups are what the platform must replace.
Drew boundaries by data ownership and team, checked each against "who else needs this data and how".
Assumed a tenant is a business unit or app and that a user has one home tenant plus roles.

## Fix

1. Shared schema with RLS per region; the EU tenant runs in an EU deployment (ADR 0001).
2. Five boundaries: accounts/contacts, pipeline, activities, automation, agent gateway; no shared tables.
3. Outbox plus Kafka for every state change; read models from events (ADR 0002).
4. Activities partitioned by month with a keyset index; timeline cost independent of account size.
5. Agents act with delegated user identity, tools are task-level, risky writes start an approval workflow.

## Trade-offs / what I would do in production

Left out of phase 1: search over activity bodies (goes to a search index later), GraphQL mutations,
sharding. Before committing I would prototype the timeline query on 50 M synthetic rows and the RLS
plus PgBouncer setup. The first thing to measure is support console read latency through the replica.
