# ANSWER: javaai/w4-t1 The tutor is slow at 09:00

## Approach

<!-- How you investigated: what you looked at first, what you ruled out and how. -->

## Root cause

<!-- The mechanism with evidence: what happens on one instance, why the autoscaler did not add
instances, where the 504s come from, why it is not cold starts. -->

## Fix

<!-- Code and service.yaml changes and how you verified them (make load before and after). -->

## Trade-offs / what I would do in production

<!-- Short. Sync def vs async client, thread pool size vs containerConcurrency, CPU allocation
(request-based vs always-on) for streaming, min instances cost, streaming responses for long
answers, load testing the 09:00 ramp. -->
