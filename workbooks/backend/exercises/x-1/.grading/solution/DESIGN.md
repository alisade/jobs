# Whiteboard: self-serve workflow automation on Keystone

## Requirements and non-goals

Questions asked first: how many teams (4, 10 in two years), what triggers (mostly events, some
schedules), how long do waits last (days; 48 h escalation), do agents start automations (yes).

Requirements: product teams build automations without platform tickets; event, schedule and API
triggers; human approvals with timers; retries and idempotent side effects; per-tenant isolation;
audit of who started and who approved what; versioning while executions are in flight.
Non-goals: a visual flow designer in phase 1, a general rules engine, running non-Keystone workloads.

## Estimates

- Stage changes 9,000 a day, about 0.3/s average, bursts of maybe 20/s after bulk updates. Activities
  1.1 M a month (0.4/s); only a fraction trigger workflows. Start rate is low; Temporal is far from its
  limits, so the risk is runaway loops, not capacity.
- Open executions: about 180,000 renewals waiting on timers (cheap, durable timers) plus a few thousand
  approvals. Histories stay small (tens of events) except long-lived ones, which continue-as-new.

## API (what a product team calls)

```text
POST /v1/automations/{type}/executions       start (Idempotency-Key, typed input, on-behalf-of user)
POST /v1/executions/{id}/signals/{name}      e.g. approve / reject (authz: approver role)
GET  /v1/executions/{id}                     status (query + search attributes)
POST /v1/executions/{id}:cancel
POST /v1/triggers                            {event_type, filter, automation_type, input_mapping}
GET  /v1/automations                         catalog of primitives and team-owned types, with schemas
```

## Data model

- Trigger registry (Postgres, owned by the automation service): trigger id, tenant, event type, filter,
  automation type and version, rate limit, enabled flag, owning team.
- Automation catalog: type, owner team, input/output JSON schema, task queue, default retry policy.
- Execution state lives in Temporal (history + search attributes: tenant, entity id, state, owner team);
  the service keeps no shadow copy.

## High-level design

```text
domain services --outbox--> Kafka --> trigger service --start (wf id = event id)--> Temporal
                                          |  rate limits, kill switch                  |
 product UI / API callers --> automation API --------------------------------------> Temporal
 agent gateway (MCP) ------> automation API (delegated identity)                       |
                                                                                       v
          platform workers (primitives: assign, approve, escalate, notify, scheduled create, sync)
          team workers (team-owned workflow code, own task queue, platform SDK wrapper)
                     | activities call domain APIs with idempotency keys and the user's identity
                     v
          accounts-svc, pipeline-svc, notifications ...
```

- Namespace per environment, task queue per team; workers per team so one team's bad deploy cannot
  starve the others. The platform SDK wrapper sets default timeouts and retry policies, injects tracing
  and passes the on-behalf-of identity into activity headers.

## Deep dive 1: approvals

Approve primitive: input (subject, approver rule, escalation policy). Waits for an `approve`/`reject`
update with a validator (approver must match the rule), a 48 h timer escalates to the next approver,
a final timer auto-rejects with a reason. Every decision is written to the audit log by an activity.

## Deep dive 2: triggers

The trigger service is a Kafka consumer group. For each event it evaluates the registered triggers for
that tenant and event type and starts workflows with `workflow_id = <trigger_id>:<event_id>`, so a
redelivered event cannot start a second execution. Offsets commit after the start call succeeds.
Rate limits per trigger and per tenant (token bucket); over-limit events go to a delay topic, not lost.

## Curveballs

1. Runaway loop: events carry a causation id and a depth counter; the trigger service refuses starts
   whose chain includes the same trigger twice within the chain, and per-trigger rate limits cap the
   damage. Breaching the limit disables the trigger (kill switch), pages the owning team, and notifies
   platform on-call.
2. Changing a workflow with 30,000 waiting executions: use `workflow.patched` markers (or worker
   versioning) so in-flight executions replay the old path and new ones take the new path; CI replays
   recorded production histories against the new code before deploy; remove the patch after the old
   executions finish.
3. Agent: the sales assistant calls a `propose_discount` tool, which starts the approve workflow with
   the user's delegated identity. The agent can query status but has no permission on the approve
   update; the workflow records agent id and on-behalf-of user, and the approver sees "proposed by the
   sales assistant for user X".
4. 20-minute outage: domain events sit in Kafka (and in each service's outbox if Kafka was also
   affected); the trigger service resumes from committed offsets and catches up; idempotent workflow ids
   make any replayed events harmless. Timers that fired during the outage fire when workers return.
