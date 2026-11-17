# ANSWER: awsfde/w1-t1 Throttling storm after the resilience release

## Approach

<!-- What you looked at first and why; what each check ruled in or out. -->

## Root cause

<!-- The mechanism, precisely: calls per request in each release and where they come from, why
synchronized retries and the portal's own retry kept the bucket empty after the spike, and why the
caller saw 504s while the Lambda kept calling Bedrock. Quote log lines, dashboard rows and commands. -->

## Fix

<!-- What you changed in answer_svc/ and why; make replay output before and after. -->

## Trade-offs / what I would do in production

<!-- Whether to ask for a quota increase, cross-Region inference profiles, retry budgets across the
fleet, alarms (InvocationThrottles vs Invocations ratio), load tests for the 09:00 wave, a review rule
for retry layers. -->
