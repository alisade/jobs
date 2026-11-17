# Design: Kestrel course tutor - bounded contexts, data and service boundaries

<!-- Audience: architects and the product lead. 5-8 pages equivalent. Use inputs/. Diagrams in
```text or ```mermaid. Be concrete: name tables, events, modules and owners. -->

## Ubiquitous language

<!-- The terms that mean different things to different people today ("lesson", "attempt", "progress",
"mastery", "course run") and the definition each context uses. -->

## Bounded contexts and context map

<!-- Contexts (for example Catalog, Authoring, Learning, Tutoring, Identity/Tenancy, Analytics), what each
owns, and the relationships (customer/supplier, conformist, anti-corruption layer). Diagram. -->

## Aggregates and invariants

<!-- For each core context: aggregates, their roots, the invariants enforced in one transaction, and
what is eventually consistent. Include the draft-vs-published quiz item problem. -->

## Write ownership and integration

<!-- Who owns which writes. Sync API vs events (Pub/Sub, transactional outbox) per interaction; what
happens when the other side is down; idempotency. Where the Python services fit. -->

## Deployment boundaries

<!-- What stays in the modular monolith (Spring Modulith modules, enforced dependencies), what is a separate
service and why (runtime, scaling, failure mode, ownership). How you will say no to the next microservice. -->

## Relational schema for the core contexts

<!-- Tables with keys, FKs, unique and check constraints, and the indexes justified by named queries.
Schema per context (PostgreSQL schemas) or not, and why. -->

## Quiz attempts at scale and analytics

<!-- Partitioning plan (key, granularity, retention), what goes to BigQuery and how (CDC or events), the
read replica's role, the 4-year academic retention. -->

## Tenancy, privacy and retention

<!-- University tenancy model (tenant_id, row-level security or schema per tenant), per-tenant export,
learner deletion, 180-day transcript retention, what the agent may store. -->

## Migration path

<!-- Steps from today's tangle without a rewrite: module boundaries first, expand-and-contract schema moves,
outbox, strangler for quiz drafts. Risks and how you will know each step worked. -->
