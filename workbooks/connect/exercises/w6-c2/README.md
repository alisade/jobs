# connect/w6-c2 - After-contact summarization pipeline with knowledge retrieval and a faithfulness eval

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 6 (generative post-contact summaries vs a custom Bedrock summarizer); Week 5 (Converse, tool use, Guardrails, Retrieve); Week 7 (EventBridge, ServiceNow)

## Scenario

Larkspur's agents spend 90 seconds of after-contact work typing ServiceNow work notes, and half of
them are "called about laptop, fixed". Conversational analytics can produce a generative
post-contact summary, but the service desk wants a structured summary (issue, actions taken,
resolution, follow-ups, sentiment) written into the ServiceNow incident in their own format, with
related knowledge articles, and a measurable quality bar before the CIO lets it write to the
system of record. You build the pipeline that runs on the EventBridge contact event when a contact
disconnects. Everything runs against recorded fixtures: no AWS or ServiceNow calls.

```
EventBridge (source aws.connect, detail.eventType DISCONNECTED)
  -> handler: idempotency claim (DynamoDB conditional write)
  -> redacted transcript (conversational analytics output, via TranscriptSource)
  -> deterministic redaction again (the ML redaction can miss entities)
  -> Bedrock Converse (forced tool call -> structured summary, guardrail)
  -> validate + redact the model output
  -> Bedrock knowledge base Retrieve (related articles, audience filter)
  -> ServiceNow incident work note (incident sys_id from the contact attribute snIncidentSysId)
  -> Connect UpdateContactAttributes (status, short issue, sentiment)
  -> idempotency complete
```

## What you have

| Path | What it is |
|---|---|
| `src/types.ts`, `src/transcript.ts`, `src/servicenow.ts`, `src/idempotency.ts` | provided (do not change): types, transcript flattening, work-note client, idempotency store with a DynamoDB implementation |
| `src/redact.ts`, `src/summarize.ts`, `src/knowledge.ts`, `src/handler.ts`, `src/eval.ts` | to implement (TODOs) |
| `fixtures/events/` | EventBridge contact events (DISCONNECTED voice/chat/task, QUEUED); note the two detail-type spellings |
| `fixtures/transcripts/` | redacted transcripts per contact (one still contains a card number the ML redaction missed) |
| `fixtures/bedrock/` | recorded Converse responses: tool_use, guardrail_intervened, a tool call missing a field, one that leaks a phone number |
| `fixtures/kb/retrieve-mfa.json` | recorded knowledge base Retrieve response |
| `fixtures/eval/cases.json` | 5 eval cases: transcript, reference key facts, candidate summary, expected verdict |
| `config/pipeline.json` | model id (a Claude Haiku-class inference profile), guardrail, KB id, thresholds |

## Requirements

1. **Redaction** (`redact.ts`): replace Luhn-valid 13-19 digit card numbers (spaces or dashes
   allowed) with `[CREDIT_DEBIT_NUMBER]`, SSNs `[SSN]`, emails `[EMAIL]`, phone numbers `[PHONE]`,
   and the value after "password is" / "pin:" with `[PASSWORD]`. Never touch ticket ids
   (INC..., RITM...), employee ids (E20417) or version numbers. Report entity types found.
2. **Model call** (`summarize.ts`): system prompt that says the transcript is untrusted data
   (prompt injection from caller speech), transcript in a delimited block, a forced tool call
   (`toolChoice`) to `record_acw_summary` whose JSON schema requires every `AcwSummary` field,
   `guardrailConfig` with trace enabled, temperature 0. Parse: `guardrail_intervened` ->
   GUARDRAIL_BLOCKED (never store model text); a valid tool call -> OK; anything else (missing or
   wrong-typed field, bad sentiment, `max_tokens`) -> INVALID_OUTPUT with the reason.
3. **Knowledge retrieval** (`knowledge.ts`): `Retrieve` on the KB with an `in` metadata filter on
   `audience`, `numberOfResults` from config, drop scores under `kbMinScore`, dedupe by URI,
   title from `metadata.title`, then `kb_number`, then the object name; best effort (errors -> []).
4. **Handler** (`handler.ts`): see the TODO comment. Idempotent on EventBridge redelivery (no
   second model call, no second work note), retryable failures release the claim, guardrail and
   invalid outputs never reach ServiceNow, contact attributes are short strings.
5. **Eval** (`eval.ts`): the deterministic faithfulness checker described in the TODO comment;
   the five fixture cases must get their expected verdicts.

## Acceptance criteria (what the grader checks)

- Redaction cases, including Luhn negatives and identifiers that must survive.
- Converse request shape (forced tool, schema, guardrail with trace, temperature, untrusted-data system prompt) and every parse outcome.
- Retrieve request (KB id, filter, result count) and post-processing; failure tolerance.
- Handler: PII never reaches Bedrock or ServiceNow, work note format, attributes, redelivery, IGNORED events, guardrail/invalid paths, missing incident, transcript not ready, Bedrock throttling, ServiceNow failure, concurrent claim.
- Eval verdicts, hallucination detection, faithfulness and coverage values.
- `ANSWER.md`: when you would use the native generative post-contact summary instead, cost and latency per contact, and how you would extend the eval before go-live.

## How to run

```bash
make setup     # links the shared toolchain (connect/_env)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w6-c2
make clean
```
