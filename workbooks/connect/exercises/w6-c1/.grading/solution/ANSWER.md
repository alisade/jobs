# ANSWER: connect/w6-c1 Conversational analytics QA processor

## Approach

Started from the schemas (output file 1.1.0, segment stream 1.0.0) and the fixtures, wrote the input
gate first (redacted + completed only), then rules, KPIs, the real-time monitor and the ServiceNow
client, testing each against the fake ServiceNow.

## Fix

- Input gate checks ContentMetadata.Output and the _analysis_redacted_ object name; raw and failed
  files are reported, never processed. Contact id from the object name.
- Rules on normalized text, participant-scoped; findings sorted by priority.
- KPIs from OverallSentiment, QUARTER deltas, TalkTime (voice only), InterruptionsByInterrupter.
- Real-time monitor: Transcript segments only, dedupe by Transcript.Id, once per alert type, state
  dropped after COMPLETED/FAILED.
- ServiceNow: client credentials token cached with early refresh, one re-auth on 401, Retry-After with
  a cap, bounded 5xx backoff, correlation_id lookup before insert; per-task error isolation.

## Trade-offs / what I would do in production

Use native conversational analytics rules for detection (categories, real-time alerts, CREATE_TASK or
EventBridge events) and keep this code for the ServiceNow QA workflow; run it per S3 object event
with a DLQ instead of nightly; restrict the raw Analysis/Voice/ prefix to legal hold; never persist
real-time voice content (it is unredacted); add generative AI evaluations for 100% coverage.
