# Reference: platform/w2-c1 Fleet upgrade planner

Reference implementation: `.grading/solution/planner.py`.

- `BLOCKING_SCOPES`: control plane minor and node minor are blocked by all three scopes; a control plane
  patch only by no upgrades; a node patch by no upgrades and no minor or node upgrades.
- `cluster_steps`: build the hop list (intermediate minors with `best_in_minor`, then the target). Before
  each hop, upgrade any pool that would exceed `max_node_skew` to the current control plane version.
  After the hops, upgrade every pool to the target. prod-blue therefore gets: CP 1.33.5, legacy-io
  1.30.14 to 1.33.5 (it would be 4 minors behind 1.34), CP 1.34.1, then default and legacy-io to 1.34.1.
- `static_blockers`: PDBs with zero allowed disruptions, and quota as max over pools (blue-green needs a
  full second pool: prod-green default is 6 x 8 = 48 vCPUs with 36 free).
- `plan`: sort by environment order, canary, name. Keep an `earliest` cursor: after each cluster,
  `start + cluster_gap_hours`; after each wave, `max(cursor, last_start + soak_hours[env])`. The first
  blocked cluster sets a halt flag; every later cluster goes to `held`.

Expected fixture result: dev-1 Tue 2026-11-17 03:00, stg-1 Thu 2026-11-19 03:00 (48 h soak), prod-blue
Thu 2026-12-03 03:00 (72 h soak lands on Sun 11-22; Wed 11-25 to Wed 12-02 fall in the
thanksgiving-freeze NO_MINOR_UPGRADES exclusion), prod-green blocked on quota.

Production notes a strong answer gives: GKE already sequences upgrades by channel and supports rollout
sequencing across fleets; a custom planner earns its place when you need reviewable intent, freeze
calendars from the business and quota checks before the window. Trigger it from Pub/Sub cluster
notifications (upgrade available, upgrade started), gate each wave on SLO burn rate of the canary,
require approval for prod, and fix prod-green by raising regional CPU quota or by switching that pool
to surge with max_surge sized to the free quota.
