# ANSWER: connect/w5-c4 AI-assisted help desk design

## Approach

Started from the drivers and the pilot failure modes (no context on transfer, repetitive prompts),
then sized the business case before choosing technology: labour minutes dominate, so containment
quality and context on handoff matter more than model price.

## Fix

Produced DESIGN.md. Key decisions: (1) deterministic self-service for resets/unlocks/status, RAG only
for how-to; (2) entitlement-filtered Retrieve + Converse with a grounding guardrail and citation
checks inside a 6.5 s voice budget, async mode as the escape hatch; (3) a handoff contract copied to
contact attributes so the workspace and ServiceNow get summary, intent and verified ID; (4) Managed KB
with the ServiceNow connector's ACL crawl as the target, spike in week 2; (5) eval gates (accuracy,
hit@3, faithfulness, zero entitlement leaks, red team) before each percentage step.

## Trade-offs / what I would do in production

Validate first: managed KB ACL crawl against 140 restricted articles, voice p95 under load, and KB
quality. Push back on a big-bang go-live and on measuring containment without repeat-contact joins.
