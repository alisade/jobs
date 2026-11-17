# ANSWER: aiarch/w5-c1

## Approach

| Pattern | Key |
|---|---|
| sessions for a user by time | PK USER#user, SK SESSION#iso#id |
| session by id | GSI1 SESSION#id / META |
| idempotency | PK IDEMP#key, SK IDEMP |
| cost per agent by day | PK COST#agent, SK DAY#date |
| all agents for one day | GSI1 DAY#date / AGENT#agent |
| approval state | PK APPROVAL#id, SK STATE (version attribute) |

One GSI is enough because GSI1 is overloaded for two patterns.

## Fix

Implemented per the README; conditional writes for sessions, idempotency and approvals;
ADD on integer micro-dollars for the ledger. Verified with make test.

## Trade-offs / what I would do in production

- Conversation turns and long-term memory live in AgentCore Memory; Strands agent state in its
  session manager; this table holds the platform's own records that other systems query.
- In production a Stream-triggered Lambda would write the ledger from span records, so agents
  never need write access to cost items.
- A single huge tenant on PK USER#x is fine for sessions; for the per-day cost GSI write volume
  is one item per agent per day. If one key ever runs hot, shard it with a suffix and merge on
  read. Use leading-key IAM conditions (dynamodb:LeadingKeys) for per-tenant access.
