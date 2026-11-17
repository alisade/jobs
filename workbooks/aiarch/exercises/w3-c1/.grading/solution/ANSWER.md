# ANSWER: aiarch/w3-c1

## Approach

Two stacks: the image repo in shared-services and one runtime stack per environment, all
values from config. I read the synthesized template after each requirement with make synth.

## Fix

Fail-fast context for env and imageTag; immutable scanned repo with lifecycle rules and a
pull-only policy for the two workload accounts; Runtime from the shared repo at the tag in VPC
mode; a role trusting AgentCore with aws:SourceAccount and Bedrock invoke on one profile and
its model; endpoints from config; isolated VPC with interface endpoints and an S3 gateway
endpoint; JWT gateway with the user-directory Lambda target; tags; the NoWildcardActions aspect.

## Trade-offs / what I would do in production

- fromEcrRepository with an immutable tag means one image digest, built and scanned once, goes
  to every account; fromAsset rebuilds on every synth and would deploy an untested image.
- Rollback is changing the prod endpoint's version in config and deploying; no image rebuild.
- The Runtime L2 adds logs, X-Ray and workload-identity statements; they are scoped and needed,
  so I kept them, but the X-Ray statement uses Resource "*" (the service requires it).
- Before prod: endpoint policies on the interface endpoints, alarms on runtime errors and
  latency, Policy in AgentCore (Cedar) on the gateway, and the shared repo pinned by digest.
