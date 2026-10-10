# Reference: connect/w5-c4

Model answer: `.grading/solution/DESIGN.md`. What separates a strong answer:

- It sizes the business case first: analyst minutes are ~97% of cost per handled contact, so the design
  optimizes containment quality (repeat-contact guard) and context on handoff (60-70 s AHT), and shows
  that token prices barely matter (doubling them adds about a cent per contained contact).
- It uses AI only where it pays: deterministic APIs for resets/unlocks/status, RAG for how-to.
- It is current: Amazon Connect Customer naming, AI agents (formerly Amazon Q in Connect), Bedrock Agents
  Classic closed to new customers, Managed KB ServiceNow connector with ACL crawl, RetrieveAndGenerate not
  on managed KBs, no native Bedrock flow block, sync 8 s / async 60 s Lambda modes.
- Entitlements are enforced in retrieval from authenticated attributes, not in the prompt.
- Evaluation has gates, owners and a rollout mechanism (shadow, percentage split, flags).
- Common misses to deduct for: no handoff contract; containment measured without repeat contacts;
  guardrails mentioned but no grounding sources; global inference profile despite US-only residency;
  invocation logs ignored as a data store; cost model with tokens only.
