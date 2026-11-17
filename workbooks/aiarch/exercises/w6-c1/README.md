# aiarch/w6-c1 - SSM Automation runbook: roll back the agent endpoint

**Type:** coding | **Estimate:** 2 hours | **Study plan:** Week 6 (Mon: SSM Automation runbooks; Tue: approvals and Change Manager)

## Scenario

Lighthouse releases move the AgentCore `prod` endpoint to a new runtime version; rollback is
moving it back. Today that is a hand-typed CLI call during an incident. Harbor Point's change
board wants it as an SSM Automation runbook, `Lighthouse-RollbackAgentEndpoint`, run from the
shared-services account: it records what it is about to change, waits for a release manager,
moves the endpoint, waits until it is serving, and fails loudly if errors do not come down.
Same discipline you apply to every live change: back up current state before you mutate it.

`ssmsim/` is an offline interpreter for runbook YAML (schemaVersion 0.3) with fake AWS APIs;
read its docstring for the supported actions and variables. It works as shipped.

## Requirements (`runbooks/rollback-agent-endpoint.yaml`)

Parameters, each validated:
`AutomationAssumeRole` (an IAM role ARN), `AgentRuntimeId` (runtime id pattern
`name-XXXXXXXXXX`), `EndpointName` (default `prod`; `prod` or `canary`), `TargetVersion`
(digits only), `BackupBucket` (bucket name), `Approvers` (StringList, default the
release-manager role), `ErrorThreshold` (Integer, default 5). `assumeRole` uses
`AutomationAssumeRole`.

Steps:
1. Read the endpoint (`bedrock-agentcore-control` `GetAgentRuntimeEndpoint`), output its
   `liveVersion`.
2. If it already serves `TargetVersion`, end successfully without asking or changing anything.
3. Back up the current state to S3 (`PutObject`) at
   `rollback/<runtime>/<endpoint>/<execution id>.json`, a JSON body with the live and target
   versions.
4. `aws:approve` with the approvers, at least one approval, and a message naming the endpoint
   and both versions.
5. `UpdateAgentRuntimeEndpoint` to `TargetVersion`.
6. Wait until `status` is `READY`, with a timeout of at most 15 minutes.
7. Read the `SystemErrors` sum from CloudWatch; if it is above `ErrorThreshold`, fail the
   execution; otherwise succeed.
8. Output the previous live version.

## Acceptance criteria (what the grader checks)

- Happy path, ordering (backup before update), rejection, waiting and timeout, error threshold,
  no-op, parameter validation, runbook shape and outputs.
- `ANSWER.md`: the assume-role policy you would attach (least privilege), how you would run it
  cross-account from shared-services, and when Change Manager is worth adding.

## How to run

```bash
make setup     # builds aiarch/.venv once
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w6-c1
make clean
```

## What to submit

`runbooks/rollback-agent-endpoint.yaml` and `ANSWER.md`.
