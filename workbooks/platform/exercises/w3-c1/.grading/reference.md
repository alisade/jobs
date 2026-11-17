# Reference: platform/w3-c1

Reference: `.grading/solution/importgen.py`. One mapper per asset type returning candidates and skips;
owners resolved after mapping (subnets inherit from their network by the network URL's last segment);
state IDs filtered; identifiers assigned in (owner, type, import ID) order so collisions get stable
suffixes; files rendered from sorted blocks.

Expected: riq file (riq-legacy network, two subnets, exports bucket, riq-legacy-pg), mdm file
(mdm-peering), riq-ml file (tsl-riq-models.v2 bucket), platform file (allow-iap-ssh, two service
accounts, three IAM members). Skipped: default network, the compute default SA, the container service
agent binding, the cloudservices editor binding. Unsupported: the Pub/Sub topic. Already managed:
allow-health-checks and the riq-api logWriter member.

Method notes: inventory with CAI, group by owner and blast radius, batches of a few resources, generate
config, clean it against the provider schema (see w3-t1), require an imports-only plan (w6-c1), then lock
out manual change. Use `google_project_iam_member` while migrating; moving to authoritative bindings
later is a separate, reviewed change.
