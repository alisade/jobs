# ANSWER: connect/w8-c1 Flow promotion tool

## Approach

Treated the logical name as the join key: dev ARN/id -> dev inventory entry -> same kind/name in
the target manifest. Walked the parsed Content recursively with a JSONPath so every string is
checked, including Metadata and JSON embedded in attribute strings.

## Fix

ARN regex over every string (exact match, Lambda base + qualifier, Lex alias, instance), then
dev UUIDs as bare ids. Problems: unknown-reference, unmapped-in-target, dangling; any problem ->
ok=false and no artifacts. Modules sorted before flows; target ids attached; report lists every
replacement. Verified with make test and make promote for test, prod and dr.

## Trade-offs / what I would do in production

Runs in CI after export: promote -> lint -> deploy modules then flows -> native flow test cases
-> synthetic call -> watch ContactFlowErrors. Manifests generated from IaC outputs. Rollback is
redeploying the previous artifact (no flow aliases). Cannot catch semantic regressions or a Lex
alias that exists but points at an unbuilt version, so those need test cases.
