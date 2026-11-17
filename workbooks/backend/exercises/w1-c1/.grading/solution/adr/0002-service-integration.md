# ADR 0002: How Keystone services integrate

## Status

Accepted for phase 1.

## Context

Accounts, pipeline, activities and automation are owned by different teams and deploy independently.
Projections (open pipeline per account), the warehouse feed and notifications need changes from all of
them. Writes to a database and a broker are two systems; one of them will fail.

## Options

1. Synchronous APIs only. Simple, consistent reads, but every consumer couples to the writer's uptime
   and latency, and fan-out (warehouse, projections) becomes polling.
2. Events through a transactional outbox, relayed to Kafka. The event row commits with the change, so
   no dual write; consumers are at-least-once and must be idempotent; ordering per account key.
3. Shared database. Fast to start, but it recreates the CRM: no ownership, schema changes break
   unknown readers.
4. CDC from each service's database (Debezium on the WAL). No outbox code, but it publishes table
   shapes instead of domain events unless combined with an outbox table and the outbox router.

## Decision

APIs for queries and commands that need an answer now; domain events through a transactional outbox
(option 2) for state changes, relayed by polling in phase 1 and by Debezium's outbox router once volume
or latency needs it. Shared tables are not allowed.

## Consequences

- Consumers keep a processed-event table (or are naturally idempotent) and tolerate duplicates.
- Read models are eventually consistent; the lag is an SLO and is shown where users can see stale data.
- Event schemas are versioned and backward compatible; a schema registry check runs in CI.
- One more moving part (the relay) to operate, with metrics on outbox age.
