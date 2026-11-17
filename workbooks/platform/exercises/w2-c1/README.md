# platform/w2-c1 - Fleet upgrade planner

**Type:** coding | **Estimate:** 2.5-3 hours | **Study plan:** Week 2 (Mon upgrades and skew, Tue windows and exclusions, Wed surge vs blue-green and quota, Thu PDBs and fleet rollout)

## Scenario

Tessellate (fictional) runs four GKE Standard clusters registered to one fleet: `dev-1` and `stg-1` on the
Regular channel, `prod-blue` (canary) and `prod-green` on Stable. Upgrades are planned by hand, so the
clusters drift and twice this year a prod node pool upgrade started during a freeze. Before automating the
upgrade itself, the platform lead wants a planner whose output can be reviewed in a pull request, like a
Terraform plan: what will change, in which window, and what blocks it.

## What you have

| Path | What it is |
|---|---|
| `planner.py` | CLI, version parsing, `window_occurrences()`, `best_in_minor()`; the planning functions are TODO |
| `fleet.json` | fleet state: target version, policy, versions per channel, clusters with node pools, windows, exclusions, quota, PDBs |
| `tests/` | visible tests |

## Your task

Implement `BLOCKING_SCOPES`, `cluster_steps()`, `static_blockers()`, `window_ok()` and `plan()`.

**Steps for one cluster** (`cluster_steps`)
- The target must be in the cluster's channel list (`channel_versions[channel]`), and the control plane
  must not be newer than the target; otherwise the cluster is blocked with a reason.
- The control plane moves **one minor at a time**. Each intermediate hop uses the highest version of
  that minor in the channel. A missing intermediate minor blocks the cluster.
- Before each control plane hop, any node pool that would end up more than `policy.max_node_skew` minors
  behind it is first upgraded to the **current** control plane version (a node pool is never newer than
  the control plane). Step `reason: "skew"` is optional.
- After the last hop, every node pool not at the target is upgraded to the target. Pools in name order.
- Each step has `kind`, `from`, `to`, `minor` (true when the minor version changes) and `pool` for pools.

**Blockers** (`static_blockers`, only for clusters that have steps)
- Any PDB with `disruptions_allowed <= 0` (name it as `namespace/name`).
- CPU quota: the extra vCPUs the upgrade needs are the maximum over pools of `max_surge * vcpus_per_node`
  for SURGE and `node_count * vcpus_per_node` for BLUE_GREEN (pools are upgraded one at a time). Blocked
  if `cpus_used + needed > cpus_limit`.

**Windows** (`window_ok`, `BLOCKING_SCOPES`)
- A cluster's steps all run in one occurrence of its maintenance window (`window_occurrences`).
- An occurrence is not allowed if it overlaps an exclusion whose scope blocks any of the steps. Use GKE's
  scope semantics: no upgrades blocks everything; no minor upgrades blocks minor upgrades of the control
  plane and of nodes but allows patches; no minor or node upgrades blocks minor upgrades and all node
  upgrades but allows control plane patches.
- No allowed occurrence within 90 days blocks the cluster.

**Ordering** (`plan`)
- Waves follow `policy.environment_order`; inside a wave the canary goes first, then by name.
- The first cluster may start at `now`. The next cluster's window must start at least
  `policy.cluster_gap_hours` after the previous cluster's window start. The next wave starts at least
  `policy.soak_hours[<env of the finished wave>]` after the last window start of that wave.
- Clusters already at the target are skipped silently. A blocked cluster is listed in `blocked`, and
  every cluster after it (in plan order) is listed in `held`, not planned.
- Output: `{"target_version", "waves": [{"environment", "clusters": [{"cluster", "window_start", "steps"}]}], "blocked": [{"cluster", "reasons"}], "held": [names]}`.
  Waves with no planned clusters are omitted. CLI exit 0 when nothing is blocked, 1 when something is,
  2 for unreadable input.

## Acceptance criteria (what the grader checks)

- On `fleet.json`: dev-1 2026-11-17, stg-1 2026-11-19, prod-blue 2026-12-03 (after the freeze), and
  prod-green blocked on quota.
- Edge cases: skew handling, missing channel or intermediate versions, already-current clusters, each
  exclusion scope with minor and patch rollouts, the 90-day horizon, surge vs blue-green quota, canary
  ordering, gap and soak, held clusters, CLI exit codes.
- `ANSWER.md`: your design and how you would run this for real (Pub/Sub cluster notifications, rollout
  sequencing, who approves).

## How to run

```bash
make setup
make run
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/w2-c1
make clean
```

## What to submit

`planner.py` and `ANSWER.md`.
