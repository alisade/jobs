# Reference: connect/x-2

Root cause: guardrail version 3 (PT-2026-17 fix) added a denied topic "Credentials and account access"
defined as "Any request about passwords, credentials, logins, MFA, account unlocks or account access"
with sample phrases that ARE the normal self-service requests ("my password", "unlock my account",
"reset password"). Input assessment blocks those turns before the model runs (invocation logs:
`stopReason: guardrail_intervened`, `usage.inputTokens: 0`, `trace.guardrail.inputAssessment...topicPolicy
...BLOCKED`), the assistant returns blockedInputMessaging and the Lambda hands off. Requests not covered
(e.g. "set up MFA on my new phone") still work, so the problem looks partial.

Red herrings: the new prompt line cannot cause it (the model received zero tokens on blocked turns);
`{USERNAME}` is the USERNAME PII entity's ANONYMIZE output action working as configured (and is why some
non-blocked turns also report guardrail_intervened).

Fix: `.grading/solution/guardrail/helpdesk-guardrail.json`: two narrow topics ("Other peoples passwords",
"Account takeover") with sample phrases about third parties, privileged/service accounts and bypassing
verification; prompt-attack HIGH and PASSWORD BLOCK unchanged; publish as version 4 and pin
`GUARDRAIL_VERSION=4` (`.grading/solution/config/lambda.env`).

Production: an eval gate (legit + red-team + held-out) before publishing a guardrail version, run with
ApplyGuardrail against the real classifier; roll guardrail versions via config with a canary; alarm on
the guardrail handoff rate; security and the help desk co-own the sample phrases.
