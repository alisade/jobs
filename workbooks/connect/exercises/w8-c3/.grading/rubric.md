# Rubric: connect/w8-c3 CI/CD and release management for Connect
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0). |
| 2 | IaC coverage accuracy | 20 | Full: a resource-by-resource table that is correct about CFN/CDK/Terraform coverage: flows and modules have CFN types but no flow alias type/API (flow versions are campaign-only), modules have versions and aliases, IntegrationAssociation for Lambda/Lex, rules/evaluation forms/views in CFN but not Terraform, TestCase in CFN, phone numbers retained; users not in IaC. Partial: mostly right with one material error (e.g. claims flow aliases exist). Zero: generic "use Terraform for everything". |
| 3 | Promotion and reference handling | 15 | Full: generated manifests (IaC outputs / List APIs), logical-name rewriting that fails closed, ref check gate, deploy ordering (associations, Lambdas, Lex alias, modules, flows, tests), DR in the same release. Partial: manual ARN spreadsheets or string replace of account ids. |
| 4 | Pipeline and testing | 20 | Full: concrete GitHub Actions sketch with OIDC, environments/required reviewers, concurrency, artifacts; flow lint, native flow test cases (StartTestCaseExecution), Lex test sets, synthetic calls, load tests placed at the right stage with what each blocks. Partial: stages listed without gates or tests named. |
| 5 | Release and rollback | 15 | Full: Lambda canary with CodeDeploy and alarms; module and Lex alias moves; flow rollback by redeploying recorded previous content; blue/green by number re-association or dispatcher flow; hotfix path and freeze handling. Partial: "roll back by re-importing". |
| 6 | Monitoring and verification | 10 | Full: AWS/Connect metrics named correctly (ContactFlowErrors, ContactFlowFatalErrors, ThrottledCalls, ConcurrentCallsPercentage, queue metrics), flow-log metric filters, post-deploy watch with automatic rollback, DR drift detection. Partial: generic dashboards. |
| 7 | Governance and offshore model | 10 | Full: standard vs normal change with evidence the pipeline provides, audit chain PR -> run -> release record -> CloudTrail, removal of prod console write access, RACI for Boston/Pune/Monterrey, freeze handling. Partial: mentions CAB only. |
| 8 | Communication | 10 | Clear structure, measurable goals, phased rollout with risks; a reviewer could approve or challenge each decision. ANSWER.md summarizes the decisions. |
Total: 100
