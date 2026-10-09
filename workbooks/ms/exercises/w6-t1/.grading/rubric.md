# Rubric: ms/w6-t1 Work order saves hang, then fail
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: synchronous PostOperation Update step on contoso_workorder with no filtering attributes; the plug-in calls Update on the same row, which re-enters the pipeline (Depth +1 each time) until the platform's infinite-loop limit (Depth 8) aborts with 0x80044182 SdkCorrelationTokenDepthTooHigh and the whole transaction rolls back. Explains why even description edits fail (no filtering attributes) and why it "hangs" (8 nested Retrieve+Update cycles). Partial: "recursion" without the mechanism or without why unrelated edits fail. Zero: blames the vendor API, sandbox, or workflows. |
| 3 | Evidence | 15 | Full: quotes trace rows sharing one correlationid with depth 1..8 and growing durations, the 0x80044182 error with ApiDepthKey 8, the empty filteringAttributes in steps-export.json, release 3.4.0 timing. Partial: some evidence. Zero: assertions only. |
| 4 | Red herring handled | 5 | Correctly dismisses the 0x80044172 Sandbox Host timeouts: different plug-in, asynchronous (mode 1), Monday 13:07-13:38 inside the vendor outage window, resolved before 3.4.0; async steps do not block saves. |
| 5 | Fix quality | 10 | Full: PreOperation sync, value set on Target, pre-image for partial updates, filtering attributes on the three inputs, no Retrieve/Update, verified by re-running make setup. Partial: only filtering attributes (PostOperation + Update still costs a second write and a nested pipeline run) or a Depth guard (Learn says do not build logic on Depth). |
| 6 | Production trade-offs | 10 | Concrete: managed solution hotfix path (patch or upgrade), disable the step as the immediate mitigation, trace log setting, code review checklist for "Update on own Target", alerting on 0x80044182, pipeline test like this simulator in CI. |
Total: 100
