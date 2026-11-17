# ANSWER: connect/w1-c3 Multi-region resiliency and DR runbook

## Approach

Started from the RTO/RPO table and the "AWS-supported only" constraint, which points to Connect Global
Resiliency; then listed every dependency in inputs/ and asked what has to exist in us-west-2 for a call to
complete the password-reset path end to end.

## Fix

DESIGN.md: ACGR replica in us-west-2 with numbers claimed to a traffic distribution group, active/standby
distribution (100/0) with global sign-in for agents, same-name Lambdas and $.AwsRegion ARNs, Lex Global
Resiliency, DynamoDB global table, CRR + multi-region KMS for recordings, ServiceNow allow-list for both NATs,
chat endpoint flag, a timed runbook with triggers, verification and failback, and a drill plan.

## Trade-offs / what I would do in production

Active/standby keeps WFM and reporting simple at the cost of idle capacity; revisit active-active global
routing after the first drill. The two unported DIDs remain a gap. Validate quotas and per-feature regional
availability before the first drill.
