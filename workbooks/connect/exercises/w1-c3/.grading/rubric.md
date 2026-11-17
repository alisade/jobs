# Rubric: connect/w1-c3 Multi-region resiliency and DR runbook
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0) |
| 2 | ACGR mechanics | 25 | Full: replica instance in the paired region, numbers claimed to a traffic distribution group (instance-level numbers do not move), telephony and agent distribution percentages, SAML global sign-in, prerequisites named (Enterprise Support, SAML, quotas parity, same Lambda names / $.AwsRegion), chat endpoint handled separately, mentions global routing (active-active) as an option. Partial: replica + "switch traffic" without how numbers and agents move. Zero: DIY second instance with re-pointed numbers or Route 53 for phone calls. |
| 3 | Dependency parity | 20 | Every dependency has a us-west-2 answer: Lambdas, Lex (Global Resiliency), DynamoDB global table, secrets, S3/KMS for recordings, ServiceNow allow list, quotas; plus how parity is kept (one pipeline, both regions, checks). Partial: Connect only. |
| 4 | Runbook | 20 | Triggers, decision owner, ordered steps with timings that fit the 15 min RTO, verification (synthetic calls, metrics), communications, failback in steps, rollback of a failed failover. Partial: a list without timings or verification. |
| 5 | Testing and operations | 10 | Drill cadence and success criteria, synthetic tests in both regions, release-time parity checks. |
| 6 | Constraints and gaps | 10 | Unported DIDs, Avaya coexistence, Okta/ServiceNow as vendor DR, in-flight chats, regional feature availability; CFO cost answer that is honest. |
| 7 | Clarity | 15 | A diagram, decisions stated with reasons, readable by CAB and security in 15 minutes; ANSWER.md summarizes key decisions and trade-offs. |
Total: 100
