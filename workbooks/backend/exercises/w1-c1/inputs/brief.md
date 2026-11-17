# Keystone program brief (v0.3, for the architecture kickoff)

## Why
- The third-party CRM contract renews in 20 months. Renewal pricing is up 38%.
- Business logic is scattered across 140 CRM flows and triggers; nobody can say what happens when an
  opportunity is closed-won without reading all of them.
- Lumenfold wants agentic apps (a sales assistant, a renewals agent) working on customer data, and the
  security team will not allow an agent broad API access to the CRM.

## Who uses it
- About 2,400 internal users: account executives, sales engineers, partner managers, renewals,
  sales ops, finance (read-mostly), support (read-mostly).
- Six business units / apps, which the brief calls tenants: `bu-amer`, `bu-emea`, `bu-apac`,
  `app-partner-portal`, `app-renewals`, `app-support-console`. Today they share one CRM org with
  sharing rules. EMEA data must stay in the EU region for two regulated customers (see open questions).
- Product teams (four of them) will build the apps; Keystone is their paved road.
- Agents: the sales assistant (reads timelines, drafts notes, proposes lead owners) and the renewals
  agent (proposes renewal opportunities and discount approvals).

## What "platform" means here
- Stable, versioned APIs and events other teams build on without asking Keystone for every change.
- Workflow primitives (assign, approve, notify, escalate, sync) product teams reuse.
- A tool surface for agents with scoped permissions and a complete audit trail.
- Self-service onboarding for a new app: a tenant, credentials, quotas, docs.

## Constraints
- Stack: Python and TypeScript services, PostgreSQL, Kafka, Temporal, Kubernetes. Go is allowed for
  platform glue. Everything in Lumenfold's own cloud accounts.
- The CRM stays the source of truth until each capability is cut over. No big-bang migration.
- Finance reads closed-won opportunities nightly into the warehouse; that feed must not break.
- Availability target for the read APIs 99.9%, for writes 99.5% during migration, 99.9% after.

## Open questions (the brief does not answer these)
- Is a tenant a business unit, an app, or both? Can a user belong to two tenants?
- EU residency: whole `bu-emea` tenant, or only two customers' records?
- Who owns the account record when sales and partner teams both edit it?
