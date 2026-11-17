# Rubric: connect/w6-c1 Conversational analytics QA processor
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Data protection | 15 | Full: only redacted + completed analyses accepted (both body and object name checked), no transcript text or [PII] tokens in ServiceNow, ANSWER.md notes that redaction is ML-based (not guaranteed), that voice redaction happens after disconnect so the real-time stream is unredacted, and who may read Analysis/Voice/ vs Analysis/Voice/Redacted/. Partial: checks only Output. Zero: processes raw files. |
| 3 | Integration robustness | 15 | Full: correlation_id lookup before create, token cache with early refresh, single re-auth on 401, Retry-After honoured with a cap, bounded attempts, fail fast on 4xx, per-task error isolation. Partial: retries unbounded or idempotency only in memory. |
| 4 | Real-time correctness | 10 | Full: partials ignored, transcript-id dedupe, once per alert type, state cleared after COMPLETED/FAILED, memory bounded. Partial: dedupe missing or state never released. |
| 5 | KPI and rule design | 5 | KPIs computed from documented fields (OverallSentiment, SentimentByPeriod.QUARTER, TalkTime, InterruptionsByInterrupter), chat handled, clear rounding. |
| 6 | ANSWER.md trade-offs | 5 | Full: compares this processor with native conversational analytics rules (categories, real-time alerts, CREATE_TASK / GENERATE_EVENTBRIDGE_EVENT actions, SUBMIT_AUTO_EVALUATION) and generative AI evaluations, and states where custom code is still justified (ServiceNow ownership, cross-contact KPIs). Partial: generic. |
Total: 100
