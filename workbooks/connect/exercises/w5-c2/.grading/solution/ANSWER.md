# ANSWER: connect/w5-c2 Permission-aware RAG answers inside a voice turn

## Approach

Treated it as a pipeline with a gate after each step: entitlements -> filter -> Retrieve -> score
gate -> Converse with guardrail -> citation gate. Wrote a recorded-response test per gate.

## Fix

Filter from contact attributes only (public-help for unverified; all-workers/all-employees/department
for employees; all-workers/contractors for contractors; region global+own; published). Score threshold
0.45 before the model. Converse with guardContent grounding_source/query, guardrail trace, temperature
0, CANNOT_ANSWER escape. Handoff on guardrail_intervened (policy names in detail), CANNOT_ANSWER,
missing or out-of-range citations. Budget 6500 ms = 8000 sync limit - ~1000 init/overhead - 500
margin; Retrieve capped at 2000 ms, Converse gets the remainder, enforced with a timer +
AbortController; SDK maxAttempts 2.

## Trade-offs / what I would do in production

Async Lambda mode with a holding prompt if Converse p95 does not fit; Managed KB with ServiceNow ACL
crawl to replace hand-maintained audience metadata; restrict model invocation logs (plaintext);
RAG evaluation (faithfulness, citation precision) on a red-team set before go-live; track
containment against CSAT and cost per answered contact.
