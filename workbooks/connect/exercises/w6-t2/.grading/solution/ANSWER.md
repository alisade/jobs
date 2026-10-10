# ANSWER: connect/w6-t2 Real-time supervisor alert never fires

## Approach

Compared the real-time and the post-call rule (same phrases and queues, so detection works), then
followed one escalated contact through the flow logs looking at every analytics block that ran.

## Root cause

`grep -h UpdateContactRecordingAndAnalyticsBehavior incident/flow-logs/*.jsonl` shows, for all three
contacts, `set-analytics` with AnalyticsModes ["RealTime"] at the start and then `set-recording` in
`mod-recording-defaults` with ["PostContact"] right before `transfer`. The last analytics block wins,
so real-time analysis stops before the agent leg (supervisors saw the live transcript only in the IVR)
and the OnRealTimeCallAnalysisAvailable rule never evaluates the escalation; post-call analysis runs,
so the weekly rule matches (EventBridge archive has only post-call matches). CHG0034502 was tested in a
sandbox flow without the module. Kinesis IteratorAge: different consumer, one interval, not rules.

## Fix

Module v4 sets AnalyticsModes ["RealTime"] with the same redaction (RedactedOnly) and entities; module
still invoked before every transfer; rule unchanged. Verified with make lint and make test (all four paths).

## Trade-offs / what I would do in production

Shared modules need owners and an impact list; add a flow test case or a synthetic escalation call in
the release pipeline; alarm when live-rule matches are zero while post-call matches are not; document
that the last analytics block wins.
