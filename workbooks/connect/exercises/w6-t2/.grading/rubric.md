# Rubric: connect/w6-t2 Real-time supervisor alert never fires
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the inbound flow enables RealTime early (set-analytics), but the shared module mod-recording-defaults invoked right before every transfer runs a second Set recording, analytics and processing behavior block with AnalyticsModes PostContact; the last block wins, so real-time analysis stops before the agent leg and the OnRealTimeCallAnalysisAvailable rule never sees the escalation phrase; post-call analysis still runs, so the weekly category matches. The sandbox flow had no module. Partial (10-15): "the module overrides it" without the last-block-wins semantics or without explaining the post-call success. Zero: blames phrases, queues, the rule, or Kinesis. |
| 3 | Evidence | 20 | Full: flow log lines showing set-analytics RealTime then set-recording PostContact in mod-recording-defaults immediately before transfer for all three contacts; supervisors seeing the live transcript only in the IVR; EventBridge archive with only post-call matches; CHG0034502 testing in a sandbox without modules. Partial: one piece. |
| 4 | Red herring handled | 5 | Rules out the Kinesis IteratorAge spike: that stream feeds the coaching dashboard consumer, rule evaluation does not depend on it, the spike was one 5-minute window on Monday 09:05 and recovered. |
| 5 | Fix quality | 10 | Module (or placement) changed so the effective mode at transfer is RealTime with redaction RedactedOnly kept, module still invoked, rule left real-time; mentions that real-time voice analytics also supports redaction of the output files (voice redaction is applied after disconnect) and that other flows using the module were reviewed. |
| 6 | Prevention | 10 | Concrete: shared module ownership and change review, a flow test case (Connect flow testing APIs / AWS::Connect::TestCase) or synthetic call asserting the real-time rule fires, alarm when the live rule has zero matches while the post-call twin has matches, document "last analytics block wins". Partial: generic. |
Total: 100
