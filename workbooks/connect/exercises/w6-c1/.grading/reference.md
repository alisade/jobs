# Reference: connect/w6-c1

Reference code: `.grading/solution/src/`. Key points:

- Input hygiene: the redacted file is a twin of the original with entities replaced by `[PII]` (or
  `[ENTITY_TYPE]`); the original (raw) file exists only when the flow asks for "redacted and original"
  (`RedactionResults: RedactedAndOriginal`) and is the only complete copy of what was said. Check both
  `ContentMetadata.Output` and the `_analysis_redacted_` object name so a mis-pointed prefix cannot leak.
- Contact id comes from the object name: the output file body has no ContactId.
- Rules: scope by participant (escalation = CUSTOMER, prohibited = AGENT), window greeting by
  `BeginOffsetMillis`, report missing disclosure without evidence turns, sort by priority.
- KPIs from documented fields: `OverallSentiment.CUSTOMER` (-5..5), `SentimentByPeriod.QUARTER` delta
  (last - first quarter), `TalkTime.DetailsByParticipant`, `Interruptions.InterruptionsByInterrupter.AGENT`.
- Real-time: `Utterance` = partial, `Transcript` = final; Kinesis is at-least-once so dedupe on
  `Transcript.Id`; voice real-time segments are NOT redacted (voice redaction runs after disconnect),
  so the monitor must not persist content.
- ServiceNow: correlation_id makes `ensureTask` safe to re-run; token cached with 60 s early refresh;
  one re-auth on 401; Retry-After honoured with a 10 s cap; 5xx exponential backoff; max 4 attempts.
- Native alternative: conversational analytics rules (TriggerEventSource
  OnRealTimeCallAnalysisAvailable / OnPostCallAnalysisAvailable, conditions such as CONTAINS_ANY on
  `$.ContactLens.RealTimeCall.ExactMatch.Transcript` with a ParticipantRole filter, actions
  ASSIGN_CONTACT_CATEGORY, CREATE_TASK, GENERATE_EVENTBRIDGE_EVENT, SEND_NOTIFICATION,
  SUBMIT_AUTO_EVALUATION). A strong answer uses rules for detection and alerting and keeps custom code
  for the ServiceNow QA workflow and cross-contact KPIs; it also mentions generative AI performance
  evaluations for scoring 100% of contacts.
