# ANSWER: platform/w3-c1

## Approach

Table-like mappers per asset type, skip rules shared by SA assets and IAM members, owner resolution
after mapping, state filtering, deterministic naming in import ID order.

## Fix

All mappings, skip rules, owner inheritance for subnets, identifier sanitizing with stable collision
suffixes, sorted rendering and a report.

## Trade-offs / what I would do in production

Part of a method: CAI inventory, group by owner and blast radius, small batches, generate config, clean by
schema, imports-only plan gate, then IAM and org policy to stop manual change. Compare with bulk-export
and terraform query. Use iam_member during migration; authoritative bindings later as a reviewed change.
