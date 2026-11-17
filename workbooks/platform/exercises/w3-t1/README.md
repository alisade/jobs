# platform/w3-t1 - Import batch 07 plans to replace the core VPC

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 3 (import blocks, generated config, migration method)

## Scenario

Tessellate (fictional) is bringing hand-built GCP resources under Terraform in small batches: import
blocks, `terraform plan -generate-config-out`, cleanup, and a plan that must be imports only before
anyone applies. Batch 07 (the RIQ legacy VPC, two subnets, an exports bucket and a Postgres instance)
plans `5 to import, 1 to add, 1 to change, 1 to destroy`. The engineer who did the cleanup worries about
the bucket label and wants to apply because "it is only labels".

There is no Terraform or GCP here: `tools/tfplan_sim.py` plans the HCL in `migration/` against the live
objects in `live/inventory.json` using a mini provider schema (`schema/google-mini.json`) with each
attribute's default and whether a change forces replacement. Read its docstring.

## What you have

| Path | What it is |
|---|---|
| `migration/` | the batch: import blocks and the cleaned-up resource config |
| `evidence/` | the thread, the generated config excerpt, the cleanup PR diff |
| `live/inventory.json`, `schema/google-mini.json` | what the provider would read, and its schema |
| `tools/tfplan_sim.py` | the local plan (`make plan`) |

## Your task

1. `make plan`: what is replaced, and which attribute forces it? Why does the config differ from live
   when nobody changed the network?
2. Deal with the bucket label difference correctly (do not change the live object).
3. Fix `migration/` until the plan is a pure import, and add the guard that turns any future
   replacement of the network or the database into a plan error.
4. `ANSWER.md`: root cause, evidence, what would have happened on apply, and a better cleanup rule for
   generated config.

## Acceptance criteria (what the grader checks)

- `Plan: 5 to import, 0 to add, 0 to change, 0 to destroy`, every resource a pure import.
- Import IDs unchanged; `auto_create_subnetworks` set explicitly on the network.
- `lifecycle { prevent_destroy = true }` on the network and the SQL instance; with a hidden live variant
  that drifts a ForceNew attribute, the plan errors instead of planning a destroy.
- `ANSWER.md` explains the cause and rules out the red herring.

## How to run

```bash
make setup
make plan
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/w3-t1
make clean
```

## What to submit

Your changes in `migration/` and `ANSWER.md`.
