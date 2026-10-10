# Rubric: connect/w5-c2 Permission-aware RAG answers inside a voice turn
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Authorization design | 15 | Full: filter built only from server-side entitlements, deny-by-default for unverified callers, contractors cannot reach employee content, ANSWER.md explains why prompt instructions are not an access control and how Managed KB ACL crawl (ServiceNow) would change this. Partial: correct filter, no reasoning. Zero: any filter value taken from the question or model output. |
| 3 | Grounding and safety | 15 | Full: guardContent qualifiers, guardrail trace used for the reason, citations validated against provided sources, canned guardrail text never spoken, sources treated as data in the prompt. Partial: guardrail wired but citation checks loose. |
| 4 | Latency engineering | 15 | Full: explicit budget arithmetic (Connect 8 s sync, Lambda cold start, Retrieve p95, model p95, margin), budget enforced with abort, SDK retries sized, ANSWER.md weighs async mode (60 s, Wait + Load Lambda result, holding prompt) and caching. Partial: timeouts present without arithmetic. Zero: relies on Lambda timeout. |
| 5 | ANSWER.md trade-offs | 10 | Full: at least three of: model choice (Haiku-class via inference profile) and cross-region inference, invocation logging contains plaintext (restrict/encrypt), RAG evaluation before go-live (faithfulness, citation quality), containment vs CSAT, cost per answered contact. Partial: generic. |
Total: 100
