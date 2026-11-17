# Design: Keystone platform layer (whiteboard write-up)

<!-- Audience: Keystone engineers and product leads. 4-8 pages equivalent. Use inputs/. Diagrams in
```text or ```mermaid blocks. State assumptions where the inputs are silent, and list what you would
ask the business. -->

## Requirements and non-goals

<!-- Functional requirements (what the platform must provide to product teams and agents), non-functional
requirements with numbers, and explicit non-goals for phase 1. -->

## Estimates

<!-- Back-of-envelope from inputs/volumes.md: storage per entity now and in 3 years, activity write rate
average vs peak, read QPS split, timeline query cost, connection budget. Show the arithmetic. -->

## Core entities and data model

<!-- Accounts, contacts, leads, opportunities, line items, activities, users/owners, custom fields,
legacy CRM ids. Keys, tenancy column, relationships (including the polymorphic WhoId/WhatId), what is
jsonb and why. A small ER sketch. -->

## Service boundaries

<!-- Diagram. Which service owns which tables and why that boundary (data ownership, business capability,
team ownership). How a service gets data it does not own. -->

## Interfaces: APIs, events, workflows, agent tools

<!-- For each capability: synchronous API, event, workflow or agent tool, and why. API style (REST vs
GraphQL read layer), versioning, idempotency, pagination, error format. Event catalog with keys and
ordering needs. Workflow primitives. -->

## Where the CRM's hidden logic goes

<!-- Walk the validation rules, flows, triggers, roll-ups and sharing rules from crm-inventory.md and
give each class a new home: constraint, service code, workflow, projection/read model, or dropped. -->

## Multi-tenancy and access

<!-- Tenant model, isolation mechanism, cross-tenant roles (partner managers), EU residency, how an
agent acting for a user gets exactly that user's access. -->

## Deep dive 1

<!-- Pick the riskiest part (for example the activity timeline at 48 M rows and 90 writes/s, or agent
writes) and go deep: schema, indexes, partitioning, queries, failure modes. -->

## Deep dive 2

<!-- The second riskiest part. -->

## Migration path off the CRM

<!-- Strangler fig per capability, sync direction and source of truth per phase, reconciliation,
rollback, what product teams do in each phase. -->

## Operations

<!-- SLOs, observability across API, outbox, Kafka and workflows, capacity, DR against the RPO/RTO. -->

## Risks and open questions
