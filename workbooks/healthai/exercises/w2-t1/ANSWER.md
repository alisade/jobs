# ANSWER: healthai/w2-t1 CriteriaService goes dark after a FHIR latency spike

## Approach

<!-- What you read first, what the repro showed, which metric gave it away. -->

## Root cause

<!-- The mechanism, with log lines and repro output as evidence. Why it outlived the spike, why CPU was idle,
why Health said SERVING, why a restart fixed it. -->

## Fix

<!-- The change and how you verified it (repro numbers before/after, tests). -->

## Trade-offs / what I would do in production

<!-- Alerting on permits/queue depth, a health check that reflects capacity, lint rules (no except BaseException),
deadline propagation, load tests with a slow dependency. -->
