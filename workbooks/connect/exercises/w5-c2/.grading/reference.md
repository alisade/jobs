# Reference: connect/w5-c2

Reference: `.grading/solution/src/rag.ts` and `.grading/solution/src/handler.ts`.

- Authorization lives in the retrieval filter built from contact attributes that the flow set
  from a server-side lookup. The model never sees content the caller may not see, so prompt
  injection cannot leak it. Deny by default: unverified callers get `public-help` only.
- Retrieve + Converse instead of RetrieveAndGenerate: own prompt, own citation format, own
  guardrail placement, per-step timeouts; and RetrieveAndGenerate is not available on Bedrock
  Managed Knowledge Bases (use Retrieve or AgenticRetrieveStream there).
- Contextual grounding needs the sources marked `grounding_source` and the question `query`
  in `guardContent`; the trace tells you which policy fired (`contextualGroundingPolicy`,
  `contentPolicy` PROMPT_ATTACK, `sensitiveInformationPolicy`) for analytics.
- Citation validation is a cheap deterministic hallucination check: no citation or an
  out-of-range citation is a handoff, not an answer.
- Budget arithmetic example: Connect sync limit 8000 ms; reserve ~1000 ms for Lambda init and
  Connect overhead and ~500 ms margin -> 6500 ms. Retrieve p95 ~600 ms (cap 2000), Converse
  Haiku-class p95 ~1500-2500 ms for 300 tokens. SDK default 3 attempts could triple a slow call:
  maxAttempts 2 at most, and the abort timer is the real guard.
- If p95 does not fit: Connect async Lambda mode (timeout up to 60 s; play a holding prompt,
  Wait, then Load Lambda result), or answer in chat only, or pre-generate answers for top intents.
