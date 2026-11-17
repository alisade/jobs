# connect/w6-c1 - Conversational analytics QA processor with ServiceNow QA tasks

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 6 (Contact Lens / conversational analytics: outputs, rules, redaction, QA; ServiceNow integration)

## Scenario

Larkspur Financial Group's service desk QA team in Charlotte reviews 2% of calls by hand and
misses the ones that matter: an offshore agent in the pilot asked a caller to read out their
password, and nobody saw it for a week. Amazon Connect conversational analytics (formerly
Contact Lens) already writes a post-contact analysis file per contact to S3 and streams
real-time analysis segments to Kinesis. The QA lead wants a nightly processor that turns
those files into per-agent sentiment and compliance KPIs, raises a ServiceNow QA task for
every compliance finding (idempotently: the job is re-run after failures), and a live monitor
that alerts supervisors while a call is still in progress.

The fixtures follow the documented schemas: post-contact output files (`Version` 1.1.0,
`ContentMetadata.Output` Raw or Redacted, `ConversationCharacteristics`, `Transcript`,
`Categories`) and real-time segment stream events (`Version` 1.0.0, `EventType`
STARTED/SEGMENTS/COMPLETED, `Utterance` and `Transcript` segments). In S3 the files live at
`Analysis/Voice/YYYY/MM/DD/<contactId>_analysis_<ts>.json` (original) and
`Analysis/Voice/Redacted/YYYY/MM/DD/<contactId>_analysis_redacted_<ts>.json` (redacted); the
fixtures keep the object names (with `:` replaced by `-` for portable file names). The
analysis file does not carry the agent: `config/contacts.json` is the matching contact-record extract.

## What you have

| Path | What it is |
|---|---|
| `fixtures/analysis/` | 9 post-contact output files for 2026-10-06 (7 redacted, 1 raw original, 1 failed job) |
| `fixtures/segments/realtime-2026-10-06.jsonl` | real-time segment stream records for two live calls |
| `config/compliance-policy.json` | QA policy: greeting, closing, required disclosure, escalation and prohibited language |
| `config/contacts.json` | contact id -> agent, queue, channel |
| `src/types.ts` | schema types (do not change) |
| `src/*.ts` | modules to implement (TODOs) |
| `connect-kit` `startFakeServiceNow` | local fake of the ServiceNow OAuth endpoint and Table API (used by the tests) |

## Requirements

1. **Input hygiene** (`src/analysis.ts`): accept only redacted, completed analyses. A file is
   redacted only if `ContentMetadata.Output` is `Redacted` AND the object name is a
   `_analysis_redacted_` name. Reject raw originals (`UnredactedInputError`), failed jobs
   (`IncompleteJobError`) and malformed files; `loadBatch` reports each rejection with a reason.
2. **Compliance rules** (`src/compliance.ts`), phrase matching on `normalize()`d text:
   - greeting: an AGENT turn starting within `withinMillis` contains a greeting phrase;
   - closing: one of the last `lastAgentTurns` AGENT turns contains a closing phrase;
   - required disclosure: some AGENT turn contains a disclosure phrase, else a finding with
     no evidence turns (`atMillis: null`);
   - escalation language: CUSTOMER turns only; prohibited language: AGENT turns only; the
     finding lists every matching turn id and the offset of the first;
   - `adherent` = greeting and closing; findings sorted by priority then ruleId. Script
     adherence is a KPI, not a QA task.
3. **KPIs** (`src/kpi.ts`): one row per agent (see the field comments on `AgentKpi`), sorted
   by agent id. Talk ratio only over contacts that have `TalkTime` (chat has none).
4. **Real-time alerts** (`src/realtime.ts`): see the class comment. Remember that partial
   `Utterance` segments are revised later and that Kinesis delivers at least once.
5. **ServiceNow QA tasks** (`src/servicenow.ts`): OAuth 2.0 client credentials with token
   caching, one re-auth on 401, `Retry-After` on 429, bounded backoff on 5xx (at most
   `maxAttempts` per request), fail fast on other 4xx, and idempotent create: look up
   `correlation_id` before inserting into the `task` table.
6. **Batch** (`src/run.ts`): one task per (contact, rule) finding with correlation id
   `<contactId>:<ruleId>`, priority from the rule, assignment group from the policy. Never copy
   transcript text into ServiceNow (redaction is ML-based and not guaranteed). One failed task
   is reported in `taskErrors` and does not stop the batch.

## Acceptance criteria (what the grader checks)

- Raw, forged and failed files never enter the pipeline; rejection reasons are reported.
- Each compliance rule on the fixture contacts, including the 15 s greeting window, CUSTOMER vs AGENT scoping, chat contacts.
- KPI values per agent (sentiment mean and quarter delta, talk ratio, interruptions, rates, counts).
- Real-time: no alerts from partials, dedupe of redelivered segments, once per type, nothing after COMPLETED, negative run reset.
- ServiceNow: idempotency, token caching, 401 re-auth, Retry-After waits, bounded retries, no retry storm on bad credentials.
- End to end: exactly the expected tasks with the right priorities and no transcript text; a re-run creates nothing.
- `ANSWER.md`: design choices and production follow-ups.

## How to run

```bash
make setup     # links the shared toolchain (connect/_env)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w6-c1
make clean
```
