# ANSWER: backend/x-2 The migration that took the API down

## Approach

<!-- How you read the evidence: which snapshot first, how you built the wait-for chain. -->

## Root cause

<!-- Who held which lock, what the migration requested, why every API query waited, why staging was
fast, why the pool change and pod restarts did nothing. Quote the evidence. -->

## Fix

<!-- Your migrations, what lock each statement takes and for how long, and how you verified them
(make lint, make migrate). -->

## Trade-offs / what I would do in production

<!-- Short: deploy pipeline changes (lint in CI, migration job separate from rollout, retries on
lock_timeout), settings for the reporting role, alerts on lock waits and long transactions. -->
