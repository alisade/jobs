# ANSWER: awsfde/w2-t1 "Order tool unavailable" after the Gateway release

## Approach

<!-- What you checked first and why; how you separated "the gateway cannot reach the function" from
"the function fails". -->

## Root cause

<!-- The exact mechanism with log lines (gateway and Lambda) and the code line. Why search kept
working. Why the authorizer, the role and the target rename are or are not the cause. -->

## Fix

<!-- What you changed and how you verified it (make test, make replay output). -->

## Trade-offs / what I would do in production

<!-- Contract tests that call the handler with Gateway-shaped contexts for every tool in tools.json,
an alarm on Lambda Errors for the target, error results the agent can act on, a staging gateway that
uses the production target name. -->
