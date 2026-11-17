# Reference: connect/w6-t2

Mechanism: the Set recording, analytics and processing behavior block's analytics settings are
overwritten by each later block in the flow (admin guide configuration tips: a later block that
unselects analytics disables it; settings in the Analytics section are overwritten by each subsequent
block). The inbound flow sets VoiceAnalyticsBehavior.AnalyticsModes ["RealTime"] at the start
(CHG0034502), but `mod-recording-defaults` (LFG-1302, March, PCI defaults) runs before every transfer and
sets ["PostContact"]. AnalyticsModes for voice can be one of RealTime or PostContact, so real-time
analysis stops before the agent leg: the live transcript shows only the IVR part, the real-time rule
(OnRealTimeCallAnalysisAvailable) never sees the agent conversation, and only the post-call rule matches.
CHG0034502 was tested in a sandbox flow without the module.

Red herring: Kinesis IteratorAge on the segment stream consumer; rules are evaluated by Connect, not by
your stream consumer, and the spike recovered in one interval.

Fix (`.grading/solution/flows/modules/mod-recording-defaults.json`): the module sets RealTime with the
same redaction defaults. Equivalent: move the RealTime block after the module call. Real-time voice
analytics still produces redacted post-contact output (redaction happens after disconnect).

Prevention: treat shared modules as owned components with a change review listing every flow that
invokes them; flow test cases in CI (test APIs / AWS::Connect::TestCase) or a synthetic call that
asserts a LIVE_ESCALATION event; alarm when the live rule's EventBridge matches drop to zero while
the post-call twin keeps matching.
