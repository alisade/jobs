# ANSWER: connect/w6-c2 After-contact summarization pipeline

## Approach

Started from the failure modes: PII leaking into the model or ServiceNow, duplicate notes on
EventBridge redelivery, and unfaithful summaries. Built redaction and the eval first, then the
Converse contract, retrieval and the handler, testing each against the recorded fixtures.

## Fix

- Deterministic redaction before and after the model (Luhn-checked cards, SSN, email, phone, password).
- Converse: untrusted-data system prompt, forced record_acw_summary tool with a strict schema,
  guardrail with trace, temperature 0; parse to OK / GUARDRAIL_BLOCKED / INVALID_OUTPUT.
- Retrieve with an audience filter and a 0.45 score floor; best effort.
- Handler: claim -> transcript -> redact -> Converse -> validate/redact -> KB -> work note -> attributes
  -> complete; release on any failure; Bedrock and ServiceNow failures are retryable.
- Eval: token-overlap faithfulness, identifier grounding, key-fact coverage.

## Trade-offs / what I would do in production

Use the native generative post-contact summary where a free-text summary in Connect is enough; keep
this pipeline for the ServiceNow format and KB links. Run it as Step Functions (retries, wait for the
analysis file, DLQ). Budget about 1k input / 200 output tokens per contact on a Haiku-class profile
plus guardrail units. Grow the eval to 200 labelled contacts with an LLM-as-judge rubric calibrated
against QA reviewers, gate prompt or model changes on it, and keep model invocation logging with a
short retention in a restricted bucket.
