# Design: CI/CD and release management for the Larkspur Amazon Connect platform

Author: model answer   Status: proposed   Date: 2026-10-09

## 1. Context and goals

Today flows are built in the dev console and moved by an export/import script, Lambdas reach test
and prod by hand, prompts, rules and evaluation forms are clicked into each instance, and nothing
verifies a release before callers do. The 2026-10-06 incident (dev Lex alias shipped to prod, every
caller routed to GeneralSupport) passed every existing stage. DR is three releases behind.

Goals (measured from the pipeline and the incident tracker, reviewed monthly):

| Metric | Today | Target in 2 quarters |
|---|---|---|
| Lead time, merged PR to prod | 1-2 weeks (CAB batch) | < 2 days for standard changes |
| Change failure rate | ~1 in 4 releases | < 1 in 10 |
| Time to roll back a flow release | hours, manual | < 10 minutes, one pipeline run |
| DR lag behind prod | 3 releases | 0 (same pipeline run) |
| Releases needing a Boston engineer awake | all | none for dev/test; prod approval only |

## 2. What is managed as code, and with what tool

| Resource | Tool | Why |
|---|---|---|
| Instance, storage config, approved origins, security keys | CDK (`lfg-connect-infra`) | Rarely changes; CDK already in place; CFN covers it. |
| Hours, queues, routing profiles, quick connects, security profiles, predefined attributes, user hierarchy | CDK | Full `AWS::Connect::*` coverage; outputs feed the env manifests. |
| Phone numbers, traffic distribution group | CDK, import existing (`cdk import`) | Numbers are precious: `RemovalPolicy.RETAIN`, never recreated. |
| Integration associations (Lambda, Lex alias) | CDK `AWS::Connect::IntegrationAssociation` | The 10-06 incident: a correct ARN still fails if the instance is not associated. |
| Lambdas | SAM (existing), CodeDeploy traffic shifting | Versions + aliases give canary and instant rollback. |
| Lex bot | `AWS::Lex::Bot` + `BotVersion` + `BotAlias` from the exported bot definition in git | Versioned, alias per env; the flow references the alias ARN from the manifest. |
| Flow modules | Exported JSON in git, deployed by `UpdateContactFlowModuleContent`, then `CreateContactFlowModuleVersion` + alias update | Modules have versions and aliases (Nov 2025): shared logic can be pinned and rolled back by alias. |
| Contact flows | Exported JSON in git, promoted by the promotion tool (connect/w8-c1), deployed by `UpdateContactFlowContent` | No flow alias API or CFN alias type; versions via API are campaign-only, so the artifact in git IS the version. Considered `AWS::Connect::ContactFlow` with `Content`: rejected for now because the team edits in the console and the content changes every release; a stack per release adds churn without adding rollback. |
| Prompts (audio) | S3 bucket per env + `AWS::Connect::Prompt` (S3Uri) | Removes hand uploads. |
| Rules (Contact Lens), evaluation forms, views | CDK (`AWS::Connect::Rule`, `EvaluationForm`, `View`) | CFN covers them; Terraform does not cover rules/views. |
| Flow test cases | `AWS::Connect::TestCase` in the same CDK app as the flows' manifests | Tests live with the code they test and run from CI. |
| Agents (users) | Identity provider + SCIM-like sync job, not IaC | Users churn daily; IaC drift would be constant. |

Terraform: the platform team standardised on CDK; Terraform's `aws_connect_*` would cover the core
but not rules, views or flow aliases, so no reason to switch.

## 3. Repository and branching model

Two repos: `lfg-connect-infra` (CDK + SAM + Lex + prompts) and `lfg-connect-flows` (exported flows
and modules, test definitions, the promotion tool). Trunk-based: short-lived branches, PR to `main`,
squash merge. `CODEOWNERS`: `/flows/**` -> Pune + Monterrey leads (either may approve), `/infra/**`
-> platform team, `/pipeline/**` -> platform team. Branch protection: one approval, required checks
(lint, unit, flow lint, promotion dry run for test and prod).

Getting console work into git: a "capture" workflow (manual dispatch or nightly) exports every flow
and module from the dev instance, normalizes the JSON (sorted keys, stable Metadata), and opens a PR
with the diff. Engineers review flows as diffs, the same as code.

## 4. Environment promotion and reference rewriting

Sandbox is not promoted from (scratch only). Dev -> Test -> Prod -> DR, the same artifact set.

- Env manifests are generated, not hand-written: a CDK stack output per env (queues, hours, prompts,
  Lambda ARNs, Lex alias ARN, module ids) written to `manifests/<env>.json` by the infra pipeline.
- The promotion tool (w8-c1) rewrites every reference by logical name and fails closed on unknown or
  unmapped references; `check-refs` (w8-t1) re-checks every ARN against the target manifest.
- Deploy order per environment: infra stack (queues, prompts, associations) -> Lambdas (alias) ->
  Lex bot version + alias -> modules (content, version, alias) -> flows (content) -> test cases.
- DR: the prod job's last step deploys the same artifacts to us-west-2 with the DR manifest; a failed
  DR step fails the release, so DR can never silently lag.

## 5. Pipeline design

Stages for the flows repo (infra repo is similar with `cdk diff` as the review artifact):

1. PR: lint (validateFlow graph rules), unit tests, promotion dry run against test and prod
   manifests (report posted to the PR), `check-refs`.
2. Merge to main: deploy to dev automatically; run flow test cases on dev.
3. Test: automatic after dev; flow test cases + synthetic calls; supervisors' UAT window for
   normal changes.
4. Prod: GitHub environment `production` with required reviewers (release manager + one Boston
   engineer); standard changes approved by the pipeline record, normal changes by CAB ticket id.
5. Post-deploy verification: test cases + a synthetic call per entry point; watch alarms 30 min.
6. DR: same artifacts, DR manifest.

```yaml
# .github/workflows/release-flows.yml (sketch)
name: release-flows
on:
  push: { branches: [main] }
  workflow_dispatch: { inputs: { target: { type: choice, options: [test, prod] } } }
permissions: { id-token: write, contents: read }
concurrency: { group: release-flows, cancel-in-progress: false }
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22 }
      - run: npm ci && npm test
      - run: npm run lint-flows
      - run: npm run promote -- --env test --dry-run && npm run promote -- --env prod --dry-run
      - uses: actions/upload-artifact@v4
        with: { name: flows-${{ github.sha }}, path: export/ }
  deploy:
    needs: build
    strategy: { max-parallel: 1, matrix: { env: [dev, test, prod, dr] } }
    environment: ${{ matrix.env }}          # prod and dr: required reviewers + business-hours rule
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { name: flows-${{ github.sha }} }
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.DEPLOY_ROLE_ARN }}   # one OIDC role per account
          aws-region: ${{ vars.AWS_REGION }}
      - run: npm run promote -- --env ${{ matrix.env }} --out dist/
      - run: npm run check-refs -- dist/
      - run: npm run deploy -- dist/ --modules-first --record releases/${{ matrix.env }}.json
      - run: npm run test-cases -- --env ${{ matrix.env }} --wait   # StartTestCaseExecution
      - run: npm run verify -- --env ${{ matrix.env }} --minutes 30 # alarms; auto-rollback on breach
```

`deploy` records the previous content of every flow/module it overwrites in a release record
(`releases/<env>.json` artifact plus an S3 copy) so rollback is a pipeline run, not archaeology.

## 6. Automated testing

| Layer | What | Where | Blocks |
|---|---|---|---|
| Unit | Lambda handlers, promotion tool | PR | merge |
| Flow lint | graph rules: error branches, bounded loops, attributes before use, Lambda limits | PR | merge |
| Reference checks | promotion dry run + check-refs per target | PR, deploy | merge, deploy |
| Native flow test cases | `AWS::Connect::TestCase` per entry point and per module path (VIP, after hours, bot intents, Lambda error branches) via `StartTestCaseExecution` | dev, test, prod post-deploy | promotion to next env; triggers rollback in prod |
| Lex | test sets / test workbench on the new bot version before aliasing | test | Lex alias move |
| Synthetic calls | scheduled and post-deploy calls to each number (DTMF and spoken) from a test harness | test, prod | prod verification |
| Load | chat and voice load against test before peak season and major flow changes | test, quarterly | release of major changes |

## 7. Release strategies and rollback

- Lambdas: `AutoPublishAlias: live` + CodeDeploy `Canary10Percent5Minutes` with alarms on Errors,
  Duration p99 and Connect `ContactFlowErrors`; rollback is automatic.
- Modules: deploy content, publish a version, move the env alias. Rollback = point the alias at the
  previous version.
- Flows: no alias API, so a release overwrites flow content. Rollback = redeploy the previous
  artifacts from the release record (same pipeline, one job, < 10 minutes). Because most logic lives
  in aliased modules, many rollbacks are an alias move.
- Blue/green for risky releases (new entry flow): deploy the new flow under a new name, run test
  cases against it, then repoint the phone numbers (`AssociatePhoneNumberContactFlow`) or switch a
  small dispatcher flow; switching back is the rollback.
- Lex: build a new bot version, run test sets, move the env alias; rollback is an alias move.
- Hotfix: branch from main, same pipeline, `hotfix` label allows the freeze window with release
  manager approval; never a console edit in prod (console edits in prod are detected by drift job).

## 8. Monitoring, alarms and release verification

- Alarms (CloudWatch, per instance): `ContactFlowErrors` > 0 sustained 5 min after a release and
  > baseline otherwise; `ContactFlowFatalErrors` > 0; `ThrottledCalls` > 0; `ConcurrentCallsPercentage`
  > 80%; `LongestQueueWaitTime` and `QueueSize` per key queue; Lambda Errors/Throttles/Duration p99 per
  function; metric filters on `/aws/connect/<alias>` flow logs for error results per block id.
- Contact Lens real-time rules for spikes in "no one asked me" style phrases are a lagging signal,
  not a release gate.
- Release verification: the pipeline watches the alarms for 30 minutes after prod deploy and
  redeploys the previous release record automatically on breach, then pages.
- DR drift: a daily job exports prod and DR flows and diffs them (normalized); any diff opens an
  incident.
- Dashboards per release: contacts by entry flow, error results per block, containment.

## 9. Governance, audit and the offshore model

- Standard change (pre-approved by CAB once): flow and module changes that pass all gates, shipped
  in business hours with automatic rollback. Normal change: new entry points, number moves, infra
  stack changes; CAB id required as a workflow input, recorded in the release record.
- Audit trail: PR (author, reviewers) -> workflow run (approver from the GitHub environment) ->
  release record (content hashes before/after) -> CloudTrail (`UpdateContactFlowContent` by the
  deploy role only). Console write access to prod is removed for humans except break-glass.
- RACI: Pune/Monterrey responsible for flows, tests and dev/test releases; Boston platform team
  accountable for the pipeline and prod approval; release manager approves prod; SRE consulted on
  alarms; CAB informed for standard changes.
- Freeze: the `production` environment's deployment branch rule blocks non-hotfix runs in freeze
  windows; hotfix requires release manager + platform lead.
- Secrets: none in the pipeline (OIDC); Lambdas read secrets from Secrets Manager.

## 10. Rollout plan and risks

1. Weeks 1-2: capture job and flows repo, lint and promotion dry run on PRs; release records.
2. Weeks 3-4: pipeline to dev and test; flow test cases for the three entry points; generated
   manifests from CDK outputs; integration associations in CDK.
3. Weeks 5-6: prod and DR through the pipeline with approvals; alarms and auto-rollback; remove
   human console write access in prod.
4. Weeks 7-8: modules with aliases for shared logic; Lex bot in CloudFormation; prompts from S3;
   rules and evaluation forms in CDK; DR drift job.

Risks: console-first habits (mitigate: capture job makes console work reviewable instead of
forbidden in dev); test-case coverage too thin to trust auto-rollback (start with entry points and
error branches, grow with every incident); CFN replacement of numbers or queues (retain policies,
`cdk diff` review required); DR deploy failure blocking prod releases (runbook to skip DR once with
an incident ticket).
