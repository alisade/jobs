# Reference: connect/w6-c2

Reference code: `.grading/solution/src/`. What a strong solution shows:

- Two redaction layers: conversational analytics redaction is ML-based and the docs warn it can miss
  entities; a deterministic pass (Luhn-checked PAN, SSN, email, phone, password values) before the
  model and on the model output. Keep ids the agent needs (INC, RITM, employee id).
- Structured output by forcing a tool call (`toolChoice: {tool: {name}}`) with a JSON schema, then
  validating anyway: models can still return a wrong type or miss a field.
- Guardrail on the Converse call with `trace: "enabled"`; `stopReason: "guardrail_intervened"` means the
  output is the guardrail's blocked message, never a summary.
- Retrieve with a metadata filter (`in` on audience) and a score floor; titles from metadata. Retrieve
  works on both customer-managed and managed knowledge bases (RetrieveAndGenerate does not support
  managed KBs).
- Idempotency: EventBridge delivers at least once. Claim with a conditional write, skip COMPLETED,
  retry IN_PROGRESS, release on retryable failure, complete only after every write. Do not match the
  detail-type string: AWS docs show both "Amazon Connect Contact Event" and "Connect Customer Contact
  Event" after the rename.
- Native alternative: conversational analytics generative post-contact summaries
  (`SummaryConfiguration.SummaryModes: ["PostContact"]` in UpdateContactRecordingAndAnalyticsBehavior),
  shown in Contact details and the output file `ConversationCharacteristics.ContactSummary`. Use it
  when the free-text summary in Connect is enough; use a custom pipeline when the format, the system
  of record write, KB links or model choice matter. Cost of custom: tokens (about 1k in, 200 out per
  contact with a Haiku-class model), guardrail text units, KB queries; latency is off the agent's path.
