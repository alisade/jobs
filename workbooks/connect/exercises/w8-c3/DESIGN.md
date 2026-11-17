# Design: CI/CD and release management for the Larkspur Amazon Connect platform

Author: <you>   Status: draft   Date: <date>

## 1. Context and goals
<!-- Two short paragraphs: what is broken today (cite inputs/current-state.md), what "good" looks like
in measurable terms (lead time, change failure rate, MTTR, DR lag). -->

## 2. What is managed as code, and with what tool
<!-- A table: resource type -> tool (CDK/CloudFormation, Terraform, SAM, exported JSON + promotion tool,
API script) -> why. Be precise about what CFN/CDK/Terraform cover and do not cover (flows vs modules,
aliases, rules, evaluation forms, prompts, Lex bots, phone numbers). -->

## 3. Repository and branching model
<!-- Repos, folder layout, branch strategy, how flows built in the dev console get into git (export job,
PR), code owners and review rules for the offshore teams. -->

## 4. Environment promotion and reference rewriting
<!-- Sandbox -> Dev -> Test -> Prod -> DR. How environment-specific ARNs/IDs are handled (manifests from IaC
outputs, the promotion tool from connect/w8-c1), deploy ordering (Lambdas, Lex alias, modules, flows,
integration associations). -->

## 5. Pipeline design
<!-- Stages, gates and who approves what. Include a GitHub Actions workflow sketch (YAML) for the flow
release path with OIDC, environments with required reviewers, and the gates. -->

## 6. Automated testing
<!-- Unit tests, flow lint (graph rules), native flow test cases (AWS::Connect::TestCase /
StartTestCaseExecution), Lex test sets, synthetic test calls, load tests; what runs where and blocks what. -->

## 7. Release strategies and rollback
<!-- Lambdas: versions/aliases with CodeDeploy canary. Modules: versions + aliases. Flows: no alias API,
so how do you release and roll back? Lex: bot versions and aliases. Blue/green options for the whole
flow set (e.g. a phone number re-association or a dispatcher flow). Hotfix path. -->

## 8. Monitoring, alarms and release verification
<!-- Metrics, alarms and dashboards that decide "release healthy" (AWS/Connect ContactFlowErrors, flow
logs metric filters, Lambda errors/duration, Contact Lens alerts, queue metrics), and the automatic
rollback trigger. DR drift detection. -->

## 9. Governance, audit and the offshore model
<!-- CAB integration (standard vs normal change), audit trail, RACI for Boston / Pune / Monterrey, change
freeze handling, secrets, least privilege. -->

## 10. Rollout plan and risks
<!-- How you get from today to this in phases, with the biggest risks and mitigations. -->
