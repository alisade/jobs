# ANSWER: platform/w6-t1 The import agent ran terraform apply in staging

## Approach

<!-- How you investigated: transcript, replay, audit excerpt. -->

## Root cause

<!-- Why the second apply passed the guard, which other control failed open, why the credentials could
apply. Quote the transcript and audit lines. Why the injection is the trigger, not the root cause. -->

## Fix

<!-- Guard design (parse, deny by default, allow list), approval fail closed, how you verified it. -->

## Trade-offs / what I would do in production

<!-- Credentials: read-only SA for the agent, no impersonation of apply SAs, plan with a separate reader
identity; applies only from the reviewed pipeline; sandboxing; alerting on agent sessions; evals with
injected labels; why a prompt change alone would not have helped. -->
