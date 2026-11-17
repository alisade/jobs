# ANSWER: platform/w2-c1 Fleet upgrade planner

## Approach

Pure functions: steps per cluster, static blockers, a window filter and a scheduler with one time
cursor. All datetimes in UTC.

## Fix

Control plane hops one minor at a time with the best patch in the channel; pools upgraded to the current
control plane when the next hop would break the skew; all pools to the target at the end. Exclusion scopes
follow GKE (patch vs minor, node vs control plane). Quota is the max extra vCPUs over pools (blue-green
needs the full pool). The first blocked cluster halts the plan and later clusters are held.

## Trade-offs / what I would do in production

GKE release channels and fleet rollout sequencing do most of this; the planner adds reviewable intent,
the business freeze calendar and quota checks before the window. Trigger from Pub/Sub cluster
notifications, gate each wave on the canary's SLO burn rate, require approval for prod, and unblock
prod-green with a quota increase or surge with max_surge sized to free quota.
