# Reference: backend/w1-c1 Whiteboard write-up: the Keystone platform layer

A model answer is in `.grading/solution/` (DESIGN.md, adr/, ANSWER.md). It is one defensible design,
not the only one. What a strong answer has in common:

1. **Numbers that decide things.** Activities are the only big table (about 58 GB of heap now, about
   150 GB with indexes in three years). That single estimate justifies monthly partitions, a keyset
   index for the timeline, and keeping accounts/contacts in a plain table. The average activity write
   rate (0.4/s) vs the peak (90/s) says the write path is easy and the read path (1,800 rps, 60% from the
   support console) is where caching and replicas matter.
2. **Boundaries by ownership.** Accounts + contacts, pipeline (opportunities, line items, contact
   roles), activities (timeline), automation (workflows), agent gateway (MCP tools). Each owns its
   tables and publishes events through an outbox. Read models (for example open pipeline per account)
   are built from events, not by joining across services.
3. **Hidden logic made explicit.** The inventory is the real requirements document: validation rules
   become constraints and service checks, flows become Temporal workflows, roll-ups become projections
   updated from events, sharing rules become RLS plus an explicit cross-tenant partner role.
4. **Agents get no more than the user.** Delegated identity flows to the database so RLS applies; tool
   writes are idempotent; risky writes (assignments, discounts) start a workflow with an approval.
5. **Migration as a product.** Strangler fig per capability, CDC from the CRM into Keystone while the
   CRM is the source of truth, reconciliation reports as a gate for each cutover, and a written rollback.

## Interview angles
- "Why not one service with a well-structured schema?" (Answer with team ownership, deploy
  independence and blast radius; concede that a modular monolith is a valid phase-1 choice if the
  team is small, as long as table ownership is enforced.)
- "Your timeline query at 400,000 activities on one account: what is the plan?"
- "Partner managers see partner accounts across tenants. How does RLS express that without a bypass?"
- "What breaks first when the agent traffic forecast is wrong by 10x?"
