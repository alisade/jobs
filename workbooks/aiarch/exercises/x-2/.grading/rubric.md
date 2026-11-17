# Rubric: aiarch/x-2 Pipeline ADR and endpoint policies
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Design exercise: grade.sh reports 0/0; this row does not apply. |
| 2 | Options analysed fairly | 20 | At least GitLab-native, CDK Pipelines via CodeConnections and a hybrid, each with flow, approval point, audit trail, credentials, cost and effort; no strawmen. |
| 3 | Decision quality | 20 | A clear pick tied to the stated constraints (audit wants one system, security wants in-AWS execution, developers want MR feedback, FinOps limit), with what is given up stated honestly. |
| 4 | Release flow | 15 | Build once, digest promotion, approval with a named approver, change window, rollback via the endpoint runbook; a readable diagram. |
| 5 | Endpoint policies | 25 | Correct sketches scoped to the org and actions; the OAuth bearer-token case handled with Principal "*" plus non-principal conditions (for example on resource ARN) and an explanation why IAM principal conditions cannot apply; interaction with the aws:SourceVpce SCP; a test plan. |
| 6 | Consequences and ANSWER.md | 20 | Concrete follow-ups, risks, what would change the decision and the migration path. |
Total: 100
