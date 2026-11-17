# ANSWER: platform/w3-t1 Import batch 07 plans to replace the core VPC

## Approach

<!-- How you read the plan and traced the diff back. -->

## Root cause

<!-- The attribute, why it differs, why it forces replacement, what apply would have done. Quote the
plan, generated.tf and the PR diff. Why the label is not the danger. -->

## Fix

<!-- What you changed and how you verified it. -->

## Trade-offs / what I would do in production

<!-- A cleanup rule for generated config (never drop ForceNew attributes, compare against the provider
schema), a CI gate that fails any migration plan that is not imports only, prevent_destroy policy for
stateful resources, small batches. -->
