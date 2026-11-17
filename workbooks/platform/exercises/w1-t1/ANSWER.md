# ANSWER: platform/w1-t1 Prod apply denied after the WIF hardening PR

## Approach

<!-- How you investigated: which artifact you read first, how you decided between the STS step and the
impersonation step, what you reproduced with the simulator. -->

## Root cause

<!-- The actual cause, with evidence: quote the claims, the audit log entries and the diff lines.
Explain why the thread's two suggestions are wrong. -->

## Fix

<!-- What you changed and why it keeps the intent of PR #388. How you verified it (simulator runs for the
cases that must pass and the cases that must fail). -->

## Trade-offs / what I would do in production

<!-- Options you rejected (attribute mapping on environment, job_workflow_ref, a principalSet on a
custom attribute), the GitHub environment protection this relies on, and how CI could catch a binding
that no real token can match before it reaches main. AWS comparison: the sub condition in an IAM OIDC
trust policy. -->
