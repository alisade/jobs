# Unit prices for the cost model - ILLUSTRATIVE ONLY

These figures are for the exercise. Before using any of them with a client, check the current
AWS pricing pages (Amazon Connect, Amazon Lex, Amazon Bedrock, Bedrock Guardrails) for the
region and the pricing model in force, and state the date you checked.

| Item | Unit | Illustrative price (USD) | Note |
|---|---|---|---|
| Connect voice usage | per minute | 0.038 | AWS pricing page 2026-10 lists Connect Customer channel pricing with AI capabilities included; verify |
| Connect chat usage | per message | 0.010 | same note |
| Inbound toll-free telephony (US) | per minute | 0.0022 | illustrative, check the country/number type |
| Lex V2 speech request | per request | 0.004 | illustrative |
| Lex V2 text request | per request | 0.00075 | illustrative |
| Bedrock model (Haiku-class) input | per 1,000 tokens | 0.001 | illustrative; varies by model and inference profile |
| Bedrock model (Haiku-class) output | per 1,000 tokens | 0.005 | illustrative |
| Knowledge base Retrieve (vector store + embedding of the query) | per request | 0.0004 | illustrative, depends on vector store |
| Bedrock Guardrails (content + sensitive info + grounding) | per 1,000 text units | 0.40 | illustrative; a text unit is up to 1,000 characters |
| Lambda + logging | per contact | 0.0005 | illustrative |
| Analyst time (fully loaded, blended) | per handled minute | 0.85 | from LFG finance |
